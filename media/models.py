from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from django.utils.timezone import now
# Create your models here.


class MediaNode(models.Model):
    uuid = models.UUIDField(db_column='UUID', primary_key=True)
    FileName = models.TextField(db_column='NAME')
    Format = models.TextField(db_column='FORMAT')
    UploadUser = models.IntegerField(db_column='UPLOAD_USER')
    UploadTime = models.DateTimeField(db_column='UPLOAD_TIME', default=now)
    Description = models.TextField(db_column='DESCRIPTION', default='None')
    AbbrPic = models.URLField(db_column='CONTENT', default='')

    class Meta:

        db_table = 'normal_media'


class Paper(MediaNode):
    Tags = ArrayField(JSONField(), db_column='TAGS', default=list)
    Rels = ArrayField(JSONField(), db_column='RELS', default=list)

    class Meta:
        db_table = 'paper'
