from django.conf.urls import url
from tools.Id_Generator import new_id_list
urlpatterns = [
    url("generate", new_id_list),
]
