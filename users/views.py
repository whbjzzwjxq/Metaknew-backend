# -*-coding=utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse
from users.models import User
from users import user as userInfo
import json
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password,check_password
# import datetime as dt
from django.utils import timezone
# Create your views here.

'''
# 删除
def delete_user(request):
    userid = request.POST['userid']
    username = request.POST['username']
    userpw = request.POST['userpassword']
    User.delete().where(User.userid == userid or User.username == username or User.userpassword == userpw).execute()
'''


# 修改用户资料     未测
def update_user(request):
    resp = HttpResponse()
    filedata={}
    filedata['userid'] = request.POST.get('userid', None)
    filedata['username'] = request.POST.get('username', None)
    filedata['useremail'] = request.POST.get('useremail', None)
    filedata['userpw'] = request.POST.get('userpw', None)
    user = userInfo.updateById(filedata)
    respData = {'status': '1', 'ret': '资料修改成功！！'}
    resp.content = json.dumps(respData)
    return HttpResponse(resp, content_type="application/json")


# 登录
def login(request):
    resp = HttpResponse()
    # 获取用户输入的手机号、密码
    param = json.loads(request.body)['data']
    phone = param['user_phone']
    password = param['user_pw']
    # 查询邮箱为phone的用户
    users = userInfo.selectByPhone(phone)
    if not users:
        respData = {'status': '0', 'ret': '用户不存在!!!'}
    for i in users:
        # 检查密码是否匹配
        if check_password(password, i.user_pw):
            try:
                respData = {'status': '1', 'ret': '登录成功!'}
            except BaseException as e:
                print(e)
                pass
                respData = {'status': '0', 'ret': '登录失败，输入信息有误!!!'}
        else:
            respData = {'status': '0', 'ret': '登录失败，密码不正确!!!'}
    resp.content = json.dumps(respData)
    return HttpResponse(resp, content_type="application/json")


# 注册
def register(request):
    """
    	"data":{
		"username":
		"user_pw":
		"user_email":
		"user_phone":
	}
    :param request:
    :return:
    """
    resp = HttpResponse()
    param = json.loads(request.body)['data']
    param['user_pw'] = make_password(param['user_pw'])  # 密码加密
    param['datetime'] = timezone.now()
    # 把数据写进数据库
    try:
        userInfo.add(param)
        respData = {'status': 1, 'ret': '注册成功!'}
    except BaseException as e:
        print(e)
        pass
        respData = {'status': 0, 'ret': '输入信息有误!'}
    resp.content = json.dumps(respData)
    return HttpResponse(resp, content_type="application/json")
