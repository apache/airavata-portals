# airavata-cms

Standalone [Wagtail](https://wagtail.org/) CMS for Airavata gateways — landing
pages, documentation sites, and other admin-authored content.

It is deliberately **decoupled** from `airavata-django-portal`: the portal is a
stateless gateway UI that talks only to the Airavata API, while this service owns
its own database and the editable content. A reverse proxy/router stitches the
two into one site for end users (the portal serves the app paths; this CMS serves
landing/docs/content paths).

## Stack

- Wagtail 7.4 / Django 6.0 / Python 3.13

## Develop

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export DJANGO_SETTINGS_MODULE=airavata_cms.settings.dev
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver            # CMS admin at /admin, pages at /
```

## Layout

- `airavata_cms/` — project (settings split into `base`/`dev`/`production`, urls, wsgi)
- `home/` — the home page app (Wagtail `Page` models live here)
- `search/` — Wagtail search view
- `Dockerfile` — production image (gunicorn)
