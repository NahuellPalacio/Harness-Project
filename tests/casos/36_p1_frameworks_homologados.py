# P1: frameworks homologados, nada de lenguaje puro, y NPM en Node.
#
# Escenarios E-01 a E-42 de docs/cambios/p1-frameworks-homologados/spec.md. Entre parentesis, el
# P1-nn del pedido de instalacion.
#
# 🔴 Nada de esto levanta una aplicacion ni instala una dependencia. Lo que se verifica son los
# CONTROLES: que P1 sea ALWAYS y sus checks nunca contesten NOT_APPLICABLE, que las dos clausulas
# derivadas hereden sin filas nuevas, que la homologacion y las versiones sigan siendo de G1, y que
# el framework tenga que GOBERNAR y no solo estar.
import ast
import importlib.util
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CONTROLES = RAIZ / "harnesses" / "desarrollo" / "controles"
SKILLS = RAIZ / "harnesses" / "desarrollo" / "skills"
RUTA_REG = str(BIN / "orquestacion" / "registro_agentes.py")

sys.path.insert(0, str(BIN))
from orquestacion import anexo2                     # noqa: E402
from orquestacion import controles as c_controles   # noqa: E402
from orquestacion import matriz as c_matriz         # noqa: E402
from orquestacion import normativa as c_normativa   # noqa: E402
from orquestacion import registro_agentes as c_reg  # noqa: E402

RUTA_FW = CONTROLES / "checks" / "framework-homologation.py"
RUTA_NP = CONTROLES / "checks" / "node-package-manager-compliance.py"


def _cargar(ruta, alias):
    spec = importlib.util.spec_from_file_location(alias, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


FW = _cargar(RUTA_FW, "p1_framework")
NP = _cargar(RUTA_NP, "p1_node")
MODULOS = (("framework-homologation", FW), ("node-package-manager-compliance", NP))

POLICIES = ("homologated-framework-required", "vanilla-development-prohibited",
            "node-package-manager-npm-only")
CHEQUEOS = ("framework-homologation", "node-package-manager-compliance")
AGENTES = ["dev-architecture", "dev-devops"]
CLAUSULAS = ("P1", "P1.node", "P1.plataformas")

TRAZA = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "P1"}

BUILD = {"id": "b-instalacion-de-p1", "runtime": "runtime-de-prueba"}
# Una tecnologia que el Anexo II declara. Sale del catalogo, no de una lista de este test.
TECNOLOGIA = "Angular"
LINEAMIENTOS = {"id": "lineamiento-de-desarrollo-de-la-plataforma",
                "source": "PLATFORM_VENDOR_GUIDELINE",
                "reference": "manual de desarrollo de la plataforma, seccion 4"}


# -- las piezas de los casos ---------------------------------------------------

