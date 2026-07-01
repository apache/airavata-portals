"""Django settings for the Airavata Django Portal."""

import contextlib
import os
import sys

from django_airavata.commons import dynamic_apps

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# SECURITY WARNING: override SECRET_KEY and set DEBUG=False in production.
SECRET_KEY = "bots0)m91u_i4gpw+103o%2jn#j57wjh7s@9$x*27_4^*jyku4"
DEBUG = True

ALLOWED_HOSTS = [".airavata.host", "localhost", "127.0.0.1"]

# Served behind the Traefik ingress (TLS terminates there, forwarding
# X-Forwarded-Proto=https) so Django reconstructs the original https URL.
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = ["https://gateway.airavata.host"]


# Application definition

INSTALLED_APPS = [
    "django_airavata.apps.admin.apps.AdminConfig",
    # No django.contrib.auth/contenttypes: no database, no Django User model —
    # identity comes from the Keycloak token (apps/auth/middleware).
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "django_airavata.apps.auth.apps.AuthConfig",
    "django_airavata.apps.workspace.apps.WorkspaceConfig",
    "django_airavata.apps.api.apps.ApiConfig",
    "django_airavata.apps.groups.apps.GroupsConfig",
    "django_airavata.apps.dataparsers.apps.DataParsersConfig",
]

# List of app labels for Airavata apps that should be hidden from menus
# For example: HIDDEN_AIRAVATA_APPS = ['django_airavata_dataparsers']
HIDDEN_AIRAVATA_APPS = []

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Validate the Keycloak access token (Bearer header or kc_token cookie) and
    # set request.user / request.authz_token; before the gRPC client.
    "django_airavata.apps.auth.middleware.keycloak_token_user_middleware",
    # Adds request.data / request.query_params for views.
    "django_airavata.apps.auth.middleware.request_data_middleware",
    # Bearer-authenticated gRPC channel (request.airavata_channel); after authz_token_middleware.
    "django_airavata.middleware.airavata_grpc_client",
    # Sets is_gateway_admin / is_read_only_gateway_admin from JWT roles; after auth.
    "django_airavata.apps.auth.middleware.admin_flags_middleware",
]

ROOT_URLCONF = "django_airavata.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "django_airavata", "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.csrf",
                "django_airavata.context_processors.user",
                "django_airavata.context_processors.airavata_app_registry",
                "django_airavata.commons.dynamic_apps.context_processors.custom_app_registry",
                "django_airavata.context_processors.user_session_data",
                "django_airavata.context_processors.shell_data",
                "django_airavata.context_processors.google_analytics_tracking_id",
            ],
        },
    },
]

WSGI_APPLICATION = "django_airavata.wsgi.application"


# No database — the dummy backend lets Django boot but raises on any ORM query;
# all persistence goes through the Airavata gRPC API / the cache.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.dummy",
    }
}

# Cache-backed sessions (no DB); file-based cache survives the dev autoreloader.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "/tmp/airavata-portal-cache",
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"


TIME_ZONE = "UTC"


# Static files
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "django_airavata", "static")]

# Data storage
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o777
FILE_UPLOAD_MAX_FILE_SIZE = 64 * 1024 * 1024  # 64 MB
FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django_airavata.uploadhandler.MaxFileSizeTemporaryFileUploadHandler",
]

# Django max file size
DATA_UPLOAD_MAX_MEMORY_SIZE = 64 * 1024 * 1024  # 64 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 64 * 1024 * 1024  # 64 MB

# Tus upload (override to enable): endpoint URL + storage dir.
TUS_ENDPOINT = None
TUS_DATA_DIR = None

# Max archive age (days), echoed by ExperimentArchiveView; archive job runs offline.
GATEWAY_USER_DATA_ARCHIVE_MAX_AGE_DAYS = None

# Optional link to a legacy PGA portal.
PGA_URL = None

PORTAL_TITLE = "Airavata Django Portal"

