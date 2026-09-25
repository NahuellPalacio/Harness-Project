# Una fuente oficial se puede aceptar en el proyecto: la decision APPLY, su vigencia, las
# regresiones, la promocion pendiente y el reporte de seguridad con la procedencia.
#
# Spec: docs/cambios/aceptar-fuentes-en-el-proyecto/spec.md. Cada test nombra su escenario.
# E-16, E-17 y E-18 instalan de verdad y viven en 57-aceptar-fuentes-instalador.ps1.
#
# 🔴 Los estados van clavados por literal, como en 45_conocimiento_fuentes.py.
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CLI = BIN / "dev-harness.py"

if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))
from orquestacion import frescura as fr                  # noqa: E402
from orquestacion import registro_fuentes as rf          # noqa: E402

HASH_A = "a" * 64
HASH_B = "b" * 64
PDF_ES0902 = "ES0902 - Estandar de Seguridad V6.2.pdf"
PDF_ES0901 = "ES0901 - Estandar de Desarrollo V6.2.pdf"
PDF_ES0903 = "ES0903 - Estandar de APIs V2.1.pdf"
VERSION_0230 = "dc0d258"


# -- el proyecto de prueba -----------------------------------------------------

def _escribir(ruta, contenido):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(contenido, bytes):
        ruta.write_bytes(contenido)
    else:
        ruta.write_text(contenido, encoding="utf-8", newline="\n")


def _proyecto(usuario="Nahue", archivos=None):
    base = Path(tempfile.gettempdir()) / ("harness-57-" + uuid.uuid4().hex[:8])
    proy, ficha = base / "proyecto", base / "ficha"
    config = {"usuario": usuario} if usuario is not None else {}
    _escribir(proy / ".claude" / "harness.config.json", json.dumps(config))
    for nombre, contenido in (archivos if archivos is not None else
                              {PDF_ES0902: "original ES0902 6.2",
                               PDF_ES0901: "original ES0901 6.2",
                               PDF_ES0903: "original ES0903 2.1"}).items():
        _escribir(ficha / nombre, contenido)
    return base, proy, ficha


