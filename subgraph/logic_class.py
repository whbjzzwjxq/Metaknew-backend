import json
import mimetypes
import oss2
from datetime import datetime, timezone
from typing import Optional, Dict, List, Type

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Max
from py2neo.data import Node, Relationship, walk

from record.logic_class import error_check, ObjectAlreadyExist, field_check
from record.models import NodeVersionRecord, WarnRecord
from subgraph.models import NodeCtrl, NodeInfo, MediaNode, Fragment
from tools import base_tools
from tools.aliyun import authorityKeys
from tools.redis_process import mime_type_query, mime_type_set
from users.models import MediaAuthority, NodeAuthority

# 创建的时候使用的是Info
create_node_format = {
    "Name": "Test",
    "PrimaryLabel": "Person",
    "Language": "en",  # 默认auto
    "Alias": [],  # 默认[]
    "Labels": [],  # 默认[]
    "Text": "this is a test node",
    "Topic": [],
    "MainPic": "123456",
    "IncludedMedia": ["123456", "345678", "324561"],
    "DateOfBirth": "1900-01-01",
    "DateOfDeath": "2000-01-01",
    "BirthPlace": "Beijing, China",
    "Nation": "China",
    "Translate": {
        "Name_zh": "测试",
        "Name_en": "Test",
        "Name_es": ""
    },
    "ExtraProps": {
        "LiveIn": "New York"
    },
    "$_IsCommon": True,
    "$_UserName": True,
    "$_IsShare": True,
}


def neo4j_create_node(
        _type: str, labels: List[str], plabel: str,
        props: Dict, collector: base_tools.NeoSet(),
        is_user_made=True, is_common=True) -> Node:
    """

    :param _type: Node | Media | Document | Fragment
    :param labels: 标签组
    :param plabel: 主标签
    :param props: 属性 ，一定要包含"_id"
    :param is_user_made: 是否是用户创建的
    :param is_common: 是否是公开的
    :param collector: 连接池
    :return: None | Node
    """
    assert "_id" in props
    node_labels = ["Used"]
    node_labels.extend(labels)
    node_labels.append(_type)
    node_labels.append(plabel),
    if is_user_made:
        node_labels.append("UserMade")
    if is_common:
        node_labels.append("Common")
    node = Node(*node_labels, **props)
    node.__primarylabel__ = plabel
    node.__primarykey__ = "_id"
    node.__primaryvalue__ = props["_id"]
    collector.tx.create(node)
    return node


def check_is_user_made(user_id):
    if user_id != 3:
        return True
    else:
        return False


class BaseFragment:
    # todo 重构Node level: 2
    label = "Fragment"

    def __init__(self, _id: int, user_id: int, collector):
        self.id = _id
        self.user_id = user_id
        self.labels = []
        self.collector = collector
        self.node = Node()
        self.info = Fragment()

    def create(self, data):
        self.info = Fragment(NodeId=self.id,
                             CreateUser=self.user_id)
        self.info_update(data)
        self.node = neo4j_create_node(_type="Fragment",
                                      labels=data["Labels"],
                                      props={"_id": self.id},
                                      plabel="Fragment",
                                      is_common=False,
                                      collector=self.collector)
        return self

    def info_update(self, node):
        needed_props = base_tools.get_update_props(self.label)
        for field in needed_props:
            old_prop = getattr(self.info, field.name)
            if field.name in node:
                new_prop = getattr(node, field.name)
            else:
                new_prop = type(old_prop)()
            self.__update_prop(field, new_prop, old_prop)
        return self

    @staticmethod
    def __update_prop(field, new_prop, old_prop):
        if new_prop != old_prop:
            setattr(field.model, field.name, new_prop)


