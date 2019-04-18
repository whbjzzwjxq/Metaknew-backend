from __future__ import unicode_literals

from django.db import models
# Create your models here.


class User(models.Model):
    userid = models.AutoField(db_column='USER_ID', primary_key=True)
    username = models.TextField(db_column='USER_NAME')
    userpw = models.TextField(db_column='USER_PASSWORD')
    useremail = models.TextField(db_column='USER_EMAIL')
    datetime = models.DateTimeField(db_column='USER_TIME')

    class Meta:
        db_table = 'user'
