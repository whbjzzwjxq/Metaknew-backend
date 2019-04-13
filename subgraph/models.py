from django.contrib.postgres.fields import *
from py2neo import *
from django.db import models
from search.views import search_by_uuid

class BaseNode(models.Model):

    # 在postgresql里储存的属性
    uuid = models.UUIDField(db_column='UUID', primary_key=True)
    Description = models.TextField(db_column='DESCRIPTION')
    Imp = models.IntegerField(db_column='IMP')
    Hot = models.IntegerField(db_column='HOT')
    StrLevel = models.FloatField(db_column='STR')
    ClaLevel = models.IntegerField(db_column='CLA')
    ImportMethod = models.CharField(db_column='IMPORT', max_length=30)
    UserId = models.IntegerField(db_column='USER_ID')

    # 在neo4j里储存的属性
    def __init__(self, uuid):
        super().__init__()
        self.Node = search_by_uuid(uuid)
        
    class Meta:
        db_table = 'BASE_NODE'


class Person(BaseNode):
    PeriodStart = models.DateField(db_column='PERIOD_START')
    PeriodEnd = models.DateField(db_column='PERIOD_END')
    BirthPlace = models.CharField(db_column='BIRTHPLACE', max_length=30)

    class Meta:
        db_table = 'PERSON'



