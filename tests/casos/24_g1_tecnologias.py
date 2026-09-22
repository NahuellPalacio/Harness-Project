# G1: tecnologias y versiones homologadas por la ASI.
#
# Escenarios E-01 a E-26 de docs/cambios/g1-tecnologias-homologadas/spec.md. Entre
# parentesis, el G1-nn del pedido que cubre cada uno.
#
# Los casos negativos usan catalogos y registros FABRICADOS en memoria. El catalogo
# instalado no se rompe para probar que el validador anda.
import copy
import importlib.util
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CONTROLES = RAIZ / "harnesses" / "desarrollo" / "controles"

sys.path.insert(0, str(BIN))
from orquestacion import anexo2 as c_anexo2            # noqa: E402
from orquestacion import controles as c_controles      # noqa: E402
from orquestacion import matriz as c_matriz            # noqa: E402
from orquestacion import roster as c_roster            # noqa: E402


def _control(nombre):
    """Un check normativo se carga por ruta: su archivo lleva guiones, como los del hook."""
    ruta = CONTROLES / "checks" / (nombre + ".py")
    spec = importlib.util.spec_from_file_location("control_" + nombre.replace("-", "_"), ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


HOMOLOGACION = _control("technology-homologation")
VERSIONES = _control("technology-version-compliance")


def _catalogo():
    return copy.deepcopy(c_anexo2.cargar())


def _entrada(doc, tid):
    for e in doc["entries"]:
        if e["id"] == tid:
            return e
    raise AssertionError("no esta " + tid)


# -- E-01 a E-03 — el catalogo -------------------------------------------------

def test_e01_el_catalogo_valida(t):
    """E-01 (G1-01) — carga y valida contra su schema."""
    doc = _catalogo()
    t.vacio("E-01 sin errores de schema", c_anexo2.validar_schema(doc))
    t.igual("E-01 son 142 entradas", 142, len(doc["entries"]))

    # Y el validador tiene dientes: una entrada que rompe el contrato no pasa.
    roto = _catalogo()
    roto["entries"][0]["versionRule"] = "COMO_QUIERA"
    t.verdadero("E-01 una regla de version inventada no valida",
                len(c_anexo2.validar_schema(roto)) > 0)
    roto = _catalogo()
    del roto["entries"][0]["sourcePage"]
    t.verdadero("E-01 y sin pagina tampoco", len(c_anexo2.validar_schema(roto)) > 0)


def test_e02_es_el_anexo_ii_de_6_3(t):
    """E-02 (G1-02) — la fuente es ES0901 6.3, y otro no se carga."""
    doc = _catalogo()
    t.igual("E-02 el estandar", "ES0901", doc["source"]["standard"])
    t.igual("E-02 la version", "6.3", doc["source"]["version"])
    t.verdadero("E-02 nombra el Anexo II",
                any("Annex II" in s for s in doc["source"].get("sections", [])))

    otro = _catalogo()
    otro["source"]["version"] = "6.1"
    problema = c_anexo2.controlar_fuente(otro)
    t.verdadero("E-02 uno de otra version no pasa", bool(problema))
    t.contiene("E-02 y dice por que", "6.3", problema)


def test_e03_ids_unicos_y_busqueda_por_alias(t):
    """E-03 — id unico, y se resuelve por id, por alias o por nombre."""
    doc = _catalogo()
    ids = [e["id"] for e in doc["entries"]]
    t.igual("E-03 ningun id repetido", len(ids), len(set(ids)))

    t.igual("E-03 por id", "php", c_anexo2.buscar("php", doc)["id"])
    t.igual("E-03 sin importar mayusculas", "php", c_anexo2.buscar("PHP", doc)["id"])
    t.igual("E-03 por nombre", "php", c_anexo2.buscar("PHP", doc)["id"])

    # Hoy ninguna entrada del Anexo II trae alias, asi que el caso se FABRICA. Saltearlo
    # cuando no hay datos deja el camino sin probar y el test pasa en vacio.
    doc = _catalogo()
    _entrada(doc, "php")["aliases"] = ["php-fpm", "hypertext-preprocessor"]
    t.igual("E-03 por alias", "php", (c_anexo2.buscar("php-fpm", doc) or {}).get("id"))
    t.igual("E-03 por alias, sin mayusculas", "php",
            (c_anexo2.buscar("HYPERTEXT-PREPROCESSOR", doc) or {}).get("id"))
    t.igual("E-03 lo que no esta", None, c_anexo2.buscar("cobol-del-95", doc))


# -- E-04 a E-10 — la version dentro de su rama --------------------------------

def _version(tec, ver, doc=None, contexto=None):
    return VERSIONES.evaluar({"technology": tec, "version": ver}, doc or _catalogo(), contexto)


def test_e04_la_version_homologada_exacta(t):
    """E-04 (G1-03) — el minimo de la rama pasa."""
    r = _version("php", "8.2.30")
    t.igual("E-04 el estado", "HOMOLOGATED", r["state"])
    t.igual("E-04 contra que version", "8.2.30", r.get("matched"))


def test_e05_un_parche_mayor_en_la_misma_rama(t):
    """E-05 (G1-04) — 8.2.31 pasa."""
    t.igual("E-05 el estado", "HOMOLOGATED", _version("php", "8.2.31")["state"])


def test_e06_un_parche_menor_en_la_misma_rama(t):
    """E-06 (G1-05) — por debajo del minimo de la rama no pasa.

    Ojo con esto: las versiones DEPRECADAS del catalogo tambien siguen la regla del parche.
    En php la homologada de la rama 8.2 es 8.2.30 y la deprecada es 8.2.29, asi que 8.2.29 no
    es "no homologada" — es "deprecada tolerada", que es otra cosa y tiene otra consecuencia.
    Lo que no llega ni al piso deprecado si es NOT_HOMOLOGATED.
    """
    r = _version("php", "8.2.29")
    t.verdadero("E-06 por debajo del minimo no esta homologada", r["state"] != "HOMOLOGATED")
    t.igual("E-06 y es la deprecada", "DEPRECATED_TOLERATED", r["state"])

    bajo = _version("php", "8.2.28")
    t.igual("E-06 mas abajo todavia", "NOT_HOMOLOGATED", bajo["state"])


def test_e07_una_rama_menor_sin_listar(t):
    """E-07 (G1-06) — 8.1.x no se vuelve valida sola."""
    t.igual("E-07 el estado", "NOT_HOMOLOGATED", _version("php", "8.1.40")["state"])


def test_e08_una_rama_mayor_sin_listar(t):
    """E-08 (G1-07) — 8.9 no es rechazo: nadie la evaluo."""
    r = _version("php", "8.9.0")
    t.igual("E-08 el estado", "ASI_EVALUATION_REQUIRED", r["state"])
    t.verdadero("E-08 no es un rechazo", r["state"] != "NOT_HOMOLOGATED")


def test_e09_dos_ramas_se_evaluan_por_separado(t):
    """E-09 (G1-16) — estar en una rama no valida la otra."""
    doc = _catalogo()
    php = _entrada(doc, "php")
    t.igual("E-09 php tiene dos ramas", 2, len(php["homologatedVersionsRaw"]))
    t.igual("E-09 la 8.2 pasa por la 8.2", "HOMOLOGATED", _version("php", "8.2.30", doc)["state"])
    t.igual("E-09 la 8.3 pasa por la 8.3", "HOMOLOGATED", _version("php", "8.3.29", doc)["state"])
    # Y el minimo de una rama no vale como minimo de la otra: 8.3.28 no alcanza el 8.3.29
    # homologado, y cae en la rama deprecada 8.3.25.
    t.verdadero("E-09 8.3.28 no esta homologada",
                _version("php", "8.3.28", doc)["state"] != "HOMOLOGATED")
    t.igual("E-09 8.3.24 no llega a nada", "NOT_HOMOLOGATED",
            _version("php", "8.3.24", doc)["state"])


def test_e10_latest_no_es_una_version(t):
    """E-10 — lo que no se puede comparar es UNRESOLVED, nunca HOMOLOGATED."""
    for cruda in ("latest", "*", "", "8.x"):
        r = _version("php", cruda)
        t.igual("E-10 `%s`" % cruda, "UNRESOLVED", r["state"])
        t.verdadero("E-10 `%s` no pasa como homologada" % cruda, r["state"] != "HOMOLOGATED")


# -- E-11 a E-13 — deprecadas e historia ---------------------------------------

def test_e11_una_version_deprecada_se_tolera(t):
    """E-11 (G1-08) — DEPRECATED_TOLERATED, con su observacion de actualizacion."""
    doc = _catalogo()
    t.verdadero("E-11 esta entre las deprecadas",
                "8.2.29" in _entrada(doc, "php")["deprecatedVersionsRaw"])
    r = VERSIONES.evaluar({"technology": "php", "version": "8.2.29"}, doc)
    t.igual("E-11 el estado", "DEPRECATED_TOLERATED", r["state"])
    t.contiene("E-11 lleva observacion", "actualizacion", r["observation"])
    t.igual("E-11 y dice contra que", "8.2.29", r.get("matched"))

    # La homologada de la misma rama gana: primero se busca en homologadas.
    t.igual("E-11 la homologada se impone", "HOMOLOGATED",
            VERSIONES.evaluar({"technology": "php", "version": "8.2.30"}, doc)["state"])


def test_e12_deprecada_no_se_vuelve_homologada(t):
    """E-12 (G1-09) — en ningun camino."""
    doc = _catalogo()
    e = _entrada(doc, "php")
    e["homologatedVersionsRaw"] = ["8.3.29"]
    e["deprecatedVersionsRaw"] = ["8.2.29", "8.2.30"]
    for v in ("8.2.29", "8.2.30", "8.2.31"):
        r = VERSIONES.evaluar({"technology": "php", "version": v}, doc)
        t.verdadero("E-12 %s no queda homologada" % v, r["state"] != "HOMOLOGATED")


def test_e13_dos_estandares_atras_pide_historia(t):
    """E-13 (G1-10) — sin catalogo historico no se bloquea por inferencia."""
    r = VERSIONES.bloqueo_por_antiguedad({"technology": "php", "version": "7.4.0"})
    t.igual("E-13 el estado", "VERSION_HISTORY_REQUIRED", r["state"])
    t.contiene("E-13 dice que falta", "catalogo", r["reason"])
    con_historia = VERSIONES.bloqueo_por_antiguedad(
        {"technology": "php", "version": "7.4.0"}, catalogo_historico={"6.1": {}})
    t.verdadero("E-13 con historia cambia", con_historia["state"] != "VERSION_HISTORY_REQUIRED")


# -- E-14 a E-17 — lo que el catalogo no fija ----------------------------------

def test_e14_una_tecnologia_que_no_esta(t):
    """E-14 (G1-11) — ASI_EVALUATION_REQUIRED: ni aprobada ni rechazada."""
    r = HOMOLOGACION.evaluar({"technology": "cobol-del-95"}, _catalogo())
    t.igual("E-14 el estado", "ASI_EVALUATION_REQUIRED", r["state"])
    t.verdadero("E-14 no la rechaza", r["state"] != "NOT_HOMOLOGATED")
    t.verdadero("E-14 ni la aprueba", r["state"] != "HOMOLOGATED")


def test_e15_version_dependiente_del_framework(t):
    """E-15 (G1-14) — VERSION_CONTEXT_REQUIRED, y con el framework declarado resuelve."""
    doc = _catalogo()
    t.igual("E-15 la regla de la entrada", "FRAMEWORK_DEPENDENT",
            _entrada(doc, "laravel-migrations")["versionRule"])
    r = VERSIONES.evaluar({"technology": "laravel-migrations", "version": ""}, doc)
    t.igual("E-15 sin contexto", "VERSION_CONTEXT_REQUIRED", r["state"])

    con = VERSIONES.evaluar({"technology": "laravel-migrations", "version": ""}, doc,
                            {"framework": {"technology": "php", "version": "8.2.30"}})
    t.igual("E-15 con el framework declarado hereda", "HOMOLOGATED", con["state"])
    t.igual("E-15 y dice de quien", "php", con.get("inheritedFrom"))

    # Y si el framework no esta homologado, tampoco lo esta lo que depende de el.
    malo = VERSIONES.evaluar({"technology": "laravel-migrations", "version": ""}, doc,
                             {"framework": {"technology": "php", "version": "8.1.0"}})
    t.igual("E-15 hereda tambien lo malo", "NOT_HOMOLOGATED", malo["state"])

    # CONTEXT_DEPENDENT es la otra forma, y la unica entrada que la tiene es ngx-spinner.
    dependientes = [e["id"] for e in doc["entries"] if e.get("versionRule") == "CONTEXT_DEPENDENT"]
    t.igual("E-15 la unica CONTEXT_DEPENDENT", ["ngx-spinner"], dependientes)
    r = VERSIONES.evaluar({"technology": "ngx-spinner", "version": "17.0.0"}, doc)
    t.igual("E-15 ngx-spinner sin contexto", "VERSION_CONTEXT_REQUIRED", r["state"])
    t.verdadero("E-15 ngx-spinner sin contexto no homologa", r["state"] != "HOMOLOGATED")
    con = VERSIONES.evaluar({"technology": "ngx-spinner", "version": "17.0.0"}, doc,
                            {"framework": {"technology": "angular", "version": "19.2.18"}})
    t.igual("E-15 ngx-spinner con angular declarado resuelve", "HOMOLOGATED", con["state"])
    t.igual("E-15 ngx-spinner dice de quien", "angular", con.get("inheritedFrom"))


def test_e16_version_asignada_por_el_proveedor(t):
    """E-16 (G1-15) — PROVIDER_VERSION_REQUIRED."""
    doc = _catalogo()
    t.igual("E-16 la regla", "PROVIDER_ASSIGNED_BY_DGSEI",
            _entrada(doc, "keycloak")["versionRule"])
    r = VERSIONES.evaluar({"technology": "keycloak", "version": "25.0.0"}, doc)
    t.igual("E-16 el estado", "PROVIDER_VERSION_REQUIRED", r["state"])


def test_e17_los_calificativos_se_conservan(t):
    """E-17 (G1-17) — LTS, LTR, SP y CE no se recortan: ni del resultado ni de la comparacion."""
    doc = _catalogo()
    t.verdadero("E-17 angular declara LTS",
                any("LTS" in v for v in _entrada(doc, "angular")["homologatedVersionsRaw"]))
    r = VERSIONES.evaluar({"technology": "angular", "version": "19.2.18"}, doc)
    t.igual("E-17 pasa", "HOMOLOGATED", r["state"])
    t.igual("E-17 y conserva el calificativo", "LTS", r.get("qualifier"))

    for crudo, esperado in (("6.0 SP1", "SP1"), ("1.1.0 CE", "CE"), ("19.2.18 (LTS)", "LTS"),
                            ("19c (LTR)", "LTR")):
        t.igual("E-17 parsea %s" % crudo, esperado,
                c_anexo2.parsear(crudo).get("qualifier"))

    # LTR: la unica entrada es Oracle `19c (LTR)`. El `c` es parte del numero, no el
    # calificativo; y el LTR se conserva.
    t.igual("E-17 el oraculo de LTR", ["19c (LTR)"],
            [v for e in doc["entries"] for v in e.get("homologatedVersionsRaw") or []
             if "LTR" in v])
    p = c_anexo2.parsear("19c (LTR)")
    t.igual("E-17 19c (LTR) es una version exacta", "EXACT", p["kind"])
    t.igual("E-17 19c (LTR) conserva el sufijo", "c", p.get("suffix"))
    t.igual("E-17 19c sin calificativo no lo inventa", "", c_anexo2.parsear("19c")["qualifier"])
    for declarada in ("19c (LTR)", "19c"):
        r = VERSIONES.evaluar({"technology": "oracle", "version": declarada}, doc)
        t.igual("E-17 oracle %s se homologa" % declarada, "HOMOLOGATED", r["state"])
        t.igual("E-17 oracle %s dice LTR" % declarada, "LTR", r.get("qualifier"))
    t.igual("E-17 oracle 19 no dice cual 19", "UNRESOLVED",
            _version("oracle", "19")["state"])

    # El calificativo compara. Cada fila es (tecnologia, declarada, estado).
    for tec, declarada, esperado in (
            ("cib-seven", "1.1.0 CE", "HOMOLOGATED"),
            ("cib-seven", "1.1.4 CE", "HOMOLOGATED"),
            ("cib-seven", "1.1.0 EE", "NOT_HOMOLOGATED"),
            ("cib-seven", "1.1.0", "UNRESOLVED"),
            ("jws", "6.0 SP1", "HOMOLOGATED"),
            ("jws", "6.0 SP2", "ASI_EVALUATION_REQUIRED"),
            ("jws", "6.0 SP0", "NOT_HOMOLOGATED"),
            ("jws", "6.0", "UNRESOLVED"),
            # Un calificativo de soporte que la tecnologia no usa: UNRESOLVED en todos lados
            # (ratificado el 2026-09-22). Angular usa LTS, no LTR.
            ("angular", "19.2.18 (LTR)", "UNRESOLVED"),
            ("cib-seven", "1.1.0 LTS", "UNRESOLVED"),
            ("jws", "6.0 LTS", "UNRESOLVED"),
            ("php", "8.2.30 LTS", "UNRESOLVED"),
            # Formas que el estandar no escribe: no se adivinan.
            ("cib-seven", "1.1.0CE", "UNRESOLVED"),
            ("oracle", "19C", "UNRESOLVED"),
            ("cib-seven", "1.1.0 ce", "UNRESOLVED"),
            ("jws", "6.0 sp1", "UNRESOLVED"),
            # Entre parentesis el catalogo escribe solo LTS y LTR; una edicion o un service pack
            # entre parentesis no se adivina (ratificado el 2026-09-22).
            ("cib-seven", "1.1.0 (CE)", "UNRESOLVED"),
            ("cib-seven", "1.1.0(CE)", "UNRESOLVED"),
            ("jws", "6.0 (SP1)", "UNRESOLVED"),
            ("jws", "6.0(SP1)", "UNRESOLVED"),
            ("angular", "19.2.18(LTS)", "HOMOLOGATED"),
            # La rama primero: fuera de toda rama listada, el calificativo no cambia nada
            # (ratificado el 2026-09-22). Mismo estado que sin calificativo.
            ("php", "7.4.0 LTS", "NOT_HOMOLOGATED"),
            ("php", "9.0.0 LTS", "ASI_EVALUATION_REQUIRED"),
            ("jws", "5.0 LTS", "NOT_HOMOLOGATED"),
            ("cib-seven", "0.9.0 LTS", "NOT_HOMOLOGATED"),
            ("cib-seven", "3.0.0 LTS", "ASI_EVALUATION_REQUIRED"),
            ("angular", "17.2.13 (LTR)", "NOT_HOMOLOGATED"),
            # El sufijo igual no salta la rama.
            ("oracle", "21c", "ASI_EVALUATION_REQUIRED"),
            ("oracle", "18c", "NOT_HOMOLOGATED"),
            # Uno que la tecnologia usa no cambia el artefacto en ninguna comparacion
            # (ratificado el 2026-09-22): homologadas sin calificativo, declaradas con LTS.
            ("dotnet", "9.0.12 (LTS)", "HOMOLOGATED"),
            ("moodle", "5.1.1 (LTS)", "HOMOLOGATED"),
            ("dotnet", "9.0.10 (LTS)", "DEPRECATED_TOLERATED"),
            ("dotnet", "9.0.11 (LTS)", "DEPRECATED_TOLERATED")):
        t.igual("E-17 %s %s" % (tec, declarada), esperado, _version(tec, declarada)["state"])

    # El orden de evaluacion (ratificado el 2026-09-22): forma, calificativo contra la rama,
    # numero.
    # Paso 1 — la forma, dentro y fuera de toda rama listada.
    for tec, declarada in (
            ("php", "7.4.0 lts"), ("php", "9.0.0 lts"),             # fuera de rama
            ("php", "8.2.30 lts"),                                  # dentro
            # dos espacios o tabulador, en formas que leidas homologarian
            ("cib-seven", "1.1.0  CE"), ("cib-seven", "1.1.0\tCE"), ("jws", "6.0  SP1"),
            ("angular", "19.2.18 \t(LTS)"), ("php", "8.2.30  LTS"),
            ("php", "7.4.0\tLTS"),                                  # tabulador, fuera de rama
            ("php", "8.2.30 "), ("php", " 8.2.30"), ("php", "8.2.30\t"),
            ("angular", "19.2.18  (LTS)"), ("angular", "19.2.18\t(LTS)"),
            ("angular", "19.2.18 (LTS"), ("cib-seven", "1.1.0 CE)"),  # parentesis suelto
            ("jws", "6.0 SP01"), ("jws", "5.0 SP01"),
            ("cib-seven", "0.9.0 (CE)")):
        t.igual("E-17 forma no canonica %r de %s" % (declarada, tec), "UNRESOLVED",
                _version(tec, declarada)["state"])

    # Paso 2 — el calificativo contra una rama listada, tambien POR DEBAJO del piso. Sin el
    # calificativo, esas mismas versiones son NOT_HOMOLOGATED: lo cambia el paso 2.
    for tec, numero, calificativo in (("php", "8.2.28", " LTS"),
                                      ("angular", "19.2.14", " (LTR)"),
                                      ("dotnet", "8.0.19", " (LTR)")):
        t.igual("E-17 %s %s sin calificativo" % (tec, numero), "NOT_HOMOLOGATED",
                _version(tec, numero)["state"])
        t.igual("E-17 %s %s%s objeta antes del numero" % (tec, numero, calificativo),
                "UNRESOLVED", _version(tec, numero + calificativo)["state"])
    for tec, declarada in (("cib-seven", "1.1 LTS"),
                           # de otro tipo que el del catalogo para esa rama
                           ("jws", "6.0 CE"), ("jws", "6.1 CE"), ("jws", "6.1 SP1"),
                           ("cib-seven", "1.1.0 SP1"), ("cib-seven", "1.1.0 X1"),
                           ("cib-seven", "1.1.0 LTS1")):
        t.igual("E-17 %s %s de otro tipo en rama listada" % (tec, declarada), "UNRESOLVED",
                _version(tec, declarada)["state"])
    # Coherencia de jws: 6.0 lista `SP1` y 6.1 no lista nada; `CE` es de otro tipo en las dos.
    t.igual("E-17 jws 6.0 CE y 6.1 CE dan lo mismo", _version("jws", "6.0 CE")["state"],
            _version("jws", "6.1 CE")["state"])

    # Paso 3 — un calificativo canonico fuera de toda rama no cambia nada, aunque sea de otro
    # tipo.
    for tec, declarada, esperado in (("cib-seven", "3.0.0 X1", "ASI_EVALUATION_REQUIRED"),
                                     ("jws", "5.0 CE", "NOT_HOMOLOGATED"),
                                     ("jws", "7.0 SP1", "ASI_EVALUATION_REQUIRED")):
        t.igual("E-17 %s %s fuera de rama" % (tec, declarada), esperado,
                _version(tec, declarada)["state"])

    for tec, fuera in (("php", "7.4.0"), ("php", "9.0.0"), ("cib-seven", "3.0.0"),
                       ("angular", "17.2.13")):
        t.igual("E-17 %s %s sin calificativo da lo mismo" % (tec, fuera),
                _version(tec, fuera + " LTS")["state"], _version(tec, fuera)["state"])

    # Una deprecada declarada con el calificativo de soporte que su tecnologia usa se tolera igual
    # que sin el (ratificado por la autora de la spec el 2026-09-22).
    for tec, deprecada in (("angular", "19.2.15"), ("django", "5.2.6"), ("dotnet", "8.0.20")):
        t.igual("E-17 %s %s es deprecada" % (tec, deprecada), "DEPRECATED_TOLERATED",
                _version(tec, deprecada)["state"])
        t.igual("E-17 %s %s (LTS) tambien" % (tec, deprecada), "DEPRECATED_TOLERATED",
                _version(tec, deprecada + " (LTS)")["state"])

    # Y por el camino de la deprecada, un calificativo de soporte que la tecnologia NO usa no se
    # descarta: PHP no usa LTS, y ni Angular, ni .NET, ni Moodle usan LTR.
    for tec, deprecada, ajeno in (("php", "8.2.29", " LTS"), ("angular", "19.2.15", " (LTR)"),
                                  ("dotnet", "8.0.20", " (LTR)"), ("moodle", "5.0", " (LTR)")):
        t.igual("E-17 %s %s es deprecada" % (tec, deprecada), "DEPRECATED_TOLERATED",
                _version(tec, deprecada)["state"])
        t.igual("E-17 %s %s%s no se tolera a ciegas" % (tec, deprecada, ajeno), "UNRESOLVED",
                _version(tec, deprecada + ajeno)["state"])
    r = _version("cib-seven", "1.1.0 EE")
    t.igual("E-17 la edicion rechazada conserva la homologada", "CE", r.get("qualifier"))
    t.igual("E-17 y la declarada", "EE", r.get("declaredQualifier"))


# -- E-18 y E-19 — la cadena de herramientas -----------------------------------

def test_e18_una_auxiliar_declarada(t):
    """E-18 (G1-12) — TOOLCHAIN_AUXILIARY_REVIEW: no se homologa individualmente."""
    r = HOMOLOGACION.evaluar({"technology": "webpack", "role": "TOOLCHAIN_AUXILIARY"},
                             _catalogo())
    t.igual("E-18 el estado", "TOOLCHAIN_AUXILIARY_REVIEW", r["state"])
    t.verdadero("E-18 igual pide revision", len(r.get("requirements") or []) > 0)


def test_e19_una_desconocida_no_se_vuelve_auxiliar(t):
    """E-19 (G1-13) — no se clasifica como auxiliar en silencio."""
    r = HOMOLOGACION.evaluar({"technology": "webpack"}, _catalogo())
    t.igual("E-19 el estado", "ASI_EVALUATION_REQUIRED", r["state"])
    t.verdadero("E-19 no la dio por auxiliar", r["state"] != "TOOLCHAIN_AUXILIARY_REVIEW")


# -- E-20 a E-23 — el registro de controles ------------------------------------

def test_e20_el_registro_declara_los_cuatro(t):
    """E-20 — los cuatro controles de G1, con su tipo y su regla."""
    doc = c_controles.cargar()
    t.vacio("E-20 valida contra su schema", c_controles.validar_schema(doc))
    de_g1 = c_controles.de_la_regla("G1", doc)
    t.igual("E-20 son cuatro", 4, len(de_g1))
    t.igual("E-20 dos policies", 2, len([c for c in de_g1 if c["type"] == "POLICY"]))
    t.igual("E-20 dos checks", 2, len([c for c in de_g1 if c["type"] == "CHECK"]))
    for c in de_g1:
        t.igual("E-20 %s conserva la traza" % c["id"], "G1", c["source"]["rule"])
        t.igual("E-20 %s la version" % c["id"], "6.3", c["source"]["version"])


def test_e21_declarado_sin_archivo_y_archivo_sin_declarar(t):
    """E-21 — el hueco se ve, y un archivo suelto no se adopta."""
    doc = copy.deepcopy(c_controles.cargar())
    doc["controls"][0]["file"] = "controles/policies/no-esta.md"
    informe = c_controles.validar(doc)
    t.igual("E-21 declarado sin archivo", "CONTROL_FILE_MISSING",
            informe["controls"][doc["controls"][0]["id"]])

    # Un archivo que el registro no declara: se ve y no se adopta.
    doc = copy.deepcopy(c_controles.cargar())
    doc["controls"] = [c for c in doc["controls"] if c["id"] != "technology-homologation"]
    sueltos = {s["file"] for s in c_controles.descubrir_no_declarados(doc)}
    t.verdadero("E-21 el archivo aparece",
                "controles/checks/technology-homologation.py" in sueltos)
    t.igual("E-21 y no esta instalado", None,
            c_controles.control("technology-homologation", doc))


def test_e22_g1_deja_de_faltar_sin_tocar_la_matriz(t):
    """E-22 — los cuatro salen de la lista, la matriz no cambio, y los demas siguen."""
    de_g1 = ("approved-technology-required", "homologated-version-required",
             "technology-homologation", "technology-version-compliance")
    resolucion = c_matriz.resolver({})
    # La premisa: G1 aplica siempre, asi que sus cuatro estan pedidos. Sin esto, "no falta"
    # se cumpliria porque nadie lo pidio.
    pedidos = set(resolucion["declaredPolicies"]) | set(resolucion["declaredChecks"])
    faltan = {f["id"] for f in c_matriz.controles_no_instalados(resolucion)}
    for cid in de_g1:
        t.verdadero("E-22 %s esta pedido" % cid, cid in pedidos)
        t.verdadero("E-22 %s ya no falta" % cid, cid not in faltan)

    # La fila de G1 no cambio una linea: los mismos ids, literales.
    g1 = c_matriz.regla("G1")
    t.igual("E-22 G1 sigue declarando sus policies",
            ["approved-technology-required", "homologated-version-required"], g1["policies"])
    t.igual("E-22 y sus checks",
            ["technology-homologation", "technology-version-compliance"], g1["checks"])

    # Lo que falta, calculado aparte: todo lo que la matriz declara, leido del JSON, menos lo que
    # el registro declara Y tiene su archivo en disco. Sin pasar por `controles` ni por `matriz`.
    harness = RAIZ / "harnesses" / "desarrollo"
    matriz_json = json.loads((harness / "reglas" / "es0901-7.1-normative-matrix.json")
                             .read_text(encoding="utf-8-sig"))
    registro = json.loads((harness / "reglas" / "control-registry.json")
                          .read_text(encoding="utf-8-sig"))
    declarados = {"POLICY": set(), "CHECK": set(), "REVIEW": set()}
    for fila in matriz_json["rules"]:
        declarados["POLICY"].update(fila.get("policies") or [])
        declarados["CHECK"].update(fila.get("checks") or [])
        declarados["REVIEW"].update(fila.get("reviews") or [])
    # La matriz entera sigue declarando lo mismo: 36 policies y 34 checks desde que se clasifico,
    # y las 2 reviews que agrego G2.
    t.igual("E-22 la matriz sigue declarando 36 policies, 34 checks y 2 reviews",
            {"POLICY": 36, "CHECK": 34, "REVIEW": 2},
            {k: len(v) for k, v in declarados.items()})
    en_disco = {(c["type"], c["id"]) for c in registro["controls"]
                if (harness / c["file"]).is_file()}
    esperado = sorted(cid for tipo, ids in declarados.items() for cid in ids
                      if (tipo, cid) not in en_disco)
    toda = {"declaredPolicies": sorted(declarados["POLICY"]),
            "declaredChecks": sorted(declarados["CHECK"]),
            "declaredReviews": sorted(declarados["REVIEW"])}
    reportados = sorted(f["id"] for f in c_matriz.controles_no_instalados(toda))
    t.igual("E-22 faltan exactamente los que la matriz declara y el disco no tiene",
            esperado, reportados)
    t.verdadero("E-22 y todavia faltan", len(reportados) > 0)
    for cid in de_g1:
        t.verdadero("E-22 %s no esta entre los que faltan de la matriz entera" % cid,
                    cid not in reportados)


def test_e23_los_checks_normativos_no_son_los_del_hook(t):
    """E-23 — otra capa, otro registro: no entran a roster.json ni al runner del hook."""
    de_g1 = ("technology-homologation", "technology-version-compliance")
    del_roster = {c["name"] for c in c_roster.cargar().get("checks", [])}
    for cid in de_g1:
        t.verdadero("E-23 %s no esta en el roster" % cid, cid not in del_roster)
    t.verdadero("E-23 el roster sigue teniendo los suyos", len(del_roster) > 0)
    t.verdadero("E-23 y el registro de controles tiene los normativos",
                len(c_controles.de_la_regla("G1")) == 4)

    # El contrato del hook. `post-tool-use.py` corre lo que hay en `<harness>/checks`, al lado
    # de `hooks/`; y ese directorio lo llena install.ps1 SOLO desde `comun/checks` y
    # `harnesses/<id>/checks`. `controles/` no es origen de ninguna copia a `checks`.
    hook = (RAIZ / "comun" / "hooks" / "post-tool-use.py").read_text(encoding="utf-8")
    t.contiene("E-23 el hook corre <harness>/checks", 'os.path.join(AQUI, "..", "checks")', hook)
    origenes = _origenes_de_checks((RAIZ / "install.ps1").read_text(encoding="utf-8-sig"))
    t.igual("E-23 install.ps1 llena checks desde comun/checks y harnesses/<id>/checks",
            ["$origen/checks", "$origenComun/checks"], origenes)

    # Lo que ese runner descubriria en un proyecto instalado, con su misma regla de descubrimiento:
    # ningun check de G1 esta ahi, y los dos existen del otro lado.
    descubiertos = set()
    for base in [RAIZ / "comun" / "checks"] + sorted((RAIZ / "harnesses").glob("*/checks")):
        for ruta in base.rglob("*.py"):
            if not ruta.name.startswith("__"):
                descubiertos.add(ruta.stem)
    t.verdadero("E-23 el runner del hook tiene checks que descubrir", len(descubiertos) > 0)
    for cid in de_g1:
        t.verdadero("E-23 %s existe como control normativo" % cid,
                    (CONTROLES / "checks" / (cid + ".py")).is_file())
        t.verdadero("E-23 %s no lo descubre el runner del hook" % cid,
                    cid not in descubiertos)

    # Y no podrian correr ahi: el contrato del hook es `verificar(evento, proyecto, config)`, el
    # normativo es `evaluar(item, ...)`.
    for nombre, modulo in (("technology-homologation", HOMOLOGACION),
                           ("technology-version-compliance", VERSIONES)):
        t.verdadero("E-23 %s no tiene el contrato del hook" % nombre,
                    not hasattr(modulo, "verificar"))
        t.verdadero("E-23 %s tiene el suyo" % nombre, callable(getattr(modulo, "evaluar", None)))


def _origenes_de_checks(texto):
    """El origen de cada `Copy-Arbol` de install.ps1 cuyo destino es `checks` del harness."""
    patron = (r"Copy-Arbol\s+\(Join-Path\s+(\$\w+)\s+'([^']+)'\)\s+"
              r"\(Join-Path\s+\$dirHarness\s+(?:'checks'|\"checks\\\$id\")\)")
    return sorted({"%s/%s" % (m.group(1), m.group(2)) for m in re.finditer(patron, texto)})


# -- E-24 a E-26 — limites, trazabilidad y determinismo ------------------------

def test_e24_g1_no_verifica_nada_de_p1(t):
    """E-24 (G1-18) — ni framework obligatorio, ni vanilla, ni gestor de paquetes."""
    de_g1 = {c["id"] for c in c_controles.de_la_regla("G1")}
    p1 = c_matriz.regla("P1")
    for cid in p1["policies"] + p1["checks"]:
        t.verdadero("E-24 %s no es de G1" % cid, cid not in de_g1)
    t.verdadero("E-24 P1 tiene los suyos", len(p1["policies"]) > 0)


def test_e25_todo_resultado_conserva_la_traza(t):
    """E-25 (G1-19) — ES0901 / 6.3 / 7.1 / G1."""
    resultados = [
        HOMOLOGACION.evaluar({"technology": "php"}, _catalogo()),
        HOMOLOGACION.evaluar({"technology": "no-existe"}, _catalogo()),
        _version("php", "8.2.30"),
        _version("php", "8.1.0"),
        VERSIONES.bloqueo_por_antiguedad({"technology": "php"}),
    ]
    for r in resultados:
        t.igual("E-25 el estandar", "ES0901", r["source"]["standard"])
        t.igual("E-25 la version", "6.3", r["source"]["version"])
        t.igual("E-25 la seccion", "7.1", r["source"]["section"])
        t.igual("E-25 la regla", "G1", r["source"]["rule"])


def test_e26_mismo_inventario_mismo_resultado(t):
    """E-26 (G1-20) — determinista."""
    inventario = [{"technology": "php", "version": "8.2.30"},
                  {"technology": "angular", "version": "19.2.18"},
                  {"technology": "cobol-del-95", "version": "1.0"},
                  {"technology": "webpack", "role": "TOOLCHAIN_AUXILIARY"}]
    doc = _catalogo()
    uno = HOMOLOGACION.evaluar_inventario(inventario, doc)
    dos = HOMOLOGACION.evaluar_inventario(copy.deepcopy(inventario), doc)
    t.igual("E-26 mismos estados", [x["state"] for x in uno], [x["state"] for x in dos])
    t.igual("E-26 y los cuatro distintos", 4, len(uno))
    t.igual("E-26 el orden se conserva",
            ["php", "angular", "cobol-del-95", "webpack"], [x["technology"] for x in uno])
