from django.core.cache import cache
from django.http import HttpResponse, HttpRequest
from authority.models import *
from tools.redis_process import redis
from users.models import User


# method = ['delete', 'change_state', 'copy', 'query_total', 'query_abbr', 'write', 'export', 'reference', 'download']

# todo 各功能权限表工作 正则匹配实现 level: 2
class AuthMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        self.url_auth_list = {
            '/search/single': [],
            '/document/add_comment': [],
            '/subgraph/add/node': [],
            '/subgraph/add/document': [],
            '/subgraph/run/script_latin': [],
            '/subgraph/run/script_add_loc': [],
            '/user/login': [],
            '/user/register': [],
            '/user/send_message': [],
            '/es_query/index': [],
            '/search/criteria_query': [],
            '/search/get_single_node': [],
            '/tools/generate': []
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
            user_id = redis.get(user_name)
            saved_token = redis.get(user_id)
            if not saved_token:
                request_info.content = '登录信息过期，请重新登录'
            elif not token == saved_token:
                request_info.content = '已经在别处登录了'
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


# class AuthChecker:
#     auth_sheet = BaseAuthority
#
#     def __init__(self, user_id, uuid):
#         self.user_id = user_id
#         self.uuid = uuid
#         self.status = False
#
#     def check(self):
#         self.status = True
#         self.user_status()
#         return self.status
#
#     def user_status(self):
#         record = User.objects.get(pk=self.user_id)
#         if record.Is_Superusero or record.Is_Developer:
#             self.status = True
#         elif record.Is_Banned:
#             self.status = False
#         elif not record.Is_Active:
#             self.status = False
#
#
# class DocQueryChecker(AuthChecker):
#
#     auth_sheet = BaseAuthority
#
#     def __init__(self, user_id, uuid):
#         super().__init__(user_id, uuid)
#         self.user_id = user_id
#         self.uuid = uuid
#         self.status = False
#         self.record = self.auth_sheet.objects.get(uuid=self.uuid)
#
#     def common_checker(self):
#         record = self.record
#         if record.Common:
#             self.status = True
#         elif record.Shared and self.user_id in record.SharedTo:
#             self.status = True
#         elif record.Paid and self.user_id in record.payment:
#             self.status = True
#         elif self.user_id in record.ChangeState:
#             self.status = True
#         elif self.user_id == record.Owner:
#             self.status = True
#
#     def check(self):
#         record = self.record
#         if self.user_id in record.query:
#             self.status = True
#         self.common_checker()
#         self.user_status()
#         return self.status
#
#
# class QueryRecord(AuthChecker):
#
#     def check(self):
#         self.status = False
#         self.user_status()
#         return self.status

class AuthChecker:
    # 这里没有对个人化的内容做验证，这里验证的是全局内容
    auth_sheet = {'document': DocAuthority,
                  'node': NodeAuthority,
                  'media': MediaAuthority
                  }

    def __init__(self, source_type, source_id, user_id, request_type, request_ip):

        self._type = source_type
        self._id = source_id
        self._user = user_id
        self.request_type = request_type
        self._ip = request_ip
        try:
            self.sheet = self.auth_sheet[request_type]
        except AttributeError('从url解析的类型有误'):
            pass

        self.name_func = {
            'delete': self.delete,
            'change_state': self.change_state,
            'copy': self.copy,
            'query_total': self.query_total,
            'query_abbr': self.query_abbr,
            'write': self.write,
            'export': self.export,
            'reference': self.reference,
            'download': self.download
        }

    def check(self):
        record = self.sheet.objects.filter(id=self._id)
        if len(record) == 0:
            self.__anti_spider()
            return HttpResponse(status=404)
        else:
              pass
    def __anti_spider(self):
        pass

    def delete(self):
        pass

    def change_state(self):
        pass

    def copy(self):
        pass

    def query_total(self):
        pass

    def query_abbr(self):
        pass

    def write(self):
        pass

    def export(self):
        pass

    def reference(self):
        pass

    def download(self):
        pass