class BaseNode:

    def __init__(self, _id: int, user_id: int, collector=base_tools.NeoSet()):

        # 以下是模型
        self.node: Optional[Node] = None
        self.info: Optional[Type[NodeInfo]] = None
        self.ctrl: Optional[NodeCtrl] = None
        self.loading_history: Optional[NodeVersionRecord] = None
        self.authority: Optional[NodeAuthority] = None
        self.warn: Optional[WarnRecord] = None

        self.history = NodeVersionRecord.objects.none()

        # 以下是值
        self.collector = collector  # neo4j连接池
        self.id = _id  # _id
        self.user_id = int(user_id)
        self.label = ""  # 主标签
        self.is_draft = False  # 是否是草稿
        self.is_create = False  # 是否是创建状态
        self.is_user_made = check_is_user_made(user_id)
        self.lack = []  # element in lack : "record" | "trans" | "node"

    # ----------------- query ----------------

    def query_base(self):
        """
        查询info,ctrl,text, authority的内容 也就是前端 索引的基本内容
        :return:
        """
        result = self.query_ctrl()
        result &= self.query_info()

        return result

    def query_all(self):
        """
        查询所有内容 包括Neo4j节点 翻译 历史文件
        :return:
        """
        success = self.query_base()
        if success:
            self.query_node()
            self.query_history()
        return self

    def query_with_label(self, label):
        """
        带有主标签的查询
        :param label:
        :return:
        """
        self.ctrl = NodeCtrl.objects.filter(PrimaryLabel=label)
        try:
            self.ctrl = self.ctrl.objects.get(pk=self.id)
            self.label = self.ctrl.PrimaryLabel
            self.info = base_tools.node_init(self.label).objects.get(pk=self.id)
            return self
        except ObjectDoesNotExist:
            return None

    def query_ctrl(self) -> bool:
        if not self.ctrl:
            try:
                self.ctrl = NodeCtrl.objects.get(NodeId=self.id)
                self.label = self.ctrl.PrimaryLabel
                return True
            except ObjectDoesNotExist:
                return False
        else:
            self.label = self.ctrl.PrimaryLabel
            return True

    def query_info(self) -> bool:
        if not self.ctrl:
            return False
        elif not self.info:
            try:
                self.info = base_tools.node_init(self.label).objects.get(NodeId=self.id)
                return True
            except ObjectDoesNotExist:
                return False
        else:
            return True

    def query_history(self):
        self.history = NodeVersionRecord.objects.filter(SourceId=self.id)
        if len(self.history) == 0:
            self.lack.append("history")

    def query_node(self):
        self.node = self.collector.Nmatcher.match(_id=self.id).first()
        if not self.node:
            self.lack.append("node")

    def query_authority(self) -> bool:
        if not self.authority:
            try:
                self.authority = NodeAuthority.objects.get(SourceId=self.id)
                return True
            except ObjectDoesNotExist:
                self.lack.append("authority")
                return False
        else:
            return True

    # ---------------- create ----------------
    # @error_check
    def create(self, data):
        self.is_draft = False
        self.is_create = True
        assert "Name" in data
        assert "PrimaryLabel" in data
        self.label = data["PrimaryLabel"]
        self.warn = WarnRecord(
            SourceId=self.id,
            SourceLabel=self.label,
            BugType="None",
            CreateUser=self.user_id
        )

        self.__history_create(data=data)  # done 09-05

        self.__ctrl_create(data=data)  # done 09-10
        self.__info_create(data=data)  # done 09-10
        self.name_checker()  # done 09-13
        self.__auth_create(data=data)  # done 09-10
        props = {"_id": self.id, "Name": data["Name"], "Imp": data["BaseImp"], "HardLevel": data["BaseHardLevel"]}
        self.node = neo4j_create_node(_type="Node", labels=data["Labels"] + data["Topic"], plabel=self.label,
                                      props=props,
                                      is_user_made=self.is_user_made, is_common=data["$_IsCommon"],
                                      collector=self.collector)
        self.collector.tx.create(self.node)
        # es索引记录 todo 异步 level :2
        return self

    @error_check
    def update_as_stable(self, data):
        self.is_draft = False

    @error_check
    def update_as_draft(self, data):
        self.is_draft = True
        pass

    # ---------------- __private_create ----------------
    def __info_create(self, data):
        """
        info创建过程
        :param data:
        :return:
        """
        # 初始化
        self.info = base_tools.node_init(self.label)()
        self.info.NodeId = self.id
        self.info.PrimaryLabel = self.label
        self.main_pic_setter(data["MainPic"])
        self.media_setter(data["IncludedMedia"])

        # update其他数据
        self.info_update(data)
        return self

    # 设置控制信息 done
    def __ctrl_create(self, data):
        if self.is_user_made:
            contributor = {"create": "system", "update": []}
        else:
            contributor = {"create": data["$_UserName"], "update": []}
        self.ctrl = NodeCtrl(
            NodeId=self.id,
            CountCacheTime=datetime.now(tz=timezone.utc).replace(microsecond=0),
            Is_UserMade=self.is_user_made,
            CreateUser=self.user_id,
            PrimaryLabel=self.label,
            Contributor=contributor
        )

    def __history_create(self, data):
        if self.is_create:
            version_id = 1
        else:
            self.query_history()
            version_id = self.history.aggregate(Max("VersionId"))
            version_id += 1
        self.loading_history = NodeVersionRecord(VersionId=version_id,
                                                 SourceId=self.id,
                                                 SourceType=self.label,
                                                 CreateUser=self.user_id,
                                                 Name=data["Name"],
                                                 Content=data,
                                                 Is_Draft=self.is_draft
                                                 )

    def __auth_create(self, data):

        self.authority = MediaAuthority(
            SourceId=self.id,
            Used=True,
            Common=data["$_IsCommon"],
            OpenSource=False,
            Shared=data["$_IsShared"],
            Payment=False,
            Vip=False,
            HighVip=False
        )

    @field_check
    def __update_prop(self, field, new_prop, old_prop):
        if new_prop != old_prop:
            if not self.is_draft:
                setattr(self.info, field.name, new_prop)

    def info_update(self, data):
        needed_props = base_tools.get_update_props(self.label)
        for field in needed_props:
            old_prop = getattr(self.info, field.name)
            if field.name in data:
                new_prop = data[field.name]
            else:
                new_prop = type(old_prop)()
            self.__update_prop(field, new_prop, old_prop)
            # todo field resolve
        return self

    def node_status(self):
        pass

    def name_checker(self):
        similar_node = base_tools.node_init(self.label).objects.filter(Name=self.info.Name)
        if len(similar_node) > 0:
            warn = {"field": "Name",
                    "warn_type": "similar_node_id" + json.dumps([node.NodeId for node in similar_node])}
            self.warn.WarnContent.append(warn)

    # todo 媒体相关field 改为 MediaField level: 3
    def main_pic_setter(self, media):
        try:
            record = MediaNode.objects.get(pk=media)
            if record.MediaType[0:5] == "image":
                self.info.MainPic = media
            else:
                warn = {"field": "MainPic", "warn_type": "error_type"}
                self.warn.WarnContent.append(warn)
        except ObjectDoesNotExist:
            warn = {"field": "MainPic", "warn_type": "empty_prop"}
            self.warn.WarnContent.append(warn)
        return self

    def media_setter(self, media_list):
        for media_id in media_list:
            try:
                record = MediaNode.objects.get(pk=media_id)
                if record:
                    self.info.IncludedMedia.append(media_id)
            except ObjectDoesNotExist:
                pass
        return self

    def delete(self):
        # todo 节点删除 level: 2
        pass

    def merge(self, node1):
        # todo 节点merge level: 2
        pass

    def change_plabel(self):
        pass
        # todo 改变主标签 level: 2

    def save(self):
        """
        注意尽量不要使用单个Node保存
        :return:
        """
        pass

    def handle_for_frontend(self):
        """
        前端所用格式
        :return:
        """
        unused_props = ["CountCacheTime",
                        "Is_Used",
                        "ImportMethod",
                        "CreateTime",
                        "NodeId",
                        "Translate",
                        "CreateUser",
                        "BaseImp",
                        "BaseHardLevel"]
        self.query_base()
        ctrl_fields = self.ctrl._meta.get_fields()
        output_ctrl_dict = {field.name: getattr(self.ctrl, field.name)
                            for field in ctrl_fields if field.name not in unused_props}
        info_fields = self.info._meta.get_fields()
        output_info_dict = {field.name: getattr(self.info, field.name)
                            for field in info_fields if field.name not in unused_props}
        output_info_dict.update({"Translate": {}})
        # todo 重写一下翻译文件的读/取注释 level: 2
        for lang in self.info.Translate:
            output_info_dict["Translate"].update({"Name_%s" % lang: self.info.Translate[lang]})
        if self.text:
            output_info_dict.update({"Text": self.text.Text})
            for lang in self.text.Translate:
                output_info_dict["Translate"].update({"Text_%s" % lang: self.text.Translate[lang]})
        else:
            output_info_dict.update({"Text": ""})
        return {"Ctrl": output_ctrl_dict, "Info": output_info_dict}

    def output_table_create(self):
        return self.ctrl, self.info, self.warn, self.loading_history, self.authority, self.text


