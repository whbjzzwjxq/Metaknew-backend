# -*-coding=utf-8 -*-

from document import comment,document_info
import datetime as dt
from django.http import HttpResponse, StreamingHttpResponse
from django.utils.encoding import escape_uri_path

from demo import settings
from django.views.decorators.csrf import csrf_exempt
import json
import uuid
import os
from demo.tools import getHttpResponse
from django.forms.models import model_to_dict



# Create your views here.
@csrf_exempt
# 根据专题id得到用户及评论信息
def get_comments(request):
    comment_id = json.loads(request.body)['data']['uuid']
    print(comment_id)
    comments = comment.selectById(comment_id)
    res = []
    for com in comments:
        com.uuid = str(com.uuid)
        com.time = str(com.time)
        res.append(dict(model_to_dict(com).items()+model_to_dict(com.user).items()))
    return HttpResponse(json.dumps(res), content_type="application/json")

# 添加评论
@csrf_exempt
def add_comment(request):
    params = json.loads(request.body)['data']
    if params['content'] == '':
        return HttpResponse(getHttpResponse('0','添加失败',''),content_type='application/json')

    params['time'] = dt.datetime.now()
    comm = comment.add(params)
    comm.time = str(comm.time)
    #return render(request,'comment.html',{'comment:':comm})
    return HttpResponse(getHttpResponse('1','添加成功',model_to_dict(comm,backrefs=True)), content_type="application/json")

# 根据commentID 更新评论
@csrf_exempt
def update_comment(request):
    params = json.loads(request.body)['data']
    if params['id'] == '':
        return HttpResponse(getHttpResponse('0','更新失败',''), content_type='application/json')

    if params['content'] == '':
        return HttpResponse(getHttpResponse('0','更新失败',''), content_type='application/json')

    id = params['id']
    ''''
    filedata = {}
    filedata['uuid'] = request.POST['uuid']
    filedata['userid'] = request.POST['userid']
    filedata['time'] = dt.datetime.now()
    filedata['content'] = request.POST['content']
    '''
    params['time'] = dt.datetime.now()
    comm = comment.updateById(id,params)
    print(comm)
    return HttpResponse(getHttpResponse(comm,'更新成功',''), content_type="application/json")

# 根据commentId删除评论
@csrf_exempt
def delete_comment(request):
    params = json.loads(request.body)['data']
    if params['id'] == '':
        return HttpResponse(getHttpResponse('0','删除失败',''), content_type='application/json')

    id = params['id']
    res = comment.deleteById(id)
    return HttpResponse(getHttpResponse(res,'删除成功',''), content_type="application/json")

# 新建专题          已测试--4.17-----ZXN
@csrf_exempt
def add_document_information(request):
    """
    "data":{
		"uuid":
		"create_user":
		"title":
		"url":
		"description":
		"area":
		"included_media":
	}
    """
    resp = HttpResponse()
    params = json.loads(request.body)['data']
    params['time'] = dt.datetime.now()
    document_info.add(params)
    respData = {'status': '1', 'ret': '添加成功!!!'}
    resp.content = json.dumps(respData)
    return HttpResponse(resp, content_type="application/json")

# 根据专题id得到专题信息   已测试--4.17------ZXN
@csrf_exempt
def get_doc_info(request):
    """
        "data":{
    		"uuid":
    	}
        """
    params = json.loads(request.body)['data']
    doc_id = params['uuid']
    docs = document_info.selectById(doc_id)
    res = []
    for doc in docs:
        doc.uuid = str(doc.uuid)
        doc.time = str(doc.time)
        res.append(dict(model_to_dict(doc).items()))
    return HttpResponse(json.dumps(res), content_type="application/json")


# 获取全部的专题信息（uuid + title）     已测试---4.17-----ZXN
@csrf_exempt
def get_all_doc_info(request):
    if request.method == 'GET':
        docs = document_info.selectAll()
        res = []
        # print(docs)
        for doc in docs:
            doc["uuid"] = str(doc["uuid"])
            res.append(doc)
        return HttpResponse(json.dumps(res), content_type="application/json")


# # 依据uuid查询相关专题的title列表    疑问：title是否唯一？每个相关专题的详细信息是否可以通过title查找
# @csrf_exempt
# def select_document_relate_title(request):
#     uuid = request.POST.get("uuid")
#     print(uuid)
#     print(request.body)
#     document = document_info.selectById(uuid)
#     title_list = {}
#     for doc in document:
#         uuids = doc.uuid_list
#         list = uuids.split(',')
#         res = []
#         print(list)
#         for i in list:
#             document_relate = document_info.selectById(i)
#             for doc_relate in document_relate:
#                 title_list['uuid'] = doc_relate.uuid
#                 title_list['title'] = doc_relate.title
#                 title_list['des'] = doc_relate.description
#                 title_list['url'] = doc_relate.url
#                 res.append(title_list)
#                 # return render(request, 'document.html', {'title_list': title_list})
#     return HttpResponse(json.dumps(res), content_type="application/json")


