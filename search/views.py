from django.http import HttpResponse
from py2neo import Graph, NodeMatcher, RelationshipMatcher
import json
graph = Graph('bolt://39.96.10.154:7687', username='neo4j', password='12345678')


class NeoSet:
    def __init__(self):
        self.tx = graph.begin()
        self.Nmatcher = NodeMatcher(graph)
        self.Rmatcher = RelationshipMatcher(graph)


def get_search(request):
    if request.method == 'GET':
        keyword = request.GET.get('keyword')
        node = search_by_name(keyword)
        return_node = {'conf': {}, 'info': dict(node)}
        labels = []
        for label in node.labels:
            labels.append(label)
        return_node['info'].update({"labels": labels})
        return HttpResponse(json.dumps(return_node, ensure_ascii=False))
        # todo 尝试中英翻译 模糊搜索


def search_by_uuid(uuid):
    result = NeoSet().Nmatcher.match(uuid=uuid).first()
    return result


# 关键词搜索
def search_by_name(name):
    result = NeoSet().Nmatcher.match(Name=name).first()
    return result


def search_rel_exist(rel):
    result = NeoSet().Rmatcher.match({rel['source'], rel['target']}).first()
    if result:
        if type(result) == 'Doc2Node' or 'Doc2Doc':
            return result
        elif 'uuid' in rel:
            if result["uuid"] == rel["uuid"]:
                return result
            return None
        return None
    return None


# labels as args,key-value as kwargs
def search_by_dict(*args, **kwargs):
    result = NeoSet().Nmatcher.match(args, kwargs)
    return result


# todo 多节点搜索
def search_relation(nodeA, nodeB):
    return 0


# 根据node搜索专题
def search_doc_by_node(node):
    return 0

