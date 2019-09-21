from elasticsearch import Elasticsearch, helpers
from subgraph.logic_class import BaseNode
from subgraph.models import Text
from tools.redis_process import set_un_index_text, set_un_index_node
from typing import List
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


def node_index(node: BaseNode, _type: str):
    ctrl = node.ctrl
    info = node.info
    body = {
        "id": node.id,
        "language": info.Language,
        "type": _type,
        "create_user": ctrl.CreateUser,
        "update_time": ctrl.UpdateTime,
        "main_pic": info.MainPic,
        "name": {
            "zh": "",
            "en": "",
            "auto": info.Name
        },
        "tags": {
            "p_label": info.PrimaryLabel,
            "alias": info.Alias,
            "labels": info.Labels,
            "topic": info.Topic
        },
        "level": {
            "imp": ctrl.Imp,
            "hard_level": ctrl.HardLevel,
            "useful": ctrl.Useful,
            "star": ctrl.Star,
            "hot": ctrl.Hot,
            "total_time": ctrl.TotalTime
        }
    }
    for lang in body["name"]:
        if lang in info.Translate:
            body["name"][lang] = info.Translate[lang]

    return body


def text_index(text: Text):
    body = {
        "id": text.NodeId,
        "language": text.Language,
        "keywords": text.Keywords,
        "text": {
            "zh": "",
            "en": "",
            "auto": text.Text
        },
        "hot": text.Hot,
        "star": text.Star,
        "is_bound": text.Is_Bound
    }
    for lang in body["text"]:
        if lang in text.Translate:
            body["text"][lang] = text.Translate[lang]
    return body


def add_node_index(node: BaseNode):
    if node.authority.Common:
        body = node_index(node, _type='node')
        result = es.index(id=node.id, index="nodes", body=body)
        if result["_shards"]["successful"] == 1:
            return True
        else:
            set_un_index_node([node.id])
            return False
    else:
        return False


def add_text_index(text: Text):
    if text:
        body = text_index(text)
        result = es.index(index="texts", body=body, doc_type="_doc")
        if result["_shards"]["successful"] == 1:
            return True
        else:
            set_un_index_text([text.NodeId])
            return False


def bulk_add_node_index(nodes: List[BaseNode]):
    def index_nodes():
        for node in nodes:
            if node.authority.Common:
                body = node_index(node, _type="node")
                yield {
                    "_op_type": "create",
                    "_index": "nodes",
                    "_id": node.id,
                    "_source": body
                }
    result = helpers.bulk(es, index_nodes())
    return result


def bulk_add_text_index(texts: List[Text]):
    def index_texts():
        for text in texts:
            if text:
                body = text_index(text)
                yield {
                    "_op_type": "create",
                    "_index": "texts",
                    "_id": text.NodeId,
                    "_source": body
                }
    result = helpers.bulk(es, index_texts())
    return result
