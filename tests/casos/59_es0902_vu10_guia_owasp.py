# ES0902 §6 Vu10: la guia OWASP que aplica, revisada y con fuente vigente.
#
# Escenarios E-01 a E-62 de docs/cambios/es0902-vu10-guia-owasp/spec.md. Cada E-nn es el VU10-nn del
# paquete con el mismo numero.
#
# 🔴 CASO es un portal web. El inventario de activos dice que es el unico activo; su tipo WEB sale del
# inventario. La foto autoritativa de la guia web trae una edicion con tres puntos -W1, W2, W3, ids de
# fantasia a proposito: el modulo no puede conocerlos- y el registro de fuentes confiables dice que esa
# edicion esta vigente. La review los dispone a los tres con evidencia. Casi todo este archivo sale de
# romperlo. E-54 lo mira en PASS.
import ast
import copy
import json
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CONTROLES = RAIZ / "harnesses" / "desarrollo" / "controles"
REGLAS = RAIZ / "harnesses" / "desarrollo" / "reglas"
SKILLS = RAIZ / "harnesses" / "desarrollo" / "skills"
AGENTES = RAIZ / "harnesses" / "desarrollo" / "agents"
SCHEMAS = RAIZ / "comun" / "schemas"

sys.path.insert(0, str(BIN))
from orquestacion import seguridad                      # noqa: E402
from orquestacion import normativa                      # noqa: E402
from orquestacion import evaluacion                     # noqa: E402
from orquestacion import controles as c_controles       # noqa: E402
from orquestacion import registro_agentes as c_reg      # noqa: E402
from orquestacion import plan as orq_plan               # noqa: E402
from orquestacion import refutacion as R                # noqa: E402
from orquestacion import guia_owasp as G                # noqa: E402
from reporte_seguridad import libro                     # noqa: E402
from reporte_seguridad import productores as prod       # noqa: E402

RUTA = BIN / "orquestacion" / "guia_owasp.py"
MATRIZ = seguridad.cargar()
TRAZA = {"standard": "ES0902", "version": "6.2", "section": "6", "rule": "Vu10"}
LOS_10 = ("PASS", "FAIL", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED", "OWASP_ASSET_COVERAGE_UNRESOLVED",
          "OWASP_GUIDANCE_SOURCE_UNAVAILABLE", "OWASP_GUIDANCE_FRESHNESS_UNRESOLVED",
          "OWASP_GUIDANCE_COVERAGE_INCOMPLETE", "OWASP_GUIDANCE_ITEM_UNRESOLVED", "REVIEW_INCOMPLETE")
NA = "NOT_APPLICABLE"
SIN_APLIC = "APPLICABILITY_UNRESOLVED"
ACTIVOS = "OWASP_ASSET_COVERAGE_UNRESOLVED"
FUENTE = "OWASP_GUIDANCE_SOURCE_UNAVAILABLE"
FRESCURA = "OWASP_GUIDANCE_FRESHNESS_UNRESOLVED"
INCOMPLETA = "OWASP_GUIDANCE_COVERAGE_INCOMPLETE"
PUNTO = "OWASP_GUIDANCE_ITEM_UNRESOLVED"
REVISION = "REVIEW_INCOMPLETE"
TOKEN = "eyJhbGciOiJSUzI1NiJ9" + ".eyJyZWFsbV9hY2Nlc3MiOnt9fQ.firma"

ACT = "portal"
URL_WEB = "https://owasp.org/Top10/"
URL_API = "https://owasp.org/API-Security/"
URL_MOB = "https://owasp.org/www-project-mobile-top-10/"
PUNTOS = ("W1", "W2", "W3")


def _e(eid, fuente, establece, valor=None, **extra):
    base = {"evidenceId": eid, "sourceType": fuente, "reference": extra.pop("reference", "ref-%s" % eid),
            "establishes": [establece] if isinstance(establece, str) else list(establece)}
    if valor is not None:
        base["value"] = valor
    base.update(extra)
    return base


def _activo(valor="PRESENT", fuente="ARCHITECTURE_DOCUMENTATION", eid="activo", activos=(ACT,), **k):
    return _e(eid, fuente, "OWASP_APPLICABLE_ASSET", valor, assets=list(activos), **k)


def _tipo(valor="WEB", eid="tipo-web", activos=(ACT,), fuente="ASSET_INVENTORY", **k):
    return _e(eid, fuente, "ASSET_TYPE", valor, assets=list(activos), **k)


def _inventario(activos=(ACT,), valor="COMPLETE", eid="inventario", fuente="ASSET_INVENTORY", **k):
    return _e(eid, fuente, "ASSET_INVENTORY", valor, assets=list(activos), **k)


def _foto(familia="WEB", edicion="2025", puntos=PUNTOS, url=URL_WEB, eid="foto-web",
          fuente="AUTHORITATIVE_SOURCE_SNAPSHOT", **k):
    k.setdefault("sourceFingerprint", "sha256:aaa")
    k.setdefault("resolvedAt", "2026-09-26")
    return _e(eid, fuente, "OWASP_GUIDANCE_SOURCE", edicion, reference=url, families=[familia],
              items=list(puntos), **k)


def _fresca(valor="CURRENT", edicion="2025", url=URL_WEB, eid="frescura-web", **k):
    return _e(eid, "TRUSTED_KNOWLEDGE_REGISTRY", "SOURCE_FRESHNESS", valor, reference=url, version=edicion, **k)


def _prueba(eid, fuente="INTEGRATION_TEST", **k):
    return _e(eid, fuente, "GUIDANCE_ITEM_EVIDENCE", **k)


EVIDENCIA = [_activo(), _tipo(), _inventario(), _foto(), _fresca(),
             _prueba("cfg", "APPLICATION_CONFIGURATION"), _prueba("test-w2"),
             _prueba("arq", "ARCHITECTURE_DOCUMENTATION")]


def _punto(pid, disp="REVIEWED_NO_FINDING", evid=(), hallazgos=(), razon=None, titulo=None):
    return {"itemId": pid, "title": titulo or "punto %s" % pid, "disposition": disp, "rationale": razon,
            "evidenceRefs": list(evid), "findingIds": list(hallazgos)}


PUNTOS_BASE = [_punto("W1", evid=["cfg"]), _punto("W2", evid=["test-w2"]),
               _punto("W3", "NOT_APPLICABLE_WITH_RATIONALE", ["arq"],
                      razon="el portal no tiene carga de archivos: la arquitectura no expone ese flujo")]


def _fam(familia="WEB", edicion="2025", url=URL_WEB, frescura="CURRENT", puntos=None, huella="sha256:aaa"):
    return {"family": familia, "source": {"edition": edicion, "sourceRef": url, "resolvedAt": "2026-09-26",
                                          "sourceFingerprint": huella, "freshness": frescura},
            "items": copy.deepcopy(PUNTOS_BASE if puntos is None else puntos), "result": "REVIEW_COMPLETE"}


def _reg(familias=None, activos=None):
    return {"version": "1.0", "evaluatedAt": "2026-09-26T10:00:00",
            "assets": copy.deepcopy(activos if activos is not None else
                                    [{"assetId": ACT, "assetTypes": ["WEB"], "componentRef": "portal/",
                                      "environment": "QA", "revisionRef": "abc123",
                                      "evidence": ["tipo-web"]}]),
            "families": copy.deepcopy([_fam()] if familias is None else familias), "overall": "PASS"}


def _caso(registro=None, evidencia=None):
    return {"registry": _reg() if registro is None else copy.deepcopy(registro),
            "evidence": copy.deepcopy(EVIDENCIA if evidencia is None else evidencia)}


def _r(registro=None, evidencia=None, senal=None):
    return G.evaluar(_caso(registro, evidencia), senal)


def _estado(registro=None, evidencia=None):
    return _r(registro, evidencia)["state"]


def _f(r, familia="WEB"):
    return [f for f in r["families"] if f["family"] == familia][0]


def _p(r, pid, familia="WEB"):
    return [p for p in _f(r, familia)["items"] if p["itemId"] == pid][0]


def _sin(*ids_y_mas):
    ids = [x for x in ids_y_mas if isinstance(x, str)]
    mas = [x for x in ids_y_mas if isinstance(x, dict)]
    return [x for x in EVIDENCIA if x["evidenceId"] not in ids] + mas


def _con_puntos(*cambios, evidencia=None):
    """El caso con los puntos cambiados: cada cambio es un punto que reemplaza al de su id."""
    puntos = {p["itemId"]: p for p in copy.deepcopy(PUNTOS_BASE)}
    for c in cambios:
        puntos[c["itemId"]] = c
    return _r(_reg([_fam(puntos=[puntos[i] for i in sorted(puntos)])]), evidencia)


