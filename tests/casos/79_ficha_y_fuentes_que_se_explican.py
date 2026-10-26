# La Ficha de Proyecto y `fuentes` dicen por que no encontraron lo que buscaban.
#
# Escenarios E-01 a E-16 de docs/cambios/ficha-y-fuentes-que-se-explican/spec.md. Cada test nombra
# su escenario. Ningun test sale a la red: Jira es el servidor falso de 19_contexto.py, que
# contesta por fragmento de URL, y dev-harness.py corre en proceso como en 19 y en 67.
#
# Los textos que NO cambian (E-03, E-13, E-15, E-16) van clavados por literal, como en
# 45_conocimiento_fuentes.py y 61_conocimiento_auto_refresco.py: leerlos del modulo y compararlos
# contra si mismos pasa con cualquier cambio.
import ast
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"

if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))
from contexto import proyecto as c_proyecto               # noqa: E402
from contexto.comun import Acumulador                      # noqa: E402
from orquestacion import registro_fuentes as rf            # noqa: E402


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, str(ruta))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


C19 = _cargar("caso_19_para_79", RAIZ / "tests" / "casos" / "19_contexto.py")
TICKET = C19.CLAVE
VACIO = (200, {"issues": []})
TIPO_ASI = ".ASI Ficha de proyecto"

# Las causas, tal como las anota el resolvedor de la Ficha. Se comparan ENTERAS: una cola pegada a la
# causa no puede pasar (E-04, E-06 a E-10).
SIN_FICHA = 'la Ficha de Proyecto: no hay ningun issue de tipo "Ficha de Proyecto" en el proyecto GCBA'
CAUSA_PARECIDO = (SIN_FICHA + '. El ticket que se paso es de tipo "%s", que se parece: si ese es el tipo de '
                  'la Ficha, escribilo en `fichaTipoDeIssue` de .claude/harness.config.json' % TIPO_ASI)
CAUSA_CONFLICTO = ('hay 2 issues de tipo "Ficha de Proyecto" en el proyecto GCBA (GCBA-7, GCBA-8). No se '
                   'elige ninguna: la Ficha de Proyecto tiene que ser unica.')
CAUSA_SIN_BUSQUEDA = ('jira.issue.search no esta disponible: sin eso no se puede buscar la Ficha de Proyecto. '
                      'Corre el setup del harness para reconfigurarla.')
CAUSA_ERROR_DE_JIRA = "la Ficha de Proyecto: Jira contesto 403 al buscarla"


def _fuente_sin_hash():
    """Una fuente del registro de fabrica sin hash aceptado: sobre ella corren E-12 a E-14. Hoy son las seis;
    si una version futura les pone hash, el caso busca otra en vez de ponerse en rojo sin que nada se rompa."""
    estados = rf.validar(rf.cargar())["sources"]
    ids = sorted(sid for sid, estado in estados.items() if estado == rf.SIN_HASH)
    return ids[0] if ids else None


SID = _fuente_sin_hash()


# -- andamios ------------------------------------------------------------------

def _issue(tipo):
    """El ticket de 19_contexto con otro tipo de issue."""
    copia = json.loads(json.dumps(C19.ISSUE))
    copia["fields"]["issuetype"] = {"name": tipo}
    return copia


def _ficha(clave="GCBA-7", tipo="Ficha de Proyecto"):
    copia = json.loads(json.dumps(C19.FICHA["issues"][0]))
    copia["key"] = clave
    copia["fields"]["issuetype"] = {"name": tipo}
    return copia


def _escribir(ruta, datos):
    with io.open(ruta, "w", encoding="utf-8") as f:
        f.write(json.dumps(datos))


def _proyecto(config=None, capacidades=None):
    """Un proyecto con Jira habilitado (el de 19_contexto), y opcionalmente otra config o capacidades."""
    raiz = C19._proyecto_listo()
    if capacidades is not None:
        _escribir(os.path.join(raiz, ".claude", "harness.capacidades.json"),
                  {"capacidades": capacidades})
    if config is not None:
        _escribir(os.path.join(raiz, ".claude", "harness.config.json"), config)
    return raiz


def _borrar(*rutas):
    for r in rutas:
        shutil.rmtree(str(r), ignore_errors=True)


