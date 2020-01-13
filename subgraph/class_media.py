import mimetypes

import oss2
from django.core.exceptions import ObjectDoesNotExist
from py2neo.data import Node as NeoNode

from es_module.logic_class import bulk_add_text_index
from record.logic_class import UnAuthorizationError
from subgraph.class_base import BaseModel
from tools import base_tools
from tools.aliyun import authorityKeys
from tools.redis_process import mime_type_query, mime_type_set


class BaseMedia(BaseModel):
    access_key_id = authorityKeys["developer"]["access_key_id"]
    access_key_secret = authorityKeys["developer"]["access_key_secret"]
    bucket_name = authorityKeys["developer"]["bucket_name"]
    endpoint = authorityKeys["developer"]["endpoint"]
    auth = oss2.Auth(access_key_id, access_key_secret)
    oss_manager = oss2.Bucket(auth, endpoint, bucket_name=bucket_name, connect_timeout=10000)

    def __init__(self, _id: int, user_id: int, _type="media", collector=base_tools.NeoSet()):
        super().__init__(_id, user_id, _type, collector)

    def query_node(self):
        if self.type != "link":
            self.node = self.collector.Nmatcher.match(self.type, self.p_label, _id=self.id).first()
            if not self.node:
                self.error_output(ObjectDoesNotExist, 'NeoNode不存在，可能是没有保存')
        else:
            self.error_output(TypeError, '异常调用')

    # ---------------- create ----------------
    # remake 2019-11-1
    def create(self, data):
        """
        别名
        :param data:
        :return:
        """
        return self.base_media_create(data)

    def base_media_create(self, data: dict):
        remote_file = data['remote_file']
        self.is_create = True
        self.p_label = data["PrimaryLabel"]
        self._ctrl_create()
        self._info_create()
        self.__node_create()
        self.info_update(data)
        self.ctrl_update_by_user(data, remote_file)
        return self

    def __node_create(self):
        node = NeoNode(self.p_label)
        node["_id"] = self.id
        node["_type"] = self.type
        node["_label"] = self.p_label
        node.__primarylabel__ = self.p_label
        node.__primarykey__ = "_id"
        node.__primaryvalue__ = self.id
        self.node = node
        self.collector.tx.create(self.node)

    # ---------------- update ----------------

    def ctrl_update_by_user(self, data, remote_file):
        """
        用户能改变权限和文件位置 放在history初始化之后进行
        :param data:
        :param remote_file:
        :return:
        """
        auth_ctrl_props = ['Is_Common', 'Is_Used', 'Is_Shared', 'Is_OpenSource']
        if self.ctrl.CreateUser == self.user_id:
            for prop in auth_ctrl_props:
                if '$_' + prop in data:
                    setattr(self.ctrl, prop, data['$_' + prop])
                else:
                    pass
            if self.ctrl.FileName != remote_file:
                if self.oss_manager.object_exists(remote_file):
                    self._history_update('FileName', self.ctrl.FileName)
                    self.ctrl.FileName = remote_file
                    self.ctrl.Format = remote_file.split('.')[1]
                else:
                    self.error_output(FileNotFoundError, '远端服务器没有文件')
        else:
            self.error_output(UnAuthorizationError, '没有权限')

    def info_special_update(self, data):
        """
        特别update过程 暂时
        :param data:
        :return:
        """
        pass

    def graph_update(self, data):
        if not self.node:
            self.query_node()

        # 更新info
        neo_prop = {
            "Name": self.info.Name,
        }
        self.node.update(neo_prop)

        # 更新ctrl
        ctrl_list = ['Is_Used', 'Is_Common', 'Is_UserMade']
        for label in ctrl_list:
            ctrl_value = getattr(self.ctrl, label)
            if ctrl_value:
                self.node.add_label(label)
            else:
                if self.node.has_label(label):
                    self.node.remove_label(label)

        # 更新labels
        self.node.update_labels(self.info.Labels)
        self.collector.tx.push(self.node)
    # ---------------- function ----------------

    def save(self):
        self.info.save()
        self.ctrl.save()
        if self.history:
            self.history.save()
        if self.warn.WarnContent:
            self.warn.save()
        self.collector.tx.commit()
        bulk_add_text_index([self])

    def check_remote_file(self) -> bool:
        """
        查看远端文件
        :return: bool
        """
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
