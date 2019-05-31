from django.conf.urls import url

from search import views, es_search

urlpatterns = [
    url('single/', views.get_node_uuid),
    url('es_ask/', es_search.es_ask),
    url('criteria_query', views.criteria_query),
]
