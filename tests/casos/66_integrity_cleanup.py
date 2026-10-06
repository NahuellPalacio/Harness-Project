# Flow Governance, Wave 6: limpieza de integridad y preparacion para la calificacion.
#
# Escenarios E-01 a E-24 y E-36 a E-46 de docs/cambios/integrity-cleanup/spec.md. E-17, E-22, E-44
# y E-45 tienen ademas su mitad de PowerShell en tests/casos/66-integrity-instalador.ps1. E-25 a
# E-34 son los archivos de la suite que nombran; E-35 es la compuerta entera.
#
# Reusa los fixtures de los casos que ya los tienen: el Bloque 4 de 30, la Context Bar de 53, la
# refutacion atomica de 55, el plan de 20, el flujo de 62 y 63. Nada sale a la red.
import importlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CLI = BIN / "dev-harness.py"
sys.path.insert(0, str(BIN))


def _cargar(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, str(archivo))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


M20 = _cargar("caso_20_para_66", RAIZ / "tests" / "casos" / "20_orquestacion.py")
M30 = _cargar("caso_30_para_66", RAIZ / "tests" / "casos" / "30_b4_contabilidad.py")
M53 = _cargar("caso_53_para_66", RAIZ / "tests" / "casos" / "53_context_bar.py")
M55 = _cargar("caso_55_para_66", RAIZ / "tests" / "casos" / "55_refutacion_atomica.py")
W2 = _cargar("caso_62_para_66", RAIZ / "tests" / "casos" / "62_estado_del_flujo.py")
W3 = _cargar("caso_63_para_66", RAIZ / "tests" / "casos" / "63_compuerta_del_flujo.py")

A, B = W2.A, W2.B


def _borrar(*rutas):
    for r in rutas:
        shutil.rmtree(str(r), ignore_errors=True)


def _tmp():
    return Path(tempfile.mkdtemp(prefix="w6-"))


def _transcripcion(carpeta, mensajes):
    """Una transcripcion de Claude Code con los mensajes del asistente que se le pasen."""
    ruta = carpeta / "t.jsonl"
    lineas = [json.dumps({"type": "user", "sessionId": "s-66", "message": {"content": "hola"}})]
    for i, (mid, uso) in enumerate(mensajes):
        mensaje = {"id": mid, "model": "m-66", "role": "assistant", "content": []}
        if uso is not None:
            mensaje["usage"] = uso
        lineas.append(json.dumps({"type": "assistant", "sessionId": "s-66",
                                  "timestamp": "2026-10-02T10:00:%02d" % i, "message": mensaje}))
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return ruta


def _adaptador():
    return importlib.import_module("contabilidad.adaptadores.claude_code")


def _sin_uso(eventos):
    return [e for e in eventos if (e.get("usage") or {}).get("state") == "USAGE_UNRESOLVED"]


# -- E-01 a E-05: el Bloque 4 no convierte la falta de uso en un uso resuelto ------------------

def test_e01_un_mensaje_sin_usage_no_es_resuelto(t):
    """E-01 — un mensaje del asistente sin usage es USAGE_UNRESOLVED con clave estable."""
    carpeta = _tmp()
    try:
        ruta = _transcripcion(carpeta, [("m-sin", None), ("m-vacio", {}),
                                        ("m-con", {"input_tokens": 3, "output_tokens": 4})])
        registros = dict((r.get("dedupKey"), r) for r in _adaptador().leer(str(ruta)))
        for clave in ("msg|m-sin", "msg|m-vacio"):
            r = registros.get(clave) or {}
            t.igual("E-01 %s: USAGE_UNRESOLVED" % clave, "USAGE_UNRESOLVED", r.get("state"))
            t.verdadero("E-01 %s: nunca RESOLVED" % clave, r.get("state") != "RESOLVED")
            t.igual("E-01 %s: conserva el modelo" % clave, "m-66", r.get("model"))
            t.verdadero("E-01 %s: con su linea" % clave, "#L" in str(r.get("reference")))
        t.igual("E-01 el que trae usage sigue RESOLVED", "RESOLVED",
                (registros.get("msg|m-con") or {}).get("state"))
    finally:
        _borrar(carpeta)


def test_e02_el_sin_uso_llega_al_libro_una_vez(t):
    """E-02 — el registro sin uso llega al libro por la barra y por `--ingerir`, una sola vez."""
    b4 = M53._b4()
    carpeta = _tmp()
    try:
        ruta = _transcripcion(carpeta, [("m-sin", None), ("m-con", {"input_tokens": 3,
                                                                    "output_tokens": 4})])
        proyecto = carpeta / "p"
        proyecto.mkdir()
        sl = M53.SL
        for _ in range(3):
            leido = sl.ingerir(b4, str(proyecto), "s-66", str(ruta), None)
        t.igual("E-02 la barra lo escribio una vez", 1, len(_sin_uso(leido)))
        t.igual("E-02 y el que trae uso tambien", 2, len(leido))
        cli = carpeta / "c"
        (cli / ".claude").mkdir(parents=True)
        for _ in range(2):
            codigo, _, _ = M30._correr_cli(["contabilidad", "GCBA-66", "--ingerir", str(ruta),
                                            "--proyecto", str(cli)])
        libro = M30.c_libro.leer(M30.c_libro.ruta_de(str(cli), "GCBA-66"))
        t.igual("E-02 --ingerir sale 0", 0, codigo)
        t.igual("E-02 --ingerir lo escribio una vez", 1, len(_sin_uso(libro)))
    finally:
        _borrar(carpeta)


def test_e03_la_barra_lo_oculta_y_el_libro_lo_conserva(t):
    """E-03 — la barra no lo muestra como tokens; el libro lo conserva."""
    b4 = M53._b4()
    carpeta = _tmp()
    try:
        ruta = _transcripcion(carpeta, [("m-sin", None)])
        proyecto = carpeta / "p"
        proyecto.mkdir()
        leido = M53.SL.ingerir(b4, str(proyecto), "s-66", str(ruta), None)
        t.igual("E-03 el libro lo conserva", 1, len(_sin_uso(leido)))
        estado = b4["barra"].de(leido, "s-66", None)
        t.verdadero("E-03 el estado lo dice", "USAGE_UNRESOLVED" in estado["unresolved"])
        linea = M53.SL.dibujar(estado, b4)
        t.no_contiene("E-03 la barra no muestra tokens", "Tok", linea)
        t.no_contiene("E-03 ni un cero", " 0 ", linea)
    finally:
        _borrar(carpeta)


def _eventos_con_costo_parcial(sesion="s-66"):
    costos = importlib.import_module("contabilidad.costos")
    return [M30._ev(dedupKey="c-1", sessionId=sesion, usage=M30._uso(),
                    cost=M30._costo(actual=1.0, equivalente=1.0, modo="API")),
            M30._ev(dedupKey="c-2", sessionId=sesion, usage=M30._uso(),
                    cost=costos.sin_precio(billing_mode="API"))]


def _politica_api():
    return dict(M30.POLITICA, billingMode="API",
                statusBar={"budgetWarningAt": 0.5, "budgetErrorAt": 0.9})


def test_e04_un_costo_parcial_no_decide(t):
    """E-04 — un costo parcial da COST_UNRESOLVED, nunca WITHIN_BUDGET; la barra no da WARNING
    ni ERROR sobre el piso."""
    presupuesto = importlib.import_module("contabilidad.presupuesto")
    politica = _politica_api()
    resumen = M30.c_agr.resumir(_eventos_con_costo_parcial(), task_id=M30.TAREA)
    t.verdadero("E-04 el costo es parcial", resumen["cost"]["state"] != "RESOLVED"
                and resumen["cost"]["actual"] is not None)
    gastado, _ = presupuesto.consumido(resumen, politica)
    t.igual("E-04 no hay consumido que comparar", None, gastado)
    decision = presupuesto.evaluar(gastado, 0, politica)
    t.igual("E-04 COST_UNRESOLVED", "COST_UNRESOLVED", decision["status"])
    t.verdadero("E-04 nunca WITHIN_BUDGET", decision["status"] != "WITHIN_BUDGET")
    barra = importlib.import_module("contabilidad.barra")
    estado = barra.de(_eventos_con_costo_parcial(), "s-66", politica)
    t.igual("E-04 la barra no tiene fraccion", None, estado["budget"]["fraction"])
    t.verdadero("E-04 ni WARNING ni ERROR", estado["budget"]["level"] not in ("WARNING", "ERROR"))


def test_e05_un_costo_resuelto_decide_como_siempre(t):
    """E-05 — un costo resuelto decide como siempre."""
    presupuesto = importlib.import_module("contabilidad.presupuesto")
    politica = _politica_api()
    eventos = [M30._ev(dedupKey="r-1", sessionId="s-66", usage=M30._uso(),
                       cost=M30._costo(actual=1.0, equivalente=1.0, modo="API"))]
    resumen = M30.c_agr.resumir(eventos, task_id=M30.TAREA)
    gastado, _ = presupuesto.consumido(resumen, politica)
    t.igual("E-05 el consumido es el real", 1.0, gastado)
    t.igual("E-05 WITHIN_BUDGET", "WITHIN_BUDGET", presupuesto.evaluar(gastado, 0, politica)["status"])


# -- E-06 a E-08: la compuerta de REFUTATION es de la operacion -----------------------------

def _no_compila(t, escenario, proy, codigo):
    R = M55.R
    run = proy / ".claude" / "refutaciones" / M55.CLAVE / "run.json"
    error = None
    try:
        R.compilar(str(proy), M55.CLAVE)
    except Exception as e:                                     # noqa: BLE001
        error = e
    t.verdadero("%s: no compila" % escenario, error is not None)
    t.igual("%s: con la excepcion de la compuerta" % escenario, "CompuertaCerrada",
            type(error).__name__)
    t.contiene("%s: dice %s" % (escenario, codigo), codigo, str(error))
    t.verdadero("%s: no escribio run.json" % escenario, not run.exists())


def test_e06_directo_con_el_plan_sin_estar_listo(t):
    """E-06 — refutacion.compilar directo, con el plan sin estar listo: PLAN_NOT_READY."""
    proy = M55._proyecto()                      # listo para la compuerta
    try:
        ruta = proy / ".claude" / "planes" / (M55.CLAVE + ".json")
        listo = ruta.read_text(encoding="utf-8")
        plan = json.loads(listo)
        plan.pop("flowPreconditions", None)       # sin las precondiciones evaluadas
        plan["status"] = M55.orq_plan.estado_de(plan)
        ruta.write_text(json.dumps(plan), encoding="utf-8")
        _no_compila(t, "E-06", proy, "PLAN_NOT_READY")
        ruta.write_text(listo, encoding="utf-8")
        M55.R.compilar(str(proy), M55.CLAVE)
        t.verdadero("E-06 listo, compila",
                    (proy / ".claude" / "refutaciones" / M55.CLAVE / "run.json").exists())
    finally:
        M55._borrar(proy)


def test_e07_directo_con_el_contexto_cambiado(t):
    """E-07 — con el TaskContext cambiado: CONTEXT_STALE."""
    proy = M55._proyecto()
    try:
        M55._listo_para_la_compuerta(proy)
        ruta = proy / ".claude" / "contextos" / (M55.CLAVE + ".json")
        contexto = json.loads(ruta.read_text(encoding="utf-8"))
        contexto["task"]["title"] = "otra cosa"
        contexto["meta"]["context_hash"] = M55.R._armador().hash_de(contexto)
        ruta.write_text(json.dumps(contexto), encoding="utf-8")
        _no_compila(t, "E-07", proy, "CONTEXT_STALE")
    finally:
        M55._borrar(proy)


def test_e08_directo_con_otro_checkout(t):
    """E-08 — con otro checkout: REPOSITORY_MISMATCH."""
    proy = M55._proyecto()
    try:
        M55._listo_para_la_compuerta(proy)
        M55._git(proy, "remote", "set-url", "origin", "https://gitlab.example/otro/proyecto.git")
        _no_compila(t, "E-08", proy, "REPOSITORY_MISMATCH")
    finally:
        M55._borrar(proy)


