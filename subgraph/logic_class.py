from py2neo.data import Node, Relationship, walk
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from tools import base_tools
from django.db.models import Max
from record.logic_class import field_check
from record.models import NodeVersionRecord, WarnRecord
from subgraph.models import NodeCtrl, NodeInfo, MediaNode, Fragment, Text
from datetime import datetime, timezone
from tools.id_generator import device_id
from tools.redis_process import set_location_queue
from record.logic_class import error_check, ObjectAlreadyExist
from users.models import MediaAuthority, NodeAuthority
from typing import Optional, Dict, List, Type
import mimetypes
import json
import base64
from tools.redis_process import mime_type_query, mime_type_set

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


def neo4j_create_node(_type: str, labels: List[str], plabel: str, props: Dict, collector: base_tools.NeoSet(),
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
    if user_id == 2:
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
        self.text: Optional[Text] = None
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
        result &= self.query_text()

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

    def query_text(self) -> bool:
        if not self.text:
            try:
                self.text = Text.objects.get(NodeId=self.id)
                return True
            except ObjectDoesNotExist:
                self.lack.append("text")
                return False
        else:
            return True

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
        self.warn = WarnRecord(SourceId=self.id, SourceLabel=self.label, BugType="None", CreateUser=self.user_id)

        self.__history_create(data=data)  # done 09-05

        self.__ctrl_create(data=data)  # done 09-10
        self.__info_create(data=data)  # done 09-10
        self.name_checker()  # done 09-13
        self.__auth_create(data=data)  # done 09-10
        self.__text_update(data=data)  # done 09-11
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
        info创建过程 注意Translate和Text把翻译放在了两个位置存储
        :param data:
        :return:
        """
        self.info = base_tools.node_init(self.label)()
        self.info.NodeId = self.id
        self.info.PrimaryLabel = self.label
        self.info.Translate = {key[5:len(key)]: value for key, value in data["Translate"].items() if
                               key[0:5] == "Name_"}
        # 初始化
        self.info_update(data)
        self.main_pic_setter(data["MainPic"])
        self.media_setter(data["IncludedMedia"])
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

    def __text_update(self, data: dict):
        if self.authority.Common and data["Text"] != "":
            if self.is_create:
                self.text = Text(NodeId=self.id,
                                 Is_Bound=True,
                                 Language=data["Language"])
            else:
                self.query_text()

            text = {key[5:len(key)]: value for key, value in data["Translate"].items() if key[0:5] == "Text_"}
            self.text.Translate = text
            self.text.Keywords = data["Labels"]
            self.text.Text = data["Text"]
            self.text.Star = self.ctrl.Star
            self.text.Hot = self.ctrl.Hot
        else:
            self.text = None
        return self

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
        # todo 把 地理识别的内容 改写为LocationField level: 3
        needed_props = base_tools.get_update_props(self.label)
        for field in needed_props:
            old_prop = getattr(self.info, field.name)
            if field.name in data:
                new_prop = data[field.name]
            else:
                new_prop = type(old_prop)()
            self.__update_prop(field, new_prop, old_prop)
            if field.name == "Location":
                set_location_queue([new_prop])
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
        unused_props = ["CountCacheTime", "Is_Used", "ImportMethod", "CreateTime", "NodeId", "Translate", "CreateUser"]
        self.query_base()
        ctrl_fields = self.ctrl._meta.get_fields()
        output_ctrl_dict = {field.name: getattr(self.ctrl, field.name)
                            for field in ctrl_fields if field.name not in unused_props}
        info_fields = self.info._meta.get_fields()
        output_info_dict = {field.name: getattr(self.info, field.name)
                            for field in info_fields if field.name not in unused_props}
        output_info_dict.update({"Translate": {}, "_id": self.id, "type": "node"})
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

    def __init__(self, _id: int, user_id: int, collector=base_tools.NeoSet()):
        self.id = _id
        self.user_id = user_id
        self.media_type = "unknown"
        self.is_create = False
        self.collector = collector
        self.media: Optional[MediaNode] = None
        self.node: Optional[Node] = None
        self.authority: Optional[MediaAuthority] = None
        self.text: Optional[Text] = None

    def create(self, data):
        self.is_create = True
        self.media_type = self.get_media_type(data["Format"])
        self.media = MediaNode(MediaId=self.id,
                               MediaType=self.media_type,
                               FileName=data["Name"],
                               Format=data["Format"],
                               UploadUser=self.user_id,
                               )
        self.node = neo4j_create_node(_type="Media",
                                      labels=data["Labels"],
                                      plabel=self.media_type.split("/")[0],
                                      props={"_id": self.id, "Name": data["Name"]},
                                      collector=self.collector)
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
        self.__text_update(data)
        return self

    def __text_update(self, data: dict):
        if self.is_create:
            self.text = Text(NodeId=self.id,
                             Is_Bound=True,
                             Language=data["Language"])
        else:
            self.query_text()

        self.text.Translate = data["Translate"]
        self.text.Keywords = data["Labels"]
        self.text.Text = data["Text"]
        self.text.Star = self.media.Star
        self.text.Hot = self.media.Hot
        return self

    def save(self):
        self.media.save()
        self.authority.save()
        self.collector.tx.commit()

    @staticmethod
    def get_media_type(file_format) -> str:
        mime_type_dict = mime_type_query()
        if mime_type_dict == {}:
            mime_type_dict = mimetypes.read_mime_types(base_tools.basePath + "/tools/mime.types")
            mime_type_set(mime_type_dict)

        if "." + file_format in mime_type_dict:
            media_type = str(mime_type_dict["." + file_format])
            return media_type
        else:
            return "unknown"

    def query_all(self):
        result = True
        result &= self.query_media()
        result &= self.query_text()
        return result

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

    def query_text(self):
        if not self.text:
            try:
                self.text = Text.objects.get(NodeId=self.id)
                return True
            except ObjectDoesNotExist:
                self.text = None
                return False
        else:
            return True

    def query_as_main_pic(self):
        self.query_all()
        if self.media.MediaType[0:5] == "image":
            with open(base_tools.basePath + "/fileUploadCache/" + str(self.id) + "." + self.media.Format, "rb") as f:
                image = f.read()
            image = base64.b64encode(image).decode()
            return "data:%s;base64," % self.media.MediaType + image
        else:
            return ""


# todo Link 重构 level: 0
class BaseLink:
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
        result = self.query_single_by_start_end(link["Start"], link["End"])
        if result:
            raise ObjectAlreadyExist
        else:
            assert "_id" in link
            self.link = Relationship(link["Start"], self.r_type, link["End"])
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
        result = self.query_single_by_start_end(link["Start"], link["End"])
        if result:
            self.update_props(link)
        else:
            self.link = Relationship(link["Start"], self.r_type, link["End"])
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
