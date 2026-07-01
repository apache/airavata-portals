"""Django Airavata Auth Middleware."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from . import utils
from .token_authentication import AnonymousUser

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpResponseBase

    from django_airavata.request import AiravataRequest

type Middleware = Callable[[AiravataRequest], HttpResponseBase]
type GetResponse = Callable[[AiravataRequest], HttpResponseBase]

log = logging.getLogger(__name__)


# Keycloak realm roles that map to the coarse gateway-admin flags.
GATEWAY_ADMIN_ROLE = "admin-rw"
READ_ONLY_ADMIN_ROLE = "admin-ro"


def set_admin_flags_from_roles(request: AiravataRequest) -> None:
    """Set is_gateway_admin / is_read_only_gateway_admin from the JWT realm roles."""
    roles = set(getattr(request.user, "realm_roles", []) or [])
    request.is_gateway_admin = GATEWAY_ADMIN_ROLE in roles
    request.is_read_only_gateway_admin = READ_ONLY_ADMIN_ROLE in roles


def admin_flags_middleware(get_response: GetResponse) -> Middleware:
    """Add 'is_gateway_admin' / 'is_read_only_gateway_admin' from the user's realm roles."""

    def middleware(request: AiravataRequest) -> HttpResponseBase:
        set_admin_flags_from_roles(request)
        return get_response(request)

    return middleware


# ---------------------------------------------------------------------------
# DRF-replacement auth middleware (session + Keycloak bearer token), wired into
# settings.MIDDLEWARE.
# ---------------------------------------------------------------------------


def request_data_middleware(get_response: GetResponse) -> Middleware:
    """Augment every request with ``request.data`` and ``request.query_params``.

    DRF supplied these on its ``Request`` wrapper; views/view_utils read them.
    ``request.data`` is the parsed JSON body when the content type is JSON, else
    the form POST dict, else an empty dict. ``request.query_params`` is
    ``request.GET``. Idempotent and safe for all paths (parse failures degrade to
    an empty dict).
    """

    def middleware(request: AiravataRequest) -> HttpResponseBase:
        request.query_params = request.GET

        content_type = (request.META.get("CONTENT_TYPE", "") or "").lower()
        if "application/json" in content_type:
            try:
                body = request.body
                request.data = json.loads(body) if body else {}
            except (ValueError, json.JSONDecodeError):
                request.data = {}
        elif request.method in ("POST", "PUT", "PATCH"):
            # form-encoded / multipart — Django parsed it into request.POST.
            request.data = request.POST.dict()
        else:
            request.data = {}

        return get_response(request)

    return middleware


def keycloak_token_user_middleware(get_response: GetResponse) -> Middleware:
    """Authenticate every request from a Keycloak access token (browser-OIDC).

    The token comes from either the ``Authorization: Bearer <jwt>`` header
    (token clients / the SDK) or the ``kc_token`` cookie (the browser PKCE flow
    sets this cookie from the access token returned by Keycloak). There is no
    Django session, no server-side OIDC redirect, and no Django-managed login —
    identity is derived purely from the verified JWT.

    Reuses ``token_authentication``'s ``_jwks`` / ``KeycloakUser``: the token is
    validated (RS256, ``verify_aud`` False) and, on success, ``request.user`` /
    ``request.authz_token`` are set (``admin_flags_middleware`` then derives the
    admin flags from realm roles). With no token, or an invalid one, the request
    is left Anonymous with ``request.authz_token = None`` (the permission/
    login_required layer then redirects to Keycloak or returns 401). An invalid
    token is logged at warning level; it does not raise.

    Must run before ``airavata_grpc_client`` (which reads ``request.authz_token``)
    and ``admin_flags_middleware`` (which reads ``request.user``).
    """
    import jwt

    from .token_authentication import KeycloakUser, _jwks

    def middleware(request: AiravataRequest) -> HttpResponseBase:
        request.user = AnonymousUser()
        request.authz_token = None

        header = request.META.get("HTTP_AUTHORIZATION", "")
        if header.startswith("Bearer "):
            token = header[len("Bearer ") :].strip()
        else:
            token = request.COOKIES.get("kc_token")

        if not token:
            return get_response(request)

        try:
            signing_key = _jwks().get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_aud": False},
            )
        except Exception as e:
            log.warning("Keycloak token validation failed: %s", e)
            return get_response(request)

        keycloak_user = KeycloakUser(claims)
        request.user = keycloak_user
        request.authz_token = utils.AuthzToken(accessToken=token)

        return get_response(request)

    return middleware
