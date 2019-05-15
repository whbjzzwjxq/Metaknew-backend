# -*-coding=utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from django.utils.timezone import now
# Create your models here.


# todo 将字段名改为驼峰写法
class Document_Information(models.Model):
    uuid = models.UUIDField(db_column='UUID', primary_key=True)  # 专题id
    create_user = models.IntegerField(db_column='CREATE_USER')  # 发表用户id
    time = models.DateTimeField(db_column='TIME', default=now)  # 发表时间
    title = models.TextField(db_column='TITLE')  # 标题
    url = models.TextField(db_column='URL', default='')  # 缩略图
    description = models.TextField(db_column='DESCRIPTION', default='')  # 描述
    imp = models.FloatField(db_column='IMP', default=0)    # 重要度
    hot = models.FloatField(db_column='HOT', default=0)  # 热度
    hard_level = models.FloatField(db_column='HARD_LEVEL', default=0)  # 难易度
    area = models.TextField(db_column='AREA')  # 领域
    size = models.IntegerField(db_column='SIZE', default=0)  # 节点数量
    share = models.BooleanField(db_column='SHARE', default=False)  # 是否处于分享状态
    feature_vector = models.TextField(db_column='FEATURE_VECTOR', default='0')  # 特征值
    main_nodes = ArrayField(models.UUIDField(), db_column='MAIN_NODES', default=list)   # 主要节点的uuid
    keywords = ArrayField(models.TextField(), db_column='KEYWORDS', default=list)  # 主要节点的名字
    authority = ArrayField(models.TextField(), db_column='AUTHORITY', default=list)  # 拥有权限的用户id
    included_media = ArrayField(models.TextField(), db_column='INCLUDED_MEDIA', default=list)  # 包含的多媒体文件url

    class Meta:
        db_table = 'document_information'


# 专题
class Document(models.Model):
    uuid = models.UUIDField(db_column='UUID', primary_key=True)  # 专题ID
    nodes = ArrayField(JSONField(db_column='NODE'))  # json里包含节点的uuid,x,y坐标
    relationships = ArrayField(JSONField(db_column='RELATIONSHIP'), default=dict)   # json

    class Meta:
        db_table = 'document'


# 专题评论
class Comment(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # 评论id
    uuid = models.UUIDField(db_column='UUID')  # 关联专题id
    userid = models.IntegerField(db_column='USER_ID')  # 用户id
    time = models.DateTimeField(db_column='TIME')  # 评论时间
    content = models.TextField(db_column='CONTENT')  # 评论内容
    imp = models.FloatField(db_column='IMP')  # 评论重要度
    hard_level = models.FloatField(db_column='HARD_LEVEL')  # 评论难易度
    useful = models.BooleanField(db_column='USEFUL')  # 是否有用

    class Meta:
        db_table = 'comment'

