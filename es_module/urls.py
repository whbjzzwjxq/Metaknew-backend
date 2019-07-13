from django.conf.urls import url

from search import views

urlpatterns = [
    url('index/', views.get_node_uuid),
]
