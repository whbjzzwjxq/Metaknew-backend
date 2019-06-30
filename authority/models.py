from django.db import models
from django.contrib.postgres.fields import ArrayField
# Create your models here.


class authority(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)  #权限表的唯一标识id
    uuid = models.UUIDField(db_column='uuid')  # 专题uuid
    create_user = models.IntegerField(db_column='createUser')  # 专题创造人的id
    read_privilege = ArrayField(models.IntegerField(), db_column='readPrivilege', default=list)  # 拥有读权限的用户
    write_privilege = ArrayField(models.IntegerField(), db_column='writePrivilege', default=list)  # 拥有写权限的用户
    reference_privilege = ArrayField(models.IntegerField(), db_column='referencePrivilege', default=list)  # 拥有引用权限的用户
    delete_privilege = ArrayField(models.IntegerField(), db_column='deletePrivilege', default=list)  # 拥有删除权限的用户
    export_privilege = ArrayField(models.IntegerField(), db_column='exportPrivilege', default=list)  # 拥有导出权限的用户
    change_state_privilege = ArrayField(models.IntegerField(), db_column='changeStatePrivilege', default=list)  # 拥有修改状态权限的用户

    class Meta:
        db_table = 'Authority'

class doc_state(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)  # 权限状态表的唯一标识id
    uuid = models.UUIDField(db_column='uuid')  # 专题uuid
    common = models.BooleanField(db_column='common', default=True)
    shared = models.BooleanField(db_column='shared', default=False)
    paid = models.BooleanField(db_column='paid', default=False)
    private = models.BooleanField(db_column='private', default=False)

    class Meta:
        db_table = 'Doc_State'
