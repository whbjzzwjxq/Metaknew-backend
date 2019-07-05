from django.http import HttpResponse
from subgraph import views
import json
from document import views
from py2neo import Graph, NodeMatcher, RelationshipMatcher
from django.forms.models import model_to_dict
from tools import base_tools

graph = Graph('bolt://39.96.10.154:7687', username='neo4j', password='12345678')
types = ['StrNode', 'InfNode', 'Media', 'Document']


class NeoSet:
    def __init__(self):
        self.tx = graph.begin()
        self.Nmatcher = NodeMatcher(graph)
        self.Rmatcher = RelationshipMatcher(graph)


def get_node_uuid(request):
    if request.method == 'GET':
        uuid = request.GET.get('uuid')
        remote = search_by_uuid(uuid)
        if remote:
            return_node = get_node(remote)
            if return_node['info']['PrimaryLabel'] == 'Document':
                for item in return_node['info']['nodes']:
                    item.update(get_node(search_by_uuid(item['uuid'])))
                    item.pop('uuid')
                for item in return_node['info']['relationships']:
                    item.update(search_rel_uuid(item['uuid']))
                    item.pop('uuid')
            return HttpResponse(json.dumps(return_node, ensure_ascii=False))
        else:
            return HttpResponse(404)


def search_doc_by_nodes(request):
    if request.method == 'GET':
        uuids = request.GET.get('uuids')
        results = []
        for uuid in uuids:
            node = search_by_uuid(uuid)
            docs = search_doc_by_node(node)
            docs = list(map(views.get_cache_doc, docs))
            results.append({'uuid': uuid, 'docs': docs})
        return HttpResponse(json.dumps(results, ensure_ascii=False))
    else:
        return HttpResponse(404)


# 从neo4j和postgresql取数据
def get_node(node):
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
        if 'PrimaryLabel' in return_node['info']:
            primary_label = return_node['info']['PrimaryLabel']
        else:
            primary_label = 'None'
        doc = (list(base_tools.init(primary_label).objects.filter(uuid=return_node['info']['uuid'])[:1]))
        if doc:
            doc = views.get_dict(doc[0])
            doc.pop('uuid')
            return_node['info'].update(doc)
        return return_node
    else:
        return {}


def criteria_query(request):
    if request.method == 'GET':
        criteria = json.loads(request.body, encoding='utf-8')['criteria']
        limit = int(request.GET.get('limit', 100))
        args = criteria["labels"]
        kwargs = criteria["propertys"]
        propertys = {}
        for prop in kwargs:
            name = prop["name"]
            query_type = prop["query_type"]
            min_range = prop["min_range"]
            max_range = prop["max_range"]
            # todo 这里是不是可能有数据库注入
            if query_type == 'equal':
                propertys.update({name + '__exact': min_range})
            if query_type == 'not_equal':
                propertys.update({name + '__not': min_range})
            if query_type == 'range':
                propertys.update({name + '__gte': min_range})
                propertys.update({name + '__lte': max_range})
            if query_type == 'more':
                propertys.update({name + '__gte': min_range})
            if query_type == 'less':
                propertys.update({name + '__lte': max_range})
            result = search_by_dict(*args, **propertys).limit(limit)
            results = list(map(get_node, result.__iter__()))
            return HttpResponse(json.dumps(results, ensure_ascii=False))


def search_by_condition(request):
    """
    {
    "data":{
        "lable":"Person",  # model名称
        "properties":[{	"name":"Hot",  # 表中的字段名称
            "query_type":"equal",  # 评判标准（equal，not_equal，range，more，less）
            "min_range":"100",  # 查询范围下限
            "max_range":"160"}]  # 查询范围上限
    }
}
    :param request:
    :return:
    """
    param = json.loads(request.body)['data']
    label = param['label']
    properties = param['properties']
    propertys = {}
    for p in properties:
        name = p['name']
        query_type = p["query_type"]
        min_range = p["min_range"]
        max_range = p["max_range"]
        if query_type == 'equal':
            propertys.update({name + '__exact': min_range})
        if query_type == 'not_equal':
            propertys.update({name + '__not': min_range})
        if query_type == 'range':
            propertys.update({name + '__gte': min_range})
            propertys.update({name + '__lte': max_range})
        if query_type == 'more':
            propertys.update({name + '__gte': min_range})
        if query_type == 'less':
            propertys.update({name + '__lte': max_range})
        results = select_by_condition(label, **propertys)
        # results = list(result.__iter__())
        res = []
        for result in results:
            res.append(dict(model_to_dict(result).items()))
        print(res)
        # return HttpResponse(json.dumps(result, ensure_ascii=False))


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
    result = NeoSet().Nmatcher.match(*args, **kwargs)
    return result


def select_by_condition(label, **propertys):
    tableModel = base_tools.init(label)
    result = tableModel.objects.filter(**propertys)
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
    rels = NeoSet().Rmatcher.match({node, None}, ['Doc2Node', 'Doc2Doc'])
    result = []
    for rel in rels:
        end_node = rel.end_node
        result.append(end_node['uuid'])
    return result
