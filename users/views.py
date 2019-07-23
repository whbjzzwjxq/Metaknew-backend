# -*-coding=utf-8 -*-
from django.http import HttpResponse
import time
from django.http import JsonResponse
from tools.redis_process import redis
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from tools.redis_process import check_message, set_message
import random


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
    phone = request.GET.get('phone')
    current = check_message(phone=phone)
    message_code = random.randint(123456, 898998)
    if current:
        return HttpResponse(content='请隔1分钟再请求验证码')
    else:
        set_message(phone, message_code)
        params = {'code': str(message_code)}
        client = AcsClient('LTAITKweDYoqN2cH', 'jU3QemPN4KbpHbz2qQ8Z3kNkgtTeSB', 'default')
        ali_request = ali_dayu_api('SendSms', 'MetaKnew', 'SMS_163847373')
        ali_request.add_query_param('TemplateParam', params)
        ali_request.add_query_param('PhoneNumbers', phone)
        client.do_action_with_exception(ali_request)
        return HttpResponse(content='发送成功', content_type="application/json")


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
    alirequest = ali_dayu_api('QuerySendDetails', 'MetaKnew', 'SMS_163847373')
    alirequest.add_query_param('PhoneNumbers', mobile)
    alirequest.add_query_param('CurrentPage', current_page)
    alirequest.add_query_param('SendDate', time.strftime("%Y%m%d", time.localtime(int(time.time()))))
    alirequest.add_query_param('PageSize', page_size)
    alirequest.add_query_param('BizId', biz_id)
    response = client.do_action_with_exception(alirequest)
    print(str(response, encoding='utf-8'))

    return JsonResponse(str(response))


# 阿里大于查询公共请求信息封装接口
def ali_dayu_api(actionName, signName, templateCode):
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
