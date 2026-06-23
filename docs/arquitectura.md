# Arquitectura Inicial

## Vision

Ecclesia es un sistema centralizado multi-iglesia con una sola base PostgreSQL. La iglesia nacional administra supervision, reportes, auditoria y parametros generales. Cada filial gestiona sus propios miembros, familias, cargos, ministerios, asistencia, finanzas locales y documentos.

No se usara una base por iglesia filial. La separacion de datos se hara por el campo `iglesia`, roles, permisos y filtros obligatorios.

## Principios

- Todo dato sensible debe estar asociado a una iglesia.
- Los usuarios de filial solo deben consultar y modificar datos de su iglesia.
- Los usuarios nacionales pueden consultar informacion segun rol y permisos.
- Los registros criticos no se eliminan fisicamente; se marcan como inactivos, anulados o finalizados.
- Las acciones sensibles deben quedar registradas en auditoria.
- La API se prepara con DRF desde el inicio, aunque los endpoints de negocio se desarrollaran por modulo.

## Apps

- `core`: modelos abstractos, mixins y utilidades compartidas.
- `parametros`: periodos y parametros configurables, como porcentaje de aporte nacional o fecha de corte.
- `usuarios`: usuario personalizado, rol principal e iglesia asociada.
- `zonas`: zonas configurables.
- `iglesias`: iglesia nacional y filiales.
- `miembros`: miembros oficiales.
- `familias`: familias y relaciones internas.
- `cargos`: catalogo de cargos e historial de asignaciones.
- `ministerios`: departamentos, ministerios, equipos, grupos y participaciones.
- `escuela_dominical`: niveles, clases, matriculas, sesiones, asistencia, cortes
  y promociones anuales.
- `certificados`: emision numerada, PDF y anulacion de certificados asociados a
  promociones confirmadas.
- `auditoria`: registros de auditoria para acciones importantes.
- `api`: punto de entrada para endpoints DRF.
- Apps reservadas: `obreros`, `asistencia`, `eventos`, `finanzas`,
  `aportes_nacionales`, `traslados`, `documentos`, `inventario`, `reportes` y
  `notificaciones`.

## Modelo multi-iglesia

Los modelos con alcance filial heredan de `IglesiaScopedModel`, que agrega una llave foranea protegida a `Iglesia`. El admin inicial incluye `IglesiaScopedAdminMixin` para limitar querysets por iglesia cuando el usuario no es nacional.

La iglesia `PRUEBAS` se usara como filial de validacion dentro de la misma base. No es un tenant ni una base separada.

El filtrado definitivo debe repetirse en:

- Managers y querysets.
- Vistas Django y HTMX.
- Formularios.
- Admin.
- Serializers y viewsets DRF.
- Reportes y exportaciones.

## Roles iniciales

Los roles estan definidos en `Usuario.Rol`:

- `SUPERADMIN`
- `ADMIN_NACIONAL`
- `PASTOR_FILIAL`
- `ENCARGADO_FILIAL`
- `SECRETARIO_FILIAL`
- `TESORERO_FILIAL`
- `SOLO_LECTURA`

Los cargos organizacionales como Presidente, Vicepresidente, Auditor, Pastor,
Encargado, Lider de ministerio o Maestro se registran mediante `Cargo`,
`AsignacionCargo` o asignaciones funcionales especificas como `Ministerio.lider`
y `ClaseEscuelaDominical.maestro`. No todos los cargos son roles de acceso.

## Infraestructura

Servicios Docker:

- `web`: Django.
- `db`: PostgreSQL.
- `redis`: broker y cache base.
- `celery_worker`: ejecucion asincrona.
- `celery_beat`: tareas programadas.

Comando de desarrollo:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

La raiz del repositorio contiene infraestructura y operacion. El backend Django vive en `backend/`, incluyendo `manage.py`, `config/`, `apps/`, `templates/`, `static/`, `media/` y los archivos `requirements`.

## Siguientes fases recomendadas

1. Ejecutar `seed_inicial` para sembrar iglesia nacional, filial `PRUEBAS`, zonas, cargos, parametros y grupos.
2. Implementar permisos granulares y decoradores/mixins de iglesia.
3. Crear flujos de miembros, familias y traslados.
4. Implementar finanzas locales y aporte nacional con cuenta corriente.
5. Crear reportes nacionales y filiales.
6. Validar el diseno PDF de certificados con los recursos institucionales.
7. Agregar backups automatizados y perfil de produccion con Nginx/HTTPS.
