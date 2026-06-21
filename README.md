# Ecclesia - Sistema Integral de Gestion de Iglesias

Sistema web centralizado multi-iglesia para una organizacion religiosa nacional con iglesias filiales.

## Stack

- Django 5
- PostgreSQL
- Docker y docker-compose
- Redis
- Celery y Celery Beat
- Django REST Framework
- HTMX
- Tailwind CSS
- django-environ
- django-axes

## Primer arranque

1. Copiar variables de entorno:

```bash
cp .env.example .env
```

2. Levantar el entorno de desarrollo:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

3. Crear superusuario:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

4. Cargar datos base:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py seed_inicial
```

5. Abrir:

- Admin: http://localhost:8020/admin/
- API health check: http://localhost:8020/api/health/

## Comandos utiles

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f web
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py seed_inicial
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py seed_usuarios_prueba
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

## Produccion base

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

En produccion la app queda publicada en `127.0.0.1:${APP_PORT:-8020}`, pensada para quedar detras de Nginx y HTTPS.

## Documentacion

La documentacion tecnica vive en [docs/README.md](docs/README.md).

## Estructura

```text
backend/                Backend Django
backend/config/         Configuracion Django
backend/apps/           Apps de dominio
backend/templates/      Plantillas compartidas
backend/static/         Assets estaticos fuente
backend/staticfiles/    Archivos estaticos recolectados
backend/media/          Archivos subidos por usuarios
backups/                Respaldos locales
docs/                   Documentacion tecnica
scripts/                Scripts operativos
```

## Seguridad inicial

- Usuario personalizado en `apps.usuarios.Usuario`.
- Bloqueo de intentos fallidos con `django-axes`.
- Configuracion sensible por `.env`.
- CSRF activo por defecto.
- Sesiones con expiracion configurable.
- Modelos sensibles preparados con campo `iglesia`.
- Eliminacion logica mediante `activo=False` en modelos criticos.

## Nota de produccion

Esta entrega deja la base lista para evolucionar hacia VPS, Nginx, HTTPS y jobs de backups. No incluye todavia vistas funcionales ni flujos completos de negocio.
