"""Bearer-authenticated raw gRPC channel for the portal.

Builds the per-request gRPC channel attached as ``request.airavata_channel``.
ViewSets build generated stubs directly from it (``ProjectServiceStub(channel)``)
and call them; the interceptor in ``airavata.auth`` injects the Keycloak token on
every call. There is no SDK facade client — the portal talks to the airavata
server through the raw generated stubs, all business logic living in the server.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    import grpc

    from django_airavata.request import AiravataRequest

logger = logging.getLogger(__name__)


def build_airavata_channel(access_token: str) -> grpc.Channel:
    """Build a Bearer-authenticated raw gRPC channel for ``access_token``.

    ViewSets build generated stubs directly from this channel
    (``ProjectServiceStub(channel)``) and call them; the interceptor in
    ``airavata.auth`` injects the token on every call.
    """
    from airavata.auth import authenticated_channel

    return authenticated_channel(
        settings.GRPC_API_HOST,
        settings.GRPC_API_PORT,
        access_token,
        secure=settings.GRPC_API_SECURE,
    )


def airavata_channel_for_request(request: AiravataRequest) -> grpc.Channel | None:
    """Build a Bearer-authenticated raw gRPC channel from ``request.authz_token``.

    Returns ``None`` for unauthenticated requests. The caller is responsible for
    closing the returned channel.
    """
    authz_token = getattr(request, "authz_token", None)
    if authz_token is None:
        return None
    return build_airavata_channel(authz_token.accessToken)
