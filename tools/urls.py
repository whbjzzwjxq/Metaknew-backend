from django.conf.urls import url
from tools.Id_Generator import new_id_list
from tools.global_word_index import word_request
from tools.test_tool import test_tool
urlpatterns = [
    url("generate", new_id_list),
    url("query_word_index", word_request),
    url("test", test_tool)
]
