from __future__ import unicode_literals

from peewee import *

# Create your models here.

psql_db = PostgresqlDatabase("demomaster", user="postgres", password="123456", host="localhost", port="5432")


class BaseModel(Model):
    class Meta:
        database = psql_db


class User(BaseModel):
    UserId = AutoField(db_column='USER_ID', primary_key=True)
    UserName = TextField(db_column='USER_NAME')
    UserPassword = TextField(db_column='USER_PASSWORD')

    class Meta:
        table_name = 'user'
