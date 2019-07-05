from django.conf.urls import url
from subgraph import views
urlpatterns = [
    url("add/node", views.add_node),
]
