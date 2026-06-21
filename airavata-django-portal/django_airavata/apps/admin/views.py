from django.shortcuts import redirect, render
from django.urls import reverse

from django_airavata.apps.auth.decorators import login_required


@login_required
def home(request):
    if request.is_gateway_admin or request.is_read_only_gateway_admin:
        return redirect(reverse("django_airavata_admin:app_catalog"))
    else:
        return redirect(reverse("django_airavata_admin:group_resource_profile"))


@login_required
def app_catalog(request):
    return render(request, "admin/admin_base.html")


@login_required
def credential_store(request):
    return render(request, "admin/admin_base.html")


@login_required
def group_resource_profile(request):
    return render(request, "admin/admin_base.html")


@login_required
def gateway_resource_profile(request):
    return render(request, "admin/admin_base.html")


@login_required
def notices(request):
    return render(request, "admin/admin_base.html")


@login_required
def users(request):
    return render(request, "admin/admin_base.html")


@login_required
def extended_user_profile(request):
    return render(request, "admin/admin_base.html")


@login_required
def experiment_statistics(request):
    return render(request, "admin/admin_base.html")


@login_required
def developers(request):
    return render(request, "admin/admin_base.html")
