# -*-coding=utf-8 -*-
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from subgraph.models import NodeInfo


# done 08-16
def node_setting():
    setting = {
        "_id": 0,
        "Type": "Document",
        "Base": {
            "x": 0.5,  # 横向坐标
            "y": 0.5,  # 纵向坐标
            "type": 0,  # 样式
            "radius": 1.0,  # 大小设置
            "color": "#FFFFFF",  # 颜色设置
            "opacity": 1.0,  # 透明度设置
        },
        "Border": {
            "width": 0,  # 额外的边框宽度
            "color": "#000000",  # 边框颜色
            "type": 0  # 样式
        },
        "Show": {
            "showAll": True,
            "showName": True,
            "showPic": True,
            "showCircle": True,
            "explode": False,  # 是否炸开(仅限专题)
            "isMain": False
        },
        "Name": {
            "location": 0,  # 名字位置设置 0 bottom 1 top 2 middle 3 left 4 right
            "offset": 2  # 名字偏移的量
        },
        "Group": 0,  # 组别
    }
    return [setting]


# done 08-16
def link_setting():
    setting = {
        "_id": 0,  # id
        "width": 1,  # 宽度
        "color": "#000000",  # 颜色
        "type": "",  # 这个type具体定义一下
        "show": True
    }
    return [setting]


# done 08-16
def note_setting():
    setting = {
        "_id": 0,
        "Conf": {"x": 0.5,
                 "y": 0.5,
                 "opacity": 0.5,
                 "background": "#000000"
                 },
        "Content": "",
        "TagType": "normal",
        "Is_Open": True,
        "Document": "0"
    }
    return [setting]


# todo level: 1 Card设置
def card_setting():
    setting = {
        "_id": 0,
        "Type": "Graph",  # Graph | Node | Sheet | Video | Picture | Text .etc
        "Group": {
            "group": 0,
            "order": 2
        },
        "Show": {
            "isMain": False,
            "width": 100,
            "height": -1
        }
    }
    return [setting]


# todo level: 1 Graph设置
def graph_setting():
    setting = {
        "Base": {
            "theme": 0,  # 这个需要商定一下
            "background": "",  # 背景图URL/id
            "color": "000000",  # 背景颜色
            "opacity": 0,  # 背景透明度
            "mode": 0,  # 0 normal 1 time 2 geo 3 imp 4...
        },
        "Group": [
            {
                "scale": 1,
                "show": True,
                "color": "",
                "move_together": "",
            }
        ],
        "Order": [
            {"_id": 0,
             "time": 10}
        ]
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


# DocGraph相关的内容 也就是在svg绘制的时候请求的内容 done in 07-22
class DocGraph(models.Model):
    DocId = models.BigIntegerField(primary_key=True, editable=False)  # 专题ID
    Nodes = ArrayField(JSONField(), db_column="Nodes", default=node_setting)  # json里包含节点在该专题下的设置
    Links = ArrayField(JSONField(), db_column="Relationships", default=link_setting)  # json里包含关系在该专题下的设置
    CommonNotes = ArrayField(JSONField(), db_column="Notes", default=note_setting)  # json里包含便签在该专题下的设置
    Conf = JSONField(db_column="Conf", default=graph_setting)  # json里包含专题本身的设置

    class Meta:
        db_table = "document_graph"


# todo paper具体的产品形式 level: 1
class DocPaper(models.Model):
    DocId = models.BigIntegerField(primary_key=True, editable=False)  # 专题ID
    Nodes = ArrayField(JSONField(), db_column="Nodes", default=card_setting)  # json里包含节点在该专题下的设置
    CommonNotes = ArrayField(JSONField(), db_column="Notes", default=note_setting)  # json里包含便签在该专题下的设置
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


# 便签 done in 07-22
class Note(models.Model):
    NoteId = models.BigIntegerField(primary_key=True)  # 便签id
    CreateUser = models.IntegerField(db_column="UserId", default="1", db_index=True)  # 用户id
    DocumentId = models.BigIntegerField(db_column="DocumentId")  # 所属专题id
    TagType = models.TextField(db_column="TagsType", default="normal")  # 便签类型
    Content = models.TextField(db_column="Content", default="")  # 便签内容
    Conf = JSONField(db_column="Configure")  # 设置
    Is_Open = models.BooleanField(db_index=True, default=False)  # 是否是一个公共便签
    Is_Delete = models.BooleanField(db_index=True, default=False)  # 是否删除了

    class Meta:
        indexes = [
            models.Index(fields=["CreateUser", "DocumentId", "Is_Delete"]),  # 统计同一用户的Note
            models.Index(fields=["CreateUser"])
        ]

        db_table = "document_note"

# todo 课程 level: 3
# class Course(DocGraph):
#     LinksInfo = ArrayField(JSONField(), db_column="LINKS_INFO")  # 学习网连接的信息
#     NodesInfo = ArrayField(JSONField(), db_column="NODES_INFO")  # 学习网
#     Total_Time = models.IntegerField(db_column="TOTAL_TIME", default=1000)
#
#     class Meta:
#         db_table = "document_course"

# todo Path level: 3
# class Path(models.Model):
#
#     PathId = models.BigIntegerField(primary_key=True)
#     CreateUser = models.IntegerField(db_column="USER_ID", db_index=True)  # 用户id
#     Order = JSONField(default=base_path())
#
#     class Meta:
#
#         db_table = "document_path"
