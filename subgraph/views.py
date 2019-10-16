import json
import numpy as np
import typing

from django.shortcuts import render
from django.http import HttpResponse
from subgraph.logic_class import BaseNode, BaseLink, BaseMediaNode
from document.logic_class import BaseDoc
from subgraph.models import Text, NodeCtrl, NodeInfo
from users.logic_class import BaseUser
from users.models import NodeAuthority
from record.models import WarnRecord, NodeVersionRecord
from es_module.logic_class import add_node_index, add_text_index, bulk_add_node_index
from tools.base_tools import NeoSet, get_special_props, basePath, node_init, DateTimeEncoder
from tools.id_generator import id_generator
from tools.redis_process import query_needed_prop, set_needed_prop, query_available_plabel


# def check_node_exist(node, collector):
#     if "uuid" in node:
#         remote = BaseNode(collector=collector)
#         if remote.query(uuid=node["uuid"]):
#             return remote
#         else:
#             return remote.create(node=node)
#     else:
#         return None
#
#
# def check_link_exist(relationship, collector):
#     if "uuid" in relationship:
#         remote = BaseLink(collector=collector)
#
#         if remote.query(uuid=relationship["uuid"]):
#             return remote
#         else:
#             return remote.create(link=relationship)
#     else:
#         return None
#
#
# def add_node(request):
#     collector = NeoSet()
#     data = json.loads(request.body, encoding="utf-8")["data"]
#     user = request.GET.get("user_id")
#     node = BaseNode(collector=collector)
#     data.update({
#         "ImportMethod": "Web",
#         "CreateUser": user,
#         "type": "StrNode"
#     })
#     try:
#         node.create(node=data)
#         node.collector.tx.commit()
#         return HttpResponse("add node success")
#     except AssertionError:
#         return HttpResponse("bad information")
#
#
# def add_relationship(request):
#     collector = NeoSet()
#     data = json.loads(request.body, encoding="utf-8")["data"]
#     user = request.GET.get("user_id")
#     link = BaseLink(collector=collector)
#     data.update({
#         "ImportMethod": "Web",
#         "CreateUser": user,
#         "type": data["Label"],
#         "Is_Used": True
#     })
#     source = NeoSet().Nmatcher.match(uuid=data["source"])
#     target = NeoSet().Nmatcher.match(uuid=data["target"])
#     if source is not None and target is not None:
#         try:
#             data["source"] = source
#             data["target"] = target
#             link.create(link=data)
#             link.collector.tx.commit()
#             return HttpResponse("add link success")
#         except AssertionError:
#             return HttpResponse("bad information")
#
#
# def add_document(request):
#     collector = NeoSet()
#     data = json.loads(request.body, encoding="utf-8")["data"]
#     user = request.GET.get("user_id")
#     # 专题节点与关系
#     nodes = data["nodes"]
#     relationships = data["relationships"]
#     info = data["info"]
#     conf = data["conf"]
#     # 专题信息
#     doc = BaseDoc()
#
#     node_index = {}
#     main_node_links = []
#
#     for node in nodes:
#         # 记录新建节点自动赋予的uuid
#
#         old_id = str(node["info"]["uuid"])
#         if not uuid_matcher(old_id):
#             node["info"].update({
#                 "ImportMethod": "Web",
#                 "CreateUser": user,
#                 "type": "StrNode"
#             })
#         new_node = check_node_exist(node=node["info"],
#                                     collector=collector).root
#         node_index.update({old_id: new_node})
#
#         # 记录专题内节点坐标
#         conf = {"uuid": new_node["uuid"], "conf": node["conf"]}
#         doc.graph.IncludedNodes.append(conf)
#
#         # 记录下主要节点
#         if new_node["Name"] in info["Keywords"]:
#             main_node_links.append({"type": "doc_main_node", "source": new_node, "count": 1})
#             doc.graph.MainNodes.append(new_node["uuid"])
#
#     for relationship in relationships:
#         # 从node_index里访问提交后的Node对象
#         relationship["info"]["source"] = node_index[str(relationship["info"]["source"])]
#         relationship["info"]["target"] = node_index[str(relationship["info"]["target"])]
#         relationship["info"].update({
#             "ImportMethod": "Web",
#             "CreateUser": user,
#             "ImportTime": datetime.datetime.now()
#         })
#         # 注意这里是传一个Node对象过去
#         new_rel = check_link_exist(relationship=relationship["info"],
#                                    collector=collector)
#         if new_rel:
#             new_rel = new_rel.root
#         conf = {"uuid": new_rel["uuid"], "conf": relationship["conf"]}
#         doc.graph.IncludedLinks.append(conf)
#
#     # 新建专题
#     new_document = {"Name": info["title"],
#                     "PrimaryLabel": "Document",
#                     "Topic": info["Topic"],
#                     "type": "Document",
#                     "Title": info["title"],
#                     "Description": info["description"],
#                     "Labels": info["Labels"],
#                     "Keywords": info["keywords"],
#                     "Alias": []
#                     }
#     new_document = doc.NeoNode(collector=collector).create(node=new_document)
#
#     # 生成专题节点后再生成专题与普通节点的关系
#
#     for link in main_node_links:
#         link.update({"target": new_document.root})
#         result = collector.Rmatcher.match(nodes=(link["source"], link["target"]),
#                                           r_type="Doc2Node").first()
#
#         if result:
#             result["count"] += 1
#             collector.tx.push(result)
#         else:
#             result = Relationship(link["source"], "Doc2Node", link["source"])
#             collector.tx.create(result)
#
#     # DocumentInformation部分
#     doc.node.uuid = new_document.origin
#     doc.graph.uuid = new_document.origin
#     doc.node.CountCacheTime = datetime.datetime.now()
#     doc.node.CreateTime = datetime.datetime.now()
#     doc.save()
#     collector.tx.commit()
#     return HttpResponse("Create Document Success")


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


