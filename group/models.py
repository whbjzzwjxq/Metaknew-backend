from django.db import models
from django.contrib.postgres.fields import ArrayField
# Create your models here.


class Group(models.Model):
    GroupId = models.AutoField(db_column='GROUP_ID', primary_key=True)
    GroupName = models.TextField(db_column='GROUP_NAME', unique=True)
    CreateUser = models.IntegerField(db_column='GROUP_CREATOR')
    Owner = models.IntegerField(db_column='OWNER')
    Manager = ArrayField(models.IntegerField(), db_column='MANAGER')
    Member = ArrayField(models.IntegerField(), db_column='Member')

    class Meta:
        db_tablespace = 'group'
        db_table = 'group_info_base'
