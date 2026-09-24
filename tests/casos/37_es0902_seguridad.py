# ES0902 v6.2: un segundo estandar sobre el mismo runtime, sin que ninguno pise al otro.
#
# Escenarios E-01 a E-71 de docs/cambios/es0902-linea-base-de-seguridad/spec.md. Entre
# parentesis, el S-nn del pedido de instalacion.
#
# 🔴 Nada de esto homologa nada. Lo que se verifica es la FRONTERA: que `G1` no identifique una
# regla, que un productor interno no pueda emitir `APPROVED`, que la configuracion local de un
# proyecto no exima de una regla de seguridad, que satisfacer el umbral de G2 no mueva el estado
# oficial, y que dos estandares que piden lo mismo no se aprueben el uno al otro.
#
# 🔴 Dos escenarios son PRODUCTOS y no listas: E-26 (todos los productores internos x todos los
# estados oficiales) y E-46 (las diez reglas Vu, cada una con su propia evidencia). Si alguno se
# degradara a un caso, el resto seguiria en verde y la frontera dejaria de ser una frontera.
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
REGLAS = RAIZ / "harnesses" / "desarrollo" / "reglas"
SCHEMAS = RAIZ / "comun" / "schemas"

sys.path.insert(0, str(BIN))
from orquestacion import seguridad                  # noqa: E402
from orquestacion import evaluacion                 # noqa: E402
from orquestacion import cruzada                    # noqa: E402
from orquestacion import controles as c_controles   # noqa: E402
from orquestacion import matriz as c_matriz         # noqa: E402
from orquestacion import senales as c_senales       # noqa: E402
from orquestacion import normativa as c_normativa   # noqa: E402
from orquestacion import roster as c_roster         # noqa: E402
from orquestacion import registro_agentes as c_reg  # noqa: E402
import rutas as rutas_mod                           # noqa: E402

MATRIZ = seguridad.cargar()
MAPA = cruzada.cargar()
ENTREGABLES = evaluacion.cargar_entregables()
REGISTRO = c_controles.cargar()

# El inventario del estandar, escrito aca a mano a proposito: si saliera del archivo, el archivo
# se validaria contra si mismo y una regla de menos pasaria sin que nadie se entere.
LAS_21 = ("O1", "O2", "C1", "C2", "C3",
          "Vu1", "Vu2", "Vu3", "Vu4", "Vu5", "Vu6", "Vu7", "Vu8", "Vu9", "Vu10",
          "Ve1", "Ve2", "G1", "G2", "G3", "G4")

# Los ocho estados globales que el paquete de instalacion exige, con ese nombre exacto.
LOS_8_ESTADOS = ("SECURITY_NORMATIVE_OVERRIDE_UNRESOLVED",
                 "CROSS_STANDARD_INTERPRETATION_REQUIRED",
                 "CROSS_STANDARD_CONTROL_BINDING_REQUIRED",
                 "OFFICIAL_STATUS_UNRESOLVED",
                 "WAF_FORM_CONTEXT_REQUIRED",
                 "VULNERABILITY_RISK_MAPPING_UNRESOLVED",
                 "SECURITY_DELIVERABLES_INCOMPLETE",
                 "EXTERNAL_NORMATIVE_CONTEXT_REQUIRED")


def _todas_las_senales(**cambios):
    """Todas las senales de ES0902 en TRUE, salvo lo que se pise. Aplicable es el caso que importa.

    Una regla que no aplica no tiene resultado, y un test que la deja sin aplicar prueba que el
    sistema no falla donde no puede fallar.
    """
    valores = {s: True for s in seguridad.senales_declaradas(MATRIZ)}
    valores.update(cambios)
    return valores


def _controles_de(rid):
    """Los ids de control que la regla declara. Salen de la MATRIZ, no de una lista de acá."""
    return [c["id"] for c in seguridad.controles_de(rid, MATRIZ)]


def _todos_en_pass(rid, **extra):
    """La evidencia que pone a una regla en PASS por la via generica. Para el caso de control."""
    ev = {"controlResults": {cid: {"result": "PASS", "evidence": ["acta-%s" % cid]}
                             for cid in _controles_de(rid)}}
    ev.update(extra)
    return ev


MAPEO_AUTORITATIVO = {"authoritative": True, "evidence": ["acta-asi"],
                      "map": {"low": "LOW", "medium": "MEDIUM", "high": "HIGH",
                              "critical": "CRITICAL"}}


def _hallazgos(bajos=0, mayores=0):
    salida = [{"id": "L%d" % i, "scannerSeverity": "low"} for i in range(bajos)]
    salida += [{"id": "H%d" % i, "scannerSeverity": "high"} for i in range(mayores)]
    return salida


# -- Identidad e inventario ----------------------------------------------------

def test_e01_la_identidad_del_estandar(t):
    """E-01 (S-01) — ES0902 6.2, 2025-08, 21 reglas. Otra version no se usa a medias."""
    t.igual("E-01 el estandar", "ES0902", MATRIZ["standard"])
    t.igual("E-01 la version", "6.2", MATRIZ["version"])
    t.igual("E-01 la fecha de fuente", "2025-08", MATRIZ["sourceDate"])
    t.igual("E-01 la cantidad declarada", 21, MATRIZ["expectedRuleCount"])
    t.igual("E-01 y la cantidad real", 21, len(MATRIZ["rules"]))

    # 🔴 Las reglas cambian entre versiones: una clasificacion vieja sobre un estandar nuevo
    # miente sin avisar, asi que se falla cerrado y no se usa media matriz.
    for campo, valor in (("standard", "ES0901"), ("version", "6.1"), ("expectedRuleCount", 20)):
        otra = dict(MATRIZ)
        otra[campo] = valor
        estado = seguridad.controlar_version(otra)
        t.contiene("E-01 %s=%r se rechaza" % (campo, valor),
                   "NORMATIVE_STANDARD_VERSION_MISMATCH", estado)
        veredicto, errores = seguridad.validar(otra)
        t.igual("E-01 %s=%r invalida la matriz" % (campo, valor),
                "NORMATIVE_MATRIX_INVALID", veredicto)


def test_e02_el_inventario_exacto_dice_cual(t):
    """E-02 (S-01) — falta, repetida o de mas: se reporta el ID, no un conteo."""
    ids = [r["id"] for r in MATRIZ["rules"]]
    t.igual("E-02 el inventario es el del estandar", sorted(LAS_21), sorted(ids))
    t.igual("E-02 sin repetidas", len(LAS_21), len(set(ids)))
    veredicto, errores = seguridad.validar(MATRIZ)
    t.igual("E-02 la matriz provista es valida", "NORMATIVE_MATRIX_VALID", veredicto)
    t.vacio("E-02 sin errores", errores)

    # 📌 Un conteo que no cierra obliga a comparar dos listas a mano. El id, no.
    faltante = dict(MATRIZ, rules=[r for r in MATRIZ["rules"] if r["id"] != "Vu7"])
    veredicto, errores = seguridad.validar(faltante)
    t.igual("E-02 una que falta invalida", "NORMATIVE_MATRIX_INVALID", veredicto)
    t.contiene("E-02 y se dice cual falta", "Vu7", " | ".join(errores))

    repetida = dict(MATRIZ, rules=list(MATRIZ["rules"]) + [dict(MATRIZ["rules"][0])])
    veredicto, errores = seguridad.validar(repetida)
    t.igual("E-02 una repetida invalida", "NORMATIVE_MATRIX_INVALID", veredicto)
    t.contiene("E-02 y se dice cual se repite", MATRIZ["rules"][0]["id"], " | ".join(errores))

    intrusa = dict(MATRIZ["rules"][0], id="Zz9", ruleKey="ES0902.Zz9")
    sobrante = dict(MATRIZ, rules=list(MATRIZ["rules"]) + [intrusa])
    veredicto, errores = seguridad.validar(sobrante)
    t.igual("E-02 una de mas invalida", "NORMATIVE_MATRIX_INVALID", veredicto)
    t.contiene("E-02 y se dice cual sobra", "Zz9", " | ".join(errores))


def test_e03_la_clave_compuesta_se_declara_y_se_compara(t):
    """E-03 (S-02) — `ruleKey` sale del archivo y se controla contra `ES0902.<id>`."""
    for r in MATRIZ["rules"]:
        t.igual("E-03 %s declara su clave" % r["id"], "ES0902.%s" % r["id"], r["ruleKey"])
        t.igual("E-03 y `clave` la deriva igual", r["ruleKey"], seguridad.clave(r["id"]))

    # 🔴 Derivarla al vuelo haria invisible una clave equivocada en el archivo.
    torcida = dict(MATRIZ, rules=[dict(r) for r in MATRIZ["rules"]])
    torcida["rules"][3]["ruleKey"] = "ES0901.C2"
    veredicto, errores = seguridad.validar(torcida)
    t.igual("E-03 una clave torcida invalida la matriz", "NORMATIVE_MATRIX_INVALID", veredicto)
    t.contiene("E-03 con el estado que le corresponde",
               "NORMATIVE_RULE_KEY_MISMATCH", " | ".join(errores))


def test_e04_g1_de_cada_estandar_no_son_la_misma_regla(t):
    """E-04 (S-02) — resolver una no devuelve la otra, y ninguna pisa a la otra."""
    g1_902 = seguridad.regla("G1", MATRIZ)
    g1_901 = c_matriz.regla("G1")
    t.igual("E-04 la de ES0902 es de aceptacion", "ACCEPTANCE", g1_902["category"])
    t.verdadero("E-04 y la de ES0901 no tiene esa forma", "ruleKey" not in g1_901)
    t.verdadero("E-04 no declaran los mismos controles",
                sorted(g1_902.get("policies") or []) != sorted(g1_901.get("policies") or []))

    t.igual("E-04 la clave de la de ES0902", "ES0902.G1", seguridad.clave("G1"))
    t.igual("E-04 y la traza conserva las dos formas", ("G1", "ES0902.G1"),
            (seguridad.trazabilidad("G1", MATRIZ)["rule"],
             seguridad.trazabilidad("G1", MATRIZ)["ruleKey"]))

    # 📌 Y por clave compuesta se llega a la misma regla que por id local: son la misma fila.
    t.igual("E-04 por clave compuesta se llega a la misma", g1_902,
            seguridad.regla("ES0902.G1", MATRIZ))

    # ES0902 tiene cuatro G y ES0901 tiene dos: el espacio de ids no coincide ni en tamano.
    ges_902 = sorted(r["id"] for r in MATRIZ["rules"] if r["id"].startswith("G"))
    t.igual("E-04 ES0902 tiene cuatro G", ["G1", "G2", "G3", "G4"], ges_902)
    ges_901 = sorted(r["id"] for r in c_matriz.reglas() if r["id"].startswith("G"))
    t.igual("E-04 y ES0901 tiene dos", ["G1", "G2"], ges_901)


def test_e05_una_regla_que_no_esta_no_se_resuelve(t):
    """E-05 (S-03) — `NORMATIVE_RULE_NOT_FOUND`, y no queda media matriz cargada."""
    for desconocida in ("Vu11", "D5", "ES0901.G1", "", None, "Zz1"):
        try:
            seguridad.regla(desconocida, MATRIZ)
            t.verdadero("E-05 %r se rechaza" % desconocida, False)
        except seguridad.SeguridadInvalida as e:
            t.contiene("E-05 %r se rechaza" % desconocida, "NORMATIVE_RULE_NOT_FOUND", str(e))

    # 📌 `D5` es de ES0901 y ES0902 no la tiene: que exista en el otro estandar no la trae.
    t.verdadero("E-05 D5 existe en ES0901", bool(c_matriz.regla("D5")))


def test_e06_es0902_no_entra_en_la_matriz_de_es0901(t):
    """E-06 (S-03) — el archivo de ES0901 sigue con su inventario y sin mencionar ES0902."""
    doc901 = c_matriz.cargar()
    t.igual("E-06 ES0901 sigue con 24 filas", 24, len(doc901["rules"]))
    t.igual("E-06 y con su inventario", sorted(c_matriz.INVENTARIO),
            sorted(r["id"] for r in doc901["rules"]))
    t.no_contiene("E-06 y no menciona ES0902", "ES0902", json.dumps(doc901, ensure_ascii=False))
    t.igual("E-06 los archivos son dos", 2,
            len({c_matriz.ARCHIVO, seguridad.ARCHIVO}))
    # 📌 Acá vivía un `or True` que dejaba la aserción verde pasara lo que pasara. Lo encontró el
    # refutador: no cambiaba el veredicto —las otras aserciones del test sostienen la proposición—
    # pero era peso muerto que inflaba el conteo y engañaba a quien lo leyera.
    # El solapamiento de ids es REAL — C1, C2, C3, G1, G2 estan en los dos — y es exactamente
    # por eso que la clave tiene que ser compuesta.
    t.igual("E-06 los ids que se solapan", ["C1", "C2", "C3", "G1", "G2"],
            sorted(set(LAS_21) & set(c_matriz.INVENTARIO)))


# -- Runtime compartido --------------------------------------------------------

def test_e07_los_dos_estandares_devuelven_el_mismo_contrato(t):
    """E-07 (S-46) — quien sabe leer un bloque normativo sabe leer los dos."""
    bloque902 = seguridad.resolver({})
    bloque901 = c_matriz.resolver({})
    t.igual("E-07 las mismas claves de primer nivel",
            sorted(bloque901), sorted(bloque902))
    for clave in ("id", "version", "section"):
        t.verdadero("E-07 `standard` de ES0902 trae `%s`" % clave, clave in bloque902["standard"])
    t.igual("E-07 y su id", "ES0902", bloque902["standard"]["id"])
    t.igual("E-07 lo propio de ES0902 viaja adentro de `standard`", "2025-08",
            bloque902["standard"]["sourceDate"])
    for campo in ("applicableRules", "notApplicableRules", "unresolvedRules",
                  "declaredPolicies", "declaredChecks", "declaredReviews"):
        t.igual("E-07 `%s` es una lista en los dos" % campo, (list, list),
                (type(bloque901[campo]), type(bloque902[campo])))

    # 🔴 Y la regla que los dos comparten: **lo que no esta, no se deduce**. Sin ninguna senal,
    # las CONDITIONAL quedan APPLICABILITY_UNRESOLVED con el nombre de la que falta al lado, y
    # NINGUNA cae en NOT_APPLICABLE. Convertir lo ausente en "no aplica" hace desaparecer la
    # regla del reporte, y una regla que desaparece no se vuelve a buscar.
    condicionales = [r["id"] for r in MATRIZ["rules"]
                     if r["applicability"]["mode"] == "CONDITIONAL"]
    t.igual("E-07 quince reglas condicionales", 15, len(condicionales))
    t.vacio("E-07 sin senales ninguna es NOT_APPLICABLE", bloque902["notApplicableRules"])
    t.igual("E-07 y las quince quedan sin resolver", sorted(condicionales),
            sorted(u["rule"] for u in bloque902["unresolvedRules"]))
    for u in bloque902["unresolvedRules"]:
        t.igual("E-07 %s con el motivo" % u["rule"], "APPLICABILITY_UNRESOLVED", u["reason"])
        t.verdadero("E-07 %s y la senal que falta" % u["rule"], bool(u["missingSignals"]))
    # FALSE explicito si es NOT_APPLICABLE: la diferencia entre "no" y "no se sabe" es el punto.
    en_falso = seguridad.resolver({s: False for s in seguridad.senales_declaradas(MATRIZ)})
    t.igual("E-07 con las senales en FALSE si son no aplicables", sorted(condicionales),
            sorted(en_falso["notApplicableRules"]))
    t.vacio("E-07 y ninguna queda sin resolver", en_falso["unresolvedRules"])


def test_e08_el_bloque_viejo_conserva_su_forma(t):
    """E-08 (S-46) — `standards` se suma al lado; nada de lo que ya se leia cambia de tipo."""
    bloque = c_normativa.resolucion({})
    for campo in ("standard", "applicableRules", "notApplicableRules", "unresolvedRules",
                  "declaredPolicies", "declaredChecks", "evidence", "signals"):
        t.verdadero("E-08 sigue estando `%s`" % campo, campo in bloque)
    t.igual("E-08 `standard` sigue siendo el de ES0901", "ES0901", bloque["standard"]["id"])
    t.igual("E-08 y trae su seccion", "7.1", bloque["standard"]["section"])
    t.igual("E-08 `applicableRules` sigue siendo lista", list, type(bloque["applicableRules"]))

    t.verdadero("E-08 y ahora hay `standards`", "standards" in bloque)
    t.igual("E-08 con los dos estandares", ["ES0901", "ES0902"], sorted(bloque["standards"]))
    t.igual("E-08 lo de arriba es lo mismo que `standards.ES0901`",
            bloque["standards"]["ES0901"]["applicableRules"], bloque["applicableRules"])

    # 🔴 Viaja a un plan en JSON: un diccionario que se apunta a si mismo no serializa.
    t.verdadero("E-08 el bloque entero serializa", bool(json.dumps(bloque)))
    t.verdadero("E-08 y `standards.ES0901` no se lleva `standards` adentro",
                "standards" not in bloque["standards"]["ES0901"])


