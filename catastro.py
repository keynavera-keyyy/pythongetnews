"""
catastro.py
-----------
Este modulo se encarga de la parte del proyecto que pide "buscar la
base de datos de Ensenada de catastro con las colonias, calles y
avenidas".

Investigacion realizada:
    El organismo que administra oficialmente la cartografia y el
    catastro del municipio de Ensenada es el IMIP (Instituto
    Municipal de Investigacion y Planeacion). Publican capas
    geoespaciales (calles, colonias, manzanas, etc.) para descarga
    publica en:

        https://sigimip.org.mx/descargas.html

    Esas capas vienen en formatos de Sistemas de Informacion
    Geografica (shapefiles, KML, etc.), que normalmente se procesan
    con librerias especializadas en geolocalizacion (por ejemplo
    geopandas o fiona). Como el proyecto pide usar UNICAMENTE
    requests, BeautifulSoup, mysql-connector y las librerias estandar
    de Python, no es posible procesar directamente esos archivos.

Decision de diseno:
    En vez de ignorar por completo esta parte del proyecto, se
    resolvio en dos niveles:

    1) Con requests + BeautifulSoup se revisa la pagina de descargas
       del IMIP y se listan los nombres de las capas disponibles
       (funcion listar_capas_imip), dejando documentado con codigo
       real donde esta la fuente oficial.
    2) Para tener un catalogo utilizable DENTRO de las limitaciones
       del proyecto, se uso un catalogo "semilla": una lista de
       calles, avenidas y colonias reales de Ensenada, tomadas de
       noticias reales de cierres viales de El Vigia. Este catalogo
       sirve para que la API de consulta (api.py) tenga datos con los
       que trabajar desde la primera ejecucion del programa, y para
       marcar como "verificada" una via urbana cuando el scraper la
       encuentra tambien mencionada en una noticia.
"""

import requests
from bs4 import BeautifulSoup

from scraper import ENCABEZADOS, ScraperError


# Catalogo semilla de vias urbanas reales de Ensenada. Cada elemento
# es una tupla (tipo, nombre). Se uso una lista de tuplas, en vez de
# un diccionario, porque puede haber mas de una via con el mismo
# nombre pero distinto tipo (por ejemplo, una "calle Reforma" y una
# "colonia Reforma" podrian coexistir).
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
    """
    Entra a la pagina de descargas del IMIP y devuelve la lista de
    nombres de capas geoespaciales que ofrecen (por ejemplo "Calles",
    "Colonias", "Manzanas"), para dejar documentada cual es la fuente
    oficial de este tipo de informacion en Ensenada.

    Esta funcion NO descarga ni procesa los archivos en si (como se
    explica arriba, eso requeriria librerias de GIS fuera del alcance
    permitido para este proyecto); solo confirma, mediante scraping
    real con requests y BeautifulSoup, que capas estan disponibles.
    """
    try:
        respuesta = requests.get(url_descargas, headers=ENCABEZADOS, timeout=10)
        respuesta.raise_for_status()
    except requests.exceptions.RequestException as error:
        raise ScraperError(
            f"No se pudo consultar la pagina de descargas del IMIP: {error}"
        ) from error

    soup = BeautifulSoup(respuesta.text, "html.parser")

    # Se buscan enlaces (<a>) cuyo texto no este vacio, ya que en la
    # pagina de descargas cada capa geoespacial se ofrece como un
    # enlace de descarga con el nombre de la capa como texto visible.
    nombres_capas = []
    for enlace in soup.find_all("a"):
        texto = enlace.get_text(strip=True)
        if texto and len(texto) < 80:
            nombres_capas.append(texto)

    return nombres_capas


def obtener_catalogo_semilla() -> list:
    """
    Devuelve el catalogo semilla de vias urbanas reales de Ensenada,
    convertido a la misma forma de diccionario que usa extractor.py,
    para poder guardarlo en la base de datos con la misma funcion de
    database.py que se usa para las vias detectadas en noticias.
    """
    return [
        {"tipo": tipo, "nombre": nombre}
        for tipo, nombre in CATALOGO_SEMILLA
    ]
