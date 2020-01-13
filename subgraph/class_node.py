import json

from django.core.exceptions import ObjectDoesNotExist
from py2neo.data import Node as NeoNode

from es_module.logic_class import bulk_add_node_index, bulk_add_text_index
from record.logic_class import UnAuthorizationError
from subgraph.class_base import BaseModel
from subgraph.class_media import BaseMedia
from subgraph.models import MediaCtrl
from tools import base_tools
from tools.redis_process import get_user_name


class BaseNode(BaseModel):

    def __init__(self, _id: int, user_id: int, _type='node', collector=base_tools.NeoSet()):
        super().__init__(_id, user_id, _type, collector)

    # ----------------- query ----------------

    def query_all(self):
        """
        查询所有内容 包括Neo4j节点 翻译 历史文件
        :return:
        """
        success = self.query_base()
        if success:
            self.query_node()
            self.query_history()
        return self

    def query_node(self):
        if self.type != "link":
            self.node = self.collector.Nmatcher.match(self.p_label, _id=self.id).first()
            if not self.node:
                self.error_output(ObjectDoesNotExist, 'NeoNode不存在，可能是没有保存')
        else:
            self.error_output(TypeError, '异常调用')

    # ---------------- create ----------------
    def create(self, data):
        """
        别名
        :param data: info
        :return:
        """
        return self.base_node_create(data)

    def base_node_create(self, data):
        self.is_create = True
        assert "Name" in data
        assert "PrimaryLabel" in data
        self.p_label = data["PrimaryLabel"]
        self._ctrl_create()
        self.ctrl_update_by_user(data)
        self._info_create()
        self.__node_create()
        self.info_update(data)
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

    def ctrl_update_by_user(self, ctrl):
        """
        用户能够改变权限的信息
        :param ctrl: ctrl
        :return:
        """
        auth_ctrl_props = ['Is_Common', 'Is_Used', 'Is_Shared', 'Is_OpenSource']
        if self.ctrl.CreateUser == self.user_id:
            for prop in auth_ctrl_props:
                if '$_' + prop in ctrl:
                    setattr(self.ctrl, prop, ctrl['$_' + prop])
                else:
                    pass
            # 更新contributor
            if self.is_create:
                self.ctrl.Contributor = {"create": "", "update": []}
                if self.is_user_made:
                    self.ctrl.Contributor['create'] = get_user_name(self.user_id)
                else:
                    self.ctrl.Contributor['create'] = 'system'
            else:
                if self.is_user_made:
                    name = get_user_name(self.user_id)
                    if name not in self.ctrl.Contributor['update']:
                        self.ctrl.Contributor['update'].append(name)
                    else:
                        pass
                else:
                    pass
        else:
            self.error_output(UnAuthorizationError, '没有权限')

    def info_special_update(self, data):
        """
        特殊的更新内容
        :param data: Info
        :return:
        """
        if type(data["MainPic"]) == str:
            self.main_pic_setter(data["MainPic"])
        if data["IncludedMedia"]:
            self.media_setter(data["IncludedMedia"])
        self.name_checker(name=data['Name'])
        self.name_lang_rewrite(data)

    @staticmethod
    def name_lang_rewrite(data):
        """
        重写一下语言配置 现在有点混乱
        :param data:
        :return:
        """
        trans = data['Translate']
        name = data['Name']
        lang = data['Language']
        if not lang or lang == 'auto':
            compute_lang = base_tools.language_detect(name)
            data['Language'] = compute_lang
            if compute_lang not in trans and compute_lang != 'auto':
                trans[compute_lang] = name
        else:
            if lang in trans:
                pass
            else:
                trans[lang] = name

    def name_checker(self, name):
        """
        查询是否有类似名字的节点
        :return:
        """
        similar_node = base_tools.node_init(self.p_label).objects.filter(Name=name)
        if len(similar_node) > 0:
            name_list = json.dumps([node.ItemId for node in similar_node])
            warn = {"field": "Name", "warn_type": "similar_node" + name_list}
            self.warn.WarnContent.append(warn)

    def main_pic_setter(self, media_name):
        """
        设置主图片
        :param media_name: media的储存路径
        :return:
        """
        media_manager = BaseMedia.oss_manager
        self.query_warn()
        if not self.is_create:
            self.history_create()
            self.history.Content['MainPic'] = self.info.MainPic
        if media_manager.object_exists(media_name):
            self.info.MainPic = media_name
            return True
        else:
            warn = {"field": "MainPic", "warn_type": "empty_prop"}
            self.warn.WarnContent.append(warn)
            self.warn_update = True
            return False

    def media_setter(self, media_list):
        """
        设置包含的媒体
        :param media_list: list of media_id
        :return: self
        """
        # todo 改写为add_media 所有人 和 media_setter 编辑权限
        if self.user_id == self.ctrl.CreateUser:
            available_media = []
            warn = []
            self.query_warn()
            if not self.is_create:
                self.history_create()
                self.history.Content['IncludedMedia'] = self.info.IncludedMedia
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
                add_warn = {"field": "IncludedMedia", "warn_type": "media_no_exist: " + str(warn)}
                self.warn.WarnContent.append(add_warn)
                self.warn_update = True
                return warn
            else:
                return True
        else:
            return self.error_output(UnAuthorizationError, '没有编辑权限', strict=False)

    def graph_update(self, data):
        if not self.node:
            self.query_node()

        # 更新info
        neo_prop = {
            "Name": self.info.Name,
            "Imp": self.info.BaseImp,
            "HardLevel": self.info.BaseHardLevel
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

    def delete(self):
        # todo 节点删除 level: 2
        pass

    def merge(self, node1):
        # todo 节点merge level: 2
        pass

    def change_plabel(self):
        pass
        # todo 改变主标签 level: 2

    def save(self):
        """
        注意尽量不要使用单个Node保存
        :return:
        """
        self.ctrl.save()
        self.info.save()
        if self.history:
            self.history.save()
        if self.warn.WarnContent:
            self.warn.save()
        self.collector.tx.commit()
        bulk_add_text_index([self])
        bulk_add_node_index([self])

    def node_index(self):
        ctrl = self.ctrl
        info = self.info
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
                "Star": ctrl.Star,
                "Hot": ctrl.Hot,
                "TotalTime": ctrl.TotalTime
            },
            "Is_Used": ctrl.Is_Used,
            "Is_Common": ctrl.Is_Common,
            "Is_OpenSource": ctrl.Is_OpenSource
        }
        for lang in ['zh', 'en']:
            if lang in info.Translate:
                body["Name_%s" % lang] = info.Translate[lang]

        return body
