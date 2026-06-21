# Estado Actual

Ultima actualizacion: 2026-06-21.

## Resumen

Ecclesia es un sistema web centralizado multi-iglesia para una organizacion
religiosa nacional con mas de 30 iglesias filiales.

La iglesia nacional necesita supervision, reportes, auditoria y control general.
Cada iglesia filial debe administrar sus propios datos como si el sistema fuera
solo de esa filial.

## Decisiones Vigentes

- Se usara una sola base PostgreSQL: `sistema_iglesia`.
- No se usara multitenant por base de datos.
- No se usaran bases por iglesia filial.
- No se usaran rutas tipo `/pruebas/`.
- La separacion de datos sera por campo `iglesia`, roles, permisos y filtros obligatorios.
- `PRUEBAS` sera una iglesia filial de validacion dentro de la misma base.
- El backend Django vive en `backend/`.
- Las apps Django viven en `backend/apps/`.
- La configuracion Django se llama `config`.
- Tailwind se compila con Node, sin CDN.
- Docker usa tres archivos:
  - `docker-compose.yml`: base comun sin puertos.
  - `docker-compose.dev.yml`: desarrollo.
  - `docker-compose.prod.yml`: produccion base.
- Puertos de Ecclesia:
  - App: `8020`.
  - PostgreSQL publicado en desarrollo: `5434`.

## Implementado

### Infraestructura

- Dockerfile con build multi-stage:
  - etapa Node para compilar Tailwind;
  - etapa Python final sin Node.
- `docker-compose.yml`.
- `docker-compose.dev.yml`.
- `docker-compose.prod.yml`.
- PostgreSQL.
- Redis.
- Celery worker.
- Celery Beat.
- Volumen para PostgreSQL.
- Volumen para `media`.
- Volumen para `staticfiles`.

### Backend

- Proyecto Django `config`.
- Django REST Framework configurado.
- Endpoint de salud: `/api/health/`.
- API inicial de consulta:
  - `/api/miembros/`.
  - `/api/miembros/<id>/`.
  - `/api/familias/`.
  - `/api/familias/<id>/`.
  - `/api/matrimonios/`.
  - `/api/cargos/`.
  - `/api/asignaciones-cargos/`.
  - `/api/asignaciones-cargos/<id>/`.
- Modulo Cargos/directivas iniciado:
  - listado en `/cargos/`;
  - detalle de asignacion;
  - creacion y edicion;
  - finalizacion de asignaciones.
- Modulo Ministerios iniciado:
  - listado en `/ministerios/`;
  - detalle de ministerio;
  - creacion y edicion;
  - agregado y finalizacion de participaciones.
- HTMX preparado en plantilla base.
- Login propio en `/login/`.
- Logout por POST en `/logout/`.
- Dashboard inicial protegido en `/`.
- Listado inicial de miembros en `/miembros/`.
- Tailwind compilado desde `backend/static/css/input.css` hacia `backend/static/css/app.css`.
- `django-environ` para variables de entorno.
- `django-axes` para proteccion contra fuerza bruta.
- Usuario personalizado `apps.usuarios.Usuario`.
- Roles iniciales definidos en `Usuario.Rol`.
- Apps creadas segun arquitectura inicial.
- Modelos base iniciales:
  - `Zona`.
  - `Iglesia`.
  - `Usuario`.
  - `Periodo`.
  - `ParametroGeneral`.
  - `Miembro`.
  - `Familia`.
  - `MiembroFamilia`.
  - `Cargo`.
  - `AsignacionCargo`.
  - `Ministerio`.
  - `ParticipacionMinisterio`.
  - `RegistroAuditoria`.
- Admin basico para modelos iniciales.
- Migraciones iniciales creadas y aplicadas.

### Multi-Iglesia

- `IglesiaScopedModel` como modelo abstracto para datos con campo `iglesia`.
- Helpers de alcance por iglesia en `apps.core.iglesias`:
  - `usuario_es_nacional`.
  - `obtener_iglesia_usuario`.
  - `filtrar_queryset_por_iglesia`.
  - `IglesiaQuerysetMixin`.
- `IglesiaScopedAdminMixin` usa los helpers de alcance por iglesia.

### Seed Inicial

- Comando idempotente:

```bash
python manage.py seed_inicial
```

- El seed crea:
  - zonas base;
  - Iglesia Nacional;
  - Iglesia Filial Pruebas;
  - cargos base;
  - parametros generales;
  - periodo anual actual;
  - grupos Django por cada rol de `Usuario.Rol`.

### Usuarios de Prueba

- Comando idempotente:

```bash
python manage.py seed_usuarios_prueba
```

- Usuarios nacionales creados:
  - `admin_nacional`: `ADMIN_NACIONAL`, iglesia `NACIONAL`.
  - `auditor_nacional`: `AUDITOR_NACIONAL`, iglesia `NACIONAL`.
- Usuarios filiales creados:
  - `pastor_pruebas`: `PASTOR_FILIAL`, iglesia `PRUEBAS`.
  - `secretario_pruebas`: `SECRETARIO_FILIAL`, iglesia `PRUEBAS`.
  - `tesorero_pruebas`: `TESORERO_FILIAL`, iglesia `PRUEBAS`.
  - `lectura_pruebas`: `SOLO_LECTURA`, iglesia `PRUEBAS`.
- Contrasena de desarrollo usada: `Cambiar12345!`.
- Todos quedan con grupo Django alineado con su rol.
- El superusuario tecnico `admin` fue normalizado como `SUPERADMIN`, iglesia `NACIONAL`.

## Datos Base Creados

El comando `seed_inicial` fue ejecutado en la base local.

### Iglesias

