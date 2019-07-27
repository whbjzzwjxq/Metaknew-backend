from django.http import HttpResponse
import json
from record.logic_class import ErrorRecord
from tools.base_tools import class_table, NeoSet
from subgraph.logic_class import BaseNode
types = ['StrNode', 'InfNode', 'Media', 'Document']


source_list = {
    "record": ErrorRecord
}


def criteria_query(request):
    if request.method == 'GET':
        criteria = json.loads(request.body, encoding='utf-8')['criteria']
        limit = int(request.GET.get('limit', 100))
        props = {}
        for prop in criteria["props"]:
            name = prop["name"]
            query_type = prop["query_type"]
            min_range = prop["min_range"]
            max_range = prop["max_range"]

            if query_type == 'equal':
                props.update({name + '__exact': min_range})
            if query_type == 'not_equal':
                props.update({name + '__not': min_range})
            if query_type == 'range':
                props.update({name + '__gte': min_range})
                props.update({name + '__lte': max_range})
            if query_type == 'more':
                props.update({name + '__gte': min_range})
            if query_type == 'less':
                props.update({name + '__lte': max_range})
            criteria = {
                "limit": limit,
                "labels": criteria["labels"],
                "props": props,
            }
            result = source_list[criteria["source"]]().query_by_criteria(criteria)
            return HttpResponse(json.dumps(result, ensure_ascii='utf-8'))


def query_label_dict(request):
    p_label = request.GET.get('PrimaryLabel')
    nodes = NeoSet().Nmatcher.match()
    return HttpResponse()


def get_single_node(request):

    uuid = request.GET.get('uuid')
    node = BaseNode().query(uuid=uuid).handle_for_frontend()

    return HttpResponse(json.dumps(node))
