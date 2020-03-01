# -*-coding=utf-8 -*-
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from subgraph.models import NodeInfo
from tools.models import SettingField, IdField, LevelField


# 设置的详情在前端查看
# done 08-16 remake 2019-10-17

def node_setting():
    setting = {
        "_id": 0,
        "_type": "node",  # "node" "media" "link"
        "_label": "DocGraph",
        "Base": {},
        "Border": {},
        "Show": {},
        "Text": {},
    }
    return [setting]


# done 08-16 remake 2019-10-17
def link_setting():
    setting = {
        "_id": 0,
        "_type": "link",
        "_label": "",
        "Base": {},
        "Arrow": {},
        "Text": {}
    }
    return [setting]


def note_content():
    setting = {
        "_title": "",
        "_content": ""
    }
    return setting


# remake 2019-10-17
def card_setting():
    setting = {
        "_id": 0,
        "_type": "node",  # "node" "media" "link"
        "_label": "",
        "Base": {},
        "Border": {},
        "Show": {},
        "Text": {}
    }
    return [setting]


# remake 2019-10-17
def graph_setting():
    setting = {
        "Base": {

        }
    }
    return setting


# todo Paper设置细化 level : 1
def paper_setting():
    setting = {
        "Base": {
            "theme": 0,
            "background": "",
            "color": "#000000",
            "opacity": 1
        },
        "Show": {
            "heightLock": True,  # 纵向锁定
            "widthLock": False,  # 横向锁定
            "percentage": False  # 使用百分比还是绝对数值
        },
        "Group": [
            {"height": 330, "width": 580, "isMain": True},
            {"height": 330, "width": 580, "isMain": True},
            {"height": 330, "width": 580, "isMain": True},
        ]
    }
    return setting


class DocGraph(models.Model):
    DocId = IdField(primary_key=True)  # 专题ID
    Nodes = ArrayField(SettingField(), default=list)  # json里包含节点在该专题下的设置
    Links = ArrayField(SettingField(), default=list)  # json里包含关系在该专题下的设置
    Medias = ArrayField(SettingField(), default=list)  # json里包含媒体在该专题下的设置
    Svgs = ArrayField(SettingField(), default=list)  # json里包含Svg
    Conf = JSONField(default=dict)  # json里包含专题本身的设置

    Complete = LevelField()
    MainNodes = ArrayField(IdField(), default=list)  # 主要节点
    Size = models.IntegerField(default=0)  # 尺寸

    def to_dict(self):
        return {
            '_id': self.DocId,
            'nodes': self.Nodes,
            'links': self.Links,
            'medias': self.Medias,
            'svgs': self.Svgs,
            'conf': self.Conf
        }

    class Meta:
        db_table = "document_graph"


# todo paper具体的产品形式 level: 1
# class DocPaper(models.Model):
#     DocId = models.BigIntegerField(primary_key=True, editable=False)
#     Nodes = ArrayField(SettingField(), default=card_setting)
#     Links = ArrayField(SettingField(), default=link_setting)
#     Path = ArrayField(JSONField(default=dict))
#     Conf = JSONField(default=paper_setting)  # 设置
#
#     class Meta:
#         db_table = "document_paper"


# 专题评论 done in 07-22
class Comment(models.Model):
    CommentId = models.BigIntegerField(db_column="ID", primary_key=True)  # 评论id
    SourceId = models.BigIntegerField(db_column="Source", db_index=True)  # 回复的资源的id
    TargetId = models.BigIntegerField(db_column="TARGET", db_index=True)  # 回复的目标的id
    TargetUser = models.BigIntegerField(db_column="TARGET_USER", db_index=True)  # 回复的用户的id
    Content = models.TextField(db_column="CONTENT", default="")  # 评论内容
    Owner = models.BigIntegerField(db_column="USER", default="0", db_index=True)  # 发表用户id
    CreateTime = models.DateTimeField(db_column="TIME", auto_now_add=True)  # 评论时间
    IsUsed = models.BooleanField(db_column="DELETED", default=False)

    class Meta:
        indexes = [
            models.Index(fields=["SourceId", "IsUsed"], name="Count_DocComment"),  # 统计资源回复
            models.Index(fields=["TargetUser", "IsUsed"], name="Count_ReplyComment"),  # 统计回复给某用户的
            models.Index(fields=["Owner", "IsUsed"], name="Count_OwnerComment"),  # 统计某用户回复的
        ]
        db_table = "document_comment"
