from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.utils.timezone import now
from django.forms.models import model_to_dict

from base_api.interface_frontend import QueryObject
from tools.models import LevelField, TopicField, HotField, NameField, TranslateField, IdField, TypeField
from users.models import User
from typing import List
from time import mktime


def feature_vector():
    return {
        "group_vector": [],
        "word_embedding": [],
        "label_embedding": []
    }


# ----------------用户权限----------------

# 原则:
# 1 Common=False的Source 不暴露id和内容
# 2 Used=False的Source 拦截所有API
# 3 只有Owner才可以delete
# 4 ChangeState 是指可以改变状态的用户，拥有除了Delete外的全部权限
# 5 Collaborator 是指可以完全操作的用户
# 5 SharedTo 是指可以进行查询级别操作的用户

class BaseInfo(models.Model):
    ItemId = IdField(primary_key=True, editable=False)  # id
    ItemType = TypeField(default='node', db_index=True, editable=False)  # ItemType
    PrimaryLabel = models.TextField(db_column="Plabel", db_index=True, editable=False)  # 主标签
    Name = NameField(db_column="Name")  # 名字
    Labels = ArrayField(models.TextField(), db_column="Labels", default=list, db_index=True)  # 创建者的标签
    Description = TranslateField()  # Description
    Translate = TranslateField()
    ExtraProps = JSONField(db_column="ExtraProps", default=dict)  # 额外属性
    StandardProps = JSONField(default=dict)  # 标准属性

    @staticmethod
    def prop_not_to_dict():
        # 从BaseInfo中去除的Field
        return ['ItemId', 'ItemType']

    @staticmethod
    def special_update() -> List[str]:
        """
        不自动生成的内容
        :return:
        """
        return ['ItemId', 'ItemType']

    @classmethod
    def saved_fields(cls):
        return [field.name for field in cls._meta.fields
                if field.name not in cls.prop_not_to_dict() and not field.auto_created]

    def to_dict(self, exclude):
        if not exclude:
            exclude = BaseInfo.prop_not_to_dict()
        content = model_to_dict(self, exclude=exclude)
        content.update({
            'id': self.ItemId,
            'type': self.ItemType,
            'PrimaryLabel': self.PrimaryLabel
        })
        return content

    def to_query_object(self):
        return {
            '_id': self.ItemId,
            '_type': self.ItemType,
            '_label': self.PrimaryLabel
        }

    class Meta:
        abstract = True


class BaseCtrl(models.Model):
    CREATE_TYPE_CHOICES = [
        ('AUTO', 'SystemAuto'),
        ('USER', 'UserMade'),
        ('OFF', 'Official'),
        ('REAL', 'RealSource')
    ]
    ItemId = IdField(primary_key=True, editable=False)
    ItemType = models.TextField(db_index=True, editable=False)  # Item的Type
    PrimaryLabel = models.TextField(db_index=True, editable=False)  # 主标签
    CreateType = models.TextField(default='USER', choices=CREATE_TYPE_CHOICES, editable=False)  # 新建方式
    CreateUser = models.BigIntegerField(default=1, editable=False)  # 创建用户
    CreateTime = models.DateField(auto_now_add=True, editable=False)  # 创建时间
    UpdateTime = models.DateField(auto_now=True, editable=False)  # 更新时间
    PropsWarning = JSONField(default=list)  # 属性更新警告
    IsUsed = models.BooleanField(default=True)  # 是否在使用

    @staticmethod
    def prop_not_to_dict():
        # 从BaseInfo中去除的Field
        return ['ItemId', 'ItemType', 'PrimaryLabel', 'CreateTime', 'UpdateTime', 'IsUsed',
                'PropsWarning']

    @classmethod
    def saved_fields(cls):
        return [field.name for field in cls._meta.fields
                if field.name not in cls.prop_not_to_dict() and not field.auto_created]

    def to_dict(self, exclude: List[str] = None):
        if not exclude:
            exclude = BaseCtrl.prop_not_to_dict()
        content = model_to_dict(self, exclude=exclude)
        content.update({
            'UpdateTime': mktime(self.UpdateTime.timetuple()),
            'CreateUser': self.CreateUser
        })
        return content

    class Meta:
        abstract = True


class PublicItem(models.Model):
    IsCommon = models.BooleanField(default=True, db_index=True)  # 是否公开
    IsShared = models.BooleanField(default=False, db_index=True)  # 是否分享
    IsOpenSource = models.BooleanField(default=False, db_index=True)  # 是否公开编辑
    Hot = HotField()  # 热度
    Labels = ArrayField(models.TextField(), default=list)  # 统计的用户标签
    NumStar = models.IntegerField(default=0)  # 收藏数量
    NumShared = models.IntegerField(default=0)  # 分享数量
    NumGood = models.IntegerField(default=0)  # 点赞数量
    NumBad = models.IntegerField(default=0)  # 点踩数量

    class Meta:
        abstract = True


class PublicItemCtrl(BaseCtrl, PublicItem):
    class Meta:
        abstract = True

    @staticmethod
    def props_update_by_user():
        return ['IsCommon', 'IsOpenSource', 'IsShared']


# remake 20191017
class NodeCtrl(PublicItemCtrl):
    CountCacheTime = models.DateTimeField(db_column="CacheTime", default=now)  # 最后统计的时间

    # 有意义的评价
    Imp = LevelField()  # 重要度
    HardLevel = LevelField()  # 难易度
    Useful = LevelField()  # 有用的程度
    # 其余参数
    Contributor = ArrayField(IdField(), default=list)  # 贡献者
    # 从数据分析统计的内容 更新频率 低
    Structure = LevelField()  # 数据完整的程度
    FeatureVec = JSONField(default=feature_vector)  # 特征值
    TotalTime = models.IntegerField(db_column="TotalTime", default=50)  # 需要的时间

    @staticmethod
    def prop_not_to_dict():
        return PublicItemCtrl.prop_not_to_dict() + ['CountCacheTime', 'FeatureVec', 'Structure']

    class Meta:
        db_table = "item_node_ctrl"


