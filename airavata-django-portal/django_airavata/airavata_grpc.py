"""gRPC Airavata client (airavata-python-sdk ``AiravataClient``).

Builds the gRPC ``AiravataClient`` (``request.airavata``) from a request's Keycloak
access token. The ``apps/api`` views/serializers talk to Airavata through this
client's facade sub-clients; the interim ``thrift_utils`` serializer layer (which
still reads Thrift model types) is removed in the later serializer/terminology pass.

Per the migration principle, the "talk to Airavata + transform" grunt belongs in
``airavata-python-sdk`` (the facade sub-clients on ``AiravataClient``), keeping the
portal a thin adapter.
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def build_airavata_client(access_token, gateway_id=None):
    """Build an :class:`AiravataClient` for the given Keycloak access token.

    The SDK is imported lazily so importing this module does not require the new
    SDK to be installed (it is provided on the path during the transition).
    """
    from airavata_sdk.client import AiravataClient

    gateway_id = gateway_id or settings.GATEWAY_ID
    return AiravataClient(
        host=settings.GRPC_API_HOST,
        port=settings.GRPC_API_PORT,
        token=access_token,
        gateway_id=gateway_id,
        secure=settings.GRPC_API_SECURE,
    )


def airavata_client_for_request(request):
    """Build an :class:`AiravataClient` from ``request.authz_token``.

    Returns ``None`` for unauthenticated requests (no ``authz_token``). The caller
    is responsible for closing the returned client.
    """
    authz_token = getattr(request, "authz_token", None)
    if authz_token is None:
        return None
    return build_airavata_client(authz_token.accessToken)
