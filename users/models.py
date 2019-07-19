from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import ArrayField
# Create your models here.


class User(models.Model):

    UserId = models.AutoField(db_column='USER_ID', primary_key=True)  # 用户id
    UserName = models.TextField(db_column='USER_NAME', unique=True)  # 用户名
    UserPw = models.TextField(db_column='USER_PASSWORD')  # 用户密码
    UserEmail = models.TextField(db_column='USER_EMAIL')  # 用户邮箱
    UserPhone = models.CharField(db_column='USER_PHONE', max_length=11, unique=True)  # 用户手机号（用于登录的账号）
    DateTime = models.DateTimeField(db_column='USER_TIME', auto_now_add=True)  # 注册时间
    Is_Superuser = models.BooleanField(db_column='ROOT', default=False)  # 是否是管理员
    Is_Developer = models.BooleanField(db_column='DEV', default=False)  # 开发账号
    Is_Active = models.BooleanField(db_column='ACTIVE', default=True)
    Is_Banned = models.BooleanField(db_column='BANNED', default=False)

    class Meta:

        db_table = 'user_info_base'


class UserRole(models.Model):

    UserId = models.IntegerField(db_column='USER_ID', primary_key=True)
    Is_Member = models.BooleanField(db_column='MEMBER', default=False)
    Is_Organizer = models.BooleanField(db_column='ORGANIZER', default=False)

    class Meta:

        db_table = 'user_info_role'


class UserCollection(models.Model):

    UserId = models.IntegerField(db_column='USER_ID', primary_key=True)
    Star = ArrayField(models.BigIntegerField(), db_column='STAR', default=list)
    CreateDoc = ArrayField(models.BigIntegerField(), db_column='CREATE', default=list)
    UploadSource = ArrayField(models.BigIntegerField(), db_column='UPLOAD', default=list)

    class Meta:

        db_table = 'user_collection'


class UserConcern(models.Model):

    UserId = models.IntegerField(db_column='USER_ID', primary_key=True)
    SourceId = models.BigIntegerField(db_column='SOURCE_ID')  # 用户打标签的内容
    Labels = ArrayField(models.TextField(), db_column='LABELS', default=list)  # 用户打的标签
    Imp = models.IntegerField(db_column='IMP', default=-1)
    HardLevel = models.IntegerField(db_column='HARD_LEVEL', default=-1)
    Useful = models.IntegerField(db_column='USEFUL', default=-1)

    class Meta:

        db_table = 'user_labels'


class Group(models.Model):
    GroupId = models.BigIntegerField(db_column='GROUP_ID', primary_key=True)
    GroupName = models.TextField(db_column='GROUP_NAME', unique=True)
    CreateUser = models.IntegerField(db_column='GROUP_CREATOR')
    Owner = models.IntegerField(db_column='OWNER')
    Manager = ArrayField(models.IntegerField(), db_column='MANAGER')
    Member = ArrayField(models.IntegerField(), db_column='Member')

    class Meta:

        db_table = 'user_group_info_base'
