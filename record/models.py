from django.db import models
from django.contrib.postgres.fields import JSONField, ArrayField


# done in 07-25
class SourceAddRecord(models.Model):

    SourceId = models.BigIntegerField(db_column="SourceId", primary_key=True)
    SourceLabel = models.TextField(db_column="Label", db_index=True, default=0)
    BugType = models.TextField(db_column="Type")
    CreateUser = models.BigIntegerField(db_column="User")
    CreateTime = models.DateTimeField(db_column="Time", auto_now_add=True)
    Is_Solved = models.BooleanField(db_column="Solved", db_index=True, default=False)

    class Meta:
        abstract = True


class ErrorRecord(SourceAddRecord):
    OriginData = JSONField(db_column="CONTENT", default=dict)

    class Meta:
        db_table = "history_error_record"


class WarnRecord(SourceAddRecord):

    WarnContent = ArrayField(JSONField(), db_column="Content", default=list)

    class Meta:
        db_table = "history_warn_record"


class TransRecord(models.Model):
    RecordId = models.AutoField(db_column="Trans", primary_key=True)
    Lang = models.TextField(db_column="TYPE", db_index=True)  # 语言类型
    Name = models.TextField(db_column="NAME")  # 基础内容 Name
    Is_Done = models.BooleanField(db_column="DONE")  # 是否完成

    # 是指从Name翻译到Lang的情况失败了
    class Meta:
        db_table = "history_trans_record"


class LocationsRecord(models.Model):
    RecordId = models.AutoField(db_column="Locations", primary_key=True)
    Location = models.TextField(db_column="NAME")  # 基础内容 Name
    Is_Done = models.BooleanField(db_column="DONE", default=False)  # 是否完成

    class Meta:
        db_table = "history_loc_record"


# todo version branch level: 2 todo 压缩记录 level: 1
class NodeVersionRecord(models.Model):
    CreateUser = models.BigIntegerField(db_column="User", editable=False)
    CreateTime = models.DateTimeField(auto_now_add=True, editable=False)
    SourceId = models.BigIntegerField(db_column="SourceId", editable=False, db_index=True)
    SourceType = models.TextField(db_column="Type", editable=False)

    Name = models.TextField(db_column="Name")
    VersionId = models.SmallIntegerField(db_column="VersionId")
    Is_Draft = models.BooleanField(db_column="Draft", db_index=True)
    Content = JSONField(db_column="Content")

    class Meta:
        indexes = [
            models.Index(fields=["SourceId", "Is_Draft"])
        ]
        constraints = [
            models.UniqueConstraint(fields=["SourceId", "VersionId"], name="NodeVersionControl")
        ]
        db_table = "history_version_record"


class DocumentVersionRecord(models.Model):
    CreateUser = models.BigIntegerField(db_column="User", editable=False)
    CreateTime = models.DateTimeField(auto_now_add=True, editable=False)
    SourceId = models.BigIntegerField(db_column="SourceId", editable=False, db_index=True)
    SourceType = models.TextField(db_column="Type", editable=False, default="Document")

    Name = models.TextField(db_column="Name")
    VersionId = models.SmallIntegerField(db_column="VersionId")
    Is_Draft = models.BooleanField(db_column="Draft", db_index=True)
    BaseHistory = models.BigIntegerField(db_column="BaseHis", db_index=True)
    GraphContent = JSONField(db_column="GraphContent")
    PaperContent = JSONField(db_column="PaperContent")

    class Meta:
        indexes = [
            models.Index(fields=["SourceId", "Is_Draft"])
        ]
        constraints = [
            models.UniqueConstraint(fields=["SourceId", "VersionId"], name="DocVersionControl")
        ]
        db_table = "history_doc_version_record"
