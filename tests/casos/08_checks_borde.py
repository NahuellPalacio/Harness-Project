# Los casos borde de los cuatro checks de desarrollo.
#
# Esto no compara contra ningun testigo: la respuesta correcta de cada caso la dice la
# regla — el ES09xx o la ley de accesibilidad que el check implementa — no una
# implementacion anterior. Lo que se repone aca es la mitad que mas importa de un check
# de nomenclatura: la NEGATIVA. Un check con falsos positivos se desactiva la primera
# semana, y entonces tampoco atrapa los verdaderos.
#
# Cada grupo de test_ trae al menos un caso POSITIVO (el check encuentra lo que tiene
# que encontrar) antes de sus casos negativos. Eso es lo que prueba que el check
# efectivamente corrio: un "no reporto nada" sin ese acompañante pasa igual si el check
# exploto o si nunca se ejecuto.
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "comun" / "hooks"))
from lib import reglas  # noqa: E402

import tempfile  # noqa: E402

DIR_CHECKS = RAIZ / "harnesses" / "desarrollo" / "checks"
TEMP = Path(tempfile.mkdtemp(prefix="gcba-harness-dev-borde-"))


def _correr(check, nombre, contenido, config=None):
    """Escribe `contenido` en `nombre` (relativo al directorio temporal, admite
    subcarpetas) y corre `check` -el .py de harnesses/desarrollo/checks, con guion-
    tal como lo haria el hook real: por ruta, con el evento minimo que arma
    Get-ArchivoEscrito / dev.archivo_escrito a partir de tool_input.file_path."""
    ruta = TEMP / nombre
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8")

    evento = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "tool_input": {"file_path": str(ruta)},
    }
    modulo = reglas._cargar(str(DIR_CHECKS / check))
    salida = modulo.verificar(evento, str(TEMP), config)
    return [s for s in (salida or []) if s]


# ── dev-dependencias ────────────────────────────────────────────────────────────

def test_dev_dependencias(t):
    con_rangos = '{ "dependencies": { "express": "^4.18.0", "lodash": "~4.17.21", "axios": "1.6.2" } }'
    r = _correr("dev-dependencias.py", "package.json", con_rangos)
    t.igual("un package.json con rangos produce un aviso", 1, len(r))
    t.verdadero("nombra las dos dependencias con rango", "express" in r[0] and "lodash" in r[0])
    t.no_contiene("no nombra la que si esta fijada", "axios", r[0])
    t.contiene("cita el estandar", "ES0901", r[0])

    exactas = '{ "dependencies": { "express": "4.18.0", "lodash": "4.17.21" } }'
    t.igual("todas exactas: silencio", 0, len(_correr("dev-dependencias.py", "package.json", exactas)))

    # composer usa las mismas formas de rango
    composer = '{ "require": { "laravel/framework": "^10.0", "guzzlehttp/guzzle": "7.8.1" } }'
    rc = _correr("dev-dependencias.py", "composer.json", composer)
    t.igual("composer.json tambien se revisa", 1, len(rc))

    # La mitad negativa
    t.igual("un json cualquiera no le incumbe", 0,
            len(_correr("dev-dependencias.py", "datos.json", con_rangos)))
    t.igual("lo que esta en node_modules no se toca", 0,
            len(_correr("dev-dependencias.py", "node_modules/algo/package.json", con_rangos)))
    t.igual("un package.json roto no explota, se saltea", 0,
            len(_correr("dev-dependencias.py", "package.json", "{ esto no es json")))


# ── dev-api-rutas ───────────────────────────────────────────────────────────────

def test_dev_api_rutas(t):
    mal = (
        'const rutas = {\n'
        '  crear:  "/api/crearUsuario",\n'
        '  ver:    "/api/usuario/{id}",\n'
        '  listar: "/api/v1/usuarios"\n'
        '};\n'
    )
    ra = _correr("dev-api-rutas.py", "rutas.ts", mal)
    todo = " ".join(ra)
    t.verdadero("detecta la ruta sin version", "sin version" in todo)
    t.verdadero("detecta el verbo en la ruta", "metodo HTTP" in todo)
    t.verdadero("detecta la coleccion en singular", "singular" in todo)
    t.no_contiene("no reporta la ruta que esta bien", "/api/v1/usuarios (", todo)

    bien = 'const r = { listar: "/api/v1/usuarios", ver: "/api/v1/usuarios/{id}" };'
    t.igual("rutas correctas: silencio", 0, len(_correr("dev-api-rutas.py", "rutas.ts", bien)))

    # El falso positivo que este check tiene que evitar si o si: una palabra que
    # EMPIEZA como un verbo pero no lo es. "postulaciones" arranca con "post".
    postulaciones = 'const r = { listar: "/api/v1/postulaciones", ver: "/api/v1/postulaciones/{id}" };'
    t.igual("postulaciones no se confunde con el verbo post", 0,
            len(_correr("dev-api-rutas.py", "rutas.ts", postulaciones)))

    # Una ruta que no es de API no le incumbe: si no, opinaria sobre todo el front.
    front = 'const r = { inicio: "/inicio/panel", detalle: "/noticia/{id}" };'
    t.igual("las rutas que no son de API no se tocan", 0,
            len(_correr("dev-api-rutas.py", "rutas.ts", front)))

    t.igual("un archivo sin rutas de API: silencio", 0,
            len(_correr("dev-api-rutas.py", "util.ts", "export const sumar = (a, b) => a + b;")))

    # El prefijo sale de la configuracion del proyecto, no esta clavado
    otro_prefijo = 'const r = { x: "/servicios/crearUsuario" };'
    cfg = {"prefijoApi": "servicios"}
    t.verdadero("respeta el prefijo de API que declara el proyecto",
                len(_correr("dev-api-rutas.py", "rutas.ts", otro_prefijo, cfg)) > 0)


