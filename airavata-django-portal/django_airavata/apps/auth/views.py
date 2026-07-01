from __future__ import annotations

import logging
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Browser-OIDC views (Authorization Code + PKCE against the Keycloak PUBLIC
# client). There is no server-side OIDC redirect and no Django-managed session:
# the browser runs the PKCE flow, the code-for-token exchange happens
# client-side in the callback template, and the raw access token is stored in
# the ``kc_token`` cookie. Django only VALIDATES that token
# (``keycloak_token_user_middleware``).
# ---------------------------------------------------------------------------


def oidc_login(request: HttpRequest) -> HttpResponse:
    """Render the browser-PKCE initiation page.

    The template (``django_airavata_auth/login.html``) generates the PKCE
    verifier/challenge and CSRF state in the browser, stashes them in
    sessionStorage (``kc_pkce_verifier`` / ``kc_oauth_state``) along with the
    post-login destination (``kc_post_login_redirect``), then redirects to
    Keycloak's authorization endpoint with the public client id and S256
    challenge.
    """
    redirect_uri = request.build_absolute_uri(reverse("django_airavata_auth:callback"))
    context = {
        "authorize_url": settings.KEYCLOAK_AUTHORIZE_URL,
        "client_id": settings.KEYCLOAK_PUBLIC_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": "openid profile email",
        "next": request.GET.get("next", "/"),
    }
    return render(request, "django_airavata_auth/login.html", context)


def oidc_callback(request: HttpRequest) -> HttpResponse:
    """Render the redirect_uri page that exchanges the code client-side.

    The template (``django_airavata_auth/callback.html``) reads the ``code`` and
    ``state`` query params, validates ``state`` against the sessionStorage
    ``kc_oauth_state``, POSTs the authorization-code grant to Keycloak's token
    endpoint (public client + PKCE ``code_verifier`` from
    ``kc_pkce_verifier``), sets the ``kc_token`` cookie from the returned
    access token, then redirects to ``kc_post_login_redirect``.
    """
    redirect_uri = request.build_absolute_uri(reverse("django_airavata_auth:callback"))
    context = {
        "token_url": settings.KEYCLOAK_TOKEN_URL,
        "client_id": settings.KEYCLOAK_PUBLIC_CLIENT_ID,
        "redirect_uri": redirect_uri,
    }
    return render(request, "django_airavata_auth/callback.html", context)


def logout(request: HttpRequest) -> HttpResponseRedirect:
    """Clear the ``kc_token`` cookie and log out at Keycloak (single logout)."""
    post_logout_redirect_uri = request.build_absolute_uri("/")
    logout_url = (
        settings.KEYCLOAK_LOGOUT_URL
        + "?"
        + urlencode(
            {
                "client_id": settings.KEYCLOAK_PUBLIC_CLIENT_ID,
                "post_logout_redirect_uri": post_logout_redirect_uri,
            }
        )
    )
    response = redirect(logout_url)
    response.delete_cookie("kc_token", path="/", samesite="Lax")
    return response


def logged_out(request: HttpRequest) -> HttpResponse:
    """Public landing page shown after a federated Keycloak logout."""
    return render(request, "django_airavata_auth/logged_out.html")
