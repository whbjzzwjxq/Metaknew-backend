from document.models import Comment, Note
from py2neo.data import Node, Relationship, walk
from document.models import DocGraph, DocInfo
from search.views import NeoSet
from tools import base_tools, translate
from subgraph.logic_class import BaseNode

types = ['StrNode', 'InfNode', 'Media', 'Document']
NeoNodeKeys = ['Name', 'Name_zh', 'Name_en', 'PrimaryLabel', 'Area', 'Language', 'Alias', 'Description']


# input item类的实例
# output dict


def from_redis(function):
    pass


def history(user):
    pass


def history_kv(user, uuid, part, key, value1, value2):
    pass


def history_dict(user, uuid, part, dict1, dict2):
    pass


class BaseDoc(object):

    def __init__(self):
        self.Info = DocInfo
        self.Graph = DocGraph
        self.nodes = []
        self.links = []
        self.NeoNode = {}

        self.origin = ''

    def query(self, uuid):
        self.origin = uuid
        self.NeoNode = BaseNode().query(uuid=uuid)
        self.Info = self.NeoNode.info
        self.Graph = self.query_graph(uuid)

        self.nodes = [node['uuid'] for node in self.nodes]
        self.links = [link['uuid'] for link in self.links]

        return self

    def create(self, data):
        assert 'info' in data
        assert 'nodes' in data
        assert 'links' in data
        info = data['info']
        uuid = base_tools.get_uuid(info['title'], 'Document', 0)
        self.Info = DocInfo(uuid=uuid)
        self.Graph = DocGraph(uuid=uuid)

    def update_info(self, uuid, data):
        self.query_info(uuid=uuid)

    def update_graph(self):
        pass

    def reference(self):
        pass

    @staticmethod
    def privilege(user, uuid):
        pass

    @staticmethod
    def query_info(uuid):
        return DocInfo.objects.get(pk=uuid)

    @staticmethod
    def query_graph(uuid):
        return DocGraph.objects.get(pk=uuid)

    def query_cache_doc(self):
        cache_doc = {
            'uuid': self.origin,
            'title': self.Info.Title,
            'area': self.Info.Area,
            'main_pic': self.Info.MainPic,
            'imp': self.Info.Imp,
            'hard_level': self.Info.HardLevel,
            'size': self.Info.Size
        }
        return cache_doc

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
        pass

    def save_image(self):
        pass

    def upload_media(self, urls):
        self.Info.IncludedMedia.append(urls)
        
    @from_redis
    def save_cache(self):
        pass

    @from_redis
    def query_cache(self):
        pass

    @from_redis
    def clear_cache(self):
        pass


class PersonalDoc:

    def __init__(self, uuid, user):
        self.user = user
        self.uuid = uuid
        self.comments = []
        self.notes = []

    def query_all(self):
        self.query_comment()
        self.query_note()
        return self

    def query_comment(self):
        self.comments = Comment.objects.filter(BaseTarget=self.uuid,
                                               Is_Delete=False)
        return self.comments

    def query_note(self):
        self.notes = Note.objects.filter(CreateUser=self.user,
                                         DocumentId=self.uuid)
        return self.notes


class BaseComment:

    def __init__(self):
        self.comment = Comment()

    def query(self, uuid):
        comment = Comment.objects.get(id=uuid)
        if not comment.Is_Delete:
            self.comment = comment
        return self

    def add(self, base, target, user, content, time):
        self.comment = Comment(BaseTarget=base,
                               Target=target,
                               UserId=user,
                               Content=content,
                               Time=time)
        self.comment.save()

    def delete(self):
        self.comment.Is_Delete = True
        self.comment.save()
