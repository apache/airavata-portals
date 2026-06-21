"""Signal and receivers for the api app."""

from django.dispatch import Signal

# providing_args=["user", "groups", "request"]
user_added_to_group = Signal()
