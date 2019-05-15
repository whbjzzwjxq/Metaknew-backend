from django.conf.urls import url
from path import views

urlpatterns = [
    url('add', views.add_path),
    url('selectAll', views.showAllPath),
]