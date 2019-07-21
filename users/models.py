from django.db import models
from django.contrib.postgres.fields import ArrayField, HStoreField

# Create your models here.


# todo 角色整理 level : 2
class User(models.Model):

    UserId = models.BigIntegerField(db_column='USER_ID', primary_key=True)  # 用户id
    UserName = models.TextField(db_column='USER_NAME', unique=True)  # 用户名
    UserPw = models.TextField(db_column='USER_PASSWORD')  # 用户密码
    UserEmail = models.TextField(db_column='USER_EMAIL')  # 用户邮箱
    UserPhone = models.CharField(db_column='USER_PHONE', max_length=11, unique=True)  # 用户手机号（用于登录的账号）
    DateTime = models.DateTimeField(db_column='USER_TIME', auto_now_add=True)  # 注册时间

    # 状态部分
    Is_Superuser = models.BooleanField(db_column='ROOT', default=False)  # 是否是管理员
    Is_Developer = models.BooleanField(db_column='DEV', default=False)  # 开发账号
    Is_Publisher = models.BooleanField(db_column='PUBLISH', default=False)  # 是否是发布者
    Is_Vip = models.BooleanField(db_column='VIP', default=False)
    Is_high_vip = models.BooleanField(db_column='HighVIP', default=False)

    # 兴趣部分
    # key: GroupId value: 0-Owner 1-Manager 2-Member 3-Applying
    Joint_Group = HStoreField(db_column='JOINT_GROUP')
    # 用户感兴趣的领域
    Area = ArrayField(models.TextField(), db_column='AREA', default=list)

    class Meta:

        db_table = 'user_info_base'


class GroupCtrl(models.Model):

    GroupId = models.BigIntegerField(db_column='Group_Id', primary_key=True)
    GroupName = models.TextField(db_column='Group_Name', unique=True)
    CreateUser = models.BigIntegerField(db_column='Create_User')
    Owner = models.BigIntegerField(db_column='Owner')
    Manager = ArrayField(models.BigIntegerField(), db_column='Manager')
    Member = ArrayField(models.BigIntegerField(), db_column='Member')
    Area = ArrayField(models.TextField(), default=list)
    Labels = ArrayField(models.TextField(), default=list)
    Is_Auto = models.BooleanField(db_column='Auto', default=False)
    Is_Open = models.BooleanField(db_column='Open', default=True)

    class Meta:

        db_table = 'user_group_info_base'


class Privilege(models.Model):

    # 注意GroupId和UserId不能重复 因此生成的时候使用同一个IdBlock
    Id = models.BigIntegerField(primary_key=True, db_index=True)
    # 用户控制
    Is_Active = models.BooleanField(db_column='ACTIVE', default=True)
    # 系统控制
    Is_Banned = models.BooleanField(db_column='BANNED', default=False)
    # 是拥有者的资源
    Is_Owner = ArrayField(models.BigIntegerField(), db_column='Owner', default=list)
    # 拥有修改状态权限的资源
    Is_Manager = ArrayField(models.BigIntegerField(), db_column='Manager', default=list)
    # 拥有完整权限的资源
    Is_Collaborator = ArrayField(models.BigIntegerField(), db_column='Coll', default=list)
    # 获得的分享
    Is_SharedTo = ArrayField(models.BigIntegerField(), db_column='ShareTo', default=list)
    # 可以免费使用的资源
    Is_FreeTo = ArrayField(models.BigIntegerField(), db_column='FreeTo', default=list)
    # 已经购买了的资源
    Is_Paid = ArrayField(models.BigIntegerField(), db_column='Paid', default=list)

    class Meta:
        db_table = 'user_authority_count'


# 用户私有仓库
class UserRepository(models.Model):

    UserId = models.IntegerField(db_column='USER_ID', primary_key=True)
    CreateDoc = ArrayField(models.BigIntegerField(), db_column='CreateDoc', default=list)
    CreateNode = ArrayField(models.BigIntegerField(), db_column='CreateNode', default=list)
    UpdateDoc = ArrayField(models.BigIntegerField(), default=list)
    UpdateNode = ArrayField(models.BigIntegerField(), default=list)
    UploadFile = ArrayField(models.BigIntegerField(), db_column='UPLOAD', default=list)

    class Meta:

        db_table = 'user_collection'


class UserConcern(models.Model):

    UserId = models.BigIntegerField(db_column='USER_ID', db_index=True)
    # 用户关心的Source
    SourceId = models.BigIntegerField(db_column='SOURCE_ID', db_index=True)
    SourceType = models.TextField(db_column='SOURCE_TYPE', db_index=True)
    # 用户打的标签
    Labels = ArrayField(models.TextField(), db_column='LABELS', default=list)
    Imp = models.SmallIntegerField(db_column='IMP', default=-1)
    HardLevel = models.SmallIntegerField(db_column='HARD_LEVEL', default=-1)
    Useful = models.SmallIntegerField(db_column='USEFUL', default=-1)
    Is_Star = models.BooleanField(db_column='STAR', default=False)

    class Meta:
        indexes = [
            models.Index(fields=['SourceId', 'SourceType'])
        ]
        db_table = 'user_labels'

