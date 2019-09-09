from py2neo.data import Node, Relationship, walk
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from tools import base_tools
from django.db.models import Max, QuerySet
from record.logic_class import EWRecord, field_check
from record.models import NodeVersionRecord, WarnRecord
from subgraph.models import NodeCtrl, NodeInfo, Translate, MediaNode
from es_module.logic_class import es
from datetime import datetime
from tools.id_generator import id_generator, device_id
from tools.redis_process import set_location_queue
from record.logic_class import error_check, IdGenerationError, ObjectAlreadyExist
from users.logic_class import BaseUser
from users.models import MediaAuthority
from typing import List
import os
import mimetypes
from tools.base_tools import basePath
from tools.redis_process import mime_type_query, mime_type_set

types = ["StrNode", "InfNode", "Media", "Document", "Fragment"]
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
        "MainPic": "123456",
        "IncludedMedia": ["123456", "345678", "324561"],
        "DateOfBirth": "1900-01-01",
        "DateOfDeath": "2000-01-01",
        "BirthPlace": "Beijing, China",
        "Nation": "China",
        "Chronology": [
            {"Start": "1901-02-09",
             "End": "1915-04-06",
             "Content": "Live in YangZhou"
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
        "ExtraProps": {
            "Livein": "New York"
        },
    },
    "Lack": [],  # 缺少的属性
    "LoadingHistory": {
        "VersionId": "",
        "Content": ""
    }
}


