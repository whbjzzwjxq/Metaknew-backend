import datetime
import json
import os
import re
from datetime import date
from functools import reduce
from typing import List, Dict, Type, Union, Optional

import numpy as np
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Field, Model
from py2neo import Graph, NodeMatcher, RelationshipMatcher
from py2neo.data import Node as NeoNode

from es_module.logic_class import bulk_add_node_index, bulk_add_text_index
from record.logic_class import field_check
from record.models import WarnRecord, NodeVersionRecord
from subgraph.models import *
from subgraph.models import BaseAuthority

re_for_info = re.compile(r".*Info")
re_for_ptr = re.compile(r".*_ptr")
graph = Graph("bolt://39.96.10.154:7687", username="neo4j", password="12345678")

basePath = os.path.dirname(os.path.dirname(__file__))
_types = Union['node', 'link', 'course', 'media']
info_models = Union[Type[NodeInfo], Type[MediaInfo], Type[RelationshipInfo]]


class NeoSet:
    def __init__(self):
        self.tx = graph.begin()
        self.Nmatcher = NodeMatcher(graph)
        self.Rmatcher = RelationshipMatcher(graph)


def type_label_to_model(_type: _types, label: str) -> info_models:
    """
    可能有多张表继承的模型
    :param _type:
    :param label:
    :return:
    """
    if _type in model_dict:
        if label in model_dict[_type]:
            return model_dict[_type][label]
        else:
            return model_dict[_type]['default']
    else:
        raise TypeError('Error Type')


ctrl_dict: Dict[str, Type[Union[NodeCtrl, RelationshipCtrl, MediaCtrl]]] = {
    "node": NodeCtrl,
    "link": RelationshipCtrl,
    "document": NodeCtrl,
    "media": MediaCtrl
}

model_dict: Dict[str, Dict[str, info_models]] = {
    "node": {
        "default": NodeNormal,
        "Person": Person,
        "Project": Project,
        "ArchProject": ArchProject,
        "DocGraph": BaseDocGraph,
    },
    "link": {
        "default": KnowLedge,
        "KnowLedge": KnowLedge,
        "SearchTogether": FrequencyCount,
        "MentionTogether": FrequencyCount,
        "VisitAfter": FrequencyCount,
        "Doc2Node": Doc2Node,
    },
    "media": {
        "default": Text,
        "Image": Image,
        "Text": Text,
        "Audio": Audio,
        "Video": Video
    }
}


def bulk_save_base_model(item_list, user_model, _type):
    info_dict = {}
    items = [item for item in item_list if item]
    if items:
        items_id = {item.id: _type for item in items}
        user_model.bulk_create_source(items_id)
        output = np.array([item.output_table_create() for item in items])
        ctrl = list(output[:, 0])
        ctrl_dict[_type].objects.bulk_create(ctrl)
        info_list = list(output[:, 1])
        for info in info_list:
            if info.PrimaryLabel not in info_dict:
                info_dict[info.PrimaryLabel] = []
            info_dict[info.PrimaryLabel].append(info)
        for key in info_dict:
            type_label_to_model(_type, key).objects.bulk_create(info_dict[key])
        bulk_add_text_index(items)
        # 保存authority
        authority = list(output[:, 2])
        authority = [auth for auth in authority if auth]
        BaseAuthority.objects.bulk_create(authority)
        # 保存warn
        warn = list(output[:, 3])
        WarnRecord.objects.bulk_create(warn)
        if _type == 'node':
            history = list(output[:, 4])
            NodeVersionRecord.objects.bulk_create(history)
            bulk_add_node_index(items)


def node_init(label: str) -> Type[NodeInfo]:
    """
    从主标签返回模型信息 下同
    :param label: PrimaryLabel
    :return: NodeInfo
    """
    return type_label_to_model('node', label)


def link_init(label: str) -> Type[RelationshipInfo]:
    return type_label_to_model('link', label)


def media_init(label: str) -> Type[MediaInfo]:
    return type_label_to_model('media', label)


def get_update_props(_type: _types, p_label: str) -> List[Field]:
    """
    :param _type: type node...
    :param p_label: PrimaryLabel...
    :return: 数据可以直接写入的属性
    """
    remove_list = {
        "node": ["NodeId", "PrimaryLabel", "MainPic", "IncludedMedia",
                 "HasPaper", "HasGraph", "Size", "MainNodes", "Complete"],
        "link": ["LinkId", "PrimaryLabel", "Star"],
        "media": ["MediaId", "PrimaryLabel"],
    }
    try:
        # 目标包含的域
        target = type_label_to_model(_type=_type, label=p_label)._meta.get_fields()
        result = [field for field in target
                  if not field.auto_created
                  and field.name not in remove_list[_type]]
        return result
    except AttributeError("没有这种标签: %s" % p_label):
        return []


def get_special_props(_type: _types, p_label: str) -> List[Field]:
    """
    :param _type: _type
    :param p_label: PrimaryLabel
    :return: 该标签的特殊属性 不包含.*Info
    """
    result = get_update_props(_type, p_label)
    result = [field for field in result if re_for_info.match(field.model.__name__)]
    return result


def neo4j_create_node(_id: int, _type: _types, labels: List[str], plabel: str,
                      props: Dict, collector: NeoSet(),
                      is_user_made=True, is_common=True) -> NeoNode:
    """

    :param _id: _id
    :param _type: Node | Media | Document | Fragment
    :param labels: 标签组
    :param plabel: 主标签
    :param props: 属性
    :param is_user_made: 是否是用户创建的
    :param is_common: 是否是公开的
    :param collector: 连接池
    :return: None | Node
    """
    node_labels = ["Used"]
    node_labels.extend(labels)
    node_labels.append(_type)
    node_labels.append(plabel),
    if is_user_made:
        node_labels.append("UserMade")
    if is_common:
        node_labels.append("Common")
    node = NeoNode(*node_labels, **props)
    node["_id"] = _id
    node["_type"] = _type
    node["_label"] = plabel
    node.__primarylabel__ = plabel
    node.__primarykey__ = "_id"
    node.__primaryvalue__ = _id
    collector.tx.create(node)
    return node


