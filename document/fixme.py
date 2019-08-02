

# # 下载文件                         已测试------4.18-----ZXN
# def download_file(request):
#     resp = HttpResponse()
#     uuid = request.POST.get("uuid", "")
#     fileName = request.POST.get("fileName", "")
#     docs = document_info.selectURLById(uuid)
#     for doc in docs:
#         names = doc.included_media
#         print(names)
#         print(fileName)
#         if fileName in names:
#             the_file_name = settings.BASE_DIR + os.sep + "files" + os.sep + "upload" + os.sep + fileName
#             file = open(the_file_name, "rb")
#             # response = StreamingHttpResponse(file_iterator(url))
#             response = StreamingHttpResponse(file)
#             response["Content-Type"] = "application/octet-stream; charset=unicode"
#             response["Content-Disposition"] = "attachment;filename="{0}"".format(escape_uri_path(
#                 fileName))  # escape_uri_path()解决中文名文件(from django.utils.encoding import escape_uri_path)
#             return response
#
#
# # 删除文件             已测试---4.18-----ZXN
# def delete_file(request):
#     resp = HttpResponse()
#     uuid = request.POST.get("uuid", "")
#     fileName = request.POST.get("fileName", "")
#     docs = document_info.selectURLById(uuid)
#     for doc in docs:
#         names = doc.included_media
#         if fileName in names:
#             names.remove(fileName)
#             document_info.updateURLById(uuid, names)
#             the_file_name = settings.BASE_DIR + os.sep + "files" + os.sep + "upload" + os.sep + fileName
#             if os.path.exists(the_file_name):
#                 os.remove(the_file_name)
#                 respData = {"status": "1", "ret": "删除成功！！！"}
#             else:
#                 respData = {"status": "0", "ret": "文件不存在，删除失败,请于管理员联系。"}
#         else:
#             respData = {"status": "0", "ret": "文件不存在，删除失败,请于管理员联系。"}
#     resp.content = json.dumps(respData)
#     return HttpResponse(resp, content_type="application/json")



# # 新增专题
# def add_document(request):
#     if request.method == "POST":
#         data = json.loads(request.body, encoding="utf-8")["data"]
#         # 专题节点与关系
#         nodes = data["nodes"]
#         relationships = data["relationships"]
#
#         # 专题信息
#         info = data["info"]
#
#         # 预定义容器
#         doc_nodes = []
#         doc_relationships = []
#         Doc2Nodes = []
#         node_index = {}
#
#         for node in nodes:
#             # 记录新建节点自动赋予的uuid
#             old_id = node["info"]["uuid"]
#             new_node = handle_node(node["info"])
#             node_index.update({old_id: new_node})
#
#             # 记录专题内节点坐标
#             conf = {"uuid": new_node["uuid"], "conf": node["conf"]}
#             doc_nodes.append(conf)
#
#             # 先记录下节点和专题的相关性
#             if new_node["Name"] in info["keywords"]:
#                 Doc2Nodes.append({"type": "Doc2Node", "rate": 0.5, "source": new_node})
#
#         for relationship in relationships:
#             # 从node_index里访问提交后的Node对象
#             relationship["info"]["source"] = node_index[relationship["info"]["source"]]
#             relationship["info"]["target"] = node_index[relationship["info"]["target"]]
#             new_rel = handle_relationship(relationship["info"])
#             conf = {"uuid": new_rel["uuid"], "conf": relationship["conf"]}
#             doc_relationships.append(conf)
#         # 新建专题
#         new_document = {"Name": info["title"],
#                         "PrimaryLabel": "Document",
#                         "Topic": info["Topic"],
#                         "type": "Document",
#                         "nodes": doc_nodes,
#                         "relationships": doc_relationships
#                         }
#         new_document = create_node(new_document)
#
#         # 生成专题节点后再生成专题与普通节点的关系
#         for Doc2Node in Doc2Nodes:
#             Doc2Node.update({"target": new_document})
#             handle_relationship(Doc2Node)
#
#         # DocumentInformation部分
#         data["info"]["uuid"] = new_document["uuid"]
#         new_document_info = DocumentInformation()
#         for key in get_dict(new_document_info):
#             if key in data["info"]:
#                 setattr(new_document_info, key, data["info"][key])
#         new_document_info.save()
#         return HttpResponse("Create Document Success")


# # 新增路径               已测试-----4.24-----ZXN
# def add_path(request):
#     """
#         "data":{
#         "path_title":"计算机",
#         "path_document":[
#             {"uuid":"b81cb129-9631-4d2f-9af0-74b8c56af8d5","order":"1","time":"200"},
#             {"uuid":"3ad90c1a-601a-4d24-a22b-9931d6b5174c","order":"2","time":"300"},
#             {"uuid":"924d061c-5517-11e9-9703-04d3b0eb8835","order":"3", "time":"100"}
#         ],
#         "path_info":{
#             "create_user":"2",
#             "imp":"0.94",
#             "hard_level":"0.99"
#         }
#     }
#     """
#     param = json.loads(request.body)["data"]
#     resp = HttpResponse()
#     paths.add(param)
#     respData = {"status": "1", "ret": "添加成功!!!"}
#     resp.content = json.dumps(respData)
#     return HttpResponse(resp, content_type="application/json")
#
#
# # 依据路径id查询路径，redis里有缓存的，则从redis里返回，没有则从数据库表里查找数据返回        已测试-----4.24-----ZXN
# def showAllPath(request):
#     param = json.loads(request.body)["data"]
#     path_id = param["path_id"]
#     path = paths.showById(path_id)
#     res = []
#     for p in path:
#         documents = p.path_document
#         for doc in documents:
#             doc_info = json.loads(doc)
#             # print(doc_info)
#             doc_uuid = doc_info["uuid"]
#             if cache.has_key(doc_uuid):
#                 res.append(cache.get(doc_uuid))
#                 # print(1)
#             else:
#                 docs = document_info.selectById(doc_uuid)
#                 for doc in docs:
#                     doc.uuid = str(doc.uuid)
#                     doc.time = str(doc.time)
#                     res.append(dict(model_to_dict(doc).items()))
#                     # print(2)
#     return HttpResponse(json.dumps(res), content_type="application/json")
