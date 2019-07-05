from search.views import NeoSet, search_rel_exist, search_by_uuid
from py2neo.data import Relationship
from django.http import HttpResponse
from subgraph.logic_class import BaseNode
from tools import base_tools
import json


# NeoNode: 存在neo4j里的部分 node: 数据源 NewNode: 存在postgre的部分  已经测试过


def create_relationship(relationship):
    # source 和 target 是Node对象
    source = relationship["source"]
    target = relationship["target"]
    relationship.update({'uuid': base_tools.get_uuid(source['Name'] + 'to' + target['Name'])})
    NeoRel = Relationship(source, relationship['type'], target)
    relationship.pop('type')
    relationship.pop('source')
    relationship.pop('target')
    NeoRel.update(relationship)
    collector = NeoSet()
    collector.tx.create(NeoRel)
    collector.tx.commit()
    return NeoRel


def check_node_exist(user, node, collector):
    if 'uuid' in node:
        remote = BaseNode(collector=collector, user=user)
        if remote.query(uuid=node['uuid']):
            remote.update_all(node=node)
            return remote
        else:
            return remote.create(node=node)
    else:
        return None


def handle_relationship(relationship):
    remote = search_rel_exist(relationship)
    if remote:
        if "uuid" in relationship:
            relationship.pop('uuid')
        remote.update(relationship)
        return remote
    else:
        return create_relationship(relationship)


def add_node(request):
    collector = base_tools.NeoSet()
    data = json.loads(request.body, encoding='utf-8')['data']
    user = json.loads(request.body, encoding='utf-8')['user']  # todo 用户注册登录
    node = BaseNode(collector=collector, user=user)
    try:
        node.create(node=data)
        node.collector.tx.commit()
        return HttpResponse("add node success")
    except AssertionError:
        return HttpResponse("bad information")


def add_document(request):
    data = json.loads(request.body, encoding='utf-8')['data']
    user = json.loads(request.body, encoding='utf-8')['user']
    # 专题节点与关系
    nodes = data['nodes']
    relationships = data['relationships']

    # 专题信息
    info = data['info']

    # 预定义容器
    doc_nodes = []
    doc_relationships = []
    Doc2Nodes = []
    node_index = {}

    for node in nodes:
        # 记录新建节点自动赋予的uuid
        old_id = node['info']['uuid']
        new_node = handle_node(node['info'])
        node_index.update({old_id: new_node})

        # 记录专题内节点坐标
        conf = {'uuid': new_node['uuid'], 'conf': node['conf']}
        doc_nodes.append(conf)

        # 先记录下节点和专题的相关性
        if new_node['Name'] in info['keywords']:
            Doc2Nodes.append({'type': 'Doc2Node', 'rate': 0.5, 'source': new_node})

    for relationship in relationships:
        # 从node_index里访问提交后的Node对象
        relationship["info"]['source'] = node_index[relationship["info"]['source']]
        relationship["info"]['target'] = node_index[relationship["info"]['target']]
        new_rel = handle_relationship(relationship['info'])
        conf = {'uuid': new_rel['uuid'], 'conf': relationship['conf']}
        doc_relationships.append(conf)
    # 新建专题
    new_document = {'Name': info['title'],
                    'PrimaryLabel': 'Document',
                    'Area': info['area'],
                    'type': "Document",
                    "nodes": doc_nodes,
                    "relationships": doc_relationships
                    }
    new_document = create_node(new_document)

    # 生成专题节点后再生成专题与普通节点的关系
    for Doc2Node in Doc2Nodes:
        Doc2Node.update({'target': new_document})
        handle_relationship(Doc2Node)

    # DocumentInformation部分
    data['info']['uuid'] = new_document['uuid']
    new_document_info = DocumentInformation()
    for key in get_dict(new_document_info):
        if key in data["info"]:
            setattr(new_document_info, key, data["info"][key])
    new_document_info.save()
    return HttpResponse('Create Document Success')
