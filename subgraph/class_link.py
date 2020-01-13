from datetime import datetime
from typing import Optional

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from py2neo import walk, Relationship
from py2neo.data import Node as NeoNode

from es_module.logic_class import bulk_add_text_index
from record.logic_class import UnAuthorizationError
from subgraph.class_base import BaseModel
from subgraph.class_node import BaseNode
from subgraph.models import RelationshipCtrl
from tools.base_tools import NeoSet, get_update_props


def node_to_dict(start: NeoNode, end: NeoNode) -> dict:
    node_ctrl_dict = {
        'Start': start["_id"],
        'StartType': start["_type"],
        'StartPLabel': start["_label"],
        'End': end["_id"],
        'EndType': end["_type"],
        'EndPLabel': end["_label"]
    }
    return node_ctrl_dict


class BaseLink(BaseModel):
    def __init__(self, _id: int, user_id: int, _type="link", collector=NeoSet()):
        """

        :param user_id:用户/设备id
        :param _id: link id
        :param _type: link
                :param collector: Neo4j连接池
        """
        super().__init__(_id, user_id, _type, collector)

        self.walk: Optional[walk] = None
        self.start: Optional[BaseNode] = None
        self.end: Optional[BaseNode] = None
        self.link: Optional[Relationship] = None
        self.node_ctrl_dict = {}  # Start id type label一系列内容

    @staticmethod
    def query_by_node_single(start: NeoNode, end: NeoNode, user_id: int, _id: int, p_label: str):
        """
        使用起始和终止节点查询
        :param user_id: 查询用户的id
        :param _id: 可选 如果有single则必选
        :param p_label: 可选
        :param start: NeoNode
        :param end: NeoNode
        :return: BaseLink
        """
        node_ctrl_dict = node_to_dict(start, end)
        try:
            ctrl_set = RelationshipCtrl.objects.filter(**node_ctrl_dict)
            if p_label:
                link_ctrl = ctrl_set.get(PrimaryLabel=p_label)
            else:
                link_ctrl = ctrl_set.get(pk=_id)

            link = BaseLink(_id=_id, user_id=user_id)
            link.ctrl = link_ctrl
            return link

        except ObjectDoesNotExist:
            return None

        except MultipleObjectsReturned:
            error_output = node_to_dict(start, end)
            error_output.update({'label': p_label, '_id': _id})
            raise MultipleObjectsReturned(error_output)

    def query_link(self):
        if not self.ctrl:
            self.query_base()
        self.start = self.collector.Nmatcher.match(self.ctrl.StartPLabel, self.ctrl.StartType, _id=self.ctrl.Start)
        self.end = self.collector.Nmatcher.match(self.ctrl.EndPLabel, self.ctrl.EndType, _id=self.ctrl.End)
        self.link = self.collector.Rmatcher.match(nodes=(self.start, self.end), r_type=self.p_label, _id=self.id)
        return self

    def base_link_create(self, start: NeoNode, end: NeoNode, p_label, data):
        """
        收集基础信息
        :param data: data
        :param start: 起点
        :param end:  终点
        :param p_label: p_label
        :return:
        """
        self.is_create = True
        self.start = start
        self.end = end
        self.p_label = p_label
        # ctrl
        self._ctrl_create()
        self.node_ctrl_dict = node_to_dict(self.start, self.end)
        self.ctrl_update_by_user(data)
        # info link
        self.__link_create()
        self._info_create()
        self.info_update(data)
        return self

    def __link_create(self):
        link = Relationship(self.start, self.p_label, self.end)
        link['_id'] = self.id
        link['_label'] = self.p_label
        self.link = link
        self.collector.tx.create(link)

    def ctrl_update_by_user(self, data):
        auth_ctrl_props = ['Is_Common', 'Is_Used', 'Is_Shared', 'Is_OpenSource']
        if self.ctrl.CreateUser == self.user_id:
            for prop in auth_ctrl_props:
                if '$_' + prop in data:
                    setattr(self.ctrl, prop, data['$_' + prop])
                else:
                    pass
            for prop in self.node_ctrl_dict:
                setattr(self.ctrl, prop, self.node_ctrl_dict[prop])

        else:
            self.error_output(UnAuthorizationError, '没有权限')

    def info_special_update(self, data):
        pass

    def graph_update(self, data):
        neo4j_props = {
            "Is_UserMade": self.ctrl.Is_UserMade,
            "Is_Used": self.ctrl.Is_Used,
            "Is_Common": self.ctrl.Is_Common
        }
        self.link.update(neo4j_props)

    def do_walk(self):
        self.walk = walk(self.link)
        self.start = self.walk.start_node
        self.end = self.walk.end_node

    def save(self):
        self.info.save()
        self.ctrl.save()
        self.collector.tx.commit()
        bulk_add_text_index([self])


class SystemMade(BaseLink):

    def __init__(self, _id: int, user_id: int, _type="link", collector=NeoSet()):

        super().__init__(_id, user_id, _type, collector)
        self.is_user_made = False

    def pre_create(self, start: NeoNode, end: NeoNode, p_label, data):
        # 注意start end是NeoNode
        if self.check_exist(start, end, p_label):
            return None
        else:
            self.base_link_create(start, end, p_label, data)
            return self

    def check_exist(self, start, end, p_label):
        return self.query_by_node_single(start, end, user_id=self.user_id, p_label=p_label, _id=self.id)

    def graph_update(self, data):
        neo4j_props = {
            "Is_Used": self.ctrl.Is_Used,
            "Is_Common": self.ctrl.Is_Common,
            "Is_UserMade": self.is_user_made,
            "CreateTime": datetime.now().replace(microsecond=0),
        }
        fields = get_update_props("link", self.p_label)
        for field in fields:
            if field.name in data:
                neo4j_props[field.name] = data[field.name]
            else:
                neo4j_props[field.name] = getattr(self.info, field.name)

        self.link.update(neo4j_props)
        self.collector.tx.push(self.link)

    def text_index(self):
        return {}

    def save(self):
        self.info.save()
        self.ctrl.save()
        self.collector.tx.commit()

    def delete(self):
        self.query_link()
        self.ctrl.Is_Used = False
        self.link['Is_Used'] = False
        return self
