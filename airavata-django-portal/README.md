# Apache Airavata Django Portal

![Build Status](https://github.com/apache/airavata-django-portal/actions/workflows/build-and-test.yaml/badge.svg)
[![Build Status](https://readthedocs.org/projects/apache-airavata-django-portal/badge/?version=latest)](https://apache-airavata-django-portal.readthedocs.io/en/latest/?badge=latest)

The Airavata Django Portal is a web interface to the
[Apache Airavata](http://airavata.apache.org/) API implemented using the Django
web framework. The intention is that the Airavata Django Portal can be used as
is for a full featured web based science gateway but it can also be customized
through various plugins to add more domain specific functionality as needed.

## Getting Started

The following steps will help you quickly get started with running the Airavata
Django Portal locally. This will allow you to try it out and can also be used as
a development environment. If you just want to run the Airavata Django Portal
locally, see the Docker instructions below for a more simplified approach.

The Airavata Django Portal requires Python 3.12. You'll need it installed
locally.

You'll also need Node.js (version 24) and npm to build the JavaScript frontend
code; npm ships with Node.js. You can use
[nvm](https://github.com/nvm-sh/nvm) to manage the Node.js install — with nvm
installed, run `nvm install && nvm use` (it reads `.nvmrc`) before building. The
frontend is an npm workspace, so a single `npm install` at the repo root installs
all of the packages.

> **Recommended (Tilt + devstack):** run the portal as a container against a
> local Apache Airavata stack, both managed with [Tilt](https://tilt.dev).
> One-time setup: `./devstack/devstack setup` (from the `airavata-portals` root).
> Then `cd ../airavata && tilt up`, and from the `airavata-portals` repo
> `tilt up --port 10351`. The portal is served at <https://gateway.airavata.host>
> (trusted HTTPS, no `-k`). The manual steps below are the equivalent without Tilt.

This project uses [uv](https://docs.astral.sh/uv/) for Python dependency
management. The portal has **no database** — there is nothing to migrate, and
all persistence goes through the Airavata gRPC API and the cache.

1.  Check out the project and install dependencies.

    ```
    git clone https://github.com/apache/airavata-django-portal.git
    cd airavata-django-portal
    uv sync
    ```

    `uv sync` creates `.venv/` (Python 3.12) and installs everything, including
    the editable `airavata-python-sdk` from a sibling `apache/airavata` checkout
    (see `[tool.uv.sources]` in `pyproject.toml`). Prefix commands with
    `uv run` (e.g. `uv run python manage.py ...`) or activate `.venv` directly.

2.  Create a local settings file by copying the sample and editing it to match
    your Keycloak and Airavata server deployment.

    ```
    cp django_airavata/settings_local.py.sample django_airavata/settings_local.py
    ```

3.  Build the JavaScript sources. There are a few JavaScript packages in the
    source tree, colocated with the Django apps in which they are used. The
    `build_js.sh` script will build them all.

    ```
    ./build_js.sh
    ```

    - **Windows note**: run `./build_js.sh` from WSL or Git Bash.

4.  Run the server.

    ```
    uv run python manage.py runserver
    ```

5.  Point your browser to http://localhost:8000.

## Docker instructions

To run the Django Portal as a Docker container, you need a `settings_local.py`
file which you can create from the `settings_local.py.sample` file. Then run the
following:

1. Build the Docker image.

   ```
   docker build -t airavata-django-portal .
   ```

2. Run the Docker container.

   ```
   docker run -d \
     -v /path/to/my/settings_local.py:/code/django_airavata/settings_local.py \
     -p 8000:8000 airavata-django-portal
   ```

3. Point your browser to http://localhost:8000.

### Multi-architecture images

To build and push
[multi-architecture images](https://docs.docker.com/desktop/multi-arch/), first
create a builder (one time)

```
docker buildx create --name mybuilder --use
```

then run

```
docker buildx build --pull --platform linux/amd64,linux/arm64 -t apache/airavata-django-portal:latest --push .
```

## Documentation

Documentation currently is available at
https://apache-airavata-django-portal.readthedocs.io/en/latest/ (built from the
'docs' directory).

To build the documentation locally, first
[set up a development environment](#setting-up-development-environment), then
run the following in the root of the project:

```
mkdocs serve
```

## Feedback

Please send feedback to the mailing list at <dev@airavata.apache.org>. If you
encounter bugs or would like to request a new feature you can do so in the
[Airavata Jira project](https://issues.apache.org/jira/projects/AIRAVATA) (just
select the _Django Portal_ component when you make your issue).

## Customization

See the Customization Guide in the
[documentation](https://apache-airavata-django-portal.readthedocs.io/en/latest/)
for information on how to customize the Airavata Django Portal user interface.
To get started we recommend going through the
[Gateways Tutorial](https://apache-airavata-django-portal.readthedocs.io/en/latest/tutorial/gateways_tutorial/).
This tutorial covers the different ways that the user interface can be
customized.

## Contributing

For general information on how to contribute, please see the
[Get Involved](http://airavata.apache.org/get-involved.html) section of the
Apache Airavata website.

### Setting up development environment

`uv sync` installs the development and testing tools (ruff, ty) alongside the
runtime dependencies. Lint, format, and type-check the Python code with:

```
uv run ruff check .       # lint
uv run ruff format .      # auto-format
uv run ty check           # type check
```

Prettier and ESLint are used for JavaScript and Vue.js code (see `lint_js.sh`).

See the docs for more information on
[developing the backend](./docs/dev/developing_backend.md) and
[frontend code](./docs/dev/developing_frontend.md).

### Running Django Tests

Run `uv run ./runtests.py` to run the Django unit tests.

## License

The Apache Airavata Django Portal is licensed under the Apache 2.0 license. For
more information see the [LICENSE](LICENSE) file.
