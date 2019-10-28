import json
import re
import typing

from django.http import HttpResponse

from document.class_document import DocGraphClass
from es_module.logic_class import bulk_add_text_index
from subgraph.class_link import BaseLink, SystemMade
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
            props = {field.name: query_field_type(field) for field in get_special_props(_type='node', p_label=label)}
            if props:
                set_needed_prop(label, props)
        label_prop_dict.update({label: props})
    return HttpResponse(json.dumps(label_prop_dict))


def query_field_type(field) -> str:
    field_type = type(field).__name__
    return field_type


def bulk_create_node(request):
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


def update_single_node_by_user(request):
    """
    和upload_media_by_user类似
    :param request:
    :return:
    """
    collector = NeoSet()
    user_id = request.GET.get("user_id")
    file_data = json.loads(request.body.decode())
    info = file_data["Info"]
    _id = info["id"]
    re_for_old_id = re.match(r'\$_[0,9]*', str(_id))
    model = type_label_to_class(_type=info['type'], _label=info["PrimaryLabel"])
    if re_for_old_id:
        new_id = id_generator(number=1, method='node')[0]
        item = model(_id=new_id, user_id=user_id, collector=collector)
        item.create(data=info)
        result = {_id: new_id}
    else:
        item = model(_id=_id, user_id=user_id, collector=collector)
        item.info_update(data=info)
        result = {}
    if item:
        item.save()
        return HttpResponse(json.dumps(result), status=200)
    else:
        return HttpResponse(status=item.status, content=item.content)


def query_single_node(request):
    _id = request.GET.get("source_id")
    _type = request.GET.get("source_type")
    user_id = request.GET.get("user_id")
    if _type == 'node':
        result = BaseNode(_id=_id, user_id=user_id).handle_for_frontend()
        return HttpResponse(json.dumps(result, cls=DateTimeEncoder))
    else:
        return HttpResponse(404)


def query_multi_source(request):
    query_list = json.loads(request.body.decode())
    user_id = request.GET.get("user_id")
    # todo 有时间改成map
    result = []
    for query in query_list:
        _type = query[1]
        p_label = query[2]
        model = type_label_to_class(_type, p_label)
        output = model(_id=query[0], user_id=user_id)
        output.query_base()
        result.append(output.handle_for_frontend())

    return HttpResponse(json.dumps(result, cls=DateTimeEncoder))


def query_multi_media(request):
    """
    data: [id]
    :param request:
    :return:
    """
    data = json.loads(request.body.decode())
    user_id = request.GET.get('user_id')
    result = [BaseMedia(_id=_id, user_id=user_id).handle_for_frontend() for _id in data]
    return HttpResponse(json.dumps(result, cls=DateTimeEncoder), status=200)


def type_label_to_class(_type, _label: str):
    _type_to_class = {
        "node": {
            'default': BaseNode
        },
        "media": {
            "default": BaseMedia
        },
        "link": {
            "default": BaseLink,
            "Doc2Node": SystemMade,
            "SearchTogether": SystemMade,
            "MentionTogether": SystemMade,
            "VisitAfter": SystemMade,
        },
        "document": {
            "default": DocGraphClass,
            "DocPaper": DocGraphClass  # todo
        }
    }
    model_list = _type_to_class[_type]
    if _label in model_list:
        model = model_list[_label]
    else:
        model = model_list["default"]
    return model
