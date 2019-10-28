import re
from time import time
from typing import Optional, List

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg

from document.models import DocGraph, Comment, Note, GraphVersionRecord
from record.logic_class import field_check, EWRecord
from subgraph.class_link import BaseLink, SystemMade
from subgraph.class_node import BaseNode
from tools import base_tools
from tools.base_tools import model_to_dict
from tools.id_generator import id_generator
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


# todo node link 改写为类 level: 2
class DocGraphClass:
    re_for_old_id = re.compile('\\$_.*')

    def __init__(self, _id: int, user_id: int, collector=base_tools.NeoSet()):
        self.user_id = int(user_id)
        self.id = int(_id)
        self.collector = collector
        self.node: Optional[BaseNode] = None
        self.graph: Optional[DocGraph] = None
        self.container: [DocGraph, GraphVersionRecord] = None
        self.new_history: Optional[GraphVersionRecord] = None
        self.history: GraphVersionRecord.objects.filter()
        self.comments = []

        self.info_change_nodes: List[BaseNode] = []  # BaseNode
        self.info_change_links: List[BaseLink] = []  # BaseLink
        self.old_id = ""  # 节点的旧id
        self.node_id_old_new_map = {}
        self.link_id_old_new_map = {}
        self.doc_to_node_links = []  # 缓存容器

    def query_base(self):
        self.node = BaseNode(_id=self.id, user_id=self.user_id, _type='document', collector=self.collector)
        self.node.query_base()
        self.graph = DocGraph.objects.get(DocId=self.id)
        return self

    def query_comment(self):
        self.comments = Comment.objects.filter(BaseTarget=self.id,
                                               Is_Delete=False)
        return self.comments

    def __query_history(self):
        self.history = GraphVersionRecord.objects.filter(SourceId=self.id)

    # @error_check
    def graph_create(self, data):
        self.old_id = data["id"]
        self.graph = DocGraph(DocId=self.id, Nodes=[], Links=[], Conf={})
        self.node = BaseNode(_id=self.id, user_id=self.user_id, _type='document', collector=self.collector)
        self.update_nodes_links_info(data)
        self.container = self.graph
        self.update_doc_to_node(data)
        self.update_container(data)
        self.update_info()
        return self

    def graph_update(self, data, is_draft):
        self.query_base()
        self.__history_create(is_draft)
        self.update_nodes_links_info(data)
        if is_draft:
            # 草稿的话 更新history
            self.container = self.new_history
            self.update_container(data)
        else:
            # 非草稿 保存现有graph 更新graph
            self.synchronous(self.graph, self.new_history)
            self.container = self.graph
            self.update_doc_to_node(data)
            self.update_container(data)
            self.update_info()
        return self

    def update_nodes_links_info(self, data):
        """
        处理所有未保存的节点和边
        :param data:
        :return:
        """
        # 所有id使用["Setting"]["_id"] 因为Info信息不一定存在
        # 先处理Info的新建/编辑边
        new_nodes = []
        new_links = []
        graph = data['Graph']
        for node in graph["nodes"]:
            if self.re_for_old_id.match(str(node["Setting"]["_id"])):
                new_nodes.append(node)
            elif node["isEdit"]:
                self.info_change_nodes.append(self.update_node(node))
        self.info_change_nodes.extend(self.create_nodes(new_nodes))

        for link in graph["links"]:
            if self.re_for_old_id.match(str(link["Setting"]["_id"])):
                # 把$_开头的前端id重新绑定
                start = str(link["Setting"]["_start"]["Setting"]["_id"])
                end = str(link["Setting"]["_end"]["Setting"]["_id"])
                if self.re_for_old_id.match(start):
                    link["Setting"]["_start"]["Setting"]["_id"] = self.node_id_old_new_map[start]
                if self.re_for_old_id.match(end):
                    link["Setting"]["_end"]["Setting"]["_id"] = self.node_id_old_new_map[end]
                new_links.append(link)

            elif link["isEdit"]:
                self.info_change_links.append(self.update_link(link))
        self.info_change_links.extend(self.create_links(new_links))

    def update_doc_to_node(self, data):
        """
        先不更新container 先比较差异
        :return:
        """
        # Doc2graph关系生成
        add_node_list = []
        remove_node_list = []
        graph = data["Graph"]
        new_node_id_list = [node["Setting"]["_id"] for node in graph['nodes']]

        for node in graph["nodes"]:
            if self.check_for_exist_in_setting(node["Setting"]["_id"], _type='node') == -1:
                add_node_list.append(node)
        for node in self.graph.Nodes:
            if node["_id"] not in new_node_id_list:
                remove_node_list.append(node)
        link_id_list = id_generator(number=len(add_node_list), method='link', jump=2)
        for (index, node) in enumerate(add_node_list):
            if node["Setting"]["_id"] != self.id:
                doc_to_node = SystemMade(_id=link_id_list[index], user_id=self.user_id, collector=self.collector)
                node_id = node["Setting"]["_id"]
                doc_to_node.pre_create(
                    start=self.node.node,
                    end=self.bound_node(node),
                    p_label='Doc2Node',
                    data={"Is_Main": node_id in self.node.info.MainNodes, "DocImp": 50, "Correlation": 50})
                self.doc_to_node_links.append(doc_to_node)

        # Doc2graph关系取消
        for (index, node) in enumerate(remove_node_list):
            doc_to_node = SystemMade.query_by_start_end(start=self.node.id,
                                                        end=node["_id"],
                                                        user_id=self.user_id,
                                                        p_label="Doc2Node",
                                                        single=True)
            self.doc_to_node_links.append(doc_to_node.delete())

    def update_container(self, data):
        """
        更新container history或者graph
        :param data: 前端数据
        :return:
        """
        self.container.Nodes = [node['Setting'] for node in data["Graph"]["nodes"]]
        self.container.Links = [link['Setting'] for link in data["Graph"]["links"]]
        self.container.Conf = data["Conf"]
        self.container.Path = data["Path"]

    def update_info(self):
        """
        更新Info部分
        :return:
        """
        info = self.node.info
        info.Size = len(self.graph.Nodes)
        info.Complete = 50
        info.MainNodes = [node["_id"] for node in self.graph.Nodes
                          if node["Show"]["isMain"] and node["_id"] != self.id]

    @staticmethod
    def synchronous(item_a, item_b):
        """
        把a的数据同步到b
        :param item_a:
        :param item_b:
        :return:
        """
        fields = ['Nodes', 'Links', 'Path', 'Conf']
        for field in fields:
            prop = getattr(item_a, field)
            setattr(item_b, field, prop)

    def __history_create(self, is_draft):
        """

        :param is_draft: 是否是草稿
        :return:
        """
        self.__query_history()
        if not self.history:
            version_id = 1
        else:
            latest_draft = self.history.latest('CreateTime')
            version_id = latest_draft.VersionId % 20 + 1
        self.new_history = GraphVersionRecord(VersionId=version_id,
                                              SourceId=self.id,
                                              CreateUser=self.user_id,
                                              Name='History' + str(version_id),
                                              Is_Draft=is_draft,
                                              Nodes=[],
                                              Links=[],
                                              Path=[],
                                              Conf={})

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
        新建nodeInfo
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
                remote_node = self.node
            else:
                new_id = id_list[index]
                remote_node = BaseNode(_id=new_id, user_id=self.user_id, collector=self.collector)
            # 同步一下id
            node["Setting"]["_id"] = new_id
            self.node_id_old_new_map[old_id] = new_id
            remote_node.create(node["Info"])
            result.append(remote_node)
        return result

    def create_links(self, link_list):
        id_list = id_generator(number=len(link_list), method='link', jump=3)
        result = []
        for (index, link) in enumerate(link_list):
            # 先修改setting
            old_id = link["Setting"]["_id"]
            new_id = id_list[index]
            link["Setting"]["_id"] = new_id
            self.link_id_old_new_map[old_id] = new_id

            # 再创建边
            start = self.bound_node(link["Setting"]['_start'])
            end = self.bound_node(link["Setting"]['_end'])
            remote_link = BaseLink(_id=new_id, user_id=self.user_id, collector=self.collector)
            remote_link.create(start=start,
                               end=end,
                               p_label=link["Info"]["PrimaryLabel"],
                               data=link["Info"],
                               is_user_made=True)
            result.append(remote_link)
        return result

    def bound_node(self, node_setting):
        """

        :param node_setting: nodeSetting 包含_id, _type, _label
        :return: NeoNode
        """
        setting = node_setting["Setting"]
        labels = [setting['_type'], setting['_label']]
        _id = setting['_id']
        node = self.collector.Nmatcher.match(*labels, _id=_id).first()
        if not node:
            if self.re_for_old_id.match(str(_id)):
                _id = self.node_id_old_new_map[_id]
            cache = [node for node in self.info_change_nodes
                     if node.id == _id][0]
            return cache.node
        else:
            return node

    @staticmethod
    def check_reference(doc_id):
        pass
        return True

    # 是否在graph里存在
    def check_for_exist_in_setting(self, _id, _type):
        if _type == 'link':
            container = self.graph.Links
            id_map = self.link_id_old_new_map
        else:
            container = self.graph.Nodes
            id_map = self.node_id_old_new_map
        # _id转化为数字
        try:
            int_id = int(_id)
        except ValueError:
            try:
                int_id = id_map[_id]
            except KeyError:
                return -1

        for index, item in enumerate(container):
            if int_id == item["_id"]:
                return index
        return -1

    def save(self):
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

    def save_cache(self):
        pass

    def clear_cache(self):
        pass

    def handle_for_frontend_as_graph(self):
        result = {
            "Base": self.node.handle_for_frontend(),
            "Graph": {
                "nodes": self.graph.Nodes,
                "links": self.graph.Links,
                "notes": []
            },  # todo 把notes加上
            "Conf": self.graph.Conf,
            "Path": self.graph.Path,
            "State": {
                "isSelf": self.node.ctrl.CreateUser == self.user_id,
            },
        }
        return result

    def handle_for_frontend(self):
        return self.node.handle_for_frontend()


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
