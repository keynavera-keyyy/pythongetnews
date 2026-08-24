"""
api.py
------
Este modulo cumple con el punto del proyecto que pide: "crear una API
de consulta de las colonias, calles y avenidas de Ensenada en una base
de datos MySQL".

Decision de diseno:
    Normalmente una API en Python se construiria con un framework como
    Flask o FastAPI, pero el proyecto exige no usar librerias extra
    fuera de requests, BeautifulSoup, mysql-connector y las librerias
    estandar. Por eso, esta API se construyo usando UNICAMENTE el
    modulo "http.server", que viene incluido en Python y permite crear
    un servidor web basico sin instalar nada adicional.

Endpoints disponibles:
    GET /vias              -> devuelve TODAS las vias guardadas
    GET /vias?nombre=texto -> busca vias cuyo nombre contenga "texto"
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

import config
import database


class ManejadorPeticiones(BaseHTTPRequestHandler):
    """
    Esta clase hereda de BaseHTTPRequestHandler (de la libreria
    estandar) y define que debe hacer el servidor cada vez que recibe
    una peticion HTTP de tipo GET. Python llama automaticamente al
    metodo do_GET() por cada peticion que llega.
    """

    def _responder_json(self, datos, codigo_estado: int = 200) -> None:
        """
        Funcion auxiliar para no repetir el mismo bloque de codigo
        (armar encabezados, convertir a JSON, enviar la respuesta)
        cada vez que se quiere devolver una respuesta en formato JSON.
        """
        cuerpo = json.dumps(datos, default=str, ensure_ascii=False).encode("utf-8")

        self.send_response(codigo_estado)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self) -> None:
        """
        Se ejecuta automaticamente cada vez que alguien visita una
        URL de la API con el metodo GET (por ejemplo, al abrir la URL
        en un navegador, o al usar herramientas como curl o Postman).
        """
        # urlparse separa la URL en sus partes (ruta y parametros de
        # busqueda); parse_qs convierte los parametros de busqueda
        # (por ejemplo "?nombre=Reforma") en un diccionario de Python.
        url_separada = urlparse(self.path)
        ruta = url_separada.path
        parametros = parse_qs(url_separada.query)

        if ruta != "/vias":
            self._responder_json(
                {"error": "Ruta no encontrada. Usa /vias"}, codigo_estado=404
            )
            return

        try:
            conexion = database.conectar(config.DB_CONFIG)
        except database.DatabaseError as error:
            self._responder_json(
                {"error": f"No se pudo conectar a la base de datos: {error}"},
                codigo_estado=500,
            )
            return

        # parse_qs guarda cada parametro como una LISTA de valores
        # (por si la misma llave se repite en la URL), por eso se
        # accede con .get("nombre", [""])[0] para tomar solo el
        # primer valor, o una cadena vacia si no se mando el parametro.
        texto_busqueda = parametros.get("nombre", [""])[0]

        try:
            if texto_busqueda:
                resultados = database.buscar_vias_por_nombre(
                    conexion, config.TABLA_VIAS_URBANAS, texto_busqueda
                )
            else:
                resultados = database.listar_vias(conexion, config.TABLA_VIAS_URBANAS)
        except database.DatabaseError as error:
            self._responder_json({"error": str(error)}, codigo_estado=500)
            return
        finally:
            conexion.close()

        self._responder_json({"total": len(resultados), "resultados": resultados})

    def log_message(self, formato, *args):
        """
        Se sobreescribe este metodo (que normalmente imprime cada
        peticion en una sola linea de texto poco clara) para mostrar
        un mensaje mas facil de leer en la terminal cada vez que
        llega una peticion a la API.
        """
        print(f"[API] {self.address_string()} -> {formato % args}")


def iniciar_servidor(host: str, puerto: int) -> None:
    """
    Crea y arranca el servidor HTTP. Esta funcion se queda "esperando"
    peticiones para siempre (hasta que se detenga el programa con
    Ctrl+C), por lo que se ejecuta al final de main.py, cuando ya se
    guardo toda la informacion en la base de datos.
    """
    servidor = HTTPServer((host, puerto), ManejadorPeticiones)
    print(f"API escuchando en http://{host}:{puerto}/vias")
    print("Ejemplo de uso: "
          f"http://{host}:{puerto}/vias?nombre=Reforma")
    print("Presiona Ctrl+C para detener el servidor.")

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo la API...")
        servidor.server_close()
