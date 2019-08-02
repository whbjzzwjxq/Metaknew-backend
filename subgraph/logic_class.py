from py2neo.data import Node, Relationship, walk
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from tools import base_tools
from django.db.models import Max
from record.logic_class import EWRecord, field_check
from record.models import NodeVersionRecord, WarnRecord
from subgraph.models import NodeCtrl, NodeInfo, Translate, MediaNode
from subgraph.models import SearchTogether, AfterVisit, MentionTogether, Doc2Node, Topic2Node, Topic2Topic
from es_module.logic_class import es
from datetime import datetime
from tools.id_generator import id_generator, device_id
from tools.redis_process import set_location_queue
from record.logic_class import error_check, IdGenerationError, ObjectAlreadyExist

types = ["StrNode", "InfNode", "Media", "Document"]
# 前端使用的格式
node_format = {
    "Conf": {},  # 这是在专题里实现的
    "Ctrl": {},  # 控制类信息 不修改
    "Info": {
        "_id": "111",
        "Type": "StrNode",
        "Name": "Test",
        "PrimaryLabel": "Person",
        "Language": "en",  # 默认auto
        "Alias": [],  # 默认[]
        "Labels": [],  # 默认[]
        "Description": "this is a test node",
        "Topic": [],
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
        ],
        "Translate": {
            "Name_auto": "Test",
            "Name_zh": "测试",
            "Name_en": "Test",
            "Names": {},
            "Des_auto": "this is a test node",
            "Des_zh": "这是测试节点",
            "Des_en": "this is a test node",
            "Description": {}
        },
    },
    "Lack": [],  # 缺少的属性
    "EditedProp": [],  # 在前端编辑过的属性
    "LoadingHistory": {
        "RecordId": "",
        "Content": ""
    }
}