def _literales(ruta, con_docstrings=False):
    """Las cadenas literales de un modulo, sin los docstrings.

    🔴 Un docstring puede explicar de que NO habla la regla; lo que el modulo no puede es
    devolverlo. Barrer el texto entero confunde las dos cosas, que es como se apaga un guard.
    """
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    docs = set()
    for nodo in ast.walk(arbol):
        cuerpo = getattr(nodo, "body", None) or []
        if not isinstance(nodo, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            continue
        if (cuerpo and isinstance(cuerpo[0], ast.Expr)
                and isinstance(cuerpo[0].value, ast.Constant)
                and isinstance(cuerpo[0].value.value, str)):
            docs.add(id(cuerpo[0].value))
    return [n.value for n in ast.walk(arbol)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and (con_docstrings or id(n) not in docs)]


def _ev(eid, tipo=None, gobierna=True, **extra):
    e = {"evidenceId": eid, "sourceType": tipo or FW.GOBERNANZA, "reference": "revision#1",
         "claim": "lo que la revision reporta", "buildId": BUILD["id"],
         "runtime": BUILD["runtime"], "governs": gobierna}
    e.update(extra)
    return e


def _framework(tecnologia=TECNOLOGIA, g1="HOMOLOGATED", referencia="G1 corrida#1"):
    return {"technology": tecnologia, "g1State": g1, "g1Reference": referencia}


def _superficie(sid="s-backend", clase="FRAMEWORK_GOVERNED", framework=None, refs=("e-1",),
                **extra):
    s = {"id": sid, "kind": clase, "evidenceRefs": list(refs)}
    if clase == "FRAMEWORK_GOVERNED":
        s["framework"] = _framework() if framework is None else framework
    s.update(extra)
    return s


def _plataforma(sid="s-plataforma", conflicto=False, **campos):
    datos = {"id": "plataforma-de-negocio-del-organismo", "structuredEnvironment": True,
             "guidelines": dict(LINEAMIENTOS), "customizationInside": True,
             "conflictsWithStandard": conflicto}
    datos.update(campos)
    return {"id": sid, "kind": "BUSINESS_PLATFORM_GOVERNED", "platform": datos,
            "evidenceRefs": []}


def _caso(items=None, evidencia=None, fuente="DELIVERY_INVENTORY", completo=True, **extra):
    caso = {
        "application": {"id": "tramites", "environment": "test"},
        "build": dict(BUILD),
        "testTarget": {"available": True},
        "surfaces": {"source": fuente, "complete": completo,
                     "items": [_superficie()] if items is None else list(items)},
        "evidence": [_ev("e-1")] if evidencia is None else list(evidencia),
    }
    caso.update(extra)
    return caso


def _pm(pid="pm-1", manager="NPM", activo=True, fuente="LOCKFILE", **extra):
    e = {"id": pid, "manager": manager, "active": activo, "source": fuente,
         "reference": "el camino de dependencias del repositorio"}
    e.update(extra)
    return e


def _nodo(managers=None, superficies=("s-backend",), completo=True, **extra):
    caso = {
        "build": dict(BUILD),
        "testTarget": {"available": True},
        "nodeContext": {"complete": completo, "surfaces": list(superficies)},
        "packageManagers": [_pm()] if managers is None else list(managers),
    }
    caso.update(extra)
    return caso


# -- los caminos de cada check, uno por estado ---------------------------------

def _caminos_de_framework():
    return {
        "PASS": _caso(),
        "FAIL": _caso(items=[_superficie(sid="s-vieja", clase="VANILLA_APPLICATION")]),
        "PARTIAL": _caso(items=[_superficie(refs=())]),
        "FRAMEWORK_CONTEXT_UNRESOLVED": _caso(
            items=[_superficie(framework=_framework(tecnologia=""))]),
        "DEVELOPMENT_SURFACE_CLASSIFICATION_UNRESOLVED": _caso(surfaces={}),
        "BUSINESS_PLATFORM_GOVERNANCE_UNRESOLVED": _caso(
            items=[_plataforma(structuredEnvironment=None)]),
        "BUSINESS_PLATFORM_STANDARD_CONFLICT": _caso(items=[_plataforma(conflicto=True)]),
        "G1_EVIDENCE_REQUIRED": _caso(items=[_superficie(framework=_framework(g1=""))]),
        "TEST_TARGET_UNAVAILABLE": _caso(testTarget={}),
    }


def _caminos_de_node():
    return {
        "PASS": _nodo(),
        "FAIL": _nodo(managers=[_pm(manager="YARN")]),
        "PARTIAL": _nodo(managers=[_pm(), _pm(pid="pm-2", manager="YARN", activo=False)]),
        "NOT_RELEVANT": _nodo(superficies=()),
        "NODE_TECHNOLOGY_CONTEXT_UNRESOLVED": _nodo(completo=False),
        "NODE_PACKAGE_MANAGER_EVIDENCE_UNRESOLVED": _nodo(managers=[]),
        "NODE_PACKAGE_MANAGER_CONFLICT": _nodo(
            managers=[_pm(), _pm(pid="pm-2", manager="PNPM")]),
        "TEST_TARGET_UNAVAILABLE": _nodo(testTarget={}),
    }


TODOS_LOS_CAMINOS = (("framework-homologation", FW, _caminos_de_framework),
                     ("node-package-manager-compliance", NP, _caminos_de_node))


# -- E-01 a E-08 — la fila, las clausulas y la herencia ------------------------

def test_e01_p1_es_always_sin_senales(t):
    """E-01 (P1-01, P1-02) — ALWAYS, cero senales, y las claves de toda fila clasificada."""
    p1 = c_matriz.regla("P1")
    t.igual("E-01 el modo", "ALWAYS", p1["applicability"]["mode"])
    t.igual("E-01 cero senales", [], p1["applicability"]["signals"])
    t.igual("E-01 la categoria", "PROGRAMMING", p1["category"])
    t.igual("E-01 sigue CLASSIFIED", "CLASSIFIED", p1["status"])
    t.igual("E-01 la intencion operativa no cambio",
            "Use homologated frameworks; pure-language development is not allowed; Node.js "
            "projects must use NPM.", p1["operationalIntentEn"])

    # 🔴 Y no se agrego ninguna senal a la matriz por la puerta de atras.
    from orquestacion import senales as c_senales
    for inventada in ("nodePresent", "businessPlatformPresent", "frameworkPresent"):
        t.vacio("E-01 %s no es una senal declarada" % inventada,
                c_senales.reglas_de(inventada))
        t.verdadero("E-01 %s no esta en el inventario" % inventada,
                    inventada not in c_senales.declaradas())

    otras = [r for r in c_matriz.reglas() if r.get("id") != "P1"]
    comunes, todas = set(otras[0].keys()), set(otras[0].keys())
    for otra in otras:
        comunes &= set(otra.keys())
        todas |= set(otra.keys())
    t.igual("E-01 tiene las claves que tiene toda fila", sorted(comunes), sorted(p1.keys()))
    t.vacio("E-01 y ninguna que no exista en el resto", sorted(set(p1.keys()) - todas))
    t.verdadero("E-01 `reviews` es opcional y alguna otra fila lo trae",
                "reviews" in todas and "reviews" not in comunes)


def test_e02_los_dos_agentes_duenos(t):
    """E-02 (P1-03) — dev-architecture y dev-devops, los que la matriz ya declaraba."""
    t.igual("E-02 los dos duenos", AGENTES, c_matriz.regla("P1")["primaryAgents"])
    registro = c_reg.cargar(RUTA_REG)
    agentes = {a["id"] for a in registro["agents"]}
    for a in AGENTES:
        t.verdadero("E-02 %s ya estaba en el registro" % a, a in agentes)
    for nombre, modulo in MODULOS:
        t.igual("E-02 %s nombra a los mismos duenos" % nombre, tuple(AGENTES), modulo.AGENTES)


def test_e03_las_tres_policies_y_los_dos_checks(t):
    """E-03 (P1-04, P1-05) — exactamente los que la matriz declara."""
    p1 = c_matriz.regla("P1")
    t.igual("E-03 tres policies", list(POLICIES), p1["policies"])
    t.igual("E-03 dos checks", list(CHEQUEOS), p1["checks"])
    filas = c_controles.de_la_regla("P1")
    t.igual("E-03 cinco filas en el registro", 5, len(filas))
    por_tipo = {}
    for f in filas:
        por_tipo.setdefault(f["type"], []).append(f["id"])
        t.igual("E-03 %s sale de P1" % f["id"], "P1", f["rule"])
        t.igual("E-03 %s conserva la tupla" % f["id"], TRAZA, f["source"])
    t.igual("E-03 las tres policies del registro", sorted(POLICIES),
            sorted(por_tipo.get("POLICY", [])))
    t.igual("E-03 los dos checks del registro", sorted(CHEQUEOS),
            sorted(por_tipo.get("CHECK", [])))
    for nombre, modulo in MODULOS:
        t.igual("E-03 el modulo %s se llama igual que su id" % nombre, nombre, modulo.CONTROL)
        t.igual("E-03 %s sale de P1" % nombre, "P1", modulo.REGLA)


def test_e04_p1_no_crea_ninguna_skill(t):
    """E-04 (P1-06) — ni la fila, ni los artefactos, ni el conteo de instaladas."""
    p1 = c_matriz.regla("P1")
    t.verdadero("E-04 la fila no declara skills", not p1.get("skills"))
    t.verdadero("E-04 ni la clave existe", "skills" not in p1)

    registro = c_reg.cargar(RUTA_REG)
    agentes = {a["id"] for a in registro["agents"]}
    declaradas = {s["id"] for a in registro["agents"] for s in a.get("skills") or []}
    for nombre, texto in _artefactos_de_p1().items():
        t.vacio("E-04 %s no declara un inventario de skills" % nombre,
                re.findall(r"(?i)\bskills\s*[:=]\s*[\"'\[]", texto))
        for mencionada in sorted(set(re.findall(r"\bdev-[a-z-]+\b", texto))):
            t.verdadero("E-04 %s nombra %s, que el registro ya declara" % (nombre, mencionada),
                        mencionada in declaradas or mencionada in agentes)
    t.igual("E-04 siguen siendo 27 las skills instaladas", 27,
            len([d for d in SKILLS.iterdir() if d.is_dir()]))


def test_e05_p1_node_hereda(t):
    """E-05 (P1-07) — misma clasificacion, y lo declara."""
    p1 = c_matriz.regla("P1")
    hija = c_matriz.regla("P1.node")
    t.igual("E-05 declara de quien hereda", "P1", hija["inheritedFrom"])
    t.igual("E-05 el id es el de la clausula", "P1.node", hija["id"])
    for campo in ("policies", "checks", "primaryAgents", "category", "status"):
        t.igual("E-05 hereda %s" % campo, p1[campo], hija[campo])
    t.igual("E-05 y la aplicabilidad", p1["applicability"], hija["applicability"])


def test_e06_p1_plataformas_hereda(t):
    """E-06 (P1-08) — igual que la otra clausula."""
    p1 = c_matriz.regla("P1")
    hija = c_matriz.regla("P1.plataformas")
    t.igual("E-06 declara de quien hereda", "P1", hija["inheritedFrom"])
    t.igual("E-06 el id es el de la clausula", "P1.plataformas", hija["id"])
    for campo in ("policies", "checks", "primaryAgents", "category", "status"):
        t.igual("E-06 hereda %s" % campo, p1[campo], hija[campo])


def test_e07_no_hay_filas_nuevas(t):
    """E-07 (P1-09) — 24 filas, ninguna con un punto, y sin controles duplicados."""
    reglas = c_matriz.reglas()
    t.igual("E-07 siguen siendo 24 filas", 24, len(reglas))
    con_punto = [r["id"] for r in reglas if "." in r["id"]]
    t.igual("E-07 ninguna fila tiene un punto en el id", [], con_punto)
    t.igual("E-07 P1 aparece una sola vez", 1, len([r for r in reglas if r["id"] == "P1"]))

    # 🔴 Y los controles de P1 no estan declarados bajo un id hijo en el registro.
    for clausula in CLAUSULAS[1:]:
        t.igual("E-07 el registro no declara controles de %s" % clausula, [],
                c_controles.de_la_regla(clausula))
    ids = [c["id"] for c in c_controles.cargar()["controls"]]
    t.igual("E-07 cada control aparece una sola vez", len(ids), len(set(ids)))


def test_e08_las_tres_clausulas_citables(t):
    """E-08 (§2) — existen, con su texto y su pagina, y las tres apuntan a P1."""
    import io
    import json
    ruta = BIN.parent / "reglas" / "es0901-7.1.json"
    doc = json.loads(io.open(ruta, encoding="utf-8-sig").read())
    por_id = {r["id"]: r for r in doc["rules"]}
    # 🔴 Un tramo distintivo de cada clausula, CLAVADO. `len(texto) > 80` se satisface con
    # cualquier prosa inventada: la mitad que importa —que el texto sea el del estandar— la
    # sostenia el test de otro cambio, no este.
    TRAMOS = {
        "P1": ("frameworks homologados",
               "lenguaje puro", "bibliotecas o componentes de bajo nivel"),
        "P1.node": ("el administrador de paquetes permitido es NPM",
                    "No esta permitido el uso de YARN"),
        "P1.plataformas": ("Para ERP, CRM, FSM",
                           "siempre que no contradigan los principios"),
    }
    for clausula in CLAUSULAS:
        cid = "ES0901-7.1-%s" % clausula
        t.verdadero("E-08 existe %s" % cid, cid in por_id)
        t.igual("E-08 %s apunta a P1" % cid, "P1", por_id[cid]["rule"])
        t.igual("E-08 %s esta en la pagina 13" % cid, 13, por_id[cid]["page"])
        for tramo in TRAMOS[clausula]:
            t.contiene("E-08 %s dice `%s`" % (cid, tramo[:32]), tramo, por_id[cid]["text"])


# -- E-09 a E-12 — la frontera con G1 ------------------------------------------

def test_e09_el_catalogo_es_el_de_g1(t):
    """E-09 (P1-10) — el mismo archivo, sin copia y sin lista adentro."""
    catalogo = anexo2.cargar()
    t.verdadero("E-09 el catalogo tiene entradas", len(anexo2.entradas(catalogo)) > 100)
    t.verdadero("E-09 y la tecnologia de prueba figura",
                anexo2.buscar(TECNOLOGIA, catalogo) is not None)
    t.igual("E-09 el catalogo es el archivo del Anexo II",
            "annex-ii-technology-catalog.json", anexo2.ARCHIVO)

    # 🔴 Y el check LO LEE, que es la mitad que este escenario enuncia y no sostenia: con un
    # catalogo vacio, la misma tecnologia deja de resolver y el resultado cambia. Sin esto, un
    # check que ignorara el catalogo dejaba a E-09 en verde.
    t.igual("E-09 con el catalogo real, la tecnologia resuelve", "PASS",
            FW.evaluar(_caso(), None, catalogo)["state"])
    vacio = {"technologies": [], "version": catalogo.get("version")}
    sin_catalogo = FW.evaluar(_caso(), None, vacio)
    t.igual("E-09 con el catalogo vacio deja de resolver", "PARTIAL", sin_catalogo["state"])
    t.igual("E-09 y lo dice", "G1_STATE_CONTRADICTED_BY_CATALOG", sin_catalogo["reason"])

    # 🔴 Ninguna lista literal de los modulos de P1 agrupa dos tecnologias del catalogo: eso
    # seria un segundo catalogo, y el catalogo es uno solo.
    nombres = {(e.get("id") or "").lower() for e in anexo2.entradas(catalogo)}
    nombres = {n for n in nombres if len(n) > 3}
    for ruta in (RUTA_FW, RUTA_NP):
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, (ast.Tuple, ast.List)):
                continue
            textos = [e.value.lower() for e in nodo.elts
                      if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            juntas = sorted({n for n in nombres for x in textos if n == x})
            t.verdadero("E-09 %s no agrupa tecnologias: %s" % (ruta.name, ", ".join(juntas)),
                        len(juntas) <= 1)


def test_e10_p1_no_duplica_la_logica_de_versiones(t):
    """E-10 (P1-11) — ni la nombra, ni la copia, ni declara una version."""
    comparacion = ("parsear", "cae_en", "version_pedida", "_RAMA", "_RANGO", "_NUM",
                   "_CON_CALIFICATIVO", "SIN_FIJAR", "_tupla", "_rama", "DEPRECADA",
                   "NO_HOMOLOGADA")
    # La premisa: los doce nombres existen de verdad en el modulo de G1, asi que ninguno es un
    # nombre que el sistema no pueda fallar.
    for nombre in comparacion:
        t.verdadero("E-10 `%s` existe en anexo2" % nombre,
                    nombre in (BIN / "orquestacion" / "anexo2.py").read_text(encoding="utf-8"))
    for ruta in (RUTA_FW, RUTA_NP):
        fuente = ruta.read_text(encoding="utf-8")
        for nombre in comparacion:
            t.verdadero("E-10 %s no nombra `%s`" % (ruta.name, nombre), nombre not in fuente)
        # Ninguna constante numerica: no hay umbrales ni versiones adentro.
        modulo = FW if ruta is RUTA_FW else NP
        numeros = sorted(n for n, v in vars(modulo).items()
                         if isinstance(v, (int, float)) and not isinstance(v, bool))
        t.igual("E-10 %s no declara constantes numericas" % ruta.name, [], numeros)
        t.vacio("E-10 %s no declara una version" % ruta.name,
                re.findall(r"(?<![.\d])\d+\.\d+\.\d+", fuente))
    # Lo unico que P1 toma de `anexo2` es el catalogo y el nombre del estado homologado.
    t.verdadero("E-10 el check consume el estado de G1", "HOMOLOGADA" in
                RUTA_FW.read_text(encoding="utf-8"))
    t.igual("E-10 y es el que G1 declara", "HOMOLOGATED", anexo2.HOMOLOGADA)


def test_e11_sin_veredicto_de_g1(t):
    """E-11 (§6) — G1_EVIDENCE_REQUIRED, porque la homologacion es de G1."""
    for nombre, framework in (("sin estado", _framework(g1="")),
                              ("sin referencia", _framework(referencia="")),
                              ("en blancos", _framework(g1="  ", referencia=" "))):
        salida = FW.evaluar(_caso(items=[_superficie(framework=framework)]))
        t.igual("E-11 %s deja el veredicto de G1 pendiente" % nombre, "G1_EVIDENCE_REQUIRED",
                salida["state"])
        t.verdadero("E-11 %s no aprueba" % nombre, not FW.aprueba(salida))


def test_e12_el_estado_de_g1_se_conserva(t):
    """E-12 (P1-15) — no homologada o pendiente de la ASI: se conserva y no pasa."""
    for estado in ("NOT_HOMOLOGATED", "ASI_EVALUATION_REQUIRED", "DEPRECATED_TOLERATED",
                   "VERSION_CONTEXT_REQUIRED"):
        salida = FW.evaluar(_caso(items=[_superficie(framework=_framework(g1=estado))]))
        t.igual("E-12 %s no pasa" % estado, "PARTIAL", salida["state"])
        t.igual("E-12 %s deja el motivo" % estado, "G1_STATE_NOT_HOMOLOGATED", salida["reason"])
        # 🔴 El campo estructurado, no el `repr`: `estado in repr(...)` se satisface con el
        # detalle, que tambien lo nombra, asi que sacar el campo dejaba el test verde.
        t.igual("E-12 %s se conserva en el campo" % estado, estado,
                salida["surfaces"][0]["g1State"])
        t.verdadero("E-12 %s no aprueba" % estado, not FW.aprueba(salida))

    # Y un veredicto que dice homologada sobre algo que el catalogo no tiene es una
    # contradiccion: los dos datos no pueden ser ciertos.
    salida = FW.evaluar(_caso(items=[_superficie(
        framework=_framework(tecnologia="una-tecnologia-que-no-figura"))]))
    t.igual("E-12 el veredicto contradicho no pasa", "PARTIAL", salida["state"])
    t.igual("E-12 con su motivo", "G1_STATE_CONTRADICTED_BY_CATALOG", salida["reason"])


# -- E-13 a E-16 — las superficies ---------------------------------------------

def test_e13_el_inventario_incompleto_no_se_resuelve(t):
    """E-13 (P1-21, P1-36) — las siete formas, y ninguna pasa."""
    formas = {
        "sin inventario": _caso(surfaces={}),
        "sin superficies": _caso(items=[]),
        "sin fuente": _caso(fuente="PROJECT_CONVENTION"),
        "con una superficie sin id": _caso(items=[_superficie(sid="  ")]),
        "con una clase desconocida": _caso(items=[_superficie(clase="OTRA_COSA")]),
        "con una superficie sin resolver": _caso(
            items=[_superficie(), _superficie(sid="s-?", clase="UNRESOLVED")]),
        "declarado incompleto": _caso(completo=False),
    }
    t.igual("E-13 son siete formas", 7, len(formas))
    for nombre, caso in sorted(formas.items()):
        salida = FW.evaluar(caso)
        t.igual("E-13 %s deja la clasificacion sin resolver" % nombre,
                "DEVELOPMENT_SURFACE_CLASSIFICATION_UNRESOLVED", salida["state"])
        t.verdadero("E-13 %s no aprueba" % nombre, not FW.aprueba(salida))


def test_e14_las_cinco_clases_de_superficie(t):
    """E-14 (§5) — nombradas una por una, no leidas de la constante que se verifica."""
    CINCO = ("FRAMEWORK_GOVERNED", "BUSINESS_PLATFORM_GOVERNED", "AUXILIARY_TOOLING",
             "VANILLA_APPLICATION", "UNRESOLVED")
    t.igual("E-14 son estas cinco clases", CINCO, FW.CLASES)
    esperado = {"FRAMEWORK_GOVERNED": "PASS", "BUSINESS_PLATFORM_GOVERNED": "PASS",
                "AUXILIARY_TOOLING": "PASS", "VANILLA_APPLICATION": "FAIL",
                "UNRESOLVED": "DEVELOPMENT_SURFACE_CLASSIFICATION_UNRESOLVED"}
    for clase in CINCO:
        if clase == "BUSINESS_PLATFORM_GOVERNED":
            caso = _caso(items=[_plataforma()])
        elif clase == "FRAMEWORK_GOVERNED":
            caso = _caso()
        else:
            caso = _caso(items=[_superficie(sid="s-" + clase, clase=clase)])
        t.igual("E-14 %s resuelve a lo suyo" % clase, esperado[clase], FW.evaluar(caso)["state"])


def test_e15_el_script_auxiliar_no_es_vanilla(t):
    """E-15 (P1-20) — declarado auxiliar, no se clasifica solo como aplicacion."""
    caso = _caso(items=[_superficie(), _superficie(sid="s-build", clase="AUXILIARY_TOOLING",
                                                   refs=())])
    salida = FW.evaluar(caso)
    t.igual("E-15 el auxiliar no hace fallar", "PASS", salida["state"])
    auxiliar = [s for s in salida["surfaces"] if s["surfaceId"] == "s-build"][0]
    t.igual("E-15 y se informa como no gobernada", False, auxiliar["governed"])
    t.igual("E-15 su estado no es FAIL", "PASS", auxiliar["state"])
    # 🔴 Y el mismo archivo declarado como aplicacion entregada si se evalua.
    entregado = _caso(items=[_superficie(sid="s-build", clase="VANILLA_APPLICATION")])
    t.igual("E-15 declarado entregado, falla", "FAIL", FW.evaluar(entregado)["state"])


def test_e16_las_superficies_se_evaluan_por_separado(t):
    """E-16 (P1-35) — el resultado nombra cada una con su estado."""
    caso = _caso(items=[_superficie(), _plataforma(),
                        _superficie(sid="s-aux", clase="AUXILIARY_TOOLING", refs=()),
                        _superficie(sid="s-vieja", clase="VANILLA_APPLICATION")])
    salida = FW.evaluar(caso)
    estados = {s["surfaceId"]: s["state"] for s in salida["surfaces"]}
    t.igual("E-16 son cuatro superficies evaluadas", 4, len(estados))
    t.igual("E-16 la del framework pasa", "PASS", estados["s-backend"])
    t.igual("E-16 la de plataforma pasa", "PASS", estados["s-plataforma"])
    t.igual("E-16 la auxiliar pasa", "PASS", estados["s-aux"])
    t.igual("E-16 la vanilla falla", "FAIL", estados["s-vieja"])
    t.igual("E-16 y el agregado falla", "FAIL", salida["state"])


# -- E-17 a E-19 — el framework, que tiene que gobernar ------------------------

def test_e17_el_framework_que_gobierna_pasa(t):
    """E-17 (P1-13) — homologado, citado y con traza de que gobierna."""
    salida = FW.evaluar(_caso())
    t.igual("E-17 el estado", "PASS", salida["state"])
    t.verdadero("E-17 aprueba", FW.aprueba(salida))
    t.igual("E-17 la superficie paso", "PASS", salida["surfaces"][0]["state"])
    t.igual("E-17 y declara la clausula", "P1", salida["surfaces"][0]["clause"])
    t.vacio("E-17 sin avisos", salida["issues"])


def test_e18_las_cinco_clases_inertes(t):
    """E-18 (P1-12) — la dependencia sola no pasa, ni ninguna de las otras cuatro."""
    INERTES = ("REPOSITORY_DEPENDENCY", "PACKAGE_MANIFEST_ENTRY", "SINGLE_MANAGED_MODULE",
               "PROJECT_DOCUMENTATION", "AGENT_STATEMENT")
    t.igual("E-18 son estas cinco clases inertes", INERTES, FW.EVIDENCIA_QUE_NO_PRUEBA)
    for tipo in INERTES:
        salida = FW.evaluar(_caso(evidencia=[_ev("e-1", tipo=tipo)]))
        t.igual("E-18 %s no da PASS" % tipo, "PARTIAL", salida["state"])
        t.igual("E-18 %s deja el motivo" % tipo, "FRAMEWORK_GOVERNANCE_UNPROVEN",
                salida["reason"])
        t.verdadero("E-18 %s no aprueba" % tipo, not FW.aprueba(salida))
    t.igual("E-18 la clase que prueba es una", 1, len(FW.EVIDENCIA_QUE_PRUEBA))
    t.igual("E-18 y es la traza de gobernanza", "FRAMEWORK_GOVERNANCE_TRACE", FW.GOBERNANZA)


def test_e19_sin_identidad_de_framework(t):
    """E-19 (P1-14) — FRAMEWORK_CONTEXT_UNRESOLVED."""
    for nombre, tecnologia in (("vacia", ""), ("en blancos", "   ")):
        salida = FW.evaluar(_caso(items=[_superficie(
            framework=_framework(tecnologia=tecnologia))]))
        t.igual("E-19 %s no resuelve el framework" % nombre, "FRAMEWORK_CONTEXT_UNRESOLVED",
                salida["state"])
        t.verdadero("E-19 %s no aprueba" % nombre, not FW.aprueba(salida))


# -- E-20 a E-24 — el lenguaje puro y el bajo nivel ----------------------------

def test_e20_el_lenguaje_puro_falla(t):
    """E-20 (P1-16) — VANILLA_RUNTIME_PATH_DETECTED."""
    salida = FW.evaluar(_caso(items=[_superficie(sid="s-vieja", clase="VANILLA_APPLICATION")]))
    t.igual("E-20 el estado", "FAIL", salida["state"])
    t.igual("E-20 el motivo", "VANILLA_RUNTIME_PATH_DETECTED", salida["reason"])
    t.verdadero("E-20 no aprueba", not FW.aprueba(salida))


def test_e21_el_framework_instalado_que_no_gobierna(t):
    """E-21 (P1-17) — la traza manda sobre lo que la superficie declare."""
    salida = FW.evaluar(_caso(evidencia=[_ev("e-1", gobierna=False)]))
    t.igual("E-21 el estado", "FAIL", salida["state"])
    t.igual("E-21 el motivo", "VANILLA_RUNTIME_PATH_DETECTED", salida["reason"])
    t.verdadero("E-21 no aprueba", not FW.aprueba(salida))
    # Y una traza que no dice si gobierna no prueba nada.
    muda = FW.evaluar(_caso(evidencia=[_ev("e-1", gobierna=None)]))
    t.igual("E-21 la traza muda no pasa", "PARTIAL", muda["state"])
    t.igual("E-21 con su motivo", "FRAMEWORK_GOVERNANCE_UNPROVEN", muda["reason"])


def test_e22_el_bajo_nivel_por_el_framework(t):
    """E-22 (P1-18) — integrado de forma indirecta, puede cumplir."""
    caso = _caso(items=[_superficie(lowLevelComponents=[
        {"id": "conector", "usage": "THROUGH_FRAMEWORK"}])])
    salida = FW.evaluar(caso)
    t.igual("E-22 el estado", "PASS", salida["state"])
    t.verdadero("E-22 aprueba", FW.aprueba(salida))
    t.igual("E-22 los tres usos declarados",
            ("THROUGH_FRAMEWORK", "DIRECT_REPLACEMENT", "UNRESOLVED"), FW.USOS)


def test_e23_el_bajo_nivel_como_reemplazo(t):
    """E-23 (P1-19) — LOW_LEVEL_DIRECT_USE_BYPASS y FAIL."""
    caso = _caso(items=[_superficie(lowLevelComponents=[
        {"id": "conector", "usage": "DIRECT_REPLACEMENT"}])])
    salida = FW.evaluar(caso)
    t.igual("E-23 el estado", "FAIL", salida["state"])
    t.igual("E-23 el motivo", "LOW_LEVEL_DIRECT_USE_BYPASS", salida["reason"])
    t.verdadero("E-23 nombra el componente",
                "conector" in repr(salida["surfaces"][0]["lowLevelDirect"]))
    t.verdadero("E-23 no aprueba", not FW.aprueba(salida))
    # 🔴 Y manda aunque haya traza de gobernanza: un reemplazo probado no mejora con traza.
    t.igual("E-23 manda sobre la traza", "FAIL", salida["state"])


def test_e24_el_uso_no_se_deduce_del_nombre(t):
    """E-24 (§7) — sin declarar como se usa, no se resuelve."""
    for uso in (None, "", "UNRESOLVED", "CUALQUIER_COSA"):
        caso = _caso(items=[_superficie(lowLevelComponents=[
            {"id": "conector", "usage": uso}])])
        salida = FW.evaluar(caso)
        t.igual("E-24 el uso `%s` no se resuelve" % uso, "PARTIAL", salida["state"])
        t.igual("E-24 el uso `%s` deja el motivo" % uso, "LOW_LEVEL_USE_UNRESOLVED",
                salida["reason"])
        t.verdadero("E-24 el uso `%s` no aprueba" % uso, not FW.aprueba(salida))


# -- E-25 a E-33 — la clausula de Node -----------------------------------------

def test_e25_node_con_npm_pasa(t):
    """E-25 (P1-22) — el camino activo usa el permitido."""
    salida = NP.evaluar(_nodo())
    t.igual("E-25 el estado", "PASS", salida["state"])
    t.verdadero("E-25 aprueba", NP.aprueba(salida))
    t.igual("E-25 el activo es el permitido", ["NPM"], salida["activeManagers"])
    t.igual("E-25 el permitido es el que el estandar nombra", "NPM", NP.PERMITIDO)
    # Y en minuscula es el mismo: lo que se compara esta normalizado de los dos lados.
    t.igual("E-25 en minuscula es el mismo", "PASS",
            NP.evaluar(_nodo(managers=[_pm(manager="npm")]))["state"])


def test_e26_yarn_activo_falla(t):
    """E-26 (P1-23) — un administrador activo que no es el permitido."""
    salida = NP.evaluar(_nodo(managers=[_pm(manager="YARN")]))
    t.igual("E-26 el estado", "FAIL", salida["state"])
    t.igual("E-26 el motivo", "ALTERNATIVE_PACKAGE_MANAGER_ACTIVE", salida["reason"])
    t.verdadero("E-26 no aprueba", not NP.aprueba(salida))


def test_e27_pnpm_activo_falla(t):
    """E-27 (P1-24) — la misma respuesta, sin que nadie lo agregue a una lista."""
    salida = NP.evaluar(_nodo(managers=[_pm(manager="PNPM")]))
    t.igual("E-27 el estado", "FAIL", salida["state"])
    t.igual("E-27 el motivo", "ALTERNATIVE_PACKAGE_MANAGER_ACTIVE", salida["reason"])


def test_e28_cualquier_alternativa_falla(t):
    """E-28 (P1-25) — el invariante: se compara contra el permitido, no contra una lista."""
    alternativas = ("YARN", "PNPM", "BUN", "CNPM", "VOLTA", "UN-ADMINISTRADOR-QUE-NO-EXISTE",
                    "yarn", "Pnpm")
    for manager in alternativas:
        salida = NP.evaluar(_nodo(managers=[_pm(manager=manager)]))
        t.igual("E-28 %s activo falla" % manager, "FAIL", salida["state"])
        t.igual("E-28 %s con el mismo motivo" % manager, "ALTERNATIVE_PACKAGE_MANAGER_ACTIVE",
                salida["reason"])
        t.verdadero("E-28 %s no aprueba" % manager, not NP.aprueba(salida))

    # 🔴 Y no hay una lista de prohibidos adentro del modulo: lo unico que nombra es el permitido.
    fuente = RUTA_NP.read_text(encoding="utf-8")
    for prohibido in ("YARN", "yarn", "PNPM", "pnpm", "BUN", "bun ", "Bun"):
        t.verdadero("E-28 el modulo no nombra `%s`" % prohibido, prohibido not in fuente)


def test_e29_sin_saber_cual_esta_activo(t):
    """E-29 (P1-26) — NODE_PACKAGE_MANAGER_EVIDENCE_UNRESOLVED."""
    # 🔴 El motivo va en la aserción, no solo el estado: la guarda de "ninguno activo" tapa a la
    # de "no dice si esta activo" y las dos dan el mismo estado. Sin el motivo, sacar la segunda
    # dejaba el test verde y el que remedia no sabia que dato le falta.
    for nombre, manager, motivo in (
            ("sin declarar la actividad", _pm(activo=None),
             "PACKAGE_MANAGER_ACTIVITY_UNDECLARED"),
            ("sin decir cual es", _pm(manager=""), "NODE_PACKAGE_MANAGER_EVIDENCE_UNRESOLVED"),
            ("sin fuente", _pm(fuente="PROJECT_CONVENTION"),
             "PACKAGE_MANAGER_SOURCE_UNDECLARED"),
            ("sin referencia", _pm(reference=""), "PACKAGE_MANAGER_SOURCE_UNDECLARED")):
        salida = NP.evaluar(_nodo(managers=[manager]))
        t.igual("E-29 %s no se resuelve" % nombre, "NODE_PACKAGE_MANAGER_EVIDENCE_UNRESOLVED",
                salida["state"])
        t.igual("E-29 %s dice que dato falta" % nombre, motivo, salida["reason"])
        t.verdadero("E-29 %s no aprueba" % nombre, not NP.aprueba(salida))
    # Y ninguna evidencia declarada tampoco.
    t.igual("E-29 sin ninguna evidencia", "NODE_PACKAGE_MANAGER_EVIDENCE_UNRESOLVED",
            NP.evaluar(_nodo(managers=[]))["state"])
    # Con todas historicas, no se sabe con que se administra hoy.
    t.igual("E-29 todas historicas", "NODE_PACKAGE_MANAGER_EVIDENCE_UNRESOLVED",
            NP.evaluar(_nodo(managers=[_pm(activo=False)]))["state"])


def test_e30_lo_historico_se_investiga(t):
    """E-30 (P1-27) — no se ignora y no falla solo."""
    historico = _pm(pid="pm-2", manager="YARN", activo=False)
    sin_investigar = NP.evaluar(_nodo(managers=[_pm(), historico]))
    t.igual("E-30 sin investigar, la pregunta queda abierta", "PARTIAL",
            sin_investigar["state"])
    t.igual("E-30 con su motivo", "HISTORICAL_ARTIFACT_NOT_INVESTIGATED",
            sin_investigar["reason"])
    t.verdadero("E-30 no aprueba", not NP.aprueba(sin_investigar))
    t.igual("E-30 y no desaparece del resultado", ["pm-2"], sin_investigar["historical"])

    investigado = dict(historico, investigated=True)
    salida = NP.evaluar(_nodo(managers=[_pm(), investigado]))
    t.igual("E-30 investigado, no falla", "PASS", salida["state"])
    t.igual("E-30 y sigue informandose", ["pm-2"], salida["historical"])


def test_e31_dos_activos_distintos(t):
    """E-31 (§8) — NODE_PACKAGE_MANAGER_CONFLICT, y no se elige uno."""
    salida = NP.evaluar(_nodo(managers=[_pm(), _pm(pid="pm-2", manager="YARN")]))
    t.igual("E-31 el estado", "NODE_PACKAGE_MANAGER_CONFLICT", salida["state"])
    t.igual("E-31 los dos se informan", ["NPM", "YARN"], salida["activeManagers"])
    t.verdadero("E-31 no aprueba", not NP.aprueba(salida))
    # Dos evidencias del mismo administrador no son un conflicto.
    t.igual("E-31 dos del mismo no es conflicto", "PASS",
            NP.evaluar(_nodo(managers=[_pm(), _pm(pid="pm-2")]))["state"])


def test_e32_sin_node_la_clausula_no_es_relevante(t):
    """E-32 (P1-28) — NOT_RELEVANT, que no es NOT_APPLICABLE."""
    salida = NP.evaluar(_nodo(superficies=()))
    t.igual("E-32 el estado", "NOT_RELEVANT", salida["state"])
    t.verdadero("E-32 no aprueba", not NP.aprueba(salida))

    # 🔴 La distincion entera: `NOT_APPLICABLE` no existe en P1, porque P1 es ALWAYS. Se barre
    # sobre las CADENAS del modulo y no sobre su texto: los docstrings explican la diferencia, y
    # explicarla es lo contrario de devolverla.
    for nombre, modulo in MODULOS:
        t.verdadero("E-32 %s no declara NOT_APPLICABLE" % nombre,
                    "NOT_APPLICABLE" not in modulo.ESTADOS)
        ruta = RUTA_FW if modulo is FW else RUTA_NP
        for literal in _literales(ruta):
            t.verdadero("E-32 %s no lo puede devolver: %s" % (nombre, literal[:30]),
                        "NOT_APPLICABLE" not in literal)
    bloque = c_normativa.resolucion({})
    t.verdadero("E-32 y P1 sigue aplicando sin ninguna senal",
                "P1" in bloque["applicableRules"])
    t.verdadero("E-32 P1 no esta entre las no aplicables",
                "P1" not in bloque["notApplicableRules"])
    # Sin contexto de tecnologias, tampoco se declara la ausencia.
    t.igual("E-32 sin contexto no se declara la ausencia", "NODE_TECHNOLOGY_CONTEXT_UNRESOLVED",
            NP.evaluar(_nodo(completo=False))["state"])


def test_e33_no_se_inventa_una_version_de_npm(t):
    """E-33 (P1-29) — ni en el modulo, ni en los artefactos."""
    numeros = sorted(n for n, v in vars(NP).items()
                     if isinstance(v, (int, float)) and not isinstance(v, bool))
    t.igual("E-33 el modulo no declara constantes numericas", [], numeros)
    for nombre, texto in _artefactos_de_p1().items():
        t.vacio("E-33 %s no le pone version al administrador" % nombre,
                re.findall(r"(?i)\bnpm\b[^\n]{0,12}\bv?\d", texto))


# -- E-34 a E-37 — la plataforma de negocio ------------------------------------

def test_e34_la_plataforma_gobernada_pasa(t):
    """E-34 (P1-30) — las cuatro cosas evidenciadas."""
    salida = FW.evaluar(_caso(items=[_plataforma()]))
    t.igual("E-34 el estado", "PASS", salida["state"])
    t.verdadero("E-34 aprueba", FW.aprueba(salida))
    t.igual("E-34 declara la clausula que la habilita", "P1.plataformas",
            salida["surfaces"][0]["clause"])
    t.igual("E-34 y cita el lineamiento", LINEAMIENTOS["id"],
            salida["surfaces"][0]["guidelines"])


def test_e35_el_nombre_del_producto_no_alcanza(t):
    """E-35 (P1-31, P1-32) — falta cualquiera de las cuatro y no se resuelve."""
    formas = {
        "solo el nombre": _plataforma(structuredEnvironment=None, guidelines={},
                                      customizationInside=None,
                                      conflictsWithStandard=None),
        "sin entorno estructurado": _plataforma(structuredEnvironment=None),
        "sin lineamientos": _plataforma(guidelines={}),
        "con un lineamiento sin fuente": _plataforma(
            guidelines={"id": "x", "reference": "r"}),
        "con un lineamiento sin referencia": _plataforma(
            guidelines={"id": "x", "source": "GCBA_NORMATIVE"}),
        "sin customizacion adentro": _plataforma(customizationInside=None),
        "sin declarar la contradiccion": _plataforma(conflictsWithStandard=None),
    }
    t.igual("E-35 son siete formas del hueco", 7, len(formas))
    for nombre, superficie in sorted(formas.items()):
        salida = FW.evaluar(_caso(items=[superficie]))
        t.igual("E-35 %s no se resuelve" % nombre,
                "BUSINESS_PLATFORM_GOVERNANCE_UNRESOLVED", salida["state"])
        t.verdadero("E-35 %s no aprueba" % nombre, not FW.aprueba(salida))


def test_e36_el_lineamiento_que_contradice(t):
    """E-36 (P1-33) — BUSINESS_PLATFORM_STANDARD_CONFLICT, y no pasa."""
    salida = FW.evaluar(_caso(items=[_plataforma(conflicto=True)]))
    t.igual("E-36 el estado", "BUSINESS_PLATFORM_STANDARD_CONFLICT", salida["state"])
    t.verdadero("E-36 no aprueba", not FW.aprueba(salida))
    # 🔴 Y manda sobre la falta de gobernanza: la contradiccion no se arregla con mas evidencia.
    incompleta = FW.evaluar(_caso(items=[_plataforma(conflicto=True,
                                                     structuredEnvironment=None)]))
    t.igual("E-36 manda sobre el hueco de gobernanza",
            "BUSINESS_PLATFORM_STANDARD_CONFLICT", incompleta["state"])


def test_e37_la_plataforma_no_exime_al_resto(t):
    """E-37 (P1-34) — los servicios propios siguen debiendo framework."""
    caso = _caso(items=[_plataforma(), _superficie(sid="s-propio",
                                                   clase="VANILLA_APPLICATION")])
    salida = FW.evaluar(caso)
    t.igual("E-37 el estado", "FAIL", salida["state"])
    t.igual("E-37 el motivo", "VANILLA_RUNTIME_PATH_DETECTED", salida["reason"])
    estados = {s["surfaceId"]: s["state"] for s in salida["surfaces"]}
    t.igual("E-37 la plataforma sigue pasando", "PASS", estados["s-plataforma"])
    t.igual("E-37 y el servicio propio falla", "FAIL", estados["s-propio"])
    # Y un servicio propio sin traza tampoco queda eximido.
    sin_traza = _caso(items=[_plataforma(), _superficie(sid="s-propio", refs=())])
    t.igual("E-37 ni uno sin traza", "PARTIAL", FW.evaluar(sin_traza)["state"])


# -- E-38 a E-42 — la propagacion, el registro, la traza y el barrido ----------

def test_e38_la_unidad_propaga_sin_senal(t):
    """E-38 (P1-37) — P1 aplica sin que la unidad declare ninguna senal."""
    for nombre, senales in (("sin senales", {}), ("con una senal ajena",
                                                  {"frontendPresent": True})):
        bloque = c_normativa.resolucion(senales)
        t.verdadero("E-38 %s P1 aplica" % nombre, "P1" in bloque["applicableRules"])
        for pid in POLICIES:
            t.verdadero("E-38 %s propaga %s" % (nombre, pid), pid in bloque["declaredPolicies"])
        for cid in CHEQUEOS:
            t.verdadero("E-38 %s propaga %s" % (nombre, cid), cid in bloque["declaredChecks"])
        t.verdadero("E-38 %s P1 no queda sin resolver" % nombre,
                    "P1" not in {u["rule"] for u in bloque["unresolvedRules"]})
    # 🔴 Y son los ids EXACTOS de la fila, no unos parecidos.
    p1 = c_matriz.regla("P1")
    bloque = c_normativa.resolucion({})
    for pid in p1["policies"]:
        t.verdadero("E-38 %s viene de la fila" % pid, pid in bloque["declaredPolicies"])
    for cid in p1["checks"]:
        t.verdadero("E-38 %s viene de la fila" % cid, cid in bloque["declaredChecks"])


def test_e39_los_controles_dejan_de_ser_un_hueco(t):
    """E-39 (P1-38) — treinta y cinco declarados, once reglas completas, sin sueltos."""
    reporte = c_controles.reporte()
    t.igual("E-39 son cuarenta y seis controles", 46, reporte["summary"]["declaredControls"])
    t.verdadero("E-39 el registro es valido", reporte["result"]["registryValid"])
    t.verdadero("E-39 y no hay archivos sin declarar", reporte["result"]["filesystemClean"])
    t.igual("E-39 ningun archivo suelto", [], reporte["undeclared"])
    t.vacio("E-39 sin errores de schema", reporte["schemaErrors"])

    for control in POLICIES + CHEQUEOS:
        t.igual("E-39 %s esta INSTALLED" % control, "INSTALLED",
                reporte["controls"].get(control))
    faltan = {f["id"] for f in c_matriz.controles_no_instalados(c_matriz.resolver({}))}
    for control in POLICIES + CHEQUEOS:
        t.verdadero("E-39 %s ya no figura como no instalado" % control, control not in faltan)

    instalados = set(c_controles.instalados()["POLICY"]) | set(
        c_controles.instalados()["CHECK"]) | set(c_controles.instalados()["REVIEW"])
    completas = []
    for r in c_matriz.reglas():
        suyos = set(r.get("policies") or []) | set(r.get("checks") or []) | set(
            r.get("reviews") or [])
        if suyos and suyos <= instalados:
            completas.append(r["id"])
    t.igual("E-39 once reglas tienen todos sus controles construidos",
            ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "G1", "G2", "P1"],
            sorted(completas))


