# from django.shortcuts import render
# import json
#
# from record.logic_class import BaseHistory
# from subgraph.logic_class import BaseNode
# from django.http import HttpResponse
# # Create your views here.
#
# def add_history(request):
#     data = json.loads(request.body)['data']
#     user_id = request.GET.get('user_id')
#     url = data['url']
#     # nodes = getNodes(url)  # 此处为解析excel并返回节点数组的函数
#     uuid_list = []
#     for node in nodes:
#         uuid_list.append(node.uuid)
#         BaseNode.create(user_id,node)
#     data['user_id'] = user_id
#     data['Nodes'] = uuid_list
#     record = BaseHistory.create(data)
#     return HttpResponse(json.dumps(record), content_type="application/json")

