# El aviso del primer recorrido del codigo, en SessionStart.
#
# Escenarios E-01 a E-13 y E-20 de docs/cambios/iniciador-code/spec.md.
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
              ruta_codebase=None, con_ficha=False):
    """Un proyecto descartable como los deja install.ps1.

    `ruta_codebase` es donde se crea el indice cuando `con_indice`; por defecto, el mismo
    default que resuelve el hook. `con_ficha` deja una ficha SIN indice: el estado en que
    queda un recorrido cortado a la mitad, que es lo que mira E-07."""
    proy = Path(tempfile.gettempdir()) / ("harness-cb-" + uuid.uuid4().hex[:8])
    proy.mkdir(parents=True, exist_ok=True)

    config = dict(config_extra or {})
    config.setdefault("usuario", "Nahue")
    _escribir(proy / ".claude" / "harness.config.json", json.dumps(config, ensure_ascii=False))
    _escribir(proy / ".claude" / "harness.lock.json",
              json.dumps({"harness": list(harness), "version": "0.13.0"}, ensure_ascii=False))

    if con_indice:
        _escribir(proy / (ruta_codebase or "docs/codebase") / "indice.md", "# Indice del codigo\n")

    if con_ficha:
        _escribir(proy / (ruta_codebase or "docs/codebase") / "comun-hooks.md", "# comun/hooks\n")

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


def test_e07_fichas_sin_indice_avisan_que_quedo_a_medias(t):
    """E-07 — terminado un recorrido existe indice.md; con fichas y sin indice, el
    recorrido quedo a medias.

    Es la mitad observable del escenario: el hook no ve terminar un recorrido, pero si ve
    el estado que deja uno cortado. Y no puede ir en PostToolUse: el agente escribe las
    fichas primero y el indice ultimo, asi que ahi dispararia una vez por ficha, con un
    presupuesto de ocho hallazgos por corrida."""
    ctx = _contexto(_proyecto(con_ficha=True))
    t.contiene("E-07: dice que quedo a medias", "a medias", ctx)
    t.contiene("E-07: y sigue nombrando al agente", AGENTE, ctx)
    t.no_contiene("E-07: no manda a arrancarlo de cero", "Sin indice del codigo todavia", ctx)


def test_e07b_sin_fichas_y_sin_indice_sigue_siendo_el_primer_recorrido(t):
    """E-07 — y el estado de siempre no cambio: sin nada escrito, se sugiere arrancar."""
    ctx = _contexto(_proyecto())
    t.contiene("E-07b: sugiere el primer recorrido", "Sin indice del codigo todavia", ctx)
    t.no_contiene("E-07b: y no habla de nada a medias", "a medias", ctx)


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


def test_e05_el_aviso_sale_como_contexto_y_nunca_como_compuerta(t):
    """E-05 — SessionStart avisa. Los secretos siguen siendo lo unico que bloquea.

    Se mira la FORMA del JSON y no el texto de la salida. Buscar la palabra "deny" en
    stdout parece equivalente y no lo es: pasaria igual con un hook que emite un
    permissionDecision con otro nombre, y fallaria en falso el dia que un aviso mencione
    la palabra. Lo que este escenario protege es que el aviso del recorrido no se vuelva
    una compuerta -el modo estricto que otras herramientas ofrecen y este harness no-."""
    salida = _correr_proceso({"session_id": "s", "cwd": str(_proyecto()),
                              "hook_event_name": "SessionStart"}).stdout.decode("utf-8")
    doc = json.loads(salida)
    hso = doc.get("hookSpecificOutput") or {}

    t.igual("E-05: el evento se declara", "SessionStart", hso.get("hookEventName"))
    t.contiene("E-05: y el aviso viaja como contexto", AGENTE, hso.get("additionalContext") or "")
    t.verdadero("E-05: sin permissionDecision en ningun nivel",
                "permissionDecision" not in doc and "permissionDecision" not in hso)
    t.verdadero("E-05: sin decision de continuar o frenar",
                doc.get("decision") is None and doc.get("continue") is not False)


def test_e06_ruta_invalida_cae_al_default_y_no_se_lleva_el_bloque(t):
    """E-06 — una `rutaCodebase` que no sirve como ruta cae al default, el hook sale con
    codigo 0 y el resto de su bloque se emite igual.

    El valor llega hasta aca porque `harness.config.json` es el archivo de la persona y
    el harness no lo valida ni lo pisa nunca. Sin la guarda de tipo, `os.path.join`
    levanta TypeError y se pierde el bloque ENTERO, no solo esta linea.

    🔴 Este escenario reemplaza al original y se probo dos veces mas de lo que quedo. El
    original usaba `docs/codebase` como ARCHIVO en vez de directorio, y no ejercitaba
    nada: `os.path.isfile` devuelve False y ya. Despues se agrego un caso con un byte
    nulo, y tampoco: `isfile` se traga el ValueError igual que el OSError -comprobado el
    2026-08-21 en Python 3.13-. Las dos defensas que eso motivaba salieron del hook
    porque ninguna tenia rojo: el `try/except` alrededor del `isfile` y la clausula que
    filtraba el nulo. Queda la guarda de tipo, que es la unica que si lo tiene."""
    proy = _proyecto(config_extra={"rutaCodebase": 12345})
    r = _correr_proceso({"session_id": "s", "cwd": str(proy),
                         "hook_event_name": "SessionStart"})
    t.igual("E-06: sale con codigo 0", 0, r.returncode)
    ctx = json.loads(r.stdout.decode("utf-8"))["hookSpecificOutput"]["additionalContext"]
    t.contiene("E-06: el resto del bloque se emite igual", "Nahue", ctx)
    t.contiene("E-06: y cae al default, donde no hay indice", AGENTE, ctx)


