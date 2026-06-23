# Seed Inicial

## Objetivo

Crear datos base idempotentes para que Ecclesia arranque con una estructura
operativa minima y consistente.

## Comando

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py seed_inicial
```

El comando puede ejecutarse varias veces. No duplica registros existentes.

## Datos creados

### Zonas

- Costa.
- Sierra.
- Oriente.
- Insular.

### Iglesias

- `NACIONAL`: Iglesia Nacional.
- `PRUEBAS`: Iglesia Filial Pruebas.

`PRUEBAS` es una filial de validacion dentro de la misma base. No es un tenant.

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
- Director de Escuela Dominical.

### Parametros

- `APORTE_NACIONAL_PORCENTAJE`: porcentaje base del aporte nacional.
- `ESCUELA_DOMINICAL_DIA_CORTE`: dia de corte para promociones.
- `CERTIFICADOS_PREFIJO`: prefijo documental.
- `CERTIFICADOS_SECUENCIAL_INICIAL`: siguiente numero disponible; se incrementa
  al emitir un certificado.
- `APORTES_RECIBOS_PREFIJO`: prefijo documental para recibos de aportes.
- `APORTES_RECIBOS_SECUENCIAL_INICIAL`: siguiente numero disponible; se
  incrementa al registrar un pago de aporte nacional.

### Grupos

Se crea un grupo Django por cada rol definido en `Usuario.Rol`.

El rol sigue siendo el identificador funcional principal del usuario. Los grupos
y permisos de Django se usan para granularidad, admin y validaciones futuras.

## Usuarios

El seed inicial no crea usuarios ni contrasenas.

Crear el primer superusuario con:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

Luego se podran crear comandos especificos para usuarios de prueba, evitando
credenciales debiles en el seed principal.
