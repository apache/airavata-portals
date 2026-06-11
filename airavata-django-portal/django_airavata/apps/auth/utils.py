"""Auth utilities."""

import logging
import os
import time

import requests
from django.conf import settings
from django.core.mail import EmailMessage
from django.http.request import split_domain_port
from django.template import Context, Template
from oauthlib.oauth2 import BackendApplicationClient, InvalidGrantError
from requests_oauthlib import OAuth2Session

from . import models

logger = logging.getLogger(__name__)


class AuthzToken:
    """Plain carrier for the Keycloak access token + gateway/user claims.

    Replaces the legacy Thrift ``AuthzToken`` value type; keeps the same
    ``accessToken`` / ``claimsMap`` attribute names so existing consumers (the
    gRPC client factory, IAM admin REST helpers, ...) are unchanged.
    """

    def __init__(self, accessToken, claimsMap=None):
        self.accessToken = accessToken
        self.claimsMap = claimsMap or {}


def get_authz_token(request, user=None, access_token=None):
    """Construct AuthzToken instance from session; refresh token if needed."""
    if access_token is not None:
        return _create_authz_token(request, user=user, access_token=access_token)
    elif is_request_access_token(request):
        return _create_authz_token(request, user=user)
    elif is_session_access_token(request) and not is_session_access_token_expired(request, user=user):
        return _create_authz_token(request, user=user, access_token=access_token)
    elif not is_refresh_token_expired(request):
        # Refresh the access token directly (no Django auth backend involved).
        token = refresh_access_token(request)
        if token:
            store_token_in_session(request, token)
            return _create_authz_token(
                request, user=user, access_token=token['access_token'])
    return None


def get_service_account_authz_token():
    client_id = settings.KEYCLOAK_CLIENT_ID
    client_secret = settings.KEYCLOAK_CLIENT_SECRET
    token_url = settings.KEYCLOAK_TOKEN_URL
    verify_ssl = settings.KEYCLOAK_VERIFY_SSL

    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)
    verify = verify_ssl
    if verify_ssl and hasattr(settings, 'KEYCLOAK_CA_CERTFILE'):
        verify = settings.KEYCLOAK_CA_CERTFILE
    token = oauth.fetch_token(
        token_url=token_url,
        client_id=client_id,
        client_secret=client_secret,
        verify=verify)

    access_token = token.get('access_token')
    return AuthzToken(
        accessToken=access_token,
        # This is a service account, so leaving out userName for now
        claimsMap={'gatewayID': settings.GATEWAY_ID})


def store_token_in_session(request, token):
    """Persist a Keycloak token dict into the session.

    Keeps the exact session keys the rest of the auth layer reads
    (``is_session_access_token_expired``, ``is_refresh_token_expired``,
    ``_get_access_token``, the desktop login views).
    """
    now = time.time()
    sess = request.session
    sess['ACCESS_TOKEN'] = token['access_token']
    sess['ACCESS_TOKEN_EXPIRES_AT'] = now + token['expires_in']
    sess['REFRESH_TOKEN'] = token['refresh_token']
    sess['REFRESH_TOKEN_EXPIRES_AT'] = now + token['refresh_expires_in']


def exchange_code_for_token(request):
    """Exchange the authorization code on the callback request for a token dict.

    Reads ``OAUTH2_STATE``/``OAUTH2_REDIRECT_URI`` (stashed by ``oidc_login``)
    from the session and completes the Authorization Code flow.
    """
    authorization_code_url = request.build_absolute_uri()
    client_id = settings.KEYCLOAK_CLIENT_ID
    client_secret = settings.KEYCLOAK_CLIENT_SECRET
    token_url = settings.KEYCLOAK_TOKEN_URL
    verify_ssl = settings.KEYCLOAK_VERIFY_SSL
    state = request.session['OAUTH2_STATE']
    redirect_uri = request.session['OAUTH2_REDIRECT_URI']
    oauth2_session = OAuth2Session(client_id,
                                   scope='openid profile email',
                                   redirect_uri=redirect_uri,
                                   state=state)
    verify = verify_ssl
    if verify_ssl and hasattr(settings, 'KEYCLOAK_CA_CERTFILE'):
        verify = settings.KEYCLOAK_CA_CERTFILE
    if not request.is_secure() and settings.DEBUG and not os.environ.get('OAUTHLIB_INSECURE_TRANSPORT'):
        # For local development (DEBUG=True), allow the insecure OAuth redirect
        # flow if OAUTHLIB_INSECURE_TRANSPORT isn't already set.
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"
        logger.info("Adding env var OAUTHLIB_INSECURE_TRANSPORT=1 to allow "
                    "OAuth redirect flow even though request is not secure")
    return oauth2_session.fetch_token(
        token_url, client_secret=client_secret,
        authorization_response=authorization_code_url, verify=verify)


