"""
extractor.py
------------
Este es el "cerebro" del proyecto: toma el texto plano de una noticia
y saca dos tipos de informacion:

    1) Menciones de dias de la semana junto con el numero (digito) de
       dia del mes que los acompana, verificando que ese numero sea
       un dia de mes valido (entre 1 y 31).
    2) Nombres de calles, avenidas, bulevares y colonias mencionados
       en el texto.

Decision de diseno:
    Se parte de la logica del script original del profesor (separar
    el texto en palabras con .split() y revisar la palabra siguiente a
    cada dia de la semana), pero convertida en funciones para poder
    reutilizarla con cualquier texto de noticia, no solo con un texto
    fijo escrito a mano.
"""

# El modulo "re" (expresiones regulares) es parte de la libreria
# estandar de Python. Se usa para reconocer patrones de texto como
# "avenida Reforma" sin tener que escribir un monton de "if" a mano.
import re


# Lista de los 7 dias de la semana en minusculas. Se usa una lista (y
# no, por ejemplo, escribir "if palabra == 'lunes' or ...") porque asi
# es mucho mas facil de leer y de modificar si hiciera falta agregar
# o quitar un dia.
DIAS_SEMANA = [
    "domingo", "lunes", "martes", "miercoles",
    "jueves", "viernes", "sabado",
]

# Palabras que, cuando aparecen justo antes de un nombre propio (una
# palabra que empieza con mayuscula), indican que ese nombre es una
# vialidad o una colonia. Se guardan en un diccionario para poder
# saber, ademas del nombre, de que TIPO de via se trata (calle,
# avenida, bulevar o colonia), que es justo lo que pide el proyecto.
PALABRAS_CLAVE_VIAS = {
    "calle": "calle",
    "avenida": "avenida",
    "av": "avenida",
    "bulevar": "bulevar",
    "blvd": "bulevar",
    "boulevard": "bulevar",
    "colonia": "colonia",
    "col": "colonia",
    "fraccionamiento": "fraccionamiento",
}

# Palabras que NO deben tratarse como parte de un nombre de calle,
# aunque empiecen con mayuscula (por ejemplo, si aparecen justo
# despues de "entre", que se usa para marcar el inicio de una segunda
# calle de referencia, no el nombre en si).
PALABRAS_DE_CORTE = {
    "entre", "y", "en", "el", "la", "los", "las", "de", "del",
    "hasta", "desde", "sur", "norte", "este", "oeste", "sentido",
}


def _es_dia_de_mes_valido(texto_numero: str):
    """
    Revisa si un texto representa un numero de dia de mes valido, es
    decir, un numero entero entre 1 y 31.

    Se separo esta validacion en su propia funcion (en vez de dejarla
    mezclada dentro del ciclo principal) porque es la pieza central
    que pide el ejercicio: "evaluar que el digito este en el rango de
    1 a 31". Al ser una funcion independiente, se puede probar por
    separado y se entiende de un vistazo que es lo que hace.

    Devuelve el numero como entero si es valido, o None si no lo es
    (por ejemplo, si no es un numero, o si es mayor a 31 o menor a 1).
    """
    # .isdigit() confirma que el texto esta hecho solo de digitos
    # (0-9), asi se descarta de inmediato algo como "Reforma".
    if not texto_numero.isdigit():
        return None

    numero = int(texto_numero)

    # Un mes nunca tiene un dia 0 ni un dia mayor a 31, sin importar
    # el mes; por eso se usa este rango fijo como validacion general.
    if 1 <= numero <= 31:
        return numero

    return None