def _correr(raiz, respuestas, *argv):
    """dev-harness.py en proceso, con el Jira falso. (codigo, stdout, stderr, transporte)."""
    transporte = C19.Transporte(respuestas)
    codigo, salida, error = C19._correr_cli(list(argv) + ["--proyecto", raiz], transporte,
                                            C19._Bytes({}))
    return codigo, salida, error, transporte


def _fuentes(raiz, respuestas, *extra):
    return _correr(raiz, respuestas, "fuentes", TICKET, *extra)


def _sin_ficha(tipo_del_ticket="Historia de Usuario"):
    return {"/issue/": (200, _issue(tipo_del_ticket)), "/search": VACIO}


def _causas(salida):
    """Las lineas `causa: ...` de lo que imprimio `fuentes`, sin la sangria."""
    return [l.strip() for l in salida.splitlines() if l.strip().startswith("causa:")]


def _contexto(raiz, respuestas):
    """`contexto` sobre el ticket, y el documento que escribe."""
    codigo, salida, error, _ = _correr(raiz, respuestas, "contexto", TICKET)
    destino = os.path.join(raiz, ".claude", "contextos", TICKET + ".json")
    documento = None
    if os.path.isfile(destino):
        with io.open(destino, encoding="utf-8") as f:
            documento = json.loads(f.read())
    return codigo, salida + error, documento


# -- E-01 a E-03: el tipo con que se busca la Ficha se ve ----------------------

def test_e01_setup_dice_el_tipo_por_defecto(t):
    """E-01 — `setup` sin la clave imprime el tipo por defecto y dice que lo es."""
    raiz = C19._proyecto_temporal()
    try:
        codigo, salida, error = C19._correr_cli(["setup", "--proyecto", raiz])
        t.igual("E-01 sale 0", 0, codigo)
        linea = [l for l in salida.splitlines() if l.startswith("Ficha de Proyecto:")]
        t.igual("E-01 hay una sola linea de la Ficha", 1, len(linea))
        t.contiene("E-01 el tipo", "«Ficha de Proyecto»", linea[0])
        t.contiene("E-01 dice que es el por defecto", "el valor por defecto", linea[0])
        t.no_contiene("E-01 y no dice que lo puso el proyecto", "lo puso el proyecto", linea[0])
        # `setup` muestra, no escribe ni pregunta (spec, «Qué queda afuera»).
        t.verdadero("E-01 setup no escribio harness.config.json",
                    not os.path.exists(os.path.join(raiz, ".claude", "harness.config.json")))
        arbol = ast.parse((BIN / "dev-harness.py").read_text(encoding="utf-8"))
        preguntas = [n.lineno for n in ast.walk(arbol) if isinstance(n, ast.Call)
                     and isinstance(n.func, ast.Name) and n.func.id == "input"]
        t.igual("E-01 dev-harness.py no pregunta: no llama a input()", [], preguntas)
        # La linea es de `setup`: `reconfigurar` no la muestra.
        _, salida_reconf, _ = C19._correr_cli(["reconfigurar", "jira", "--proyecto", raiz])
        t.igual("E-01 reconfigurar no muestra la linea del tipo", [],
                [l for l in salida_reconf.splitlines() if l.startswith("Ficha de Proyecto:")])
    finally:
        _borrar(raiz)


def test_e02_setup_dice_el_tipo_del_proyecto(t):
    """E-02 — con la clave en harness.config.json, `setup` imprime ese valor y dice que es del proyecto."""
    raiz = C19._proyecto_temporal()
    try:
        ruta = os.path.join(raiz, ".claude", "harness.config.json")
        _escribir(ruta, {"fichaTipoDeIssue": TIPO_ASI, "prefijoApi": "interno-xyz",
                         "topeTextoDocumento": 424242})
        with io.open(ruta, "rb") as f:
            antes = f.read()
        codigo, salida, error = C19._correr_cli(["setup", "--proyecto", raiz])
        linea = [l for l in salida.splitlines() if l.startswith("Ficha de Proyecto:")]
        t.igual("E-02 sale 0", 0, codigo)
        t.igual("E-02 hay una sola linea de la Ficha", 1, len(linea))
        t.contiene("E-02 el tipo del proyecto", "«%s»" % TIPO_ASI, linea[0])
        t.contiene("E-02 dice que lo puso el proyecto", "lo puso el proyecto", linea[0])
        t.no_contiene("E-02 y no dice que es el por defecto", "el valor por defecto", linea[0])
        # Solo el tipo de la Ficha: las otras claves de harness.config.json no se muestran, y el archivo
        # queda como estaba.
        t.no_contiene("E-02 no muestra prefijoApi ni su valor", "interno-xyz", salida + error)
        t.no_contiene("E-02 ni topeTextoDocumento ni su valor", "424242", salida + error)
        with io.open(ruta, "rb") as f:
            t.verdadero("E-02 setup no reescribio harness.config.json", f.read() == antes)
    finally:
        _borrar(raiz)