def test_e09_toda_fila_conserva_su_traza(t):
    """E-09 (S-47) — estandar, version y regla en cada resultado. Ninguna la pierde."""
    senales = _todas_las_senales()
    for r in seguridad.resultados({}, senales, MATRIZ):
        t.igual("E-09 %s trae su regla" % r["rule"], r["rule"], r["source"]["rule"])
        t.igual("E-09 %s trae el estandar" % r["rule"], "ES0902", r["source"]["standard"])
        t.igual("E-09 %s trae la version" % r["rule"], "6.2", r["source"]["version"])
        t.igual("E-09 %s trae su clave compuesta" % r["rule"],
                "ES0902.%s" % r["rule"], r["ruleKey"])
    t.igual("E-09 son las 21", 21, len(seguridad.resultados({}, senales, MATRIZ)))

    # Y las que quedan sin resolver por aplicabilidad tambien la llevan.
    sin_resolver = seguridad.resolver({})["unresolvedRules"]
    for u in sin_resolver:
        t.igual("E-09 %s sin resolver trae su clave" % u["rule"],
                "ES0902.%s" % u["rule"], u["ruleKey"])


def test_e10_las_senales_de_es0902_quedan_declaradas(t):
    """E-10 (S-03) — quince senales, y las de ES0901 siguen donde estaban."""
    del902 = seguridad.senales_declaradas(MATRIZ)
    t.igual("E-10 ES0902 declara quince senales", 15, len(del902))
    declaradas = c_senales.declaradas()
    for s in sorted(del902):
        t.verdadero("E-10 `%s` esta declarada" % s, s in declaradas)
        senal = {"signalId": s, "value": "TRUE",
                 "evidence": [{"source": "TASK_CONTEXT", "supports": "TRUE",
                               "reference": "ficha"}],
                 "producer": {"kind": "DETERMINISTIC", "id": "prueba"}}
        r = c_senales.resolver_una(senal)
        t.no_contiene("E-10 `%s` no sale SIGNAL_NOT_DECLARED" % s,
                      "SIGNAL_NOT_DECLARED", repr(r["states"]))

    del901 = {s for r in c_matriz.reglas()
              for s in ((r.get("applicability") or {}).get("signals") or [])}
    t.igual("E-10 ES0901 sigue con catorce", 14, len(del901))
    for s in sorted(del901):
        t.verdadero("E-10 la de ES0901 `%s` sigue declarada" % s, s in declaradas)
    t.igual("E-10 y el total es la union", len(del901 | del902), len(declaradas))
    t.igual("E-10 la unica compartida", ["authenticationPresent"], sorted(del901 & del902))
    t.igual("E-10 y `reglas_de` la atribuye a las dos", ["D2", "ES0902.C1"],
            c_senales.reglas_de("authenticationPresent"))


def test_e11_los_agentes_existen_en_el_registro(t):
    """E-11 — la matriz no crea agentes: uno que no este es NORMATIVE_AGENT_REFERENCE_INVALID."""
    declarados = {a["id"] for a in c_reg.cargar()["agents"]}
    nombrados = sorted({a for r in MATRIZ["rules"] for a in r["primaryAgents"]})
    t.igual("E-11 la matriz nombra seis agentes", 6, len(nombrados))
    for aid in nombrados:
        t.verdadero("E-11 `%s` esta en el registro" % aid, aid in declarados)
    t.vacio("E-11 sin errores de referencia", seguridad.validar_referencias(MATRIZ))

    inventado = dict(MATRIZ, rules=[dict(r) for r in MATRIZ["rules"]])
    inventado["rules"][0] = dict(inventado["rules"][0], primaryAgents=["dev-no-existe"])
    errores = seguridad.validar_referencias(inventado)
    t.igual("E-11 un agente inventado da un error", 1, len(errores))
    t.contiene("E-11 con su estado", "NORMATIVE_AGENT_REFERENCE_INVALID", errores[0])
    t.contiene("E-11 y con su nombre", "dev-no-existe", errores[0])
    t.verdadero("E-11 y no se crea", "dev-no-existe" not in declarados)


# -- El registro de controles, multi-fuente ------------------------------------

def test_e12_un_control_conserva_todas_sus_fuentes(t):
    """E-12 (S-04) — varias fuentes normativas, todas enteras."""
    compartidos = cruzada.controles_compartidos(MAPA)
    t.igual("E-12 el mapa declara seis controles compartidos", 6, len(compartidos))
    for cid, claves in sorted(compartidos.items()):
        control = c_controles.control(cid, REGISTRO)
        t.verdadero("E-12 `%s` esta en el registro" % cid, control is not None)
        fuentes = c_controles.fuentes_de(control)
        t.igual("E-12 `%s` declara tantas fuentes como claves" % cid, len(claves), len(fuentes))
        t.igual("E-12 `%s` y son exactamente esas" % cid, sorted(claves),
                sorted(f["ruleKey"] for f in fuentes))
        for f in fuentes:
            for campo in ("standard", "version", "rule", "ruleKey"):
                t.verdadero("E-12 `%s` conserva `%s`" % (cid, campo), bool(f.get(campo)))
            t.igual("E-12 `%s` la clave es coherente con la tupla" % cid,
                    "%s.%s" % (f["standard"], f["rule"]), f["ruleKey"])

    t.igual("E-12 los cuatro de G1 tienen tres fuentes", 4,
            len([c for c, k in compartidos.items() if len(k) == 3]))
    t.igual("E-12 y los dos de D2 tienen dos", 2,
            len([c for c, k in compartidos.items() if len(k) == 2]))


def test_e13_la_forma_vieja_sigue_valiendo(t):
    """E-13 (S-04) — `source` singular se lee como una fuente. La migracion no rompe."""
    viejo = {"id": "x", "type": "CHECK", "rule": "D1", "file": "f.py", "status": "INSTALLED",
             "source": {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "D1"}}
    fuentes = c_controles.fuentes_de(viejo)
    t.igual("E-13 una fuente", 1, len(fuentes))
    t.igual("E-13 y es la que declaro", "D1", fuentes[0]["rule"])

    # 📌 Los 36 controles que no comparten nada siguen con la forma vieja, sin tocar: 25 de
    # ES0901 y los 21 que instalaron O1, O2, C1, C2, Vu1, Vu2, Vu3, Vu4, Vu5 y Vu6, que salen de un solo estandar y no necesitan
    # la lista.
    sin_migrar = [c for c in REGISTRO["controls"] if "normativeSources" not in c]
    t.igual("E-13 cuarenta y seis controles siguen con `source` solo", 46, len(sin_migrar))
    for c in sin_migrar:
        t.igual("E-13 `%s` se lee igual" % c["id"], 1, len(c_controles.fuentes_de(c)))
    t.igual("E-13 veinticinco son de ES0901", 25,
            len([c for c in sin_migrar
                 if c_controles.fuentes_de(c)[0]["standard"] == "ES0901"]))
    t.igual("E-13 y los veintiuno de O1, O2, C1, C2, Vu1, Vu2, Vu3, Vu4, Vu5 y Vu6 son de ES0902",
            ["authentication-abuse-protection",
             "authentication-abuse-protection-required",
             "browser-close-session-termination",
             "browser-close-session-termination-required",
             "client-server-validation-parity",
             "client-validation-server-mirroring-required",
             "custom-error-message-compliance",
             "custom-error-messages-required",
             "dgsei-keycloak-provider-required",
             "gcba-it-security-normative-compliance-required",
             "gcba-it-security-normative-review",
             "gcba-security-control-authority-required",
             "oidc-keycloak-integration",
             "openid-connect-authentication-required",
             "qa-security-approval-evidence",
             "qa-security-approval-required",
             "security-control-authority-evidence",
             "sensitive-data-plaintext-transmission-prohibited",
             "sensitive-data-transport-protection",
             "session-inactivity-timeout",
             "session-inactivity-timeout-required"],
            sorted(c["id"] for c in sin_migrar
                   if c_controles.fuentes_de(c)[0]["standard"] == "ES0902"))

    informe = c_controles.validar(REGISTRO)
    t.vacio("E-13 el registro entero valida contra el schema", informe["schemaErrors"])
    t.igual("E-13 y los 52 controles siguen instalados", 52,
            len([e for e in informe["controls"].values() if e == "INSTALLED"]))

    # La lista gana cuando esta: no se suman las dos formas.
    mixto = dict(viejo, normativeSources=[{"standard": "ES0902", "version": "6.2", "rule": "C1",
                                           "ruleKey": "ES0902.C1"}])
    t.igual("E-13 con las dos formas gana la lista", ["ES0902"],
            [f["standard"] for f in c_controles.fuentes_de(mixto)])


def test_e14_un_control_compartido_se_declara_una_vez(t):
    """E-14 (S-04) — no hay un `authentication-delegation` de D2 y otro de C1."""
    ids = [c["id"] for c in REGISTRO["controls"]]
    t.igual("E-14 ningun id repetido", len(ids), len(set(ids)))
    t.igual("E-14 el registro declara 52 controles", 52, len(ids))
    for cid in sorted(cruzada.controles_compartidos(MAPA)):
        t.igual("E-14 `%s` aparece una sola vez" % cid, 1, ids.count(cid))
        t.igual("E-14 `%s` lo citan dos estandares" % cid, ["ES0901", "ES0902"],
                c_controles.estandares_de(cid, REGISTRO))

    # 📌 Y se llega al mismo control por las dos reglas, sin duplicarlo. Desde que C1 instalo
    # sus tres propios, ES0902.C1 alcanza cinco: los dos que comparte con D2 y los suyos.
    por_d2 = [c["id"] for c in c_controles.de_la_regla("D2", REGISTRO)]
    por_c1 = [c["id"] for c in c_controles.de_la_regla("ES0902.C1", REGISTRO)]
    t.igual("E-14 D2 y ES0902.C1 llegan a los mismos dos", sorted(por_d2),
            sorted(set(por_d2) & set(por_c1)))
    t.igual("E-14 y son los que el mapa nombra",
            ["authentication-delegation", "credential-entry-delegation-required"],
            sorted(set(por_d2) & set(por_c1)))
    t.igual("E-14 lo demas de C1 es suyo y no de D2",
            ["dgsei-keycloak-provider-required", "oidc-keycloak-integration",
             "openid-connect-authentication-required"], sorted(set(por_c1) - set(por_d2)))


def test_e15_el_resultado_no_se_propaga_entre_estandares(t):
    """E-15 (S-05) — se ejecuta una vez y PASS por D2 no pone en PASS a C1."""
    claves = cruzada.controles_compartidos(MAPA)["authentication-delegation"]
    anotado = cruzada.resultado_por_fuente("authentication-delegation",
                                           {"result": "PASS"}, claves, MAPA)
    t.igual("E-15 una sola ejecucion", 1, anotado["executions"])
    t.igual("E-15 anotada para las dos fuentes", ["ES0901.D2", "ES0902.C1"],
            sorted(anotado["bySource"]))
    for k, fila in anotado["bySource"].items():
        t.igual("E-15 %s ve el resultado del control" % k, "PASS", fila["controlResult"])
        t.igual("E-15 %s y NO hereda un resultado de regla" % k, None, fila["ruleResult"])

    # 🔴 Y de verdad: con C1 aplicable y el control compartido en PASS, C1 no cumple, porque
    # tiene tres policies y dos checks y solo uno de ellos esta.
    ev = {"controlResults": {"authentication-delegation": {"result": "PASS",
                                                           "evidence": ["acta-d2"]}}}
    r = seguridad.resultado("C1", ev, _todas_las_senales(), MATRIZ)
    t.igual("E-15 C1 no cumple por el PASS de D2", "UNRESOLVED", r["result"])
    t.contiene("E-15 y dice que le falta evidencia", "SECURITY_CONTROL_EVIDENCE_MISSING",
               repr(r["states"]))
    t.contiene("E-15 nombrando el control de OIDC", "oidc-keycloak-integration",
               " | ".join(r["reasons"]))


def test_e16_el_patron_de_regla_acepta_los_ids_de_es0902(t):
    """E-16 (S-04) — O1, Vu1 y Ve1 entran; un id que no es de ningun estandar no."""
    import re
    esquema = json.loads((SCHEMAS / "control-registry.schema.json").read_text(encoding="utf-8"))
    patron = esquema["properties"]["controls"]["items"]["properties"]["rule"]["pattern"]
    compilado = re.compile(patron)
    for rid in LAS_21:
        t.verdadero("E-16 `%s` de ES0902 entra" % rid, bool(compilado.match(rid)))
    for rid in c_matriz.INVENTARIO:
        t.verdadero("E-16 `%s` de ES0901 sigue entrando" % rid, bool(compilado.match(rid)))
    for rid in ("Zz1", "vu1", "1G", "Vu", "", "ES0902.G1", "G-1"):
        t.verdadero("E-16 `%s` no entra" % rid, not compilado.match(rid))

    # Y no es solo el patron: el registro real valida contra el schema real.
    t.vacio("E-16 el registro instalado valida", c_controles.validar_schema(REGISTRO))
    con_o1 = dict(REGISTRO, controls=list(REGISTRO["controls"]) + [
        {"id": "una-policy-de-es0902", "type": "POLICY", "rule": "O1",
         "file": "controles/policies/una.md", "status": "DECLARED_NOT_INSTALLED",
         "normativeSources": [{"standard": "ES0902", "version": "6.2", "rule": "O1",
                               "ruleKey": "ES0902.O1"}]}])
    t.vacio("E-16 y un control de ES0902 valida tambien",
            c_controles.validar_schema(con_o1))


def test_e17_un_control_sin_fuente_es_invalido(t):
    """E-17 — no se acepta un control que no dice de donde sale."""
    huerfano = {"id": "sin-origen", "type": "CHECK", "rule": "G1", "file": "controles/checks/x.py",
                "status": "INSTALLED"}
    t.vacio("E-17 no tiene ninguna fuente", c_controles.fuentes_de(huerfano))
    doc = dict(REGISTRO, controls=list(REGISTRO["controls"]) + [huerfano])
    informe = c_controles.validar(doc)
    t.igual("E-17 el estado es el que le corresponde", "CONTROL_NORMATIVE_SOURCE_MISSING",
            informe["controls"]["sin-origen"])
    t.verdadero("E-17 y no queda instalado",
                "sin-origen" not in c_controles.instalados(doc)["CHECK"])
    # Las dos formas vacias tambien.
    for vacio in ({"source": {}}, {"normativeSources": []}, {"normativeSources": [1, 2]}):
        t.vacio("E-17 %r tampoco es una fuente" % sorted(vacio),
                c_controles.fuentes_de(dict(huerfano, **vacio)))


# -- La excepcion aprobada por ASI ---------------------------------------------

def _excepcion(contrato=None, asi=None, reglas=("Vu2",), motivo="lo pidio el contrato"):
    doc = {"affectedRules": list(reglas), "reason": motivo,
           "contractEvidence": [], "asiApprovalEvidence": []}
    if contrato:
        doc["contractEvidence"] = [{"source": contrato, "reference": "anexo-3"}]
    if asi:
        doc["asiApprovalEvidence"] = [{"source": asi, "reference": "acta-asi-118"}]
    return doc


