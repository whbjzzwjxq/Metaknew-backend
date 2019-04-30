from django.conf.urls import url

from search import views, es_search

urlpatterns = [
    url('fuzzy/', es_search.fuzzy_ask_node),
    url('', views.get_single_node)
]
