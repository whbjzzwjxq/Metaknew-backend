from django.db import models
from django.contrib.postgres.fields import ArrayField


# Create your models here.


class DocAuthority(models.Model):
    uuid = models.UUIDField(db_column='uuid', primary_key=True)  # 专题uuid
    Owner = models.IntegerField(db_column='createUser')  # 专题所有人的id
    ChangeState = ArrayField(models.IntegerField(), db_column='changeStatePrivilege', default=list)  # 拥有修改状态权限的用户
    SharedTo = ArrayField(models.IntegerField(), db_column='SharePrivilege', default=list)  # 分享给的用户
    query = ArrayField(models.IntegerField(), db_column='readPrivilege', default=list)  # 拥有读权限的用户
    write = ArrayField(models.IntegerField(), db_column='writePrivilege', default=list)  # 拥有写权限的用户
    reference = ArrayField(models.IntegerField(), db_column='referencePrivilege', default=list)  # 拥有引用权限的用户
    delete = ArrayField(models.IntegerField(), db_column='deletePrivilege', default=list)  # 拥有删除权限的用户
    export = ArrayField(models.IntegerField(), db_column='exportPrivilege', default=list)  # 拥有导出权限的用户
    payment = ArrayField(models.IntegerField(), db_column='exportPrivilege', default=list)  # 已经支付的用户

    Common = models.BooleanField(db_column='common', default=True)
    Shared = models.BooleanField(db_column='shared', default=False)
    Paid = models.BooleanField(db_column='paid', default=False)

    class Meta:
        db_tablespace = 'authority'
        db_table = 'doc_authority'

