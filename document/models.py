# -*-coding=utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from django.utils.timezone import now
from users.models import User
# Create your models here.


# 专题的信息 也就是在cache_doc里面请求的内容
class DocumentInformation(models.Model):
    uuid = models.UUIDField(db_column='UUID', primary_key=True)  # 专题id
    Title = models.TextField(db_column='TITLE')  # 标题
    Url = models.TextField(db_column='URL', default='')  # 缩略图
    Area = models.TextField(db_column='AREA', default='None')  # 领域
    CreateUser = models.IntegerField(db_column='USER', default='0')  # 发表用户id
    CreateTime = models.DateTimeField(db_column='CREATE_TIME', auto_now_add=True)  # 创建的时间
    UpdateTime = models.DateTimeField(db_column='UPDATE_TIME', auto_now=True)  # 最后更新的时间
    HardLevel = models.FloatField(db_column='HARD_LEVEL', default=0)  # 难易度
    Size = models.IntegerField(db_column='SIZE', default=0)  # 节点数量
    Imp = models.IntegerField(db_column='IMP', default=0)  # 重要度
    Hot = models.IntegerField(db_column='HOT', default=0)  # 热度
    Useful = models.FloatField(db_column='USEFUL', default=0)  # 有用的程度
    Description = models.TextField(db_column='DESCRIPTION', default='None')  # 描述
    IncludedMedia = ArrayField(models.TextField(), db_column='INCLUDED_MEDIA', default=list)  # 包含的多媒体文件url

    class Meta:
        db_table = 'document_information'


# 专题的Graph相关的内容 也就是在svg绘制的时候请求的内容
class Document(models.Model):
    uuid = models.UUIDField(db_column='UUID', primary_key=True)  # 专题ID
    MainNodes = ArrayField(models.UUIDField(), db_column='MAIN_NODES', default=list)   # 主要节点的uuid
    Keywords = ArrayField(models.TextField(), db_column='KEYWORDS', default=list)
    IncludedNodes = ArrayField(JSONField(db_column='NODES'), default=list)  # json里包含节点在该专题下的设置
    IncludedRels = ArrayField(JSONField(db_column='RELATIONSHIPS'), default=list)  # json里包含关系在该专题下的设置
    FeatureVec = models.TextField(db_column='FEATURE_VECTOR', default='0')  # 特征值

    class Meta:
        db_table = 'document'


# 专题评论
class Comment(models.Model):
    id = models.UUIDField(db_column='ID', primary_key=True)  # 评论id
    uuid = models.UUIDField(db_column='UUID')  # 回复的内容的id
    User = models.ForeignKey(User, on_delete=models.CASCADE)  # 发表用户id
    Time = models.DateTimeField(db_column='TIME', default=now)  # 评论时间
    Content = models.TextField(db_column='CONTENT')  # 评论内容

    class Meta:
        db_table = 'comment'