def test_e40_todo_resultado_conserva_la_traza(t):
    """E-40 (P1-39) — ES0901 / 6.3 / 7.1 / P1, en todos los caminos de los dos checks."""
    for nombre, modulo, caminos in TODOS_LOS_CAMINOS:
        t.igual("E-40 %s declara la tupla" % nombre, TRAZA, modulo.TRAZA)
        for estado, caso in caminos().items():
            salida = modulo.evaluar(caso)
            t.igual("E-40 %s en %s conserva la tupla" % (nombre, estado), TRAZA,
                    salida["source"])
            t.igual("E-40 %s en %s dice que control es" % (nombre, estado), nombre,
                    salida["control"])
            t.igual("E-40 %s en %s dice de que regla" % (nombre, estado), "P1", salida["rule"])
            texto = repr(salida)
            for otra in ("D1", "D5", "D6", "D7", "D8", "ES0902"):
                t.verdadero("E-40 %s en %s no nombra %s" % (nombre, estado, otra),
                            otra not in texto)


def test_e41_los_estados_existen_y_solo_pasa_uno(t):
    """E-41 (§12) — los nueve y los ocho, y los dos motivos que el pedido lista como estados."""
    NUEVE = ("PASS", "FAIL", "PARTIAL", "FRAMEWORK_CONTEXT_UNRESOLVED",
             "DEVELOPMENT_SURFACE_CLASSIFICATION_UNRESOLVED",
             "BUSINESS_PLATFORM_GOVERNANCE_UNRESOLVED", "BUSINESS_PLATFORM_STANDARD_CONFLICT",
             "G1_EVIDENCE_REQUIRED", "TEST_TARGET_UNAVAILABLE")
    OCHO = ("PASS", "FAIL", "PARTIAL", "NOT_RELEVANT", "NODE_TECHNOLOGY_CONTEXT_UNRESOLVED",
            "NODE_PACKAGE_MANAGER_EVIDENCE_UNRESOLVED", "NODE_PACKAGE_MANAGER_CONFLICT",
            "TEST_TARGET_UNAVAILABLE")
    t.igual("E-41 el check de framework declara estos nueve", NUEVE, FW.ESTADOS)
    t.igual("E-41 el de Node declara estos ocho", OCHO, NP.ESTADOS)

    for nombre, modulo, caminos in TODOS_LOS_CAMINOS:
        declarados = set(modulo.ESTADOS)
        alcanzados = {estado: modulo.evaluar(caso)["state"]
                      for estado, caso in caminos().items()}
        t.igual("E-41 %s alcanza todos los que declara" % nombre, declarados, set(alcanzados))
        for esperado, obtenido in sorted(alcanzados.items()):
            t.igual("E-41 %s alcanza %s" % (nombre, esperado), esperado, obtenido)
            t.igual("E-41 %s aprueba en %s solo si es PASS" % (nombre, esperado),
                    esperado == "PASS",
                    modulo.aprueba(modulo.evaluar(caminos()[esperado])))

    # 🔴 Los dos que el pedido lista como estados y aca son MOTIVOS: alcanzables, informados, y
    # ninguno aprueba.
    vanilla = FW.evaluar(_caso(items=[_superficie(sid="s-v", clase="VANILLA_APPLICATION")]))
    t.igual("E-41 VANILLA_RUNTIME_PATH_DETECTED se alcanza", "VANILLA_RUNTIME_PATH_DETECTED",
            vanilla["reason"])
    t.verdadero("E-41 y no aprueba", not FW.aprueba(vanilla))
    bajo = FW.evaluar(_caso(items=[_superficie(lowLevelComponents=[
        {"id": "c", "usage": "DIRECT_REPLACEMENT"}])]))
    t.igual("E-41 LOW_LEVEL_DIRECT_USE_BYPASS se alcanza", "LOW_LEVEL_DIRECT_USE_BYPASS",
            bajo["reason"])
    t.verdadero("E-41 y tampoco aprueba", not FW.aprueba(bajo))
    t.igual("E-41 los dos estan declarados en el modulo",
            ("VANILLA_RUNTIME_PATH_DETECTED", "LOW_LEVEL_DIRECT_USE_BYPASS"),
            (FW.RUNTIME_VANILLA, FW.BYPASS_DE_BAJO_NIVEL))


