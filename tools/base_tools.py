import hashlib
import re
import uuid
from subgraph.models import *
from media.models import *
from py2neo import Graph, NodeMatcher, RelationshipMatcher
from document.models import DocInfo

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
    return uuid.uuid1()


def get_dict(node):
    keylist = {}
    for key, value in node.__dict__.items():
        if not re.match(r'__.*__', key):
            keylist.update({key: value})
    if '_state' in keylist:
        keylist.pop('_state')
    return keylist


def delete_by_uuid(target, element, *args):
    i = 0
    length = len(target)
    while i < length:
        for name in args:
            if name in target[i]:
                if target[i][name] == element:
                    target.pop(i)
                    i = length
        i += 1
    return target
