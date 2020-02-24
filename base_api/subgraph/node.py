import json

from django.http import HttpResponse

from base_api.logic_class import HttpRequestBoundUser, Api
from base_api.subgraph.common import ItemApi
from base_api.interface_frontend import NodeBulkCreateData
from typing import List, Type

from subgraph.class_node import NodeModel
from tools.base_tools import NeoSet
from tools.id_generator import id_generator


class NodeApi(ItemApi):
    abstract = True
    URL = 'node/'


class NodeBulkCreate(NodeApi):
    abstract = False
    method = 'POST'
    URL = 'bulk_create'
    frontend_data = NodeBulkCreateData
    meta = NodeApi.meta.rewrite()

    def _main_hook(self, result: NodeBulkCreateData, request: HttpRequestBoundUser):
        data_list = result.Data
        collector = NeoSet()
        user_model = request.user
        id_list = id_generator(number=len(data_list), method='node', jump=3)
        node_model_list = [
            NodeModel(_id=_id,
                      user_id=user_model.user_id,
                      _type=node_info.type,
                      collector=collector
                      ).create(node_info, create_type=result.CreateType)
            for node_info, _id in zip(data_list, id_list)]
        return node_model_list, collector

    def _save_hook(self, result: (List[NodeModel], NeoSet)):
        result = NodeModel.bulk_save_create(*result)
        return result

    def _response_hook(self, result):
        if result is not None:
            return HttpResponse(status=200, content=json.dumps(result))
        else:
            return HttpResponse(status=400, content=json.dumps(result))


class NodeBulkUpdate(NodeApi):
    abstract = False
    method = 'POST'
    URL = 'bulk_update'
    frontend_data = NodeBulkCreateData

    def _main_hook(self, result: NodeBulkCreateData, request: HttpRequestBoundUser):
        data_list = result.Data
        collector = NeoSet()
        user_model = request.user
        node_model_list = [
            NodeModel(_id=node_info._id,
                      user_id=user_model.user_id,
                      _type=node_info.type,
                      collector=collector
                      ).update_by_user(node_info, create_type=result.CreateType)
            for node_info in data_list]
        return node_model_list, collector

    def _save_hook(self, result):
        result = NodeModel.bulk_save_update(*result)
        return result

    def _response_hook(self, result) -> HttpResponse:
        if result is not None:
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=400)


apis: List[Type[Api]] = [
    NodeBulkCreate,
    NodeBulkUpdate
]