from py2neo.data import Node, Relationship, walk
from django.core.exceptions import ObjectDoesNotExist
from tools import base_tools, translate
from history.logic_class import AddRecord
from tools.base_tools import get_props_for_user_ctrl as get_props
from subgraph.models import Node as NodeInfo
from es_module.logic_class import es
from copy import deepcopy
import asyncio

import json
from datetime import datetime

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
        self.keys = []
        self.already = False

    def query(self, _id):
        self.root = self.collector.Nmatcher.match(id=_id).first()
        self.origin = _id
        if self.root:
            try:
                self.label = self.info.PrimaryLabel
                self.info = base_tools.init(self.root['PrimaryLabel']).objects.get(pk=_id)
                self.keys = get_props(self.label)
                self.already = True
                return self
            except ObjectDoesNotExist:
                return None
        else:
            return None

    def create(self, node):
        assert 'type' in node
        assert 'Name' in node
        assert 'PrimaryLabel' in node
        assert 'Area' in node
        assert 'id' in node

        if 'Labels' not in node:
            node['Labels'] = []
        if 'Description' not in node:
            node['Description'] = ''
        if 'Alias' not in node:
            node['Alias'] = []
        if 'Language' not in node:
            node['Language'] = 'auto'

        self.already = True
        # 初始化
        self.__neo4j_create(node=node)
        self.origin = node['id']
        self.label = node['PrimaryLabel']
        self.info = base_tools.init(self.label)()
        self.keys = get_props(self.label)
        self.info.id = self.origin
        self.info.ImportMethod = node['ImportMethod']
        self.info.CreateUser = node['CreateUser']
        # 翻译名字 todo 异步 level :2
        self.__language_setter(node, 'zh', node['Language'])
        self.__language_setter(node, 'en', node['Language'])
        # 处理Label类信息
        self.update_all(node=node)

        # es索引记录 todo 异步 level :2
        if not self.label == 'Document':
            asyncio.run(add_node_index(self))
        # 返回self对象
        return self

    # Neo4j主标签主键设定
    def __neo4j_create(self, node):
        assert 'type' in node
        assert 'id' in node
        assert 'PrimaryLabel' in node
        self.root = Node(node['type'])
        self.root.update({
            "id": node['id'],
            "Name": node["Name"]
        })
        self.root.add_label(node['PrimaryLabel'])
        self.root.add_label(node['Area'])
        self.root.__primarylabel__ = node['PrimaryLabel']
        self.root.__primarykey__ = "id"
        self.root.__primaryvalue__ = node['id']
        self.collector.tx.create(self.root)

    def __language_setter(self, node, language_to, language_from):
        name_tran = 'Name_{}'.format(language_to)
        if name_tran not in node:
            if not language_to == language_from:
                setattr(self.info, name_tran, translate.translate(node['Name'], language_to, language_from))
            else:
                setattr(self.info, name_tran, node['Name'])

    def update_labels(self, node):
        assert self.already
        if "Labels" in node:
            self.root.update_labels(node['Labels'])
            self.info.Labels = node["Labels"]

    def update_props(self, node):
        assert self.already
        temp = deepcopy(node)
        temp = base_tools.dict_dryer(temp)
        # 存入class Node下的非默认数据以及标签代表的特殊属性
        key_list = self.keys
        null_group = []
        print(key_list)
        for key in key_list:
            if key in temp and temp[key]:
                setattr(self.info, key, temp[key])
                temp.pop(key)
            else:
                null_group.append(key)
        print(temp)
        self.info.ExtraProps = temp

        # 记录warn数据
        if null_group is not []:
            AddRecord.add_record(error=False,
                                 warn=True,
                                 source_id=self.origin,
                                 source_type=self.label,
                                 content={"lack_props": null_group})

    def update_all(self, node):
        assert self.already
        self.update_labels(node=node)
        self.update_props(node=node)

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
        self.collector.tx.commit()
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


# 增加多个节点
def add_nodes(self, nodes):
    for node in nodes:
        try:
            b = BaseNode()
            b.create(node)
        except(Exception):
            a = AddRecord()
            content = {'name': node['name'],
                       'error_type': 'CreateFailed',
                       'time': datetime.now()}
            a.add_record(True, False, '', node['PrimaryLabel'], json.dumps(content))
