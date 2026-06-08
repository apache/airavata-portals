from . import views
from django.urls import re_path

app_name='workspace'
urlpatterns = [
    re_path(r'^storage/$', views.storage, name="storages"),
    re_path(r'^storage/(?P<storage_id>[^/]+)/$', views.resources, name="resources")
]