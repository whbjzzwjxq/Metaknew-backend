from elasticsearch import Elasticsearch
from subgraph.logic_class import BaseNode
import json
es = Elasticsearch([{'host': '39.96.10.154', 'port': 7000}])
node_params = ['name_zh', 'name_en', ]


def add_node_index(uuid, name, language, p_label, name_zh='', name_en='', description='', alias='', keywords='',
                   labels=''):
    body = {
        "alias": alias,
        "content": {language: description},
        "keywords": keywords,
        "labels": labels,
        "language": language,
        "name": {'auto': name, 'zh': name_zh, 'en': name_en},
        "p_label": p_label,
        "uuid": uuid
    }
    result = es.index(index='nodes', body=body, doc_type='_doc')
    if result['_shards']['successful'] == 1:
        return True
    else:
        return False


def fuzzy_query(keyword, target):
    body = {
        "query": {
            "fuzzy": {
                "name": {
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
    }
    es_result = es.search(index="nodes", body=body)
    if es_result:
        nodes = es_result['hits']['hits']
        result = [node['uuid'] for node in nodes if 'uuid' in node]
        return result
    else:
        return []


def auto_complete(keyword):
    body = {
        "query": {
            "match": {
                "name": keyword
            }
        }
    }
    es_result = es.search(index="nodes", body=body)
    if es_result:
        nodes = es_result['hits']['hits']
        result = [node['uuid'] for node in nodes if 'uuid' in node]
        return result
    else:
        return []


def es_ask(request):
    if request.method == 'GET':
        keyword = request.GET.get('keyword')
        auto = request.GET.get('auto')
        fuzzy = request.GET.get('fuzzy')
        if keyword:
            return_docs, return_nodes = [], []
            if auto:
                results1 = auto_complete(keyword)
            if fuzzy:
                results2 = fuzzy_query(keyword, "auto")
            
            result = {'return_docs': return_docs, 'return_nodes': return_nodes}
            return HttpResponse(json.dumps(result, ensure_ascii=False))
        else:
            return HttpResponse(json.dumps({}, ensure_ascii=False))
