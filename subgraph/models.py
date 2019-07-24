from django.contrib.postgres.fields import *
from django.db import models
from users.models import User


# 将可能的模板写在前面
def contributor():
    return [{"user_id": 1, "level": 0}]


def feature_vector():
    return {"group_vector": [],
            "word_embedding": [],
            "label_embedding": []}

# global_word 使用值去压缩 常用且能用常识推断的字符串 目前只使用了PrimaryLabel LinkType 键值应该也是可以的


# 控制属性 不会直接update done
class NodeCtrl(models.Model):
    id = models.BigIntegerField(db_column='ID', primary_key=True, editable=False)
    # 不传回的控制性内容
    History = models.BigIntegerField(db_column='HISTORY', editable=False)  # 历史记录的编号
    CountCacheTime = models.DateTimeField(db_column='CACHE_TIME')  # 最后统计的时间
    NameTrans = models.BigIntegerField(db_column='Name_Trans')  # 名字翻译文件
    DescriptionTrans = models.BigIntegerField(db_column='Description_Trans')  # 名字翻译文件
    Is_UserMade = models.BooleanField(db_column='UserMade', db_index=True)  # 是否是用户新建的
    # 直接传回的内容
    CreateTime = models.DateField(db_column='TIME', auto_now_add=True, editable=False)
    CreateUser = models.BigIntegerField(db_column='USER', default='0', editable=False)  # 创建用户
    UpdateTime = models.DateTimeField(db_column='Update_Time', auto_now=True)  # 最后更新时间
    PrimaryLabel = models.IntegerField(db_column='P_LABEL', db_index=True)  # 主标签  # global_word

    # 从用户(UserConcern)那里统计的内容 更新频率 高
    Imp = models.IntegerField(db_column='IMP', default=0)
    HardLevel = models.IntegerField(db_column='HARD_LEVEL', default=0)  # 难易度
    Useful = models.IntegerField(db_column='USEFUL', default=0)  # 有用的程度
    Star = models.IntegerField(db_column='STAR', default=0)  # 收藏数量
    Contributor = ArrayField(JSONField(), db_column='CONTRIBUTOR', default=contributor())
    UserLabels = ArrayField(models.TextField(), db_column='USER_LABELS', default=list)

    # 从数据分析统计的内容 更新频率 低
    Hot = models.IntegerField(db_column='HOT', default=0)  # 热度统计
    Structure = models.IntegerField(db_column='STR', default=0)  # 结构化的程度
    FeatureVec = JSONField(db_column='FEATURE_VECTOR', default=feature_vector())  # 特征值

    class Meta:
        db_table = 'graph_node_ctrl'


# Node直接允许简单写入/传回的属性 done
class Node(models.Model):
    id = models.BigIntegerField(db_column='ID', primary_key=True, editable=False)
    Name = models.TextField(db_column='NAME')
    PrimaryLabel = models.IntegerField(db_column='P_LABEL', db_index=True)  # 主标签 注意干燥 # global_word
    Alias = ArrayField(models.TextField(), db_column='ALIAS', default=list)
    Language = models.TextField(db_column='LANG')
    Area = ArrayField(models.TextField(), db_column='AREA')
    Labels = ArrayField(models.TextField(), db_column='LABELS', default=list, db_index=True)
    ExtraProps = JSONField(db_column='EXTRA_PROPS', default=dict)
    MainPic = models.BigIntegerField(db_column='MAIN')  # 缩略图/主要图片
    Description = models.TextField(db_column='DESCRIPTION')
    IncludedMedia = ArrayField(models.BigIntegerField(), db_column='INCLUDED_MEDIA', default=list)  # 包含的多媒体文件id

    class Meta:
        db_table = 'graph_node_base'


# todo 更多标签 level: 1
class Person(Node):

    PeriodStart = models.TextField(db_column='PERIOD_START')
    PeriodEnd = models.TextField(db_column='PERIOD_END')
    BirthPlace = models.TextField(db_column='BIRTHPLACE', max_length=30)
    Nation = models.TextField(db_column='NATION', max_length=30)
    Chronology = models.BigIntegerField(db_column='Chronology')

    class Meta:
        db_table = 'graph_node_person'


