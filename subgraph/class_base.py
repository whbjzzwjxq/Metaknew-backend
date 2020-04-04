import datetime
from typing import Optional, Type

import numpy as np
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, DatabaseError
from django.db.models import Field
from django.forms.models import model_to_dict
from py2neo.data import Node as NeoNode
from py2neo.database import TransactionError

from base_api.interface_frontend import InfoFrontend, QueryObject, CommonInfoFrontend
from es_module.logic_class import bulk_add_text_index
from record.exception import UnAuthorizationError, ErrorForWeb
from record.logic_class import ItemHistory
from subgraph.models import BaseInfo, BaseCtrl, NodeInfo, MediaInfo, NodeCtrl, MediaCtrl, PublicItemCtrl, FragmentInfo, \
    FragmentCtrl
from tools.base_tools import NeoSet
from tools.global_const import item_id, item_type


def field_check(_func):
    def wrapped(self, field: Field, new_prop, old_prop):
        warn_type = ''
        if isinstance(new_prop, str) and len(new_prop) > 1024:
            warn_type = 'toolong_str'

        if isinstance(new_prop, list) and len(new_prop) > 128:
            warn_type = 'toolong_list'

        if isinstance(new_prop, dict) and len(new_prop) > 128:
            warn_type = 'toolong_dict'

        if not bool(new_prop):
            warn_type = 'empty_prop'

        # 这里主要是针对JSONField 和 ArrayField
        if type(new_prop) != type(old_prop):
            warn_type = 'error_type'
        if warn_type != '':
            self.warn_add(field.name, warn_type)
        return _func(self, field, new_prop, old_prop)

    return wrapped


class FieldWarn:

    def __init__(self, fn, wt, ui):
        """
        变量名都是缩写
        :param fn: field_name
        :param wt: warn_type
        :param ui: user_id
        """
        self.field_name = fn
        self.warn_type = wt
        self.user_id = ui

    @property
    def to_dict(self):
        return {
            'fn': self.field_name,
            'wt': self.warn_type,
            'ui': self.user_id
        }

    @staticmethod
    def dict_to_class(data):
        return FieldWarn(**data)