# ── dev-infra-en-codigo ─────────────────────────────────────────────────────────

def test_dev_infra_en_codigo(t):
    con_ip = 'const cfg = { url: "http://10.51.2.30/api", puerto: 8080 };'
    ri = _correr("dev-infra-en-codigo.py", "config.ts", con_ip)
    t.igual("una IP en posicion de host produce un aviso", 1, len(ri))
    t.contiene("nombra la IP y su linea", "10.51.2.30", ri[0])

    t.igual("localhost no se reporta", 0,
            len(_correr("dev-infra-en-codigo.py", "config.ts", 'const u = "http://127.0.0.1:3000";')))
    t.igual("un nombre DNS es justamente lo correcto", 0,
            len(_correr("dev-infra-en-codigo.py", "config.ts",
                        'const u = "https://siccsir.buenosaires.gob.ar/api";')))

    # El falso positivo clasico: cuatro numeros con puntos que son una version.
    t.igual("una version no se confunde con una IP", 0,
            len(_correr("dev-infra-en-codigo.py", "config.ts", 'const version = "10.51.2.300";')))
    t.igual("un numero suelto con puntos tampoco", 0,
            len(_correr("dev-infra-en-codigo.py", "notas.ts", 'const build = "8.4.1.2";')))


# ── dev-accesibilidad-html ──────────────────────────────────────────────────────

def test_dev_accesibilidad_html(t):
    html_mal = (
        '<html>\n'
        '<body>\n'
        '  <h1>Uno</h1>\n'
        '  <h1>Dos</h1>\n'
        '  <img src="logo.png">\n'
        '  <input type="text">\n'
        '</body>\n'
        '</html>\n'
    )
    rh = _correr("dev-accesibilidad-html.py", "pagina.html", html_mal)
    todo = " ".join(rh)
    t.verdadero("detecta html sin lang", "sin atributo lang" in todo)
    t.verdadero("detecta img sin alt", "sin atributo alt" in todo)
    t.verdadero("detecta el control sin nombre", "sin forma de nombrarlos" in todo)
    t.verdadero("detecta los dos h1", "2 elementos <h1>" in todo)

    html_bien = (
        '<html lang="es">\n'
        '<body>\n'
        '  <h1>Titulo</h1>\n'
        '  <img src="logo.png" alt="Escudo del GCBA">\n'
        '  <label for="nombre">Nombre</label>\n'
        '  <input type="text" id="nombre">\n'
        '</body>\n'
        '</html>\n'
    )
    t.igual("un html correcto: silencio", 0,
            len(_correr("dev-accesibilidad-html.py", "pagina.html", html_bien)))

    # alt vacio es una afirmacion -"esta imagen es decorativa"- y es correcta.
    decorativa = '<html lang="es"><h1>x</h1><img src="linea.png" alt=""></html>'
    t.igual("alt vacio es correcto y no se reporta", 0,
            len(_correr("dev-accesibilidad-html.py", "pagina.html", decorativa)))

    # Un parcial no tiene <html> ni tiene por que tener h1.
    parcial = '<div class="tarjeta"><p>Un fragmento</p></div>'
    t.igual("un parcial sin h1 no se reporta", 0,
            len(_correr("dev-accesibilidad-html.py", "tarjeta.component.html", parcial)))

    # Los campos ocultos y los botones no llevan etiqueta.
    ocultos = ('<html lang="es"><h1>x</h1><input type="hidden" name="token">'
               '<input type="submit" value="Enviar"></html>')
    t.igual("hidden y submit no piden etiqueta", 0,
            len(_correr("dev-accesibilidad-html.py", "pagina.html", ocultos)))

    t.igual("un .ts no le incumbe al check de html", 0,
            len(_correr("dev-accesibilidad-html.py", "algo.ts", html_mal)))
