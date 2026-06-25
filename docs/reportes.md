# Estrategia General De Reportes

Ultima actualizacion: 2026-06-24.

## Objetivo

Los reportes de Ecclesia deben permitir supervision nacional y control local sin
romper la separacion por iglesia.

Un reporte no reemplaza la operacion del modulo. Su funcion es consolidar,
comparar, auditar o resumir informacion ya registrada por los flujos
funcionales.

## Tipos De Reportes

### Reportes nacionales

Uso:

- supervision de todas las filiales;
- comparacion por zona, filial, periodo o estado;
- seguimiento de pendientes;
- control administrativo nacional.

Acceso:

- `SUPERADMIN`;
- `ADMIN_NACIONAL`, segun matriz de permisos.

Regla:

- un reporte nacional puede consolidar filiales, pero no debe permitir operar
  registros locales desde la pantalla del reporte.

### Reportes locales

Uso:

- control operativo de una filial;
- revision pastoral, administrativa o financiera local;
- seguimiento interno por periodo o estado.

Acceso:

- roles filiales autorizados por el modulo correspondiente;
- `SOLO_LECTURA` cuando la matriz lo permita.

Regla:

- un usuario de filial solo debe ver datos de su iglesia.

## Reportes Implementados

### Reporte financiero consolidado

Ruta:

```text
/reportes/finanzas/
```

Alcance:

- nacional.

Fuente funcional:

- cierres mensuales financieros cerrados;
- aportes nacionales asociados a cierres.

Filtros:

- filial;
- zona;
- anio;
- mes.

Totales:

- ingresos;
- egresos;
- saldo local;
- aporte generado;
- aporte pagado;
- aporte pendiente.

Reglas:

- solo considera cierres en estado `CERRADO`;
- un cierre anulado para correccion no debe consolidarse;
- aportes se muestran segun su estado vigente.

### Reporte nacional de traslados

Ruta:

```text
/reportes/traslados/
```

Alcance:

- nacional.

Fuente funcional:

- solicitudes de traslado entre iglesias filiales.

Filtros:

- estado;
- iglesia origen;
- iglesia destino;
- fecha desde;
- fecha hasta;
- busqueda por miembro o iglesia.

Totales:

- total de traslados;
- conteo por estado.

Reglas:

- debe conservar historial aunque el miembro ya pertenezca a la iglesia
  destino;
- debe permitir supervision del flujo origen/destino sin operar el traslado
  desde el reporte.

### Reporte nacional de inventario

Ruta:

```text
/reportes/inventario/
```

Alcance:

- nacional.

Fuente funcional:

- activos de inventario registrados por filiales.

Filtros:

- filial;
- zona;
- categoria;
- estado;
- busqueda por codigo, nombre, categoria, ubicacion o iglesia.

Totales:

- total de activos;
- activos vigentes;
- valor referencial total;
- conteo por estado.

Reglas:

- debe mostrar activos dados de baja como parte del historial cuando el filtro
  lo permita;
- no debe permitir modificar activos desde el reporte.

## Criterios Comunes

### Filtros Minimos

Cuando aplique, todo reporte debe evaluar:

- filial;
- zona;
- periodo o rango de fechas;
- estado;
- busqueda textual.

No todos los reportes necesitan todos los filtros. La seleccion depende del
modulo.

### Periodos

Los reportes financieros usan `anio` y `mes` cuando su fuente son cierres.

Los reportes de eventos o flujos usan rango de fechas:

- `desde`;
- `hasta`.

Los reportes de Escuela Dominical y certificados deben preferir `Periodo`
cuando la informacion dependa de ciclo anual.

### Totales Y Resumenes

Cada reporte debe incluir, cuando sea util:

- conteo total;
- conteos por estado;
- sumas monetarias;
- saldo o pendiente;
- subtotales por filial o zona si el reporte lo requiere.

Los totales deben calcularse sobre el mismo conjunto filtrado que ve el usuario.

### Alcance Por Iglesia

Los reportes nacionales pueden consultar multiples iglesias.

Los reportes locales deben usar alcance por iglesia, igual que vistas,
formularios, API y exportaciones.

Nunca se debe confiar en filtros de iglesia enviados por el cliente para ampliar
el alcance de un usuario filial.

### Estados

Los reportes deben respetar estados funcionales:

- registros anulados no deben mezclarse con vigentes salvo que el reporte sea
  historico;
- cierres financieros anulados no entran en consolidado financiero;
- activos dados de baja pueden aparecer en inventario si el filtro lo permite;
- traslados rechazados o anulados se conservan como historial del flujo.

### Limites Iniciales

Los reportes web pueden mostrar una cantidad limitada de filas para mantener la
pantalla util.

Los totales deben calcularse sobre todo el conjunto filtrado, no solo sobre las
filas visibles.

## Exportaciones

Las exportaciones aun no son un bloque implementado.

Cuando se implementen, deben respetar:

- mismos filtros visibles;
- mismo alcance por iglesia;
- mismas reglas de permisos;
- fecha y usuario que genero la exportacion cuando aplique;
- identificacion del reporte, periodo y filtros usados.

## Impresion Y PDF

No todo reporte debe generar PDF.

PDF aplica mejor cuando:

- el documento se entrega oficialmente;
- requiere firmas;
- requiere numeracion;
- queda como respaldo institucional.

Para supervision operativa, una vista web o exportacion puede ser suficiente.

## Prioridad De Nuevos Reportes

Orden recomendado:

1. Reportes que ayuden a supervision nacional obligatoria.
2. Reportes que cierren procesos ya implementados.
3. Reportes que reduzcan errores operativos.
4. Reportes locales recurrentes para pastor, encargado, secretario o tesorero.
5. Reportes historicos o analiticos de menor uso.

## Reportes Candidatos Futuros

Sin comprometer implementacion inmediata, los candidatos funcionales son:

- miembros por filial, estado, edad o membresia;
- familias por filial y estado;
- escuela dominical por periodo, clase, asistencia y promociones;
- certificados emitidos/anulados por periodo;
- documentos adjuntos por modulo y estado;
- auditoria por modulo, usuario, filial y fecha;
- cargos/directivas vigentes por filial;
- ministerios y participaciones activas por filial.

Cada nuevo reporte debe documentar su fuente funcional, filtros, totales,
alcance y permisos antes de implementarse.