# todo 各种权限表生成与实现 level: 0  bulk_create level: 0
class BaseNode:

    def __init__(self, user, _id, collector=base_tools.NeoSet()):
        self.node = Node()
        self.info = NodeInfo()
        self.ctrl = NodeCtrl()
        self.trans = Translate()

        # 注意history的id和node不一致
        # 当前加载的历史文件 稳定版的历史固定为空
        self.loading_history = NodeVersionRecord()

        # 新建的历史文件
        self.new_history = NodeVersionRecord()
        self.needed_props = []  # 该种PrimaryLabel必须的标签

        self.collector = collector  # neo4j连接池
        self._id = _id  # _id
        self.label = ""  # 标签
        self.user = user  # 操作用户
        self.is_draft = False  # 是否是草稿
        self.is_create = False  # 是否是创建状态

        self.edited_props = []  # 发生过编辑的属性
        self.lack = []  # element in lack : "record" | "trans" | "node"
        self.warn = WarnRecord()  # 警告信息

    # ----------------- query ----------------
    # 只查询基础信息: info 和 ctrl
    def query_base(self):
        try:
            self.ctrl = NodeCtrl.objects.get(pk=self._id)
            self.label = self.ctrl.PrimaryLabel
            self.info = base_tools.node_init(self.label).objects.get(pk=self._id)
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
            self.info = base_tools.node_init(self.label).objects.get(pk=self._id)
            self.needed_props = base_tools.get_user_props(self.label)
            return self
        except ObjectDoesNotExist:
            return None

    # 查询历史 / 翻译 / 节点 todo 查询超时设置 level: 2
    def __query_translate(self):
        try:
            self.trans = Translate.objects.get(FileId=self._id)
        except ObjectDoesNotExist:
            self.lack.append("trans")

    def __query_history(self):
        self.history = NodeVersionRecord.objects.filter(SourceId=self._id)
        if len(self.history) == 0:
            self.lack.append("record")

    def __query_node(self):
        try:
            self.node = self.collector.Nmatcher.match(_id=self._id).first()
        except ObjectDoesNotExist:
            self.lack.append("node")

    # ---------------- create ----------------
    @error_check
    def create(self, node):
        self.is_draft = False
        self.is_create = True
        # 注意这里id是从生成器取的！！
        if "_id" not in node:
            raise IdGenerationError
        else:
            assert "type" in node
            assert "Name" in node
            assert "PrimaryLabel" in node
            self._id = node["_id"]
            self.label = node["PrimaryLabel"]
            self.needed_props = base_tools.get_user_props(self.label)
            self.__history_create(name=node["Name"])
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
        pass

    # ---------------- __private_create ----------------
    def __info_create(self, node):
        self.info = base_tools.node_init(self.label)()
        # 基础信息 专有修改接口
        self.info.NodeId = self._id
        self.info.PrimaryLabel = self.label
        # 初始化
        self.info_update(node)
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
            CountCacheTime=datetime.now().replace(microsecond=0),
            Is_UserMade=user,  # 注意这里后台导入时user == 0
            CreateUser=node["user"],
            PrimaryLabel=self.label,
            Contributor=contributor
        )

    def __history_create(self, name):
        if self.is_create:
            version_id = 1
        else:
            self.__query_history()
            version_id = self.history.aggregate(Max("VersionId"))
            version_id += 1
        self.new_history = NodeVersionRecord(VersionId=version_id,
                                             SourceId=self._id,
                                             SourceType=self.label,
                                             CreateUser=self.user,
                                             Name=name,
                                             Content={},
                                             Is_Draft=self.is_draft
                                             )
        if self.is_draft:
            self.new_history.BaseHistory = self.loading_history.VersionId
        else:
            if self.is_create:
                self.new_history.BaseHistory = 0
            else:
                self.loading_history.BaseHistory = self.new_history.VersionId
                self.new_history.BaseHistory = 0

    def __history_save(self):

        if self.is_draft:
            self.new_history.save()
        else:
            if self.is_create:
                self.new_history.save()
            else:
                self.loading_history.save()
                self.new_history.save()

    def __translation_create(self):
        self.trans = Translate(FileId=self._id)
        return self

    # Neo4j创建 done
    def __neo4j_create(self, node):
        self.node = Node(node["type"])
        self.node.update({
            "_id": self._id,
            "Name": node["Name"],
            "Imp": node["BaseImp"],
            "HardLevel": node["BaseHardLevel"],
        })
        self.node.__primarylabel__ = node["PrimaryLabel"]
        self.node.__primarykey__ = "_id"
        self.node.__primaryvalue__ = self._id
        self.collector.tx.create(self.node)
        self.__neo4j_update()

    def __neo4j_update(self):
        labels = [self.info.PrimaryLabel]
        labels.extend(self.info.Topic)
        labels.extend(self.info.Labels)
        self.node.update_labels(labels)
        self.collector.tx.push(self.node)

    def translation_setter(self, node):
        trans_list = [field for field in self.trans._meta.get_fields()]
        for field in trans_list:
            new_prop = getattr(node["Translate"], field.name)
            old_prop = getattr(self.trans, field.name)
            self.__update_prop(field, new_prop, old_prop)
        return self

    @field_check
    def __update_prop(self, field, new_prop, old_prop):
        if new_prop != old_prop:
            if self.is_draft:
                self.new_history.Content.update({field.model + "-" + field.name: new_prop})
            else:
                self.loading_history.Content.update({field.model + "-" + field.name: old_prop})
                setattr(field.model, field.name, new_prop)

    def info_update(self, node):
        # todo 把 地理识别的内容 改写为LocationField level: 3
        for field in self.needed_props:
            old_prop = getattr(self.info, field.name)
            if field.name in node:
                new_prop = getattr(node, field.name)
            else:
                new_prop = type(old_prop)()
            self.__update_prop(field, new_prop, old_prop)
            if field.name == "Location":
                set_location_queue([new_prop])
        return self

    # todo 媒体相关field 改为 MediaField level: 3
    def main_pic_setter(self, media):
        try:
            record = MediaNode.objects.get(pk=media)
            if record.MediaType == "picture":
                self.info.MainPic = media
            else:
                warn = {"field": "MainPic", "warn_type": "error_type"}
                self.warn.WarnContent.append(warn)
        except ObjectDoesNotExist:
            warn = {"field": "MainPic", "warn_type": "empty_prop"}
            self.warn.WarnContent.append(warn)
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
        # props["uuid"] = str(props["uuid"])
        # todo 更加详细的前端数据格式 level : 0
        # return {"Labels": labels, "Props": props}


