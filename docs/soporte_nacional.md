# Soporte Nacional Auditado A Filiales

## Objetivo

Definir cuando y como la administracion nacional puede apoyar a una iglesia
filial sin convertir el soporte en operacion local ordinaria.

Este documento no habilita nuevas funciones por si mismo. Establece criterios
funcionales para futuras implementaciones, auditoria y procedimientos internos.

## Principios

- La filial conserva la responsabilidad de su operacion diaria.
- La administracion nacional no debe operar modulos locales como rutina.
- Todo soporte nacional sobre datos de una filial debe ser excepcional,
  justificado, limitado y auditable.
- La intervencion debe resolver el menor alcance posible.
- No se deben compartir credenciales ni usar cuentas locales para actuar como
  administracion nacional.
- La supervision nacional debe privilegiar reportes, revision y acompanamiento
  antes que modificacion directa de datos.
- Cualquier intervencion sobre dinero, autoridades, certificados, traslados o
  documentos sensibles requiere mayor trazabilidad.

## Casos Permitidos

El soporte nacional puede considerarse cuando exista una de estas situaciones:

- una filial solicita ayuda formal para corregir un error que no puede resolver
  con sus permisos actuales;
- existe una inconsistencia entre filiales, por ejemplo en traslados, cargos o
  membresia;
- se requiere apoyo para alta inicial, reemplazo o recuperacion de autoridad
  principal de una filial;
- un cierre, aporte, certificado o documento queda bloqueado por una condicion
  administrativa que requiere validacion nacional;
- una migracion, carga inicial o correccion tecnica necesita supervision
  institucional;
- una auditoria nacional detecta datos incompatibles con las reglas vigentes.

## Casos No Permitidos

No debe tratarse como soporte nacional:

- registrar miembros, finanzas, asistencia, inventario o ministerios por
  comodidad de la filial;
- reemplazar el trabajo regular de pastor, encargado, secretario, tesorero,
  maestro o lider local;
- modificar decisiones pastorales locales sin solicitud o autorizacion;
- corregir datos sin motivo registrado;
- usar usuarios locales prestados;
- saltarse reglas multi-iglesia, permisos o filtros por iglesia.

## Niveles De Soporte

### Nivel 1: Orientacion

La administracion nacional guia a la filial, pero no modifica datos.

Ejemplos:

- indicar que pantalla o reporte revisar;
- explicar un flujo vigente;
- solicitar que la filial complete datos faltantes.

Auditoria requerida:

- no requiere auditoria de sistema si no existe cambio de datos;
- puede registrarse externamente como atencion administrativa.

### Nivel 2: Correccion Local Supervisada

La filial realiza la correccion con sus propios permisos y la administracion
nacional solo valida el criterio.

Ejemplos:

- anulacion de un movimiento local permitido por el sistema;
- correccion de un cargo vigente por parte de la autoridad local;
- actualizacion de documentos adjuntos por el usuario responsable.

Auditoria requerida:

- aplica la auditoria o historial propio del modulo afectado.

### Nivel 3: Intervencion Nacional Auditada

La administracion nacional interviene sobre datos de una filial cuando el caso
supera las capacidades locales y existe justificacion institucional.

Ejemplos:

- desbloqueo administrativo validado por autoridad nacional;
- correccion de inconsistencia entre dos filiales;
- asistencia ante ausencia o reemplazo de autoridad principal.

Auditoria requerida:

- registro explicito de solicitud, aprobacion, usuario ejecutor, modulo,
  iglesia afectada, registros afectados, motivo y resultado.

### Nivel 4: Intervencion Tecnica

`SUPERADMIN` realiza una accion tecnica excepcional para resolver datos,
permisos o estados que no deben exponerse como operacion funcional normal.

Ejemplos:

- reparacion de datos por migracion;
- correccion de una inconsistencia producida por error tecnico;
- restauracion controlada luego de una incidencia.

Auditoria requerida:

- registro tecnico e institucional, con antes/despues cuando aplique.

## Flujo Funcional

1. La filial o una autoridad nacional identifica la necesidad de soporte.
2. Se registra el motivo, modulo, iglesia afectada, registros involucrados y
   resultado esperado.
3. Se clasifica el nivel de soporte.
4. Si basta con orientacion o correccion local, la filial ejecuta la accion.
5. Si se requiere intervencion nacional, se valida la autorizacion institucional.
6. La accion se ejecuta con alcance minimo.
7. Se registra la auditoria correspondiente.
8. La filial confirma que el caso quedo resuelto.

## Datos Minimos De Auditoria

Para intervenciones de nivel 3 o 4 deben conservarse, como minimo:

- iglesia filial afectada;
- modulo o proceso afectado;
- registro o registros afectados;
- usuario solicitante;
- usuario que aprueba, cuando aplique;
- usuario ejecutor;
- motivo;
- accion realizada;
- estado anterior y nuevo cuando sea posible;
- fecha y hora;
- observaciones;
- documentos de soporte si existen.

## Criterios Por Modulo

### Iglesias Y Usuarios

La nacional puede gestionar alta de filiales, autoridad inicial, usuarios
delegados iniciales y reemplazos institucionales. Este es el principal punto de
soporte nacional esperado.

### Finanzas Locales

La administracion nacional no debe registrar movimientos locales por la filial.
El soporte debe orientarse a revision, correccion local supervisada o bloqueo de
acciones que afecten cierres y aportes nacionales.

Cuando un cierre ya genero aporte nacional, cualquier correccion debe tratarse
como caso sensible y no como edicion ordinaria.

### Aportes Nacionales

`ADMIN_NACIONAL` puede consultar aportes y registrar pagos nacionales segun las
reglas vigentes. Esto no implica permiso para operar la contabilidad local de
cada filial.

### Traslados

El soporte nacional puede intervenir cuando exista conflicto o inconsistencia
entre origen y destino. No debe reemplazar la aceptacion o rechazo local salvo
que exista autorizacion institucional clara.

### Cargos Y Autoridades

La nacional puede apoyar reemplazos o normalizaciones de autoridad principal.
Los cargos funcionales locales que sincronizan acceso deben auditarse con mayor
cuidado porque afectan permisos.

### Certificados

El soporte nacional debe limitarse a problemas de numeracion, firmantes,
anulacion justificada o consistencia institucional. La emision ordinaria sigue
siendo local.

### Documentos Adjuntos

Los reemplazos o anulaciones de documentos sensibles deben conservar motivo,
usuario y trazabilidad. El soporte nacional no debe usarse para cargar soportes
ordinarios de la filial.

## Regla De Implementacion Futura

Antes de habilitar pantallas o permisos de soporte nacional directo debe existir
un flujo explicito de solicitud, aprobacion, ejecucion y auditoria. Cualquier
permiso futuro debe estar separado de `ADMIN_NACIONAL` ordinario para evitar que
la supervision se convierta en operacion local permanente.
