from django.db import models


class GlobalWordIndex(models.Model):

    id = models.AutoField(db_column='INDEX', primary_key=True)
    Word = models.TextField(db_column='WORD', db_index=True, unique=True)

    class Meta:
        db_table = 'global_word_index'

# block_size = 65535


# Node使用PrimaryLabel作为block划分依据
class GlobalLabelBlock(models.Model):

    id = models.AutoField(db_column='ID', primary_key=True)
    PrimaryLabel = models.TextField(db_column='LabelContent', db_index=True)
    RegisterTime = models.DateTimeField(db_column='RegisterTime', auto_now_add=True)

    class Meta:
        db_table = 'global_label_block'


class LabelBlockId(models.Model):

    BlockId = models.IntegerField(db_column='BLOCK_ID', db_index=True)
    OutId = models.BigIntegerField(db_column='OUT_ID', primary_key=True)

    class Meta:
        db_table = 'global_node_id'


# Document, Note之类的内容使用device作为划分依据
class GlobalDeviceBlock(models.Model):

    id = models.AutoField(db_column='ID', primary_key=True)
    DeviceId = models.SmallIntegerField(db_column='DeviceId', db_index=True)
    RegisterTime = models.DateTimeField(db_column='RegisterTime', auto_now_add=True)

    class Meta:
        db_table = 'global_device_block'


class DeviceBlockId(models.Model):

    BlockId = models.IntegerField(db_column='BLOCK_ID', db_index=True)
    OutId = models.BigIntegerField(db_column='OUT_ID', primary_key=True)

    class Meta:
        db_table = 'global_device_id'
