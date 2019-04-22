

from django.conf.urls import url
from note import views

urlpatterns = [
    url('add', views.add_note),
    url('delete', views.delete_note),
    url('update', views.update_note),
    url('select', views.show_note),
]