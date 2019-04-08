from django.contrib.postgres.fields import *
from py2neo import *
from django.db import models


class BaseNode(models.Model):
    uuid = models.UUIDField(db_column='UUID', primary_key=True)
    Description = models.TextField(db_column='DESCRIPTION')
    Imp = models.IntegerField(db_column='IMP')
    Hot = models.IntegerField(db_column='HOT')
    StrLevel = models.FloatField(db_column='STR')
    ClaLevel = models.IntegerField(db_column='CLA')
    ImportMethod = models.CharField(db_column='IMPORT', max_length=30)
    UserId = models.IntegerField(db_column='USER_ID')

    class Meta:
        db_table = 'BASE_NODE'


class Person(BaseNode):
    PeriodStart = models.DateField(db_column='PERIOD_START')
    PeriodEnd = models.DateField(db_column='PERIOD_END')
    BirthPlace = models.CharField(db_column='BIRTHPLACE', max_length=30)
