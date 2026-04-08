"""Django Airavata Auth Middleware."""

import copy
import logging
from collections.abc import Callable
from typing import Any

from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

from . import utils

log = logging.getLogger(__name__)


def authz_token_middleware(
    get_response: Callable[[HttpRequest], HttpResponse],
) -> Callable[[HttpRequest], HttpResponse]:
    """Automatically add the 'authz_token' to the request."""

    def middleware(request: Any) -> HttpResponse:

        authz_token = None
        if request.user.is_authenticated:
            authz_token = utils.get_authz_token(request)
            # If we can't construct an authz_token then need to re-login
            if authz_token is None:
                # logout user since no longer logged in with IAM server
                logout(request)

        request.authz_token = authz_token

        return get_response(request)

    return middleware


def set_admin_group_attributes(request: Any, gateway_groups: Any = None) -> None:
    """Set is_gateway_admin and is_read_only_gateway_admin request attrs."""
    if gateway_groups is None:
        gateway_groups = request.airavata_client.iam.get_gateway_groups()
    admins_group_id = (
        gateway_groups.get("adminsGroupId") if isinstance(gateway_groups, dict) else gateway_groups.admins_group_id
    )
    read_only_admins_group_id = (
        gateway_groups.get("readOnlyAdminsGroupId")
        if isinstance(gateway_groups, dict)
        else gateway_groups.read_only_admins_group_id
    )
    airavata_internal_user_id = request.user.username + "@" + settings.GATEWAY_ID
    group_memberships = request.airavata_client.sharing.get_all_groups_user_belongs(airavata_internal_user_id)
    group_ids = [group.id for group in group_memberships]
    request.is_gateway_admin = admins_group_id in group_ids
    request.is_read_only_gateway_admin = read_only_admins_group_id in group_ids


def gateway_groups_middleware(
    get_response: Callable[[HttpRequest], HttpResponse],
) -> Callable[[HttpRequest], HttpResponse]:
    """Add 'is_gateway_admin' and 'is_read_only_gateway_admin' to request."""

    def middleware(request: Any) -> HttpResponse:

        request.is_gateway_admin = False
        request.is_read_only_gateway_admin = False

        if (
            not request.user.is_authenticated
            or not request.authz_token
            or (hasattr(request.user, "user_profile") and not request.user.user_profile.is_complete)
        ):
            return get_response(request)

        try:
            # Load the GatewayGroups and check if user is in the Admins and/or
            # Read Only Admins groups
            if not request.session.get("GATEWAY_GROUPS"):
                gateway_groups = request.airavata_client.iam.get_gateway_groups()
                gateway_groups_dict = (
                    copy.deepcopy(gateway_groups.__dict__)
                    if hasattr(gateway_groups, "__dict__")
                    else dict(gateway_groups)
                )
                request.session["GATEWAY_GROUPS"] = gateway_groups_dict
            set_admin_group_attributes(request, gateway_groups=request.session.get("GATEWAY_GROUPS"))
            # Gateway Admins are made 'superuser' in Django so they can edit
            # pages in the CMS
            if request.is_gateway_admin and (not request.user.is_superuser or not request.user.is_staff):
                request.user.is_superuser = True
                request.user.is_staff = True
                request.user.save()
        except Exception as e:
            log.warning("Failed to set is_gateway_admin, is_read_only_gateway_admin for user", exc_info=e)

        return get_response(request)

    return middleware


def user_profile_completeness_check(
    get_response: Callable[[HttpRequest], HttpResponse],
) -> Callable[[HttpRequest], HttpResponse]:
    """Check if user profile is complete and if not, redirect to user profile editor."""

    def middleware(request: Any) -> HttpResponse:

        if not request.user.is_authenticated:
            return get_response(request)

        allowed_paths = [
            reverse("django_airavata_auth:user_profile"),
            reverse("django_airavata_auth:logout"),
        ]
        incomplete_user_profile = hasattr(request.user, "user_profile") and not request.user.user_profile.is_complete
        # Exclude admin's from the ext user profile check since they will be
        # creating/editing the ext user profile fields
        invalid_ext_user_profile = (
            not getattr(request, "is_gateway_admin", False)
            and hasattr(request.user, "user_profile")
            and not request.user.user_profile.is_ext_user_profile_valid
        )
        if (
            (incomplete_user_profile or invalid_ext_user_profile)
            and request.path not in allowed_paths
            and "text/html" in request.META["HTTP_ACCEPT"]
        ):
            return redirect("django_airavata_auth:user_profile")
        else:
            return get_response(request)

    return middleware
