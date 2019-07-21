# -*-coding=utf-8 -*-
from django.http import HttpResponse
import json
import time
from django.http import JsonResponse
from django.contrib.auth.hashers import check_password
from users.models import User
from tools.login_token import make_token
from tools.encrypt_AES import decode
from tools.redis_process import week, redis


class BaseUser:

    def __init__(self):

        self.user = User

    def login_normal(self, request):

        phone = request.GET.get('phone')
        name = request.GET.get('name')
        email = request.GET.get('email')
        password = request.GET.get('password')
        length = request.GET.get('length')
        password = decode(password, length)
        if phone:
            self.user = User.objects.get(UserPhone=phone)
        elif name:
            self.user = User.objects.get(UserName=name)
        else:
            self.user = User.objects.get(UserEmail=email)
        if not self.user:
            return HttpResponse(content='账户不存在', status=401)
        else:
            # 检查密码是否匹配
            if check_password(password, self.user.UserPw):
                self.login_success()
            else:
                return HttpResponse(content='用户名或密码错误', status=401)

    def login_success(self):
        name = self.user.UserName
        _id = self.user.UserId
        cache_info = {
            'root': self.user.Is_Superuser,
            'dev': self.user.Is_Developer,
            'vip': self.user.Is_Vip,
            'high_vip': self.user.Is_high_vip,
            'token': make_token(name, _id)
        }
        cache_info.update(self.user.Joint_Group)
        redis.hmset(_id, cache_info)
        response = HttpResponse()
        response.set_cookie(key='token', value=cache_info['token'], max_age=week, httponly=True)
        response.set_cookie(key='user_name', value=self.user.UserName, max_age=week)
        response.content = '登陆成功'
        response.status_code = 200
        return response
