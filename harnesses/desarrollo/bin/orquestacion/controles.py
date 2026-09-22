"""El registro de controles normativos: que policy, que check y que review existen.

Es la unica respuesta a "esto esta instalado". Sin el, `instalado` es una afirmacion de quien
la dice, y `matriz.controles_no_instalados` no tiene contra que comparar.

La forma es la misma que la del registro de agentes, y la razon tambien: **el registro
declara y el disco diagnostica**. Un archivo que aparece solo no da de alta un control, y un
control declarado sin archivo es un hueco que se ve.

🔴 **Estos checks no son los checks del hook.** Los de `comun/checks/` corren en `PreToolUse`,
devuelven tres salidas, salen 0 siempre y pagan latencia en cada llamada a una herramienta. Un
check normativo se evalua contra evidencia y devuelve su estado con el motivo. Comparten la
palabra y nada mas, y por eso no comparten registro: meterlos en el mismo cajon seria
heredarles un contrato que no pueden cumplir.

🔴 **Esto no dice si un control se cumple.** Dice si existe.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402
from . import roster                             # noqa: E402

ARCHIVO = "control-registry.json"
SCHEMA = "control-registry.schema.json"

TIPOS = ("POLICY", "CHECK", "REVIEW")
ESTADOS = ("INSTALLED", "DECLARED_NOT_INSTALLED", "DEPRECATED")

INSTALADO = "INSTALLED"
SIN_ARCHIVO = "CONTROL_FILE_MISSING"
NO_DECLARADO = "UNDECLARED_CONTROL"
DUPLICADO = "DUPLICATE_CONTROL_ID"
TIPO_INVALIDO = "CONTROL_TYPE_INVALID"
SIN_FUENTE = "CONTROL_NORMATIVE_SOURCE_MISSING"

# Como se llama el hueco de cada tipo. Son tres nombres y no uno porque el que lee un plan
# tiene que saber si le falta una restriccion, una comprobacion o un criterio.
HUECO = {"POLICY": "DECLARED_POLICY_NOT_INSTALLED",
         "CHECK": "DECLARED_CHECK_NOT_INSTALLED",
         "REVIEW": "DECLARED_REVIEW_NOT_INSTALLED"}


class RegistroInvalido(Exception):
    """El registro de controles no se lee a medias."""


# -- carga ---------------------------------------------------------------------

def cargar(desde=None):
    """El registro como dato. Vacio si no esta: un harness sin controles es valido."""
    ruta = roster.ruta_de_regla(ARCHIVO, desde or __file__)
    if ruta is None:
        return {"version": "0.0.0", "registryType": "control-registry",
                "controlTypes": list(TIPOS), "controls": []}
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        raise RegistroInvalido("%s no se pudo leer: %s" % (ruta, e))


def validar_schema(doc, desde=None):
    from . import tools
    armador = tools._armador()
    if armador is None:
        raise RegistroInvalido("no esta contexto-armar.py, de donde sale el validador.")
    ruta = rutas.localizar(("schemas", SCHEMA), desde or __file__)
    if ruta is None:
        raise RegistroInvalido("no esta %s" % SCHEMA)
    with io.open(ruta, encoding="utf-8") as f:
        esquema = json.load(f)
    armador.controlar_soporte(esquema)
    return armador.validar(doc, esquema)


def _raices(desde=None):
    return roster._dir_del_harness(desde or __file__)


def _ruta_de(relativa, desde=None):
    if not relativa:
        return None
    partes = relativa.split("/")
    candidatas = [os.path.join(r, *partes) for r in _raices(desde)]
    for c in candidatas:
        if os.path.exists(c):
            return c
    return candidatas[0] if candidatas else None


# -- validacion ----------------------------------------------------------------

def validar(doc=None, desde=None):
    """{id: estado} de cada control declarado, mas los errores de schema."""
    documento = doc if doc is not None else cargar(desde)
    errores = list(validar_schema(documento, desde))
    estados = {}
    vistos = set()
    for c in documento.get("controls", []):
        cid = c.get("id", "")
        if cid in vistos:
            estados[cid] = DUPLICADO
            continue
        vistos.add(cid)
        if c.get("type") not in TIPOS:
            estados[cid] = TIPO_INVALIDO
            continue
        if not fuentes_de(c):
            estados[cid] = SIN_FUENTE
            continue
        if c.get("status") != INSTALADO:
            estados[cid] = HUECO.get(c.get("type"), NO_DECLARADO)
            continue
        ruta = _ruta_de(c.get("file", ""), desde)
        estados[cid] = INSTALADO if (ruta and os.path.isfile(ruta)) else SIN_ARCHIVO
    return {"schemaErrors": errores, "controls": estados}


def instalados(doc=None, desde=None):
    """Los ids que existen de verdad, por tipo. Lo que la matriz consulta."""
    documento = doc if doc is not None else cargar(desde)
    informe = validar(documento, desde)
    salida = {"POLICY": [], "CHECK": [], "REVIEW": []}
    for c in documento.get("controls", []):
        if informe["controls"].get(c.get("id")) == INSTALADO:
            salida.setdefault(c.get("type"), []).append(c.get("id"))
    return {k: sorted(v) for k, v in salida.items()}


def fuentes_de(control):
    """Las fuentes normativas de un control, siempre como lista.

    🔴 La lista entera o la singular, nunca las dos mezcladas. `normativeSources` gana cuando
    esta; `source` sigue valiendo solo, y vale como una fuente. Un control que no declara
    ninguna de las dos no dice de donde sale, y un control sin origen normativo es una
    comprobacion que nadie pidio.

    Un control que dos estandares citan se declara UNA vez con las dos fuentes. Compartir la
    ejecucion no es compartir el resultado: cada fuente conserva el suyo.
    """
    c = control if isinstance(control, dict) else {}
    lista = c.get("normativeSources")
    if isinstance(lista, list) and lista:
        return [dict(f) for f in lista if isinstance(f, dict)]
    singular = c.get("source")
    if isinstance(singular, dict) and singular:
        return [dict(singular)]
    return []


def control(control_id, doc=None, desde=None):
    documento = doc if doc is not None else cargar(desde)
    for c in documento.get("controls", []):
        if c.get("id") == control_id:
            return c
    return None


def de_la_regla(rule_id, doc=None, desde=None):
    """Los controles que salen de una regla, en el orden en que se declararon.

    Acepta el id local -`D2`- y la clave compuesta -`ES0902.C1`-. Con el id local mira `rule`,
    que es el campo que existia; con la clave compuesta mira las fuentes normativas, que es
    donde vive el segundo estandar.
    """
    documento = doc if doc is not None else cargar(desde)
    if "." in (rule_id or ""):
        estandar, local = rule_id.split(".", 1)
        return [c for c in documento.get("controls", [])
                if any(f.get("standard") == estandar and f.get("rule") == local
                       for f in fuentes_de(c))]
    return [c for c in documento.get("controls", []) if c.get("rule") == rule_id]


def estandares_de(control_id, doc=None, desde=None):
    """Los estandares que citan este control. Mas de uno es un control compartido."""
    c = control(control_id, doc, desde)
    return sorted({f.get("standard") for f in fuentes_de(c) if f.get("standard")})


def descubrir_no_declarados(doc=None, desde=None):
    """Archivos de control que el registro no declara. Diagnostico: no dan de alta nada."""
    documento = doc if doc is not None else cargar(desde)
    declarados = {c.get("file") for c in documento.get("controls", [])}
    salida = []
    for sub, ext in (("controles/policies", ".md"), ("controles/checks", ".py")):
        for raiz in _raices(desde):
            d = os.path.join(raiz, *sub.split("/"))
            if not os.path.isdir(d):
                continue
            for n in sorted(os.listdir(d)):
                if not n.endswith(ext) or n.startswith("__"):
                    continue
                relativa = "%s/%s" % (sub, n)
                if relativa not in declarados:
                    salida.append({"file": relativa, "state": NO_DECLARADO,
                                   "severity": "ERROR"})
    return salida


def reporte(doc=None, desde=None):
    """El estado completo, con las cuentas calculadas."""
    documento = doc if doc is not None else cargar(desde)
    informe = validar(documento, desde)
    hay = instalados(documento, desde)
    no_declarados = descubrir_no_declarados(documento, desde)
    declarados = documento.get("controls", [])
    return {
        "registryVersion": documento.get("version", ""),
        "summary": {
            "declaredControls": len(declarados),
            "installedPolicies": len(hay.get("POLICY", [])),
            "installedChecks": len(hay.get("CHECK", [])),
            "installedReviews": len(hay.get("REVIEW", [])),
            "undeclaredFiles": len(no_declarados),
        },
        "controls": informe["controls"],
        "undeclared": no_declarados,
        "schemaErrors": informe["schemaErrors"],
        "result": {
            "registryValid": not informe["schemaErrors"] and all(
                e == INSTALADO or e in HUECO.values()
                for e in informe["controls"].values()),
            "filesystemClean": not no_declarados,
        },
    }
