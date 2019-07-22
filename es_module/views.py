from elasticsearch import Elasticsearch
from subgraph.logic_class import BaseNode
from document.logic_class import BaseDoc
from es_module.logic_class import EsQuery
from tools.base_tools import merge_list
import json
from django.shortcuts import HttpResponse

es = Elasticsearch([{'host': '39.96.10.154', 'port': 7000}])


def es_ask_all(request):
    if request.method == 'GET':
        keyword = request.GET.get('keyword')
        auto = request.GET.get('auto')
        fuzzy = request.GET.get('fuzzy')
        language = request.GET.get('language')
        es_query = EsQuery(index="nodes")
        node_results = []
        doc_results = []
        if keyword:
            if auto:
                node_results.append(es_query.auto_name_nodes(keyword=keyword, language=language))
                doc_results.append(es_query.auto_title_documents(keywords=keyword, language=language))
            if fuzzy:
                node_results.append(es_query.fuzzy_alias_nodes(keyword=keyword))
                node_results.append(es_query.fuzzy_name_nodes(keyword=keyword, language=language))
                doc_results.append(es_query.fuzzy_keyword_documents(keywords=keyword))
            node_list = merge_list(node_results)
            doc_list = merge_list(doc_results)
            node_results = [BaseNode().query(uuid).handle_for_frontend() for uuid in node_list]
            doc_results = [BaseDoc().query(uuid).handle_for_frontend() for uuid in doc_list]
            result = {"nodes": node_results, "docs": doc_results}
            return HttpResponse(json.dumps(result, ensure_ascii=False))
        else:
            result = {"nodes": {}, "docs": {}}
            return HttpResponse(json.dumps(result, ensure_ascii=False))
