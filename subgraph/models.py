from django.contrib.postgres.fields import *
from django.db import models
from users.models import User


# 将可能的模板写在前面
def contributor():
    return [{"user_id": 1, "level": 10}]


def feature_vector():
    return {"group_vector": [],
            "word_embedding": [],
            "label_embedding": []}


def chronology():
    return [
        {
            "start": "",
            "end": "",
            "content": ""
        }
    ]


pictures = ['jpg', 'png', 'gif']
# todo 媒体文件格式 level: 1

# global_word 储存不使用 可以使用在前后端交互节约流量 level: 1


# 控制属性 不会直接update done
class NodeCtrl(models.Model):
    NodeId = models.BigIntegerField(primary_key=True, editable=False)
    # 不传回的控制性内容
    History = models.BigIntegerField(db_column='History')  # 当前版本的history标号
    CountCacheTime = models.DateTimeField(db_column='CACHE_TIME')  # 最后统计的时间
    Is_UserMade = models.BooleanField(db_column='UserMade', db_index=True)  # 是否是用户新建的
    # 直接传回的内容
    CreateTime = models.DateField(db_column='TIME', auto_now_add=True, editable=False)
    CreateUser = models.BigIntegerField(db_column='USER', default='0', editable=False)  # 创建用户
    UpdateTime = models.DateTimeField(db_column='UpdateTime', auto_now=True)  # 最后更新时间
    PrimaryLabel = models.TextField(db_column='P_LABEL', db_index=True)  # 主标签 注意干燥

    # 从用户(UserConcern)那里统计的内容 更新频率 高
    Imp = models.IntegerField(db_column='IMP', default=1)
    HardLevel = models.IntegerField(db_column='HARD_LEVEL', default=1)  # 难易度
    Useful = models.IntegerField(db_column='USEFUL', default=1)  # 有用的程度
    Star = models.IntegerField(db_column='STAR', default=0)  # 收藏数量
    Contributor = ArrayField(JSONField(), db_column='CONTRIBUTOR', default=contributor())
    UserLabels = ArrayField(models.TextField(), db_column='USER_LABELS', default=list)

    # 从数据分析统计的内容 更新频率 低
    Hot = models.IntegerField(db_column='Hot', default=1)  # 热度统计
    Structure = models.IntegerField(db_column='STR', default=1)  # 结构化的程度
    FeatureVec = JSONField(db_column='FEATURE_VECTOR', default=feature_vector())  # 特征值

    class Meta:
        db_table = 'graph_node_ctrl'


# Node直接允许简单写入/传回的属性 done
class NodeInfo(models.Model):
    NodeId = models.BigIntegerField(primary_key=True, editable=False)
    Name = models.TextField(db_column='Name')
    PrimaryLabel = models.TextField(db_column='Plabel', db_index=True)  # 主标签 注意干燥
    MainPic = models.BigIntegerField(db_column='Main')  # 缩略图/主要图片
    Description = models.TextField(db_column='Description')
    IncludedMedia = ArrayField(models.BigIntegerField(), db_column='IncludedMedia', default=list)  # 包含的多媒体文件id
    # 以上不是自动处理
    BaseImp = models.IntegerField(db_column='BaseImp', default=1)  # 基础重要度
    BaseHardLevel = models.IntegerField(db_column='BaseHardLevel', default=1)  # 基础难易度

    Alias = ArrayField(models.TextField(), db_column='Alias', default=list)
    Language = models.TextField(db_column='Language')
    Topic = ArrayField(models.TextField(), db_column='Topic')
    Labels = ArrayField(models.TextField(), db_column='Labels', default=list, db_index=True)
    ExtraProps = JSONField(db_column='ExtraProps', default=dict)

    class Meta:
        db_table = 'graph_node_base'


# todo 更多标签 level: 1
class Person(NodeInfo):
    DateOfBirth = models.TextField(db_column='DateOfBirth')
    DateOfDeath = models.TextField(db_column='DateOfDeath')
    BirthPlace = models.TextField(db_column='BirthPlace', max_length=30)
    Nation = models.TextField(db_column='Nation', max_length=30)

    class Meta:
        db_table = 'graph_node_person'


class Project(NodeInfo):
    PeriodStart = models.TextField(db_column='Period_Start')
    PeriodEnd = models.TextField(db_column='Period_End')
    Nation = models.TextField(db_column='Nation', max_length=30)
    Leader = ArrayField(models.TextField(), db_column='Leader', default=list)  # 领头人

    class Meta:
        db_table = 'graph_node_project'


class ArchProject(Project):
    Location = models.TextField(db_column='Location', default='Beijing')
    WorkTeam = ArrayField(models.TextField(), db_column='WorkTeam', default=list)
    Longitude = models.TextField(default='')
    Latitude = models.TextField(default='')

    class Meta:
        db_table = 'graph_node_arch_project'


