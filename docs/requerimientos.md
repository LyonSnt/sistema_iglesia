# Requerimientos Vigentes

## Alcance

Ecclesia es un sistema centralizado para una organizacion religiosa nacional.

La organizacion tiene:

- Una iglesia nacional principal.
- Mas de 30 iglesias filiales.
- Directivos nacionales.
- Usuarios y responsables por filial.

## Decision de datos

Se usara una sola base PostgreSQL:

```text
sistema_iglesia
```

No se usara multi-tenant por base de datos en esta fase.

No se crearan:

- Base `master`.
- Bases por iglesia filial.
- Rutas tenant como `/pruebas/`.
- Variables `TENANT_*`.
- Routers dinamicos por tenant.

## Separacion de informacion

La separacion se hara por:

- Campo `iglesia` en modelos sensibles.
- Roles nacionales y filiales.
- Permisos granulares.
- Filtros obligatorios por iglesia.
- Auditoria.

## Flujo esperado

Cada iglesia filial administra sus datos:

- Miembros.
- Familias.
- Ministerios.
- Asistencia.
- Finanzas locales.
- Documentos.
- Inventario.

La iglesia nacional puede ver y controlar, segun permisos:

- Reportes nacionales.
- Auditoria.
- Aportes nacionales.
- Iglesias con pendientes.
- Traslados.
- Certificados.
- Control general.

## Iglesia de pruebas

Para validacion tecnica y funcional se creara una filial:

```text
codigo: PRUEBAS
nombre: Iglesia Filial Pruebas
tipo: FILIAL
```

Esta filial no representa una base separada. Es un registro normal de `Iglesia`
dentro de `sistema_iglesia`.

## Regla central

Un usuario de filial debe operar como si el sistema fuera solo de su iglesia.

Un usuario nacional debe poder consolidar informacion de las filiales segun su
rol y permisos, sin entrar a bases separadas.
