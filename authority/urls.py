from django.conf.urls import url

from authority import views

urlpatterns = [
    url('add', views.addAuthority)

]
