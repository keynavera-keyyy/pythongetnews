import requests
from bs4 import BeautifulSoup

from scraper import ENCABEZADOS, ScraperError
CATALOGO_SEMILLA = [
    ("bulevar", "Lázaro Cárdenas"),
    ("bulevar", "Las Dunas"),
    ("calle", "Club Rotario"),
    ("calle", "De las Rocas"),
    ("calle", "Primera"),
    ("calle", "del Faro"),
    ("avenida", "Castillo"),
    ("avenida", "Reforma"),
    ("avenida", "Juárez"),
    ("avenida", "Ryerson"),
    ("colonia", "Puerto Azul"),
    ("colonia", "Ampliación Moderna"),
    ("colonia", "Fovissste"),
]


def listar_capas_imip(url_descargas: str) -> list:
    
    try:
        respuesta = requests.get(url_descargas, headers=ENCABEZADOS, timeout=10)
        respuesta.raise_for_status()
    except requests.exceptions.RequestException as error:
        raise ScraperError(
            f"No se pudo consultar la pagina de descargas del IMIP: {error}"
        ) from error

    soup = BeautifulSoup(respuesta.text, "html.parser")
    nombres_capas = []
    for enlace in soup.find_all("a"):
        texto = enlace.get_text(strip=True)
        if texto and len(texto) < 80:
            nombres_capas.append(texto)

    return nombres_capas


def obtener_catalogo_semilla() -> list:
    return [
        {"tipo": tipo, "nombre": nombre}
        for tipo, nombre in CATALOGO_SEMILLA
    ]