def test_e18_la_configuracion_local_nunca_exime(t):
    """E-18 (S-06) — un proyecto que se exime a si mismo no tiene excepcion, tiene un archivo."""
    for fuente in seguridad.FUENTES_LOCALES:
        doc = _excepcion(contrato=fuente, asi=fuente)
        r = seguridad.excepcion(doc)
        t.verdadero("E-18 `%s` no exime" % fuente, not r["granted"])
        t.igual("E-18 `%s` deja el estado" % fuente,
                "SECURITY_NORMATIVE_OVERRIDE_UNRESOLVED", r["state"])
    t.igual("E-18 son cinco fuentes locales", 5, len(seguridad.FUENTES_LOCALES))
    # 🔴 Y ninguna esta admitida por ninguna de las dos mitades. Sin esto, la guarda de arriba
    # es codigo muerto: hoy no hay solapamiento, y el dia que alguien agregue una fuente local
    # a las de contrato el test de arriba seguiria verde porque prueba las locales de HOY.
    admitidas = set(seguridad.FUENTES_DE_CONTRATO) | set(seguridad.FUENTES_DE_APROBACION_ASI)
    t.vacio("E-18 ninguna fuente local esta admitida",
            sorted(set(seguridad.FUENTES_LOCALES) & admitidas))
    t.igual("E-18 tres fuentes de contrato", 3, len(seguridad.FUENTES_DE_CONTRATO))
    t.igual("E-18 una sola de aprobacion", 1, len(seguridad.FUENTES_DE_APROBACION_ASI))

    # 🔴 Ni siquiera mezclada con una que si alcanza del otro lado.
    r = seguridad.excepcion(_excepcion(contrato="PROJECT_LOCAL_CONFIGURATION",
                                       asi="ASI_APPROVAL"))
    t.verdadero("E-18 local + ASI tampoco", not r["granted"])
    # Y la regla sigue exigiendose: el resultado no es EXCEPTUADA.
    ev = {"overrides": [_excepcion(contrato="PROJECT_LOCAL_CONFIGURATION",
                                   asi="PROJECT_LOCAL_CONFIGURATION")]}
    res = seguridad.resultado("Vu2", ev, _todas_las_senales(), MATRIZ)
    t.verdadero("E-18 y la regla no queda exceptuada", res["result"] != "OVERRIDDEN")
    t.contiene("E-18 con el estado a la vista", "SECURITY_NORMATIVE_OVERRIDE_UNRESOLVED",
               repr(res["states"]))


def test_e19_contrato_sin_asi_no_exime(t):
    """E-19 (S-07) — falta la mitad que aprueba."""
    for fuente in seguridad.FUENTES_DE_CONTRATO:
        r = seguridad.excepcion(_excepcion(contrato=fuente))
        t.verdadero("E-19 `%s` solo no exime" % fuente, not r["granted"])
        t.igual("E-19 `%s` deja el estado" % fuente,
                "SECURITY_NORMATIVE_OVERRIDE_UNRESOLVED", r["state"])
        t.contiene("E-19 `%s` y dice que falta ASI" % fuente, "aprobacion de ASI",
                   " | ".join(r["reasons"]))

    # 🔴 Y una excepcion PEDIDA y no concedida no deja la regla en COMPLIANT aunque todos sus
    # controles esten en PASS. Un estado sin resolver no convive con un cumplimiento: el que
    # lee veria el verde y no el pendiente.
    senales = _todas_las_senales()
    pedida = _todos_en_pass("Vu2")
    pedida["overrides"] = [_excepcion(contrato="PROJECT_CONTRACT")]
    r = seguridad.resultado("Vu2", pedida, senales, MATRIZ)
    t.igual("E-19 con la excepcion pendiente no cumple", "UNRESOLVED", r["result"])
    t.contiene("E-19 y el pendiente esta a la vista",
               "SECURITY_NORMATIVE_OVERRIDE_UNRESOLVED", repr(r["states"]))
    t.igual("E-19 sin la excepcion pendiente si cumpliria", "COMPLIANT",
            seguridad.resultado("Vu2", _todos_en_pass("Vu2"), senales, MATRIZ)["result"])


def test_e20_asi_sin_contrato_no_exime(t):
    """E-20 (S-07) — falta la mitad que licencia."""
    r = seguridad.excepcion(_excepcion(asi="ASI_APPROVAL"))
    t.verdadero("E-20 ASI sola no exime", not r["granted"])
    t.igual("E-20 con el mismo estado", "SECURITY_NORMATIVE_OVERRIDE_UNRESOLVED", r["state"])
    t.contiene("E-20 y dice que falta el contrato", "evidencia de contrato",
               " | ".join(r["reasons"]))
    # Una fuente de contrato no sirve como aprobacion de ASI ni al reves.
    t.verdadero("E-20 una fuente de contrato no aprueba",
                not seguridad.excepcion(_excepcion(contrato="PROJECT_CONTRACT",
                                                   asi="PROJECT_CONTRACT"))["granted"])
    t.verdadero("E-20 ni ASI sirve de contrato",
                not seguridad.excepcion(_excepcion(contrato="ASI_APPROVAL",
                                                   asi="ASI_APPROVAL"))["granted"])


def test_e21_las_dos_mitades_eximen_y_conservan_todo(t):
    """E-21 (S-08) — contrato + ASI, y los cuatro campos viajan enteros."""
    doc = _excepcion(contrato="PROJECT_CONTRACT", asi="ASI_APPROVAL")
    r = seguridad.excepcion(doc)
    t.verdadero("E-21 se concede", r["granted"])
    t.igual("E-21 sin estado pendiente", None, r["state"])
    t.vacio("E-21 sin motivos de rechazo", r["reasons"])
    for campo in seguridad.CAMPOS_DE_EXCEPCION:
        t.verdadero("E-21 conserva `%s`" % campo, campo in r)
    t.igual("E-21 `affectedRules` entero", ["Vu2"], r["affectedRules"])
    t.igual("E-21 `contractEvidence` entero", doc["contractEvidence"], r["contractEvidence"])
    t.igual("E-21 `asiApprovalEvidence` entero", doc["asiApprovalEvidence"],
            r["asiApprovalEvidence"])
    t.igual("E-21 `reason` entero", "lo pidio el contrato", r["reason"])

    res = seguridad.resultado("Vu2", {"overrides": [doc]}, _todas_las_senales(), MATRIZ)
    t.igual("E-21 la regla queda exceptuada", "OVERRIDDEN", res["result"])
    t.verdadero("E-21 con la excepcion pegada al resultado", res["override"]["granted"])
    t.igual("E-21 y el respaldo viaja con ella", doc["asiApprovalEvidence"],
            res["override"]["asiApprovalEvidence"])

    # Una excepcion sin motivo escrito no se concede: quien la lea tiene que saber por que.
    t.verdadero("E-21 sin `reason` no se concede",
                not seguridad.excepcion(dict(doc, reason=""))["granted"])
    t.verdadero("E-21 sin `affectedRules` tampoco",
                not seguridad.excepcion(dict(doc, affectedRules=[]))["granted"])


def test_e22_una_excepcion_no_derrama(t):
    """E-22 (S-08) — alcanza solo a las reglas que nombra."""
    doc = _excepcion(contrato="PROJECT_CONTRACT", asi="ASI_APPROVAL", reglas=("Vu2",))
    senales = _todas_las_senales()
    exceptuada = seguridad.resultado("Vu2", {"overrides": [doc]}, senales, MATRIZ)
    t.igual("E-22 Vu2 queda exceptuada", "OVERRIDDEN", exceptuada["result"])

    for otra in ("Vu1", "Vu3", "Vu5", "C1", "G1"):
        con = seguridad.resultado(otra, {"overrides": [doc]}, senales, MATRIZ)
        sin = seguridad.resultado(otra, {}, senales, MATRIZ)
        t.verdadero("E-22 `%s` no queda exceptuada" % otra, con["result"] != "OVERRIDDEN")
        t.igual("E-22 `%s` sale igual que sin excepcion" % otra, sin["result"], con["result"])
        t.igual("E-22 `%s` con los mismos estados" % otra, sin["states"], con["states"])

    # Y nombra por clave compuesta tambien, sin que eso ensanche el alcance.
    porclave = _excepcion(contrato="PROJECT_CONTRACT", asi="ASI_APPROVAL",
                          reglas=("ES0902.Vu3",))
    t.igual("E-22 nombrada por clave compuesta alcanza a Vu3", "OVERRIDDEN",
            seguridad.resultado("Vu3", {"overrides": [porclave]}, senales, MATRIZ)["result"])
    t.verdadero("E-22 y no a Vu2",
                seguridad.resultado("Vu2", {"overrides": [porclave]}, senales,
                                    MATRIZ)["result"] != "OVERRIDDEN")


# -- La frontera de la aprobacion oficial --------------------------------------

def _oficial(estado, productor, evidencia=("acta",)):
    return {"state": estado, "producer": productor, "evidence": list(evidencia)}


def test_e23_un_escaneo_automatico_no_aprueba(t):
    """E-23 (S-09) — queda en lo suyo y el estado oficial no se mueve."""
    r = evaluacion.estado_oficial(_oficial("APPROVED", "AUTOMATED_SCAN"))
    t.igual("E-23 el estado queda sin resolver", "OFFICIAL_STATUS_UNRESOLVED", r["state"])
    t.contiene("E-23 con el estado que lo explica",
               "SECURITY_INTERNAL_PRODUCER_CANNOT_SET_OFFICIAL_STATE", repr(r["states"]))
    t.igual("E-23 y se conserva que lo pidio", "APPROVED", r["requestedState"])
    t.igual("E-23 y quien lo pidio", "AUTOMATED_SCAN", r["producer"])

    # Lo que SI puede declarar, lo declara.
    interno = evaluacion.resultado_interno({"result": "INTERNAL_REVIEW_COMPLETE",
                                            "producer": "AUTOMATED_SCAN"})
    t.igual("E-23 un resultado interno si sale", "INTERNAL_REVIEW_COMPLETE", interno["result"])
    t.vacio("E-23 sin estados pendientes", interno["states"])


def test_e24_una_review_interna_no_aprueba(t):
    """E-24 (S-10) — ni declarandolo. `dev-security` prepara, no homologa."""
    for productor in ("INTERNAL_SECURITY_REVIEW", "DEV_SECURITY_AGENT", "HARNESS_CHECK"):
        r = evaluacion.estado_oficial(_oficial("APPROVED", productor))
        t.igual("E-24 `%s` no aprueba" % productor, "OFFICIAL_STATUS_UNRESOLVED", r["state"])
        t.contiene("E-24 `%s` y se dice por que" % productor, "no es una autoridad externa",
                   " | ".join(r["reasons"]))
        pedido = evaluacion.resultado_interno({"result": "APPROVED", "producer": productor})
        t.igual("E-24 `%s` tampoco por la via interna" % productor, None, pedido["result"])
        t.contiene("E-24 `%s` con su estado" % productor,
                   "SECURITY_INTERNAL_PRODUCER_CANNOT_SET_OFFICIAL_STATE", repr(pedido["states"]))


def test_e25_lo_oficial_exige_procedencia_externa(t):
    """E-25 (S-11) — y evidencia. Sin las dos cosas, OFFICIAL_STATUS_UNRESOLVED."""
    bueno = evaluacion.estado_oficial(_oficial("APPROVED", "GCBA_DGSEI"))
    t.igual("E-25 con autoridad externa y evidencia si", "APPROVED", bueno["state"])

    sin_evidencia = evaluacion.estado_oficial({"state": "APPROVED", "producer": "GCBA_DGSEI"})
    t.igual("E-25 sin evidencia no", "OFFICIAL_STATUS_UNRESOLVED", sin_evidencia["state"])
    t.contiene("E-25 y se dice que falta", "exige evidencia",
               " | ".join(sin_evidencia["reasons"]))

    sin_productor = evaluacion.estado_oficial({"state": "APPROVED", "evidence": ["acta"]})
    t.igual("E-25 sin productor tampoco", "OFFICIAL_STATUS_UNRESOLVED", sin_productor["state"])

    inventado = evaluacion.estado_oficial(_oficial("APPROVED", "EL_EQUIPO_DEL_PROYECTO"))
    t.igual("E-25 un productor que nadie declaro tampoco", "OFFICIAL_STATUS_UNRESOLVED",
            inventado["state"])
    t.igual("E-25 el estado sin resolver es el exigido por el paquete",
            "OFFICIAL_STATUS_UNRESOLVED", seguridad.ESTADO_OFICIAL_SIN_RESOLVER)


def test_e26_la_guarda_es_estructural(t):
    """E-26 (S-09..S-11) — PRODUCTO: todos los productores internos x todos los oficiales.

    🔴 El barrido sale del MODULO. Una lista de estados prohibidos escrita a mano se
    desactualiza en silencio el dia que aparece un productor nuevo, y el productor nuevo queda
    permitido: es justo el agujero que este escenario existe para cerrar.
    """
    internos = evaluacion.PRODUCTORES_INTERNOS
    oficiales = evaluacion.ESTADOS_OFICIALES
    t.igual("E-26 cinco productores internos", 5, len(internos))
    t.igual("E-26 cinco estados oficiales", 5, len(oficiales))

    celdas = 0
    for productor in internos:
        for estado in oficiales:
            celdas += 1
            t.verdadero("E-26 %s no puede %s" % (productor, estado),
                        not evaluacion.puede_emitir(productor, estado))
            r = evaluacion.estado_oficial(_oficial(estado, productor))
            t.igual("E-26 %s pidiendo %s queda sin resolver" % (productor, estado),
                    "OFFICIAL_STATUS_UNRESOLVED", r["state"])
            t.contiene("E-26 %s/%s con el estado" % (productor, estado),
                       "SECURITY_INTERNAL_PRODUCER_CANNOT_SET_OFFICIAL_STATE", repr(r["states"]))
    t.igual("E-26 el producto tiene veinticinco celdas", 25, celdas)

    # Los del harness si, y son seis. La particion no deja ningun estado afuera ni repetido.
    for estado in evaluacion.ESTADOS_DEL_HARNESS:
        t.verdadero("E-26 %s si lo puede un interno" % estado,
                    evaluacion.puede_emitir("AUTOMATED_SCAN", estado))
    t.igual("E-26 seis estados del harness", 6, len(evaluacion.ESTADOS_DEL_HARNESS))
    t.vacio("E-26 la particion no se solapa",
            sorted(set(evaluacion.ESTADOS_DEL_HARNESS) & set(oficiales)))
    t.igual("E-26 y cubre los doce",
            sorted(evaluacion.ESTADOS),
            sorted(set(evaluacion.ESTADOS_DEL_HARNESS) | set(oficiales)
                   | {"OFFICIAL_STATUS_UNRESOLVED"}))
    # Un externo si puede, o la guarda no seria una guarda sino un candado.
    for estado in oficiales:
        t.verdadero("E-26 una autoridad externa si puede %s" % estado,
                    evaluacion.puede_emitir("GCBA_DGSEI", estado))


def test_e27_todos_los_principios_en_pass_no_aprueban(t):
    """E-27 (S-34) — ES0902 G1 como invariante. Los controles no agregan a una homologacion."""
    principios = [r["id"] for r in MATRIZ["rules"] if r["category"] == "SECURITY_PRINCIPLE"]
    t.igual("E-27 los principios son diez", 10, len(principios))

    resultados = {}
    senales = _todas_las_senales()
    ev = {"controlResults": {}, "assetTypes": ["WEB_APPLICATION"],
          "inactivityTimeout": [{"kind": "IDLE_SESSION_TIMEOUT", "evidence": ["conf"]}],
          "abuseControls": [{"mechanism": "RATE_LIMITING", "evidence": ["gateway"]}],
          "owaspGuidance": [{"reference": "OWASP Top 10", "version": "2021",
                             "date": "2021-09-24"}]}
    for rid in principios:
        for cid in _controles_de(rid):
            ev["controlResults"][cid] = {"result": "PASS", "evidence": ["acta-%s" % cid]}
    for rid in principios:
        resultados[rid] = seguridad.resultado(rid, ev, senales, MATRIZ)
    en_pass = [rid for rid, r in resultados.items() if r["result"] == "COMPLIANT"]
    t.igual("E-27 los diez principios cumplen", 10, len(en_pass))

    # 🔴 Y el estado oficial no se movio. No hay agregacion de PASS que lo mueva: nadie lo
    # consulta, y el unico que lo decide exige una autoridad externa.
    oficial = evaluacion.estado_oficial({"state": None})
    t.igual("E-27 el estado oficial sigue sin resolver", "OFFICIAL_STATUS_UNRESOLVED",
            oficial["state"])
    for rid, r in resultados.items():
        t.no_contiene("E-27 %s no publica APPROVED" % rid, "APPROVED", repr(r))
    t.verdadero("E-27 y G1 no declara ningun check que pueda agregarlos",
                not (seguridad.regla("G1", MATRIZ)["checks"]))
    t.igual("E-27 G1 declara la prohibicion como policy",
            ["security-principles-do-not-imply-assessment-approval"],
            seguridad.regla("G1", MATRIZ)["policies"])
    prohibiciones = cruzada.prohibiciones(MAPA)
    t.igual("E-27 el mapa cruzado la declara una vez", 1, len(prohibiciones))
    t.igual("E-27 desde ES0902.G1", "ES0902.G1", prohibiciones[0]["from"])
    t.igual("E-27 contra la evaluacion del harness", "HARNESS.SECURITY_ASSESSMENT",
            prohibiciones[0]["to"])


