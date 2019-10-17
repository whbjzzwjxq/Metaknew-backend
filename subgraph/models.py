from django.contrib.postgres.fields import ArrayField, JSONField, HStoreField
from django.db import models
from users.models import User
from django.utils.timezone import now
from tools.models import LevelField, TopicField, HotField


# 将可能的模板写在前面
def contributor():
    return {"create": "system", "update": []}


def feature_vector():
    return {"group_vector": [],
            "word_embedding": [],
            "label_embedding": []}

# global_word 储存不使用 可以使用在前后端交互节约流量 level: 1


# remake 20191017
class NodeCtrl(models.Model):
    NodeId = models.BigIntegerField(primary_key=True, editable=False)
    # 不传回的控制性内容
    CountCacheTime = models.DateTimeField(db_column="CacheTime", default=now)  # 最后统计的时间
    Is_UserMade = models.BooleanField(db_column="UserMade", db_index=True)  # 是否是用户新建的
    ImportMethod = models.TextField(db_column="ImportMethod", db_index=True, default="Excel")  # 导入方式
    CreateTime = models.DateField(db_column="CreateTime", auto_now_add=True, editable=False)  # 创建时间
    # 直接传回的内容
    CreateUser = models.BigIntegerField(db_column="CreateUser", default="0", editable=False)  # 创建用户
    UpdateTime = models.DateField(db_column="UpdateTime", auto_now=True)  # 最后更新时间
    PrimaryLabel = models.TextField(db_column="Plabel", db_index=True)  # 主标签 注意干燥

    # 从用户(UserConcern)那里统计的内容 更新频率 高
    Imp = LevelField()  # 重要度
    HardLevel = LevelField()  # 难易度
    Useful = models.IntegerField(db_column="Useful", default=-1)  # 有用的程度
    Star = models.IntegerField(db_column="Star", default=0)  # 收藏数量
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
    MainPic = models.BigIntegerField(db_column="Main", default=-1)  # 缩略图/主要图片, 注意储存的是id
    IncludedMedia = ArrayField(models.BigIntegerField(), db_column="IncludedMedia", default=list)  # 包含的多媒体文件id
    # 以上不是自动处理

    Name = models.TextField(db_column="Name")
    Text = JSONField(default=dict)
    Translate = JSONField(default=dict)
    Alias = ArrayField(models.TextField(), db_column="Alias", default=list)
    BaseImp = LevelField()  # 基础重要度
    BaseHardLevel = LevelField()  # 基础难易度
    Language = models.TextField(db_column="Language", default="auto")
    Topic = TopicField()
    Labels = ArrayField(models.TextField(), db_column="Labels", default=list, db_index=True)

    ExtraProps = HStoreField(db_column="ExtraProps", default=dict)

    class Meta:
        abstract = True
        db_table = "graph_node_info"


# todo 更多标签 level: 1
class Person(NodeInfo):
    DateOfBirth = models.TextField(db_column="DateOfBirth")
    DateOfDeath = models.TextField(db_column="DateOfDeath")
    BirthPlace = models.TextField(db_column="BirthPlace", max_length=30)
    Nation = models.TextField(db_column="Nation", max_length=30)
    Job = models.TextField(db_column='Job', default='')
    Gender = models.TextField(db_column='Gender', default='Man')

    class Meta:
        db_table = "graph_node_person"


class Project(NodeInfo):
    PeriodStart = models.TextField(db_column="Period_Start")
    PeriodEnd = models.TextField(db_column="Period_End")
    Nation = models.TextField(db_column="Nation", max_length=30)
    Leader = ArrayField(models.TextField(), db_column="Leader", default=list)  # 领头人

    class Meta:
        db_table = "graph_node_project"


class ArchProject(NodeInfo):
    PeriodStart = models.TextField(db_column="Period_Start")
    PeriodEnd = models.TextField(db_column="Period_End")
    Nation = models.TextField(db_column="Nation", max_length=30)
    Leader = ArrayField(models.TextField(), db_column="Leader", default=list)  # 领头人
    Location = models.TextField(db_column="Location", default="Beijing")
    WorkTeam = ArrayField(models.TextField(), db_column="WorkTeam", default=list)

    class Meta:
        db_table = "graph_node_arch_project"


class NodeNormal(NodeInfo):
    class Meta:
        db_table = "graph_node_normal"


