# El reporte de seguridad: del libro al tablero.
#
# Escenarios E-01 a E-55 de docs/cambios/reporte-de-seguridad/spec.md. E-56 vive en
# 30-contabilidad-instalador.ps1, que es el caso que ya instala `desarrollo` en un proyecto
# temporal y corre la CLI desde ahi.
#
# 🔴 Casi todo pasa por los productores y por `libro.agregar`, no por un libro escrito a mano: lo
# que se prueba es que la salida de una funcion del harness llega al tablero sin que nadie en el
# medio decida nada. Donde un test arma un evento a mano es para probar que `agregar` lo rechaza.
import ast
import html.parser
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
CLI = BIN / "dev-harness.py"
PAQUETE = BIN / "reporte_seguridad"
SCHEMAS = RAIZ / "comun" / "schemas"
REGLAS = RAIZ / "harnesses" / "desarrollo" / "reglas"

sys.path.insert(0, str(BIN))
from orquestacion import evaluacion                    # noqa: E402
from orquestacion import frescura                      # noqa: E402
from orquestacion import integridad                    # noqa: E402
from orquestacion import seguridad                     # noqa: E402
from orquestacion import tools as orq_tools            # noqa: E402
from reporte_seguridad import libro                    # noqa: E402
from reporte_seguridad import productores as prod      # noqa: E402
from reporte_seguridad import reporte                  # noqa: E402
from reporte_seguridad import resumen                  # noqa: E402

ARMADOR = orq_tools._armador()
TAREA = "GCBA-4848"
MATRIZ = (REGLAS / seguridad.ARCHIVO).read_bytes()
DOMINIOS = resumen.cargar_dominios()
DOMINIOS_BYTES = (REGLAS / "security-report-domains.json").read_bytes()
ALCANCE = {"project": "Sistema de prueba", "application": "tramites-web", "environment": "QA",
           "branch": "release/1.4", "commitSha": "abc123def", "buildId": "b-77",
           "releaseId": "1.4.0", "artifactDigest": "sha256:d1"}

_RELOJ = [0]


def _cuando():
    _RELOJ[0] += 1
    return "2026-09-23T10:%02d:%02d" % (_RELOJ[0] // 60, _RELOJ[0] % 60)


# -- las entradas, con la forma de lo que devuelve cada funcion del harness ----

def _regla(rid, resultado):
    """La forma de `seguridad.resultado`."""
    return {"rule": rid, "ruleKey": seguridad.clave(rid), "result": resultado,
            "states": [], "reasons": [], "applicability": "APPLICABLE",
            "source": {"standard": "ES0902", "version": "6.2", "rule": rid}}


def _reglas(resultados=None, por_defecto=seguridad.CUMPLE, omitir=()):
    resultados = resultados or {}
    eventos = []
    for rid in seguridad.INVENTARIO:
        if rid in omitir:
            continue
        eventos += prod.desde_regla(_regla(rid, resultados.get(rid, por_defecto)), TAREA,
                                    ALCANCE, _cuando())
    return eventos


def _fuentes(estado=frescura.CURRENT, version="6.2", verificado="2026-09-23T09:00:00"):
    return {"schema_version": frescura.VERSION_SCHEMA, "verified_at": verificado,
            "sources": {"ES0902": {"state": estado, "registry_version": version,
                                   "blocking": estado not in frescura.NO_BLOQUEAN}}}


def _conocimiento(estado=frescura.CURRENT):
    return prod.desde_frescura(_fuentes(estado), TAREA, ALCANCE)


def _check(control, estado, regla=None, evidencia=None):
    salida = {"control": control, "state": estado, "evidence": list(evidencia or [])}
    if regla:
        salida["rule"] = regla
    return salida


def _hallazgo(fid, severidad, confianza="MEDIUM", bloquea=None, titulo=None, regla=None):
    h = {"findingId": fid, "severity": severidad, "confidence": confianza,
         "evidence": ["ev:%s" % fid]}
    if bloquea is not None:
        h["blocking"] = bloquea
    if titulo:
        h["title"] = titulo
    if regla:
        h["rule"] = regla
    return h


def _c2(estado, evidencia=("dgsei:acta-1",)):
    return {"control": "qa-security-approval-evidence", "rule": "C2", "state": estado,
            "approvalEvidenceRef": {"approvalId": "AP-1", "evidenceReference": "dgsei:acta-1",
                                    "fingerprint": "sha256:" + "a" * 64},
            "evidence": list(evidencia)}


def _base_confiable():
    return {"repository": "gitlab/tramites", "ref": "v1.3.0", "commitSha": "c0ffee1",
            "source": "APPROVED_RELEASE", "evidence": ["release:1.3.0"]}


def _tmp():
    return tempfile.mkdtemp(prefix="sr48_")


def _libro_de(eventos):
    carpeta = _tmp()
    ruta = libro.ruta_de(carpeta, TAREA)
    libro.agregar_varios(ruta, eventos)
    return carpeta, ruta


def _resumir(eventos, bloque4=b"", dominios=None):
    carpeta, ruta = _libro_de(eventos)
    try:
        return resumen.resumir(libro.bytes_de(ruta), MATRIZ, TAREA,
                               DOMINIOS_BYTES if dominios is None else dominios, bloque4)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def _todo(eventos):
    r = _resumir(eventos)
    return r, reporte.generar_md(r), reporte.generar_html(r)


def _fila(r, rid):
    return [f for f in r["normative"]["rules"] if f["rule"] == rid][0]


def _fuentes_py(paquete=PAQUETE):
    return sorted(paquete.rglob("*.py"))


def _imports(ruta):
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    nombres = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres += [a.name for a in nodo.names]
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level:
                nombres += ["." + (nodo.module or "") + ":" + a.name for a in nodo.names]
            else:
                nombres.append(nodo.module or "")
                nombres += ["%s.%s" % (nodo.module, a.name) for a in nodo.names]
    return nombres


class _Campos(html.parser.HTMLParser):
    """Junta (data-field, texto) de cada elemento que declara uno."""

    def __init__(self):
        html.parser.HTMLParser.__init__(self)
        self.campos, self._pila = [], []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        self._pila.append([d.get("data-field"), []])

    def handle_endtag(self, tag):
        if self._pila:
            campo, textos = self._pila.pop()
            if campo is not None:
                self.campos.append((campo, "".join(textos)))

    def handle_data(self, data):
        for item in self._pila:
            item[1].append(data)


def _campos(html_):
    p = _Campos()
    p.feed(html_)
    return p.campos


def _pagina_1(html_):
    return html_.split('<section class="pagina" id="pagina-2">')[0]


def _resolver(r, ruta):
    """La ruta del data-field, resuelta aca y no con el renderizador.

    `<ruta>.length` es la unica ruta derivada que la pagina usa: la cantidad de elementos de la
    lista en `<ruta>`. Se resuelve con esa regla, escrita aca de nuevo.
    """
    derivada = ruta.endswith(".length")
    if derivada:
        ruta = ruta[:-len(".length")]
    actual = r
    for m in re.finditer(r"([A-Za-z0-9_]+)|\[(\d+)\]", ruta):
        if m.group(1) is not None:
            actual = actual[m.group(1)]
        else:
            actual = actual[int(m.group(2))]
    if derivada:
        assert isinstance(actual, list), ruta
        return len(actual)
    return actual


def _esperado(r, ruta):
    """Lo que la pagina tiene que mostrar, calculado aca y no con el renderizador."""
    valor = _resolver(r, ruta)
    if ruta.endswith("Pct"):
        return "N/D" if valor is None else "%.1f%%" % valor
    if valor is None or valor == "":
        return "desconocido"
    if valor is True:
        return "sí"
    if valor is False:
        return "no"
    if isinstance(valor, list):
        return ", ".join(str(v) for v in valor) if valor else "ninguna"
    return str(valor)


def _tabla_ejecutiva(md):
    bloque = md.split("## Resumen ejecutivo", 1)[1].split("\n## ", 1)[0]
    filas = {}
    for linea in bloque.splitlines():
        partes = [p.strip() for p in linea.strip().strip("|").split("|")]
        if len(partes) == 2 and partes[0] not in ("Métrica", "---"):
            filas[partes[0]] = partes[1]
    return filas


def _correr_cli(argv):
    spec = importlib.util.spec_from_file_location("dev_harness_sr48", str(CLI))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    salida, error = io.StringIO(), io.StringIO()
    previos = (sys.stdout, sys.stderr)
    sys.stdout, sys.stderr = salida, error
    try:
        codigo = modulo.main(argv)
    finally:
        sys.stdout, sys.stderr = previos
    return codigo, salida.getvalue(), error.getvalue()


def _proyecto_con_fuentes(estado=frescura.CURRENT):
    carpeta = _tmp()
    os.makedirs(os.path.join(carpeta, ".claude"))
    with io.open(frescura.ruta_por_defecto(carpeta), "w", encoding="utf-8") as f:
        f.write(json.dumps(_fuentes(estado)))
    return carpeta


# -- el libro --------------------------------------------------------------------

def test_e01_el_libro_es_append_only(t):
    carpeta = _tmp()
    try:
        ruta = libro.ruta_de(carpeta, TAREA)
        a = prod.desde_regla(_regla("O1", seguridad.CUMPLE), TAREA, ALCANCE, _cuando())[0]
        b = prod.desde_regla(_regla("O2", seguridad.NO_CUMPLE), TAREA, ALCANCE, _cuando())[0]
        t.verdadero("E-01 el primer evento entra", libro.agregar(ruta, a)[0])
        antes = libro.bytes_de(ruta)
        t.verdadero("E-01 el segundo evento entra", libro.agregar(ruta, b)[0])
        despues = libro.bytes_de(ruta)
        t.verdadero("E-01 los bytes que ya estaban quedan identicos al frente",
                    despues.startswith(antes) and len(despues) > len(antes))
        t.igual("E-01 un eventId repetido no entra dos veces", False, libro.agregar(ruta, a)[0])
        t.igual("E-01 y el libro no cambia", despues, libro.bytes_de(ruta))
        t.igual("E-01 quedan dos eventos", 2, len(libro.leer(ruta)))
        try:
            libro.escribir_atomico(ruta, "{}")
            t.verdadero("E-01 el escritor atomico se niega a pisar el libro", False)
        except ValueError:
            t.verdadero("E-01 el escritor atomico se niega a pisar el libro", True)
        try:
            reporte._escribir(ruta, "x")
            t.verdadero("E-01 el del reporte tambien", False)
        except ValueError:
            t.verdadero("E-01 el del reporte tambien", True)
        t.igual("E-01 despues de los dos intentos el libro sigue igual", despues,
                libro.bytes_de(ruta))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def test_e01_el_paquete_no_tiene_verbo_que_reescriba_el_libro(t):
    prohibidos = ("remove", "unlink", "rmtree", "truncate", "rmdir", "removedirs")
    for ruta in _fuentes_py():
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Attribute) and nodo.attr in prohibidos:
                t.verdadero("E-01 %s no llama %s" % (ruta.name, nodo.attr), False)
        # Todo `open` en modo de escritura vive en una funcion que se niega a pisar el libro.
        for funcion in [n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef)]:
            for nodo in ast.walk(funcion):
                if not (isinstance(nodo, ast.Call) and getattr(nodo.func, "attr", "") == "open"):
                    continue
                modos = [a.value for a in nodo.args[1:2] if isinstance(a, ast.Constant)]
                modos += [k.value.value for k in nodo.keywords
                          if k.arg == "mode" and isinstance(k.value, ast.Constant)]
                for modo in modos:
                    if "w" in modo or "+" in modo:
                        t.verdadero("E-01 %s.%s abre en `%s` y es un escritor guardado"
                                    % (ruta.name, funcion.name, modo),
                                    funcion.name in ("escribir_atomico", "_escribir"))
                    if "a" in modo:
                        t.igual("E-01 solo agregar abre en modo `a`", "agregar", funcion.name)


