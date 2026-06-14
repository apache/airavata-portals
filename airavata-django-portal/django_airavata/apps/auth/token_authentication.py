"""Pure Keycloak token validation primitives.

Track D: the portal expects a valid Keycloak access token and validates it
against the realm's JWKS — there is no separate Django auth layer (no login flow,
no session-stored tokens, no DB ``User``). Identity is derived from the verified
JWT claims, and ``request.authz_token`` is built directly from the token so the
gRPC facade (``request.airavata``) carries it.

``keycloak_bearer_middleware`` (``apps/auth/middleware.py``) consumes the
``_jwks`` JWKS client and the :class:`KeycloakUser` claims wrapper defined here.
"""

import logging
import ssl

import jwt
from django.conf import settings

logger = logging.getLogger(__name__)

_jwks_client = None


def _jwks():
    """Lazily build a cached PyJWKClient for the realm's signing keys."""
    global _jwks_client
    if _jwks_client is None:
        certs_url = settings.KEYCLOAK_TOKEN_URL.rsplit("/", 1)[0] + "/certs"
        ssl_context = None
        if not getattr(settings, "KEYCLOAK_VERIFY_SSL", True):
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
        self.username = claims.get("preferred_username") or claims.get("sub")
        self.email = claims.get("email", "")
        self.first_name = claims.get("given_name", "")
        self.last_name = claims.get("family_name", "")

    def __str__(self):
        return self.username or "<anonymous>"

    @property
    def realm_roles(self):
        return (self.claims.get("realm_access") or {}).get("roles") or []

    @property
    def is_staff(self):
        return False


class AnonymousUser:
    """Non-DB anonymous user.

    Replaces ``django.contrib.auth.models.AnonymousUser``, which cannot be
    imported once ``django.contrib.auth`` is removed from ``INSTALLED_APPS``
    (importing that module instantiates the auth model classes). Exposes the
    minimal surface the middleware, ``login_required``, and templates rely on.
    """

    is_authenticated = False
    is_anonymous = True
    is_active = False
    is_staff = False
    username = ""

    def __str__(self):
        return "AnonymousUser"

    def has_perm(self, perm, obj=None):
        return False

    def has_module_perms(self, app_label):
        return False
