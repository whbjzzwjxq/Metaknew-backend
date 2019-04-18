# -*-coding=utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse
from users.models import User
from users import user as userInfo
import json
from django.http import JsonResponse
import datetime as dt
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
    # if request.method == 'GET':
    #     return render(request, 'demo/login.html')
    # else:
    #     # 初始化返回信息
    #     respData = {'status': '0', 'ret': '登录失败，输入信息有误!!!'}

    # 预定义一个最终返回的Response对象(可以动态地为其配置内容,要想勒令客户端做事情必须要有一个Response对象)
    resp = HttpResponse()

    # 获取用户输入的用户名、密码、验证码
    email = request.POST.get('useremail', None)
    password = request.POST.get('userpw', None)
    respData = {}
    # 查询邮箱为email的用户
    userss = userInfo.selectByEmail(email)
    if not userss:
        respData = {'status': '0', 'ret': '用户不存在!!!'}

    for i in userss:
        # 检查密码、验证码是否匹配
        if password == i.userpassword:
            try:
                respData = {'status': '1', 'ret': '登录成功!'}
            except BaseException as e:
                print(e)
                pass
                respData = {'status': '0', 'ret': '登录失败，输入信息有误!!!'}
        else:
            respData = {'status': '0', 'ret': '登录失败，密码不正确!!!'}
    resp.content = json.dumps(respData)
    # return resp
    return HttpResponse(resp, content_type="application/json")


# 注册
def register(request):

    if request.method == 'GET':
        return render(request, 'SitesApp/register.html')
    else:
        # 获取用户输入的用户名、密码、邮箱
        filedata = {}
        filedata['username']= request.POST.get('username', None)
        filedata['userpw'] = request.POST.get('userpw', None)
        filedata['useremail'] = request.POST.get('useremail', None)
        filedata['datetime'] = dt.datetime.now()

        # 把数据写进数据库
        try:
            userInfo.add(filedata)
            return JsonResponse({'status': 1, 'ret': '注册成功!'})
        except BaseException as e:
            print(e)
            pass
    return JsonResponse({'status': 0, 'ret': '输入信息有误!'})
