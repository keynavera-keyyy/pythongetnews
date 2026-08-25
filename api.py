import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

import config
import database


class ManejadorPeticiones(BaseHTTPRequestHandler):


    def _responder_json(self, datos, codigo_estado: int = 200) -> None:
        cuerpo = json.dumps(datos, default=str, ensure_ascii=False).encode("utf-8")

        self.send_response(codigo_estado)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self) -> None:
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
        print(f"[API] {self.address_string()} -> {formato % args}")


def iniciar_servidor(host: str, puerto: int) -> None:
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
