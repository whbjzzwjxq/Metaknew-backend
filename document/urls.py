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
from django.conf.urls import url
from django.contrib import admin

from document import views

urlpatterns = [
    url(r'^comment/get$', views.get_comments),
    url('comment/add', views.add_comment),
    # url('documentRelate/select', views.select_document_relate_title),
    url('resource/select', views.select_resource),
    url('documentInformation/add', views.add_document_information),
    url('comment/update', views.update_comment),
    url('comment/del', views.delete_comment),
    url('documentInformation/get', views.get_doc_info),
    url('documentInformation/showAll', views.get_all_doc_info),
    url('file/upload', views.upload_file),
    url('file/delete', views.delete_file),
    url('file/download', views.download_file),
    url('change/add', views.add_document)
]
