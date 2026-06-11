"""Django Airavata Auth Middleware."""
import json
import logging
import time

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.models import AnonymousUser

from . import utils

log = logging.getLogger(__name__)


def authz_token_middleware(get_response):
    """Automatically add the 'authz_token' to the request."""
    def middleware(request):

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


def _gateway_groups_dict(request):
    """Fetch the gateway's admin group ids via the gRPC compute facade."""
    gg = request.airavata.compute.get_gateway_groups()
    return {'adminsGroupId': gg.admins_group_id,
            'readOnlyAdminsGroupId': gg.read_only_admins_group_id,
            'defaultGatewayUsersGroupId': gg.default_gateway_users_group_id}


def set_admin_group_attributes(request, gateway_groups=None):
    """Set is_gateway_admin and is_read_only_gateway_admin request attrs."""
    if gateway_groups is None:
        gateway_groups = _gateway_groups_dict(request)
    admins_group_id = gateway_groups['adminsGroupId']
    read_only_admins_group_id = gateway_groups['readOnlyAdminsGroupId']
    group_memberships = request.airavata.sharing.gm_get_all_groups_user_belongs(
        request.user.username + "@" + settings.GATEWAY_ID)
    group_ids = [group.id for group in group_memberships]
    request.is_gateway_admin = admins_group_id in group_ids
    request.is_read_only_gateway_admin = read_only_admins_group_id in group_ids


def gateway_groups_middleware(get_response):
    """Add 'is_gateway_admin' and 'is_read_only_gateway_admin' to request."""
    def middleware(request):

        request.is_gateway_admin = False
        request.is_read_only_gateway_admin = False

        if not request.user.is_authenticated or not request.authz_token:
            return get_response(request)

        try:
            # Load the GatewayGroups and check if user is in the Admins and/or
            # Read Only Admins groups
            if not request.session.get('GATEWAY_GROUPS'):
                request.session['GATEWAY_GROUPS'] = _gateway_groups_dict(request)
            set_admin_group_attributes(request, gateway_groups=request.session.get("GATEWAY_GROUPS"))
        except Exception as e:
            log.warning("Failed to set is_gateway_admin, "
                        "is_read_only_gateway_admin for user", exc_info=e)

        return get_response(request)
    return middleware


# ---------------------------------------------------------------------------
# DRF-replacement middleware (Phase B). NOT wired into settings yet — defined
# here so the cutover can add them to MIDDLEWARE in one step.
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

        content_type = (request.META.get('CONTENT_TYPE', '') or '').lower()
        if 'application/json' in content_type:
            try:
                body = request.body
                request.data = json.loads(body) if body else {}
            except (ValueError, json.JSONDecodeError):
                request.data = {}
        elif request.method in ('POST', 'PUT', 'PATCH'):
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
            token, signing_key.key, algorithms=['RS256'],
            options={'verify_aud': False})

    def middleware(request):
        # If a prior middleware already authenticated the request, no-op.
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            return get_response(request)

        # This middleware replaces AuthenticationMiddleware, so it owns
        # request.user. Default to Anonymous; the token paths below upgrade it.
        request.user = AnonymousUser()

        if 'ACCESS_TOKEN' not in request.session:
            return get_response(request)

        now = time.time()
        access_token = request.session['ACCESS_TOKEN']
        access_expires_at = request.session.get('ACCESS_TOKEN_EXPIRES_AT', 0)
        refresh_expires_at = request.session.get('REFRESH_TOKEN_EXPIRES_AT', 0)

        try:
            if access_expires_at > now:
                claims = _decode(access_token)
                request.user = KeycloakUser(claims)
            elif ('REFRESH_TOKEN' in request.session and
                    refresh_expires_at > now):
                token = utils.refresh_access_token(request)
                if token is None:
                    request.session.flush()
                    return get_response(request)
                utils.store_token_in_session(request, token)
                claims = _decode(token['access_token'])
                request.user = KeycloakUser(claims)
            # else: token expired and no usable refresh token; leave Anonymous.
        except Exception as e:  # noqa: BLE001 - any failure is an auth failure
            log.warning("Failed to derive user from session token: %s", e)
            request.session.flush()

        return get_response(request)

    return middleware


def keycloak_bearer_middleware(get_response):
    """Authenticate ``Authorization: Bearer <jwt>`` requests against Keycloak.

    Mirrors ``token_authentication.KeycloakTokenAuthentication`` (reusing
    ``_jwks`` / ``KeycloakUser`` / ``AuthzToken``): if ``request.user`` is already
    authenticated (session) this is a no-op; elif a Bearer token is present it is
    validated and ``request.user`` / ``request.authz_token`` (+ the
    ``is_gateway_admin`` / ``is_read_only_gateway_admin`` defaults) are set; else
    the request is left Anonymous. An invalid token leaves the user Anonymous (no
    raise — the permission layer returns 401).

    NOT wired into settings yet.
    """
    import jwt

    from .token_authentication import KeycloakUser, _jwks

    def middleware(request):
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            return get_response(request)

        header = request.META.get('HTTP_AUTHORIZATION', '')
        if not header.startswith('Bearer '):
            return get_response(request)

        token = header[len('Bearer '):].strip()
        try:
            signing_key = _jwks().get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token, signing_key.key, algorithms=['RS256'],
                options={'verify_aud': False})
        except Exception as e:  # noqa: BLE001 - any failure is an auth failure
            log.warning("Keycloak bearer token validation failed: %s", e)
            request.user = AnonymousUser()
            return get_response(request)

        keycloak_user = KeycloakUser(claims)
        authz_token = utils.AuthzToken(
            accessToken=token,
            claimsMap={'gatewayID': settings.GATEWAY_ID,
                       'userName': keycloak_user.username})
        request.user = keycloak_user
        request.authz_token = authz_token
        # The session-based gateway_groups_middleware sets these; pure-token auth
        # skips it, so default to non-admin (matches KeycloakTokenAuthentication).
        request.is_gateway_admin = False
        request.is_read_only_gateway_admin = False

        return get_response(request)

    return middleware
