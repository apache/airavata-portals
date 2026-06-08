"""New-stack gRPC Airavata client (airavata-python-sdk ``AiravataClient``).

Track D: the portal is migrating from the legacy Thrift API to the new Airavata
gRPC/REST server. This module builds the gRPC ``AiravataClient`` from a request's
Keycloak access token. It is intentionally additive — the gRPC client
(``request.airavata``) coexists with the legacy Thrift client
(``request.airavata_client``) while ``apps/api`` views are repointed resource
family by resource family. The Thrift client and ``thrift_utils`` are removed once
nothing depends on them.

Per the migration principle, the "talk to Airavata + transform" grunt belongs in
``airavata-python-sdk`` (the facade sub-clients on ``AiravataClient``), keeping the
portal a thin adapter.
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def build_airavata_client(access_token, gateway_id=None, claims=None):
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
        claims=claims,
    )


def airavata_client_for_request(request):
    """Build an :class:`AiravataClient` from ``request.authz_token``.

    Returns ``None`` for unauthenticated requests (no ``authz_token``). The caller
    is responsible for closing the returned client.
    """
    authz_token = getattr(request, "authz_token", None)
    if authz_token is None:
        return None
    claims = dict(authz_token.claimsMap) if authz_token.claimsMap else None
    return build_airavata_client(authz_token.accessToken, claims=claims)
