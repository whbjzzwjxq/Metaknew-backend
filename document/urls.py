"""myblog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

from . import views

urlpatterns = [
    url(r'^comment/get$', views.get_comments),
    url('comment/add', views.add_comment),
    url('documentRelate/add', views.add_document_relate),
    url('documentRelate/select', views.select_document_relate_title),
    url('resource/add', views.add_resource),
    url('resource/select', views.select_resource),
    url('resource/delete', views.delete_resource),
    url('resource/update', views.update_resource)
]
