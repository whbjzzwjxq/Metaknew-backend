from users.models import User
import datetime as dt


# 新建用户
def add(filedata={}):
    username = filedata['username'] if 'username' in filedata else ''
    userpw = filedata['userpw'] if 'userpw' in filedata else ''
    useremail = filedata['useremail'] if 'useremail' in filedata else ''
    usertime = filedata['usertime'] if 'usertime' in filedata else dt.datetime.now()
    user = User.create(username=username, userpassword=userpw, dateTime=usertime, useremail=useremail)
    return user


# 查询用户
def selectByEmail(email):
    assert email
    # user = User.get(User.useremail == email)
    user = User.select().where(User.useremail == email)
    return user


# 修改用户资料
def updateById(filedata):
    userid = filedata['userid'] if 'userid' in filedata else ''
    username = filedata['username'] if 'username' in filedata else ''
    useremail = filedata['useremail'] if 'useremail' in filedata else ''
    userpw = filedata['userpw'] if 'userpw' in filedata else ''
    user = User.update({User.username: username, User.useremail: useremail, User.userpassword: userpw}).where(User.userid == userid).execute()
    return user

