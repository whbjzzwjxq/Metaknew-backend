from django.conf.urls import url

from search import views

urlpatterns = [
    url('', views.get_single_node),
    url('fuzzy/', views.fuzzy_ask_node)
]
