from django.db import models

# Create your models here.

# 便签
class Note(models.Model):
    id = models.AutoField(db_column="ID", primary_key=True)  # 便签id
    user_id = models.IntegerField(db_column="USER_ID")  # 用户id
    tags_type = models.TextField(db_column="TAGS_TYPE")  # 便签类型
    content = models.TextField(db_column="CONTENT")  # 便签内容
    document_id = models.UUIDField(db_column="DOCUMENT_ID")  # 所属专题uuid

    class Meta:
        db_table = 'note'