def _dos_familias(puntos_api=("P1", "P2")):
    activos = [{"assetId": ACT, "assetTypes": ["WEB", "API_OR_WEB_SERVICE"], "evidence": []}]
    evid = EVIDENCIA + [_tipo("API_OR_WEB_SERVICE", "tipo-api", fuente="API_SPECIFICATION"),
                        _foto("API_OR_WEB_SERVICE", "2023", puntos_api, URL_API, "foto-api"),
                        _fresca(edicion="2023", url=URL_API, eid="frescura-api")]
    api = _fam("API_OR_WEB_SERVICE", "2023", URL_API, puntos=[_punto(p, evid=["cfg"]) for p in puntos_api])
    return activos, evid, api


def _arbol():
    return ast.parse(RUTA.read_text(encoding="utf-8"))


def _literales():
    arbol = _arbol()
    docs = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.FunctionDef)):
            doc = ast.get_docstring(nodo, clean=False)
            if doc:
                docs.add(doc)
    return {n.value for n in ast.walk(arbol) if isinstance(n, ast.Constant) and isinstance(n.value, str)} - docs


def _json(r):
    return json.dumps(r, sort_keys=True, ensure_ascii=False)


def _todas():
    return {s: True for s in seguridad.senales_declaradas(MATRIZ)}


def _vu10_en_seguridad(r):
    ev, sen = G.para_seguridad(r)
    return seguridad.resultado("Vu10", ev, dict(_todas(), **sen), MATRIZ)


def _unidad(r, senal=True):
    senales = {"owaspApplicableAssetPresent": senal} if senal is not None else {}
    return normativa.resolucion(senales, evidencia={"ES0902.Vu10": r})["standards"]["ES0902"]["rules"]["Vu10"]


def _de_control_pasa(regla):
    fila = seguridad.regla(regla, MATRIZ)
    return {"controlResults": {c: {"result": "PASS", "evidence": ["ev-%s" % regla]}
                               for c in fila["policies"] + fila["checks"] + fila["reviews"]}}


def _dinamica(eid="dinamica", **cambios):
    datos = dict(environment="QA", authorized=True, bounded=True, syntheticData=True)
    datos.update(cambios)
    return _prueba(eid, "AUTHORIZED_DYNAMIC_TEST", **{k: v for k, v in datos.items() if v is not None})


# -- La fila --------------------------------------------------------------------

def test_e01_la_clave(t):
    """E-01."""
    t.igual("E-01 la fila", "ES0902.Vu10", seguridad.regla("Vu10", MATRIZ)["ruleKey"])
    t.igual("E-01 el modulo", "ES0902.Vu10", G.CLAVE)
    for nombre, r in (("pasa", _r()), ("vacio", G.evaluar({})),
                      ("falla", _r(_reg([_fam()], [{"assetId": ACT, "assetTypes": ["WEB", "MOBILE"],
                                                    "evidence": []}]), EVIDENCIA + [_tipo("MOBILE", "tipo-mob")])),
                      ("no aplica", G.evaluar({"registry": dict(_reg([], []), overall="NOT_APPLICABLE"),
                                               "evidence": [_activo("ABSENT", "SECURITY_DOCUMENTATION")]}))):
        t.igual("E-01 el resultado (%s)" % nombre, "ES0902.Vu10", r["ruleKey"])
        t.igual("E-01 y en seguridad (%s)" % nombre, "ES0902.Vu10", _vu10_en_seguridad(r)["ruleKey"])


def test_e02_los_ids(t):
    """E-02."""
    fila = seguridad.regla("Vu10", MATRIZ)
    t.igual("E-02 CONDITIONAL", "CONDITIONAL", fila["applicability"]["mode"])
    t.igual("E-02 la senal", ["owaspApplicableAssetPresent"], fila["applicability"]["signals"])
    t.igual("E-02 el agente", ["dev-security"], fila["primaryAgents"])
    t.igual("E-02 la policy", ["owasp-security-guidance-required"], fila["policies"])
    t.igual("E-02 la review", ["owasp-security-guidance-review"], fila["reviews"])
    t.igual("E-02 el modulo", ("owasp-security-guidance-review", "owasp-security-guidance-required",
                               "owaspApplicableAssetPresent"), (G.REVIEW, G.POLICY, G.SENAL))
    t.igual("E-02 la senal que produce es la de la matriz", "owaspApplicableAssetPresent",
            G.senal(_caso())["signalId"])
    registro = {c["id"]: c for c in c_controles.cargar()["controls"]}
    for cid, tipo, archivo in (("owasp-security-guidance-required", "POLICY",
                                "controles/policies/owasp-security-guidance-required.md"),
                               ("owasp-security-guidance-review", "REVIEW",
                                "controles/reviews/owasp-security-guidance-review.md")):
        t.igual("E-02 %s tipo" % cid, tipo, registro[cid]["type"])
        t.igual("E-02 %s archivo" % cid, archivo, registro[cid]["file"])
        t.igual("E-02 %s fuente" % cid, TRAZA, registro[cid]["source"])
        t.igual("E-02 %s instalado" % cid, "INSTALLED", registro[cid]["status"])
        t.verdadero("E-02 %s en disco" % cid, (RAIZ / "harnesses" / "desarrollo" / archivo).is_file())
    gobierno = (REGLAS / "es0902-vu10-governance.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    for trozo in ("ruleKey: ES0902.Vu10", "- owaspApplicableAssetPresent", "- owasp-security-guidance-required",
                  "checks: []", "- owasp-security-guidance-review", "primaryAgents:\n  - dev-security"):
        t.contiene("E-02 el gobierno declara `%s`" % trozo, trozo, gobierno)


def test_e03_sin_check(t):
    """E-03."""
    t.igual("E-03 la fila no tiene checks", [], seguridad.regla("Vu10", MATRIZ)["checks"])
    checks = [p.name for p in (CONTROLES / "checks").glob("*.py")]
    t.igual("E-03 ningun check nombra Vu10 ni OWASP", [],
            [n for n in checks if "owasp" in n.lower() or "vu10" in n.lower()])
    t.igual("E-03 ningun control de Vu10 es un CHECK", [],
            [c["id"] for c in c_controles.cargar()["controls"] if c.get("rule") == "Vu10" and c["type"] == "CHECK"])


def test_e04_nada_nuevo(t):
    """E-04."""
    t.igual("E-04 diez agentes", 11, len(c_reg.cargar()["agents"]))  # once desde la Wave 6: dev-iniciador-code se registro (integrity-cleanup, E-21)
    t.igual("E-04 once archivos de agentes", 11, len(list(AGENTES.glob("*.md"))))
    t.igual("E-04 veintisiete skills", 27, len([d for d in SKILLS.iterdir() if d.is_dir()]))
    t.igual("E-04 ALGORITMOS sigue en diez", 10, len(seguridad.ALGORITMOS))
    for nombre, r, esperado in (("PASS", _r(), "COMPLIANT"), ("sin resolver", _r(evidencia=_sin("frescura-web")),
                                                                "UNRESOLVED")):
        t.igual("E-04 con la review (%s), Vu10 da lo del generico" % nombre, esperado,
                _vu10_en_seguridad(r)["result"])
    ev, _ = G.para_seguridad(_r())
    t.verdadero("E-04 con la forma vieja, sin guia, sigue sin cumplir",
                seguridad.resultado("Vu10", dict(ev, assetTypes=["WEB_APPLICATION"]), _todas(),
                                    MATRIZ)["result"] != "COMPLIANT")


# -- La aplicabilidad ---------------------------------------------------------------------

def _senal(evidencia, activos=()):
    return G.derivar({"registry": _reg([], list(activos)), "evidence": evidencia})["value"]


def test_e05_un_activo_web(t):
    """E-05."""
    t.igual("E-05 enciende la senal", "TRUE", _senal([_activo()]))
    r = _r()
    t.igual("E-05 aporta la familia WEB", ["WEB"], r["applicableFamilies"])
    t.igual("E-05 y pasa", "PASS", r["state"])


def test_e06_un_activo_api(t):
    """E-06."""
    activos = [{"assetId": ACT, "assetTypes": ["API_OR_WEB_SERVICE"], "evidence": []}]
    evid = _sin("tipo-web", "foto-web", "frescura-web",
                _tipo("API_OR_WEB_SERVICE", "tipo-api", fuente="API_SPECIFICATION"),
                _foto("API_OR_WEB_SERVICE", "2023", PUNTOS, URL_API, "foto-api"),
                _fresca(edicion="2023", url=URL_API, eid="frescura-api"))
    r = _r(_reg([_fam("API_OR_WEB_SERVICE", "2023", URL_API)], activos), evid)
    t.igual("E-06 aporta la familia de API", ["API_OR_WEB_SERVICE"], r["applicableFamilies"])
    t.igual("E-06 y pasa", "PASS", r["state"])


