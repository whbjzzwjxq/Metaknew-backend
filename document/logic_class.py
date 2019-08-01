from document.models import DocPaper, DocGraph, DocInfo, Comment, Note
from django.core.exceptions import ObjectDoesNotExist
from tools import base_tools, encrypt
from time import time
import datetime
from users.models import UserConcern, UserRepository, UserDocProgress, Privilege
from record.logic_class import error_check, field_check
from subgraph.logic_class import BaseNode
from django.db.models import Avg

types = ['StrNode', 'InfNode', 'Media', 'Document']

# todo doc重新定义 level: 0

# todo 数据结构精简化 目的: 节约内存 节约流量 level: 3
# Field: Field -> TranslateField, LocationField, TypeField 等等 可以给每个Field注入格式检测， 翻译队列等
# Privilege: BaseSource: self.user, self._id 可以捕获异常和错误 统一生成权限表
# HistoryRecord: UpdateField 可以记录每个Field的变化

document_frontend_edit = {
    "node": {
        "info": {},
        "ctrl": {},
        "conf": {},
    },
    "graph": {
        "RefNodes": [],
        "RefLinks": [],
        "UpdateNodes": [],
        "UpdateLinks": [],
        "AddNodes": [],
        "AddLinks": [],
        "CommonNotes": []
    },
    "paper": {}
}

document_frontend_normal = {
    "node": {
        "info": {},
        "ctrl": {},
        "conf": {},
    },
    "graph": {
        "Nodes": [],
        "Links": [],
        "CommonNotes": []
    },
    "paper": {

    }
}


class BaseDoc:

    def __init__(self, _id, user, collector=base_tools.NeoSet()):
        self.user = user
        self._id = _id
        self.collector = collector

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

        self.include_nodes = []
        self.include_links = []
        self.comments = []

    def query_comment(self):
        self.comments = Comment.objects.filter(BaseTarget=self._id,
                                               Is_Delete=False)
        return self.comments

    @error_check
    def create(self, data):
        info = data["info"]
        self.node = BaseNode(_id=self._id, user=self.user, collector=self.collector).create(info)
        if info["Has_Graph"]:
            graph = data["graph"]
            self.update_graph(graph)
        if data["Has_Paper"]:
            paper = data["paper"]

    def update_graph(self, graph):
        ref_nodes = graph["RefNodes"]
        ref_links = graph["RefLinks"]
        update_nodes = graph["UpdateNodes"]
        update_links = graph["UpdateLinks"]
        add_nodes = graph["AddNodes"]
        add_links = graph["AddLinks"]
        common_notes = graph["CommonNotes"]

    def update_paper(self, paper):
        pass

    def update_info(self, data):
        self.node.Title = data['title']
        self.node.MainPic = data['main_pic']
        self.node.Topic = data['Topic']
        self.node.Description = data['description']

    def reference(self):
        pass

    def add_node(self, doc_id, conf):
        self.nodes.append({'doc_id': doc_id, 'conf': conf})

    def remove_node(self, doc_id):
        if doc_id in self.nodes:
            index = self.nodes.index(doc_id)
            self.graph.IncludedNodes.pop(index)

        self.remove_main_node(doc_id=doc_id)
        self.remove_rel(node=doc_id, link_doc_id=None)

    def update_node(self, doc_id, conf):
        if doc_id in self.nodes:
            index = self.nodes.index(doc_id)
            self.graph.IncludedNodes[index]['conf'] = conf

    def set_main_node(self, doc_id):
        self.graph.MainNodes.append(doc_id)

    def remove_main_node(self, doc_id):
        self.graph.MainNodes.remove(doc_id)

    def add_rel(self, doc_id, source, target, conf):
        self.graph.IncludedLinks.append({'doc_id': doc_id,
                                         'source': source,
                                         'target': target,
                                         'conf': conf})

    def remove_rel(self, link_doc_id: None, node: None):
        if link_doc_id is not None:
            if link_doc_id in self.links:
                index = self.links.index(link_doc_id)
                self.graph.IncludedLinks.pop(index)
        elif node is not None:
            source = [link['source'] for link in self.graph.IncludedLinks]
            target = [link['target'] for link in self.graph.IncludedLinks]
            while node in source:
                index = source.index(node)
                self.graph.IncludedLinks.pop(index)
            while node in target:
                index = target.index(node)
                self.graph.IncludedLinks.pop(index)

    def update_rel(self, doc_id, conf):

        if doc_id in self.links:
            index = self.links.index(doc_id)
            self.graph.IncludedLinks[index]['conf'] = conf

    def save(self):
        if time() - self.node.CountCacheTime.timestamp() > encrypt.week:
            self.re_count()
            self.node.CountCacheTime = datetime.datetime.now()
        self.node.UpdateTime = datetime.datetime.now()
        self.node.save()
        self.graph.save()

    def re_count(self):
        self.node.info.Size = self.graph.IncludedNodes.count()
        result = UserConcern.objects.filter(SourceId=self._id)
        self.node.ctrl.Useful = result.filter(Useful__gte=0).aggregate(Avg('Useful'))
        self.node.ctrl.HardLevel = result.filter(HardLevel__gte=0).aggregate(Avg('HardLevel'))
        self.node.ctrl.Imp = result.filter(Imp__gte=0).aggregate(Avg('Imp'))
        self.node.CountCacheTime = time()
        # todo hot_count level : 1

    def get_default_image(self):
        pass

    def upload_media(self, medias):
        self.node.IncludedMedia.extend(medias)

    def update_media_by_doc_id(self, doc_id, include_media):
        self.node = DocInfo.objects.filter(doc_id=doc_id).update(IncludedMedia=include_media)
        return self

    def remove_media(self, medias):
        pass

    def save_cache(self):
        pass

    def clear_cache(self):
        pass


