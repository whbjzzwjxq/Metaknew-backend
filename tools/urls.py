from django.conf.urls import url
from tools.id_generator import new_id_list

urlpatterns = [
    url("generate", new_id_list),
]
