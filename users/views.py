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


# 修改用户资料
def update_user(request):
    filedata={}
    filedata['userid'] = request.POST.get('userid', None)
    filedata['username'] = request.POST.get('username', None)
    filedata['useremail'] = request.POST.get('useremail', None)
    filedata['userpw'] = request.POST.get('userpw', None)
    user = userInfo.updateById(filedata)
    return render(request, 'userInfo.html', {'user': user})


# 登录
def login(request):
    if request.method == 'GET':
        return render(request, 'demo/login.html')
    else:
        # 初始化返回信息
        respData = {'status': '0', 'ret': '登录失败，输入信息有误!!!'}

        # 预定义一个最终返回的Response对象(可以动态地为其配置内容,要想勒令客户端做事情必须要有一个Response对象)
        resp = HttpResponse()

        # 获取用户输入的用户名、密码、验证码
        email = request.POST.get('email', None)
        password = request.POST.get('password', None)

        # 查询邮箱为email的用户
        user = userInfo.selectByEmail(email)
        if not user:
            respData = {'status': '0', 'ret': '用户不存在!!!'}

        # 检查密码、验证码是否匹配
        if password == user.userpassword:
            try:
                respData = {'status': '1', 'ret': 'login success!'}
            except BaseException as e:
                print(e)
                pass
                respData = {'status': '0', 'ret': '登录失败，输入信息有误!!!'}
    resp.content = json.dumps(respData)
    return resp


# 注册
def register(request):

    if request.method == 'GET':
        return render(request, 'SitesApp/register.html')
    else:
        # 获取用户输入的用户名、密码、邮箱
        filedata = {}
        filedata['username']= request.POST.get('username', None)
        filedata[' userpw'] = request.POST.get('userpw', None)
        filedata['useremail'] = request.POST.get('useremail', None)
        filedata['usertime'] = dt.datetime.now()

        # 把数据写进数据库
        try:
            userInfo.add(filedata)
            return JsonResponse({'status': 1, 'ret': 'register success!'})
        except BaseException as e:
            print(e)
            pass
    return JsonResponse({'status': 0, 'ret': '输入信息有误!'})
