"""Django Airavata Auth Middleware."""

import logging
from collections.abc import Callable
from typing import Any

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


def set_admin_group_attributes(request, gateway_groups=None):
    """Set request.is_gateway_admin / request.is_read_only_gateway_admin from JWT realm roles.

    The legacy implementation called the sharing service to look up groups; that
    path raised AttributeError on unauthenticated requests. Now we read realm
    roles directly from the Keycloak JWT (claim: realm_access.roles).
    """
    realm_roles = _extract_realm_roles(request)
    request.is_gateway_admin = "gateway-admin" in realm_roles
    request.is_read_only_gateway_admin = "gateway-readonly-admin" in realm_roles


def _extract_realm_roles(request):
    """Return a set of realm roles from the user's JWT (or empty if unavailable)."""
    import base64
    import json
    import logging
    logger = logging.getLogger(__name__)
    try:
        token = None
        authz = getattr(request, "authz_token", None)
        if authz:
            if isinstance(authz, dict):
                token = authz.get("accessToken")
            else:
                token = getattr(authz, "accessToken", None) or getattr(authz, "access_token", None)
        if not token and hasattr(request, "session"):
            token = request.session.get("ACCESS_TOKEN")
        if not token:
            return set()
        parts = token.split(".")
        if len(parts) != 3:
            return set()
        pad = "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + pad))
        realm_access = payload.get("realm_access") or {}
        roles = realm_access.get("roles") or []
        return set(roles)
    except Exception as e:
        logger.debug("Could not extract realm roles: %s", e)
        return set()


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
            # Admin flags are now derived from Keycloak JWT realm roles;
            # no call to the sharing/compute services is needed.
            set_admin_group_attributes(request)
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
