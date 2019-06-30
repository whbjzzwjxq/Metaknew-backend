from py2neo.data import Node
from py2neo.data import Relationship
from document.models import Document, DocumentInformation
from search.views import NeoSet, search_by_name, search_rel_exist, search_by_uuid
from subgraph import tools, translate

types = ['StrNode', 'InfNode', 'Media', 'Document']
NeoNodeKeys = ['Name', 'Name_zh', 'Name_en', 'PrimaryLabel', 'Area', 'Language', 'Alias']


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
        self.Document = {}
        self.nodes = []
        self.rels = []
        self.NeoNode = {}
        self.user = user

    def query(self, uuid):
        self.Info = self.query_info(uuid)
        self.Document = self.query_graph(uuid)
        self.nodes = self.Document['IncludedNodes']
        self.rels = self.Document['IncludedRels']
        self.NeoNode = NeoNode(uuid).root

    def create(self, data):
        assert 'info' in data
        assert 'nodes' in data
        assert 'rels' in data
        info = data['info']
        uuid = tools.get_uuid(info['title'], 'Document', 0)
        self.Info = DocumentInformation(uuid=uuid)
        self.Document = Document(uuid=uuid)
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
        return DocumentInformation.objects.get(pk=uuid)

    @staticmethod
    def query_graph(uuid):
        return Document.objects.get(pk=uuid)

    @history
    def add_node(self, uuid, conf):
        self.nodes.append({'uuid': uuid, 'conf': conf})

    @history
    def remove_node(self, uuid):
        self.nodes = tools.delete_by_uuid(self.nodes, uuid, 'uuid')
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
        self.rels = tools.delete_by_uuid(self.rels, uuid, 'source', 'target')

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


class NeoNode(object):

    def __init__(self, collector=NeoSet()):
        self.root = Node()
        self.info = tools.init('None')()
        self.origin = ''
        self.collector = collector

    def query(self, uuid):
        self.root = self.collector.Nmatcher.match(uuid=uuid).first()
        self.origin = uuid
        if self.root:
            self.info = tools.init(self.root['PrimaryLabel']).objects.get(pk=uuid)
            return True
        else:
            return False

    def create(self, user, node):
        # 这里的type是指的节点的类型， 定义在types中的
        assert 'type' in node
        assert 'Name' in node
        assert 'PrimaryLabel' in node
        # 初始化
        self.origin = node['uuid']
        node['uuid'] = tools.get_uuid(node['Name'], node['PrimaryLabel'], 0)
        self.info = tools.init([node['PrimaryLabel']])()
        self.root = Node(node['type'])
        node.pop("type")

        # Neo4j主标签主键设定
        self.root.__primarylabel__ = node['PrimaryLabel']
        self.root.__primarykey__ = "uuid"
        self.root.__primaryvalue__ = node['uuid']

        # 处理Label类信息
        self.root.add_label('Common')
        self.root.add_label('Used')
        self.update_labels(node)

        # 翻译名字
        if 'Language' not in node:
            node['Language'] = 'auto'
        self.language_setter('zh', node['Language'])
        self.language_setter('en', node['Language'])

        # 设置属性
        self.update_prop(user=user, node=node)

        # 启动Neo4j连接
        self.collector.tx.create(self.root)
        self.save()
        # 返回一个uuid-NeoNode的字典对象
        return {self.origin: self.root}

    def language_setter(self, language_to, language_from):
        name_tran = 'Name_{}'.format(language_to)
        if name_tran not in self.root:
            self.root[name_tran] = translate.translate(self.root['Name'], language_to, language_from)

    def update_labels(self, node):
        if "Labels" in node:
            self.root.update_labels(node['Labels'])
            node.pop("Labels")

    def update_prop(self, user, node):
        node.pop("Labels")
        # history记录器还是看一下怎么分类比较合适
        uuid = node['uuid']
        # 存入postgreSQL固定属性
        for key, value in tools.get_dict(self.info).items():
            if key in node:
                history_kv(user, uuid, 'postgre', key, value, node[key])
                setattr(self.info, key, node[key])
                if key != 'uuid':
                    node.pop(key)
        # 存入不定的Neo4j属性
        if self.root:
            dict1 = dict(self.root)
            self.root.update(node)
            history_dict(user, uuid, 'neo4j', dict1, dict(self.root))

    def delete(self):
        if 'Used' in self.root:
            self.root.remove_label('Used')
            self.root.add_label('Deleted')

    # 这里的node1指另一个NeoNode
    def merge(self, node1):
        pass

    def save(self):
        self.collector.tx.push(self.root)
        self.info.save()
