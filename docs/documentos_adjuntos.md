# Documentos Adjuntos

## Objetivo

Definir el uso funcional de documentos adjuntos reutilizables por modulo.

El modelo `DocumentoAdjunto` es generico, pero cada modulo debe mostrar y
aceptar solo los tipos documentales que tienen sentido para su proceso.

## Reglas Generales

- Todo documento adjunto pertenece a una iglesia.
- El documento debe pertenecer a la misma iglesia del registro asociado.
- En traslados, la iglesia del documento corresponde a la iglesia origen del
  traslado.
- Los archivos permitidos son PDF, imagenes y documentos de oficina.
- La anulacion es logica: el archivo no se borra fisicamente.
- La anulacion requiere motivo.
- El tipo documental debe ser coherente con el modulo asociado.

## Tipos Por Modulo

### Cargos Y Autoridades

Tipos permitidos:

- Acta.
- Otro.

Uso esperado:

- acta de designacion;
- acta de finalizacion o reemplazo;
- soporte institucional excepcional.

No corresponde adjuntar facturas, garantias o fotos como soporte ordinario de un
cargo.

### Traslados

Tipos permitidos:

- Acta.
- Otro.

Uso esperado:

- solicitud firmada;
- carta o acta de traslado;
- soporte pastoral o administrativo.

No corresponde usar tipos financieros o de inventario para traslados.

### Finanzas Locales

Tipos permitidos:

- Comprobante.
- Factura.
- Otro.

Uso esperado:

- comprobante de ingreso;
- comprobante de egreso;
- factura o respaldo de compra;
- soporte excepcional cuando no exista comprobante formal.

No corresponde adjuntar fotos o garantias como tipo principal de un movimiento
financiero.

### Inventario

Tipos permitidos:

- Factura.
- Foto.
- Garantia.
- Acta.
- Comprobante.
- Otro.

Uso esperado:

- factura de compra;
- foto del activo;
- garantia;
- acta de entrega, baja o donacion;
- comprobante relacionado con adquisicion o reparacion;
- soporte excepcional.

Inventario mantiene el conjunto mas amplio porque puede necesitar soportes
financieros, fisicos y administrativos.

## Criterio Para Nuevos Modulos

Antes de integrar documentos adjuntos en un nuevo modulo se debe definir:

- tipos permitidos;
- quien puede adjuntar documentos;
- quien puede descargarlos;
- quien puede anularlos;
- si algun tipo es obligatorio para completar el proceso;
- si el documento afecta auditoria nacional o reportes.

## Estado Funcional

La clasificacion por modulo esta aplicada para Cargos, Traslados, Finanzas e
Inventario. El formulario muestra solo los tipos permitidos y la validacion del
modelo rechaza tipos no permitidos para el registro asociado.
