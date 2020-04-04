import json
from typing import *

from django.core.exceptions import ObjectDoesNotExist

from base_api.interface_frontend import NodeInfoFrontend
from record.exception import UnAuthorizationError
from subgraph.class_base import BaseNodeModel
from subgraph.class_media import MediaModel
from subgraph.models import NodeCtrl, MediaCtrl, NodeInfo
from tools import base_tools
from tools.global_const import item_id


class NodeModel(BaseNodeModel):
    info_class = NodeInfo
    ctrl_class = NodeCtrl

    def __init__(self, _id: item_id, user_id: int, _type='node', collector=base_tools.NeoSet()):
        super().__init__(_id, user_id, _type, collector)
        self._ctrl: Optional[Type[NodeCtrl]] = None
        self._info: Optional[Type[NodeInfo]] = None

    # ---------------- update ----------------

    def _ctrl_update_special_hook(self, frontend_data: NodeInfoFrontend, create_type: str = 'USER'):
        """
        用户能够改变权限的信息
        :param frontend_data: 前端传回的数据
        :return:
        """
        super()._ctrl_update_special_hook(frontend_data)
        # 更新contributor
        if self.is_create:
            self.ctrl.Contributor = []
        else:
            if self.user_id not in self.ctrl.Contributor:
                self.ctrl.Contributor.append(self.user_id)

    def _info_update_special_hook(self, frontend_data: NodeInfoFrontend):
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
                return warn
            else:
                return []
        else:
            self.error_output(UnAuthorizationError, '没有编辑权限', strict=False)
            return False

    def handle_for_frontend(self):
        result = super().handle_for_frontend()
        info: NodeInfo = self.info
        result['Ctrl']['Imp'] = info.BaseImp
        result['Ctrl']['HardLevel'] = info.BaseHardLevel
        result['Ctrl']['Useful'] = info.BaseUseful
        return result

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
