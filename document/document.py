
# -*-coding=utf-8 -*-
from document import models

# id 表示专题uuid
def selectById(uuid):
    assert uuid
    doc = models.Document.objects.filter(uuid=uuid)
    return doc

