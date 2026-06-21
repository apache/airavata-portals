# Create your views here.

from django.shortcuts import render

from django_airavata.apps.auth.decorators import login_required


@login_required
def groups_manage(request):

    return render(
        request, "django_airavata_groups/base.html", {"bundle_name": "group-list"}
    )


@login_required
def groups_create(request):

    return render(
        request,
        "django_airavata_groups/base.html",
        {
            "bundle_name": "group-create",
            "next": request.GET.get("next"),
        },
    )


@login_required
def edit_group(request, group_id):

    return render(
        request,
        "django_airavata_groups/group_edit.html",
        {
            "bundle_name": "group-edit",
            "group_id": group_id,
            "next": request.GET.get("next"),
        },
    )
