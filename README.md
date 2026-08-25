# pythongetnews

Programa en Python que analiza noticias reales del periódico **El
Vigía** (Ensenada, B.C.) para detectar avisos de **cierres de calles**,

1. Los **días de la semana** mencionados junto con su **número de día
   del mes**
2. Las **calles, avenidas, bulevares y colonias** mencionadas.

Toda la información se guarda en una base de datos **MySQL**, y el
proyecto incluye una **API propia** (sin frameworks externos)

# Qué hice

El proyecto está dividido en 6 módulos

| Archivo | Qué hace |
|---|---|
| `main.py` | Archivo principal. Orquesta todo el proceso paso a paso. |
| `scraper.py` | Descarga la lista de noticias del feed de El Vigía y el texto completo de cada artículo. |
| `extractor.py` | Analiza el texto: valida días/dígitos (1-31) y extrae calles/avenidas/colonias. |
| `catastro.py` | Documenta la fuente oficial de calles/colonias de Ensenada (IMIP) y provee un catálogo semilla real. |
| `database.py` | Se conecta a MySQL, crea las 2 tablas, guarda e imprime los datos. |
| `api.py` | API HTTP propia (con `http.server`, sin Flask) para consultar las vías guardadas. |
| `config.py` | Configuración centralizada (URLs y datos de conexión a MySQL). |

# El paso a paso

1. **Investigación de la fuente de noticias:** se buscó un periódico
   real de Ensenada que publique avisos de cierres viales. Se
   encontró que **El Vigía** publica un feed de noticias en formato **Atom** (un tipo de XML pensado para que los programas lean noticias automáticamente), disponible en `https://www.elvigia.net/rss/feed.html?r=77` para la sección General, que es donde se publican este tipo de avisos.

2. **Investigación del catastro de Ensenada:** se buscó la base de
   datos oficial de calles y colonias de Ensenada. Se encontró que el
   organismo responsable es el **IMIP** (Instituto Municipal de
   Investigación y Planeación), que publica capas geoespaciales
   (calles, colonias, manzanas) para descarga pública en
   `https://sigimip.org.mx/descargas.html`se optó por dos cosas: (a) `catastro.py` sí entra a esa página con `requests` y `BeautifulSoup` para listar qué capas ofrecen, dejando documentada la fuente oficial con código real; y (b) se armó un **catálogo semilla** de calles, avenidas y colonias de Ensenada que sirve como catálogo de referencia utilizable dentro de la herramientas permitidas.

3. **Descarga de noticias:** `scraper.py` descarga el feed y, por cada
   noticia, entra a su página para leer el texto completo

4. **Extracción de días y dígitos:** `extractor.py` recorre el texto
   palabra por palabra buscando los 7 días de la semana. Cuando encuentra uno, revisa si la palabra siguiente es un número válido de día de mes (entre 1 y 31) y lo guarda; si no es válido (por ejemplo "35"), lo descarta.

5. **Extracción de vías urbanas:** también en `extractor.py`, se usa
   una expresión regular para encontrar palabras clave como "calle",
   "avenida", "bulevar" o "colonia" seguidas de un nombre propio permitiendo capturar nombres de más de una palabra como "Lázaro Cárdenas".

6. **Guardado en MySQL:** `database.py` crea dos tablas
   (`dias_digitos` y `vias_urbanas`) y guarda ahí los resultados,
   evitando duplicados en el catálogo de vías gracias a una
   restricción `UNIQUE`.

7. **API de consulta:** `api.py` levanta un servidor con el módulo
   `http.server` (parte de Python, no requiere instalar nada) que
   responde en `/vias` con el catálogo completo, o en
   `/vias?nombre=Reforma` con una búsqueda filtrada.

---

# Por qué decidi esto

- **RSS/Atom en vez de raspar el HTML de la portada:** un feed de
  noticias tiene una estructura fija (título, enlace, fecha) que casi
  nunca cambia, a diferencia del diseño visual de una página, que sí
  puede cambiar en cualquier momento y romper un scraper basado en
  clases CSS específicas.

