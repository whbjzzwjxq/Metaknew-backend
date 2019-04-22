from django.contrib.postgres.fields import *
from py2neo import *
from django.db import models
from search.views import search_by_uuid


test = list


class BaseNode(models.Model):

    # 在postgresql里储存的属性
    uuid = models.UUIDField(db_column='UUID', primary_key=True)
    Description = models.TextField(db_column='DESCRIPTION', default='None')
    Imp = models.IntegerField(db_column='IMP')
    Hot = models.IntegerField(db_column='HOT')
    StrLevel = models.FloatField(db_column='STR')
    ClaLevel = models.IntegerField(db_column='CLA')
    ImportMethod = models.CharField(db_column='IMPORT', max_length=30)
    UserId = models.IntegerField(db_column='USER_ID')
    TestArray = ArrayField(models.IntegerField(), db_column='NUM')

    class Meta:
        abstract = True


class Person(BaseNode):
    PeriodStart = models.DateField(db_column='PERIOD_START')
    PeriodEnd = models.DateField(db_column='PERIOD_END')
    BirthPlace = models.CharField(db_column='BIRTHPLACE', max_length=30)
    Nation = models.CharField(db_column='NATION', max_length=30, default='None')

    class Meta:
        db_table = 'PERSON'


# class Architect(Person):
#     Projects = ArrayField(models.ForeignKey(to_field='Project', on_delete=models.CASCADE))


class Project(BaseNode):
    PeriodStart = models.DateField(db_column='PERIOD_START')
    PeriodEnd = models.DateField(db_column='PERIOD_END')
    Location = models.TextField(db_column='LOCATION')
    Nation = models.TextField(db_column='NATION', max_length=30)

    class Meta:
        db_table = 'PROJECT'


class ArchProject(Project):
    Architect = ArrayField(models.TextField(), db_column='ARCHITECT')

    class Meta:
        db_table = 'ARCH_PROJECT'
