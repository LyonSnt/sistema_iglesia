# Sesion 2026-06-20 - Estructura Inicial

## Decisiones

- El repositorio se llama `sistema_iglesia`.
- El nombre visible del sistema es `Ecclesia - Sistema Integral de Gestion de Iglesias`.
- Django vive en `backend/`.
- Las apps Django viven en `backend/apps/`.
- La configuracion Django se llama `config`.
- Docker usa tres compose:
  - `docker-compose.yml`
  - `docker-compose.dev.yml`
  - `docker-compose.prod.yml`
- El compose base no publica puertos.
- Desarrollo publica la app por `APP_PORT`, default `8020`.
- Desarrollo publica PostgreSQL por `DB_PUBLIC_PORT`, default `5434`.
- Produccion publica la app solo en `127.0.0.1:${APP_PORT}`.
- Tailwind se manejara compilado con Node, no por CDN como solucion final.
- Ecclesia usara una sola base PostgreSQL.
- La separacion entre filiales se hara por `iglesia`, roles, permisos y filtros obligatorios.
- No se implementara multi-tenant por base de datos en esta fase.
- `PRUEBAS` sera una iglesia filial de validacion dentro de la misma base, no un tenant.

## Estado actual

- Estructura base creada.
- Modelos iniciales creados.
- Migraciones iniciales creadas.
- Admin basico creado.
- DRF configurado con health check.
- Celery y Redis configurados.
- django-axes configurado.
- Seed inicial agregado para zonas, iglesias, cargos, parametros y grupos.
- Helpers de alcance por iglesia agregados en `apps.core.iglesias`.
- Seed de usuarios de prueba agregado y ejecutado.

## Pendiente inmediato

- Integrar build real de Tailwind.
- Crear scripts operativos.
- Ejecutar `seed_inicial` en el entorno local.
- Normalizar superusuario tecnico con rol/grupo `SUPERADMIN`.
- Definir permisos por modulo con mas detalle.
