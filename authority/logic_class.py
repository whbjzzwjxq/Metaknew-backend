from django.core.cache import cache
from django.http import HttpResponse, HttpRequest
from authority.models import BaseAuthority
from django.db import models
from users.models import User


class AuthMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        self.url_auth_list = {
            '/search/single': [DocQueryChecker],
            '/document/add_comment': [AuthChecker],
            '/subgraph/add/node': [],
            '/subgraph/add/document': [],
            '/user/login': [],
            '/user/register': [],
            '/user/send_message': [],
            '/search/es_ask/': []
        }

    def __call__(self, request: HttpRequest()):
        path = request.path
        if str(path) in self.url_auth_list:
            _checkers = self.url_auth_list[path]

            if _checkers is not []:
                result = True

                # 注意这里的参数要求
                uuid = request.GET.get('uuid')
                if not uuid:
                    uuid = request.POST.get('uuid')
                if not uuid:
                    uuid = ''
                request_info = self.get_user_auth(request)
                for _check in _checkers:
                    result = result and _check(user_id=request_info.user_id,
                                               uuid=uuid).check()
                if result:
                    return self.get_response(request)
                else:
                    return HttpResponse(status=400, content="操作失败， 原因可能是: %s" % request_info.content)
            else:
                return self.get_response(request)
        else:
            print('未注册的API')
            return HttpResponse(status=400)

    @staticmethod
    def get_user_auth(request: HttpRequest()):
        # 默认情况下视为游客
        request_info = RequestInfo()

        if 'token' in request.COOKIES and 'user_name' in request.COOKIES:
            token = request.COOKIES['token']
            user_name = request.COOKIES['user_name']
            user_id = cache.get(user_name)
            saved_token = cache.get(user_id)
            if not saved_token:
                request_info.content = '登录信息过期，请重新登录'
            elif not token == saved_token:
                request_info.content = '在别处登录了'
            else:
                request_info.content = '您没有这个操作的权限'
                request_info.status = True
                request_info.user_id = user_id
                request.GET._mutable = True
                request.GET.update({"user_id": user_id})
                request.GET._mutable = False
        else:
            request_info.content = '以游客身份登录'
        return request_info


class RequestInfo:

    def __init__(self):
        self.status = False
        self.content = '以游客身份登录'
        self.user_id = 1


class AuthChecker:
    auth_sheet = BaseAuthority

    def __init__(self, user_id, uuid):
        self.user_id = user_id
        self.uuid = uuid
        self.status = False

    def check(self):
        self.status = True
        self.user_status()
        return self.status

    def user_status(self):
        record = User.objects.get(pk=self.user_id)
        if record.Is_Superuser:
            self.status = True
        elif record.Is_Banned:
            self.status = False
        elif not record.Is_Active:
            self.status = False


class DocQueryChecker(AuthChecker):

    auth_sheet = BaseAuthority

    def __init__(self, user_id, uuid):
        super().__init__(user_id, uuid)
        self.user_id = user_id
        self.uuid = uuid
        self.status = False
        self.record = self.auth_sheet.objects.get(uuid=self.uuid)

    def common_checker(self):
        record = self.record
        if record.Common:
            self.status = True
        elif record.Shared and self.user_id in record.SharedTo:
            self.status = True
        elif record.Paid and self.user_id in record.payment:
            self.status = True
        elif self.user_id in record.ChangeState:
            self.status = True
        elif self.user_id == record.Owner:
            self.status = True

    def check(self):
        record = self.record
        if self.user_id in record.query:
            self.status = True
        self.common_checker()
        self.user_status()
        return self.status
