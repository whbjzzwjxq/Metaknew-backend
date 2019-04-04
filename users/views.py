# -*-coding=utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse
from users.models import User
# Create your views here.


# 新建用户
def add_user(request):
    username = request.POST['username']
    userpw = request.POST['userpassword']
    user = User.create(username=username, userpassword=userpw)
    return render(request, 'add_user.html', {'user': user})


# 删除
def delete_user(request):
    userid = request.POST['userid']
    username = request.POST['username']
    userpw = request.POST['userpassword']
    User.delete().where(User.userid == userid or User.username == username or User.userpassword == userpw).execute()


# 修改用户
def update_user(request):
    userid = request.POST['userid']
    username = request.POST['username']
    userpw = request.POST['userpassword']
    User.update({User.username: username, User.userpassword: userpw}).where(User.userid == userid).execute()


# 查询用户
def select_user(request):
    userid = request.POST['userid']
    user = User.get(User.userid == userid)
    #user = User.select().where(User.userid==userid).get()
    return render(request, 'user.html', {'user': user})