def test_e03_sin_la_clave_se_busca_ficha_de_proyecto(t):
    """E-03 — el default no se movio: sin la clave, `fuentes` busca por `Ficha de Proyecto`."""
    raiz = _proyecto()
    try:
        _, _, _, transporte = _fuentes(raiz, _sin_ficha())
        busquedas = [u for u in transporte.llamadas if "/search" in u]
        t.igual("E-03 hizo una busqueda", 1, len(busquedas))
        t.contiene("E-03 por Ficha de Proyecto", "Ficha%20de%20Proyecto", busquedas[0])
    finally:
        _borrar(raiz)
    raiz = _proyecto(config={"fichaTipoDeIssue": TIPO_ASI})
    try:
        _, _, _, transporte = _fuentes(raiz, _sin_ficha())
        busquedas = [u for u in transporte.llamadas if "/search" in u]
        t.contiene("E-03 control: con la clave, busca por la del proyecto", "ASI%20Ficha",
                   busquedas[0])
    finally:
        _borrar(raiz)


# -- E-04 a E-08: la causa llega a la persona ----------------------------------

def test_e04_fuentes_dice_la_causa(t):
    """E-04 — sin ningun issue del tipo buscado, `fuentes <CLAVE>` imprime el tipo y el proyecto."""
    raiz = _proyecto()
    try:
        codigo, salida, error, _ = _fuentes(raiz, _sin_ficha())
        t.contiene("E-04 sigue diciendo ficha=ninguna", "ficha=ninguna", salida)
        # Una sola causa, entera: el tipo y el proyecto. El resolvedor de la tarea comparte el acumulador
        # y anota lo suyo (aca, los criterios de aceptacion, porque el proyecto no los configura): eso no
        # es la causa de que falte la Ficha.
        t.igual("E-04 la causa: el tipo y el proyecto, y nada mas", ["causa: " + SIN_FICHA],
                _causas(salida))
        t.no_contiene("E-04 no arrastra lo que le falto a la tarea", "criterios de aceptacion", salida)
    finally:
        _borrar(raiz)


def test_e05_el_rechazo_de_aceptar_lleva_la_causa(t):
    """E-05 — con --aceptar, el rechazo incluye la causa; no escribe nada y sale con el codigo de siempre."""
    raiz = _proyecto()
    try:
        codigo, salida, error, _ = _fuentes(raiz, _sin_ficha(), "--aceptar", "ES0902",
                                            "--por", "Ana Prueba")
        t.igual("E-05 sale 2, como una falla del harness", 2, codigo)
        t.contiene("E-05 sigue diciendo que no se puede aceptar",
                   "ES0902 no se puede aceptar (FRESHNESS_UNVERIFIED): no hay canal", error)
        t.contiene("E-05 y dice por que, y sigue sin escribir nada",
                   "Causa: %s. No se escribio nada." % SIN_FICHA, error)
        t.verdadero("E-05 no hay harness.fuentes.json",
                    not os.path.exists(os.path.join(raiz, ".claude", "harness.fuentes.json")))
    finally:
        _borrar(raiz)


def test_e06_el_conflicto_se_dice(t):
    """E-06 — con dos Fichas, la salida dice cuantas y cuales claves, no el texto generico."""
    raiz = _proyecto()
    try:
        dos = {"issues": [_ficha("GCBA-7"), _ficha("GCBA-8")]}
        respuestas = {"/issue/": (200, _issue("Historia de Usuario")), "/search": (200, dos)}
        _, salida, _, _ = _fuentes(raiz, respuestas)
        t.igual("E-06 cuantas, cuales y que no se elige ninguna, y nada mas", ["causa: " + CAUSA_CONFLICTO],
                _causas(salida))
    finally:
        _borrar(raiz)