def test_e07_un_activo_mobile(t):
    """E-07."""
    activos = [{"assetId": "app", "assetTypes": ["MOBILE"], "evidence": []}]
    evid = [_activo(activos=["app"]), _tipo("MOBILE", "tipo-mob", ["app"], "MOBILE_BUILD_CONFIGURATION"),
            _inventario(["app"]), _foto("MOBILE", "2024", PUNTOS, URL_MOB, "foto-mob"),
            _fresca(edicion="2024", url=URL_MOB, eid="frescura-mob"),
            _prueba("cfg", "APPLICATION_CONFIGURATION"), _prueba("test-w2"), _prueba("arq", "ARCHITECTURE_DOCUMENTATION")]
    r = _r(_reg([_fam("MOBILE", "2024", URL_MOB)], activos), evid)
    t.igual("E-07 aporta la familia MOBILE", ["MOBILE"], r["applicableFamilies"])
    t.igual("E-07 y pasa", "PASS", r["state"])


def test_e08_web_mas_api(t):
    """E-08."""
    activos, evid, api = _dos_familias()
    r = _r(_reg([_fam(), api], activos), evid)
    t.igual("E-08 un activo aporta las dos familias", ["API_OR_WEB_SERVICE", "WEB"], r["applicableFamilies"])
    t.igual("E-08 con las dos revisadas pasa", "PASS", r["state"])
    solo_web = _r(_reg([_fam()], activos), evid)
    t.igual("E-08 con una sola, falla: no se colapsan", "FAIL", solo_web["state"])


def test_e09_interno_y_autenticado(t):
    """E-09."""
    r = _r(evidencia=_sin("tipo-web", _tipo(internal=True, authenticated=True)))
    t.igual("E-09 un web interno y autenticado cuenta igual", "PASS", r["state"])
    t.igual("E-09 y aporta WEB", ["WEB"], r["applicableFamilies"])
    t.igual("E-09 el modulo no lee internal ni authenticated",
            [1, 1], [len([n for n in ast.walk(_arbol()) if isinstance(n, ast.Constant) and n.value == c])
                     for c in ("internal", "authenticated")])


def test_e10_lo_incompleto(t):
    """E-10."""
    t.igual("E-10 sin inventario", ACTIVOS, _estado(evidencia=_sin("inventario")))
    t.igual("E-10 con un inventario incompleto", ACTIVOS,
            _estado(evidencia=EVIDENCIA + [_inventario(valor="INCOMPLETE", eid="parcial")]))
    t.igual("E-10 con un activo que el inventario no nombra", ACTIVOS,
            _estado(evidencia=_sin("inventario", _inventario(["otro"]))))
    t.igual("E-10 un tipo sin sostener", ACTIVOS, _estado(evidencia=_sin("tipo-web")))
    # Refutador, pase 1: lo ilegible sobre el activo pesa en todas sus formas.
    for nombre, item in (("con outcome UNAVAILABLE", _tipo("MOBILE", "tipo-mob", outcome="UNAVAILABLE")),
                         ("mal formado", dict(_tipo("MOBILE", "tipo-mob"), extra="x"))):
        t.igual("E-10 un tipo %s sobre el activo" % nombre, ACTIVOS, _estado(evidencia=EVIDENCIA + [item]))
    # Refutador, pase 2: un tipo legible de una clase que no lo sostiene igual contradice lo declarado.
    t.igual("E-10 un tipo legible de otra clase que contradice", ACTIVOS,
            _estado(evidencia=EVIDENCIA + [_tipo("MOBILE", "tipo-mob", fuente="APPLICATION_CONFIGURATION")]))
    # Refutador, pase 3: la regla 2 tambien para el tipo y el inventario de activos.
    for nombre, item in (("UNKNOWN", _tipo("UNKNOWN", "tipo-raro")),
                         ("sin valor", {k: v for k, v in _tipo(eid="tipo-raro").items() if k != "value"}),
                         ("SERVER", _tipo("SERVER", "tipo-raro"))):
        t.igual("E-10 un tipo que no dice una familia (%s)" % nombre, ACTIVOS, _estado(evidencia=EVIDENCIA + [item]))
    for nombre, item in (("COMPLETE con otro activo", _inventario([ACT, "otro"], eid="inv-raro", outcome="INCONCLUSIVE")),
                         ("INCOMPLETE", _inventario(valor="INCOMPLETE", eid="inv-raro", outcome="UNAVAILABLE"))):
        t.igual("E-10 un inventario ilegible que nombra el activo (%s)" % nombre, ACTIVOS,
                _estado(evidencia=EVIDENCIA + [item]))
    t.igual("E-10 un tipo debil que no dice una familia no pesa", "PASS",
            _estado(evidencia=EVIDENCIA + [_tipo("UNKNOWN", "tipo-raro", fuente="README_STATEMENT")]))
    t.igual("E-10 uno debil no pesa", "PASS",
            _estado(evidencia=EVIDENCIA + [_tipo("MOBILE", "tipo-mob", fuente="README_STATEMENT")]))
    t.igual("E-10 un tipo que la evidencia dice y el registro no", ACTIVOS,
            _estado(evidencia=EVIDENCIA + [_tipo("MOBILE", "tipo-mob")]))
    t.igual("E-10 el vacio", SIN_APLIC, G.evaluar({"registry": _reg([], []), "evidence": []})["state"])
    t.igual("E-10 una evidencia debil", SIN_APLIC, _estado(_reg([], []), [_activo(fuente="MODEL_KNOWLEDGE")]))


def test_e11_ninguna_familia(t):
    """E-11."""
    ausente = _activo("ABSENT", "SECURITY_DOCUMENTATION")
    t.igual("E-11 una ausencia autoritativa sola no aplica", NA, _estado(_reg([], []), [ausente]))
    t.igual("E-11 con un activo registrado, no", SIN_APLIC, _estado(evidencia=[ausente]))
    # Refutador, pase 1: lo ilegible por `outcome` sobre la pregunta tambien impide apagarla.
    for outcome in ("INCONCLUSIVE", "UNAVAILABLE", "REFUTED"):
        for valor in (None, "ABSENT"):
            raro = _e("raro", "ARCHITECTURE_DOCUMENTATION", "OWASP_APPLICABLE_ASSET", valor, outcome=outcome)
            t.igual("E-11 con una %s ilegible (%s), no" % (valor or "sin valor", outcome), SIN_APLIC,
                    _estado(_reg([], []), [ausente, raro]))
    # Refutador, pase 2: y lo mal formado, lo repetido, lo sin id y lo que no dice ni si ni no.
    raro = _e("raro", "ARCHITECTURE_DOCUMENTATION", "OWASP_APPLICABLE_ASSET", "ABSENT")
    for nombre, items in (("mal formado", [dict(raro, extra="x")]),
                          ("repetido", [raro, dict(raro)]),
                          ("sin id", [dict(raro, evidenceId=None)]),
                          ("que no dice ni si ni no", [dict(raro, value="UNKNOWN")]),
                          ("sin valor", [{k: v for k, v in raro.items() if k != "value"}])):
        t.igual("E-11 con algo %s sobre la pregunta, no" % nombre, SIN_APLIC,
                _estado(_reg([], []), [ausente] + items))
    t.igual("E-11 con el registro invalido, no", SIN_APLIC,
            G.evaluar({"registry": {"version": "1.0"}, "evidence": [ausente]})["state"])
    t.igual("E-11 de una clase que no puede decirlo, no", SIN_APLIC,
            _estado(_reg([], []), [_activo("ABSENT", "APPLICATION_CODE")]))


# -- La fuente -------------------------------------------------------------------------

def test_e12_la_familia_se_ata_a_su_foto(t):
    """E-12."""
    r = _r()
    t.igual("E-12 la foto de la familia", ["foto-web"], _f(r)["source"]["snapshot"])
    t.igual("E-12 una foto de otra familia no la ata", FUENTE,
            _estado(evidencia=_sin("foto-web", _foto("MOBILE"))))
    t.igual("E-12 una foto con otra huella no la ata", FUENTE,
            _estado(evidencia=_sin("foto-web", _foto(sourceFingerprint="sha256:bbb"))))


def test_e13_la_memoria_no_es_fuente(t):
    """E-13."""
    for clase in ("MODEL_KNOWLEDGE", "AGENT_STATEMENT", "README_STATEMENT"):
        t.igual("E-13 una edicion de %s no resuelve la fuente" % clase, FUENTE,
                _estado(evidencia=_sin("foto-web", _foto(fuente=clase))))


