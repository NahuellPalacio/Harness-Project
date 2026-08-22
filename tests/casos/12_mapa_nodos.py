# El mapa de nodos del codigo: los enlaces entre fichas, y el grafo que dibujan.
#
# Escenarios E-02 a E-17 de docs/cambios/mapa-de-nodos/spec.md. Los cuatro que faltan
# -E-01, E-18, E-19, E-20- tienen por sujeto una corrida de dev-iniciador-code y se
# verifican por lectura, ADR-0009: ningun test puede obligar a un modelo a enlazar.
import ast
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(RAIZ / "comun" / "hooks"))
from lib import reglas  # noqa: E402

CHECK = RAIZ / "harnesses" / "desarrollo" / "checks" / "dev-codebase-forma.py"
CHECKS_DEV = RAIZ / "harnesses" / "desarrollo" / "checks"
GENERADOR = RAIZ / "comun" / "bin" / "mapa-codigo.py"
FIXTURE = RAIZ / "tests" / "fixtures" / "proyecto-codebase"
ENLACES = "docs/codebase-enlaces"


def _hallazgos(nombre, dir_ficha=ENLACES, ruta_codebase=None):
    """`dir_ficha` es donde esta el archivo; `ruta_codebase` es lo que el proyecto tiene
    configurado como directorio del indice. Van separados a proposito: el unico test que
    los cruza es el del recorte, y si el helper los atara siempre juntos ese test miraria
    otra ficha -una sana- y pasaria sin probar nada."""
    ruta_codebase = ruta_codebase or dir_ficha
    archivo = FIXTURE / dir_ficha / nombre
    evento = {"hook_event_name": "PostToolUse", "tool_name": "Write",
              "cwd": str(FIXTURE), "tool_input": {"file_path": str(archivo)}}
    modulo = reglas._cargar(str(CHECK))
    return list(modulo.verificar(evento, str(FIXTURE), {"rutaCodebase": ruta_codebase}) or [])


# ── Los enlaces entre fichas ─────────────────────────────────────────────────────

def test_e02_una_dependencia_sin_ficha_se_nombra_sin_enlace_y_no_pasa_nada(t):
    """E-02 — la ficha sana enlaza a su hermana, vuelve al indice, apunta a un ADR de
    afuera del directorio y nombra Python y git sin enlace. Nada de eso es un hallazgo.

    Es el test que defiende contra el falso positivo, que es el modo de falla que mata
    un check: si `../adr/0008-...md` o `indice.md` dieran hallazgo, el aviso apareceria
    sobre fichas bien escritas y en dos semanas nadie lo lee."""
    t.igual("E-02: ficha sana con enlaces legitimos, sin hallazgos", [],
            _hallazgos("comun-hooks.md"))


def test_e04_un_enlace_a_una_ficha_que_no_existe_se_reporta(t):
    """E-04 — el enlace es la arista: si apunta a la nada, el grafo dibuja una arista
    falsa y el que la sigue no encuentra el archivo."""
    hallazgos = _hallazgos("comun-checks.md")
    t.igual("E-04: un hallazgo", 1, len(hallazgos))
    t.contiene("E-04: nombra la ficha de origen", "comun-checks.md", hallazgos[0])
    t.contiene("E-04: nombra el destino roto", "comun-reglas.md", hallazgos[0])
    t.contiene("E-04: y el segundo destino roto", "comun-bin.md", hallazgos[0])


def test_e03_una_ficha_con_wikilinks_se_reporta(t):
    """E-03 — GitHub no renderiza `[[wiki]]`: los muestra con los corchetes. El hallazgo
    dice con que se reemplaza, porque un aviso que no da la salida se ignora."""
    hallazgos = _hallazgos("comun-wiki.md")
    t.verdadero("E-03: al menos un hallazgo", len(hallazgos) >= 1)
    juntos = " ".join(hallazgos)
    t.contiene("E-03: nombra la ficha", "comun-wiki.md", juntos)
    t.contiene("E-03: dice que el problema son los wikilinks", "[[wiki]]", juntos)
    t.contiene("E-03: y da la salida", "markdown relativo", juntos)