# -- E-09 y E-10: el harness no escribe la configuracion de la persona ----------------------

def test_e09_set_y_remove_no_escriben_el_env(t):
    """E-09 — set/remove levantan y dejan el .env byte a byte igual."""
    almacen = importlib.import_module("integraciones.almacen")
    carpeta = _tmp()
    try:
        env = carpeta / ".env"
        env.write_bytes(b"# de la persona\nJIRA_TOKEN=x\nOTRA=y\n")
        antes = env.read_bytes()
        a = almacen.AlmacenSecretos(str(env), {})
        for rotulo, accion in (("set", lambda: a.set("JIRA_TOKEN", "nuevo")),
                               ("set nueva", lambda: a.set("OTRO_TOKEN", "z")),
                               ("remove", lambda: a.remove("JIRA_TOKEN"))):
            levanto = None
            try:
                accion()
            except almacen.ErrorDeAlmacen as e:
                levanto = str(e)
            t.verdadero("E-09 %s levanta ErrorDeAlmacen" % rotulo, levanto is not None)
            t.igual("E-09 %s no toca el .env" % rotulo, antes, env.read_bytes())
        t.igual("E-09 get sigue leyendo", "x", a.get("JIRA_TOKEN"))
    finally:
        _borrar(carpeta)


def test_e10_ninguna_ruta_del_harness_escribe_el_almacen(t):
    """E-10 — ningun archivo del harness llama a set ni a remove del almacen."""
    patron = re.compile(r"(almacen\w*|AlmacenSecretos\([^)]*\))\.(set|remove)\(", re.I)
    for raiz in (RAIZ / "harnesses", RAIZ / "comun"):
        for archivo in raiz.rglob("*.py"):
            texto = archivo.read_text(encoding="utf-8", errors="replace")
            t.vacio("E-10 %s no escribe el almacen" % archivo.name, patron.findall(texto))


# -- E-11 a E-13: el deny cruzado nombra lo que evaluo ---------------------------------------

def _contabilidad(clave):
    return W3._harness("contabilidad %s" % clave)


def test_e11_e12_sesion_bloqueada_no_corre_contabilidad_de_otra(t):
    """E-11/E-12 — deny, y el motivo nombra la tarea del comando y la que se evaluo."""
    p = W3._por_token()
    try:
        s = "w6-cruce"
        W3._vincular(p, s, A)
        salida = W3._pre(p, s, *_contabilidad(B))
        t.igual("E-11 sigue siendo deny", "deny", W3._decision(salida))
        motivo = W3._motivo(salida) or ""
        t.contiene("E-12 nombra la tarea del comando", B, motivo)
        t.contiene("E-12 y la de la sesion", A, motivo)
    finally:
        W3._borrar(p)


def test_e13_tampoco_si_la_otra_esta_sana(t):
    """E-13 — con la otra tarea sana, una sesion ligada a una bloqueada sigue sin pasar."""
    p = W2._proyecto(env=W3.ENV_SIN_TOKEN)
    try:
        W3._reconciliar(p, A)
        W2._listo(p, B)
        t.igual("E-13 la otra esta sana", "ACTIVE", (W2._estado(p, B) or {}).get("status"))
        t.igual("E-13 la de la sesion esta bloqueada", "BLOCKED", (W2._estado(p, A) or {}).get("status"))
        s = "w6-salto"
        W3._vincular(p, s, A)
        t.igual("E-13 deny: no hay salto de tarea", "deny", W3._decision(W3._pre(p, s, *_contabilidad(B))))
    finally:
        W3._borrar(p)


# -- E-14 y E-15: el plan ----------------------------------------------------------------

def test_e14_el_repositorio_de_la_unidad_es_el_del_flujo(t):
    """E-14 — workUnits[].context.repository es el de la identidad del flujo."""
    plan = importlib.import_module("orquestacion.plan")
    doc = plan.armar(M20._propuesta([M20._unidad("u1", dominio="integration")]), M20.CONTEXTO,
                     {}, {}, "0.26.0", "docs/x.json", M20.PRECONDICIONES)
    esperado = M20.PRECONDICIONES["repository"]["taskRepository"]
    t.igual("E-14 el de la identidad", esperado, doc["workUnits"][0]["context"].get("repository"))
    t.igual("E-14 el mismo de flowPreconditions", doc["flowPreconditions"]["repository"]["taskRepository"],
            doc["workUnits"][0]["context"].get("repository"))
    vacio = dict(M20.CONTEXTO, repository={"project": {"name": ""}})
    doc = plan.armar(M20._propuesta([M20._unidad("u1", dominio="integration")]), vacio,
                     {}, {}, "0.26.0", "docs/x.json", M20.PRECONDICIONES)
    t.igual("E-14 sin nombre en el TaskContext, igual el del flujo", esperado,
            doc["workUnits"][0]["context"].get("repository"))


def test_e15_el_aviso_de_es0901_dice_lo_que_cuenta(t):
    """E-15 — el aviso nombra el archivo que cuenta y no dice que la matriz no existe."""
    normativa = importlib.import_module("orquestacion.normativa")
    aviso = normativa.aviso_de_matriz()
    t.verdadero("E-15 sigue habiendo aviso", bool(aviso))
    t.contiene("E-15 nombra el archivo que cuenta", "es0901-7.1.json", aviso)
    t.contiene("E-15 nombra la matriz normativa", "matriz normativa", aviso)
    t.no_contiene("E-15 no dice que la matriz no se construyo", "no se construyo", aviso)
    t.verdadero("E-15 la matriz existe", (RAIZ / "harnesses" / "desarrollo" / "reglas" /
                                          "es0901-7.1-normative-matrix.json").is_file())


# -- E-16 a E-18: ningun estado mas fuerte que su evidencia -----------------------------------

def _componentes(doc):
    return doc["runtimeComponents"]


def test_e16_sin_libro_no_hay_active(t):
    """E-16 — sin libro, el Bloque 4 no es ACTIVE y la barra con senal OK es CONFIGURED."""
    proy = M53._registrado_y_visto()
    try:
        M53._senal(proy, sesion=M53.SESION, con_datos=False)
        doc = M53.B.resolver(str(proy), sesion=M53.SESION)
        t.igual("E-16 sin libro: Bloque 4 CONFIGURED", "CONFIGURED",
                _componentes(doc)["block4Accounting"]["state"])
        t.igual("E-16 sin libro: la barra CONFIGURED", "CONFIGURED",
                _componentes(doc)["contextBar"]["state"])
        t.igual("E-16 y no suma condicion", "READY", doc["bootstrap"]["status"])
        libro = Path(M53.B.libro_de_la_sesion(str(proy), M53.SESION))
        libro.parent.mkdir(parents=True, exist_ok=True)
        libro.write_text(json.dumps({"eventId": "e-1"}) + "\n", encoding="utf-8")
        doc = M53.B.resolver(str(proy), sesion=M53.SESION)
        t.igual("E-16 con libro: Bloque 4 ACTIVE", "ACTIVE", _componentes(doc)["block4Accounting"]["state"])
        t.igual("E-16 con libro: la barra ACTIVE", "ACTIVE", _componentes(doc)["contextBar"]["state"])
    finally:
        _borrar(proy)


def test_e18_una_senal_sin_lo_que_registro_el_instalador_no_prueba(t):
    """E-18 — sin la version o el momento que registro el instalador: RELOAD_REQUIRED."""
    proy = M53._proyecto(senal={"block4": M53.B.BLOCK4_OK})
    try:
        (proy / ".claude" / "harness.installation.json").unlink()
        doc = M53.B.resolver(str(proy), sesion=M53.SESION)
        t.igual("E-18 sin registro de instalacion: RELOAD_REQUIRED", "RELOAD_REQUIRED",
                _componentes(doc)["contextBar"]["state"])
    finally:
        _borrar(proy)
    proy = M53._registrado_y_visto()
    try:
        ruta = proy / ".claude" / "harness.installation.json"
        doc = json.loads(ruta.read_text(encoding="utf-8"))
        doc["runtimeComponents"]["contextBar"].pop("integrationVersion", None)
        ruta.write_text(json.dumps(doc), encoding="utf-8")
        M53._senal(proy, sesion=M53.SESION)
        t.igual("E-18 sin integrationVersion registrada: RELOAD_REQUIRED", "RELOAD_REQUIRED",
                _componentes(M53.B.resolver(str(proy), sesion=M53.SESION))["contextBar"]["state"])
    finally:
        _borrar(proy)


# -- E-19 y E-20: un error de dominio sale con 2 --------------------------------------------

def test_e19_una_propuesta_invalida_sale_con_2(t):
    """E-19 — plan con una propuesta invalida: sale 2, sin traceback."""
    p = W2._proyecto()
    try:
        W2._contexto(p, A)
        for rotulo, propuesta in (("sin unidades", {"objective": "x", "domains": ["backend"],
                                                    "workUnits": []}),
                                  ("dominio inventado", {"objective": "x", "domains": ["inventado"],
                                                         "workUnits": [{"id": "u", "domain": "backend"}]})):
            ruta = p / "prop.json"
            ruta.write_text(json.dumps(propuesta), encoding="utf-8")
            codigo, salida, error = W2._cli(p, "plan", A, "--propuesta", str(ruta))
            t.igual("E-19 %s: sale 2" % rotulo, 2, codigo)
            t.no_contiene("E-19 %s: sin traceback" % rotulo, "Traceback", salida + error)
            t.contiene("E-19 %s: dice que falla" % rotulo, "harness:", error)
    finally:
        _borrar(p)


def test_e20_un_error_inesperado_no_se_disfraza(t):
    """E-20 — un error inesperado no se convierte en un error de dominio ni sale con 2."""
    p = W2._proyecto()
    try:
        W2._contexto(p, A)
        ruta = p / "prop.json"
        ruta.write_text(json.dumps(W2._propuesta()), encoding="utf-8")
        modulo = _cargar("dev_harness_66", CLI)

        def _roto(*_a, **_k):
            raise KeyError("un bug")
        modulo.orq_plan.armar = _roto
        levanto = None
        try:
            codigo = modulo.main(["plan", A, "--propuesta", str(ruta), "--proyecto", str(p)])
        except KeyError as e:
            levanto, codigo = e, None
        t.verdadero("E-20 el KeyError sigue siendo un KeyError", isinstance(levanto, KeyError))
        t.verdadero("E-20 y no sale con 2", codigo != 2)
    finally:
        _borrar(p)


# -- E-21: dev-iniciador-code --------------------------------------------------------------

def test_e21_dev_iniciador_code_queda_registrado(t):
    """E-21 — registrado, no huerfano, y resuelve su ruteo."""
    reg = importlib.import_module("orquestacion.registro_agentes")
    r = reg.resolver_ruteo("dev-iniciador-code")
    t.verdadero("E-21 existe como agente", r.get("agentExists"))
    t.verdadero("E-21 no es huerfano", r.get("result") != "ORPHAN_AGENT")
    t.verdadero("E-21 rutea", r.get("routable"))
    t.verdadero("E-21 no aparece entre los huerfanos",
                "dev-iniciador-code" not in [h["id"] for h in reg.descubrir_huerfanos()])
    reconocidos = json.loads((RAIZ / "harnesses" / "desarrollo" / "reglas" /
                              "huerfanos-reconocidos.json").read_text(encoding="utf-8"))
    t.igual("E-21 ya no es un huerfano reconocido", [],
            [h["id"] for h in reconocidos.get("acknowledgedOrphans") or []])
    t.vacio("E-21 el registro valida", reg.validar_schema(reg.cargar()))


# -- E-22: Python ---------------------------------------------------------------------------

def test_e22_invoke_tests_no_toma_el_alias_por_un_python(t):
    """E-22 — Invoke-Tests valida el candidato: que corra y diga donde esta."""
    texto = (RAIZ / "tests" / "Invoke-Tests.ps1").read_text(encoding="utf-8-sig")
    t.contiene("E-22 Invoke-Tests pide sys.executable", "sys.executable", texto)
    t.no_contiene("E-22 y no elige por Get-Command solo",
                  "if (Get-Command $c -ErrorAction SilentlyContinue) { $python = $c; break }", texto)


