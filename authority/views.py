from django.http import HttpResponse
from django.shortcuts import render
import json
# Create your views here.
from users import user,role
from authority import authority


def addAuthority(request):
    resp = HttpResponse()
    params = json.loads(request.body)['data']
    if_common = params['if_common']
    users = user.showAll()
    res = []
    for u in users:
     res.extend(list(u.values()))
    if if_common == 'CommonWithoutPaid':
        params['read_privilege'] = res
        params['reference_privilege'] = res
        print(params)
        authority.add(params)
        respData = {'status': '1', 'ret': '添加成功!!!'}
    elif if_common == 'CommonWithPaid':
        params['read_privilege'] = res
        authority.add(params)
        respData = {'status': '1', 'ret': '添加成功!!!'}
    elif if_common == 'private':
        role_id = role.getIdByName('root')
        params['total_control'] = user.selectUserByRole(role_id)
        authority.add(params)
        respData = {'status': '1', 'ret': '添加成功!!!'}
    else:
        respData = {'status': '0', 'ret': '添加失败，没有此权限'}
    resp.content = json.dumps(respData)
    return HttpResponse(resp, content_type="application/json")


