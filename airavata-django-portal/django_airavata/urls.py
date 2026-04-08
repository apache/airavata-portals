"""django_airavata_gateway URL Configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    re_path(r"^djadmin/", admin.site.urls),
    re_path(r"^admin/", include("django_airavata.apps.admin.urls")),
    re_path(r"^auth/", include("django_airavata.apps.auth.urls")),
    re_path(r"^workspace/", include("django_airavata.apps.workspace.urls")),
    re_path(r"^api/", include("django_airavata.apps.api.urls")),
    re_path(r"^groups/", include("django_airavata.apps.groups.urls")),
    re_path(r"^dataparsers/", include("django_airavata.apps.dataparsers.urls")),
    re_path(r"^home$", views.home, name="home"),
    re_path(r"^cms/", include(wagtailadmin_urls)),
    re_path(r"^documents/", include(wagtaildocs_urls)),
    # For testing, developing error pages
    re_path(r"^400/", views.error400),
    re_path(r"^403/", views.error403),
    re_path(r"^404/", views.error404),
    re_path(r"^500/", views.error500),
    path("", include("django_airavata.dynamic_apps.urls")),
    path("", include(wagtail_urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = views.error400
handler403 = views.error403
handler404 = views.error404
handler500 = views.error500
