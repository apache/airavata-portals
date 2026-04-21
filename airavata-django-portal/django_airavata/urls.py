"""django_airavata_gateway URL Configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from . import views
from .apps.workspace import views as workspace_views

urlpatterns = [
    path("health/", views.health, name="health"),
    re_path(r"^djadmin/", admin.site.urls),
    re_path(r"^admin/", include("django_airavata.apps.admin.urls")),
    re_path(r"^auth/", include("django_airavata.apps.auth.urls")),
    re_path(r"^workspace/", include("django_airavata.apps.workspace.urls")),
    re_path(r"^api/", include("django_airavata.apps.api.urls")),
    re_path(r"^dataparsers/", include("django_airavata.apps.dataparsers.urls")),
    # Resource routes under /resources/
    re_path(r"^resources/storage/(?P<storage_resource_id>[^/]+)$", workspace_views.storage_detail, name="storage_detail"),
    re_path(r"^resources/storage$", workspace_views.user_storage, name="storage"),
    re_path(r"^resources/compute/(?P<compute_resource_id>[^/]+)$", workspace_views.compute_detail, name="compute_detail"),
    re_path(r"^resources/compute$", workspace_views.compute_resources, name="compute"),
    re_path(r"^resources/credentials", workspace_views.credentials, name="credentials"),
    # Gateway settings
    re_path(r"^gateway/settings$", workspace_views.gateway_settings, name="gateway_settings"),
    re_path(r"^home$", views.home, name="home"),
    re_path(r"^cms/", include(wagtailadmin_urls)),
    re_path(r"^documents/", include(wagtaildocs_urls)),
    # For testing, developing error pages
    re_path(r"^400/", views.error400),
    re_path(r"^403/", views.error403),
    re_path(r"^404/", views.error404),
    re_path(r"^500/", views.error500),
    path("", views.landing, name="landing"),
    path("pages/", include("django_airavata.dynamic_apps.urls")),
    path("pages/", include(wagtail_urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = views.error400
handler403 = views.error403
handler404 = views.error404
handler500 = views.error500
