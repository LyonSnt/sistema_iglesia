# Docker

## Objetivo

Mantener una separacion clara entre infraestructura y backend Django.

La raiz del repositorio contiene los archivos Docker y Compose. El codigo Django vive en `backend/`.

## Archivos

- `docker-compose.yml`: base comun, sin puertos publicados.
- `docker-compose.dev.yml`: entorno local de desarrollo.
- `docker-compose.prod.yml`: base de produccion detras de Nginx/HTTPS.
- `Dockerfile`: imagen Python/Django.

## Uso en desarrollo

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

En desarrollo:

- `backend/` se monta como volumen en `/app`.
- Django corre con `runserver`.
- La app publica `${APP_PORT:-8020}:8020`.
- PostgreSQL publica `${DB_PUBLIC_PORT:-5434}:5432`.
- Redis no publica puerto al host.

## Uso en produccion

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

En produccion:

- No se monta el codigo fuente como bind mount.
- Se ejecuta `collectstatic`.
- Se ejecutan migraciones.
- Se levanta `gunicorn`.
- La app queda disponible en `127.0.0.1:${APP_PORT:-8020}` para que Nginx haga proxy.

## Variables

Compose usa `${ENV_FILE:-.env}` para cargar variables dentro de los contenedores.

Nota: la interpolacion de variables del propio YAML depende del `.env` del directorio o del shell. Por eso los YAML deben conservar defaults razonables.