# 根据专题uuid查询资源信息         已测试---4.17----ZXN
def select_resource(request):
    param = json.loads(request.body)['data']
    resource = document_info.selectURLById(param['uuid'])
    urls = []
    url = {}
    for res in resource:
        url['included_media'] = res.included_media
        urls.append(url)
    return HttpResponse(json.dumps(urls), content_type='application/json')


# # 根据uuid删除资源信息(用于删除专题时，需删除和其有关的全部资源信息)
# def delete_resource(request):
#     uuid = request.POST["uuid"]
#     res = resource.deleteById(uuid)
#     return render(request, 'resource.html', {'res': res})


# 删除资源信息（用于删除某一个专题下的某个资源）      未测
def delete_resource(request):
    param = json.loads(request.body)['data']


# 上传文件        已测试---4.18-----ZXN
def upload_file(request):
    resp = HttpResponse()
    uuid = request.POST.get("uuid", "")
    my_file = request.FILES.get("myfile", None)
    if not my_file:
        respData = {'status': '0', 'ret': '没有可上传的文件！！！'}
    else:
        if os.sep in my_file.name:
            respData = {'status': '1', 'ret': r"""请注意文件命名格式，'\ / " * ? < > '符号文件不允许上传。"""}
        else:
            myfilepath = settings.BASE_DIR + os.sep + "files" + os.sep + "upload" + os.sep + my_file.name
            print(myfilepath)
            docs = document_info.selectURLById(uuid)
            for doc in docs:
                names = doc.included_media
                print(names)
                if names != None:
                    if my_file.name in names:
                        respData = {'status': '2', 'ret': '该文件已存在,请勿重复上传'}
                    else:
                        with open(myfilepath, 'wb+') as f:
                            for chunk in my_file.chunks():  # 分块写入文件
                                f.write(chunk)
                        names.append(my_file.name)
                        document_info.updateURLById(uuid, names)
                        respData = {'status': '3', 'ret': '上传成功！！！'}
                else:
                    with open(myfilepath, 'wb+') as f:
                        for chunk in my_file.chunks():  # 分块写入文件
                            f.write(chunk)
                    names = []
                    print(str(my_file.name))
                    names.append(str(my_file.name))
                    print(names)
                    document_info.updateURLById(uuid, names)
                    respData = {'status': '3', 'ret': '上传成功！！！'}
    resp.content = json.dumps(respData)
    return HttpResponse(resp, content_type="application/json")


# 下载文件                         已测试------4.18-----ZXN
def download_file(request):
    resp = HttpResponse()
    uuid = request.POST.get("uuid", "")
    fileName = request.POST.get("fileName", "")
    docs = document_info.selectURLById(uuid)
    for doc in docs:
        names = doc.included_media
        print(names)
        print(fileName)
        if fileName in names:
            the_file_name = settings.BASE_DIR + os.sep + "files" + os.sep + "upload" + os.sep + fileName
            file = open(the_file_name, 'rb')
            # response = StreamingHttpResponse(file_iterator(url))
            response = StreamingHttpResponse(file)
            response['Content-Type'] = 'application/octet-stream; charset=unicode'
            response['Content-Disposition'] = 'attachment;filename="{0}"'.format(escape_uri_path(fileName))  # escape_uri_path()解决中文名文件(from django.utils.encoding import escape_uri_path)
            return response
        # return HttpResponse(resp, content_type="application/json")


# 删除文件             已测试---4.18-----ZXN
def delete_file(request):
    resp = HttpResponse()
    uuid = request.POST.get("uuid", "")
    fileName = request.POST.get("fileName", "")
    docs = document_info.selectURLById(uuid)
    for doc in docs:
        names = doc.included_media
        if fileName in names:
            names.remove(fileName)
            document_info.updateURLById(uuid, names)
            the_file_name = settings.BASE_DIR + os.sep + "files" + os.sep + "upload" + os.sep + fileName
            if os.path.exists(the_file_name):
                os.remove(the_file_name)
                respData = {'status': '1', 'ret': '删除成功！！！'}
            else:
                respData = {'status': '0', 'ret': "文件不存在，删除失败,请于管理员联系。"}
        else:
            respData = {'status': '0', 'ret': "文件不存在，删除失败,请于管理员联系。"}
    resp.content = json.dumps(respData)
    return HttpResponse(resp, content_type="application/json")