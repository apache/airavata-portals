# Deploying the portal + CMS behind one origin

The Airavata Django portal is the gateway **application** (login, workspace,
experiments, API). Landing pages, documentation, and other editable content are
served by the separate [`airavata-cms`](../../airavata-cms) Wagtail service. A
reverse proxy unifies them under one hostname.

`reverse-proxy.conf` (nginx) is the routing contract: the portal's app path
prefixes go to the portal, everything else goes to the CMS. Keep the portal
prefix list in sync with `django_airavata/urls.py`.

## CMS-side prefix contract

The portal owns `/static` and `/media`, and `/admin` is the portal admin app, so
the CMS must serve its own assets and admin under non-colliding prefixes that
fall through to the catch-all → CMS rule:

| Concern | Portal | CMS |
|---------|--------|-----|
| Static  | `/static`  | `/cms-static` (`STATIC_URL`) |
| Media   | `/media`   | `/cms-media` (`MEDIA_URL`)   |
| Admin   | `/admin` (portal app) | `/cms` (`WAGTAILADMIN_*`) |

Public CMS pages (`/`, `/about`, docs, …) need no special prefix — the catch-all
routes them to the CMS.
