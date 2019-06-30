from __future__ import unicode_literals

from django.db import models
# import datetime as dt
from django.utils.timezone import now
# Create your models here.


class User(models.Model):
    UserId = models.AutoField(db_column='USER_ID', primary_key=True)  # 用户id
    UserName = models.TextField(db_column='USER_NAME')  # 用户名
    UserPw = models.TextField(db_column='USER_PASSWORD')  # 用户密码
    UserEmail = models.TextField(db_column='USER_EMAIL')  # 用户邮箱
    UserPhone = models.CharField(db_column='USER_PHONE', max_length=11)  # 用户手机号（用于登录的账号）
    DateTime = models.DateTimeField(db_column='USER_TIME', default=now)  # 注册时间

    class Meta:
        db_tablespace = 'user'
        db_table = 'user_info_base'