# ── La ruta, con la clave y sin ella ─────────────────────────────────────────────

def test_e20_el_check_tambien_resuelve_el_default_sin_la_clave(t):
    """E-20 — la mitad del escenario que no cubria nadie.

    🔴 El veredicto del 2026-08-21 dejo E-20 `sin sustento` teniendo `rojo visto: si`,
    porque el escenario habla de dos cosas —el aviso y lo que mira el indice— y solo el
    aviso tenia test: `_hallazgos()` siempre le pasa `rutaCodebase` explicito al check,
    asi que su default nunca se ejercitaba.

    Se arma un proyecto con una ficha COJA adentro del default. Si el check resuelve bien,
    la ficha cae adentro del alcance y hay hallazgo. Si el default estuviera mal, quedaria
    afuera y el check se callaria: por eso la ficha es coja y no sana, que es la misma
    leccion de `test_no_mira_lo_que_cae_fuera`.

    🔴 Se llama con las DOS formas. El escenario dice `harness.config.json` PREEXISTENTE
    y sin la clave, que es `{}`; `None` es el archivo que no existe. El veredicto del
    2026-08-21 marco que el test ejercitaba la segunda y el escenario nombra la primera.
    Hoy las dos caen en el mismo `(config or {}).get()` y por eso esta distincion NO tiene
    rojo propio ni puede tenerlo: vale como guarda para el dia que alguien separe las dos
    ramas, no como sustento nuevo."""
    proy = Path(tempfile.gettempdir()) / ("harness-cb-def-" + uuid.uuid4().hex[:8])
    ficha = proy / "docs" / "codebase" / "comun-hooks.md"
    _escribir(ficha, "# comun/hooks\n\n## Qué es\n\nLe faltan tres secciones a proposito.\n")

    evento = {"hook_event_name": "PostToolUse", "tool_name": "Write",
              "cwd": str(proy), "tool_input": {"file_path": str(ficha)}}
    modulo = reglas._cargar(str(CHECK))

    con_archivo = list(modulo.verificar(evento, str(proy), {}) or [])
    t.igual("E-20: config preexistente sin la clave, resuelve el default y ve la ficha",
            1, len(con_archivo))
    t.contiene("E-20: y nombra lo que falta", "De qué depende",
               con_archivo[0] if con_archivo else "")

    sin_archivo = list(modulo.verificar(evento, str(proy), None) or [])
    t.igual("E-20: y sin harness.config.json resuelve igual", con_archivo, sin_archivo)


def test_e20_sin_la_clave_usa_el_default(t):
    """E-20 — un proyecto instalado antes de este cambio no tiene `rutaCodebase` en su
    harness.config.json y no la va a tener nunca: ese archivo no se reescribe. El default
    tiene que resolverse igual."""
    proy = _proyecto(con_indice=True)          # sin `rutaCodebase` en la config
    config = json.loads((proy / ".claude" / "harness.config.json").read_text(encoding="utf-8"))
    t.verdadero("E-20: la config no trae la clave", "rutaCodebase" not in config)
    t.no_contiene("E-20: encontro el indice en el default", AGENTE, _contexto(proy))


