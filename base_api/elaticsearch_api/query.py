import json

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest, HttpResponse

from base_api.interface_frontend import EsQueryData
from base_api.logic_class import OpenApi, ApiMeta
from document.class_document import DocGraphModel
from es_module.logic_class import EsQuery
from tools.base_tools import filter_to_two_part


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
        result = EsQuery().main(result)
        documents, metas = filter_to_two_part(result, lambda x: x['type'] == 'document')
        active_document = []
        for doc in documents:
            try:
                if DocGraphModel(_id=doc['id'], user_id=0).queryable():
                    active_document.append(doc)
                else:
                    pass
            except ObjectDoesNotExist or BaseException as e:
                pass
        return {'Document': active_document, "Meta": metas}

    def _response_hook(self, result) -> HttpResponse:
        return HttpResponse(status=200, content=json.dumps(result))


apis = [HomePageQuery]
