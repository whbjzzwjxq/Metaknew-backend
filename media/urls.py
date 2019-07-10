from django.conf.urls import url

from media import views

urlpatterns = [
    url('upload', views.upload_file),
]