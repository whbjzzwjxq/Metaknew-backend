import json

from django.http import HttpRequest, HttpResponse

from base_api.interface_frontend import TextBulkCreateData
from base_api.subgraph.common import ItemApi
from tools.id_generator import id_generator


class TextApi(ItemApi):
    abstract = True
    URL = 'text/'


class TextCreateApi(TextApi):
    """
    创建Text
    """
    abstract = False
    URL = 'bulk_create'
    method = 'POST'
    frontend_data = TextBulkCreateData

    def _main_hook(self, result: TextBulkCreateData, request: HttpRequest):
        id_list = id_generator(len(result.Texts), 'item')
        return {old_id: new_id for new_id, old_id in zip(id_list, result.Texts)}

    def _response_hook(self, result) -> HttpResponse:
        return HttpResponse(content=json.dumps(result), status=200)


apis = [TextCreateApi]