class BaseModel:
    """
    提供的方法
    query_ctrl, query_info, query_node, query_authority, auth_create, info_update
    """
    info_class = BaseInfo
    ctrl_class = BaseCtrl

    def __init__(self, _id: item_id, user_id: item_id, _type: item_type, collector=NeoSet()):
        self._info: Optional[Type[BaseInfo]] = None
        self._ctrl: Optional[Type[BaseCtrl]] = None
        self._history: Optional[ItemHistory] = None

        # 以下是值
        self.collector = collector  # neo4j连接池
        self.id = int(_id)  # _id
        self.user_id = int(user_id)  # 操作用户的id
        self.type = _type  # model type
        self.frontend_id = ''  # 前端的id
        self.is_create = False  # 是否是创建状态

    @property
    def ctrl(self):
        if self._ctrl is None:
            try:
                self._ctrl = self.ctrl_class.objects.get(pk=self.id)
            except ObjectDoesNotExist:
                raise ObjectDoesNotExist()
        return self._ctrl

    @property
    def info(self):
        if self._info is None:
            try:
                self._info = self.info_class.objects.get(pk=self.id)
            except ObjectDoesNotExist:
                raise ObjectDoesNotExist()
        return self._info

    @property
    def history(self):
        if self._history is None:
            self._history = ItemHistory(user_id=self.user_id, query_object=self.query_object)
        return self._history

    @property
    def editable(self):
        if not self.ctrl:
            return False
        else:
            return self.ctrl.CreateUser == self.user_id

    @property
    def p_label(self):
        label = self.ctrl.PrimaryLabel
        if label is not '':
            return label
        else:
            return 'default'

    @property
    def query_object(self) -> QueryObject:
        return QueryObject(id=self.id, type=self.type, pLabel=self.p_label)

    # ----------------- init ----------------

    def _ctrl_init(self, p_label: str, create_type: str):
        self._ctrl = self.ctrl_class(
            ItemId=self.id,
            ItemType=self.type,
            CreateUser=self.user_id,
            CreateType=create_type,
            PrimaryLabel=p_label,
            PropsWarning=[]
        )

    def _info_init(self):
        self._info = self.info_class(
            ItemId=self.id,
            ItemType=self.type
        )

    def _special_init(self, *args, **kwargs):
        pass

    # ----------------- function ----------------

    def warn_add(self, field_name, warn_type):
        self.ctrl.PropsWarning.append(FieldWarn(fn=field_name, wt=warn_type, ui=self.user_id).to_dict)

    def error_output(self, error: Type[BaseException], description: str, is_dev=False, strict=True):
        """
        捕获错误
        :param error: 错误object
        :param description: 错误描述
        :param is_dev: 这个原因是否是开发模式 dev=False会传回前端
        :param strict: 这个错误是否是严格的 如果是会raise
        :return:
        """
        output = {
            'type': self.type,
            'name': error.__name__,
            'id': self.id,
            'user': self.user_id
        }
        error = ErrorForWeb(error=error, description=description, content=output, is_dev=is_dev, is_error=strict)
        if not strict:
            return error
        else:
            error.raise_error()

    @field_check
    def __update_prop(self, field, new_prop, old_prop):
        if new_prop != old_prop:
            setattr(self.info, field.name, new_prop)
        else:
            pass

    def output_table_create(self):
        return self.ctrl, self.info, self.history

    # ----------------- create&update ----------------

    def create(self, frontend_data: Type[InfoFrontend], create_type):
        """
        :param frontend_data:
        :param create_type: 创建方式
        :return:
        """
        self.is_create = True
        self.frontend_id = frontend_data.id
        self._ctrl_init(frontend_data.PrimaryLabel, create_type)
        self._info_init()
        self._special_init(frontend_data, create_type)
        self.update(frontend_data, create_type)
        return self

    def update(self, frontend_data: Type[InfoFrontend], create_type):
        """
        三个过程 ctrl_update info_update special_update
        :param frontend_data:
        :param create_type:
        :return:
        """
        self.ctrl_update_hook(frontend_data, create_type)
        self.info_update_hook(frontend_data, create_type)
        self._update_special_hook(frontend_data, create_type)
        return self

    def ctrl_update_hook(self, frontend_data: Type[InfoFrontend], create_type: str = 'USER'):
        """
        model通用过程
        :param frontend_data:
        :param create_type:
        :return:
        """
        self.ctrl.PrimaryLabel = frontend_data.PrimaryLabel
        self.ctrl.CreateType = create_type
        self._ctrl_update_special_hook(frontend_data)

    def _ctrl_update_special_hook(self, frontend_data: Type[InfoFrontend]):
        """
        子类单独过程
        :param frontend_data:
        :return:
        """
        pass

    def info_update_hook(self, frontend_data: Type[InfoFrontend], create_type: str):
        """
        更新info的过程 special -> props -> neo object
        :param frontend_data: 前端传回的过程
        :param create_type: 更新的方式
        :return: self
        """

        if self.editable:
            if not self.is_create:
                name = self.info.Name + str(datetime.datetime.now())
                content = model_to_dict(self.info, exclude=self.info.prop_not_to_dict())
                self.history.record_from_item(content=content, name=name)
            # 特殊的属性update
            fields = self.info_class._meta.fields
            fields = [field for field in fields
                      if not field.auto_created and field.name not in self.info_class.special_update()]
            # field属性update
            for field in fields:
                old_prop = getattr(self.info, field.name)
                new_prop = getattr(frontend_data, field.name, None)
                if new_prop is None:
                    new_prop = field.default
                    # 如果是dict list等构造类 实例化
                    if isinstance(new_prop, type):
                        new_prop = new_prop()
                self.__update_prop(field, new_prop, old_prop)
            self._info_update_special_hook(frontend_data)
            return True
        else:
            return self.error_output(UnAuthorizationError, '没有权限')

    def _info_update_special_hook(self, data):
        pass

    def _update_special_hook(self, frontend_data: Type[InfoFrontend], create_type):
        pass

    def save(self, history_save=True, neo4j_save=True):
        """
        整体的save过程
        :return: None
        """
        # try:
        with transaction.atomic():
            self.ctrl.save()
            self.info.save()
            if history_save and not self.is_create:
                self.history.current_record.save()
        # except DatabaseError:
        #     raise DatabaseError
        try:
            if neo4j_save:
                self.collector.tx.commit()
        except TransactionError:
            raise TransactionError

    @classmethod
    def bulk_save_create(cls, model_list, collector):
        """
        create的时候集体保存
        :param model_list: 逻辑的model_list
        :param collector: neo4j连接池
        :return:
        """
        output_model = np.array([model.output_table_create() for model in model_list])
        try:
            if len(output_model) > 0:
                with transaction.atomic():
                    ctrl_model_list = list(output_model[:, 0])
                    cls.ctrl_class.objects.bulk_create(ctrl_model_list)
                    info_model_list = list(output_model[:, 1])
                    cls.info_class.objects.bulk_create(info_model_list)
                    frontend_id_current_id_map = {model.frontend_id: model.id for model in model_list}
                    return frontend_id_current_id_map
            else:
                return None
        except DatabaseError or TransactionError as e:
            ErrorForWeb(e, description='数据库错误').raise_error()

    @classmethod
    def bulk_save_update(cls, model_list, collector):
        """
        update的时候集体保存
        :param model_list: 逻辑的model_list
        :param collector: neo4j连接池
        :return:
        """
        output_model = np.array([model.output_table_create() for model in model_list])
        try:
            if len(output_model) > 0:
                with transaction.atomic():
                    ctrl_model_list = list(output_model[:, 0])
                    cls.ctrl_class.objects.bulk_update(ctrl_model_list, ctrl_model_list[0].saved_fields())
                    info_model_list = list(output_model[:, 1])
                    cls.info_class.objects.bulk_update(info_model_list, info_model_list[0].saved_fields())
                    history_model_list = [his for his in output_model[:, 2]]
                    ItemHistory.bulk_save(history_model_list)
                return True
        except DatabaseError or TransactionError:
            return None

    def handle_for_frontend(self):
        result = {
            'Info': self.info.to_dict(exclude=None),
            'Ctrl': self.ctrl.to_dict(exclude=None)
        }
        result['Info']['IsUsed'] = self.ctrl.IsUsed
        return result


