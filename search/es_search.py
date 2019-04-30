from elasticsearch import Elasticsearch
# 注意es必须配置在服务器上 考虑另起一个django项目
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])


def fuzzy_ask(keyword, target, index):
    body = {
        "query": {
            "fuzzy": {
                target: {
                    "value": keyword,
                    "boost": 1.0,
                    "fuzziness": 3,
                    "prefix_length": 3,
                    "max_expansions": 20
                }
            }
        }
    }
    return es.search(index=index, body=body)

