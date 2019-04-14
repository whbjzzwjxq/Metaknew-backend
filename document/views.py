# -*-coding=utf-8 -*-
from django.shortcuts import render
from document import comment,document_info,documentrelate,resource
import datetime as dt
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import uuid
import os
from demo.tools import getHttpResponse
from playhouse.shortcuts import model_to_dict, dict_to_model

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
        res.append(dict(model_to_dict(com,backrefs=True).items()+model_to_dict(com.user, backrefs=True).items()))
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

#根据专题id得到专题info
@csrf_exempt
def get_doc_info(request):
    params = json.loads(request.body)['data']
    doc_id = params['id']
    docs = document_info.selectById(doc_id)
    # return render(request, 'comment.html', {'comments': comments})
    # model_to_dict(comments)
    return HttpResponse(str(docs), content_type="application/json")


# 新增相关专题，先增加新的专题，再添加相关性
def add_document_relate(request):
    if request.POST['title'] == 'null':
        return render(request, 'add_document_relate.html', {})
    filedata = {}
    uuid_now = request.POST["uuid_now"]
    filedata['uuid'] = uuid.uuid1()
    filedata['userid'] = request.POST["userid"]
    filedata['title'] = request.POST["title"]
    filedata['description'] = request.POST["description"]
    filedata['url'] = request.POST["url"]
    filedata['area'] = request.POST["area"]
    document = document_info.add(filedata)
    document_now = document_info.selectById(uuid_now)
    for doc in document_now:
        list = doc.uuid_list
        # print(list)
        if list is not None:
            list_new = list + "," + str(filedata['uuid'])
        else:
            list_new = str(filedata['uuid'])
        document = documentrelate.update_uuidlist(uuid_now, list_new)
    # return render(request, 'add_document_relate.html', {'document': document})
    return HttpResponse(json.dumps(document), content_type="application/json")


# 依据uuid查询相关专题的title列表    疑问：title是否唯一？每个相关专题的详细信息是否可以通过title查找
def select_document_relate_title(request):
    uuid = request.POST.get("uuid")
    print(uuid)
    print(request.body)
    document = document_info.selectById(uuid)
    title_list = {}
    for doc in document:
        uuids = doc.uuid_list
        list = uuids.split(',')
        res = []
        print(list)
        for i in list:
            document_relate = document_info.selectById(i)
            for doc_relate in document_relate:
                title_list['title'] = doc_relate.title
                title_list['des'] = doc_relate.description
                title_list['url'] = doc_relate.url
                res.append(title_list)
                # return render(request, 'document.html', {'title_list': title_list})
    return HttpResponse(json.dumps(res), content_type="application/json")


# 添加专题资源
def add_resource(request):
    filedata = {}
    resp = HttpResponse()
    uuid1 = request.POST["uuid"]
    url = request.POST["file"]
    # res = resource.add(filedata)
    print(url)
    res = resource.selectById(uuid1)
    if not res:
        # l = set()
        # l.add(url)
        l = [url]
        filedata["uuid"] = uuid1
        filedata["file"] = l
        print(filedata["file"])
        resource.add(filedata)
        respData = {'status': '1', 'ret': '添加成功!!!'}
    else:
        for i in res:
            urls = i.file
            urls = urls.append(url)
            filedata["uuid"] = uuid1
            filedata["file"] = urls
            resource.updateById(filedata)
            respData = {'status': '2', 'ret': '资源更新成功!!!'}
    resp.content = json.dumps(respData)
    return HttpResponse(resp, content_type="application/json")


# 根据专题uuid查询资源信息
def select_resource(request):
    uuid = request.POST["uuid"]
    res = resource.selectById(uuid)
    urllist = []
    for i in res:
        url = i.file
        list = url.split(',')
        for j in list:
            urllist.append(j)
    # return render(request, 'resource.html', {'res': res})
    return HttpResponse(json.dumps(urllist), content_type='application/json')


# 根据uuid删除资源信息(用于删除专题时，需删除和其有关的全部资源信息)
def delete_resource(request):
    uuid = request.POST["uuid"]
    res = resource.deleteById(uuid)
    return render(request, 'resource.html', {'res': res})


# 删除资源信息（用于删除某一个专题下的某个资源）      未测
def delete_resource_one(request):
    uuid = request.POST["uuid"]
    url = request.POST["file"]
    filedata = {}
    res = resource.selectById(uuid)
    urls1 = []
    urls2 = []
    urls3 = ''
    urls1.append(url)
    for i in res:
        file = i.file
        filedata['id'] = i.id
        urls2.append(file)
    for i in urls2:
        if i not in urls1:
            if urls3 == '':
                urls3 = i
            else:
                urls3 = urls3 + ',' + i
    filedata['uuid'] = uuid
    filedata['file'] = urls3
    resource.updateById(filedata)


# 更新专题资源
def update_resource(request):
    filedata = {'id': request.POST["id"], 'uuid': request.POST["uuid"]}
    file = request.POST["file"]
    res = resource.selectById(request.POST['uuid'])
    for re in res:
        urls = re.file
        if urls is not None:
            urls = urls + "," + file
        else:
            urls = file

    filedata['file'] = urls
    res = resource.updateById(filedata)
    return render(request, 'resource.html', {'res': res})


def upload_file(request):
    if request.method == "POST":    # 请求方法为POST时，进行处理
        myFile =request.FILES.get("myfile", None)    # 获取上传的文件，如果没有文件，则默认为None
        if not myFile:
            return HttpResponse("no files for upload!")
        destination = open(os.path.join("E:\\upload", myFile.name), 'wb+')    # 打开特定的文件进行二进制的写操作
        for chunk in myFile.chunks():      # 分块写入文件
            destination.write(chunk)
        destination.close()
        return HttpResponse("upload over!")
