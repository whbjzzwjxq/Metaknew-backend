from typing import Optional, Union
from typing import Type

from django.core.exceptions import ObjectDoesNotExist
from py2neo import walk, Relationship
from py2neo.data import Node as NeoNode

from base_api.interface_frontend import LinkInfoFrontend, QueryObject
from subgraph.class_base import PublicItemModel
from subgraph.models import RelationshipCtrl, RelationshipInfo, KnowLedge, FrequencyCount, DocToNode
from tools.base_tools import NeoSet
from tools.global_const import type_and_label_to_ctrl_model


def query_object_to_link_ctrl(query_object: dict, prefix: str) -> dict:
    return {
        prefix + 'Id': query_object['_id'],
        prefix + 'Type': query_object['_type'],
        prefix + 'PLabel': query_object['_label']
    }


class LinkModel(PublicItemModel):
    ctrl_class = KnowLedge
    info_class = RelationshipInfo

    def __init__(self, _id: Union[int, str], user_id: int, _type='link', collector=NeoSet()):
        """
        :param user_id:用户/设备id
        :param _id: link id
        :param _type: link
        :param collector: Neo4j连接池
        """
        super().__init__(_id, user_id, _type, collector)
        self._start: Optional[NeoNode] = None
        self._end: Optional[NeoNode] = None
        self._walk = None
        self._graph_link: Optional[Relationship] = None
        self._ctrl: Optional[Type[RelationshipCtrl]] = None
        self._info: Optional[Type[RelationshipInfo]] = None

    def query_neo4j_node(self, _id, _type, _label):
        return self.collector.Nmatcher.match(_type, _label, _id=_id).first()

    @property
    def graph_link(self):
        if not self._graph_link:
            self._graph_link = self.collector.Rmatcher.match(r_type=self.p_label, _id=self.id).first()
            if not self._graph_link:
                self._graph_link_init()
                return self._graph_link
            return self._graph_link
        else:
            return self._graph_link

    @property
    def start(self):
        if not self._start:
            self._start = self.collector.match_node(self.ctrl.StartId)
        return self._start

    @property
    def end(self):
        if not self._end:
            self._end = self.collector.match_node(self.ctrl.EndId)
        return self._end

    @property
    def walk(self):
        if not self._walk:
            self._walk = walk(self.graph_link())
            return self._walk
        else:
            return self._walk

    @staticmethod
    def query_by_node(p_label: str, start=None, end=None):
        """
        使用起始和终止节点查询
        :param p_label: 主标签
        :param start: QueryObject
        :param end: QueryObject
        :return: BaseLink
        """
        query_dict = {
            'PrimaryLabel': p_label
        }
        if start:
            query_dict.update(query_object_to_link_ctrl(start, 'Start'))
        if end:
            query_dict.update(query_object_to_link_ctrl(end, 'End'))
        try:
            ctrl_set = RelationshipCtrl.objects.filter(**query_dict)
            return ctrl_set

        except ObjectDoesNotExist:
            return None

    def create(self, frontend_data: LinkInfoFrontend, create_type: str = 'USER'):
        """
        收集基础信息
        :param create_type: 创建
        :param frontend_data: 前端传回的数据
        :return:
        """
        self.is_create = True
        self.frontend_id = frontend_data.id
        self._start = self.collector.match_node(frontend_data.Start.id).first()
        self._end = self.collector.match_node(frontend_data.End.id).first()
        self.update(frontend_data, create_type)
        return self

    def _ctrl_update_special_hook(self, frontend_data: LinkInfoFrontend):
        self.ctrl.StartId = frontend_data.Start.id
        self.ctrl.StartType = frontend_data.Start.type
        self.ctrl.StartLabel = frontend_data.Start.pLabel
        self.ctrl.EndId = frontend_data.End.id
        self.ctrl.EndType = frontend_data.End.type
        self.ctrl.EndPLabel = frontend_data.End.pLabel

    def _update_special_hook(self, frontend_data: LinkInfoFrontend, create_type):
        self.graph_link_update()

    def _graph_link_init(self):
        link = Relationship(self.start, self.p_label, self.end)
        link['_id'] = self.id
        link['_label'] = self.p_label
        self._graph_link = link
        self.collector.tx.create(self.graph_link)

    def graph_link_update(self):
        neo_prop = {
            "IsUsed": self.ctrl.IsUsed,
            "Name": self.info.Name,
            "CreateTime": self.ctrl.CreateTime,
            "CreateType": self.ctrl.CreateType,
        }
        self.graph_link.update(neo_prop)
        self.collector.tx.push(self.graph_link)

    @classmethod
    def bulk_save_create(cls, model_list, collector):
        result = super().bulk_save_create(model_list, collector)
        if result is not None:
            collector.tx.commit()
        return result

    @classmethod
    def bulk_save_update(cls, model_list, collector):
        result = super().bulk_save_update(model_list, collector)
        if result:
            collector.tx.commit()
        return result

    def save(self, history_save=True, neo4j_save=True, es_index_text=True):
        super().save(history_save, neo4j_save, es_index_text)


