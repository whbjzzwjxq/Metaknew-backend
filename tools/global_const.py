import os
import re
from typing import Union, Type, Dict

from py2neo import Graph

from subgraph.models import NodeInfo, MediaInfo, RelationshipInfo, NodeCtrl, \
    DocumentCtrl, MediaCtrl, FragmentCtrl, FragmentInfo, FrequencyCount, DocToNode, KnowLedge, \
    BaseInfo, BaseCtrl, RelationshipCtrl

# 远端id检测
re_for_frontend_id = re.compile('\\$_.*')
# neo4j连接池
graph = Graph("bolt://39.96.10.154:7687", Name="neo4j", password="12345678")
# 项目路径
basePath = os.path.dirname(os.path.dirname(__file__))
# InfoModel的集合
info_models = Union[Type[NodeInfo], Type[MediaInfo], Type[RelationshipInfo]]
# NeoNode为基础的Ctrl
node_class_ctrl = Union[Type[NodeCtrl], Type[MediaCtrl], Type[DocumentCtrl]]
# NeoLink为基础的Ctrl
link_class_ctrl = Union[Type[RelationshipCtrl], Type[FrequencyCount], Type[DocToNode], Type[KnowLedge]]
# id的类型
item_id = Union[str, int]
# document中Item的类型
item_type = Union['document', 'node', 'link', 'media', 'note', 'svg']
# 所有的资源的类型
source_type = Union[item_type, 'fragment', 'path']

# QueryObject
QueryObject = {
    '_id': 0,
    '_type': 'node',
    '_label': ''
}
# type_label与ctrl模型的字典
ctrl_dict: Dict[source_type, Dict[str, Type[BaseCtrl]]] = {
    "node": {
        'default': NodeCtrl
    },
    "link": {
        'default': KnowLedge,
        'DocToNode': DocToNode,
        'Frequency': FrequencyCount,
        'KnowLedge': KnowLedge
    },
    "document": {
        'default': DocumentCtrl
    },
    "media": {
        'default': MediaCtrl
    },
    "fragment": {
        'default': FragmentCtrl
    }
}
# type_label与info模型的字典
info_dict: Dict[source_type, Dict[str, Type[BaseInfo]]] = {
    "node": {
        'default': NodeInfo
    },
    "link": {
        'default': RelationshipInfo
    },
    "media": {
        'default': MediaInfo
    },
    "document": {
        'default': NodeInfo
    },
    "fragment": {
        'default': FragmentInfo
    }
}
# node的标签和属性的字典
node_label_prop_dict = {
    'ArchProject':
        {
            'PeriodStart': {
                'type': 'StringField',
                'resolve': 'time'
            },
            'PeriodEnd': {
                'type': 'StringField',
                'resolve': 'time'
            },
            'Nation': {
                'type': 'StringField',
                'resolve': 'location'
            },
            'Leader': {
                'type': 'ArrayField',
                'resolve': 'name'
            },
            'Location': {
                'type': 'StringField',
                'resolve': 'location'
            },
            'WorkTeam': {
                'type': 'ArrayField',
                'resolve': 'name'
            }
        },
    'Person':
        {
            'DateOfBirth': {
                'type': 'StringField',
                'resolve': 'time'
            },
            'DateOfDeath': {
                'type': 'StringField',
                'resolve': 'time'
            },
            'BirthPlace': {
                'type': 'StringField',
                'resolve': 'location'
            },
            'Nation': {
                'type': 'StringField',
                'resolve': 'location'
            },
            'Job': {
                'type': 'StringField',
                'resolve': 'name'
            },
            'Gender': {
                'type': 'StringField',
                'resolve': 'normal'
            }
        },
    'Project':
        {
            'PeriodStart': {
                'type': 'StringField',
                'resolve': 'time'
            },
            'PeriodEnd': {
                'type': 'StringField',
                'resolve': 'time'
            },
            'Nation': {
                'type': 'StringField',
                'resolve': 'location'
            },
            'Leader': {
                'type': 'ArrayField',
                'resolve': 'name'
            }
        },
}


def type_and_label_to_ctrl_model(_type: source_type, _label: str):
    if _type in ctrl_dict:
        if _label in ctrl_dict[_type]:
            return ctrl_dict[_type][_label]
        else:
            return ctrl_dict[_type]['default']
    else:
        raise TypeError('Error Type')


def type_and_label_to_info_model(_type: source_type, _label: str):
    if _type in info_dict:
        if _label in info_dict[_type]:
            return info_dict[_type][_label]
        else:
            return info_dict[_type]['default']
    else:
        raise TypeError('Error Type')

def default_translate():
    return {
        'auto': ''
    }