class BaseMediaNode:
    access_key_id = authorityKeys["developer"]["access_key_id"]
    access_key_secret = authorityKeys["developer"]["access_key_secret"]
    bucket_name = authorityKeys["developer"]["bucket_name"]
    endpoint = authorityKeys["developer"]["endpoint"]

    def __init__(self, _id: int, user_id: int, collector=base_tools.NeoSet()):
        self.id = int(_id)
        self.user_id = user_id
        self.media_type = "unknown"
        self.is_create = False

        self.collector = collector
        self.oss_manager: Optional[oss2.Bucket] = None
        self.media: Optional[MediaNode] = None
        self.node: Optional[Node] = None
        self.authority: Optional[MediaAuthority] = None

    # remake 2019-10-17
    def create(self, data: dict, remote_file: str):
        self.is_create = True
        self.media_type = data["PrimaryLabel"]
        self.media = MediaNode(
            MediaId=self.id,
            FileName=remote_file,
            Format=remote_file.split(".")[1],
            Title=data["Name"],
            Labels=data["Labels"],
            MediaType=self.media_type,
            UploadUser=self.user_id,
        )
        # 注意这里还是写了名字的 但是之后如果移动了文件位置那么还是会重新给名字的
        if data["Text"]:
            self.media.Text = data["Text"]
        else:
            self.media.Text = {"auto": ""}
        self.node = neo4j_create_node(
            _type="Media",
            labels=data["Labels"],
            plabel=self.media_type,
            props={"_id": self.id, "Title": data["Name"]},
            collector=self.collector
        )
        self.authority = MediaAuthority(
            SourceId=self.id,
            Used=True,
            Common=data["$_IsCommon"],
            OpenSource=False,
            Shared=data["$_IsShared"],
            Payment=False,
            Vip=False,
            HighVip=False
        )
        return self

    def save(self):
        self.media.save()
        self.authority.save()
        self.collector.tx.commit()

    def set_oss_manager(self):
        if not self.oss_manager:
            auth = oss2.Auth(self.access_key_id, self.access_key_secret)
            self.oss_manager = oss2.Bucket(auth, self.endpoint, bucket_name=self.bucket_name, connect_timeout=10000)
        else:
            pass

    def check_remote_file(self) -> bool:
        """
        查看远端文件
        :return: bool
        """
        self.set_oss_manager()
        return self.oss_manager.object_exists(self.media.FileName)

    def move_remote_file(self, new_location):
        """
        移动远端文件
        :param new_location:
        :return:
        """
        if self.check_remote_file():
            return self.oss_manager.copy_object(self.bucket_name, self.media.FileName, new_location)
        else:
            raise FileNotFoundError

    @staticmethod
    def get_media_type(file_format) -> str:
        """
        注意返回的是完整的mime_type不是json, image之类的
        :param file_format: str such as 'jpg'
        :return: mime_type: str such as 'application/json'
        """
        mime_type_dict = mime_type_query()
        if mime_type_dict == {}:
            mime_type_dict = mimetypes.read_mime_types(base_tools.basePath + "/tools/mime.types")
            mime_type_set(mime_type_dict)

        if "." + file_format in mime_type_dict:
            media_type = str(mime_type_dict["." + file_format])
            return media_type
        else:
            return "unknown"

    def query_media(self):
        if not self.media:
            try:
                self.media = MediaNode.objects.get(pk=self.id)
                self.media_type = self.media.MediaType
                return True
            except ObjectDoesNotExist:
                return False
        else:
            return True

    @staticmethod
    def query_as_main_pic(self):
        pass