def test_e02_un_evento_incompleto_no_entra(t):
    carpeta = _tmp()
    try:
        ruta = libro.ruta_de(carpeta, TAREA)
        base = prod.desde_regla(_regla("O1", seguridad.CUMPLE), TAREA, ALCANCE, _cuando())[0]
        libro.agregar(ruta, base)
        antes = libro.bytes_de(ruta)
        for campo in ("schema_version", "eventId", "timestamp", "eventType", "taskId", "scope",
                      "result"):
            roto = dict(base)
            roto.pop(campo)
            roto["eventId"] = "sev-sin-%s" % campo if campo != "eventId" else None
            if campo == "eventId":
                roto.pop("eventId")
            try:
                libro.agregar(ruta, roto)
                t.verdadero("E-02 sin %s se rechaza" % campo, False)
            except libro.EventoInvalido:
                t.verdadero("E-02 sin %s se rechaza" % campo, True)
            t.igual("E-02 sin %s el libro queda igual" % campo, antes, libro.bytes_de(ruta))
        otro = dict(base, eventId="sev-otro-tipo", eventType="RULE_OPINION")
        try:
            libro.agregar(ruta, otro)
            t.verdadero("E-02 un eventType fuera del enum se rechaza", False)
        except libro.EventoInvalido:
            t.verdadero("E-02 un eventType fuera del enum se rechaza", True)
        t.igual("E-02 y el libro queda igual", antes, libro.bytes_de(ruta))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def test_e03_ningun_secreto_llega_al_disco(t):
    carpeta = _tmp()
    try:
        ruta = libro.ruta_de(carpeta, TAREA)
        pem = ("-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEAq9wZ3kLmN8pQrStUvWxYz0123abcd\n"
               "Zq8Lm4Np2Rs6Tu0Vw9Xy1Za3Bc5De7Fg\n-----END RSA PRIVATE KEY-----")
        secretos = {
            "contrasena": "Hunter2Qw9Zp!",
            "bearer": "Bearer q8Zk3Lm9Np2Rs6Tu0Vw4Xy7Aa1Bb",
            "pem": "MIIEowIBAAKCAQEAq9wZ3kLmN8pQrStUvWxYz0123abcd",
            "jsession": "JSESSIONID=9F8E7D6C5B4A39281706",
            "sesion": "sessionid=q1w2e3r4t5y6u7i8o9p0",
        }
        h = _hallazgo("SEC-1", "HIGH", titulo="login con password=%s" % secretos["contrasena"])
        h["evidence"] = [secretos["jsession"], pem, "cabecera %s" % secretos["bearer"]]
        evento = prod.desde_hallazgo(h, "CREATED", TAREA, ALCANCE, cuando=_cuando())[0]
        evento["details"] = dict(evento["details"], nota="cookie %s" % secretos["sesion"],
                                 anidado={"auth": secretos["bearer"]},
                                 password="p4ssW0rdReal", token="tk-9Zq8Yp7Xo6",
                                 secret="s3cr3t-Valor", cookie="c00kie-valor",
                                 sessionId="sid-8877", privateKey="pk-5566")
        libro.agregar(ruta, evento)
        crudo = libro.bytes_de(ruta).decode("utf-8")
        for nombre, valor in sorted(secretos.items()):
            t.no_contiene("E-03 %s no llega al disco" % nombre, valor, crudo)
        t.no_contiene("E-03 el cuerpo de la clave PEM tampoco", "Zq8Lm4Np2Rs6Tu0Vw9Xy1Za3Bc5De7Fg",
                      crudo)
        for valor in ("q8Zk3Lm9Np2Rs6Tu0Vw4Xy7Aa1Bb", "9F8E7D6C5B4A39281706",
                      "q1w2e3r4t5y6u7i8o9p0", "Hunter2Qw9Zp"):
            t.no_contiene("E-03 ni el valor suelto %s..." % valor[:4], valor, crudo)
        escrito = libro.leer(ruta)[0]["details"]
        for clave in ("password", "token", "secret", "cookie", "sessionId", "privateKey"):
            t.igual("E-03 details.%s llega como [redactado]" % clave, "[redactado]",
                    escrito.get(clave))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def test_e04_sin_productor_o_sin_huella_no_entra(t):
    carpeta = _tmp()
    try:
        ruta = libro.ruta_de(carpeta, TAREA)
        base = prod.desde_regla(_regla("O1", seguridad.CUMPLE), TAREA, ALCANCE, _cuando())[0]
        casos = {
            "sin details": dict(base, details=None),
            "sin producer": dict(base, details={"ruleKey": "ES0902.O1"}),
            "con un producer que no es de la lista": dict(base, details={"producer": "a-mano"}),
            "sin evidenceFingerprints": dict((k, v) for k, v in base.items()
                                             if k != "evidenceFingerprints"),
            "con evidenceFingerprints vacio": dict(base, evidenceFingerprints=[]),
            "con una huella que no es sha256": dict(base, evidenceFingerprints=["md5:abc"]),
        }
        for nombre, evento in sorted(casos.items()):
            evento = dict(evento, eventId="sev-%s" % nombre.replace(" ", "-"))
            try:
                libro.agregar(ruta, evento)
                t.verdadero("E-04 %s se rechaza" % nombre, False)
            except libro.EventoInvalido:
                t.verdadero("E-04 %s se rechaza" % nombre, True)
        t.igual("E-04 el libro sigue vacio", b"", libro.bytes_de(ruta))
        t.verdadero("E-04 y el de un productor si entra", libro.agregar(ruta, base)[0])
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


# -- el resumen ------------------------------------------------------------------

def _libro_variado():
    return (_conocimiento() + _reglas({"Vu2": seguridad.NO_CUMPLE}, omitir=("G3",))
            + prod.desde_hallazgo(_hallazgo("SEC-9", "CRITICAL"), "CREATED", TAREA, ALCANCE,
                                  cuando=_cuando())
            + prod.desde_check(_check("browser-close-session-termination",
                                      "BROWSER_SESSION_TERMINATION_TEST_UNSAFE", "Vu3"),
                               TAREA, ALCANCE, _cuando()))


def test_e05_el_mismo_libro_da_el_mismo_resumen_byte_a_byte(t):
    carpeta, ruta = _libro_de(_libro_variado())
    try:
        uno = resumen.como_texto(resumen.generar(carpeta, TAREA))
        dos = resumen.como_texto(resumen.generar(carpeta, TAREA))
        t.igual("E-05 dos corridas, el mismo texto", uno, dos)
        destino = libro.ruta_de(carpeta, TAREA, libro.RESUMEN)
        resumen.escribir(resumen.generar(carpeta, TAREA), destino)
        primero = Path(destino).read_bytes()
        resumen.escribir(resumen.generar(carpeta, TAREA), destino)
        t.igual("E-05 y el mismo archivo byte a byte", primero, Path(destino).read_bytes())
        r = json.loads(uno)
        eventos = libro.leer(ruta)
        t.igual("E-05 generatedAt es el timestamp del ultimo evento", eventos[-1]["timestamp"],
                r["generatedAt"])
        t.igual("E-05 la huella es la de las cuatro entradas",
                resumen.huella_de_la_foto(libro.bytes_de(ruta), MATRIZ, DOMINIOS_BYTES, None),
                r["snapshotFingerprint"])
        t.igual("E-05 reportId sale de la huella",
                "SEC-%s-%s" % (TAREA, r["snapshotFingerprint"][7:19]), r["reportId"])
        t.verdadero("E-05 las claves se escriben ordenadas",
                    uno == json.dumps(json.loads(uno), ensure_ascii=False, indent=2,
                                      sort_keys=True) + "\n")
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def test_e06_el_paquete_no_llama_modelos_ni_hace_red(t):
    permitidos = ("io", "os", "sys", "json", "re", "hashlib", "decimal", "datetime", "tempfile",
                  "rutas", "contexto", "orquestacion")
    prohibidos = ("urllib", "http", "socket", "ssl", "requests", "anthropic", "openai",
                  "integraciones", "controles", "subprocess", "httpx", "aiohttp")
    for ruta in _fuentes_py():
        for nombre in _imports(ruta):
            if nombre.startswith("."):
                continue
            raiz = nombre.split(".")[0]
            t.verdadero("E-06 %s importa %s, de la stdlib o del harness" % (ruta.name, nombre),
                        raiz in permitidos)
            t.verdadero("E-06 %s no importa %s" % (ruta.name, nombre), raiz not in prohibidos)


def test_e07_no_hay_puntaje(t):
    r = _resumir(_libro_variado())
    prohibidas = ("score", "grade", "rating", "riskscore")

    def claves(nodo):
        if isinstance(nodo, dict):
            for k, v in nodo.items():
                yield k
                for x in claves(v):
                    yield x
        elif isinstance(nodo, list):
            for v in nodo:
                for x in claves(v):
                    yield x

    esquema = json.loads((SCHEMAS / "security-summary.schema.json").read_text(encoding="utf-8"))
    for origen, nodo in (("el resumen", r), ("el schema", esquema)):
        encontradas = sorted(set(k for k in claves(nodo) if str(k).lower() in prohibidas))
        t.vacio("E-07 %s no tiene score, grade, rating ni riskScore" % origen, encontradas)
    numericos = sorted(k for k, v in r.items()
                       if isinstance(v, (int, float)) and not isinstance(v, bool))
    t.vacio("E-07 ningun valor numerico global del sistema", numericos)


def test_e08_no_aplicable_no_suma_al_denominador(t):
    r = _resumir(_conocimiento() + _reglas({"Vu9": seguridad.NO_APLICABLE}))
    t.igual("E-08 veinte PASS y una NOT_APPLICABLE dan 20 aplicables", 20,
            r["coverage"]["applicableRules"])
    t.igual("E-08 y la cobertura es 100", 100.0, r["coverage"]["assessmentCoveragePct"])


