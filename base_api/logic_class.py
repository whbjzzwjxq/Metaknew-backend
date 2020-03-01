import json
from dataclasses import dataclass, asdict, field
from typing import Any, TypeVar, Dict
from typing import Type

from django.http import HttpRequest, HttpResponse
from django.urls import path
from enum import Enum

from base_api.interface_frontend import Interface, DataClass
from record.exception import RewriteMethodError, TestApi
from users.logic_class import BaseUser


class VersionApi(Enum):
    latest = 'latest'


class HttpRequestUser(HttpRequest):
    """
    绑定了user_model的请求
    """
    user: BaseUser


def merge_request(request: HttpRequest, user_model: BaseUser) -> HttpRequestUser:
    request.user = user_model
    return request


@dataclass
class ApiMeta:
    """
    API 元数据
    """
    is_user: bool = True  # 是否需要用户登录
    is_dev: bool = False  # 是否是开发级别的API
    is_record: bool = False  # 是否需要记录
    is_active: bool = True  # 是否正在使用
    is_test: bool = True  # 是否是测试逻辑 不保存模型
    version: str = 'latest'  # 版本

    @property
    def to_dict(self):
        return asdict(self)

    def rewrite(self, **kwargs):
        """
        简易的重写方法
        :param kwargs:
        :return:
        """
        props = self.to_dict
        props.update(kwargs)
        return ApiMeta(**props)


@dataclass
class LoginResponse(DataClass):
    token: str
    userName: str
    userId: str
    fileToken: dict
    personalId: str
    content: str = field(default='登录成功')


class __ApiBase:
    """
    API基类
    """
    meta: ApiMeta  # 元信息
    URL = ''  # url
    method: str  # 方法
    frontend_data: Type[Interface] = Interface  # 前端数据格式
    response_data: Any  # 后端数据格式
    abstract: bool = True  # 是否抽象

    def __init__(self):
        pass

    def __call__(self, request: HttpRequest):
        raise RewriteMethodError


class Api(__ApiBase):
    """
    API
    """
    meta = ApiMeta(is_user=True, is_dev=False, is_record=False, is_test=False, is_active=True, version='2020-02-01')
    URL = ''

    @property
    def url_pattern(self):
        """
        输出Api
        :return:
        """
        if self.abstract:
            return None
        else:
            return path(self.base_url, self)

    @property
    def base_url(self):
        """
        基本Api
        :return:
        """
        url = ''
        for cls in self.__class__.__mro__:
            url = getattr(cls, 'URL', '') + url
        print(self.__class__.__name__ + ' url: ' + url)
        return url

    def __call__(self, request):
        result = self._serialize_hook(request)
        result = self._main_hook(result, request)
        if not self.meta.is_test:
            result = self._save_hook(result)
            return self._response_hook(result)
        else:
            TestApi.raise_error()

    def _serialize_hook(self, request):
        """
        序列化请求数据
        :param request:
        :return:
        """
        if self.frontend_data:
            expect_format = self.frontend_data.fields()
            if self.method == 'GET':
                # GET 只是扁平数据
                frontend_dict = {}
                for k in expect_format:
                    v = request.GET.get(k.name, None)
                    frontend_dict[k.name] = v
                return self.frontend_data(**frontend_dict)
            elif self.method == 'POST':
                return self.frontend_data(**json.loads(request.body))
            else:
                return self._special_hook_(request)
        else:
            return None

    def _special_hook_(self, request) -> Type[Interface]:
        """
        特殊方法钩子
        :param request:
        :return:
        """
        pass

    def _main_hook(self, result: Type[Interface], request: HttpRequest) -> Any:
        """
        主执行体钩子
        :param result:
        :return:
        """
        pass

    def _save_hook(self, result) -> Any:
        """
        保存模型钩子
        :param result: 默认返回main_hook的结果
        :return:
        """
        return result

    def _response_hook(self, result) -> HttpResponse:
        """
        响应前端钩子
        :param result:
        :return:
        """
        pass


class DevApi(Api):
    """
    开发API
    """
    meta = ApiMeta(is_user=True, is_dev=True, is_record=False, version='2020-02-01')
    URL = 'dev/'
    abstract = True


class OpenApi(Api):
    """
    前端API
    """
    URL = 'apis/'
    abstract = True


class GuestApi(OpenApi):
    """
    游客可用Api
    """
    meta = Api.meta.rewrite(is_user=False)
    URL = ''
    abstract = True


class UserApi(OpenApi):
    """
    用户登录才能用的Api
    """
    meta = Api.meta.rewrite(is_user=True)
    URL = ''
    abstract = True

    def _main_hook(self, result: Type[Interface], request: HttpRequestUser) -> Any:
        """
        主执行体钩子
        :param result:
        :return:
        """
        pass


T = TypeVar('T')
all_subclasses = {}


def get_all_subclass(model: T) -> Dict[str, T]:
    for sub in model.__subclasses__():
        if sub.__name__ not in all_subclasses:
            all_subclasses.update({sub.__name__: sub})
        get_all_subclass(sub)
    return all_subclasses
