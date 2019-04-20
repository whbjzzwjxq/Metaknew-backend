from __future__ import unicode_literals

from django.db import models
# import datetime as dt
from django.utils import timezone
# Create your models here.


class User(models.Model):
    user_id = models.AutoField(db_column='USER_ID', primary_key=True)  # 用户id
    username = models.TextField(db_column='USER_NAME')  # 用户名
    user_pw = models.TextField(db_column='USER_PASSWORD')  # 用户密码
    user_email = models.TextField(db_column='USER_EMAIL')  # 用户邮箱
    user_phone = models.CharField(db_column='USER_PHONE', max_length=11)  # 用户手机号（用于登录的账号）
    datetime = models.DateTimeField(db_column='USER_TIME', default=timezone.now())  # 注册时间

    class Meta:
        db_table = 'user'
