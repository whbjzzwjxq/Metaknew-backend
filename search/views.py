from django.http import HttpResponse
from py2neo import Graph, NodeMatcher, RelationshipMatcher, walk
from document.models import Document
from subgraph import views
import json
graph = Graph('bolt://39.96.10.154:7687', username='neo4j', password='12345678')


class NeoSet:
    def __init__(self):
        self.tx = graph.begin()
        self.Nmatcher = NodeMatcher(graph)
        self.Rmatcher = RelationshipMatcher(graph)


def get_single_node(request):
    if request.method == 'GET':
        keyword = request.GET.get('keyword')
        node = search_by_name(keyword)
        if node:
            return_node = {'conf': {}, 'info': dict(node)}
            labels = []
            for label in node.labels:
                labels.append(label)
            return_node['info'].update({"labels": labels})
            if node['PrimaryLabel'] == 'Document':
                doc = list(Document.objects.filter(uuid=node['uuid'])[:1])[0]
                if doc:
                    key_in_store = doc.__dict__
                    for key in views.get_dict(doc):
                        return_node['info'].update({key: str(key_in_store[key])})
            return HttpResponse(json.dumps(return_node, ensure_ascii=False))
        else:
            return HttpResponse(404)
        # todo 尝试中英翻译 模糊搜索


# 查询关系是否存在
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


# uuid搜节点
def search_by_uuid(uuid):
    result = NeoSet().Nmatcher.match(uuid=uuid).first()
    return result


# 关键词搜索
def search_by_name(name):
    result = NeoSet().Nmatcher.match(Name=name).first()
    return result


# todo 多节点搜索
def search_relation(nodeA, nodeB):
    return 0


# 根据node搜索专题
def search_doc_by_node(node):
    rels = NeoSet().Rmatcher.match({node, None}, 'Doc2Node')
    result = []
    for rel in rels:
        end_node = walk(rel).end_node
        result.append(end_node)
    return result

