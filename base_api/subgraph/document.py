import json
from dataclasses import dataclass
from typing import List, Dict

from django.http import HttpResponse

from base_api.interface_frontend import VisNodeBulkCreateData, InfoFrontend
from base_api.interface_setting import GraphBulkCreateData
from base_api.logic_class import HttpRequestUser, UserApi
from base_api.subgraph.common import ItemApi
from document.class_document import DocGraphModel
from subgraph.class_media import MediaModel
from subgraph.class_node import NodeModel
from tools.base_tools import NeoSet
from tools.global_const import re_for_frontend_id
from tools.id_generator import id_generator


def frontend_check(item: InfoFrontend):
    return re_for_frontend_id.match(item.id)


def bulk_handle(info_list, id_generator_method, model, user_id, create_type, collector):
    """
    :param info_list: info的队列
    :param id_generator_method: 生成id的方式
    :param model: 对应的逻辑模型
    :param user_id: 用户id
    :param create_type: 创建方式
    :param collector: neo4j连接池
    :return:
    """
    id_list = id_generator(len(info_list), method=id_generator_method)
    return [model(_id=_id, user_id=user_id, collector=collector).create(info, create_type)
            for _id, info in zip(id_list, info_list)]


class DocumentApi(UserApi):
    """
    专题模型
    """
    URL = 'document/'
    abstract = True


class VisNodeBulkCreate(ItemApi):
    """
    保存所有link节点的模型
    """
    URL = 'vis_node_bulk_create'
    abstract = False
    meta = ItemApi.meta.rewrite()
    method = 'POST'
    frontend_data = VisNodeBulkCreateData

    def _main_hook(self, result: VisNodeBulkCreateData, request: HttpRequestUser):
        collector = NeoSet()
        user_model = request.user
        user_id = user_model.user_id
        model_dict = {
            'Node': bulk_handle(result.Nodes, 'node', NodeModel, user_id, result.CreateType, collector),
            'Media': bulk_handle(result.Medias, 'node', MediaModel, user_id, result.CreateType, collector)
        }
        return model_dict, collector

    def _save_hook(self, result) -> Dict[str, Dict[str, str]]:
        node_list: List[NodeModel] = result[0]['Node']
        media_list: List[MediaModel] = result[0]['Media']
        return {
            'node': NodeModel.bulk_save_create(node_list, collector=result[1]),
            'media': MediaModel.bulk_save_create(media_list, collector=result[1]),
        }

    def _response_hook(self, result) -> HttpResponse:
        return HttpResponse(status=200, content=json.dumps(result))


class DocumentBulkCreate(DocumentApi):
    """
    创建专题
    """
    URL = 'bulk_create'
    abstract = False
    method = 'POST'
    frontend_data = GraphBulkCreateData
    meta = DocumentApi.meta.rewrite()

    def _main_hook(self, result: GraphBulkCreateData, request: HttpRequestUser):
        user_model = request.user
        collector = NeoSet()
        return [
            DocGraphModel(graph.Conf.id, user_model.user_id, collector).create(graph) for graph in result.GraphList
        ]

    def _save_hook(self, result: List[DocGraphModel]) -> List[int]:
        return DocGraphModel.bulk_save_create(result)

    def _response_hook(self, result) -> HttpResponse:
        return HttpResponse(status=200, content=json.dumps(result))


class DocumentBulkUpdate(DocumentApi):
    """
    更新专题
    """
    URL = 'bulk_update'
    abstract = False
    method = 'POST'
    frontend_data = GraphBulkCreateData
    meta = DocumentApi.meta.rewrite()

    def _main_hook(self, result: GraphBulkCreateData, request: HttpRequestUser):
        user_model = request.user
        collector = NeoSet()
        return [
            DocGraphModel(graph.Conf.id, user_model.user_id, collector).update(graph) for graph in result.GraphList
        ]

    def _save_hook(self, result: List[DocGraphModel]) -> List[int]:
        return DocGraphModel.bulk_save_update(result)

    def _response_hook(self, result) -> HttpResponse:
        return HttpResponse(status=200, content=json.dumps(result))


apis = [VisNodeBulkCreate, DocumentBulkCreate, DocumentBulkUpdate]
