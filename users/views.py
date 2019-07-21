# -*-coding=utf-8 -*-
from django.http import HttpResponse
import json
import time
from django.http import JsonResponse
from django.contrib.auth.hashers import check_password
# import datetime as dt
from django.utils import timezone
from django.contrib.auth.hashers import make_password
import numpy as np
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from tools.Meta_Response import get_http_response as getHttpResponse
from django.core.cache import cache
from users.models import User
from tools.login_token import make_token, week
from users.models import UserCollection, UserRole
from tools.redis_process import user_login
# Create your views here.


# 修改用户资料     未测
def update_user(request):
    response = HttpResponse()
    file_data = {'UserName': request.POST.get('user_name', None),
                 'UserEmail': request.POST.get('user_email', None)}
    User.objects.update(file_data)
    resp_data = {'status': '1', 'ret': '资料修改成功！！'}
    response.content = json.dumps(resp_data)
    return HttpResponse(response, content_type="application/json")


# todo 登录类 level: 3
def login_by_phone_pw(request):
    # 获取用户输入的手机号、密码
    response = HttpResponse()
    param = json.loads(request.body)['data']
    phone = param['user_phone']
    password = param['user_pw']
    user = User.objects.get(UserPhone=phone)
    if not user:
        resp_data = {'status': '0', 'ret': '用户不存在!!!'}
    else:
        # 检查密码是否匹配
        if check_password(password, user.UserPw):
            token = make_token(user.UserName, user.UserId)
            user_login(user_name=user.UserName, user_id=user.UserId, token=token)
            resp_data = {'status': '1', 'ret': '登录成功!'}
            response.set_cookie(key='token', value=token, max_age=week, httponly=True)
            response.set_cookie(key='user_name', value=user.UserName, max_age=week)
        else:
            resp_data = {'status': '0', 'ret': '登录失败，账号或密码不正确'}
    response.content = json.dumps(resp_data)
    return response


# 注册
def register(request):
    """
        "data":{
        "user_name":
        "user_pw":
        "user_email":
        "user_phone":
    }
    :param request:
    :return:
    """
    response = HttpResponse()
    param = json.loads(request.body)['data']
    if param['user_name'] == '':
        param['user_name'] = param['user_phone']
    # redis中读取验证码信息
    message_code = cache.get(param['user_phone'])  # 用户session
    if message_code is None:
        return HttpResponse(getHttpResponse('0', '验证码失效，请重新发送验证码', ''), content_type='application/json')
    elif message_code != param['code']:
        return HttpResponse(getHttpResponse('0', '验证码有误，请重新输入', ''), content_type='application/json')
    else:
        # 把数据写进数据库
        try:
            user_info = User.objects.get(UserPhone=param['user_phone'])
            if user_info:
                return HttpResponse(getHttpResponse('0', '该手机号已注册', ''), content_type='application/json')
            else:
                user_info = User.objects.create(
                    UserPhone=param['user_phone'],
                    UserEmail=param['user_email'],
                    UserName=param['user_name'],
                    UserPw=make_password(param['user_pw']),
                    DateTime=timezone.now()
                )
                token = make_token(user_info.UserName, user_info.UserId)
                UserCollection.objects.create(UserId=user_info).save()
                UserRole.objects.create(UserId=user_info).save()
                user_info.save()
                response.set_cookie(key='token', value=token, max_age=week, httponly=True)
                response.set_cookie(key='user_name', value=user_info.UserName, max_age=week)
                respData = {'status': 1, 'ret': '注册成功!'}
        except BaseException as e:
            print(e)
            respData = {'status': 0, 'ret': '输入信息有误!'}
        response.content = json.dumps(respData)
        return response


# 发送验证码短信
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
    TemplateParam = {}
    message_code = ''
    for i in range(6):
        i = np.random.randint(0, 9)
        message_code += str(i)
    TemplateParam['code'] = message_code
    print(message_code)

    # session = json.loads(request.body)['data']['session']     #用户session   一分钟后验证码发送
    # cache.set(session,message_code)  #设置缓存

    mobile = json.loads(request.body)['data']['mobile']
    cache.set(mobile, message_code)  # 根据手机号设置缓存
    client = AcsClient('LTAITKweDYoqN2cH', 'jU3QemPN4KbpHbz2qQ8Z3kNkgtTeSB', 'default')
    alirequest = requestAPI('SendSms', 'MetaKnew', 'SMS_163847373')
    alirequest.add_query_param('TemplateParam', TemplateParam)
    alirequest.add_query_param('PhoneNumbers', mobile)
    response = client.do_action_with_exception(alirequest)
    print(str(response, encoding='utf-8'))

    return HttpResponse(getHttpResponse('1', '发送成功', json.loads(str(response, encoding='utf-8'))),
                        content_type="application/json")


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

    client = AcsClient('LTAITKweDYoqN2cH', 'jU3QemPN4KbpHbz2qQ8Z3kNkgtTeSB', 'default')
    alirequest = requestAPI('QuerySendDetails', 'MetaKnew', 'SMS_163847373')
    alirequest.add_query_param('PhoneNumbers', mobile)
    alirequest.add_query_param('CurrentPage', current_page)
    alirequest.add_query_param('SendDate', time.strftime("%Y%m%d", time.localtime(int(time.time()))))
    alirequest.add_query_param('PageSize', page_size)
    alirequest.add_query_param('BizId', biz_id)
    response = client.do_action_with_exception(alirequest)
    print(str(response, encoding='utf-8'))

    return JsonResponse(str(response))


# 阿里大于查询公共请求信息封装接口
def requestAPI(actionName, signName, templateCode):
    alirequest = CommonRequest()
    alirequest.set_accept_format('json')
    alirequest.set_domain('dysmsapi.aliyuncs.com')
    alirequest.set_method('POST')
    alirequest.set_protocol_type('https')  # https | http
    alirequest.set_version('2017-05-25')
    alirequest.set_action_name(actionName)
    alirequest.add_query_param('SignName', signName)
    alirequest.add_query_param('TemplateCode', templateCode)

    return alirequest
