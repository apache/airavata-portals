# Airavata Django App Cookiecutter

Scaffolds a custom Django app for the
[Airavata Django Portal](https://github.com/apache/airavata-django-portal). One
template, three modes: page-serving app, output-view provider, or both.

## Quickstart

Install Cookiecutter if you haven't:

    pip install --user -U cookiecutter

Generate an app:

    cookiecutter https://github.com/apache/airavata-django-app-cookiecutter.git

You'll be prompted for:

- **include_app_pages** (`yes`/`no`) — generate page views (`views.py`, `urls.py`,
  a `home.html` template) plus a minimal Vite frontend the portal loads.
- **include_output_view** (`yes`/`no`) — generate an output-view provider under
  `output_views/` that renders experiment output in the portal.

The `output_view_*` and `number_of_output_files` prompts only apply when
`include_output_view` is `yes`. Answering `no` to **both** aborts generation.

## Modes

| include_app_pages | include_output_view | You get |
|-------------------|---------------------|---------|
| yes | no  | `views.py` + `urls.py` + `home.html` + Vite frontend; `airavata.djangoapp` entry point only |
| no  | yes | `output_views/<slug>_output_view.py`; `airavata.djangoapp` + `airavata.output_view_providers` entry points; minimal `apps.py` |
| yes | yes | both of the above |

## Vite frontend

When `include_app_pages` is `yes`, the app ships its own Vite bundle under
`static/<slug>/`. The portal loads it through its native Vite manifest tags
(`{% vite_js 'main' vite_app %}` / `{% vite_css 'main' vite_app %}`) — not
django-webpack-loader.

The app's `AppConfig.merge_settings` registers its `dist/.vite/manifest.json`
into the portal's `VITE_MANIFESTS`. Build the manifest before starting the
portal:

    cd <slug>/<slug>/static/<slug>
    npm install
    npm run build      # or `npm run watch` while developing

## Install into the portal

See the generated project's `README.md`. In short: `pip install -e .` into the
portal's virtualenv (build the Vite frontend first if applicable), then restart
the portal.
