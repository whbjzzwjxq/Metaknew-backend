# -*-coding=utf-8 -*-
from django.http import HttpResponse
import json
from django.contrib.auth.hashers import check_password
from users.models import User, GroupCtrl, UserConcern, UserRepository, Privilege
from tools.encrypt import make_token
from tools.redis_process import *
from django.contrib.auth.hashers import make_password
from tools.id_generator import id_generator, device_id

salt = 'al76vdj895as12cq'


class BaseUser:

    def __init__(self):

        self.user = User()
        self.privilege = Privilege()
        self.repository = UserRepository()
        self.concern = UserConcern()

    def login_normal(self, request):

        phone = request.POST.get('phone')
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        # todo 前端密码加密 level: 3
        # length = request.POST.get('length')
        # password = decode(password, length)
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
                return self.login_success()
            else:
                return HttpResponse(content='用户名或密码错误', status=401)

    def login_cookie(self, request):
        if 'token' in request.COOKIES and 'user_name' in request.COOKIES:
            token = request.COOKIES['token']
            name = request.COOKIES['user_name']
            _id, saved_token = query_user_by_name(name)
            if not saved_token:
                return HttpResponse(content='登录信息过期，请重新登录', status=401)
            elif not token == saved_token:
                return HttpResponse(content='已经在别处登录了', status=401)
            else:
                return self.login_success()
        else:
            return HttpResponse(content='以游客身份登录', status=200)

    def login_message(self, request):
        body = json.dumps(request.body)
        info = body['info']
        message_code = query_message(info['phone'])  # 用户session
        if message_code is None:
            return HttpResponse(content='验证码失效，请重新发送验证码', status=400)
        elif message_code != info['code']:
            return HttpResponse(content='验证码有误，请重新输入', status=400)
        else:
            user_info = User.objects.get(UserPhone=info['phone'])
            if not user_info:
                return HttpResponse(content='该手机号不存在', status=400)
            else:
                return self.login_success()

    def login_success(self):
        name = self.user.UserName
        _id = self.user.UserId
        token = make_token(name, _id)
        set_user_login(self.user, token)
        response = HttpResponse(content='登录成功', status=200)
        response.set_cookie(key='token', value=token, max_age=week, httponly=True)
        response.set_cookie(key='user_name', value=self.user.UserName, max_age=week)
        return response

    def register(self, request):
        body = json.dumps(request.body)
        info = body['info']
        concern = body['concern']
        status = body['status']
        if info['name'] == '':
            info['name'] = info['phone']
        # redis中读取验证码信息
        message_code = query_message(info['phone'])  # 用户session
        if message_code is None:
            return HttpResponse(content='验证码失效，请重新发送验证码', status=400)
        elif message_code != info['code']:
            return HttpResponse(content='验证码有误，请重新输入', status=400)
        else:
            user_info = User.objects.get(UserPhone=info['phone'])
            if user_info:
                return HttpResponse(content='该手机号已注册', status=400)
            else:
                self.__create(info=info, concern=concern, status=status)
                response = self.login_success()
                response.content = '注册成功'
                return response

    def __create(self, info, concern, status):
        _id = id_generator(number=1, method='device', content=device_id, jump=3)[0]
        password = info['password']
        # todo 前端密码加密 level: 3
        # password = decode(password, info['length'])
        self.user = User.objects.create(
            UserId=_id,
            UserName=info['name'],
            UserPhone=info['phone'],
            UserEmail=info['email'],
            UserPw=make_password(password=password, salt=salt)
        )
        if status:
            self.user.Topic = concern['Topic']
            self.user.Joint_Group = BaseGroup.apply(_id, concern['group'])
        self.privilege = Privilege.objects.create(UserId=_id)
        self.repository = UserRepository.objects.create(UserId=_id)
        self.save()

    def save(self):
        self.user.save()
        self.privilege.save()
        self.repository.save()
        # 注意Concern是不save的，有独立的保存方法


class BaseGroup:

    def __init__(self):

        self.group = GroupCtrl()
        self.already = False

    def query_id(self, _id):

        self.group = GroupCtrl.objects.filter(GroupId=_id)
        if not len(self.group) == 0:
            self.already = True
        return self

    @staticmethod
    def apply(user_id, group_ids):

        # todo 改成list of group level: 3
        groups = GroupCtrl.objects.in_bulk(group_ids)

        def check(group):
            if group.Is_open:
                return 2
            else:
                pass
                # todo 申请 level : 3
                return 3

        output = {group.GroupId: check(group) for group in groups}
        return output
