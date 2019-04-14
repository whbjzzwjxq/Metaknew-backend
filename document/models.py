# -*-coding=utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.contrib.postgres.fields import ArrayField

from peewee import *

# Create your models here.

post_gre_sql_db = PostgresqlDatabase("demomaster", user="postgres", password="123456", host="localhost", port="5432")


class BaseModel(Model):
    class Meta:
        database = post_gre_sql_db  # This model uses the "people.db" database.


# 专题
class Document(BaseModel):
    id = AutoField(db_column='ID', primary_key=True)
    uuid = UUIDField(db_column='UUID')  # 专题id
    userid = IntegerField(db_column='USER_ID')  # 发表用户id
    time = DateTimeField(db_column='TIME', default=datetime.datetime.now)  # 发表时间
    title = CharField(db_column='TITLE')  # 标题
    url = TextField(db_column='URL')  # 缩略图
    description = CharField(db_column='DESCRIPTION')  # 描述
    imp = DoubleField(db_column='IMP', default=0)    # 重要度
    hot = DoubleField(db_column='HOT', default=0)  # 热度
    hard_level = DoubleField(db_column='HARD_LEVEL', default=0)  # 难易度
    area = CharField(db_column='AREA')  # 领域
    size = IntegerField(db_column='SIZE', default=0)  # 节点数量
    uuid_list = TextField(db_column='UUID_LIST')  # 相关专题uuid

    class Meta:
        table_name = 'document'


# 专题评论
class Comment(BaseModel):
    id = AutoField(db_column='ID', primary_key=True)  # 评论id
    uuid = UUIDField(db_column='UUID')  # 关联专题id
    userid = IntegerField(db_column='USER_ID')  # 用户id
    time = DateTimeField(db_column='TIME')  # 评论时间
    content = CharField(db_column='CONTENT')  # 评论内容
    imp = DoubleField(db_column='IMP')  # 评论重要度
    hard_level = DoubleField(db_column='HARD_LEVEL')  # 评论难易度
    useful = BooleanField(db_column='USEFUL')  # 是否有用

    class Meta:
        table_name = 'comment'


# 专题资源
class Resource(BaseModel):
    id = AutoField(db_column='ID', primary_key=True)  # 资源id
    uuid = UUIDField(db_column='UUID')  # 关联专题ID
    file = ArrayField(CharField(db_column='FILE', max_length=200))   # 文件信息

    class Meta:
        table_name = 'resource'


# 专题信息   ?????未定
class DocumentInfo(BaseModel):
    uuid = IntegerField()   #包含的专题list

    class Meta:
        table_name = 'documentInfo'
