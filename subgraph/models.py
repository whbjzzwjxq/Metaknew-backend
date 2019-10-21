from django.contrib.postgres.fields import ArrayField, JSONField, HStoreField
from django.db import models
from users.models import User
from django.utils.timezone import now
from tools.models import LevelField, TopicField, HotField, NameField, TranslateField, TimeField, LocationField


# 将可能的模板写在前面
def contributor():
    return {"create": "system", "update": []}


def feature_vector():
    return {"group_vector": [],
            "word_embedding": [],
            "label_embedding": []}


# remake 20191017
class NodeCtrl(models.Model):
    NodeId = models.BigIntegerField(primary_key=True, editable=False)
    IsUsed = models.BooleanField(default=True)
    # 不传回的控制性内容
    CountCacheTime = models.DateTimeField(db_column="CacheTime", default=now)  # 最后统计的时间
    Is_UserMade = models.BooleanField(db_column="UserMade", db_index=True)  # 是否是用户新建的
    ImportMethod = models.TextField(db_column="ImportMethod", db_index=True, default="Excel")  # 导入方式
    CreateTime = models.DateField(db_column="CreateTime", auto_now_add=True, editable=False)  # 创建时间
    # 直接传回的内容
    CreateUser = models.BigIntegerField(db_column="CreateUser", default="0", editable=False)  # 创建用户
    UpdateTime = models.DateField(db_column="UpdateTime", auto_now=True)  # 最后更新时间
    PrimaryLabel = models.TextField(db_column="Plabel", db_index=True)  # 主标签 注意干燥

    # 有意义的评价
    Imp = LevelField()  # 重要度
    HardLevel = LevelField()  # 难易度
    Useful = LevelField()  # 有用的程度
    Star = models.IntegerField(default=0)  # 收藏数量

    # 简易的评价
    IsGood = models.IntegerField(default=0)
    IsBad = models.IntegerField(default=0)

    # 其余参数
    Hot = HotField()
    Contributor = JSONField(default=contributor)  # 贡献者
    UserLabels = ArrayField(models.TextField(), db_column="UserLabels", default=list)  # 用户打的标签

    # 从数据分析统计的内容 更新频率 低
    Structure = LevelField()  # 结构化的程度
    FeatureVec = JSONField(default=feature_vector)  # 特征值
    TotalTime = models.IntegerField(db_column="TotalTime", default=50)  # 需要的时间

    class Meta:
        db_table = "graph_node_ctrl"


# remake 20191017
class NodeInfo(models.Model):
    NodeId = models.BigIntegerField(primary_key=True, editable=False)
    PrimaryLabel = models.TextField(db_column="Plabel", db_index=True)  # 主标签
    MainPic = models.TextField(default="")  # 缩略图/主要图片, 注意储存的是url
    IncludedMedia = ArrayField(models.BigIntegerField(), db_column="IncludedMedia", default=list)  # 包含的多媒体文件id
    ExtraProps = JSONField(db_column="ExtraProps", default=dict)  # 额外的属性
    # 以上不是自动处理

    # 直接迭代处理的Field
    Name = models.TextField(db_column="Name")
    Alias = ArrayField(NameField(), db_column="Alias", default=list)
    Topic = TopicField()
    Labels = ArrayField(models.TextField(), db_column="Labels", default=list, db_index=True)
    Text = TranslateField(default=dict)  # Description
    Translate = JSONField(default=dict)  # 名字的翻译
    BaseImp = LevelField()  # 基础重要度
    BaseHardLevel = LevelField()  # 基础难易度
    Language = models.TextField(db_column="Language", default="auto")

    # 写成abstract的理由 不在Info表里存 减小查询规模
    class Meta:
        abstract = True


# todo 更多标签 level: 1
# remake 2019-10-17
class Person(NodeInfo):
    DateOfBirth = TimeField(db_column="DateOfBirth")
    DateOfDeath = TimeField(db_column="DateOfDeath")
    BirthPlace = LocationField(db_column="BirthPlace", max_length=30)
    Nation = models.TextField(db_column="Nation", max_length=30)
    Job = models.TextField(db_column='Job', default='')
    Gender = models.TextField(db_column='Gender', default='Man', db_index=True)

    class Meta:
        db_table = "graph_node_person"


