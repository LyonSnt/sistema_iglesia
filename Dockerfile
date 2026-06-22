FROM node:20-alpine AS assets

WORKDIR /build

COPY backend/package.json /build/package.json
RUN npm install

COPY backend/tailwind.config.js /build/tailwind.config.js
COPY backend/static /build/static
COPY backend/templates /build/templates
COPY backend/apps /build/apps
RUN npm run build:css


FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev gettext \
    && rm -rf /var/lib/apt/lists/*

ARG REQUIREMENTS_FILE=requirements.txt
COPY backend/requirements.txt backend/requirements-dev.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/${REQUIREMENTS_FILE}

COPY backend /app
COPY --from=assets /build/static/css/app.css /app/static/css/app.css
COPY --from=assets /build/static/css/app.css /opt/ecclesia-assets/app.css

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/staticfiles /app/media \
    && chown -R appuser:appuser /app

USER appuser
