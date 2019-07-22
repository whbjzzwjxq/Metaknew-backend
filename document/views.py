# -*-coding=utf-8 -*-
# APP内定义
from document.logic_class import BaseComment, BaseNote, BaseDoc
# django定义与工具包
import datetime as dt
from django.http import HttpResponse, StreamingHttpResponse
from django.utils.encoding import escape_uri_path

from demo import settings
from django.views.decorators.csrf import csrf_exempt
import json
import os
from tools.Meta_Response import get_http_response as getHttpResponse
from django.forms.models import model_to_dict
from django.core.cache import cache
from document.logic_class import PersonalDoc


# Create your views here.
@csrf_exempt
# 根据专题id得到个人化的信息
def get_personal_by_doc(request):
    doc_id = request.GET.get('uuid')
    user = request.GET.get('user_id')
    print(user)
    result = PersonalDoc(uuid=doc_id, user=user).query_all()
    print(result.__dict__)
    return HttpResponse(json.dumps(result.__dict__), content_type="application/json")


# 添加评论
@csrf_exempt
def add_comment(request):
    data = json.loads(request.body)['data']
    uuid = request.GET.get('uuid')
    user_id = request.GET.get('user_id')
    if data['content'] == '':
        return HttpResponse("评论不能为空")
    else:
        BaseComment().add(
            base=uuid,
            target=data['target'],
            user=user_id,
            content=str(data['content']),
            update_time=dt.datetime.now()
        )

    return HttpResponse("回复成功")


# 根据commentId删除评论
@csrf_exempt
def delete_comment(request):
    uuid = request.GET.get('uuid')
    if uuid == '':
        return HttpResponse(getHttpResponse('0', '删除失败', ''), content_type='application/json')
    else:
        comment = BaseComment().query(uuid=uuid)
        comment.delete()
    return HttpResponse(getHttpResponse('1', '删除成功', ''), content_type="application/json")


# Create your views here.

# 添加便签         已测试-----4.19----ZXN
def add_note(request):
    """
        "data":{
            "note_type":"normal",
            "content": "test"
        },
        "user_id":
        "uuid":
    }
    """
    data = json.loads(request.body)['data']
    uuid = request.GET.get('uuid')
    user_id = request.GET.get('user_id')
    response = HttpResponse()
    if data['content'] == '':
        return HttpResponse("便签不能为空")
    else:
        BaseNote().add(
            user=user_id,
            doc_uuid=uuid,
            content=data['content'],
            note_type=data['note_type']
        )
        response.content = json.dumps({'status': '1', 'ret': '添加成功!!!'})
        return HttpResponse(response, content_type="application/json")


def update_note(request):
    data = json.loads(request.body)['data']
    target = data['target']
    response = HttpResponse()
    if data['content'] == '':
        return HttpResponse("便签不能为空")
    else:
        BaseNote().query(uuid=target).update_content(new_content=data['content'],
                                                     new_type=data['tag_type'])
        response.content = json.dumps({'status': '1', 'ret': '保存成功!!!'})
        return HttpResponse(response, content_type="application/json")


def delete_note(request):
    data = json.loads(request.body)['data']
    target = BaseNote().query(uuid=data['target'])
    response = HttpResponse()
    if target:
        target.delete()
        response.content = json.dumps({'status': '1', 'ret': '保存成功!!!'})
        return HttpResponse(response, content_type="application/json")
    else:
        return HttpResponse("删除过程错误")