def test_e09_unresolved_se_intento_y_no_se_resolvio(t):
    r = _resumir(_conocimiento() + _reglas({"Vu3": seguridad.RESULTADO_SIN_RESOLVER}))
    t.igual("E-09 suma a attemptedRules", 21, r["coverage"]["attemptedRules"])
    t.igual("E-09 y no a resolvedRules", 20, r["coverage"]["resolvedRules"])
    t.igual("E-09 cobertura 100.0", 100.0, r["coverage"]["assessmentCoveragePct"])
    t.igual("E-09 resolucion 95.2, redondeada a un decimal", 95.2,
            r["coverage"]["evidenceResolutionPct"])


def test_e10_sin_evento_suma_a_aplicables_y_no_a_intentadas(t):
    r = _resumir(_conocimiento() + _reglas(omitir=("Vu5",)))
    t.igual("E-10 applicableRules", 21, r["coverage"]["applicableRules"])
    t.igual("E-10 attemptedRules", 20, r["coverage"]["attemptedRules"])
    t.igual("E-10 la regla figura NOT_EVALUATED", "NOT_EVALUATED", _fila(r, "Vu5")["result"])


def test_e11_sin_denominador_es_n_d(t):
    r, md, html_ = _todo(_conocimiento() + _reglas(por_defecto=seguridad.NO_APLICABLE))
    t.igual("E-11 applicableRules es 0", 0, r["coverage"]["applicableRules"])
    t.igual("E-11 assessmentCoveragePct es null", None, r["coverage"]["assessmentCoveragePct"])
    t.igual("E-11 evidenceResolutionPct es null", None, r["coverage"]["evidenceResolutionPct"])
    filas = _tabla_ejecutiva(md)
    t.igual("E-11 el md dice N/D en la cobertura", "N/D", filas["Cobertura de la evaluación"])
    t.igual("E-11 y en la resolucion", "N/D", filas["Resolución de la evidencia"])
    t.no_contiene("E-11 el md nunca dice 100%", "100", " ".join(filas.values()))
    campos = dict(_campos(html_))
    t.igual("E-11 el html dice N/D", "N/D", campos["coverage.assessmentCoveragePct"])
    t.no_contiene("E-11 el html nunca dice 100%", "100.0%", html_)


def test_e12_el_resumen_valida_y_los_schemas_se_entienden(t):
    for nombre in ("security-ledger-event", "security-summary", "security-report"):
        esquema = json.loads((SCHEMAS / ("%s.schema.json" % nombre)).read_text(encoding="utf-8"))
        try:
            ARMADOR.controlar_soporte(esquema)
            t.verdadero("E-12 %s pasa entero por controlar_soporte" % nombre, True)
        except Exception as e:  # noqa: BLE001
            t.verdadero("E-12 %s pasa entero por controlar_soporte: %s" % (nombre, e), False)
    for nombre, eventos in (("variado", _libro_variado()), ("vacio", []),
                            ("sin denominador",
                             _reglas(por_defecto=seguridad.NO_APLICABLE))):
        r = _resumir(eventos)
        t.vacio("E-12 el resumen %s valida contra security-summary" % nombre, resumen.validar(r))
    esquema = json.loads((SCHEMAS / "security-report.schema.json").read_text(encoding="utf-8"))
    t.vacio("E-12 el contrato de renderizado valida contra security-report",
            ARMADOR.validar(reporte.CONTRATO, esquema))
    cobertura = json.loads((SCHEMAS / "security-summary.schema.json").read_text(
        encoding="utf-8"))["properties"]["coverage"]["properties"]
    t.igual("E-12 la divergencia del paquete: los porcentajes admiten null",
            [["number", "null"], ["number", "null"]],
            [cobertura["assessmentCoveragePct"]["type"],
             cobertura["evidenceResolutionPct"]["type"]])


# -- el estado del sistema -------------------------------------------------------

def test_e13_frescura_bloqueante_da_blocked(t):
    r = _resumir(_conocimiento(frescura.SIN_VERIFICAR) + _reglas())
    t.igual("E-13 veintiuna PASS y frescura bloqueante: BLOCKED", "BLOCKED",
            r["systemSecurityState"])
    t.verdadero("E-13 con un bloqueo de knowledge",
                any(b["source"] == "knowledge" for b in r["blockingConditions"]))


def test_e14_sin_conocimiento_da_blocked(t):
    r = _resumir(_reglas())
    t.igual("E-14 sin KNOWLEDGE_STATE: BLOCKED", "BLOCKED", r["systemSecurityState"])


def test_e15_sin_evaluar_o_evidencia_material_da_review_incomplete(t):
    r = _resumir(_conocimiento() + _reglas(omitir=("Vu6",)))
    t.igual("E-15 una regla sin evaluar: REVIEW_INCOMPLETE", "REVIEW_INCOMPLETE",
            r["systemSecurityState"])
    r = _resumir(_conocimiento() + _reglas() + prod.desde_check(
        _check("custom-error-message-compliance", "EVIDENCE_REFERENCE_MISSING", "Vu6"),
        TAREA, ALCANCE, _cuando()))
    t.igual("E-15 la evidencia es MISSING y material", [{"evidenceRef":
            "check:custom-error-message-compliance", "result": "MISSING"}],
            r["evidence"]["material"])
    t.igual("E-15 un EVIDENCE_STATE material MISSING: REVIEW_INCOMPLETE", "REVIEW_INCOMPLETE",
            r["systemSecurityState"])


def test_e16_una_falla_da_action_required(t):
    r = _resumir(_conocimiento() + _reglas({"Vu2": seguridad.NO_CUMPLE}))
    t.igual("E-16 veinte PASS y una FAIL: ACTION_REQUIRED", "ACTION_REQUIRED",
            r["systemSecurityState"])
    t.igual("E-16 hay un bloqueo de ES0902.Vu2", ["ES0902.Vu2"],
            [b["source"] for b in r["blockingConditions"]])


def test_e17_todo_en_pass_da_ready(t):
    r = _resumir(_conocimiento() + _reglas() + prod.desde_hallazgo(
        _hallazgo("SEC-2", "HIGH"), "CREATED", TAREA, ALCANCE, cuando=_cuando()))
    t.igual("E-17 READY_FOR_SECURITY_REVIEW", "READY_FOR_SECURITY_REVIEW",
            r["systemSecurityState"])
    t.vacio("E-17 sin bloqueos", r["blockingConditions"])


def test_e18_listo_no_es_aprobado(t):
    r, md, html_ = _todo(_conocimiento() + _reglas())
    t.igual("E-18 el sistema esta listo", "READY_FOR_SECURITY_REVIEW", r["systemSecurityState"])
    t.igual("E-18 y la aprobacion es NOT_AVAILABLE", "NOT_AVAILABLE",
            r["officialApprovalStatus"])
    t.contiene("E-18 el md muestra el aviso", reporte.AVISO_OFICIAL, md)
    t.contiene("E-18 el html tambien", reporte.AVISO_OFICIAL, html_)


# -- la evaluacion y la aprobacion -----------------------------------------------

def _flujo(estado, productor="HARNESS_CHECK", evidencia=("ev-1",)):
    return prod.desde_evaluacion(evaluacion.estado_oficial(
        {"state": estado, "producer": productor, "evidence": list(evidencia)}),
        TAREA, ALCANCE, _cuando())


def _umbral_satisfecho():
    u = evaluacion.umbral([], {"authoritative": True, "evidence": ["mapeo-1"], "map": {}})
    return prod.desde_g2(u, TAREA, ALCANCE, _cuando())


def _aprobacion(estado, productor="GCBA_DGSEI", ambiente="QA", release="1.4.0"):
    return prod.desde_aprobacion(_c2(estado), TAREA, ALCANCE, productor, ambiente, release,
                                 _cuando())


def test_e19_el_umbral_de_g2_no_es_una_aprobacion(t):
    g2 = _umbral_satisfecho()
    t.igual("E-19 umbral dio satisfied", True, g2[0]["details"]["satisfied"])
    r = _resumir(_conocimiento() + _reglas() + _flujo("INTERNAL_ASSESSMENT") + g2)
    t.igual("E-19 G2_THRESHOLD_SATISFIED", "G2_THRESHOLD_SATISFIED", r["assessmentState"])
    t.igual("E-19 la aprobacion queda NOT_AVAILABLE", "NOT_AVAILABLE",
            r["officialApprovalStatus"])
    r = _resumir(_conocimiento() + _reglas() + _flujo("READY_TO_REQUEST") + g2)
    t.igual("E-19 tambien desde READY_TO_REQUEST", "G2_THRESHOLD_SATISFIED",
            r["assessmentState"])


def test_e20_un_aprobado_interno_no_es_externo(t):
    r = _resumir(_conocimiento() + _reglas() + _flujo("APPROVED", "HARNESS_CHECK")
                 + _aprobacion("PASS", productor="HARNESS_CHECK"))
    t.igual("E-20 un APPROVED interno no evidencia nada en la evaluacion",
            "ASSESSMENT_STATE_UNRESOLVED", r["assessmentState"])
    t.verdadero("E-20 ni en la aprobacion",
                r["officialApprovalStatus"] != "EXTERNAL_APPROVAL_EVIDENCED")
    # Sin pasar por la guarda de estado_oficial: el resumen vuelve a mirar quien lo declaro.
    crudo = prod.desde_evaluacion({"state": "APPROVED", "requestedState": "APPROVED",
                                   "producer": "INTERNAL_SECURITY_REVIEW", "evidence": ["x"]},
                                  TAREA, ALCANCE, _cuando())
    r = _resumir(_conocimiento() + _reglas() + crudo)
    t.igual("E-20 un APPROVED interno que esquivo la guarda tampoco",
            "ASSESSMENT_STATE_UNRESOLVED", r["assessmentState"])
    r = _resumir(_conocimiento() + _reglas() + _flujo("APPROVED", "GCBA_DGSEI")
                 + _aprobacion("PASS", productor="GCBA_DGSEI"))
    t.igual("E-20 uno de GCBA_DGSEI si, en la evaluacion", "EXTERNAL_APPROVAL_EVIDENCED",
            r["assessmentState"])
    t.igual("E-20 y con C2 PASS en QA, en la aprobacion", "EXTERNAL_APPROVAL_EVIDENCED",
            r["officialApprovalStatus"])


def test_e21_c2_cambiada_o_a_reevaluar_esta_vencida(t):
    for estado in ("SECURITY_APPROVAL_EVIDENCE_CHANGED", "SECURITY_REASSESSMENT_REQUIRED"):
        r = _resumir(_conocimiento() + _reglas() + _aprobacion(estado))
        t.igual("E-21 %s da EXTERNAL_APPROVAL_STALE" % estado, "EXTERNAL_APPROVAL_STALE",
                r["officialApprovalStatus"])