def _cli(proy, *args, cli=CLI):
    salida = subprocess.run([sys.executable, str(cli)] + list(args) + ["--proyecto", str(proy)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (salida.returncode, salida.stdout.decode("utf-8", "replace"),
            salida.stderr.decode("utf-8", "replace"))


def _estado(proy):
    ruta = proy / ".claude" / fr.ARCHIVO
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.is_file() else None


def _bytes_del_estado(proy):
    ruta = proy / ".claude" / fr.ARCHIVO
    return ruta.read_bytes() if ruta.is_file() else None


def _entrada(sid):
    return [e for e in rf.gestionadas(rf.cargar()) if e["id"] == sid][0]


def _obs(sid="ES0902", version="6.2", sha=HASH_A, **extra):
    o = {"id": sid, "found": True, "attachmentId": None, "filename": PDF_ES0902, "size": 10,
         "created": None, "observed_version": version, "observed_sha256": sha,
         "downloaded": False, "identity_changed": None, "evidence": []}
    o.update(extra)
    return o


def _aplicar(obs, **extra):
    d = {"decision": "APPLY", "observed_version": obs["observed_version"],
         "observed_sha256": obs["observed_sha256"], "attachmentId": obs.get("attachmentId"),
         "filename": obs.get("filename"), "channel": "archivo:x", "by": "Nahue",
         "at": "2026-09-25T10:00:00", "overridesRegistryVersion": None}
    d.update(extra)
    return d


def _sin_derivados(sid):
    return {sid: {"controls": [], "matrices": [], "matrixRows": [], "agents": [],
                  "skills": []}}


# -- E-01 a E-04: aceptar, reusar, invalidar -----------------------------------

def test_e01_e02_aceptar_y_reusar(t):
    base, proy, ficha = _proyecto()
    try:
        codigo, _, err = _cli(proy, "fuentes", "--archivo", str(ficha), "--aceptar", "ES0902")
        t.igual("E-01 aceptar sale 0", 0, codigo)
        doc = _estado(proy)
        t.igual("E-01 ES0902 queda CURRENT", "CURRENT", doc["sources"]["ES0902"]["state"])
        d = doc["decisions"]["ES0902"]
        t.igual("E-01 la decision es APPLY", "APPLY", d["decision"])
        t.igual("E-01 con la version observada", "6.2", d["observed_version"])
        t.igual("E-01 con el SHA-256 del original",
                hashlib.sha256((ficha / PDF_ES0902).read_bytes()).hexdigest(),
                d["observed_sha256"])
        t.igual("E-01 con el archivo", PDF_ES0902, d["filename"])
        t.igual("E-01 con el canal", "archivo:" + str(ficha), d["channel"])
        t.igual("E-01 con quien", "Nahue", d["by"])
        t.verdadero("E-01 y cuando", bool(d["at"]))
        t.igual("E-01 no es una regresion", None, d["overridesRegistryVersion"])
        codigo, _, _ = _cli(proy, "fuentes", "--archivo", str(ficha))
        t.igual("E-02 la corrida siguiente sale 0", 0, codigo)
        t.igual("E-02 sin --aceptar, la aceptacion se reusa", "CURRENT",
                _estado(proy)["sources"]["ES0902"]["state"])
    finally:
        shutil.rmtree(str(base), ignore_errors=True)


def test_e03_otro_byte_invalida(t):
    base, proy, ficha = _proyecto()
    try:
        _cli(proy, "fuentes", "--archivo", str(ficha), "--aceptar", "ES0902")
        _escribir(ficha / PDF_ES0902, "original ES0902 6.2, reemplazado")
        _cli(proy, "fuentes", "--archivo", str(ficha))
        f = _estado(proy)["sources"]["ES0902"]
        t.igual("E-03 vuelve a FRESHNESS_UNVERIFIED", "FRESHNESS_UNVERIFIED", f["state"])
        t.igual("E-03 sin aceptacion vigente", None, f["acceptance"])
        t.verdadero("E-03 y la evidencia lo dice",
                    any("no alcanza" in e and "hash" in e for e in f["evidence"]))
    finally:
        shutil.rmtree(str(base), ignore_errors=True)


def test_e04_otra_version_invalida(t):
    base, proy, ficha = _proyecto()
    try:
        _cli(proy, "fuentes", "--archivo", str(ficha), "--aceptar", "ES0902")
        (ficha / PDF_ES0902).unlink()
        _escribir(ficha / "ES0902 - Estandar de Seguridad V6.3.pdf", "original ES0902 6.3")
        _cli(proy, "fuentes", "--archivo", str(ficha))
        f = _estado(proy)["sources"]["ES0902"]
        t.igual("E-04 sin aceptacion vigente", None, f["acceptance"])
        t.igual("E-04 se compara contra la fabrica: hay una version posterior",
                "UPDATE_AVAILABLE", f["state"])
        t.verdadero("E-04 y la evidencia dice por que no alcanza",
                    any("no alcanza" in e and "version" in e for e in f["evidence"]))
    finally:
        shutil.rmtree(str(base), ignore_errors=True)


def test_e05_otro_adjunto_invalida(t):
    entrada = _entrada("ES0902")
    obs = _obs(attachmentId="10001")
    decision = _aplicar(obs)
    t.verdadero("E-05 con el mismo adjunto, vale",
                fr.aceptacion_vigente(entrada, obs, decision) is not None)
    otro = _obs(attachmentId="10002")
    evidencia = []
    t.igual("E-05 con otro adjunto, no vale", None,
            fr.aceptacion_vigente(entrada, otro, decision, evidencia))
    t.verdadero("E-05 y dice que es el adjunto", any("adjunto" in e for e in evidencia))
    salida = fr.resolver_una(entrada, otro, True, decision)
    t.igual("E-05 el estado vuelve a la fabrica", "FRESHNESS_UNVERIFIED", salida["state"])


# -- E-06 a E-08: lo que no se acepta ------------------------------------------

def test_e06_lo_que_no_se_puede_aceptar_no_escribe(t):
    casos = (
        ("sin canal", {}, ["--aceptar", "ES0902"]),
        ("la fuente ausente", {}, ["--archivo", None, "--aceptar", "PC0901"]),
        ("sin quien", {"usuario": None}, ["--archivo", None, "--aceptar", "ES0902"]),
        ("una fuente que no existe", {}, ["--archivo", None, "--aceptar", "ES9999"]),
    )
    for nombre, extra, args in casos:
        base, proy, ficha = _proyecto(**extra)
        try:
            _cli(proy, "fuentes", "--archivo", str(ficha))
            antes = _bytes_del_estado(proy)
            args = [str(ficha) if a is None else a for a in args]
            codigo, _, err = _cli(proy, "fuentes", *args)
            t.igual("E-06 %s: sale 2" % nombre, 2, codigo)
            t.igual("E-06 %s: no escribe nada" % nombre, antes, _bytes_del_estado(proy))
        finally:
            shutil.rmtree(str(base), ignore_errors=True)
    entrada = _entrada("ES0902")
    t.igual("E-06 sin version no se acepta", "VERSION_UNRESOLVED",
            fr.aceptable(entrada, _obs(version=None), True)[0])
    t.igual("E-06 sin hash no se acepta", "FRESHNESS_UNVERIFIED",
            fr.aceptable(entrada, _obs(sha=None), True)[0])
    t.igual("E-06 con un hash que no es un hash tampoco", "FRESHNESS_UNVERIFIED",
            fr.aceptable(entrada, _obs(sha="sha256:" + HASH_A), True)[0])


def test_e07_sin_evidencia_no_hay_current(t):
    entrada = _entrada("ES0902")
    obs = _obs()
    for nombre, decision, observada in (
            ("decision sin hash", _aplicar(obs, observed_sha256=None), obs),
            ("decision de otra version", _aplicar(obs, observed_version="6.1"), obs),
            ("observacion sin hash", _aplicar(obs), _obs(sha=None)),
            ("observacion sin version", _aplicar(obs), _obs(version=None)),
            ("fuente no encontrada", _aplicar(obs), {"found": False, "evidence": []}),
            ("sin canal", _aplicar(obs), obs)):
        disponible = nombre != "sin canal"
        salida = fr.resolver_una(entrada, observada, disponible, decision)
        t.verdadero("E-07 %s: no es CURRENT" % nombre, salida["state"] != "CURRENT")
        t.igual("E-07 %s: sin aceptacion" % nombre, None, salida["acceptance"])


def test_e08_la_aceptacion_no_tapa_una_alerta(t):
    entrada = dict(_entrada("ES0902"), sha256=HASH_B)
    obs = _obs(sha=HASH_A)
    t.igual("E-08 no se acepta", "SOURCE_INTEGRITY_ALERT", fr.aceptable(entrada, obs, True)[0])
    salida = fr.resolver_una(entrada, obs, True, _aplicar(obs))
    t.igual("E-08 una decision escrita a mano no la tapa", "SOURCE_INTEGRITY_ALERT",
            salida["state"])


# -- E-09 a E-12: regresiones y promocion --------------------------------------

def test_e09_e10_regresion(t):
    base, proy, ficha = _proyecto()
    try:
        _cli(proy, "fuentes", "--archivo", str(ficha))
        antes = _bytes_del_estado(proy)
        codigo, _, err = _cli(proy, "fuentes", "--archivo", str(ficha), "--aceptar", "ES0901")
        t.igual("E-09 sin --regresion sale 2", 2, codigo)
        t.contiene("E-09 y dice que use --regresion", "--regresion", err)
        t.igual("E-09 no escribe nada", antes, _bytes_del_estado(proy))
        t.igual("E-09 sigue en regresion", "VERSION_REGRESSION",
                _estado(proy)["sources"]["ES0901"]["state"])
        codigo, _, _ = _cli(proy, "fuentes", "--archivo", str(ficha), "--aceptar", "ES0901",
                            "--regresion")
        t.igual("E-10 con --regresion sale 0", 0, codigo)
        doc = _estado(proy)
        f = doc["sources"]["ES0901"]
        t.igual("E-10 registra que version de fabrica se piso", "6.3",
                doc["decisions"]["ES0901"]["overridesRegistryVersion"])
        t.igual("E-10 queda KNOWLEDGE_PROMOTION_INCOMPLETE", "KNOWLEDGE_PROMOTION_INCOMPLETE",
                f["state"])
        t.igual("E-10 y bloquea", True, f["blocking"])
        t.igual("E-10 registry_version sigue siendo la de fabrica", "6.3", f["registry_version"])
        t.igual("E-10 la aceptada es 6.2", "6.2", f["acceptance"]["version"])
        t.verdadero("E-10 stale_derived nombra los derivados de 6.3", len(f["stale_derived"]) > 0)
    finally:
        shutil.rmtree(str(base), ignore_errors=True)


def test_e11_la_regresion_vale_contra_la_fabrica_que_piso(t):
    entrada = _entrada("ES0901")
    obs = _obs("ES0901", "6.2", HASH_A, filename=PDF_ES0901)
    decision = _aplicar(obs, overridesRegistryVersion="6.3")
    t.verdadero("E-11 con la fabrica en 6.3, vale",
                fr.aceptacion_vigente(entrada, obs, decision) is not None)
    otra = dict(entrada, version="6.4")
    t.igual("E-11 si la fabrica pasa a 6.4, deja de valer", None,
            fr.aceptacion_vigente(otra, obs, decision))
    t.igual("E-11 y sin overridesRegistryVersion nunca valio", None,
            fr.aceptacion_vigente(entrada, obs, _aplicar(obs)))


def test_e12_aceptar_una_posterior_es_promocion_pendiente(t):
    entrada = dict(_entrada("ES0901"), sha256=None)
    obs = _obs("ES0901", "6.4", HASH_A, filename="ES0901 - Estandar V6.4.pdf")
    ind = _sin_derivados("ES0901")
    sin = fr.resolver_una(entrada, obs, True, None, ind)
    t.igual("E-12 sin aceptacion, UPDATE_AVAILABLE", "UPDATE_AVAILABLE", sin["state"])
    con = fr.resolver_una(entrada, obs, True, _aplicar(obs), ind)
    t.igual("E-12 aceptada, con el extracto en 6.3, KNOWLEDGE_PROMOTION_INCOMPLETE",
            "KNOWLEDGE_PROMOTION_INCOMPLETE", con["state"])
    t.verdadero("E-12 y la evidencia nombra al extracto",
                any("extracto" in e for e in con["evidence"]))


# -- E-13 a E-15: sin aceptacion, como hoy -------------------------------------

def _arbol_0230():
    """El arbol de 0.23.0 en un temporal, sacado de git. Es la unica comparacion honesta contra
    "como hoy": correr el codigo de antes sobre la misma evidencia."""
    destino = Path(tempfile.mkdtemp(prefix="harness-0230-"))
    salida = subprocess.run(["git", "-C", str(RAIZ), "archive", "--format=tar", VERSION_0230,
                             "comun", "harnesses", "normativa/extractos"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if salida.returncode != 0:
        return None
    ruta = destino / "arbol.tar"
    ruta.write_bytes(salida.stdout)
    with tarfile.open(str(ruta)) as tar:
        tar.extractall(str(destino))
    return destino


def test_e13_sin_aceptacion_igual_que_0230(t):
    viejo = _arbol_0230()
    t.verdadero("E-13 el arbol de 0.23.0 se pudo sacar de git", viejo is not None)
    if viejo is None:
        return
    base, proy, ficha = _proyecto()
    base2, proy2, _ = _proyecto()
    try:
        c1, nuevo, _ = _cli(proy, "fuentes", "--archivo", str(ficha), "--json")
        c2, antes, _ = _cli(proy2, "fuentes", "--archivo", str(ficha), "--json",
                            cli=viejo / "harnesses" / "desarrollo" / "bin" / "dev-harness.py")
        t.igual("E-13 los dos salen 0", [0, 0], [c1, c2])
        nuevo, antes = json.loads(nuevo), json.loads(antes)
        t.igual("E-13 las mismas fuentes", sorted(antes["sources"]), sorted(nuevo["sources"]))
        for sid in sorted(antes["sources"]):
            a, n = antes["sources"][sid], nuevo["sources"][sid]
            t.igual("E-13 %s: sin aceptacion" % sid, None, n.get("acceptance"))
            for campo in ("state", "evidence", "registry_version", "observed_version",
                          "observed_sha256", "stale_derived", "blocking", "effectiveRisk"):
                t.igual("E-13 %s: %s igual que 0.23.0" % (sid, campo), a[campo], n[campo])
        t.igual("E-13 ES0902 FRESHNESS_UNVERIFIED", "FRESHNESS_UNVERIFIED",
                nuevo["sources"]["ES0902"]["state"])
        t.igual("E-13 ES0901 VERSION_REGRESSION", "VERSION_REGRESSION",
                nuevo["sources"]["ES0901"]["state"])
        t.igual("E-13 ES0903 VERSION_REGRESSION", "VERSION_REGRESSION",
                nuevo["sources"]["ES0903"]["state"])
    finally:
        for b in (base, base2, viejo):
            shutil.rmtree(str(b), ignore_errors=True)


def test_e14_posponer(t):
    entrada = dict(_entrada("ES0901"), sha256=HASH_A)
    obs = _obs("ES0901", "6.4", HASH_B, filename="ES0901 - Estandar V6.4.pdf")
    ind = _sin_derivados("ES0901")
    t.igual("E-14 la base es UPDATE_AVAILABLE", "UPDATE_AVAILABLE",
            fr.resolver_una(entrada, obs, True, None, ind)["state"])
    pospuesta = {"decision": "POSTPONE", "observed_version": "6.4", "observed_sha256": HASH_B}
    salida = fr.resolver_una(entrada, obs, True, pospuesta, ind)
    t.igual("E-14 posponer la misma identidad da ACKNOWLEDGED_PENDING", "ACKNOWLEDGED_PENDING",
            salida["state"])
    t.igual("E-14 y bloquea", True, salida["blocking"])
    otra = dict(pospuesta, observed_sha256=HASH_A)
    t.igual("E-14 sobre otra identidad no alcanza", "UPDATE_AVAILABLE",
            fr.resolver_una(entrada, obs, True, otra, ind)["state"])


def test_e15_fuente_nueva(t):
    entrada = dict(_entrada("GuiaDGISIS"), version=None, sha256=None)
    obs = _obs("GuiaDGISIS", "1.0", HASH_A, filename="Guia de Procesos - DGISIS.pdf")
    ind = _sin_derivados("GuiaDGISIS")
    t.igual("E-15 sin version de fabrica es NEW_SOURCE", "NEW_SOURCE",
            fr.resolver_una(entrada, obs, True, None, ind)["state"])
    t.igual("E-15 se puede aceptar", (None, None), fr.aceptable(entrada, obs, True))
    salida = fr.resolver_una(entrada, obs, True, _aplicar(obs), ind)
    t.igual("E-15 aceptada, con el extracto en 1.0, CURRENT", "CURRENT", salida["state"])


# -- E-19 y E-20: el reporte de seguridad --------------------------------------

def _reporte(proy):
    codigo, _, err = _cli(proy, "seguridad", "PRUEBA-1", "--conocimiento", "--reporte")
    carpeta = proy / ".claude" / "runtime" / "security" / "PRUEBA-1"
    resumen = json.loads((carpeta / "security-summary.json").read_text(encoding="utf-8"))
    md = (carpeta / "security-status.md").read_text(encoding="utf-8")
    return codigo, resumen, md


def test_e19_reporte_con_la_fuente_aceptada(t):
    base, proy, ficha = _proyecto()
    try:
        _cli(proy, "fuentes", "--archivo", str(ficha), "--aceptar", "ES0902")
        codigo, resumen, md = _reporte(proy)
        t.igual("E-19 el reporte sale 0", 0, codigo)
        bloqueos = [b for b in resumen["blockingConditions"] if b.get("source") == "knowledge"]
        t.igual("E-19 sin condicion de conocimiento", [], bloqueos)
        k = resumen["knowledge"]
        d = _estado(proy)["decisions"]["ES0902"]
        t.igual("E-19 knowledge.version", "6.2", k["version"])
        t.igual("E-19 knowledge.freshness", "CURRENT", k["freshness"])
        t.igual("E-19 knowledge.sha256", d["observed_sha256"], k["sha256"])
        t.igual("E-19 knowledge.channel", "archivo:" + str(ficha), k["channel"])
        t.igual("E-19 knowledge.acceptedBy", "Nahue", k["acceptedBy"])
        t.igual("E-19 knowledge.acceptedAt", d["at"], k["acceptedAt"])
        t.igual("E-19 knowledge.registryVersion", "6.2", k["registryVersion"])
        seccion = md[md.find("## Conocimiento normativo"):md.find("## Condiciones de bloqueo")]
        for valor in (d["observed_sha256"], "archivo:", "Nahue", d["at"],
                      "Versión que esperaba el registro"):
            t.contiene("E-19 el md muestra %s" % valor[:20], valor, seccion)
    finally:
        shutil.rmtree(str(base), ignore_errors=True)


def test_e20_reporte_sin_aceptacion(t):
    base, proy, ficha = _proyecto()
    try:
        _cli(proy, "fuentes", "--archivo", str(ficha))
        codigo, resumen, _ = _reporte(proy)
        bloqueos = [b for b in resumen["blockingConditions"] if b.get("source") == "knowledge"]
        t.igual("E-20 hay una condicion de conocimiento", 1, len(bloqueos))
        t.contiene("E-20 con FRESHNESS_UNVERIFIED", "FRESHNESS_UNVERIFIED",
                   json.dumps(bloqueos, ensure_ascii=False))
        t.igual("E-20 knowledge.sha256 sin aceptacion es null", None,
                resumen["knowledge"]["sha256"])
    finally:
        shutil.rmtree(str(base), ignore_errors=True)


# -- E-21 y E-22: contrato y presentacion --------------------------------------

def test_e21_el_contrato(t):
    base, proy, ficha = _proyecto()
    viejo = _arbol_0230()
    try:
        _cli(proy, "fuentes", "--archivo", str(ficha), "--aceptar", "ES0902")
        doc = _estado(proy)
        t.igual("E-21 con una aceptacion valida contra sources-state/1.1", [], fr.validar(doc))
        t.igual("E-21 sigue siendo sources-state/1.1", "sources-state/1.1", doc["schema_version"])
        if viejo is not None:
            base2, proy2, _ = _proyecto()
            try:
                _cli(proy2, "fuentes", "--archivo", str(ficha),
                     cli=viejo / "harnesses" / "desarrollo" / "bin" / "dev-harness.py")
                t.igual("E-21 un estado de 0.23.0 valida contra el schema nuevo", [],
                        fr.validar(_estado(proy2)))
            finally:
                shutil.rmtree(str(base2), ignore_errors=True)
        roto = json.loads(json.dumps(doc))
        roto["decisions"]["ES0902"]["nota"] = "acepto porque si"
        t.verdadero("E-21 una clave no declarada en la decision se rechaza",
                    bool(fr.validar(roto)))
    finally:
        shutil.rmtree(str(base), ignore_errors=True)
        if viejo is not None:
            shutil.rmtree(str(viejo), ignore_errors=True)


def test_e22_espanol_para_la_persona(t):
    base, proy, ficha = _proyecto()
    try:
        codigo, texto, _ = _cli(proy, "fuentes", "--archivo", str(ficha), "--aceptar", "ES0902")
        t.igual("E-22 sale 0", 0, codigo)
        for frase in ("Aceptada ES0902 6.2", "Canal     archivo:", "Aceptó    Nahue",
                      "Estado    CURRENT"):
            t.contiene("E-22 dice «%s»" % frase, frase, texto)
        codigo, texto, _ = _cli(proy, "fuentes", "--archivo", str(ficha), "--aceptar", "ES0901",
                                "--regresion")
        t.contiene("E-22 una regresion aceptada se avisa", "anterior a la 6.3", texto)
        codigo, salida, _ = _cli(proy, "fuentes", "--archivo", str(ficha), "--json")
        estados = set(f["state"] for f in json.loads(salida)["sources"].values())
        t.verdadero("E-22 --json con estados canonicos", estados <= set(fr.ESTADOS))
    finally:
        shutil.rmtree(str(base), ignore_errors=True)
