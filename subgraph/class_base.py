from typing import Optional, Type, Union

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max
from py2neo import Node as NeoNode

from record.logic_class import field_check, UnAuthorizationError, RewriteMethodError
from record.models import WarnRecord, VersionRecord
from tools.base_tools import NeoSet, type_label_to_info_model, ctrl_dict, check_is_user_made, get_update_props

str_types = Union['node', 'link', 'course', 'media']


class BaseModel:
    """
    提供的方法
    query_ctrl, query_info, query_node, query_authority, auth_create, info_update
    """

    def __init__(self, _id: int, user_id: int, _type: str_types, collector=NeoSet()):
        default = 'default'
        self.node: Optional[NeoNode] = None
        self.info: Optional[type_label_to_info_model(_type, default)] = None
        self.ctrl: Optional[ctrl_dict[_type]] = None
        self.warn: Optional[WarnRecord] = None
        self.history: Optional[VersionRecord] = None
        self.history_list = VersionRecord.objects.none()

        # 以下是值
        self.collector = collector  # neo4j连接池
        self.id = _id  # _id
        self.user_id = int(user_id)
        self.type = _type
        self.p_label = ""  # 主标签

        self.is_create = False  # 是否是创建状态
        self.is_user_made = check_is_user_made(user_id)

    def error_output(self, error: Type[BaseException], reason):
        output = {
            'type': self.type,
            'name': error.__name__,
            'id': self.id,
            'user': self.user_id,
            'reason': reason
        }
        raise error(output)

    # ----------------- create ----------------

    def history_create(self):
        if self.type != 'link' and not self.is_create:
            self.query_history()
            if self.history_list:
                new_version = self.history_list.aggregate(Max('VersionId'))
                if new_version['VersionId__max']:
                    new_version_id = new_version['VersionId__max'] + 1
                else:
                    new_version_id = 1
                    self.error_output(ObjectDoesNotExist, '历史文件不存在')
            else:
                new_version_id = 1

            self.history = VersionRecord(
                CreateUser=self.user_id,
                SourceId=self.id,
                SourceType=self.type,
                SourceLabel=self.p_label,
                VersionId=new_version_id,
                Content={}
            )
        else:
            pass

    def warn_create(self):
        self.query_warn()

    # ----------------- query ----------------

    def query_base(self):
        """
        查询info,ctrl,text, authority的内容 也就是前端 索引的基本内容
        :return:
        """
        result = self.query_ctrl()
        result &= self.query_info()
        return result

    def query_ctrl(self) -> bool:
        if not self.ctrl:
            try:
                self.ctrl = ctrl_dict[self.type].objects.get(pk=self.id)
                if self.ctrl.PrimaryLabel:
                    self.p_label = self.ctrl.PrimaryLabel
                return True
            except ObjectDoesNotExist:
                self.error_output(ObjectDoesNotExist, 'Ctrl不存在')
        else:
            self.p_label = self.ctrl.PrimaryLabel
            return True

    def query_info(self) -> bool:
        if not self.ctrl:
            result = self.query_ctrl()
            if result:
                return self.query_info()
        elif not self.info:
            try:
                self.info = type_label_to_info_model(self.type, self.p_label).objects.get(pk=self.id)
                return True
            except ObjectDoesNotExist:
                self.error_output(ObjectDoesNotExist, 'Info不存在,可能是标签有误')
        else:
            return True

    def query_history(self):
        if self.type != 'link':
            self.history_list = VersionRecord.objects.filter(SourceType=self.type, SourceId=self.id)
        else:
            self.error_output(TypeError, 'link没有历史记录')

    def query_warn(self):
        remote_warn = WarnRecord.objects.filter(SourceType=self.type, SourceId=self.id)
        if remote_warn:
            self.warn = remote_warn.first()
            # 重新更新
            self.warn.WarnContent = []
        else:
            self.warn = WarnRecord(
                SourceId=self.id,
                SourceType=self.type,
                SourceLabel=self.p_label,
                CreateUser=self.user_id,
                BugType='Warn',
                WarnContent=[]
            )

    # ----------------- create ----------------

    def _ctrl_create(self):
        self.ctrl = ctrl_dict[self.type]()
        self.ctrl.ItemId = self.id
        self.ctrl.ItemType = self.type
        self.ctrl.PrimaryLabel = self.p_label
        self.ctrl.Is_UserMade = self.is_user_made
        self.ctrl.Is_Used = True
        self.ctrl.Is_Common = True
        self.ctrl.Is_Shared = False
        self.ctrl.Is_OpenSource = False
        self.ctrl.CreateUser = self.user_id

    def _info_create(self):
        if not self.p_label:
            self.error_output(AttributeError, '主标签不能为空')
        else:
            self.info = type_label_to_info_model(self.type, self.p_label)()
            self.info.PrimaryLabel = self.p_label
            self.info.ItemId = self.id
            return self

    # ----------------- update ----------------

    @field_check
    def __update_prop(self, field, new_prop, old_prop):
        if new_prop != old_prop:
            setattr(self.info, field.name, new_prop)
            self._history_update(field.name, old_prop)
        else:
            pass

    def _history_update(self, prop, value):
        if self.type != 'link' and not self.is_create:
            try:
                self.history.Content.update({prop: value})
            except KeyError or AttributeError as e:
                self.error_output(e, '更新历史文件出错')

    def info_update(self, data):
        """
        更新info的过程 special -> props -> neo object
        :param data:
        :return:
        """
        # todo authority
        if self.user_id == self.ctrl.CreateUser:
            self.query_warn()
            self.history_create()
            self.query_info()

            self.info_special_update(data)
            if 'Text' in data:
                if data["Text"]:
                    self.info.Text = data["Text"]
                else:
                    self.info.Text = {"auto": ""}
            needed_props = get_update_props(self.type, self.p_label)
            for field in needed_props:
                old_prop = getattr(self.info, field.name)
                if field.name in data:
                    new_prop = data[field.name]
                else:
                    new_prop = field.default
                    # 如果是dict list等构造类 实例化
                    if isinstance(new_prop, type):
                        new_prop = new_prop()
                self.__update_prop(field, new_prop, old_prop)
                # todo field resolve
                self.graph_update(data)
        else:
            self.error_output(UnAuthorizationError, '没有编辑权限')

    def info_special_update(self, data):
        self.error_output(RewriteMethodError, '方法需要重写')

    def graph_update(self, data):
        """
        更新图数据库里的内容
        :return:
        """
        self.error_output(RewriteMethodError, '方法需要重写')

    def text_index(self):
        if len(list(self.info.Text.keys())) > 0:
            language = list(self.info.Text.keys())[0]
            text = self.info.Text[language]
        else:
            language = "auto"
            text = ""
        if self.type == 'link':
            hot = self.info.Hot
            star = self.info.Star
        else:
            hot = self.ctrl.Hot
            star = self.ctrl.Star

        body = {
            "id": self.id,
            "type": self.type,
            "PrimaryLabel": self.p_label,
            "Language": language,
            "Name": self.info.Name,
            "Tags": {
                "Labels": self.info.Labels,
            },
            "Text": {
                "zh": "",
                "en": "",
                "auto": text
            },
            "Hot": hot,
            "Star": star
        }
        for lang in body["Text"]:
            if lang in self.info.Text:
                body["Text"][lang] = self.info.Text[lang]
        return body

    def output_table_create(self):
        return self.ctrl, self.info, self.warn, self.history

    def handle_for_frontend(self):
        """
        前端所用格式
        :return:
        """
        unused_props = ["CountCacheTime",
                        "Is_Used",
                        "Is_UserMade",
                        "Is_Common",
                        "Is_Shared",
                        "Is_OpenSource",
                        "ImportMethod",
                        "CreateTime",
                        "ItemId",
                        "ItemType",
                        "CreateUser",
                        "Format",
                        "History",
                        "MediaId",
                        ]
        self.query_base()
        ctrl_fields = self.ctrl._meta.get_fields()
        output_ctrl_dict = {field.name: getattr(self.ctrl, field.name)
                            for field in ctrl_fields if field.name not in unused_props}

        info_fields = self.info._meta.get_fields()
        output_info_dict = {field.name: getattr(self.info, field.name)
                            for field in info_fields if field.name not in unused_props}
        output_info_dict["id"] = self.id
        output_info_dict["type"] = self.type

        output_ctrl_dict["$_Is_Common"] = self.ctrl.Is_Common
        output_ctrl_dict["$_Is_OpenSource"] = self.ctrl.Is_OpenSource
        output_ctrl_dict["$_IsShared"] = self.ctrl.Is_Shared
        result = {
            "Ctrl": output_ctrl_dict,
            "Info": output_info_dict,
        }
        return result
