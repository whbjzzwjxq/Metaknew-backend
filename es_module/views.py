from elasticsearch import Elasticsearch
from es_module.logic_class import EsQuery
import json
from django.shortcuts import HttpResponse

es = Elasticsearch([{"host": "39.96.10.154", "port": 7000}])
hits_format = {"took": 1,
               "timed_out": False,
               "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
               "hits": {"total": {"value": 0, "relation": "eq"},
                        "max_score": None,
                        "hits": []}}


def query_for_home_page(request):
    """
    首页搜索框的请求
    :param request:
    :return:
    """
    if request.method == "POST":
        request_params = json.loads(request.body)



def query_name_similarity(request):
    def make_pattern(name_lang):
        name = name_lang[0]
        lang = name_lang[1]
        query_index = json.dumps({"index": "nodes"}) + "\n"
        query_object = json.dumps({
            "id": "single_name_query",
            "params": {"field": "doc.name.%s.keyword" % language_support(lang), "name": name}}) + "\n "
        return query_index + query_object

    def handle_hit(result):
        hits = result["hits"]
        if hits["max_score"]:
            return hits["hits"][0]["_source"]["doc"]
        else:
            return None

    if request.method == "POST":
        name_lang_list = json.loads(request.body)
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
