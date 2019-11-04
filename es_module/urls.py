from django.conf.urls import url

from es_module import views

urlpatterns = [
    url("query/node/name_similarity", views.query_name_similarity),
    url("_function/node/reindex_nodes", views.reindex_nodes),
    url("query/home_page_search", views.home_page_search)
]
