from elasticsearch import Elasticsearch, helpers
es = Elasticsearch([{"host": "39.96.10.154", "port": 7000}])


#  todo 加入评分 level: 3
class EsQuery:

    def __init__(self, index):
        self.index = index
        self.result = []
        self.es = Elasticsearch([{"host": "39.96.10.154", "port": 7000}])

    @staticmethod
    def get_uuid_from_result(es_result):
        if es_result:
            nodes = es_result["hits"]["hits"]
            result = [node["_source"]["uuid"] for node in nodes if "uuid" in node["_source"]]
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


def bulk_add_node_index(nodes):
    def index_nodes():
        for node in nodes:
            if node.authority.Common:
                body = node.node_index()
                yield {
                    "_op_type": "create",
                    "_index": "nodes",
                    "_id": node.id,
                    "_source": body
                }
    result = helpers.bulk(es, index_nodes())
    return result


def bulk_add_text_index(nodes):
    def index_texts():
        for node in nodes:
            if node.type != 'link':
                body = node.text_index()
                yield {
                    "_op_type": "create",
                    "_index": "texts",
                    "_id": node.id,
                    "_source": body
                }
    result = helpers.bulk(es, index_texts())
    return result