def test_e22_otro_ambiente_u_otro_release_no_evidencian(t):
    r = _resumir(_conocimiento() + _reglas() + _aprobacion("PASS", ambiente="HML"))
    t.verdadero("E-22 una aprobacion externa en HML no evidencia",
                r["officialApprovalStatus"] != "EXTERNAL_APPROVAL_EVIDENCED")
    r = _resumir(_conocimiento() + _reglas() + _aprobacion("PASS", release="1.3.0"))
    t.verdadero("E-22 ni una en QA de otro release",
                r["officialApprovalStatus"] != "EXTERNAL_APPROVAL_EVIDENCED")
    r = _resumir(_conocimiento() + _reglas() + _aprobacion("PASS"))
    t.igual("E-22 la del mismo release en QA si", "EXTERNAL_APPROVAL_EVIDENCED",
            r["officialApprovalStatus"])


def test_e23_c2_a_reevaluar_gana_sobre_el_flujo(t):
    r = _resumir(_conocimiento() + _reglas() + _flujo("READY_TO_REQUEST")
                 + _aprobacion("SECURITY_REASSESSMENT_REQUIRED"))
    t.igual("E-23 REASSESSMENT_REQUIRED aunque el flujo diga READY_TO_REQUEST",
            "REASSESSMENT_REQUIRED", r["assessmentState"])
    t.igual("E-23 con un bloqueo de assessment", ["assessment"],
            [b["source"] for b in r["blockingConditions"]])


# -- el mapa de calor ------------------------------------------------------------

def test_e24_las_21_reglas_en_el_orden_del_estandar(t):
    r = _resumir([])
    t.igual("E-24 las 21 claves, en el orden del estandar",
            [seguridad.clave(x) for x in seguridad.INVENTARIO],
            [f["ruleKey"] for f in r["normative"]["rules"]])
    en_archivo = [x["id"] for x in json.loads(MATRIZ.decode("utf-8"))["rules"]]
    t.verdadero("E-24 que no es el orden del archivo", en_archivo != list(seguridad.INVENTARIO))


def test_e25_un_control_compartido_no_le_pone_nota_a_ninguna(t):
    check = prod.desde_check(_check("technology-homologation", "PASS", "C3"), TAREA, ALCANCE,
                             _cuando())
    r = _resumir(_conocimiento() + check)
    t.igual("E-25 C3 sigue sin evaluar", "NOT_EVALUATED", _fila(r, "C3")["result"])
    t.igual("E-25 Ve1 tambien", "NOT_EVALUATED", _fila(r, "Ve1")["result"])
    r = _resumir(_conocimiento() + check + prod.desde_regla(_regla("C3", seguridad.CUMPLE),
                                                           TAREA, ALCANCE, _cuando()))
    t.igual("E-25 el RULE_EVALUATION de C3 la pone en PASS", "PASS", _fila(r, "C3")["result"])
    t.igual("E-25 y Ve1 sigue NOT_EVALUATED", "NOT_EVALUATED", _fila(r, "Ve1")["result"])


def test_e26_overridden_baja_a_unresolved_en_los_tres(t):
    r, md, html_ = _todo(_conocimiento() + _reglas({"Vu3": seguridad.RESULTADO_SIN_RESOLVER,
                                                    "Vu4": seguridad.EXCEPTUADA}))
    for rid in ("Vu3", "Vu4"):
        t.igual("E-26 %s en el resumen es UNRESOLVED" % rid, "UNRESOLVED", _fila(r, rid)["result"])
        t.contiene("E-26 %s en el md es UNRESOLVED" % rid, "| ES0902.%s | UNRESOLVED |" % rid, md)
        i = seguridad.INVENTARIO.index(rid)
        t.igual("E-26 %s en el html es UNRESOLVED" % rid, "UNRESOLVED",
                dict(_campos(html_))["normative.rules[%d].result" % i])
    t.igual("E-26 sourceResult conserva OVERRIDDEN", "OVERRIDDEN", _fila(r, "Vu4")["sourceResult"])
    t.no_contiene("E-26 y OVERRIDDEN no sale como PASS en el md", "| ES0902.Vu4 | PASS", md)


def test_e27_sin_evento_es_not_evaluated_en_los_tres(t):
    r, md, html_ = _todo(_conocimiento() + _reglas(omitir=("Vu8",)))
    t.igual("E-27 en el resumen", "NOT_EVALUATED", _fila(r, "Vu8")["result"])
    t.contiene("E-27 en el md", "| ES0902.Vu8 | NOT_EVALUATED |", md)
    celda = re.search(r'<div class="regla r-([A-Z_]+)" data-rule="Vu8"><b>Vu8</b><span '
                      r'data-field="normative\.rules\[(\d+)\]\.result">([A-Z_]+)</span>',
                      _pagina_1(html_))
    t.verdadero("E-27 la grilla de la pagina 1 tiene la celda de Vu8", celda is not None)
    if celda:
        t.igual("E-27 y dice NOT_EVALUATED", ("NOT_EVALUATED", "NOT_EVALUATED"),
                (celda.group(1), celda.group(3)))


def test_e28_el_reporte_muestra_el_conocimiento(t):
    r, md, html_ = _todo(_conocimiento(frescura.SIN_VERIFICAR) + _reglas())
    k = r["knowledge"]
    t.igual("E-28 el resumen trae lo del evento", ("ES0902", "6.2", "FRESHNESS_UNVERIFIED",
                                                   "UNVERIFIED"),
            (k["standard"], k["version"], k["freshness"], k["sourceIntegrity"]))
    for etiqueta, valor in (("Estándar", "ES0902"), ("Versión", "6.2"),
                            ("Frescura", "FRESHNESS_UNVERIFIED"),
                            ("Integridad de la fuente", "UNVERIFIED")):
        t.contiene("E-28 el md muestra %s" % etiqueta, "| %s | %s |" % (etiqueta, valor), md)
    campos = dict(_campos(_pagina_1(html_)))
    for campo in ("standard", "version", "freshness", "sourceIntegrity"):
        t.igual("E-28 la pagina 1 muestra knowledge.%s" % campo, k[campo],
                campos.get("knowledge.%s" % campo))


# -- el conocimiento -------------------------------------------------------------

def test_e29_freshness_unverified_es_unverified(t):
    evento = _conocimiento(frescura.SIN_VERIFICAR)[0]
    t.igual("E-29 sourceIntegrity UNVERIFIED", "UNVERIFIED", evento["details"]["sourceIntegrity"])
    r = _resumir([evento] + _reglas())
    t.verdadero("E-29 y el sistema no queda listo",
                r["systemSecurityState"] != "READY_FOR_SECURITY_REVIEW")


def test_e30_alerta_de_integridad_bloquea(t):
    evento = _conocimiento(frescura.ALERTA_DE_INTEGRIDAD)[0]
    t.igual("E-30 sourceIntegrity ALERT", "ALERT", evento["details"]["sourceIntegrity"])
    t.igual("E-30 SOURCE_CHANGED_SAME_VERSION tambien es ALERT", "ALERT",
            _conocimiento(frescura.CAMBIO_MISMA_VERSION)[0]["details"]["sourceIntegrity"])
    r, _, html_ = _todo([evento] + _reglas())
    t.igual("E-30 BLOCKED", "BLOCKED", r["systemSecurityState"])
    campos = _campos(_pagina_1(html_))
    t.verdadero("E-30 la pagina 1 muestra el bloqueo de knowledge",
                ("blockingConditions[0].source", "knowledge") in campos)


def test_e31_current_es_verified_y_no_bloquea(t):
    evento = _conocimiento(frescura.CURRENT)[0]
    t.igual("E-31 sourceIntegrity VERIFIED", "VERIFIED", evento["details"]["sourceIntegrity"])
    r = _resumir([evento] + _reglas({"Vu2": seguridad.NO_CUMPLE}))
    t.verdadero("E-31 no hay bloqueo de knowledge",
                not any(b["source"] == "knowledge" for b in r["blockingConditions"]))
    t.igual("E-31 el estado sale de las reglas", "ACTION_REQUIRED", r["systemSecurityState"])
    t.igual("E-31 y todo en PASS da READY", "READY_FOR_SECURITY_REVIEW",
            _resumir([evento] + _reglas())["systemSecurityState"])


# -- los hallazgos y los bloqueos ------------------------------------------------

def _hallazgo_ev(h, accion="CREATED", estado=None):
    return prod.desde_hallazgo(h, accion, TAREA, ALCANCE, estado=estado, cuando=_cuando())


def test_e32_severidad_y_confianza_no_se_mezclan(t):
    r = _resumir(_conocimiento() + _reglas()
                 + _hallazgo_ev(_hallazgo("SEC-L", "LOW", "HIGH"))
                 + _hallazgo_ev(_hallazgo("SEC-C", "CRITICAL", "LOW")))
    items = dict((i["findingId"], i) for i in r["findings"]["items"])
    t.igual("E-32 el LOW conserva su severidad y su confianza", ("LOW", "HIGH"),
            (items["SEC-L"]["severity"], items["SEC-L"]["confidence"]))
    t.igual("E-32 el CRITICAL tambien", ("CRITICAL", "LOW"),
            (items["SEC-C"]["severity"], items["SEC-C"]["confidence"]))
    mezcladas = [k for i in items.values() for k in i
                 if "sever" in k.lower() and "confid" in k.lower()]
    t.vacio("E-32 ningun campo mezcla las dos", mezcladas)
    t.igual("E-32 cada hallazgo tiene las dos por separado y nada que las combine",
            ["blocking", "confidence", "evidenceRefs", "findingId", "rule", "severity", "state",
             "title"], sorted(items["SEC-L"]))


def test_e33_un_critico_abierto_pide_accion(t):
    r, _, html_ = _todo(_conocimiento() + _reglas()
                        + _hallazgo_ev(_hallazgo("SEC-C", "CRITICAL", "LOW")))
    t.igual("E-33 ACTION_REQUIRED", "ACTION_REQUIRED", r["systemSecurityState"])
    t.igual("E-33 un bloqueo de finding", ["finding"], [b["source"] for b in r["blockingConditions"]])
    campos = dict(_campos(_pagina_1(html_)))
    t.igual("E-33 CRITICAL: 1 en la pagina 1", "1", campos["findings.totalsBySeverity.CRITICAL"])


def test_e34_los_bloqueos_son_una_lista_propia(t):
    r = _resumir(_conocimiento() + _reglas({"Vu2": seguridad.NO_CUMPLE})
                 + _hallazgo_ev(_hallazgo("SEC-H", "HIGH"))
                 + _hallazgo_ev(_hallazgo("SEC-B", "MEDIUM", bloquea=True)))
    for b in r["blockingConditions"]:
        t.verdadero("E-34 %s tiene blockerId, source, title, state y evidenceRefs" % b["blockerId"],
                    set(("blockerId", "source", "title", "state", "evidenceRefs")) <= set(b)
                    and isinstance(b["evidenceRefs"], list))
    t.igual("E-34 el HIGH sin blocking cuenta en totalsBySeverity", 1,
            r["findings"]["totalsBySeverity"]["HIGH"])
    t.verdadero("E-34 y no esta en la lista",
                not any("SEC-H" in " ".join(b["evidenceRefs"]) for b in r["blockingConditions"]))
    t.verdadero("E-34 el marcado blocking por su productor si esta",
                any("finding:SEC-B" in b["evidenceRefs"] for b in r["blockingConditions"]))


