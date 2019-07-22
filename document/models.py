# -*-coding=utf-8 -*-
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from users.models import User
from subgraph.models import Node


def node_setting():
    setting = {
        'x': 0.5,  # 横向坐标
        'y': 0.5,  # 纵向坐标
        'group': 0,  # 组别
        'radius': 1.0,  # 大小设置
        'bright': 1.0,  # 亮度设置
        'border': 0,   # 额外的边框宽度
        'border_color': '',  # 边框颜色
        'type': 'normal',  # 节点的类型
        'show': True,  # 是否默认显示
        'show_name': True,  # 是否显示名字
        'show_circle': True,  # 是否显示圆
        'show_pic': True,  # 是否显示默认图片
        'name_location': 'bottom',  # 名字的位置 left right top bottom middle
        'explode': False  # 是否炸开(仅限专题)
    }
    return setting


# todo 专题可能还有一些别的信息?
class _Doc(Node):

    Paper = models.URLField(db_column='PAPER')  # '真正'的文档 包含文字图片等等
    Size = models.IntegerField(db_column='SIZE', default=0)
    Keywords = ArrayField(models.TextField(), db_column='KEYWORDS', default=list)  # 关键词
    Total_Time = models.IntegerField(db_column='TOTAL_TIME', default=1000)

    class Meta:
        db_table = 'document_info'


# 专题的Graph相关的内容 也就是在svg绘制的时候请求的内容 todo
class DocGraph(models.Model):

    id = models.BigIntegerField(db_column='ID', primary_key=True, editable=False)  # 专题ID
    MainNodes = ArrayField(models.BigIntegerField(), db_column='MAIN_NODES', default=list)   # 主要节点的uuid
    IncludedNodes = ArrayField(JSONField(), db_column='NODES', default=list)  # json里包含节点在该专题下的设置
    IncludedLinks = ArrayField(JSONField(), db_column='RELATIONSHIPS', default=list)  # json里包含关系在该专题下的设置
    Conf = JSONField(db_column='CONF')  # json里包含专题本身的设置

    class Meta:

        db_table = 'document_graph'


# 专题评论
class Comment(models.Model):

    id = models.BigAutoField(db_column='ID', primary_key=True)  # 评论id
    TargetType = models.IntegerField(db_column='TARGET_TYPE')  # global_word
    TargetId = models.BigIntegerField(db_column='TARGET')  # 回复的资源/评论的id
    TargetUser = models.BigIntegerField(db_column='TARGET_USER')  # 回复的用户的id
    Owner = models.BigIntegerField(db_column='USER', default='0')  # 发表用户id
    Time = models.DateTimeField(db_column='TIME', auto_now_add=True)  # 评论时间
    Content = models.TextField(db_column='CONTENT', default='')  # 评论内容
    Is_Delete = models.BooleanField(db_column='DELETED', default=False)

    class Meta:

        db_table = 'document_comment'


# 课程 todo
class Course(DocGraph):

    LinksInfo = ArrayField(JSONField(), db_column='LINKS_INFO')  # 学习网连接的信息
    NodesInfo = ArrayField(JSONField(), db_column='NODES_INFO')  # 学习网
    Total_Time = models.IntegerField(db_column='TOTAL_TIME', default=1000)

    class Meta:

        db_table = 'document_course'


# 便签
class Note(models.Model):

    id = models.BigIntegerField(db_column="ID", primary_key=True)  # 便签id
    CreateUser = models.IntegerField(db_column="USER_ID", default='1', db_index=True)  # 用户id
    TagType = models.TextField(db_column="TAGS_TYPE")  # 便签类型
    Content = models.TextField(db_column="CONTENT")  # 便签内容
    DocumentId = models.BigIntegerField(db_column="DOCUMENT_ID")  # 所属专题uuid

    class Meta:

        index = [
            models.Index(fields=['CreateUser', 'DocumentId'])
        ]

        db_table = 'document_note'