# -- E-23 y E-24: la politica y el modelo de amenaza ------------------------------------------

def _clase(comando, tool="Bash"):
    policy = importlib.import_module("lib.tool_policy")
    return policy.clasificar(tool, {"command": comando})["class"]


def test_e23_desconocido_sigue_cerrado_y_la_salida_larga_es_escritura(t):
    """E-23 — un programa desconocido es UNRESOLVED; una opcion larga de salida es escritura."""
    sys.path.insert(0, str(RAIZ / "comun" / "hooks"))
    t.igual("E-23 desconocido", importlib.import_module("lib.tool_policy").UNRESOLVED,
            _clase("herramienta-desconocida --flag x"))
    for comando in ("grep --output=salida.txt patron f", "jq --output-file x . f.json",
                    "sort --out x f", "cut -f1 --outfile=y f", "tree --output y"):
        t.igual("E-23 %s: escritura" % comando, "MUTATING", _clase(comando))
    for comando in ("cat f", "grep -n patron f", "sort -u f", "ls -la"):
        t.igual("E-23 %s: lectura" % comando, "READ_ONLY", _clase(comando))


def test_e24_los_puntos_de_persistencia_estan_protegidos(t):
    """E-24 — con estado del flujo, escribir un punto de persistencia del host con una herramienta
    es FLOW_AUTHORITY_PROTECTED, tambien con la tarea sana; el git status de SessionStart corre sin
    core.fsmonitor; y el modelo de amenaza esta escrito."""
    p = W2._proyecto()
    try:
        W2._listo(p, A)
        s = "w6-persistencia"
        W3._vincular(p, s, A)
        t.igual("E-24 la tarea esta sana", None,
                W3._decision(W3._pre(p, s, "Write", {"file_path": str(p / "src" / "app.py"),
                                                     "content": "x"})))
        casa = "C:/Users/alguien"
        for ruta in (casa + "/AppData/Roaming/Python/Python312/site-packages/usercustomize.py",
                     casa + "/AppData/Roaming/Python/Python312/site-packages/x.pth",
                     str(p / "sitecustomize.py"),
                     casa + "/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1",
                     casa + "/Documents/PowerShell/profile.ps1",
                     casa + "/.gitconfig"):
            salida = W3._pre(p, s, "Write", {"file_path": ruta, "content": "x"})
            t.igual("E-24 Write %s: deny" % Path(ruta).name, "deny", W3._decision(salida))
            t.contiene("E-24 Write %s: protegido" % Path(ruta).name, "FLOW_AUTHORITY_PROTECTED",
                       W3._motivo(salida) or "")
        for tool, comando in (("Bash", "echo x >> ~/.gitconfig"),
                              ("PowerShell", "Add-Content $PROFILE 'x'"),
                              ("Bash", "echo import os > sitecustomize.py"),
                              ("Bash", "cp x.pth ~/AppData/Roaming/Python/site-packages/")):
            salida = W3._pre(p, s, tool, {"command": comando})
            t.igual("E-24 %s: deny" % comando, "deny", W3._decision(salida))
            t.contiene("E-24 %s: protegido" % comando, "FLOW_AUTHORITY_PROTECTED",
                       W3._motivo(salida) or "")
        t.igual("E-24 leer el .gitconfig sigue pasando", None,
                W3._decision(W3._pre(p, s, "Bash", {"command": "cat ~/.gitconfig"})))
    finally:
        W3._borrar(p)
    fuente = (RAIZ / "comun" / "hooks" / "session-start.py").read_text(encoding="utf-8")
    t.contiene("E-24 SessionStart corre git sin core.fsmonitor", "core.fsmonitor=false", fuente)
    doc = RAIZ / "docs" / "cambios" / "flow-governance" / "qualification-readiness.md"
    texto = doc.read_text(encoding="utf-8") if doc.exists() else ""
    for termino in ("THREAT_MODEL_BOUNDARY", "usercustomize.py", "sitecustomize.py", ".pth",
                    "perfil de PowerShell", "~/.gitconfig"):
        t.contiene("E-24 el modelo de amenaza nombra %s" % termino, termino, texto)
    t.no_contiene("E-24 no se declara calificado", "QUALIFIED\n", texto)


# -- Lo que encontro la primera pasada de la verificacion --------------------------------------

def test_e01b_un_usage_sin_numeros_tampoco_es_resuelto(t):
    """E-01 — un usage con las claves pero sin ningun numero (null, texto) no es un uso resuelto."""
    carpeta = _tmp()
    try:
        ruta = _transcripcion(carpeta, [("m-nulos", {"input_tokens": None, "output_tokens": None}),
                                        ("m-texto", {"input_tokens": "x"}),
                                        ("m-cero", {"input_tokens": 0, "output_tokens": 0})])
        registros = dict((r.get("dedupKey"), r) for r in _adaptador().leer(str(ruta)))
        for clave in ("msg|m-nulos", "msg|m-texto"):
            t.igual("E-01 %s: USAGE_UNRESOLVED" % clave, "USAGE_UNRESOLVED",
                    (registros.get(clave) or {}).get("state"))
        t.igual("E-01 un cero medido sigue RESOLVED", "RESOLVED",
                (registros.get("msg|m-cero") or {}).get("state"))
    finally:
        _borrar(carpeta)


def test_e18b_un_registro_vacio_tampoco_prueba(t):
    """E-18 — una version o un momento registrados que no son lo que dice el contrato (vacios, un
    texto cualquiera) no prueban nada: RELOAD_REQUIRED."""
    for campo, valor in (("lastValidatedAt", ""), ("lastValidatedAt", "!"),
                         ("lastValidatedAt", "ayer"), ("integrationVersion", "")):
        proy = M53._registrado_y_visto()
        try:
            ruta = proy / ".claude" / "harness.installation.json"
            doc = json.loads(ruta.read_text(encoding="utf-8"))
            doc["runtimeComponents"]["contextBar"][campo] = valor
            ruta.write_text(json.dumps(doc), encoding="utf-8")
            M53._senal(proy, sesion=M53.SESION)
            t.igual("E-18 %s=%r: RELOAD_REQUIRED" % (campo, valor), "RELOAD_REQUIRED",
                    _componentes(M53.B.resolver(str(proy), sesion=M53.SESION))["contextBar"]["state"])
        finally:
            _borrar(proy)


def _nombre_corto(ruta):
    """El nombre 8.3 de un archivo que existe, o None si el volumen no los tiene."""
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(512)
        n = ctypes.windll.kernel32.GetShortPathNameW(str(ruta), buf, 512)
        corto = buf.value if n else None
        return corto if corto and corto.lower() != str(ruta).lower() else None
    except Exception:                                          # noqa: BLE001
        return None


def test_e24b_los_puntos_de_persistencia_sin_nombrarlos(t):
    """E-24 — tambien protegidos sin nombrarlos de frente: `git config --global|--system|--file`,
    un stream de NTFS (`::$DATA`), un nombre corto 8.3, `${PROFILE}`, y lo que va a un
    site-packages."""
    p = W2._proyecto()
    casa = _tmp()
    try:
        W2._listo(p, A)
        s = "w6-persistencia-b"
        W3._vincular(p, s, A)
        protegidos = [("Write", {"file_path": "C:/Users/x/.gitconfig::$DATA", "content": "x"}),
                      ("Write", {"file_path": "C:/Users/x/AppData/Roaming/Python/site-packages/x.pth:$DATA",
                                 "content": "x"}),
                      ("Write", {"file_path": "C:/Users/x/Documents/WindowsPowerShell/"
                                              "Microsoft.PowerShell_profile.ps1::$DATA", "content": "x"}),
                      ("Write", {"file_path": "C:/Users/x/AppData/Roaming/Python/Python312/site-packages/"
                                              "requests/__init__.py", "content": "x"}),
                      ("Bash", {"command": "git config --global core.fsmonitor calc.exe"}),
                      ("Bash", {"command": "git config --system core.hooksPath /tmp/h"}),
                      ("Bash", {"command": "git config --file ~/.config/git/config core.pager x"}),
                      ("PowerShell", {"command": "Add-Content ${PROFILE} 'calc'"}),
                      ("Bash", {"command": "cp -r payload/ ~/AppData/Roaming/Python/Python312/site-packages/"})]
        real = casa / ".gitconfig"
        real.write_text("[user]\n", encoding="utf-8")
        corto = _nombre_corto(real)
        if corto:
            protegidos.append(("Write", {"file_path": corto, "content": "x"}))
        for tool, entrada in protegidos:
            salida = W3._pre(p, s, tool, entrada)
            rotulo = str(entrada.get("command") or entrada.get("file_path"))[-46:]
            t.igual("E-24 %s %s: deny" % (tool, rotulo), "deny", W3._decision(salida))
            t.contiene("E-24 %s %s: protegido" % (tool, rotulo), "FLOW_AUTHORITY_PROTECTED",
                       W3._motivo(salida) or "")
        for tool, entrada in (("Bash", {"command": "git config --get user.name"}),
                              ("Bash", {"command": "git config --global --get user.name"}),
                              # Desde E24-E13 (decision del 02-10-2026) escribir .git/config con
                              # `git config` es autoridad: el control es la lectura del mismo nombre.
                              ("Bash", {"command": "git config user.email"})):
            t.verdadero("E-24 %s: no es un punto de persistencia del host" % entrada["command"],
                        "FLOW_AUTHORITY_PROTECTED" not in (W3._motivo(W3._pre(p, s, tool, entrada)) or ""))
    finally:
        W3._borrar(p)
        _borrar(casa)


def test_e08b_la_biblioteca_no_acepta_otra_configuracion(t):
    """E-08 — `compilar` no recibe la configuracion de GitLab de quien la llama: la lee del .env
    con un solo lector, asi un argumento armado no saltea la compuerta."""
    import inspect
    R = M55.R
    t.verdadero("E-08 compilar no tiene parametro gitlab", "gitlab" not in inspect.signature(R.compilar).parameters)
    t.verdadero("E-08 ni la compuerta", "gitlab" not in inspect.signature(R.compuerta).parameters)


def test_e24c_nombres_cortos_desde_el_shell_y_la_config_xdg_de_git(t):
    """E-24 — un nombre corto 8.3 escrito desde el shell tambien es un punto de persistencia, y la
    configuracion global de git en su ruta XDG (`~/.config/git/config`) tambien."""
    p = W2._proyecto()
    casa = _tmp()
    try:
        W2._listo(p, A)
        s = "w6-persistencia-c"
        W3._vincular(p, s, A)
        real = casa / ".gitconfig"
        real.write_text("[user]\n", encoding="utf-8")
        sitio = casa / "site-packages"
        sitio.mkdir()
        casos = [("Bash", {"command": "echo x >> ~/.config/git/config"}),
                 ("Write", {"file_path": "C:/Users/x/.config/git/config", "content": "x"})]
        corto = _nombre_corto(real)
        if corto:
            casos += [("Bash", {"command": "echo x >> '%s'" % corto.replace("\\", "/")}),
                      ("PowerShell", {"command": "Add-Content '%s' x" % corto})]
        corto_sitio = _nombre_corto(sitio)
        if corto_sitio:
            casos.append(("Bash", {"command": "echo x > '%s/zz.py'" % corto_sitio.replace("\\", "/")}))
        t.verdadero("E-24 el volumen tiene nombres cortos para probarlo", bool(corto))
        for tool, entrada in casos:
            salida = W3._pre(p, s, tool, entrada)
            rotulo = str(entrada.get("command") or entrada.get("file_path"))[-46:]
            t.igual("E-24 %s %s: deny" % (tool, rotulo), "deny", W3._decision(salida))
            t.contiene("E-24 %s %s: protegido" % (tool, rotulo), "FLOW_AUTHORITY_PROTECTED",
                       W3._motivo(salida) or "")
        t.igual("E-24 escribir otro archivo con un nombre corto sigue pasando", None,
                W3._decision(W3._pre(p, s, "Bash", {"command": "echo x > '%s/otro.txt'" % str(
                    casa).replace("\\", "/")})))
    finally:
        W3._borrar(p)
        _borrar(casa)


