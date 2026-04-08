from django_airavata.dynamic_apps import CUSTOM_DJANGO_APPS
from django.conf.urls import include
from django.urls import path

urlpatterns = []
for custom_django_app in CUSTOM_DJANGO_APPS:
    # Custom Django apps may define a url_prefix, otherwise label will be used
    # as url prefix
    url_prefix = getattr(custom_django_app, "url_prefix", custom_django_app.label)
    urlpatterns.append(
        path(f"{url_prefix}/", include(custom_django_app.name + ".urls"))
    )
