"""
scraper.py
----------
Modulo encargado de traer informacion desde internet: primero la lista
de noticias (desde el feed de El Vigia), y despues el texto completo
de cada noticia (entrando a la pagina de cada articulo).

Decision de diseno:
    Se separo en DOS pasos (lista de noticias, y luego texto completo)
    en vez de uno solo, porque el feed de noticias NO trae el texto
    completo del articulo (solo el titulo y a veces un fragmento). El
    texto completo, que es donde estan los cierres de calles con dias
    y numeros, solo esta disponible entrando a la pagina de cada
    noticia por separado.
"""

import warnings

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

# El feed de El Vigia esta en formato Atom (un tipo de XML). Al usar
# "html.parser" (que no distingue XML de HTML) para leerlo,
# BeautifulSoup muestra una advertencia recomendando el parser "xml".
# Ese parser depende de la libreria externa lxml, que el proyecto no
# puede usar, asi que se silencia esta advertencia concreta a
# proposito.
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Encabezado que se manda en cada peticion HTTP para identificar el
# programa ante el servidor, y para reducir la posibilidad de que el
# sitio rechace la peticion por parecer trafico automatizado sin
# identificar.
ENCABEZADOS = {"User-Agent": "pythongetnews/2.0 (proyecto educativo UABC)"}


class ScraperError(Exception):
    """Error propio para identificar rapido cualquier fallo de red."""
    pass


def _descargar(url: str, timeout: int = 10) -> str:
    """
    Descarga el contenido de una URL como texto. Es una funcion
    interna (por eso el guion bajo al inicio) que usan las otras dos
    funciones publicas de este modulo, para no repetir el mismo
    bloque de try/except dos veces.
    """
    try:
        respuesta = requests.get(url, headers=ENCABEZADOS, timeout=timeout)
        respuesta.raise_for_status()
    except requests.exceptions.RequestException as error:
        raise ScraperError(f"No se pudo descargar '{url}': {error}") from error

    return respuesta.text


def obtener_lista_noticias(url_feed: str, limite: int = None) -> list:
    """
    Descarga el feed de noticias y devuelve una lista de diccionarios
    con el titulo y el enlace de cada noticia.

    El feed de El Vigia usa el formato Atom, donde cada noticia esta
    dentro de una etiqueta <entry> (a diferencia del formato RSS 2.0
    clasico, que usa <item>). Dentro de cada <entry>, el titulo esta
    en <title> y el enlace esta en el ATRIBUTO href de la etiqueta
    <link> (no en su texto, como en RSS 2.0).
    """
    xml_texto = _descargar(url_feed)
    soup = BeautifulSoup(xml_texto, "html.parser")

    noticias = []
    for entrada in soup.find_all("entry"):
        etiqueta_titulo = entrada.find("title")
        etiqueta_enlace = entrada.find("link")

        if not etiqueta_titulo or not etiqueta_enlace:
            # Si a una entrada le falta el titulo o el enlace, no
            # sirve de nada y se descarta.
            continue

        titulo = etiqueta_titulo.get_text(strip=True)
        # El enlace esta guardado como ATRIBUTO href, no como texto:
        # <link href="https://..." />, por eso se usa .get("href") en
        # vez de .get_text().
        enlace = etiqueta_enlace.get("href", "").strip()

        if not enlace:
            continue

        noticias.append({"titulo": titulo, "enlace": enlace})

    if limite is not None:
        noticias = noticias[:limite]

    return noticias


def obtener_texto_articulo(url: str) -> str:
    """
    Entra a la pagina de una noticia especifica y extrae el texto
    completo del cuerpo de la nota (sin menus, publicidad ni pie de
    pagina), para poder analizarlo despues con extractor.py.

    Decision de diseno:
        En vez de buscar una etiqueta con un nombre de clase CSS muy
        especifico (que puede cambiar si el sitio actualiza su
        diseno), se uso un metodo mas general: se toman TODOS los
        parrafos <p> de la pagina, y se descartan los que son
        demasiado cortos (menos de 40 caracteres), ya que en la
        practica los parrafos de menus, botones o pie de pagina son
        casi siempre frases muy cortas, mientras que los parrafos de
        una noticia real son mucho mas largos. Esto hace el scraper
        mas resistente a pequenos cambios de diseno del sitio.
    """
    html = _descargar(url)
    soup = BeautifulSoup(html, "html.parser")

    parrafos_utiles = []
    for parrafo in soup.find_all("p"):
        texto_parrafo = parrafo.get_text(strip=True)

        if len(texto_parrafo) >= 40:
            parrafos_utiles.append(texto_parrafo)

    # Se unen todos los parrafos utiles en un solo texto grande,
    # separados por un salto de linea, para que extractor.py pueda
    # analizar la noticia completa de una sola vez.
    return "\n".join(parrafos_utiles)
