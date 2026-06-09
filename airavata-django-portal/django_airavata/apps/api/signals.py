"""Signal and receivers for the api app."""

import logging

from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.dispatch import Signal, receiver

log = logging.getLogger(__name__)


# Signals
# providing_args=["user", "groups", "request"]
user_added_to_group = Signal()


# Receivers
@receiver(user_logged_in)
def create_user_storage_dir(sender, request, user, **kwargs):
    """Create user's home directory in gateway storage (gRPC storage facade)."""
    storage = request.airavata.storage
    if not storage.dir_exists("~/"):
        storage.create_dir("~/")
        log.info("Created home directory for user {}".format(user.username))

    if hasattr(settings, 'GATEWAY_DATA_SHARED_DIRECTORIES'):
        for name, entry in settings.GATEWAY_DATA_SHARED_DIRECTORIES.items():
            storage.create_symlink(entry['path'], "~/" + name)
