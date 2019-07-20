import hashlib
import re
import uuid
from subgraph.models import *
from media.models import *
from py2neo import Graph, NodeMatcher, RelationshipMatcher
from document.models import DocInfo
from functools import reduce

re_for_uuid = re.compile(r'\w{8}(-\w{4}){3}-\w{12}')
re_for_ptr = re.compile(r'.*_ptr')
graph = Graph('bolt://39.96.10.154:7687', username='neo4j', password='12345678')
types = ['StrNode', 'InfNode', 'Media', 'Document']

# Neo4j Node用到的key
NeoNodeKeys = ['Name', 'Name_zh', 'Name_en', 'PrimaryLabel', 'Area', 'Language']


# Neo4j Relationship用到的key


class NeoSet:
    def __init__(self):
        self.tx = graph.begin()
        self.Nmatcher = NodeMatcher(graph)
        self.Rmatcher = RelationshipMatcher(graph)


class_table = {
    'Base': Node,
    'Person': Person,
    'Project': Project,
    'ArchProject': ArchProject,
    'Document': DocInfo,
    'Paper': Paper
}

label_hash = {
    'Person': '000a',
    'Project': '000b',
    'ArchProject': '001b',
    'Document': 'a000',
    'Path': 'ab00',
    'Rel': 'aa99',
    'Comment': 'a0a0'
}

device_hash = {
    '0': '000a',
    '1': '000b'
}


def init(label):
    if label in class_table:
        return class_table[label]
    else:
        return Node


def get_uuid(name, label, device):
    origin_uuid = str(uuid.uuid1())[-17:]
    md5 = hashlib.md5(name.encode(encoding='UTF-8')).hexdigest()[0:8]
    a = label_hash.get(label, '0000')
    b = device_hash.get(device, '0000')
    return md5 + '-' + a + '-' + b + '-' + origin_uuid


def rel_uuid():
    return str(uuid.uuid1())


def get_props_for_user_ctrl(p_label: str):
    """
    :param p_label: PrimaryLabel
    :return: 不包含BaseNode字段信息的列表
    注意p_label = Document进行了特殊处理
    """
    if not p_label == 'Document':
        try:
            # 目标包含的域
            target = class_table[p_label]._meta.get_fields()
            result = [field.name for field in target
                      if not field.model == NodeShow
                      and not field.model == NodeCtrl
                      and not re_for_ptr.match(field.name)]
            return result
        except AttributeError('没有这种标签: %s' % p_label):
            return []
    else:
        return ["Title", "MainPic", "Area", "CreateUser", "Description", "Keywords"]


def uuid_matcher(string):
    if re_for_uuid.match(string):
        return True
    else:
        return False


def dict_dryer(node: dict):
    dry_prop = ['id', 'Labels', 'type', 'PrimaryLabel']
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


