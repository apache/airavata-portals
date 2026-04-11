from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse


@login_required
def home(request):
    return redirect(reverse("django_airavata_admin:credential_store"))


@login_required
def app_catalog(request):
    # The list view is merged into the workspace dashboard;
    # sub-routes (new, edit) still render the admin SPA editor.
    path = request.path.rstrip("/")
    if path == "/admin/applications":
        return redirect(reverse("django_airavata_workspace:applications"))
    request.active_nav_item = "app_catalog"
    return render(request, "admin/admin_base.html")


@login_required
def credential_store(request):
    request.active_nav_item = "credentials"
    return render(request, "admin/admin_base.html")


@login_required
def compute_resource(request):
    return render(request, "admin/compute_resource.html")


@login_required
def group_resource_profile(request):
    request.active_nav_item = "group_resource_profile"
    return render(request, "admin/admin_base.html")


@login_required
def gateway_resource_profile(request):
    request.active_nav_item = "gateway_resource_profile"
    return render(request, "admin/admin_base.html")


@login_required
def notices(request):
    request.active_nav_item = "notices"
    return render(request, "admin/admin_base.html")


@login_required
def users(request):
    request.active_nav_item = "users"
    return render(request, "admin/admin_base.html")


@login_required
def extended_user_profile(request):
    request.active_nav_item = "users"
    return render(request, "admin/admin_base.html")


@login_required
def experiment_statistics(request):
    request.active_nav_item = "experiment-statistics"
    return render(request, "admin/admin_base.html")


@login_required
def developers(request):
    request.active_nav_item = "developers"
    return render(request, "admin/admin_base.html")