- **Extraer el texto del artículo usando "todos los párrafos largos"
  en vez de una clase CSS exacta:** esto hace el scraper más
  resistente a cambios de diseño del sitio, a costa de ser un poco
  menos preciso.

- **`_es_dia_de_mes_valido()` como función separada:** es el corazón
  del requisito de "evaluar que el dígito esté en el rango de 1 a
  31", así que se aisló en su propia función para que sea fácil de
  leer, probar y confirmar que hace exactamente eso y nada más.

- **Expresión regular para las vías urbanas, en vez de repetir el
  patrón de "revisar la palabra siguiente":** un nombre de calle
  puede tener varias palabras ("Lázaro Cárdenas", "Club Rotario"), y
  una expresión regular permite capturar esa secuencia de palabras
  con mayúscula de forma mucho más simple que hacerlo a mano.

- **`(?i:...)` aplicado SOLO a la palabra clave y no al nombre:**
  durante las pruebas se descubrió que aplicar `IGNORECASE` a todo el
  patrón hacía que el programa reconociera por error palabras en
  minúscula como si fueran nombres de calles. Se corrigió para que
  solo la palabra clave (calle/avenida/etc.) ignore mayúsculas, pero
  el nombre siga exigiendo mayúscula inicial real, como corresponde a
  un nombre propio.

- **Dos tablas separadas (`dias_digitos` y `vias_urbanas`) en vez de
  una sola:** son dos tipos de información distintos con su propia
  estructura; mezclarlos en una sola tabla obligaría a dejar columnas
  vacías según el tipo de dato, lo cual no es una buena práctica de
  diseño de bases de datos.

- **Columna `verificada` en `vias_urbanas`:** permite distinguir entre
  las vías que vienen del catálogo oficial semilla y las que el programa detectó automáticamente en el texto de una noticia.

# Versión de Python usada

**Python 3.13.5**

# Cómo ejecutarlo

# 1. Clonar el repositorio

```bash
git clone https://github.com/TU-USUARIO/pythongetnews.git
cd pythongetnews
```

# 2. Crear un entorno virtual (recomendado)

```bash
python3 -m venv venv
source venv/bin/activate          # En Windows: venv\Scripts\activate
```

# 3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

# 4. Tener MySQL corriendo

```sql
CREATE USER IF NOT EXISTS 'tu_usuario'@'localhost' IDENTIFIED BY 'tu_contrasena';
GRANT ALL PRIVILEGES ON *.* TO 'tu_usuario'@'localhost';
FLUSH PRIVILEGES;
```

# 5. Configurar la conexión a la base de datos

El programa lee la configuración desde variables de entorno.

```bash
export DB_HOST=localhost
export DB_USER=tu_usuario
export DB_PASSWORD=tu_contrasena
export DB_NAME=pythongetnews
```

# 6. Ejecutar el programa

```bash
python3 main.py
```

Scraping y guardado, y además dejar la API corriendo al final:

```bash
python3 main.py --api
```

Con la API corriendo, se puede consultar desde el navegador o con
`curl`:

```bash
curl "http://127.0.0.1:8000/vias"
curl "http://127.0.0.1:8000/vias?nombre=Reforma"
```

---

# Estructura del proyecto

```
pythongetnews/
├── main.py            # Archivo principal (se ejecuta con python3 main.py)
├── scraper.py          # Descarga noticias y el texto de cada articulo
├── extractor.py         # Valida dias/digitos y extrae vias urbanas
├── catastro.py           # Catalogo semilla + investigacion de fuente IMIP
├── database.py            # Conexion, tablas y guardado en MySQL
├── api.py                  # API de consulta (http.server, sin librerias extra)
├── config.py                # Configuracion (URLs y datos de la BD)
├── requirements.txt          # Librerias necesarias
├── .gitignore
└── README.md
```
