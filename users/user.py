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
def updateById(filedata):
    user_id = filedata['user_id']
    user = models.User.objects.filter(userid=userid).update(username=username, useremail=useremail, userpw=userpw)
    return user

#根据user_id查询用户
def selectById(id):
    assert id
    user = models.User.objects.filter(user_id=id)
    return user