def create_document(request):
    collector = NeoSet()
    doc_id = id_generator(number=1,
                          method="node",
                          content="document",
                          jump=3)
    user = request.GET.get("user_id")
    data = json.dumps(request.body)
    doc = BaseDoc(_id=doc_id, user=user, collector=collector)
    if not doc:
        try:
            doc.create(data)
            doc.save()
            return HttpResponse(content="Create Document Success", status=200)
        except BaseException:
            return HttpResponse(content="TimeoutError Please Contact the Admin", status=400)
    else:
        return HttpResponse(content="Document Already Exist", status=401)


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
        id_list = id_generator(number=len(data_list), method='node', content=plabel, jump=3)
        # 创建node object
        nodes = [BaseNode(_id=_id, collector=collector, user_id=user_id) for _id in id_list]
        # 注入数据
        nodes = [node.create(data=data) for node, data in zip(nodes, data_list)]
        # 去除掉生成错误的节点 可以看create的装饰器 发生错误返回None
        nodes: typing.List[BaseNode] = [node for node in nodes if node]
        if nodes:
            nodes_id = {node.id: "Node" for node in nodes}
            user_model.bulk_create_source(nodes_id)
            # 保存
            output = np.array([node.output_table_create() for node in nodes])
            # 保存ctrl
            ctrl = list(output[:, 0])
            NodeCtrl.objects.bulk_create(ctrl)
            # 保存info
            info = list(output[:, 1])
            node_init(plabel).objects.bulk_create(info)
            # 保存warn
            warn = list(output[:, 2])
            WarnRecord.objects.bulk_create(warn)
            # 保存history
            history = list(output[:, 3])
            NodeVersionRecord.objects.bulk_create(history)
            # 保存authority
            authority = list(output[:, 4])
            NodeAuthority.objects.bulk_create(authority)
            # 保存neo4j节点
            collector.tx.commit()
            texts = []
            bulk_add_node_index(nodes)
            for node in nodes:
                if node.text:
                    texts.append(node.text)
                    add_text_index(node.text)
            Text.objects.bulk_create(texts)

        return HttpResponse(content='创建成功 %s个节点 ' % len(nodes), status=200)
    else:
        return HttpResponse(content='用户不存在', status=400)


# todo 图片缩放 level: 1
def upload_main_pic(request):
    collector = NeoSet()
    user_id = request.GET.get("user_id")
    user_model = BaseUser(_id=user_id)
    file = request.FILES["file"]
    file_format = str(file.name).split(".")[-1].lower()
    _id = id_generator(number=1, method='node', content='Media', jump=2)[0]
    data = {"Format": file_format,
            "Name": request.POST.get("name"),
            "Text": request.POST.get("description"),
            "$_IsCommon": True,
            "$_IsShared": True,
            "Payment": False,
            "Language": "auto",
            "Labels": [],
            "Translate": {}
            }
    # 写入文件
    with open(basePath + "/fileUploadCache/" + str(_id) + "." + file_format, "wb+") as target:
        target.write(file.read())

    media = BaseMediaNode(_id=_id, user_id=user_id, collector=collector).create(data)
    user_model.bulk_create_source({media.id: "Media"})
    media.save()

    return HttpResponse(json.dumps({"_id": _id, "format": media.media_type}), status=200)


def query_main_pic(request):
    user_id = request.GET.get("user_id")
    media_ids = json.loads(request.body)["_idList"]
    result = []
    for _id in media_ids:
        media = BaseMediaNode(_id=_id, user_id=user_id).query_all()
        if media:
            result.append({"name": media.media.FileName, "image": media.query_as_main_pic()})
        else:
            result.append(None)
    return HttpResponse(json.dumps(result), status=200)


def upload_media(request):
    print(request)
    collector = NeoSet()
    user_id = request.GET.get("user_id")
    user_model = BaseUser(_id=user_id)
    file = request.FILES["file"]
    file_format = str(file.name).split(".")[-1].lower()
    _id = id_generator(number=1, method='node', content='Media', jump=2)[0]
    data = {"Format": file_format,
            "Name": request.POST.get("name"),
            "Text": request.POST.get("description"),
            "$_IsCommon": True,
            "$_IsShared": True,
            "Payment": False,
            "Language": request.POST.get("Language"),
            "Labels": json.loads(request.POST.get("Labels")),
            "Translate": json.loads(request.POST.get("Translate"))
            }
    if request.POST.get("$_IsCommon") == "false":
        data["$_IsCommon"] = False
    if request.POST.get("$_IsShared") == "false":
        data["$_IsShared"] = False

    # 写入文件
    with open(basePath + "/fileUploadCache/" + str(_id) + "." + file_format, "wb+") as target:
        target.write(file.read())
    media = BaseMediaNode(_id=_id, user_id=user_id, collector=collector).create(data)
    user_model.bulk_create_source({media.id: "Media"})
    media.save()
    if media.text:
        media.text.save()
        add_text_index(text=media.text)
    return HttpResponse(json.dumps({"_id": _id, "format": media.media_type}), status=200)


def query_single_node(request):
    _id = request.GET.get("source_id")
    _type = request.GET.get("source_type")
    user_id = request.GET.get("user_id")
    if _type == 'node':
        result = BaseNode(_id=_id, user_id=user_id).handle_for_frontend()
        return HttpResponse(json.dumps(result, cls=DateTimeEncoder))
    else:
        return HttpResponse(404)

