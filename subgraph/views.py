from django.http import HttpResponse
from subgraph.logic_class import BaseNode, BaseLink
from document.logic_class import BaseDoc
from tools.base_tools import NeoSet, get_user_props, get_special_props
from tools.id_generator import id_generator
from py2neo import Relationship
import json
import datetime
from users.logic_class import BaseUser
from users.models import User
from django.db.models import ObjectDoesNotExist
from subgraph.models import NodeCtrl, NodeInfo
from record.logic_class import EWRecord, History
import numpy as np
from tools.redis_process import query_needed_prop, set_needed_prop, query_available_plabel


# NeoNode: 存在neo4j里的部分 node: 数据源 NewNode: 存在postgre的部分  已经测试过


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
    base_prop = [field.name for field in get_user_props(p_label="BaseNode")]
    for label in labels:
        props = query_needed_prop(label)
        if not props:
            props = [field.name for field in get_special_props(p_label=label)]
            if props:
                set_needed_prop(label, props)
        label_prop_dict.update({label: props})
    label_prop_dict.update({"BaseNode": []})
    result = {
        "baseProp": base_prop,
        "specialProp": label_prop_dict
    }
    return HttpResponse(json.dumps(result))


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
    data_list = request.POST.get("data")
    user_id = request.GET.get("user_id")
    plabel = request.POST.get("plabel")
    user_model = BaseUser(_id=user_id).query_user()
    if user_model:
        # 请求一定数量的id
        id_list = id_generator(number=len(data_list), method='node', content=plabel, jump=3)
        # 创建node object
        nodes = [BaseNode(user=user_model, _id=_id, collector=collector) for _id in id_list]
        # 注入数据
        nodes = [node.create(node=data) for node, data in zip(nodes, data_list)]
        # 去除掉生成错误的节点 可以看create的装饰器
        nodes = [node for node in nodes if node]
        # 保存
        output = np.array([node.output_table_create() for node in nodes])
        ctrl = list(output[:, 0])
        NodeCtrl.objects.bulk_create(ctrl, batch_size=batch_size)
        info = list(output[:, 1])
        NodeInfo.objects.bulk_create(info, batch_size=batch_size)
        warn = list(output[:, 2])
        EWRecord.bulk_save_warn_record(warn)
        history = list(output[:, 3])
        History.bulk_save_node_history(history)

        return HttpResponse(content='创建成功', status=200)
    else:
        return HttpResponse(content='用户不存在', status=400)


