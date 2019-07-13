from elasticsearch import Elasticsearch

es = Elasticsearch([{'host': '39.96.10.154', 'port': 7000}])


#  todo 加入评分
class EsQuery:

    def __init__(self, index):
        self.index = index
        self.result = []
        self.es = Elasticsearch([{'host': '39.96.10.154', 'port': 7000}])

    @staticmethod
    def get_uuid_from_result(es_result):
        if es_result:
            nodes = es_result['hits']['hits']
            result = [node['uuid'] for node in nodes if 'uuid' in node]
            return result
        else:
            return []

    def fuzzy_query(self, target):
        body = {
            "query": {
                "fuzzy": target
            }
        }
        return self.es.search(index="nodes", body=body)

    def fuzzy_name(self, keyword, language):
        target_name = {"name": {
            language: {
                "value": keyword,
                "fuzziness": 3,
                "prefix_length": 3,
                "max_expansions": 20
            }
        }
        }
        return self.get_uuid_from_result(self.fuzzy_query(target=target_name))

    def fuzzy_alias(self, keyword):
        target_alias = {"alias": {
            "value": keyword,
            "fuzziness": 3,
            "prefix_length": 3,
            "max_expansions": 20
        }
        }
        return self.get_uuid_from_result(self.fuzzy_query(target=target_alias))

    def fuzzy_keyword(self, keyword):
        target_keywords = {"keywords": {
            "value": keyword,
            "fuzziness": 3,
            "prefix_length": 3,
            "max_expansions": 20
        }
        }
        return self.get_uuid_from_result(self.fuzzy_query(target=target_keywords))

    def auto_complete(self, target):
        body = {
            "query": {
                "match": target
            }
        }
        return self.es.search(index="nodes", body=body)

    def auto_name(self, keyword):
        target = {"name": keyword}
        return self.get_uuid_from_result(self.auto_complete(target=target))


async def add_node_index(uuid, name, language, p_label, name_zh='', name_en='', description='', alias='', keywords='',
                         labels=''):
    body = {
        "alias": alias,
        "content": {language: description},
        "keywords": keywords,
        "labels": labels,
        "language": language,
        "name": {'auto': name, 'zh': name_zh, 'en': name_en},
        "p_label": p_label,
        "uuid": uuid
    }
    result = es.index(index='nodes', body=body, doc_type='_doc')
    if result['_shards']['successful'] == 1:
        return True
    else:
        # todo record
        return False
