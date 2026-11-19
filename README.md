# Miramar Hotel Boutique

Sitio web de un hotel boutique frente al mar en Huanchaco, Trujillo. La
aplicación está construida con **Flask**, **SQLite** y estilos compilados con
**Tailwind CSS**.

## Secciones

El sitio público tiene tres secciones:

- **Inicio** (`/`): hero con carrusel, servicios, habitaciones destacadas,
  historia del hotel y llamada a reservar.
- **Habitaciones** (`/habitaciones`): catálogo de habitaciones y suites con
  búsqueda, filtros por tipo y ordenamiento por precio.
- **Contacto** (`/contacto`): datos del hotel, formulario de solicitud de
  reserva, mapa y preguntas frecuentes.

## Requisitos

- Python 3.10 o superior.
- Dependencias Python: `pip install -r requirements.txt`.
- No se necesita Node.js para ejecutar el sitio: `output.css` ya está
  compilado. Solo se requiere npm si vas a modificar los estilos.

## Ejecutar

```bash
python app.py
```

La aplicación queda disponible en `http://localhost:5000`.

## Base de datos

Flask-SQLAlchemy usa SQLite. El archivo se crea automáticamente en
`instance/miramar.db` y al arrancar se cargan las habitaciones definidas en
`app/catalog.py` con su inventario inicial.

Los mensajes del formulario de contacto se guardan en la tabla de mensajes y
pueden consultarse desde la base de datos.

## Estilos

Los estilos se compilan con Tailwind CSS:

```bash
npm install
npm run build:css
```

Para desarrollo con recarga automática:

```bash
npm run watch:css
```

## Estructura

- `app/templates/`: plantillas Jinja (base, inicio, habitaciones y contacto).
- `app/static/css/styles.css`: tokens de marca y estilos personalizados.
- `app/static/img/`: imágenes locales del hotel.
- `app/routes/`: rutas HTTP de las tres secciones.
- `app/services/`: reglas de negocio y acceso a datos.
- `app/catalog.py`: definición de habitaciones, precios y descripciones.