# -- El flujo de evaluacion ----------------------------------------------------

def test_e28_los_doce_estados_y_ninguno_mas(t):
    """E-28 (S-03) — un estado que no esta en la lista falla cerrado."""
    esperados = ("NOT_STARTED", "INTERNAL_ASSESSMENT", "READY_TO_REQUEST", "REQUESTED",
                 "IN_ASSESSMENT", "FINDINGS_RECEIVED", "REMEDIATION", "READY_TO_RESUBMIT",
                 "RESUBMITTED", "APPROVED", "REJECTED", "OFFICIAL_STATUS_UNRESOLVED")
    t.igual("E-28 son doce", 12, len(evaluacion.ESTADOS))
    t.igual("E-28 y son estos", sorted(esperados), sorted(evaluacion.ESTADOS))

    for inventado in ("SECURITY_APPROVED", "OK", "PASSED", "", "approved", None):
        r = evaluacion.estado_oficial({"state": inventado, "producer": "GCBA_DGSEI",
                                       "evidence": ["acta"]})
        t.igual("E-28 `%r` no se acepta" % inventado, "OFFICIAL_STATUS_UNRESOLVED", r["state"])
    t.contiene("E-28 y se dice que no es del flujo", "SECURITY_ASSESSMENT_STATE_UNKNOWN",
               repr(evaluacion.estado_oficial({"state": "SECURITY_APPROVED",
                                               "producer": "GCBA_DGSEI",
                                               "evidence": ["a"]})["states"]))
    # Los cuatro resultados internos que el paquete nombra existen y son otra cosa.
    t.igual("E-28 cuatro resultados internos", 4, len(evaluacion.RESULTADOS_INTERNOS))
    for r in ("INTERNAL_REVIEW_COMPLETE", "READY_TO_REQUEST", "READY_TO_RESUBMIT",
              "G2_THRESHOLD_SATISFIED"):
        t.verdadero("E-28 `%s` es un resultado interno" % r,
                    r in evaluacion.RESULTADOS_INTERNOS)


def test_e29_c2_fuera_de_qa_no_cumple(t):
    """E-29 (S-12) — la aprobacion se evidencia en QA o no cuenta."""
    senales = _todas_las_senales()
    # Desde ES0902 C2 son dos nombres, los mismos que emite el check: otro ambiente, o no saberlo.
    for ambiente, estado in (("DEV", "SECURITY_APPROVAL_NOT_IN_QA"),
                             ("HML", "SECURITY_APPROVAL_NOT_IN_QA"),
                             ("PRD", "SECURITY_APPROVAL_NOT_IN_QA"),
                             (None, "SECURITY_APPROVAL_ENVIRONMENT_UNRESOLVED"),
                             ("qa", "SECURITY_APPROVAL_ENVIRONMENT_UNRESOLVED")):
        ev = _todos_en_pass("C2", environment=ambiente,
                            officialApproval=_oficial("APPROVED", "GCBA_DGSEI"))
        r = seguridad.resultado("C2", ev, senales, MATRIZ)
        t.verdadero("E-29 en `%r` C2 no cumple" % ambiente, r["result"] != "COMPLIANT")
        t.contiene("E-29 en `%r` con su estado" % ambiente, estado, repr(r["states"]))
    t.igual("E-29 el ambiente de homologacion es QA", "QA",
            evaluacion.AMBIENTE_DE_HOMOLOGACION)


def test_e30_c2_cumple_en_qa_con_aprobacion_oficial(t):
    """E-30 (S-13) — y una review interna en QA no alcanza."""
    senales = _todas_las_senales()
    bueno = _todos_en_pass("C2", environment="QA",
                           officialApproval=_oficial("APPROVED", "GCBA_DGSEI"))
    r = seguridad.resultado("C2", bueno, senales, MATRIZ)
    t.igual("E-30 en QA con aprobacion oficial cumple", "COMPLIANT", r["result"])
    t.igual("E-30 y el estado oficial es APPROVED", "APPROVED", r["officialState"])

    interno = _todos_en_pass("C2", environment="QA",
                             officialApproval=_oficial("APPROVED", "INTERNAL_SECURITY_REVIEW"))
    r = seguridad.resultado("C2", interno, senales, MATRIZ)
    t.verdadero("E-30 una review interna en QA no alcanza", r["result"] != "COMPLIANT")
    t.contiene("E-30 y se dice por que", "no es una aprobacion", " | ".join(r["reasons"]))

    sin = _todos_en_pass("C2", environment="QA")
    r = seguridad.resultado("C2", sin, senales, MATRIZ)
    t.verdadero("E-30 en QA sin nada tampoco", r["result"] != "COMPLIANT")
    t.igual("E-30 el estado oficial queda sin resolver", "OFFICIAL_STATUS_UNRESOLVED",
            r["officialState"])


def test_e31_ready_to_request_exige_todo_resuelto(t):
    """E-31 (S-18) — entregables y WAF. Un estado abierto bloquea."""
    ctx_completo = {"providedDeliverables": ENTREGABLES["assetTypes"]["SERVER"]["requirements"]}
    listo = evaluacion.listo_para_pedir(["SERVER"], ctx_completo)
    t.igual("E-31 con todo resuelto se llega", "READY_TO_REQUEST", listo["state"])
    t.vacio("E-31 sin bloqueos", listo["blockedBy"])

    faltante = {"providedDeliverables":
                ENTREGABLES["assetTypes"]["SERVER"]["requirements"][:-1]}
    bloqueado = evaluacion.listo_para_pedir(["SERVER"], faltante)
    t.igual("E-31 con un entregable de menos no se llega", None, bloqueado["state"])
    t.contiene("E-31 y se dice que lo bloquea", "SECURITY_DELIVERABLES_INCOMPLETE",
               repr(bloqueado["blockedBy"]))

    # Un servicio web con todos sus entregables pero sin la plantilla de WAF tampoco llega.
    ctx_waf = {"providedDeliverables":
               ENTREGABLES["assetTypes"]["WEB_SERVICE"]["requirements"]}
    con_waf = evaluacion.listo_para_pedir(["WEB_SERVICE"], ctx_waf)
    t.igual("E-31 sin la plantilla de WAF no se llega", None, con_waf["state"])
    t.contiene("E-31 y el bloqueo es el del WAF", "WAF_FORM_CONTEXT_REQUIRED",
               repr(con_waf["blockedBy"]))
    ctx_waf["wafFormTemplate"] = "formulario-prevencion-v3"
    ctx_waf["wafFormCompleted"] = True
    t.igual("E-31 con la plantilla y el formulario completo si", "READY_TO_REQUEST",
            evaluacion.listo_para_pedir(["WEB_SERVICE"], ctx_waf)["state"])


# -- Entregables y WAF ---------------------------------------------------------

def test_e32_e1_a_e5_por_tipo_de_activo(t):
    """E-32 (S-14) — los requisitos son los del archivo: ninguno se agrega, ninguno se pierde."""
    esperados = {"WEB_SERVICE": "E1", "WEB_APPLICATION": "E2", "MOBILE_APPLICATION": "E3",
                 "SERVER": "E4", "TOTEM": "E5"}
    t.igual("E-32 cinco tipos de activo", 5, len(ENTREGABLES["assetTypes"]))
    t.igual("E-32 y son estos", sorted(esperados), evaluacion.tipos_de_activo())

    # 🔴 El ancla es la seccion 5 del estandar, no el archivo. Comparar la salida contra el
    # mismo archivo del que sale es comparar el archivo consigo mismo: cambiar un requisito
    # mueve los dos lados de la igualdad y el test no se entera.
    CUANTOS = {"WEB_SERVICE": 5, "WEB_APPLICATION": 6, "MOBILE_APPLICATION": 6,
               "SERVER": 4, "TOTEM": 9}
    PRIMERO = {"WEB_SERVICE": "description of all Web Service methods",
               "WEB_APPLICATION": "URL or IP",
               "MOBILE_APPLICATION": "APK",
               "SERVER": "IP",
               "TOTEM": "physical asset"}
    for tipo in sorted(CUANTOS):
        resuelto = evaluacion.entregables([tipo])
        t.igual("E-32 %s exige %d requisitos" % (tipo, CUANTOS[tipo]), CUANTOS[tipo],
                len(resuelto["requirements"]))
        # 📌 Pertenencia EXACTA, no subcadena: `"APK firmado"` contiene `"APK"` y un
        # `contiene` sobre el repr dejaba pasar un requisito reescrito.
        t.verdadero("E-32 %s trae textual el de la seccion 5" % tipo,
                    PRIMERO[tipo] in resuelto["requirements"])
    t.igual("E-32 treinta requisitos en total", 30, sum(CUANTOS.values()))
    for tipo, sid in sorted(esperados.items()):
        bloque = ENTREGABLES["assetTypes"][tipo]
        t.igual("E-32 %s es %s" % (tipo, sid), sid, bloque["sourceId"])
        resuelto = evaluacion.entregables([tipo])
        t.igual("E-32 %s trae su sourceId" % tipo, [sid], resuelto["sourceIds"])
        t.igual("E-32 %s trae exactamente sus requisitos" % tipo,
                sorted(bloque["requirements"]), resuelto["requirements"])
        t.igual("E-32 %s no agrega ninguno" % tipo,
                len(bloque["requirements"]), len(resuelto["requirements"]))
    t.vacio("E-32 el archivo valida contra su contrato", evaluacion.validar_entregables())

    desconocido = evaluacion.entregables(["DRON"])
    t.igual("E-32 un tipo que el estandar no trae queda explicito", ["DRON"],
            desconocido["unknownAssetTypes"])
    t.contiene("E-32 con su estado", "EXTERNAL_NORMATIVE_CONTEXT_REQUIRED",
               repr(desconocido["states"]))
    t.vacio("E-32 y no se le inventan requisitos", desconocido["requirements"])


def test_e33_varios_tipos_dan_la_union(t):
    """E-33 (S-15) — nunca el mas chico, nunca el del primero."""
    t.verdadero("E-33 el archivo declara que es union",
                ENTREGABLES["unionWhenMultipleAssetTypes"] is True)
    e1 = set(ENTREGABLES["assetTypes"]["WEB_SERVICE"]["requirements"])
    e2 = set(ENTREGABLES["assetTypes"]["WEB_APPLICATION"]["requirements"])
    union = evaluacion.entregables(["WEB_SERVICE", "WEB_APPLICATION"])
    t.igual("E-33 los requisitos son la union", sorted(e1 | e2), union["requirements"])
    t.igual("E-33 los dos sourceIds", ["E1", "E2"], union["sourceIds"])
    t.verdadero("E-33 y es mas que el mas chico",
                len(union["requirements"]) > min(len(e1), len(e2)))
    t.verdadero("E-33 y mas que el primero", len(union["requirements"]) >= len(e1))
    t.igual("E-33 el orden de los tipos no cambia el resultado", union["requirements"],
            evaluacion.entregables(["WEB_APPLICATION", "WEB_SERVICE"])["requirements"])

    # Los cinco a la vez: la union de las cinco, sin repetidos.
    todos = evaluacion.entregables(evaluacion.tipos_de_activo())
    completa = set()
    for bloque in ENTREGABLES["assetTypes"].values():
        completa |= set(bloque["requirements"])
    t.igual("E-33 los cinco dan la union entera", sorted(completa), todos["requirements"])
    t.igual("E-33 con los cinco sourceIds", ["E1", "E2", "E3", "E4", "E5"], todos["sourceIds"])


def test_e34_el_servicio_web_exige_waf(t):
    """E-34 (S-16) — y el artefacto es el que trae el archivo."""
    waf = evaluacion.requisito_de_waf(["WEB_SERVICE"])
    t.verdadero("E-34 lo exige", waf["required"])
    t.igual("E-34 para el servicio web", ["WEB_SERVICE"], waf["requiredFor"])
    t.igual("E-34 con el artefacto del archivo", ENTREGABLES["waf"]["artifact"], waf["artifact"])


def test_e35_la_aplicacion_web_exige_waf(t):
    """E-35 (S-17) — y los que no estan en la lista no lo exigen."""
    waf = evaluacion.requisito_de_waf(["WEB_APPLICATION"])
    t.verdadero("E-35 lo exige", waf["required"])
    t.igual("E-35 los dos tipos que lo exigen son los del archivo",
            sorted(ENTREGABLES["waf"]["requiredFor"]),
            sorted(["WEB_SERVICE", "WEB_APPLICATION"]))
    for tipo in ("MOBILE_APPLICATION", "SERVER", "TOTEM"):
        otro = evaluacion.requisito_de_waf([tipo])
        t.verdadero("E-35 %s no lo exige" % tipo, not otro["required"])
        t.vacio("E-35 %s sin estados de WAF" % tipo, otro["states"])
        t.igual("E-35 %s sin artefacto" % tipo, None, otro["artifact"])


def test_e36_sin_plantilla_el_estado_bloquea(t):
    """E-36 (S-18) — WAF_FORM_CONTEXT_REQUIRED, y bloquea READY_TO_REQUEST."""
    for tipo in ("WEB_SERVICE", "WEB_APPLICATION"):
        waf = evaluacion.requisito_de_waf([tipo], {})
        t.igual("E-36 %s sin plantilla" % tipo, ["WAF_FORM_CONTEXT_REQUIRED"], waf["states"])
        t.verdadero("E-36 %s la plantilla no esta" % tipo, waf["templateAvailable"] is False)
        ctx = {"providedDeliverables": ENTREGABLES["assetTypes"][tipo]["requirements"]}
        listo = evaluacion.listo_para_pedir([tipo], ctx)
        t.igual("E-36 %s no llega a READY_TO_REQUEST" % tipo, None, listo["state"])
        t.contiene("E-36 %s bloqueado por el WAF" % tipo, "WAF_FORM_CONTEXT_REQUIRED",
                   repr(listo["blockedBy"]))
    t.igual("E-36 el estado sale del archivo", ENTREGABLES["waf"]["missingTemplateState"],
            seguridad.WAF_SIN_CONTEXTO)


def test_e37_ningun_campo_del_formulario_se_inventa(t):
    """E-37 (S-18) — lo unico que sale del WAF es lo que trae el archivo."""
    ctx = {"wafFormTemplate": "formulario-prevencion-v3", "wafFormCompleted": True}
    waf = evaluacion.requisito_de_waf(["WEB_APPLICATION"], ctx)
    t.igual("E-37 las claves de la salida son las del contrato",
            ["artifact", "reasons", "required", "requiredFor", "states", "templateAvailable"],
            sorted(waf))
    t.igual("E-37 y el artefacto es textual", "Prevention team WAF policy form", waf["artifact"])

    # 🔴 El sujeto del barrido son IDENTIFICADORES de un formulario, no una palabra del idioma.
    fuente = (BIN / "orquestacion" / "evaluacion.py").read_text(encoding="utf-8")
    for campo in ("fieldName", "formFields", "wafRuleSet", "ipWhitelist", "backendPool",
                  "originIp", "tlsPolicy"):
        t.no_contiene("E-37 el modulo no inventa `%s`" % campo, campo, fuente)
        t.no_contiene("E-37 y no sale en la salida `%s`" % campo, campo, repr(waf))
    t.igual("E-37 el archivo describe el artefacto y no sus campos",
            ["artifact", "missingTemplateState", "requiredFor"], sorted(ENTREGABLES["waf"]))


def test_e38_entregables_faltantes_con_su_estado(t):
    """E-38 (S-18) — SECURITY_DELIVERABLES_INCOMPLETE, y cuales faltan."""
    requisitos = ENTREGABLES["assetTypes"]["TOTEM"]["requirements"]
    parcial = evaluacion.entregables(["TOTEM"], {"providedDeliverables": requisitos[:3]})
    t.contiene("E-38 el estado", "SECURITY_DELIVERABLES_INCOMPLETE", repr(parcial["states"]))
    t.igual("E-38 faltan los que faltan", sorted(requisitos[3:]), parcial["missing"])
    t.igual("E-38 y son seis", len(requisitos) - 3, len(parcial["missing"]))

    completo = evaluacion.entregables(["TOTEM"], {"providedDeliverables": requisitos})
    t.vacio("E-38 con todos no falta ninguno", completo["missing"])
    t.vacio("E-38 y sin estados", completo["states"])

    # Sin declarar nada faltan todos: el silencio no entrega nada.
    nada = evaluacion.entregables(["TOTEM"])
    t.igual("E-38 sin declarar nada faltan todos", sorted(requisitos), nada["missing"])