def extraer_dias_y_digitos(texto: str) -> dict:
    """
    Recorre el texto palabra por palabra buscando dias de la semana
    (domingo, lunes, martes, etc). Cuando encuentra uno, revisa la
    palabra inmediatamente siguiente: si es un numero valido de dia
    de mes (1-31), lo guarda asociado a ese dia de la semana.

    Devuelve un diccionario donde cada llave es un dia de la semana y
    el valor es una LISTA de los numeros validos encontrados junto a
    ese dia (una lista, porque el mismo dia de la semana podria
    mencionarse mas de una vez en la misma noticia con distintas
    fechas).

    Ejemplo de salida:
        {"domingo": [9], "lunes": [10], "martes": [11]}
    """
    resultado = {}

    # .split() separa el texto en una lista de palabras usando los
    # espacios en blanco como separador (igual que en el script
    # original del profesor).
    palabras = texto.split()
    total_palabras = len(palabras)

    for indice in range(total_palabras):
        # .strip(",.;:") quita signos de puntuacion pegados a la
        # palabra (por ejemplo "domingo," se convierte en "domingo"),
        # y .lower() la pasa a minusculas para poder compararla contra
        # la lista DIAS_SEMANA sin importar como estaba escrita
        # originalmente ("Domingo", "DOMINGO", "domingo" cuentan igual).
        palabra_actual = palabras[indice].strip(",.;:").lower()

        if palabra_actual not in DIAS_SEMANA:
            # Si la palabra actual no es un dia de la semana, no hay
            # nada que hacer con ella y se sigue con la siguiente.
            continue

        # Si la palabra encontrada es el ULTIMO elemento del texto,
        # no existe una "palabra siguiente" que revisar, asi que se
        # evita el error de salirse del rango de la lista.
        if indice + 1 >= total_palabras:
            continue

        palabra_siguiente = palabras[indice + 1].strip(",.;:")
        numero_valido = _es_dia_de_mes_valido(palabra_siguiente)

        if numero_valido is None:
            # La palabra que sigue al dia de la semana no es un
            # numero valido de 1 a 31 (por ejemplo "35", o una
            # palabra como "Reforma"), asi que se descarta.
            continue

        # setdefault crea la lista vacia la primera vez que aparece
        # ese dia de la semana, y en las siguientes veces reutiliza la
        # lista que ya existe, para poder ir agregando mas numeros.
        resultado.setdefault(palabra_actual, []).append(numero_valido)

    return resultado


def extraer_vias_urbanas(texto: str) -> list:
    """
    Busca en el texto menciones de calles, avenidas, bulevares y
    colonias, identificandolas por una palabra clave (como "calle" o
    "avenida") seguida del nombre propio de la via.

    Devuelve una lista de diccionarios, cada uno con:
        - "tipo": calle / avenida / bulevar / colonia / fraccionamiento
        - "nombre": el nombre encontrado (por ejemplo "Reforma")

    Decision de diseno:
        Se uso una expresion regular en vez de repetir el patron de
        ".split() + revisar palabra siguiente" que se uso para los
        dias de la semana, porque aqui el nombre de una via puede
        tener MAS de una palabra (por ejemplo "Lazaro Cardenas" o
        "Ramirez Mendez"), y las expresiones regulares permiten
        capturar varias palabras seguidas que empiecen con mayuscula
        de una forma mucho mas simple que hacerlo a mano palabra por
        palabra.
    """
    resultados = []

    # Se arma un patron que junta todas las palabras clave (calle,
    # avenida, bulevar, colonia, etc.) separadas por "|" (que en
    # expresiones regulares significa "o"), para buscarlas todas de
    # una sola vez sin importar mayusculas/minusculas.
    palabras_clave_patron = "|".join(PALABRAS_CLAVE_VIAS.keys())

    # Explicacion del patron completo:
    #   (?i:calle|avenida|...)  -> Grupo 1: la palabra clave, sin
    #                              importar mayusculas/minusculas
    #                              (el "(?i:...)" aplica IGNORECASE
    #                              SOLO dentro de ese grupo)
    #   \s+                     -> uno o mas espacios en blanco
    #   ((?:[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ]*\s?){1,4})
    #                           -> Grupo 2: de 1 a 4 palabras seguidas
    #                              que empiezan con MAYUSCULA (asi se
    #                              exige que sea un nombre propio real,
    #                              y no cualquier palabra en minuscula
    #                              que aparezca despues de la palabra
    #                              clave)
    patron = re.compile(
        r"((?i:" + palabras_clave_patron + r"))\s+"
        r"((?:[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ]*\s?){1,4})"
    )

    for coincidencia in patron.finditer(texto):
        palabra_clave = coincidencia.group(1).lower()
        nombre_crudo = coincidencia.group(2).strip()

        # El nombre capturado puede traer de mas alguna palabra de
        # corte al final (por ejemplo "Reforma entre" en vez de solo
        # "Reforma"), asi que se recorta ahi si aparece alguna.
        palabras_nombre = nombre_crudo.split()
        nombre_limpio = []
        for palabra in palabras_nombre:
            if palabra.lower() in PALABRAS_DE_CORTE:
                break
            nombre_limpio.append(palabra.rstrip(","))

        if not nombre_limpio:
            # Si despues de limpiar no quedo ningun nombre util, se
            # descarta esta coincidencia.
            continue

        resultados.append({
            "tipo": PALABRAS_CLAVE_VIAS[palabra_clave],
            "nombre": " ".join(nombre_limpio),
        })

    return resultados