# todo Link 重构 level: 0
class BaseLink(object):
    def __init__(self, link_type, collector=base_tools.NeoSet(), user=0):
        self._id = 0
        self.r_type = link_type
        if user == 0:
            self.user = device_id
            self.is_user_made = False
        else:
            self.user = user
            self.is_user_made = True

        self.is_create = False
        self.warn = WarnRecord()
        self.link_info = base_tools.link_init(link_type)
        self.collector = collector
        self.link = Relationship()
        self.walk = walk()
        self.start = Node()
        self.end = Node()

    def query_single_by_id(self, _id):
        try:
            self.link_info = self.link_info.objects.filter(Type=self.r_type)
            self.link_info = self.link_info.objects.get(LinkId=_id)
            self._id = self.link_info.LinkId
            self.r_type = self.link_info.Type
            self.link = self.collector.Rmatcher.match(nodes=None, r_type=self.r_type, _id=self._id).first()
            self.do_walk()
            return self
        except ObjectDoesNotExist or MultipleObjectsReturned:
            return None

    # 主要是系统生成的关系使用 因为是唯一的
    def query_single_by_start_end(self, start, end):
        try:
            self.link_info = self.link_info.objects.get(Start=start["_id"], End=end["_id"], Type=self.r_type)
            self._id = self.link_info.LinkId
            self.r_type = self.link_info.Type
            self.link = self.collector.Rmatcher.match(nodes=(start, end), r_type=self.r_type, _id=self._id).first()
            self.do_walk()
            return self
        except ObjectDoesNotExist or MultipleObjectsReturned:
            return None

    def do_walk(self):
        self.walk = walk(self.link)
        self.start = self.walk.start_node
        self.end = self.walk.end_node


class SystemMade(BaseLink):

    @error_check
    def create(self, link):
        # 注意start end就已经是Node()而不是_id了
        result = self.query_single_by_start_end(link["start"], link["end"])
        if result:
            raise ObjectAlreadyExist
        else:
            assert "_id" in link
            self.link = Relationship(link["start"], self.r_type, link["end"])
            props = base_tools.get_system_link_props(self.r_type)
            for prop in props:
                value = getattr(link, prop.name)
                self.link.update({prop.name: value})
                self.link_info.objects.update({prop.name: value})
            self.do_walk()
            self.collector.tx.push(self.link)
        return self


class KnowLedge(BaseLink):

    @error_check
    def create(self, link):
        self.is_create = True
        assert "_id" in link
        result = self.query_single_by_start_end(link["start"], link["end"])
        if result:
            self.update_props(link)
        else:
            self.link = Relationship(link["start"], self.r_type, link["end"])
            self.link_info = self.link_info()
            self.update_props(link)
        self.do_walk()
        self.collector.tx.push(self.link)
        return self

    @field_check
    def __update_prop(self, field, new_prop, old_prop):
        self.link.update({field.name: new_prop})
        setattr(self.link_info, field.name, new_prop)

    def update_props(self, link):
        props = base_tools.get_system_link_props(self.r_type)
        for prop in props:
            if prop.name in link:
                new_prop = getattr(link, prop.name)
                old_prop = getattr(self.link_info, prop.name)
                self.__update_prop(prop, new_prop, old_prop)
            else:
                pass
        if self.is_create:
            confidence = 50 + int(self.is_user_made) * 50
            # test
            self.__update_prop(self.link_info.objects.Is_UserMade, self.is_user_made, False)
            self.__update_prop(self.link_info.objects.CreateUser, self.user, 0)
            self.__update_prop(self.link_info.objects.Confidence, confidence, 50)


# todo 消息队列处理 level :3
async def add_node_index(node):
    assert node.already
    root = node.root
    info = node.info
    target = "content.%s" % root["Language"]
    body = {
        "alias": info["Alias"],
        target: info["Description"],
        "labels": list(root.labels),
        "language": root["Language"],
        "name": {"auto": root["name"],
                 "zh": root["name_zh"],
                 "en": root["name_en"]},
        "p_label": root["PrimaryLabel"],
        "uuid": root["uuid"]
    }
    result = es.index(index="nodes", body=body, doc_type="_doc")
    if result["_shards"]["successful"] == 1:
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
        "Topic": info.Topic,
        target: info.Description,
        "hard_level": info.HardLevel,
        "hot": info.Hot,
        "imp": info.Imp,
        "keyword": info.Keywords,
        "labels": list(root.labels),
        "language": root["Language"],
        "size": info.Size,
        "title": {"auto": root["name"],
                  "zh": root["name_zh"],
                  "en": root["name_en"]},
        "updatetime": updatetime,
        "useful": info.Useful,
        "uuid": root["uuid"]
    }
    result = es.index(index="documents", body=body, doc_type="_doc")
    if result["_shards"]["successful"] == 1:
        return True
    else:
        return False