# 🔴 El invariante de P1: un artefacto de la regla no lleva una version, una lista de tecnologias,
# una lista de administradores prohibidos ni un producto de plataforma. Lo que SI puede llevar son
# las citas del estandar, que nombran a NPM, a YARN y a las tecnologias de ejemplo — por eso el
# barrido busca la VERSION pegada a una tecnologia y no el nombre suelto.
PROHIBIDOS = (
    # localizadores de red
    r"(?i)https?://",
    r"(?i)\b[a-z0-9][a-z0-9-]*(\.[a-z0-9-]+)*\.(ar|com|net|org|gov|gob|io|dev|app|cloud|bue|"
    r"tech|local)\b",
    r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    # una version pegada a una tecnologia o a un administrador de paquetes: eso es de G1
    r"(?i)\b(angular|react|nestjs|node|nodejs|npm|java|php|python|laravel|spring|dotnet|vue|"
    r"express)\b[\s:=v]{0,3}\d",
    r"(?i)\b(version|versión|ver\.)\s*[:=]?\s*v?\d+\.\d+",
    r"(?<![.\d])\d+\.\d+\.\d+",
    r"(?i)\b\d+\.\d+\.x\b",
    # comparacion de versiones, que es de G1 y no se reimplementa
    r"(?i)\b(semver|patch[_-]?level|version[_-]?range|deprecat\w*[_-]?toleran\w*)\b",
    # paquetes
    r"(?i)\b(npm|pnpm|yarn|bun)\s+(i|install|add|ci|run)\b",
    r"@[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*",
)

