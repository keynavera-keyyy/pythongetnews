import os

URL_FEED_NOTICIAS = "https://www.elvigia.net/rss/feed.html?r=77"

LIMITE_NOTICIAS = 15

URL_DESCARGAS_IMIP = "https://sigimip.org.mx/descargas.html"
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "pythongetnews"),
}

TABLA_DIAS_DIGITOS = "dias_digitos"
TABLA_VIAS_URBANAS = "vias_urbanas"

API_HOST = os.environ.get("API_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("API_PORT", "8000"))
