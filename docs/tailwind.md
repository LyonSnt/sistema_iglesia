# Tailwind CSS

## Decision

Ecclesia usara Tailwind compilado con Node, sin CDN en produccion.

No se usara Vite al inicio porque Django + HTMX no requiere bundling avanzado de JavaScript en esta fase.

No se usara `django-tailwind` al inicio para mantener el build frontend explicito y desacoplado de Django.

## Estructura

```text
backend/
├── package.json
├── tailwind.config.js
└── static/
    └── css/
        ├── input.css
        └── app.css
```

`input.css` es la fuente Tailwind. `app.css` es el archivo compilado y no se versiona.

## Desarrollo

El entorno de desarrollo levanta un servicio `tailwind` con Node:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

El servicio ejecuta:

```bash
npm install && npm run watch:css
```

Esto compila `backend/static/css/app.css` y lo actualiza cuando cambian templates, apps o clases CSS.

## Produccion

El `Dockerfile` tiene una etapa Node (`assets`) que ejecuta:

```bash
npm run build:css
```

La imagen final Python recibe el CSS compilado desde esa etapa. Node no queda instalado en la imagen final.

## Comandos manuales

```bash
npm run watch:css
npm run build:css
```

## Pendiente

- Agregar `package-lock.json` cuando se ejecute `npm install` por primera vez y decidir si se versiona para builds reproducibles.
