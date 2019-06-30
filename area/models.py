from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import ArrayField
# Create your models here.


class Area(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)
    areaname = models.TextField(db_column='AREA')
    relative_area = ArrayField(models.TextField(), db_column='RELATIVE_AREA')  #关联的area

    class Meta:
        db_table = 'area'
