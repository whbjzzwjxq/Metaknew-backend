from django.db import models
from django.contrib.postgres.fields import ArrayField


# Create your models here.


class BaseAuthority(models.Model):

    uuid = models.UUIDField(db_column='uuid', primary_key=True)  # 资源uuid
    Owner = models.IntegerField(db_column='createUser')  # 专题所有人的id
    ChangeState = ArrayField(models.IntegerField(), db_column='changeStatePrivilege', default=list)  # 拥有修改状态权限的用户
    SharedTo = ArrayField(models.IntegerField(), db_column='SharePrivilege', default=list)  # 分享给的用户

    query = ArrayField(models.IntegerField(), db_column='readPrivilege', default=list)  # 拥有读权限的用户
    write = ArrayField(models.IntegerField(), db_column='writePrivilege', default=list)  # 拥有写权限的用户
    reference = ArrayField(models.IntegerField(), db_column='referencePrivilege', default=list)  # 拥有引用权限的用户
    delete = ArrayField(models.IntegerField(), db_column='deletePrivilege', default=list)  # 拥有删除权限的用户
    export = ArrayField(models.IntegerField(), db_column='exportPrivilege', default=list)  # 拥有导出权限的用户
    payment = ArrayField(models.IntegerField(), db_column='payment', default=list)  # 已经支付的用户
    source_type = models.TextField(db_column='type', default='Document')  # 权限针对的对象类型

    Common = models.BooleanField(db_column='common', default=True)
    Shared = models.BooleanField(db_column='shared', default=False)
    Paid = models.BooleanField(db_column='paid', default=False)

    class Meta:

        db_table = 'base_authority'
