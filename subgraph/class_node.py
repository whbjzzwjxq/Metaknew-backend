import json
from typing import *

from django.core.exceptions import ObjectDoesNotExist

from base_api.interface_frontend import NodeInfoFrontend
from record.exception import UnAuthorizationError
from subgraph.class_base import BaseNodeModel
from subgraph.class_media import MediaModel
from subgraph.models import NodeCtrl, MediaCtrl, NodeInfo, DocumentCtrl
from tools import base_tools


class NodeModel(BaseNodeModel):
    info_class = NodeInfo
    ctrl_class = NodeCtrl

    def __init__(self, _id: int, user_id: int, _type='node', collector=base_tools.NeoSet()):
        super().__init__(_id, user_id, _type, collector)
        self._ctrl: Optional[Type[NodeCtrl]] = None
        self._info: Optional[Type[NodeInfo]] = None

    # ---------------- create ----------------

    def create(self, frontend_data: NodeInfoFrontend, create_type: str):
        super().create(frontend_data, create_type)
        self._ctrl_init(frontend_data.PrimaryLabel, create_type)
        self._info_init(frontend_data.PrimaryLabel)
        self._graph_node_init()
        self.ctrl_update_by_user(frontend_data)
        self.update_by_user(frontend_data, create_type)
        self.graph_node_update()
        return self

    # ---------------- update ----------------

    def ctrl_update_by_user(self, frontend_data: NodeInfoFrontend):
        """
        用户能够改变权限的信息
        :param frontend_data: 前端传回的数据
        :return:
        """
        super().ctrl_update_by_user(frontend_data)
        # 更新contributor
        if self.is_create:
            self.ctrl.Contributor = []
        else:
            if self.user_id not in self.ctrl.Contributor:
                self.ctrl.Contributor.append(self.user_id)

    def info_special_update(self, frontend_data: NodeInfoFrontend):
        """
        特殊的更新内容
        :param frontend_data: 前端数据
        :return:
        """
        if type(frontend_data.MainPic) == str:
            self.main_image_setter(frontend_data.MainPic)
        if frontend_data.IncludedMedia:
            self.media_setter(frontend_data.IncludedMedia)
        self.name_checker(name=frontend_data.Name)

    def name_checker(self, name):
        """
        查询是否有类似名字的节点
        :return:
        """
        similar_node = NodeInfo.objects.filter(Name=name)
        if len(similar_node) > 0:
            name_list = json.dumps([node.ItemId for node in similar_node])
            self.warn_add(field_name='Name', warn_type='similar_name: [' + name_list + ']')
        else:
            pass

    def main_image_setter(self, media_name) -> bool:
        """
        设置主图片
        :param media_name: media的储存路径
        :return:
        """
        media_manager = MediaModel.oss_manager
        if media_manager.object_exists(media_name):
            self.info.MainPic = media_name
            return True
        else:
            self.warn_add(field_name='MainPic', warn_type='empty_prop')
            return False

    def media_setter(self, media_list):
        """
        设置包含的媒体
        :param media_list: list of media_id
        :return: self
        """
        if self.editable:
            available_media = []
            warn = []
            for media_id in media_list:
                _id = int(media_id)
                if _id in self.info.IncludedMedia:
                    available_media.append(_id)
                else:
                    try:
                        record = MediaCtrl.objects.get(pk=_id)
                        if record:
                            available_media.append(_id)
                    except ObjectDoesNotExist:
                        warn.append(_id)
            self.info.IncludedMedia = available_media

            if warn:
                self.warn_add(field_name="IncludedMedia", warn_type="media_no_exist: " + str(warn))
                return False, "media_no_exist: " + str(warn)
            else:
                return True, ''
        else:
            self.error_output(UnAuthorizationError, '没有编辑权限', strict=False)
            return False

    # ---------------- function ----------------

    def delete(self):
        # todo 节点删除 level: 2
        pass

    def merge(self, node1):
        # todo 节点merge level: 2
        pass

    def save(self, history_save=True, neo4j_save=True, es_index_text=True, es_index_node=True):
        super().save(history_save, neo4j_save, es_index_text)

    @classmethod
    def bulk_save_create(cls, model_list, collector):
        result = super().bulk_save_create(model_list, collector)
        return result

    @classmethod
    def bulk_save_update(cls, model_list, collector):
        result = super().bulk_save_update(model_list, collector)
        return result

    def node_index(self):
        ctrl: NodeCtrl = self.ctrl
        info: NodeInfo = self.info
        if not info.Language:
            lang = 'auto'
        else:
            lang = info.Language
        body = {
            "id": self.id,
            "type": self.type,
            "PrimaryLabel": ctrl.PrimaryLabel,
            "Language": lang,
            "CreateUser": ctrl.CreateUser,
            "UpdateTime": ctrl.UpdateTime,
            "MainPic": info.MainPic,
            "Alias": info.Alias,
            "Name_zh": "",
            "Name_en": "",
            "Name_auto": info.Name,
            "Tags": {
                "Labels": info.Labels,
                "Topic": info.Topic
            },
            "Level": {
                "Imp": ctrl.Imp,
                "HardLevel": ctrl.HardLevel,
                "Useful": ctrl.Useful,
                "TotalTime": ctrl.TotalTime
            },
            "IsUsed": ctrl.IsUsed,
            "IsCommon": ctrl.IsCommon,
            "IsOpenSource": ctrl.IsOpenSource
        }
        for lang in ['zh', 'en']:
            if lang in info.Translate:
                body["Name_%s" % lang] = info.Translate[lang]

        return body

    def handle_for_frontend(self):
        return {
            'Info': self.info.to_dict(exclude=None),
            'Ctrl': self.ctrl.to_dict(exclude=None)
        }


class DocumentNodeModel(NodeModel):
    ctrl_class = DocumentCtrl