# todo Link 重构 level: 0
class BaseLink:
    def __init__(self, obj_id: int, _id: int, link_type: str, collector=base_tools.NeoSet()):
        """

        :param obj_id:用户/设备id
        :param _id: link id
        :param link_type: link type 是更加深化的type
        :param collector: Neo4j连接池
        """
        self._id = _id
        self.r_type = link_type
        self.obj_id = obj_id

        self.link_info = base_tools.link_init(link_type)
        self.collector = collector
        self.link: Optional[Relationship] = None
        self.walk: Optional[walk] = None
        self.start: Optional[Node] = None
        self.end: Optional[Node] = None

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

    def base_create(self, start, end, is_user_made):
        """
        收集基础信息
        :param start: 起点
        :param end:  终点
        :param is_user_made: 是否是用户生成
        :return:
        """
        self.link = Relationship(start, self.r_type, end)
        neo4j_prop = {"Is_UserMade": is_user_made, "CreateTime": datetime.now().strftime('%a, %b %d %H:%M')}
        self.link.update(neo4j_prop)
        self.link_info.LinkId = self._id
        self.link_info.Start = start["_id"]
        self.link_info.End = end["_id"]
        self.link_info.Is_UserMade = is_user_made
        self.link_info.CreatorId = self.obj_id
        self.link_info.Type = self.r_type