# todo 各种权限表生成与实现 level: 0  bulk_create level: 0
class CommonNode:

    def __init__(self, user: BaseUser, _id: int, collector=base_tools.NeoSet()):

        # 以下是模型
        self.node = Node()
        self.info = NodeInfo()
        self.ctrl = NodeCtrl()
        self.trans = Translate()
        self.loading_history = NodeVersionRecord()
        self.history = NodeVersionRecord.objects.none()
        self.user_model = user
        self.warn = WarnRecord()  # 警告信息

        # 以下是值
        self.collector = collector  # neo4j连接池
        self._id = _id  # _id
        self.label = ""  # 标签
        self.user_id = user.user_id  # 操作用户
        self.is_draft = False  # 是否是草稿
        self.is_create = False  # 是否是创建状态
        self.lack = []  # element in lack : "record" | "trans" | "node"

    # ----------------- query ----------------

    def query_base(self):
        """
        查询info和ctrl的内容
        :return:
        """
        try:
            self.ctrl = NodeCtrl.objects.get(pk=self._id)
            self.label = self.ctrl.PrimaryLabel
            self.info = base_tools.node_init(self.label).objects.get(pk=self._id)
            return self
        except ObjectDoesNotExist:
            return None

    def query_all(self):
        """
        查询所有内容 包括Neo4j节点 翻译 历史文件
        :return:
        """
        success = self.query_base()
        if success:
            self.__query_node()
            self.__query_translate()
            self.__query_history()
        return self

    def query_with_label(self, label):
        """
        带有主标签的查询
        :param label:
        :return:
        """
        self.ctrl = NodeCtrl.objects.filter(PrimaryLabel=label)
        try:
            self.ctrl = self.ctrl.objects.get(pk=self._id)
            self.label = self.ctrl.PrimaryLabel
            self.info = base_tools.node_init(self.label).objects.get(pk=self._id)
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
        assert "type" in node
        assert "Name" in node
        assert "PrimaryLabel" in node
        self.label = node["PrimaryLabel"]
        self.__history_create(node=node)  # done 09-05
        self.__translation_create()  # done 09-05

        self.__ctrl_create(node=node)  # done 09-05
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
        self.info.NodeId = self._id
        self.info.PrimaryLabel = self.label
        # 初始化
        self.info_update(node)
        self.translation_setter(node)
        self.main_pic_setter(node["MainPic"])
        return self

    # 设置控制信息 done
    def __ctrl_create(self, node):
        if self.user_id == 0:
            is_user_made = False,
            contributor = []
        else:
            is_user_made = True
            contributor = [{"user_id": self.user_id, "level": 10}]
        self.ctrl = NodeCtrl(
            NodeId=self._id,
            Type=node["type"],
            CountCacheTime=datetime.now().replace(microsecond=0),
            Is_UserMade=is_user_made,
            CreateUser=self.user_id,
            PrimaryLabel=self.label,
            Contributor=contributor
        )

    def __history_create(self, node):
        if self.is_create:
            version_id = 1
        else:
            self.__query_history()
            version_id = self.history.aggregate(Max("VersionId"))
            version_id += 1
        self.loading_history = NodeVersionRecord(VersionId=version_id,
                                                 SourceId=self._id,
                                                 SourceType=self.label,
                                                 CreateUser=self.user_id,
                                                 Name=node["Name"],
                                                 Content=node,
                                                 Is_Draft=self.is_draft
                                                 )

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
            if not self.is_draft:
                setattr(field.model, field.name, new_prop)

    def info_update(self, node):
        # todo 把 地理识别的内容 改写为LocationField level: 3
        needed_props = base_tools.get_user_props(self.label)
        for field in needed_props:
            old_prop = getattr(self.info, field.name)
            if field.name in node:
                new_prop = getattr(node, field.name)
            else:
                new_prop = type(old_prop)()
            self.__update_prop(field, new_prop, old_prop)
            if field.name == "Location":
                set_location_queue([new_prop])
        return self

    def user_privilege(self):
        self.user_model.query_privilege()
        self.user_model.query_repository()
        if self.label == 'Document':
            self.user_model.create_doc(self._id)
        else:
            self.user_model.create_source(self._id)

    def node_status(self):
        pass

    # todo 媒体相关field 改为 MediaField level: 3
    def main_pic_setter(self, media):
        try:
            record = MediaNode.objects.get(pk=media)
            if record.MediaType == "image":
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
            EWRecord.add_warn_record(user=self.user_id,
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

    def output_table_create(self):
        return self.ctrl, self.info, self.warn, self.loading_history


# todo Link 重构 level: 0
class BaseLink(object):
    def __init__(self, link_type, collector=base_tools.NeoSet(), user=0):
        self._id = 0
        self.r_type = link_type
        if user == 0:
            self.user_id = device_id
            self.is_user_made = False
        else:
            self.user_id = user
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
            self.__update_prop(self.link_info.objects.CreateUser, self.user_id, 0)
            self.__update_prop(self.link_info.objects.Confidence, confidence, 50)


class BaseMediaNode:

    def __init__(self, _id: int, user_id: int, collector=base_tools.NeoSet()):
        self._id = _id
        self.user_id = user_id
        self.user_model: [BaseUser, None] = None
        self.collector = collector
        self.media = MediaNode()
        self.node = Node()
        self.authority = MediaAuthority()
        self.media_type = "unknown"

    def create(self, data):
        self.media_type = self.get_media_type(data["format"])
        self.media = MediaNode(MediaId=self._id,
                               MediaType=self.media_type,
                               FileName=data["name"],
                               Format=data["format"],
                               UploadUser=self.user_id,
                               Description=data["description"]
                               )
        self.node = Node("Media", self.media_type)
        self.node.update({"_id": self._id, "Name": data["name"]})
        self.user_model = BaseUser(_id=self.user_id).query_user()
        if self.user_model:
            self.user_model.query_privilege()
            self.user_model.query_repository()
            self.user_model.privilege.Is_Owner.append(self._id)
            self.user_model.repository.UploadFile.append(self._id)
            self.authority = MediaAuthority(
                SourceId=self._id,
                Used=True,
                Common=data["Common"],
                OpenSource=False,
                Shared=data["Shared"],
                Payment=data["Payment"]
            )
            self.save()
            return self
        else:
            return None

    def save(self):
        self.media.save()
        self.user_model.save()
        self.authority.save()
        self.collector.tx.create(self.node)
        self.collector.tx.commit()

    @staticmethod
    def get_media_type(file_format) -> str:
        mime_type_dict = mime_type_query()
        if mime_type_dict == {}:
            mime_type_dict = mimetypes.read_mime_types(basePath + "/tools/mime.types")
            mime_type_set(mime_type_dict)

        if "." + file_format in mime_type_dict:
            media_type = str(mime_type_dict["." + file_format])
            return media_type
        else:
            return "unknown"

    def query(self):
        try:
            self.media = MediaNode.objects.get(pk=self._id)
            self.media_type = self.media.MediaType
            return self
        except ObjectDoesNotExist:
            return None
