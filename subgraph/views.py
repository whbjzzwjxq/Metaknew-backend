from django.shortcuts import render
import os
from subgraph.models import BaseNode
from search.views import NeoSet
from py2neo.data import Node, Relationship
# Create your views here.
Neo4jKeys = ['type', 'Name', 'Name_zh', 'Name_en', 'PrimaryLabel', 'Labels']
# 这是已经处理好的数据，这里只存储
def create_node(node):
    newnode = Node(node.type, Name=node.Name, Name_zh=node.Name_zh, Name_en=node.Name_en)
    newnode.add_label(node.PrimaryLabel)
    newnode.add_label('Common')
    newnode.add_label('Used')
    newnode.update(node.Labels)
    for key in Neo4jKeys:
        if key in node:
            node.pop(key)
    NeoSet.tx.push(newnode)
    NeoSet.tx.commit()
    newnode = NeoSet.tx.pull(newnode)

