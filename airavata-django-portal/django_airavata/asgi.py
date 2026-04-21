"""ASGI config for django_airavata project."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_airavata.settings")

# Django's `runserver` auto-wraps the app with ASGIStaticFilesHandler when
# DEBUG is on; standalone ASGI servers (uvicorn) do not. Wrap here so
# `uv run uvicorn django_airavata.asgi:application` still serves /static/
# in dev.
_inner = get_asgi_application()

from django.conf import settings  # noqa: E402  (must import after django setup)

if settings.DEBUG:
    from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
    application = ASGIStaticFilesHandler(_inner)
else:
    application = _inner
