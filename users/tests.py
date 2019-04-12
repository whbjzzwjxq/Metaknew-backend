from django.test import TestCase

# Create your tests here.
from users import user as userInfo
import json

def login(email, password):

    respData = {}
    # 查询邮箱为email的用户
    userss = userInfo.selectByEmail(email)
    if not userss:
        respData = {'status': '0', 'ret': '用户不存在!!!'}
    for i in userss:
        # 检查密码、验证码是否匹配
        if password == i.userpassword:
            try:
                respData = {'status': '1', 'ret': 'login success!'}
            except BaseException as e:
                print(e)
                pass
                respData = {'status': '0', 'ret': '登录失败，输入信息有误!!!'}
    return respData
    # resp.content = json.dumps(respData)
    # return resp

    # return render(request,'add_user.html',{'user':user})


if __name__ == '__main__':
    i = login('1234@163.com', '1234567890')
    print(i)
