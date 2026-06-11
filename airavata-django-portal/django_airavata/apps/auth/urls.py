
from django.urls import path, re_path

from . import views

app_name = 'django_airavata_auth'
urlpatterns = [
    re_path(r'^login$', views.oidc_login, name='login'),
    re_path(r'^logout$', views.logout, name='logout'),
    re_path(r'^logged-out$', views.logged_out, name='logged_out'),
    re_path(r'^callback/$', views.oidc_callback, name='callback'),
    re_path(r'^login-desktop/$', views.login_desktop, name="login_desktop"),
    re_path(r'^login-desktop-success/$',
            views.login_desktop_success, name="login_desktop_success"),
    re_path(r'^refreshed-token-desktop$', views.refreshed_token_desktop,
            name="refreshed_token_desktop"),
    re_path(r'^access-token-redirect$', views.access_token_redirect, name="access_token_redirect"),
    path('settings-local/', views.download_settings_local, name="download_settings_local"),
]
