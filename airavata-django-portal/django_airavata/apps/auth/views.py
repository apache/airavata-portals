import io
import logging
import time
from urllib.parse import quote, urlencode, urlparse

import requests
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import (
    FileResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse

from . import utils
from .decorators import login_required

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Browser-OIDC views (Authorization Code + PKCE against the Keycloak PUBLIC
# client). There is no server-side OIDC redirect and no Django-managed session:
# the browser runs the PKCE flow, the code-for-token exchange happens
# client-side in the callback template, and the raw access token is stored in
# the ``kc_token`` cookie. Django only VALIDATES that token
# (``keycloak_token_user_middleware``).
# ---------------------------------------------------------------------------


def oidc_login(request):
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
        "token_url": settings.KEYCLOAK_TOKEN_URL,
        "client_id": settings.KEYCLOAK_PUBLIC_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": "openid profile email",
        "next": request.GET.get("next", "/"),
    }
    return render(request, "django_airavata_auth/login.html", context)


def oidc_callback(request):
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


def logout(request):
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


def logged_out(request):
    """Public landing page shown after a federated Keycloak logout."""
    return render(request, "django_airavata_auth/logged_out.html")


def login_desktop(request):
    context = {"options": settings.AUTHENTICATION_OPTIONS, "login_desktop": True}
    if "username" in request.GET:
        context["username"] = request.GET["username"]
    download_code = request.GET.get("download-code", "false") == "true"
    show_code = request.GET.get("show-code", "false") == "true"
    context["download_code"] = download_code
    context["show_code"] = show_code
    return render(request, "django_airavata_auth/login-desktop.html", context)


def login_desktop_success(request):
    download_code = request.GET.get("download-code", "false") == "true"
    show_code = request.GET.get("show-code", "false") == "true"

    access_token = request.session["ACCESS_TOKEN"]
    if download_code:
        access_token_bytesio = io.BytesIO(access_token.encode())
        return FileResponse(
            access_token_bytesio, as_attachment=True, filename="access_token.txt"
        )
    else:
        context = (
            {
                "show_code": show_code,
                "code": access_token,
            }
            if (show_code)
            else {}
        )
        return render(
            request, "django_airavata_auth/login-desktop-success.html", context
        )


def refreshed_token_desktop(request):
    refresh_code = request.GET["refresh_code"]
    token = utils.refresh_access_token(request, refresh_token=refresh_code)
    if token is not None:
        utils.store_token_in_session(request, token)
        valid_time = int(request.session["ACCESS_TOKEN_EXPIRES_AT"] - time.time())
        return JsonResponse(
            {
                "status": "ok",
                "code": request.session["ACCESS_TOKEN"],
                "refresh_code": request.session["REFRESH_TOKEN"],
                "valid_time": valid_time,
            }
        )
    else:
        return JsonResponse(
            {
                "status": "failed",
            }
        )


def _create_login_desktop_success_response(
    request, download_code=False, show_code=False
):
    valid_time = int(request.session["ACCESS_TOKEN_EXPIRES_AT"] - time.time())
    query_params = {
        "status": "ok",
        "code": request.session["ACCESS_TOKEN"],
        "refresh_code": request.session["REFRESH_TOKEN"],
        "valid_time": valid_time,
        "username": request.user.username,
    }
    if download_code:
        query_params["download-code"] = "true"
    if show_code:
        query_params["show-code"] = "true"
    return redirect(
        reverse("django_airavata_auth:login_desktop_success")
        + "?"
        + urlencode(query_params)
    )


def _create_login_desktop_failed_response(request):
    params = {"status": "failed"}
    return redirect(
        reverse("django_airavata_auth:login_desktop") + "?" + urlencode(params)
    )


@login_required
def access_token_redirect(request):
    redirect_uri = request.GET["redirect_uri"]
    config = next(
        filter(
            lambda d: d.get("URI") == redirect_uri,
            settings.ACCESS_TOKEN_REDIRECT_ALLOWED_URIS,
        ),
        None,
    )
    if config is None:
        logger.warning(
            f"redirect_uri value '{redirect_uri}' is not configured "
            "in ACCESS_TOKEN_REDIRECT_ALLOWED_URIS setting"
        )
        return HttpResponseForbidden("Invalid redirect_uri value")
    return redirect(
        redirect_uri
        + f"{'&' if '?' in redirect_uri else '?'}{config.get('PARAM_NAME', 'access_token')}="
        f"{quote(request.authz_token.accessToken)}"
    )


@login_required
def download_settings_local(request):

    if not (request.is_gateway_admin or request.is_read_only_gateway_admin):
        raise PermissionDenied()

    if settings.DEBUG:
        return HttpResponseBadRequest(
            "Downloading a settings_local.py file isn't allowed in DEBUG mode."
        )

    development_client_id = f"local-django-{request.user.username}"
    access_token = utils.get_service_account_authz_token().accessToken
    clients_endpoint = get_clients_endpoint()
    development_client = get_client(
        access_token, clients_endpoint, development_client_id
    )
    if development_client is None:
        development_client_endpoint = create_client(
            access_token, clients_endpoint, development_client_id
        )
    else:
        development_client_endpoint = get_client_endpoint(development_client)
    development_client_secret = get_client_secret(
        access_token, development_client_endpoint
    )

    context = {}
    context["AUTHENTICATION_OPTIONS"] = settings.AUTHENTICATION_OPTIONS
    context["keycloak_client_id"] = development_client_id
    context["keycloak_client_secret"] = development_client_secret
    context["KEYCLOAK_AUTHORIZE_URL"] = settings.KEYCLOAK_AUTHORIZE_URL
    context["KEYCLOAK_TOKEN_URL"] = settings.KEYCLOAK_TOKEN_URL
    context["KEYCLOAK_USERINFO_URL"] = settings.KEYCLOAK_USERINFO_URL
    context["KEYCLOAK_LOGOUT_URL"] = settings.KEYCLOAK_LOGOUT_URL
    context["GATEWAY_ID"] = settings.GATEWAY_ID
    context["AIRAVATA_API_HOST"] = settings.AIRAVATA_API_HOST
    context["AIRAVATA_API_PORT"] = settings.AIRAVATA_API_PORT
    context["AIRAVATA_API_SECURE"] = settings.AIRAVATA_API_SECURE
    if hasattr(settings, "GATEWAY_DATA_STORE_REMOTE_API"):
        context["GATEWAY_DATA_STORE_REMOTE_API"] = (
            settings.GATEWAY_DATA_STORE_REMOTE_API
        )
    else:
        context["GATEWAY_DATA_STORE_REMOTE_API"] = request.build_absolute_uri("/")
    context["PROFILE_SERVICE_HOST"] = settings.PROFILE_SERVICE_HOST
    context["PROFILE_SERVICE_PORT"] = settings.PROFILE_SERVICE_PORT
    context["PROFILE_SERVICE_SECURE"] = settings.PROFILE_SERVICE_SECURE
    context["PORTAL_TITLE"] = settings.PORTAL_TITLE
    settings_local_str = render_to_string(
        "django_airavata_auth/settings_local.py.template", context
    )
    settings_local_bytesio = io.BytesIO(settings_local_str.encode())
    return FileResponse(
        settings_local_bytesio, as_attachment=True, filename="settings_local.py"
    )


def get_client(access_token, clients_endpoint, client_id):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    r = requests.get(clients_endpoint, {"clientId": client_id}, headers=headers)
    r.raise_for_status()
    clients = r.json()
    if len(clients) == 0:
        return None
    else:
        return clients[0]


def get_clients_endpoint():
    realm = settings.GATEWAY_ID
    parse_result = urlparse(settings.KEYCLOAK_AUTHORIZE_URL)
    clients_endpoint = f"{parse_result.scheme}://{parse_result.netloc}/auth/admin/realms/{realm}/clients"
    return clients_endpoint


def get_client_endpoint(client):
    return f"{get_clients_endpoint()}/{client['id']}"


def create_client(access_token, clients_endpoint, client_id):
    client = {
        "clientId": client_id,
        "redirectUris": [
            "http://localhost:8000/",
            "http://localhost:8000/auth/callback*",
            "http://127.0.0.1:8000/",
            "http://127.0.0.1:8000/auth/callback*",
        ],
        "directAccessGrantsEnabled": True,
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    r = requests.post(clients_endpoint, json=client, headers=headers)
    r.raise_for_status()
    return r.headers["Location"]


def get_client_secret(access_token, client_endpoint):

    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(client_endpoint + "/client-secret", headers=headers)
    r.raise_for_status()
    return r.json()["value"]
