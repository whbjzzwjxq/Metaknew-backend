from django.db import models
from django.contrib.postgres.fields import ArrayField, HStoreField, JSONField
from tools.models import TopicField, LevelField, IdField, TypeField, SettingField, NameField


def user_setting():
    return {
        'fragmentCollect': {},
    }


def note_content():
    setting = {
        "_title": "",
        "_content": ""
    }
    return setting


# todo 角色整理 level : 3
class User(models.Model):
    UserId = IdField(primary_key=True)  # 用户id
    Name = models.TextField(unique=True, db_index=True)  # 用户名
    UserPw = models.TextField()  # 用户密码
    Email = models.TextField(unique=True, db_index=True, null=True)  # 用户邮箱
    Phone = models.CharField(max_length=11, unique=True)  # 用户手机号（用于登录的账号）
    CreateTime = models.DateTimeField(auto_now_add=True)  # 注册时间
    Setting = JSONField(default=user_setting)  # 用户设置
    PersonalId = models.BigIntegerField(default=0)  # 记录一个用户创建内容的id
    # 状态部分
    IsSuperuser = models.BooleanField(default=False)  # 是否是管理员
    IsDeveloper = models.BooleanField(default=False)  # 开发账号
    IsPublisher = models.BooleanField(default=False)  # 是否是发布者
    IsVip = models.BooleanField(default=False)
    IsHighVip = models.BooleanField(default=False)
    IsGroup = models.BooleanField(default=False)
    # 用户控制
    IsActive = models.BooleanField(default=True)
    # 系统控制
    IsBanned = models.BooleanField(default=False)
    # 参与的组别
    JointGroup = HStoreField(default=dict)

    class Meta:
        db_table = "user_info_base_user"


# GroupId 与 UserId 使用同一个id_generator
class GroupCtrl(models.Model):
    GroupId = IdField(primary_key=True)
    GroupName = models.TextField(db_column="Group_Name", unique=True)
    CreateUser = models.BigIntegerField(db_column="Create_User")
    Owner = models.BigIntegerField(db_column="Owner")
    Manager = ArrayField(models.BigIntegerField(), db_column="Manager")
    Member = ArrayField(models.BigIntegerField(), db_column="Member")
    Topic = TopicField()
    Labels = ArrayField(models.TextField(), default=list)
    IsAuto = models.BooleanField(db_column="Auto", default=False)
    IsOpen = models.BooleanField(db_column="Open", default=True)

    class Meta:
        db_table = "user_info_base_group"


# 用户/组 权限
class Privilege(models.Model):
    # 注意GroupId和UserId不能重复 因此生成的时候使用同一个IdBlock
    UserId = IdField(primary_key=True)
    # 是拥有者的资源
    IsOwner = ArrayField(models.BigIntegerField(), db_column="Owner", default=list)
    # 拥有修改状态权限的资源
    IsManager = ArrayField(models.BigIntegerField(), db_column="Manager", default=list)
    # 拥有完整权限的资源
    IsCollaborator = ArrayField(models.BigIntegerField(), db_column="Coll", default=list)
    # 获得的分享
    IsSharedTo = ArrayField(models.BigIntegerField(), db_column="ShareTo", default=list)
    # 可以免费使用的资源
    IsFreeTo = ArrayField(models.BigIntegerField(), db_column="FreeTo", default=list)
    # 已经购买了的资源
    IsPaid = ArrayField(models.BigIntegerField(), db_column="Paid", default=list)

    class Meta:
        db_table = "user_authority_count"


# 用户关注的内容 更加宽泛一些
class UserConcern(models.Model):
    UserId = IdField(primary_key=True)
    # 用户关心的Source
    SourceId = IdField(db_index=True)
    SourceType = TypeField(db_index=True)
    SourceLabel = models.TextField()
    Labels = ArrayField(models.TextField(), default=list)
    Imp = LevelField()
    HardLevel = LevelField()
    Useful = LevelField()
    IsStar = models.BooleanField(default=False)  # 是否收藏
    IsGood = models.BooleanField(default=False)  # 是否点赞
    IsShared = models.BooleanField(default=False)  # 是否分享给别人
    IsBad = models.BooleanField(default=False)  # 是否点踩

    class Meta:
        indexes = [
            models.Index(fields=["SourceId", "SourceType"])
        ]
        db_table = "user_info_concern"


class UserItem(models.Model):
    UserId = IdField(db_index=True)
    ItemId = IdField(db_index=True)  # Item的id
    CreateTime = models.DateTimeField(auto_now_add=True)
    UpdateTime = models.DateTimeField(auto_now=True)
    IsUsed = models.BooleanField(default=True)  # 是否删除了

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['UserId', 'ItemId'], name='UserItemUnique')
        ]
        abstract = True


class Note(UserItem):
    DocumentId = IdField(db_index=True)  # 所属专题id
    Content = SettingField(default=note_content)  # 内容Dict

    class Meta:
        db_table = "user_item_note"


class NoteBook(UserItem):
    Name = NameField(default='')
    Text = models.TextField(default='')
    Svg = JSONField(default=dict)

    class Meta:
        db_table = "user_item_notebook"
