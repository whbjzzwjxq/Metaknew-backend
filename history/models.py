from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields import JSONField
# Create your models here.


class ExcelRecord(models.Model):

    uuid = models.UUIDField(db_column='UUID', primary_key=True)
    ExcelURL = models.URLField(db_column='URL')
    UserId = models.IntegerField(db_column='USER_ID')
    Nodes = ArrayField(models.UUIDField(), db_column='NODES')

    class Meta:

        db_table = 'excel_upload'


class SourceAddRecord(models.Model):

    id = models.AutoField(db_column='ID', primary_key=True)
    Is_Error = models.BooleanField(db_column='ERROR', default=False)
    Is_Warn = models.BooleanField(db_column='WARN', default=False)
    SourceId = models.UUIDField(db_column='UUID')
    SourceType = models.TextField(db_column='TYPE')
    Content = JSONField(db_column='CONTENT', default=dict)
    Time = models.DateTimeField(db_column='TIME', auto_now_add=True)

    class Meta:
        db_table = 'source_add_record'
