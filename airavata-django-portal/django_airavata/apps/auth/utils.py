"""Auth utilities."""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.template import Context, Template
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

logger = logging.getLogger(__name__)


class AuthzToken:
    """Plain carrier for the Keycloak access token.

    Replaces the legacy Thrift ``AuthzToken`` value type; keeps the
    ``accessToken`` attribute name so existing consumers (the gRPC client
    factory, IAM admin REST helpers, ...) are unchanged.
    """

    def __init__(self, accessToken: str | None) -> None:
        self.accessToken = accessToken


def get_service_account_authz_token() -> AuthzToken:
    client_id = settings.KEYCLOAK_CLIENT_ID
    client_secret = settings.KEYCLOAK_CLIENT_SECRET
    token_url = settings.KEYCLOAK_TOKEN_URL
    verify_ssl = settings.KEYCLOAK_VERIFY_SSL

    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)
    verify = verify_ssl
    if verify_ssl and hasattr(settings, "KEYCLOAK_CA_CERTFILE"):
        verify = settings.KEYCLOAK_CA_CERTFILE
    token = oauth.fetch_token(
        token_url=token_url,
        client_id=client_id,
        client_secret=client_secret,
        verify=verify,
    )

    access_token = token.get("access_token")
    return AuthzToken(accessToken=access_token)


def send_email_to_user(template_id: int, context: Context) -> None:
    email_template = settings.PORTAL_EMAIL_TEMPLATES[template_id]
    subject = Template(email_template["subject"]).render(context)
    body = Template(email_template["body"]).render(context)
    msg = EmailMessage(
        subject=subject,
        body=body,
        from_email=f'"{settings.PORTAL_TITLE}" <{settings.SERVER_EMAIL}>',
        to=[
            '"{} {}" <{}>'.format(
                context["first_name"], context["last_name"], context["email"]
            )
        ],
        reply_to=[
            f'"{a[0]}" <{a[1]}>'
            for a in getattr(settings, "PORTAL_ADMINS", settings.ADMINS)
        ],
    )
    msg.content_subtype = "html"
    msg.send()
