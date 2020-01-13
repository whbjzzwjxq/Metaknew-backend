import json

from django.shortcuts import HttpResponse

from es_module.logic_class import bulk_add_node_index, es, EsQuery
from subgraph.class_node import BaseNode
from subgraph.models import NodeCtrl

hits_format = {"took": 1,
               "timed_out": False,
               "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
               "hits": {"total": {"value": 0, "relation": "eq"},
                        "max_score": None,
                        "hits": []}}


def home_page_search(request):
    query_object = json.loads(request.body.decode())
    result = {
        'recent': [],
        'info': EsQuery().main(query_object),
        'text': []
    }
    return HttpResponse(json.dumps(result), status=200)


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
    def query_common_node(ctrl):
        _id = ctrl.ItemId
        base_node = BaseNode(_id=_id, user_id=user_id)
        base_node.ctrl = ctrl
        base_node.is_create = True
        try:
            base_node.query_base()
            return base_node
        except Exception:
            return None

    user_id = request.GET.get("user_id")
    ctrl_list = NodeCtrl.objects.filter(Is_Common=True, Is_Used=True, ItemType='node')
    base_nodes = [query_common_node(ctrl)for ctrl in ctrl_list]
    base_nodes = [node for node in base_nodes if node]
    batch_size = 256
    batch = int(len(base_nodes) / batch_size) + 1
    for i in range(0, batch):
        nodes = base_nodes[i * batch_size: (i+1) * batch_size - 1]
        bulk_add_node_index(nodes)
    return HttpResponse(status=200)
