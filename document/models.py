# -*-coding=utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from django.utils.timezone import now
from users.models import User
# Create your models here.
# 专题的信息 也就是在cache_doc里面请求的内容


class DocInfo(models.Model):
    uuid = models.UUIDField(db_column='UUID', primary_key=True)  # 专题id
    Title = models.TextField(db_column='TITLE', default=uuid)  # 标题
    MainPic = models.URLField(db_column='MAIN_PICTURE', default='')  # 缩略图
    Area = models.TextField(db_column='AREA', default='None')  # 领域
    CreateUser = models.IntegerField(db_column='USER', default='0')  # 发表用户id
    CreateTime = models.DateTimeField(db_column='CREATE_TIME', auto_now_add=True)  # 创建的时间
    UpdateTime = models.DateTimeField(db_column='UPDATE_TIME', auto_now=True)  # 最后更新的时间
    HardLevel = models.FloatField(db_column='HARD_LEVEL', default=0)  # 难易度
    Size = models.IntegerField(db_column='SIZE', default=0)  # 节点数量
    Imp = models.IntegerField(db_column='IMP', default=0)  # 重要度
    Hot = models.IntegerField(db_column='HOT', default=0)  # 热度
    Useful = models.IntegerField(db_column='USEFUL', default=0)  # 有用的程度
    Description = models.TextField(db_column='DESCRIPTION', default='None')  # 描述
    IncludedMedia = ArrayField(models.URLField(), db_column='INCLUDED_MEDIA', default=list)  # 包含的多媒体文件url
    FeatureVec = models.TextField(db_column='FEATURE_VECTOR', default='0')  # 特征值

    class Meta:
        db_tablespace = 'document'
        db_table = 'document_info'


# 专题的Graph相关的内容 也就是在svg绘制的时候请求的内容
class DocGraph(models.Model):
    uuid = models.UUIDField(db_column='UUID', primary_key=True)  # 专题ID
    MainNodes = ArrayField(models.UUIDField(), db_column='MAIN_NODES', default=list)   # 主要节点的uuid
    IncludedNodes = ArrayField(JSONField(), db_column='NODES', default=list)  # json里包含节点在该专题下的设置
    IncludedLinks = ArrayField(JSONField(), db_column='RELATIONSHIPS', default=list)  # json里包含关系在该专题下的设置

    class Meta:
        db_tablespace = 'document'
        db_table = 'document_graph'


# 专题评论
class Comment(models.Model):
    id = models.UUIDField(db_column='ID', primary_key=True)  # 评论id
    BaseTarget = models.UUIDField(db_column='TARGET')  # 注意是回复的专题的id
    Target = models.UUIDField(db_column='')
    Owner = models.IntegerField(db_column='USER', default='0')  # 发表用户id
    Time = models.DateTimeField(db_column='TIME', default=now)  # 评论时间
    Content = models.TextField(db_column='CONTENT', default='')  # 评论内容
    Is_Delete = models.BooleanField(db_column='DELETED', default=False)

    class Meta:
        db_tablespace = 'document'
        db_table = 'comment'


# 路径
class Path(models.Model):
    uuid = models.UUIDField(db_column='PATH_ID', primary_key=True)  # 路径id
    PathTitle = models.TextField(db_column='PATH_TITLE')  # 路径题目
    PathDocument = ArrayField(JSONField(), db_column='PATH_DOCUMENT')  # 路径包含的专题信息（uuid//uuid Order//查看节点的顺序 Time//持续时间）
    Title = models.TextField(db_column='TITLE')  # 标题
    Area = ArrayField(models.TextField(), db_column='AREA', default='None')  # 领域
    CreateUser = models.IntegerField(db_column='USER', default='0')  # 发表用户id
    CreateTime = models.DateTimeField(db_column='CREATE_TIME', auto_now_add=True)  # 创建的时间
    UpdateTime = models.DateTimeField(db_column='UPDATE_TIME', auto_now=True)  # 最后更新的时间
    HardLevel = models.FloatField(db_column='HARD_LEVEL', default=0)  # 难易度
    Hot = models.IntegerField(db_column='HOT', default=0)  # 热度
    Useful = models.IntegerField(db_column='USEFUL', default=0)  # 有用的程度
    Description = models.TextField(db_column='DESCRIPTION', default='None')  # 描述

    class Meta:
        db_tablespace = 'document'
        db_table = 'path'


# 便签
class Note(models.Model):
    uuid = models.UUIDField(db_column="ID", primary_key=True)  # 便签id
    CreateUser = models.IntegerField(db_column="USER_ID", default='1')  # 用户id
    TagType = models.TextField(db_column="TAGS_TYPE")  # 便签类型
    Content = models.TextField(db_column="CONTENT")  # 便签内容
    DocumentId = models.UUIDField(db_column="DOCUMENT_ID")  # 所属专题uuid

    class Meta:
        db_tablespace = 'document'
        db_table = 'note'