def test_e07_la_capacidad_ausente_se_dice(t):
    """E-07 — sin jira.issue.search, la salida dice que esa capacidad falta."""
    sin_busqueda = dict(C19.TODAS)
    sin_busqueda["jira.issue.search"] = "NOT_CONFIGURED"
    raiz = _proyecto(capacidades=sin_busqueda)
    try:
        _, salida, _, transporte = _fuentes(raiz, _sin_ficha())
        t.igual("E-07 dice cual falta, y nada mas", ["causa: " + CAUSA_SIN_BUSQUEDA], _causas(salida))
        t.igual("E-07 y no la busco", [], [u for u in transporte.llamadas if "/search" in u])
    finally:
        _borrar(raiz)


def test_e08_el_error_de_jira_se_dice(t):
    """E-08 — con Jira contestando un error a la busqueda, la salida dice el codigo."""
    raiz = _proyecto()
    try:
        respuestas = {"/issue/": (200, _issue("Historia de Usuario")),
                      "/search": (403, {"errorMessages": ["sin permiso"]})}
        _, salida, _, _ = _fuentes(raiz, respuestas)
        t.igual("E-08 el codigo, y nada mas", ["causa: " + CAUSA_ERROR_DE_JIRA], _causas(salida))
    finally:
        _borrar(raiz)


# -- E-09 a E-11: la sugerencia del tipo ---------------------------------------

def test_e09_el_tipo_parecido_se_sugiere(t):
    """E-09 — el ticket es `.ASI Ficha de proyecto` y se busca el por defecto: la causa lo nombra, en
    `fuentes` y en `contexto`."""
    raiz = _proyecto()
    try:
        _, salida, _, _ = _fuentes(raiz, _sin_ficha(TIPO_ASI))
        t.igual("E-09 fuentes: el tipo real del ticket y donde escribirlo", ["causa: " + CAUSA_PARECIDO],
                _causas(salida))
    finally:
        _borrar(raiz)
    raiz = _proyecto()
    try:
        _, texto, documento = _contexto(raiz, _sin_ficha(TIPO_ASI))
        t.verdadero("E-09 contexto escribio el documento", documento is not None)
        t.verdadero("E-09 contexto: la causa con el tipo real esta, entera, en lo que falta",
                    CAUSA_PARECIDO in documento["gaps_and_conflicts"]["missing"])
    finally:
        _borrar(raiz)
    # La relacion es de contencion en las dos direcciones, y solo entre nombres distintos.
    se_parece = c_proyecto._se_parece
    t.verdadero("E-09 el del ticket contiene al buscado", se_parece(TIPO_ASI, "Ficha de Proyecto"))
    t.verdadero("E-09 el buscado contiene al del ticket", se_parece("Ficha", "Ficha de Proyecto"))
    t.verdadero("E-09 sin mayusculas", se_parece("FICHA DE PROYECTO ASI", "ficha de proyecto"))
    t.verdadero("E-09 iguales sin mayusculas no se sugieren",
                not se_parece("ficha de proyecto", "Ficha de Proyecto"))
    t.verdadero("E-09 un tipo vacio no se parece a nada", not se_parece("", "Ficha de Proyecto"))


def test_e10_un_tipo_que_no_se_parece_no_se_sugiere(t):
    """E-10 — con una historia, la causa es la de siempre y no nombra fichaTipoDeIssue."""
    raiz = _proyecto()
    try:
        _, salida, _, _ = _fuentes(raiz, _sin_ficha("Historia de Usuario"))
        t.igual("E-10 la causa de siempre, entera y sin cola", ["causa: " + SIN_FICHA], _causas(salida))
        t.no_contiene("E-10 sin sugerencia", "fichaTipoDeIssue", salida)
        t.no_contiene("E-10 ni el tipo del ticket", "que se parece", salida)
    finally:
        _borrar(raiz)
    for tipo in ("Bug", "Task", "Epic", "Tarea"):
        t.verdadero("E-10 %s no se parece" % tipo, not c_proyecto._se_parece(tipo, "Ficha de Proyecto"))


