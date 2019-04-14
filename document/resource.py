# -*-coding=utf-8 -*-
from document.models import Resource
import uuid as id
import numpy as np


def add(filedata={}):
    uuid = filedata['uuid'] if 'uuid' in filedata else id.uuid1()
    url = filedata['file'] if 'file' in filedata else ''
    print(url)
    resource = Resource.create(uuid=uuid, file=np.array(url))  # 数组怎么存储!!!!!!!!!!!!!!!
    print(resource)


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


