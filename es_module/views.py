from elasticsearch import Elasticsearch
from es_module.logic_class import bulk_add_node_index, es
# from subgraph.logic_class import BaseNode, BaseMediaNode
from subgraph.models import BaseAuthority
import json
from django.shortcuts import HttpResponse

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
        # todo 综合查询 level: 2
        return_template = {
            "name": "test",
            "id": 0,
            "score": 10,
            "star": 20,
            "type": "node",
            "pLabel": "ArchProject",
            "topic": ["Architecture"],
            "labels": ["Recent", "Latin-America"],
            "totalTime": 60,
            "mainPic": BaseMediaNode(_id=2, user_id=2).query_as_main_pic()
        }
        templates = [return_template] * 5
        for index, temp in enumerate(templates):
            temp["id"] = index
        results = {"Nodes": [templates[0]],
                   "Documents": [templates[1], templates[2], templates[3]],
                   "Course": [templates[4]]}
        return HttpResponse(json.dumps(results))


def query_name_similarity(request):
    def make_pattern(name_lang):
        name = name_lang[0]
        lang = name_lang[1]
        query_index = json.dumps({"index": "nodes"}) + "\n"
        query_object = json.dumps({
            "id": "single_name_query",
            "params": {"field": "name.%s" % language_support(lang), "name": name}}) + "\n "
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


def reindex_nodes(request):
    def query_common_node(auth):
        _id = auth.SourceId
        base_node = BaseNode(_id=_id, user_id=user_id)
        base_node.authority = auth
        base_node.query_base()
        return base_node
    user_id = request.GET.get("user_id")
    authorities = BaseAuthority.objects.filter(Common=True, Used=True, SourceType='node')
    base_nodes = [query_common_node(auth)for auth in authorities]
    bulk_add_node_index(base_nodes)
    return HttpResponse(status=200)
