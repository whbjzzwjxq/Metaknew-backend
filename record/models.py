from django.db import models
from django.contrib.postgres.fields import JSONField, ArrayField, HStoreField


# done in 07-25
class SourceAddRecord(models.Model):

    SourceId = models.BigIntegerField(primary_key=True, db_index=True)
    SourceType = models.TextField()
    SourceLabel = models.TextField(db_index=True, default=0)
    BugType = models.TextField()
    CreateUser = models.BigIntegerField()
    CreateTime = models.DateTimeField(auto_now=True)
    Is_Solved = models.BooleanField(db_index=True, default=False)

    class Meta:
        abstract = True


class WarnRecord(SourceAddRecord):

    WarnContent = ArrayField(JSONField(), default=list)

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


class VersionRecord(models.Model):
    CreateUser = models.BigIntegerField(editable=False)
    CreateTime = models.DateTimeField(auto_now_add=True, editable=False)
    SourceId = models.BigIntegerField(editable=False, db_index=True)
    VersionId = models.IntegerField(default=1)
    SourceType = models.TextField(editable=False)
    SourceLabel = models.TextField(default='')
    Content = HStoreField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=["SourceId", "SourceType", "SourceLabel"])
        ]
        constraints = [
            models.UniqueConstraint(fields=["SourceId", "VersionId"], name="NodeVersionControl")
        ]
        db_table = "history_node_version_record"
