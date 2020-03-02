import json
from typing import List, Dict
from django.http import HttpResponse
from base_api.interface_frontend import Interface, LinkBulkCreateData
from dataclasses import dataclass

from base_api.logic_class import HttpRequestUser
from base_api.subgraph.common import ItemApi
from tools.base_tools import NeoSet
from tools.id_generator import id_generator
from subgraph.class_link import LinkModel


class LinkApi(ItemApi):
    abstract = True
    URL = 'link/'


@dataclass(init=False)
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
        id_list = id_generator(len(result.Links), 'link')
        return [LinkModel(_id, user_model.user_id, 'link', collector).create(info, result.CreateType)
                for info, _id in zip(result.Links, id_list)]

    def _save_hook(self, result: List[LinkModel]) -> Dict[str, str]:
        return LinkModel.bulk_save_create(result, collector=result[0].collector)

    def _response_hook(self, result) -> HttpResponse:
        return HttpResponse(status=200, content=json.dumps(result))


apis = [LinkBulkCreate]
