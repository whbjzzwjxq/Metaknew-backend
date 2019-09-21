from django.conf.urls import url
from subgraph import views

urlpatterns = [
    url("create/media/main_pic", views.upload_main_pic),
    url("create/node/bulk_create", views.bulk_create_node),
    url("create/media/normal", views.upload_media),
    url("query/query_main_pic", views.query_main_pic),
    url("query/query_needed_props", views.query_frontend_prop),
    url("query/query_single_node", views.query_single_node)
]
