# Despliegue

## Objetivo

Preparar Ecclesia para correr en VPS con Docker, PostgreSQL, Redis, Celery, Gunicorn, Nginx y HTTPS.

## Estrategia inicial

- Docker Compose controla servicios internos.
- Nginx queda fuera o delante del compose como proxy reverso.
- Gunicorn atiende Django dentro del contenedor `web`.
- El puerto de aplicacion se enlaza a `127.0.0.1` en produccion.
- HTTPS se gestionara con Nginx y certificados.

## Produccion

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Checklist de produccion

- `DEBUG=False`.
- `SECRET_KEY` unica y privada.
- `ALLOWED_HOSTS` con dominios reales.
- `CSRF_TRUSTED_ORIGINS` con HTTPS.
- Cookies seguras activadas.
- `SECURE_SSL_REDIRECT=True` cuando Nginx/HTTPS este listo.
- Backups configurados.
- Logs revisables.

## Pendiente

- Crear configuracion Nginx.
- Definir dominio final.
- Automatizar backups.
- Documentar restauracion.
