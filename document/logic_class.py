from document.models import Comment, Note
from document.models import DocGraph, _Doc
from django.core.exceptions import ObjectDoesNotExist
from tools import base_tools, login_token
from subgraph.logic_class import BaseNode
from django.core.cache import cache
from time import time
import datetime
from users.models import UserConcern
from django.db.models import Avg
types = ['StrNode', 'InfNode', 'Media', 'Document']
NeoNodeKeys = ['Name', 'Name_zh', 'Name_en', 'PrimaryLabel', 'Area', 'Language', 'Alias', 'Description']


# todo doc重新定义 level: 0

front_end_doc = {
    
}


class BaseDoc:

    def __init__(self):
        self.Info = _Doc()
        self.Graph = DocGraph()
        self.nodes = []
        self.links = []
        self.comments = []
        self.already = False
        self.origin = ''

    def query(self, doc_id):
        key = "cache_doc_" + self.origin[-17:]
        cache_doc = cache.get(key)
        self.origin = doc_id
        if not cache_doc:
            self.NeoNode = BaseNode().query(_id=doc_id)
            self.Graph = self.query_graph(doc_id)
            self.save_cache()
        else:
            self.NeoNode = cache_doc["NeoNode"]
            self.Graph = cache_doc["Graph"]
            timeout = cache.ttl(key) + login_token.hour
            cache.expire(key, timeout=timeout)

        self.Info = self.NeoNode.info
        self.nodes = [node['doc_id'] for node in self.nodes]
        self.links = [link['doc_id'] for link in self.links]
        self.already = True
        return self

    def create(self, data):
        pass

    def update_info(self, data):
        self.Info.Title = data['title']
        self.Info.MainPic = data['main_pic']
        self.Info.Area = data['area']
        self.Info.Description = data['description']

    def update_graph(self):
        pass

    def reference(self):
        pass

    def query_info(self, doc_id):
        self.origin = doc_id
        try:
            self.Info = DocInfo.objects.get(doc_id=doc_id)
            return self
        except ObjectDoesNotExist:
            return self

    def query_graph(self, doc_id):
        self.origin = doc_id
        try:
            self.Graph = DocGraph.objects.get(pk=doc_id)
            return self
        except ObjectDoesNotExist:
            return self

    def query_abbr_doc(self, doc_id):
        self.query_info(doc_id)
        key = "abbr_" + self.origin[-17:]
        abbr_doc = cache.get(key)
        if abbr_doc:
            cache.expire(key, timeout=login_token.week)
            return abbr_doc
        else:
            abbr_doc = {
                'doc_id': self.origin,
                'title': self.Info.Title,
                'area': self.Info.Area,
                'main_pic': self.Info.MainPic,
                'imp': self.Info.Imp,
                'hard_level': self.Info.HardLevel,
                'size': self.Info.Size
            }
            cache.add(key, abbr_doc, timeout=login_token.week)
            return abbr_doc

    def query_comment(self):
        self.comments = Comment.objects.filter(BaseTarget=self.origin,
                                               Is_Delete=False)
        return self.comments

    def add_node(self, doc_id, conf):
        self.nodes.append({'doc_id': doc_id, 'conf': conf})

    def remove_node(self, doc_id):
        if doc_id in self.nodes:
            index = self.nodes.index(doc_id)
            self.Graph.IncludedNodes.pop(index)

        self.remove_main_node(doc_id=doc_id)
        self.remove_rel(node=doc_id, link_doc_id=None)

    def update_node(self, doc_id, conf):
        if doc_id in self.nodes:
            index = self.nodes.index(doc_id)
            self.Graph.IncludedNodes[index]['conf'] = conf

    def set_main_node(self, doc_id):
        self.Graph.MainNodes.append(doc_id)

    def remove_main_node(self, doc_id):
        self.Graph.MainNodes.remove(doc_id)

    def add_rel(self, doc_id, source, target, conf):
        self.Graph.IncludedLinks.append({'doc_id': doc_id,
                                         'source': source,
                                         'target': target,
                                         'conf': conf})

    def remove_rel(self, link_doc_id: None, node: None):
        if link_doc_id is not None:
            if link_doc_id in self.links:
                index = self.links.index(link_doc_id)
                self.Graph.IncludedLinks.pop(index)
        elif node is not None:
            source = [link['source'] for link in self.Graph.IncludedLinks]
            target = [link['target'] for link in self.Graph.IncludedLinks]
            while node in source:
                index = source.index(node)
                self.Graph.IncludedLinks.pop(index)
            while node in target:
                index = target.index(node)
                self.Graph.IncludedLinks.pop(index)

    def update_rel(self, doc_id, conf):

        if doc_id in self.links:
            index = self.links.index(doc_id)
            self.Graph.IncludedLinks[index]['conf'] = conf

    def save(self):
        if time() - self.Info.CountCacheTime.timestamp() > login_token.week:
            self.re_count()
            self.Info.CountCacheTime = datetime.datetime.now()
        self.Info.UpdateTime = datetime.datetime.now()
        self.Info.save()
        self.Graph.save()

    def re_count(self):
        self.Info.Size = self.Graph.IncludedNodes.count()
        result = UserConcern.objects.filter(SourceId=self.origin)
        self.Info.Useful = result.filter(Useful__gte=0).aggregate(Avg('Useful'))
        self.Info.HardLevel = result.filter(HardLevel__gte=0).aggregate(Avg('HardLevel'))
        self.Info.Imp = result.filter(Imp__gte=0).aggregate(Avg('Imp'))
        self.Info.CountCacheTime = time()
        # todo hot_count level : 1

    def get_default_image(self):
        pass

    def upload_media(self, doc_id_list):
        self.Info.IncludedMedia.extend(doc_id_list)

    def update_media_by_doc_id(self, doc_id, include_media):
        self.Info = DocInfo.objects.filter(doc_id=doc_id).update(IncludedMedia=include_media)
        return self

    def remove_media(self, doc_id_list):
        for doc_id in doc_id_list:
            if doc_id in self.Info.IncludedMedia:
                self.Info.IncludedMedia.remove(doc_id)

    def save_cache(self):
        key = "cache_doc_" + self.origin[-17:]
        cache_doc = {
            "NeoNode": self.NeoNode,
            "Graph": self.Graph
        }
        cache.add(key, cache_doc, timeout=login_token.hour * 2)

    def clear_cache(self):
        key = "cache_doc_" + self.origin[-17:]
        cache.expire(key, timeout=1)


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
        self.comment = Comment()

    def query(self, doc_id):
        comment = Comment.objects.filter(doc_id=doc_id)
        if not comment.Is_Delete:
            self.comment = comment
        return self

    def add(self, base, target, user, content, update_time):
        content = str(content)

        self.comment = Comment(doc_id=doc_id,
                               BaseTarget=base,
                               Target=target,
                               UserId=user,
                               Content=content,
                               Time=update_time)
        self.comment.save()

    def delete(self):
        self.comment.Is_Delete = True
        self.comment.save()


class BaseNote:

    tag_type = [
        "normal",
        "dark",
        "circle"
    ]

    def __init__(self):
        self.note = Note()

    def query(self, _id):
        try:
            self.note = Note.objects.get(id=_id)
            return self
        except ObjectDoesNotExist:
            return None

    def add(self, user, note_type, content, doc_doc_id):
        content = str(content)
        doc_id = base_tools.get_doc_id(name=content[0]+'comment',
                                   label='Note',
                                   device=0)
        self.note = Note(doc_id=doc_id,
                         CreateUser=user,
                         TagType=note_type,
                         Content=content,
                         DocumentId=doc_doc_id)
        self.note.save()

    def delete(self):
        self.note.delete()

    def update_content(self, new_content, new_type):
        self.note.Content = str(new_content)
        if new_type in self.tag_type:
            self.note.TagType = new_type
        self.note.save()

