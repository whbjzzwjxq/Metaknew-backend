from django.db import models
from django.contrib.postgres.fields import JSONField
from tools.models import IdField
from document.models import DocGraph
from tools.models import TypeField


def default_graph():
    return {
        'Nodes': [],
        'Links': [],
        'Medias': [],
        'Svgs': [],
        'Conf': {}
    }


class TransRecord(models.Model):
    RecordId = models.AutoField(db_column="Trans", primary_key=True)
    Lang = models.TextField(db_column="TYPE", db_index=True)  # 语言类型
    Name = models.TextField(db_column="NAME")  # 基础内容 Name
    Is_Done = models.BooleanField(db_column="DONE")  # 是否完成

    # 是指从Name翻译到Lang的情况失败了
    class Meta:
        db_table = "record_translation"


class LocationsRecord(models.Model):
    RecordId = models.AutoField(db_column="Locations", primary_key=True)
    Location = models.TextField(db_column="NAME")  # 基础内容 Name
    Is_Done = models.BooleanField(db_column="DONE", default=False)  # 是否完成

    class Meta:
        db_table = "record_location"


class BaseRecord(models.Model):
    SourceId = models.BigIntegerField(editable=False, db_index=True)
    SourceType = TypeField(db_index=True, editable=False)
    SourceLabel = models.TextField(db_index=True, default='')
    UpdateTime = models.DateTimeField(auto_now=True, editable=False)
    CreateUser = IdField(editable=False)
    CreateType = models.TextField(default='USER')

    Name = models.TextField(db_column="Name", default='Draft')  # 草稿的名字
    IsUsed = models.BooleanField(default=True)  # 是否被删除
    DontClear = models.BooleanField(default=False)  # 是否不要清除
    Content = JSONField(default=dict)

    class Meta:
        abstract = True


class ItemVersionRecord(BaseRecord):
    """
    记录json content 但是是版本
    """
    VersionId = models.IntegerField(default=1)

    def to_query_object(self):
        return {
            '_id': self.SourceId,
            '_type': self.SourceType,
            '_label': self.SourceLabel
        }

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["SourceId", "VersionId"], name="ItemVersionControl")
        ]
        db_table = "record_item_version"


class ItemDraft(BaseRecord):
    """
    草稿形式的记录
    """
    IsAuto = models.BooleanField(default=False)  # 是否是自动生成的

    def to_query_object(self):
        return {
            '_id': '$_' + str(self.SourceId),
            '_type': self.SourceType,
            '_label': self.SourceLabel
        }

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["SourceId", "CreateUser"], name="ItemDraftControl")
        ]
        db_table = "record_item_draft"


class GraphVersionRecord(models.Model):
    DocId = IdField(primary_key=True)  # 专题ID
    CreateUser = models.BigIntegerField(db_column="User", editable=False, db_index=True)
    CreateTime = models.DateTimeField(auto_now=True, editable=False)
    BranchId = models.IntegerField(db_column="VersionId", default=0)  # 分支的Id
    BranchName = models.TextField(default='NewBranch')  # 分支的名字
    BranchDescription = models.TextField(default='')  # 分支描述
    IsUsed = models.BooleanField(default=True)  # 是否正在使用
    IsMerged = models.BooleanField(default=False)  # 是否合并
    IsCurrent = models.BooleanField(default=False)  # 是否是当前的内容
    Content = JSONField(default=default_graph)  # Content

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["DocId", "BranchId"], name="GraphVersionControl")
        ]
        db_table = "record_document_graph_branch"