# -- C1, y el cruce con ES0901 D1 ----------------------------------------------

def test_e39_c1_reusa_los_controles_de_d2(t):
    """E-39 (S-19) — los dos de delegacion, con ES0902.C1 como segunda fuente."""
    relacion = [r for r in MAPA["relations"]
                if r["from"] == "ES0902.C1" and r["to"] == "ES0901.D2"]
    t.igual("E-39 el mapa declara la relacion una vez", 1, len(relacion))
    t.igual("E-39 y es de reuso", "OVERLAP_REUSE", relacion[0]["type"])
    compartidos = sorted(relacion[0]["sharedControls"])
    t.igual("E-39 los dos controles", ["authentication-delegation",
                                       "credential-entry-delegation-required"], compartidos)
    for cid in compartidos:
        t.verdadero("E-39 `%s` lo declara C1 en la matriz" % cid, cid in _controles_de("C1"))
        fuentes = c_controles.fuentes_de(c_controles.control(cid, REGISTRO))
        claves = sorted(f["ruleKey"] for f in fuentes)
        t.igual("E-39 `%s` tiene las dos fuentes" % cid, ["ES0901.D2", "ES0902.C1"], claves)
        t.igual("E-39 `%s` sigue instalado" % cid, "INSTALLED",
                c_controles.validar(REGISTRO)["controls"][cid])


def test_e40_c1_exige_evidencia_de_oidc_con_keycloak(t):
    """E-40 (S-20) — sin ella queda sin resolver, nunca en PASS."""
    senales = _todas_las_senales()
    declarados = _controles_de("C1")
    t.contiene("E-40 C1 declara la policy de OIDC", "openid-connect-authentication-required",
               repr(declarados))
    t.contiene("E-40 y la del proveedor de DGSEI", "dgsei-keycloak-provider-required",
               repr(declarados))
    t.contiene("E-40 y el check de integracion", "oidc-keycloak-integration", repr(declarados))

    sin = seguridad.resultado("C1", {"controlResults": {}}, senales, MATRIZ)
    t.igual("E-40 sin evidencia no cumple", "UNRESOLVED", sin["result"])
    t.contiene("E-40 con el estado", "SECURITY_CONTROL_EVIDENCE_MISSING", repr(sin["states"]))
    t.contiene("E-40 nombrando el check que falta", "oidc-keycloak-integration",
               " | ".join(sin["reasons"]))

    con = seguridad.resultado("C1", _todos_en_pass("C1"), senales, MATRIZ)
    t.igual("E-40 con evidencia de los cinco controles cumple", "COMPLIANT", con["result"])
    t.igual("E-40 y son cinco", 5, len(declarados))


def test_e41_d1_y_c1_juntas_no_se_reconcilian_solas(t):
    """E-41 (S-21) — CROSS_STANDARD_INTERPRETATION_REQUIRED."""
    bloque = cruzada.resolver(["D1", "D2"], ["C1"], {}, MAPA)
    t.contiene("E-41 el estado sale", "CROSS_STANDARD_INTERPRETATION_REQUIRED",
               repr(bloque["states"]))
    conflicto = [r for r in bloque["relations"] if r["type"] == "POTENTIAL_CONFLICT"]
    t.igual("E-41 hay un conflicto", 1, len(conflicto))
    t.igual("E-41 entre C1 y D1", ("ES0902.C1", "ES0901.D1"),
            (conflicto[0]["from"], conflicto[0]["to"]))
    t.igual("E-41 sin reconciliar", None, conflicto[0]["reconciliation"])

    # 🔴 Si D1 no aplica, no hay conflicto: dos reglas que no aplican no chocan.
    sola = cruzada.resolver([], ["C1"], {}, MAPA)
    t.no_contiene("E-41 sin D1 aplicable no hay conflicto",
                  "CROSS_STANDARD_INTERPRETATION_REQUIRED", repr(sola["states"]))
    # 🔴 Y con NADA aplicable no sale ninguna relacion, ni siquiera las que apuntan al harness
    # en vez de a otra regla. Un cruce que aparece cuando ninguna de sus dos puntas aplica
    # llena todo reporte de conflictos que no le pasan a nadie.
    vacio = cruzada.resolver([], [], {}, MAPA)
    t.vacio("E-41 sin nada aplicable no hay relaciones", vacio["relations"])
    t.vacio("E-41 ni estados", vacio["states"])
    t.vacio("E-41 ni controles compartidos", vacio["sharedControls"])
    t.igual("E-41 aunque el mapa declare ocho", 8, len(MAPA["relations"]))

    # Con evidencia autoritativa se reconcilia; con evidencia del proyecto, no.
    autoritativa = {"reconciliations": [{"between": ["ES0902.C1", "ES0901.D1"],
                                         "source": "GCBA_NORMATIVE",
                                         "evidence": ["circular-asi-2026"]}]}
    resuelto = cruzada.resolver(["D1"], ["C1"], autoritativa, MAPA)
    t.no_contiene("E-41 con evidencia autoritativa se resuelve",
                  "CROSS_STANDARD_INTERPRETATION_REQUIRED", repr(resuelto["states"]))
    del_proyecto = {"reconciliations": [{"between": ["ES0902.C1", "ES0901.D1"],
                                         "source": "PROJECT_DECISION",
                                         "evidence": ["acta-de-equipo"]}]}
    t.contiene("E-41 con una decision del proyecto no",
               "CROSS_STANDARD_INTERPRETATION_REQUIRED",
               repr(cruzada.resolver(["D1"], ["C1"], del_proyecto, MAPA)["states"]))
    sin_evidencia = {"reconciliations": [{"between": ["ES0902.C1", "ES0901.D1"],
                                          "source": "GCBA_NORMATIVE"}]}
    t.contiene("E-41 ni una fuente autoritativa sin evidencia",
               "CROSS_STANDARD_INTERPRETATION_REQUIRED",
               repr(cruzada.resolver(["D1"], ["C1"], sin_evidencia, MAPA)["states"]))


def test_e42_no_se_inventa_ninguna_reconciliacion(t):
    """E-42 (S-22) — ni realm, ni client, ni issuer, ni flow, en ningun lado."""
    senales = _todas_las_senales()
    salidas = repr([seguridad.resultados({}, senales, MATRIZ),
                    seguridad.resolver(senales),
                    cruzada.resolver(list(c_matriz.INVENTARIO), list(LAS_21), {}, MAPA),
                    evaluacion.entregables(evaluacion.tipos_de_activo())])
    fuentes = "".join((BIN / "orquestacion" / n).read_text(encoding="utf-8")
                      for n in ("seguridad.py", "evaluacion.py", "cruzada.py"))
    # 🔴 Identificadores de configuracion de OIDC, no palabras del idioma.
    # 🔴 Sin bajar a minusculas, `ISSUER_DE_KEYCLOAK` se escapaba del barrido: una constante
    # gritada no es menos configuracion que un campo en camelCase.
    salidas_bajas, fuentes_bajas = salidas.lower(), fuentes.lower()
    for campo in ("realm", "issuer", "clientid", "clientsecret", "granttype",
                  "authorizationendpoint", "tokenendpoint", "redirecturi", "responsetype"):
        t.no_contiene("E-42 `%s` no sale en ninguna salida" % campo, campo, salidas_bajas)
        t.no_contiene("E-42 `%s` no esta en los modulos" % campo, campo, fuentes_bajas)
    # 📌 `keycloak` SI aparece en la salida y tiene que aparecer: son los ids de control que la
    # matriz declara -`dgsei-keycloak-provider-required`, `oidc-keycloak-integration`-. Declarar
    # que hace falta un control no es configurarlo. Lo que no puede aparecer es miBA, que es la
    # otra mitad del cruce que nadie reconcilio.
    for palabra in ("miBA", "MIBA"):
        t.no_contiene("E-42 `%s` no aparece en ninguna salida" % palabra, palabra, salidas)
    t.contiene("E-42 y el control de Keycloak si esta declarado",
               "dgsei-keycloak-provider-required", salidas)
    # 🔴 En la fuente el sujeto tiene que ser un IDENTIFICADOR: `MIBA` esta en el docstring de
    # `cruzada.py` diciendo que no se reconcilia, y una prosa que explica la prohibicion no es
    # una violacion. Lo que no puede existir es una TABLA que mapee una cosa con la otra.
    for identificador in ("MIBA_A_KEYCLOAK", "EQUIVALENCIAS", "RECONCILIACION",
                          "MAPEO_DE_AUTENTICACION"):
        t.no_contiene("E-42 no hay tabla `%s`" % identificador, identificador, fuentes)
    # Y la relacion existe declarada, que es la unica forma en que el cruce aparece.
    t.igual("E-42 el cruce esta declarado en el mapa y no resuelto", 1,
            len([r for r in MAPA["relations"]
                 if r.get("state") == "CROSS_STANDARD_INTERPRETATION_REQUIRED"]))


# -- Tecnologia y versiones ----------------------------------------------------

def test_e43_c3_reusa_los_controles_de_g1(t):
    """E-43 (S-23) — los cuatro de ES0901 G1, sin duplicar Anexo II ni comparacion de versiones."""
    g1 = c_matriz.regla("G1")
    los_cuatro = sorted((g1.get("policies") or []) + (g1.get("checks") or []))
    t.igual("E-43 ES0901 G1 declara cuatro controles", 4, len(los_cuatro))
    t.igual("E-43 C3 declara exactamente esos", los_cuatro, sorted(_controles_de("C3")))

    relacion = [r for r in MAPA["relations"]
                if r["from"] == "ES0902.C3" and r["to"] == "ES0901.G1"]
    t.igual("E-43 el mapa lo declara", 1, len(relacion))
    t.igual("E-43 como reuso de control", "CONTROL_REUSE", relacion[0]["type"])
    t.igual("E-43 con los cuatro", los_cuatro, sorted(relacion[0]["sharedControls"]))

    # 🔴 Y el modulo de ES0902 no tiene logica propia de ninguna de las dos cosas.
    fuentes = "".join((BIN / "orquestacion" / n).read_text(encoding="utf-8")
                      for n in ("seguridad.py", "evaluacion.py", "cruzada.py"))
    for identificador in ("anexo2", "annex-ii", "ANNEX_II", "annex_ii",
                          "technology-catalog", "annexIiReference"):
        t.no_contiene("E-43 no reimplementa `%s`" % identificador, identificador, fuentes)
    # Y sobre todo: no importa el modulo que SI tiene esa logica. El reuso es de los controles
    # declarados, no de la implementacion copiada.
    t.no_contiene("E-43 no importa el modulo del Anexo II", "import anexo2", fuentes)
    t.verdadero("E-43 el modulo del Anexo II existe y es de ES0901",
                (BIN / "orquestacion" / "anexo2.py").exists())


def test_e44_ve1_reusa_los_mismos(t):
    """E-44 (S-24) — y son literalmente los mismos ids que C3."""
    t.igual("E-44 Ve1 declara lo mismo que C3", sorted(_controles_de("C3")),
            sorted(_controles_de("Ve1")))
    relacion = [r for r in MAPA["relations"]
                if r["from"] == "ES0902.Ve1" and r["to"] == "ES0901.G1"]
    t.igual("E-44 el mapa lo declara", 1, len(relacion))
    t.igual("E-44 como reuso de control", "CONTROL_REUSE", relacion[0]["type"])
    # Y en el registro, los cuatro quedaron con tres fuentes: G1, C3 y Ve1.
    for cid in sorted(_controles_de("Ve1")):
        claves = sorted(f["ruleKey"] for f in
                        c_controles.fuentes_de(c_controles.control(cid, REGISTRO)))
        t.igual("E-44 `%s` tiene las tres fuentes" % cid,
                ["ES0901.G1", "ES0902.C3", "ES0902.Ve1"], claves)


def test_e45_ve2_exige_consenso_de_infraestructura(t):
    """E-45 (S-25) — una version mas nueva no se vuelve permitida por ser mas nueva."""
    senales = _todas_las_senales()
    sin = seguridad.resultado("Ve2", _todos_en_pass("Ve2"), senales, MATRIZ)
    t.verdadero("E-45 sin consenso no cumple", sin["result"] != "COMPLIANT")
    t.contiene("E-45 con el estado", "EXTERNAL_NORMATIVE_CONTEXT_REQUIRED", repr(sin["states"]))
    t.contiene("E-45 y se dice que falta", "consenso de Infraestructura",
               " | ".join(sin["reasons"]))

    declarado_sin_evidencia = _todos_en_pass(
        "Ve2", infrastructureConsensus=[{"source": "INFRASTRUCTURE"}])
    t.verdadero("E-45 declarado sin evidencia tampoco",
                seguridad.resultado("Ve2", declarado_sin_evidencia, senales,
                                    MATRIZ)["result"] != "COMPLIANT")

    con = _todos_en_pass("Ve2", infrastructureConsensus=[
        {"source": "INFRASTRUCTURE", "evidence": ["acta-infra-77"]}])
    t.igual("E-45 con consenso evidenciado cumple", "COMPLIANT",
            seguridad.resultado("Ve2", con, senales, MATRIZ)["result"])

    # 🔴 Y no hay ninguna via de "lo mas nuevo es lo mas seguro": el modulo no mira la version.
    fuentes = (BIN / "orquestacion" / "seguridad.py").read_text(encoding="utf-8")
    for atajo in ("latest", "newer_is", "es_mas_nueva", "version_mayor"):
        t.no_contiene("E-45 no hay atajo `%s`" % atajo, atajo, fuentes)


# -- Los diez principios de seguridad ------------------------------------------

def test_e46_vu1_a_vu10_son_diez_reglas_distintas(t):
    """E-46 (S-26) — PRODUCTO: ninguna se colapsa en una review generica de seguridad.

    🔴 Cada una tiene su senal, su policy y su check propios. Si dos compartieran los tres,
    serian la misma regla con dos nombres, y el estandar tendria una obligacion menos.
    """
    vus = [r for r in MATRIZ["rules"] if r["id"].startswith("Vu")]
    t.igual("E-46 son diez", 10, len(vus))
    t.igual("E-46 y estan las diez", sorted(["Vu%d" % i for i in range(1, 11)]),
            sorted(r["id"] for r in vus))

    policies, checks, senales_vistas = [], [], []
    for r in vus:
        rid = r["id"]
        t.igual("E-46 %s declara una policy" % rid, 1, len(r["policies"]))
        policies.append(r["policies"][0])
        # Vu10 es la unica con REVIEW en vez de CHECK: considerar guia OWASP es criterio.
        if rid == "Vu10":
            t.igual("E-46 Vu10 es una review", ["owasp-security-guidance-review"], r["reviews"])
            t.vacio("E-46 Vu10 no tiene check", r["checks"])
        else:
            t.igual("E-46 %s declara un check" % rid, 1, len(r["checks"]))
            checks.append(r["checks"][0])
        senales_vistas.extend((r["applicability"] or {}).get("signals") or [])

    t.igual("E-46 diez policies distintas", 10, len(set(policies)))
    t.igual("E-46 nueve checks distintos", 9, len(set(checks)))
    t.igual("E-46 y ninguna comparte senal con otra", len(senales_vistas), len(set(senales_vistas)))
    t.igual("E-46 Vu7 es la unica que aplica siempre",
            ["Vu7"], sorted(r["id"] for r in vus if r["applicability"]["mode"] == "ALWAYS"))

    # Y resuelven por separado: cada una cae por su propia evidencia, no por la del vecino.
    senales = _todas_las_senales()
    for r in vus:
        rid = r["id"]
        propia = _todos_en_pass(rid)
        del propia["controlResults"][r["policies"][0]]
        salida = seguridad.resultado(rid, propia, senales, MATRIZ)
        t.verdadero("E-46 %s cae por su propia policy" % rid, salida["result"] != "COMPLIANT")
        for otra in vus:
            if otra["id"] == rid:
                continue
            t.no_contiene("E-46 %s no menciona a %s" % (rid, otra["id"]),
                          otra["policies"][0], " | ".join(salida["reasons"]))


