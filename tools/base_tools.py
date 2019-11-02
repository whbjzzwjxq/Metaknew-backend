import datetime
import json
import os
import re
from datetime import date
from functools import reduce
from typing import List, Dict, Type, Union

import numpy as np
from django.db.models import Field, Model
from py2neo import Graph, NodeMatcher, RelationshipMatcher
from py2neo.data import Node as NeoNode

from es_module.logic_class import bulk_add_node_index, bulk_add_text_index
from record.models import WarnRecord, VersionRecord
from subgraph.models import *

re_for_info = re.compile(r".*Info")
re_for_ptr = re.compile(r".*_ptr")
graph = Graph("bolt://39.96.10.154:7687", username="neo4j", password="12345678")

basePath = os.path.dirname(os.path.dirname(__file__))
str_types = Union['node', 'link', 'course', 'media']
info_models = Union[Type[NodeInfo], Type[MediaInfo], Type[RelationshipInfo]]


class NeoSet:
    def __init__(self):
        self.tx = graph.begin()
        self.Nmatcher = NodeMatcher(graph)
        self.Rmatcher = RelationshipMatcher(graph)


def type_label_to_info_model(_type: str_types, label: str) -> info_models:
    """
    可能有多张表继承的模型
    :param _type:
    :param label:
    :return:
    """
    if _type in info_dict:
        if label in info_dict[_type]:
            return info_dict[_type][label]
        else:
            return info_dict[_type]['default']
    else:
        raise TypeError('Error Type')


ctrl_dict: Dict[str, Type[ItemCtrl]] = {
    "node": NodeCtrl,
    "link": RelationshipCtrl,
    "document": NodeCtrl,
    "media": MediaCtrl
}

info_dict: Dict[str, Dict[str, info_models]] = {
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
        "default": Image,
        "image": Image,
        "text": Text,
        "audio": Audio,
        "video": Video
    },
    "document": {
        "default": BaseDocGraph,
        "DocGraph": BaseDocGraph
    }
}


def bulk_save_base_model(item_list, user_model, _type):
    ctrl_un_update_props = ['ItemId', 'ItemType', 'PrimaryLabel', 'CreateTime']
    ctrl_update_props = [field for field in ctrl_dict[_type]._meta.fields if field.name not in ctrl_un_update_props]

    def info_list_to_dict(info_list):
        """
        整理info_list 找到对应的info_dict
        :return:
        """
        info_label_dict = {}
        for info in info_list:
            if info.PrimaryLabel not in info_label_dict:
                info_label_dict[info.PrimaryLabel] = []
            info_label_dict[info.PrimaryLabel].append(info)
        return info_label_dict

    items = [item for item in item_list if item]
    if items:
        # 创建内容记录
        items_id = {item.id: _type for item in items if item.is_create}
        user_model.bulk_create_source(items_id)

        # create部分
        output_create = np.array([item.output_table_create() for item in items if item.is_create])
        if len(output_create) > 0:
            ctrl_container = list(output_create[:, 0])
            ctrl_dict[_type].objects.bulk_create(ctrl_container)

            info_container = info_list_to_dict(list(output_create[:, 1]))
            for key in info_container:
                type_label_to_info_model(_type, key).objects.bulk_create(info_container[key])

            warn_container = [warn for warn in output_create[:, 2] if warn.WarnContent != []]
            WarnRecord.objects.bulk_create(warn_container)

        # update部分
        output_update = np.array([item.output_table_create() for item in items if not item.is_create])
        if len(output_update) > 0:
            ctrl_container = list(output_update[:, 0])
            ctrl_dict[_type].objects.bulk_update(ctrl_container, [field.name for field in ctrl_update_props])
            info_container = info_list_to_dict(list(output_update[:, 1]))
            for key in info_container:
                fields = [field.name for field in get_update_props(_type=_type, p_label=key)]
                type_label_to_info_model(_type, key).objects.bulk_update(info_container[key], fields)

            # warn_content
            warn_container: List[WarnRecord] = []
            for warn in output_update[:, 2]:
                warn: WarnRecord
                if not warn.WarnContent:
                    warn.Is_Solved = True
                else:
                    warn.Is_Solved = False
                warn_container.append(warn)
            WarnRecord.objects.bulk_update(warn_container, fields=['WarnContent', 'Is_Solved', 'CreateUser'])
            if _type != 'link':
                history = list(output_update[:, 3])
                VersionRecord.objects.bulk_create(history)

        # es_index
        bulk_add_text_index(items)
        if _type == 'node':
            bulk_add_node_index(items)


def node_init(label: str) -> Type[NodeInfo]:
    """
    从主标签返回模型信息 下同
    :param label: PrimaryLabel
    :return: NodeInfo
    """
    return type_label_to_info_model('node', label)


def link_init(label: str) -> Type[RelationshipInfo]:
    return type_label_to_info_model('link', label)


def media_init(label: str) -> Type[MediaInfo]:
    return type_label_to_info_model('media', label)


def get_update_props(_type: str_types, p_label: str) -> List[Field]:
    """
    :param _type: type node...
    :param p_label: PrimaryLabel...
    :return: 数据可以直接写入的属性
    """
    remove_list = {
        "node": ["ItemId", "PrimaryLabel", "MainPic", "IncludedMedia"],
        "link": ["ItemId", "PrimaryLabel", "Star", "Hot"],
        "media": ["ItemId", "PrimaryLabel"],
        "document": ["ItemId", "PrimaryLabel", "MainPic", "IncludedMedia",
                     "Size", "MainNodes", "Complete"],
    }
    try:
        # 目标包含的域
        target = type_label_to_info_model(_type=_type, label=p_label)._meta.get_fields()
        result = [field for field in target
                  if not field.auto_created
                  and field.name not in remove_list[_type]]
        return result
    except AttributeError("没有这种标签: %s" % p_label):
        return []


def get_special_props(_type: str_types, p_label: str) -> List[Field]:
    """
    :param _type: _type
    :param p_label: PrimaryLabel
    :return: 该标签的特殊属性 不包含.*Info
    """
    result = get_update_props(_type, p_label)
    result = [field for field in result if re_for_info.match(field.model.__name__)]
    return result


def neo4j_create_node(_id: int, _type: str_types, labels: List[str], plabel: str,
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
    collector.tx.base_node_create(node)
    return node


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