class Project(Node):
    PeriodStart = models.TextField(db_column='PERIOD_START')
    PeriodEnd = models.TextField(db_column='PERIOD_END')
    Nation = models.TextField(db_column='NATION', max_length=30)
    Leader = ArrayField(models.TextField(), db_column='LEADER', default=list)  # 领头人

    class Meta:
        db_table = 'graph_node_project'


class ArchProject(Project):
    Location = models.TextField(db_column='LOCATION', default='Beijing')
    WorkTeam = ArrayField(models.TextField(), db_column='WORK_TEAM', default=list)

    class Meta:
        db_table = 'graph_node_arch_project'


# todo 更多media  level: 2
class MediaNode(models.Model):
    MediaId = models.BigIntegerField(db_column='ID', primary_key=True)
    FileName = models.TextField(db_column='NAME')
    Format = models.TextField(db_column='FORMAT')
    Url = models.URLField(db_column='URL', default='')
    UploadUser = models.BigIntegerField(db_column='UPLOAD_USER')
    UploadTime = models.DateTimeField(db_column='UPLOAD_TIME', auto_now_add=True)
    Description = models.TextField(db_column='DESCRIPTION', default='None')

    class Meta:
        db_table = 'graph_media_base'


# class Paper(MediaNode):
#     Tags = ArrayField(JSONField(), db_column='TAGS', default=list)
#     Rels = ArrayField(JSONField(), db_column='RELS', default=list)
#
#     class Meta:
#         db_table = 'media_paper'


# 以下是更加基础的资源 地理位置映射 / 名字翻译 / 描述文件记录
# done
class LocationDoc(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)
    Name = models.TextField(db_column='NAME', default='Beijing')
    LocId = models.TextField(db_column='LOC_ID', default='ChIJ58KMhbNLzJQRwfhoMaMlugA', db_index=True)
    Alias = ArrayField(models.TextField(), db_column='ALIAS', default=list, db_index=True)
    Doc = JSONField(db_column='DOC', default=dict)

    class Meta:
        db_table = 'source_location_doc'


# done
class Translate(models.Model):
    id = models.BigIntegerField(db_column='id', primary_key=True)
    auto = models.TextField(db_column='name', db_index=True)
    zh = models.TextField(db_column='name_zh')
    en = models.TextField(db_column='name_en')
    names = HStoreField(db_column='name_more')

    class Meta:
        db_table = 'source_translate'


# done
class Description(models.Model):

    id = models.BigIntegerField(db_column='id', primary_key=True)
    auto = models.TextField(db_column='description', db_index=True)
    zh = models.TextField(db_column='description_zh')
    en = models.TextField(db_column='description_en')
    descriptions = HStoreField(db_column='description_more')

    class Meta:

        db_table = 'source_description'


# 基准类 done
class Relationship(models.Model):

    LinkId = models.BigIntegerField(db_column='id', primary_key=True)
    Source = models.BigIntegerField(db_column='source', db_index=True)
    Target = models.BigIntegerField(db_column='target', db_index=True)
    CreateTime = models.DateTimeField(db_column='CreateTime')
    Type = models.IntegerField(db_index=True)  # global_word

    class Meta:

        abstract = True


# 系统生成的关系 Type = Doc2Node / SearchTogether / AfterVisit
class SystemMade(Relationship):

    Count = models.IntegerField(db_column='count', default=0)
    # todo 历史记录分析 level: 2

    class Meta:
        db_table = 'graph_link_sys'


# 图谱上的关系
class KnowLedgeGraph(Relationship):

    Time = models.TextField(db_column='Time', db_index=True)
    Location = models.TextField(db_column='Loc', db_index=True)
    PrimaryLabel = models.IntegerField(db_column='PLabel')  # global_word
    Props = JSONField(db_column='props', default=dict)
    Content = models.TextField(db_column='content')

    indexes = [
        models.Index(fields=['Time', 'Location'])
    ]

    class Meta:

        db_table = 'graph_link_knowledge'


class UserMade(KnowLedgeGraph):

    CreateUser = models.BigIntegerField(db_column='CreateUser', db_index=True)
    Confidence = models.SmallIntegerField(db_column='Confidence')

    class Meta:

        db_table = 'graph_link_user_made'
