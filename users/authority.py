from django.http import HttpResponse, HttpRequest
from tools.redis_process import *
from users.models import BaseAuthority, DocAuthority, NodeAuthority, MediaAuthority, CourseAuthority
import regex
import typing

default_request_info = {
    "status": True,
    "content": "",
    "user_id": 0
}


# todo 各功能权限表工作 正则匹配实现 level: 2
class AuthMiddleware:
    accurate_match_url = {
        "/subgraph/media_node_create": {"user_type": "user", "method": "create"}
    }
    regex_match_url = {}
    default_checker = {
        "user_type": "guest",  # guest || User || Vip || HighVip || Publisher || Developer || Superuser
        "method": "query",  # query || update || download || create ||
        "common_source": False,  # True || False
        "personal_source": False,  # True || False
        "source_type": "node",  # node || media || document || course  公有资源
                                # link || comment || note || fragment  私有资源
    }
    auth_sheet :typing.Dict[str: BaseAuthority]= {
        "document": DocAuthority,
        "node": NodeAuthority,
        "media": MediaAuthority,
        "course": CourseAuthority
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest()):
        request_info = self.confirm_login_status(request)
        if not request_info["status"]:
            return HttpResponse(status=400, content=request_info["content"])
        else:
            _checker = self.match_url(request)
            if _checker == {}:
                return self.get_response(request)
            else:
                user_info = user_query_info_by_id(request_info["user_id"])

                # 如果请求允许游客访问就不检查了
                if _checker["user_type"] != "guest":

                    # 如果是游客 就拒绝
                    if user_info == {}:
                        return HttpResponse(status=400, content='当前操作不支持游客访问')
                    else:
                        status, content = self.check_user_type(_checker, user_info)
                        request_info["content"] = content
                        request_info["status"] &= status

                # 针对共有资源的权限检查
                if _checker["common_source"]:
                    _id = request.GET.get("_id")
                    status, content = self.check_common_source(_checker, user_info, _id)
                    request_info["content"] = content
                    request_info["status"] &= status

                # 针对私有资源的权限检查
                if _checker["personal_source"]:
                    _id = request.GET.get("_id")
                    status, content = self.check_personal_source(_checker, user_info, _id)
                    request_info["content"] = content
                    request_info["status"] &= status

                if request_info["status"]:
                    return self.get_response(request)
                else:
                    return HttpResponse(status=400, content=request_info["content"])

    def __anti_spider(self):
        pass

    def match_url(self, request: HttpRequest()):
        path = request.path

        for url in self.accurate_match_url:
            if path == url:
                _checker = self.accurate_match_url[url]

                # 会填充默认内容
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
                request_info["status"] = False
            elif not token == saved_token:
                request_info["content"] = "已经在别处登录了"
                request_info["status"] = False
            else:
                request_info["content"] = ""
                request_info["status"] = True
                request_info["user_id"] = user_id

                request.GET._mutable = True
                request.GET.update({"user_id": user_id})
                request.GET._mutable = False
        else:
            request_info["content"] = "以游客身份登录"
            request_info["status"] = True
            request_info["user_id"] = 0
        return request_info

    @staticmethod
    def check_user_type(_checker, user_info) -> (bool, str):

        """
        用户类型检查
        :param _checker: 验证配置
        :param user_info: 用户信息
        :return: (bool, str)
        """

        user_type = _checker["user_type"]  # 需要的用户类型
        bool_info = user_info["bool_info"]  # 用户实际类型的表
        content = "操作需要您有%s的权限" % user_type
        # 总体控制
        if bool_info["Is_Banned"]:
            return False, "您的账号已经被封禁"
        if not bool_info["Is_Active"]:
            return False, "您的账号已经暂时冻结"
        if bool_info["Is_Superuser"]:
            return True, ""

        # 角色验证
        if user_type == "SuperUser":
            if bool_info["Is_Superuser"]:
                return True, ""
            else:
                return False, content
        elif user_type == "Developer":
            if bool_info["Is_Developer"]:
                return True, ""
            else:
                return False, content
        elif user_type == "Publisher":
            if bool_info["Publisher"]:
                return True, ""
            else:
                return False, content
        elif user_type == "Vip":
            if bool_info["Is_Vip"] or bool_info["Is_high_vip"]:
                return True, ""
            else:
                return False, content
        elif user_type == "HighVip":
            if bool_info["Is_high_vip"]:
                return True, ""
            else:
                return False, content
        elif user_type == "User":
            return True, ""

    def check_common_source(self, _checker, user_info, _id) -> (bool, str):
        """
        共有资源权限验证
        :param _checker: 验证配置
        :param user_info: 用户信息
        :param _id: 共有资源id
        :return: (bool, str)
        """
        method = _checker["method"]
        source_type = _checker["source_type"]
        record = self.auth_sheet[source_type].objects.filter(SourceId=_id)
        if len(record) == 0:
            self.__anti_spider()
            return HttpResponse(status=404)
        else:
            record = record[0]
            if not record.Used and not method == 'recycle':
                return False, "资源已经失效"
            else:
                # root和dev可以完全操作
                bool_info = user_info["bool_info"]
                user_privilege = user_info["privilege"]
                join_group = user_info["join_group"]
                if bool_info["Is_Superuser"]:
                    return True, ""
                elif bool_info["Is_Developer"] and not method == "delete":
                    return True, ""

                # 业务性验证
                if not record.Common:
                   pass


        return True, ""

    @staticmethod
    def check_personal_source(_checker, user_info, _id) -> (bool, str):
        return True, ""


class AuthChecker:
    # 这里没有对个人化的内容做验证，这里验证的是全局内容
    auth_sheet = {"document": DocAuthority,
                  "node": NodeAuthority,
                  "media": MediaAuthority,
                  "course": CourseAuthority
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
