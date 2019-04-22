
from note import models

# 添加便签
def add(filedata = {}):
    notes = models.Note.objects.create(**filedata)
    return notes


# 删除便签
def deleteById(id):
    assert id
    notes = models.Note.objects.filter(id=id).delete()
    return notes


# 更新便签
def updateById(filedata = {}):
    id = filedata['id']
    notes = models.Note.objects.filter(id=id).update(**filedata)
    return notes


# 依据用户id和专题uuid查询便签, document_id代表专题的uuid
def selectByUserId(user_id, document_id):
    assert user_id, document_id
    notes = models.Note.objects.filter(user_id=user_id, document_id=document_id)
    return notes