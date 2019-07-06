from document.logic_class import BaseDoc
from django.http import HttpResponse
from subgraph.logic_class import BaseNode, BaseLink

from tools import base_tools
import json


# NeoNode: 存在neo4j里的部分 node: 数据源 NewNode: 存在postgre的部分  已经测试过


def check_node_exist(user, node, collector):
    if 'uuid' in node:
        remote = BaseNode(collector=collector)
        if remote.query(uuid=node['uuid']):
            return remote
        else:
            return remote.create(node=node, user=user)
    else:
        return None


def check_link_exist(user, relationship, collector):
    if 'uuid' in relationship:
        remote = BaseLink(collector=collector)

        if remote.query(uuid=relationship['uuid']) is not None:
            return remote
        else:
            return remote.create(link=relationship, user=user)
    else:
        return None


def add_node(request):
    collector = base_tools.NeoSet()
    data = json.loads(request.body, encoding='utf-8')['data']
    user = request.GET.get('user_id')
    node = BaseNode(collector=collector)
    try:
        node.create(node=data, user=user)
        node.collector.tx.commit()
        return HttpResponse("add node success")
    except AssertionError:
        return HttpResponse("bad information")


def add_document(request):
    collector = base_tools.NeoSet()
    data = json.loads(request.body, encoding='utf-8')['data']
    user = request.GET.get('user_id')
    # 专题节点与关系
    nodes = data['nodes']
    relationships = data['relationships']
    info = data['info']
    # 专题信息
    doc = BaseDoc()

    node_index = {}
    Doc2Nodes = []

    for node in nodes:
        # 记录新建节点自动赋予的uuid
        old_id = node['info']['uuid']
        new_node = check_node_exist(user=user,
                                    node=node['info'],
                                    collector=collector).root
        node_index.update({old_id: new_node})

        # 记录专题内节点坐标
        conf = {'uuid': new_node['uuid'], 'conf': node['conf']}
        doc.Graph.IncludedNodes.append(conf)

        # 先记录下节点和专题的相关性
        if new_node['Name'] in info['keywords']:
            Doc2Nodes.append({'type': 'Doc2Node', 'source': new_node, 'count': 1})
            doc.Graph.MainNodes.append(new_node['uuid'])
    for relationship in relationships:
        # 从node_index里访问提交后的Node对象
        relationship["info"]['source'] = node_index[relationship["info"]['source']]
        relationship["info"]['target'] = node_index[relationship["info"]['target']]
        # 注意这里是传一个Node对象过去
        new_rel = check_link_exist(user=user,
                                   relationship=relationship['info'],
                                   collector=collector)
        conf = {'uuid': new_rel['uuid'], 'conf': relationship['conf']}
        doc.Graph.IncludedLinks.append(conf)

    # 新建专题
    new_document = {'Name': info['title'],
                    'PrimaryLabel': 'Document',
                    'Area': info['area'],
                    'type': "Document",
                    'Title': info['title'],
                    'Description': info['description'],
                    'MainPic': info['main_pic']
                    }
    new_document = doc.NeoNode.create(user=user, node=new_document)
    doc.NeoNode.collector = collector
    # 生成专题节点后再生成专题与普通节点的关系
    for Doc2Node in Doc2Nodes:
        Doc2Node.update({'target': new_document})
        result = collector.Rmatcher.match(nodes=(Doc2Node['source'], Doc2Node['target']),
                                          r_type='Doc2Node').first()
        if result:
            result['count'] += 1
            collector.tx.push(result)
        else:
            collector.tx.create(Doc2Node)

    # DocumentInformation部分
    doc.Info.uuid = new_document.uuid
    doc.Graph.uuid = new_document.uuid
    doc.save()
    collector.tx.commit()
    return HttpResponse('Create Document Success')
