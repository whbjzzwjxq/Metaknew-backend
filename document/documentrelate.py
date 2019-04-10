# -*-coding=utf-8 -*-

from document.models import Document


# 更新资源的相关专题列表
def update_uuidlist(uuid_now, list_new):
    assert uuid_now, list_new
    documnet = Document.update({Document.uuid_list: list_new}).where(Document.uuid == uuid_now).execute()
    return documnet

