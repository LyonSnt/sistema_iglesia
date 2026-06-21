# HTMX

## Objetivo

Usar HTMX para interfaces Django dinamicas sin convertir el sistema en una SPA.

## Convenciones

- Las vistas completas renderizan templates normales.
- Las interacciones parciales renderizan partials.
- Los partials deben vivir cerca del modulo que los usa.
- Los formularios HTMX deben devolver errores de validacion en el mismo partial.
- Toda vista debe aplicar permisos y filtro por iglesia antes de renderizar.

## Respuestas

- `200`: partial actualizado.
- `204`: accion exitosa sin contenido.
- `400`: formulario invalido.
- `403`: acceso denegado.

## Seguridad

- CSRF siempre activo.
- No confiar en datos del cliente para `iglesia`.
- Validar permisos antes de mutar datos.

## Pendiente

- Definir layout base.
- Definir convencion de nombres para partials.
- Crear mixins de vistas por iglesia.
