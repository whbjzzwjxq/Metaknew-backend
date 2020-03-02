import langdetect
from elasticsearch import Elasticsearch, helpers
from elasticsearch.helpers.errors import BulkIndexError

es = Elasticsearch([{"host": "39.96.10.154", "port": 7000}])


def language_detect(text):
    lang = langdetect.detect(text)
    if lang == 'zh_cn' or lang == 'zh_tw':
        lang = 'zh'
    elif lang == 'en':
        lang = 'en'
    else:
        lang = 'auto'
    return lang


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
        body_list = []
        labels = [label.lower() for label in query_object["labels"]]
        props = query_object["props"]
        keyword = query_object["keyword"]

        # name-alias
        if 'language' in query_object:
            language = query_object["language"]
        else:
            language = language_detect(keyword)

        body_list.append(self.name_match_body(keyword, language))

        # type
        active_types = []
        for _type in self._types:
            if _type in labels:
                active_types.append(_type)
                labels.remove(_type)
        if active_types:
            body_list.append(self.type_match_body(active_types))

        # label topic
        if labels:
            body_list.append(self.label_boost_body(labels))

        dis_max_body = {
            "dis_max": {
                "queries": body_list,
                "tie_breaker": 0.7
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
    def name_match_body(keyword, language):
        if language == 'auto':
            fields = ["Name_auto", "Name_auto.total",
                      "Alias"]
        else:
            fields = ["Name_auto", "Name_auto.total",
                      'Name_%s' % language, 'Name_%s.total' % language,
                      "Alias"]
        body = {
            "multi_match": {
                "query": keyword,
                "fields": fields,
                "type": "best_fields",
                "tie_breaker": 0.7
            }
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
        body = {
            'terms': {
                "Labels": labels,
                "boost": 2
            }
        }
        return body

    @staticmethod
    def get_info_from_result(es_result):
        if es_result:
            nodes = es_result["hits"]["hits"]
            result = [node["_source"] for node in nodes if "id" in node["_source"]]
            return result
        else:
            return []


def bulk_add_text_index(nodes):
    """
    自动判断是否是update
    :param nodes: 公开资源PublicItem的列表 PublicItemModel
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

    try:
        result = helpers.bulk(es, index_texts())
        return result
    except BulkIndexError or BaseException:
        return None
