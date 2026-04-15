import logging

from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import authentication, exceptions

from django_airavata.apps.auth import utils
from django_airavata.apps.auth.middleware import set_admin_group_attributes
from django_airavata.utils import create_airavata_client

logger = logging.getLogger(__name__)


class OAuthAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):

        if "HTTP_AUTHORIZATION" in request.META:
            try:
                user = authenticate(request=request)
                if user is None:
                    raise exceptions.AuthenticationFailed("Token failed to authenticate")
                _, token = request.META.get("HTTP_AUTHORIZATION").split()

                logger.debug(f"OAuthAuthentication authenticated user {user}")
                # Set request attributes that are normally set by middleware.
                # DRF authenticators run before AiravataClientMiddleware.__call__,
                # so request.airavata_client is not yet set here. Create one
                # defensively so set_admin_group_attributes can use it.
                request.authz_token = utils.get_authz_token(request, user=user, access_token=token)
                request.user = user
                if not hasattr(request, "airavata_client") or request.airavata_client is None:
                    request.airavata_client = create_airavata_client(
                        token, settings.GATEWAY_ID, user.username
                    )
                set_admin_group_attributes(request)
                return (user, token)
            except Exception as e:
                raise exceptions.AuthenticationFailed("Token failed to authenticate") from e
        else:
            return None
