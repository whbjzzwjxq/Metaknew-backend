import json
from django.http import HttpResponse
from django.forms.models import model_to_dict
from note import note_info
# Create your views here.

# 添加便签         已测试-----4.19----ZXN
def add_note(request):
    """
        "data":{
        "user_id":
        "tags_type":
        "content":
        "document_id":
    }
    """
    param = json.loads(request.body)['data']
    resp = HttpResponse()
    note_info.add(param)
    respData = {'status': '1', 'ret': '添加成功!!!'}
    resp.content = json.dumps(respData)
    return HttpResponse(resp, content_type="application/json")


# 删除便签         已测试-----4.19----ZXN
def delete_note(request):
    param = json.loads(request.body)['data']
    resp = HttpResponse()
    note_info.deleteById(param['id'])
    respData = {'status': '1', 'ret': '删除成功！！！'}
    resp.content = json.dumps(respData)
    return HttpResponse(resp, content_type="application/json")

# 更新便签         已测试-----4.19----ZXN
def update_note(request):
    """
     "data": {
         "id":
         "user_id":
         "tags_type":
         "content":
         "document_id":
     }
     :param filedata:
     :return:
     """
    param = json.loads(request.body)['data']
    resp = HttpResponse()
    note_info.updateById(param)
    respData = {'status': '1', 'ret': '更新成功！！！'}
    resp.content = json.dumps(respData)
    return HttpResponse(resp, content_type="application/json")


# 显示便签         已测试-----4.19----ZXN
def show_note(request):
    """
       "data":{
           "user_id":
           "document_id":
       }
       :param request:
       :return:
       """
    param = json.loads(request.body)['data']
    notes = note_info.selectByUserId(param['user_id'], param['document_id'])
    res = []
    for note in notes:
        note.document_id = str(note.document_id)
        res.append(dict(model_to_dict(note).items()))
    return HttpResponse(json.dumps(res), content_type="application/json")
