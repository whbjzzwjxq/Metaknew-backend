from django.db import models
from django.contrib.postgres.fields import JSONField

from base_api.interface_frontend import QueryObject
from tools.models import IdField
from document.models import Document
from tools.models import TypeField


def default_graph():
    return {
        'Nodes': [],
        'Links': [],
        'Medias': [],
        'Texts': [],
        'Conf': {}
    }


class TransRecord(models.Model):
    RecordId = models.AutoField(db_column="Trans", primary_key=True)
    Lang = models.TextField(db_column="TYPE", db_index=True)  # 语言类型
    Name = models.TextField(db_column="NAME")  # 基础内容 Name
    IsDone = models.BooleanField(db_column="DONE")  # 是否完成

    class Meta:
        db_table = "record_translation"


class LocationsRecord(models.Model):
    RecordId = models.AutoField(db_column="Locations", primary_key=True)
    Location = models.TextField(db_column="NAME")  # 基础内容 Name
    IsDone = models.BooleanField(db_column="DONE", default=False)  # 是否完成

    class Meta:
        db_table = "record_location"


class ItemVersionRecord(models.Model):
    """
    记录json content 但是是版本
    """
    SourceId = models.BigIntegerField(editable=False, db_index=True)
    SourceType = TypeField(db_index=True, editable=False)
    SourceLabel = models.TextField(db_index=True, default='')
    VersionId = models.IntegerField(default=1)
    UpdateTime = models.DateTimeField(auto_now=True, editable=False)
    CreateUser = IdField(editable=False)
    CreateType = models.TextField(default='USER')

    Name = models.TextField(db_column="Name", default='Draft')  # 草稿的名字
    Content = JSONField(default=dict)  # 草稿的内容
    IsUsed = models.BooleanField(default=True)  # 是否被删除
    IsAuto = models.BooleanField(default=False)  # 是否是自动生成的
    IsDraft = models.BooleanField(default=True)  # 是否是草稿
    DontClear = models.BooleanField(default=False)  # 是否不要清除

    def to_query_object(self) -> QueryObject:
        return QueryObject({'id': self.SourceId, 'type': self.SourceType, 'pLabel': self.SourceLabel})

    @staticmethod
    def update_fields():
        return ['CreateUser', 'CreateType', 'Name', 'Content', 'IsUsed', 'IsAuto', 'IsDraft', 'DontClear']

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["SourceId", "VersionId"], name="ItemVersionControl")
        ]
        db_table = "record_item_version"


# class DocumentVersionRecord(models.Model):
#     ItemId = IdField()  # 专题Id
#     CreateUser = models.BigIntegerField(db_column="User", editable=False, db_index=True)
#     CreateTime = models.DateTimeField(auto_now=True, editable=False)
#     BranchId = IdField()  # 分支的Id
#     BranchName = models.TextField(default='NewBranch')  # 分支的名字
#     BranchDescription = models.TextField(default='')  # 分支描述
#     IsUsed = models.BooleanField(default=True)  # 是否正在使用
#     IsMerged = models.BooleanField(default=False)  # 是否合并
#     IsCurrent = models.BooleanField(default=False)  # 是否是当前的内容
#     Content = JSONField(default=default_graph)  # Content

#     class Meta:
#         constraints = [
#             models.UniqueConstraint(fields=["DocId", "BranchId"], name="GraphVersionControl")
#         ]
#         db_table = "record_document_document_branch"
