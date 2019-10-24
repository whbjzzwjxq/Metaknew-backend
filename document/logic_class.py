import datetime
from time import time
from typing import Optional, List

import re
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg
from django.db.models import Max

from document.models import DocGraph, Comment, Note
from record.logic_class import error_check, field_check, EWRecord
from record.models import DocumentVersionRecord
from subgraph.class_link import BaseLink, SystemMade
from subgraph.class_node import BaseNode
from tools import base_tools
from tools.base_tools import model_to_dict
from tools.id_generator import id_generator
from tools.redis_process import week
from users.models import UserConcern

# Field: Field -> TranslateField, LocationField, TypeField 等等 可以给每个Field注入格式检测， 翻译队列等
# Privilege: BaseSource: self.user, self._id 可以捕获异常和错误 统一生成权限表
# HistoryRecord: UpdateField 可以记录每个Field的变化
frontend_format = {
    "Info": {
        "MainNodes": []
    },
    "Ctrl": {},
    "Graph": {
        "nodes": [],  # 添加的已有节点 或者 改变了样式的已有节点
        "links": [],  # 添加的已有关系 或者 改变了样式的已有关系
        "notes": [],
        "Conf": {}
    },
    "Setting": {},
    "Path": []
}


class BaseDocGraph:
    re_for_new_id = re.compile('\\$_.*')

    def __init__(self, _id: int, user_id: int, collector=base_tools.NeoSet()):
        self.user_id = int(user_id)
        self.id = int(_id)
        self.collector = collector
        self.is_create = False
        self.is_draft = False
        self.node: Optional[BaseNode] = None
        self.graph: Optional[DocGraph] = None

        self.loading_history = DocumentVersionRecord()
        self.new_history = DocumentVersionRecord()
        self.info_change_nodes: List[BaseNode] = []  # BaseNode
        self.info_change_links: List[BaseLink] = []  # BaseLink
        self.new_nodes_cache = []  # 需要新建的节点
        self.new_links_cache = []  # 需要新建的边
        self.add_node_list = []  # 新加入的节点
        self.old_id = ""
        self.comments = []
        self.node_id_old_new_map = {}
        self.link_id_old_new_map = {}
        self.doc_to_node_links = []  # 缓存容器

    def query_base(self):
        self.node = BaseNode(_id=self.id, user_id=self.user_id, collector=self.collector)
        self.node.query_base()
        self.graph = DocGraph.objects.get(DocId=self.id)
        return self

    def query_comment(self):
        self.comments = Comment.objects.filter(BaseTarget=self.id,
                                               Is_Delete=False)
        return self.comments

    # @error_check
    def create(self, data):
        self.is_create = True
        self.is_draft = False
        self.old_id = data["id"]
        self.graph = DocGraph(DocId=self.id, Nodes=[], Links=[], Conf={})
        self.__all_update(data)
        return self

    def update(self, data, is_draft):
        self.query_base()
        self.is_create = False
        self.is_draft = is_draft
        self.__all_update(data)
        return self

    def __all_update(self, data):
        self.update_graph(data["Graph"])
        self.graph.Conf = data["Conf"]
        self.graph.Paths = data["Path"]
        self.node.info.Size = len(self.graph.Nodes)
        self.node.info.Complete = 50
        for node in self.graph.Nodes:
            if node["Show"]["isMain"] and type(node["_id"]) == int:
                self.node.info.MainNodes.append(node["_id"])
        link_id_list = id_generator(number=len(self.add_node_list), method='link', jump=2)
        for (index, node) in enumerate(self.add_node_list):
            doc_to_node = SystemMade(_id=link_id_list[index], user_id=self.user_id, collector=self.collector)
            node_id = node["Setting"]["_id"]
            labels = [node["Setting"]["_type"], node["Setting"]["_label"]]
            doc_to_node.pre_create(
                start=self.node.node,
                end=self.bound_node(labels=labels, _id=node_id),
                p_label='Doc2Node',
                data={"Is_Main": node_id in self.node.info.MainNodes, "DocImp": 50, "Correlation": 50})
            self.doc_to_node_links.append(doc_to_node)

    def check_privilege(self):
        pass

    def __history_create(self, name):
        if self.is_create:
            version_id = 1
        else:
            self.__query_history()
            version_id = self.history.aggregate(Max("VersionId"))
            version_id += 1
        self.new_history = DocumentVersionRecord(VersionId=version_id,
                                                 SourceId=self.id,
                                                 CreateUser=self.user_id,
                                                 Name=name,
                                                 GraphContent={
                                                     "nodes": [],
                                                     "links": [],
                                                     "notes": [],
                                                     "Conf": {}
                                                 },
                                                 PaperContent={},
                                                 Is_Draft=self.is_draft
                                                 )
        if self.is_draft:
            self.new_history.BaseHistory = self.loading_history.VersionId
        else:
            if self.is_create:
                self.new_history.BaseHistory = 0
            else:
                self.loading_history.BaseHistory = self.new_history.VersionId
                self.new_history.BaseHistory = 0

    def __query_history(self):
        self.history = DocumentVersionRecord.objects.filter(SourceId=self.id)

    def __history_save(self):

        if self.is_draft:
            self.new_history.save()
        else:
            self.loading_history.save()

    def update_graph(self, graph):
        # 所有id使用["Setting"]["_id"] 因为Info信息不一定存在
        # 先处理Info的新建/编辑边
        for node in graph["nodes"]:
            if not node["isRemote"]:
                self.new_nodes_cache.append(node)
            elif node["isEdit"]:
                self.info_change_nodes.append(self.update_node(node))
        self.info_change_nodes.extend(self.create_nodes(self.new_nodes_cache))

        # 再处理graph.Nodes的变化
        for node in graph["nodes"]:
            if node["State"]["isDeleted"]:
                self.remove_node(node)
            elif node["State"]["isAdd"]:
                self.add_node(node)
            else:
                self.change_node(node)

        # 然后新建/编辑边
        for link in graph["links"]:
            if not link["isRemote"]:
                # 把$_开头的前端id重新绑定
                start = str(link["Setting"]["_start"]["Setting"]["_id"])
                end = str(link["Setting"]["_end"]["Setting"]["_id"])
                if self.re_for_new_id.match(start):
                    link["Setting"]["_start"]["Setting"]["_id"] = self.node_id_old_new_map[start]
                if self.re_for_new_id.match(end):
                    link["Setting"]["_end"]["Setting"]["_id"] = self.node_id_old_new_map[end]
                self.new_links_cache.append(link)

            elif link["isEdit"]:
                self.info_change_links.append(self.update_link(link))
        self.info_change_links.extend(self.create_links(self.new_links_cache))

        for link in graph["links"]:
            if link["State"]["isDeleted"]:
                self.remove_link(link)
            elif link["State"]["isAdd"]:
                self.add_link(link)
            else:
                self.change_link(link)

    def add_node(self, node: dict):
        """
        向Graph添加节点
        :param node:
        :return:
        """
        # self.loading_history.GraphContent["addNodes"].append(node)
        state = True
        # 如果是专题而且不允许引用就不引用 防止Hack引用
        if node["Setting"]["_type"] == "document" and not self.check_reference(node["Setting"]["_id"]):
            state = False
        if state:
            self.graph.Nodes.append(node["Setting"])
            self.add_node_list.append(node)
        return state

    def add_link(self, link):
        """
        向Graph添加已有关系
        :param link:
        :return:
        """
        # self.loading_history.GraphContent["addLinks"].append(link)
        self.graph.Links.append(link["Setting"])
        return True

    def add_doc2node(self, node):
        pass

    def remove_node(self, node):
        """
        移除节点
        :param node:
        :return:
        """
        index = self.check_for_exist_in_setting(node["Setting"]["_id"], self.graph.Nodes)
        if index >= 0:
            node = self.graph.Nodes[index]
            # self.loading_history.GraphContent["removeNodes"].append(node)
            self.graph.Nodes.pop(index)
            doc_to_node = SystemMade.query_by_start_end(start=self.node.id,
                                                        end=node["Setting"]["_id"],
                                                        user_id=self.user_id,
                                                        p_label="Doc2Node",
                                                        single=True)
            doc_to_node.ctrl.isUsed = False
            doc_to_node.ctrl.save()
        else:
            raise ObjectDoesNotExist

    def remove_link(self, link):
        """
        移除关系
        :param link: 前端link格式
        :return:
        """
        index = self.check_for_exist_in_setting(link["Info"]["id"], self.graph.Links)
        if index >= 0:
            link = self.graph.Links[index]
            # self.loading_history.GraphContent["removeLinks"].append(link)
            self.graph.Links.pop(index)
        else:
            raise ObjectDoesNotExist

    def update_node(self, node):
        """
        编辑的节点
        :param node:
        :return:
        """
        # update节点 注意不要存入Nodes
        remote_node = BaseNode(_id=node["Setting"]["_id"], user_id=self.user_id, collector=self.collector)
        remote_node.query_base()
        remote_node.info_update(node["Info"])
        return remote_node

    def update_link(self, link):
        remote_link = BaseLink(_id=link["Setting"]["_id"], user_id=self.user_id, collector=self.collector)
        remote_link.query_base()
        remote_link.info_update(link["Info"])
        return remote_link

    def create_nodes(self, node_list):
        """
        新建node
        :param node_list:
        :return:
        """
        id_list = id_generator(number=len(node_list), method='node', jump=3)
        result = []
        for (index, node) in enumerate(node_list):
            # 因为link这个时候还是旧有id 所以要存下来
            old_id = node["Setting"]["_id"]
            if old_id == self.old_id:
                new_id = self.id
                remote_node = BaseNode(_id=new_id, user_id=self.user_id, collector=self.collector)
                self.node = remote_node
            else:
                new_id = id_list[index]
                remote_node = BaseNode(_id=new_id, user_id=self.user_id, collector=self.collector)
            node["Setting"]["_id"] = new_id
            node["isAdd"] = True
            self.node_id_old_new_map[old_id] = new_id
            remote_node.create(node["Info"])
            result.append(remote_node)
            # 这里处理一下Graph自身
        return result

    def create_links(self, link_list):
        id_list = id_generator(number=len(link_list), method='link', jump=3)
        result = []
        for (index, link) in enumerate(link_list):
            # 先修改setting
            old_id = link["Setting"]["_id"]
            new_id = id_list[index]
            link["Setting"]["_id"] = new_id
            link["isAdd"] = True
            self.link_id_old_new_map[old_id] = new_id

            # 再创建边
            start = self.link_id_to_node(link, "_start")
            end = self.link_id_to_node(link, "_end")
            remote_link = BaseLink(_id=new_id, user_id=self.user_id, collector=self.collector)
            remote_link.create(start=start,
                               end=end,
                               p_label=link["Info"]["PrimaryLabel"],
                               data=link["Info"],
                               is_user_made=True)
            result.append(remote_link)
        return result

    def link_id_to_node(self, link, location):
        """

        :param link: link
        :param location: start||end
        :return: NeoNode
        """
        setting = link["Setting"]
        labels = [setting[location]["Setting"]["_label"], setting[location]["Setting"]["_type"]]
        # 先在远端查找对应节点
        _id = setting[location]["Setting"]["_id"]
        return self.bound_node(labels, _id)

    def bound_node(self, labels, _id):
        node = self.collector.Nmatcher.match(*labels, _id=_id).first()
        if not node:
            if self.re_for_new_id.match(str(_id)):
                _id = self.node_id_old_new_map[_id]
            cache = [node for node in self.info_change_nodes
                     if node.id == _id][0]
            return cache.node
        else:
            return node

    def change_node(self, node):
        index = self.check_for_exist_in_setting(node["Setting"]["_id"], self.graph.Nodes)
        if index >= 0:
            self.graph.Nodes[index] = node["Setting"]
        else:
            if node["Setting"]["_id"] == self.node.id:
                self.graph.Nodes.append(node["Setting"])

    def change_link(self, link):
        index = self.check_for_exist_in_setting(link["Setting"]["_id"], self.graph.Links)
        if index >= 0:
            self.graph.Links[index] = link["Setting"]

    @staticmethod
    def check_reference(doc_id):
        pass
        return True

    @staticmethod
    def check_for_exist_in_setting(_id, target):
        for index, item in enumerate(target):
            if int(_id) == item["_id"]:
                return index
        return -1

    def save(self):
        if time() - self.node.ctrl.CountCacheTime.timestamp() > week:
            self.re_count()
            self.node.ctrl.CountCacheTime = datetime.datetime.now().replace(microsecond=0)
        pass

    def re_count(self):
        result = UserConcern.objects.filter(SourceId=self.id)
        self.node.ctrl.Useful = result.filter(Useful__gte=0).aggregate(Avg("Useful"))
        self.node.ctrl.HardLevel = result.filter(HardLevel__gte=0).aggregate(Avg("HardLevel"))
        self.node.ctrl.Imp = result.filter(Imp__gte=0).aggregate(Avg("Imp"))
        self.node.ctrl.CountCacheTime = time()
        # todo hot_count level : 1

    def node_index(self):
        body = self.node.node_index()
        body["type"] = "document"
        return body

    def get_default_image(self):
        pass

    def update_media_by_doc_id(self, doc_id, include_media):
        pass
        return self

    def remove_media(self, medias):
        pass

    def save_cache(self):
        pass

    def clear_cache(self):
        pass

    def handle_for_frontend(self):
        result = {
            "Base": self.node.handle_for_frontend(),
            "Graph": {
                "nodes": self.graph.Nodes,
                "links": self.graph.Links,
                "notes": []
            },  # todo 把notes加上
            "Conf": self.graph.Conf,
            "Path": self.graph.Paths,
            "State": {
                "isSelf": self.node.ctrl.CreateUser == self.user_id,
            },
        }
        return result


