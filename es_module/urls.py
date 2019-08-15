from django.conf.urls import url

from es_module import views

urlpatterns = [
    url("query/node/name", views.es_ask_all),
    url("query/all/name", views.es_ask_all)
]