def test_e47_vu2_texto_plano_no_cumple(t):
    """E-47 (S-27) — un hallazgo abierto que cita la regla la deja sin cumplir."""
    senales = _todas_las_senales()
    hallazgo = {"id": "VU2-1", "rule": "ES0902.Vu2", "scannerSeverity": "high",
                "title": "credenciales en claro sobre HTTP"}
    ev = _todos_en_pass("Vu2")
    ev["findings"] = [hallazgo]
    r = seguridad.resultado("Vu2", ev, senales, MATRIZ)
    t.igual("E-47 no cumple", "NON_COMPLIANT", r["result"])
    t.contiene("E-47 y se nombra el hallazgo", "VU2-1", " | ".join(r["reasons"]))

    # 📌 El PASS de los controles no lo tapa: el hallazgo gana. Y el mismo caso sin hallazgo si
    # cumple, o el test estaria probando que un caso imposible falla.
    t.igual("E-47 sin el hallazgo si cumple", "COMPLIANT",
            seguridad.resultado("Vu2", _todos_en_pass("Vu2"), senales, MATRIZ)["result"])
    # Un hallazgo cerrado ya no lo bloquea.
    ev["findings"] = [dict(hallazgo, status="CLOSED")]
    t.igual("E-47 un hallazgo cerrado no bloquea", "COMPLIANT",
            seguridad.resultado("Vu2", ev, senales, MATRIZ)["result"])
    # Y un hallazgo de OTRA regla no la toca.
    ev["findings"] = [dict(hallazgo, rule="ES0902.Vu3")]
    t.igual("E-47 un hallazgo de Vu3 no toca a Vu2", "COMPLIANT",
            seguridad.resultado("Vu2", ev, senales, MATRIZ)["result"])
    t.igual("E-47 pero si toca a Vu3", "NON_COMPLIANT",
            seguridad.resultado("Vu3", dict(_todos_en_pass("Vu3"), findings=ev["findings"]),
                                senales, MATRIZ)["result"])


def test_e48_vu4_es_independiente_del_token(t):
    """E-48 (S-28) — el tiempo de vida del token no prueba el vencimiento por inactividad."""
    senales = _todas_las_senales()
    t.igual("E-48 tres clases de evidencia no sirven", 3,
            len(seguridad.EVIDENCIA_QUE_NO_ES_INACTIVIDAD))
    for clase in seguridad.EVIDENCIA_QUE_NO_ES_INACTIVIDAD:
        ev = _todos_en_pass("Vu4", inactivityTimeout=[{"kind": clase, "evidence": ["oidc.json"]}])
        r = seguridad.resultado("Vu4", ev, senales, MATRIZ)
        t.verdadero("E-48 `%s` no satisface Vu4" % clase, r["result"] != "COMPLIANT")
        t.contiene("E-48 `%s` y se dice por que" % clase, "son dos cosas distintas",
                   " | ".join(r["reasons"]))

    sin_nada = _todos_en_pass("Vu4")
    t.verdadero("E-48 sin evidencia propia tampoco",
                seguridad.resultado("Vu4", sin_nada, senales, MATRIZ)["result"] != "COMPLIANT")

    propia = _todos_en_pass("Vu4", inactivityTimeout=[
        {"kind": "IDLE_SESSION_TIMEOUT", "evidence": ["web.config"]}])
    t.igual("E-48 con evidencia propia cumple", "COMPLIANT",
            seguridad.resultado("Vu4", propia, senales, MATRIZ)["result"])

    # Las dos juntas tambien: la del token no descalifica, simplemente no alcanza sola.
    las_dos = _todos_en_pass("Vu4", inactivityTimeout=[
        {"kind": "OPENID_TOKEN_LIFETIME", "evidence": ["oidc.json"]},
        {"kind": "IDLE_SESSION_TIMEOUT", "evidence": ["web.config"]}])
    t.igual("E-48 con las dos cumple", "COMPLIANT",
            seguridad.resultado("Vu4", las_dos, senales, MATRIZ)["result"])


def test_e49_vu5_solo_cliente_no_cumple(t):
    """E-49 (S-29) — sin el espejo del servidor no hay PASS."""
    senales = _todas_las_senales()
    solo_cliente = {"controlResults": {
        "client-validation-server-mirroring-required": {"result": "PASS",
                                                        "evidence": ["form.ts"]}}}
    r = seguridad.resultado("Vu5", solo_cliente, senales, MATRIZ)
    t.verdadero("E-49 no cumple", r["result"] != "COMPLIANT")
    t.contiene("E-49 falta el check de paridad", "client-server-validation-parity",
               " | ".join(r["reasons"]))

    en_fail = {"controlResults": {
        "client-validation-server-mirroring-required": {"result": "PASS", "evidence": ["a"]},
        "client-server-validation-parity": {"result": "FAIL", "evidence": ["b"]}}}
    t.igual("E-49 con la paridad en FAIL no cumple", "NON_COMPLIANT",
            seguridad.resultado("Vu5", en_fail, senales, MATRIZ)["result"])
    t.igual("E-49 con el espejo verificado si", "COMPLIANT",
            seguridad.resultado("Vu5", _todos_en_pass("Vu5"), senales, MATRIZ)["result"])


def test_e50_vu9_no_inventa_ningun_umbral(t):
    """E-50 (S-30) — ningun numero de limite que no venga de un contrato."""
    import re
    senales = _todas_las_senales()
    con = _todos_en_pass("Vu9", abuseControls=[{"mechanism": "RATE_LIMITING",
                                                "evidence": ["gateway.yaml"]}])
    r = seguridad.resultado("Vu9", con, senales, MATRIZ)
    t.verdadero("E-50 la salida no trae un umbral", "threshold" not in r)

    fuente = (BIN / "orquestacion" / "seguridad.py").read_text(encoding="utf-8")
    trozo = fuente[fuente.index("def _vu9"):fuente.index("def _vu10")]
    numeros = re.findall(r"(?<![\w_])[0-9]{2,}(?![\w_])", trozo)
    t.vacio("E-50 no hay ningun numero de dos cifras o mas en Vu9", numeros)
    for palabra in ("per_minute", "requestsPerSecond", "rpm", "maxRequests", "burst"):
        t.no_contiene("E-50 ni el identificador `%s`" % palabra, palabra, fuente)

    # 🔴 Y con un contrato SI sale, porque ahi el numero lo puso alguien que puede ponerlo.
    con_contrato = dict(con, platformContract={"threshold": 100, "source": "PLATFORM_CONTRACT"})
    r = seguridad.resultado("Vu9", con_contrato, senales, MATRIZ)
    t.igual("E-50 con un contrato el umbral sale", 100, r["threshold"]["value"])
    t.igual("E-50 con su fuente", "PLATFORM_CONTRACT", r["threshold"]["source"])


def test_e51_vu9_acepta_cualquier_mecanismo_con_evidencia(t):
    """E-51 (S-31) — el limite de tasa no es el unico compliant."""
    senales = _todas_las_senales()
    sin = _todos_en_pass("Vu9", abuseControls=[])
    r = seguridad.resultado("Vu9", sin, senales, MATRIZ)
    t.igual("E-51 sin ningun mecanismo no cumple", "NON_COMPLIANT", r["result"])
    t.contiene("E-51 y se dice por que", "sin ningun mecanismo de control de abuso",
               " | ".join(r["reasons"]))

    t.igual("E-51 hay siete mecanismos declarados", 7, len(seguridad.MECANISMOS_DE_ABUSO))
    for mecanismo in seguridad.MECANISMOS_DE_ABUSO:
        ev = _todos_en_pass("Vu9", abuseControls=[{"mechanism": mecanismo,
                                                   "evidence": ["evidencia"]}])
        r = seguridad.resultado("Vu9", ev, senales, MATRIZ)
        t.igual("E-51 `%s` alcanza" % mecanismo, "COMPLIANT", r["result"])
        t.igual("E-51 `%s` queda anotado" % mecanismo, [mecanismo], r["mechanisms"])

    # 📌 Declarado sin evidencia no alcanza: algo con forma de mecanismo no es un mecanismo.
    t.igual("E-51 declarado sin evidencia no alcanza", "NON_COMPLIANT",
            seguridad.resultado("Vu9", _todos_en_pass("Vu9", abuseControls=[
                {"mechanism": "QUOTA"}]), senales, MATRIZ)["result"])
    # Ni un mecanismo inventado.
    t.igual("E-51 un mecanismo que nadie declaro tampoco", "NON_COMPLIANT",
            seguridad.resultado("Vu9", _todos_en_pass("Vu9", abuseControls=[
                {"mechanism": "REZAR", "evidence": ["x"]}]), senales, MATRIZ)["result"])
    # Y varios juntos quedan los varios.
    varios = _todos_en_pass("Vu9", abuseControls=[
        {"mechanism": "QUOTA", "evidence": ["a"]},
        {"mechanism": "ANTI_BOT", "evidence": ["b"]}])
    t.igual("E-51 dos mecanismos quedan los dos", ["ANTI_BOT", "QUOTA"],
            seguridad.resultado("Vu9", varios, senales, MATRIZ)["mechanisms"])


def test_e52_vu10_resuelve_la_guia_por_tipo_de_activo(t):
    """E-52 (S-32) — Web, API y Mobile, con referencia, version y fecha."""
    senales = _todas_las_senales()
    esperadas = {"WEB_APPLICATION": "OWASP Top 10",
                 "WEB_SERVICE": "OWASP API Security",
                 "MOBILE_APPLICATION": "OWASP Mobile Top 10"}
    t.igual("E-52 tres tipos mapeados", esperadas, seguridad.GUIA_OWASP)

    for tipo, guia in sorted(esperadas.items()):
        ev = _todos_en_pass("Vu10", assetTypes=[tipo], owaspGuidance=[
            {"reference": guia, "version": "2023", "date": "2023-06-01"}])
        r = seguridad.resultado("Vu10", ev, senales, MATRIZ)
        t.igual("E-52 %s espera `%s`" % (tipo, guia), [guia], r["expectedGuidance"])
        t.igual("E-52 %s cumple con esa guia" % tipo, "COMPLIANT", r["result"])
        t.igual("E-52 %s conserva referencia, version y fecha" % tipo,
                {"reference": guia, "version": "2023", "date": "2023-06-01"},
                r["guidance"][guia])
        # La guia de OTRO tipo no lo satisface.
        otra = [g for g in esperadas.values() if g != guia][0]
        cruzado = _todos_en_pass("Vu10", assetTypes=[tipo], owaspGuidance=[
            {"reference": otra, "version": "2023", "date": "2023-06-01"}])
        t.verdadero("E-52 %s no se satisface con `%s`" % (tipo, otra),
                    seguridad.resultado("Vu10", cruzado, senales,
                                        MATRIZ)["result"] != "COMPLIANT")

    # Dos tipos a la vez esperan las dos guias.
    dos = _todos_en_pass("Vu10", assetTypes=["WEB_APPLICATION", "WEB_SERVICE"])
    t.igual("E-52 dos tipos esperan dos guias",
            ["OWASP API Security", "OWASP Top 10"],
            seguridad.resultado("Vu10", dos, senales, MATRIZ)["expectedGuidance"])

    # 🔴 Y no hay ninguna lista de categorias historicas cacheada adentro del modulo.
    fuente = (BIN / "orquestacion" / "seguridad.py").read_text(encoding="utf-8")
    for categoria in ("A01", "A02", "Injection", "Broken Access Control",
                      "Cryptographic Failures", "SSRF"):
        t.no_contiene("E-52 no hay categoria cacheada `%s`" % categoria, categoria, fuente)


def test_e53_vu10_una_referencia_desconocida_queda_explicita(t):
    """E-53 (S-33) — no se completa con una lista cacheada, se dice que falta."""
    senales = _todas_las_senales()
    # Un tipo que ES0902 no mapea: no se le elige una guia por parecido.
    for tipo in ("SERVER", "TOTEM"):
        ev = _todos_en_pass("Vu10", assetTypes=[tipo])
        r = seguridad.resultado("Vu10", ev, senales, MATRIZ)
        t.contiene("E-53 %s queda explicito" % tipo, "EXTERNAL_NORMATIVE_CONTEXT_REQUIRED",
                   repr(r["states"]))
        t.contiene("E-53 %s y se dice que no hay mapeo" % tipo, "no mapea guia OWASP",
                   " | ".join(r["reasons"]))
        t.vacio("E-53 %s sin guia esperada" % tipo, r["expectedGuidance"])

    # Una referencia sin version o sin fecha queda incompleta, no se completa sola.
    for falta in ("version", "date"):
        guia = {"reference": "OWASP Top 10", "version": "2021", "date": "2021-09-24"}
        del guia[falta]
        ev = _todos_en_pass("Vu10", assetTypes=["WEB_APPLICATION"], owaspGuidance=[guia])
        r = seguridad.resultado("Vu10", ev, senales, MATRIZ)
        t.verdadero("E-53 sin `%s` no cumple" % falta, r["result"] != "COMPLIANT")
        t.contiene("E-53 sin `%s` se dice cual" % falta, "sin version o sin fecha",
                   " | ".join(r["reasons"]))
        t.verdadero("E-53 sin `%s` no se inventa el campo" % falta,
                    "OWASP Top 10" not in (r.get("guidance") or {}))


# -- Aceptacion: G2, G3 y G4 ---------------------------------------------------

def test_e54_g2_con_algo_por_encima_de_low_no_da(t):
    """E-54 (S-35) — uno solo alcanza para no satisfacer el umbral."""
    u = evaluacion.umbral(_hallazgos(bajos=0, mayores=1), MAPEO_AUTORITATIVO)
    t.verdadero("E-54 no se satisface", not u["satisfied"])
    t.igual("E-54 se cuenta uno por encima", 1, u["aboveLowCount"])
    t.contiene("E-54 y se dice", "por encima de LOW", " | ".join(u["reasons"]))
    t.verdadero("E-54 no aparece el resultado interno", "result" not in u)

    # Aun con cero LOW, y aun mezclado con LOW por debajo del maximo.
    u = evaluacion.umbral(_hallazgos(bajos=3, mayores=1), MAPEO_AUTORITATIVO)
    t.verdadero("E-54 con tres LOW y uno mayor tampoco", not u["satisfied"])
    t.igual("E-54 los LOW se cuentan igual", 3, u["lowCount"])

    senales = _todas_las_senales()
    ev = _todos_en_pass("G2", findings=_hallazgos(mayores=1), riskMapping=MAPEO_AUTORITATIVO)
    t.igual("E-54 y la regla G2 no cumple", "NON_COMPLIANT",
            seguridad.resultado("G2", ev, senales, MATRIZ)["result"])


def test_e55_g2_con_mas_de_diez_low_no_da(t):
    """E-55 (S-36) — el maximo es diez, y once ya es once."""
    t.igual("E-55 el maximo declarado", 10, evaluacion.MAXIMO_DE_BAJOS)
    u = evaluacion.umbral(_hallazgos(bajos=11), MAPEO_AUTORITATIVO)
    t.verdadero("E-55 once no da", not u["satisfied"])
    t.igual("E-55 se cuentan once", 11, u["lowCount"])
    t.contiene("E-55 y se dice el maximo", "el maximo es 10", " | ".join(u["reasons"]))
    t.verdadero("E-55 el maximo viaja en la salida", u["maxLowAllowed"] == 10)
    # Un hallazgo cerrado no cuenta: doce con uno cerrado son once abiertos, y siguen sin dar.
    docena = _hallazgos(bajos=11) + [{"id": "X", "scannerSeverity": "low", "status": "CLOSED"}]
    t.verdadero("E-55 un cerrado no suma", not evaluacion.umbral(docena,
                                                                MAPEO_AUTORITATIVO)["satisfied"])
    t.igual("E-55 y no se cuenta", 11, evaluacion.umbral(docena, MAPEO_AUTORITATIVO)["lowCount"])


def test_e56_g2_con_hasta_diez_low_da(t):
    """E-56 (S-37) — exactamente en el borde, y por debajo."""
    for cuantos in (0, 1, 9, 10):
        u = evaluacion.umbral(_hallazgos(bajos=cuantos), MAPEO_AUTORITATIVO)
        t.verdadero("E-56 con %d LOW da" % cuantos, u["satisfied"])
        t.igual("E-56 con %d LOW el resultado interno" % cuantos,
                "G2_THRESHOLD_SATISFIED", u["result"])
        t.igual("E-56 con %d LOW se cuentan bien" % cuantos, cuantos, u["lowCount"])
        t.igual("E-56 con %d LOW ninguno mayor" % cuantos, 0, u["aboveLowCount"])
    senales = _todas_las_senales()
    ev = _todos_en_pass("G2", findings=_hallazgos(bajos=10), riskMapping=MAPEO_AUTORITATIVO)
    r = seguridad.resultado("G2", ev, senales, MATRIZ)
    t.igual("E-56 y la regla G2 cumple", "COMPLIANT", r["result"])
    t.igual("E-56 con su resultado interno", "G2_THRESHOLD_SATISFIED", r["internalResult"])


