import json
import typing

from django.http import HttpResponse
from django.shortcuts import render

from document.logic_class import BaseDocGraph
from es_module.logic_class import bulk_add_text_index
from subgraph.class_media import BaseMedia
from subgraph.class_node import BaseNode
from tools.base_tools import NeoSet, get_special_props, DateTimeEncoder, bulk_save_base_model
from tools.id_generator import id_generator
from tools.redis_process import query_needed_prop, set_needed_prop, query_available_plabel
from users.logic_class import BaseUser


def query_frontend_prop(request):
    labels = query_available_plabel()
    label_prop_dict = {}
    for label in labels:
        props = query_needed_prop(label)
        if not props:
            props = {field.name: query_field_type(field) for field in get_special_props(p_label=label)}
            if props:
                set_needed_prop(label, props)
        label_prop_dict.update({label: props})
    return HttpResponse(json.dumps(label_prop_dict))


def query_field_type(field) -> str:
    field_type = type(field).__name__
    return field_type


def create_graph(request):
    collector = NeoSet()
    doc_id = id_generator(number=1, method="node", jump=3)[0]
    user_id = request.GET.get("user_id")
    data = json.loads(request.body.decode())
    graph = data["graph"]
    user_model = BaseUser(_id=user_id).query_user()
    doc = BaseDocGraph(_id=doc_id, user_id=user_id, collector=collector)
    document = doc.create(graph)
    document.info_change_nodes.append(document.node)
    nodes = [node for node in document.info_change_nodes if node.type != 'media']
    medias = [media for media in document.info_change_nodes if media.type == 'media']
    links = document.info_change_links
    bulk_save_base_model(nodes, user_model, "node")
    bulk_save_base_model(medias, user_model, "media")
    bulk_save_base_model(links, user_model, "link")
    collector.tx.commit()
    document.graph.save()
    return HttpResponse(content="Create Document Success", status=200)


def bulk_create_node(request):
    batch_size = 256
    collector = NeoSet()
    data_list = json.loads(request.body)["data"]
    plabel = json.loads(request.body)["pLabel"]
    user_id = request.GET.get("user_id")
    user_model = BaseUser(_id=user_id).query_user()
    user_name = user_model.user.UserName
    for data in data_list:
        data["$_UserName"] = user_name
        data["PrimaryLabel"] = plabel
    if user_model:
        # 请求一定数量的id
        id_list = id_generator(number=len(data_list), method='node', jump=3)
        # 创建node object
        nodes = [BaseNode(_id=_id, collector=collector, user_id=user_id) for _id in id_list]
        # 注入数据
        nodes = [node.create(data=data) for node, data in zip(nodes, data_list)]
        # 去除掉生成错误的节点 可以看create的装饰器 发生错误返回None
        nodes: typing.List[BaseNode] = [node for node in nodes if node]
        bulk_save_base_model(nodes, user_model, "node")
        collector.tx.commit()

        return HttpResponse(content='创建成功 %s个节点 ' % len(nodes), status=200)
    else:
        return HttpResponse(content='用户不存在', status=400)


# remake 2019-10-17
def upload_media_by_user(request):
    """
        file_data_example = {
        'name': 'userFileCache/5fdf0145-e538-668a-6f9d-38f83b27904b.jpg',
        'Info': {
            'id': '$_1',
            'type': 'media',
            'PrimaryLabel': 'image',
            'Name': '1.jpg',
            'Text': {},
            'Labels': [],
            '$_IsCommon': True,
            '$_IsShared': True,
            '$_OpenSource': False
        }
    }
    :param request:
    :return: HttpResponse
    """
    collector = NeoSet()
    user_id = request.GET.get("user_id")
    user_model = BaseUser(_id=user_id)
    file_data = json.loads(request.body.decode())
    _id = id_generator(number=1, method='node', jump=2)[0]
    media = BaseMedia(_id=_id, user_id=user_id, collector=collector)
    media = media.create(data=file_data["Info"], remote_file=file_data["name"], is_user_made=True)
    new_location = 'userResource/' + str(media.id) + "." + media.ctrl.Format
    result = media.move_remote_file(new_location)
    if result.status == 200:
        media.ctrl.FileName = new_location
        user_model.bulk_create_source({media.id: "media"})
        media.save()
        if media.info.Text != {}:
            bulk_add_text_index([media])
        return HttpResponse(content=_id, status=200)
    else:
        return HttpResponse(status=500)


def update_media_by_user(request):
    """
    和upload_media_by_user类似
    :param request:
    :return:
    """
    collector = NeoSet()
    user_id = request.GET.get("user_id")
    user_model = BaseUser(_id=user_id)
    file_data = json.loads(request.body.decode())
    _id = file_data["Info"]["id"]
    media = BaseMedia(_id=_id, user_id=user_id, collector=collector).query_base()


def query_single_node(request):
    _id = request.GET.get("source_id")
    _type = request.GET.get("source_type")
    user_id = request.GET.get("user_id")
    if _type == 'node':
        result = BaseNode(_id=_id, user_id=user_id).handle_for_frontend()
        return HttpResponse(json.dumps(result, cls=DateTimeEncoder))
    else:
        return HttpResponse(404)
