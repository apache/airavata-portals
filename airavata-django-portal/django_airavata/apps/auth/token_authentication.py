"""Pure Keycloak token authentication.

Track D: the portal expects a valid Keycloak access token and validates it
against the realm's JWKS — there is no separate Django auth layer (no login flow,
no session-stored tokens, no DB ``User``). Identity is derived from the verified
JWT claims, and ``request.authz_token`` is built directly from the token so both
the gRPC facade (``request.airavata``) and the still-Thrift calls carry it.
"""

import logging
import ssl

import jwt
from django.conf import settings
from rest_framework import authentication, exceptions

from .utils import AuthzToken

logger = logging.getLogger(__name__)

_jwks_client = None


def _jwks():
    """Lazily build a cached PyJWKClient for the realm's signing keys."""
    global _jwks_client
    if _jwks_client is None:
        certs_url = settings.KEYCLOAK_TOKEN_URL.rsplit('/', 1)[0] + '/certs'
        ssl_context = None
        if not getattr(settings, 'KEYCLOAK_VERIFY_SSL', True):
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        _jwks_client = jwt.PyJWKClient(certs_url, ssl_context=ssl_context)
    return _jwks_client


class KeycloakUser:
    """Lightweight, non-DB authenticated user derived from a Keycloak token."""

    is_authenticated = True
    is_anonymous = False
    is_active = True

    def __init__(self, claims):
        self.claims = claims
        self.username = claims.get('preferred_username') or claims.get('sub')
        self.email = claims.get('email', '')
        self.first_name = claims.get('given_name', '')
        self.last_name = claims.get('family_name', '')

    def __str__(self):
        return self.username or '<anonymous>'

    @property
    def is_staff(self):
        return False


class KeycloakTokenAuthentication(authentication.BaseAuthentication):
    """Validate a Keycloak Bearer token; no session, no DB user.

    On success sets ``request.authz_token`` (Keycloak access token + gateway/user
    claims) so downstream gRPC/Thrift calls are authenticated.
    """

    def authenticate(self, request):
        header = request.META.get('HTTP_AUTHORIZATION', '')
        if header.startswith('Bearer '):
            token = header[len('Bearer '):].strip()
            bearer = True
        else:
            # Browser bridge: the session login flow stores the Keycloak access
            # token in the session; use it when no Authorization header is sent
            # so the existing browser session authenticates against the
            # token-only API. (Final state: the frontend sends the token as a
            # Bearer header and the session login is removed.)
            bearer = False
            session = getattr(request, 'session', None)
            token = session.get('ACCESS_TOKEN') if session is not None else None
            if not token:
                return None
        try:
            signing_key = _jwks().get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token, signing_key.key, algorithms=['RS256'],
                options={'verify_aud': False})
        except Exception as e:  # noqa: BLE001 - any failure is an auth failure
            logger.warning("Keycloak token validation failed: %s", e)
            raise exceptions.AuthenticationFailed("Invalid or expired token")

        # Browser-session bridge: when the token comes from the session (no
        # Bearer header), the Django session login already established a
        # DB-backed user that the user/profile views depend on
        # (``request.user.id``, ``request.user.user_profile``). Reuse it. A pure
        # Bearer request (API/desktop client) has no session user, so derive a
        # lightweight non-DB user straight from the verified token claims.
        session_user = None
        if hasattr(request, '_request'):
            session_user = getattr(request._request, 'user', None)
        if not bearer and session_user is not None and session_user.is_authenticated:
            user = session_user
        else:
            user = KeycloakUser(claims)
        authz_token = AuthzToken(
            accessToken=token,
            claimsMap={'gatewayID': settings.GATEWAY_ID,
                       'userName': user.username})
        # Set on both the DRF Request and the underlying HttpRequest: middleware
        # (e.g. the lazy gRPC client builder) closes over the HttpRequest, while
        # views/serializers read it through the DRF Request wrapper.
        request.authz_token = authz_token
        if hasattr(request, '_request'):
            request._request.authz_token = authz_token
            request._request.user = user
        # Several serializers read request.is_gateway_admin (it was set by the
        # session-based gateway_groups_middleware, which pure-token auth skips).
        # Default to non-admin so those serializers don't crash. TODO (D5): derive
        # real admin status from gRPC — compute.get_gateway_groups() +
        # sharing.gm_get_all_groups_user_belongs(username) — once there is an admin
        # gateway user to validate the group/field shapes against, and cache it.
        request.is_gateway_admin = False
        request.is_read_only_gateway_admin = False
        if hasattr(request, '_request'):
            request._request.is_gateway_admin = False
            request._request.is_read_only_gateway_admin = False
        return (user, token)

    def authenticate_header(self, request):
        return 'Bearer'