def test_e57_sin_mapeo_autoritativo_no_se_calcula(t):
    """E-57 (S-39) — VULNERABILITY_RISK_MAPPING_UNRESOLVED, y el umbral NO se calcula igual."""
    # 📌 `"false"` —el string— y `1` son verdaderos para Python y no son `True`. Un productor que
    # mande el flag malformado no puede habilitar el cálculo: se compara por identidad, no por
    # verdad. Lo señaló el refutador como observación menor y costaba una línea.
    for mapeo in (None, {}, {"map": {"low": "LOW"}},
                  {"authoritative": True, "map": {"low": "LOW"}},
                  {"authoritative": False, "evidence": ["x"], "map": {"low": "LOW"}},
                  {"authoritative": "false", "evidence": ["x"], "map": {"low": "LOW"}},
                  {"authoritative": "true", "evidence": ["x"], "map": {"low": "LOW"}},
                  {"authoritative": 1, "evidence": ["x"], "map": {"low": "LOW"}}):
        u = evaluacion.umbral(_hallazgos(bajos=1), mapeo)
        t.verdadero("E-57 con %r no se satisface" % sorted(mapeo or {}), not u["satisfied"])
        t.contiene("E-57 con %r sale el estado" % sorted(mapeo or {}),
                   "VULNERABILITY_RISK_MAPPING_UNRESOLVED", repr(u["states"]))
        # 🔴 Lo que importa: NO se calculo. Un conteo publicado seria un umbral evaluado con
        # las etiquetas crudas del escaner, que es justo la equivalencia que nadie firmo.
        t.igual("E-57 con %r no hay conteo de LOW" % sorted(mapeo or {}), None, u["lowCount"])
        t.igual("E-57 con %r no hay conteo de mayores" % sorted(mapeo or {}), None,
                u["aboveLowCount"])

    # Una severidad que el mapeo no cubre deja todo sin resolver, aunque las otras si esten.
    u = evaluacion.umbral([{"id": "A", "scannerSeverity": "low"},
                           {"id": "B", "scannerSeverity": "informational"}], MAPEO_AUTORITATIVO)
    t.contiene("E-57 una severidad sin mapear deja todo sin resolver",
               "VULNERABILITY_RISK_MAPPING_UNRESOLVED", repr(u["states"]))
    t.contiene("E-57 y se dice cual", "B", " | ".join(u["reasons"]))
    t.igual("E-57 sin conteo", None, u["lowCount"])

    senales = _todas_las_senales()
    ev = _todos_en_pass("G2", findings=_hallazgos(bajos=1))
    r = seguridad.resultado("G2", ev, senales, MATRIZ)
    t.igual("E-57 la regla G2 queda sin resolver", "UNRESOLVED", r["result"])


def test_e58_el_umbral_nunca_produce_aprobacion(t):
    """E-58 (S-38) — satisfacerlo y aprobar son dos hechos distintos."""
    u = evaluacion.umbral(_hallazgos(bajos=2), MAPEO_AUTORITATIVO)
    t.verdadero("E-58 el umbral da", u["satisfied"])
    t.igual("E-58 y el estado oficial sigue sin resolver", "OFFICIAL_STATUS_UNRESOLVED",
            u["officialState"])
    t.no_contiene("E-58 la salida no dice APPROVED", "APPROVED", repr(u))

    senales = _todas_las_senales()
    ev = _todos_en_pass("G2", findings=_hallazgos(bajos=2), riskMapping=MAPEO_AUTORITATIVO)
    r = seguridad.resultado("G2", ev, senales, MATRIZ)
    t.igual("E-58 la regla cumple", "COMPLIANT", r["result"])
    t.igual("E-58 y el estado oficial tampoco se movio", "OFFICIAL_STATUS_UNRESOLVED",
            r["officialState"])

    # 📌 `G2_THRESHOLD_SATISFIED` es un resultado INTERNO, no un estado del flujo.
    t.verdadero("E-58 no es un estado del flujo",
                "G2_THRESHOLD_SATISFIED" not in evaluacion.ESTADOS)
    t.verdadero("E-58 es un resultado interno",
                "G2_THRESHOLD_SATISFIED" in evaluacion.RESULTADOS_INTERNOS)
    pedido = evaluacion.resultado_interno({"result": "G2_THRESHOLD_SATISFIED",
                                           "producer": "HARNESS_THRESHOLD_CALCULATION"})
    t.igual("E-58 el calculo si lo puede declarar", "G2_THRESHOLD_SATISFIED", pedido["result"])
    t.igual("E-58 y no puede declarar APPROVED", None,
            evaluacion.resultado_interno({"result": "APPROVED",
                                          "producer": "HARNESS_THRESHOLD_CALCULATION"})["result"])


def test_e59_g3_exige_el_cien_por_ciento(t):
    """E-59 (S-40) — con uno sin recontrolar, no alcanza. Y se conserva su identidad."""
    senales = _todas_las_senales()
    previos = [{"id": "F%d" % i} for i in range(1, 6)]
    todos = [{"findingId": f["id"], "evidence": ["retest-%s" % f["id"]]} for f in previos]

    completo = _todos_en_pass("G3", previousFindings=previos, retests=todos,
                              findings=[], riskMapping=MAPEO_AUTORITATIVO)
    r = seguridad.resultado("G3", completo, senales, MATRIZ)
    t.igual("E-59 con el 100% cumple", "COMPLIANT", r["result"])
    t.igual("E-59 cinco previos", 5, r["previousFindingCount"])
    t.igual("E-59 cinco recontrolados", 5, r["retestedCount"])
    t.vacio("E-59 ninguno sin recontrolar", r["notRetested"])

    for faltan in (1, 2, 5):
        parcial = _todos_en_pass("G3", previousFindings=previos, retests=todos[:5 - faltan],
                                 findings=[], riskMapping=MAPEO_AUTORITATIVO)
        r = seguridad.resultado("G3", parcial, senales, MATRIZ)
        t.igual("E-59 con %d sin recontrolar no cumple" % faltan, "NON_COMPLIANT", r["result"])
        t.igual("E-59 y se nombran los %d" % faltan, faltan, len(r["notRetested"]))
        t.contiene("E-59 con su identidad conservada (%d)" % faltan, "F5",
                   " | ".join(r["notRetested"]))

    # Un retest declarado SIN evidencia no recontrola nada.
    sin_evidencia = _todos_en_pass("G3", previousFindings=previos,
                                   retests=[{"findingId": f["id"]} for f in previos],
                                   findings=[], riskMapping=MAPEO_AUTORITATIVO)
    t.igual("E-59 retests sin evidencia no cuentan", "NON_COMPLIANT",
            seguridad.resultado("G3", sin_evidencia, senales, MATRIZ)["result"])
    # Y un reenvio sin reporte previo no se puede recontrolar: queda sin resolver.
    vacio = _todos_en_pass("G3", previousFindings=[], retests=[],
                           findings=[], riskMapping=MAPEO_AUTORITATIVO)
    t.igual("E-59 sin reporte previo queda sin resolver", "UNRESOLVED",
            seguridad.resultado("G3", vacio, senales, MATRIZ)["result"])


def test_e60_g3_sigue_evaluando_g2(t):
    """E-60 (S-41) — recontrolar todo no exime del umbral."""
    senales = _todas_las_senales()
    previos = [{"id": "F1"}]
    retests = [{"findingId": "F1", "evidence": ["retest"]}]
    ev = _todos_en_pass("G3", previousFindings=previos, retests=retests,
                        findings=_hallazgos(mayores=1), riskMapping=MAPEO_AUTORITATIVO)
    r = seguridad.resultado("G3", ev, senales, MATRIZ)
    t.verdadero("E-60 G2 se evaluo", r["g2Applies"])
    t.verdadero("E-60 y no se satisfizo", not r["threshold"]["satisfied"])
    t.igual("E-60 con el 100% recontrolado pero un hallazgo mayor, no cumple",
            "NON_COMPLIANT", r["result"])
    t.contiene("E-60 y se dice por el umbral", "por encima de LOW", " | ".join(r["reasons"]))

    # Sin mapeo autoritativo, el 100% recontrolado tampoco alcanza para cumplir.
    sin_mapeo = _todos_en_pass("G3", previousFindings=previos, retests=retests,
                               findings=_hallazgos(bajos=1))
    r = seguridad.resultado("G3", sin_mapeo, senales, MATRIZ)
    t.verdadero("E-60 sin mapeo no cumple", r["result"] != "COMPLIANT")
    t.contiene("E-60 con el estado del mapeo", "VULNERABILITY_RISK_MAPPING_UNRESOLVED",
               repr(r["states"]))


def test_e61_g4_exige_alcance_completo(t):
    """E-61 (S-42) — no solo los hallazgos previos, y los nuevos entran."""
    senales = _todas_las_senales()
    solo_previos = _todos_en_pass("G4", assessmentScope="PREVIOUS_FINDINGS_ONLY",
                                  findings=[], riskMapping=MAPEO_AUTORITATIVO)
    r = seguridad.resultado("G4", solo_previos, senales, MATRIZ)
    t.igual("E-61 limitada a los previos no cumple", "NON_COMPLIANT", r["result"])
    t.contiene("E-61 y se dice por que", "alcance completo", " | ".join(r["reasons"]))

    sin_declarar = _todos_en_pass("G4", findings=[], riskMapping=MAPEO_AUTORITATIVO)
    r = seguridad.resultado("G4", sin_declarar, senales, MATRIZ)
    t.verdadero("E-61 sin declarar el alcance tampoco", r["result"] != "COMPLIANT")
    t.contiene("E-61 con el estado", "SECURITY_CONTROL_EVIDENCE_MISSING", repr(r["states"]))

    completo = _todos_en_pass("G4", assessmentScope="FULL", findings=[],
                              riskMapping=MAPEO_AUTORITATIVO)
    r = seguridad.resultado("G4", completo, senales, MATRIZ)
    t.igual("E-61 de alcance completo cumple", "COMPLIANT", r["result"])
    t.verdadero("E-61 y los hallazgos nuevos estan permitidos", r["newFindingsAllowed"])

    # Un hallazgo nuevo aparece y se evalua; no se descarta por no ser previo.
    con_nuevo = _todos_en_pass("G4", assessmentScope="FULL",
                               findings=_hallazgos(bajos=3), riskMapping=MAPEO_AUTORITATIVO)
    r = seguridad.resultado("G4", con_nuevo, senales, MATRIZ)
    t.igual("E-61 tres hallazgos nuevos se cuentan", 3, r["threshold"]["lowCount"])
    t.igual("E-61 y siguen debajo del umbral", "COMPLIANT", r["result"])


def test_e62_g4_sigue_evaluando_g2(t):
    """E-62 (S-43) — reevaluar entero no exime del umbral."""
    senales = _todas_las_senales()
    ev = _todos_en_pass("G4", assessmentScope="FULL", findings=_hallazgos(bajos=11),
                        riskMapping=MAPEO_AUTORITATIVO)
    r = seguridad.resultado("G4", ev, senales, MATRIZ)
    t.verdadero("E-62 G2 se evaluo", r["g2Applies"])
    t.igual("E-62 once LOW no satisfacen", 11, r["threshold"]["lowCount"])
    t.igual("E-62 y G4 no cumple", "NON_COMPLIANT", r["result"])

    mayor = _todos_en_pass("G4", assessmentScope="FULL", findings=_hallazgos(mayores=1),
                           riskMapping=MAPEO_AUTORITATIVO)
    t.igual("E-62 un hallazgo nuevo mayor tampoco", "NON_COMPLIANT",
            seguridad.resultado("G4", mayor, senales, MATRIZ)["result"])
    # Y G3 y G4 no se colapsan: son dos reglas con dos senales y dos algoritmos.
    t.verdadero("E-62 G3 y G4 tienen senales distintas",
                seguridad.regla("G3", MATRIZ)["applicability"]["signals"]
                != seguridad.regla("G4", MATRIZ)["applicability"]["signals"])
    t.verdadero("E-62 y algoritmos distintos",
                seguridad.ALGORITMOS["G3"] is not seguridad.ALGORITMOS["G4"])


# -- Los activos de seguridad que ya existen -----------------------------------

def test_e63_no_se_crea_ningun_agente(t):
    """E-63 (S-44) — los mismos diez, y `dev-security` sigue siendo el unico de seguridad."""
    registro = c_reg.cargar()
    ids = sorted(a["id"] for a in registro["agents"])
    t.igual("E-63 siguen siendo diez", 10, len(ids))
    t.igual("E-63 y son los mismos",
            ["dev-architecture", "dev-backend", "dev-devops", "dev-frontend", "dev-integration",
             "dev-orchestrator", "dev-quality", "dev-refutador", "dev-security",
             "dev-tool-builder"], ids)
    seguridad_ids = [i for i in ids if "security" in i or "seguridad" in i]
    t.igual("E-63 uno solo de seguridad", ["dev-security"], seguridad_ids)

    # 🔴 El barrido tiene que ser sobre el REGISTRO y sobre el disco: un archivo que aparece
    # solo no da de alta un agente, pero un archivo que aparece solo tampoco puede estar.
    archivos = sorted(p.stem for p in
                      (RAIZ / "harnesses" / "desarrollo" / "agents").glob("*.md"))
    t.verdadero("E-63 no hay un agente de seguridad de mas en disco",
                [a for a in archivos if "security" in a] == ["dev-security"])
    t.no_contiene("E-63 la matriz no nombra ningun agente nuevo", "dev-appsec",
                  json.dumps(MATRIZ, ensure_ascii=False))


def test_e64_las_skills_de_seguridad_siguen_siendo_la_capa(t):
    """E-64 (S-45) — las cuatro que existen, sin redefinir ni cambiar de dueno."""
    registro = c_reg.cargar()
    de_security = [a for a in registro["agents"] if a["id"] == "dev-security"][0]
    skills = sorted(s["id"] for s in de_security.get("skills") or [])
    t.igual("E-64 las cuatro skills de dev-security",
            ["dev-appsec-review", "dev-security-analysis", "dev-security-assessment",
             "dev-vulnerability-management"], skills)

    # Ninguna otra agente se las lleva.
    for a in registro["agents"]:
        if a["id"] == "dev-security":
            continue
        ajenas = [s["id"] for s in a.get("skills") or [] if s["id"] in skills]
        t.vacio("E-64 `%s` no se lleva ninguna" % a["id"], ajenas)

    # Y ES0902 no declara ninguna skill: la matriz no tiene ese campo y no lo inventa.
    for r in MATRIZ["rules"]:
        t.verdadero("E-64 %s no declara skills" % r["id"], "skills" not in r)
    t.no_contiene("E-64 y la matriz no nombra una skill nueva", "dev-security-",
                  json.dumps(MATRIZ, ensure_ascii=False))


# -- Fallo cerrado, y el arbol instalado ---------------------------------------

def test_e65_los_ocho_estados_globales_con_ese_nombre(t):
    """E-65 (S-03) — ninguno se llama parecido, y todos se emiten."""
    t.igual("E-65 son ocho", 8, len(seguridad.ESTADOS_GLOBALES))
    t.igual("E-65 y son estos", sorted(LOS_8_ESTADOS), sorted(seguridad.ESTADOS_GLOBALES))

    senales = _todas_las_senales()
    emitidos = set()
    # Cada uno sale de un caso real, no de leer la constante.
    emitidos |= set(seguridad.resultado(
        "Vu2", {"overrides": [_excepcion(contrato="PROJECT_CONTRACT")]},
        senales, MATRIZ)["states"])
    emitidos |= set(cruzada.resolver(["D1"], ["C1"], {}, MAPA)["states"])
    emitidos |= set(cruzada.resolver(["P5"], ["Vu5"], {}, MAPA)["states"])
    emitidos.add(evaluacion.estado_oficial(_oficial("APPROVED", "AUTOMATED_SCAN"))["state"])
    emitidos |= set(evaluacion.requisito_de_waf(["WEB_SERVICE"], {})["states"])
    emitidos |= set(evaluacion.umbral(_hallazgos(bajos=1), None)["states"])
    emitidos |= set(evaluacion.entregables(["TOTEM"])["states"])
    emitidos |= set(seguridad.resultado("Ve2", {}, senales, MATRIZ)["states"])

    for estado in LOS_8_ESTADOS:
        t.verdadero("E-65 `%s` se emite de verdad" % estado, estado in emitidos)


