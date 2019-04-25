from django.conf.urls import url

from search import views

urlpatterns = [
    url('/fuzzyask', views.FuzzyAsk),
    url('/document', views.get_document)
]
