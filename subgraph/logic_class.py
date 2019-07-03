from py2neo.data import Node, Relationship, walk
from document.models import DocGraph, DocInfo
from search.views import NeoSet
from tools import base_tools, translate
from subgraph.models import BaseNodeCtrl
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


class Doc(object):

    def __init__(self, user=1):
        self.Info = {}
        self.Graph = {}
        self.nodes = []
        self.rels = []
        self.NeoNode = {}
        self.user = user
        self.origin = ''

    def query(self, uuid):
        self.origin = uuid
        self.Info = self.query_info(uuid)
        self.Graph = self.query_graph(uuid)
        self.nodes = self.Graph['IncludedNodes']
        self.rels = self.Graph['IncludedRels']
        self.NeoNode = BaseNode(uuid).root

    def create(self, data):
        assert 'info' in data
        assert 'nodes' in data
        assert 'rels' in data
        info = data['info']
        uuid = base_tools.get_uuid(info['title'], 'Document', 0)
        self.Info = DocInfo(uuid=uuid)
        self.Graph = DocGraph(uuid=uuid)
        self.nodes = data['nodes']

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

    @history
    def add_node(self, uuid, conf):
        self.nodes.append({'uuid': uuid, 'conf': conf})

    @history
    def remove_node(self, uuid):
        self.nodes = base_tools.delete_by_uuid(self.nodes, uuid, 'uuid')
        self.remove_rel(uuid)

    @history
    def update_node(self, uuid, conf):
        for node in self.nodes:
            if node['uuid'] == uuid:
                node['conf'] = conf

    @history
    def add_rel(self, uuid, source, target, conf):
        self.rels.append({'uuid': uuid, 'source': source, 'target': target, 'conf': conf})

    @history
    def remove_rel(self, uuid):
        self.rels = base_tools.delete_by_uuid(self.rels, uuid, 'source', 'target')

    @history
    def update_rel(self, uuid, conf):
        for rel in self.rels:
            if rel['uuid'] == uuid:
                rel['conf'] = conf
                break

    def save(self):
        pass

    @from_redis
    def save_cache(self):
        pass

    @from_redis
    def query_cache(self):
        pass

    @from_redis
    def clear_cache(self):
        pass


class BaseNode(object):

    def __init__(self, collector=NeoSet(), user=1):
        self.root = Node()
        self.uuid = ''
        self.info = BaseNode()
        self.ctrl_info = BaseNodeCtrl()

        self.user = user
        self.collector = collector

    def query(self, uuid):
        self.root = self.collector.Nmatcher.match(uuid=uuid).first()
        self.uuid = uuid
        if self.root:
            self.info = base_tools.init(self.root['PrimaryLabel']).objects.get(pk=uuid)
            self.ctrl_info = BaseNodeCtrl.objects.get(pk=uuid)
            return True
        else:
            return False

    def create(self, node):
        # 这里的type是指的节点的类型， 定义在types中的
        assert 'type' in node
        assert 'Name' in node
        assert 'PrimaryLabel' in node
        # 初始化
        origin = node['uuid']
        self.root = Node(node['type'])
        self.uuid = base_tools.get_uuid(node['Name'], node['PrimaryLabel'], 0)
        self.info = base_tools.init(node['PrimaryLabel'])()
        self.ctrl_info = BaseNodeCtrl(uuid=self.uuid,
                                      ImportMethod='Web',
                                      CreateUser=self.user
                                      )

        # Neo4j主标签主键设定
        self.root.__primarylabel__ = node['PrimaryLabel']
        self.root.__primarykey__ = "uuid"
        self.root.__primaryvalue__ = node['uuid']

        # 处理Label类信息
        self.update_labels(node)

        # 翻译名字
        if 'Language' not in node:
            node['Language'] = 'auto'
        self.language_setter('zh', node['Language'])
        self.language_setter('en', node['Language'])

        # 设置属性
        self.update_prop(node=node)

        # 启动Neo4j连接
        self.collector.tx.create(self.root)
        self.save()
        # 返回一个uuid-NeoNode的字典对象
        return {origin: self}

    def language_setter(self, language_to, language_from):
        name_tran = 'Name_{}'.format(language_to)
        if name_tran not in self.root:
            self.root[name_tran] = translate.translate(self.root['Name'], language_to, language_from)

    def update_labels(self, node):
        if "Labels" in node:
            self.root.update_labels(node['Labels'])

    def update_prop(self, node):
        temp = node
        temp.pop('Labels')
        temp.pop('uuid')
        temp.pop('type')
        # 存入postgreSQL固定属性
        for key, value in base_tools.get_dict(self.info).items():
            if key in temp:
                setattr(self.info, key, temp[key])
                if key != 'uuid':
                    temp.pop(key)
        # 存入不定的Neo4j属性
        if self.root:
            self.root.update(temp)

    def update_all(self, node):
        self.update_labels(node=node)
        self.update_prop(node=node)

    def delete(self):
        pass

    # 这里的node1指另一个NeoNode
    def merge(self, node1):
        pass

    # 这里Neo4j还没有commit
    def save(self):
        self.collector.tx.push(self.root)
        self.info.save()
        self.ctrl_info.save()

    def handle_for_front(self):
        pass


class BaseRel(object):
    def __init__(self, collector=NeoSet()):
        self.origin = ''
        self.start = {}
        self.end = {}
        self.walk = {}
        self.root = Relationship()
        self.collector = collector

    def query(self, uuid):
        self.root = self.collector.Rmatcher.match(uuid=uuid).first()
        self.origin = uuid
        if self.root:
            self.walk = walk(self.root)
            self.start = self.walk.start_node
            self.end = self.walk.en_node
            return True
        else:
            return False

    def create(self, relationship):
        # source 和 target 是Node对象
        self.start = relationship["source"]
        self.end = relationship["target"]
        relationship.update({'uuid': base_tools.rel_uuid()})
        self.root = Relationship(self.start, relationship['type'], self.end)
        relationship.pop('type')
        relationship.pop('source')
        relationship.pop('target')
        self.root.update(relationship)
        self.collector.tx.create(self.root)
        self.save()
    
    def save(self):
        self.collector.tx.push(self.root)