def test_e14_sin_fuente(t):
    """E-14."""
    t.igual("E-14 sin foto", FUENTE, _estado(evidencia=_sin("foto-web")))
    r = _r(_reg([_fam(frescura="SOURCE_UNAVAILABLE")]))
    t.igual("E-14 declarada SOURCE_UNAVAILABLE", FUENTE, r["state"])
    t.igual("E-14 y en seguridad no cumple", "UNRESOLVED", _vu10_en_seguridad(r)["result"])


def test_e15_sin_frescura(t):
    """E-15."""
    t.igual("E-15 sin frescura del registro de fuentes", FRESCURA, _estado(evidencia=_sin("frescura-web")))
    for estado in ("FRESHNESS_UNVERIFIED", "ACKNOWLEDGED_PENDING", "SOURCE_MISSING"):
        t.igual("E-15 con %s" % estado, FRESCURA, _estado(evidencia=_sin("frescura-web", _fresca(estado))))
    t.igual("E-15 declarada FRESHNESS_UNVERIFIED", FRESCURA,
            _estado(_reg([_fam(frescura="FRESHNESS_UNVERIFIED")])))


def test_e16_la_edicion(t):
    """E-16."""
    t.igual("E-16 la edicion sale", "2025", _f(_r())["source"]["edition"])


def test_e17_fecha_referencia_y_huella(t):
    """E-17."""
    fuente = _f(_r())["source"]
    t.igual("E-17 salen", ("2026-09-26", URL_WEB, "sha256:aaa"),
            (fuente["resolvedAt"], fuente["sourceRef"], fuente["sourceFingerprint"]))
    sin_huella = _r(_reg([_fam(huella=None)]), _sin("foto-web", _foto(sourceFingerprint=None)))
    t.igual("E-17 sin huella se llega igual", "PASS", sin_huella["state"])


def test_e18_una_edicion_nueva(t):
    """E-18."""
    nueva = _fresca("UPDATE_AVAILABLE", eid="frescura-nueva")
    r = _r(evidencia=EVIDENCIA + [nueva])
    t.igual("E-18 UPDATE_AVAILABLE le quita el CURRENT a la foto vieja", FRESCURA, r["state"])
    t.igual("E-18 y queda a la vista", ["frescura-nueva"], _f(r)["freshness"]["contradictedBy"])
    entrada = {"state": "UPDATE_AVAILABLE", "registry_version": "2025", "observed_version": "2029"}
    item = G.evidencia_de_frescura("OWASP-TOP10", entrada, URL_WEB, "2025")
    t.igual("E-18 la traduccion lleva el estado del mecanismo tal cual", "UPDATE_AVAILABLE", item["value"])
    t.igual("E-18 y con ella tampoco pasa", FRESCURA, _estado(evidencia=_sin("frescura-web", item)))
    t.igual("E-18 una entrada CURRENT si", "PASS",
            _estado(evidencia=_sin("frescura-web", G.evidencia_de_frescura("OWASP-TOP10", {"state": "CURRENT"},
                                                                            URL_WEB, "2025"))))
    # Refutador, pase 1: el "no" pasa por la misma compuerta que el "si": de cualquier clase, y lo ilegible.
    for clase in ("AUTHORITATIVE_SOURCE_SNAPSHOT", "SECURITY_DOCUMENTATION", "OTHER_AUTHORITATIVE_EVIDENCE"):
        otra = dict(_fresca("UPDATE_AVAILABLE", eid="nueva"), sourceType=clase)
        t.igual("E-18 un UPDATE_AVAILABLE de %s tambien le quita el CURRENT" % clase, FRESCURA,
                _estado(evidencia=EVIDENCIA + [otra]))
    t.igual("E-18 una frescura ilegible sobre la fuente tambien", FRESCURA,
            _estado(evidencia=EVIDENCIA + [_fresca("CURRENT", eid="rara", outcome="INCONCLUSIVE")]))
    t.igual("E-18 una mal formada que nombra la fuente tambien", FRESCURA,
            _estado(evidencia=EVIDENCIA + [dict(_fresca("CURRENT", eid="torcida"), extra="x")]))
    # Refutador, pase 2: quita el CURRENT lo que dice otro estado u otra edicion; un CURRENT redundante no.
    t.igual("E-18 un CURRENT redundante de otra clase, de la misma edicion, no la quita", "PASS",
            _estado(evidencia=EVIDENCIA + [dict(_fresca(eid="otra"), sourceType="SECURITY_DOCUMENTATION")]))
    t.igual("E-18 un CURRENT de otra edicion si", FRESCURA,
            _estado(evidencia=EVIDENCIA + [_fresca(edicion="2029", eid="otra")]))
    t.igual("E-18 una foto ilegible de la misma fuente tambien", FRESCURA,
            _estado(evidencia=EVIDENCIA + [_foto(eid="foto-rara", outcome="INCONCLUSIVE")]))
    t.igual("E-18 un CURRENT de otra clase no la sostiene", FRESCURA,
            _estado(evidencia=_sin("frescura-web", dict(_fresca(), sourceType="SECURITY_DOCUMENTATION"))))
    t.igual("E-18 una entrada sin estado es FRESHNESS_UNVERIFIED", "FRESHNESS_UNVERIFIED",
            G.evidencia_de_frescura("X", {}, URL_WEB, "2025")["value"])


# -- Los puntos ------------------------------------------------------------------------

def test_e19_los_puntos_de_la_foto(t):
    """E-19."""
    t.igual("E-19 los esperados son los de la foto", list(PUNTOS), _f(_r())["expectedItems"])


def test_e20_ninguna_lista_eterna(t):
    """E-20."""
    ids = re.compile(r"^(A|API|M)\d{1,2}(:|$)|injection|broken|misconfiguration|ssrf|cryptographic", re.I)
    t.igual("E-20 el modulo no tiene puntos de OWASP", [], sorted(x for x in _literales() if ids.search(x)))
    otra = _r(_reg([_fam(edicion="2031", puntos=[_punto("Z9", evid=["cfg"])])]),
              _sin("foto-web", "frescura-web", _foto(edicion="2031", puntos=["Z9"]), _fresca(edicion="2031")))
    t.igual("E-20 otra edicion con otros puntos pasa sin tocar nada", "PASS", otra["state"])


def test_e21_repetido_o_ajeno(t):
    """E-21."""
    t.igual("E-21 un punto repetido", INCOMPLETA,
            _estado(_reg([_fam(puntos=PUNTOS_BASE + [_punto("W1", evid=["cfg"])])])))
    sin_disposicion = copy.deepcopy(PUNTOS_BASE)
    del sin_disposicion[0]["disposition"]
    t.igual("E-21 un punto sin disposicion deja la review incompleta", REVISION,
            _estado(_reg([_fam(puntos=sin_disposicion)])))
    t.igual("E-21 un punto con disposicion nula tambien", REVISION,
            _estado(_reg([_fam(puntos=[dict(PUNTOS_BASE[0], disposition=None)] + PUNTOS_BASE[1:])])))
    t.igual("E-21 un punto que la edicion no tiene", INCOMPLETA,
            _estado(_reg([_fam(puntos=PUNTOS_BASE + [_punto("X1", evid=["cfg"])])])))


def test_e22_un_punto_que_falta(t):
    """E-22."""
    r = _r(_reg([_fam(puntos=PUNTOS_BASE[:2])]))
    t.igual("E-22 falta un punto", INCOMPLETA, r["state"])
    t.igual("E-22 y se dice cual", ["W3"], _f(r)["missingItems"])


def test_e23_revisado_sin_hallazgo(t):
    """E-23."""
    t.igual("E-23 con evidencia vale", "PASS", _p(_r(), "W1")["state"])
    r = _con_puntos(_punto("W1"))
    t.igual("E-23 sin evidencia no", PUNTO, _p(r, "W1")["state"])
    # Refutador, pase 1: la foto, la frescura o el inventario no son evidencia de haber revisado el punto.
    t.igual("E-23 citar la foto de OWASP no revisa nada", PUNTO,
            _p(_con_puntos(_punto("W1", evid=["foto-web", "frescura-web", "inventario"])), "W1")["state"])
    # Refutador, pase 2: lo decide la clase, no lo que el item dice de si mismo.
    foto_que_dice = dict(_foto(), establishes=["OWASP_GUIDANCE_SOURCE", "GUIDANCE_ITEM_EVIDENCE"])
    t.igual("E-23 la foto que dice ser evidencia de punto tampoco revisa nada", PUNTO,
            _p(_con_puntos(_punto("W1", evid=["foto-web"]), evidencia=_sin("foto-web", foto_que_dice)), "W1")["state"])
    fresca_que_dice = dict(_fresca(), establishes=["SOURCE_FRESHNESS", "GUIDANCE_ITEM_EVIDENCE"])
    t.igual("E-23 ni la frescura que dice serlo", PUNTO,
            _p(_con_puntos(_punto("W1", evid=["frescura-web"]), evidencia=_sin("frescura-web", fresca_que_dice)),
               "W1")["state"])
    registro = _prueba("reg", "TRUSTED_KNOWLEDGE_REGISTRY")
    t.igual("E-23 ni un item del registro de fuentes", PUNTO,
            _p(_con_puntos(_punto("W1", evid=["reg"]), evidencia=EVIDENCIA + [registro]), "W1")["state"])
    t.igual("E-23 y la review no pasa", REVISION, r["state"])


