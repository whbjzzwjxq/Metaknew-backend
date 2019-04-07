from peewee import *
from py2neo import *

post_gre_sql = PostgresqlDatabase("demomaster", user="postgres", password="123456", host="localhost", port="5432")


class BaseModel(Model):
    class Meta:
        database = post_gre_sql  # This model uses the "people.db" database.
# Create your models here.


class BaseNode(BaseModel):
    uuid = UUIDField(db_column='UUID')
    Description = CharField(db_column='DESCRIPTION')
    Imp = IntegerField(db_column='IMP')
    Hot = IntegerField(db_column='HOT')
    StrLevel = DoubleField(db_column='STR')
    ClaLevel = IntegerField(db_column='CLA')
    ImportMethod = CharField(db_column='IMPORT')
    UserId = IntegerField(db_column='')
