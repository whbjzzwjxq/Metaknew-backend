from django.conf.urls import url
from subgraph import views
urlpatterns = [
    url("add/node", views.single_node),
    url('uploadExcel', views.upload_excel)
]
