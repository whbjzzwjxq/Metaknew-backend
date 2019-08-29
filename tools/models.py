from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.postgres.fields import HStoreField
from django.core.exceptions import ValidationError

# 预定义的Field和Checker

max_value = MaxValueValidator(limit_value=100)
min_value = MinValueValidator(limit_value=0)


class LevelField(models.SmallIntegerField):

    description = "0-100百分制Field"

    def __init__(self, *args, **kwargs):
        kwargs["validators"] = [min_value, max_value]
        kwargs["default"] = 1
        super().__init__(*args, **kwargs)


class TopicField(HStoreField):

    description = "资源等使用的Topic, key是Topic value是用户对Topic感兴趣的程度/资源跟Topic的相关度"

    def __init__(self, *args, **kwargs):
        kwargs["validators"] = [validate_topic]
        kwargs["default"] = dict
        kwargs["db_index"] = True
        super().__init__(*args, **kwargs)


class MediaIdField(models.BigIntegerField):

    description = "储存媒体文件使用的_id"


def validate_topic(value):
    for key in value:
        if not isinstance(key, str):
            raise ValidationError(_("%(value)s is not an string"), params={"value": key})
        elif not isinstance(value[key], int) or not isinstance(value[key], float):
            raise ValidationError(_("%(value)s is not an int/float"), params={"value": value[key]})


class GlobalWordIndex(models.Model):

    WordIndex = models.AutoField(db_column="Index", primary_key=True)
    Word = models.TextField(db_column="Word", db_index=True, unique=True, editable=False)

    class Meta:
        db_table = "global_word_index"


# block_size = 65535
# BlockManager: 一个体系的全局管理
# Node, Media使用PrimaryLabel的index作为划分依据
# Document, Comment之类的功能内容使用device作为划分依据
# Record之类的事务内容使用time作为划分依据
class BaseBlockManager(models.Model):

    BlockId = models.AutoField(db_column="BlockId", primary_key=True)
    Classifier = models.IntegerField(db_column="LabelContent", db_index=True)
    RegisterTime = models.DateTimeField(db_column="RegisterTime", auto_now_add=True)

    class Meta:
        abstract = True


class NodeBlockManager(BaseBlockManager):
    class Meta:
        db_table = "global_node_block_manager"


class DeviceBlockManager(BaseBlockManager):
    class Meta:
        db_table = "global_device_block_manager"


class RecordBlockManager(BaseBlockManager):
    class Meta:
        db_table = "global_private_block_manager"


# 每个Block的管理记录
class BlockIdRecord(models.Model):

    BlockId = models.IntegerField(db_column="BLOCK_ID", db_index=True)
    OutId = models.BigIntegerField(db_column="OUT_ID", primary_key=True)

    class Meta:
        abstract = True


class NodeBlockIdRecord(BlockIdRecord):
    class Meta:
        db_table = "device_node_block"


class DeviceBlockIdRecord(BlockIdRecord):

    class Meta:
        db_table = "device_device_block"


class RecordBlockIdRecord(BlockIdRecord):

    class Meta:
        db_table = "device_time_block"
