import logging

import thrift
import thrift.transport.TTransport
from django.shortcuts import render

from . import utils

logger = logging.getLogger(__name__)


class AiravataClientMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        with utils.airavata_api_client_pool.connection() as airavata_client:
            request.airavata_client = airavata_client
            response = self.get_response(request)

        return response

    def process_exception(self, request, exception):
        if isinstance(exception, thrift.transport.TTransport.TTransportException):
            return render(
                request,
                'django_airavata/error_page.html',
                status=500,
                context={
                    'title': 'Airavata is down',
                    'text': """The Airavata API server is not reachable. Please try again."""})
        else:
            return None


def airavata_grpc_client(get_response):
    """Attach the new-stack gRPC ``AiravataClient`` as ``request.airavata``.

    Track D: additive — coexists with the legacy Thrift ``request.airavata_client``
    while ``apps/api`` views are repointed from Thrift to gRPC. ``request.airavata``
    is a lazy object: the client (and the ``airavata_sdk`` import) is built only
    when a view first accesses it, carrying the user's Keycloak token from
    ``request.authz_token``. The channel is closed after the response if it was
    used. Views that never touch ``request.airavata`` incur no cost and do not
    require the SDK to be importable.

    Usage in a view::

        experiments = request.airavata.research.get_user_experiments(
            gateway_id=settings.GATEWAY_ID, user_name=request.user.username)
    """
    from django.utils.functional import SimpleLazyObject, empty

    from .airavata_grpc import airavata_client_for_request

    def middleware(request):
        request.airavata = SimpleLazyObject(
            lambda: airavata_client_for_request(request))
        try:
            return get_response(request)
        finally:
            lazy = request.__dict__.get('airavata')
            if isinstance(lazy, SimpleLazyObject) and lazy._wrapped is not empty:
                client = lazy._wrapped
                if client is not None:
                    client.close()

    return middleware


def profile_service_client(get_response):
    """Open and close Profile Service client for each request.

    Usage:
        request.profile_service['group_manager'].getGroup(
            request.authz_token, groupId)
    """

    def middleware(request):
        request.profile_service = {
            'group_manager': utils.group_manager_client_pool,
            'iam_admin': utils.iamadmin_client_pool,
            'tenant_profile': utils.tenant_profile_client_pool,
            'user_profile': utils.user_profile_client_pool,
        }
        response = get_response(request)

        return response

    return middleware
