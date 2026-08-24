"""
database.py
-----------
Modulo encargado de TODO lo relacionado con MySQL: conectarse, crear
las DOS tablas que pide el proyecto, y guardar la informacion que
extraen scraper.py y extractor.py.

Las dos tablas son:
    1) dias_digitos  -> guarda cada mencion valida de un dia de la
                         semana junto con su numero de dia de mes.
    2) vias_urbanas  -> guarda las calles, avenidas, bulevares y
                         colonias identificadas (tanto las del
                         catalogo semilla del IMIP como las detectadas
                         en noticias reales).
"""

import mysql.connector
from mysql.connector import Error as MySQLError


class DatabaseError(Exception):
    """Error propio para identificar rapido fallos de base de datos."""
    pass


def conectar(config: dict):
    """Abre y devuelve una conexion a MySQL."""
    try:
        return mysql.connector.connect(**config)
    except MySQLError as error:
        raise DatabaseError(f"No se pudo conectar a MySQL: {error}") from error


def crear_tablas(conexion, nombre_tabla_dias: str, nombre_tabla_vias: str) -> None:
    """
    Crea las dos tablas del proyecto si todavia no existen, para que
    el programa se pueda ejecutar de inmediato sin tener que preparar
    la base de datos a mano.
    """
    consulta_dias = f"""
        CREATE TABLE IF NOT EXISTS {nombre_tabla_dias} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            dia_semana VARCHAR(20) NOT NULL,
            digito_dia INT NOT NULL,
            noticia_titulo VARCHAR(500),
            noticia_url VARCHAR(1000),
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    # La columna "nombre" es UNIQUE junto con "tipo" (una misma calle
    # no deberia repetirse dos veces con el mismo tipo), lo que
    # permite usar INSERT IGNORE para no duplicar vias que ya estan
    # en el catalogo cuando se vuelven a encontrar en una noticia.
    consulta_vias = f"""
        CREATE TABLE IF NOT EXISTS {nombre_tabla_vias} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tipo VARCHAR(30) NOT NULL,
            nombre VARCHAR(200) NOT NULL,
            verificada BOOLEAN DEFAULT FALSE,
            fuente VARCHAR(1000),
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY tipo_nombre_unico (tipo, nombre)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    try:
        cursor = conexion.cursor()
        cursor.execute(consulta_dias)
        cursor.execute(consulta_vias)
        conexion.commit()
        cursor.close()
    except MySQLError as error:
        raise DatabaseError(f"No se pudo crear las tablas: {error}") from error


def guardar_dias_digitos(
    conexion, nombre_tabla: str, dias_digitos: dict,
    noticia_titulo: str = "", noticia_url: str = "",
) -> int:
    """
    Guarda en la base de datos cada combinacion de dia de la semana +
    numero de dia de mes que encontro extractor.extraer_dias_y_digitos().

    Recibe un diccionario como {"lunes": [10], "martes": [11]} y lo
    recorre para insertar una FILA por cada numero encontrado (ya que
    un mismo dia de la semana puede tener varios numeros asociados en
    la misma noticia).

    Devuelve cuantas filas se insertaron.
    """
    consulta = f"""
        INSERT INTO {nombre_tabla}
            (dia_semana, digito_dia, noticia_titulo, noticia_url)
        VALUES (%s, %s, %s, %s)
    """

    filas_insertadas = 0
    try:
        cursor = conexion.cursor()
        for dia_semana, lista_digitos in dias_digitos.items():
            for digito in lista_digitos:
                cursor.execute(
                    consulta, (dia_semana, digito, noticia_titulo, noticia_url)
                )
                filas_insertadas += 1
        conexion.commit()
        cursor.close()
    except MySQLError as error:
        raise DatabaseError(f"No se pudo guardar dias/digitos: {error}") from error

    return filas_insertadas


def guardar_vias_urbanas(
    conexion, nombre_tabla: str, vias: list,
    verificada: bool = False, fuente: str = "",
) -> dict:
    """
    Guarda en la base de datos una lista de vias urbanas (calles,
    avenidas, bulevares, colonias), evitando duplicados gracias a la
    restriccion UNIQUE sobre (tipo, nombre) y a INSERT IGNORE.

    El parametro "verificada" se usa para distinguir entre las vias
    que vienen del catalogo oficial semilla (verificada=True) y las
    que se detectaron automaticamente en el texto de una noticia
    (verificada=False), ya que estas ultimas podrian tener errores de
    extraccion.

    Devuelve un resumen con cuantas fueron nuevas y cuantas ya
    existian.
    """
    consulta = f"""
        INSERT IGNORE INTO {nombre_tabla} (tipo, nombre, verificada, fuente)
        VALUES (%s, %s, %s, %s)
    """

    resumen = {"nuevas": 0, "duplicadas": 0}
    try:
        cursor = conexion.cursor()
        for via in vias:
            cursor.execute(
                consulta, (via["tipo"], via["nombre"], verificada, fuente)
            )
            if cursor.rowcount == 1:
                resumen["nuevas"] += 1
            else:
                resumen["duplicadas"] += 1
        conexion.commit()
        cursor.close()
    except MySQLError as error:
        raise DatabaseError(f"No se pudo guardar vias urbanas: {error}") from error

    return resumen


def buscar_vias_por_nombre(conexion, nombre_tabla: str, texto_busqueda: str) -> list:
    """
    Busca en la tabla de vias urbanas todas las filas cuyo nombre
    contenga el texto de busqueda (sin importar mayusculas/
    minusculas), y devuelve el resultado como una lista de
    diccionarios. Esta funcion es la que usa api.py para responder a
    las consultas de la API.
    """
    consulta = f"""
        SELECT id, tipo, nombre, verificada, fuente, fecha_registro
        FROM {nombre_tabla}
        WHERE nombre LIKE %s
        ORDER BY nombre
    """

    try:
        # dictionary=True hace que cada fila se devuelva como un
        # diccionario (columna -> valor) en vez de como una simple
        # tupla, lo cual es mucho mas comodo para despues convertir
        # el resultado a formato JSON en la API.
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(consulta, (f"%{texto_busqueda}%",))
        filas = cursor.fetchall()
        cursor.close()
    except MySQLError as error:
        raise DatabaseError(f"No se pudo realizar la busqueda: {error}") from error

    return filas


def listar_vias(conexion, nombre_tabla: str) -> list:
    """Devuelve TODAS las vias urbanas guardadas en la base de datos."""
    consulta = f"""
        SELECT id, tipo, nombre, verificada, fuente, fecha_registro
        FROM {nombre_tabla}
        ORDER BY tipo, nombre
    """
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(consulta)
        filas = cursor.fetchall()
        cursor.close()
    except MySQLError as error:
        raise DatabaseError(f"No se pudo listar las vias: {error}") from error

    return filas
