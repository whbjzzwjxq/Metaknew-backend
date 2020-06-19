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


def type_check(value):
    available_type = ['node', 'media', 'link', 'text', 'document', 'fragment', 'note']
    if value not in available_type:
        raise ValidationError('_type %(value) is not available', params={'value': value})


def default_text():
    return {
        "auto": ""
    }


class IdField(models.BigIntegerField):
    description = "IdField"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TypeField(models.TextField):
    description = 'TypeField'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        kwargs["validators"] = [type_check]


class HotField(models.IntegerField):
    description = "热度Field"

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
# Document, Comment之类的功能内容使用device作为划分依据
# Record之类的事务内容使用time作为划分依据
# 全局唯一
class BaseBlockManager(models.Model):
    BlockId = models.AutoField(db_column="BlockId", primary_key=True)
    RegisterTime = models.DateTimeField(db_column="RegisterTime", auto_now_add=True)
    RegisterDevice = models.IntegerField(db_index=True)

    class Meta:
        abstract = True


class NodeBlockManager(BaseBlockManager):
    class Meta:
        db_table = "block_manager_node"


class LinkBlockManager(BaseBlockManager):
    class Meta:
        db_table = "block_manager_link"


class DeviceBlockManager(BaseBlockManager):
    class Meta:
        db_table = "block_manager_device"


class TimeBlockManager(BaseBlockManager):
    class Meta:
        db_table = "block_manager_time"


# 每个Block的管理记录 例如Block5 OutId 20 就是第五个Block的id=20位置已经使用
# 每个机器有一份
class BlockIdRecord(models.Model):
    BlockId = models.IntegerField(db_column="BLOCK_ID", db_index=True)
    OutId = models.BigIntegerField(db_column="OUT_ID", primary_key=True)

    class Meta:
        abstract = True


class NodeBlockIdRecord(BlockIdRecord):
    class Meta:
        db_table = "block_record_node"


class LinkBlockIdRecord(BlockIdRecord):
    class Meta:
        db_table = "block_record_link"


class DeviceBlockIdRecord(BlockIdRecord):
    class Meta:
        db_table = "block_record_device"


class TimeBlockIdRecord(BlockIdRecord):
    class Meta:
        db_table = "block_record_time"


# 暂时未使用 word的Index
class GlobalWordIndex(models.Model):
    WordIndex = models.AutoField(db_column="Index", primary_key=True)
    Word = models.TextField(db_column="Word", db_index=True, unique=True, editable=False)

    class Meta:
        db_table = "source_global_word_index"


# 以下是更加基础的资源 地理位置映射 / 名字翻译 / 描述文件记录
# done
class LocationDoc(models.Model):
    FileId = models.AutoField(db_column="LocationFile", primary_key=True)
    Name = models.TextField(db_column="Name", default="Beijing")
    LocId = models.TextField(db_column="LocId", default="ChIJ58KMhbNLzJQRwfhoMaMlugA", db_index=True)
    Alias = ArrayField(models.TextField(), db_column="Alias", default=list, db_index=True)
    Doc = JSONField(db_column="Content", default=dict)

    class Meta:
        db_table = "source_location_doc"


class Chronology(models.Model):
    FileId = models.BigIntegerField(primary_key=True)
    PeriodStart = models.DateField(db_column="Start", null=True)
    PeriodEnd = models.DateField(db_column="End", null=True)
    Content = models.TextField(db_column="Content")

    class Meta:
        db_table = "source_chronology"
