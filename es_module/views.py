from elasticsearch import Elasticsearch
from subgraph.logic_class import BaseNode
from es_module.logic_class import EsQuery
from tools.base_tools import merge_list
import json
from django.shortcuts import HttpResponse

es = Elasticsearch([{'host': '39.96.10.154', 'port': 7000}])
node_params = ['name_zh', 'name_en', ]


def es_ask_node(request):
    if request.method == 'GET':
        keyword = request.GET.get('keyword')
        auto = request.GET.get('auto')
        fuzzy = request.GET.get('fuzzy')
        language = request.GET.get('language')
        es_query = EsQuery(index="nodes")
        results = []
        if keyword:
            if auto:
                results.append(es_query.auto_name(keyword=keyword))
            if fuzzy:
                results.append(es_query.fuzzy_alias(keyword=keyword))
                results.append(es_query.fuzzy_keyword(keyword=keyword))
                results.append(es_query.fuzzy_name(keyword=keyword, language=language))
            uuid_list = merge_list(results)
            result = [BaseNode().query(uuid).handle_for_frontend() for uuid in uuid_list]
            print(result)
            return HttpResponse(json.dumps(result, ensure_ascii=False))
        else:
            return HttpResponse(json.dumps({}, ensure_ascii=False))
