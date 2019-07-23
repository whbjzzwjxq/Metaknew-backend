from django.db import models


class GlobalWordIndex(models.Model):

    id = models.AutoField(db_column='INDEX', primary_key=True)
    Word = models.TextField(db_column='WORD', db_index=True, unique=True)

    class Meta:
        db_table = 'global_word_index'


# block_size = 65535
# BlockManager: 一个体系的全局管理
# Node, Media使用PrimaryLabel的index作为划分依据
# Document, Comment之类的功能内容使用device作为划分依据
# Record之类的事务内容使用time作为划分依据
class BaseBlockManager(models.Model):

    id = models.AutoField(db_column='ID', primary_key=True)
    Classifier = models.IntegerField(db_column='LabelContent', db_index=True)
    RegisterTime = models.DateTimeField(db_column='RegisterTime', auto_now_add=True)

    class Meta:
        abstract = True


class NodeBlockManager(BaseBlockManager):
    class Meta:
        db_table = 'global_node_block'


class DeviceBlockManager(BaseBlockManager):
    class Meta:
        db_table = 'global_media_block'


class RecordBlockManager(BaseBlockManager):
    class Meta:
        db_table = 'global_private_block'


# 每个Block的管理记录
class BlockIdRecord(models.Model):

    BlockId = models.IntegerField(db_column='BLOCK_ID', db_index=True)
    OutId = models.BigIntegerField(db_column='OUT_ID', primary_key=True)

    class Meta:
        abstract = True


class NodeBlockIdRecord(BlockIdRecord):
    class Meta:
        db_table = 'global_node_block'


class DeviceBlockIdRecord(models.Model):

    class Meta:
        db_table = 'global_device_block'


class RecordBlockIdRecord(models.Model):

    class Meta:
        db_table = 'global_time_block'
