import json

from django.http import HttpRequest, HttpResponse

from base_api.interface_frontend import EsQueryData
from base_api.logic_class import OpenApi, ApiMeta
from es_module.logic_class import EsQuery


class EsApi(OpenApi):
    """
    Es相关Api
    """
    URL = 'es/'
    abstract = True
    meta = ApiMeta(is_user=False, is_dev=False, is_record=False)


class HomePageQuery(EsApi):
    """
    首页查询
    """
    URL = 'home_query'
    abstract = False
    frontend_data = EsQueryData
    method = 'GET'

    def _main_hook(self, result: EsQueryData, request: HttpRequest):
        return EsQuery().main(result)

    def _response_hook(self, result) -> HttpResponse:
        return HttpResponse(status=200, content=json.dumps(result))


apis = [HomePageQuery]
