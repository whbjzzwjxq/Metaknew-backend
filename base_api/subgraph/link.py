import json
from typing import List, Dict

from django.http import HttpResponse

from base_api.interface_frontend import LinkBulkCreateData, QueryData
from base_api.logic_class import HttpRequestUser
from base_api.subgraph.common import ItemApi
from subgraph.class_link import LinkModel
from tools.base_tools import NeoSet, DateTimeEncoder
from tools.id_generator import id_generator


class LinkApi(ItemApi):
    abstract = True
    URL = 'link/'


class LinkBulkCreate(LinkApi):
    """
    link bulk 创建
    """
    URL = 'bulk_create'
    abstract = False
    method = 'POST'
    meta = LinkApi.meta.rewrite()
    frontend_data = LinkBulkCreateData

    def _main_hook(self, result: LinkBulkCreateData, request: HttpRequestUser) -> List[LinkModel]:
        collector = NeoSet()
        user_model = request.user
        id_list = id_generator(len(result.Links), 'item')
        return [LinkModel(_id, user_model.user_id, 'link', collector).create(info, result.CreateType)
                for info, _id in zip(result.Links, id_list)]

    def _save_hook(self, result: List[LinkModel]) -> Dict[str, str]:
        if result is not []:
            return LinkModel.bulk_save_create(result, collector=result[0].collector)
        else:
            return {}

    def _response_hook(self, result) -> HttpResponse:
        return HttpResponse(status=200, content=json.dumps(result))


class LinkBulkUpdate(LinkApi):
    """
    link update
    """
    URL = 'bulk_update'
    abstract = False
    method = 'POST'
    meta = LinkApi.meta.rewrite()
    frontend_data = LinkBulkCreateData

    def _main_hook(self, result: LinkBulkCreateData, request: HttpRequestUser):
        collector = NeoSet()
        user_model = request.user
        return [LinkModel(link.id, user_model.user_id, 'link', collector).update(link, result.CreateType)
                for link in result.Links]

    def _save_hook(self, result):
        if len(result) > 0:
            return LinkModel.bulk_save_update(result, collector=result[0].collector)
        else:
            return True

    def _response_hook(self, result) -> HttpResponse:
        if result is not None:
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=400)


class LinkQuery(LinkApi):
    """
    link Query
    """
    URL = 'query'
    abstract = False
    method = 'POST'
    frontend_data = QueryData
    meta = LinkApi.meta.rewrite(is_user=False)

    def _main_hook(self, result: QueryData, request: HttpRequestUser):
        user_id = getattr(request.user, 'user_id', 0)
        return [LinkModel(_id=query.id, user_id=user_id, _type=query.type).handle_for_frontend()
                for query in result.DataList]

    def _response_hook(self, result) -> HttpResponse:
        return HttpResponse(status=200, content=json.dumps(result, cls=DateTimeEncoder))


apis = [LinkBulkCreate, LinkBulkUpdate, LinkQuery]