# todo 更多media  level: 2
class MediaNode(models.Model):
    MediaId = models.BigIntegerField(primary_key=True)
    FileName = models.TextField(db_column="Name")  # 储存在阿里云OSS里的Name

    Title = models.TextField(db_index=True, default="NewMedia")
    Labels = ArrayField(models.TextField(), db_column="Labels", default=list, db_index=True)
    Text = JSONField(default=dict)

    Format = models.TextField(db_column="Format", db_index=True)
    MediaType = models.TextField(db_column="Type")

    # 控制属性
    UploadUser = models.BigIntegerField(db_column="UploadUser")
    UploadTime = models.DateTimeField(db_column="UploadTime", auto_now_add=True)
    CountCacheTime = models.DateTimeField(db_column='CountCacheTime', default=now)
    TotalTime = models.IntegerField(db_column="TotalTime", default=10)  # 需要的时间

    # 用户相关
    Useful = models.SmallIntegerField(db_column='Useful', default=0)
    Star = models.BigIntegerField(db_column='Star', default=0)
    Hot = HotField()

    class Meta:
        db_table = "graph_node_media_base"


class Fragment(models.Model):
    NodeId = models.BigIntegerField(primary_key=True)
    Keywords = ArrayField(models.TextField(), default=list)
    Content = models.TextField(default="")
    Props = JSONField(default=dict)
    Labels = ArrayField(models.TextField(), default=list)

    OriginSource = models.BigIntegerField(default=0)
    CreateTime = models.DateField(default=now)
    CreateUser = models.BigIntegerField()

    class Meta:
        db_table = "graph_node_fragment"


class Text(models.Model):
    NodeId = models.BigIntegerField(primary_key=True)
    Title = models.TextField(default="NewText")
    Text = JSONField(default=dict)
    Keywords = ArrayField(models.TextField(), default=list)
    Useful = models.SmallIntegerField(db_column='Useful', default=0)
    Star = models.BigIntegerField(default=0)
    Hot = HotField()

    class Meta:
        db_table = "graph_node_text"


# done 08-16
class BaseDoc(NodeInfo):
    MainNodes = ArrayField(models.BigIntegerField(), db_column="MainNodes", default=list)  # 主要节点的id
    Size = models.IntegerField(db_column="Size", default=1)  # 专题的规模
    Complete = LevelField()  # 计算得出

    class Meta:
        db_table = "graph_node_doc_base"


# 以下是更加基础的资源 地理位置映射 / 名字翻译 / 描述文件记录
# done
class LocationDoc(models.Model):
    FileId = models.AutoField(db_column="LocationFile", primary_key=True)
    Name = models.TextField(db_column="Name", default="Beijing")
    LocId = models.TextField(db_column="LocId", default="ChIJ58KMhbNLzJQRwfhoMaMlugA", db_index=True)
    Alias = ArrayField(models.TextField(), db_column="Alias", default=list, db_index=True)
    Doc = JSONField(db_column="Content", default=dict)

    class Meta:
        db_table = "graph_source_location_doc"


class Chronology(models.Model):
    FileId = models.BigIntegerField(primary_key=True)
    PeriodStart = models.DateField(db_column="Start", null=True)
    PeriodEnd = models.DateField(db_column="End", null=True)
    Content = models.TextField(db_column="Content")

    class Meta:
        db_table = "graph_source_chronology"


# 系统生成的控制性关系 done
SystemMade = ["Topic2Topic", "Topic2Node", "Doc2Node",
              "SearchTogether", "AfterVisit", "MentionTogether"]


class Relationship(models.Model):
    LinkId = models.BigIntegerField(primary_key=True)
    Start = models.BigIntegerField(db_column="Start", db_index=True)
    End = models.BigIntegerField(db_column="End", db_index=True)
    Is_UserMade = models.BooleanField(db_column="Is_UserMade", db_index=True, default=True)
    CreatorId = models.BigIntegerField(db_column="CreatorId", db_index=True, default=0)
    CreateTime = models.DateTimeField(db_column="CreateTime", auto_now_add=True)
    Type = models.TextField(db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["Start", "End"], name="start_end")
        ]
        abstract = True


# todo 日志聚合 level: 2
class FrequencyCount(Relationship):
    Count = models.IntegerField(db_column="Count", default=1)
    Frequency = models.FloatField(db_column="Frequency", default=0)
    UpdateTime = models.DateTimeField(auto_now=True)
    Action = models.TextField(default="SearchTogether")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["Start", "End", "Type"], name="unique_count_type")
        ]
        abstract = True


# 专题和节点的连接
class Doc2Node(Relationship):
    Is_Main = models.BooleanField(db_column="Main", default=False)  # 是否是Main节点
    Correlation = models.IntegerField(db_column="Correlation", default=1)  # 相关度
    DocImp = models.IntegerField(db_column="DocImp", default=1)  # 节点在该话题下的重要度

    class Meta:
        db_table = "graph_link_doc2node"


# 图谱上的关系
class KnowLedge(Relationship):
    Confidence = models.SmallIntegerField(db_column="Confidence", default=50)
    PrimaryLabel = models.TextField(default="Include")
    Labels = ArrayField(models.TextField(), default=list)
    ExtraProps = HStoreField(default=dict)
    Text = models.TextField(db_column="Content", default="")

    class Meta:
        db_table = "graph_link_knowledge"
