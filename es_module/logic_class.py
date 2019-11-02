from elasticsearch import Elasticsearch, helpers

es = Elasticsearch([{"host": "39.96.10.154", "port": 7000}])


#  todo 加入评分 level: 3
class EsQuery:
    _types = ['node', 'media', 'document', 'fragment']

    def __init__(self):
        self.es = Elasticsearch([{"host": "39.96.10.154", "port": 7000}])

    def query(self, body, index):
        query_body = {
            "query": body
        }
        return self.es.search(index=index, body=query_body)

    def main(self, query_object):
        labels = query_object["labels"]
        props = query_object["props"]
        keyword = query_object["keyword"]
        active_types = [_type for _type in self._types if _type in labels]
        body_list = [
            self.fuzzy_query_body(keyword, 'auto'),
            self.fuzzy_alias_body(keyword)
        ]
        # todo 详细的搜索引擎 level: 1
        dis_max_body = {
            "dis_max": {
                "queries": body_list,
                "tie_breaker": 0.5
            }
        }
        result = self.query(body=dis_max_body, index="nodes")
        return self.get_info_from_result(result)

    @staticmethod
    def type_match_body(_types):
        should = [{"term": {"type": _type}} for _type in _types]
        body = {
            "should": should
        }
        return body

    @staticmethod
    def fuzzy_query_body(keyword, language):
        body = {
            "fuzzy": {
                "Name.%s" % language: {
                    "value": keyword,
                    "fuzziness": 6,
                    "prefix_length": 3,
                    "max_expansions": 20,
                    "transpositions": True,
                }
            }
        }
        return body

    @staticmethod
    def fuzzy_alias_body(keyword):
        body = {
            "fuzzy": {
                "Alias": {
                    "value": keyword,
                    "fuzziness": 6,
                    "prefix_length": 3,
                    "max_expansions": 20,
                    "transpositions": True,
                }
            }
        }
        return body

    @staticmethod
    def label_boost_body(labels):
        pass

    @staticmethod
    def get_info_from_result(es_result):
        if es_result:
            nodes = es_result["hits"]["hits"]
            result = [node["_source"] for node in nodes if "id" in node["_source"]]
            return result
        else:
            return []


def bulk_add_node_index(nodes):
    """
    调用了is_create
    :param nodes:
    :return:
    """
    def index_nodes():
        for node in nodes:
            body = node.node_index()
            if node.is_create:
                _type = 'create'
            else:
                _type = 'update'
                body = {"doc": body}
            yield {
                "_op_type": _type,
                "_index": "nodes",
                "_id": node.id,
                "_source": body
            }

    result = helpers.bulk(es, index_nodes())
    return result


def bulk_add_text_index(nodes):
    """
    调用了is_create
    :param nodes:
    :return:
    """
    def index_texts():
        for node in nodes:
            body = node.text_index()
            if node.is_create:
                _type = 'create'
            else:
                _type = 'update'
                body = {"doc": body}
            if body:
                yield {
                    "_op_type": _type,
                    "_index": "texts",
                    "_id": node.id,
                    "_source": body
                }

    result = helpers.bulk(es, index_texts())
    return result
