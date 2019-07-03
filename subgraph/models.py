from django.contrib.postgres.fields import *
from django.db import models
from django.utils.timezone import now
import tools.location as tool
from users.models import User


# 不要在模型中写字段以外的属性或方法， 这里是储存用的

# 没有修改接口的基本控制属性
class BaseNodeCtrl(models.Model):
    # 在postgresql里储存的属性
    uuid = models.UUIDField(db_column='UUID', primary_key=True, editable=False)
    Imp = models.IntegerField(db_column='IMP', default=0)
    Hot = models.IntegerField(db_column='HOT', default=0)
    StrLevel = models.FloatField(db_column='STR', default=0)
    ClaLevel = models.IntegerField(db_column='CLA', default=0)
    ImportMethod = models.CharField(db_column='IMPORT_METHOD', max_length=30)
    ImportTime = models.DateTimeField(db_column='IMPORT_TIME', default=now)
    IncludedMedia = ArrayField(models.URLField(), db_column='INCLUDED_MEDIA', default=list)  # 包含的多媒体文件url
    FeatureVec = models.TextField(db_column='FEATURE_VECTOR', default='0')  # 特征值
    CreateUser = models.IntegerField(db_column='USER', default='0')  # 创建用户
    Is_Common = models.BooleanField(db_column='COMMON', default=True)
    Is_Used = models.BooleanField(db_column='USED', default=True)

    class Meta:
        db_tablespace = 'nodes'
        db_table = 'nodes_ctrl'


class BaseNode(models.Model):
    uuid = models.UUIDField(db_column='UUID', primary_key=True, editable=False)

    class Meta:
        db_tablespace = 'nodes'
        db_table = 'base_node'


class Person(BaseNode):
    PeriodStart = models.DateField(db_column='PERIOD_START')
    PeriodEnd = models.DateField(db_column='PERIOD_END')
    BirthPlace = models.CharField(db_column='BIRTHPLACE', max_length=30)
    Nation = models.CharField(db_column='NATION', max_length=30, default='None')

    class Meta:
        db_table = 'person'


class Project(BaseNode):
    PeriodStart = models.DateField(db_column='PERIOD_START')
    PeriodEnd = models.DateField(db_column='PERIOD_END')
    Location = models.TextField(db_column='LOCATION')
    Longitude = models.FloatField(db_column='LONGITUDE', default=tool.getLocation(Location)[0])
    Latitude = models.FloatField(db_column='LATITUDE', default=tool.getLocation(Location)[1])
    Nation = models.TextField(db_column='NATION', max_length=30)

    class Meta:
        db_table = 'project'


class ArchProject(Project):
    Architect = ArrayField(models.TextField(), db_column='ARCHITECT')

    class Meta:
        db_table = 'arch_project'


class Media(models.Model):
    uuid = models.UUIDField(db_column='UUID', primary_key=True)
    Description = models.TextField(db_column='DESCRIPTION', default='None')
    ImportMethod = models.CharField(db_column='IMPORT_METHOD', max_length=30)
    ImportTime = models.DateTimeField(db_column='IMPORT_TIME', default=now)
    ImportUser = models.IntegerField(db_column='IMPORT_USER', default=0)
    CreateUser = models.IntegerField(db_column='USER', default='0')
    Content = models.URLField(db_column='CONTENT', default='')

    class Meta:
        db_tablespace = 'medias'
        abstract = True


class Paper(Media):
    Tags = ArrayField(JSONField(), db_column='TAGS', default=list)
    Rels = ArrayField(JSONField(), db_column='RELS', default=list)

    class Meta:
        db_table = 'paper'