def _msys(ruta):
    """C:\\x\\y -> /c/x/y, como la escribe Git Bash."""
    r = str(ruta).replace("\\", "/")
    return "/" + r[0].lower() + r[2:] if len(r) > 1 and r[1] == ":" else r


def test_e24d_cada_forma_de_la_misma_ruta(t):
    """E-24 — la misma ruta en cada forma que el texto deja ver: un stream o un punto final en
    cualquier segmento (tambien la ruta XDG), la forma MSYS de Git Bash, y `-Parametro:valor` de
    PowerShell."""
    p = W2._proyecto()
    casa = _tmp()
    try:
        W2._listo(p, A)
        s = "w6-persistencia-d"
        W3._vincular(p, s, A)
        real = casa / ".gitconfig"
        real.write_text("[user]\n", encoding="utf-8")
        corto = _nombre_corto(real)
        casos = [("Write", {"file_path": "C:/Users/x/.config/git/config::$DATA", "content": "x"}),
                 ("Write", {"file_path": "C:/Users/x/.config/git/config.", "content": "x"}),
                 ("Write", {"file_path": "C:/Users/x/.config./git/config", "content": "x"}),
                 ("Write", {"file_path": "C:/Users/x/.gitconfig.", "content": "x"}),
                 ("PowerShell", {"command": "Add-Content 'C:/Users/x/.config/git/config::$DATA' x"}),
                 ("PowerShell", {"command": "Add-Content 'C:/Users/x/.gitconfig.' x"}),
                 ("Bash", {"command": "echo x >> 'C:/Users/x/.gitconfig.'"}),
                 ("Bash", {"command": "echo x >> /c/Users/x/.config/git/config"})]
        if corto:
            casos += [("Bash", {"command": "echo x >> '%s'" % _msys(corto)}),
                      ("PowerShell", {"command": "Add-Content -Path:'%s' -Value x" % corto}),
                      ("PowerShell", {"command": "Set-Content -LiteralPath:%s x" % corto})]
        for tool, entrada in casos:
            salida = W3._pre(p, s, tool, entrada)
            rotulo = str(entrada.get("command") or entrada.get("file_path"))[-46:]
            t.igual("E-24 %s %s: deny" % (tool, rotulo), "deny", W3._decision(salida))
            t.contiene("E-24 %s %s: protegido" % (tool, rotulo), "FLOW_AUTHORITY_PROTECTED",
                       W3._motivo(salida) or "")
        for tool, entrada in (("Bash", {"command": "echo x > config.txt"}),
                              ("Write", {"file_path": str(p / "src" / "config"), "content": "x"}),
                              ("Bash", {"command": "echo x > '%s'" % _msys(casa / "otro.txt")})):
            t.igual("E-24 %s: sigue pasando" % str(entrada.get("command") or entrada.get("file_path"))[-40:],
                    None, W3._decision(W3._pre(p, s, tool, entrada)))
    finally:
        W3._borrar(p)
        _borrar(casa)


# -- Lo que encontro la revision adversarial independiente -------------------------------------

def test_e24e_la_revision_independiente(t):
    """E-24 — las tres clases que encontro la revision adversarial independiente: un site-packages
    como destino final (con punto final, con barra, por nombre corto), las formas de git config que
    git acepta por las protegidas (`--glob`, `--sys`, `--fil`, `-f<ruta>`), y `uniq` con `-` como
    entrada, que es la forma de escribir su salida."""
    p = W2._proyecto()
    casa = _tmp()
    try:
        W2._listo(p, A)
        s = "w6-persistencia-e"
        W3._vincular(p, s, A)
        sitio = casa / "site-packages"
        sitio.mkdir()
        corto_sitio = _nombre_corto(sitio)
        win = "C:\\Users\\x\\AppData\\Roaming\\Python\\Python312\\site-packages."
        casos = [("E24-E1", "PowerShell", "Copy-Item -Recurse payload %s" % win),
                 ("E24-E2", "Bash", "cp -r payload/ C:/Users/x/AppData/Roaming/Python/Python312/site-packages./"),
                 ("E24-E4", "Bash", "git config --glob core.fsmonitor calc.exe"),
                 ("E24-E5", "Bash", "git config --sys core.hooksPath /tmp/h"),
                 ("E24-E6", "Bash", "git config --fil C:/tmp/otra.cfg core.pager x"),
                 ("E24-E7", "Bash", "git config -fC:/tmp/otra.cfg core.pager x"),
                 ("E24-E8", "Bash", "uniq - C:/Users/x/.gitconfig"),
                 ("E24-E9", "Bash", "uniq -- - C:/Users/x/.gitconfig")]
        t.verdadero("E24-E3 el volumen tiene nombres cortos para probarlo", bool(corto_sitio))
        if corto_sitio:
            casos += [("E24-E3", "Bash", "cp -r payload/ '%s'" % corto_sitio.replace("\\", "/")),
                      ("E24-E3", "PowerShell", "Copy-Item -Recurse payload '%s'" % corto_sitio)]
        for escenario, tool, comando in casos:
            salida = W3._pre(p, s, tool, {"command": comando})
            t.igual("%s %s: deny" % (escenario, comando[-50:]), "deny", W3._decision(salida))
            t.contiene("%s %s: protegido" % (escenario, comando[-50:]), "FLOW_AUTHORITY_PROTECTED",
                       W3._motivo(salida) or "")
        policy = importlib.import_module("lib.tool_policy")
        for comando in ("uniq - C:/Users/x/salida.txt", "uniq -- - C:/Users/x/salida.txt"):
            t.igual("E24-E8/E9 %s: escritura" % comando, "MUTATING", _clase(comando))
        # Los controles negativos: lo que lee sigue leyendo, y un destino cualquiera no se vuelve
        # protegido por parecerse.
        for comando in ("cat ~/.gitconfig", "git config --global --get user.name",
                        "git config --glob --get user.name", "git config --fil x --list",
                        "uniq f", "uniq -", "uniq -c f", "uniq -- f"):
            t.igual("E-24 %s: lectura" % comando, "READ_ONLY", _clase(comando))
        for tool, comando in (("Bash", "cp -r payload/ build/"),
                              ("Bash", "cp -r payload/ C:/Users/x/site-packages-viejo/"),
                              ("PowerShell", "Copy-Item -Recurse payload C:\\Users\\x\\packages"),
                              ("Bash", "git config user.email"),   # la escritura es E24-E13
                              ("Bash", "uniq - salida.txt")):
            salida = W3._pre(p, s, tool, {"command": comando})
            t.igual("E-24 %s: sigue pasando con la tarea sana" % comando, None, W3._decision(salida))
            t.verdadero("E-24 %s: no es protegido" % comando,
                        "FLOW_AUTHORITY_PROTECTED" not in (W3._motivo(salida) or ""))
        t.igual("E-24 la politica sigue con su clase desconocida", "UNRESOLVED_TOOL_CLASS",
                policy.UNRESOLVED)
    finally:
        W3._borrar(p)
        _borrar(casa)


# -- Lo que encontro la quinta pasada --------------------------------------------------------------

def test_e24f_la_quinta_pasada(t):
    """E-24 — lo que encontro la quinta pasada: `git config --global` lanzado por otro programa con
    sus argumentos en una sola palabra (`Start-Process git '...'`, un alias de `-c`), la carpeta
    site-packages pegada a una opcion con `=`, y un archivo de persistencia pegado a una opcion
    corta (`sort -ositecustomize.py`)."""
    p = W2._proyecto()
    try:
        W2._listo(p, A)
        s = "w6-persistencia-f"
        W3._vincular(p, s, A)
        casos = [("E24-E10", "PowerShell", "Start-Process git 'config --global core.fsmonitor calc'"),
                 ("E24-E10", "PowerShell",
                  "Start-Process -FilePath git -ArgumentList 'config --global core.fsmonitor calc'"),
                 ("E24-E10", "Bash", "git -c alias.x='config --global core.fsmonitor calc' x"),
                 ("E24-E10", "PowerShell",
                  "Start-Process git -ArgumentList 'config','--global','core.fsmonitor','calc'"),
                 ("E24-E10", "PowerShell", "Start-Process git -ArgumentList config, --global, core.fsmonitor, calc"),
                 ("E24-E11", "Bash", "cp -r payload --target-directory=site-packages"),
                 ("E24-E11", "Bash", "cp -r payload --target-directory=site-packages."),
                 ("E24-E12", "Bash", "sort -ositecustomize.py f"),
                 ("E24-E12", "Bash", "sort -ousercustomize.py f"),
                 ("E24-E12", "Bash", "sort -o.gitconfig f"),
                 ("E24-E12", "Bash", "sort -osite-packages/x.py f")]
        for escenario, tool, comando in casos:
            salida = W3._pre(p, s, tool, {"command": comando})
            t.igual("%s %s: deny" % (escenario, comando[-50:]), "deny", W3._decision(salida))
            t.contiene("%s %s: protegido" % (escenario, comando[-50:]), "FLOW_AUTHORITY_PROTECTED",
                       W3._motivo(salida) or "")
        for tool, comando in (("Bash", "sort -osalida.txt f"),
                              ("Bash", "cp -r payload --target-directory=build"),
                              ("Bash", "git commit -m arreglo"),
                              ("PowerShell", "Start-Process git 'commit -m x'")):
            salida = W3._pre(p, s, tool, {"command": comando})
            t.verdadero("E-24 %s: no es protegido" % comando,
                        "FLOW_AUTHORITY_PROTECTED" not in (W3._motivo(salida) or ""))
    finally:
        W3._borrar(p)


def test_e16b_un_libro_sin_ningun_registro_no_es_datos(t):
    """E-16 — un libro que existe pero no tiene ningun registro (un salto de linea, un espacio, una
    linea que no es JSON, un objeto vacio) no es un libro con datos: el Bloque 4 y la barra siguen
    CONFIGURED."""
    for contenido in ("\n", " ", "x", "{}\n", "[1]\n"):
        proy = M53._registrado_y_visto()
        try:
            M53._senal(proy, sesion=M53.SESION, con_datos=False)
            libro = Path(M53.B.libro_de_la_sesion(str(proy), M53.SESION))
            libro.parent.mkdir(parents=True, exist_ok=True)
            libro.write_text(contenido, encoding="utf-8")
            doc = M53.B.resolver(str(proy), sesion=M53.SESION)
            t.igual("E-16 libro %r: Bloque 4 CONFIGURED" % contenido, "CONFIGURED",
                    _componentes(doc)["block4Accounting"]["state"])
            t.igual("E-16 libro %r: la barra CONFIGURED" % contenido, "CONFIGURED",
                    _componentes(doc)["contextBar"]["state"])
        finally:
            _borrar(proy)


# -- git config sin alcance: la configuracion del repositorio es autoridad -----------------------