class BaseComment:

    def __init__(self):
        self.comment = None

    @staticmethod
    def query_doc(doc_id):
        comment = Comment.objects.filter(Source=doc_id, Is_Delete=False)
        return comment

    @staticmethod
    def query_user(user):
        comment = Comment.objects.filter(Owner=user, Is_Delete=False)
        return comment

    @staticmethod
    def query_reply_to_user(user):
        comment = Comment.objects.filter(TargetUser=user, Is_Delete=False)
        return comment

    def add_single(self, _id, target_id, reply_id, reply_user, content, user):
        content = str(content)

        self.comment = Comment(CommentId=_id,
                               SourceId=target_id,
                               TargetId=reply_id,
                               TargetUser=reply_user,
                               Content=content,
                               Owner=user,
                               Is_Delete=False)
        self.comment.save()
        return self

    def delete(self):
        self.comment.Is_Delete = True
        self.comment.save()
        return True


class BaseNote:
    note_type = [
        "normal",
        "dark",
        "circle"
    ]

    editable_prop = ["Content", "TagType", "Conf", "Is_Open"]

    def __init__(self, user, _id, note: Note()):
        self.user = user
        self.note = note
        self._id = _id
        self.warn = []

    def query_single(self):
        try:
            self.note = Note.objects.get(NoteId=self._id, Is_Delete=False)
            return self
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def query_user_document(doc_id, user):
        notes = Note.objects.filter(DocumentId=doc_id, CreateUser=user, Is_Delete=False)
        result = []
        for note in notes:
            result.append(model_to_dict(note))
        return result

    def create(self, note):
        self.note = Note(NoteId=note["NoteId"],
                         CreateUser=self.user,
                         DocumentId=note["DocumentId"])

        self.update_content(note)

    def delete(self):
        self.note.Is_Delete = True
        self.note.save()

    @field_check
    def update_prop(self, field, new_prop, old_prop):
        setattr(self.note, field, new_prop)

    def update_content(self, note):

        update_prop = {}
        if len(str(note["Content"])) <= 1024:
            update_prop.update({"Content": str(note["Content"])})
        else:
            self.warn.append({"field": "Content", "warn_type": "toolong_str"})

        if note["TagType"] in self.note_type:
            update_prop.update({"TagType": note["TagType"]})
        else:
            self.warn.append({"field": "TagType", "warn_type": "error_type"})

        if note["Conf"] is not {}:
            self.note.Conf = note["Conf"]
        else:
            self.warn.append({"field": "Conf", "warn_type": "empty_prop"})

        update_prop.update({"Is_Open": note["Is_Open"]})

        if not self.warn == []:
            EWRecord.add_warn_record(user=self.user,
                                     source_id=self.note.NoteId,
                                     source_label="note",
                                     content=self.warn)
        self.note.objects.update(update_prop)
        return self

    def handle_for_open(self):
        pass
