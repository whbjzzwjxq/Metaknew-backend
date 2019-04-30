from elasticsearch import Elasticsearch
es = Elasticsearch([{'host': '39.96.10.154', 'port': 9200}])


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

