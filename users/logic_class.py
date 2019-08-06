# -*-coding=utf-8 -*-
from django.http import HttpResponse
import json
from django.contrib.auth.hashers import check_password
from users.models import User, GroupCtrl, UserConcern, UserRepository, Privilege
from tools.encrypt import make_token
from tools.redis_process import *
from django.contrib.auth.hashers import make_password
from tools.id_generator import id_generator, device_id
from django.db.models import ObjectDoesNotExist

salt = "al76vdj895as12cq"


class BaseUser:

    def __init__(self, user):

        self.user = user
        self.privilege = Privilege()
        self.repository = UserRepository()
        self.concern = UserConcern()

    def login_success(self):
        name = self.user.UserName
        _id = self.user.UserId
        token = make_token(name, _id)
        set_user_login(self.user, token)
        response = HttpResponse(content="登录成功", status=200)
        response.set_cookie(key="token", value=token, max_age=week, httponly=True)
        response.set_cookie(key="user_name", value=self.user.UserName, max_age=week)
        return response

    def create(self, info, concern, status):
        _id = id_generator(number=1, method="device", content=device_id, jump=3)[0]
        password = info["password"]
        # todo 前端密码加密 level: 3
        # password = decode(password, info["length"])
        self.user = User.objects.create(
            UserId=_id,
            UserName=info["name"],
            UserPhone=info["phone"],
            UserEmail=info["email"],
            UserPw=make_password(password=password, salt=salt)
        )
        if status:
            self.user.Topic = concern["Topic"]
            self.user.Joint_Group = BaseGroup.apply(_id, concern["group"])
        self.privilege = Privilege.objects.create(UserId=_id)
        self.repository = UserRepository.objects.create(UserId=_id)
        self.save()
        return self

    def query_privilege(self, _id):
        try:
            self.privilege = Privilege.objects.get(UserId=_id)
            return self
        except ObjectDoesNotExist as e:
            raise e

    def query_repository(self, _id):
        try:
            self.repository = UserRepository.objects.get(UserId=_id)
            return self
        except ObjectDoesNotExist as e:
            raise e

    def create_node(self, _id):
        self.privilege.Is_Owner.append(_id)
        self.repository.CreateNode.append(_id)

    def create_doc(self, _id):
        self.privilege.Is_Owner.append(_id)
        self.repository.CreateDoc.append(_id)

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
