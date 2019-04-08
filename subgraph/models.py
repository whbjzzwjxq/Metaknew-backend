from django.contrib.postgres.fields import *
from py2neo import *
from django.db import models


class BaseNode(models.Model):
    uuid = models.UUIDField(db_column='UUID').primary_key
    Description = models.CharField(db_column='DESCRIPTION')
    Imp = models.IntegerField(db_column='IMP')
    Hot = models.IntegerField(db_column='HOT')
    StrLevel = models.FloatField(db_column='STR')
    ClaLevel = models.IntegerField(db_column='CLA')
    ImportMethod = models.CharField(db_column='IMPORT')
    UserId = models.IntegerField(db_column='')

    class Meta:
        db_table = 'BASE_NODE'


class DocNode(models.Model):
    uuid = models.UUIDField(db_column='UUID').primary_key
