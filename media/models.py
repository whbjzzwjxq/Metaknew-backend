from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from django.utils.timezone import now
# Create your models here.


class Media(models.Model):
    uuid = models.UUIDField(db_column='UUID', primary_key=True)
    Description = models.TextField(db_column='DESCRIPTION', default='None')
    ImportMethod = models.CharField(db_column='IMPORT_METHOD', max_length=30)
    ImportTime = models.DateTimeField(db_column='IMPORT_TIME', default=now)
    ImportUser = models.IntegerField(db_column='IMPORT_USER', default=0)
    CreateUser = models.IntegerField(db_column='USER', default='0')
    Content = models.URLField(db_column='CONTENT', default='')

    class Meta:
        db_tablespace = 'medias'
        abstract = True


class Paper(Media):
    Tags = ArrayField(JSONField(), db_column='TAGS', default=list)
    Rels = ArrayField(JSONField(), db_column='RELS', default=list)

    class Meta:
        db_table = 'paper'
