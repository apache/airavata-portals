# Create your views here.

from __future__ import annotations

from typing import TYPE_CHECKING

from django.shortcuts import render

from django_airavata.apps.auth.decorators import login_required

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


@login_required
def groups_manage(request: HttpRequest) -> HttpResponse:

    return render(
        request, "django_airavata_groups/base.html", {"bundle_name": "group-list"}
    )


@login_required
def groups_create(request: HttpRequest) -> HttpResponse:

    return render(
        request,
        "django_airavata_groups/base.html",
        {
            "bundle_name": "group-create",
            "next": request.GET.get("next"),
        },
    )


@login_required
def edit_group(request: HttpRequest, group_id: str) -> HttpResponse:

    return render(
        request,
        "django_airavata_groups/group_edit.html",
        {
            "bundle_name": "group-edit",
            "group_id": group_id,
            "next": request.GET.get("next"),
        },
    )
