from django.db import models
from django.contrib.postgres.fields import  ArrayField, JSONField

# Create your models here.

class Path(models.Model):
    path_id = models.AutoField(db_column='PATH_ID', primary_key=True)  # 路径id
    path_title = models.TextField(db_column='PATH_TITLE')  # 路径题目
    path_document = ArrayField(JSONField(), db_column='PATH_DOCUMENT') # 路径包含的专题信息（uuid//uuid     Order//查看节点的顺序    Time//持续时间）
    path_info = JSONField(db_column='PATH_INFO')  # 路径具体信息（Create_User //创建用户    Imp//重要度    Hard_Level//难易度）

    class Meta:
        db_table = 'path'