from django.db import models
from django.contrib.postgres.fields import ArrayField


# Create your models here.

class BaseAuthority(models.Model):

    id = models.BigIntegerField(db_column='id', primary_key=True)  # 资源uuid
    Owner = models.IntegerField(db_column='createUser', db_index=True)  # 专题所有人的id
    # 拥有修改状态权限的用户
    ChangeState = ArrayField(models.IntegerField(), db_column='changeStatePrivilege', default=list, db_index=True)
    # 分享给的用户
    SharedTo = ArrayField(models.IntegerField(), db_column='SharePrivilege', default=list, db_index=True)

    Query = ArrayField(models.IntegerField(), db_column='readPrivilege', default=list)  # 拥有读权限的用户
    Write = ArrayField(models.IntegerField(), db_column='writePrivilege', default=list)  # 拥有写权限的用户
    Delete = ArrayField(models.IntegerField(), db_column='deletePrivilege', default=list)  # 拥有删除权限的用户
    Export = ArrayField(models.IntegerField(), db_column='exportPrivilege', default=list)  # 拥有导出权限的用户

    Common = models.BooleanField(db_column='common', default=True)
    Shared = models.BooleanField(db_column='shared', default=False)
    Used = models.BooleanField(db_column='used', default=True)
    OpenSource = models.BooleanField(db_column='open', default=False)
    License = models.
    class Meta:
        abstract = True


class DocAuthority(BaseAuthority):

    Reference = ArrayField(models.IntegerField(), db_column='referencePrivilege', default=list)  # 拥有引用权限的用户
    Payment = ArrayField(models.IntegerField(), db_column='payment', default=list)  # 已经支付的用户

    Paid = models.BooleanField(db_column='paid', default=False)

    class Meta:
        db_table = 'authority_doc'


class NodeAuthority(BaseAuthority):

    class Meta:
        db_table = 'authority_node'


class MediaAuthority(BaseAuthority):

    DownLoad = ArrayField(models.IntegerField(), db_column='downloadPrivilege', default=list)