def test_e66_un_estado_desconocido_falla_cerrado(t):
    """E-66 — no cae en PASS, no cae en APPROVED, y se dice cual era."""
    for inventado in ("SECURITY_APPROVED", "OK", "COMPLIANT", "APROBADO", "Approved"):
        r = evaluacion.estado_oficial(_oficial(inventado, "GCBA_DGSEI"))
        t.igual("E-66 `%s` no se acepta" % inventado, "OFFICIAL_STATUS_UNRESOLVED", r["state"])
        t.contiene("E-66 `%s` se dice cual era" % inventado, inventado, repr(r["requestedState"]))
        t.contiene("E-66 `%s` con su estado" % inventado, "SECURITY_ASSESSMENT_STATE_UNKNOWN",
                   repr(r["states"]))
        interno = evaluacion.resultado_interno({"result": inventado,
                                                "producer": "AUTOMATED_SCAN"})
        t.igual("E-66 `%s` tampoco como resultado interno" % inventado, None, interno["result"])

    # Un resultado de regla nunca sale con un valor que no este declarado.
    senales = _todas_las_senales()
    for r in seguridad.resultados({}, senales, MATRIZ):
        t.verdadero("E-66 %s tiene un resultado declarado" % r["rule"],
                    r["result"] in seguridad.RESULTADOS)
    t.igual("E-66 cinco resultados posibles", 5, len(seguridad.RESULTADOS))

    # 🔴 Una regla que no declara NINGUN control no cumple al vacio. Ninguna de las 21 esta hoy
    # en ese caso, y por eso hay que fabricarlo: cumplir sobre un conjunto vacio de controles es
    # la forma mas barata de que un estandar entero salga verde el dia que alguien agregue una
    # fila sin clasificar.
    hueca = dict(seguridad.regla("Vu7", MATRIZ), policies=[], checks=[], reviews=[])
    doc_hueco = dict(MATRIZ, rules=[hueca if r["id"] == "Vu7" else r for r in MATRIZ["rules"]])
    r = seguridad.resultado("Vu7", {"controlResults": {}}, senales, doc_hueco)
    t.verdadero("E-66 una regla sin controles no cumple", r["result"] != "COMPLIANT")
    t.igual("E-66 queda sin resolver", "UNRESOLVED", r["result"])
    t.contiene("E-66 con el estado que lo dice", "SECURITY_RULE_DECLARES_NO_CONTROL",
               repr(r["states"]))
    t.contiene("E-66 y el motivo", "no hay contra que medir", " | ".join(r["reasons"]))
    # Y la de verdad, con sus dos controles, si cumple cuando los tiene.
    t.igual("E-66 la Vu7 real con evidencia cumple", "COMPLIANT",
            seguridad.resultado("Vu7", _todos_en_pass("Vu7"), senales, MATRIZ)["result"])


def _arbol(tmp, omitir=(), romper=()):
    """La forma que deja el instalador: `reglas/` colgando de `.claude/harness/`."""
    binario = Path(tmp) / ".claude" / "harness" / "bin" / "desarrollo" / "orquestacion"
    reglas_h = Path(tmp) / ".claude" / "harness" / "reglas"
    reglas_d = reglas_h / "desarrollo"
    esquemas = Path(tmp) / ".claude" / "harness" / "schemas"
    for d in (binario, reglas_d, esquemas):
        d.mkdir(parents=True)
    (reglas_h / "secretos.patrones.json").write_text("{}", encoding="utf-8")
    for nombre in ("es0902-6.2-normative-matrix.json", "es0902-cross-standard-map.json",
                   "es0902-security-deliverables.json", "es0901-7.1-normative-matrix.json",
                   "agent-registry.json", "control-registry.json"):
        if nombre in omitir:
            continue
        if nombre in romper:
            (reglas_d / nombre).write_text("{ esto no es json", encoding="utf-8")
            continue
        shutil.copy(str(REGLAS / nombre), str(reglas_d / nombre))
    for esquema in SCHEMAS.glob("*.schema.json"):
        shutil.copy(str(esquema), str(esquemas / esquema.name))
    desde = binario / "seguridad.py"
    desde.write_text("# marcador\n", encoding="utf-8")
    return desde


def test_e67_un_estandar_roto_no_se_lleva_al_otro(t):
    """E-67 — se falla cerrado con el estado, y ES0901 sigue resolviendo."""
    for caso, kwargs in (("ausente", {"omitir": ("es0902-6.2-normative-matrix.json",)}),
                         ("ilegible", {"romper": ("es0902-6.2-normative-matrix.json",)})):
        tmp = tempfile.mkdtemp(prefix="es0902-%s" % caso)
        try:
            desde = _arbol(tmp, **kwargs)
            try:
                seguridad.cargar(str(desde))
                t.verdadero("E-67 %s: se rechaza" % caso, False)
            except seguridad.SeguridadInvalida as e:
                t.verdadero("E-67 %s: se rechaza con su motivo" % caso, bool(str(e)))

            bloque = c_normativa.resolucion({}, str(desde))
            t.igual("E-67 %s: ES0901 sigue resolviendo" % caso, "ES0901",
                    bloque["standard"]["id"])
            t.igual("E-67 %s: y sigue con sus 24 reglas" % caso, 24,
                    len(bloque["applicableRules"]) + len(bloque["notApplicableRules"])
                    + len(bloque["unresolvedRules"]))
            t.verdadero("E-67 %s: ES0902 esta y dice que fallo" % caso,
                        bool(bloque["standards"]["ES0902"].get("error")))
            t.vacio("E-67 %s: sin reglas aplicables de ES0902" % caso,
                    bloque["standards"]["ES0902"]["applicableRules"])
            # 🔴 Y las senales de ES0901 siguen declaradas: un estandar roto no borra al otro.
            declaradas = c_senales.declaradas(str(desde))
            t.verdadero("E-67 %s: las de ES0901 siguen" % caso,
                        "citizenFacing" in declaradas)
            t.verdadero("E-67 %s: las de ES0902 no estan" % caso,
                        "sessionPresent" not in declaradas)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def test_e68_los_tres_modulos_arrancan_instalados(t):
    """E-68 — `reglas/` cuelga a distinta altura instalado, y por eso existe `roster`.

    🔴 Es lo que decide si la capacidad EXISTE en un proyecto. Verde donde corre la suite y
    muerta donde corre el harness es el defecto que este escenario esta para encontrar.
    """
    for nombre in ("seguridad.py", "evaluacion.py", "cruzada.py"):
        fuente = (BIN / "orquestacion" / nombre).read_text(encoding="utf-8")
        t.contiene("E-68 %s busca con roster" % nombre, "roster.ruta_de_regla", fuente)
        t.verdadero("E-68 %s no usa una localizacion sin raices extra" % nombre,
                    'rutas.localizar(("reglas"' not in fuente)

    tmp = tempfile.mkdtemp(prefix="es0902-inst")
    try:
        desde = _arbol(tmp)
        t.igual("E-68 una localizacion sin raices extra no lo encuentra", None,
                rutas_mod.localizar(("reglas", "es0902-6.2-normative-matrix.json"), str(desde)))
        t.verdadero("E-68 y roster si",
                    bool(c_roster.ruta_de_regla("es0902-6.2-normative-matrix.json", str(desde))))

        doc = seguridad.cargar(str(desde))
        t.igual("E-68 la matriz carga instalada", 21, len(doc["rules"]))
        t.igual("E-68 y resuelve", "ES0902", seguridad.resolver({}, doc)["standard"]["id"])
        r = seguridad.resultado("Vu2", {}, _todas_las_senales(), doc, str(desde))
        t.igual("E-68 y una regla se resuelve", "Vu2", r["rule"])

        mapa = cruzada.cargar(str(desde))
        t.igual("E-68 el mapa cruzado carga instalado", 8, len(mapa["relations"]))
        entregables = evaluacion.cargar_entregables(str(desde))
        t.igual("E-68 los entregables cargan instalados", 5, len(entregables["assetTypes"]))
        t.igual("E-68 y se resuelven", ["E1"],
                evaluacion.entregables(["WEB_SERVICE"], {}, entregables)["sourceIds"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_e69_los_modulos_no_tienen_como_conseguir_un_secreto(t):
    """E-69 — no importan el almacen, no leen el ambiente, y abren sus tres archivos y nada mas.

    🔴 La proposicion honesta: un valor sale solo si el que llama lo metio en la evidencia. Lo
    que se verifica es que los modulos no tengan NINGUNA via propia de conseguir uno.
    """
    import ast
    for nombre in ("seguridad.py", "evaluacion.py", "cruzada.py"):
        ruta = BIN / "orquestacion" / nombre
        fuente = ruta.read_text(encoding="utf-8")
        arbol = ast.parse(fuente)
        importados = set()
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                importados |= {a.name.split(".")[0] for a in nodo.names}
            elif isinstance(nodo, ast.ImportFrom):
                importados |= {a.name for a in nodo.names}
        for prohibido in ("almacen", "integraciones", "subprocess", "socket", "urllib",
                          "requests", "keyring"):
            t.verdadero("E-69 %s no importa `%s`" % (nombre, prohibido),
                        prohibido not in importados)
        for via in ("os.environ", "getenv", "getpass", "input("):
            t.no_contiene("E-69 %s no usa `%s`" % (nombre, via), via, fuente)

        # Los unicos archivos que abre son los que declara como constante de modulo.
        # 🔴 Las DOS formas de llamar. `getattr(n.func, "attr", "")` ve `io.open(...)` y no ve un
        # `open(...)` pelado, donde `n.func` es un `ast.Name` sin `attr`: hoy los tres módulos
        # usan `io.open`, así que el barrido se sostenía de casualidad y se caía el día que
        # alguien escribiera la forma corta. Lo encontró el refutador.
        abiertos = [n for n in ast.walk(arbol) if isinstance(n, ast.Call)
                    and (getattr(n.func, "attr", "") == "open"
                         or getattr(n.func, "id", "") == "open")]
        t.verdadero("E-69 %s abre a lo sumo dos archivos" % nombre, len(abiertos) <= 2)
        t.vacio("E-69 %s no llama a `open` pelado" % nombre,
                [n for n in ast.walk(arbol) if isinstance(n, ast.Call)
                 and getattr(n.func, "id", "") == "open"])

    # Y ninguna salida trae una clave con pinta de secreto.
    senales = _todas_las_senales()
    salida = repr([seguridad.resultados({}, senales, MATRIZ), seguridad.resolver(senales),
                   cruzada.resolver(list(c_matriz.INVENTARIO), list(LAS_21), {}, MAPA),
                   evaluacion.entregables(evaluacion.tipos_de_activo()),
                   evaluacion.umbral(_hallazgos(bajos=1), MAPEO_AUTORITATIVO)])
    for clave in ("password", "passwd", "secretValue", "apiKey", "privateKey", "token="):
        t.no_contiene("E-69 la salida no trae `%s`" % clave, clave, salida)


def test_e70_lo_declarado_no_finge_estar_instalado(t):
    """E-70 — nueve policies, siete checks y una review declarados y sin construir."""
    resolucion = seguridad.resolver(_todas_las_senales())
    t.igual("E-70 con todas las senales aplican las 21", 21, len(resolucion["applicableRules"]))
    t.igual("E-70 veintitres policies declaradas", 23, len(resolucion["declaredPolicies"]))
    t.igual("E-70 diecinueve checks declarados", 19, len(resolucion["declaredChecks"]))
    t.igual("E-70 dos reviews declaradas", 2, len(resolucion["declaredReviews"]))

    faltan = seguridad.controles_no_instalados(resolucion)
    por_estado = {}
    for f in faltan:
        por_estado[f["state"]] = por_estado.get(f["state"], 0) + 1
    t.igual("E-70 nueve policies no instaladas", 9,
            por_estado.get("DECLARED_POLICY_NOT_INSTALLED"))
    t.igual("E-70 siete checks no instalados", 7,
            por_estado.get("DECLARED_CHECK_NOT_INSTALLED"))
    t.igual("E-70 una review no instalada", 1,
            por_estado.get("DECLARED_REVIEW_NOT_INSTALLED"))
    t.igual("E-70 diecisiete huecos en total", 17, len(faltan))

    # 🔴 Y eso NO invalida la matriz: es el estado correcto de un harness que clasifico antes
    # de construir. Los seis que si estan instalados son los compartidos con ES0901.
    veredicto, errores = seguridad.validar(MATRIZ)
    t.igual("E-70 la matriz sigue valida", "NORMATIVE_MATRIX_VALID", veredicto)
    instalados = set(c_controles.instalados(REGISTRO)["POLICY"]) \
        | set(c_controles.instalados(REGISTRO)["CHECK"])
    declarados = set(resolucion["declaredPolicies"]) | set(resolucion["declaredChecks"])
    t.igual("E-70 veintiseis de los declarados por ES0902 ya estan instalados", 26,
            len(declarados & instalados))
    # Los seis compartidos con ES0901, mas los veinte de O1, O2, C1, C2, Vu1, Vu2, Vu3, Vu4, Vu5 y Vu6 que no comparten nada:
    # salen de ES0902 secciones 3 y 6 y de ningun otro lado. La review de O1 no entra en esta cuenta, que es de
    # policies y checks.
    t.igual("E-70 y son los compartidos mas los de O1, O2, C1, C2, Vu1, Vu2, Vu3, Vu4, Vu5 y Vu6",
            sorted(set(cruzada.controles_compartidos(MAPA))
                   | {"gcba-it-security-normative-compliance-required",
                      "gcba-security-control-authority-required",
                      "security-control-authority-evidence",
                    "openid-connect-authentication-required",
                    "dgsei-keycloak-provider-required", "oidc-keycloak-integration",
                    "qa-security-approval-required", "qa-security-approval-evidence",
                    "authentication-abuse-protection-required",
                    "authentication-abuse-protection",
                    "sensitive-data-plaintext-transmission-prohibited",
                    "sensitive-data-transport-protection",
                    "browser-close-session-termination-required",
                    "browser-close-session-termination",
                    "session-inactivity-timeout-required",
                    "session-inactivity-timeout",
                    "client-validation-server-mirroring-required",
                    "client-server-validation-parity",
                    "custom-error-messages-required",
                    "custom-error-message-compliance"}),
            sorted(declarados & instalados))
    t.verdadero("E-70 la review de O1 tambien esta instalada",
                "gcba-it-security-normative-review"
                in c_controles.instalados(REGISTRO)["REVIEW"])


def test_e71_un_id_declarado_con_dos_tipos_se_reporta(t):
    """E-71 — la matriz provista no se corrige: se reporta la colision y se sigue."""
    colisiones = seguridad.colisiones_de_id(MATRIZ)
    t.igual("E-71 hay una colision", 1, len(colisiones))
    t.igual("E-71 y es la del umbral", "security-vulnerability-acceptance-threshold",
            colisiones[0]["id"])
    t.igual("E-71 declarado como los dos tipos", ["CHECK", "POLICY"], colisiones[0]["types"])
    t.igual("E-71 con su estado", "SECURITY_CONTROL_ID_TYPE_COLLISION", colisiones[0]["state"])

    # 🔴 El archivo provisto queda como vino: corregir normativa provista es inventarla.
    g2 = seguridad.regla("G2", MATRIZ)
    t.contiene("E-71 G2 sigue declarandolo como policy",
               "security-vulnerability-acceptance-threshold", repr(g2["policies"]))
    t.contiene("E-71 y como check", "security-vulnerability-acceptance-threshold",
               repr(g2["checks"]))
    veredicto, errores = seguridad.validar(MATRIZ)
    t.igual("E-71 y la matriz sigue valida", "NORMATIVE_MATRIX_VALID", veredicto)

    # Se ve en el reporte de huecos, con un tipo cada vez.
    faltan = seguridad.controles_no_instalados(seguridad.resolver(_todas_las_senales()))
    del_umbral = [f for f in faltan
                  if f["id"] == "security-vulnerability-acceptance-threshold"]
    t.igual("E-71 aparece dos veces en los huecos", 2, len(del_umbral))
    t.igual("E-71 una por tipo", ["DECLARED_CHECK_NOT_INSTALLED",
                                  "DECLARED_POLICY_NOT_INSTALLED"],
            sorted(f["state"] for f in del_umbral))