class PublicItemModel(BaseModel):
    """
    公开的可以检索的内容
    """

    ctrl_class = PublicItemCtrl

    def __init__(self, _id: item_id, user_id: item_id, _type: item_type, collector=NeoSet()):
        super().__init__(_id, user_id, _type, collector)
        self._ctrl: Optional[Type[PublicItemCtrl]] = None

    def _ctrl_update_special_hook(self, frontend_data: CommonInfoFrontend):
        """
        用户能够改变权限的信息
        :param frontend_data: 前端传回的数据
        :return:
        """
        if self.editable:
            for prop in self.ctrl_class.props_update_by_user():
                value = getattr(frontend_data, prop, None)
                if value is not None:
                    setattr(self.ctrl, prop, value)
                else:
                    pass
            return True
        else:
            return self.error_output(UnAuthorizationError, '没有权限')

    def editable(self):
        if not self.ctrl:
            return False
        else:
            return self.ctrl.CreateUser == self.user_id or self.ctrl.IsOpenSource

    def text_index(self):
        ctrl: PublicItemCtrl = self.ctrl
        info: BaseInfo = self.info
        language_list = list(self.info.Description.keys())
        if len(language_list) > 0:
            language = language_list[0]
            description = self.info.Description[language]
        else:
            language = "auto"
            description = ""

        body = {
            "id": self.id,
            "type": self.type,
            "PrimaryLabel": self.p_label,
            "Language": language,
            "CreateUser": ctrl.CreateUser,
            "UpdateTime": str(ctrl.UpdateTime),
            "MainPic": getattr(info, 'MainPic', ''),
            "Alias": getattr(info, 'Alias', []),
            "Hot": ctrl.Hot,
            "Name": {
                "zh": "",
                "en": "",
                "auto": info.Name
            },
            "Description": {
                "zh": "",
                "en": "",
                "auto": description
            },
            "Tags": {
                "UserLabels": info.Labels,
                "Labels": ctrl.Labels,
                "Topic": getattr(info, 'Topic', [])
            },
            "Num": {
                "NumStar": ctrl.NumStar,
                "NumShared": ctrl.NumShared,
                "NumGood": ctrl.NumGood,
                "NumBad": ctrl.NumBad,
            },
            "Auth": {
                "IsUsed": ctrl.IsUsed,
                "IsCommon": ctrl.IsCommon,
                "IsOpenSource": ctrl.IsOpenSource
            }
        }
        for lang in body["Description"]:
            if lang in info.Description:
                body["Description"][lang] = info.Description[lang]

        for lang in ['zh', 'en']:
            if lang in info.Translate:
                body["Name"]["%s" % lang] = info.Translate[lang]
        return body

    def save(self, history_save=True, neo4j_save=False, es_index_text=True):
        super().save(history_save, neo4j_save)
        if es_index_text:
            bulk_add_text_index([self])

    @classmethod
    def bulk_save_create(cls, model_list, collector):
        result = super().bulk_save_create(model_list, collector)
        if result is not None:
            bulk_add_text_index(model_list)
        return result

    @classmethod
    def bulk_save_update(cls, model_list, collector):
        result = super().bulk_save_update(model_list, collector)
        if result:
            bulk_add_text_index(model_list)
        return result

    def handle_for_frontend(self):
        result = super().handle_for_frontend()
        result['Info']['IsCommon'] = self.ctrl.IsCommon
        result['Info']['IsOpenSource'] = self.ctrl.IsOpenSource
        return result