class SystemMade(BaseLink):

    def create(self, start, end, data):
        # 注意start end就已经是Node()而不是_id了
        result = self.query_single_by_start_end(start, end)
        if result:
            raise ObjectAlreadyExist
        else:
            self.base_create(start, end, False)
            self.update_props(data)
            self.do_walk()
            self.collector.tx.push(self.link)
        return self

    def update_props(self, data):
        props = base_tools.get_system_link_props(self.r_type)
        for prop in props:
            if prop.name in data:
                value = data[prop.name]
                self.link_info.objects.update({prop.name: value})
            else:
                pass


class KnowLedge(BaseLink):

    def create(self, start, end, data):
        result = self.query_single_by_start_end(start, end)
        if result:
            self.update_props(data)
        else:
            self.link = Relationship(start, self.r_type, end)
            self.base_create(start, end, data["Is_UserMade"])
            self.update_props(data)
            if "Confidence" not in data:
                confidence = 50 + int(data["Is_UserMade"]) * 50
                self.update_confidence(confidence)
        self.do_walk()
        self.collector.tx.push(self.link)
        return self

    def update_props(self, data):
        props = base_tools.get_system_link_props(self.r_type)
        for prop in props:
            if prop.name in data:
                value = data[prop.name]
                self.link_info.objects.update({prop.name: value})
            else:
                pass

    def update_confidence(self, value):
        self.link_info.Confidence = value
        self.link.update({"Confidence": value})
