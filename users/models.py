from __future__ import unicode_literals

from peewee import *

# Create your models here.

psql_db = PostgresqlDatabase("demomaster", user="postgres", password="123456", host="localhost", port="5432")

class BaseModel(Model):
    class Meta:
        database = psql_db # This model uses the "people.db" database.

class User(BaseModel):
    userid = AutoField(db_column='USER_ID', primary_key=True)
    username = TextField(db_column='USER_NAME')
    userpassword = TextField(db_column='USER_PASSWORD')

    class Meta:
        table_name = 'user'