# todo 更多media  level: 2
class MediaNode(models.Model):
    MediaId = models.BigIntegerField(primary_key=True)
    FileName = models.TextField(db_column='Name')
    Format = models.TextField(db_column='Format')
    MediaType = models.TextField(db_column='Type')
    Url = models.URLField(db_column='URL', default='')
    UploadUser = models.BigIntegerField(db_column='UploadUser')
    UploadTime = models.DateTimeField(db_column='UploadTime', auto_now_add=True)
    Description = models.TextField(db_column='Description', default='None')

    class Meta:
        db_table = 'graph_media_base'


# 以下是更加基础的资源 地理位置映射 / 名字翻译 / 描述文件记录
# done
class LocationDoc(models.Model):
    FileId = models.AutoField(db_column='LocationFile', primary_key=True)
    Name = models.TextField(db_column='Name', default='Beijing')
    LocId = models.TextField(db_column='LocId', default='ChIJ58KMhbNLzJQRwfhoMaMlugA', db_index=True)
    Alias = ArrayField(models.TextField(), db_column='Alias', default=list, db_index=True)
    Doc = JSONField(db_column='Content', default=dict)

    class Meta:
        db_table = 'source_location_doc'


# done
class Translate(models.Model):
    FileId = models.BigIntegerField(primary_key=True)
    Name_auto = models.TextField(db_column='Name', db_index=True, default='')
    Name_zh = models.TextField(db_column='Name_zh', default='')
    Name_en = models.TextField(db_column='Name_en', default='')
    Names = HStoreField(db_column='Name_more', default=dict)
    Des_auto = models.TextField(db_column='Description', db_index=True, default='')
    Des_zh = models.TextField(db_column='Description_zh', default='')
    Des_en = models.TextField(db_column='Description_en', default='')
    Descriptions = HStoreField(db_column='Description_more', default=dict)

    class Meta:
        db_table = 'source_translate'


class Chronology(models.Model):
    FileId = models.BigIntegerField(primary_key=True)
    PeriodStart = models.DateField(db_column='Start', null=True)
    PeriodEnd = models.DateField(db_column='End', null=True)
    Content = models.TextField(db_column='Content')
    
    class Meta:
        db_table = 'source_chronology'


# 基准类 done
# 系统生成的控制性关系
SystemMade = ["Topic2Topic", "Topic2Node", "Doc2Node",
              "SearchTogether", "AfterVisit", "MentionTogether"]


class Relationship(models.Model):
    LinkId = models.BigIntegerField(primary_key=True)
    Start = models.BigIntegerField(db_column='Start', db_index=True)
    End = models.BigIntegerField(db_column='End', db_index=True)
    CreateTime = models.DateTimeField(db_column='CreateTime', auto_now_add=True)
    Type = models.TextField(db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["Start", "End"], name="start_end")
        ]
        abstract = True


# todo 日志聚合 level: 2
class FrequencyCount(Relationship):

    Count = models.IntegerField(db_column='Count', default=1)
    Frequency = models.FloatField(db_column='Frequency', default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["Start", "End", "Type"], name="unique_count_type")
        ]
        abstract = True


class SearchTogether(FrequencyCount):

    class Meta:
        db_table = 'graph_link_search_tog'


class AfterVisit(FrequencyCount):
    class Meta:
        db_table = 'graph_link_visit_tog'


class MentionTogether(FrequencyCount):
    class Meta:
        db_table = "graph_link_mention_tog"


# start是father end是 child
class Topic2Topic(Relationship):
    Is_Parent = models.BooleanField(db_column='Parent', default=False)
    Correlation = models.IntegerField(db_column="Correlation", default=1)
    CommonSource = models.IntegerField(db_column='CommonSource', default=0)
    
    class Meta:
        db_table = 'graph_link_topic2topic'


# 话题与节点的连接
class Topic2Node(Relationship):
    Is_Main = models.BooleanField(db_column='Main', default=False)  # 是否是Main节点
    Correlation = models.IntegerField(db_column="Correlation", default=1)  # 相关度
    TopicImp = models.IntegerField(db_column="TopicImp", default=1)  # 节点在该话题下的重要度

    class Meta:
        db_table = 'graph_link_topic2node'


# 专题和节点的连接
class Doc2Node(Relationship):
    Is_Main = models.BooleanField(db_column='Main', default=False)  # 是否是Main节点
    Correlation = models.IntegerField(db_column="Correlation", default=1)  # 相关度

    class Meta:
        db_table = 'graph_link_doc2node'


# 图谱上的关系
class KnowLedge(Relationship):
    Is_UserMade = models.BooleanField(db_column='Is_UserMade', db_index=True)
    CreateUser = models.BigIntegerField(db_column='CreateUser', db_index=True)
    # todo LocationField level: 2
    PrimaryLabel = models.TextField(db_column='Plabel', db_index=True)
    Props = JSONField(db_column='Props', default=dict)
    Content = models.TextField(db_column='Content')
    LinkedSource = models.BigIntegerField(db_column='Linked')
    Confidence = models.SmallIntegerField(db_column='Confidence')

    class Meta:
        db_table = 'graph_link_knowledge'


class Event(KnowLedge):

    Time = models.TextField(db_column='Time', db_index=True)
    Location = models.TextField(db_column='Location', db_index=True)

    class Meta:
        db_table = 'graph_link_event'

