# Usuarios de Prueba

## Objetivo

Crear cuentas de validacion para probar roles nacionales, roles filiales,
permisos y filtros por iglesia sin usar el superusuario tecnico.

## Comando

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py seed_usuarios_prueba
```

El comando es idempotente: puede ejecutarse varias veces sin duplicar usuarios.

## Contrasena de desarrollo

Si no se pasa una contrasena, el comando usa:

```text
Cambiar12345!
```

Esta contrasena es solo para desarrollo local. No debe usarse con datos reales.

Para definir otra contrasena:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py seed_usuarios_prueba --password "OtraClaveSegura123!"
```

Para reiniciar contrasenas de usuarios existentes:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py seed_usuarios_prueba --reset-passwords
```

## Usuarios creados

### Nacionales

| Usuario | Rol | Iglesia | Staff |
| --- | --- | --- | --- |
| `admin_nacional` | `ADMIN_NACIONAL` | `NACIONAL` | Si |
| `auditor_nacional` | `AUDITOR_NACIONAL` | `NACIONAL` | Si |

### Filial PRUEBAS

| Usuario | Rol | Iglesia | Staff |
| --- | --- | --- | --- |
| `pastor_pruebas` | `PASTOR_FILIAL` | `PRUEBAS` | No |
| `secretario_pruebas` | `SECRETARIO_FILIAL` | `PRUEBAS` | No |
| `tesorero_pruebas` | `TESORERO_FILIAL` | `PRUEBAS` | No |
| `lider_pruebas` | `LIDER_MINISTERIO` | `PRUEBAS` | No |
| `maestro_pruebas` | `MAESTRO` | `PRUEBAS` | No |
| `lectura_pruebas` | `SOLO_LECTURA` | `PRUEBAS` | No |

## Politica

- El superusuario tecnico se usa para administracion tecnica.
- Los usuarios de prueba se usan para validar reglas reales de acceso.
- Cada usuario debe tener:
  - `Usuario.rol` definido.
  - Grupo Django con el mismo nombre del rol.
  - Iglesia asociada.
- Los usuarios filiales no deben operar datos de otra iglesia.
- Los usuarios nacionales pueden consultar informacion consolidada segun rol y permisos.
- Las cuentas creadas o restablecidas con contrasena temporal deben cambiarla
  antes de acceder a los modulos.

## Nota sobre superusuario tecnico

Si el superusuario fue creado con `createsuperuser`, puede quedar con el rol por
defecto `SOLO_LECTURA`. Al ser `is_superuser=True`, conserva acceso total, pero
se recomienda asignarle rol `SUPERADMIN` y grupo `SUPERADMIN` para mantener
consistencia administrativa.

Para normalizarlo:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py normalizar_superusuario --username admin
```
