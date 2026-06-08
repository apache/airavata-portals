"""Template tags that render the portal app-shell ("chrome") from settings.

These source the favicon, header logo, title, and user-menu links for
``base.html`` from ``settings.PORTAL_CHROME`` / ``settings.PORTAL_TITLE``. The
portal no longer ships a CMS; landing pages and other content are served by the
standalone airavata-cms service.
"""

from django import template
from django.conf import settings

register = template.Library()


def _chrome():
    return getattr(settings, "PORTAL_CHROME", {}) or {}


@register.inclusion_tag("portal_chrome/favicon.html")
def portal_favicon():
    return {"favicon_url": _chrome().get("favicon_url")}


@register.inclusion_tag("portal_chrome/logo.html")
def portal_logo():
    chrome = _chrome()
    return {
        "logo_url": chrome.get("logo_url"),
        "logo_background_color": chrome.get("logo_background_color"),
    }


@register.simple_tag
def portal_title():
    return _chrome().get("title") or getattr(settings, "PORTAL_TITLE", "")


@register.inclusion_tag("portal_chrome/main_menu.html")
def portal_main_menu():
    return {"user_menu_links": _chrome().get("user_menu_links") or []}
