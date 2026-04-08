# Create your views here.

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

ENTRY_POINTS = {
    'group-list': 'static/django_airavata_groups/js/group-listing-entry-point.js',
    'group-create': 'static/django_airavata_groups/js/group-create-entry-point.js',
    'group-edit': 'static/django_airavata_groups/js/group-edit-entry-point.js',
}


@login_required
def groups_manage(request):
    request.active_nav_item = "manage"

    return render(request, 'django_airavata_groups/base.html', {
        'bundle_name': 'group-list',
        'entry_point': ENTRY_POINTS['group-list'],
    })


@login_required
def groups_create(request):
    request.active_nav_item = "manage"

    return render(request, 'django_airavata_groups/base.html', {
        'bundle_name': 'group-create',
        'entry_point': ENTRY_POINTS['group-create'],
        'next': request.GET.get('next'),
    })


@login_required
def edit_group(request, group_id):
    request.active_nav_item = "manage"

    return render(request, 'django_airavata_groups/group_edit.html', {
        'bundle_name': 'group-edit',
        'entry_point': ENTRY_POINTS['group-edit'],
        'group_id': group_id,
        'next': request.GET.get('next'),
    })