def test_e03b_un_wikilink_entre_comillas_invertidas_es_documentacion(t):
    """E-03b — nombrar la cosa no es hacerla. Una ficha que explica que los `[[wiki]]` no
    van los escribe como codigo, y reportarla seria avisarle a alguien que hizo justo lo
    que se le pidio.

    Salio de correr el check contra las 13 fichas reales de este repo: `checks.md`
    documenta la regla y el check la delataba a ella."""
    t.igual("E-03b: wikilink en un span de codigo, sin hallazgo", [],
            _hallazgos("comun-doc.md"))


def test_e06_el_enlace_al_indice_no_es_un_hallazgo(t):
    """E-06 — `indice.md` no es una ficha y esta siempre. Volver al indice desde una
    ficha es lo que se quiere, no algo que avisar."""
    t.no_contiene("E-06: el indice no aparece como destino roto", "indice.md",
                  " ".join(_hallazgos("comun-hooks.md")) or "(sin hallazgos)")


def test_e07_una_escritura_fuera_del_directorio_no_dispara_nada(t):
    """E-07 — el check solo mira lo que cayo adentro del directorio del indice.

    Se usa a proposito la ficha ROTA: con una sana el test pasaria igual sin recorte
    ninguno y no probaria nada."""
    t.igual("E-07: fuera del directorio, silencio", [],
            _hallazgos("comun-checks.md", ruta_codebase="docs/codebase"))
    t.verdadero("E-07: y esa misma ficha adentro si da hallazgo",
                len(_hallazgos("comun-checks.md")) == 1)


def test_e05_el_hallazgo_avisa_y_no_bloquea(t):
    """E-05 — el hallazgo sale por el camino de PostToolUse, que es additionalContext, y
    el archivo queda escrito.

    Se prueba sobre `correr_checks` y no lanzando post-tool-use.py como proceso porque el
    hook resuelve su directorio de checks como `comun/checks`, y en el REPO los checks del
    harness de desarrollo no estan ahi: se juntan en `.claude/harness/checks/` recien al
    instalar. Lo que este test sostiene es que el check devuelve un string y no una
    excepcion -un check que explota se saltea en silencio y no avisa nada- y que el
    archivo sigue en disco despues de correrlo."""
    archivo = FIXTURE / ENLACES / "comun-checks.md"
    evento = {"hook_event_name": "PostToolUse", "tool_name": "Write",
              "cwd": str(FIXTURE), "tool_input": {"file_path": str(archivo)}}
    hallazgos = reglas.correr_checks(evento, str(CHECKS_DEV), str(FIXTURE),
                                     {"rutaCodebase": ENLACES})
    t.verdadero("E-05: el hallazgo llega por correr_checks",
                any("comun-reglas.md" in h for h in hallazgos))
    t.verdadero("E-05: el archivo sigue en disco", archivo.is_file())


# ── El generador: comun/bin/mapa-codigo.py ───────────────────────────────────────
#
# Las fichas de estos tests se arman en un directorio temporal en vez de versionar un
# fixture con su mapa.html adentro: el HTML es salida generada, y un generado commiteado
# se desactualiza contra el generador que lo escribio sin que nadie lo note.

def _cargar_generador():
    return reglas._cargar(str(GENERADOR))


