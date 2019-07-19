from django.contrib.postgres.fields import *
from django.db import models
from django.utils.timezone import now
from users.models import User


# 不要在模型中写字段以外的属性或方法， 这里是储存用的

# Node的控制属性而且不直接传回前端
class NodeCtrl(models.Model):

    id = models.BigIntegerField(db_column='ID', primary_key=True, editable=False)
    ImportMethod = models.CharField(db_column='IMPORT_METHOD', max_length=30, editable=False)
    ImportTime = models.DateTimeField(db_column='IMPORT_TIME', auto_now_add=True)
    CreateUser = models.IntegerField(db_column='USER', default='0', editable=False)  # 创建用户
    Is_Common = models.BooleanField(db_column='COMMON', default=True)
    Is_Used = models.BooleanField(db_column='USED', default=True)
    History = models.BigIntegerField(db_column='HISTORY')  # 历史记录的编号
    IncludedMedia = ArrayField(models.BigIntegerField(), db_column='INCLUDED_MEDIA', default=list)  # 包含的多媒体文件uuid
    FeatureVec = JSONField(db_column='FEATURE_VECTOR', default=dict)  # 特征值

    class Meta:
        abstract = True


# Node前端不需要处理就抛出的属性
class NodeShow(NodeCtrl):

    Imp = models.IntegerField(db_column='IMP', default=0)
    Hot = models.IntegerField(db_column='HOT', default=0)
    StrLevel = models.FloatField(db_column='STR', default=0)
    ClaLevel = models.IntegerField(db_column='CLA', default=0)
    Contributor = JSONField(db_column='CONTRIBUTOR', default=dict)

    class Meta:
        abstract = True


class Node(NodeShow):

    Name = models.TextField(db_column='NAME')
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

