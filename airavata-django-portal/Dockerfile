# node image is based on Debian and includes necessary build tools
# node 24 LTS — satisfies vite 8 (^18 || ^20 || >=22) and the dataparsers
# maplibre-gl/@unovis chain, which requires node >=22.
FROM node:24 as build-stage

WORKDIR /code

# The frontend is a single npm-workspaces monorepo: one root package.json declares
# the 8 member packages, one root package-lock.json pins the whole graph. Copy the
# root manifest + lockfile and EVERY member's package.json first so `npm ci` is
# cached independently of source changes (npm needs each member's manifest present
# to resolve and link the workspace graph).
COPY package.json package-lock.json ./
COPY django_airavata/apps/api/package.json ./django_airavata/apps/api/
COPY django_airavata/static/common/package.json ./django_airavata/static/common/
COPY django_airavata/apps/auth/package.json ./django_airavata/apps/auth/
COPY django_airavata/apps/admin/package.json ./django_airavata/apps/admin/
COPY django_airavata/apps/groups/package.json ./django_airavata/apps/groups/
COPY django_airavata/apps/dataparsers/package.json ./django_airavata/apps/dataparsers/
COPY django_airavata/apps/workspace/package.json ./django_airavata/apps/workspace/
COPY django_airavata/apps/workspace/django-airavata-workspace-plugin-api/package.json ./django_airavata/apps/workspace/django-airavata-workspace-plugin-api/

# One install for the whole workspace (cached npm download dir speeds rebuilds).
RUN --mount=type=cache,target=/root/.npm npm ci

# Copy sources and run the ordered workspace build (api + common first, then the
# rest; workspace-plugin-api before workspace). build_js.sh fans out via
# `npm run build --workspace=<name>` from this root.
COPY build_js.sh ./
COPY django_airavata ./django_airavata
RUN ./build_js.sh



FROM python:3.12-slim as server-stage

# The portal's only Airavata dependency is the editable airavata-python-sdk, pinned in
# pyproject.toml as `[tool.uv.sources] path = "../../airavata/airavata-python-sdk"`. uv
# REFUSES a relative source path that escapes above the project root, so the app cannot
# live at /code (depth 1). We mirror the host's repo layout instead: the portal at
# /workspace/airavata-portals/airavata-django-portal and the SDK at
# /workspace/airavata/airavata-python-sdk, so `../../airavata/...` resolves in-tree —
# identically at build time, in the running container, and on the host (remote mode).
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/workspace/airavata-portals/airavata-django-portal/.venv/bin:$PATH"

# uv for dependency management (https://docs.astral.sh/uv/).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

EXPOSE 8000

WORKDIR /workspace/airavata-portals/airavata-django-portal
RUN apt-get update && apt-get install -y --no-install-recommends \
        git gcc g++ zlib1g-dev libjpeg-dev && \
    rm -rf /var/lib/apt/lists/*

# Sibling airavata-python-sdk, staged into the portal context by the `stage-sdk` Tilt step
# (it lives in the sibling airavata repo, outside this build context). Placed two levels up
# so the pyproject `../../airavata/airavata-python-sdk` path resolves to it.
COPY .devstack-sdk/airavata-python-sdk /workspace/airavata/airavata-python-sdk
COPY pyproject.toml uv.lock README.md ./
COPY ./django_airavata ./django_airavata
RUN uv sync --frozen --no-dev

# Copy in a default settings_local.py file
COPY ./django_airavata/settings_local.py.sample ./django_airavata/settings_local.py

COPY ./ .

# Copy javascript builds from build-stage (sources stay at the build-stage's /code)
WORKDIR /workspace/airavata-portals/airavata-django-portal/django_airavata/apps/api/static/django_airavata_api
COPY --from=build-stage /code/django_airavata/apps/api/static/django_airavata_api .
WORKDIR /workspace/airavata-portals/airavata-django-portal/django_airavata/static/common/dist
COPY --from=build-stage /code/django_airavata/static/common/dist .
WORKDIR /workspace/airavata-portals/airavata-django-portal/django_airavata/apps/admin/static/django_airavata_admin
COPY --from=build-stage /code/django_airavata/apps/admin/static/django_airavata_admin .
WORKDIR /workspace/airavata-portals/airavata-django-portal/django_airavata/apps/groups/static/django_airavata_groups
COPY --from=build-stage /code/django_airavata/apps/groups/static/django_airavata_groups .
WORKDIR /workspace/airavata-portals/airavata-django-portal/django_airavata/apps/auth/static/django_airavata_auth
COPY --from=build-stage /code/django_airavata/apps/auth/static/django_airavata_auth .
WORKDIR /workspace/airavata-portals/airavata-django-portal/django_airavata/apps/workspace/static/django_airavata_workspace
COPY --from=build-stage /code/django_airavata/apps/workspace/static/django_airavata_workspace .
WORKDIR /workspace/airavata-portals/airavata-django-portal/django_airavata/apps/dataparsers/static/django_airavata_dataparsers
COPY --from=build-stage /code/django_airavata/apps/dataparsers/static/django_airavata_dataparsers .

WORKDIR /workspace/airavata-portals/airavata-django-portal

ENTRYPOINT ["/workspace/airavata-portals/airavata-django-portal/scripts/start-server.sh"]
