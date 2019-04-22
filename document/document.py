from document import models

# 新增专题
def add(filedata = {}):
    doc = models.Document.objects.create(**filedata)
    return doc


