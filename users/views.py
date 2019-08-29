# -*-coding=utf-8 -*-
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
import random
from django.http import HttpResponse
import json
from django.contrib.auth.hashers import check_password
from users.models import User
from users.logic_class import BaseUser
from tools.redis_process import *
from django.db.models import ObjectDoesNotExist
from tools.id_generator import id_generator, device_id


# 发送验证码短信
@csrf_exempt
def send_message(request):
    """
    返回参数{
    BizId 发送回执ID
    Code OK
    Message OK
    RequestId 请求ID
    }
    """

    # 模版变量对应参数值
    phone = request.GET.get("phone")
    current = user_check_message(phone=phone)
    message_code = random.randint(123456, 898998)
    if current:
        return HttpResponse(content="请隔3分钟再请求验证码")
    else:
        user_set_message(phone, message_code)
        params = {"code": str(message_code)}
        client = AcsClient("LTAITKweDYoqN2cH", "jU3QemPN4KbpHbz2qQ8Z3kNkgtTeSB", "default")
        ali_request = ali_dayu_api("SendSms", "MetaKnew", "SMS_163847373")
        ali_request.add_query_param("TemplateParam", params)
        ali_request.add_query_param("PhoneNumbers", phone)
        client.do_action_with_exception(ali_request)
        return HttpResponse(content="发送成功", content_type="application/json")


@csrf_exempt
def register(request):
    body = json.loads(request.body)
    info = body["info"]
    concern = body["concern"]
    status = body["status"]
    if info["name"] == "":
        info["name"] = info["phone"]
    # redis中读取验证码信息
    message_code = user_query_message(info["phone"])
    if message_code is None:
        return HttpResponse(content="验证码失效，请重新发送验证码", status=400)
    elif message_code != info["code"]:
        return HttpResponse(content="验证码有误，请重新输入", status=400)
    else:
        try:
            User.objects.get(UserPhone=info["phone"])
        except ObjectDoesNotExist:
            _id = id_generator(number=1, method="device", content=device_id, jump=3)[0]
            new_user = BaseUser(_id=_id).create(info=info, concern=concern, status=status)
            response = new_user.login_success()
            response.content = "注册成功"
            return response
        else:
            return HttpResponse(content="该手机号已注册", status=400)


@csrf_exempt
def login_normal(request):
    info = json.loads(request.body)
    phone = info["phone"]
    name = info["name"]
    email = info["email"]
    password = info["password"]
    # todo 前端密码加密 level: 3
    # length = request.POST.get("length")
    # password = decode(password, length)
    try:
        if phone:
            user = User.objects.get(UserPhone=phone)
        elif name:
            user = User.objects.get(UserName=name)
        else:
            user = User.objects.get(UserEmail=email)
    except ObjectDoesNotExist:
        return HttpResponse(content="账户不存在", status=400)
    else:
        # 检查密码是否匹配
        if check_password(password, user.UserPw):
            base_user = BaseUser(_id=user.UserId)
            base_user.user = user
            return base_user.login_success()
        else:
            return HttpResponse(content="用户名或密码错误", status=400)


@csrf_exempt
def login_cookie(request):
    token = request.headers["Token"]
    user_name = request.headers["User-Name"]
    if token != "null" and user_name != "null":
        _id, saved_token = user_query_by_name(user_name)
        if not saved_token:
            return HttpResponse(content="登录信息过期，请重新登录", status=400)
        elif not token == saved_token:
            return HttpResponse(content="已经在别处登录了", status=400)
        else:
            user = BaseUser(_id=_id).query_user()
            if not user:
                return HttpResponse(content="非法的用户名", status=400)
            else:
                # 需不需要刷新状态 todo level: 3
                return user.login_success()
    else:
        return HttpResponse(content="以游客身份登录", status=200)


@csrf_exempt
def login_message(request):
    body = json.dumps(request.body)
    info = body["info"]
    message_code = user_query_message(info["phone"])  # 用户session
    if message_code is None:
        return HttpResponse(content="验证码失效，请重新发送验证码", status=400)
    elif message_code != info["code"]:
        return HttpResponse(content="验证码有误，请重新输入", status=400)
    else:
        try:
            user = User.objects.get(UserPhone=info["phone"])
        except ObjectDoesNotExist:
            return HttpResponse(content="该手机号不存在", status=400)
        else:
            base_user = BaseUser(_id=user.UserId)
            base_user.user = user
            return base_user.login_success()


# 查询发送记录
def query_send_detail(biz_id, mobile, page_size=10, current_page=1):
    """"
    短信详情查询
    请求参数{
        biz_id: 流水号
        phone_number: 手机号码
        page_size: 每页大小
        current_page: 当前页
        send_date : 发送日期（30天内的记录查询）
    }
    返回参数{
        TotalCount
        Message
        RequestId
        SmsSendDetailDTOs
        Code
    }
    {
        "TotalCount":1,
        "Message":"OK",
        "RequestId":"819BE656-D2E0-4858-8B21-B2E477085AAF",
        "SmsSendDetailDTOs":{
            "SmsSendDetailDTO":[
                {
                    "SendDate":"2019-01-08 16:44:10",
                    "OutId":"123",
                    "SendStatus":3,
                    "ReceiveDate":"2019-01-08 16:44:13",
                    "ErrCode":"DELIVRD",
                    "TemplateCode":"SMS_122310183",
                    "Content":"【阿里云】验证码为：123，您正在登录，若非本人操作，请勿泄露",
                    "PhoneNum":"15298356881"
                }
            ]
        },
        "Code":"OK"
    }
        """

    client = AcsClient("LTAITKweDYoqN2cH", "jU3QemPN4KbpHbz2qQ8Z3kNkgtTeSB", "default")
    alirequest = ali_dayu_api("QuerySendDetails", "MetaKnew", "SMS_163847373")
    alirequest.add_query_param("PhoneNumbers", mobile)
    alirequest.add_query_param("CurrentPage", current_page)
    alirequest.add_query_param("SendDate", time.strftime("%Y%m%d", time.localtime(int(time.time()))))
    alirequest.add_query_param("PageSize", page_size)
    alirequest.add_query_param("BizId", biz_id)
    response = client.do_action_with_exception(alirequest)
    print(str(response, encoding="utf-8"))

    return JsonResponse(str(response))


# 阿里大于查询公共请求信息封装接口
def ali_dayu_api(actionName, signName, templateCode):
    alirequest = CommonRequest()
    alirequest.set_accept_format("json")
    alirequest.set_domain("dysmsapi.aliyuncs.com")
    alirequest.set_method("POST")
    alirequest.set_protocol_type("https")  # https | http
    alirequest.set_version("2017-05-25")
    alirequest.set_action_name(actionName)
    alirequest.add_query_param("SignName", signName)
    alirequest.add_query_param("TemplateCode", templateCode)

    return alirequest
