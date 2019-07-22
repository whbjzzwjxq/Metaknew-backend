from django.conf.urls import url

from es_module import views

urlpatterns = [
    url('index', views.es_ask_all),
]
