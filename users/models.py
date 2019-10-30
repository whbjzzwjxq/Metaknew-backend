from django.db import models
from django.contrib.postgres.fields import ArrayField, HStoreField, JSONField
from tools.models import TopicField, LevelField

# Create your models here.


# todo 角色整理 level : 3
class User(models.Model):
    UserId = models.BigIntegerField(db_column="USER_ID", primary_key=True)  # 用户id
    UserName = models.TextField(db_column="USER_NAME", unique=True)  # 用户名
    UserPw = models.TextField(db_column="USER_PASSWORD")  # 用户密码
    UserEmail = models.TextField(db_column="USER_EMAIL")  # 用户邮箱
    UserPhone = models.CharField(db_column="USER_PHONE", max_length=11, unique=True)  # 用户手机号（用于登录的账号）
    DateTime = models.DateTimeField(db_column="USER_TIME", auto_now_add=True)  # 注册时间

    # 状态部分
    Is_Superuser = models.BooleanField(db_column="ROOT", default=False)  # 是否是管理员
    Is_Developer = models.BooleanField(db_column="DEV", default=False)  # 开发账号
    Is_Publisher = models.BooleanField(db_column="PUBLISH", default=False)  # 是否是发布者
    Is_Vip = models.BooleanField(db_column="VIP", default=False)
    Is_high_vip = models.BooleanField(db_column="HighVIP", default=False)
    # 用户控制
    Is_Active = models.BooleanField(db_column="Active", default=True)
    # 系统控制
    Is_Banned = models.BooleanField(db_column="Banned", default=False)
    # 参与的组别
    Joint_Group = HStoreField(db_column="JOINT_GROUP", default=dict)

    class Meta:
        db_table = "user_info_base"


# GroupId 与 UserId 使用同一个id_generator
class GroupCtrl(models.Model):
    GroupId = models.BigIntegerField(db_column="Group_Id", primary_key=True)
    GroupName = models.TextField(db_column="Group_Name", unique=True)
    CreateUser = models.BigIntegerField(db_column="Create_User")
    Owner = models.BigIntegerField(db_column="Owner")
    Manager = ArrayField(models.BigIntegerField(), db_column="Manager")
    Member = ArrayField(models.BigIntegerField(), db_column="Member")
    Topic = TopicField()
    Labels = ArrayField(models.TextField(), default=list)
    Is_Auto = models.BooleanField(db_column="Auto", default=False)
    Is_Open = models.BooleanField(db_column="Open", default=True)

    class Meta:
        db_table = "user_info_base_group"


# 用户/组 权限
class Privilege(models.Model):
    # 注意GroupId和UserId不能重复 因此生成的时候使用同一个IdBlock
    UserId = models.BigIntegerField(primary_key=True, db_index=True)
    # 是拥有者的资源
    Is_Owner = ArrayField(models.BigIntegerField(), db_column="Owner", default=list)
    # 拥有修改状态权限的资源
    Is_Manager = ArrayField(models.BigIntegerField(), db_column="Manager", default=list)
    # 拥有完整权限的资源
    Is_Collaborator = ArrayField(models.BigIntegerField(), db_column="Coll", default=list)
    # 获得的分享
    Is_SharedTo = ArrayField(models.BigIntegerField(), db_column="ShareTo", default=list)
    # 可以免费使用的资源
    Is_FreeTo = ArrayField(models.BigIntegerField(), db_column="FreeTo", default=list)
    # 已经购买了的资源
    Is_Paid = ArrayField(models.BigIntegerField(), db_column="Paid", default=list)

    class Meta:
        db_table = "user_authority_count"


# 用户私有仓库 remake 2019-10-20
class UserRepository(models.Model):
    """
    记录所有用户创建的内容的表
    """
    UserId = models.IntegerField(primary_key=True)
    # 以下是CommonSource
    CreateDoc = ArrayField(models.BigIntegerField(), default=list)
    CreateNode = ArrayField(models.BigIntegerField(), default=list)
    CreateCourse = ArrayField(models.BigIntegerField(), default=list)
    CreateFile = ArrayField(models.BigIntegerField(), default=list)
    CreatePath = ArrayField(models.BigIntegerField(), default=list)
    CreateLink = ArrayField(models.BigIntegerField(), default=list)
    CreateTopic = ArrayField(models.BigIntegerField(), default=list)
    # 以下是PrivateSource
    Fragments = ArrayField(models.BigIntegerField(), default=list)
    Notes = ArrayField(models.BigIntegerField(), default=list)
    Comments = ArrayField(models.BigIntegerField(), default=list)

    class Meta:
        db_table = "user_info_collection"


# 用户关注的内容 更加宽泛一些
class UserConcern(models.Model):
    UserId = models.BigIntegerField(db_index=True)
    # 用户关心的Source
    SourceId = models.BigIntegerField(db_index=True)
    SourceType = models.TextField(db_index=True)

    Labels = ArrayField(models.TextField(), default=list)
    Imp = LevelField()
    HardLevel = LevelField()
    Useful = LevelField()
    Is_Star = models.BooleanField(default=False)  # 是否收藏
    Is_Good = models.BooleanField(default=False)  # 是否点赞
    Is_Shared = models.BooleanField(default=False)  # 是否分享给别人
    SpendTime = models.IntegerField(db_column="SpendTime", default=0)  # 花费的时间

    class Meta:
        indexes = [
            models.Index(fields=["SourceId", "SourceType"])
        ]
        db_table = "user_info_concern"


# todo 用户进度记录 level: 2
class UserDocProgress(models.Model):
    UserId = models.BigIntegerField(db_column="UserId", db_index=True)
    # 用户查看的专题
    SourceId = models.BigIntegerField(db_column="SourceId", db_index=True)
    SourceType = models.TextField(db_column="SourceType", db_index=True)
    SpendTime = models.IntegerField(db_column="SpendTime")
    LastPart = models.BigIntegerField(db_column="LastPart")  # 上次最后停在哪个位置

    class Meta:
        db_table = "user_info_progress"


class UserDraft(models.Model):
    UserId = models.BigIntegerField(db_column="UserId", db_index=True)
    SourceId = models.BigIntegerField(db_column="SourceId", db_index=True)
    SourceType = models.TextField(db_column="SourceType", db_index=True)
    VersionId = models.IntegerField()  # 版本

    Name = models.TextField()
    UpdateTime = models.DateTimeField(db_column="UpdateTime", auto_now=True)  # 最后更新时间
    Content = JSONField(default=dict)
    DontClear = models.BooleanField(default=False)
    Deleted = models.BooleanField(default=False)  # 是否被删除

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["SourceId", "VersionId"], name="DraftVersionControl")
        ]
        db_table = "user_draft"