def test_e24g_git_config_que_escribe_es_autoridad(t):
    """E24-E13 — `.git/` es autoridad del flujo desde la Wave 4: escribirla con `git config`, sin
    alcance o con cualquiera, es lo mismo que escribir `.git/config` con Write. Decision de la
    persona del 02-10-2026: sin excepcion por clave. Las lecturas de `git config` siguen siendo
    lecturas, y `git commit` no es `git config`."""
    p = W2._proyecto()
    try:
        W2._listo(p, A)
        s = "w6-git-config-local"
        W3._vincular(p, s, A)
        escrituras = [("E24-E13a", "git config user.email x@example.invalid"),
                      ("E24-E13b", "git config core.fsmonitor sintetico-w6"),
                      ("E24-E13c", "git config --add user.name x"),
                      ("E24-E13d", "git config --replace-all user.name x"),
                      ("E24-E13e", "git config --unset user.name"),
                      ("E24-E13e", "git config --unset-all user.name"),
                      ("E24-E13e", "git config --remove-section alias"),
                      ("E24-E13e", "git config unset user.name"),
                      ("E24-E13", "git config --local core.hooksPath h"),
                      ("E24-E13", "git config --worktree core.pager x"),
                      ("E24-E13", "git config set user.name x"),
                      ("E24-E13", "git config --edit"),
                      ("E24-E13", "git -C . config core.fsmonitor sintetico-w6"),
                      # Detras de un programa que le agrega argumentos al correr, un nombre solo
                      # puede ser una escritura: el valor lo pone xargs (septima pasada).
                      ("E24-E13j", "echo sintetico-w6 | xargs git config core.fsmonitor"),
                      ("E24-E13j", "xargs -a args.txt git config core.fsmonitor"),
                      ("E24-E13j", "echo sintetico-w6 | xargs git config --local core.fsmonitor"),
                      ("E24-E13j", "echo calc | xargs git config --glob core.fsmonitor")]
        for escenario, comando in escrituras:
            salida = W3._pre(p, s, "Bash", {"command": comando})
            t.igual("%s %s: deny" % (escenario, comando), "deny", W3._decision(salida))
            t.contiene("%s %s: protegido" % (escenario, comando), "FLOW_AUTHORITY_PROTECTED",
                       W3._motivo(salida) or "")
        lecturas = [("E24-E13f", "git config user.email"),
                    ("E24-E13g", "git config --get user.email"),
                    ("E24-E13h", "git config --list"),
                    ("E24-E13h", "git config -l"),
                    ("E24-E13", "git config --get-regexp user"),
                    ("E24-E13", "git config --global --get user.name"),
                    ("E24-E13", "git config get user.email"),
                    ("E24-E13", "git config list"),
                    ("E24-E13", "git config --show-origin --list"),
                    ("E24-E13", "git config --type=bool --get core.bare"),
                    ("E24-E13", "git config -z --list")]
        for escenario, comando in lecturas:
            t.igual("%s %s: lectura" % (escenario, comando), "READ_ONLY", _clase(comando))
            t.igual("%s %s: pasa" % (escenario, comando), None,
                    W3._decision(W3._pre(p, s, "Bash", {"command": comando})))
        for comando in ("git commit -m arreglo", "git status", "git diff"):
            salida = W3._pre(p, s, "Bash", {"command": comando})
            t.igual("E24-E13i %s: pasa con la tarea sana" % comando, None, W3._decision(salida))
            t.verdadero("E24-E13i %s: no es protegido" % comando,
                        "FLOW_AUTHORITY_PROTECTED" not in (W3._motivo(salida) or ""))
        # Una palabra cualquiera que termina en `=config` no es un alias de git.
        salida = W3._pre(p, s, "Bash", {"command": "npm run build --modo=config a b"})
        t.verdadero("E24-E13 `--modo=config a b` no es git config",
                    "FLOW_AUTHORITY_PROTECTED" not in (W3._motivo(salida) or ""))
        # E-53 de la Wave 4, decidido por la persona: lo desconocido pasa con la tarea sana.
        t.igual("E24-E13 npm test sigue pasando con la tarea sana", None,
                W3._decision(W3._pre(p, s, "Bash", {"command": "npm test"})))
    finally:
        W3._borrar(p)
    p = W3._dos()
    try:
        s = W3._sesion("w6-git-config-bloqueada")
        W3._vincular(p, s, A)
        t.igual("E24-E13 npm test con la tarea bloqueada: deny", "deny",
                W3._decision(W3._pre(p, s, *W3._bash("npm test"))))
    finally:
        W3._borrar(p)


# -- Una herramienta desconocida que no es shell (MCP) -------------------------------------------

def test_e24h_una_herramienta_desconocida_no_escribe_la_autoridad(t):
    """E24-E14 — una herramienta que la politica no conoce y no es shell (un servidor MCP que
    escribe archivos) no escribe `.claude/`, `.git/` ni un punto de persistencia del host: si un
    valor de una linea de su `tool_input`, a cualquier profundidad, es una de esas rutas, es
    FLOW_AUTHORITY_PROTECTED tambien con la tarea sana. Decision de la persona del 02-10-2026."""
    p = W2._proyecto()
    try:
        W2._listo(p, A)
        s = "w6-mcp"
        W3._vincular(p, s, A)
        decision = str(p / ".claude" / "runtime" / "tasks" / A / "decisions" / "d.json")
        protegidos = [("E24-E14a", "mcp__filesystem__write_file", {"path": decision, "content": "{}"}),
                      ("E24-E14b", "mcp__filesystem__write_file", {"path": ".claude/settings.json", "content": "x"}),
                      ("E24-E14c", "mcp__filesystem__write_file", {"path": str(p / ".git" / "config"), "content": "x"}),
                      ("E24-E14d", "mcp__filesystem__write_file", {"path": "C:/Users/x/.gitconfig", "content": "x"}),
                      ("E24-E14e", "mcp__filesystem__move_file",
                       {"source": "a.py", "destination": "C:/Users/x/AppData/Roaming/Python/site-packages/usercustomize.py"}),
                      ("E24-E14f", "mcp__filesystem__edit_file",
                       {"edits": [{"path": "C:/Users/x/Documents/PowerShell/profile.ps1", "newText": "x"}]})]
        for escenario, tool, entrada in protegidos:
            salida = W3._pre(p, s, tool, entrada)
            t.igual("%s %s: deny" % (escenario, tool), "deny", W3._decision(salida))
            t.contiene("%s %s: protegido" % (escenario, tool), "FLOW_AUTHORITY_PROTECTED",
                       W3._motivo(salida) or "")
        controles = [("mcp__filesystem__write_file", {"path": str(p / "src" / "app.py"), "content": "x"}),
                     ("mcp__filesystem__write_file",
                      {"path": str(p / "README.md"), "content": "Agregar .claude/ y .git/ al ignore\nlisto\n"}),
                     ("mcp__jira__get_issue", {"key": A}),
                     ("mcp__x__y", {})]
        for tool, entrada in controles:
            salida = W3._pre(p, s, tool, entrada)
            t.igual("E24-E14 %s %s: pasa con la tarea sana" % (tool, list(entrada.values())[:1]), None,
                    W3._decision(salida))
            t.verdadero("E24-E14 %s: no es protegido" % tool,
                        "FLOW_AUTHORITY_PROTECTED" not in (W3._motivo(salida) or ""))
        policy = importlib.import_module("lib.tool_policy")
        t.igual("E24-E14 una herramienta desconocida sin rutas sigue UNRESOLVED", policy.UNRESOLVED,
                policy.clasificar("mcp__x__y", {"q": "hola"})["class"])
        t.igual("E24-E14 Task sigue siendo la delegacion", "WORKFLOW_ADVANCING",
                policy.clasificar("Task", {"prompt": "revisar .claude/settings.json"})["class"])
    finally:
        W3._borrar(p)


def test_e24i_las_herramientas_mcp_llegan_a_la_compuerta(t):
    """E24-E15 — el matcher registrado de PreToolUse alcanza a las herramientas MCP (`^mcp__`,
    anclado): sin eso E24-E14 y la compuerta no ven una sesion real (octava pasada). No alcanza a
    nada mas de lo que no alcanzaba, y PostToolUse no cambia. Decision de la persona del
    02-10-2026. Y los valores de E24-E14 se miran a cualquier profundidad, tambien las claves de un
    objeto (`{"files": {ruta: contenido}}`)."""
    plantilla = json.loads((RAIZ / "comun" / "settings" / "hooks.plantilla.json").read_text(
        encoding="utf-8"))
    pre = [g["matcher"] for g in plantilla["hooks"]["PreToolUse"]]
    for herramienta in ("mcp__filesystem__write_file", "mcp__filesystem__move_file", "mcp__x__y",
                        "mcp__jira__get_issue"):
        t.verdadero("E24-E15 PreToolUse alcanza a %s" % herramienta,
                    any(re.search(m, herramienta) for m in pre))
    for herramienta in ("TaskCreate", "TaskOutput", "Read", "Glob", "Grep", "WebFetch", "x_mcp__y"):
        t.verdadero("E24-E15 y sigue sin alcanzar a %s" % herramienta,
                    not any(re.search(m, herramienta) for m in pre))
    t.igual("E24-E15 PostToolUse no cambia", "Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell",
            plantilla["hooks"]["PostToolUse"][0]["matcher"])
    p = W2._proyecto()
    try:
        W2._listo(p, A)
        s = "w6-mcp-hondo"
        W3._vincular(p, s, A)
        hondo = ".claude/settings.json"
        for _ in range(12):
            hondo = [hondo]
        anidado = ".claude/settings.json"
        for clave in "abcdefghijkl":
            anidado = {clave: anidado}
        for rotulo, entrada in (("lista de 12 niveles", {"a": hondo}),
                                ("objeto de 12 niveles", anidado),
                                ("la ruta como clave", {"files": {".claude/settings.json": "{}"}}),
                                ("el .gitconfig como clave",
                                 {"files": {"~/.gitconfig": "[core]\n fsmonitor = calc\n"}})):
            salida = W3._pre(p, s, "mcp__fs__write_files", entrada)
            t.igual("E24-E15 %s: deny" % rotulo, "deny", W3._decision(salida))
            t.contiene("E24-E15 %s: protegido" % rotulo, "FLOW_AUTHORITY_PROTECTED",
                       W3._motivo(salida) or "")
        salida = W3._pre(p, s, "mcp__fs__write_files", {"files": {"src/app.py": "x = 1\n"}})
        t.igual("E24-E15 una clave que es codigo sigue pasando", None, W3._decision(salida))
    finally:
        W3._borrar(p)


def test_e24j_una_mcp_que_corre_comandos(t):
    """E24-E16 — un servidor MCP que corre comandos recibe el comando en un valor de una linea: ese
    valor se mira tambien como comando, con la misma regla que Bash (`git config` que escribe, un
    punto de persistencia nombrado). Decision de la persona del 02-10-2026. Un valor de varias
    lineas sigue siendo contenido: es un limite declarado."""
    p = W2._proyecto()
    try:
        W2._listo(p, A)
        s = "w6-mcp-shell"
        W3._vincular(p, s, A)
        for tool, comando in (("mcp__shell__run", "git config core.fsmonitor evil"),
                              ("mcp__desktop-commander__start_process", "git config core.hooksPath h"),
                              ("mcp__shell__run", "git config --global core.fsmonitor evil"),
                              ("mcp__shell__run", "echo [core] >> ~/.gitconfig && echo ok"),
                              ("mcp__shell__run", "cp x.pth C:/Users/x/AppData/Roaming/Python/site-packages/")):
            salida = W3._pre(p, s, tool, {"command": comando})
            t.igual("E24-E16 %s «%s»: deny" % (tool, comando), "deny", W3._decision(salida))
            t.contiene("E24-E16 %s «%s»: protegido" % (tool, comando), "FLOW_AUTHORITY_PROTECTED",
                       W3._motivo(salida) or "")
        for comando in ("npm test", "git config --get user.name", "git status", "pytest -q"):
            salida = W3._pre(p, s, "mcp__shell__run", {"command": comando})
            t.igual("E24-E16 mcp__shell__run «%s»: pasa con la tarea sana" % comando, None,
                    W3._decision(salida))
    finally:
        W3._borrar(p)


