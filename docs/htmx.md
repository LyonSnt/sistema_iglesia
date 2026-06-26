# HTMX

Ultima actualizacion: 2026-06-25.

## Objetivo

Usar HTMX para interfaces Django dinamicas sin convertir el sistema en una SPA.

## Convenciones

- Las vistas completas renderizan templates normales.
- Las interacciones parciales renderizan partials.
- Los partials deben vivir cerca del modulo que los usa, dentro de la misma
  carpeta funcional de templates.
- Los partials reutilizables deben nombrarse con prefijo `_`, por ejemplo
  `_documentos_table.html`.
- Los formularios completos pueden usar nombres descriptivos como
  `miembro_form.html`, `movimiento_form.html` o `traslado_responder_form.html`.
- Cuando un formulario se use tanto como pagina completa como respuesta parcial,
  la vista debe decidir el template segun el tipo de solicitud y no duplicar la
  logica de permisos.
- Los formularios HTMX deben devolver errores de validacion en el mismo partial.
- Toda vista debe aplicar permisos y filtro por iglesia antes de renderizar.

## Layout Base

La plantilla `backend/templates/base.html` es la base de las pantallas normales.

Reglas:

- la navegacion principal y los mensajes globales pertenecen al layout base;
- los partials HTMX no deben incluir `base.html`;
- los partials solo deben renderizar el fragmento que sera reemplazado;
- las pantallas completas deben seguir funcionando aunque la mejora HTMX no se
  ejecute.

## Formularios HTMX

Reglas funcionales:

- validar permisos antes de construir opciones del formulario;
- no confiar en campos ocultos para `iglesia`, usuario actor o alcance;
- mantener los errores de validacion junto al campo correspondiente;
- devolver el mismo formulario con estado `400` cuando sea invalido;
- devolver el fragmento actualizado o redirigir de forma explicita cuando sea
  valido;
- conservar mensajes de exito/error visibles para el usuario.

Patrones recomendados:

- usar `hx-post` para acciones que crean, actualizan, finalizan, anulan o
  registran respuestas;
- usar `hx-get` para cargar formularios o fragmentos de lectura;
- usar `hx-target` sobre contenedores estables con id descriptivo;
- usar `hx-swap` explicito cuando el reemplazo no sea el comportamiento por
  defecto esperado;
- evitar que una accion parcial cambie informacion fuera del fragmento sin
  actualizar tambien el resumen visible.

## Respuestas

- `200`: partial actualizado.
- `204`: accion exitosa sin contenido.
- `400`: formulario invalido.
- `403`: acceso denegado.
- `404`: registro inexistente o fuera del alcance del usuario.

Cuando una accion exitosa modifica totales, listados o estados visibles, se
prefiere devolver el fragmento actualizado con `200` en vez de `204`.

## Seguridad

- CSRF siempre activo.
- No confiar en datos del cliente para `iglesia`.
- Validar permisos antes de mutar datos.
- Filtrar querysets por iglesia antes de buscar registros por id.
- Auditar acciones criticas igual que en vistas no HTMX.
- No exponer documentos adjuntos por URL directa sin validar permisos.

## Nombres Recomendados

- Partial de tabla reutilizable: `_nombre_table.html`.
- Partial de fila reutilizable: `_nombre_row.html`.
- Partial de resumen: `_nombre_resumen.html`.
- Formulario de accion: `objeto_accion_form.html`.
- Confirmacion de anulacion o baja: `objeto_anular.html` o `objeto_baja.html`.

## Pendiente Tecnico

- Crear mixins reutilizables para detectar solicitud HTMX y seleccionar
  template completo o partial.
- Crear helpers de respuesta para formularios validos e invalidos.
- Estandarizar contenedores `hx-target` en pantallas que crezcan con
  interacciones parciales.
