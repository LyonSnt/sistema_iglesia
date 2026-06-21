# Modelo Multi-Iglesia con Una Sola Base

## Modelo

Ecclesia es un sistema centralizado multi-iglesia con una sola base PostgreSQL.

No se usara multi-tenant por base de datos en esta fase. No habra base `master`,
bases por iglesia, rutas tipo `/pruebas/` ni routers dinamicos por tenant.

La separacion de datos se hara por `iglesia`, roles, permisos y filtros
obligatorios.

## Estructura organizacional

- Una iglesia nacional.
- Varias iglesias filiales.
- Las filiales administran sus propios datos dentro del mismo sistema.
- La nacional consulta reportes, auditoria y control general segun permisos.

Ejemplo:

```text
sistema_iglesia
├── Iglesia Nacional
├── Iglesia Filial Pruebas
├── Iglesia Filial 1
├── Iglesia Filial 2
└── ...
```

## Regla principal

Todo modelo sensible debe tener `iglesia`.

## Acceso

Usuarios de filial:

- Solo pueden ver datos de su iglesia.
- No deben poder modificar `iglesia` desde formularios normales.

Usuarios nacionales:

- Pueden ver informacion segun rol y permisos.
- No necesariamente pueden modificar todo.
- Pueden consolidar reportes nacionales sin consultar multiples bases.

## Iglesia de pruebas

Para validacion tecnica y funcional se usara una filial de prueba:

```text
codigo: PRUEBAS
nombre: Iglesia Filial Pruebas
tipo: FILIAL
```

Esta iglesia servira para probar permisos, filtros, miembros, familias,
finanzas, aportes, reportes y auditoria sin tocar datos reales.

`PRUEBAS` no es un tenant separado; es un registro de `Iglesia` dentro de la
misma base `sistema_iglesia`.

## Capas donde aplicar filtro por iglesia

- Querysets.
- Managers.
- Vistas.
- Formularios.
- Admin.
- DRF serializers/viewsets.
- Reportes.
- Exportaciones.
- Tareas Celery.

## Reglas

- Nunca confiar en `iglesia_id` enviado por el cliente.
- Resolver iglesia desde `request.user`.
- Registrar auditoria en acciones criticas.
- No eliminar datos criticos fisicamente.
- No crear bases separadas por filial.
- No agregar variables `TENANT_*` mientras el alcance sea una sola organizacion nacional.