def _pre_crudo(p, crudo):
    """PreToolUse con un evento que se manda tal cual, sin pasar por json.dumps."""
    return subprocess.run([sys.executable, str(RAIZ / "comun" / "hooks" / "pre-tool-use.py")],
                          input=crudo.encode("utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=W3._env(), cwd=str(p))


def _salida_cruda(r):
    texto = r.stdout.decode("utf-8")
    return json.loads(texto) if texto.strip() else None


def test_e24k_un_evento_que_no_se_puede_leer(t):
    """E24-E17 — si PreToolUse no puede leer el evento (un JSON de 3000 niveles que json.loads no
    aguanta, o uno roto) y el proyecto tiene estado del flujo, falla cerrado: deny
    FLOW_GATE_UNRESOLVED, como un fallo interno de la compuerta (E-54 de la Wave 3). Sin estado
    del flujo, sigue sin bloquear. Decision de la persona del 02-10-2026."""
    hondo = "[" * 3000 + "]" * 3000
    p = W2._proyecto()
    try:
        W2._listo(p, A)
        s = "w6-evento-hondo"
        W3._vincular(p, s, A)
        cwd = json.dumps(str(p))
        for rotulo, crudo in (
                ("JSON de 3000 niveles", '{"session_id": "%s", "cwd": %s, "hook_event_name": "PreToolUse", '
                                         '"tool_name": "mcp__x__y", "tool_input": {"meta": %s}}' % (s, cwd, hondo)),
                ("JSON roto", '{"session_id": "%s", "cwd": %s, "tool_name": "Bash", "tool_input": {' % (s, cwd))):
            r = _pre_crudo(p, crudo)
            salida = _salida_cruda(r)
            t.igual("E24-E17 %s: sale 0" % rotulo, 0, r.returncode)
            t.igual("E24-E17 %s, tarea sana: deny" % rotulo, "deny", W3._decision(salida))
            t.contiene("E24-E17 %s: FLOW_GATE_UNRESOLVED" % rotulo, "FLOW_GATE_UNRESOLVED",
                       W3._motivo(salida))
        t.igual("E24-E17 un evento que se lee sigue decidiendose normal", None,
                W3._decision(W3._pre(p, s, "mcp__x__y", {"meta": [[1]]})))
        # Corrido desde otra carpeta: alcanza el `cwd` que se lee en el texto.
        afuera = _tmp()
        try:
            r = _pre_crudo(afuera, '{"session_id": "%s", "cwd": %s, "tool_name": "mcp__x__y", '
                           '"tool_input": {"meta": %s}}' % (s, cwd, hondo))
            t.igual("E24-E17 desde otra carpeta, el cwd del texto: deny", "deny",
                    W3._decision(_salida_cruda(r)))
        finally:
            _borrar(afuera)
    finally:
        W3._borrar(p)
    libre = _tmp()
    try:
        r = _pre_crudo(libre, '{"cwd": %s, "tool_name": "mcp__x__y", "tool_input": {"meta": %s}}'
                       % (json.dumps(str(libre)), hondo))
        t.igual("E24-E17 sin estado del flujo: sale 0", 0, r.returncode)
        t.verdadero("E24-E17 sin estado del flujo: no bloquea",
                    W3._decision(_salida_cruda(r)) is None)
    finally:
        _borrar(libre)


def test_e24l_una_mcp_con_el_comando_en_partes(t):
    """E24-E18 — una MCP de shell que recibe el comando como arreglo (`["git", "config", ...]`) o
    repartido en campos (`command` + `args`) no escribe la autoridad: cada lista y cada objeto se
    mira tambien como la secuencia de sus palabras. Y un salto de linea al borde no convierte un
    comando en contenido. E24-E19 — un texto de una linea con una comilla sin cerrar (un apostrofo
    en un comentario) no es «ante la duda, si» en una herramienta que no es shell: se parte por
    los espacios, y si no nombra la autoridad, pasa."""
    p = W2._proyecto()
    try:
        W2._listo(p, A)
        s = "w6-mcp-argv"
        W3._vincular(p, s, A)
        for rotulo, tool, entrada in (
                ("E24-E18 argv", "mcp__shell-server__shell_execute",
                 {"command": ["git", "config", "core.fsmonitor", "evil"], "directory": str(p)}),
                ("E24-E18 argv --global", "mcp__shell-server__shell_execute",
                 {"command": ["git", "config", "--global", "core.fsmonitor", "evil"]}),
                ("E24-E18 command + args", "mcp__x__run",
                 {"command": "git", "args": ["config", "core.hooksPath", "h"]}),
                ("E24-E18 argv a un .gitconfig", "mcp__x__run",
                 {"command": ["cp", "x", "C:/Users/x/.gitconfig"]}),
                ("E24-E18 \\n al final", "mcp__shell__run", {"command": "git config core.fsmonitor evil\n"}),
                ("E24-E18 \\r\\n al final", "mcp__shell__run", {"command": "git config core.fsmonitor evil\r\n"})):
            salida = W3._pre(p, s, tool, entrada)
            t.igual("%s: deny" % rotulo, "deny", W3._decision(salida))
            t.contiene("%s: protegido" % rotulo, "FLOW_AUTHORITY_PROTECTED", W3._motivo(salida) or "")
        for rotulo, tool, entrada in (
                ("E24-E19 un apostrofo en un comentario", "mcp__jira__add_comment",
                 {"issueKey": A, "body": "Don't merge yet"}),
                ("E24-E19 un apostrofo en un mensaje", "mcp__slack__post_message", {"text": "it's done"}),
                ("E24-E19 una comilla suelta", "mcp__x__y", {"q": 'a "b'}),
                ("E24-E18 argv que no escribe la autoridad", "mcp__shell-server__shell_execute",
                 {"command": ["git", "config", "--get", "user.name"]}),
                ("E24-E18 argv npm", "mcp__shell-server__shell_execute", {"command": ["npm", "test"]})):
            salida = W3._pre(p, s, tool, entrada)
            t.igual("%s: pasa con la tarea sana" % rotulo, None, W3._decision(salida))
        salida = W3._pre(p, s, "mcp__x__y", {"q": "a 'b", "path": ".claude/settings.json"})
        t.igual("E24-E19 con una comilla suelta, una ruta de la autoridad sigue negada", "deny",
                W3._decision(salida))
        salida = W3._pre(p, s, "Write", {"file_path": str(p / "src" / "O'Brien.py"), "content": "x"})
        t.igual("E24-E19 Write a una ruta con apostrofo que no es la autoridad pasa", None,
                W3._decision(salida))
        salida = W3._pre(p, s, "Write", {"file_path": str(p / "x'" / ".claude" / "y.json"), "content": "x"})
        t.igual("E24-E19 Write a .claude/ con un apostrofo en la ruta sigue negado", "deny",
                W3._decision(salida))
    finally:
        W3._borrar(p)


def test_e24m_una_mcp_en_cualquier_orden(t):
    """E24-E20 — a una herramienta que la politica no conoce no se le puede saber como arma su
    comando: el orden de sus campos ni sus comillas. Sus palabras se miran como una bolsa, sin
    orden: si estan git y `config`, es protegido, salvo una sola `config` que parseada estricta es
    una lectura de `git config`. Lo encontro la undecima pasada."""
    p = W2._proyecto()
    try:
        W2._listo(p, A)
        s = "w6-mcp-bolsa"
        W3._vincular(p, s, A)
        for rotulo, tool, entrada in (
                ("args antes que command", "mcp__x__run", {"args": ["config", "core.hooksPath", "h"], "command": "git"}),
                ("un campo en el medio", "mcp__x__run",
                 {"command": "git", "cwd": str(p), "args": ["config", "core.fsmonitor", "evil"]}),
                ("argv antes que program", "mcp__x__run", {"argv": ["config", "core.fsmonitor", "evil"], "program": "git"}),
                ("args anidados", "mcp__x__run", {"command": "git", "args": [["config", "core.fsmonitor", "evil"]]}),
                ("bash -c con un apostrofo escapado", "mcp__shell__run",
                 {"command": "bash -c \"git config core.fsmonitor evil\"; echo don\\'t"}),
                ("Start-Process con un apostrofo escapado", "mcp__shell__run",
                 {"command": "Start-Process git 'config --global core.fsmonitor evil'; Write-Host don`'t"}),
                ("un alias con un apostrofo escapado", "mcp__shell__run",
                 {"command": "git -c alias.x='config core.fsmonitor evil' x; echo don\\'t"}),
                ("sh -c && apostrofo", "mcp__shell__run",
                 {"command": "sh -c \"git config --global core.hooksPath h\" && echo don\\'t"}),
                ("un .gitconfig con un apostrofo escapado", "mcp__shell__run",
                 {"command": "echo x >> ~/.gitconfig; echo don\\'t"})):
            salida = W3._pre(p, s, tool, entrada)
            t.igual("E24-E20 %s: deny" % rotulo, "deny", W3._decision(salida))
            t.contiene("E24-E20 %s: protegido" % rotulo, "FLOW_AUTHORITY_PROTECTED", W3._motivo(salida) or "")
        for rotulo, tool, entrada in (
                ("una lectura de git config", "mcp__shell__run", {"command": "git config --get user.name"}),
                ("el argv de una lectura", "mcp__x__run",
                 {"command": ["git", "config", "--get", "user.name"], "directory": str(p)}),
                ("un apostrofo sin git config", "mcp__jira__add_comment", {"issueKey": A, "body": "Don't merge yet"}),
                ("npm test", "mcp__shell__run", {"command": "npm test"}),
                ("git status", "mcp__x__run", {"args": ["status"], "command": "git"})):
            t.igual("E24-E20 %s: pasa con la tarea sana" % rotulo, None, W3._decision(W3._pre(p, s, tool, entrada)))
    finally:
        W3._borrar(p)


def test_e24n_git_config_a_la_vista(t):
    """E24-E21 — la duodecima pasada encontro dos formas de PowerShell que llegaban a un `git config`
    que escribe sin quedar protegido: un scriptblock sin espacio despues de `{` y Start-Process con
    un arreglo `@(...)` o con `-FilePath:`. Decision de la persona del 04-10-2026: no se sigue
    parseando forma por forma. Si el texto deja ver git y `config` y el parser no prueba que es una
    lectura, es protegido (INTENTIONAL_CONSERVATIVE_OVERPROTECTION). La palabra sola no alcanza, y
    lo desconocido sin git config sigue pasando con la tarea sana (E-53 de la Wave 4)."""
    p = W2._proyecto()
    try:
        W2._listo(p, A)
        s = "w6-git-config-a-la-vista"
        W3._vincular(p, s, A)
        protegidos = [
            ("A", "PowerShell", {"command": "& {git config --global core.fsmonitor sintetico-w6}"}),
            ("A", "PowerShell", {"command": "Invoke-Command -ScriptBlock {git config core.hooksPath h}"}),
            ("A", "PowerShell", {"command": "& {git config --local core.fsmonitor sintetico-w6;}"}),
            ("B", "PowerShell", {"command": "Start-Process git -ArgumentList @('config','--global','core.fsmonitor','sintetico-w6')"}),
            ("B", "PowerShell", {"command": "Start-Process -FilePath git -ArgumentList @('config', 'core.hooksPath', 'h') -Wait"}),
            ("C", "PowerShell", {"command": "Start-Process -FilePath:git -ArgumentList 'config --global core.fsmonitor sintetico-w6'"}),
            ("C", "PowerShell", {"command": "Start-Process -FilePath:'C:/Program Files/Git/cmd/git.exe' -ArgumentList:@('config','core.fsmonitor','x')"}),
            ("D", "Bash", {"command": "g\\it config --global core.fsmonitor sintetico-w6"}),
            ("D", "PowerShell", {"command": "g`it config --global core.fsmonitor sintetico-w6"}),
            ("D", "Bash", {"command": "cmd /c g^it config core.hooksPath h"}),
            ("D", "PowerShell", {"command": "& ('gi'+'t') config --global core.fsmonitor sintetico-w6"}),
            # Lo que el shell une al leer la palabra: una continuacion de linea (`\`, `` ` `` o `^`
            # mas un salto) o algo que vale vacio (`$''`, `$()`). Decimotercera pasada.
            ("D", "Bash", {"command": "g\\\ni\\\nt config core.pager sintetico-w6"}),
            ("D", "Bash", {"command": "git conf\\\nig core.pager sintetico-w6"}),
            ("D", "PowerShell", {"command": "g`\nit config core.pager sintetico-w6"}),
            ("D", "PowerShell", {"command": "g`\r\nit config core.pager sintetico-w6"}),
            ("D", "Bash", {"command": "cmd /c g^\nit config core.pager sintetico-w6"}),
            ("D", "Bash", {"command": "g$'i't config core.pager sintetico-w6"}),
            ("D", "PowerShell", {"command": "& \"g$()it\" config core.pager sintetico-w6"}),
            ("D", "PowerShell", {"command": "Start-Process -FilePath:g`\nit -ArgumentList 'config core.pager x'"}),
            ("I", "mcp__shell__run", {"command": "& {git config --global core.fsmonitor evil}"}),
            ("I", "mcp__shell__run", {"command": "Start-Process -FilePath:git -ArgumentList @('config','core.fsmonitor','evil')"}),
            ("I", "mcp__x__run", {"program": "-FilePath:git", "args": "@('config','core.hooksPath','h')"}),
            ("J", "PowerShell", {"command": "git config $valor"}),
            ("J", "PowerShell", {"command": "git config @argumentos"}),
            ("J", "PowerShell", {"command": "$a = @('core.fsmonitor','x'); git config @a"}),
            ("J", "Bash", {"command": "git config $NOMBRE"})]
        for letra, tool, entrada in protegidos:
            salida = W3._pre(p, s, tool, entrada)
            rotulo = "E24-E21 %s %s «%s»" % (letra, tool, list(entrada.values())[0])
            t.igual("%s: deny" % rotulo, "deny", W3._decision(salida))
            t.contiene("%s: protegido" % rotulo, "FLOW_AUTHORITY_PROTECTED", W3._motivo(salida) or "")
        policy = importlib.import_module("lib.tool_policy")
        lecturas = [("E", "Bash", "git config --get user.email"),
                    ("E", "PowerShell", "git config --get-regexp user"),
                    ("E", "PowerShell", "git config --list"),
                    ("E", "Bash", "git config -l"),
                    ("F", "Bash", "git config --global --get user.name"),
                    ("F", "PowerShell", "git config --local --list"),
                    ("F", "Bash", "git config --system -l"),
                    ("F", "PowerShell", "git config --file x.cfg --get a.b")]
        for letra, tool, comando in lecturas:
            t.igual("E24-E21 %s %s «%s»: lectura" % (letra, tool, comando), "READ_ONLY",
                    policy.clasificar(tool, {"command": comando})["class"])
            t.igual("E24-E21 %s %s «%s»: pasa" % (letra, tool, comando), None,
                    W3._decision(W3._pre(p, s, tool, {"command": comando})))
        # Una lectura que el parser prueba aunque el comando entero no se reconozca (`-c`): no es
        # protegida, y la clase desconocida sigue siendo la de siempre.
        clase = policy.clasificar("Bash", {"command": "git -c color.ui=never config --get user.name"})
        t.igual("E24-E21 F git -c ... config --get: desconocida", "UNRESOLVED_TOOL_CLASS", clase["class"])
        t.verdadero("E24-E21 F git -c ... config --get: no es protegido", not clase["protected"])
        controles = [("G", "PowerShell", {"command": "& {git status}"}),
                     ("G", "PowerShell", {"command": "Start-Process git -ArgumentList @('status')"}),
                     ("G", "Bash", {"command": "nohup git log -1"}),
                     ("G", "Bash", {"command": "git commit -m arreglo"}),
                     ("G", "mcp__shell__run", {"command": "& {git status}"}),
                     ("H", "Bash", {"command": "npm config set registry https://registry.npmjs.org"}),
                     ("H", "PowerShell", {"command": "Start-Process npm -ArgumentList @('config','list')"}),
                     ("H", "PowerShell", {"command": "& {npm config get prefix}"}),
                     ("H", "mcp__shell__run", {"command": "npm config get prefix"}),
                     ("H", "mcp__jira__add_comment", {"issueKey": A, "body": "revisar la config del servidor"})]
        for letra, tool, entrada in controles:
            salida = W3._pre(p, s, tool, entrada)
            rotulo = "E24-E21 %s %s «%s»" % (letra, tool, list(entrada.values())[-1])
            t.igual("%s: pasa con la tarea sana" % rotulo, None, W3._decision(salida))
            t.verdadero("%s: no es protegido" % rotulo,
                        "FLOW_AUTHORITY_PROTECTED" not in (W3._motivo(salida) or ""))
        t.igual("E24-E21 lo desconocido sigue UNRESOLVED_TOOL_CLASS", policy.UNRESOLVED,
                policy.clasificar("PowerShell", {"command": "& {npm config get prefix}"})["class"])
    finally:
        W3._borrar(p)
    p = W3._dos()
    try:
        s = W3._sesion("w6-git-config-a-la-vista-bloqueada")
        W3._vincular(p, s, A)
        t.igual("E24-E21 lo desconocido con la tarea bloqueada: deny", "deny",
                W3._decision(W3._pre(p, s, "PowerShell", {"command": "& {npm config get prefix}"})))
    finally:
        W3._borrar(p)


# -- E-36 a E-46: la evidencia de la Context Bar sobrevive al reinicio (Manual B) ---------------
#
# Lo que fallo en la aceptacion real: una sesion dibujo con datos, se reinicio Claude Code, la
# sesion nueva dibujo sin datos y -Doctor dijo CONFIGURADA. La sesion nueva no tiene por que ser
# ACTIVE en su SessionStart (E-05 de la Context Bar), pero su primer dibujo vacio no puede borrar
# la prueba de que otra sesion, con ESTA configuracion, ya dibujo datos.
#
# Corre el renderizador de verdad: el arbol que arma medir_barra (lo que copia install.ps1), el
# comando con su huella como ultimo argumento y el registro del instalador.

S1, S2, S3 = "s-w6-mb-uno", "s-w6-mb-dos", "s-w6-mb-tres"
SIN_DATOS = "HARNESS | sin datos del Bloque 4"


def _registrar_comando(proy, renderizador, extra=""):
    """Escribe el statusLine como lo escribe install.ps1 -con la huella al final- y devuelve el
    comando con el que corre."""
    sin_huella = "python '%s'%s" % (Path(renderizador).as_posix(), extra)
    huella = M53.B.huella_statusline({"type": "command", "command": sin_huella})
    M53._json(proy / ".claude" / "settings.json",
              {"permissions": M53._DENY_ENV,
               "statusLine": {"type": "command", "command": "%s '%s'" % (sin_huella, huella)}})
    return [sys.executable, str(renderizador)] + ([extra.strip(" '")] if extra else []) + [huella]


def _barra_real():
    """(base, proyecto, comando). El comando es la lista con la que corre el renderizador, con la
    huella del bloque registrado como ultimo argumento."""
    base = _tmp()
    proy = base / "proyecto"
    renderizador = M53.MEDIDOR.armar(str(proy))
    M53._json(proy / ".claude" / "harness.lock.json",
              {"version": "0.26.0", "harness": ["comun", "desarrollo"],
               "instalado": "2026-10-01 10:00:00", "archivos": []})
    comando = _registrar_comando(proy, renderizador)
    M53.B.registrar_instalacion(str(proy), barra_probada=True, momento="2026-10-01T10:00:00")
    return base, proy, comando


def _dibuja(proy, comando, sesion, con_datos):
    entrada = {"session_id": sesion}
    if con_datos:
        entrada["transcript_path"] = M53._transcripcion(proy.parent / ("t-%s.jsonl" % sesion), sesion)
    _, salida, _ = M53._dibujar(entrada, comando=comando)
    return salida.strip()


def _evidencia(proy):
    return (M53._senal_de(proy) or {}).get("lastSessionWithData") or {}


def _version_del_renderizador(ruta):
    """La INTEGRATION_VERSION que declara el renderizador instalado en `ruta`."""
    m = re.search(r'^INTEGRATION_VERSION = "([^"]+)"', Path(ruta).read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


def _doctor(proy, lib=None):
    """Lo que corre -Doctor con Python: bienvenida.py barra <proyecto>, del arbol instalado. (codigo,
    contextBar o None, stderr)."""
    lib = lib or proy / ".claude" / "harness" / "hooks" / "lib" / "bienvenida.py"
    r = subprocess.run([sys.executable, str(lib), "barra", str(proy)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    try:
        barra = json.loads(r.stdout.decode("utf-8"))
    except ValueError:
        barra = None
    return r.returncode, barra if isinstance(barra, dict) else None, r.stderr.decode("utf-8", "replace")


def _numeros(nodo):
    if isinstance(nodo, dict):
        return [n for v in nodo.values() for n in _numeros(v)]
    return [nodo] if isinstance(nodo, (int, float)) and not isinstance(nodo, bool) else []


def _s1_con_datos_y_s2_vacia():
    """La secuencia de la aceptacion: S1 dibuja con datos, reinicio, SessionStart de S2 y su
    primer dibujo sin datos."""
    base, proy, comando = _barra_real()
    _dibuja(proy, comando, S1, True)
    M53._sesion(proy, sesion=S2)
    _dibuja(proy, comando, S2, False)
    return base, proy, comando


def test_e36_un_dibujo_con_datos_deja_evidencia(t):
    """E-36 — S1 dibuja con datos: la senal guarda la evidencia de S1, con la huella del comando
    que corrio y la version del renderizador. Sin ningun numero contable. Un dibujo vacio no la
    inventa."""
    base, proy, comando = _barra_real()
    try:
        linea = _dibuja(proy, comando, S1, True)
        t.verdadero("E-36 S1 dibujo con datos", linea.startswith("HARNESS | ") and linea != SIN_DATOS)
        ev = _evidencia(proy)
        t.igual("E-36 la evidencia es de S1", S1, ev.get("sessionId"))
        t.igual("E-36 con la huella del comando que corrio", comando[-1],
                ev.get("configurationFingerprint"))
        # La version sale del renderizador instalado, no de un literal: la integracion con 0.28.0
        # la paso de 1.0.0 a 1.2.0 (docs/cambios/flow-governance/integracion-0.28.md).
        t.igual("E-36 con la version del renderizador", _version_del_renderizador(comando[1]),
                ev.get("integrationVersion"))
        t.verdadero("E-36 con el momento del dibujo",
                    bool(re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", ev.get("renderedAt") or "")))
        senal = M53._senal_de(proy)
        t.verdadero("E-36 la senal cumple el contrato", M53.B.cumple(senal, M53.B.CONTRATO_SENAL))
        t.igual("E-36 y ningun numero", [], _numeros(senal))
    finally:
        _borrar(base)
    base, proy, comando = _barra_real()
    try:
        _dibuja(proy, comando, S1, False)
        t.igual("E-36 un dibujo sin datos no inventa evidencia", {}, _evidencia(proy))
    finally:
        _borrar(base)


def test_e37_sessionstart_de_la_sesion_nueva_sigue_configured(t):
    """E-37 — SessionStart de S2 despues de que S1 dibujo con datos: CONFIGURED y
    activeInCurrentSession false (E-05 de la Context Bar), sin copiar el true de S1. La
    evidencia de S1 queda en la senal y el estado guardado la nombra."""
    base, proy, comando = _barra_real()
    try:
        _dibuja(proy, comando, S1, True)
        M53._sesion(proy, sesion=S1)
        barra = M53._barra(M53._estado(proy))
        t.igual("E-37 SessionStart de S1 con su senal: ACTIVE en esta sesion", ("ACTIVE", True),
                (barra["state"], barra["activeInCurrentSession"]))
        M53._sesion(proy, sesion=S2)
        barra = M53._barra(M53._estado(proy))
        t.igual("E-37 SessionStart de S2: CONFIGURED", "CONFIGURED", barra["state"])
        t.igual("E-37 activeInCurrentSession false, no copiado de S1", False,
                barra["activeInCurrentSession"])
        t.igual("E-37 la evidencia de S1 sigue en la senal", S1, _evidencia(proy).get("sessionId"))
        t.igual("E-37 y el estado guardado la nombra", S1, barra.get("lastSessionWithData"))
        t.vacio("E-37 el estado guardado valida contra el schema", M53._validar(M53._estado(proy)))
    finally:
        _borrar(base)


def test_e38_un_dibujo_vacio_no_borra_la_evidencia(t):
    """E-38 — el primer dibujo sin datos de S2 no borra, no reemplaza y no degrada la evidencia
    de S1."""
    base, proy, comando = _s1_con_datos_y_s2_vacia()
    try:
        antes = _evidencia(proy)
        t.igual("E-38 la senal es de S2", S2, (M53._senal_de(proy) or {}).get("sessionId"))
        t.igual("E-38 la evidencia sigue siendo de S1", S1, antes.get("sessionId"))
        _dibuja(proy, comando, S2, False)
        t.igual("E-38 otro dibujo vacio no la toca", antes, _evidencia(proy))
    finally:
        _borrar(base)


def test_e39_doctor_reconoce_la_evidencia_compatible(t):
    """E-39 — despues del reinicio y el dibujo vacio de S2, -Doctor con Python (bienvenida.py
    barra) y `harness` calculan en vivo: ACTIVE por la evidencia de S1, sin decir que S2 esta
    activa. El estado guardado por SessionStart sigue CONFIGURED."""
    base, proy, comando = _s1_con_datos_y_s2_vacia()
    try:
        codigo, barra, error = _doctor(proy)
        t.igual("E-39 bienvenida.py barra sale 0", 0, codigo)
        t.vacio("E-39 sin traceback", error.strip())
        barra = barra or {}
        t.igual("E-39 -Doctor: ACTIVE", "ACTIVE", barra.get("state"))
        t.igual("E-39 por la evidencia de S1", S1, barra.get("lastSessionWithData"))
        t.igual("E-39 y no es actividad de esta sesion", False, barra.get("activeInCurrentSession"))
        t.igual("E-39 la ultima sesion vista es S2", S2, barra.get("lastSessionId"))
        doc = M53.B.resolver(str(proy))
        cli = M53._barra(doc)
        t.igual("E-39 `harness` dice lo mismo", ("ACTIVE", S1, False),
                (cli["state"], cli.get("lastSessionWithData"), cli["activeInCurrentSession"]))
        t.contiene("E-39 y nombra la sesion con datos",
                   "Context Bar ACTIVA (última sesión: %s)" % S1[:8], M53.B.renderizar_linea(doc))
        t.igual("E-39 el Bloque 4 tambien, por la misma sesion", "ACTIVE",
                doc["runtimeComponents"]["block4Accounting"]["state"])
        guardado = M53._barra(M53._estado(proy))
        t.igual("E-39 lo que dejo SessionStart de S2 no cambia", ("CONFIGURED", False),
                (guardado["state"], guardado["activeInCurrentSession"]))
        sesion = M53._barra(M53.B.resolver(str(proy), sesion=S2))
        t.igual("E-39 en la sesion S2 sigue CONFIGURED", ("CONFIGURED", False),
                (sesion["state"], sesion["activeInCurrentSession"]))
    finally:
        _borrar(base)


def test_e40_otra_configuracion_invalida_la_evidencia(t):
    """E-40 — la evidencia esta atada a la configuracion: con otro statusLine, o registrada otra
    vez despues del dibujo, la evidencia de S1 no prueba nada y -Doctor no dice ACTIVE."""
    base, proy, comando = _s1_con_datos_y_s2_vacia()
    try:
        renderizador = comando[1]
        _registrar_comando(proy, renderizador, extra=" '--otro'")
        _, barra, _ = _doctor(proy)
        t.verdadero("E-40 statusLine cambiado a mano: no es ACTIVE",
                    (barra or {}).get("state") not in (None, "ACTIVE"))
        t.igual("E-40 y no nombra evidencia", None, (barra or {}).get("lastSessionWithData"))
        nuevo = _registrar_comando(proy, renderizador, extra=" '--otro'")
        M53.B.registrar_instalacion(str(proy), barra_probada=True, momento="2026-10-01T11:00:00")
        _dibuja(proy, nuevo, S3, False)
        t.igual("E-40 la evidencia vieja sigue escrita, con la huella vieja", comando[-1],
                _evidencia(proy).get("configurationFingerprint"))
        _, barra, _ = _doctor(proy)
        t.igual("E-40 -Update con otra huella y S3 vacia: CONFIGURED, no ACTIVE", "CONFIGURED",
                (barra or {}).get("state"))
        t.igual("E-40 ni la nombra", None, (barra or {}).get("lastSessionWithData"))
    finally:
        _borrar(base)
    base, proy, comando = _s1_con_datos_y_s2_vacia()
    try:
        # Un -Update que cambio otra huella (session-start.py) despues del dibujo de S1.
        inicio = proy / ".claude" / "harness" / "hooks" / "session-start.py"
        inicio.write_text(inicio.read_text(encoding="utf-8") + "\n# otro\n", encoding="utf-8")
        M53.B.registrar_instalacion(str(proy), barra_probada=True, momento="2099-01-01T00:00:00")
        _, barra, _ = _doctor(proy)
        t.igual("E-40 registrada despues del dibujo: RELOAD_REQUIRED, no ACTIVE", "RELOAD_REQUIRED",
                (barra or {}).get("state"))
    finally:
        _borrar(base)


def test_e41_otra_version_de_la_integracion_invalida_la_evidencia(t):
    """E-41 — con otra version del renderizador, la evidencia de S1 (la version instalada) no
    prueba nada.

    La version se lee del renderizador instalado y la nueva se deriva de ella: el literal 1.0.0
    dejo de ser la version con la integracion de 0.28.0, que la pasa a 1.2.0, y el reemplazo no
    cambiaba nada (docs/cambios/flow-governance/integracion-0.28.md)."""
    base, proy, comando = _s1_con_datos_y_s2_vacia()
    try:
        renderizador = Path(comando[1])
        vieja = _version_del_renderizador(renderizador)
        nueva = vieja + ".1"
        texto = renderizador.read_text(encoding="utf-8")
        cambiado = texto.replace('INTEGRATION_VERSION = "%s"' % vieja,
                                 'INTEGRATION_VERSION = "%s"' % nueva)
        t.verdadero("E-41 el renderizador instalado cambio de version", cambiado != texto)
        renderizador.write_text(cambiado, encoding="utf-8")
        M53.B.registrar_instalacion(str(proy), barra_probada=True, momento="2026-10-01T11:00:00")
        _, barra, _ = _doctor(proy)
        t.verdadero("E-41 version nueva sin dibujar: no es ACTIVE",
                    (barra or {}).get("state") not in (None, "ACTIVE"))
        _dibuja(proy, comando, S3, False)
        t.igual("E-41 la evidencia vieja sigue con la version vieja", vieja,
                _evidencia(proy).get("integrationVersion"))
        _, barra, _ = _doctor(proy)
        t.igual("E-41 S3 vacia con la version nueva: CONFIGURED, no ACTIVE", "CONFIGURED",
                (barra or {}).get("state"))
        t.igual("E-41 ni la nombra", None, (barra or {}).get("lastSessionWithData"))
    finally:
        _borrar(base)


def test_e42_un_dibujo_con_datos_de_otra_sesion_avanza_la_evidencia(t):
    """E-42 — S2 termina dibujando con datos: la evidencia pasa de S1 a S2."""
    base, proy, comando = _s1_con_datos_y_s2_vacia()
    try:
        _dibuja(proy, comando, S2, True)
        t.igual("E-42 la evidencia es de S2", S2, _evidencia(proy).get("sessionId"))
        _, barra, _ = _doctor(proy)
        t.igual("E-42 -Doctor: ACTIVE por S2", ("ACTIVE", S2),
                ((barra or {}).get("state"), (barra or {}).get("lastSessionWithData")))
        M53._sesion(proy, sesion=S2)
        guardado = M53._barra(M53._estado(proy))
        t.igual("E-42 y SessionStart de S2 ya la ve activa en esta sesion", ("ACTIVE", True),
                (guardado["state"], guardado["activeInCurrentSession"]))
    finally:
        _borrar(base)


def test_e43_sin_ninguna_sesion_con_datos_no_hay_active(t):
    """E-43 — instalacion nueva, o sesiones que solo dibujaron vacio: -Doctor no dice ACTIVE."""
    base, proy, comando = _barra_real()
    try:
        _, barra, _ = _doctor(proy)
        t.igual("E-43 recien instalada: RELOAD_REQUIRED", "RELOAD_REQUIRED", (barra or {}).get("state"))
        _dibuja(proy, comando, S1, False)
        M53._sesion(proy, sesion=S2)
        _dibuja(proy, comando, S2, False)
        codigo, barra, _ = _doctor(proy)
        t.igual("E-43 solo dibujos vacios: CONFIGURED", (0, "CONFIGURED"),
                (codigo, (barra or {}).get("state")))
        t.igual("E-43 sin sesion con datos", None, (barra or {}).get("lastSessionWithData"))
    finally:
        _borrar(base)


def test_e44_bienvenida_barra_sin_harness_no_levanta(t):
    """E-44 — bienvenida.py barra sobre un proyecto sin harness ni senal: un JSON sin ACTIVE y sin
    traceback. -Doctor nunca recibe un ACTIVE inventado."""
    vacio = _tmp()
    try:
        codigo, barra, error = _doctor(vacio, lib=RAIZ / "comun" / "hooks" / "lib" / "bienvenida.py")
        t.igual("E-44 sale 0", 0, codigo)
        t.vacio("E-44 sin traceback", error.strip())
        t.verdadero("E-44 un JSON de la barra", isinstance(barra, dict) and "state" in barra)
        t.verdadero("E-44 que no es ACTIVE", (barra or {}).get("state") != "ACTIVE")
    finally:
        _borrar(vacio)


def test_e44_la_forma_que_acepta_doctor_es_la_de_bienvenida(t):
    """E-44 — -Doctor mira la salida de `bienvenida.py barra` con Test-FormaDeLaBarra antes de
    leerla (pasada 15 del refutador). Esa forma no es un schema propio de PowerShell: son los
    campos requeridos de _FORMA_BARRA, la evidencia que -Doctor nombra y ESTADOS_DE_COMPONENTE.
    Esto los compara, para que no se separen."""
    texto = (RAIZ / "install.ps1").read_text(encoding="utf-8-sig")
    funcion = re.search(r"function Test-FormaDeLaBarra \{(.*?)\n\}", texto, re.S)
    t.verdadero("E-44 install.ps1 define Test-FormaDeLaBarra", funcion is not None)
    cuerpo = funcion.group(1) if funcion else ""

    def lista(nombre):
        valores = re.search(r"\$%s = @\(([^)]*)\)" % nombre, cuerpo)
        return sorted(re.findall(r"'([^']+)'", valores.group(1))) if valores else []

    t.igual("E-44 los estados que acepta son los de bienvenida.py",
            sorted(M53.B.ESTADOS_DE_COMPONENTE), lista("estados"))
    t.igual("E-44 los campos que exige son los requeridos de la barra y la evidencia",
            sorted(M53.B._FORMA_BARRA["required"] + ["lastSessionWithData"]), lista("requeridos"))


def test_e46_la_secuencia_b1_b4(t):
    """E-46 — la secuencia de la aceptacion, con el renderizador de verdad: B1 despues de un
    -Update, RELOAD_REQUIRED; B2/B3 sesion nueva sin datos, CONFIGURED; B4 una sesion dibujo con
    datos, reinicio, la nueva dibuja vacio: -Doctor ACTIVE, la sesion nueva no."""
    base, proy, comando = _barra_real()
    try:
        _, barra, _ = _doctor(proy)
        t.igual("E-46 B1 despues del -Update: RELOAD_REQUIRED", "RELOAD_REQUIRED",
                (barra or {}).get("state"))
        M53._sesion(proy, sesion=S1)
        _dibuja(proy, comando, S1, False)
        M53._sesion(proy, sesion=S1)
        guardado = M53._barra(M53._estado(proy))
        t.igual("E-46 B2/B3 sesion nueva sin datos: CONFIGURED", ("CONFIGURED", False),
                (guardado["state"], guardado["activeInCurrentSession"]))
        _, barra, _ = _doctor(proy)
        t.igual("E-46 B3 -Doctor: CONFIGURED", "CONFIGURED", (barra or {}).get("state"))
        _dibuja(proy, comando, S1, True)
        M53._sesion(proy, sesion=S2)
        _dibuja(proy, comando, S2, False)
        _, barra, _ = _doctor(proy)
        t.igual("E-46 B4 despues del reinicio: -Doctor ACTIVE", ("ACTIVE", S1, False),
                ((barra or {}).get("state"), (barra or {}).get("lastSessionWithData"),
                 (barra or {}).get("activeInCurrentSession")))
        guardado = M53._barra(M53._estado(proy))
        t.igual("E-46 B4 la sesion nueva no es ACTIVE en su SessionStart", ("CONFIGURED", False),
                (guardado["state"], guardado["activeInCurrentSession"]))
    finally:
        _borrar(base)
