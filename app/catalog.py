ROOMS = [
    {
        "id": "habitacion-clasica",
        "name": "Habitación Clásica",
        "detail": "22 m² · Cama queen",
        "description": (
            "Un refugio cálido con acabados de madera, ropa de cama de algodón "
            "y todo lo esencial para descansar después de un día junto al mar."
        ),
        "category": "clasica",
        "price": 220.00,
        "featured": False,
        "rating": 4.6,
        "image": "/static/img/room-clasica.jpg",
        "alt": "Habitación clásica con cama queen y vista al jardín",
    },
    {
        "id": "habitacion-superior",
        "name": "Habitación Superior",
        "detail": "30 m² · Cama king",
        "description": (
            "Más espacio, balcón privado y una vista privilegiada a los "
            "jardines. Incluye desayuno buffet y acceso a la piscina."
        ),
        "category": "superior",
        "price": 320.00,
        "featured": True,
        "rating": 4.8,
        "image": "/static/img/room-superior.jpg",
        "alt": "Habitación superior con cama king y ventanales",
    },
    {
        "id": "suite-miramar",
        "name": "Suite Miramar",
        "detail": "48 m² · Vista al mar",
        "description": (
            "Nuestra suite insignia: sala de estar, cama king y un ventanal "
            "que enmarca el atardecer sobre el Pacífico."
        ),
        "category": "suite",
        "price": 480.00,
        "featured": True,
        "rating": 4.9,
        "image": "/static/img/room-suite.jpg",
        "alt": "Suite Miramar con cama amplia y luz natural",
    },
    {
        "id": "suite-terraza",
        "name": "Suite Terraza",
        "detail": "54 m² · Terraza privada",
        "description": (
            "Dos ambientes, tina exterior y una terraza privada rodeada de "
            "palmeras. Ideal para una escapada en pareja."
        ),
        "category": "suite",
        "price": 560.00,
        "featured": True,
        "rating": 4.9,
        "image": "/static/img/room-terraza.jpg",
        "alt": "Suite Terraza con cama king y puertas al jardín",
    },
    {
        "id": "habitacion-familiar",
        "name": "Habitación Familiar",
        "detail": "42 m² · 2 camas + sofá cama",
        "description": (
            "Pensada para compartir: dos camas matrimoniales, sofá cama y un "
            "espacio de estar para toda la familia."
        ),
        "category": "familiar",
        "price": 390.00,
        "featured": False,
        "rating": 4.7,
        "image": "/static/img/room-familiar.jpg",
        "alt": "Habitación familiar con cama amplia y cabecera de madera",
    },
    {
        "id": "suite-deluxe",
        "name": "Suite Deluxe",
        "detail": "40 m² · Jacuzzi privado",
        "description": (
            "Detalles de autor, iluminación cálida y un jacuzzi privado para "
            "cerrar el día con una experiencia de bienestar."
        ),
        "category": "suite",
        "price": 440.00,
        "featured": False,
        "rating": 4.8,
        "image": "/static/img/room-deluxe.jpg",
        "alt": "Suite Deluxe con jacuzzi y decoración contemporánea",
    },
]

# Nombre histórico del catálogo: los servicios del hotel se cargan con las
# mismas reglas de inventario y persistencia que antes usaban los productos.
PRODUCTS = ROOMS