def test_e35_resuelto_y_abierto_otra_vez_es_reopened(t):
    h = _hallazgo("SEC-R", "MEDIUM")
    r = _resumir(_conocimiento() + _reglas() + _hallazgo_ev(h) + _hallazgo_ev(h, "RESOLVED")
                 + _hallazgo_ev(h, "UPDATED", "OPEN"))
    t.igual("E-35 el estado es REOPENED", "REOPENED", r["findings"]["items"][0]["state"])
    t.igual("E-35 cuenta en reopened", 1, r["findings"]["reopened"])
    t.igual("E-35 y no en open", 0, r["findings"]["open"])


def test_e36_un_resuelto_no_desaparece(t):
    h = _hallazgo("SEC-D", "HIGH")
    r = _resumir(_conocimiento() + _reglas() + _hallazgo_ev(h) + _hallazgo_ev(h, "RESOLVED"))
    items = r["findings"]["items"]
    t.igual("E-36 sigue en items con su id", ["SEC-D"], [i["findingId"] for i in items])
    t.igual("E-36 con estado RESOLVED", "RESOLVED", items[0]["state"])
    t.igual("E-36 y sus evidenceRefs", ["ev:SEC-D"], items[0]["evidenceRefs"])
    t.igual("E-36 cuenta en resolved", 1, r["findings"]["resolved"])


# -- la integridad del repositorio -----------------------------------------------

def _integridad_ev(revision):
    return prod.desde_integridad(revision, TAREA, ALCANCE, _cuando())


def test_e37_sin_linea_de_base_bloquea_solo_en_incidente(t):
    incidente = integridad.revisar(None, {}, modo=integridad.INCIDENTE)
    t.igual("E-37 integridad.revisar sin base da TRUSTED_BASELINE_UNRESOLVED",
            "TRUSTED_BASELINE_UNRESOLVED", incidente["state"])
    r, md, html_ = _todo(_conocimiento() + _reglas() + _integridad_ev(incidente))
    t.igual("E-37 el panel lo muestra asi", "TRUSTED_BASELINE_UNRESOLVED",
            r["repositoryIntegrity"]["state"])
    t.igual("E-37 en SECURITY_INCIDENT da BLOCKED", "BLOCKED", r["systemSecurityState"])
    normal = integridad.revisar(None, {}, modo=integridad.NORMAL)
    r, md, html_ = _todo(_conocimiento() + _reglas() + _integridad_ev(normal))
    t.igual("E-37 en otro modo no bloquea", "READY_FOR_SECURITY_REVIEW", r["systemSecurityState"])
    t.contiene("E-37 pero sigue visible en el md", "| Estado | TRUSTED_BASELINE_UNRESOLVED |", md)
    t.igual("E-37 y en la pagina 1", "TRUSTED_BASELINE_UNRESOLVED",
            dict(_campos(_pagina_1(html_)))["repositoryIntegrity.state"])


FRASES_DE_AUSENCIA = ("no hay código malicioso", "sin código malicioso",
                      "libre de código malicioso", "no contiene código malicioso",
                      "no hay malware", "libre de malware", "no es malicioso")


def test_e38_sin_indicadores_no_es_sin_malware(t):
    limpia = integridad.revisar(_base_confiable(), {}, modo=integridad.NORMAL)
    t.igual("E-38 integridad.revisar da NO_SUSPICIOUS_CHANGE_FOUND",
            "NO_SUSPICIOUS_CHANGE_FOUND", limpia["state"])
    r, md, html_ = _todo(_conocimiento() + _reglas() + _integridad_ev(limpia))
    t.igual("E-38 sale como NO_SUSPICIOUS_INDICATORS_DETECTED",
            "NO_SUSPICIOUS_INDICATORS_DETECTED", r["repositoryIntegrity"]["state"])
    t.contiene("E-38 el md lo dice asi", "| Estado | NO_SUSPICIOUS_INDICATORS_DETECTED |", md)
    t.contiene("E-38 el texto dice que no se detectaron indicadores",
               "No se detectaron indicadores sospechosos", md)
    for frase in FRASES_DE_AUSENCIA:
        t.no_contiene("E-38 el md no dice `%s`" % frase, frase, md.lower())
        t.no_contiene("E-38 el html no dice `%s`" % frase, frase, html_.lower())


def test_e39_malicioso_confirmado_tiene_su_rotulo(t):
    senal = {"category": "SECRET_EXFILTRATION", "evidence": ["ev-1"], "directEvidence": True,
             "indicators": ["NEW_EXTERNAL_UPLOAD"], "directEvidenceReference": "cita-1"}
    rev = integridad.revisar(_base_confiable(), {}, [senal], modo=integridad.EVALUACION)
    t.igual("E-39 integridad.revisar da MALICIOUS_BEHAVIOR_CONFIRMED_BY_EVIDENCE",
            "MALICIOUS_BEHAVIOR_CONFIRMED_BY_EVIDENCE", rev["state"])
    r, md, html_ = _todo(_conocimiento() + _reglas() + _integridad_ev(rev))
    t.igual("E-39 el panel lo muestra con su rotulo", "MALICIOUS_BEHAVIOR_CONFIRMED_BY_EVIDENCE",
            r["repositoryIntegrity"]["state"])
    t.contiene("E-39 con su texto propio en el md",
               reporte.INTEGRIDAD["MALICIOUS_BEHAVIOR_CONFIRMED_BY_EVIDENCE"], md)
    t.igual("E-39 un bloqueo de repository-integrity", ["repository-integrity"],
            [b["source"] for b in r["blockingConditions"]])
    t.igual("E-39 cuenta en confirmedMalicious", 1, r["repositoryIntegrity"]["confirmedMalicious"])
    t.igual("E-39 y se ve en la pagina 1", "1",
            dict(_campos(_pagina_1(html_)))["repositoryIntegrity.confirmedMalicious"])


# -- la evidencia ----------------------------------------------------------------

def test_e40_cuenta_el_ultimo_estado_de_cada_evidencia(t):
    def c(control, estado):
        return prod.desde_check(_check(control, estado), TAREA, ALCANCE, _cuando())
    eventos = (_conocimiento() + _reglas()
               + c("a", "EVIDENCE_REFERENCE_MISSING") + c("a", "PASS")
               + c("b", "PASS") + c("b", "SOURCE_CONFLICT")
               + c("c", "RENDERED_EVIDENCE_MISSING")
               + c("d", "SENSITIVE_DATA_TRANSPORT_TEST_UNSAFE")
               + c("e", "TRANSPORT_PROTECTION_UNRESOLVED") + c("f", "FAIL")
               + c("g", "NOT_APPLICABLE"))
    r = _resumir(eventos)
    ev = r["evidence"]
    t.igual("E-40 los cinco contadores cuentan el ultimo estado de cada ref",
            {"verified": 2, "missing": 1, "conflicting": 1, "unsafeTestsSkipped": 1,
             "unresolved": 1},
            dict((k, ev[k]) for k in ("verified", "missing", "conflicting",
                                      "unsafeTestsSkipped", "unresolved")))
    t.igual("E-40 el mismo libro da los mismos numeros", r["evidence"],
            _resumir(eventos)["evidence"])


def test_e41_una_prueba_insegura_deja_su_evidencia(t):
    eventos = prod.desde_check(_check("browser-close-session-termination",
                                      "BROWSER_SESSION_TERMINATION_TEST_UNSAFE", "Vu3"),
                               TAREA, ALCANCE, _cuando())
    t.igual("E-41 el check produce CHECK_EVALUATION y EVIDENCE_STATE",
            ["CHECK_EVALUATION", "EVIDENCE_STATE"], [e["eventType"] for e in eventos])
    t.igual("E-41 el EVIDENCE_STATE es UNSAFE_TEST_SKIPPED", "UNSAFE_TEST_SKIPPED",
            eventos[1]["result"])
    r, md, html_ = _todo(_conocimiento() + _reglas() + eventos)
    t.igual("E-41 el contador", 1, r["evidence"]["unsafeTestsSkipped"])
    t.contiene("E-41 sale en el md", "| Pruebas inseguras salteadas | 1 |", md)
    t.igual("E-41 y en el html", "1", dict(_campos(html_))["evidence.unsafeTestsSkipped"])


def test_e42_solo_la_evidencia_material_cambia_el_estado(t):
    def check(material):
        return prod.desde_check(_check("session-inactivity-timeout", "TEST_TARGET_UNAVAILABLE",
                                       "Vu4"), TAREA, ALCANCE, _cuando(), material=material)
    r = _resumir(_conocimiento() + _reglas() + check(True))
    t.igual("E-42 una material UNRESOLVED impide READY", "REVIEW_INCOMPLETE",
            r["systemSecurityState"])
    r = _resumir(_conocimiento() + _reglas() + check(False))
    t.igual("E-42 una con blocking false suma al contador", 1, r["evidence"]["unresolved"])
    t.igual("E-42 y no cambia el estado", "READY_FOR_SECURITY_REVIEW", r["systemSecurityState"])


# -- el md y el html -------------------------------------------------------------

def test_e43_la_tabla_ejecutiva_es_el_resumen(t):
    r = _resumir(_libro_variado())
    filas = _tabla_ejecutiva(reporte.generar_md(r))
    esperado = {
        "Estado de seguridad del sistema": r["systemSecurityState"],
        "Condiciones de bloqueo": str(len(r["blockingConditions"])),
        "Cobertura de la evaluación": "%.1f%%" % r["coverage"]["assessmentCoveragePct"],
        "Resolución de la evidencia": "%.1f%%" % r["coverage"]["evidenceResolutionPct"],
        "Aprobación oficial": r["officialApprovalStatus"],
        "Estado de la evaluación": r["assessmentState"],
        "Hallazgos críticos": str(r["findings"]["totalsBySeverity"]["CRITICAL"]),
        "Hallazgos altos": str(r["findings"]["totalsBySeverity"]["HIGH"]),
        "Frescura del conocimiento": r["knowledge"]["freshness"],
    }
    t.igual("E-43 cada valor de la tabla es el campo del resumen", esperado, filas)
    cambiado = json.loads(json.dumps(r))
    cambiado["systemSecurityState"] = "REVIEW_INCOMPLETE"
    cambiado["coverage"]["assessmentCoveragePct"] = 12.3
    cambiado["findings"]["totalsBySeverity"]["HIGH"] = 7
    otras = _tabla_ejecutiva(reporte.generar_md(cambiado))
    t.igual("E-43 cambiar el resumen cambia el md",
            ("REVIEW_INCOMPLETE", "12.3%", "7"),
            (otras["Estado de seguridad del sistema"], otras["Cobertura de la evaluación"],
             otras["Hallazgos altos"]))


