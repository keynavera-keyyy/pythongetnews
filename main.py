"""
main.py
-------
Punto de entrada del programa. Es el unico archivo que se debe
ejecutar directamente.

Uso:
    python3 main.py             -> hace todo el proceso de scraping y
                                    guardado, y termina
    python3 main.py --api       -> hace el proceso de scraping y
                                    guardado, y despues deja corriendo
                                    la API de consulta

Decision de diseno:
    Igual que en la version anterior de este proyecto, main.py no
    contiene logica propia de scraping, extraccion ni base de datos:
    solo llama, en orden, a las funciones de los demas modulos
    (catastro.py, scraper.py, extractor.py, database.py, api.py) y
    muestra en pantalla el progreso, para que sea facil de leer de
    arriba a abajo.
"""

import sys

import api
import catastro
import config
import database
import extractor
import scraper


def cargar_catalogo_semilla(conexion) -> None:
    """
    Paso 1 del programa: guarda en la base de datos el catalogo
    semilla de vias urbanas reales de Ensenada (ver catastro.py),
    marcandolas como "verificadas" porque vienen de una lista
    curada, no de una extraccion automatica de texto.
    """
    print("\n[1/3] Cargando catalogo semilla de vias urbanas de Ensenada...")

    catalogo = catastro.obtener_catalogo_semilla()
    resumen = database.guardar_vias_urbanas(
        conexion,
        config.TABLA_VIAS_URBANAS,
        catalogo,
        verificada=True,
        fuente="Catalogo semilla (IMIP - sigimip.org.mx)",
    )

    print(
        f"      {resumen['nuevas']} vias nuevas del catalogo, "
        f"{resumen['duplicadas']} ya existian."
    )


def procesar_noticias(conexion) -> None:
    """
    Paso 2 del programa: descarga la lista de noticias, entra a cada
    una, extrae los dias/digitos y las vias urbanas mencionadas, y
    guarda todo en la base de datos.
    """
    print(f"\n[2/3] Descargando noticias desde:\n      {config.URL_FEED_NOTICIAS}")

    try:
        noticias = scraper.obtener_lista_noticias(
            config.URL_FEED_NOTICIAS, limite=config.LIMITE_NOTICIAS
        )
    except scraper.ScraperError as error:
        print(f"      Error al obtener la lista de noticias: {error}")
        return

    print(f"      Se encontraron {len(noticias)} noticias. Analizando cada una...")

    total_dias_guardados = 0
    total_vias_nuevas = 0

    for noticia in noticias:
        try:
            texto_articulo = scraper.obtener_texto_articulo(noticia["enlace"])
        except scraper.ScraperError as error:
            print(f"      Aviso: no se pudo leer '{noticia['titulo']}': {error}")
            continue

        dias_digitos = extractor.extraer_dias_y_digitos(texto_articulo)
        vias_encontradas = extractor.extraer_vias_urbanas(texto_articulo)

        if dias_digitos:
            filas = database.guardar_dias_digitos(
                conexion,
                config.TABLA_DIAS_DIGITOS,
                dias_digitos,
                noticia_titulo=noticia["titulo"],
                noticia_url=noticia["enlace"],
            )
            total_dias_guardados += filas

        if vias_encontradas:
            resumen_vias = database.guardar_vias_urbanas(
                conexion,
                config.TABLA_VIAS_URBANAS,
                vias_encontradas,
                verificada=False,
                fuente=noticia["enlace"],
            )
            total_vias_nuevas += resumen_vias["nuevas"]

    print(
        f"      Total: {total_dias_guardados} registros de dias/digitos guardados, "
        f"{total_vias_nuevas} vias nuevas detectadas en noticias."
    )


def main() -> int:
    print("=" * 65)
    print(" pythongetnews - Analisis de cierres viales (El Vigia, Ensenada)")
    print("=" * 65)

    try:
        conexion = database.conectar(config.DB_CONFIG)
        database.crear_tablas(
            conexion, config.TABLA_DIAS_DIGITOS, config.TABLA_VIAS_URBANAS
        )
    except database.DatabaseError as error:
        print(f"\nError de base de datos: {error}")
        print(
            "Revisa que MySQL este corriendo y que los datos de conexion "
            "en config.py (o tus variables de entorno) sean correctos."
        )
        return 1

    cargar_catalogo_semilla(conexion)
    procesar_noticias(conexion)

    print("\n[3/3] Proceso de scraping y guardado terminado.")
    conexion.close()

    # Si el programa se ejecuto como "python3 main.py --api", despues
    # de terminar el scraping se deja corriendo la API de consulta.
    if "--api" in sys.argv:
        api.iniciar_servidor(config.API_HOST, config.API_PORT)

    return 0


if __name__ == "__main__":
    sys.exit(main())
