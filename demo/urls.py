"""demo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path("", views.home, name="home")
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path("", Home.as_view(), name="home")
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path("blog/", include("blog.urls"))
"""
from base_api.user import login
from base_api.subgraph import node
from base_api.subgraph import common
from base_api.subgraph import media
from django.conf.urls.static import static
from django.conf import settings

all_api = login.apis + node.apis + common.apis + media.apis
urlpatterns = [
    api().url_pattern for api in all_api if api.meta.is_active and not api.abstract
] + static(settings.STATIC_URL)