def refresh_access_token(request, refresh_token=None):
    """Refresh the access token via the refresh-token grant.

    Returns the new token dict, or ``None`` if the refresh token is no longer
    valid (e.g. session terminated by an admin or by logout elsewhere).
    """
    client_id = settings.KEYCLOAK_CLIENT_ID
    client_secret = settings.KEYCLOAK_CLIENT_SECRET
    token_url = settings.KEYCLOAK_TOKEN_URL
    verify_ssl = settings.KEYCLOAK_VERIFY_SSL
    oauth2_session = OAuth2Session(client_id, scope='openid profile email')
    verify = verify_ssl
    if verify_ssl and hasattr(settings, 'KEYCLOAK_CA_CERTFILE'):
        verify = settings.KEYCLOAK_CA_CERTFILE
    refresh_token_ = (refresh_token
                      if refresh_token is not None
                      else request.session['REFRESH_TOKEN'])
    # refresh_token doesn't take a client_secret kwarg, so build auth explicitly
    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    try:
        return oauth2_session.refresh_token(token_url=token_url,
                                            refresh_token=refresh_token_,
                                            auth=auth,
                                            verify=verify)
    except InvalidGrantError as e:
        logger.warning("Failed to refresh token: %s", e)
        return None


def _create_authz_token(request, user=None, access_token=None):
    if access_token is None:
        access_token = _get_access_token(request)
    if user is None:
        user = request.user
    username = user.username
    gateway_id = settings.GATEWAY_ID
    return AuthzToken(accessToken=access_token,
                      claimsMap={'gatewayID': gateway_id,
                                 'userName': username})


def _get_access_token_source(request):
    if hasattr(request, 'auth') and request.auth is not None:
        return 'request'
    elif 'ACCESS_TOKEN' in request.session:
        return 'session'
    else:
        return None


def _get_access_token(request):
    source = _get_access_token_source(request)
    if source == 'request':
        return request.auth
    elif source == 'session':
        return request.session['ACCESS_TOKEN']
    else:
        return None


def is_session_access_token(request):
    """Return True if access token is stored in the user's session."""
    return _get_access_token_source(request) == 'session'


def is_request_access_token(request):
    """Return True if access token passed in request, e.g., a Bearer token."""
    return _get_access_token_source(request) == 'request'


def is_session_access_token_expired(request, user=None):
    """Return True if session access_token is not available or is expired."""
    user = user if user is not None else request.user
    now = time.time()
    return not user.is_authenticated \
        or 'ACCESS_TOKEN' not in request.session \
        or 'ACCESS_TOKEN_EXPIRES_AT' not in request.session \
        or request.session['ACCESS_TOKEN_EXPIRES_AT'] < now


def is_refresh_token_expired(request):
    """Return True if refresh_token is not available or is expired."""
    now = time.time()
    return 'REFRESH_TOKEN' not in request.session \
        or 'REFRESH_TOKEN_EXPIRES_AT' not in request.session \
        or request.session['REFRESH_TOKEN_EXPIRES_AT'] < now


def send_new_user_email(request, username, email, first_name, last_name):
    """Send new user email notification to portal admins."""
    new_user_email_template = models.EmailTemplate.objects.get(
        pk=models.NEW_USER_EMAIL_TEMPLATE)
    domain, port = split_domain_port(request.get_host())
    context = Context({
        "username": username,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "portal_title": settings.PORTAL_TITLE,
        "gateway_id": settings.GATEWAY_ID,
        "http_host": domain,
    })
    subject = Template(new_user_email_template.subject).render(context)
    body = Template(new_user_email_template.body).render(context)
    send_email_to_admins(subject, body)


def send_email_to_admins(subject, body):
    msg = EmailMessage(subject=subject,
                       body=body,
                       from_email=f'"{settings.PORTAL_TITLE}" <{settings.SERVER_EMAIL}>',
                       to=[f'"{a[0]}" <{a[1]}>' for a in getattr(settings,
                                                                 'PORTAL_ADMINS',
                                                                 settings.ADMINS)])
    msg.content_subtype = 'html'
    msg.send()


def send_email_to_user(template_id, context):
    email_template = models.EmailTemplate.objects.get(pk=template_id)
    subject = Template(email_template.subject).render(context)
    body = Template(email_template.body).render(context)
    msg = EmailMessage(
        subject=subject,
        body=body,
        from_email="\"{}\" <{}>".format(settings.PORTAL_TITLE,
                                        settings.SERVER_EMAIL),
        to=["\"{} {}\" <{}>".format(context['first_name'],
                                    context['last_name'],
                                    context['email'])],
        reply_to=[f"\"{a[0]}\" <{a[1]}>" for a in getattr(settings,
                                                          'PORTAL_ADMINS',
                                                          settings.ADMINS)]
    )
    msg.content_subtype = 'html'
    msg.send()
