from __future__ import annotations

from typing import TYPE_CHECKING

from django.shortcuts import redirect, render
from django.urls import reverse

from django_airavata.apps.auth.decorators import login_required

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse, HttpResponseRedirect

    from django_airavata.request import AiravataRequest


@login_required
def home(request: AiravataRequest) -> HttpResponseRedirect:
    if request.is_gateway_admin or request.is_read_only_gateway_admin:
        return redirect(reverse("django_airavata_admin:app_catalog"))
    else:
        return redirect(reverse("django_airavata_admin:group_resource_profile"))


@login_required
def app_catalog(request: HttpRequest) -> HttpResponse:
    return render(request, "admin/admin_base.html")


@login_required
def credential_store(request: HttpRequest) -> HttpResponse:
    return render(request, "admin/admin_base.html")


@login_required
def group_resource_profile(request: HttpRequest) -> HttpResponse:
    return render(request, "admin/admin_base.html")


@login_required
def gateway_resource_profile(request: HttpRequest) -> HttpResponse:
    return render(request, "admin/admin_base.html")


@login_required
def notices(request: HttpRequest) -> HttpResponse:
    return render(request, "admin/admin_base.html")


@login_required
def users(request: HttpRequest) -> HttpResponse:
    return render(request, "admin/admin_base.html")


@login_required
def extended_user_profile(request: HttpRequest) -> HttpResponse:
    return render(request, "admin/admin_base.html")


@login_required
def experiment_statistics(request: HttpRequest) -> HttpResponse:
    return render(request, "admin/admin_base.html")


@login_required
def developers(request: HttpRequest) -> HttpResponse:
    return render(request, "admin/admin_base.html")
