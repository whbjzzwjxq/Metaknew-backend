from py2neo.data import Node
from py2neo import Graph, NodeMatcher, RelationshipMatcher
graph = Graph('bolt://39.96.10.154:7687', username='neo4j', password='12345678')

class NeoSet:
    def __init__(self):
        self.tx = graph.begin()
        self.Nmatcher = NodeMatcher(graph)
        self.Rmatcher = RelationshipMatcher(graph)
test = Node('test')
a = NeoSet()
a.tx.create(test)
a.tx.push(test)
a.tx.commit()
