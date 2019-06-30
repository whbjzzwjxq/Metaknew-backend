from py2neo import Graph, NodeMatcher, RelationshipMatcher
from py2neo.data import Node, Relationship
graph = Graph('bolt://39.96.10.154:7687', username='neo4j', password='12345678')


class NeoSet:
    def __init__(self):
        self.tx = graph.begin()
        self.Nmatcher = NodeMatcher(graph)
        self.Rmatcher = RelationshipMatcher(graph)


a = Node('test', uuid='9ccf92f6-1d71-11e9-8395-00163e2ebf00')
collector = NeoSet()
collector.tx.create(a)
a.__primarykey__ = "uuid"
a.__primaryvalue__ = '9ccf92f6-1d71-11e9-8395-00163e2ebf00'
a.add_label('Used')
collector.tx.push(a)
collector.tx.commit()