# Productos de plataforma de negocio. Aca no se nombra ninguno: el estandar nombra CATEGORIAS
# —ERP, CRM, FSM— y el nombre de un producto no establece nada, que es justo lo que la regla dice.
PEGADOS = ("salesforce", "servicenow", "dynamics365", "sapbusiness", "oraclefusion",
           "sugarcrm", "zohocrm", "microsoftdynamics")
SUELTOS = ("sap", "odoo", "netsuite", "hubspot", "peoplesoft", "workday", "siebel")


def _seccion_de_p1_del_doc():
    """La seccion que P1 agrego a `docs/normativa-7.1.md`."""
    texto = (RAIZ / "docs" / "normativa-7.1.md").read_text(encoding="utf-8")
    titulo = "## Una regla, tres cláusulas y ninguna señal: P1"
    if titulo not in texto:
        return titulo, ""
    return titulo, texto.split(titulo, 1)[1].split("\n## ", 1)[0]


def _artefactos_de_p1():
    """Los ocho textos que la tabla `Qué se construye` de la spec declara como artefactos."""
    textos = {}
    for pid in POLICIES:
        textos["la policy %s" % pid] = (CONTROLES / "policies" / (pid + ".md")).read_text(
            encoding="utf-8")
    for cid in CHEQUEOS:
        textos["el check %s" % cid] = (CONTROLES / "checks" / (cid + ".py")).read_text(
            encoding="utf-8")
    textos["el registro"] = repr(c_controles.de_la_regla("P1"))
    textos["la fila de la matriz"] = repr(c_matriz.regla("P1"))
    textos["la doc"] = _seccion_de_p1_del_doc()[1]
    return textos


