import json
from typing import List, Type

import random
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpRequest

from base_api.interface_frontend import LoginByPhoneData, LoginUserNameData, RegisterData, CheckInfoDuplicateData, \
    SendCodeData
from base_api.logic_class import GuestApi, HttpRequestBoundUser, LoginResponse, Api
from record.exception import ErrorForWeb, CodeExistError, CodeExpiredError, CodeDoesNotMatchError, ObjectAlreadyExist, \
    UnAuthorization, WrongPassword
from tools.aliyun import authorityKeys
from tools.id_generator import id_generator
from tools.redis_process import user_query_message, user_check_message, user_set_message
from users.logic_class import BaseUser
from users.models import User


def ali_dayu_api(action_name, sign_name, template_code):
    ali_request = CommonRequest(
        action_name=action_name,
        domain="dysmsapi.aliyuncs.com",
        version="2017-05-25",
    )
    ali_request.set_accept_format("json")
    ali_request.set_method("POST")
    ali_request.set_protocol_type("https")  # https | http
    ali_request.add_query_param('SignName', sign_name)
    ali_request.add_query_param('TemplateCode', template_code)

    return ali_request


class LoginApi(GuestApi):
    """
    登录相关API
    """
    URL = 'user/login/'


class RegisterApi(GuestApi):
    """
    注册相关API
    """
    URL = 'user/register/'


class LoginByCookie(LoginApi):
    meta = LoginApi.meta.rewrite(is_user=True)
    URL = 'cookie'
    description = '用cookie自动登录'
    method = 'GET'
    frontend_data = None
    abstract = False

    def _main_hook(self, result: None, request: HttpRequestBoundUser) -> LoginResponse:
        if request.user:
            result = LoginResponse(**request.user.login_success())
            return result
        else:
            UnAuthorization('登录信息过期').raise_error()

    def _response_hook(self, result):
        return HttpResponse(status=200, content=json.dumps(result.to_dict))


class LoginByPhone(LoginApi):
    """
    用手机账户登录
    """
    URL = 'phone_code'
    method = 'GET'
    frontend_data = LoginByPhoneData
    abstract = False

    def _main_hook(self, result: LoginByPhoneData, request: HttpRequest) -> LoginResponse:
        phone = result.Phone
        code = result.Code
        current_code = user_query_message(phone)
        if not current_code:
            raise ErrorForWeb(CodeExpiredError, is_dev=False, is_error=True)
        if code != current_code:
            raise ErrorForWeb(CodeDoesNotMatchError, is_dev=False, is_error=True)
        else:
            try:
                user = User.objects.get(Phone=phone)
                user_model = BaseUser(_id=user.UserId)
                user_model._user = user
                result = LoginResponse(**user_model.login_success())
                return result
            except ObjectDoesNotExist:
                raise ErrorForWeb(ObjectDoesNotExist, description='手机号不存在', is_dev=False, is_error=True)

    def _response_hook(self, result: LoginResponse):
        return HttpResponse(status=200, content=json.dumps(result.to_dict))


class LoginByName(LoginApi):
    """
    用户名邮箱登录
    """
    URL = 'user_name'
    method = 'GET'
    frontend_data = LoginUserNameData
    abstract = False

    def _main_hook(self, result: LoginUserNameData, request: HttpRequest) -> LoginResponse:
        try:
            if not result.IsEmail:
                user = User.objects.get(Name=result.Name)
            else:
                user = User.objects.get(Email=result.Name)
        except ObjectDoesNotExist:
            raise ErrorForWeb(ObjectDoesNotExist, description='账户不存在', is_dev=False, is_error=True)
        else:
            # 检查密码是否匹配
            if check_password(result.Password, user.UserPw):
                user_model = BaseUser(_id=user.UserId)
                user_model._user = user
                result = LoginResponse(**user_model.login_success())
                return result
            else:
                raise WrongPassword(description="账户或密码错误")


class SendCode(RegisterApi):
    """
    发送验证码
    """
    URL = 'send_code'
    method = 'GET'
    frontend_data = SendCodeData
    response_data = None
    abstract = False
    meta = LoginApi.meta.rewrite()

    def _main_hook(self, result: SendCodeData, request) -> None:
        phone = result.Phone
        current_code = user_check_message(phone=phone)
        message_code = random.randint(123456, 898998)
        if current_code:
            ErrorForWeb(CodeExistError, description=CodeExistError.__doc__, is_dev=False, is_error=True, status=401)
        else:
            user_set_message(phone, message_code)
            params = {"code": str(message_code)}
            client = AcsClient(ak=authorityKeys["developer"]["access_key_id"],
                               secret=authorityKeys["developer"]["access_key_secret"],
                               region_id="default")
            ali_request = ali_dayu_api("SendSms", "MetaKnew", "SMS_163847373")
            ali_request.add_query_param("TemplateParam", params)
            ali_request.add_query_param("PhoneNumbers", phone)
            client.do_action_with_exception(ali_request)
            return None

    def _response_hook(self, result):
        return HttpResponse(status=200)


class Register(RegisterApi):
    URL = ''
    method = 'POST'
    frontend_data = RegisterData
    abstract = True

    def _main_hook(self, result: RegisterData, request: HttpRequest) -> LoginResponse:
        result_info = result.Info
        current_code = user_check_message(phone=result_info.Phone)
        if not current_code:
            raise ErrorForWeb(CodeExpiredError, description=CodeExpiredError.__doc__, is_dev=False, is_error=True,
                              status=400)
        elif user_query_message(result_info.Phone) != result_info.Code:
            raise ErrorForWeb(CodeDoesNotMatchError, description=CodeDoesNotMatchError.__doc__, is_dev=False,
                              is_error=True, status=400)
        else:
            try:
                User.objects.get(Phone=result_info.Phone)
            except ObjectDoesNotExist:
                _id = id_generator(1, 'time')[0]
                user_model = BaseUser(_id=_id).create(
                    name=result_info.Name,
                    phone=result_info.Phone,
                    password=result_info.Password,
                    email=result_info.Email,
                )
                response = LoginResponse(**user_model.login_success())
                response.content = '注册成功'
                return response
            else:
                raise ErrorForWeb(ObjectAlreadyExist, description='手机号已注册', is_dev=False, is_error=True, status=400)

    def _response_hook(self, result: LoginResponse):
        return HttpResponse(status=200, content=json.dumps(result.to_dict))


class RegisterNormal(Register):
    """
    基本注册
    """
    URL = 'normal'
    abstract = False


class RegisterFast(Register):
    """
    手机快速注册
    """
    URL = 'fast'
    abstract = False


class CheckInfoDuplicate(RegisterApi):
    """
    检查名字，电话，邮箱是否重复
    """
    method = 'GET'
    abstract = False
    URL = 'check_info_duplicate'

    def _main_hook(self, result: CheckInfoDuplicateData, request: HttpRequest) -> bool:
        condition = {}
        valid = False
        for k, v in result.to_dict:
            if v:
                condition = {k: v}
                valid = True
        try:
            if not valid:
                raise ErrorForWeb(AttributeError, description='字段错误，电话姓名邮箱至少有一项', is_dev=True, is_error=True)
            User.objects.get(**condition)
            return True
        except ObjectDoesNotExist:
            return False

    def _response_hook(self, result: bool):
        if result:
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=400)


apis: List[Type[Api]] = [
    LoginByCookie,
    LoginByPhone,
    LoginByCookie,
    RegisterFast,
    RegisterNormal,
    SendCode,
    CheckInfoDuplicate
]
