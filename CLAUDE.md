# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Monorepo of web portals, SDKs, and tools built on top of Apache Airavata. Contains the reference Django-based science gateway, newer React-based portals, Python client libraries, and template generators.

## Sub-Projects

| Project | Stack | Purpose |
|---------|-------|---------|
| `airavata-django-portal` | Django 3.2 + Vue 2 | Reference science gateway (main portal) |
| `airavata-research-portal` | React 19 + Vite + TypeScript | CyberShuttle research platform (newest) |
| `airavata-custos-portal` | Django + Vue 2 | Identity, group, and permissions management UI |
| `airavata-mft-portal` | Django + Webpack | Managed File Transfer dashboard |
| `airavata-local-agent` | Electron + Next.js | Desktop app for local Docker container management |
| `airavata-mcp-client-chatbot` | Flask + React | MCP-based chatbot for querying CyberShuttle resources |
| `airavata-jupyterhub` | JupyterHub + Docker | JupyterHub deployment for gateway notebook sessions (config, images, user container) |
| `airavata-cookiecutter-django-app` | Cookiecutter | Template for scaffolding custom Django apps |
| `airavata-cookiecutter-django-output-view` | Cookiecutter | Template for output viewer plugins |
| `airavata-php-gateway` | PHP | Legacy gateway (archived, replaced by Django portal) |

## airavata-django-portal (Main Portal)

### Build & Dev

```bash
cd airavata-django-portal

# Backend setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py load_cms_data new_default_theme
python manage.py runserver                        # Port 8000

# Frontend (builds all 8 JS packages)
./build_js.sh

# Frontend dev (hot reload for a single app)
cd django_airavata/apps/workspace
yarn
yarn run serve

# Tests
./runtests.py                                     # Django backend tests
./test_js.sh                                      # Frontend tests (Jest)
flake8 .                                          # Python lint
./lint_js.sh                                      # JS lint (ESLint + Prettier)
autopep8 -i -aaa -r . && isort .                  # Auto-format Python
```

### Django Apps

Each app under `django_airavata/apps/` is self-contained with its own frontend:

| App | Purpose |
|-----|---------|
| `workspace` | Main job/project workspace (Vue 2 + web components) |
| `api` | REST API endpoints + DRF serializers |
| `auth` | OAuth/Keycloak login + user management |
| `admin` | Admin dashboard |
| `groups` | Group management |
| `dataparsers` | Data parsing and visualization |

### Architecture

- **Backend**: Django + DRF, Thrift-based Airavata client, Wagtail CMS for page content
- **Frontend**: Vue 2 per app, webpack/Vue CLI builds, each app has colocated `static/` with its own build config
- **Dynamic apps**: Plugin-style extensions discovered via Python entry points (powered by `django_airavata.commons`)
- **Web components**: Workspace app builds Vue components as reusable web components
- **No business logic** — the portal is a rendering layer. All logic lives in the Airavata server.

### Configuration

- `django_airavata/settings.py` — main settings
- `django_airavata/settings_local.py` — local overrides (copy from `settings_local.py.sample`)
- Docker: multi-stage Dockerfile (Node build + Python runtime)

## airavata-research-portal

```bash
cd airavata-research-portal
npm install
npm run dev                                       # Vite dev server
npm run build                                     # Production build
npm run lint                                      # ESLint
```

React 19 + TypeScript + Vite + Chakra UI 3. OIDC auth via `oidc-client-ts`.

## Root pyrightconfig.json

Pyright type checking configured for Python 3.10, scoped to the Django portal and SDK sources.
