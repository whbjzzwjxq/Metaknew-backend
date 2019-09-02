import re
from subgraph.models import *
from py2neo import Graph, NodeMatcher, RelationshipMatcher
from subgraph.models import BaseDoc
from functools import reduce
from django.db.models import Model
from django.db.models import Field
from typing import List, Dict
import os

re_for_uuid = re.compile(r"\w{8}(-\w{4}){3}-\w{12}")
re_for_ptr = re.compile(r".*_ptr")
graph = Graph("bolt://39.96.10.154:7687", username="neo4j", password="12345678")
types = ["StrNode", "InfNode", "Media", "Document"]

basePath = os.path.dirname(os.path.dirname(__file__))


class NeoSet:
    def __init__(self):
        self.tx = graph.begin()
        self.Nmatcher = NodeMatcher(graph)
        self.Rmatcher = RelationshipMatcher(graph)


node_model_dict: Dict[str, NodeInfo] = {
    "BaseNode": NodeInfo,
    "Person": Person,
    "Project": Project,
    "ArchProject": ArchProject,
    "Document": BaseDoc,
}


link_model_dict: Dict[str, Relationship] = {
    "Topic2Topic": Topic2Topic,
    "Topic2Node": Topic2Node,
    "Doc2Node": Doc2Node,
    "SearchTogether": SearchTogether,
    "AfterVisit": AfterVisit,
    "MentionTogether": MentionTogether,
    "KnowLedge": KnowLedge,
}


def node_init(label) -> node_model_dict:
    if label in node_model_dict:
        return node_model_dict[label]
    else:
        return NodeInfo


def link_init(label) -> link_model_dict:
    if label in link_model_dict:
        return link_model_dict[label]
    else:
        return KnowLedge


def get_user_props(p_label: str) -> List[Field]:
    """
    :param p_label: PrimaryLabel
    :return: 该主标签下需要用户/前端提交的属性
    """
    remove_list = ["NodeId", "PrimaryLabel", "MainPic", "IncludedMedia"]
    try:
        # 目标包含的域
        target = node_model_dict[p_label]._meta.get_fields()
        result = [field for field in target
                  if not field.auto_created
                  and field.name not in remove_list]
        return result
    except AttributeError("没有这种标签: %s" % p_label):
        return []


def get_special_props(p_label: str) -> List[Field]:
    """
    :param p_label: PrimaryLabel
    :return: 该标签的特殊属性 不包含NodeInfo
    """
    if p_label in node_model_dict:
        result = get_user_props(p_label)
        result = [field for field in result if field.model.__name__ != 'NodeInfo']
        return result
    else:
        return []


def get_system_link_props(r_type: str) -> List[Field]:
    """
    :param r_type: Link的Type
    :return: 该link之下需要填充的属性
    """
    try:
        target = link_model_dict[r_type]._meta.get_fields()
        result = [field for field in target
                  if not re_for_ptr.match(field.name)
                  and field.model != "Relationship"]
        return result
    except AttributeError("没有这种标签: %s" % r_type):
        return []


def dict_dryer(node: dict):
    dry_prop = ["_id", "type", "PrimaryLabel"]
    for key in dry_prop:
        if key in node:
            node.pop(key)
    return node


def merge_list(lists):
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