def _fugas_en(texto):
    sin_separadores = re.sub(r"[\s_\-]+", "", texto).lower()
    hallados = [p for p in PROHIBIDOS if re.search(p, texto)]
    hallados += [v for v in PEGADOS if v in sin_separadores]
    hallados += [v for v in SUELTOS
                 if re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(v), texto.lower())]
    return sorted(set(hallados))


def test_e42_ningun_artefacto_lleva_una_version_ni_un_catalogo(t):
    """E-42 (§4, P1-29, P1-31) — el invariante sobre los ocho artefactos, y sus tres mitades."""
    titulo, seccion = _seccion_de_p1_del_doc()
    t.verdadero("E-42 la seccion de P1 esta en la doc", bool(seccion))
    t.verdadero("E-42 y tiene contenido", len(seccion) > 2000)

    artefactos = _artefactos_de_p1()
    t.igual("E-42 son ocho textos los que se barren", 8, len(artefactos))
    for nombre, texto in sorted(artefactos.items()):
        t.igual("E-42 %s esta limpio" % nombre, [], _fugas_en(texto))

    for nombre, modulo, caminos in TODOS_LOS_CAMINOS:
        for estado, caso in caminos().items():
            t.igual("E-42 ni el resultado de %s en %s" % (nombre, estado), [],
                    _fugas_en(repr(modulo.evaluar(caso))))

    # 🔴 La segunda mitad, en crudo.
    FUGAS = (
        "Angular 17",
        "se exige React 18.2",
        "NestJS v10",
        "node 20.11.1",
        "npm 10",
        "la version homologada es 8.2.30",
        "PHP 8.2",
        "Laravel 11",
        "Spring Boot 3.2.1",
        "version: 1.2.3",
        "ver. 4.5",
        "la rama 8.2.x",
        "se compara con semver",
        "patch_level dentro de la rama",
        "deprecated-tolerance de dos estandares",
        "npm install",
        "yarn add",
        "pnpm i",
        "bun install",
        "@angular/core",
        "https://registry.example/paquete",
        "registry.gcba.gob.ar",
        "10.20.30.40/registry",
        # Productos de plataforma, juntos, partidos y pegados.
        "la plataforma es SAP",
        "Sales force como CRM",
        "ServiceNow para FSM",
        "Microsoft Dynamics 365",
        "se usa Odoo",
        "el ERP es NetSuite",
        "Oracle Fusion",
        "Sugar CRM",
    )
    t.igual("E-42 son treinta y una formas de fuga", 31, len(FUGAS))
    for fuga in FUGAS:
        t.verdadero("E-42 se detecta: %s" % fuga[:40], bool(_fugas_en(fuga)))

    base = artefactos["la policy homologated-framework-required"]
    t.igual("E-42 la premisa: la policy esta limpia", [], _fugas_en(base))
    t.verdadero("E-42 y con una fuga adentro deja de estarlo",
                bool(_fugas_en(base + "\nAngular 17 es la version homologada.\n")))
    t.verdadero("E-42 y la doc tambien",
                bool(_fugas_en(artefactos["la doc"] + "\nLa plataforma es SAP.\n")))

    # 🔴 La tercera mitad: lo que NO es una fuga. Es la mas delicada de las cuatro reglas con
    # barrido, porque los artefactos de P1 TIENEN que poder citar al estandar, que nombra al
    # administrador permitido, a las alternativas y a las tecnologias de ejemplo.
    LIMPIOS = (
        "el administrador de paquetes permitido es NPM (Node Package Manager)",
        "no esta permitido el uso de YARN u otras alternativas",
        "en desarrollos que utilicen tecnologias basadas en Node.js, como Angular, React o NestJS",
        "para ERP, CRM, FSM, etc., su uso esta habilitado bajo los lineamientos propios",
        "todo desarrollo debe realizarse utilizando frameworks homologados en este documento",
        "no se permite el uso del lenguaje puro ('vanilla') sin el soporte de su framework",
        "conectores de base de datos usados por un ORM",
        "ES0901 6.3, seccion 7.1, regla P1, pagina 13",
        "P1.node y P1.plataformas heredan la clasificacion de P1",
        "la homologacion y la version son de G1, y no se reimplementan aca",
        "se reusa annex-ii-technology-catalog.json, que es el archivo del Anexo II",
        "G1_EVIDENCE_REQUIRED cuando no hay veredicto citado",
        "NOT_RELEVANT no es NOT_APPLICABLE, y la diferencia es el punto",
        "FRAMEWORK_GOVERNED BUSINESS_PLATFORM_GOVERNED AUXILIARY_TOOLING VANILLA_APPLICATION",
        "THROUGH_FRAMEWORK y DIRECT_REPLACEMENT son dos usos del mismo paquete",
        "27 skills instaladas y 31 controles declarados",
        "controles/checks/framework-homologation.py y la policy de al lado",
        "docs/normativa-7.1.md, es0901-7.1.json y la matriz",
        "un entorno de desarrollo estructurado con lineamientos autoritativos",
        "el nombre del producto no establece nada",
        "la fila declara dos agentes duenos y cero senales",
    )
    for limpio in LIMPIOS:
        t.igual("E-42 no dispara con: %s" % limpio[:38], [], _fugas_en(limpio))
