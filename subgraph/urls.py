from django.conf.urls import url

from subgraph import views

urlpatterns = [
    url("update/node/main_pic", views.upload_media_by_user),
    url("create/node/bulk_create", views.bulk_create_node),
    url("create/media/normal", views.upload_media_by_user),
    url("update/node/normal", views.update_single_node_by_user),
    url("query/query_needed_props", views.query_frontend_prop),
    url("query/query_single_node", views.query_single_node),
    url("query/multi", views.query_multi_source),
    url("query/media/multi", views.query_multi_media)
]
