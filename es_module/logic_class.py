from elasticsearch import Elasticsearch
from record.logic_class import ErrorRecord

import json

es = Elasticsearch([{'host': '39.96.10.154', 'port': 7000}])


#  todo 加入评分 level: 3
class EsQuery:

    def __init__(self, index):
        self.index = index
        self.result = []
        self.es = Elasticsearch([{'host': '39.96.10.154', 'port': 7000}])

    @staticmethod
    def get_uuid_from_result(es_result):
        if es_result:
            nodes = es_result['hits']['hits']
            result = [node['_source']['uuid'] for node in nodes if 'uuid' in node['_source']]
            return result
        else:
            return []

    def fuzzy_query(self, target, index):
        body = {
            "query": {
                "fuzzy": target
            }
        }
        return self.es.search(index=index, body=body)

    def fuzzy_name_nodes(self, keyword, language):
        target_name = {
            "name.%s" % language: {
                "value": keyword,
                "fuzziness": 3,
                "prefix_length": 3,
                "max_expansions": 20}
        }

        return self.get_uuid_from_result(self.fuzzy_query(target=target_name, index="nodes"))

    def fuzzy_alias_nodes(self, keyword):
        target_alias = {"alias": {
            "value": keyword,
            "fuzziness": 3,
            "prefix_length": 3,
            "max_expansions": 20
        }
        }
        return self.get_uuid_from_result(self.fuzzy_query(target=target_alias, index="nodes"))

    def fuzzy_keyword_documents(self, keywords):
        target_keywords = {"keywords": {
            "value": keywords,
            "fuzziness": 3,
            "prefix_length": 3,
            "max_expansions": 20
        }
        }
        return self.get_uuid_from_result(self.fuzzy_query(target=target_keywords, index="documents"))

    def auto_complete(self, target, index):
        body = {
            "query": {
                "match": target
            }
        }
        return self.es.search(index=index, body=body)

    def auto_name_nodes(self, keyword, language):
        target = {"name.%s" % language: keyword}
        return self.get_uuid_from_result(self.auto_complete(target=target, index="nodes"))

    def auto_title_documents(self, keywords, language):
        target = {"name.%s" % language: keywords}
        return self.get_uuid_from_result(self.auto_complete(target=target, index="documents"))


# # todo 消息队列处理 level :1
# async def add_node_index(node: BaseNode):
#     assert node.already
#     root = node.root
#     info = node.info
#     target = "content.%s" % root["Language"]
#     body = {
#         "alias": info["Alias"],
#         target: info["Description"],
#         "labels": list(root.labels),
#         "language": root["Language"],
#         "name": {'auto': root["name"],
#                  'zh': root["name_zh"],
#                  'en': root["name_en"]},
#         "p_label": root["PrimaryLabel"],
#         "uuid": root["uuid"]
#     }
#     result = es.index(index='nodes', body=body, doc_type='_doc')
#     if result['_shards']['successful'] == 1:
#         return True
#     else:
#         a = AddRecord()
#         content = {'result': result,
#                    'status': 'Failed',
#                    'type': 'es_upload'}
#         a.add_record(False, True, uuid, p_label, json.dumps(content))
#         return False