class _Fichas(object):
    """Un directorio de fichas descartable."""

    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix="mapa-nodos-")

    def poner(self, nombre, titulo, enlaces=()):
        cuerpo = "# %s\n\n## De qué depende\n\n" % titulo
        for e in enlaces:
            cuerpo += "- La ficha [%s](%s).\n" % (e[:-3], e)
        with io.open(os.path.join(self.dir, nombre), "w", encoding="utf-8",
                     newline="\n") as f:
            f.write(cuerpo)
        return self

    def poner_crudo(self, nombre, texto):
        with io.open(os.path.join(self.dir, nombre), "w", encoding="utf-8",
                     newline="\n") as f:
            f.write(texto)
        return self

    def html(self):
        with io.open(os.path.join(self.dir, "mapa.html"), encoding="utf-8") as f:
            return f.read()

    def limpiar(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def _un_par():
    f = _Fichas()
    f.poner("comun-hooks.md", "comun/hooks", ["comun-checks.md"])
    f.poner("comun-checks.md", "comun/checks")
    f.poner("indice.md", "Índice del código", ["comun-hooks.md", "comun-checks.md"])
    return f


def test_e08_dos_corridas_dan_el_mismo_byte(t):
    """E-08 — el mapa se versiona. Un layout que se acomoda distinto en cada corrida
    convierte cada regeneracion en un diff de mil lineas y esconde el cambio real."""
    f = _un_par()
    try:
        gen = _cargar_generador()
        gen.generar(f.dir)
        primero = f.html()
        gen.generar(f.dir)
        t.igual("E-08: mismo HTML byte a byte", primero, f.html())
    finally:
        f.limpiar()


def test_e09_el_html_no_referencia_nada_de_afuera(t):
    """E-09 — se abre con doble clic, a veces sin red, en una maquina donde no se
    instala nada. Una fuente o una libreria de un CDN lo rompen justo ahi.

    Lo que se prohibe es el recurso EXTERNO, no el script. La pagina lleva un script
    propio, en linea, para desplazar el grafo y abrir el panel: eso no sale a buscar
    nada. Un `src=` si, y por eso es lo que se busca."""
    f = _un_par()
    try:
        _cargar_generador().generar(f.dir)
        html = f.html()
        for aguja in ("http://", "https://", "src="):
            t.no_contiene("E-09: sin %s" % aguja, aguja, html)
        t.contiene("E-09: y el script propio va en linea", "<script>", html)
    finally:
        f.limpiar()


def test_e10_un_nodo_por_ficha_sin_contar_el_indice(t):
    """E-10 — `indice.md` no es un modulo: es la puerta. Dibujarlo lo pondria en el
    centro del grafo conectado con todo, que es la forma que menos informa."""
    f = _un_par()
    try:
        resumen = _cargar_generador().generar(f.dir)
        t.igual("E-10: dos nodos, no tres", 2, resumen["nodos"])
        t.igual("E-10: dos cajas dibujadas", 2, f.html().count('<g class="nodo'))
        t.no_contiene("E-10: el indice no es un nodo", ">Índice del código<", f.html())
    finally:
        f.limpiar()


def test_e11_dos_enlaces_a_la_misma_ficha_son_una_arista(t):
    """E-11 — en el dibujo es la misma flecha. Dos lineas encima se ven como una mas
    gruesa y sugieren un peso que no existe."""
    f = _Fichas()
    try:
        f.poner("a.md", "a", ["b.md", "b.md", "b.md"])
        f.poner("b.md", "b")
        resumen = _cargar_generador().generar(f.dir)
        t.igual("E-11: una sola arista", 1, resumen["aristas"])
        t.igual("E-11: una sola linea", 1, f.html().count('<line class="arista"'))
    finally:
        f.limpiar()


def test_e12_la_ficha_que_nadie_enlaza_queda_marcada(t):
    """E-12 — la huerfana es el hallazgo del mapa: o le falta una arista a otra ficha, o
    es un modulo que de verdad no usa nadie. Las dos cosas se quieren ver."""
    f = _Fichas()
    try:
        f.poner("a.md", "a", ["b.md"])
        f.poner("b.md", "b")
        f.poner("suelta.md", "suelta")
        resumen = _cargar_generador().generar(f.dir)
        t.igual("E-12: dos huerfanas", ["a.md", "suelta.md"], resumen["huerfanas"])
        t.igual("E-12: dos cajas huerfanas", 2, f.html().count('class="nodo huerfano"'))
    finally:
        f.limpiar()


def test_e13_un_ciclo_se_dibuja_y_el_generador_termina(t):
    """E-13 — A depende de B y B de A pasa de verdad, y un layout iterativo es el lugar
    donde un ciclo se cuelga si esta mal escrito."""
    f = _Fichas()
    try:
        f.poner("a.md", "a", ["b.md"])
        f.poner("b.md", "b", ["a.md"])
        resumen = _cargar_generador().generar(f.dir)
        t.igual("E-13: dos aristas", 2, resumen["aristas"])
        t.igual("E-13: ninguna huerfana", [], resumen["huerfanas"])
    finally:
        f.limpiar()


def test_e14_sin_fichas_no_escribe_y_lo_dice(t):
    """E-14 — un mapa vacio es la promesa de que habia algo que mirar. Se corre como
    proceso porque lo que se prueba es tambien que el resumen sale por stdout: de ahi
    saca el recorrido los numeros de su reporte."""
    f = _Fichas()
    try:
        r = subprocess.run([sys.executable, str(GENERADOR), f.dir],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        t.igual("E-14: sale con codigo 0", 0, r.returncode)
        resumen = json.loads(r.stdout.decode("utf-8"))
        t.igual("E-14: dice que no escribio", False, resumen["escrito"])
        t.contiene("E-14: y por que", "no hay fichas", resumen["motivo"])
        t.verdadero("E-14: no hay mapa.html",
                    not os.path.exists(os.path.join(f.dir, "mapa.html")))
    finally:
        f.limpiar()


def test_e15_e16_solo_toca_el_directorio_de_las_fichas(t):
    """E-15 y E-16 — el generador no lee el codigo del proyecto y no escribe en ningun
    otro lado. Lo primero es lo que hace que no pueda filtrar un secreto que las fichas
    no tengan ya adentro; lo segundo es la misma invariante que tiene el agente que
    recorre.

    Se envuelve `io.open`, que es por donde el generador lee y escribe."""
    f = _un_par()
    abiertos = []
    gen = _cargar_generador()
    real = gen.io.open

    def espia(archivo, *a, **kw):
        modo = a[0] if a else kw.get("mode", "r")
        abiertos.append((str(archivo), modo))
        return real(archivo, *a, **kw)

    try:
        gen.io.open = espia
        gen.generar(f.dir)
        gen.io.open = real

        afuera = [ruta for ruta, _m in abiertos
                  if os.path.dirname(os.path.abspath(ruta)) != os.path.abspath(f.dir)]
        t.igual("E-15: no abrio nada de afuera del directorio", [], afuera)
        t.verdadero("E-15: y abrio las fichas, no una lista vacia", len(abiertos) >= 3)

        escritos = sorted(os.path.basename(r) for r, m in abiertos if "w" in m)
        t.igual("E-16: lo unico escrito es mapa.html", ["mapa.html"], escritos)
    finally:
        gen.io.open = real
        f.limpiar()


def test_e17_solo_biblioteca_estandar_y_sintaxis_de_39(t):
    """E-17 — el harness declara Python 3.9 y no instala nada. Un import de afuera o una
    sintaxis mas nueva convierten al generador en un requisito, que es justo lo que
    ADR-0008 no deja hacer."""
    with io.open(str(GENERADOR), encoding="utf-8") as f:
        arbol = ast.parse(f.read())

    permitidos = {"argparse", "io", "json", "math", "os", "re", "sys"}
    importados = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            importados.update(a.name.split(".")[0] for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.add(nodo.module.split(".")[0])
    t.igual("E-17: no importa nada de afuera de la estandar", set(),
            importados - permitidos)

    match = [n for n in ast.walk(arbol) if type(n).__name__ == "Match"]
    t.igual("E-17: sin sintaxis posterior a 3.9", 0, len(match))


# ── El panel y lo que se recorre ─────────────────────────────────────────────────

def test_e21_cada_ficha_va_embebida_en_la_pagina(t):
    """E-21 — sobre `file://` un `fetch` lo bloquea CORS, asi que el texto de la ficha
    tiene que estar adentro del archivo o el panel no tiene nada que mostrar. Embeber
    no es una opcion entre varias."""
    f = _un_par()
    try:
        resumen = _cargar_generador().generar(f.dir)
        html = f.html()
        t.igual("E-21: un article por nodo", resumen["nodos"],
                html.count('<article class="ficha"'))
        t.contiene("E-21: con el texto de la ficha adentro", "De qué depende", html)
        t.no_contiene("E-21: el indice no tiene panel propio",
                      'data-ficha="indice.md"', html)
    finally:
        f.limpiar()


def test_e22_cada_nodo_es_un_enlace_a_su_ficha(t):
    """E-22 — si el script no corre, el clic tiene que llevar igual a algun lado. El
    panel es mejor que abrir el .md crudo, pero no puede ser la unica puerta: una
    pagina que sin JavaScript no hace nada es una pagina rota, no una degradada."""
    f = _un_par()
    try:
        _cargar_generador().generar(f.dir)
        html = f.html()
        for ficha in ("comun-hooks.md", "comun-checks.md"):
            t.contiene("E-22: %s envuelta en su enlace" % ficha,
                       '<a href="%s" class="ir">' % ficha, html)
    finally:
        f.limpiar()


def test_e23_el_html_de_una_ficha_sale_escapado(t):
    """E-23 — la ficha la escribe un modelo sobre codigo ajeno. Si su texto se inyectara
    crudo en la pagina, un `<script>` copiado de un archivo del proyecto se ejecutaria al
    abrir el mapa. Se escapa antes de armar el marcado, no despues."""
    f = _un_par()
    try:
        f.poner_crudo("comun-raro.md",
                      "# comun/raro\n\n## Qué es\n\n"
                      "Un módulo que copia <script>window.MALO=1</script> de su fuente,\n"
                      "y un <b>bold</b> crudo.\n")
        _cargar_generador().generar(f.dir)
        html = f.html()
        t.no_contiene("E-23: el script de la ficha no queda crudo",
                      "<script>window.MALO", html)
        t.contiene("E-23: sale como texto", "&lt;script&gt;window.MALO", html)
        t.no_contiene("E-23: y tampoco el bold", "<b>bold</b>", html)
    finally:
        f.limpiar()


def test_e24_un_enlace_a_una_hermana_cambia_de_ficha_y_uno_de_afuera_no(t):
    """E-24 — adentro del panel, saltar a otra ficha no deberia sacarte del mapa. Un
    enlace a un ADR si sale, porque ese archivo no esta embebido: prometerle al lector
    que se abre en el panel y que no pase nada seria peor que mandarlo afuera."""
    f = _un_par()
    try:
        f.poner_crudo("comun-mixta.md",
                      "# comun/mixta\n\n## De qué depende\n\n"
                      "- La hermana [comun-hooks](comun-hooks.md).\n"
                      "- El [ADR-0008](../adr/0008-lo-externo.md).\n")
        _cargar_generador().generar(f.dir)
        html = f.html()
        t.contiene("E-24: la hermana abre en el panel",
                   'class="a-ficha" data-ficha="comun-hooks.md"', html)
        t.contiene("E-24: el de afuera es un enlace comun",
                   '<a href="../adr/0008-lo-externo.md">', html)
        t.no_contiene("E-24: y no finge abrirse en el panel",
                      'data-ficha="../adr/0008-lo-externo.md"', html)
    finally:
        f.limpiar()


# ── Los dos que salieron de abrirlo ──────────────────────────────────────────────
#
# E-25 y E-26 son aserciones sobre la FORMA del script, no sobre lo que hace el
# navegador: nada en esta suite abre uno. No prueban que el mapa se comporte bien;
# prueban que las dos defensas que lo arreglaron sigan estando el dia que alguien
# simplifique el handler. Los dos bugs que cubren aparecieron abriendo el archivo, no
# leyendolo, y eso es lo que dice el riesgo declarado en la spec.

def test_e25_el_mapa_no_atrapa_el_desplazamiento_de_la_pagina(t):
    """E-25 — la rueda sola desplaza la pagina. Un mapa que hace zoom apenas el puntero
    le pasa por encima encierra al lector: no puede seguir bajando y no entiende por
    que. El zoom pide Ctrl -que es lo que manda el navegador al pellizcar en un
    trackpad- y ademas hay botones."""
    f = _un_par()
    try:
        _cargar_generador().generar(f.dir)
        html = f.html()
        t.no_contiene("E-25: no bloquea el gesto de la pagina", "touch-action:none", html)
        t.contiene("E-25: el zoom por rueda pide Ctrl", "ev.ctrlKey", html)
        t.contiene("E-25: y se puede acercar sin rueda", 'id="acercar"', html)
        t.contiene("E-25: y alejar", 'id="alejar"', html)
    finally:
        f.limpiar()


def test_e26_el_clic_llega_al_nodo_y_el_arrastre_termina(t):
    """E-26 — dos defensas de la misma familia, las dos aprendidas rompiendo.

    `setPointerCapture` en el <svg> desvia el `click` posterior al lienzo: el nodo deja
    de recibirlo y abrir una ficha no hace nada. Y un arrastre que no se anula al soltar
    deja el mapa moviendose con solo pasar el mouse."""
    f = _un_par()
    try:
        _cargar_generador().generar(f.dir)
        html = f.html()
        t.no_contiene("E-26: no captura el puntero en el lienzo",
                      "setPointerCapture(", html)
        t.contiene("E-26: el arrastre se corta si el boton no esta apretado",
                   "ev.buttons === 0", html)
        # `arrastre = null` a secas tambien matchea la DECLARACION de la variable, y la
        # asercion se cumplia sola: se vio corriendo la rotura, que no dio rojo. Lo que
        # importa es que se anule adentro de terminar(), asi que se pide la secuencia.
        t.contiene("E-26: y se anula al soltar, no solo al declararse",
                   "ultimoMovio = !!(arrastre && arrastre.movio);\n"
                   "    arrastre = null;",
                   html)
    finally:
        f.limpiar()
