# -*-coding=utf-8 -*-
from document import models
from users import models
import datetime as dt


def add(filedata={}):
    """
    uuid = filedata['uuid'] if 'uuid' in filedata else ''
    userid = filedata['userid'] if 'userid' in filedata else ''
    time = filedata['time'] if 'time' in filedata else dt.datetime.now()
    content = filedata['content'] if 'content' in filedata else ''
    star = filedata['star'] if 'star' in filedata else 0.0
    """
    comment = models.Comment.objects.create(**filedata)

    return comment
#
# # id 表示专题id
# # 根据专题id得到用户及评论信息
# def selectById(uuid):
#     assert uuid
#     comments = models.Comment.select(Comment,User).join(User,on=(User.userid == Comment.userid)).where(Comment.uuid == uuid)
#     return comments

# ID 表示评论id
def updateById(id,filedata={}):
    assert id
    update_field = {}
    for filename in filedata:
        update_field[filename] = filedata[filename]
    res = models.Comment.objects.filter(id=id).update()

    return res

# ID 表示评论id
def deleteById(id):
    assert id
    res = models.Comment.milter(id=id).delete()
    return res