from django.conf.urls import url

from search import views

urlpatterns = [
    url('single', views.get_node_uuid),
    url('searchByCondition', views.search_by_condition),
    url('criteria_query', views.criteria_query)
]
