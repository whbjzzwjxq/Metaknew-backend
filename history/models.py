from django.db import models
from django.contrib.postgres.fields import ArrayField
# Create your models here.


class ExcelRecord(models.Model):

    id = models.AutoField(db_column='ID', primary_key=True)
    ExcelURL = models.URLField(db_column='URL')
    UserId = models.IntegerField(db_column='USER_ID')
    Nodes = ArrayField(models.UUIDField(), db_column='NODES')

    class Meta:
        db_tablespace = 'history'
        db_table = 'excel_upload'