def test_e44_cada_data_field_es_el_valor_del_resumen(t):
    ejecucion = {"events": {"counted": 3}, "time": {"wallMs": 1200, "modelMs": None,
                                                    "toolMs": 5},
                 "tokens": {"inputTokens": 10, "outputTokens": 20},
                 "cost": {"actual": None, "apiEquivalentEstimated": 0.5, "currency": "USD"}}
    eventos = (_libro_variado() + _hallazgo_ev(_hallazgo("SEC-X", "LOW", "HIGH"))
               + _aprobacion("PASS", ambiente="HML")
               + _integridad_ev(integridad.revisar(_base_confiable(), {})))
    carpeta, ruta = _libro_de(eventos)
    try:
        r = resumen.resumir(libro.bytes_de(ruta), MATRIZ, TAREA, DOMINIOS_BYTES,
                            json.dumps(ejecucion).encode("utf-8"))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    campos = _campos(reporte.generar_html(r))
    t.verdadero("E-44 la pagina declara muchos campos", len(campos) > 150)
    malos = [(ruta_, texto_, _esperado(r, ruta_)) for ruta_, texto_ in campos
             if texto_ != _esperado(r, ruta_)]
    t.vacio("E-44 cada data-field muestra el valor de su ruta", malos)
    calculan = ("seguridad", "evaluacion", "integridad", "frescura", "libro", "resumen",
                "productores", "orquestacion", "contabilidad")
    importados = _imports(PAQUETE / "reporte.py")
    t.vacio("E-44 el renderizador no importa nada que calcule estado",
            [n for n in importados if any(c in n for c in calculan)])
    t.igual("E-44 importa solo os y la guarda de archivo.py", [".:archivo", "os"],
            sorted(importados))


def test_e45_md_y_html_muestran_la_huella_y_el_id(t):
    r, md, html_ = _todo(_libro_variado())
    for nombre in ("snapshotFingerprint", "reportId"):
        t.contiene("E-45 el md muestra %s" % nombre, r[nombre], md)
        t.contiene("E-45 el html muestra %s" % nombre, r[nombre], html_)
        t.contiene("E-45 el pie de la pagina 1 lo muestra", 'data-field="%s">%s<'
                   % (nombre, r[nombre]), _pagina_1(html_).split('<div class="pie">')[1])


def test_e46_el_alcance_muestra_lo_que_trae_el_libro(t):
    r, md, html_ = _todo(_libro_variado())
    campos = dict(_campos(html_))
    for etiqueta, campo in (("Proyecto", "project"), ("Ambiente", "environment"),
                            ("Rama", "branch"), ("Commit", "commitSha"), ("Release", "releaseId")):
        t.igual("E-46 el resumen trae %s" % campo, ALCANCE[campo], r["scope"][campo])
        t.contiene("E-46 el md muestra %s" % campo, "- %s: %s\n" % (etiqueta, ALCANCE[campo]), md)
        t.igual("E-46 el html muestra %s" % campo, ALCANCE[campo], campos["scope." + campo])


def test_e47_un_alcance_ausente_dice_desconocido(t):
    alcance = {"project": "Sistema de prueba", "environment": None, "branch": ""}
    eventos = prod.desde_regla(_regla("O1", seguridad.CUMPLE), TAREA, alcance, _cuando())
    r, md, html_ = _todo(eventos)
    campos = _campos(html_)
    for etiqueta, campo in (("Aplicación", "application"), ("Ambiente", "environment"),
                            ("Rama", "branch"), ("Commit", "commitSha"), ("Build", "buildId"),
                            ("Release", "releaseId"), ("Digest del artefacto", "artifactDigest")):
        t.contiene("E-47 el md dice desconocido en %s" % campo,
                   "- %s: desconocido\n" % etiqueta, md)
        textos = [x for c, x in campos if c == "scope." + campo]
        t.verdadero("E-47 el html muestra scope.%s" % campo, bool(textos))
        t.verdadero("E-47 y dice desconocido", all(x == "desconocido" for x in textos))
    t.vacio("E-47 ningun valor vacio en el html", [c for c, x in campos if not x.strip()])
    t.verdadero("E-47 ninguna linea de alcance vacia en el md",
                not re.search(r"^- [^:\n]+: *$", md, re.M))


# -- el Bloque 4 -----------------------------------------------------------------

