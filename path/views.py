import json
from django.http import HttpResponse
from django.core.cache import cache
from django.forms.models import model_to_dict
from path import paths
from document import document_info

# Create your views here.

# 新增路径               已测试-----4.24-----ZXN
def add_path(request):
    """
    	"data":{
		"path_title":"计算机",
		"path_document":[
			{"uuid":"b81cb129-9631-4d2f-9af0-74b8c56af8d5","order":"1","time":"200"},
			{"uuid":"3ad90c1a-601a-4d24-a22b-9931d6b5174c","order":"2","time":"300"},
			{"uuid":"3ad90c1a-601a-4d24-a22b-9931d6b5174c","order":"2","time":"300"},
			{"uuid":"924d061c-5517-11e9-9703-04d3b0eb8835","order":"3", "time":"100"}
		],
		"path_info":{
			"create_user":"2",
			"imp":"0.94",
			"hard_level":"0.99"
		}
	}
    """
    param = json.loads(request.body)['data']
    resp = HttpResponse()
    paths.add(param)
    respData = {'status': '1', 'ret': '添加成功!!!'}
    resp.content = json.dumps(respData)
    return HttpResponse(resp, content_type="application/json")



# 依据路径id查询路径，redis里有缓存的，则从redis里返回，没有则从数据库表里查找数据返回        已测试-----4.24-----ZXN
def showAllPath(request):
    param = json.loads(request.body)['data']
    path_id = param['path_id']
    path = paths.showById(path_id)
    res = []
    for p in path:
        documents = p.path_document
        for doc in documents:
            doc_info = json.loads(doc)
            # print(doc_info)
            doc_uuid = doc_info['uuid']
            if cache.has_key(doc_uuid):
                res.append(cache.get(doc_uuid))
                # print(1)
            else:
                docs = document_info.selectById(doc_uuid)
                for doc in docs:
                    doc.uuid = str(doc.uuid)
                    doc.time = str(doc.time)
                    res.append(dict(model_to_dict(doc).items()))
                    # print(2)
    return HttpResponse(json.dumps(res), content_type="application/json")
