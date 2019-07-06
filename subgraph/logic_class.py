from py2neo.data import Node, Relationship, walk
from django.core.exceptions import ObjectDoesNotExist
from tools import base_tools, translate
from subgraph.models import Node as NodeCtrl
types = ['StrNode', 'InfNode', 'Media', 'Document']
NeoNodeKeys = ['Name', 'Name_zh', 'Name_en', 'PrimaryLabel', 'Area', 'Language', 'Alias', 'Description']


# input item类的实例
# output dict

class BaseNode(object):

    def __init__(self, collector=base_tools.NeoSet()):
        self.root = Node()
        self.uuid = ''
        self.info = NodeCtrl()

        self.collector = collector

    def query(self, uuid):
        self.root = self.collector.Nmatcher.match(uuid=uuid).first()
        self.uuid = uuid
        if self.root:
            try:
                self.info = base_tools.init(self.root['PrimaryLabel']).objects.get(pk=uuid)
                return self
            except ObjectDoesNotExist:
                return None
        else:
            return None

    def create(self, user, node):
        # 这里的type是指的节点的类型， 定义在types中的
        assert 'type' in node
        assert 'Name' in node
        assert 'PrimaryLabel' in node
        # 初始化
        self.root = Node(node['type'])
        self.uuid = base_tools.get_uuid(name=node['Name'],
                                        label=node['PrimaryLabel'],
                                        device=0)

        self.info = base_tools.init(node['PrimaryLabel'])()
        self.info.uuid = self.uuid
        # Neo4j主标签主键设定
        self.root.update({
            "uuid": self.uuid,
            "Name": node["Name"]
        })
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
        return self

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
        temp.pop('type')
        temp.pop('PrimaryLabel')
        # 存入postgreSQL固定属性
        for key, value in base_tools.get_dict(self.info).items():
            if key in temp:
                setattr(self.info, key, temp[key])
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

    def handle_for_front(self):
        pass


class BaseLink(object):
    def __init__(self, collector=base_tools.NeoSet()):
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
            return self
        else:
            return None

    def create(self, link, user):
        # source 和 target 是Node对象
        self.start = link["source"]
        self.end = link["target"]
        link.update({'uuid': base_tools.rel_uuid()})
        self.root = Relationship(self.start, link['type'], self.end)
        link.pop('type')
        link.pop('source')
        link.pop('target')
        self.root.update(link)
        self.root.update({'user': user})
        self.collector.tx.create(self.root)
        self.save()

    def save(self):
        self.collector.tx.push(self.root)
