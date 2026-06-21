# Sesion 2026-06-20 - Cierre del Dia

## Estado Cerrado

Se dejo Ecclesia con infraestructura base funcionando, documentacion inicial,
datos base y usuarios de prueba.

## Decisiones Confirmadas

- Ecclesia no usara multitenant.
- Se usara una sola base PostgreSQL.
- La separacion de datos sera por `iglesia`, roles, permisos y filtros.
- `PRUEBAS` sera una iglesia filial de validacion, no un tenant.
- Tailwind se compilara con Node desde Docker.
- El documento principal para retomar sera `docs/estado_actual.md`.

## Implementado Hoy

- Proyecto organizado con `backend/`.
- Docker base/dev/prod.
- Puertos propios de Ecclesia:
  - app `8020`;
  - PostgreSQL desarrollo `5434`.
- Tailwind compilado con Node:
  - sin CDN;
  - etapa Node en Dockerfile;
  - servicio `tailwind` en desarrollo.
- Documentacion tecnica ampliada.
- `docs/estado_actual.md` creado como punto de reentrada.
- Helpers de alcance por iglesia en `apps.core.iglesias`.
- `IglesiaScopedAdminMixin` conectado a esos helpers.
- `seed_inicial` creado, ejecutado y validado.
- `seed_usuarios_prueba` creado, ejecutado y validado.
- Warning de `django-axes` corregido usando `AXES_LOCKOUT_PARAMETERS`.

## Datos Creados

- Iglesia Nacional.
- Iglesia Filial Pruebas.
- Zonas base.
- Cargos base.
- Parametros generales.
- Grupos por rol.
- Usuarios de prueba:
  - `admin_nacional`.
  - `auditor_nacional`.
  - `pastor_pruebas`.
  - `secretario_pruebas`.
  - `tesorero_pruebas`.
  - `lectura_pruebas`.

## Validaciones

- `/admin/` funciona.
- `/api/health/` funciona.
- `python manage.py check` sin issues.
- `python manage.py makemigrations --check --dry-run` sin cambios pendientes.
- `seed_inicial` idempotente.
- `seed_usuarios_prueba` idempotente.
- Usuarios de prueba tienen rol, grupo e iglesia correctos.

## Pendiente Recomendado Para Retomar

1. Normalizar el superusuario tecnico `admin` con rol/grupo `SUPERADMIN`.
2. Definir matriz de permisos funcionales por modulo.
3. Crear decoradores/mixins de permisos para vistas.
4. Crear login/home/dashboard minimo despues de cerrar permisos.

## Frase Para Retomar

```text
Lee docs/estado_actual.md. Continuemos desde allí. Antes de modificar código o datos, resume qué contiene actualmente el sistema, qué está implementado, qué está pendiente y cuál sería el siguiente paso recomendado. No hagas cambios hasta que lo confirme.
```
