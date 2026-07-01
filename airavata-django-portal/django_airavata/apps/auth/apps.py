from __future__ import annotations

from typing import override

from django.apps import AppConfig


class AuthConfig(AppConfig):
    name = "django_airavata.apps.auth"
    label = "django_airavata_auth"

    @override
    def ready(self) -> None:
        from . import signals  # noqa