def test_e24_con_hallazgo(t):
    """E-24."""
    r = _con_puntos(_punto("W2", "FINDING_PRESENT", hallazgos=["F-1"]), evidencia=_sin(HALLAZGO))
    t.igual("E-24 un hallazgo es una disposicion valida", "PASS", _p(r, "W2")["state"])
    # Refutador, pase 1: el hallazgo tiene que existir; un nombre no es un hallazgo.
    t.igual("E-24 un hallazgo que el catalogo no tiene no vale", PUNTO,
            _p(_con_puntos(_punto("W2", "FINDING_PRESENT", hallazgos=["F-inventado"])), "W2")["state"])
    t.igual("E-24 ni uno real junto a uno inventado", PUNTO,
            _p(_con_puntos(_punto("W2", "FINDING_PRESENT", hallazgos=["F-1", "F-9"]), evidencia=_sin(HALLAZGO)),
               "W2")["state"])
    for clase in ("MODEL_KNOWLEDGE", "AGENT_STATEMENT", "RULE_RESULT", "AUTHORITATIVE_SOURCE_SNAPSHOT"):
        t.igual("E-24 ni un hallazgo de %s" % clase, PUNTO,
                _p(_con_puntos(_punto("W2", "FINDING_PRESENT", hallazgos=["F-1"]),
                               evidencia=_sin(dict(HALLAZGO, sourceType=clase))), "W2")["state"])
    t.igual("E-24 ni uno ilegible", PUNTO,
            _p(_con_puntos(_punto("W2", "FINDING_PRESENT", hallazgos=["F-1"]),
                           evidencia=_sin(dict(HALLAZGO, outcome="INCONCLUSIVE"))), "W2")["state"])
    t.igual("E-24 sin el id del hallazgo no", PUNTO, _p(_con_puntos(_punto("W2", "FINDING_PRESENT")), "W2")["state"])


def test_e25_no_aplica_con_razon(t):
    """E-25."""
    for razon in (None, "", "   "):
        r = _con_puntos(_punto("W3", "NOT_APPLICABLE_WITH_RATIONALE", ["arq"], razon=razon))
        t.igual("E-25 sin razon (%r) no vale" % razon, PUNTO, _p(r, "W3")["state"])


def test_e26_ningun_no_aplica_por_defecto(t):
    """E-26."""
    r = _con_puntos(_punto("W3", "NOT_APPLICABLE_WITH_RATIONALE", razon="no aplica"))
    t.igual("E-26 sin evidencia no vale", PUNTO, _p(r, "W3")["state"])
    instalado = json.loads((REGLAS / "owasp-security-guidance-review.json").read_text(encoding="utf-8"))
    t.igual("E-26 la review instalada no trae ninguna familia ni punto", ([], []),
            (instalado["families"], instalado["assets"]))
    t.igual("E-26 y su estado es REVIEW_INCOMPLETE", "REVIEW_INCOMPLETE", instalado["overall"])


def test_e27_un_punto_sin_resolver(t):
    """E-27."""
    r = _con_puntos(_punto("W1", "UNRESOLVED", ["cfg"]))
    t.verdadero("E-27 no pasa", r["state"] != "PASS")
    t.verdadero("E-27 y dice que el punto esta abierto", PUNTO in r["states"])


# -- Los hallazgos ------------------------------------------------------------------------

HALLAZGO = _e("F-1", "SECURITY_FINDING", "SECURITY_FINDING", title="validacion en el cliente solamente",
              severity="HIGH", confidence="medium")


def _con_hallazgo(**k):
    ev = _sin(dict(HALLAZGO, **k))
    return _con_puntos(_punto("W2", "FINDING_PRESENT", ["test-w2"], ["F-1"]), evidencia=ev), ev


def test_e28_un_hallazgo_no_es_falla(t):
    """E-28."""
    r, _ = _con_hallazgo()
    t.igual("E-28 una review completa con un hallazgo no es FAIL", "PASS", r["state"])


def test_e29_el_hallazgo_va_al_reporte(t):
    """E-29."""
    r, ev = _con_hallazgo()
    caso = _caso(evidencia=ev)
    eventos = G.hallazgos_para_reporte(r, caso, [], "GCBA-1029", {"project": "P"}, "2026-09-26T10:00:00")
    t.igual("E-29 sale un FINDING_CREATED", ["FINDING_CREATED"], [e["eventType"] for e in eventos])
    t.igual("E-29 de Vu10, con su id", ("Vu10", ["F-1"]), (eventos[0]["normative"]["rule"], eventos[0]["findingIds"]))
    t.igual("E-29 por desde_hallazgo", "desde_hallazgo", eventos[0]["details"]["producer"])
    # Refutador, pase 3: un nombre en findingIds de otra disposicion, o que el catalogo no tiene, no llega.
    otro = _con_puntos(_punto("W1", evid=["cfg"], hallazgos=["inventado"]))
    t.igual("E-29 un nombre en un REVIEWED_NO_FINDING no es un hallazgo", [], otro["findings"])
    t.igual("E-29 y no sale al reporte", [], G.hallazgos_para_reporte(otro, _caso(), [], "T", {"project": "P"}))
    mezcla = _con_puntos(_punto("W2", "FINDING_PRESENT", hallazgos=["F-1", "F-9"]), evidencia=_sin(HALLAZGO))
    t.igual("E-29 de un FINDING_PRESENT sale el real y no el inventado", (["F-1"], ["F-9"]),
            (mezcla["findings"], _p(mezcla, "W2")["unknownFindingIds"]))
    real_ajeno = _con_puntos(_punto("W1", evid=["cfg"], hallazgos=["F-1"]), evidencia=_sin(HALLAZGO))
    t.igual("E-29 un hallazgo real citado desde un REVIEWED_NO_FINDING no se reporta", [], real_ajeno["findings"])
    t.igual("E-29 uno que ya esta en el libro no se vuelve a crear", [],
            G.hallazgos_para_reporte(r, caso, ["F-1"], "GCBA-1029", {"project": "P"}))


def test_e30_la_severidad_no_es_cobertura(t):
    """E-30."""
    estados = {s: _con_hallazgo(severity=s)[0]["state"] for s in ("CRITICAL", "HIGH", "LOW", "INFORMATIONAL")}
    t.igual("E-30 la severidad no cambia el estado", {s: "PASS" for s in estados}, estados)
    r, ev = _con_hallazgo(severity="CRITICAL")
    t.igual("E-30 y viaja en el hallazgo", "CRITICAL",
            G.hallazgos_para_reporte(r, _caso(evidencia=ev), [], "T", {"project": "P"})[0]["severity"])


def test_e31_la_confianza_aparte(t):
    """E-31."""
    t.igual("E-31 la confianza no cambia el estado", ["PASS", "PASS"],
            [_con_hallazgo(confidence=c)[0]["state"] for c in ("low", "high")])
    r, ev = _con_hallazgo(confidence="low")
    evento = G.hallazgos_para_reporte(r, _caso(evidencia=ev), [], "T", {"project": "P"})[0]
    t.igual("E-31 viaja en su campo, separada de la severidad", ("LOW", "HIGH"), (evento["confidence"], evento["severity"]))


def test_e32_una_politica_mas_estricta(t):
    """E-32."""
    r, ev = _con_hallazgo(blocking=True, severity="CRITICAL")
    evento = G.hallazgos_para_reporte(r, _caso(evidencia=ev), [], "T", {"project": "P"})[0]
    t.verdadero("E-32 el hallazgo que bloquea sale con blocking", evento["blocking"] is True)
    t.igual("E-32 y la review sigue en PASS", "PASS", r["state"])
    t.igual("E-32 y Vu10 cumple por su lado", "COMPLIANT", _vu10_en_seguridad(r)["result"])


# -- Los marcos que Vu10 no pide ----------------------------------------------------------

def _no_nombra(t, eid, patron):
    t.igual("%s el modulo no lo nombra" % eid, [], sorted(x for x in _literales() if re.search(patron, x, re.I)))
    t.no_contiene("%s y el caso que pasa tampoco" % eid, patron.split("|")[0].lower(), _json(_caso()).lower())
    t.igual("%s se pasa sin el" % eid, "PASS", _estado())


