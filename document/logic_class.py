from document.models import Comment, Note
from document.models import DocGraph, DocInfo
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
class BaseDoc:

    def __init__(self):
        self.Info = DocInfo()
        self.Graph = DocGraph()
        self.nodes = []
        self.links = []
        self.NeoNode = BaseNode()
        self.comments = []
        self.already = False
        self.origin = ''

    def query(self, uuid):
        key = "cache_doc_" + self.origin[-17:]
        cache_doc = cache.get(key)
        self.origin = uuid
        if not cache_doc:
            self.NeoNode = BaseNode().query(_id=uuid)
            self.Graph = self.query_graph(uuid)
            self.save_cache()
        else:
            self.NeoNode = cache_doc["NeoNode"]
            self.Graph = cache_doc["Graph"]
            timeout = cache.ttl(key) + login_token.hour
            cache.expire(key, timeout=timeout)

        self.Info = self.NeoNode.info
        self.nodes = [node['uuid'] for node in self.nodes]
        self.links = [link['uuid'] for link in self.links]
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

    def query_info(self, uuid):
        self.origin = uuid
        try:
            self.Info = DocInfo.objects.get(uuid=uuid)
            return self
        except ObjectDoesNotExist:
            return self

    def query_graph(self, uuid):
        self.origin = uuid
        try:
            self.Graph = DocGraph.objects.get(pk=uuid)
            return self
        except ObjectDoesNotExist:
            return self

    def query_abbr_doc(self, uuid):
        self.query_info(uuid)
        key = "abbr_" + self.origin[-17:]
        abbr_doc = cache.get(key)
        if abbr_doc:
            cache.expire(key, timeout=login_token.week)
            return abbr_doc
        else:
            abbr_doc = {
                'uuid': self.origin,
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

    def add_node(self, uuid, conf):
        self.nodes.append({'uuid': uuid, 'conf': conf})

    def remove_node(self, uuid):
        if uuid in self.nodes:
            index = self.nodes.index(uuid)
            self.Graph.IncludedNodes.pop(index)

        self.remove_main_node(uuid=uuid)
        self.remove_rel(node=uuid, link_uuid=None)

    def update_node(self, uuid, conf):
        if uuid in self.nodes:
            index = self.nodes.index(uuid)
            self.Graph.IncludedNodes[index]['conf'] = conf

    def set_main_node(self, uuid):
        self.Graph.MainNodes.append(uuid)

    def remove_main_node(self, uuid):
        self.Graph.MainNodes.remove(uuid)

    def add_rel(self, uuid, source, target, conf):
        self.Graph.IncludedLinks.append({'uuid': uuid,
                                         'source': source,
                                         'target': target,
                                         'conf': conf})

    def remove_rel(self, link_uuid: None, node: None):
        if link_uuid is not None:
            if link_uuid in self.links:
                index = self.links.index(link_uuid)
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

    def update_rel(self, uuid, conf):

        if uuid in self.links:
            index = self.links.index(uuid)
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
        # todo hot_count

    def get_default_image(self):
        pass

    def upload_media(self, uuid_list):
        self.Info.IncludedMedia.extend(uuid_list)

    def update_media_by_uuid(self, uuid, include_media):
        self.Info = DocInfo.objects.filter(uuid=uuid).update(IncludedMedia=include_media)
        return self

    def remove_media(self, uuid_list):
        for uuid in uuid_list:
            if uuid in self.Info.IncludedMedia:
                self.Info.IncludedMedia.remove(uuid)

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

    def __init__(self, uuid, user):
        self.user = user
        self.uuid = uuid
        self.concern = {}
        self.notes = []

    def query_all(self):
        self.query_note()
        self.query_concern()
        return self

    def query_note(self):
        self.notes = Note.objects.filter(CreateUser=self.user,
                                         DocumentId=self.uuid)
        return self.notes

    def query_concern(self):
        self.concern = UserConcern.objects.filter(UserId=self.user,
                                                  SourceId=self.uuid)
        return self.concern


class BaseComment:

    def __init__(self):
        self.comment = Comment()

    def query(self, uuid):
        comment = Comment.objects.get(uuid=uuid)
        if not comment.Is_Delete:
            self.comment = comment
        return self

    def add(self, base, target, user, content, update_time):
        content = str(content)
        uuid = base_tools.get_uuid(name=content[0]+'comment',
                                   label='Comment',
                                   device=0)
        self.comment = Comment(uuid=uuid,
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

    def query(self, uuid):
        try:
            self.note = Note.objects.get(uuid=uuid)
            return self
        except ObjectDoesNotExist:
            return None

    def add(self, user, note_type, content, doc_uuid):
        content = str(content)
        uuid = base_tools.get_uuid(name=content[0]+'comment',
                                   label='Note',
                                   device=0)
        self.note = Note(uuid=uuid,
                         CreateUser=user,
                         TagType=note_type,
                         Content=content,
                         DocumentId=doc_uuid)
        self.note.save()

    def delete(self):
        self.note.delete()

    def update_content(self, new_content, new_type):
        self.note.Content = str(new_content)
        if new_type in self.tag_type:
            self.note.TagType = new_type
        self.note.save()


class BasePath(BaseDoc):

    def query_graph(self, uuid):
        self.origin = uuid
        try:
            self.Graph = StudyNet.objects.get(pk=uuid)
            return self
        except ObjectDoesNotExist:
            return self

    def set_prop_node(self):
        pass

