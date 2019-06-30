
# Create your models here.

from django.db import models

class history(models.Model):
    id = models.AutoField(db_column='id')
    userId = models.IntegerField(db_column='userId')  # 用户ID
    uuid = models.UUIDField(db_column='uuid')
    type = models.TextField(db_column='type')  # 操作的内容类型
    time = models.DateField(db_column='time')
    operation = models.TextField(db_column='operation')  # 具体执行的操作

    class Meta:
        db_table = 'History'
