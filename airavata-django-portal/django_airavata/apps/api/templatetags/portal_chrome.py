"""Template tags that render the portal app-shell ("chrome") from settings.

These source the favicon for ``base.html`` from ``settings.PORTAL_CHROME``. The
portal no longer ships a CMS; landing pages and other content are served by the
standalone airavata-cms service.
"""

from __future__ import annotations

from typing import Any

from django import template
from django.conf import settings

register = template.Library()


def _chrome() -> dict[str, Any]:
    return getattr(settings, "PORTAL_CHROME", {}) or {}


@register.inclusion_tag("portal_chrome/favicon.html")
def portal_favicon() -> dict[str, Any]:
    return {"favicon_url": _chrome().get("favicon_url")}