def test_e11_con_ficha_no_se_agrega_nada(t):
    """E-11 — si hay una Ficha, ni `fuentes` ni `contexto` agregan causa ni sugerencia, aunque el ticket
    tenga un tipo que se parece."""
    # Una Ficha con un hueco propio (sin seccion de arquitectura): el resolvedor lo anota, y eso es
    # un hueco de la Ficha encontrada, no la causa de que falte.
    con_hueco = _ficha()
    con_hueco["fields"]["description"] = C19._adf(
        "Sistema de tramites.\nObjetivos\nBajar el tiempo.\nAlcance\nBackoffice.")
    respuestas = {"/issue/": (200, _issue(TIPO_ASI)), "/search": (200, {"issues": [con_hueco]})}
    raiz = _proyecto()
    try:
        _, salida, error, _ = _fuentes(raiz, respuestas)
        t.contiene("E-11 fuentes encontro la Ficha", "ficha=GCBA-7", salida)
        t.no_contiene("E-11 fuentes: sin causa", "causa:", salida)
        t.no_contiene("E-11 fuentes: sin sugerencia", "fichaTipoDeIssue", salida + error)
        _, salida, _, _ = _fuentes(raiz, respuestas, "--json")
        t.igual("E-11 fuentes: el canal es el de la Ficha, como siempre",
                {"key": "GCBA-7", "issue_type": "Ficha de Proyecto", "reachable": True,
                 "channel": "jira:GCBA-7"}, json.loads(salida)["ficha"])
    finally:
        _borrar(raiz)
    raiz = _proyecto()
    try:
        _, _, documento = _contexto(raiz, respuestas)
        faltas = json.dumps(documento["gaps_and_conflicts"], ensure_ascii=False)
        t.contiene("E-11 contexto: el hueco propio de la Ficha si esta", "seccion de architecture",
                   faltas)
        t.no_contiene("E-11 contexto: sin sugerencia", "fichaTipoDeIssue", faltas)
        t.no_contiene("E-11 contexto: sin causa de ficha ausente", "no hay ningun issue de tipo",
                      faltas)
    finally:
        _borrar(raiz)


# -- E-12 a E-14: el aviso del hash faltante nombra el canal en uso ------------

def _aviso(sid):
    """El aviso del hash faltante, sin el comando que sugiere."""
    return ("la fuente %s no tiene hash aceptado: su integridad no se puede verificar hasta que alguien "
            "acepte el original" % sid)


def test_e12_con_una_clave_el_aviso_sugiere_la_clave(t):
    """E-12 — `fuentes <CLAVE>` sugiere `fuentes <CLAVE> --aceptar <ID>` y no nombra --archivo."""
    t.verdadero("E-12 precondicion: el registro de fabrica tiene una fuente sin hash", SID is not None)
    if SID is None:
        return
    raiz = _proyecto()
    try:
        _, salida, error, _ = _fuentes(raiz, _sin_ficha())
        t.contiene("E-12 el aviso con la clave",
                   "aviso: %s (fuentes %s --aceptar %s)" % (_aviso(SID), TICKET, SID), salida)
        t.no_contiene("E-12 y sin --archivo", "--archivo", salida + error)
    finally:
        _borrar(raiz)


def test_e13_con_archivo_el_aviso_es_el_de_hoy(t):
    """E-13 — `fuentes --archivo <dir>`: el aviso es el de siempre."""
    t.verdadero("E-13 precondicion: el registro de fabrica tiene una fuente sin hash", SID is not None)
    if SID is None:
        return
    raiz = _proyecto()
    originales = tempfile.mkdtemp(prefix="harness-79-originales-")
    try:
        codigo, salida, error, _ = _correr(raiz, {}, "fuentes", "--archivo", originales)
        t.contiene("E-13 el aviso de siempre",
                   "aviso: %s (fuentes --archivo <dir> --aceptar %s)" % (_aviso(SID), SID), salida)
    finally:
        _borrar(raiz, originales)


def test_e14_sin_canal_el_aviso_nombra_las_dos_formas(t):
    """E-14 — sin clave ni --archivo, el aviso nombra las dos formas."""
    t.verdadero("E-14 precondicion: el registro de fabrica tiene una fuente sin hash", SID is not None)
    if SID is None:
        return
    raiz = _proyecto()
    try:
        _, salida, error, _ = _correr(raiz, {}, "fuentes")
        t.contiene("E-14 las dos formas",
                   "aviso: %s (fuentes <CLAVE-DE-JIRA> --aceptar %s, o fuentes --archivo <dir> "
                   "--aceptar %s)" % (_aviso(SID), SID, SID), salida)
    finally:
        _borrar(raiz)


