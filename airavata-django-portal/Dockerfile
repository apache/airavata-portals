# --- Stage 1: Build frontend assets ---
FROM node:20-slim AS frontend-builder

WORKDIR /app
COPY . .

# Install Yarn classic (v1)
RUN corepack enable && corepack prepare yarn@1.22.19 --activate

# Install dependencies and build frontend assets
RUN yarn install --ignore-engines
RUN ./build_js.sh

# --- Stage 2: Python backend ---
FROM python:3.11-slim AS backend

# Install system dependencies for Python, MySQL, and image processing
RUN apt-get update && apt-get install -y \
    build-essential \
    libmariadb-dev-compat \
    libmariadb-dev \
    git \
    gcc \
    g++ \
    zlib1g-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend source code
COPY . .

# Copy built frontend assets from builder stage
COPY --from=frontend-builder /app/django_airavata/static/common ./django_airavata/static/common
COPY --from=frontend-builder /app/django_airavata/apps/api ./django_airavata/apps/api
COPY --from=frontend-builder /app/django_airavata/apps/admin ./django_airavata/apps/admin
COPY --from=frontend-builder /app/django_airavata/apps/auth ./django_airavata/apps/auth
COPY --from=frontend-builder /app/django_airavata/apps/dataparsers ./django_airavata/apps/dataparsers
COPY --from=frontend-builder /app/django_airavata/apps/groups ./django_airavata/apps/groups
COPY --from=frontend-builder /app/django_airavata/apps/workspace ./django_airavata/apps/workspace

# Install Python dependencies
COPY requirements.txt ./
COPY requirements-mysql.txt ./
COPY setup.py ./
RUN pip install --upgrade pip && \
    pip install gunicorn && \
    pip install -r requirements.txt && \
    pip install -r requirements-mysql.txt && \
    rm -rf ~/.cache/pip

# Expose port 8000
EXPOSE 8000

# Entrypoint: Gunicorn for production
CMD ["gunicorn", "django_airavata.wsgi:application", "-b", "0.0.0.0:8000", "--workers=3", "--log-level=info"]