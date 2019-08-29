# -*-coding=utf-8 -*-
from django.http import HttpResponse
import json
from django.contrib.auth.hashers import check_password
from users.models import User, GroupCtrl, UserConcern, UserRepository, Privilege
from tools.encrypt import make_token
from tools.redis_process import *
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned


salt = "al76vdj895as12cq"


class BaseUser:

    def __init__(self, _id: int):
        self.user_id = _id
        self.user = User()
        self.privilege = Privilege()
        self.repository = UserRepository()
        self.concern = UserConcern()

    # 登录成功之后的设置
    def login_success(self):
        name = self.user.UserName
        _id = self.user.UserId
        token = make_token(name, _id)
        self.query_privilege()
        user_login_set(self.user, self.privilege, token)
        result = {
            "content": "登录成功",
            "token": token,
            "userName": self.user.UserName
        }
        response = HttpResponse(json.dumps(result), content_type="application/json", status=200)
        return response

    def create(self, info, concern, status):
        password = info["password"]
        # todo 前端密码加密 level: 3
        # password = decode(password, info["length"])
        self.user = User.objects.create(
            UserId=self.user_id,
            UserName=info["name"],
            UserPhone=info["phone"],
            UserEmail=info["email"],
            UserPw=make_password(password=password, salt=salt)
        )
        if status:
            self.user.Topic = concern["Topic"]
            self.user.Joint_Group = BaseGroup.apply(self.user_id, concern["group"])
        self.privilege = Privilege.objects.create(UserId=self.user_id)
        self.repository = UserRepository.objects.create(UserId=self.user_id)
        self.save()
        return self

    @staticmethod
    def query_user_by_info(criteria):
        try:
            user = User.objects.get(criteria)
        except ObjectDoesNotExist or MultipleObjectsReturned:
            return None
        else:
            return user

    def query_user(self):
        try:
            self.user = User.objects.get(pk=self.user_id)
        except ObjectDoesNotExist:
            return None
        else:
            return self

    def query_privilege(self):
        try:
            self.privilege = Privilege.objects.get(UserId=self.user.UserId)
            return self
        except ObjectDoesNotExist as e:
            raise e

    def query_repository(self):
        try:
            self.repository = UserRepository.objects.get(UserId=self.user.UserId)
            return self
        except ObjectDoesNotExist as e:
            raise e

    def create_node(self, _id):
        """

        :param _id: 创建的节点id
        :return:
        """
        self.privilege.Is_Owner.append(_id)
        self.repository.CreateNode.append(_id)

    def create_doc(self, _id):
        """

        :param _id: 创建的专题id
        :return:
        """
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