class Project(NodeInfo):
    PeriodStart = TimeField(db_column="Period_Start")
    PeriodEnd = TimeField(db_column="Period_End")
    Nation = models.TextField(db_column="Nation", max_length=30)
    Leader = ArrayField(NameField(), db_column="Leader", default=list)  # 领头人

    class Meta:
        db_table = "graph_node_project"


class ArchProject(NodeInfo):
    PeriodStart = TimeField(db_column="Period_Start")
    PeriodEnd = TimeField(db_column="Period_End")
    Nation = models.TextField(db_column="Nation", max_length=30)
    Leader = ArrayField(NameField(), db_column="Leader", default=list)  # 领头人
    Location = LocationField(db_column="Location", default="Beijing")
    WorkTeam = ArrayField(NameField(), db_column="WorkTeam", default=list)

    class Meta:
        db_table = "graph_node_arch_project"


# remake 2019-10-17
class BaseDocGraph(NodeInfo):
    # 主要是给Cache使用 也就是请求Graph信息可能用到
    MainNodes = ArrayField(models.BigIntegerField(), db_column="MainNodes", default=list)  # 主要节点的id
    Size = models.IntegerField(db_column="Size", default=1)  # 专题的规模
    Complete = LevelField()  # 计算得出

    class Meta:
        db_table = "graph_node_doc_base"


# 如果pLabel识别不了那么就使用基础模型
class NodeNormal(NodeInfo):
    class Meta:
        db_table = "graph_node_normal"


class MediaCtrl(models.Model):
    MediaId = models.BigIntegerField(primary_key=True)
    IsUsed = models.BooleanField(default=True)
    Is_UserMade = models.BooleanField(db_column="UserMade", db_index=True)  # 是否是用户新建的
    FileName = models.TextField(db_column="Name")  # 储存在阿里云OSS里的Name
    Format = models.TextField(db_column="Format", db_index=True)  # 储存在阿里云OSS里的format
    # 控制属性
    History = ArrayField(HStoreField(), default=list)  # 储存历史文件名
    CreateUser = models.BigIntegerField()
    UploadTime = models.DateTimeField(db_column="UploadTime", auto_now_add=True)
    CountCacheTime = models.DateTimeField(db_column='CountCacheTime', default=now)
    TotalTime = models.IntegerField(db_column="TotalTime", default=10)  # 需要的时间 主要是给音频和视频用的
    # 用户相关
    IsGood = models.BigIntegerField(default=0)
    IsBad = models.BigIntegerField(default=0)
    Star = models.BigIntegerField(default=0)
    Hot = HotField()
    UserLabels = ArrayField(models.TextField(), default=list, db_index=True)

    class Meta:
        db_table = 'graph_media_ctrl'


class MediaInfo(models.Model):
    MediaId = models.BigIntegerField(primary_key=True)
    Name = models.TextField(db_index=True, default="NewMedia")
    Labels = ArrayField(models.TextField(), db_column="Labels", default=list, db_index=True)
    Text = TranslateField()
    PrimaryLabel = models.TextField(db_index=True)

    class Meta:
        abstract = True


class Image(MediaInfo):
    Size = models.TextField(default='large')
    dpiX = models.IntegerField(default=1920)
    dpiY = models.IntegerField(default=1080)
    ContainObject = JSONField(default=dict)

    class Meta:
        db_table = 'graph_media_info_image'


class Text(MediaInfo):
    Pages = models.IntegerField(default=1)

    class Meta:
        db_table = 'graph_media_info_text'


class Audio(MediaInfo):
    class Meta:
        db_table = 'graph_media_info_audio'


class Video(MediaInfo):
    class Meta:
        db_table = 'graph_media_info_video'


