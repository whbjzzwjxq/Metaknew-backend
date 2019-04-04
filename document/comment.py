# -*-coding=utf-8 -*-
from document.models import Comment
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
def selectById(id):
    assert id
    comments = Comment.select().where(Comment.uuid == id)
    return comments

# ID 表示评论id
def updateById(id,filedata={}):
    assert id
    update_field = {}
    for filename in filedata:
        update_field['Comment.'+filename] = filedata[filename]
    res = Comment.update(update_field).where(Comment.id == id).execute()

    return res

# ID 表示评论id
def deleteById(id):
    assert id
    res = Comment.delete().where(Comment.id == id).execute()
    return res