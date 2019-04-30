from django.conf.urls import url

from search import views

urlpatterns = [
    url('', views.get_single_node)
]