def test_con_la_clave_respeta_la_ruta_declarada(t):
    """Si el proyecto disiente del default, al hook se le hace caso.

    🔴 Este test se llamaba `test_e20b_...` y el id estaba pisado: existe desde
    `fdfb726`, ANTES de que E-20b fuera un escenario. Su premisa es CON la clave y su
    sujeto es el hook; el E-20b de la spec dice SIN la clave y su sujeto es el agente.
    Quien greppeaba `E-20b` encontraba tres afirmaciones verdes que no hablan de eso.

    La proposicion que prueba es real y no tiene escenario propio, y no se le inventa
    uno: escribir la spec desde el codigo es el error que el refutador existe para
    cazar. Se queda sin id, que es lo que corresponde a un test libre."""
    proy = _proyecto(config_extra={"rutaCodebase": "docs/mapa-del-codigo"},
                     con_indice=True, ruta_codebase="docs/mapa-del-codigo")
    t.no_contiene("con la clave: lee la ruta declarada", AGENTE, _contexto(proy))

    proy_sin = _proyecto(config_extra={"rutaCodebase": "docs/mapa-del-codigo"},
                         con_indice=True, ruta_codebase="docs/codebase")
    t.contiene("con la clave: y no se conforma con el default",
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


def test_e13_una_copia_al_lado_del_original_se_reporta(t):
    """E-13 — un segundo recorrido no duplica fichas. El recorrido regenera el indice
    entero y pisa lo que habia: `comun-hooks-1.md` con `comun-hooks.md` todavia al lado es
    exactamente lo que el escenario niega."""
    hallazgos = _hallazgos(FIXTURE / "docs/codebase-duplicada/comun-hooks-1.md",
                           ruta_codebase="docs/codebase-duplicada")
    t.igual("E-13: un hallazgo", 1, len(hallazgos))
    t.contiene("E-13: nombra la copia", "comun-hooks-1.md", hallazgos[0])
    t.contiene("E-13: y el original que sigue ahi", "comun-hooks.md", hallazgos[0])


def test_e13b_el_sufijo_solo_no_alcanza(t):
    """E-13 — y un modulo que termina en numero no es copia de nada. `docs-adr-0006` tiene
    sufijo y no tiene original: sin `docs-adr.md` al lado no hay dos versiones del mismo
    modulo, y un check que lo reportara igual haria ruido sobre nombres legitimos."""
    t.igual("E-13: sufijo sin original, silencio", [],
            _hallazgos(FIXTURE / "docs/codebase-duplicada/docs-adr-0006.md",
                       ruta_codebase="docs/codebase-duplicada"))
    t.igual("E-13: y el original no se reporta a si mismo", [],
            _hallazgos(FIXTURE / "docs/codebase-duplicada/comun-hooks.md",
                       ruta_codebase="docs/codebase-duplicada"))


def test_no_mira_lo_que_cae_fuera_del_directorio(t):
    """El check solo actua sobre lo que se escribio adentro del indice. Un .md de
    cualquier otro lado del proyecto no es asunto suyo.

    Se usa a proposito la ficha COJA, que si estuviera adentro daria un hallazgo: con una
    ficha sana el test pasaria igual sin recorte ninguno y no probaria nada. Se comprobo
    el 2026-08-21 sacando `_adentro`, y con la ficha sana el test seguia verde."""
    t.igual("fuera del directorio: silencio", [],
            _hallazgos(FIXTURE / "docs/codebase-ficha-coja/comun-hooks.md",
                       ruta_codebase="docs/codebase"))


CODEBASE_REAL = RAIZ / "docs" / "codebase"


def _catalogo():
    return secretos.importar_patrones(str(RAIZ / "comun" / "reglas" / "secretos.patrones.json"))


def _bloquea(texto, catalogo):
    h = secretos.buscar_secreto(texto, catalogo)
    return bool(h) and h.get("confianza") == "alta"


def test_e10_control_positivo_el_detector_encuentra_lo_que_tiene_que_encontrar(t):
    """E-10, la mitad que hace que la otra valga algo.

    🔴 Este control existe porque el veredicto del 2026-08-21 fallo la version anterior
    de E-10: escaneaba fichas de fixture escritas a mano, sobre un corpus donde la propia
    spec declara que nunca se va a plantar un secreto. Un test que por diseno no puede
    fallar no sostiene nada.

    Se ataca al reves: primero se comprueba que la maquinaria SI encuentra, sobre el
    corpus que existe justamente para eso, y recien despues se afirma que sobre lo que
    escribio el recorrido no encuentra nada. Sin este control, un catalogo que no carga
    o un detector roto darian el mismo verde que un indice limpio."""
    catalogo = _catalogo()
    altas = [p for p in catalogo["patrones"] if p.get("confianza") == "alta"]
    t.verdadero("E-10: el catalogo trae patrones que bloquean", len(altas) > 0)

    corpus = (RAIZ / "tests" / "fixtures" / "corpus-secretos.txt").read_text(encoding="utf-8")
    t.verdadero("E-10: sobre el corpus de secretos, el detector encuentra",
                _bloquea(corpus, catalogo))


def test_e10_nada_de_lo_que_escribio_el_recorrido_matchea_un_patron_alto(t):
    """E-10 — ningun archivo ESCRITO POR EL RECORRIDO matchea un patron de bloqueo.

    El sujeto es docs/codebase/ de este repositorio, que es salida real de
    dev-iniciador-code y esta versionada. No es un fixture: si un recorrido futuro
    escribe un secreto y alguien lo commitea, este test se pone en rojo.

    Se verifica en la suite y no con un check en tiempo de ejecucion: pre-tool-use.py ya
    bloquea el secreto ANTES de que el archivo llegue al disco, y es la unica regla que
    este harness bloquea. Un segundo detector en PostToolUse llegaria tarde.

    El catalogo no tiene campo `severidad`: la que bloquea es `confianza: alta`."""
    catalogo = _catalogo()
    archivos = sorted(CODEBASE_REAL.glob("*.md"))
    t.verdadero("E-10: hay salida del recorrido que mirar", len(archivos) >= 10)
    for f in archivos:
        t.verdadero("E-10: %s sin secreto de confianza alta" % f.name,
                    not _bloquea(f.read_text(encoding="utf-8"), catalogo))
