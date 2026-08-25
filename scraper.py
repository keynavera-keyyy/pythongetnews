import warnings

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

ENCABEZADOS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "es-MX,es;q=0.9"}


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
            continue

        titulo = etiqueta_titulo.get_text(strip=True)
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

    return "\n".join(parrafos_utiles)
