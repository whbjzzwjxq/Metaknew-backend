# -*-coding=utf-8 -*-
from users import models
#
# def addRole(filedata={}):
#     role = models.Role.objects.create(**filedata)
#     return role
#
# def updateById(role_id, filedata={}):
#     assert role_id
#     role = models.Role.objects.filter(role_id=role_id).update(**filedata)
#     return role
#
# def deleteById(role_id):
#     assert role_id
#     role = models.Role.objects.filter(role_id=role_id).delete()
#     return role
#
# # 根据角色名称查询角色id
# def getIdByName(role_name):
#     assert role_name
#     role_id = models.User.objects.get(role_name=role_name)
#     return role_id
