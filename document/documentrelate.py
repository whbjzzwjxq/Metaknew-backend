# -*-coding=utf-8 -*-

from django.shortcuts import render
from document.models import Document
import uuid


# 新增相关专题，先增加新的专题，再添加相关性    已测试
def add_document_relate(request):
    uuid_now = request.POST["uuid_now"]
    a = uuid.uuid1()
    userid = request.POST["userid"]
    title = request.POST["title"]
    description = request.POST["description"]
    url = request.POST["url"]
    area = request.POST["area"]
    document = Document.create(uuid=a, userid=userid, title=title, description=description, url=url, area=area)
    document_now = Document.select().where(Document.uuid == uuid_now)
    for doc in document_now:
        list = doc.uuid_list
        # print(list)
        if (list != None):
            list_new = list + "," + str(a)
        else:
            list_new = str(a)
        Document.update({Document.uuid_list: list_new}).where(Document.uuid == uuid_now).execute()
    return render(request, 'add_document_relate.html', {'document': document})


# 依据uuid查询相关专题的title列表    疑问：title是否唯一？每个相关专题的详细信息是否可以通过title查找
def select_document_relate_title(request):
    uuid = request.POST["uuid"]
    document = Document.select().where(Document.uuid == uuid)
    title_list = []
    for doc in document:
        uuids = doc.uuid_list
        list = uuids.split[","]
        for i in list:
            document_relate = Document.select().where(Document.uuid == i)
            for doc_relate in document_relate:
                title_list.append(doc_relate.title)
    return render(request, 'document.html', {'title_list': title_list})


# 更新资源信息
def update_document_relate(request):
    uuid = request.POST["uuid"]
    userid = request.POST["userid"]
    title = request.POST["title"]
    description = request.POST["description"]
    url = request.POST["url"]
    area = request.POST["area"]
    Document.update({Document.userid: userid, Document.title: title, Document.description: description,
                     Document.url: url, Document.area: area}).where(Document.uuid == uuid).execute()
