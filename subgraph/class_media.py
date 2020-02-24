import mimetypes
from typing import Optional

import oss2

import tools.global_const
from subgraph.class_base import BaseNodeModel
from subgraph.models import MediaCtrl, MediaInfo
from tools import base_tools
from tools.aliyun import authorityKeys
from tools.redis_process import mime_type_query, mime_type_set


class MediaModel(BaseNodeModel):
    access_key_id = authorityKeys["developer"]["access_key_id"]
    access_key_secret = authorityKeys["developer"]["access_key_secret"]
    bucket_name = authorityKeys["developer"]["bucket_name"]
    endpoint = authorityKeys["developer"]["endpoint"]
    auth = oss2.Auth(access_key_id, access_key_secret)
    oss_manager = oss2.Bucket(auth, endpoint, bucket_name=bucket_name, connect_timeout=10000)

    def __init__(self, _id: int, user_id: int, _type="media", collector=base_tools.NeoSet()):
        super().__init__(_id, user_id, _type, collector)
        self._ctrl: Optional[MediaCtrl] = None
        self._info: Optional[MediaInfo] = None
        self.info_class = MediaInfo
        self.ctrl_class = MediaCtrl

    # ---------------- create ----------------

    def create(self, frontend_data):
        """
        base_media_create的别名
        :param frontend_data: 前端的数据
        :return:
        """
        return self.create(frontend_data)

    def create(self, frontend_data: dict):
        super().create(frontend_data)
        assert "Name" in frontend_data
        assert "PrimaryLabel" in frontend_data
        assert "CreateType" in frontend_data
        assert 'FileName' in frontend_data
        self._ctrl_init(frontend_data["PrimaryLabel"], frontend_data["CreateType"])
        self.ctrl_update_by_user(frontend_data)
        self.history().add_record()
        self._info_init(frontend_data["PrimaryLabel"])
        self._graph_node_create()
        self.update_by_user(frontend_data)
        return self

    # ---------------- update ----------------

    def ctrl_update_by_user(self, frontend_data):
        """
        用户能改变权限和文件位置
        :param frontend_data: 前端的数据
        :return:
        """
        super().ctrl_update_by_user(frontend_data)
        file_name = frontend_data['FileName']
        if self.ctrl.FileName != file_name:
            if self.oss_manager.object_exists(file_name):
                self.ctrl.FileName = file_name
                self.ctrl.Format = file_name.split('.')[1]
                self.ctrl.Thumb = ''  # todo 缩略图生成
            else:
                self.error_output(FileNotFoundError, '远端服务器没有文件')
        else:
            pass

    def info_special_update(self, data):
        """
        特别update过程 暂时没有
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
    def get_media_type(file_format) -> str:
        """
        注意返回的是完整的mime_type不是json, image之类的
        :param file_format: str such as 'jpg'
        :return: mime_type: str such as 'application/json'
        """
        mime_type_dict = mime_type_query()
        if mime_type_dict == {}:
            mime_type_dict = mimetypes.read_mime_types(tools.global_const.basePath + "/tools/mime.types")
            mime_type_set(mime_type_dict)

        if "." + file_format in mime_type_dict:
            media_type = str(mime_type_dict["." + file_format])
            return media_type
        else:
            return "unknown"

    def handle_for_frontend(self):
        return {
            'Info': self.info.to_dict(exclude=None),
            'Ctrl': self.ctrl.to_dict(exclude=None)
        }
