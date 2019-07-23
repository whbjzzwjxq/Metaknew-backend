from django.db import models
from django.contrib.postgres.fields import ArrayField

# Create your models here.
# 原则:
# 1 Common=False的Source 不暴露id和内容
# 2 Used=False的Source 拦截所有API
# 3 只有Owner才可以delete
# 4 ChangeState 是指可以改变状态的用户，拥有除了Delete外的全部权限
# 5 Collaborator 是指可以完全操作的用户
# 5 SharedTo 是指可以进行查询级别操作的用户


# done in 07-22
class BaseAuthority(models.Model):

    id = models.BigIntegerField(db_column='id', primary_key=True, db_index=True)  # 资源uuid

    # 状态
    Used = models.BooleanField(db_column='used', default=True)
    Common = models.BooleanField(db_column='common', default=True)
    Shared = models.BooleanField(db_column='shared', default=False)
    OpenSource = models.BooleanField(db_column='open', default=False)
    Payment = models.BooleanField(db_column='payment', default=False)

    class Meta:
        abstract = True


class DocAuthority(BaseAuthority):

    class Meta:
        db_table = 'authority_doc'


class NodeAuthority(BaseAuthority):

    class Meta:
        db_table = 'authority_node'


class MediaAuthority(BaseAuthority):

    class Meta:
        db_table = 'authority_media'


# todo 支付管理 level: 3
# class PaymentManager(models.Model):
#
#     id = models.BigIntegerField(db_column='OrderId', primary_key=True)
#     SourceId = models.IntegerField(db_column='SourceId')
#     Success = models.BooleanField(db_column='Success')
#     Time = models.DateTimeField(db_column='Time', auto_now=True)
#     Price = models.FloatField(db_column='Price', default=0)
#     Free = models.FloatField(db_column='Free', default=1)
#
#     class Meta:
#         db_table = 'authority_payment'


# 注意这个表单只做统计信息用 权限检测在User下实现 done
class AuthorityCount(models.Model):
    id = models.BigIntegerField(db_column='id', primary_key=True)  # 资源uuid
    Owner = models.BigIntegerField(db_column='Owner', db_index=True)  # 专题所有人的id
    # 拥有修改状态权限的用户
    Manager = ArrayField(models.BigIntegerField(), db_column='Manager', default=list)
    # 拥有完整权限的用户
    Collaborator = ArrayField(models.BigIntegerField(), db_column='Coll', default=list)
    # 分享的用户
    SharedTo = ArrayField(models.BigIntegerField(), db_column='ShareTo', default=list)
    # 可以无偿使用的用户
    FreeTo = ArrayField(models.BigIntegerField(), db_column='FreeTo', default=list)

    class Meta:
        db_table = 'authority_count_user'
