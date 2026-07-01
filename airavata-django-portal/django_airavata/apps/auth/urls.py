from django.urls import re_path

from . import views

app_name = "django_airavata_auth"
urlpatterns = [
    re_path(r"^login$", views.oidc_login, name="login"),
    re_path(r"^logout$", views.logout, name="logout"),
    re_path(r"^logged-out$", views.logged_out, name="logged_out"),
    re_path(r"^callback/$", views.oidc_callback, name="callback"),
]
