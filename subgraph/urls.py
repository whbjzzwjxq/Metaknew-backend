from django.conf.urls import url
from subgraph import views
from subgraph.script import Latin_America_Import as latin
from subgraph.script import add_location_info

urlpatterns = [
    url("run/script_latin", latin.script_latin),
    url("run/script_add_loc", add_location_info.run_script),
    url("query/query_needed_props", views.query_frontend_prop),
    url("media_node_create", views.upload_main_pic),
    url("bulk_node_create", views.bulk_create_node),
    url("query/query_main_pic", views.query_main_pic)
]
