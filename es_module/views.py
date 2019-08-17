from elasticsearch import Elasticsearch
from subgraph.logic_class import BaseNode
from document.logic_class import BaseDoc
from es_module.logic_class import EsQuery
from tools.base_tools import merge_list
import json
from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt

es = Elasticsearch([{"host": "39.96.10.154", "port": 7000}])
hits_format = {"took": 1,
               "timed_out": False,
               "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
               "hits": {"total": {"value": 0, "relation": "eq"},
                        "max_score": None,
                        "hits": []}}


def es_ask_all(request):
    if request.method == "GET":
        keyword = request.GET.get("keyword")
        auto = request.GET.get("auto")
        fuzzy = request.GET.get("fuzzy")
        language = request.GET.get("language")
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


@csrf_exempt
def query_name_similarity(request):
    def make_pattern(name_lang):
        name = name_lang[0]
        lang = name_lang[1]
        query_index = json.dumps({"index": "nodes"}) + "\n"
        query_object = json.dumps({"id": "single_name_query",
                                   "params": {"field": language_support(lang), "name": name}}) + "\n"
        return query_index + query_object

    def handle_hit(result):
        hits = result["hits"]
        if hits["max_score"]:
            return hits["hits"][0]
        else:
            return None

    if request.method == "POST":
        name_lang_list = json.loads(request.body)["data"]
        query_str = [make_pattern(name_lang) for name_lang in name_lang_list]
        query_str = "".join(query_str)

        results = es.msearch_template(body=query_str,
                                      index="nodes",
                                      search_type="query_then_fetch")
        response = [handle_hit(result) for result in results["responses"]]
        return HttpResponse(json.dumps(response))


def language_support(lang):
    if lang == "en" or lang == "zh":
        field = lang
    else:
        field = "auto"
    return field
