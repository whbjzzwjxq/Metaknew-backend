"""demo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from subgraph import views
from django.conf.urls import url
from django.views.static import serve
from django.conf import settings

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('document/', include('document.urls')),
    path('user/', include('users.urls')),
    path('note/', include('note.urls')),
    path('uploadExcel', views.upload_excel),
    url(r'media/(?P<path>.*)', serve, {'document_root': settings.BASE_DIR}),
    path('search/', include('search.urls'))
]