def test_e33_asvs(t):
    """E-33."""
    _no_nombra(t, "E-33", "asvs")


def test_e34_masvs(t):
    """E-34."""
    _no_nombra(t, "E-34", "masvs")


def test_e35_samm(t):
    """E-35."""
    _no_nombra(t, "E-35", "samm")


def test_e36_ningun_scanner(t):
    """E-36."""
    _no_nombra(t, "E-36", "scanner|zap|burp|sonar|snyk|nessus|dast|sast")
    clases = {x["sourceType"] for x in EVIDENCIA}
    t.igual("E-36 un punto se sostiene con cualquier clase del proyecto", "PASS",
            _estado(evidencia=_sin("cfg", _prueba("cfg", "SECURITY_DOCUMENTATION"))))
    t.verdadero("E-36 ninguna clase de scanner en el caso base", not any("SCAN" in c for c in clases))


def test_e37_ningun_umbral(t):
    """E-37."""
    numeros = sorted({n.value for n in ast.walk(_arbol()) if isinstance(n, ast.Constant)
                      and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)})
    t.igual("E-37 el modulo no tiene numeros mas alla de 0, 1 y 2", [], [x for x in numeros if x not in (0, 1, 2)])
    ids = ["F-%d" % i for i in range(10)]
    ev = EVIDENCIA + [dict(HALLAZGO, evidenceId=i) for i in ids]
    r = _con_puntos(_punto("W2", "FINDING_PRESENT", hallazgos=ids), evidencia=ev)
    t.igual("E-37 diez hallazgos siguen en PASS", "PASS", r["state"])


# -- La evidencia de otras reglas -----------------------------------------------------------

def _prestada(regla):
    item = _prueba("de-%s" % regla, "APPLICATION_CODE", reusedFrom="ES0902.%s" % regla)
    return _con_puntos(_punto("W1", evid=[item["evidenceId"]]), evidencia=EVIDENCIA + [item])


def _no_mueve(t, eid, regla):
    todas = _todas()
    t.verdadero("%s el PASS de %s no pone en PASS a Vu10" % (eid, regla),
                seguridad.resultado("Vu10", _de_control_pasa(regla), todas, MATRIZ)["result"] != "COMPLIANT")
    # Refutador, pase 1: el caso fuerte, con la review de Vu10 incompleta al lado.
    ev, sen = G.para_seguridad(_r(_reg([_fam(puntos=PUNTOS_BASE[:2])])))
    junto = {"controlResults": dict(_de_control_pasa(regla)["controlResults"], **ev["controlResults"])}
    t.igual("%s con la review de Vu10 incompleta, el PASS de %s no la cierra" % (eid, regla), "UNRESOLVED",
            seguridad.resultado("Vu10", junto, dict(todas, **sen), MATRIZ)["result"])


def test_e38_evidencia_de_vu5(t):
    """E-38."""
    t.igual("E-38 evidencia de Vu5 sostiene un punto", "PASS", _p(_prestada("Vu5"), "W1")["state"])


def test_e39_vu5_no_es_vu10(t):
    """E-39."""
    _no_mueve(t, "E-39", "Vu5")
    resultado = _prueba("vu5-pass", "RULE_RESULT", value="PASS", reusedFrom="ES0902.Vu5")
    r = _con_puntos(_punto("W1", evid=["vu5-pass"]), evidencia=EVIDENCIA + [resultado])
    t.igual("E-39 el resultado final de Vu5 no sostiene un punto", PUNTO, _p(r, "W1")["state"])


def test_e40_evidencia_de_vu8(t):
    """E-40."""
    t.igual("E-40 evidencia de Vu8 sostiene un punto", "PASS", _p(_prestada("Vu8"), "W1")["state"])


def test_e41_vu8_no_es_vu10(t):
    """E-41."""
    _no_mueve(t, "E-41", "Vu8")


def test_e42_evidencia_de_vu9(t):
    """E-42."""
    t.igual("E-42 evidencia de Vu9 sostiene un punto", "PASS", _p(_prestada("Vu9"), "W1")["state"])


def test_e43_vu9_no_es_vu10(t):
    """E-43."""
    _no_mueve(t, "E-43", "Vu9")


def test_e44_un_hallazgo_una_vez(t):
    """E-44."""
    ev = _sin(HALLAZGO)
    r = _con_puntos(_punto("W1", "FINDING_PRESENT", hallazgos=["F-1"]),
                    _punto("W2", "FINDING_PRESENT", hallazgos=["F-1"]), evidencia=ev)
    t.igual("E-44 el hallazgo sale una vez", ["F-1"], r["findings"])
    t.igual("E-44 y un solo evento", 1,
            len(G.hallazgos_para_reporte(r, _caso(evidencia=ev), [], "T", {"project": "P"})))


# -- La review y la refutacion atomica ----------------------------------------------------

CLAVE_REF = "GCBA-1045"
_PLANTILLA = {}


def _escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8", newline="\n")


def _plan(clave):
    if clave not in _PLANTILLA:
        tc = {"meta": {"task_key": clave, "context_hash": "h"}, "task": {"title": "t"}}
        prop = {"objective": "o", "domains": ["backend"],
                "workUnits": [{"id": "WU-1", "objective": "x", "domain": "backend"}]}
        _PLANTILLA[clave] = json.dumps(orq_plan.armar(prop, tc, {}, {}))
    return json.loads(_PLANTILLA[clave])


