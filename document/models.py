# -*-coding=utf-8 -*-
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from subgraph.models import NodeInfo
from tools.models import SettingField, IdField, LevelField, TypeField


def node_setting_default():
    return {
        '_id': '-1',
        '_type': 'node',
        '_label': 'BaseNode',
        'InGraph': {
            'Base': {},
        },
        'InPaper': {}
    }


def document_components_default():
    return {
        'InPaper': {
            'Section': {
                '_children': []
            }
        },
        'InGraph': {
            'SubGraph': []
        }
    }


class Document(models.Model):
    ItemId = IdField(primary_key=True)  # 专题ID
    ItemType = TypeField(default='document')  # 不需要管理
    PrimaryLabel = models.TextField(default='_DocGraph', db_index=True)  # 专题类型
    # Content
    Nodes = ArrayField(SettingField(), default=list)  # 节点设置
    Links = ArrayField(SettingField(), default=list)  # 关系设置
    Medias = ArrayField(SettingField(), default=list)  # 媒体设置
    Texts = ArrayField(SettingField(), default=list)  # 文字设置

    # Components
    Components = JSONField(default=document_components_default)  # 组件与插件
    # Ctrl
    Complete = LevelField()
    MainNodes = ArrayField(IdField(), default=list)  # 主要节点
    Size = models.IntegerField(default=0)  # 尺寸
    LinkFailed = models.BooleanField(default=False)  # 保存关系出错

    @property
    def visual_node_setting(self):
        return [self.Nodes + self.Medias]

    @classmethod
    def all_fields(cls):
        return [field.name for field in cls._meta.fields if not field.name == 'ItemId']

    class Meta:
        db_table = "document_graph"


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
