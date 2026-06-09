import logging

logger = logging.getLogger(__name__)


def airavata_grpc_client(get_response):
    """Attach the gRPC ``AiravataClient`` as ``request.airavata``.

    ``request.airavata`` is a lazy object: the client (and the ``airavata_sdk``
    import) is built only when a view first accesses it, carrying the user's
    Keycloak token from ``request.authz_token``. The channel is closed after the
    response if it was used. Views that never touch ``request.airavata`` incur no
    cost and do not require the SDK to be importable.

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
