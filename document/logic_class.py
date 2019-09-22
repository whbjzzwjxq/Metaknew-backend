from document.models import DocPaper, DocGraph, Comment, Note
from django.core.exceptions import ObjectDoesNotExist
from tools import base_tools, encrypt
from time import time
import datetime
from users.models import UserConcern, UserRepository, UserDocProgress, Privilege
from record.logic_class import error_check, field_check, EWRecord
from record.models import DocumentVersionRecord
from subgraph.logic_class import BaseNode, SystemMade
from django.db.models import Avg
from tools.id_generator import id_generator, device_id
from django.db.models import Max
from tools.redis_process import week
from tools.base_tools import model_to_dict

types = ["StrNode", "InfNode", "Media", "Document"]

# todo doc重新定义 level: 0

# todo 数据结构精简化 目的: 节约内存 节约流量 level: 3
# Field: Field -> TranslateField, LocationField, TypeField 等等 可以给每个Field注入格式检测， 翻译队列等
# Privilege: BaseSource: self.user, self._id 可以捕获异常和错误 统一生成权限表
# HistoryRecord: UpdateField 可以记录每个Field的变化


class BaseDoc:

    def __init__(self, _id: str, user: str, collector=base_tools.NeoSet()):
        self.user = user
        self._id = _id
        self.collector = collector
        self.is_create = False
        self.is_draft = False
        self.is_creator = True
        self.personal_notes = []
        self.node = BaseNode(_id=self._id, user=self.user, collector=self.collector).query_with_label("Document")
        if self.node:
            if self.node.info.Has_Paper:
                try:
                    self.paper = DocPaper.objects.get(pk=self._id)
                except ObjectDoesNotExist:
                    self.paper = DocPaper()

            if self.node.info.Has_Graph:
                try:
                    self.graph = DocGraph.objects.get(pk=self._id)
                except ObjectDoesNotExist:
                    self.graph = DocGraph()

        self.loading_history = DocumentVersionRecord()
        self.new_history = DocumentVersionRecord()
        self.include_nodes = []
        self.include_links = []
        self.comments = []

    def query_comment(self):
        self.comments = Comment.objects.filter(BaseTarget=self._id,
                                               Is_Delete=False)
        return self.comments

    @error_check
    def create(self, data):
        self.is_create = True
        self.is_draft = True
        self.is_creator = True
        info = data["info"]
        self.node = BaseNode(_id=self._id, user=self.user, collector=self.collector).create(info)
        if info["Has_Graph"]:
            graph = data["graph"]
            self.graph = DocGraph()
            self.update_graph(graph)
        if data["Has_Paper"]:
            paper = data["paper"]

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
                                                 SourceId=self._id,
                                                 CreateUser=self.user,
                                                 Name=name,
                                                 GraphContent={
                                                     "AddNodes": [],
                                                     "AddLinks": [],
                                                     "RemoveNodes": [],
                                                     "RemoveLinks": [],
                                                     "RefNodes": [],
                                                     "RefLinks": [],
                                                     "CommonNotes": [],
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
        self.history = DocumentVersionRecord.objects.filter(SourceId=self._id)

    def __history_save(self):

        if self.is_draft:
            self.new_history.save()
        else:
            self.loading_history.save()

    def update_paper(self, paper):
        pass

    def update_graph(self, graph):
        if self.is_draft:
            self.new_history.GraphContent = graph
        else:
            # 先Add, 再Remove, 最后Update
            # todo history 简单化 level: 2
            add_nodes = map(self.add_node, graph["AddNodes"])
            add_links = map(self.add_link, graph["AddLinks"])
            remove_nodes = map(self.remove_node, graph["RemoveNodes"])
            remove_links = map(self.remove_link, graph["RemoveLinks"])
            ref_nodes = map(self.update_node, graph["RefNodes"])
            ref_links = map(self.update_link, graph["RefLinks"])

    def add_node(self, node):  # done
        self.loading_history.GraphContent["AddNodes"].append(node)
        if node["Plabel"] == "Document":
            if self.reference(node["_id"]):
                self.graph.Nodes.append(node)
                self.add_doc2node(node)
                return True
            else:
                return False
        else:
            self.graph.Nodes.append(node)
            self.add_doc2node(node)
            return True

    def add_doc2node(self, node):
        new_link = {
            "start": self.collector.Nmatcher.match(node["_id"]).first(),
            "end": self.node.node,
            "Is_Main": node["Is_Main"],
            "Correlation": 50 + int(node["Is_Main"]) * 25
        }
        link = SystemMade(link_type="Doc2Node", collector=self.collector, user=self.user)
        link.create(new_link)

    def add_link(self, link):  # done
        self.loading_history.GraphContent["AddLinks"].append(link)
        self.graph.Links.append(link)
        return True

    def remove_node(self, conf):  # done
        index = self.check_for_exist(conf["_id"], self.graph.Nodes)
        if index >= 0:
            node = self.graph.Nodes[index]
            self.loading_history.GraphContent["RemoveNodes"].append(node)
            self.graph.Nodes.pop(index)
        else:
            raise ObjectDoesNotExist

    def remove_link(self, conf):
        index = self.check_for_exist(conf["_id"], self.graph.Links)
        if index >= 0:
            link = self.graph.Links[index]
            self.loading_history.GraphContent["RemoveLinks"].append(link)
            self.graph.Links.pop(index)
        else:
            raise ObjectDoesNotExist

    def update_node(self, conf):
        index = self.check_for_exist(conf["_id"], self.graph.Nodes)
        if index >= 0:
            node = self.graph.Nodes[index]
            for key in node:
                old_prop = getattr(node, key, default=None)
                new_prop = getattr(conf, key, default=None)
                field = (self.graph.Nodes, index, key, "RefNodes")
                self.update_prop(field, old_prop, new_prop)

    def update_link(self, conf):
        # todo 看看这里需不需要field_check level: 3
        index = self.check_for_exist(conf["_id"], self.graph.Links)
        if index >= 0:
            link = self.graph.Links[index]
            for key in link:
                old_prop = getattr(link, key, default=None)
                new_prop = getattr(conf, key, default=None)
                field = (self.graph.Links, index, key, "RefLinks")
                self.update_prop(field, old_prop, new_prop)

    def update_prop(self, field, old_prop, new_prop):
        self.loading_history.GraphContent[field[3]].append(old_prop)
        target = field[0][1]
        setattr(target, field[2], new_prop)

    def update_note(self, notes):
        # 更新个人notes
        self.personal_notes = BaseNote.query_user_document(doc_id=self._id, user=self.user)
        new_id = id_generator(number=len(notes["AddNotes"]),
                              method='Device',
                              content=device_id,
                              jump=1)
        for note in notes["RemoveNotes"]:
            index = self.check_for_exist(note["_id"], self.personal_notes)
            if index >= 0:
                self.personal_notes.pop(index)
            else:
                raise ObjectDoesNotExist

        for note in notes["RefNotes"]:
            index = self.check_for_exist(note["_id"], self.personal_notes)
            if index >= 0:
                self.personal_notes[index] = note
            else:
                raise ObjectDoesNotExist

        for index, note in enumerate(notes["AddNotes"]):
            note["_id"] = new_id[index]
            note["Document"] = self._id
            self.personal_notes.append(note)
            # test 测试getattr setattr 等方法

    def update_common_note(self, notes):
        if self.is_creator:
            self.loading_history.GraphContent["CommonNotes"] = self.graph.CommonNotes
            self.graph.CommonNotes = notes

    def update_conf(self, conf):
        pass

    @staticmethod
    def reference(doc_id):
        pass
        return True

    @staticmethod
    def check_for_exist(_id, target):
        for index, ele in enumerate(target):
            old_id = getattr(ele, "_id")
            if _id == old_id:
                return index
        return -1

    def save(self):
        if time() - self.node.CountCacheTime.timestamp() > week:
            self.re_count()
            self.node.CountCacheTime = datetime.datetime.now().replace(microsecond=0)
        self.node.UpdateTime = datetime.datetime.now().replace(microsecond=0)
        self.node.save()
        self.graph.save()

    def re_count(self):
        self.node.info.Size = self.graph.Nodes.count()
        result = UserConcern.objects.filter(SourceId=self._id)
        self.node.ctrl.Useful = result.filter(Useful__gte=0).aggregate(Avg("Useful"))
        self.node.ctrl.HardLevel = result.filter(HardLevel__gte=0).aggregate(Avg("HardLevel"))
        self.node.ctrl.Imp = result.filter(Imp__gte=0).aggregate(Avg("Imp"))
        self.node.CountCacheTime = time()
        # todo hot_count level : 1

    def get_default_image(self):
        pass

    def upload_media(self, medias):
        self.node.IncludedMedia.extend(medias)

    def update_media_by_doc_id(self, doc_id, include_media):
        pass
        return self

    def remove_media(self, medias):
        pass

    def save_cache(self):
        pass

    def clear_cache(self):
        pass


# # 个人化的跟专题有关的内容
# class PersonalDoc:
#
#     def __init__(self, doc_id, user):
#         self.user = user
#         self.doc_id = doc_id
#         self.concern = {}
#         self.notes = []
#
#     def query_all(self):
#         self.query_note()
#         self.query_concern()
#         return self
#
#     def query_note(self):
#         self.notes = Note.objects.filter(CreateUser=self.user,
#                                          DocumentId=self.doc_id)
#         return self.notes
#
#     def query_concern(self):
#         self.concern = UserConcern.objects.filter(UserId=self.user,
#                                                   SourceId=self.doc_id)
#         return self.concern


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

    def handle_for_frontend(self):
        # test 测试记录一下
        note = {field.name: field for field in self.note.objects.fields}
        return note

    def handle_for_open(self):
        pass