class SysLinkModel:
    ctrl_class = DocToNode

    def __init__(self, _id: int, user_id: int, _label: str, _type="link", collector=NeoSet()):
        self.id = _id
        self.user_id = int(user_id)
        self.collector = collector
        self.p_label = _label
        self._ctrl: Optional[Type[DocToNode], Type[FrequencyCount]] = None
        self._link: Optional[Relationship] = None
        self.ctrl_class: Type[RelationshipCtrl] = type_and_label_to_ctrl_model('link', _label)

    @property
    def ctrl(self):
        if self._ctrl is None:
            self._ctrl = self.ctrl_class.objects.get(pk=self.id)
        return self._ctrl

    @property
    def link(self):
        if self._link is None:
            self._link = self.collector.match_link({'_id': self.id, 'type': 'link', '_label': self.p_label}).first()
        return self._link

    @property
    def start(self):
        return self.link.start_node

    @property
    def end(self):
        return self.link.end_node

    @staticmethod
    def query_by_node(p_label: str, start: str = None, end: str = None) -> \
            Optional[Type[RelationshipCtrl]]:
        """
        使用起始和终止节点查询
        :param p_label: 主标签
        :param start: id
        :param end: id
        :return: BaseLink
        """
        query_dict = {
            'PrimaryLabel': p_label
        }
        if start:
            query_dict.update({'StartId': start})
        if end:
            query_dict.update({'EndId': end})
        try:
            ctrl_set = type_and_label_to_ctrl_model('link', p_label).objects.filter(**query_dict).first()
            return ctrl_set

        except ObjectDoesNotExist:
            return None

    def _link_init(self, data):
        link = self.collector.match_link({'_id': self.id, 'type': 'link', '_label': self.p_label}).first()
        if link:
            self._link = link
        else:
            link = Relationship(data['Start'], self.p_label, data['End'], _id=self.id)
            self.collector.tx.create(link)
            self._link = link

    def _ctrl_init(self, data):
        self._ctrl = self.ctrl_class(
            ItemId=self.id,
            ItemType='link',
            PrimaryLabel=self.p_label,
            CreateUser=self.user_id,
            CreateType='AUTO',
            PropsWarning={}
        )
        self.ctrl.StartId = data['Start']['_id']
        self.ctrl.StartType = data['Start']['_type']
        self.ctrl.StartPLabel = data['Start']['_label']
        self.ctrl.EndId = data['End']['_id']
        self.ctrl.EndType = data['End']['_type']
        self.ctrl.EndPLabel = data['End']['_label']

    def ctrl_update(self, data):
        self.ctrl.IsUsed = data['IsUsed']
        self.ctrl.IsMain = data['IsMain']
        self.ctrl.Correlation = data['Correlation']
        self.ctrl.DocumentImp = data['DocumentImp']

    def create(self, data):
        self._ctrl_init(data)
        self._link_init(data)
        self.update(data)
        return self

    def update(self, data):
        self.ctrl_update(data)
        self.graph_link_update()
        return self

    def graph_link_update(self):
        # 注意这里是ctrl
        props = self.ctrl.props_to_neo()
        for prop in props:
            value = getattr(self.ctrl, prop)
            if prop == 'CreateTime':
                value = str(value)
            self.link.update({prop: value})
        self.collector.tx.push(self.link)

    def save(self):
        self.ctrl.save()
        self.collector.tx.commit()

    def delete(self):
        self.ctrl.IsUsed = False
        self.link['IsUsed'] = False
        return self

    @classmethod
    def bulk_save_update(cls, model_list, collector: NeoSet):
        ctrl_list = [link.ctrl for link in model_list]
        cls.ctrl_class.objects.bulk_update(ctrl_list, [field.name for field in cls.ctrl_class._meta.fields
                                                       if not field.auto_created and not field.name == 'ItemId'])
        collector.tx.commit()
        return True

    @classmethod
    def bulk_save_create(cls, model_list, collector: NeoSet):
        ctrl_list = [link.ctrl for link in model_list]
        cls.ctrl_class.objects.bulk_create(ctrl_list)
        collector.tx.commit()
        return True
