# -*-coding=utf-8 -*-
from django.shortcuts import render
from document.models import Resource


# 添加专题资源         已测试
def add_resource(request):
    uuid = request.POST["uuid"]
    url = request.POST["url"]
    resource = Resource.create(uuid=uuid, file=url)
    return render(request, 'add_resource.html', {'resource': resource})
    # resource = Resource.select().where(Resource.uuid == uuid)
    # for re in resource:
    #     if re == "null":
    #         resource = Resource.create(uuid=uuid, file=url)
    #         return render(request, 'add_resource.html', {'resource': resource})
    #     else:
    #         urls = re.file
    #         urls = urls + url
    #         Resource.update({Resource.file: urls}).where(Resource.uuid == uuid).execute()


# 根据专题uuid查询资源信息   已测试
def select_resource(request):
    uuid = request.POST["uuid"]
    resource = Resource.get(Resource.uuid == uuid)
    return render(request, 'resource.html', {'resource': resource})


# 根据资源id删除资源信息   已测试
def delete_resource(request):
    id = request.POST["id"]
    Resource.delete().where(Resource.id == id).execute()


# 更新专题资源    已测试
def update_resource(request):
    id = request.POST["id"]
    uuid = request.POST["uuid"]
    file = request.POST["file"]
    resource = Resource.select().where(Resource.uuid == uuid)
    for re in resource:
        urls = re.file
        if(urls != None):
            urls = urls + "," + file
        else:
            urls = file
    Resource.update({Resource.uuid: uuid, Resource.file: urls}).where(Resource.id == id).execute()
