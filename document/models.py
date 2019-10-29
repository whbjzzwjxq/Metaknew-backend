# -*-coding=utf-8 -*-
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from subgraph.models import NodeInfo
from tools.models import SettingField


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


# done in 07-22 remake 2019-10-17
# todo Path 设计 Level:2
class DocGraph(models.Model):
    DocId = models.BigIntegerField(primary_key=True, editable=False)  # 专题ID
    Nodes = ArrayField(SettingField(), default=node_setting)  # json里包含节点在该专题下的设置
    Links = ArrayField(SettingField(), default=link_setting)  # json里包含关系在该专题下的设置
    Path = ArrayField(JSONField(default=dict))
    Conf = JSONField(default=graph_setting)  # json里包含专题本身的设置

    class Meta:
        db_table = "document_graph"


# todo paper具体的产品形式 level: 1
class DocPaper(models.Model):
    DocId = models.BigIntegerField(primary_key=True, editable=False)
    Nodes = ArrayField(SettingField(), default=card_setting)
    Links = ArrayField(SettingField(), default=link_setting)
    Path = ArrayField(JSONField(default=dict))
    Conf = JSONField(default=paper_setting)  # 设置

    class Meta:
        db_table = "document_paper"


# 专题评论 done in 07-22
class Comment(models.Model):
    CommentId = models.BigIntegerField(db_column="ID", primary_key=True)  # 评论id
    SourceId = models.BigIntegerField(db_column="Source", db_index=True)  # 回复的资源的id
    TargetId = models.BigIntegerField(db_column="TARGET", db_index=True)  # 回复的目标的id
    TargetUser = models.BigIntegerField(db_column="TARGET_USER", db_index=True)  # 回复的用户的id
    Content = models.TextField(db_column="CONTENT", default="")  # 评论内容
    Owner = models.BigIntegerField(db_column="USER", default="0", db_index=True)  # 发表用户id
    CreateTime = models.DateTimeField(db_column="TIME", auto_now_add=True)  # 评论时间
    Is_Delete = models.BooleanField(db_column="DELETED", default=False)

    class Meta:
        indexes = [
            models.Index(fields=["SourceId", "Is_Delete"], name="Count_DocComment"),  # 统计资源回复
            models.Index(fields=["TargetUser", "Is_Delete"], name="Count_ReplyComment"),  # 统计回复给某用户的
            models.Index(fields=["Owner", "Is_Delete"], name="Count_OwnerComment"),  # 统计某用户回复的
        ]
        db_table = "document_comment"


# 便签 remake 2019-10-17
class Note(models.Model):
    NoteId = models.BigIntegerField(primary_key=True)  # 便签id
    CreateUser = models.IntegerField(db_column="UserId", default="1", db_index=True)  # 用户id
    DocumentId = models.BigIntegerField(db_column="DocumentId")  # 所属专题id
    Content = models.TextField(db_column="Content", default="")  # 便签内容
    Conf = JSONField(db_column="Configure")  # 设置
    Is_Delete = models.BooleanField(db_index=True, default=False)  # 是否删除了

    class Meta:
        indexes = [
            models.Index(fields=["CreateUser", "DocumentId", "Is_Delete"]),  # 统计同一用户的Note
            models.Index(fields=["CreateUser"])
        ]

        db_table = "document_note"


class GraphVersionRecord(models.Model):
    CreateUser = models.BigIntegerField(db_column="User", editable=False, db_index=True)
    CreateTime = models.DateTimeField(auto_now=True, editable=False)
    SourceId = models.BigIntegerField(db_column="SourceId", editable=False, db_index=True)
    VersionId = models.SmallIntegerField(db_column="VersionId", default=0)  # 最多20个版本
    SourceType = models.TextField(editable=False, default="DocGraph")

    Name = models.TextField(db_column="Name", default='Draft')
    Is_Draft = models.BooleanField(db_column="Draft", default=True)  # 是草稿还是历史版本
    DontClear = models.BooleanField(default=False)  # 是否不要清除
    Nodes = ArrayField(SettingField(), default=node_setting)  # json里包含节点在该专题下的设置
    Links = ArrayField(SettingField(), default=link_setting)  # json里包含关系在该专题下的设置
    Path = ArrayField(JSONField(default=dict))
    Conf = JSONField(default=graph_setting)  # json里包含专题本身的设置

    class Meta:
        indexes = [
            models.Index(fields=["SourceId", "Is_Draft"])
        ]
        constraints = [
            models.UniqueConstraint(fields=["SourceId", "VersionId"], name="GraphVersionControl")
        ]
        db_table = "document_graph_record"
