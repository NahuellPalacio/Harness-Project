# El aviso del primer recorrido del codigo, en SessionStart.
#
# Escenarios E-01 a E-06 y E-20 de docs/cambios/iniciador-code/spec.md.
#
# Se invoca el hook como proceso hijo, igual que lo invoca Claude Code, porque lo que se
# esta probando es su salida completa y no una funcion suelta.
import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
HOOKS = RAIZ / "comun" / "hooks"

AGENTE = "dev-iniciador-code"


def _escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


def _correr_proceso(payload):
    return subprocess.run(
        [sys.executable, str(HOOKS / "session-start.py")],
        input=json.dumps(payload).encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _proyecto(harness=("comun", "desarrollo"), config_extra=None, con_indice=False,
              ruta_codebase=None):
    """Un proyecto descartable como los deja install.ps1.

    `ruta_codebase` es donde se crea el indice cuando `con_indice`; por defecto, el mismo
    default que resuelve el hook."""
    proy = Path(tempfile.gettempdir()) / ("harness-cb-" + uuid.uuid4().hex[:8])
    proy.mkdir(parents=True, exist_ok=True)

    config = dict(config_extra or {})
    config.setdefault("usuario", "Nahue")
    _escribir(proy / ".claude" / "harness.config.json", json.dumps(config, ensure_ascii=False))
    _escribir(proy / ".claude" / "harness.lock.json",
              json.dumps({"harness": list(harness), "version": "0.13.0"}, ensure_ascii=False))

    if con_indice:
        _escribir(proy / (ruta_codebase or "docs/codebase") / "indice.md", "# Indice del codigo\n")

    return proy


def _contexto(proy):
    """El additionalContext del hook, o cadena vacia si no dijo nada."""
    salida = _correr_proceso({"session_id": "s", "cwd": str(proy),
                              "hook_event_name": "SessionStart"}).stdout.decode("utf-8")
    if not salida.strip():
        return ""
    return json.loads(salida)["hookSpecificOutput"]["additionalContext"]


# ── El aviso aparece, y desaparece solo ──────────────────────────────────────────

def test_e01_avisa_cuando_falta_el_indice(t):
    """E-01 — con desarrollo instalado y sin indice, una linea que nombra al agente."""
    ctx = _contexto(_proyecto())
    t.contiene("E-01: nombra a dev-iniciador-code", AGENTE, ctx)
    lineas = [l for l in ctx.split("\n") if AGENTE in l]
    t.igual("E-01: una sola linea, no dos", 1, len(lineas))


def test_e02_calla_cuando_el_indice_existe(t):
    """E-02 — el aviso desaparece solo. Un aviso permanente se vuelve ruido."""
    ctx = _contexto(_proyecto(con_indice=True))
    t.no_contiene("E-02: ya no lo nombra", AGENTE, ctx)


def test_e03_calla_sin_desarrollo_en_el_lockfile(t):
    """E-03 — un proyecto de solo analisis no tiene codigo que recorrer."""
    ctx = _contexto(_proyecto(harness=("comun", "analisis")))
    t.no_contiene("E-03: no lo nombra", AGENTE, ctx)
    t.contiene("E-03: y el resto del bloque sigue saliendo", "Nahue", ctx)


# ── Lo que el aviso cuesta ───────────────────────────────────────────────────────

def test_e04_el_aviso_agrega_exactamente_una_linea(t):
    """E-04 — el aviso cuesta una linea y nada mas.

    🔴 El escenario original decia "la salida no supera sus 12 lineas". Se midio el peor
    caso el 2026-08-21 y da 13 lineas SIN este aviso: encabezado, git, "Ultimo trabajo"
    con tres commits, "En la cache quedo anotado" con cuatro items mas el "y N mas", y las
    definiciones pendientes. El techo de 12 es un comentario del hook que nadie mide y que
    ya estaba pasado antes de este cambio.
    Se verifica lo que este cambio si controla -su propio costo- y el exceso preexistente
    queda anotado en Pendientes/Fix-Harness/PENDIENTES-FH.md, que es donde se arregla."""
    sin = _contexto(_proyecto(con_indice=True))
    con = _contexto(_proyecto())
    delta = len(con.split("\n")) - len(sin.split("\n"))
    t.igual("E-04: el aviso agrega una linea", 1, delta)


def test_e05_no_devuelve_deny_ni_ask(t):
    """E-05 — SessionStart avisa. Los secretos siguen siendo lo unico que bloquea."""
    salida = _correr_proceso({"session_id": "s", "cwd": str(_proyecto()),
                              "hook_event_name": "SessionStart"}).stdout.decode("utf-8")
    t.no_contiene("E-05: sin deny", "deny", salida)
    t.no_contiene("E-05: sin ask", "\"ask\"", salida)
    t.contiene("E-05: sale como additionalContext", "additionalContext", salida)


def test_e06_ruta_ilegible_sale_cero_y_no_pierde_el_resto(t):
    """E-06 — si la ruta del indice no se puede recorrer, el hook no se cae ni se lleva
    puesto el resto del bloque. Aca `docs/codebase` es un ARCHIVO, no un directorio."""
    proy = _proyecto()
    _escribir(proy / "docs" / "codebase", "esto no es un directorio")

    r = _correr_proceso({"session_id": "s", "cwd": str(proy),
                         "hook_event_name": "SessionStart"})
    t.igual("E-06: sale con codigo 0", 0, r.returncode)
    ctx = json.loads(r.stdout.decode("utf-8"))["hookSpecificOutput"]["additionalContext"]
    t.contiene("E-06: el resto del bloque se emite igual", "Nahue", ctx)


def test_e06b_ruta_que_revienta_al_resolverse_no_se_lleva_el_bloque(t):
    """E-06b — una `rutaCodebase` que no es una ruta no se lleva puesto el bloque.

    `harness.config.json` es el archivo de la persona: el harness no lo valida ni lo pisa
    nunca. Un valor de otro tipo llega igual hasta acá, y sin la guarda de tipo
    `os.path.join` levanta TypeError y se pierde el bloque entero -no solo esta línea-.

    🔴 El `except (OSError, ValueError)` que rodea al `isfile` es defensivo y **la suite
    no lo alcanza**: se comprobó el 2026-08-21 rompiéndolo a propósito y los tests
    siguieron verdes. Queda porque el resto del hook lee disco con la misma red, no
    porque esté verificado."""
    proy = _proyecto(config_extra={"rutaCodebase": 12345})

    r = _correr_proceso({"session_id": "s", "cwd": str(proy),
                         "hook_event_name": "SessionStart"})
    t.igual("E-06b: sale con codigo 0", 0, r.returncode)
    ctx = json.loads(r.stdout.decode("utf-8"))["hookSpecificOutput"]["additionalContext"]
    t.contiene("E-06b: el resto del bloque se emite igual", "Nahue", ctx)
    t.contiene("E-06b: y cae al default, donde no hay indice", AGENTE, ctx)


# ── La ruta, con la clave y sin ella ─────────────────────────────────────────────

def test_e20_sin_la_clave_usa_el_default(t):
    """E-20 — un proyecto instalado antes de este cambio no tiene `rutaCodebase` en su
    harness.config.json y no la va a tener nunca: ese archivo no se reescribe. El default
    tiene que resolverse igual."""
    proy = _proyecto(con_indice=True)          # sin `rutaCodebase` en la config
    config = json.loads((proy / ".claude" / "harness.config.json").read_text(encoding="utf-8"))
    t.verdadero("E-20: la config no trae la clave", "rutaCodebase" not in config)
    t.no_contiene("E-20: encontro el indice en el default", AGENTE, _contexto(proy))


def test_e20b_con_la_clave_respeta_la_ruta_declarada(t):
    """E-20b — y si el proyecto disiente del default, se le hace caso."""
    proy = _proyecto(config_extra={"rutaCodebase": "docs/mapa-del-codigo"},
                     con_indice=True, ruta_codebase="docs/mapa-del-codigo")
    t.no_contiene("E-20b: lee la ruta declarada", AGENTE, _contexto(proy))

    proy_sin = _proyecto(config_extra={"rutaCodebase": "docs/mapa-del-codigo"},
                         con_indice=True, ruta_codebase="docs/codebase")
    t.contiene("E-20b: y no se conforma con el default cuando hay clave",
               AGENTE, _contexto(proy_sin))


# ── La forma de lo escrito: dev-codebase-forma ───────────────────────────────────
#
# El check se carga por ruta y se le pasa un evento de escritura sobre un archivo real
# de fixture, igual que hace 07_checks.py: `dev.archivo_escrito` lee del disco y no del
# evento, asi que un payload con `content` inventado no probaria nada.

sys.path.insert(0, str(RAIZ / "comun" / "hooks"))
from lib import reglas, secretos  # noqa: E402

CHECK = RAIZ / "harnesses" / "desarrollo" / "checks" / "dev-codebase-forma.py"
FIXTURE = RAIZ / "tests" / "fixtures" / "proyecto-codebase"


def _hallazgos(archivo, ruta_codebase="docs/codebase"):
    evento = {"hook_event_name": "PostToolUse", "tool_name": "Write",
              "cwd": str(FIXTURE), "tool_input": {"file_path": str(archivo)}}
    modulo = reglas._cargar(str(CHECK))
    return list(modulo.verificar(evento, str(FIXTURE), {"rutaCodebase": ruta_codebase}) or [])


def test_e08_indice_y_fichas_bien_no_dicen_nada(t):
    """E-08 — silencio es silencio: el costo tiene que ser proporcional a los problemas."""
    t.igual("E-08: indice sano, sin hallazgos", [],
            _hallazgos(FIXTURE / "docs/codebase/indice.md"))


def test_e08b_el_indice_roto_reporta_los_dos_sentidos(t):
    """E-08 — la correspondencia va en los dos sentidos, y cada sentido duele distinto."""
    hallazgos = _hallazgos(FIXTURE / "docs/codebase-indice-roto/indice.md",
                           ruta_codebase="docs/codebase-indice-roto")
    t.igual("E-08: dos hallazgos, uno por sentido", 2, len(hallazgos))
    juntos = " ".join(hallazgos)
    t.contiene("E-08: nombra la ficha que falta", "comun-hooks.md", juntos)
    t.contiene("E-08: y la segunda que falta", "comun-reglas.md", juntos)
    t.contiene("E-08: nombra la ficha huerfana", "comun-bin.md", juntos)


def test_e09_ficha_completa_no_dice_nada(t):
    """E-09 — las cuatro secciones estan."""
    t.igual("E-09: ficha completa, sin hallazgos", [],
            _hallazgos(FIXTURE / "docs/codebase/comun-hooks.md"))


def test_e09b_ficha_coja_nombra_las_secciones_que_faltan(t):
    """E-09 — y una ficha a la que le falta una no cumple."""
    hallazgos = _hallazgos(FIXTURE / "docs/codebase-ficha-coja/comun-hooks.md",
                           ruta_codebase="docs/codebase-ficha-coja")
    t.igual("E-09: un hallazgo", 1, len(hallazgos))
    t.contiene("E-09: nombra la que falta", "De qué depende", hallazgos[0])
    t.contiene("E-09: y la otra", "Dónde está", hallazgos[0])


def test_no_mira_lo_que_cae_fuera_del_directorio(t):
    """El check solo actua sobre lo que se escribio adentro del indice. Un .md de
    cualquier otro lado del proyecto no es asunto suyo.

    Se usa a proposito la ficha COJA, que si estuviera adentro daria un hallazgo: con una
    ficha sana el test pasaria igual sin recorte ninguno y no probaria nada. Se comprobo
    el 2026-08-21 sacando `_adentro`, y con la ficha sana el test seguia verde."""
    t.igual("fuera del directorio: silencio", [],
            _hallazgos(FIXTURE / "docs/codebase-ficha-coja/comun-hooks.md",
                       ruta_codebase="docs/codebase"))


def test_e10_nada_de_lo_escrito_matchea_un_patron_de_confianza_alta(t):
    """E-10 — ningun archivo del indice matchea un patron de bloqueo.

    Se verifica en la suite y no con un check en tiempo de ejecucion: pre-tool-use.py ya
    bloquea el secreto ANTES de que el archivo llegue al disco, y es la unica regla que
    este harness bloquea. Un segundo detector en PostToolUse llegaria tarde.

    El catalogo no tiene campo `severidad`: la que bloquea es `confianza: alta`."""
    catalogo = secretos.importar_patrones(str(RAIZ / "comun" / "reglas" / "secretos.patrones.json"))
    # Sin esto el test seria vacio: un catalogo que no cargo no encuentra nada y todo
    # pasa. Que el detector funcione lo prueba 04_secretos.py, con 100 comprobaciones.
    altas = [p for p in catalogo["patrones"] if p.get("confianza") == "alta"]
    t.verdadero("E-10: el catalogo cargo y tiene patrones que bloquean", len(altas) > 0)

    archivos = sorted((FIXTURE / "docs" / "codebase").glob("*.md"))
    t.verdadero("E-10: hay fichas que mirar", len(archivos) >= 3)
    for f in archivos:
        hallazgo = secretos.buscar_secreto(f.read_text(encoding="utf-8"), catalogo)
        bloquea = bool(hallazgo) and hallazgo.get("confianza") == "alta"
        t.verdadero("E-10: %s sin secreto de confianza alta" % f.name, not bloquea)
