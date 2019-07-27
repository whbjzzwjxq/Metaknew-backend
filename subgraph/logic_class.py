from py2neo.data import Node, Relationship, walk
from django.core.exceptions import ObjectDoesNotExist
from tools import base_tools
from record.logic_class import EWRecord, field_check
from record.models import VersionRecord
from subgraph.models import NodeCtrl, Translate, MediaNode, NodeInfo
from es_module.logic_class import es
from datetime import datetime
from tools.id_generator import id_generator, device_id
from copy import deepcopy
from tools.redis_process import set_location_queue
from record.logic_class import error_check, IdGenerationError

types = ['StrNode', 'InfNode', 'Media', 'Document']
node_format = {
    "conf": {},  # 这是在专题里实现的
    "ctrl": {},  # 控制类信息 不修改
    "info": {
        "_id": "111",
        "type": "StrNode", 
        "Name": "Test",
        "PrimaryLabel": "Person",
        "Language": "en",  # 默认auto
        "Alias": [],  # 默认[]
        "Labels": [],  # 默认[]
        "Description": "this is a test node",
        "Area": [],
        "ExtraProps": {
            "Livein": "New York"
        },
        "MainPic": "123456",
        "IncludedMedia": ["123456", "345678", "324561"],
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
    "loading_history": {

    },
    "translate": {
        "name_auto": "Test",
        "name_zh": "测试",
        "name_en": "Test",
        "names": {},
        "des_auto": "this is a test node",
        "des_zh": "这是测试节点",
        "des_en": "this is a test node",
        "description": {}
    },
    "status": {
        "lack": []
    }
}


# todo 各种权限表生成与实现 level: 0  bulk_create level: 0
class BaseNode(object):

    def __init__(self, user, _id, collector=base_tools.NeoSet()):
        self.node = Node()
        self.info = NodeInfo()
        self.ctrl = NodeCtrl()
        self.trans = Translate()

        # history的id和node不一致
        self.loading_history = VersionRecord("0")
        self.new_history = VersionRecord()

        self.collector = collector  # neo4j连接池
        self._id = _id  # _id
        self.label = ''  # 标签
        self.user = user  # 操作用户
        self.is_draft = False  # 是否是草稿
        self.current_trans = {}  # 目前的翻译文件内容

        self.needed_props = []  # 该种PrimaryLabel必须的标签
        self.lack = []  # element in lack : 'record' | 'trans' | 'node'
        self.warn = []  # 警告信息

    # ----------------- query ----------------
    # 只查询基础信息: info 和 ctrl
    def query_base(self):
        try:
            self.ctrl = NodeCtrl.objects.get(pk=self._id)
            self.label = self.ctrl.PrimaryLabel
            self.info = base_tools.init(self.label).objects.get(pk=self._id)
            self.needed_props = base_tools.get_user_props(self.label)
            return self
        except ObjectDoesNotExist:
            return None

    # 查询完整信息
    def query_all(self):
        success = self.query_base()
        if success:
            self.__query_node()
            self.__query_translate()
            self.__query_history()
        return self

    # 通过标签查询
    def query_with_label(self, label):
        self.ctrl = NodeCtrl.objects.filter(PrimaryLabel=label)
        try:
            self.ctrl = self.ctrl.objects.get(pk=self._id)
            self.label = self.ctrl.PrimaryLabel
            self.info = base_tools.init(self.label).objects.get(pk=self._id)
            self.needed_props = base_tools.get_user_props(self.label)
            return self
        except ObjectDoesNotExist:
            return None

    # 查询历史 / 翻译 / 节点 todo 查询超时设置 level: 2
    def __query_translate(self):
        try:
            self.trans = Translate.objects.get(FileId=self._id)
        except ObjectDoesNotExist:
            self.lack.append('trans')

    def __query_history(self):
        try:
            self.history = VersionRecord.objects.filter(SourceId=self._id)
        except ObjectDoesNotExist:
            self.lack.append('record')

    def __query_node(self):
        try:
            self.node = self.collector.Nmatcher.match(_id=self._id).first()
        except ObjectDoesNotExist:
            self.lack.append('node')

    # ---------------- create ----------------
    @error_check
    def create(self, node):
        # 注意这里id是从生成器取的！！
        if '_id' not in node:
            raise IdGenerationError
        else:
            assert 'type' in node
            assert 'Name' in node
            assert 'PrimaryLabel' in node
            self._id = node['_id']
            self.label = node['PrimaryLabel']
            self.needed_props = base_tools.get_user_props(self.label)
            self.loading_history = self.__history_create(node=node)
            self.__translation_create()
            self.__ctrl_create(node=node)
            self.__info_create(node=node)
            self.__neo4j_create(node=node)

            # es索引记录 todo 异步 level :2
            # 返回self对象
            return self

    @error_check
    def update_as_stable(self, node):
        self.is_draft = False

    @error_check
    def update_as_draft(self, node):
        self.is_draft = True

    def __info_create(self, node):
        self.info = base_tools.init(self.label)()
        self.is_draft = False
        # 基础信息 专有修改接口
        self.info.NodeId = self._id
        self.info.PrimaryLabel = self.label
        # 初始化
        self.update_props(node)
        self.translation_setter(node)
        self.main_pic_setter(node["MainPic"])
        return self

    # 设置控制信息 done
    def __ctrl_create(self, node):
        if self.user == 0:
            user = False,
            contributor = []
        else:
            user = True
            contributor = [{"user_id": self.user, "level": 10}]
        self.ctrl = NodeCtrl(
            NodeId=self._id,
            History=self.history.RecordId,
            CountCacheTime=datetime.now(),
            Is_UserMade=user,  # 注意这里后台导入时user == 0
            CreateUser=node["user"],
            PrimaryLabel=self.label,
            Contributor=contributor
        )

    def __history_create(self, node):
        version_id = id_generator(1, method='device', content=device_id, jump=3)
        new_history = VersionRecord(RecordId=version_id,
                                    SourceId=self._id,
                                    SourceType=self.label,
                                    CreateUser=self.user,
                                    Name=node["Name"],
                                    FrontRecord=self.loading_history.RecordId,
                                    Content={},
                                    Is_Draft=self.is_draft
                                    )
        return new_history

    def __translation_create(self):
        self.trans = Translate(FileId=self._id)

    # Neo4j创建 done
    def __neo4j_create(self, node):
        self.node = Node(node['type'])
        self.node.update({
            "_id": self._id,
            "Name": node["Name"]["auto"]
        })
        self.node.__primarylabel__ = node['PrimaryLabel']
        self.node.__primarykey__ = "_id"
        self.node.__primaryvalue__ = self._id
        self.collector.tx.create(self.node)
        self.__neo4j_update_label()

    def __neo4j_update_label(self):
        labels = [self.info.PrimaryLabel]
        labels.extend(self.info.Area)
        labels.extend(self.info.Labels)
        self.node.update_labels(labels)
        self.collector.tx.push(self.node)

    def translation_setter(self, node):
        trans_list = [field for field in self.trans._meta.get_fields()]
        for field in trans_list:
            new_prop = getattr(node["translate"], field.name)
            old_prop = getattr(self.trans, field.name)
            self.update_prop(field, new_prop, old_prop)
        return self

    @field_check
    def update_prop(self, field, new_prop, old_prop):
        if new_prop != old_prop:
            if self.is_draft:
                self.new_history.Content.update({field.model + '-' + field.name: new_prop})
            else:
                self.loading_history.Content.update({field.model + '-' + field.name: old_prop})
                setattr(field.model, field.name, new_prop)

    def update_props(self, node):
        # todo 把 地理识别的内容 改写为LocationField level: 3
        # todo 把 需要翻译的内容 改写为NameField level: 3
        for key in self.needed_props:
            if key not in node:
                warn = {"field": key, "warn_type": "lack_prop"}
                self.warn.append(warn)
            else:
                current_prop = getattr(self.info, key)
                new_prop = node[key]
                # test 默认值问题 level: 0
                if not type(current_prop) == type(new_prop):
                    warn = {"field": key, "warn_type": "error_type"}
                    self.warn.append(warn)
                else:
                    if type(new_prop).__name__ == 'str' and len(new_prop) >= 512:
                        warn = {"field": key, "warn_type": "toolong_str"}
                        self.warn.append(warn)
                        # 记录warn
                    elif type(new_prop).__name__ == 'list' and len(new_prop) >= 128:
                        warn = {"field": key, "warn_type": "toolong_list"}
                        self.warn.append(warn)
                        # 记录warn
                    else:
                        if key == 'Location':
                            set_location_queue([node[key]])
                        setattr(self.info, key, node[key])
        return self

    # todo 媒体相关field 改为 MediaField level: 3
    def main_pic_setter(self, media):
        try:
            record = MediaNode.objects.get(pk=media)
            if record.MediaType == 'picture':
                self.info.MainPic = media
        except ObjectDoesNotExist:
            warn = {'field': 'MainPic', 'warn_type': "error_type"}
            self.warn.append(warn)
        return self

    def delete(self):
        # todo 节点删除 level: 2
        pass

    # 这里的node1指另一个node
    def merge(self, node1):
        # todo 节点merge level: 2
        pass

    def change_plabel(self):
        pass
        # todo 改变主标签 level: 2

    # 注意尽量不要使用单个Node保存
    def save(self):
        if not self.warn == []:
            EWRecord.add_warn_record(user=self.user,
                                     source_id=self._id,
                                     source_label=self.label,
                                     content=self.warn)
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


# todo Link 重构 level: 0
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
