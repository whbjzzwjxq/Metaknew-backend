import json
import mimetypes
import oss2
from datetime import datetime, timezone
from typing import Optional, Dict, List, Type

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Max
from py2neo.data import Node as NeoNode

from record.logic_class import error_check, ObjectAlreadyExist, field_check
from record.models import NodeVersionRecord, WarnRecord
from subgraph.models import NodeCtrl, NodeInfo, Fragment
from tools import base_tools
from tools.aliyun import authorityKeys
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
    "$_IsShared": True,
}


# class BaseFragment:
#     # todo 重构Node level: 2
#     label = "Fragment"
#
#     def __init__(self, _id: int, user_id: int, collector):
#         self.id = _id
#         self.user_id = user_id
#         self.labels = []
#         self.collector = collector
#         self.node = Node()
#         self.info = Fragment()
#
#     def create(self, data):
#         self.info = Fragment(NodeId=self.id,
#                              CreateUser=self.user_id)
#         self.info_update(data)
#         self.node = neo4j_create_node(_type="Fragment",
#                                       labels=data["Labels"],
#                                       props={"_id": self.id},
#                                       plabel="Fragment",
#                                       is_common=False,
#                                       collector=self.collector)
#         return self
#
#     def info_update(self, node):
#         needed_props = base_tools.get_update_props(self.label)
#         for field in needed_props:
#             old_prop = getattr(self.info, field.name)
#             if field.name in node:
#                 new_prop = getattr(node, field.name)
#             else:
#                 new_prop = type(old_prop)()
#             self.__update_prop(field, new_prop, old_prop)
#         return self
#
#     @staticmethod
#     def __update_prop(field, new_prop, old_prop):
#         if new_prop != old_prop:
#             setattr(field.model, field.name, new_prop)
