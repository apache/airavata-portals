# Apache Airavata Django Portal

Web portal for Apache Airavata, providing a user interface for managing experiments, applications, and compute resources.

## Tech Stack

- **Backend:** Python 3.12+, Django 5.1, Django REST Framework
- **Frontend:** Vue 3, Vite, Bootstrap 5
- **CMS:** Wagtail 6
- **API Client:** airavata-python-sdk (gRPC)

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.12+ |
| Node.js | 22+ |
| Yarn | 1.22+ |
| Docker | 20.10+ |
| Tilt | 0.33+ |

## Quick Start

```bash
tilt up
```

This starts MariaDB, the Django dev server (port 8000), and frontend dev servers with HMR.

## Manual Setup

```bash
# Infrastructure
docker compose -f compose/docker-compose.yaml up -d

# Backend
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
python manage.py migrate
python manage.py runserver

# Frontend (per app)
cd django_airavata/apps/api/static/django_airavata_api
yarn install && yarn dev
```

## Configuration

The portal connects to the Airavata server via the Python SDK:

```python
# settings.py
AIRAVATA_API_HOST = 'localhost'
AIRAVATA_API_PORT = 9090
GATEWAY_ID = 'default'
```

## Docker

```bash
# Build
docker build -t airavata-django-portal .

# Run
docker run -d \
  -v /path/to/my/settings_local.py:/code/django_airavata/settings_local.py \
  -p 8000:8000 airavata-django-portal

# Load initial CMS pages (first run only)
docker exec CONTAINER_ID python manage.py load_cms_data new_default_theme
```

### Multi-architecture images

```bash
docker buildx create --name mybuilder --use
docker buildx build --pull --platform linux/amd64,linux/arm64 -t apache/airavata-django-portal:latest --push .
```

## Documentation

Documentation is available at https://apache-airavata-django-portal.readthedocs.io/en/latest/

To build locally:

```bash
mkdocs serve
```

## Contributing

See the [Get Involved](http://airavata.apache.org/get-involved.html) section of the Apache Airavata website.

### Development

```bash
pip install -e ".[dev]"
```

Uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting. Run `ruff check` and `ruff format` before committing.

### Running Tests

```bash
./runtests.py
```

## License

Apache License 2.0
