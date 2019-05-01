from django.conf.urls import url

from search import views, es_search

urlpatterns = [
    url('fuzzy/', es_search.fuzzy_ask_node),
    url('auto/', es_search.auto_complete),
    url('', views.get_single_node)
]
