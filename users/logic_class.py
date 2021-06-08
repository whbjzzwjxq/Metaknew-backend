import datetime
import json
from typing import Union, Optional, Type, List

from aliyunsdkcore import client
from aliyunsdkcore.profile import region_provider
from aliyunsdksts.request.v20150401 import AssumeRoleRequest
from django.contrib.auth.hashers import make_password
from django.db.models import QuerySet

from record.exception import RewriteMethodError
from tools.encrypt import make_user_token
from tools.redis_process import *
from users.models import GroupCtrl, UserPropResolve, UserPLabelExtraProps, UserEditDataBase

salt = "al76vdj895as12cq"


class BaseUser:

    def __init__(self, _id: Union[int, str]):
        self.user_id = int(_id)
        self.is_login = False
        self._user: Optional[User] = None
        self._privilege: Optional[Privilege] = None
        self._prop_resolve: Optional[Type[QuerySet]] = None

    @property
    def user_info(self):
        if self._user is None:
            self._user = User.objects.get(pk=self.user_id)
        return self._user

    @property
    def privilege(self):
        if self._privilege is None:
            self._privilege = Privilege.objects.get(pk=self.user_id)
        return self._privilege

    # 登录成功之后的设置
    def login_success(self):
        self.is_login = True
        name = self.user_info.Name
        _id = self.user_info.UserId
        token = make_user_token(name, _id)
        user_login_set(self.user_info, self.privilege, token)
        result = {
            "content": "登录成功",
            "token": token,
            "userName": self.user_info.Name,
            "userId": self.user_info.UserId,
            "fileToken": self.resource_auth_for_ali_oss()["Credentials"],
            "personalId": self.user_info.PersonalId
        }
        return result

    def resource_auth_for_ali_oss(self):
        region_id = 'cn-beijing'
        endpoint = 'sts-vpc.cn-beijing.aliyuncs.com'
        authority_keys = {
            "guest": {
                "id": '000000',
                "secret": '000000',
            },
            "developer": {
                "id": '000000',
                "secret": "000000"
            }
        }
        if self.is_login:
            region_provider.add_endpoint('Sts', region_id=region_id, end_point=endpoint)
            clt = client.AcsClient(ak=authority_keys["guest"]["id"],
                                   secret=authority_keys["guest"]["secret"],
                                   region_id=region_id)
            request = AssumeRoleRequest.AssumeRoleRequest()
            role_arn = "acs:ram::1807542795506680:role/webservernormaluser"
            request.set_RoleArn(role_arn)
            request.set_RoleSessionName("user" + str(self.user_id))
            request.set_DurationSeconds(3600)
            response = json.loads(clt.do_action_with_exception(request).decode())

            # 转为时间戳
            expire = datetime.datetime.strptime(response["Credentials"]["Expiration"], '%Y-%m-%dT%H:%M:%SZ')
            response["Credentials"]["Expiration"] = expire.timestamp() + 8 * 3600
            return response
        else:
            raise AttributeError

    def create(self, name, phone, password, email, addition=None):
        # todo 前端密码加密 level: 3
        # password = decode(password, info["length"])
        if addition is None:
            addition = {}
        self._user = User.objects.create(
            UserId=self.user_id,
            Name=name,
            Phone=phone,
            Email=email,
            UserPw=make_password(password=password, salt=salt)
        )
        self._privilege = Privilege.objects.create(UserId=self.user_id)
        self.save()
        return self

    def save(self):
        self.user_info.save()
        self.privilege.save()


class BaseGroup:

    def __init__(self, _id: int):
        self.group = GroupCtrl()
        self.privilege = Privilege()
        self._id = _id

    @staticmethod
    def apply(user_id, group_ids):
        pass
        # # todo 改成list of group level: 3
        # groups = GroupCtrl.objects.in_bulk(group_ids)
        #
        # def check(group):
        #     if group.Is_open:
        #         return 2
        #     else:
        #         pass
        #         # todo 申请 level : 3
        #         return 3
        #
        # output = {group.GroupId: check(group) for group in groups}
        # return output


M = Union[Type[UserEditDataBase], UserEditDataBase]


class _UserEditDataModel:
    model: M = UserEditDataBase

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.model_set: QuerySet = self.model.objects.filter(UserId=user_id)
        self.update_list: List[M] = []
        self.create_list: List[M] = []

    def update_create(self, data_list):
        for data in data_list:
            try:
                result: M = self.model_set.get(Key=data.Key)
                self.update_list.append(result)
            except ObjectDoesNotExist:
                result: M = self.model(
                    Key=data.Key,
                    UserId=self.user_id
                )
                self.create_list.append(result)
            for field in self.model.update_fields():
                setattr(result, field, getattr(data, field))
        return self

    def frontend_dict(self):
        raise RewriteMethodError


class UserPropResolveModel(_UserEditDataModel):
    model = UserPropResolve

    def frontend_dict(self):
        return {data.Key: {'type': data.FieldType, 'resolve': data.ResolveType} for data in self.model_set}


class UserPLabelExtraPropsModel(_UserEditDataModel):
    model = UserPLabelExtraProps

    def frontend_dict(self):
        return {data.Key: data.PropNames for data in self.model_set}