# -- E-15 y E-16: lo que no cambia ---------------------------------------------

def test_e15_los_otros_avisos_no_cambian(t):
    """E-15 — registro que no valida, fuente repetida y extracto ausente salen con el texto de 0.36.0."""
    repetida = {"schema_version": "source-registry/1.1", "sources": [
        {"id": "ES0901", "extract": "normativa/extractos/ES0901.md", "sha256": "a" * 64},
        {"id": "ES0901", "extract": "normativa/extractos/ES0901.md", "sha256": "a" * 64}]}
    avisos = rf.hallazgos(repetida)
    t.verdadero("E-15 fuente repetida: texto de siempre",
                "la fuente ES0901 esta declarada dos veces: el registro lleva una entrada por "
                "fuente, no una por version" in avisos)
    sin_extracto = {"schema_version": "source-registry/1.1", "sources": [
        {"id": "ES0904", "extract": "normativa/extractos/NO-EXISTE.md", "sha256": "a" * 64}]}
    avisos = rf.hallazgos(sin_extracto)
    t.verdadero("E-15 extracto ausente: texto de siempre",
                "la fuente ES0904 declara el extracto normativa/extractos/NO-EXISTE.md y no esta "
                "en este arbol" in avisos)
    # Los textos del validador, enteros, tal como los da 0.36.0 para este registro: una cola o un prefijo
    # agregado a cualquiera de ellos se ve.
    roto = {"schema_version": "source-registry/1.1", "sources": [{"id": 5}]}
    t.igual("E-15 registro que no valida: los avisos de siempre, enteros", [
        "el registro de fuentes no valida: $.sources[0].kind: falta y es obligatorio",
        "el registro de fuentes no valida: $.sources[0].title: falta y es obligatorio",
        "el registro de fuentes no valida: $.sources[0].status: falta y es obligatorio",
        "el registro de fuentes no valida: $.sources[0].version: falta y es obligatorio",
        "el registro de fuentes no valida: $.sources[0].extract: falta y es obligatorio",
        "el registro de fuentes no valida: $.sources[0].sha256: falta y es obligatorio",
        "el registro de fuentes no valida: $.sources[0].id: se esperaba string y vino int",
        "la fuente 5 declara el extracto None y no esta en este arbol"], rf.hallazgos(roto))
    # El aviso del hash faltante cambia de texto solo en el comando que sugiere (E-12 a E-14): con
    # --archivo es el de siempre.
    sin_hash = {"schema_version": "source-registry/1.1", "sources": [
        {"id": "ES0901", "extract": "normativa/extractos/ES0901.md", "sha256": None}]}
    t.verdadero("E-15 el del hash con --archivo es el de siempre",
                ("%s (fuentes --archivo <dir> --aceptar ES0901)" % _aviso("ES0901"))
                in rf.hallazgos(sin_hash, canal={"archivo": True}))


def test_e16_el_json_de_fuentes_no_lleva_la_causa(t):
    """E-16 — con --json, stdout es el documento de siempre: la causa va a stderr, no al documento."""
    raiz = _proyecto()
    try:
        codigo, salida, error, _ = _fuentes(raiz, _sin_ficha(TIPO_ASI), "--json")
        documento = json.loads(salida)
        t.igual("E-16 la ficha del documento es la de 0.36.0",
                {"reachable": False,
                 "reason": "no se pudo resolver la Ficha de Proyecto del ticket %s" % TICKET},
                documento["ficha"])
        t.no_contiene("E-16 el documento no tiene la causa", "no hay ningun issue de tipo", salida)
        t.no_contiene("E-16 ni la sugerencia", "fichaTipoDeIssue", salida)
        t.igual("E-16 la causa si salio, entera, por stderr", ["causa: " + CAUSA_PARECIDO], _causas(error))
        estado = os.path.join(raiz, ".claude", "harness.fuentes.json")
        with io.open(estado, encoding="utf-8") as f:
            escrito = json.loads(f.read())
        t.igual("E-16 y el estado escrito dice lo mismo", documento["ficha"], escrito["ficha"])
    finally:
        _borrar(raiz)
