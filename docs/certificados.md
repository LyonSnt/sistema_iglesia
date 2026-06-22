# Certificados de Escuela Dominical

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
