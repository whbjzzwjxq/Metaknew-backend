from django.conf.urls import url

from es_module import views

urlpatterns = [
    url("query/node/name_similarity", views.query_name_similarity)
]
