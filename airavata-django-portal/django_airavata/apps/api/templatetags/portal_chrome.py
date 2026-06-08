"""Template tags that render the portal app-shell ("chrome") from settings.

These replace the Wagtail-backed ``navigation_tags`` used by ``base.html``,
sourcing the favicon, header logo, title, and user-menu links from
``settings.PORTAL_CHROME`` / ``settings.PORTAL_TITLE``. They must not import
Wagtail. (The Wagtail CMS-page shell keeps its own ``navigation_tags`` until the
CMS is extracted.)
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
