# from elasticsearch_dsl import connections, UpdateByQuery
#
# es = connections.create_connection(hosts=["39.96.10.154:7000"], timeout=60)
#
#
# # Create your views here.
#
#
# def add_node_index(uuid,
#                    name, name_zh='', name_en='', language='',
#                    alias=None, p_label='', keywords=None, labels=None,
#                    description='', description_zh='', description_en=''):
#     """
#
#     :param uuid: 节点的id
#     :param name: 节点的name
#     :param name_zh: 节点的中文名
#     :param name_en: 节点的英文名
#     :param language: 节点的原生语言种类
#     :param alias: 节点的别名
#     :param p_label: 节点的主标签
#     :param keywords: 节点的关键词
#     :param labels: 节点的标签
#     :param description: 节点的简介
#     :param description_zh:
#     :param description_en:
#     :return:
#     """
#     if alias is None:
#         alias = []
#     if not (language == "en" or language == "zh"):
#         language = "auto"
#     ubq = UpdateByQuery.from_dict({
#         "query": {
#             "match": {
#                 "_id": uuid
#             }
#         },
#         "script": {
#             "lang": "painless",
#             "source": """
#                     if doc['hits']['total']['value'] == 0 {
#                         ctx._source.name.auto = params.name
#                         ctx._source.name.zh = params.name_zh
#                         ctx._source.name.en = params.name_en
#                         ctx._source.name.en = params.name_en
#                         ctx._source.language = params.lang
#                         ctx._source.alias = params.alias
#                         ctx._source.p_label = params.p_label
#                         ctx._source.keywords = params.keywords
#                         ctx._source.labels = params.labels
#                         ctx._source.description.auto = params.de
#                         ctx._source.description.zh = params.de_zh
#                         ctx._source.description.en = params.de_en
#                         }
#
#             """,
#             "params": {
#                 "uuid": uuid,
#                 "name": name,
#                 "name_zh": name_zh,
#                 "name_en": name_en,
#                 "lang": language,
#                 "alias": alias,
#                 "p_label": p_label,
#                 "keywords": keywords,
#                 "labels": labels,
#                 "de": description,
#                 "de_zh": description_zh,
#                 "de_en": description_en
#             }
#         },
#     })
#
#     ubq._index = ["nodes"]
#
#     response = ubq.execute()
#     print(response)
#
#
# if __name__ == "__main__":
#     add_node_index(uuid="1111",
#                    name="2222",
#                    name_zh='',
#                    name_en='',
#                    language="auto"
#                    )
