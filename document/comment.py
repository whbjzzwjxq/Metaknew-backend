# -*-coding=utf-8 -*-
from document.models import Comment
from users.models import User
import datetime as dt

def add(filedata={}):

    uuid = filedata['uuid'] if 'uuid' in filedata else ''
    userid = filedata['userid'] if 'userid' in filedata else ''
    time = filedata['time'] if 'time' in filedata else dt.datetime.now()
    content = filedata['content'] if 'content' in filedata else ''
    star = filedata['star'] if 'star' in filedata else 0.0
    comment = Comment.create(uuid=uuid, userid=userid,time=time,content=content,star=star)

    return comment

# id 表示专题id
# 根据专题id得到用户及评论信息
def selectById(uuid):
    assert uuid
    comments = Comment.select(Comment,User).join(User,on=(User.userid == Comment.userid)).where(Comment.uuid == uuid)
    return comments

# ID 表示评论id
def updateById(id,filedata={}):
    assert id
    update_field = {}
    for filename in filedata:
        update_field[filename] = filedata[filename]
    res = Comment.update(update_field).where(Comment.id == id).execute()

    return res

# ID 表示评论id
def deleteById(id):
    assert id
    res = Comment.delete().where(Comment.id == id).execute()
    return res