# remake 2019-10-17
class Fragment(models.Model):
    NodeId = models.BigIntegerField(primary_key=True)
    Labels = ArrayField(models.TextField(), default=list)
    Content = ArrayField(models.TextField(), default=list)  # 少于16个字符作为Keyword处理
    ExtraProps = JSONField(default=dict)  # 主要是NLP识别用

    OriginSource = models.BigIntegerField(default=0)
    CreateTime = models.DateField(default=now)
    CreateUser = models.BigIntegerField(db_index=True)

    class Meta:
        db_table = "graph_node_fragment"


# remake 2019-10-17 2019-10-20
class RelationshipCtrl(models.Model):
    LinkId = models.BigIntegerField(primary_key=True)
    IsUsed = models.BooleanField(default=True)
    PrimaryLabel = models.TextField(db_index=True)
    Start = models.BigIntegerField(db_column="Start", db_index=True)
    End = models.BigIntegerField(db_column="End", db_index=True)
    Is_UserMade = models.BooleanField(db_column="Is_UserMade", db_index=True, default=True)
    CreateUser = models.BigIntegerField(db_column="CreatorId", db_index=True, default=0)
    CreateTime = models.DateTimeField(db_column="CreateTime", auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["Start", "End"], name="start_end")
        ]
        db_table = "graph_link_ctrl"


class RelationshipInfo(models.Model):
    LinkId = models.BigIntegerField(primary_key=True)
    PrimaryLabel = models.TextField(db_index=True)

    class Meta:
        abstract = True


# todo 日志聚合 level: 2
class FrequencyCount(RelationshipInfo):
    Count = models.IntegerField(db_column="Count", default=1)
    Frequency = models.FloatField(db_column="Frequency", default=0)
    UpdateTime = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["Start", "End", "Type"], name="unique_count_type")
        ]
        db_table = "graph_link_frequency"


# 专题和节点的连接
class Doc2Node(RelationshipInfo):
    Is_Main = models.BooleanField(db_column="Main", default=False)  # 是否是Main节点
    Correlation = models.IntegerField(db_column="Correlation", default=1)  # 相关度
    DocImp = models.IntegerField(db_column="DocImp", default=1)  # 节点在该话题下的重要度

    class Meta:
        db_table = "graph_link_doc2node"


# 图谱上的关系
class KnowLedge(RelationshipInfo):
    Confidence = models.SmallIntegerField(db_column="Confidence", default=50)
    # 被他人选中的次数
    SelectTimes = models.IntegerField(default=0)
    Star = models.IntegerField(default=0)
    Labels = ArrayField(models.TextField(), default=list)
    ExtraProps = JSONField(default=dict)
    Text = models.TextField(db_column="Content", default="")

    class Meta:
        db_table = "graph_link_knowledge"


# ----------------用户权限----------------

# 原则:
# 1 Common=False的Source 不暴露id和内容
# 2 Used=False的Source 拦截所有API
# 3 只有Owner才可以delete
# 4 ChangeState 是指可以改变状态的用户，拥有除了Delete外的全部权限
# 5 Collaborator 是指可以完全操作的用户
# 5 SharedTo 是指可以进行查询级别操作的用户


# done 07-22 remake 2019-10-21
# 控制主题


class BaseAuthority(models.Model):
    SourceId = models.BigIntegerField(primary_key=True)  # 资源id
    SourceType = models.TextField(db_index=True)
    # 状态
    Used = models.BooleanField(db_column="used", default=True)
    Common = models.BooleanField(db_column="common", default=True)
    Shared = models.BooleanField(db_column="shared", default=False)
    OpenSource = models.BooleanField(db_column="open", default=False)

    # 暂时默认
    Payment = models.BooleanField(db_column="payment", default=False)
    Vip = models.BooleanField(db_column="vip", default=False)
    HighVip = models.BooleanField(db_column="high_vip", default=False)

    class Meta:
        indexes = [
            models.Index(fields=["Used", "Common"])
        ]
        db_table = "graph_authority"
