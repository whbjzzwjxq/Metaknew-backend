from elasticsearch import Elasticsearch
from django.http import HttpResponse
import json
from search.views import search_by_uuid, search_doc_by_node
from document import views
# 注意es必须配置在服务器上 考虑另起一个django项目
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])


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


def fuzzy_ask_node(request):
    if request.method == 'GET':
        keyword = request.GET.get('keyword')
        results = fuzzy_ask(keyword, 'name.keyword', 'nodes-strnode')
        results_doc = fuzzy_ask(keyword, 'name.keyword', 'nodes-document')
        uuids = []
        # 通过符合的节点搜索专题
        if results:
            results = results['hits']['hits']
            for result in results:
                for node in search_doc_by_node(search_by_uuid(result['_id'])):
                    uuids.append(node['uuid'])
                # todo 调整一下索引 这里两次搜索太蠢了
        # 直接搜索符合的专题
        if results_doc:
            results_doc = results_doc['hits']['hits']
            #todo 这里没有排序 以后要改一下
            for x in results_doc:
                uuids.append(x['_id'])
        result = views.get_cache_doc(uuids)
        return HttpResponse(json.dumps(result, ensure_ascii=False))


def auto_complete(request):
    if request.method == 'GET':
        keyword = request.GET.get('keyword')
        results_doc = complete_ask(keyword, 'nodes-document')
        uuids = []
        if results_doc:
            results_doc = results_doc['hits']['hits']
            for x in results_doc:
                uuids.append(x['_id'])
        result = views.get_cache_doc(uuids)
        return HttpResponse(json.dumps(result, ensure_ascii=False))