class BaseNodeModel(PublicItemModel):
    """
    在图数据库里作为节点的内容
    """

    def __init__(self, _id: item_id, user_id: item_id, _type: item_type, collector=NeoSet()):
        super().__init__(_id, user_id, _type, collector)
        self._graph_node: Optional[NeoNode] = None
        self._info: Optional[Type[NodeInfo], Type[MediaInfo]] = None
        self._ctrl: Optional[Type[NodeCtrl], Type[MediaCtrl]] = None

    def _special_init(self, frontend_data: Type[InfoFrontend], create_type):
        self._graph_node_init()

    def _update_special_hook(self, frontend_data: Type[InfoFrontend], create_type):
        self.graph_node_update()

    @property
    def graph_node(self):
        if not self._graph_node:
            self._graph_node = self.collector.Nmatcher.match(_id=self.id).first()
            if self._graph_node is None:
                raise ObjectDoesNotExist()
        return self._graph_node

    def _graph_node_init(self):
        node = NeoNode(self.p_label, self.type)
        node["_id"] = self.id
        node["_type"] = self.type
        node["_label"] = self.p_label
        node.__primarylabel__ = self.p_label
        node.__primarykey__ = "_id"
        node.__primaryvalue__ = self.id
        self._graph_node = node
        self.collector.tx.create(self._graph_node)

    def graph_node_update(self):
        # 更新info
        neo_prop = {
            "Name": self.info.Name,
            "NumGood": self.ctrl.NumGood,
            "NumBad": self.ctrl.NumBad,
            "CreateType": self.ctrl.CreateType,
        }
        self.graph_node.update(neo_prop)
        # 更新ctrl
        for label in self.ctrl_class.props_update_by_user():
            ctrl_value = getattr(self.ctrl, label)
            if ctrl_value:
                self.graph_node.add_label(label)
            else:
                if self.graph_node.has_label(label):
                    self.graph_node.remove_label(label)
        # 更新labels
        no_empty_labels = [label for label in self.info.Labels if label is not '']
        self.graph_node.update_labels(no_empty_labels)
        self.collector.tx.push(self.graph_node)

    def save(self, history_save=True, neo4j_save=True, es_index_text=True):
        super().save(history_save, neo4j_save, es_index_text)

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


class FragmentModel(BaseModel):
    info_class = FragmentInfo
    ctrl_class = FragmentCtrl