# Portal app-shell "chrome" (base.html): favicon, header logo, user-menu links.
# Every key is optional; override in settings_local.py.
PORTAL_CHROME = {
    # Favicon URL (absolute or static). Falls back to the bundled Airavata logo.
    "favicon_url": None,
    # Header logo image URL. Falls back to the bundled Airavata logo.
    "logo_url": None,
    # Optional background color for the header logo container.
    "logo_background_color": None,
    # Extra dropdown items in the user menu. List of
    # {"link": str, "link_text": str, "icon_class": str}.
    "user_menu_links": [],
}

# Portal email templates, keyed by template_type int (see apps/auth/models.py) and
# rendered in apps/auth/utils.send_email_to_user. Override in settings_local.py.
PORTAL_EMAIL_TEMPLATES = {
    # USER_ADDED_TO_GROUP_TEMPLATE
    4: {
        "subject": "You've been added to group"
        "{{ group_names|length|pluralize }} "
        "[{{group_names|join:'] and ['}}] in {{portal_title}}",
        "body": """
<p>
Dear {{first_name}} {{last_name}},
</p>

<p>
Your user account (username {{username}}) has been added to the
group{{ group_names|length|pluralize }} {{group_names|join:' and '}}.
{{portal_title}} uses groups to share applications and experiments.
</p>

<p>
You may have access to additional applications now that you are a
member of {{group_names|join:' and '}}. To check what applications you
have access to, please check: <a href="{{dashboard_url}}">{{dashboard_url}}</a>.
</p>

<p>
You may also have access to additional experiments. To check what
experiments you have access to, please check: <a
href="{{experiments_url}}">{{experiments_url}}</a>.
</p>

<p>
Please let us know if you have any questions.  Thanks.
</p>
""".strip(),
    },
}

# Per-application custom workspace template overrides, keyed by application_module_id
# and read in apps/workspace/views.get_custom_template. Override in settings_local.py:
#   PORTAL_APPLICATION_TEMPLATES = {
#       "<app_module_id>": {"template_path": "custom/template.html",
#                            "context_processors": ["pkg.module.callable"]},
#   }
PORTAL_APPLICATION_TEMPLATES = {}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

LOGIN_URL = "django_airavata_auth:login"

AUTHENTICATION_OPTIONS = {
    # 'external': [{'idp_alias': 'cilogon', 'name': 'CILogon', 'logo': 'path/to/image'}]
}

# Vite native manifests, read by the {% vite_js/vite_css %} template tags
# (django_airavata/apps/api/templatetags/vite.py). `base` is each vite config's
# publicPath; `manifest` is the app's dist/.vite/manifest.json.
VITE_MANIFESTS = {
    "COMMON": {
        "base": "/static/common/dist/",
        "manifest": os.path.join(
            BASE_DIR,
            "django_airavata",
            "static",
            "common",
            "dist",
            ".vite",
            "manifest.json",
        ),
    },
    "ADMIN": {
        "base": "/static/django_airavata_admin/dist/",
        "manifest": os.path.join(
            BASE_DIR,
            "django_airavata",
            "apps",
            "admin",
            "static",
            "django_airavata_admin",
            "dist",
            ".vite",
            "manifest.json",
        ),
    },
    "DATAPARSERS": {
        "base": "/static/django_airavata_dataparsers/dist/",
        "manifest": os.path.join(
            BASE_DIR,
            "django_airavata",
            "apps",
            "dataparsers",
            "static",
            "django_airavata_dataparsers",
            "dist",
            ".vite",
            "manifest.json",
        ),
    },
    "GROUPS": {
        "base": "/static/django_airavata_groups/dist/",
        "manifest": os.path.join(
            BASE_DIR,
            "django_airavata",
            "apps",
            "groups",
            "static",
            "django_airavata_groups",
            "dist",
            ".vite",
            "manifest.json",
        ),
    },
    "WORKSPACE": {
        "base": "/static/django_airavata_workspace/dist/",
        "manifest": os.path.join(
            BASE_DIR,
            "django_airavata",
            "apps",
            "workspace",
            "static",
            "django_airavata_workspace",
            "dist",
            ".vite",
            "manifest.json",
        ),
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s %(name)s:%(lineno)d %(levelname)s] %(message)s",
        },
        "verbose-safe": {
            "()": "django_airavata.log_utils.SafeFormatter",
            "format": "[%(asctime)s %(name)s:%(lineno)d %(levelname)s] %(message)s",
        },
    },
    "handlers": {
        # Log everything to the console when DEBUG=True
        "console_debug": {
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        # Only log INFO and higher levels to console when DEBUG=False
        "console": {
            "filters": ["require_debug_false"],
            "class": "logging.StreamHandler",
            "formatter": "verbose-safe",
            "level": "INFO",
        },
        "mail_admins": {
            "filters": ["require_debug_false"],
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": True,
        },
    },
    "loggers": {
        "django_airavata": {
            "handlers": ["console", "console_debug", "mail_admins"],
            "level": "DEBUG",
            # Don't also bubble up to the root logger, whose handlers (console/console_debug)
            # would otherwise re-emit every django_airavata record a second time.
            "propagate": False,
        },
        "root": {"handlers": ["console", "console_debug"], "level": "WARNING"},
    },
}


