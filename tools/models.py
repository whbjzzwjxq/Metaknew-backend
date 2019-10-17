from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.postgres.fields import ArrayField, HStoreField, JSONField
from django.core.exceptions import ValidationError

# 预定义的Field和Checker
max_value = MaxValueValidator(limit_value=100)
min_value = MinValueValidator(limit_value=-1)


def setting_check(value):
    required_list = ["_id", "_type", "_label"]
    for word in required_list:
        if word not in value:
            raise ValidationError('setting need param %(key)s', params={'key': word})


def default_text():
    return {
        "auto": ""
    }


class HotField(models.IntegerField):
    description = "热度的Field"

    def __init__(self, *args, **kwargs):
        kwargs["default"] = 100
        kwargs["validators"] = [MinValueValidator(limit_value=1)]
        super().__init__(*args, **kwargs)


class LevelField(models.SmallIntegerField):
    description = "0-100百分制Field"

    def __init__(self, *args, **kwargs):
        kwargs["validators"] = [min_value, max_value]
        kwargs["default"] = -1
        super().__init__(*args, **kwargs)


class TopicField(ArrayField):
    description = "资源等使用的Topic, element是Topic"

    def __init__(self, *args, **kwargs):
        kwargs["default"] = list
        kwargs["db_index"] = True
        kwargs["base_field"] = models.TextField()
        super().__init__(*args, **kwargs)


class TranslateField(HStoreField):
    description = "允许翻译文本的Field"

    def __init__(self, *args, **kwargs):
        kwargs["default"] = default_text
        super().__init__(*args, **kwargs)


class SettingField(JSONField):
    description = "样式设置的Field"

    def __init__(self, *args, **kwargs):
        kwargs["validators"] = [setting_check]
        super().__init__(*args, **kwargs)


# resolveField
class NameField(models.TextField):
    description = "可能与名字有关的Field"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class LocationField(models.TextField):
    description = "可能与地名有关的Field"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TimeField(models.TextField):
    description = "可能与地名有关的Field"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


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


# 每个Block的管理记录 例如Block5 OutId 20 就是第五个Block的id=20位置已经使用
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


# 暂时未使用 word的Index
class GlobalWordIndex(models.Model):
    WordIndex = models.AutoField(db_column="Index", primary_key=True)
    Word = models.TextField(db_column="Word", db_index=True, unique=True, editable=False)

    class Meta:
        db_table = "global_word_index"
