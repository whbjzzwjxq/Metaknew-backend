from django.conf.urls import url

from es_module import views

urlpatterns = [
    url("query/node/name_similarity", views.query_name_similarity),
    url("query/common/home_page", views.query_for_home_page),
    url("_function/node/reindex_nodes", views.reindex_nodes)
]
