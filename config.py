"""
config.py
---------
Todos los "numeros magicos" y datos de configuracion del proyecto se
concentran aqui, para que nadie tenga que buscar dentro de scraper.py,
extractor.py o database.py si quiere cambiar, por ejemplo, la fuente
de noticias o los datos de conexion a MySQL.
"""

# Se importa el modulo "os" (viene incluido en Python, no hay que
# instalarlo) porque permite leer variables de entorno del sistema
# operativo con os.environ.get().
import os

# --------------------------------------------------------------------
# Fuente de noticias: Periodico El Vigia (Ensenada, B.C.)
# --------------------------------------------------------------------
# El Vigia es el periodico de mayor circulacion en Ensenada y publica
# un feed en formato Atom (un tipo de XML hecho para que los programas
# lean noticias de forma automatica) para la seccion "General", que es
# donde se publican los avisos de cierres de calles, vialidades, etc.
URL_FEED_NOTICIAS = "https://www.elvigia.net/rss/feed.html?r=77"

# Cuantas noticias como maximo se van a revisar en cada ejecucion.
LIMITE_NOTICIAS = 15

# --------------------------------------------------------------------
# Fuente del catalogo de calles/colonias/avenidas de Ensenada
# --------------------------------------------------------------------
# El organismo oficial que administra la cartografia y el catastro del
# municipio de Ensenada es el IMIP (Instituto Municipal de
# Investigacion y Planeacion). Publican capas geoespaciales (calles,
# colonias) para descarga publica en este sitio:
URL_DESCARGAS_IMIP = "https://sigimip.org.mx/descargas.html"

# --------------------------------------------------------------------
# Conexion a MySQL
# --------------------------------------------------------------------
# Igual que con el feed de noticias: los datos sensibles (usuario,
# contrasena) se leen primero desde variables de entorno del sistema
# operativo, y solo si no existen se usa un valor por defecto pensado
# para pruebas locales. Asi nunca queda una contrasena real escrita
# directamente en el codigo que se sube a GitHub.
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "pythongetnews"),
}

# Nombres de las dos tablas que pide el proyecto.
TABLA_DIAS_DIGITOS = "dias_digitos"
TABLA_VIAS_URBANAS = "vias_urbanas"

# --------------------------------------------------------------------
# Configuracion de la API de consulta
# --------------------------------------------------------------------
API_HOST = os.environ.get("API_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("API_PORT", "8000"))
