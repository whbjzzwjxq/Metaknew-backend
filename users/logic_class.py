# -*-coding=utf-8 -*-
from django.http import HttpResponse
import json
from users.models import User, GroupCtrl, UserConcern, UserRepository, Privilege
from tools.encrypt import make_token
from tools.redis_process import *
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
import typing
from tools.base_tools import model_to_dict

salt = "al76vdj895as12cq"


class BaseUser:

    def __init__(self, _id: int):
        self.user_id = _id
        self.user: typing.Optional[User] = None
        self.privilege: typing.Optional[Privilege] = None
        self.repository: typing.Optional[UserRepository] = None
        self.concern: typing.Optional[UserConcern] = None

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
        if not self.user:
            try:
                self.user = User.objects.get(pk=self.user_id)
            except ObjectDoesNotExist:
                return None
            else:
                return self
        else:
            return self

    def query_privilege(self):
        if not self.privilege:
            try:
                self.privilege = Privilege.objects.get(UserId=self.user_id)
                return self
            except ObjectDoesNotExist as e:
                return None
        else:
            return self

    def query_repository(self):
        if not self.repository:
            try:
                self.repository = UserRepository.objects.get(UserId=self.user_id)
                return self
            except ObjectDoesNotExist as e:
                return None
        else:
            return self

    def bulk_create_source(self, id_type_dict: typing.Dict[int, str]):
        """
        source的定义:Node Media Document
        :param id_type_dict: 创建的内容的id-source dict
        :return:
        """
        self.query_repository()
        self.query_privilege()
        if id_type_dict:
            for _id, source_type in id_type_dict.items():
                self.privilege.Is_Owner.append(_id)
                if source_type == "Node":
                    self.repository.CreateNode.append(_id)
                elif source_type == "Media":
                    self.repository.UploadFile.append(_id)
                elif source_type == "Document":
                    self.repository.CreateDoc.append(_id)
                elif source_type == "Fragment":
                    self.repository.Fragment.append(_id)
                else:
                    raise AttributeError("Unknown Source Type")
            self.repository.save()
            self.privilege.save()

    def save(self):
        self.user.save()
        self.privilege.save()
        self.repository.save()
        # 注意Concern是不save的，有独立的保存方法


class BaseGroup:

    def __init__(self, _id: int):

        self.group = GroupCtrl()
        self.privilege = Privilege()
        self._id = _id

    def query_group(self):
        try:
            self.group = GroupCtrl.objects.get(GroupId=self._id)
            return self
        except ObjectDoesNotExist as e:
            raise e

    def query_privilege(self):
        try:
            self.privilege = Privilege.objects.get(GroupId=self._id)
            group_privilege_set(_id=self._id, privilege=self.privilege)
            return self
        except ObjectDoesNotExist as e:
            raise e

    def query_privilege_cache(self) -> dict:
        result = user_group_privilege_info_query(self._id)
        if result:
            return result
        else:
            try:
                self.privilege = Privilege.objects.get(GroupId=self._id)
                group_privilege_set(_id=self._id, privilege=self.privilege)
                return model_to_dict(self.privilege)
            except ObjectDoesNotExist as e:
                raise e

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