def dict_dryer(node: dict):
    dry_prop = ["_id", "type", "PrimaryLabel"]
    for key in dry_prop:
        if key in node:
            node.pop(key)
    return node


class BaseModel:
    """
    提供的方法
    query_ctrl, query_info, query_node, query_authority, auth_create, info_update
    """

    def __init__(self, _id: int, user_id: int, _type: _types, collector=NeoSet()):
        default = 'default'
        self.node: Optional[NeoNode] = None
        self.info: Optional[type_label_to_model(_type, default)] = None
        self.ctrl: Optional[ctrl_dict[_type]] = None
        self.authority: Optional[BaseAuthority] = None
        self.warn: Optional[WarnRecord] = None
        # 以下是值
        self.collector = collector  # neo4j连接池
        self.id = _id  # _id
        self.user_id = int(user_id)
        self.type = _type
        self.p_label = ""  # 主标签
        self.is_draft = False  # 是否是草稿
        self.is_create = False  # 是否是创建状态
        self.is_user_made = check_is_user_made(user_id)
        self.lack = []

    # ----------------- query ----------------
    def query_base(self):
        """
        查询info,ctrl,text, authority的内容 也就是前端 索引的基本内容
        :return:
        """
        result = self.__query_ctrl()
        result &= self.__query_info()

        return result

    def __query_ctrl(self) -> bool:
        if not self.ctrl:
            try:
                self.ctrl = ctrl_dict[self.type].objects.get(pk=self.id)
                self.p_label = self.ctrl.PrimaryLabel
                return True
            except ObjectDoesNotExist:
                return False
        else:
            self.p_label = self.ctrl.PrimaryLabel
            return True

    def __query_info(self) -> bool:
        if not self.ctrl:
            return False
        elif not self.info:
            try:
                self.info = type_label_to_model(self.type, self.p_label).objects.get(pk=self.id)
                return True
            except ObjectDoesNotExist:
                return False
        else:
            return True

    def __query_node(self):
        if self.type != "link":
            self.node = self.collector.Nmatcher.match(_id=self.id).first()
            if not self.node:
                self.lack.append("node")
        else:
            raise TypeError('link does not have NeoNode!')

    def __query_authority(self) -> bool:
        if self.type != "link":
            if not self.authority:
                try:
                    self.authority = BaseAuthority.objects.get(SourceId=self.id, SourceType=self.type)
                    return True
                except ObjectDoesNotExist:
                    self.lack.append("authority")
                    return False
            else:
                return True
        else:
            raise TypeError('link does not have Authority!')

    def auth_create(self, data):
        self.authority = BaseAuthority(
            SourceId=self.id,
            SourceType=self.type,
            Used=True,
            Common=data["$_IsCommon"],
            OpenSource=data["$_IsOpen"],
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
        self.warn = WarnRecord(
            SourceId=self.id,
            SourceLabel=self.p_label,
            BugType="None",
            CreateUser=self.user_id
        )
        if self.user_id == self.ctrl.CreateUser:
            if self.info:
                needed_props = get_update_props(self.type, self.p_label)
                for field in needed_props:
                    old_prop = getattr(self.info, field.name)
                    if field.name in data:
                        new_prop = data[field.name]
                    else:
                        new_prop = field.default
                    self.__update_prop(field, new_prop, old_prop)
                    # todo field resolve
                return self
            else:
                return ErrorContent(status=400, state=False, reason="info dos not query")
        else:
            return ErrorContent(status=401, state=False, reason="unAuthorization")

    def text_index(self):
        if len(list(self.info.Text.keys())) > 0:
            language = list(self.info.Text.keys())[0]
            text = self.info.Text[language]
        else:
            language = "auto"
            text = ""
        body = {
            "id": self.id,
            "type": self.type,
            "PrimaryLabel": self.p_label,
            "Language": language,
            "Name": self.info.Name,
            "Labels": self.info.Labels,
            "Text": {
                "zh": "",
                "en": "",
                "auto": text
            },
            "Hot": self.ctrl.Hot,
            "Star": self.ctrl.Star
        }
        for lang in body["Text"]:
            if lang in self.info.Text:
                body["Text"][lang] = self.info.Text[lang]
        return body

    def output_table_create(self):
        return self.ctrl, self.info, self.authority, self.warn


class ErrorContent:
    """
    适用于不直接返回HttpResponse的情况
    """

    def __init__(self, status: int, state: bool, reason: str):
        self.status = status
        self.state = state
        self.reason = reason

    def __repr__(self):
        return {"state": self.state, "reason": self.reason}

    def __bool__(self):
        return False


def check_is_user_made(user_id):
    if user_id != 1:
        return True
    else:
        return False


def merge_list(lists):
    """
    合并并去重list
    :param lists:
    :return:
    """

    def merge(list1: list, list2: list):
        temp = [ele for ele in list2 if ele not in list1]
        list1.extend(temp)
        return list1

    result = reduce(merge, lists)
    return result


def model_to_dict(model: Model):
    fields = model._meta.get_fields()
    result = {field.name: getattr(model, field) for field in fields if not field.auto_created}
    return result


class DateTimeEncoder(json.JSONEncoder):
    """
    DateTime 转为字符串
    """

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        return json.JSONEncoder.default(self, obj)
