"""django_airavata_gateway URL Configuration

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

from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.urls import path, re_path

from . import views
from .apps.api import downloads as api_downloads
from .apps.api import views as api_views

urlpatterns = [
    re_path(r"^admin/", include("django_airavata.apps.admin.urls")),
    re_path(r"^auth/", include("django_airavata.apps.auth.urls")),
    re_path(r"^workspace/", include("django_airavata.apps.workspace.urls")),
    re_path(r"^api/", include("django_airavata.apps.api.urls")),
    re_path(r"^groups/", include("django_airavata.apps.groups.urls")),
    re_path(r"^dataparsers/", include("django_airavata.apps.dataparsers.urls")),
    # Directory zip + single-file downloads the file browser / output displays link
    # to. Paths kept under /sdk/ so the built frontend's hardcoded hrefs keep working
    # (the retired airavata_django_portal_sdk served these from /sdk/).
    path("sdk/download/", api_views.download, name="sdk_download"),
    path("sdk/download-dir/", api_downloads.download_dir, name="download_dir"),
    path(
        "sdk/download-experiment-dir/<experiment_id>/",
        api_downloads.download_experiment_dir,
        name="download_experiment_dir",
    ),
    # Root + /home render the portal landing. In production a reverse proxy
    # routes / to the standalone airavata-cms; standalone (no proxy) lands here.
    re_path(r"^(?:home)?$", views.home, name="home"),
    # For testing, developing error pages
    re_path(r"^400/", views.error400),
    re_path(r"^403/", views.error403),
    re_path(r"^404/", views.error404),
    re_path(r"^500/", views.error500),
    # Landing pages, documentation, and other CMS content are served by the
    # standalone airavata-cms service; a reverse proxy routes the portal's app
    # paths (below) here and everything else to the CMS (see deploy/).
    path("", include("django_airavata.commons.dynamic_apps.urls")),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]

handler400 = views.error400
handler403 = views.error403
handler404 = views.error404
handler500 = views.error500
