"""Typed view of the portal's middleware-augmented ``HttpRequest``."""

from typing import TYPE_CHECKING, Any

from django.http import HttpRequest, QueryDict

if TYPE_CHECKING:
    import grpc

    from django_airavata.apps.auth.token_authentication import (
        AnonymousUser,
        KeycloakUser,
    )
    from django_airavata.apps.auth.utils import AuthzToken


class AiravataRequest(HttpRequest):
    """An ``HttpRequest`` after the portal middleware chain has run.

    The middlewares declared in ``settings.MIDDLEWARE`` attach these attributes:

    * ``user`` / ``authz_token`` — ``keycloak_token_user_middleware``
    * ``data`` / ``query_params`` — ``request_data_middleware``
    * ``airavata_channel`` — ``airavata_grpc_client`` (the Bearer-authenticated gRPC
      channel, built lazily, from which ViewSets construct generated stubs)
    * ``is_gateway_admin`` / ``is_read_only_gateway_admin`` — ``admin_flags_middleware``

    Views and viewsets annotate ``request: AiravataRequest`` to read them with
    full typing. This is a typing-only view: it is never instantiated — Django's
    real ``HttpRequest`` carries these attributes at runtime, and the middlewares
    are the (``# ty: ignore``-annotated) augmentation points.

    ``airavata_channel`` is typed as the non-optional channel because views run
    behind ``login_required`` / ``IsAuthenticated``; for an anonymous request the
    middleware leaves it ``None`` and the permission layer short-circuits first.
    """

    user: "KeycloakUser | AnonymousUser"
    authz_token: "AuthzToken | None"
    airavata_channel: "grpc.Channel"
    data: dict[str, Any]
    query_params: QueryDict
    is_gateway_admin: bool
    is_read_only_gateway_admin: bool
