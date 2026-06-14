"""Django Airavata Auth Middleware."""

import json
import logging
import time

from django.conf import settings

from . import utils
from .token_authentication import AnonymousUser

log = logging.getLogger(__name__)


def authz_token_middleware(get_response):
    """Automatically add the 'authz_token' to the request."""

    def middleware(request):

        authz_token = None
        if request.user.is_authenticated:
            authz_token = utils.get_authz_token(request)
            # If we can't construct an authz_token then need to re-login
            if authz_token is None:
                # no longer logged in with the IAM server: clear the session
                # (cache-backed, no DB) and drop back to anonymous
                request.session.flush()
                request.user = AnonymousUser()

        request.authz_token = authz_token

        return get_response(request)

    return middleware


# Keycloak realm roles that map to the coarse gateway-admin flags.
GATEWAY_ADMIN_ROLE = "admin-rw"
READ_ONLY_ADMIN_ROLE = "admin-ro"


def set_admin_flags_from_roles(request):
    """Set is_gateway_admin / is_read_only_gateway_admin from the JWT realm roles."""
    roles = set(getattr(request.user, "realm_roles", []) or [])
    request.is_gateway_admin = GATEWAY_ADMIN_ROLE in roles
    request.is_read_only_gateway_admin = READ_ONLY_ADMIN_ROLE in roles


def admin_flags_middleware(get_response):
    """Add 'is_gateway_admin' / 'is_read_only_gateway_admin' from the user's realm roles."""

    def middleware(request):
        set_admin_flags_from_roles(request)
        return get_response(request)

    return middleware


# ---------------------------------------------------------------------------
# DRF-replacement auth middleware (session + Keycloak bearer token), wired into
# settings.MIDDLEWARE.
# ---------------------------------------------------------------------------


def request_data_middleware(get_response):
    """Augment every request with ``request.data`` and ``request.query_params``.

    DRF supplied these on its ``Request`` wrapper; views/view_utils read them.
    ``request.data`` is the parsed JSON body when the content type is JSON, else
    the form POST dict, else an empty dict. ``request.query_params`` is
    ``request.GET``. Idempotent and safe for all paths (parse failures degrade to
    an empty dict).
    """

    def middleware(request):
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


def session_keycloak_user_middleware(get_response):
    """Derive ``request.user`` from the Keycloak access token in the session.

    Replaces ``AuthenticationMiddleware`` for the OIDC session flow: there is no
    DB ``User`` and no ``login()`` call, so identity comes from the verified JWT
    stored in the session by the OIDC callback. If the access token is expired
    but a valid refresh token is present, the token is refreshed in place. On any
    failure the session is flushed and the request is left Anonymous (the
    permission/login_required layer then redirects to Keycloak).

    Must run before ``authz_token_middleware`` so ``request.user`` is set when
    ``get_authz_token`` runs, and before ``keycloak_bearer_middleware`` (which
    no-ops when a session already authenticated the request).
    """
    import jwt

    from .token_authentication import KeycloakUser, _jwks

    def _decode(token):
        signing_key = _jwks().get_signing_key_from_jwt(token)
        return jwt.decode(
            token, signing_key.key, algorithms=["RS256"], options={"verify_aud": False}
        )

    def middleware(request):
        # If a prior middleware already authenticated the request, no-op.
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            return get_response(request)

        # This middleware replaces AuthenticationMiddleware, so it owns
        # request.user. Default to Anonymous; the token paths below upgrade it.
        request.user = AnonymousUser()

        if "ACCESS_TOKEN" not in request.session:
            return get_response(request)

        now = time.time()
        access_token = request.session["ACCESS_TOKEN"]
        access_expires_at = request.session.get("ACCESS_TOKEN_EXPIRES_AT", 0)
        refresh_expires_at = request.session.get("REFRESH_TOKEN_EXPIRES_AT", 0)

        try:
            if access_expires_at > now:
                claims = _decode(access_token)
                request.user = KeycloakUser(claims)
            elif "REFRESH_TOKEN" in request.session and refresh_expires_at > now:
                token = utils.refresh_access_token(request)
                if token is None:
                    request.session.flush()
                    return get_response(request)
                utils.store_token_in_session(request, token)
                claims = _decode(token["access_token"])
                request.user = KeycloakUser(claims)
            # else: token expired and no usable refresh token; leave Anonymous.
        except Exception as e:
            log.warning("Failed to derive user from session token: %s", e)
            request.session.flush()

        return get_response(request)

    return middleware


def keycloak_bearer_middleware(get_response):
    """Authenticate ``Authorization: Bearer <jwt>`` requests against Keycloak.

    Reuses ``token_authentication``'s ``_jwks`` / ``KeycloakUser`` / ``AuthzToken``:
    if ``request.user`` is already
    authenticated (session) this is a no-op; elif a Bearer token is present it is
    validated and ``request.user`` / ``request.authz_token`` are set (the
    ``admin_flags_middleware`` then derives the admin flags from realm roles); else
    the request is left Anonymous. An invalid token leaves the user Anonymous (no
    raise — the permission layer returns 401).
    """
    import jwt

    from .token_authentication import KeycloakUser, _jwks

    def middleware(request):
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            return get_response(request)

        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header.startswith("Bearer "):
            return get_response(request)

        token = header[len("Bearer ") :].strip()
        try:
            signing_key = _jwks().get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_aud": False},
            )
        except Exception as e:
            log.warning("Keycloak bearer token validation failed: %s", e)
            request.user = AnonymousUser()
            return get_response(request)

        keycloak_user = KeycloakUser(claims)
        authz_token = utils.AuthzToken(
            accessToken=token,
            claimsMap={
                "gatewayID": settings.GATEWAY_ID,
                "userName": keycloak_user.username,
            },
        )
        request.user = keycloak_user
        request.authz_token = authz_token

        return get_response(request)

    return middleware
