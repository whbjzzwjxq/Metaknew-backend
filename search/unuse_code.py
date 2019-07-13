from elasticsearch import Elasticsearch
from django.http import HttpResponse
import json
from search.views import search_by_uuid, search_doc_by_node, get_node
from document.logic_class import BaseDoc
es = Elasticsearch([{'host': '39.96.10.154', 'port': 7000}])


def fuzzy_ask(keyword, target, index):
    body = {
        "query": {
            "fuzzy": {
                target: {
                    "value": keyword,
                    "boost": 1.0,
                    "fuzziness": 3,
                    "prefix_length": 3,
                    "max_expansions": 20
                }
            }
        }
    }
    return es.search(index=index, body=body)


def complete_ask(keyword, index):
    body = {
        "query": {
            "match": {
                "name": keyword
            }
        }
    }
    return es.search(index=index, body=body)


def es_ask(request):
    if request.method == 'GET':
        keyword = request.GET.get('keyword')
        auto = request.GET.get('auto')
        fuzzy = request.GET.get('fuzzy')
        if keyword:
            return_docs, return_nodes = [], []
            if auto:
                docs, nodes = auto_complete_node_doc(keyword)
                return_docs += docs
                return_nodes += nodes
            if fuzzy:
                docs, nodes = fuzzy_ask_node_doc(keyword)
                for doc in docs:
                    for exist_doc in return_docs:
                        if doc["uuid"] != exist_doc["uuid"]:
                            return_docs.append(doc)
                for node in docs:
                    for exist_node in return_docs:
                        if node["uuid"] != exist_node["uuid"]:
                            return_docs.append(node)
            result = {'return_docs': return_docs, 'return_nodes': return_nodes}
            return HttpResponse(json.dumps(result, ensure_ascii=False))
        else:
            return HttpResponse(json.dumps({}, ensure_ascii=False))


def fuzzy_ask_node_doc(keyword):
    if keyword:
        results_docs = fuzzy_ask(keyword, 'name.keyword', 'nodes-document')
        results_nodes = fuzzy_ask(keyword, 'name.keyword', 'nodes-strnode')
        # 处理
        return_docs = get_result_docs(results_docs)
        return_nodes = get_result_nodes(results_nodes)
        return return_docs, return_nodes


def auto_complete_node_doc(keyword):
    if keyword:
        results_docs = complete_ask(keyword, 'nodes-document')
        results_nodes = complete_ask(keyword, 'nodes-strnode')
        # 处理
        return_docs = get_result_docs(results_docs)
        return_nodes = get_result_nodes(results_nodes)
        return return_docs, return_nodes


# 搜索节点
def get_result_nodes(nodes):
    return_nodes = []
    if nodes:
        nodes = nodes['hits']['hits']
        for node in nodes:
            if '_id' in node:
                return_node = search_by_uuid(node['_id'])
                if return_node:
                    return_node['score'] = node['_score']
            # todo 这里没有排序 以后要改一下
                    return_nodes.append(return_node)
    return_nodes = list(map(get_node, return_nodes))
    return return_nodes


# 搜索专题
def get_result_docs(docs):
    return_docs = []
    if docs:
        docs = docs['hits']['hits']
        for doc in docs:
            if '_id' in doc:
                return_docs.append(doc['_id'])
    return_docs = [BaseDoc().query_abbr_doc(uuid=uuid) for uuid in return_docs]
    return return_docs


# 搜索与节点相关的专题
def get_rel_doc_by_nodes(nodes):
    return_docs = []
    for node in nodes:
        for doc in search_doc_by_node(node):
            return_docs.append(doc)
    return_docs = [BaseDoc().query_abbr_doc(uuid=uuid) for uuid in return_docs]
    return return_docs