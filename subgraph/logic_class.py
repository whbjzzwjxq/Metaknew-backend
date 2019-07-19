from py2neo.data import Node, Relationship, walk
from django.core.exceptions import ObjectDoesNotExist
from tools import base_tools, translate
from tools.base_tools import get_label_special_attr as get_special
from subgraph.models import Node as NodeInfo
from es_module.logic_class import es
from copy import deepcopy
import asyncio

types = ['StrNode', 'InfNode', 'Media', 'Document']
NeoNodeKeys = ['Name', 'Name_zh', 'Name_en', 'PrimaryLabel', 'Area', 'Language', 'Alias', 'Description']


# input item类的实例
# output dict

class BaseNode(object):

    def __init__(self, collector=base_tools.NeoSet()):
        self.root = Node()
        self.origin = ''
        self.info = NodeInfo()
        self.collector = collector
        self.label = ''
        self.already = False

    def query(self, uuid):
        self.root = self.collector.Nmatcher.match(uuid=uuid).first()
        self.origin = uuid
        if self.root:
            try:
                self.label = self.root['PrimaryLabel']
                self.info = base_tools.init(self.root['PrimaryLabel']).objects.get(pk=uuid)
                self.already = True
                return self
            except ObjectDoesNotExist:
                return None
        else:
            return None

    def create(self, node):
        # 这里的type是指的节点的类型， 定义在types中的
        assert 'type' in node
        assert 'Name' in node
        assert 'PrimaryLabel' in node
        assert 'Area' in node
        if 'Language' not in node:
            node['Language'] = 'auto'
        self.already = True
        # 初始化
        self.root = Node(node['type'])
        self.origin = base_tools.get_uuid(name=node['Name'],
                                          label=node['PrimaryLabel'],
                                          device=0)
        self.label = node['PrimaryLabel']

        self.info = base_tools.init(self.label)()

        # Neo4j主标签主键设定
        self.root.update({
            "uuid": self.origin,
            "Name": node["Name"],
            "PrimaryLabel": self.label,
            "Language": node["Language"]
        })
        self.root.add_label(self.label)
        self.root.add_label(node['Area'])
        self.root.__primarylabel__ = self.label
        self.root.__primarykey__ = "uuid"
        self.root.__primaryvalue__ = self.origin

        # 处理Label类信息
        self.update_labels(node)

        # 翻译名字 todo 异步
        self.language_setter('zh', node['Language'])
        self.language_setter('en', node['Language'])

        # 设置属性
        self.update_prop(node=node)

        # 启动Neo4j连接
        self.collector.tx.create(self.root)
        self.save()
        if 'Description' not in node:
            node['Description'] = ''
        if 'Alias' not in node:
            node['Alias'] = []

        # es索引记录 异步
        if not self.label == 'Document':
            asyncio.run(add_node_index(self))
        # 返回self对象
        return self

    def language_setter(self, language_to, language_from):
        name_tran = 'Name_{}'.format(language_to)
        if name_tran not in self.root:
            if not language_to == language_from:
                self.root[name_tran] = translate.translate(self.root['Name'], language_to, language_from)
            else:
                self.root[name_tran] = self.root['Name']

    def update_labels(self, node):
        assert self.already
        if "Labels" in node:
            self.root.update_labels(node['Labels'])

    def update_prop(self, node):
        assert self.already
        temp = deepcopy(node)
        temp = base_tools.dict_dryer(temp)
        # 存入class Node下的非默认数据以及标签代表的特殊属性
        self.info.uuid = self.origin
        key_list = get_special(self.label)
        for key in key_list:
            if key in temp:
                setattr(self.info, key, temp[key])
                temp.pop(key)

        # 存入不定的Neo4j属性
        if self.root:
            self.root.update(temp)

    def update_all(self, node):
        assert self.already
        self.update_labels(node=node)
        self.update_prop(node=node)

    def delete(self):
        assert self.already
        pass

    # 这里的node1指另一个NeoNode
    def merge(self, node1):
        assert self.already
        # todo
        pass

    # 这里Neo4j还没有commit
    def save(self):
        assert self.already
        self.collector.tx.push(self.root)
        self.info.save()

    def handle_for_frontend(self):
        assert self.already
        labels = list(self.root.labels)
        props = dict(self.root)

        for key in get_special(self.label):
            props.update({key: self.info.__getattribute__(key)})
        props['uuid'] = str(props['uuid'])
        # todo 更加详细的前端数据格式
        return {"Labels": labels, "Props": props}


class BaseLink(object):
    def __init__(self, collector=base_tools.NeoSet()):
        self.origin = ''
        self.start = {}
        self.end = {}
        self.walk = {}
        self.root = {}
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

    def create(self, link):
        # source 和 target 是Node对象
        self.start = link["source"]
        self.end = link["target"]
        link.update({'uuid': base_tools.rel_uuid()})
        self.root = Relationship(self.start, link['type'], self.end)
        link.pop('type')
        link.pop('source')
        link.pop('target')
        self.root.update(link)
        self.collector.tx.create(self.root)
        self.save()
        return self

    def save(self):
        self.collector.tx.push(self.root)


# todo 消息队列处理
async def add_node_index(node: BaseNode()):
    assert node.already
    root = node.root
    info = node.info
    target = "content.%s" % root["Language"]
    body = {
        "alias": info["Alias"],
        target: info["Description"],
        "labels": list(root.labels),
        "language": root["Language"],
        "name": {'auto': root["name"],
                 'zh': root["name_zh"],
                 'en': root["name_en"]},
        "p_label": root["PrimaryLabel"],
        "uuid": root["uuid"]
    }
    result = es.index(index='nodes', body=body, doc_type='_doc')
    if result['_shards']['successful'] == 1:
        return True
    else:
        # todo record
        return False


async def add_doc_index(doc):
    assert doc.already
    root = doc.NeoNode
    info = doc.Info
    target = "content.%s" % root["Language"]
    updatetime = info.UpdateTime.date()
    body = {
        "area": info.Area,
        target: info.Description,
        "hard_level": info.HardLevel,
        "hot": info.Hot,
        "imp": info.Imp,
        "keyword": info.Keywords,
        "labels": list(root.labels),
        "language": root["Language"],
        "size": info.Size,
        "title": {'auto': root["name"],
                  'zh': root["name_zh"],
                  'en': root["name_en"]},
        "updatetime": updatetime,
        "useful": info.Useful,
        "uuid": root["uuid"]
    }
    result = es.index(index='documents', body=body, doc_type='_doc')
    if result['_shards']['successful'] == 1:
        return True
    else:
        # todo record
        return False