- `NACIONAL`: Iglesia Nacional.
- `PRUEBAS`: Iglesia Filial Pruebas.

### Zonas

- Costa.
- Sierra.
- Oriente.
- Insular.

### Cargos

- Presidente.
- Vicepresidente.
- Secretario.
- Tesorero.
- Auditor.
- Vocal.
- Pastor.
- Encargado.
- Lider de ministerio.
- Maestro.

### Parametros

- `APORTE_NACIONAL_PORCENTAJE`.
- `ESCUELA_DOMINICAL_DIA_CORTE`.
- `CERTIFICADOS_PREFIJO`.
- `CERTIFICADOS_SECUENCIAL_INICIAL`.

### Grupos

Se creo un grupo Django por cada rol inicial:

- `SUPERADMIN`
- `ADMIN_NACIONAL`
- `PRESIDENTE_NACIONAL`
- `VICEPRESIDENTE_NACIONAL`
- `SECRETARIO_NACIONAL`
- `TESORERO_NACIONAL`
- `AUDITOR_NACIONAL`
- `PASTOR_FILIAL`
- `ENCARGADO_FILIAL`
- `SECRETARIO_FILIAL`
- `TESORERO_FILIAL`
- `LIDER_MINISTERIO`
- `MAESTRO`
- `SOLO_LECTURA`

## Validado

- Docker levanta y Django responde en `http://localhost:8020`.
- `/admin/` responde correctamente.
- `/api/health/` responde correctamente.
- `python manage.py check` no reporta issues.
- `python manage.py makemigrations --check --dry-run` no reporta cambios pendientes.
- `seed_inicial` fue probado dos veces y es idempotente.
- `seed_usuarios_prueba` fue ejecutado y es idempotente.
- Usuarios de prueba tienen rol, grupo e iglesia correctos.
- Existe comando para normalizar el superusuario tecnico:
  `python manage.py normalizar_superusuario --username admin`.
- Helpers/decoradores de permisos funcionales en `apps.core.permisos`.
- Dashboard inicial usa la matriz de permisos para mostrar modulos disponibles por rol.
- Modulo Miembros iniciado con listado, busqueda, filtro por estado, detalle,
  creacion, edicion, acciones pastorales iniciales y alcance por iglesia.
- Familias integradas al detalle de Miembros:
  - crear familia desde un miembro;
  - vincular miembro a familia existente de la misma iglesia.
- Modulo Familias iniciado con listado, detalle, creacion, edicion y agregado
  de integrantes.
- Familias permite desactivar vinculos familiares sin borrar historial.
- Al crear o editar familia, el jefe de hogar queda vinculado como
  `REPRESENTANTE` activo y debe pertenecer a la misma iglesia.
- Matrimonios implementados dentro del flujo Miembros/Familias:
  - modelo `Matrimonio`;
  - registro desde el detalle de miembro;
  - actualizacion de estado civil a `CASADO`;
  - vinculacion opcional de ambos miembros como `CONYUGE` en una familia.
- `normalizar_superusuario --username admin` fue ejecutado correctamente.
- La matriz funcional inicial de permisos por modulo quedo documentada.
- Tests de `apps.core` cubren permisos, login y dashboard inicial.
- Tests de `apps.miembros` cubren acceso, permisos, busqueda, detalle,
  creacion, edicion, acciones pastorales iniciales y aislamiento por iglesia.
- Tests de familias dentro de Miembros cubren creacion, vinculacion, duplicados,
  permisos y aislamiento por iglesia.
- Tests de `apps.familias` cubren listado, detalle, creacion, edicion,
  agregado de integrantes, permisos y aislamiento por iglesia.
- Tests de `apps.familias` tambien cubren desactivacion/reactivacion de vinculos
  y ajuste de jefe de hogar.
- Tests de matrimonios cubren registro, duplicados, permisos, alcance por
  iglesia, estado civil y vinculos familiares opcionales.
- Tests de `apps.api` cubren health publico, autenticacion, permisos, busqueda
  y alcance por iglesia para Miembros/Familias/Matrimonios.
- Tests de `apps.cargos` cubren listado, detalle, creacion, validaciones,
  finalizacion, permisos y aislamiento por iglesia.
- API de Cargos/directivas expone cargos y asignaciones en modo consulta,
  protegida por permisos y alcance por iglesia.
- Tests de `apps.ministerios` cubren listado, detalle, creacion, validaciones,
  participaciones, finalizacion, permisos y aislamiento por iglesia.
- Tailwind ya no usa CDN.
- Compose dev y prod validan correctamente.

## Pendiente Proximo Recomendado

Siguiente bloque recomendado:

1. Agregar API de consulta para Ministerios.
2. Iniciar el siguiente modulo funcional pequeno: Escuela Dominical.

No conviene iniciar vistas de modulos grandes hasta cerrar permisos y acceso por
iglesia.

## Comandos Utiles

Levantar desarrollo:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Ver logs:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f web
```

Ejecutar migraciones:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
```

Ejecutar seed:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py seed_inicial
```

Crear o actualizar usuarios de prueba:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py seed_usuarios_prueba
```

Normalizar superusuario tecnico:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py normalizar_superusuario --username admin
```

Validar Django:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
```

Validar migraciones pendientes:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check --dry-run
```

## Documentos Relacionados

- [Requerimientos vigentes](requerimientos.md)
- [Arquitectura](arquitectura.md)
- [Modelo multi-iglesia](multi_iglesia.md)
- [Seed inicial](seed_inicial.md)
- [Usuarios de prueba](usuarios_prueba.md)
- [Matriz de permisos y roles](matriz_permisos_roles.md)
- [Seguridad](seguridad.md)
- [Pendientes](pendientes.md)
- [Tailwind CSS](tailwind.md)
