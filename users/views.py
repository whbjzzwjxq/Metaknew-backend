# -*-coding=utf-8 -*-
import time

from aliyunsdkcore.client import AcsClient
from django.http import JsonResponse
from base_api.user_api import ali_dayu_api


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
