from django.http import HttpResponse, HttpRequest
from tools.redis_process import *
from users.models import DocAuthority, NodeAuthority, MediaAuthority
import regex

default_request_info = {
    "status": True,
    "content": "",
    "user_id": 0
}


# todo 各功能权限表工作 正则匹配实现 level: 2
class AuthMiddleware:
    accurate_match_url = {
        "/subgraph/media_node_create": {"user_type": "user"}
    }
    regex_match_url = {}
    default_checker = {
        "user_type": "guest",  # guest || user || vip || high_vip || publisher || developer || superuser
        "method_type": "query",  # query || write || download ||
        "need_source_id": False,  # True || False
        "source_type": "node"  # node || media || document || course
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest()):
        request_info = self.confirm_login_status(request)
        _checker = self.match_url(request)

        if _checker == {}:
            return self.get_response(request)
        else:
            user_info = user_query_info_by_id(request_info["user_id"])
            return self.get_response(request)

    def match_url(self, request: HttpRequest()):
        path = request.path
        for url in self.accurate_match_url:
            if path == url:
                _checker = self.accurate_match_url[url]
                for key in self.default_checker:
                    if key not in _checker:
                        _checker.update({key: self.default_checker[key]})
                return _checker

        for regex_instance in self.regex_match_url:
            if regex_instance.match(path):
                _checker = self.regex_match_url[regex_instance]
                for key in self.default_checker:
                    if key not in _checker:
                        _checker.update({key: self.default_checker[key]})
                return _checker

        return {}

    @staticmethod
    def confirm_login_status(request: HttpRequest()) -> default_request_info:
        # 默认情况下视为游客
        request_info = default_request_info
        token = request.headers["Token"]
        user_name = request.headers["User-Name"]
        if token != "null" and user_name != "null":
            user_id, saved_token = user_query_by_name(user_name)
            if not saved_token:
                request_info["content"] = "登录信息过期，请重新登录"
            elif not token == saved_token:
                request_info["content"] = "已经在别处登录了"
            else:
                request_info["content"] = "您没有这个操作的权限"
                request_info["status"] = True
                request_info["user_id"] = user_id

                request.GET._mutable = True
                request.GET.update({"user_id": user_id})
                request.GET._mutable = False
        else:
            request_info["content"] = "以游客身份登录"
        return request_info

    def user_type_check(self):
        pass


class AuthChecker:
    # 这里没有对个人化的内容做验证，这里验证的是全局内容
    auth_sheet = {"document": DocAuthority,
                  "node": NodeAuthority,
                  "media": MediaAuthority
                  }

    def __init__(self, source_type, source_id, user_id, request_type, request_ip):

        self._type = source_type
        self._id = source_id
        self._user = user_id
        self.request_type = request_type
        self._ip = request_ip
        try:
            self.sheet = self.auth_sheet[request_type]
        except AttributeError("从url解析的类型有误"):
            pass

        self.name_func = {
            "delete": self.delete,
            "change_state": self.change_state,
            "copy": self.copy,
            "query_total": self.query_total,
            "query_abbr": self.query_abbr,
            "write": self.write,
            "export": self.export,
            "reference": self.reference,
            "download": self.download
        }

    def check(self):
        record = self.sheet.objects.filter(RecordId=self._id)
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
