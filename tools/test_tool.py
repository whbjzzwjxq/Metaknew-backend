from django.shortcuts import HttpResponse
from subgraph.models import Node
from tools.base_tools import get_props_for_user_ctrl

def test_tool(request):

    node = Node()
    node.PrimaryLabel = 'Person'
    key_list = get_props_for_user_ctrl('Node')
    for key in key_list:
        a = getattr(node, key)
        print(key, a)
