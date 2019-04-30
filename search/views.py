from django.http import HttpResponse
from subgraph import views
import json
from subgraph.models import *
from document.models import Document
graph = Graph('bolt://39.96.10.154:7687', username='neo4j', password='12345678')
types = ['StrNode', 'InfNode', 'Media', 'Document']

class_table = {
    'Person': Person,
    'Project': Project,
    'ArchProject': ArchProject,
    'Document': Document,
}


def init(label):
    if label in class_table:
        return class_table[label]
    else:
        return Person


class NeoSet:
    def __init__(self):
        self.tx = graph.begin()
        self.Nmatcher = NodeMatcher(graph)
        self.Rmatcher = RelationshipMatcher(graph)


def get_single_node(request):
    if request.method == 'GET':
        keyword = request.GET.get('keyword')
        remote = search_by_name(keyword)
        if remote:
            uuid = remote['uuid']
            return_node = get_node(uuid)
            if return_node['info']['PrimaryLabel'] == 'Document':
                for item in return_node['info']['nodes']:
                    item.update(get_node(item['uuid']))
                    item.pop('uuid')
                for item in return_node['info']['relationships']:
                    item.update(search_rel_uuid(item['uuid']))
                    item.pop('uuid')
            return HttpResponse(json.dumps(return_node, ensure_ascii=False))
        else:
            return HttpResponse(404)


def get_node(uuid):
    node = search_by_uuid(uuid)
    if node:
        return_node = {'info': dict(node)}
        labels = []
        for label in node.labels:
            labels.append(label)
        return_node['info'].update({"labels": labels})
        for label in types:
            if label in return_node['info']['labels']:
                return_node['info']['type'] = label
                return_node['info']['labels'].remove(label)
        primary_label = return_node['info']['PrimaryLabel']
        doc = (list(init(primary_label).objects.filter(uuid=uuid)[:1]))
        if doc:
            doc = views.get_dict(doc[0])
            doc.pop('uuid')
            return_node['info'].update(doc)
        return return_node
    else:
        return {}


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


# uuid搜关系
def search_rel_uuid(uuid):
    result = NeoSet().Rmatcher.match(uuid=uuid).first()
    rel = {'info': {'source': result.start_node['uuid'], 'target': result.end_node['uuid']}}
    rel['info'].update(dict(result))
    return rel


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
        end_node = rel.end_node
        result.append(end_node)
    return result