def _con_contabilidad(carpeta):
    dir_cont = os.path.join(carpeta, ".claude", "runtime", "accounting", TAREA)
    os.makedirs(dir_cont)
    doc = {"taskId": TAREA, "events": {"counted": 4, "duplicates": 1},
           "time": {"wallMs": 65000, "modelMs": 30000, "toolMs": None},
           "tokens": {"inputTokens": 1234, "outputTokens": 567},
           "cost": {"actual": 0.4321, "apiEquivalentEstimated": 1.5, "currency": "USD"}}
    with io.open(os.path.join(dir_cont, "summary.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(doc))
    with io.open(os.path.join(dir_cont, "ledger.jsonl"), "w", encoding="utf-8") as f:
        f.write('{"eventId": "e1"}\n')
    return dir_cont, doc


def test_e48_la_tarjeta_de_ejecucion_copia_al_bloque_4(t):
    carpeta, _ = _libro_de(_libro_variado())
    try:
        _, doc = _con_contabilidad(carpeta)
        r = resumen.generar(carpeta, TAREA)
        t.igual("E-48 block4ExecutionRef", "task:%s" % TAREA, r["block4ExecutionRef"])
        html_ = reporte.generar_html(r)
        md = reporte.generar_md(r)
        campos = dict(_campos(html_))
        t.contiene("E-48 la tarjeta aparece", 'data-card="block4Execution"', html_)
        for ruta in ("events.counted", "time.wallMs", "tokens.inputTokens", "tokens.outputTokens",
                     "cost.actual", "cost.apiEquivalentEstimated", "cost.currency"):
            grupo, campo = ruta.split(".")
            t.igual("E-48 %s tal cual" % ruta, str(doc[grupo][campo]),
                    campos["block4Execution." + ruta])
        t.contiene("E-48 el md tambien la muestra", "| Costo real | 0.4321 |", md)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    for ruta in _fuentes_py():
        for nombre in _imports(ruta):
            t.verdadero("E-48 %s no importa contabilidad.agregacion ni .costos (%s)"
                        % (ruta.name, nombre),
                        "agregacion" not in nombre and "costos" not in nombre
                        and not nombre.startswith("contabilidad"))
    carpeta, _ = _libro_de(_libro_variado())
    try:
        r = resumen.generar(carpeta, TAREA)
        t.igual("E-48 sin summary.json del Bloque 4, block4ExecutionRef es null", None,
                r["block4ExecutionRef"])
        t.no_contiene("E-48 y la tarjeta no aparece", "block4Execution",
                      reporte.generar_html(r))
        t.no_contiene("E-48 ni la seccion del md", "## Ejecución", reporte.generar_md(r))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def _foto(carpeta):
    fotos = {}
    for raiz, _, archivos in os.walk(carpeta):
        for a in archivos:
            ruta = os.path.join(raiz, a)
            with io.open(ruta, "rb") as f:
                fotos[os.path.relpath(ruta, carpeta)] = f.read()
    return fotos


def test_e49_el_subcomando_no_toca_la_contabilidad(t):
    carpeta = _proyecto_con_fuentes()
    try:
        dir_cont, _ = _con_contabilidad(carpeta)
        base = os.path.dirname(dir_cont)
        antes = _foto(base)
        codigo, _, error = _correr_cli(["seguridad", TAREA, "--conocimiento", "--resumen",
                                        "--reporte", "--proyecto", carpeta])
        t.igual("E-49 el subcomando sale con 0", 0, codigo)
        t.igual("E-49 los bytes de accounting/ quedan iguales", antes, _foto(base))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def test_e50_una_clave_de_api_no_llega_al_libro(t):
    carpeta = _tmp()
    try:
        ruta = libro.ruta_de(carpeta, TAREA)
        anthropic_ = "sk-ant-api03-Zq8Lm4Np2Rs6Tu0Vw9Xy1Za3Bc5De7FgHi"
        aws = "AKIAZ7Q2M4N6P8R0T2V4"
        evento = prod.desde_hallazgo(_hallazgo("SEC-K", "HIGH", titulo="clave %s" % anthropic_),
                                     "CREATED", TAREA, ALCANCE, cuando=_cuando())[0]
        evento["details"] = dict(evento["details"], nota="aws %s" % aws,
                                 lista=["x", anthropic_])
        libro.agregar(ruta, evento)
        crudo = libro.bytes_de(ruta).decode("utf-8")
        t.no_contiene("E-50 sk-ant no llega al libro", anthropic_, crudo)
        t.no_contiene("E-50 ni su cuerpo", "Zq8Lm4Np2Rs6", crudo)
        t.no_contiene("E-50 AKIA no llega al libro", aws, crudo)
        t.no_contiene("E-50 ni la muestra que deja el catalogo", aws[:12], crudo)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


# -- la pagina 1 -----------------------------------------------------------------

def test_e51_las_cuatro_tarjetas_primarias_siempre(t):
    for nombre, eventos in (("un libro vacio", []), ("un libro con eventos", _libro_variado())):
        pagina = _pagina_1(reporte.generar_html(_resumir(eventos)))
        for tarjeta in ("systemSecurityState", "blockingConditions", "coverage",
                        "officialApprovalStatus"):
            t.contiene("E-51 con %s la pagina 1 tiene %s" % (nombre, tarjeta),
                       'class="tarjeta primaria" data-card="%s"' % tarjeta, pagina)


def test_e52_hasta_cinco_bloqueos_y_mas(t):
    fallan = dict((rid, seguridad.NO_CUMPLE) for rid in ("O1", "O2", "C1", "C2", "C3", "Vu1",
                                                         "Vu2"))
    r = _resumir(_conocimiento() + _reglas(fallan))
    pagina = _pagina_1(reporte.generar_html(r))
    t.igual("E-52 hay siete bloqueos", 7, len(r["blockingConditions"]))
    t.igual("E-52 la pagina 1 muestra cinco", 5, pagina.count('class="bloqueo"'))
    t.contiene("E-52 y un +2 más", "+2 más", pagina)
    r = _resumir(_conocimiento() + _reglas(dict(list(fallan.items())[:3])))
    pagina = _pagina_1(reporte.generar_html(r))
    t.igual("E-52 con tres, los tres", 3, pagina.count('class="bloqueo"'))
    t.no_contiene("E-52 y ningun +N", " más</div>", pagina)
    pagina = _pagina_1(reporte.generar_html(_resumir(_conocimiento() + _reglas())))
    t.contiene("E-52 sin bloqueos, el panel dice que no hay", "No hay condiciones de bloqueo.",
               pagina)


def test_e53_el_aviso_solo_falta_con_aprobacion_externa(t):
    r, md, html_ = _todo(_conocimiento() + _reglas() + _aprobacion("PASS", ambiente="HML"))
    t.contiene("E-53 sin aprobacion externa, el pie lo dice", reporte.AVISO_OFICIAL,
               _pagina_1(html_).split('<div class="pie">')[1])
    t.contiene("E-53 y el md", reporte.AVISO_OFICIAL, md)
    r, md, html_ = _todo(_conocimiento() + _reglas() + _aprobacion("PASS"))
    t.igual("E-53 con la aprobacion evidenciada", "EXTERNAL_APPROVAL_EVIDENCED",
            r["officialApprovalStatus"])
    t.no_contiene("E-53 el html no lo dice", reporte.AVISO_OFICIAL, html_)
    t.no_contiene("E-53 ni el md", reporte.AVISO_OFICIAL, md)


# -- la CLI ----------------------------------------------------------------------

def test_e54_el_subcomando_deja_los_cuatro_archivos(t):
    carpeta = _proyecto_con_fuentes()
    try:
        codigo, salida, error = _correr_cli(["seguridad", "GCBA-1", "--conocimiento",
                                             "--resumen", "--reporte", "--proyecto", carpeta])
        t.igual("E-54 sale con codigo 0", 0, codigo)
        dir_seg = os.path.join(carpeta, ".claude", "runtime", "security", "GCBA-1")
        t.igual("E-54 los cuatro archivos",
                ["security-ledger.ndjson", "security-status.html", "security-status.md",
                 "security-summary.json"], sorted(os.listdir(dir_seg)) if os.path.isdir(dir_seg)
                else [])
        if os.path.isdir(dir_seg):
            r = json.loads(Path(dir_seg, "security-summary.json").read_text(encoding="utf-8"))
            t.igual("E-54 el conocimiento entro al libro", "CURRENT", r["knowledge"]["freshness"])
        codigo, _, _ = _correr_cli(["seguridad", "GCBA-1", "--conocimiento", "--proyecto",
                                    carpeta])
        t.igual("E-54 correrlo de nuevo no duplica el evento", 1,
                len(libro.leer(os.path.join(dir_seg, libro.LIBRO))))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def test_e55_una_tarea_con_ruta_se_rechaza_antes_del_disco(t):
    for tarea in ("../GCBA-1", "..", "a/b", "a\\b", "C:x", ""):
        carpeta = _proyecto_con_fuentes()
        try:
            codigo, _, error = _correr_cli(["seguridad", tarea, "--conocimiento", "--resumen",
                                            "--reporte", "--proyecto", carpeta])
            t.igual("E-55 `%s` sale con 2" % tarea, 2, codigo)
            t.verdadero("E-55 `%s` no crea nada bajo runtime" % tarea,
                        not os.path.exists(os.path.join(carpeta, ".claude", "runtime")))
            t.verdadero("E-55 `%s` no escribe afuera" % tarea,
                        sorted(os.listdir(carpeta)) == [".claude"]
                        and sorted(os.listdir(os.path.dirname(carpeta))).count("GCBA-1") == 0)
        finally:
            shutil.rmtree(carpeta, ignore_errors=True)
        try:
            libro.carpeta_de(_tmp(), tarea)
            t.verdadero("E-55 libro.carpeta_de rechaza `%s`" % tarea, False)
        except libro.TareaInvalida:
            t.verdadero("E-55 libro.carpeta_de rechaza `%s`" % tarea, True)


# -- lo que sostiene a los escenarios ---------------------------------------------

def test_los_dominios_agrupan_las_21_reglas_una_vez(t):
    t.vacio("cada regla en un solo dominio", resumen.controlar_dominios(DOMINIOS))
    t.igual("son ocho dominios", 8, len(DOMINIOS["domains"]))
    roto = json.loads(json.dumps(DOMINIOS))
    roto["domains"][0]["rules"].append("Vu8")
    t.verdadero("una regla en dos dominios se detecta", bool(resumen.controlar_dominios(roto)))


def test_los_productores_exigen_la_forma_de_su_entrada(t):
    casos = (
        ("desde_regla sin ruleKey", lambda: prod.desde_regla({"rule": "O1", "result": "COMPLIANT"},
                                                             TAREA, ALCANCE)),
        ("desde_regla con un resultado inventado",
         lambda: prod.desde_regla(dict(_regla("O1", "PASS")), TAREA, ALCANCE)),
        ("desde_aprobacion de otro control",
         lambda: prod.desde_aprobacion(dict(_c2("PASS"), control="otro"), TAREA, ALCANCE)),
        ("desde_evaluacion sin la forma de estado_oficial",
         lambda: prod.desde_evaluacion({"state": "APPROVED"}, TAREA, ALCANCE)),
        ("desde_integridad sin capability",
         lambda: prod.desde_integridad({"state": "NO_SUSPICIOUS_CHANGE_FOUND"}, TAREA, ALCANCE)),
        ("un alcance sin project",
         lambda: prod.desde_regla(_regla("O1", "COMPLIANT"), TAREA, {"environment": "QA"})),
    )
    for nombre, llamada in casos:
        try:
            llamada()
            t.verdadero("%s se rechaza" % nombre, False)
        except prod.ProductorInvalido:
            t.verdadero("%s se rechaza" % nombre, True)
    real = seguridad.resultado("G1")
    eventos = prod.desde_regla(real, TAREA, ALCANCE, _cuando())
    t.igual("la salida real de seguridad.resultado entra", real["result"], eventos[0]["result"])
    t.vacio("y valida", libro.validar(eventos[0]))


# -- segunda pasada del refutador ------------------------------------------------

VARIANTES_DEL_LIBRO = ("SECURITY-LEDGER.NDJSON", "security-ledger.ndjson.",
                       "security-ledger.ndjson ", "Security-Ledger.ndjson. .",
                       "security-ledger.ndjson:flujo")


def test_e01_ninguna_grafia_del_libro_esquiva_la_guarda(t):
    carpeta = _tmp()
    try:
        ruta = libro.ruta_de(carpeta, TAREA)
        libro.agregar(ruta, prod.desde_regla(_regla("O1", seguridad.CUMPLE), TAREA, ALCANCE,
                                             _cuando())[0])
        antes = libro.bytes_de(ruta)
        r = _resumir([])
        escritores = (("libro.escribir_atomico", lambda d: libro.escribir_atomico(d, "{}")),
                      ("reporte._escribir", lambda d: reporte._escribir(d, "x")),
                      ("resumen.escribir", lambda d: resumen.escribir(r, d)))
        for variante in VARIANTES_DEL_LIBRO:
            destino = os.path.join(os.path.dirname(ruta), variante)
            for nombre, escribir in escritores:
                try:
                    escribir(destino)
                    t.verdadero("E-01 %s se niega a `%s`" % (nombre, variante), False)
                except ValueError:
                    t.verdadero("E-01 %s se niega a `%s`" % (nombre, variante), True)
        # Una ruta que no se parece y ES el libro: un hardlink.
        enlace = os.path.join(os.path.dirname(ruta), "otro-nombre.json")
        try:
            os.link(ruta, enlace)
            hay_enlace = True
        except (OSError, AttributeError):
            hay_enlace = False
        if hay_enlace:
            for nombre, escribir in escritores:
                try:
                    escribir(enlace)
                    t.verdadero("E-01 %s se niega a un hardlink del libro" % nombre, False)
                except ValueError:
                    t.verdadero("E-01 %s se niega a un hardlink del libro" % nombre, True)
        t.igual("E-01 el libro sigue identico despues de todos los intentos", antes,
                libro.bytes_de(ruta))
        t.verdadero("E-01 y un nombre legitimo si se escribe",
                    bool(libro.escribir_atomico(os.path.join(os.path.dirname(ruta),
                                                             "otro.json"), "{}")))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


CONTRASENAS_CITADAS = (
    ('password = "Hunter8Qw9Zp"', "Hunter8Qw9Zp"),
    ("PASSWORD='Hunter9Qw9Zp'", "Hunter9Qw9Zp"),
    ('{"password": "Hunter4Qw9Zp"}', "Hunter4Qw9Zp"),
    ("password='Hunter7Qw9Zp'", "Hunter7Qw9Zp"),
    ("db_password: HunterAQw9Zp", "HunterAQw9Zp"),
    ('{\\"password\\": \\"HunterBQw9Zp\\"}', "HunterBQw9Zp"),
    ('JSESSIONID="QuotedSess998877"', "QuotedSess998877"),
    ("x_sessionid=Pegada55443322", "Pegada55443322"),
    ("ASP.NET_SessionId=AspNet9988776655", "AspNet9988776655"),
    ("Authorization: Bearer zQ7k2", "zQ7k2"),
    ("clave sk-ant-a1", "sk-ant-a1"),
)


def test_e03_citada_o_espaciada_tampoco_llega(t):
    pgp = ("-----BEGIN PGP PRIVATE KEY BLOCK-----\n\nlQOYBGZqPgpCuerpoSecreto77aa\n"
           "=Xy9Q\n-----END PGP PRIVATE KEY BLOCK-----")
    for texto, secreto in CONTRASENAS_CITADAS + ((pgp, "lQOYBGZqPgpCuerpoSecreto77aa"),):
        carpeta = _tmp()
        try:
            ruta = libro.ruta_de(carpeta, TAREA)
            h = _hallazgo("SEC-Q", "HIGH")
            h["evidence"] = ["ref %s" % texto]
            evento = prod.desde_hallazgo(h, "CREATED", TAREA, ALCANCE, cuando=_cuando())[0]
            evento["details"] = dict(evento["details"], nota="en la nota %s fin" % texto)
            libro.agregar(ruta, evento)
            crudo = libro.bytes_de(ruta).decode("utf-8")
            t.no_contiene("E-03 `%s` no llega al libro" % texto[:40], secreto, crudo)
        finally:
            shutil.rmtree(carpeta, ignore_errors=True)


def test_e50_los_hallazgos_no_repiten_la_muestra(t):
    aws = "AKIAZ7Q2M4N6P8R0T2V4"
    carpeta = _tmp()
    try:
        ruta = libro.ruta_de(carpeta, TAREA)
        evento = prod.desde_hallazgo(_hallazgo("SEC-M", "HIGH", titulo="aws %s" % aws),
                                     "CREATED", TAREA, ALCANCE, cuando=_cuando())[0]
        _, hallazgos = libro.agregar(ruta, evento)
        texto = "\n".join(hallazgos)
        t.verdadero("E-50 agregar informa que redacto algo", bool(hallazgos))
        t.no_contiene("E-50 los hallazgos no traen la muestra de doce caracteres", aws[:12], texto)
        t.no_contiene("E-50 ni el valor", aws, texto)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
    carpeta = _tmp()
    try:
        os.makedirs(os.path.join(carpeta, ".claude"))
        doc = _fuentes()
        doc["sources"]["ES0902"]["evidence"] = ["nota con %s" % aws]
        with io.open(frescura.ruta_por_defecto(carpeta), "w", encoding="utf-8") as f:
            f.write(json.dumps(doc))
        _, salida, error = _correr_cli(["seguridad", TAREA, "--conocimiento",
                                        "--proyecto", carpeta])
        t.no_contiene("E-50 la CLI no imprime la muestra", aws[:12], salida + error)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def test_e05b_la_huella_cubre_las_cuatro_entradas(t):
    carpeta, ruta = _libro_de(_libro_variado())
    try:
        datos = libro.bytes_de(ruta)
        base = resumen.resumir(datos, MATRIZ, TAREA, DOMINIOS_BYTES, b"")
        bloque4 = json.dumps({"events": {"counted": 4}, "cost": {"actual": 1.0}}).encode()
        con_b4 = resumen.resumir(datos, MATRIZ, TAREA, DOMINIOS_BYTES, bloque4)
        t.verdadero("E-05b crear el summary.json del Bloque 4 cambia la huella",
                    con_b4["snapshotFingerprint"] != base["snapshotFingerprint"])
        t.verdadero("E-05b crearlo cambia el reportId", con_b4["reportId"] != base["reportId"])
        otro_b4 = resumen.resumir(datos, MATRIZ, TAREA, DOMINIOS_BYTES,
                                  bloque4.replace(b"1.0", b"2.0"))
        t.verdadero("E-05b cambiar un byte del Bloque 4 cambia la huella",
                    otro_b4["snapshotFingerprint"] != con_b4["snapshotFingerprint"])
        t.verdadero("E-05b y el reportId", otro_b4["reportId"] != con_b4["reportId"])
        dominios = DOMINIOS_BYTES.replace("Gobierno".encode(), "Gobiernx".encode())
        otro_dom = resumen.resumir(datos, MATRIZ, TAREA, dominios, b"")
        t.verdadero("E-05b cambiar un byte de los dominios cambia la huella",
                    otro_dom["snapshotFingerprint"] != base["snapshotFingerprint"])
        t.verdadero("E-05b cambiarlo cambia el reportId", otro_dom["reportId"] != base["reportId"])
        _con_contabilidad(carpeta)
        con = resumen.generar(carpeta, TAREA)
        os.remove(os.path.join(carpeta, ".claude", "runtime", "accounting", TAREA,
                               "summary.json"))
        sin = resumen.generar(carpeta, TAREA)
        t.verdadero("E-05b borrar el summary.json del Bloque 4 cambia la huella",
                    con["snapshotFingerprint"] != sin["snapshotFingerprint"])
        t.verdadero("E-05b borrarlo cambia el reportId", con["reportId"] != sin["reportId"])
        t.igual("E-05b sin Bloque 4 la cuarta entrada va ausente",
                resumen.resumir(datos, MATRIZ, TAREA, DOMINIOS_BYTES, None)["snapshotFingerprint"],
                sin["snapshotFingerprint"])
        # Cada entrada va con su nombre y su largo: correr un byte de una a otra cambia la huella.
        t.verdadero("E-05b la frontera entre entradas cuenta",
                    resumen.huella_de_la_foto(datos + MATRIZ[:1], MATRIZ[1:], DOMINIOS_BYTES, b"")
                    != resumen.huella_de_la_foto(datos, MATRIZ, DOMINIOS_BYTES, b""))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def test_e22b_las_cinco_filas_en_orden(t):
    sin_release = dict(ALCANCE, releaseId=None)
    casos = (
        ("una externa en HML", ALCANCE, "PASS", "GCBA_DGSEI", "HML", "1.4.0", "UNRESOLVED"),
        ("una interna en QA", ALCANCE, "PASS", "HARNESS_CHECK", "QA", "1.4.0", "UNRESOLVED"),
        ("una interna en QA de otro release", ALCANCE, "PASS", "HARNESS_CHECK", "QA", "1.3.0",
         "UNRESOLVED"),
        ("una externa en QA de otro release", ALCANCE, "PASS", "GCBA_DGSEI", "QA", "1.3.0",
         "EXTERNAL_APPROVAL_STALE"),
        ("un C2 cambiado con productor interno", ALCANCE, "SECURITY_APPROVAL_EVIDENCE_CHANGED",
         "HARNESS_CHECK", "QA", "1.4.0", "EXTERNAL_APPROVAL_STALE"),
        ("una externa en QA sin releaseId en el alcance", sin_release, "PASS", "GCBA_DGSEI", "QA",
         "1.4.0", "EXTERNAL_APPROVAL_EVIDENCED"),
        ("una externa en QA sin release en la aprobacion", ALCANCE, "PASS", "GCBA_DGSEI", "QA",
         None, "EXTERNAL_APPROVAL_EVIDENCED"),
        ("un C2 en FAIL de una externa en QA", ALCANCE, "FAIL", "GCBA_DGSEI", "QA", "1.4.0",
         "UNRESOLVED"),
    )
    for nombre, alcance, estado, productor, ambiente, release, esperado in casos:
        eventos = [dict(e, scope=dict(e["scope"], releaseId=alcance.get("releaseId")))
                   for e in _conocimiento() + _reglas()]
        eventos += prod.desde_aprobacion(_c2(estado), TAREA, alcance, productor, ambiente,
                                         release, _cuando())
        r = _resumir(eventos)
        t.igual("E-22b %s da %s" % (nombre, esperado), esperado, r["officialApprovalStatus"])


# -- tercera pasada del refutador ------------------------------------------------

CONTRASENAS_POR_PALABRA = (
    ("'password' => 'Pw1Php77xx',", "Pw1Php77xx"),
    ("<password>Pw2Xml77xx</password>", "Pw2Xml77xx"),
    ("--password Pw3Cli77xx", "Pw3Cli77xx"),
    ("set password Pw4Set77xx", "Pw4Set77xx"),
    ("pass=Pw5Pas77xx", "Pw5Pas77xx"),
    ("clave: Pw6Cla77xx", "Pw6Cla77xx"),
    ("PASSWD := Pw7Asg77xx", "Pw7Asg77xx"),
    ("Contraseña -> Pw8Esp77xx", "Pw8Esp77xx"),
    ("passphrase='Pw9Frs77xx'", "Pw9Frs77xx"),
    ("db_pwd=PwAPwd77xx", "PwAPwd77xx"),
)


def _redactado(texto):
    limpio, _ = libro.redactar({"details": {"nota": texto}, "evidenceRefs": [texto]})
    return json.dumps(limpio, ensure_ascii=False)


def test_e03b_la_palabra_anuncia_la_contrasena(t):
    for texto, secreto in CONTRASENAS_POR_PALABRA:
        t.no_contiene("E-03b `%s` no llega al libro" % texto, secreto, _redactado(texto))
    # La frontera: `password_hash` no es la palabra, y `bypass` tampoco.
    for texto, valor in (("password_hash=h4sh", "h4sh"), ("bypass=b1en", "b1en"),
                         ("passwords: lista", "lista")):
        t.contiene("E-03b `%s` no se toma como contrasena" % texto, valor, _redactado(texto))
    # Y un libro de verdad: las formas nuevas, por agregar, no llegan al disco.
    carpeta = _tmp()
    try:
        ruta = libro.ruta_de(carpeta, TAREA)
        h = _hallazgo("SEC-P", "HIGH")
        h["evidence"] = [texto for texto, _ in CONTRASENAS_POR_PALABRA]
        libro.agregar(ruta, prod.desde_hallazgo(h, "CREATED", TAREA, ALCANCE,
                                                cuando=_cuando())[0])
        crudo = libro.bytes_de(ruta).decode("utf-8")
        for texto, secreto in CONTRASENAS_POR_PALABRA:
            t.no_contiene("E-03b `%s` no llega al disco" % texto, secreto, crudo)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def test_e01_un_tmp_enlazado_al_libro_no_se_trunca(t):
    carpeta = _tmp()
    otra = _tmp()
    try:
        ruta = libro.ruta_de(carpeta, TAREA)
        libro.agregar(ruta, prod.desde_regla(_regla("O1", seguridad.CUMPLE), TAREA, ALCANCE,
                                             _cuando())[0])
        antes = libro.bytes_de(ruta)
        # El libro vive en una carpeta y el destino en otra: el `.tmp` es un hardlink al libro.
        destino = os.path.join(otra, "security-summary.json")
        try:
            os.link(ruta, destino + ".tmp")
            hay_enlace = True
        except (OSError, AttributeError):
            hay_enlace = False
        t.verdadero("E-01 el sistema de archivos permite el hardlink", hay_enlace)
        if hay_enlace:
            for nombre, escribir in (
                    ("libro.escribir_atomico", lambda: libro.escribir_atomico(destino, "{}")),
                    ("reporte._escribir", lambda: reporte._escribir(destino, "x")),
                    ("resumen.escribir", lambda: resumen.escribir(_resumir([]), destino))):
                try:
                    escribir()
                except ValueError:
                    pass
                t.igual("E-01 %s no trunca el libro por un .tmp enlazado" % nombre, antes,
                        libro.bytes_de(ruta))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
        shutil.rmtree(otra, ignore_errors=True)


def test_e05b_ausente_y_vacio_no_comparten_huella(t):
    carpeta, ruta = _libro_de(_libro_variado())
    try:
        datos = libro.bytes_de(ruta)
        ausente = resumen.resumir(datos, MATRIZ, TAREA, DOMINIOS_BYTES, None)
        vacio = resumen.resumir(datos, MATRIZ, TAREA, DOMINIOS_BYTES, b"")
        t.verdadero("E-05b un summary.json de 0 bytes y uno ausente dan huellas distintas",
                    ausente["snapshotFingerprint"] != vacio["snapshotFingerprint"])
        t.verdadero("E-05b y reportId distintos", ausente["reportId"] != vacio["reportId"])
        t.igual("E-05b el vacio deja block4ExecutionRef en null", None,
                vacio["block4ExecutionRef"])
        dir_cont = os.path.join(carpeta, ".claude", "runtime", "accounting", TAREA)
        os.makedirs(dir_cont)
        sin = resumen.generar(carpeta, TAREA)
        io.open(os.path.join(dir_cont, "summary.json"), "wb").close()
        con_vacio = resumen.generar(carpeta, TAREA)
        t.verdadero("E-05b desde el proyecto: crear un summary.json vacio cambia la huella",
                    sin["snapshotFingerprint"] != con_vacio["snapshotFingerprint"])
        t.igual("E-05b el ausente es el de resumir con None", ausente["snapshotFingerprint"],
                sin["snapshotFingerprint"])
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
