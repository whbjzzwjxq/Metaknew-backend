from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
import json
import os
from demo import settings
from document.logic_class import BaseDoc
from media.logic_class import BaseMedia
import datetime as dt

# 上传文件
def upload_file(request):
    response = HttpResponse()
    resp = []
    uuid = request.POST.get("uuid")
    user_id = request.POST.get('userId')
    Description = request.POST.get('description')
    data = {}
    data['uuid'] = uuid
    data['Description'] = Description
    data['UploadUser'] = user_id
    data['UploadTime'] = dt.datetime.now()
    my_file = request.FILES.get("my_file", None)
    respData = {}
    if not my_file:
        respData = {'status': '0', 'ret': '没有上传文件！！！'}
    else:
        if os.sep in my_file.name:
            respData = {'status': '1', 'ret': r"""请注意文件命名格式，'\ / " * ? < > '符号文件不允许上传。"""}
        else:
            myfilepath = settings.BASE_DIR + os.sep + "files" + os.sep + "upload" + os.sep + my_file.name
            data['Url'] = myfilepath
            data['AbbrPic'] = myfilepath
            data['FileName'] = os.path.splitext(my_file.name)[0]
            data['Format'] = os.path.splitext(my_file.name)[-1]
            print("文件名称：" + data['FileName'],"扩展名：" + data['Format'])
            d = BaseDoc()
            b = BaseMedia()
            docs = d.query_info(uuid=uuid)
            print(docs.Info.uuid)
            media_uuid_list = docs.Info.IncludedMedia
            print(media_uuid_list[0])
            if media_uuid_list[0] != None:
                if my_file.name in media_uuid_list:
                    respData = {'status': '2', 'ret': '该文件已存在,请勿重复上传'}
                else:
                    with open(myfilepath, 'wb+') as f:
                        for chunk in my_file.chunks():  # 分块写入文件
                            f.write(chunk)
                    doc = b.create(data)
                    media_uuid_list.append(doc.Media.uuid)
                    d.update_media_by_uuid(uuid, media_uuid_list)
                    respData = {'status': '3', 'ret': '上传成功！！！'}
            else:
                with open(myfilepath, 'wb+') as f:
                    for chunk in my_file.chunks():  # 分块写入文件
                        f.write(chunk)
                names = []
                doc = b.create(data)
                print(str(doc))
                names.append(str(my_file.name))
                print(names)
                d.update_media_by_uuid(uuid, names)
                respData = {'status': '3', 'ret': '上传成功！！！'}

    return HttpResponse(json.dumps(respData), content_type="application/json")

