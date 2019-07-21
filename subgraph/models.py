from django.contrib.postgres.fields import *
from django.db import models
from users.models import User


# 将可能的模板写在前面
def contributor():
    return [{"user_id": 1, "level": 0}]


def feature_vector():

    return {"group_vector": [],
            "word_embedding": [],
            "label_embedding": [],
            "extra_space": {}}


# Node的控制属性而且不直接传回前端
class NodeCtrl(models.Model):

    id = models.BigIntegerField(db_column='ID', primary_key=True, editable=False)
    CreateMethod = models.CharField(db_column='METHOD', max_length=30, editable=False)
    CreateTime = models.DateTimeField(db_column='TIME', auto_now_add=True, editable=False)
    CreateUser = models.IntegerField(db_column='USER', default='0', editable=False)  # 创建用户
    History = models.BigIntegerField(db_column='HISTORY', editable=False)  # 历史记录的编号
    CountCacheTime = models.DateTimeField(db_column='CACHE_TIME', auto_now=True)  # 最后统计的时间

    class Meta:
        abstract = True


# Node前端会用 但是不是简单获得的属性
class NodeShow(NodeCtrl):

    Imp = models.IntegerField(db_column='IMP', default=0)

    Hot = models.IntegerField(db_column='HOT', default=0)
    Favorite = models.IntegerField(db_column='FAVORITE', default=0)
    StrLevel = models.FloatField(db_column='STR', default=0)
    ClaLevel = models.IntegerField(db_column='CLA', default=0)
    Contributor = ArrayField(JSONField, db_column='CONTRIBUTOR', default=contributor())

    ExtraProps = JSONField(db_column='EXTRA_PROPS', default=dict)
    UserLabels = ArrayField(models.TextField(), db_column='USER_LABELS', default=list)
    Labels = ArrayField(models.TextField(), db_column='LABELS', default=list)

    IncludedMedia = ArrayField(models.BigIntegerField(), db_column='INCLUDED_MEDIA', default=list)  # 包含的多媒体文件uuid
    FeatureVec = JSONField(db_column='FEATURE_VECTOR', default=feature_vector())  # 特征值

    class Meta:

        db_table = 'node_frontend'


# Node直接简单抛出的属性
class Node(NodeShow):

    Name = models.TextField(db_column='NAME')
    Name_zh = models.TextField(db_column='NAME_ZH')
    Name_en = models.TextField(db_column='NAME_EN')
    Language = models.TextField(db_column='LANG', default='auto')
    Area = models.TextField(db_column='AREA')
    PrimaryLabel = models.TextField(db_column='P_LABEL', db_index=True)
    Alias = ArrayField(models.TextField(), db_column='ALIAS', default=list)
    Description = models.TextField(db_column='DESCRIPTION', default='')

    class Meta:

        db_table = 'node_base'


class Person(Node):

    PeriodStart = models.TextField(db_column='PERIOD_START')
    PeriodEnd = models.TextField(db_column='PERIOD_END')
    BirthPlace = models.CharField(db_column='BIRTHPLACE', max_length=30)
    Nation = models.CharField(db_column='NATION', max_length=30, default='None')

    class Meta:
        db_table = 'node_person'


class Project(Node):

    PeriodStart = models.TextField(db_column='PERIOD_START')
    PeriodEnd = models.TextField(db_column='PERIOD_END')
    Nation = models.TextField(db_column='NATION', max_length=30)
    Leader = ArrayField(models.TextField(), db_column='LEADER', default=list)  # 领头人

    class Meta:
        db_table = 'node_project'


class ArchProject(Project):

    Location = models.TextField(db_column='LOCATION', default='Beijing')
    WorkTeam = ArrayField(models.TextField(), db_column='WORK_TEAM', default=list)

    class Meta:
        db_table = 'node_arch_project'


class LocationDoc(models.Model):

    id = models.AutoField(db_column='ID', primary_key=True)
    Name = models.TextField(db_column='NAME', default='Beijing')
    LocId = models.TextField(db_column='LOC_ID', default='ChIJ58KMhbNLzJQRwfhoMaMlugA')
    Alias = ArrayField(models.TextField(), db_column='ALIAS', default=list)
    Doc = JSONField(db_column='DOC', default=dict)

    class Meta:
        db_table = 'location_doc'