# 个人化的跟专题有关的内容
class PersonalDoc:

    def __init__(self, doc_id, user):
        self.user = user
        self.doc_id = doc_id
        self.concern = {}
        self.notes = []

    def query_all(self):
        self.query_note()
        self.query_concern()
        return self

    def query_note(self):
        self.notes = Note.objects.filter(CreateUser=self.user,
                                         DocumentId=self.doc_id)
        return self.notes

    def query_concern(self):
        self.concern = UserConcern.objects.filter(UserId=self.user,
                                                  SourceId=self.doc_id)
        return self.concern


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

    def __init__(self, user):
        self.user = user
        self.note = Note()
        self.warn = []

    def query_single(self, _id):
        try:
            self.note = Note.objects.get(NoteId=_id, Is_Delete=False)
            return self
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def query_user_document(_id, user):
        notes = Note.objects.filter(DocumentId=_id, CreateUser=user, Is_Delete=False)
        return notes

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
        warn = []
        update_prop = {}
        if len(str(note["Content"])) <= 1024:
            update_prop.update({"Content": str(note["Content"])})
        else:
            warn.append({"field": "Content", "warn_type": "toolong_str"})

        if note["TagType"] in self.note_type:
            update_prop.update({"TagType": note["TagType"]})
        else:
            warn.append({"field": "TagType", "warn_type": "error_type"})

        if note["Conf"] is not {}:
            self.note.Conf = note["Conf"]
        else:
            warn.append({"field": "Conf", "warn_type": "empty_prop"})

        update_prop.update({"Is_Open": note["Is_Open"]})

        if not warn == []:
            ErrorRecord.add_warn_record(user=self.user,
                                        source_id=self.note.NoteId,
                                        source_label='note',
                                        content=warn)
        self.note.objects.update(update_prop)
        return self

    def handle_for_frontend(self):
        # test 测试记录一下
        note = {field.name: field for field in self.note.objects.fields}
        return note

    def handle_for_open(self):
        pass
