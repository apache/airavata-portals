"""DB-free auth decorators.

``django.contrib.auth.decorators.login_required`` cannot be used once
``django.contrib.auth`` / ``django.contrib.contenttypes`` are removed from
``INSTALLED_APPS``: its anonymous-redirect path lazily imports
``django.contrib.auth.views`` -> ``forms`` -> ``models`` ->
``contenttypes.models``, which raises because those model classes have no
installed app. Identity here comes from the verified Keycloak token, so this is
a minimal ``request.user.is_authenticated`` check that redirects to
``settings.LOGIN_URL`` with the usual ``?next=`` parameter.
"""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.http import HttpResponseRedirect, QueryDict
from django.shortcuts import resolve_url

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpResponseBase

    from django_airavata.request import AiravataRequest

type ViewFunc = Callable[..., HttpResponseBase]


def login_required(
    view_func: ViewFunc | None = None,
    redirect_field_name: str = "next",
    login_url: str | None = None,
) -> ViewFunc | Callable[[ViewFunc], ViewFunc]:
    def decorator(view: ViewFunc) -> ViewFunc:
        @wraps(view)
        def _wrapped(
            request: AiravataRequest, *args: Any, **kwargs: Any
        ) -> HttpResponseBase:
            if getattr(request.user, "is_authenticated", False):
                return view(request, *args, **kwargs)
            resolved_url = resolve_url(login_url or settings.LOGIN_URL)
            parts = list(urlparse(resolved_url))
            if redirect_field_name:
                querystring = QueryDict(parts[4], mutable=True)
                querystring[redirect_field_name] = request.get_full_path()
                parts[4] = querystring.urlencode(safe="/")
            return HttpResponseRedirect(urlunparse(parts))

        return _wrapped

    if view_func:
        return decorator(view_func)
    return decorator
