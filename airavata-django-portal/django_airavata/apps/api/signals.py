"""Signal and receivers for the api app."""

import logging

from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.dispatch import Signal, receiver

from django_airavata.apps.api import user_storage
from django_airavata.utils import create_airavata_client

log = logging.getLogger(__name__)


# Signals
# providing_args=["user", "groups", "request"]
user_added_to_group = Signal()


# Receivers
@receiver(user_logged_in)
def create_user_storage_dir(sender, request, user, **kwargs):
    """Create user's home direct in gateway storage."""
    # AiravataClientMiddleware builds request.airavata_client from the token in
    # the session at the start of the request. The login callback's authenticate()
    # call writes ACCESS_TOKEN to the session only after the middleware has already
    # snapshotted, so request.airavata_client at this point has no credentials and
    # Airavata returns "Missing authorization metadata". Rebuild with the fresh
    # session token before making storage calls.
    access_token = request.session.get("ACCESS_TOKEN", "")
    if not access_token:
        log.debug("No access token in session yet; skipping user storage provisioning")
        return
    if hasattr(request, "airavata_client"):
        try:
            request.airavata_client.close()
        except Exception:
            pass
    request.airavata_client = create_airavata_client(access_token, settings.GATEWAY_ID, user.username)

    try:
        path = ""
        if not user_storage.dir_exists(request, path):
            user_storage.create_user_dir(request, path)
            log.info(f"Created home directory for user {user.username}")

        if hasattr(settings, "GATEWAY_DATA_SHARED_DIRECTORIES"):
            for name, entry in settings.GATEWAY_DATA_SHARED_DIRECTORIES.items():
                user_storage.create_symlink(request, entry["path"], name)
    except Exception:
        log.warning("create_user_storage_dir failed (storage RPC may be unimplemented); skipping", exc_info=True)
