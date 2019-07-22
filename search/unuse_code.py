# from elasticsearch import Elasticsearch
# from django.http import HttpResponse
# import json
# from search.views import search_by_uuid, search_doc_by_node, get_node
# from document.logic_class import BaseDoc
# es = Elasticsearch([{'host': '39.96.10.154', 'port': 7000}])
#
#
# def fuzzy_ask(keyword, target, index):
#     body = {
#         "query": {
#             "fuzzy": {
#                 target: {
#                     "value": keyword,
#                     "boost": 1.0,
#                     "fuzziness": 3,
#                     "prefix_length": 3,
#                     "max_expansions": 20
#                 }
#             }
#         }
#     }
#     return es.search(index=index, body=body)
#
#
# def complete_ask(keyword, index):
#     body = {
#         "query": {
#             "match": {
#                 "name": keyword
#             }
#         }
#     }
#     return es.search(index=index, body=body)
#
#
# def es_ask(request):
#     if request.method == 'GET':
#         keyword = request.GET.get('keyword')
#         auto = request.GET.get('auto')
#         fuzzy = request.GET.get('fuzzy')
#         if keyword:
#             return_docs, return_nodes = [], []
#             if auto:
#                 docs, nodes = auto_complete_node_doc(keyword)
#                 return_docs += docs
#                 return_nodes += nodes
#             if fuzzy:
#                 docs, nodes = fuzzy_ask_node_doc(keyword)
#                 for doc in docs:
#                     for exist_doc in return_docs:
#                         if doc["uuid"] != exist_doc["uuid"]:
#                             return_docs.append(doc)
#                 for node in docs:
#                     for exist_node in return_docs:
#                         if node["uuid"] != exist_node["uuid"]:
#                             return_docs.append(node)
#             result = {'return_docs': return_docs, 'return_nodes': return_nodes}
#             return HttpResponse(json.dumps(result, ensure_ascii=False))
#         else:
#             return HttpResponse(json.dumps({}, ensure_ascii=False))
#
#
# def fuzzy_ask_node_doc(keyword):
#     if keyword:
#         results_docs = fuzzy_ask(keyword, 'name.keyword', 'nodes-document')
#         results_nodes = fuzzy_ask(keyword, 'name.keyword', 'nodes-strnode')
#         # 处理
#         return_docs = get_result_docs(results_docs)
#         return_nodes = get_result_nodes(results_nodes)
#         return return_docs, return_nodes
#
#
# def auto_complete_node_doc(keyword):
#     if keyword:
#         results_docs = complete_ask(keyword, 'nodes-document')
#         results_nodes = complete_ask(keyword, 'nodes-strnode')
#         # 处理
#         return_docs = get_result_docs(results_docs)
#         return_nodes = get_result_nodes(results_nodes)
#         return return_docs, return_nodes
#
#
# # 搜索节点
# def get_result_nodes(nodes):
#     return_nodes = []
#     if nodes:
#         nodes = nodes['hits']['hits']
#         for node in nodes:
#             if '_id' in node:
#                 return_node = search_by_uuid(node['_id'])
#                 if return_node:
#                     return_node['score'] = node['_score']
#
#                     return_nodes.append(return_node)
#     return_nodes = list(map(get_node, return_nodes))
#     return return_nodes
#
#
# # 搜索专题
# def get_result_docs(docs):
#     return_docs = []
#     if docs:
#         docs = docs['hits']['hits']
#         for doc in docs:
#             if '_id' in doc:
#                 return_docs.append(doc['_id'])
#     return_docs = [BaseDoc().query_abbr_doc(uuid=uuid) for uuid in return_docs]
#     return return_docs
#
#
# # 搜索与节点相关的专题
# def get_rel_doc_by_nodes(nodes):
#     return_docs = []
#     for node in nodes:
#         for doc in search_doc_by_node(node):
#             return_docs.append(doc)
#     return_docs = [BaseDoc().query_abbr_doc(uuid=uuid) for uuid in return_docs]
#     return return_docs
#
#
# def get_node_uuid(request):
#     if request.method == 'GET':
#         uuid = request.GET.get('uuid')
#         remote = search_by_uuid(uuid)
#         if remote:
#             return_node = get_node(remote)
#             if return_node['info']['PrimaryLabel'] == 'Document':
#                 for item in return_node['info']['nodes']:
#                     item.update(get_node(search_by_uuid(item['uuid'])))
#                     item.pop('uuid')
#                 for item in return_node['info']['relationships']:
#                     item.update(search_rel_uuid(item['uuid']))
#                     item.pop('uuid')
#             return HttpResponse(json.dumps(return_node, ensure_ascii=False))
#         else:
#             return HttpResponse(404)
#
#
# def search_doc_by_nodes(request):
#     if request.method == 'GET':
#         uuids = request.GET.get('uuids')
#         results = []
#         for uuid in uuids:
#             node = search_by_uuid(uuid)
#             docs = search_doc_by_node(node)
#             docs = [BaseDoc().query_abbr_doc(uuid=uuid) for uuid in docs]
#             results.append({'uuid': uuid, 'docs': docs})
#         return HttpResponse(json.dumps(results, ensure_ascii=False))
#     else:
#         return HttpResponse(404)
#
#
# # 从neo4j和postgresql取数据
# def get_node(node):
#     if node:
#         return_node = {'info': dict(node)}
#         labels = []
#         for label in node.labels:
#             labels.append(label)
#         return_node['info'].update({"labels": labels})
#         for label in types:
#             if label in return_node['info']['labels']:
#                 return_node['info']['type'] = label
#                 return_node['info']['labels'].remove(label)
#         if 'PrimaryLabel' in return_node['info']:
#             primary_label = return_node['info']['PrimaryLabel']
#         else:
#             primary_label = 'None'
#         doc = (list(base_tools.init(primary_label).objects.filter(uuid=return_node['info']['uuid'])[:1]))
#         if doc:
#             doc = views.get_dict(doc[0])
#             doc.pop('uuid')
#             return_node['info'].update(doc)
#         return return_node
#     else:
#         return {}
#
#
# def search_by_condition(request):
#     """
#     {
#     "data":{
#         "lable":"Person",  # model名称
#         "properties":[{	"name":"Hot",  # 表中的字段名称
#             "query_type":"equal",  # 评判标准（equal，not_equal，range，more，less）
#             "min_range":"100",  # 查询范围下限
#             "max_range":"160"}]  # 查询范围上限
#     }
# }
#     :param request:
#     :return:
#     """
#     param = json.loads(request.body)['data']
#     label = param['label']
#     properties = param['properties']
#     propertys = {}
#     for p in properties:
#         name = p['name']
#         query_type = p["query_type"]
#         min_range = p["min_range"]
#         max_range = p["max_range"]
#         if query_type == 'equal':
#             propertys.update({name + '__exact': min_range})
#         if query_type == 'not_equal':
#             propertys.update({name + '__not': min_range})
#         if query_type == 'range':
#             propertys.update({name + '__gte': min_range})
#             propertys.update({name + '__lte': max_range})
#         if query_type == 'more':
#             propertys.update({name + '__gte': min_range})
#         if query_type == 'less':
#             propertys.update({name + '__lte': max_range})
#         results = select_by_condition(label, **propertys)
#         # results = list(result.__iter__())
#         res = []
#         for result in results:
#             res.append(dict(model_to_dict(result).items()))
#
#         # return HttpResponse(json.dumps(result, ensure_ascii=False))
# 查询关系是否存在
# def search_rel_exist(rel):
#     result = NeoSet().Rmatcher.match({rel['source'], rel['target']}).first()
#     if result:
#         if type(result) == 'Doc2Node' or 'Doc2Doc':
#             return result
#         elif 'uuid' in rel:
#             if result["uuid"] == rel["uuid"]:
#                 return result
#             return None
#         return None
#     return None
#
#
# # labels as args,key-value as kwargs
# def search_by_dict(*args, **kwargs):
#     result = NeoSet().Nmatcher.match(*args, **kwargs)
#     return result
#
#
# def select_by_condition(label, **propertys):
#     tableModel = base_tools.init(label)
#     result = tableModel.objects.filter(**propertys)
#     return result
#
#
# # uuid搜节点
# def search_by_uuid(uuid):
#     result = NeoSet().Nmatcher.match(uuid=uuid).first()
#     return result
#
#
# # uuid搜关系
# def search_rel_uuid(uuid):
#     result = NeoSet().Rmatcher.match(uuid=uuid).first()
#     rel = {'info': {'source': result.start_node['uuid'], 'target': result.end_node['uuid']}}
#     rel['info'].update(dict(result))
#     return rel
#
#
# # 关键词搜索
# def search_by_name(name):
#     result = NeoSet().Nmatcher.match(Name=name).first()
#     return result
#
#
#
# def search_relation(nodeA, nodeB):
#     return 0
#
#
# # 根据node搜索专题
# def search_doc_by_node(node):
#     rels = NeoSet().Rmatcher.match({node, None}, ['Doc2Node', 'Doc2Doc'])
#     result = []
#     for rel in rels:
#         end_node = rel.end_node
#         result.append(end_node['uuid'])
#     return result