# Devstack defaults: the portal runs on the shared `airavata-devstack` network and
# reaches Keycloak/Airavata at their *.airavata.host / in-network names, so it works
# with no settings_local.py. Override via env vars or settings_local.py.
GATEWAY_ID = os.environ.get("GATEWAY_ID", "default")

# Keycloak OIDC (realm: default, client: pga). The secret is the committed dev secret.
KEYCLOAK_CLIENT_ID = "pga"
KEYCLOAK_CLIENT_SECRET = "m36BXQIxX3j3VILadeHMK5IvbOeRlCCc"
# Public client (PKCE S256) used by the browser Authorization Code flow. No
# secret; the token exchange happens client-side in the callback template.
KEYCLOAK_PUBLIC_CLIENT_ID = "pga-public"
KEYCLOAK_AUTHORIZE_URL = (
    "https://auth.airavata.host/realms/default/protocol/openid-connect/auth"
)
KEYCLOAK_TOKEN_URL = (
    "https://auth.airavata.host/realms/default/protocol/openid-connect/token"
)
KEYCLOAK_USERINFO_URL = (
    "https://auth.airavata.host/realms/default/protocol/openid-connect/userinfo"
)
KEYCLOAK_LOGOUT_URL = (
    "https://auth.airavata.host/realms/default/protocol/openid-connect/logout"
)
# mkcert dev cert; the python OIDC client doesn't import the CA, so skip verify.
KEYCLOAK_VERIFY_SSL = False

# Airavata gRPC/REST server (raw airavata-python-sdk generated stubs), in-network as
# airavata-server:9090 (not published to the host).
GRPC_API_HOST = os.environ.get("GRPC_API_HOST", "airavata-server")
GRPC_API_PORT = int(os.environ.get("GRPC_API_PORT", 9090))
GRPC_API_SECURE = os.environ.get("GRPC_API_SECURE", "false").lower() == "true"

# Allow all settings to be overridden by settings_local.py file
with contextlib.suppress(ImportError):
    from django_airavata.settings_local import *  # noqa

# Keycloak self-service account console, derived from KEYCLOAK_AUTHORIZE_URL.
if "KEYCLOAK_ACCOUNT_CONSOLE_URL" not in dir() and "KEYCLOAK_AUTHORIZE_URL" in dir():
    KEYCLOAK_ACCOUNT_CONSOLE_URL = (
        KEYCLOAK_AUTHORIZE_URL.split("/protocol/openid-connect/")[0] + "/account/"
    )

# Load custom Django apps registered via the "airavata.djangoapp" entry point;
# must run after the settings above so custom code sees them.
dynamic_apps.load(INSTALLED_APPS, "airavata.djangoapp")

# Merge VITE_MANIFESTS settings from custom Django apps
settings_module = sys.modules[__name__]
dynamic_apps.merge_settings(settings_module)
