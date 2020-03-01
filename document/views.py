import json
from datetime import datetime

from django.http import HttpResponse

from document.class_document import DocGraphModel
from record.logic_class import ItemHistory
from subgraph.class_link import KnowledgeLinkModel
from subgraph.class_media import MediaModel
from subgraph.class_node import NodeModel
from subgraph.views import UserApi
from tools.base_tools import NeoSet
from tools.base_tools import filter_to_two_part
from tools.global_const import re_for_frontend_id
from tools.id_generator import id_generator


def frontend_check(item):
    return re_for_frontend_id.match(item['_id'])


def bulk_handle(info_list, id_generator_method, model, user_id, collector):
    """

    :param info_list: info的队列
    :param id_generator_method: 生成id的方式
    :param model: 对应的逻辑模型
    :param user_id: 用户id
    :param collector: neo4j连接池
    :return:
    """
    new_item, remote_item = filter_to_two_part(info_list, frontend_check)
    id_list = id_generator(len(new_item), method=id_generator_method)
    new_item_list = [model(_id=_id, user_id=user_id, collector=collector).create(info)
                     for _id, info in zip(id_list, info_list)]
    remote_item_list = [model(_id=info['_id'], user_id=user_id, collector=collector).ctrl_update_hook(info) for info in info_list]
    return model.bulk_save_create(new_item_list), model.bulk_save_update(remote_item_list)


class DocumentApi(UserApi):

    def query(self):
        """
        data_example: {
            "_id": '',
            "_type": "",
            "_label": ""
        }
        :return:
        """
        pass

    def update_info(self, request):
        """
        data_example: {
            "nodes": [],  info部分
            "links": [],  info部分
            "medias": [],  info部分
        }
        :param request:
        :return:
        """
        collector = NeoSet()
        frontend_data, user_model = self._meta_resolve(request)
        result_id_map = {
            'nodes': {},
            'links': {},
            'medias': {}
        }
        # 先更新所有info
        user_id = user_model.user_id
        nodes = frontend_data['nodes']
        medias = frontend_data['medias']
        links = frontend_data['links']
        result_id_map['nodes'] = bulk_handle(nodes, 'node', NodeModel, user_id, collector)
        result_id_map['medias'] = bulk_handle(medias, 'node', MediaModel, user_id, collector)
        result_id_map['links'] = bulk_handle(links, 'link', KnowledgeLinkModel, user_id, collector)
        return HttpResponse(status=200, content=json.dumps(result_id_map))

    def draft_save(self, request):
        """
        data_example: {
            "_id": "",
            "IsAuto": bool,
            "Name": '',
            "Content": {
                "Graph": "",
                "Conf": {},
            },
        }
        :param request:
        :return:
        """
        frontend_data, user_model = self._meta_resolve(request)
        query_object = {
            '_type': 'document',
            '_label': 'DocGraph'
        }
        if re_for_frontend_id.match(frontend_data['_id']):
            query_object['_id'] = id_generator(1, 'node')[0]
            response = {frontend_data['_id']: query_object['_id']}
        else:
            query_object['_id'] = frontend_data['_id']
            response = {}
        history = ItemHistory(user_id=user_model.user_id, **query_object)
        history.record_update(
            content=frontend_data['Content'],
            name=frontend_data['Name'] + str(datetime.now()))
        history.save()
        return HttpResponse(status=200, content=json.dumps(response))

    def bulk_create(self, request):
        """
        data_example: {
            ["_id": "",
            "Content": {
                "Graph": "",
                "Conf": {}
            }]
        }
        :return:
        """
        collector = NeoSet()
        frontend_data, user_model = self._meta_resolve(request)
        user_id = user_model.user_id
        graph_model_list = [DocGraphModel(_id=data['_id'], user_id=user_id, collector=collector).base_create(data)
                            for data in frontend_data]
        DocGraphModel.bulk_save_create(graph_model_list)
        return HttpResponse(status=200)
