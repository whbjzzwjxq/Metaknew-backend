from django.conf.urls import url

from search import views

urlpatterns = [
    url('criteria_query', views.criteria_query),
    url('get_single_node', views.get_single_node)
    # url('get_prop_dict', views.get_dict)
]
