# -*-coding=utf-8 -*-
from document.models import Document
import datetime as dt

def add(filedata={}):

    '''
    id  = AutoField(db_column='ID', primary_key=True)
    uuid = UUIDField(db_column='UUID')  # 专题id
    userid = IntegerField(db_column='USER_ID')  # 发表用户id
    time = DateTimeField(db_column='TIME')  # 发表时间
    title = CharField(db_column='TITLE')  # 标题
    url = CharField(db_column='URL')  # 缩略图
    description = CharField(db_column='DESCRIPTION')  # 描述
    imp = DoubleField(db_column='IMP')    # 重要度
    hot = DoubleField(db_column='HOT')  # 热度
    hard_level = DoubleField(db_column='HARD_LEVEL')  # 难易度
    area = CharField(db_column='AREA')  # 领域
    size = IntegerField(db_column='SIZE')  # 节点数量
    uuid_list = BinaryUUIDField(db_column='UUID_LIST')  # 相关专题
    :param filedata:
    :return:
    '''
    uuid = filedata['uuid'] if 'uuid' in filedata else ''
    userid = filedata['userid'] if 'userid' in filedata else ''
    time = filedata['time'] if 'time' in filedata else dt.datetime.now()
    title = filedata['title'] if 'title' in filedata else ''
    url = filedata['url'] if 'url' in filedata else ''
    description = filedata['description'] if 'description' in filedata else ''
    imp = filedata['imp'] if 'imp' in filedata else 0.0
    hot = filedata['hot'] if 'hot' in filedata else 0.0
    hard_level = filedata['hard_level'] if 'hard_level' in filedata else 0.0
    area = filedata['area'] if 'area' in filedata else ''
    size = filedata['size'] if 'size' in filedata else 0
    uuid_list = filedata['uuid_list'] if 'uuid_list' in filedata else ''
    doc = Document.create(uuid=uuid, userid=userid,time=time,title=title,
                              url=url,description=description,imp=imp,hot=hot,
                              hard_level=hard_level,area=area,size=size,uuid_list=uuid_list)

    return doc

# id 表示专题id
def selectById(id):
    assert id
    doc = Document.select().where(Document.uuid == id)
    return doc

# ID 表示专题id
def updateById(id,filedata={}):
    assert id
    update_field = {}
    for filename in filedata:
        update_field['Document.'+filename] = filedata[filename]
    res = Document.update(update_field).where(Document.id == id).execute()

    return res

# ID 表示专题id not专题uuid
def deleteById(id):
    assert id
    res = Document.delete().where(Document.id == id).execute()
    return res