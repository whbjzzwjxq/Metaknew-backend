from py2neo.data import Node, Relationship, walk
from django.core.exceptions import ObjectDoesNotExist
from tools import base_tools, translate
from history.logic_class import AddRecord
from history.models import VersionRecord
from subgraph.models import NodeCtrl, Translate
from es_module.logic_class import es
from datetime import datetime
import asyncio
import json

types = ['StrNode', 'InfNode', 'Media', 'Document']
node_format = {
    "conf": {},  # 这是在专题里实现的
    "ctrl": {},  # 控制类信息 不修改
    "info": {
        "_id": "111",
        "type": "StrNode",
        "user": "0",
        "Name": {
            "auto": "Test",
            "zh": "测试"
        },
        "PrimaryLabel": "Person",
        "Language": "en",  # 默认auto
        "Alias": [],  # 默认[]
        "Labels": [],  # 默认[]
        "Description": {
            "auto": "this is a test node",
            "zh": "这是测试节点"
        },
        "Area": [],
        "ExtraProps": {
            "Livein": "New York"
        },
        "DateOfBirth": "1900-01-01",
        "DateOfDeath": "2000-01-01",
        "BirthPlace": "Beijing, China",
        "Nation": "China",
        "Chronology": [
            {"start": "1901-02-09",
             "end": "1915-04-06",
             "content": "Live in YangZhou"
             }
        ]
    },
}


class BaseNode(object):

    def __init__(self, user, collector=base_tools.NeoSet()):
        self.node = None
        self.info = None
        self.ctrl = None
        self.trans = None
        self.history = None

        self.collector = collector
        self._id = ''
        self.label = ''
        self.needed_props = []
        self.lack = []  # element in lack : 'history' | 'trans' | 'node'
        self.user = user

    # 只查询基础信息: info 和 ctrl
    def query_base(self, _id):
        try:
            self.ctrl = NodeCtrl.objects.get(pk=_id)
            self._id = _id
            self.label = self.ctrl.PrimaryLabel
            self.info = base_tools.init(self.label).objects.get(pk=_id)
            self.needed_props = base_tools.get_user_props(self.label)
            return self
        except ObjectDoesNotExist:
            return None
            
    # 查询完整信息
    def query_all(self, _id):
        success = self.query_base(_id)
        if success:      
            self.__query_node()
            self.__query_translate()
            self.__query_history()
        return self

    # 查询翻译文件
    def __query_translate(self):
        try:
            self.trans = Translate.objects.get(FileId=self._id)
        except ObjectDoesNotExist:
            self.lack.append('trans')
            
    # 查询历史 / 翻译 / 节点 todo 查询超时设置 level: 2  
    def __query_history(self):
        try:
            self.history = VersionRecord.objects.get(SourceId=self._id)
        except ObjectDoesNotExist:
            self.lack.append('history')
            
    def __query_node(self):
        try:
            self.node = self.collector.Nmatcher.match(_id=self._id).first()
        except ObjectDoesNotExist:
            self.lack.append('node')
            
    @base_tools.error_check
    def create(self, node):
        # 注意这里id是从生成器取的！！
        if '_id' not in node:
            raise base_tools.IdGenerationError
        else:
            assert 'type' in node
            assert 'Name' in node
            assert 'PrimaryLabel' in node
            self._id = node['_id']
            self.label = node['PrimaryLabel']
            self.needed_props = base_tools.get_user_props(self.label)

            self.__neo4j_create(node=node)
            self.__ctrl_create(node=node)
            self.__info_create(node=node)

            # 翻译名字 todo 异步 level :2
            self.__language_setter(self, node, node['Language'])
            # 处理Label类信息
            self.update_all(node=node)

            # es索引记录 todo 异步 level :2
            if not self.label == 'Document':
                asyncio.run(add_node_index(self))
            # 返回self对象
            return self

    def __info_create(self, node):
        self.info = base_tools.init(self.label)
        
     
    # 设置控制信息 done
    def __ctrl_create(self, node):
        if self.user == 0:
            user = False,
            contributor = []
        else:
            user = True
            contributor = [{"user_id":self.user, "level": 10}]
        self.ctrl = NodeCtrl(
            NodeId=self._id,
            History=self._id,
            CountCacheTime=datetime.now(),
            Is_UserMade=user,  # 注意这里后台导入时user == 0
            CreateUser=node["user"],
            PrimaryLabel=self.label,
            Contributor=contributor
        )

    # Neo4j创建 done
    def __neo4j_create(self, node):
        self.node = Node(node['type'])
        self.node.update({
            "_id": self._id,
            "Name": node["Name"]["auto"]
        })
        self.node.add_label(node['PrimaryLabel'])
        self.node.add_label(node['Area'])
        self.node.add_label(node['Labels'])
        self.node.__primarylabel__ = node['PrimaryLabel']
        self.node.__primarykey__ = "_id"
        self.node.__primaryvalue__ = self._id
        self.collector.tx.create(self.node)

    def __language_setter(self, node, language_to, language_from):
        name_tran = 'Name_{}'.format(language_to)
        if name_tran not in node:
            if not language_to == language_from:
                setattr(self.info, name_tran, translate.translate(node['Name'], language_to, language_from))
            else:
                setattr(self.info, name_tran, node['Name'])

    def update_labels(self, labels):
        pass

    def update_all(self, node):
        pass

    def update_props(self, node):
        key_list = self.needed_props
        lack = False
        for key in key_list:
            if key in node:
                if isinstance(node[key], list):
                    setattr(self.info, key, node[key])
            else:
                lack = True
        # 记录warn数据
        if lack:
            pass

    def delete(self):
        assert self.already
        pass

    # 这里的node1指另一个node
    def merge(self, node1):
        assert self.already
        # todo level: 3
        pass

    # 注意尽量不要使用单个保存
    def save(self):
        assert self.already
        self.collector.tx.push(self.node)
        self.collector.tx.commit()
        self.info.save()
        self.ctrl.save()

    def handle_for_frontend(self):
        pass
        # assert self.already
        # labels = list(self.root.labels)
        # props = dict(self.root)
        #
        # for key in get_special(self.label):
        #     props.update({key: self.info.__getattribute__(key)})
        # props['uuid'] = str(props['uuid'])
        # todo 更加详细的前端数据格式 level : 0
        # return {"Labels": labels, "Props": props}


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


# todo 消息队列处理 level :3
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
        # todo record 记录索引失败 level: 2
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
