from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING, Any

from django.apps import AppConfig

if TYPE_CHECKING:
    from collections.abc import Callable

    from django_airavata.request import AiravataRequest

logger = logging.getLogger(__name__)


class AiravataAppConfig(AppConfig, ABC):
    """Custom AppConfig for Django Airavata apps."""

    # Declaration-only (no class-body default): subclasses set ``nav`` and
    # ``enabled`` when they expose them, and the registries probe both with
    # ``hasattr`` / ``getattr(..., None)``. Annotating here keeps that runtime
    # probing intact while giving the registries precise types.
    nav: list[dict[str, Any]]
    enabled: Callable[[AiravataRequest], bool]

    @property
    def url_app_name(self) -> str | None:
        """Return the urls application namespace."""
        return get_url_app_name(self)

    @property
    @abstractmethod
    def app_order(self) -> int:
        """Return positive int order of app in listings, lowest sorts first."""
        pass

    @property
    @abstractmethod
    def url_home(self) -> str:
        """Named route of home page for this application."""
        pass

    @property
    @abstractmethod
    def fa_icon_class(self) -> str:
        """Font Awesome icon class name."""
        pass

    @property
    @abstractmethod
    def app_description(self) -> str:
        """Some user friendly text to briefly describe the application."""
        pass


def get_url_app_name(app_config: AppConfig) -> str | None:
    """Return the urls namespace for the given AppConfig instance."""
    urls = get_app_urls(app_config)
    return getattr(urls, "app_name", None)


def get_app_urls(app_config: AppConfig) -> ModuleType:
    return import_module(".urls", app_config.name)
