import re
from subgraph.models import *
from py2neo import Graph, NodeMatcher, RelationshipMatcher
from document.models import _Doc
from functools import reduce
from record.logic_class import ErrorRecord

re_for_uuid = re.compile(r'\w{8}(-\w{4}){3}-\w{12}')
re_for_ptr = re.compile(r'.*_ptr')
graph = Graph('bolt://39.96.10.154:7687', username='neo4j', password='12345678')
types = ['StrNode', 'InfNode', 'Media', 'Document']


class NeoSet:
    def __init__(self):
        self.tx = graph.begin()
        self.Nmatcher = NodeMatcher(graph)
        self.Rmatcher = RelationshipMatcher(graph)


class_table = {
    'NodeInfo': NodeInfo,
    'Person': Person,
    'Project': Project,
    'ArchProject': ArchProject,
    'Document': _Doc,
}


def init(label):
    if label in class_table:
        return class_table[label]
    else:
        return NodeInfo


def get_user_props(p_label: str) -> list:
    """
    :param p_label: PrimaryLabel
    :return: 不包含BaseNode字段信息的列表
    注意p_label = Document进行了特殊处理
    """
    remove_list = ['_id', 'PrimaryLabel', 'MainPic']
    try:
        # 目标包含的域
        target = class_table[p_label]._meta.get_fields()
        result = [field for field in target
                  if not re_for_ptr.match(field.name)
                  and field.name not in remove_list]
        return result
    except AttributeError('没有这种标签: %s' % p_label):
        return []


def dict_dryer(node: dict):
    dry_prop = ['_id', 'type', 'PrimaryLabel']
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

