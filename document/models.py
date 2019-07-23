# -*-coding=utf-8 -*-
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from users.models import User
from subgraph.models import Node


def node_setting():
    setting = {
        '_id': 0,
        'base': {
            'x': 0.5,  # 横向坐标
            'y': 0.5,  # 纵向坐标
            'type': 0,  # 样式
            'radius': 1.0,  # 大小设置
            'bright': 1.0,  # 亮度设置
            'opacity': 1.0,  # 透明度设置
        },
        'border': {
            'width': 0,  # 额外的边框宽度
            'color': '000000',  # 边框颜色
            'type': 0  # 样式
        },
        'show': {
            'show_all': True,
            'show_name': True,
            'show_pic': True,
            'show_circle': True
        },
        'name': {
            'location': 0,  # 名字位置设置 0 bottom 1 top 2 middle 3 left 4 right
            'offset': 2  # 名字偏移的量
        },
        'group': 0,  # 组别
        'explode': False  # 是否炸开(仅限专题)
        # todo 可能还有更多的设置 level : 3
    }
    return [setting]


def link_setting():
    setting = {
        '_id': 0,  # id
        'width': 1,  # 宽度
        'color': '000000',  # 颜色
        'type': 1,  # 这个type具体定义一下
        'show': True
    }
    return [setting]


def note_setting():

    setting = {
        '_id': 0,
        'x': 0.5,
        'y': 0.5,
        'opacity': 0.5,
        'type': 0,
        'content': ''
    }
    return [setting]


def graph_setting():
    setting = {
        'base': {
            'theme': 0,  # 这个需要商定一下
            'background': '',  # 背景图URL/id
            'color': '000000',  # 背景颜色
            'opacity': 0,  # 背景透明度
            'mode': 0,  # 0 normal 1 time 2 geo 3 imp 4...
        },
        'group': [
            {
                'scale': 1,
                'show': True,
                'color': '',
                'move_together': '',
            }
        ],
        'order': [
            {'_id': 0,
             'time': 10}
        ]
        # todo 可能还有更多的设置 level : 3
    }
    return setting


# done in 07-22
class _Doc(Node):
    Paper = models.URLField(db_column='PAPER')  # '真正'的文档 包含文字图片等等
    Size = models.IntegerField(db_column='SIZE', default=0)
    Keywords = ArrayField(models.TextField(), db_column='KEYWORDS', default=list)  # 关键词
    Total_Time = models.IntegerField(db_column='TOTAL_TIME', default=1000)

    class Meta:
        db_table = 'document_info'


# 专题的Graph相关的内容 也就是在svg绘制的时候请求的内容 done in 07-22
class DocGraph(models.Model):
    id = models.BigIntegerField(db_column='ID', primary_key=True, editable=False)  # 专题ID
    MainNodes = ArrayField(models.BigIntegerField(), db_column='MAIN_NODES', default=list)  # 主要节点的uuid
    IncludedNodes = ArrayField(JSONField(), db_column='NODES', default=node_setting())  # json里包含节点在该专题下的设置
    IncludedLinks = ArrayField(JSONField(), db_column='RELATIONSHIPS', default=link_setting())  # json里包含关系在该专题下的设置
    IncludedNotes = ArrayField(JSONField(), db_column='RELATIONSHIPS', default=note_setting())  # json里包含关系在该专题下的设置
    Conf = JSONField(db_column='CONF', default=graph_setting())  # json里包含专题本身的设置

    class Meta:
        db_table = 'document_graph'


# 专题评论 done in 07-22
class Comment(models.Model):
    id = models.BigAutoField(db_column='ID', primary_key=True)  # 评论id
    TargetId = models.BigIntegerField(db_column='TARGET', db_index=True)  # 回复的资源/评论的id
    TargetUser = models.BigIntegerField(db_column='TARGET_USER', db_index=True)  # 回复的用户的id
    Content = models.TextField(db_column='CONTENT', default='')  # 评论内容
    Owner = models.BigIntegerField(db_column='USER', default='0', db_index=True)  # 发表用户id
    Time = models.DateTimeField(db_column='TIME', auto_now_add=True)  # 评论时间
    Is_Delete = models.BooleanField(db_column='DELETED', default=False)
    Is_Sub = models.BooleanField(db_column='SUB', default=False)  # 回复是否是二级回复

    class Meta:
        indexes = [
            models.Index(fields=['Is_Sub', 'Is_Delete'], name='Count_SubComment'),  # 统计二级回复
        ]
        db_table = 'document_comment'


# 便签 done in 07-22
class Note(models.Model):
    id = models.BigIntegerField(db_column="ID", primary_key=True)  # 便签id
    CreateUser = models.IntegerField(db_column="USER_ID", default='1', db_index=True)  # 用户id
    TagType = models.TextField(db_column="TAGS_TYPE")  # 便签类型
    Content = models.TextField(db_column="CONTENT")  # 便签内容
    DocumentId = models.BigIntegerField(db_column="DOCUMENT_ID")  # 所属专题uuid
    Is_Open = models.BooleanField(db_index=True)  # 是否是一个公共便签

    class Meta:
        indexes = [
            models.Index(fields=['CreateUser', 'DocumentId'])  # 统计同一用户的Note
        ]

        db_table = 'document_note'


# 课程 todo level : 3
# class Course(DocGraph):
#     LinksInfo = ArrayField(JSONField(), db_column='LINKS_INFO')  # 学习网连接的信息
#     NodesInfo = ArrayField(JSONField(), db_column='NODES_INFO')  # 学习网
#     Total_Time = models.IntegerField(db_column='TOTAL_TIME', default=1000)
#
#     class Meta:
#         db_table = 'document_course'
