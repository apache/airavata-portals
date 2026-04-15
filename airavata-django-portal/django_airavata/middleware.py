import logging
from collections.abc import Callable
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .utils import create_airavata_client

logger = logging.getLogger(__name__)


class AiravataClientMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: Any) -> HttpResponse:
        # Bypass for the async SSE endpoint. The sync middleware would otherwise
        # force Django to run the async view via async_to_sync, which blocks the
        # single WSGI worker thread on the long-lived event stream and starves
        # all other requests. The SSE view does not use request.airavata_client.
        if request.path.startswith("/api/events"):
            return self.get_response(request)

        access_token = _get_access_token(request)
        gateway_id = settings.GATEWAY_ID
        username = request.user.username if request.user.is_authenticated else ""
        request.airavata_client = create_airavata_client(access_token, gateway_id, username)
        try:
            response = self.get_response(request)
        except Exception:
            logger.exception("Error during request processing")
            raise
        finally:
            request.airavata_client.close()
        return response

    def process_exception(self, request: HttpRequest, exception: Exception) -> HttpResponse | None:
        # Handle connection errors to the Airavata API server
        if isinstance(exception, ConnectionError):
            return render(
                request,
                "django_airavata/error_page.html",
                status=500,
                context={
                    "title": "Airavata is down",
                    "text": """The Airavata API server is not reachable. Please try again.""",
                },
            )
        return None


def _get_access_token(request: HttpRequest) -> str:
    """Extract access token from request auth or session."""
    if hasattr(request, "auth") and request.auth is not None:
        return str(request.auth)
    return request.session.get("ACCESS_TOKEN", "")
