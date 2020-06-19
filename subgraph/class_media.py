import mimetypes
from typing import Optional

import oss2

import tools.global_const
from base_api.interface_frontend import MediaInfoFrontend
from subgraph.class_base import BaseNodeModel
from subgraph.models import MediaCtrl, MediaInfo
from tools import base_tools
from tools.aliyun import authorityKeys
from tools.redis_process import mime_type_query, mime_type_set
from tools.global_const import item_id


class MediaModel(BaseNodeModel):
    access_key_id = authorityKeys["developer"]["access_key_id"]
    access_key_secret = authorityKeys["developer"]["access_key_secret"]
    bucket_name = authorityKeys["developer"]["bucket_name"]
    endpoint = authorityKeys["developer"]["endpoint"]
    auth = oss2.Auth(access_key_id, access_key_secret)
    oss_manager = oss2.Bucket(auth, endpoint, bucket_name=bucket_name, connect_timeout=10000)

    def __init__(self, _id: item_id, user_id: int, _type="media", collector=base_tools.NeoSet()):
        super().__init__(_id, user_id, _type, collector)
        self._ctrl: Optional[MediaCtrl] = None
        self._info: Optional[MediaInfo] = None
        self.info_class = MediaInfo
        self.ctrl_class = MediaCtrl

    # ---------------- update ----------------

    def _ctrl_update_special_hook(self, frontend_data: MediaInfoFrontend):
        """
        用户能改变权限和文件位置
        :param frontend_data: 前端的数据
        :return:
        """
        super()._ctrl_update_special_hook(frontend_data)
        file_name = frontend_data.FileName
        if self.ctrl.FileName != file_name:
            if self.oss_manager.object_exists(file_name):
                self.ctrl.FileName = file_name
                self.ctrl.Format = file_name.split('.')[1]
                self.ctrl.Thumb = ''  # todo 缩略图生成
            else:
                self.error_output(FileNotFoundError, '远端服务器没有文件')
        else:
            pass

    def _info_update_special_hook(self, data):
        """
        特别update过程 暂时没有将来把缩略图加入
        :param data:
        :return:
        """
        pass
    # ---------------- function ----------------

    def save(self, history_save=True, neo4j_save=True, es_index_text=True):
        super().save(history_save, neo4j_save, es_index_text)

    def check_remote_file(self) -> bool:
        """
        查看远端文件
        :return: bool
        """
        return self.oss_manager.object_exists(self.ctrl.FileName)

    def move_remote_file(self, new_location):
        """
        移动远端文件 会修改ctrl
        :param new_location:
        :return:
        """
        if self.check_remote_file():
            result = self.oss_manager.copy_object(self.bucket_name, self.ctrl.FileName, new_location)
            if result.status == 200:
                self.ctrl.FileName = new_location
                return True
        else:
            raise FileNotFoundError

    @staticmethod
    def get_media_label(file_format: str) -> str:
        """
        注意返回的是json, image之类的
        :param file_format: str such as 'jpg'
        :return: mime_type: str such as 'json'
        """
        file_format = file_format.lower()
        special_media_type = {
            'text/markdown': 'markdown'
        }
        mime_type_dict = mime_type_query()
        if mime_type_dict == {}:
            mime_type_dict = mimetypes.read_mime_types(tools.global_const.basePath + "/tools/mime.types")
            mime_type_set(mime_type_dict)

        if "." + file_format in mime_type_dict:
            mime_type = str(mime_type_dict["." + file_format])
            media_tuple = mime_type.split('/')
            if media_tuple[0] == 'application':
                result = media_tuple[1]
            else:
                result = media_tuple[0]
            if mime_type in special_media_type:
                result = special_media_type[mime_type]
            return result
        else:
            return "unknown"
