import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, cast

from django.http import HttpRequest, HttpResponse

if TYPE_CHECKING:
    from django_airavata.request import AiravataRequest

logger = logging.getLogger(__name__)


def airavata_grpc_client(
    get_response: Callable[[HttpRequest], HttpResponse],
) -> Callable[[HttpRequest], HttpResponse]:
    """Attach the Bearer-authenticated gRPC channel as ``request.airavata_channel``.

    It is a lazy object: the channel (and the ``airavata`` import) is built only
    when a view first accesses it, carrying the user's Keycloak token from
    ``request.authz_token``; it is closed after the response if it was used. Views
    that never touch it incur no cost. ViewSets build generated stubs directly::

        from airavata.services import experiment_service_pb2 as pb2
        from airavata.services.experiment_service_pb2_grpc import (
            ExperimentServiceStub,
        )

        experiments = ExperimentServiceStub(request.airavata_channel).GetUserExperiments(
            pb2.GetUserExperimentsRequest(
                gateway_id=settings.GATEWAY_ID, user_name=request.user.username)
        ).experiments
    """
    from django.utils.functional import SimpleLazyObject, empty

    from .airavata_grpc import airavata_channel_for_request

    def middleware(request: HttpRequest) -> HttpResponse:
        request.airavata_channel = SimpleLazyObject(  # ty: ignore[unresolved-attribute]  # middleware augments the request (see AiravataRequest)
            lambda: airavata_channel_for_request(cast("AiravataRequest", request))
        )
        try:
            return get_response(request)
        finally:
            channel_lazy = request.__dict__.get("airavata_channel")
            if (
                isinstance(channel_lazy, SimpleLazyObject)
                and channel_lazy._wrapped is not empty
            ):
                channel = channel_lazy._wrapped
                if channel is not None:
                    channel.close()

    return middleware
