# Certificados Institucionales

## Alcance Actual

El modulo de Certificados esta implementado inicialmente para Escuela Dominical:

- cambio de nivel confirmado;
- egreso a Jovenes;
- emision individual o por lote;
- numeracion unica;
- PDF;
- anulacion sin borrado.

Los demas certificados institucionales quedan definidos en esta hoja funcional,
pero no estan implementados todavia.

## Principios Generales

- Un certificado o constancia debe emitirse desde datos ya existentes en el
  sistema.
- La emision no debe modificar el hecho que certifica.
- Todo documento emitido debe tener numero unico cuando sea institucional.
- La anulacion no borra ni reutiliza numeros.
- Los firmantes se guardan historicamente al momento de emitir.
- Si faltan datos obligatorios o firmantes vigentes, no se debe consumir
  numeracion.
- Cada tipo documental debe respetar alcance por iglesia y permisos del modulo
  que origina la informacion.

## Regla funcional

- Cada cambio de nivel confirmado genera derecho a un certificado.
- El egreso del nivel 5 hacia Jovenes tambien genera un certificado final.
- La promocion no emite automaticamente el documento.
- `SECRETARIO_FILIAL` emite certificados individualmente o por lote.
- `PASTOR_FILIAL` y `SOLO_LECTURA` pueden consultar los documentos emitidos.
- Solo se certifican resultados de promocion confirmados.
- Una promocion puede tener un unico certificado.

## Acceso

- Listado y pendientes: `/certificados/`.
- Emision individual: operacion `POST` desde el listado.
- Emision por lote: operacion `POST` por proceso de promocion confirmado.
- Consulta PDF: documento en linea protegido por rol y alcance de iglesia.
- Anulacion: formulario protegido para usuarios con gestion de certificados.

## Firmantes

Antes de emitir deben existir asignaciones vigentes en la iglesia para:

- `Pastor`.
- `Director de Escuela Dominical`.

Los nombres quedan guardados en el certificado como datos historicos. Un cambio
posterior de autoridades no modifica documentos ya emitidos.

Las asignaciones se administran desde el modulo Cargos/directivas. Si falta uno
de los dos firmantes vigentes, la emision se rechaza sin consumir numeracion.

## Numeracion

El numero se genera con:

- `CERTIFICADOS_PREFIJO`.
- `CERTIFICADOS_SECUENCIAL_INICIAL`.

El valor del secuencial representa el siguiente numero disponible y se
incrementa dentro de la misma transaccion de emision. Ejemplo: `EC-000001`.

La emision es idempotente: repetir la accion sobre la misma promocion devuelve
el certificado existente y no crea otro numero.

## Documento

El PDF usa formato A4 horizontal inspirado en el certificado institucional:

- bordes y detalles dorados;
- iglesia y titulo de graduacion;
- nombre destacado del alumno;
- nivel completado y periodo lectivo;
- Proverbios 22:6;
- fecha de graduacion;
- firmas de Pastor y Director;
- numero unico del certificado.

## Anulacion

Los certificados no se eliminan ni se renumeran. Una anulacion conserva el
registro, usuario, fecha y motivo, y el PDF queda marcado como anulado.

## Dependencia

Los PDF se generan con `reportlab`, declarado en `backend/requirements.txt`.

## Tipos Documentales Institucionales Futuros

### Constancia de membresia

Objetivo:

- certificar que una persona consta como miembro de una iglesia filial.

Fuente funcional:

- modulo Miembros.

Datos minimos:

- iglesia;
- nombres y apellidos;
- identificacion si existe;
- fecha de membresia;
- estado actual de membresia;
- fecha de emision;
- firmante pastoral vigente.

Reglas:

- solo debe emitirse para miembros de la iglesia del usuario;
- no debe emitirse para fallecidos o trasladados como constancia vigente;
- debe conservar historico si luego cambia el estado del miembro.

### Constancia de bautismo

Objetivo:

- certificar que una persona fue bautizada.

Fuente funcional:

- modulo Miembros.

Datos minimos:

- iglesia;
- nombres y apellidos;
- fecha de bautismo;
- fecha de emision;
- firmante pastoral vigente.

Reglas:

- requiere fecha de bautismo registrada;
- no debe modificar la fecha de bautismo;
- si falta fecha de bautismo, la emision debe rechazarse.

### Constancia de traslado

Objetivo:

- certificar un traslado aceptado entre iglesias filiales.

Fuente funcional:

- modulo Traslados.

Datos minimos:

- miembro;
- iglesia origen;
- iglesia destino;
- fecha de solicitud;
- fecha de aceptacion;
- estado aceptado;
- firmante autorizado.

Reglas:

- solo aplica a traslados aceptados;
- no aplica a traslados solicitados, rechazados o anulados;
- debe conservar origen y destino historicos.

### Certificacion de cargo o directiva

Objetivo:

- certificar que una persona ocupa u ocupo un cargo eclesiastico.

Fuente funcional:

- modulo Cargos/directivas.

Datos minimos:

- iglesia;
- cargo;
- persona asignada;
- fecha de inicio;
- fecha de fin si existe;
- estado de la asignacion;
- fecha de emision;
- firmante autorizado.

Reglas:

- puede emitirse para cargos vigentes o historicos;
- debe distinguir claramente si el cargo esta vigente o finalizado;
- no debe cambiar roles ni accesos.

### Constancia pastoral

Objetivo:

- emitir una constancia general respaldada por autoridad pastoral.

Fuente funcional:

- Miembros y Cargos/directivas.

Datos minimos:

- miembro;
- iglesia;
- motivo o texto controlado;
- fecha de emision;
- firmante pastoral vigente.

Reglas:

- debe evitar texto completamente libre sin control institucional;
- debe quedar auditada o al menos trazable por usuario emisor;
- debe requerir permisos pastorales o administrativos definidos.

## Priorizacion Recomendada

1. Constancia de membresia.
2. Constancia de bautismo.
3. Constancia de traslado aceptado.
4. Certificacion de cargo o directiva.
5. Constancia pastoral general.

La prioridad responde a frecuencia de uso real, dependencia de datos ya
implementados y riesgo operativo bajo.

## Reglas Comunes Para Implementacion Futura

Antes de implementar un nuevo tipo documental debe definirse:

- fuente funcional exacta;
- datos obligatorios;
- estado minimo requerido;
- firmantes;
- permisos de emision y consulta;
- numeracion compartida o especifica;
- si permite emision por lote;
- condiciones de anulacion;
- texto institucional;
- formato PDF.

## Pendientes Funcionales

- Validar plantilla institucional, logotipo o fondo oficial.
- Definir si todos los tipos documentales comparten la misma numeracion.
- Definir cuales documentos requieren auditoria explicita.
- Definir si se usara un modelo generico de certificados o modelos
  especializados por tipo.
