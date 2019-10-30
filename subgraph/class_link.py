from datetime import datetime
from typing import Optional

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from py2neo import walk, Relationship
from py2neo.data import Node as NeoNode

from es_module.logic_class import bulk_add_text_index
from subgraph.class_node import BaseNode
from subgraph.models import RelationshipCtrl
from tools.base_tools import BaseModel, NeoSet, ctrl_dict, ErrorContent, link_init, get_update_props


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

    @staticmethod
    def query_by_start_end(start: int, end: int, single: bool, user_id: int, p_label=None, _id=0):
        """

        :param user_id: 查询用户的id
        :param _id: 可选 如果有single则必选
        :param p_label: 可选
        :param single: 是否是唯一性关系
        :param start: id
        :param end: id
        :return: list of link
        """
        try:
            ctrl_set = ctrl_dict["link"].objects.filter(Start=start, End=end)
            if single:
                if p_label:
                    ctrl_set = ctrl_set.filter(PrimaryLabel=p_label)
                link_ctrl = ctrl_set.get(pk=_id)
                link = BaseLink(_id=_id, user_id=user_id)
                link.ctrl = link_ctrl
                return link
            else:
                return ctrl_set

        except ObjectDoesNotExist or MultipleObjectsReturned:
            return ErrorContent(status=400, state=False, reason='关系不唯一')

    def query_link(self):
        if not self.ctrl:
            self.query_base()
        self.start = self.collector.Nmatcher.match(self.ctrl.StartPLabel, self.ctrl.StartType, _id=self.ctrl.Start)
        self.end = self.collector.Nmatcher.match(self.ctrl.EndPLabel, self.ctrl.EndType, _id=self.ctrl.End)
        self.link = self.collector.Rmatcher.match(nodes=(self.start, self.end), r_type=self.p_label, _id=self.id)
        return self

    def do_walk(self):
        self.walk = walk(self.link)
        self.start = self.walk.start_node
        self.end = self.walk.end_node

    def create(self, start: NeoNode, end: NeoNode, p_label, data, is_user_made):
        """
        收集基础信息
        :param data: data
        :param is_user_made: 是否是user_made
        :param start: 起点
        :param end:  终点
        :param p_label: p_label
        :return:
        """
        self.is_create = True
        self.bound_node(start, end, p_label, is_user_made)
        self.p_label = p_label
        # ctrl
        self.__ctrl_create()
        self.auth_create(data=data)
        # info
        self.info = link_init(p_label)()
        self.info.PrimaryLabel = p_label
        self.info.LinkId = self.id
        self.info_update(data)

        # link
        self.link = Relationship(self.start, p_label, self.end)
        self.__link_update(data)
        self.collector.tx.create(self.link)
        return self

    def __ctrl_create(self):
        self.ctrl = RelationshipCtrl(
            LinkId=self.id,
            PrimaryLabel=self.p_label,
            Start=self.start["_id"],
            StartType=self.start["_type"],
            StartPLabel=self.start["_label"],
            End=self.end["_id"],
            EndType=self.end["_type"],
            EndPLabel=self.end["_label"],
            Is_UserMade=self.is_user_made,
            CreateUser=self.user_id
        )

    def bound_node(self, start, end, p_label, is_user_made):
        self.start = start
        self.end = end
        self.p_label = p_label
        self.is_user_made = is_user_made

    def __link_update(self, data):
        neo4j_props = {"Is_UserMade": self.is_user_made, "CreateTime": datetime.now().strftime('%a, %b %d %H:%M')}
        self.link.update(neo4j_props)

    def save(self):
        self.info.save()
        self.ctrl.save()
        self.collector.tx.commit()
        bulk_add_text_index([self])


class SystemMade(BaseLink):

    def pre_create(self, start: NeoNode, end: NeoNode, p_label, data):
        # 注意start end是NeoNode
        if self.check_exist(start, end, p_label):
            return None
        else:
            self.create(start, end, p_label, data, False)
        return self

    def check_exist(self, start, end, p_label):
        return self.query_by_start_end(start["_id"], end["_id"], single=True, user_id=self.user_id, p_label=p_label,
                                       _id=self.id)

    def __link_update(self, data):
        neo4j_props = {
            "Is_UserMade": self.is_user_made,
            "CreateTime": datetime.now().strftime('%a, %b %d %H:%M'),
        }
        fields = get_update_props("link", self.p_label)
        for field in fields:
            if field.name in data:
                neo4j_props[field.name] = data[field.name]
            else:
                neo4j_props[field.name] = getattr(self.info, field.name)

    def text_index(self):
        return {}

    def auth_create(self, data):
        pass

    def save(self):
        self.info.save()
        self.ctrl.save()
        self.collector.tx.commit()

    def delete(self):
        self.query_link()
        self.ctrl.isUsed = False
        self.link['isUsed'] = False
        return self
