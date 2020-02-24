from datetime import datetime
from typing import Optional
from typing import Type

from django.core.exceptions import ObjectDoesNotExist
from py2neo import walk, Relationship
from py2neo.data import Node as NeoNode

from subgraph.class_base import PublicItemModel, type_and_label_to_ctrl_model, type_and_label_to_info_model
from subgraph.models import RelationshipCtrl, RelationshipInfo, KnowLedge, FrequencyCount, DocToNode
from tools.base_tools import NeoSet
from record.models import ItemVersionRecord


def query_object_to_link_ctrl(query_object: dict, prefix: str) -> dict:
    return {
        prefix + 'Id': query_object['_id'],
        prefix + 'Type': query_object['_type'],
        prefix + 'PLabel': query_object['_label']
    }


class BaseLinkModel(PublicItemModel):

    def __init__(self, _id: int, user_id: int, _label: str, _type='link', collector=NeoSet()):
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
        self._link: Optional[Relationship] = None
        self._ctrl: Optional[Type[RelationshipCtrl]] = None
        self._info: Optional[Type[RelationshipInfo]] = None
        self.ctrl_class = type_and_label_to_ctrl_model(_type, _label)
        self.info_class = type_and_label_to_info_model(_type, _label)

    def query_neo4j_node(self, _id, _type, _label):
        return self.collector.Nmatcher.match(_type, _label, _id=_id).first()

    def start(self):
        if not self._start:
            ctrl = self.ctrl
            self._start = self.query_neo4j_node(ctrl.EndId, ctrl.EndType, ctrl.EndLabel)
        return self._start

    def end(self):
        if not self._end:
            ctrl = self.ctrl
            self._end = self.query_neo4j_node(ctrl.StartId, ctrl.StartType, ctrl.StartLabel)
        return self._end

    def link(self):
        if not self._link:
            self._link = self.collector.Rmatcher.match(r_type=self.p_label, _id=self.id).first()
            return self._link
        else:
            return self._link

    def walk(self):
        if not self._walk:
            self._walk = walk(self.link())
            return self._walk
        else:
            return self._walk

    def node_ctrl_dict(self):
        result = {}
        result.update(query_object_to_link_ctrl(self.start(), 'Start'))
        result.update(query_object_to_link_ctrl(self.end(), 'End'))
        return result

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

    def create(self, frontend_data):
        """
        收集基础信息
        :param frontend_data: 前端传回的数据
        :return:
        """
        self.is_create = True
        self._start = self.query_neo4j_node(**frontend_data['Start'])
        self._end = self.query_neo4j_node(**frontend_data['End'])
        p_label = frontend_data['PrimaryLabel']
        # ctrl
        self._ctrl_init(p_label, frontend_data['CreateType'])
        # info link
        self._graph_link_create()
        self._info_init(p_label)
        self.update_by_user(frontend_data)
        return self

    def _graph_link_create(self):
        link = Relationship(self.start, self.p_label, self.end)
        link['_id'] = self.id
        link['_label'] = self.p_label
        self._link = link
        self.collector.tx.create(self.link())

    def info_special_update(self, data):
        pass

    def graph_link_update(self, data):
        neo_prop = {
            "IsUsed": self.ctrl.IsUsed,
            "Name": self.info.Name,
            "CreateTime": datetime.now().replace(microsecond=0),
            "CreateType": self.ctrl.CreateType,
        }
        self.link().update(neo_prop)
        self.collector.tx.push(self.link)

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


class KnowledgeLinkModel(BaseLinkModel, PublicItemModel):
    ctrl_class = KnowLedge

    def __init__(self, _id: int, user_id: int, _label: str, _type="link", collector=NeoSet()):
        super().__init__(_id, user_id, _label, _type, collector)
        self._ctrl: Optional[Type[KnowLedge]] = None

    def create(self, frontend_data):
        super().create(frontend_data)
        self.ctrl_update_by_user(frontend_data)

    def save(self, history_save=True, neo4j_save=True, es_index_text=True):
        super().save(history_save, neo4j_save, es_index_text)

    @classmethod
    def bulk_save_update(cls, model_list, collector):
        result = super().bulk_save_update(model_list, collector)
        if result:
            collector.tx.commit()
            history_model_list = [model.history.current_record for model in model_list]
            ItemVersionRecord.objects.bulk_create(history_model_list)
        return result


class SystemMadeLinkModel:

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
        if not self._ctrl:
            self._ctrl = self.ctrl_class.objects.get(pk=self.id)
        return self._ctrl

    @property
    def link(self):
        if not self._link:
            self._link = self.collector.match_link({'_id': self.id, 'type': 'link', '_label': self.p_label})
        return self._link

    @staticmethod
    def query_by_node(p_label: str, start=None, end=None) -> Optional[Type[RelationshipCtrl]]:
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
            ctrl_set = type_and_label_to_ctrl_model('link', p_label).objects.filter(**query_dict).first()
            return ctrl_set

        except ObjectDoesNotExist:
            return None

    def link_init(self, p_label, frontend_data):
        start = frontend_data['Start']
        end = frontend_data['End']
        if self.check_exist(start=start, end=end, p_label=p_label):
            return self
        else:
            self.base_create(frontend_data)
            return self

    def base_create(self, data):
        self._ctrl = self.ctrl_class(
            ItemId=self.id,
            ItemType='link',
            PrimaryLabel=self.p_label,
            CreateType=data['CreateType'],
            CreateUser=self.user_id,
            PropsWarning={}
        )
        self._link = Relationship(data['Start'], self.p_label, data['End'])
        self.graph_link_update(data)

    def check_exist(self, start, end, p_label):
        ctrl_set = self.query_by_node(p_label, start, end)
        ctrl = ctrl_set.first()
        if ctrl:
            self._ctrl = ctrl
            return True
        else:
            return False

    def graph_link_update(self, data):
        neo_prop = {}
        # 注意这里是ctrl
        fields = [field for field in self.ctrl_class._meta.fields
                  if not field.auto_created and field.model.__name__ == self.ctrl_class.__name__]
        for field in fields:
            if field.name in data:
                neo_prop[field.name] = data[field.name]
            else:
                neo_prop[field.name] = getattr(self.ctrl, field.name)
        neo_prop['IsUsed'] = self.ctrl.IsUsed
        self.link.update(neo_prop)
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
        cls.ctrl_class.objects.bulk_update(ctrl_list)
        collector.tx.commit()
        return True

    @classmethod
    def bulk_save_create(cls, model_list, collector: NeoSet):
        ctrl_list = [link.ctrl for link in model_list]
        cls.ctrl_class.objects.bulk_create(ctrl_list)
        collector.tx.commit()
        return True
