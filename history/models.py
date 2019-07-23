from django.db import models
from django.contrib.postgres.fields import JSONField


# 查找缺漏使用 只在内部生成的时候使用 todo level: 2
class SourceAddRecord(models.Model):

    id = models.AutoField(db_column='ID', primary_key=True)
    Is_Error = models.BooleanField(db_column='ERROR', default=False, db_index=True)
    Is_Warn = models.BooleanField(db_column='WARN', default=False)
    SourceId = models.BigIntegerField(db_column='ID', db_index=True)
    SourceLabel = models.TextField(db_column='LABEL', db_index=True)
    Content = JSONField(db_column='CONTENT', default=dict)
    ContentType = models.TextField(db_column='TYPE')
    Time = models.DateTimeField(db_column='TIME', auto_now_add=True)
    Is_Solved = models.BooleanField(db_column='Solved', db_index=True)

    class Meta:
        db_table = 'history_source_add_record'


class TransRecord(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)
    Lang = models.TextField(db_column='TYPE', db_index=True)  # 语言类型
    Name = models.TextField(db_column='NAME')  # 基础内容 Name
    Is_Done = models.BooleanField(db_column='DONE')  # 是否完成

    # 是指从Name翻译到Lang的情况失败了
    class Meta:
        db_table = 'history_trans_record'


class LocationsRecord(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)
    Location = models.TextField(db_column='NAME')  # 基础内容 Name
    Is_Done = models.BooleanField(db_column='DONE', default=False)  # 是否完成

    # 是指从Name翻译到Lang的情况失败了
    class Meta:
        db_table = 'history_trans_record'


class UserEditRecord(models.Model):

    id = models.AutoField(db_column='ID', primary_key=True)
    EditTarget = models.BigIntegerField(db_column='')
    EditTime = models.DateTimeField(db_column='TIME', auto_now_add=True)


# todo version control level: 1
class VersionRecord(models.Model):

    id = models.AutoField(db_column='ID', primary_key=True)
    SourceId = models.BigIntegerField(db_column='UUID')
    SourceType = models.TextField(db_column='TYPE')
    Content = models.IntegerField(db_column='VERSION')

    class Meta:
        db_table = 'history_version_record'
