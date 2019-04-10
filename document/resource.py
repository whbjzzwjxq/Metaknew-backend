# -*-coding=utf-8 -*-
from django.shortcuts import render
from document.models import Resource
import uuid as id


def add(filedata={}):
    uuid = filedata['uuid'] if 'uuid' in filedata else id.uuid1()
    url = filedata['file'] if 'file' in filedata else ''
    resource = Resource.create(uuid=uuid, file=url)
    return resource
    # resource = Resource.select().where(Resource.uuid == uuid)
    # for re in resource:
    #     if re == "null":
    #         resource = Resource.create(uuid=uuid, file=url)
    #         return render(request, 'add_resource.html', {'resource': resource})
    #     else:
    #         urls = re.file
    #         urls = urls + url
    #         Resource.update({Resource.file: urls}).where(Resource.uuid == uuid).execute()


def selectById(uuid):
    assert uuid
    resource = Resource.select().where(Resource.uuid == uuid)
    return resource


def deleteById(uuid):
    assert uuid
    res = Resource.delete().where(Resource.uuid == uuid).execute()
    return res


def updateById(filedata = {}):
    id = filedata['id'] if 'id' in filedata else ''
    uuid = filedata['uuid'] if 'uuid' in filedata else ''
    file = filedata['file'] if 'file' in filedata else ''
    res = Resource.update({Resource.uuid: uuid, Resource.file: file}).where(Resource.id == id).execute()
    return res
