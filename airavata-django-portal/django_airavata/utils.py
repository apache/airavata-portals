import logging

from django.conf import settings

from airavata_sdk import AiravataClient

log = logging.getLogger(__name__)


def create_airavata_client(access_token, gateway_id):
    """Create an AiravataClient instance for the given auth token."""
    return AiravataClient(
        host=settings.AIRAVATA_API_HOST,
        port=settings.AIRAVATA_API_PORT,
        token=access_token,
        gateway_id=gateway_id,
        secure=getattr(settings, 'AIRAVATA_API_SECURE', False),
    )