def _plantilla():
    if "base" not in _PLANTILLA:
        base = Path(tempfile.gettempdir()) / ("harness-vu10-base-" + uuid.uuid4().hex[:8])
        _escribir(base / "src" / "subida.py", "def subir(f): validar(f)\n")
        _escribir(base / "otro" / "nada.py", "x = 1\n")
        for args in (("init", "-q"), ("add", "-A"), ("commit", "-q", "-m", "i")):
            subprocess.run(["git", "-C", str(base), "-c", "user.email=t@t", "-c", "user.name=t"] + list(args),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        _PLANTILLA["base"] = base
    return _PLANTILLA["base"]


def _bloque():
    return {"standard": {"id": "ES0902", "version": "6.2"}, "applicableRules": ["Vu10"],
            "notApplicableRules": [], "unresolvedRules": [], "declaredPolicies": [],
            "declaredChecks": [], "declaredReviews": ["owasp-security-guidance-review"]}


def _tarea(proy, clave, scope):
    doc = _plan(clave)
    for u in doc["workUnits"]:
        u["normative"] = dict(u["normative"], standards={"ES0902": _bloque()})
    _escribir(proy / ".claude" / "planes" / (clave + ".json"), json.dumps(doc, ensure_ascii=False))
    _escribir(proy / ".claude" / "refutaciones" / clave / "scope.json",
              json.dumps({"schema_version": R.VERSION_ALCANCE, "workUnits": scope}))


def _proyecto(scope):
    proy = Path(tempfile.gettempdir()) / ("harness-vu10-" + uuid.uuid4().hex[:8])
    shutil.copytree(str(_plantilla()), str(proy))
    _tarea(proy, CLAVE_REF, scope)
    _caso_55()._listo_para_la_compuerta(proy, CLAVE_REF)
    return proy


def _caso_55():
    """La refutacion atomica, por su `_listo_para_la_compuerta` (Wave 6: `compilar` evalua la
    compuerta tambien como biblioteca)."""
    if "55" not in _CASOS:
        import importlib.util as _iu
        spec = _iu.spec_from_file_location("caso_55_compuerta", str(
            Path(__file__).resolve().parent / "55_refutacion_atomica.py"))
        modulo = _iu.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        _CASOS["55"] = modulo
    return _CASOS["55"]


_CASOS = {}


def _unidades(proy, clave=CLAVE_REF):
    return R.leer(str(proy), clave)[1]


def _veredicto(u, **cambios):
    v = {"schema_version": R.VERSION_VEREDICTO, "refutationUnitId": u["refutationUnitId"],
         "workUnitId": u["workUnitId"], "ruleKey": "ES0902.Vu10", "verdict": "cumple", "reason": None,
         "citation": {"skillId": u["skillId"], "locator": "ES0902 §6"},
         "evidence": [{"path": "src/subida.py", "line": 1, "observed": "def subir(f): validar(f)"}],
         "needed": None, "cacheKey": u["cacheKey"], "evidenceFingerprint": u["evidenceFingerprint"],
         "repoRevision": u["repoRevision"]}
    v.update(cambios)
    return v


def _levanta(funcion, codigo=None):
    try:
        funcion()
    except R.RefutacionInvalida as e:
        return codigo is None or e.codigo == codigo
    return False


def _alcance():
    return G.alcance_de_punto("WEB", "W3", ACT, ["src/subida.py"])


def test_e45_es_una_review(t):
    """E-45."""
    registro = {c["id"]: c for c in c_controles.cargar()["controls"]}
    t.igual("E-45 registrada como REVIEW", "REVIEW", registro["owasp-security-guidance-review"]["type"])
    doc = (CONTROLES / "reviews" / "owasp-security-guidance-review.md").read_text(encoding="utf-8")
    t.contiene("E-45 con su documento", "type: REVIEW", doc)
    t.igual("E-45 la fila no tiene checks", [], seguridad.regla("Vu10", MATRIZ)["checks"])
    t.igual("E-45 el modulo se declara review", "REVIEW", G.TIPO)


def test_e46_la_refutacion_no_reemplaza_la_review(t):
    """E-46."""
    proy = _proyecto({"WU-1": _alcance()})
    try:
        R.compilar(str(proy), CLAVE_REF)
        u = _unidades(proy)[0]
        t.igual("E-46 la unidad queda pendiente: no hay check que la cierre", "PENDING_SEMANTIC", u["status"])
        R.registrar(str(proy), CLAVE_REF, json.dumps(_veredicto(u)))
        R.compilar(str(proy), CLAVE_REF)
        t.igual("E-46 el veredicto resuelve la unidad", "RESOLVED", _unidades(proy)[0]["status"])
        incompleta = _r(_reg([_fam(puntos=PUNTOS_BASE[:2])]))
        t.igual("E-46 y la review sigue incompleta", INCOMPLETA, incompleta["state"])
        importados = {a.name for n in ast.walk(_arbol()) if isinstance(n, ast.ImportFrom) for a in n.names}
        t.verdadero("E-46 el modulo no lee veredictos: no importa la refutacion", "refutacion" not in importados)
    finally:
        shutil.rmtree(str(proy), ignore_errors=True)


def test_e47_un_punto_una_unidad(t):
    """E-47."""
    alcance = _alcance()
    t.igual("E-47 el alcance nombra un punto y un activo", "owasp.WEB.W3.portal", alcance[0]["scopeId"])
    raro = G.alcance_de_punto("API_OR_WEB_SERVICE", "X:2031", "app movil", ["src/subida.py"])
    t.igual("E-47 un id con dos puntos o espacios cumple el patron del alcance", [],
            R.validar({"schema_version": R.VERSION_ALCANCE, "workUnits": {"WU-1": raro}}, R.SCHEMA_UNIDAD,
                      "scopeInput"))
    proy = _proyecto({"WU-1": alcance})
    try:
        R.compilar(str(proy), CLAVE_REF)
        de_vu10 = [u for u in _unidades(proy) if u["standard"]["ruleKey"] == "ES0902.Vu10"]
        t.igual("E-47 una sola unidad de Vu10", 1, len(de_vu10))
        t.igual("E-47 con las rutas del punto", ["src/subida.py"], de_vu10[0]["evidenceScope"]["paths"])
        t.verdadero("E-47 la skill es de dev-security",
                    de_vu10[0]["skillId"] in {s["id"] for a in c_reg.cargar()["agents"]
                                              if a["id"] == "dev-security" for s in a["skills"]})
    finally:
        shutil.rmtree(str(proy), ignore_errors=True)


def test_e48_nunca_el_repo_entero(t):
    """E-48."""
    for nombre, paths in (("vacio", []), ("el punto", ["."]), ("todo", ["**"]), ("la raiz", ["/"])):
        t.igual("E-48 un alcance %s se rechaza" % nombre, None, G.alcance_de_punto("WEB", "W3", ACT, paths))
    t.igual("E-48 sin punto tambien", None, G.alcance_de_punto("WEB", "", ACT, ["src/subida.py"]))
    t.igual("E-48 con una familia que no existe tambien", None, G.alcance_de_punto("SERVER", "W3", ACT, ["a.py"]))
    proy = _proyecto({"WU-1": _alcance()})
    try:
        R.compilar(str(proy), CLAVE_REF)
        u = _unidades(proy)[0]
        t.verdadero("E-48 un veredicto con evidencia fuera del alcance se rechaza",
                    _levanta(lambda: R.registrar(str(proy), CLAVE_REF, json.dumps(_veredicto(
                        u, evidence=[{"path": "otro/nada.py", "line": 1, "observed": "x = 1"}]))),
                             "REFUTATION_OUTPUT_INVALID"))
    finally:
        shutil.rmtree(str(proy), ignore_errors=True)


def test_e49_la_huella_invalida_la_cache(t):
    """E-49."""
    proy = _proyecto({"WU-1": _alcance()})
    try:
        R.compilar(str(proy), CLAVE_REF)
        u = _unidades(proy)[0]
        R.registrar(str(proy), CLAVE_REF, json.dumps(_veredicto(u)))
        _tarea(proy, "GCBA-1049", {"WU-1": _alcance()})
        _caso_55()._listo_para_la_compuerta(proy, "GCBA-1049")
        R.compilar(str(proy), "GCBA-1049")
        t.igual("E-49 con la misma evidencia se reusa", "CACHE", _unidades(proy, "GCBA-1049")[0]["resolutionPath"])
        _escribir(proy / "src" / "subida.py", "def subir(f): pass\n")
        _tarea(proy, "GCBA-1050", {"WU-1": _alcance()})
        _caso_55()._listo_para_la_compuerta(proy, "GCBA-1050")
        R.compilar(str(proy), "GCBA-1050")
        otra = _unidades(proy, "GCBA-1050")[0]
        t.verdadero("E-49 otra huella, otra clave", otra["cacheKey"] != u["cacheKey"])
        t.igual("E-49 el veredicto guardado no se reusa", "PENDING_SEMANTIC", otra["status"])
    finally:
        shutil.rmtree(str(proy), ignore_errors=True)


# -- La prueba dinamica -----------------------------------------------------------------------

def test_e50_nada_se_ejecuta(t):
    """E-50."""
    raices = ({a.name.split(".")[0] for n in ast.walk(_arbol()) if isinstance(n, ast.Import) for a in n.names}
              | {(n.module or "").split(".")[0] for n in ast.walk(_arbol()) if isinstance(n, ast.ImportFrom)})
    t.igual("E-50 no importa nada que abra una conexion o un proceso", set(),
            {"subprocess", "socket", "urllib", "requests", "http", "asyncio", "threading", "ssl"} & raices)
    escrituras = [n for n in ast.walk(_arbol()) if isinstance(n, ast.Call)
                  and getattr(n.func, "attr", getattr(n.func, "id", "")) == "open"
                  and any(isinstance(a, ast.Constant) and "w" in str(a.value) for a in n.args[1:])]
    t.igual("E-50 y no abre nada para escribir", [], escrituras)


def _con_dinamica(**cambios):
    return _con_puntos(_punto("W1", evid=["dinamica"]), evidencia=EVIDENCIA + [_dinamica(**cambios)])


def test_e51_prd_o_destructiva(t):
    """E-51."""
    t.igual("E-51 una prueba segura sostiene", "PASS", _p(_con_dinamica(), "W1")["state"])
    for nombre, cambio in (("en PRD", {"environment": "PRD"}), ("destructiva", {"destructive": True}),
                           ("no acotada", {"bounded": None}), ("con datos reales", {"syntheticData": False})):
        t.igual("E-51 una prueba %s no sostiene" % nombre, PUNTO, _p(_con_dinamica(**cambio), "W1")["state"])
        t.verdadero("E-51 (%s) y no es FAIL" % nombre, _con_dinamica(**cambio)["state"] != "FAIL")
    t.igual("E-51 los motivos", ["DESTRUCTIVE", "PRODUCTION"],
            G.prueba_segura(_dinamica(environment="PRD", destructive=True)))


def test_e52_sin_objetivo(t):
    """E-52."""
    for nombre, cambio in (("sin objetivo", {"outcome": "UNAVAILABLE"}), ("no autorizada", {"authorized": None})):
        r = _con_dinamica(**cambio)
        t.igual("E-52 una prueba %s deja el punto sin resolver" % nombre, PUNTO, _p(r, "W1")["state"])
        t.igual("E-52 (%s) y la review incompleta" % nombre, REVISION, r["state"])


def test_e53_ninguna_credencial(t):
    """E-53."""
    contrasena = "postgres://portal:" + "S3cr3t0!@db.qa.local/app"
    r = _con_puntos(_punto("W3", "NOT_APPLICABLE_WITH_RATIONALE", ["arq"], razon="token=" + TOKEN + " " + contrasena))
    salidas = (("la salida", _json(r)), ("la unidad", _json(_unidad(r))),
               ("el libro", _json(prod.desde_regla(_vu10_en_seguridad(r), "T", {"project": "P"},
                                                   "2026-09-26T10:00:00"))))
    for nombre, texto in salidas:
        t.no_contiene("E-53 %s no lleva el token" % nombre, TOKEN, texto)
        t.no_contiene("E-53 %s no lleva la contrasena" % nombre, "S3cr3t0", texto)
    esquema = json.loads((SCHEMAS / "owasp-security-guidance-review.schema.json").read_text(encoding="utf-8"))
    t.igual("E-53 el schema es el que se valida", "owasp-security-guidance-review/1.0", esquema["$id"])
    t.vacio("E-53 el registro instalado valida",
            G.validar_schema(json.loads((REGLAS / "owasp-security-guidance-review.json").read_text(encoding="utf-8"))))
    for capa, parchar in (("la raiz", lambda d: d.update(token="x")),
                          ("el activo", lambda d: d["assets"][0].update(password="x")),
                          ("la familia", lambda d: d["families"][0].update(exploit="x")),
                          ("la fuente", lambda d: d["families"][0]["source"].update(cookie="x")),
                          ("el punto", lambda d: d["families"][0]["items"][0].update(payload="x"))):
        doc = _reg()
        parchar(doc)
        t.verdadero("E-53 una clave de mas en %s no valida" % capa, G.validar_schema(doc))
    r = _r(evidencia=_sin("cfg", dict(_prueba("cfg", "APPLICATION_CONFIGURATION"), payload="x")))
    t.verdadero("E-53 un item con un payload queda mal formado", any("mal formada" in i for i in r["issues"]))
    t.verdadero("E-53 y no hay PASS", r["state"] != "PASS")


# -- El agregado ---------------------------------------------------------------------------

def test_e54_completa_sin_hallazgos(t):
    """E-54."""
    r = _r()
    t.igual("E-54 pasa", "PASS", r["state"])
    t.igual("E-54 sin hallazgos", [], r["findings"])
    t.igual("E-54 y en seguridad cumple", "COMPLIANT", _vu10_en_seguridad(r)["result"])


def test_e55_completa_con_un_hallazgo(t):
    """E-55."""
    r, _ = _con_hallazgo()
    t.igual("E-55 pasa con un hallazgo registrado", "PASS", r["state"])
    t.igual("E-55 y el hallazgo queda a la vista", ["F-1"], r["findings"])


def test_e56_una_familia_ignorada(t):
    """E-56."""
    activos, evid, _ = _dos_familias()
    r = _r(_reg([_fam()], activos), evid)
    t.igual("E-56 una familia aplicable omitida falla", "FAIL", r["state"])
    t.igual("E-56 y se dice cual", ["API_OR_WEB_SERVICE"], r["omittedFamilies"])
    t.igual("E-56 en seguridad no cumple", "NON_COMPLIANT", _vu10_en_seguridad(r)["result"])
    t.igual("E-56 la review vacia no es FAIL, es incompleta", REVISION, _estado(_reg([])))


def test_e57_sin_frescura_no_hay_pass(t):
    """E-57."""
    r = _r(_reg([_fam(frescura="UPDATE_AVAILABLE")]))
    t.igual("E-57 sin frescura no pasa aunque este completa", FRESCURA, r["state"])
    t.verdadero("E-57 y no es FAIL", r["state"] != "FAIL")


def test_e58_un_punto_abierto(t):
    """E-58."""
    r = _con_puntos(_punto("W2", "UNRESOLVED"))
    t.igual("E-58 un punto sin resolver da REVIEW_INCOMPLETE", REVISION, r["state"])
    t.verdadero("E-58 con el punto en states", PUNTO in r["states"])


def test_e59_sin_modelo(t):
    """E-59."""
    raices = ({a.name.split(".")[0] for n in ast.walk(_arbol()) if isinstance(n, ast.Import) for a in n.names}
              | {(n.module or "") for n in ast.walk(_arbol()) if isinstance(n, ast.ImportFrom)})
    t.igual("E-59 importa esto y nada mas", sorted({"", "importlib", "io", "json", "os", "re",
                                                     "reporte_seguridad", "rutas"}), sorted(raices))
    t.igual("E-59 ningun nombre de proveedor de modelos", [],
            sorted(x for x in _literales() if re.search(r"anthropic|openai|claude|gpt|llm", x, re.I)))


def test_e60_el_mismo_resultado(t):
    """E-60."""
    activos, evid, api = _dos_familias()
    registro = _reg([_fam(), api], activos)
    base = _json(_r(registro, evid))
    t.igual("E-60 el caso de dos familias pasa", "PASS", json.loads(base)["state"])
    azar = random.Random(60)
    for vuelta in range(6):
        reg, ev = copy.deepcopy(registro), copy.deepcopy(evid)
        azar.shuffle(reg["families"])
        azar.shuffle(ev)
        for f in reg["families"]:
            azar.shuffle(f["items"])
        t.igual("E-60 desordenado %d" % vuelta, base, _json(_r(reg, ev)))
    t.igual("E-60 los diez estados", sorted(LOS_10), sorted(G.ESTADOS))
    nfc, nfd = (unicodedata.normalize(f, "W-acción") for f in ("NFC", "NFD"))
    t.igual("E-60 un punto en NFD es el de la foto en NFC", "PASS",
            _estado(_reg([_fam(puntos=[_punto(nfd, evid=["cfg"])])]),
                    _sin("foto-web", _foto(puntos=[nfc]))))


def test_e61_la_trazabilidad(t):
    """E-61."""
    for nombre, r in (("pasa", _r()), ("vacio", G.evaluar({})), ("incompleta", _r(_reg([])))):
        t.igual("E-61 %s la fuente" % nombre, TRAZA, r["source"])
        t.igual("E-61 %s la review" % nombre, "owasp-security-guidance-review", r["review"])
    u = _unidad(_r())
    t.igual("E-61 la unidad lleva Vu10 en PASS", "PASS", u["result"])
    t.igual("E-61 con su fuente", TRAZA, u["source"])
    t.igual("E-61 con sus familias", ["WEB"], u["families"])
    t.igual("E-61 y nada mas", ["applicability", "evidence", "families", "result", "source"], sorted(u))
    t.igual("E-61 sin la senal, sin resolver", "UNRESOLVED", _unidad(_r(), None)["result"])
    t.igual("E-61 un resultado ajeno no se proyecta", "UNRESOLVED", _unidad(dict(_r(), review="otra"))["result"])
    ev, _ = G.para_seguridad(_r())
    oficial = evaluacion.estado_oficial({"state": "APPROVED", "producer": "HARNESS_CHECK",
                                         "evidence": ev["controlResults"][G.REVIEW]["evidence"]})
    t.igual("E-61 el estado oficial no se mueve", "OFFICIAL_STATUS_UNRESOLVED", oficial["state"])


def test_e62_el_libro_de_siempre(t):
    """E-62."""
    carpeta = tempfile.mkdtemp(prefix="vu10_62_")
    try:
        ruta = libro.ruta_de(carpeta, "GCBA-1062")
        esperados = (("pasa", _r(), "COMPLIANT"), ("falla", _r(_reg([_fam()], _dos_familias()[0]), _dos_familias()[1]),
                                                   "NON_COMPLIANT"),
                     ("sin frescura", _r(evidencia=_sin("frescura-web")), "UNRESOLVED"))
        for i, (nombre, r, resultado) in enumerate(esperados):
            regla = _vu10_en_seguridad(r)
            t.igual("E-62 %s en seguridad" % nombre, resultado, regla["result"])
            for evento in prod.desde_regla(regla, "GCBA-1062", {"project": "P"}, "2026-09-26T10:00:%02d" % i):
                libro.agregar(ruta, evento)
        eventos = libro.leer(ruta)
        eventos = eventos[0] if isinstance(eventos, tuple) else eventos
        t.igual("E-62 tres RULE_EVALUATION de ES0902.Vu10", [("RULE_EVALUATION", "ES0902.Vu10")] * 3,
                [(e["eventType"], e["details"]["ruleKey"]) for e in eventos])
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    dominios = json.loads((REGLAS / "security-report-domains.json").read_text(encoding="utf-8"))["domains"]
    t.igual("E-62 Vu10 esta en owasp-application-security", ["owasp-application-security"],
            [d["domainId"] for d in dominios if "Vu10" in d["rules"]])
    t.igual("E-62 reporte_seguridad no tiene ningun archivo nuevo",
            ["__init__.py", "archivo.py", "libro.py", "productores.py", "reporte.py", "resumen.py"],
            sorted(p.name for p in (BIN / "reporte_seguridad").iterdir() if p.is_file()))
    t.igual("E-62 un resultado ajeno no se traduce", ({}, {}), G.para_seguridad(dict(_r(), review="otra")))
