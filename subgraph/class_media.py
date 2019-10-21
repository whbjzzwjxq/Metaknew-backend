import mimetypes
from datetime import datetime, timezone
from typing import Optional

import oss2

from subgraph.models import MediaCtrl
from tools import base_tools
from tools.aliyun import authorityKeys
from tools.base_tools import ErrorContent, neo4j_create_node
from tools.redis_process import mime_type_query, mime_type_set


class BaseMedia(base_tools.BaseModel):
    access_key_id = authorityKeys["developer"]["access_key_id"]
    access_key_secret = authorityKeys["developer"]["access_key_secret"]
    bucket_name = authorityKeys["developer"]["bucket_name"]
    endpoint = authorityKeys["developer"]["endpoint"]

    def __init__(self, _id: int, user_id: int, _type="media", collector=base_tools.NeoSet()):
        super().__init__(_id, user_id, _type, collector)
        self.p_label = "unknown"
        self.is_create = False
        self.oss_manager: Optional[oss2.Bucket] = None

    # remake 2019-10-17 2019-10-20
    def create(self, data: dict, remote_file: str, is_user_made):
        self.is_create = True
        self.p_label = data["PrimaryLabel"]
        self.ctrl_create(remote_file, is_user_made)
        self.info_create(data)
        if data["Text"]:
            self.info.Text = data["Text"]
        else:
            self.info.Text = {"auto": ""}

        self.node = neo4j_create_node(
            _type="Media",
            labels=data["Labels"],
            plabel=self.p_label,
            props={"_id": self.id, "Name": data["Name"]},
            collector=self.collector
        )
        self.auth_create(data=data)
        return self

    def info_create(self, data):
        self.info = base_tools.media_init(self.p_label)()
        self.info.PrimaryLabel = self.p_label
        self.info.MediaId = self.id
        self.info_update(data)
        return self

    def ctrl_create(self, remote_file, is_user_made):
        # 注意这里还是写了文件位置的 之后可以移动文件位置
        self.ctrl = MediaCtrl(
            MediaId=self.id,
            FileName=remote_file,
            CreateUser=self.user_id,
            Format=remote_file.split("/")[1],
            Is_UserMade=is_user_made,
            CountCacheTime=datetime.now(tz=timezone.utc).replace(microsecond=0)
        )

    def update(self, data, remote_name, user_id) -> ErrorContent:
        """

        :param data: 前端的Info
        :param remote_name: 远端的文件名 主要是修改文件之后文件名会变化
        :param user_id: 请求者id
        :return: ErrorContent
        """
        # todo 更加详细的权限管理
        if self.ctrl.CreateUser == user_id:
            if remote_name == self.ctrl.FileName:
                self.info_update(data)
            else:
                self.set_oss_manager()
                if self.oss_manager.object_exists(remote_name):
                    history = {
                        "FileName": self.ctrl.FileName,
                        "UpdateTime": datetime.now(),
                        "Info": data
                    }
                    self.ctrl.History.append(history)
                    self.ctrl.FileName = remote_name
                    self.ctrl.Format = remote_name.split("/")[1]
                    self.info_update(data)
                else:
                    return ErrorContent(status=400, state=False, reason='NewFile Dos not Exist')
        else:
            return ErrorContent(status=401, state=False, reason='UnAuthorization')

    def save(self):
        self.info.save()
        self.ctrl.save()
        self.authority.save()
        self.collector.tx.commit()

    def set_oss_manager(self):
        if not self.oss_manager:
            auth = oss2.Auth(self.access_key_id, self.access_key_secret)
            self.oss_manager = oss2.Bucket(auth, self.endpoint, bucket_name=self.bucket_name, connect_timeout=10000)
        else:
            pass

    def check_remote_file(self) -> bool:
        """
        查看远端文件
        :return: bool
        """
        self.set_oss_manager()
        return self.oss_manager.object_exists(self.ctrl.FileName)

    def move_remote_file(self, new_location):
        """
        移动远端文件
        :param new_location:
        :return:
        """
        if self.check_remote_file():
            return self.oss_manager.copy_object(self.bucket_name, self.ctrl.FileName, new_location)
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
            mime_type_dict = mimetypes.read_mime_types(base_tools.basePath + "/tools/mime.types")
            mime_type_set(mime_type_dict)

        if "." + file_format in mime_type_dict:
            media_type = str(mime_type_dict["." + file_format])
            return media_type
        else:
            return "unknown"

    def handle_for_frontend(self):
        """
        前端所用格式
        :return:
        """
        unused_props = [
            "MediaId",
            "FileName",
            "Format",
            "History",
            "CountCacheTime",
            "TotalTime",
            "Hot",
            "CountCacheTime",
        ]
        self.query_base()
        ctrl_fields = self.ctrl._meta.get_fields()
        output_ctrl_dict = {field.name: getattr(self.ctrl, field.name)
                            for field in ctrl_fields if field.name not in unused_props}
        info_fields = self.info._meta.get_fields()
        output_info_dict = {field.name: getattr(self.info, field.name)
                            for field in info_fields if field.name not in unused_props}
        output = {
            "src": self.ctrl.FileName,
            "format": self.ctrl.Format,
            "Ctrl": output_ctrl_dict,
            "Info": output_info_dict,
        }
        return output
