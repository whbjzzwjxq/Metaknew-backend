# -*-coding=utf-8 -*-
from users import models
import datetime as dt


# 新建用户
def add(filedata={}):
    user = models.User.objects.create(**filedata)
    return user


# 查询用户
def selectByPhone(user_phone):
    assert user_phone
    user = models.User.objects.filter(user_phone=user_phone)
    return user


# 修改用户资料
def updateById(filedata = {}):
    user_id = filedata['user_id']
    user = models.User.objects.filter(userid=user_id).update(**filedata)
    return user

# 根据user_id查询用户
def selectById(user_id):
    assert user_id
    user = models.User.objects.filter(user_id=user_id)
    return user

# 获取所有用户的id
def showAll():
    userIds = models.User.objects.all().values('user_id')
    return userIds


# 根据角色id查询对应用户id
def selectUserByRole(role_id):
    roleIds = models.User_Role.objects.filter(role_id=role_id)
    return roleIds