# remake 20191017
class NodeInfo(BaseInfo):
    # 直接迭代处理的Field
    Alias = ArrayField(NameField(), db_column="Alias", default=list)
    Topic = TopicField()
    BaseImp = LevelField()  # 基础重要度
    BaseHardLevel = LevelField()  # 基础难易度
    BaseUseful = LevelField()  # 基础有用程度
    Language = models.TextField(db_column="Language", default="auto")

    # 以下不是自动处理
    MainPic = models.TextField(default="")  # 缩略图/主要图片, 注意储存的是url
    IncludedMedia = ArrayField(IdField(), db_column="IncludedMedia", default=list)  # 包含的多媒体文件id

    @staticmethod
    def special_update() -> List[str]:
        field_list = BaseInfo.special_update()
        field_list.extend(['Alias', 'Topic', 'BaseImp', 'BaseHardLevel', 'BaseUseful', 'Language', 'Translate'])
        return field_list

    class Meta:
        db_table = 'item_node_info'


class MediaCtrl(PublicItemCtrl):
    ItemType = TypeField(default='media')  # Item的Type
    FileName = models.TextField()  # 储存在阿里云OSS里的Name
    Format = models.TextField(db_column="Format", db_index=True)  # 储存在阿里云OSS里的format
    Thumb = models.TextField(default="")  # 缩略图
    # 控制属性
    CountCacheTime = models.DateTimeField(db_column='CountCacheTime', default=now)
    TotalTime = models.IntegerField(db_column="TotalTime", default=10)  # 需要的时间 主要是给音频和视频用的

    class Meta:
        db_table = 'item_media_ctrl'


class MediaInfo(BaseInfo):
    ItemType = TypeField(default='media')  # Item的Type

    @staticmethod
    def prop_not_to_dict():
        # 从BaseInfo中去除的Field
        parent_list = BaseInfo.prop_not_to_dict()
        parent_list.extend(['PrimaryLabel'])
        return parent_list

    class Meta:
        db_table = 'item_media_info'


class FragmentInfo(BaseInfo):
    Src = models.TextField(default='')  # 如果是图片, 那么有来源
    # PrimaryLabel = 'text' | 'image'

    class Meta:
        db_table = "item_fragment_info"


class FragmentCtrl(BaseCtrl):
    SourceId = IdField(db_index=True)
    SourceType = TypeField(db_index=True)
    SourceLabel = models.TextField()
    IsLinked = models.BooleanField(default=False)

    class Meta:
        db_table = "item_fragment_ctrl"


# remake 2019-10-17 2019-10-20
class RelationshipCtrl(BaseCtrl):
    ItemType = TypeField(default='link')  # Item的Type
    StartId = IdField(db_index=True)
    EndId = IdField(db_index=True)
    StartType = TypeField()
    EndType = TypeField()
    StartPLabel = models.TextField()
    EndPLabel = models.TextField()

    def query_object(self) -> List[QueryObject]:
        return [
            QueryObject(**{'id': self.StartId, 'type': self.StartType, 'pLabel': self.StartPLabel}),
            QueryObject(**{'id': self.EndId, 'type': self.EndType, 'pLabel': self.EndPLabel})
        ]

    @staticmethod
    def prop_not_to_dict():
        return BaseCtrl.prop_not_to_dict() + ['StartId', 'StartType', 'StartPLabel', 'EndId', 'EndType', 'EndPLabel']

    def to_dict(self, exclude: List[str] = None):
        if not exclude:
            exclude = RelationshipCtrl.prop_not_to_dict()
        content = model_to_dict(self, exclude=exclude)
        content.update({
            'Start': {
                'id': self.StartId,
                'type': self.StartType,
                'PrimaryLabel': self.StartPLabel
            },
            'End': {
                'id': self.EndId,
                'type': self.EndType,
                'PrimaryLabel': self.EndPLabel
            },
            'CreateUser': self.CreateUser
        })
        return content

    class Meta:
        abstract = True


class RelationshipInfo(BaseInfo):

    class Meta:
        db_table = "item_link_info"


# systemMade 没有info!!!
class FrequencyCount(RelationshipCtrl):
    Count = models.IntegerField(db_column="Count", default=1)
    Frequency = models.FloatField(db_column="Frequency", default=0)

    class Meta:
        db_table = "item_link_ctrl_frequency"


# 专题和节点的连接
class DocToNode(RelationshipCtrl):
    IsMain = models.BooleanField(db_column="Main", default=False)  # 是否是Main节点
    Correlation = LevelField(db_column="Correlation")  # 相关度
    DocumentImp = LevelField(db_column="DocImp")  # 节点在该话题下的重要度

    @staticmethod
    def props_to_neo():
        return ['CreateTime', 'IsUsed', 'IsMain', 'Correlation', 'ItemId']

    class Meta:
        db_table = "item_link_ctrl_doc_to_node"


# 图谱上的关系
class KnowLedge(RelationshipCtrl, PublicItem):
    Confidence = models.SmallIntegerField(db_column="Confidence", default=50)
    SelectTimes = models.IntegerField(default=0)  # 被他人选中的次数

    class Meta:
        db_table = "item_link_ctrl_knowledge"
