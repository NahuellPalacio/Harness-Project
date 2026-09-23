"""ES0902 C3: las herramientas versionadas y autorizadas, con los controles de G1.

    source: ES0902 / 6.2 / 3 / C3
    autoridad: ES0901 / 6.3 / 6.10, 7.1 G1, Anexo II

C3 no trae catalogo propio: delega en el Estandar de Desarrollo. Este modulo no homologa nada ni
compara una sola version -eso es `anexo2.py` y los checks de G1-. Hace tres cosas:

    1. resuelve la linea base: que el Estandar de Desarrollo vigente, el catalogo instalado y los
       controles que lo leen sean del mismo estandar y de la misma version
    2. ejecuta los dos checks de G1 UNA vez sobre el inventario, y anota los resultados con sus
       fuentes
    3. agrega esos resultados en una regla -G1 o C3- sin leer el resultado de la otra

🔴 **C3 no queda congelada en 6.3.** Nombra *el* Estandar de Desarrollo. El dia que se cargue otro
ES0901, el catalogo y los controles tienen que moverse con el, o C3 no pasa: un catalogo
reemplazado que sigue aprobando es la forma mas silenciosa de que la regla mienta.

🔴 **G1 no se copia en C3.** La agregacion recibe los resultados compartidos, nunca el de la otra
regla. Una sola ejecucion, dos agregaciones.

🔴 **Las semanticas de G1 no se reescriben.** Deprecada sale deprecada; mas nueva no es autorizada;
una auxiliar de toolchain no es una tecnologia homologada; la version que asigna el proveedor no
se inventa.

🔴 **Lo que no tiene forma no cuenta, y lo que falta no aprueba.** Un inventario ausente, vacio o
con una tecnologia mal formada deja la regla sin resolver: nunca `NOT_APPLICABLE`.

🔴 **C3 no es seguridad.** No mira vulnerabilidades, ni configuracion, ni aprobaciones: conforme en
C3 no mueve ninguna otra regla.
"""
import importlib.util
import io
import json
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from . import anexo2                             # noqa: E402
from . import controles as _controles            # noqa: E402
from . import linea_base                         # noqa: E402
from . import roster                             # noqa: E402
from . import seguridad                          # noqa: E402

REGLA = "C3"
CLAVE = seguridad.clave(REGLA)
TRAZA = {"standard": seguridad.ESTANDAR, "version": seguridad.VERSION_ESPERADA, "section": "3",
         "rule": REGLA}

ESTANDAR_DE_DESARROLLO = "ES0901"

POLICIES = ("approved-technology-required", "homologated-version-required")
HOMOLOGACION = "technology-homologation"
VERSION = "technology-version-compliance"
CHECKS = (HOMOLOGACION, VERSION)

# -- la linea base --------------------------------------------------------------

RESUELTA = "RESOLVED"
SIN_RESOLVER = "UNRESOLVED"
DESFASADA = "MISMATCH"

BASE_SIN_RESOLVER = "DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_UNRESOLVED"
BASE_DESFASADA = "DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_MISMATCH"
SIN_CATALOGO = "TECHNOLOGY_CATALOG_UNAVAILABLE"
SIN_CONTROL = "SHARED_TECHNOLOGY_CONTROL_UNAVAILABLE"
SIN_INVENTARIO = "TECHNOLOGY_INVENTORY_UNAVAILABLE"

ESTADOS_DE_BASE = (BASE_SIN_RESOLVER, BASE_DESFASADA, SIN_CATALOGO, SIN_CONTROL)

# El status que el catalogo tiene que declarar para servir a una version del estandar.
PREFIJO_DE_STATUS = "COMPLETE_FOR_ANNEX_II_V"

# -- la agregacion --------------------------------------------------------------

CUMPLE = seguridad.CUMPLE
CUMPLE_CON_OBSERVACIONES = "COMPLIANT_WITH_OBSERVATIONS"
NO_CUMPLE = seguridad.NO_CUMPLE
RESULTADO_SIN_RESOLVER = seguridad.RESULTADO_SIN_RESOLVER
RESULTADOS_DE_C3 = (CUMPLE, CUMPLE_CON_OBSERVACIONES, NO_CUMPLE, RESULTADO_SIN_RESOLVER)

# Los estados de G1 que dejan una tecnologia sin resolver. Son los de `anexo2`, por nombre: este
# modulo no los define.
PENDIENTES_DE_G1 = (anexo2.EVALUACION_ASI, anexo2.AUXILIAR, anexo2.FALTA_CONTEXTO,
                    anexo2.FALTA_HISTORIA, anexo2.FALTA_PROVEEDOR, anexo2.SIN_RESOLVER)


def _catalogo_crudo(desde=None):
    """El catalogo sin validar su version, o `None`. El resolvedor tiene que ver la diferencia."""
    ruta = roster.ruta_de_regla(anexo2.ARCHIVO, desde or __file__)
    if ruta is None:
        return None
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


def _id_canonico(valor):
    """El id sin como esta escrito: NFKD, solo letras y numeros -sin marcas combinadas, que se
    separan de su letra-, en mayusculas. `ÉS0901` y `ES0901́` dan lo mismo."""
    return "".join(c for c in unicodedata.normalize("NFKD", str(valor or ""))
                   if unicodedata.category(c)[0] in ("L", "N")).upper()


def _vigente(linea, motivos):
    """La version de ES0901 vigente, o `None`.

    🔴 Una fuente que no se puede leer no se descarta: podia ser la vigente. Un `sources` que no
    es una lista, una entrada que no es un diccionario, o una de ES0901 con un `status` o una
    `currency` que no se reconocen dejan la linea base sin resolver. Y un ES0901 declarado
    reemplazado no rige aunque sea el unico cargado.
    """
    fuentes = (linea or {}).get("sources")
    if not isinstance(fuentes, list) or not all(isinstance(f, dict) for f in fuentes):
        motivos.append("la linea base normativa trae fuentes que no se pueden leer")
        return None
    # 🔴 La regla del tercer pase, que cierra la clase y no un caso: toda fuente tiene un id de
    # texto no vacio, y una cuyo id canonico CONTIENE al del Estandar de Desarrollo sin ser
    # exactamente el -`ES0901 `, `ＥＳ0901`, `ES0901-6.4`- deja la linea base sin resolver. Puede
    # ser la vigente escrita de otra forma, y descartarla dejaria resolver a la que quedo.
    buscado = _id_canonico(ESTANDAR_DE_DESARROLLO)
    propias = [f for f in fuentes if f.get("id") == ESTANDAR_DE_DESARROLLO]
    if any(not isinstance(f.get("id"), str) or not _id_canonico(f["id"]) for f in fuentes) \
            or any(buscado in _id_canonico(f.get("id")) and f.get("id") != ESTANDAR_DE_DESARROLLO
                   for f in fuentes):
        motivos.append("la linea base declara un %s con el id escrito de otra forma, o una fuente "
                       "sin id" % ESTANDAR_DE_DESARROLLO)
        return None
    # 🔴 Un ES0901 declarado vigente que no esta cargado dice que rige OTRA version, y el catalogo
    # instalado no es de ella: no se aprueba contra el que si esta.
    vigente_sin_cargar = [f for f in propias if linea_base.vigencia_de(f) == linea_base.VIGENTE
                          and linea_base.estado_de(f) != linea_base.CARGADA]
    if vigente_sin_cargar:
        motivos.append("la linea base declara vigente un %s que no esta cargado (%s)"
                       % (ESTANDAR_DE_DESARROLLO,
                          ", ".join(sorted(str(f.get("version")) for f in vigente_sin_cargar))))
        return None
    torcidas = [f for f in propias
                if linea_base.estado_de(f) is None
                or (f.get("currency") is not None
                    and f.get("currency") not in linea_base.VIGENCIAS)]
    if torcidas:
        motivos.append("la linea base declara un %s con un estado o una vigencia que no se "
                       "reconocen" % ESTANDAR_DE_DESARROLLO)
        return None
    cargadas = [f for f in propias if linea_base.estado_de(f) == linea_base.CARGADA
                and linea_base.vigencia_de(f) != linea_base.REEMPLAZADA]
    if not cargadas:
        motivos.append("la linea base normativa no tiene un %s cargado" % ESTANDAR_DE_DESARROLLO)
        return None
    if len(cargadas) > 1:
        # 🔴 No se elige la mas vieja porque su catalogo existe, ni la mas nueva porque es mas
        # nueva: la vigencia la declara la linea base.
        vigentes = [f for f in cargadas if linea_base.vigencia_de(f) == linea_base.VIGENTE]
        if len(vigentes) != 1:
            motivos.append("hay %d %s cargados y %d declarados vigentes: no se sabe cual rige"
                           % (len(cargadas), ESTANDAR_DE_DESARROLLO, len(vigentes)))
            return None
        cargadas = vigentes
    version = cargadas[0].get("version")
    if not isinstance(version, str) or not version.strip():
        motivos.append("el %s cargado no declara su version" % ESTANDAR_DE_DESARROLLO)
        return None
    return version


def resolver_base(linea=None, catalogo=None, registro=None, version_de_controles=None,
                  desde=None):
    """La linea base tecnologica que C3 consume. Falla cerrado, y dice en que paso.

    Cada argumento reemplaza lo instalado; sin argumentos lee la linea base normativa, el
    catalogo del Anexo II y el registro de controles.
    """
    motivos = []
    salida = {"status": SIN_RESOLVER, "standard": ESTANDAR_DE_DESARROLLO, "version": None,
              "catalogRef": anexo2.ARCHIVO, "catalogVersion": None, "catalogSource": None,
              "policies": list(POLICIES), "checks": list(CHECKS), "states": [],
              "reasons": motivos}

    try:
        doc_linea = linea if linea is not None else linea_base.cargar(desde)
    except Exception as e:                           # noqa: BLE001 - se falla cerrado
        motivos.append("la linea base normativa no se pudo leer: %s" % e)
        doc_linea = None
    vigente = _vigente(doc_linea, motivos) if doc_linea is not None else None
    salida["version"] = vigente
    if vigente is None:
        return _base(salida, SIN_RESOLVER, BASE_SIN_RESOLVER)

    doc = catalogo if catalogo is not None else _catalogo_crudo(desde)
    if not isinstance(doc, dict) or not isinstance(doc.get("source"), dict):
        motivos.append("no esta %s, o no se puede leer" % anexo2.ARCHIVO)
        return _base(salida, SIN_RESOLVER, SIN_CATALOGO)
    fuente = doc["source"]
    salida["catalogVersion"] = doc.get("catalogVersion")
    salida["catalogSource"] = {"standard": fuente.get("standard"),
                               "version": fuente.get("version")}
    if fuente.get("standard") != ESTANDAR_DE_DESARROLLO or fuente.get("version") != vigente:
        motivos.append("el catalogo es de %s %s y el Estandar de Desarrollo vigente es %s %s"
                       % (fuente.get("standard"), fuente.get("version"),
                          ESTANDAR_DE_DESARROLLO, vigente))
        return _base(salida, DESFASADA, BASE_DESFASADA)
    esperado = PREFIJO_DE_STATUS + vigente.replace(".", "_")
    if doc.get("status") != esperado:
        motivos.append("el catalogo declara `%s` y para %s tiene que declarar `%s`"
                       % (doc.get("status"), vigente, esperado))
        return _base(salida, DESFASADA, BASE_DESFASADA)
    de_los_controles = (version_de_controles if version_de_controles is not None
                        else anexo2.VERSION_ESPERADA)
    if de_los_controles != vigente:
        motivos.append("los controles de G1 estan escritos para el Anexo II de %s y el vigente "
                       "es %s: catalogo y comparador se mueven juntos" % (de_los_controles,
                                                                        vigente))
        return _base(salida, DESFASADA, BASE_DESFASADA)

    try:
        doc_registro = registro if registro is not None else _controles.cargar(desde)
        estados = _controles.validar(doc_registro, desde)["controls"]
    except Exception as e:                           # noqa: BLE001 - se falla cerrado
        motivos.append("el registro de controles no se pudo leer: %s" % e)
        return _base(salida, SIN_RESOLVER, SIN_CONTROL)
    faltan = [c for c in POLICIES + CHECKS if estados.get(c) != _controles.INSTALADO]
    if faltan:
        motivos.append("controles compartidos que no estan instalados: %s" % ", ".join(faltan))
        return _base(salida, SIN_RESOLVER, SIN_CONTROL)

    salida["status"] = RESUELTA
    return salida


def _base(salida, status, estado):
    salida["status"] = status
    salida["states"] = [estado]
    return salida


# -- la ejecucion compartida ----------------------------------------------------

_CHECKS = {}


def _check(control_id, desde=None):
    """El modulo del check de G1, cargado del archivo que declara el registro. Se cachea."""
    if control_id in _CHECKS:
        return _CHECKS[control_id]
    c = _controles.control(control_id, None, desde)
    ruta = _controles._ruta_de((c or {}).get("file", ""), desde)
    if not ruta or not os.path.isfile(ruta):
        return None
    spec = importlib.util.spec_from_file_location("c3_compartido_" + control_id.replace("-", "_"),
                                                  ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    _CHECKS[control_id] = modulo
    return modulo


def _bien_formada(item):
    """Una tecnologia del inventario: un nombre de texto, y lo demas de la forma que G1 lee."""
    if not isinstance(item, dict):
        return False
    if not isinstance(item.get("technology"), str) or not item["technology"].strip():
        return False
    if item.get("version") is not None and not isinstance(item.get("version"), str):
        return False
    if item.get("role") is not None and not isinstance(item.get("role"), str):
        return False
    contexto = item.get("context")
    if contexto is not None:
        if not isinstance(contexto, dict):
            return False
        framework = contexto.get("framework")
        if framework is not None and not (
                isinstance(framework, dict) and isinstance(framework.get("technology"), str)
                and (framework.get("version") is None
                     or isinstance(framework.get("version"), str))):
            return False
    return True


def _orden(fila):
    return json.dumps(fila, sort_keys=True, ensure_ascii=False, default=str)


def ejecutar(inventario, catalogo=None, desde=None):
    """Los dos checks de G1, UNA vez por tecnologia, con las fuentes de cada resultado.

    `inventario` es el mismo que recibe G1: `[{"technology", "version", "role"?, "context"?}]`.
    Devuelve `None` en `results` si el inventario no se puede leer: no se ejecuta sobre la mitad.
    """
    salida = {"executions": {HOMOLOGACION: 0, VERSION: 0}, "results": None, "issues": []}
    if not isinstance(inventario, list) or not inventario:
        salida["issues"].append("no hay inventario de tecnologias")
        return salida
    torcidas = [i for i in inventario if not _bien_formada(i)]
    if torcidas:
        salida["issues"].append("el inventario trae %d tecnologia(s) sin la forma declarada; "
                                "no se ejecuta sobre la mitad" % len(torcidas))
        return salida

    homologacion, version = _check(HOMOLOGACION, desde), _check(VERSION, desde)
    if homologacion is None or version is None:
        salida["issues"].append("los checks compartidos no estan")
        return salida
    doc = catalogo if catalogo is not None else anexo2.cargar(desde)
    try:
        registro = _controles.cargar(desde)
    except Exception:                                # noqa: BLE001
        registro = {"controls": []}
    fuentes = {cid: sorted(f.get("ruleKey") or "" for f in
                           _controles.fuentes_de(_controles.control(cid, registro) or {}))
               for cid in CHECKS}

    filas = []
    for item in inventario:
        try:
            h = homologacion.evaluar(item, doc, desde)
            salida["executions"][HOMOLOGACION] += 1
            v = version.evaluar(item, doc, item.get("context"), desde)
            salida["executions"][VERSION] += 1
        except Exception as e:                       # noqa: BLE001 - se falla cerrado
            salida["issues"].append("un check compartido no pudo evaluar `%s`: %s"
                                    % (item.get("technology"), e))
            salida["results"] = None
            return salida
        filas.append({"technology": item["technology"], "declaredVersion": item.get("version"),
                      "homologation": h, "version": v,
                      "normativeSources": {HOMOLOGACION: fuentes[HOMOLOGACION],
                                           VERSION: fuentes[VERSION]}})
    salida["results"] = sorted(filas, key=_orden)
    return salida


# -- la agregacion --------------------------------------------------------------

# Los estados que emiten los checks de G1. Los de `anexo2`, por nombre.
ESTADOS_DE_G1 = (anexo2.HOMOLOGADA, anexo2.DEPRECADA, anexo2.NO_HOMOLOGADA) + PENDIENTES_DE_G1


def fila_legible(fila):
    """Si una fila compartida tiene su tecnologia y las dos mitades, del control que las produce."""
    if not isinstance(fila, dict) or not isinstance(fila.get("technology"), str):
        return False
    for parte, control in (("homologation", HOMOLOGACION), ("version", VERSION)):
        mitad = fila.get(parte)
        if not isinstance(mitad, dict) or mitad.get("control") != control \
                or mitad.get("state") not in ESTADOS_DE_G1:
            return False
    return True


def _coinciden(compartidos, inventario):
    """Si los resultados compartidos son de ESTE inventario, tecnologia por tecnologia."""
    if not isinstance(inventario, list) or not all(_bien_formada(i) for i in inventario):
        return False
    filas = compartidos.get("results") if isinstance(compartidos, dict) else None
    if not isinstance(filas, list) or not all(isinstance(f, dict) for f in filas):
        return False
    pedidas = sorted((i["technology"], str(i.get("version"))) for i in inventario)
    vistas = sorted((str(f.get("technology")), str(f.get("declaredVersion"))) for f in filas)
    return pedidas == vistas


def agregar(compartidos, clave_de_regla):
    """El resultado de UNA regla a partir de los resultados compartidos. No lee a la otra.

    🔴 Recibe lo que devolvio `ejecutar`, y nada mas. No hay argumento para el resultado de G1:
    la unica forma de que C3 dependa de G1 es que dependa de los mismos controles.
    """
    filas = compartidos.get("results") if isinstance(compartidos, dict) else None
    salida = {"ruleKey": clave_de_regla, "technologies": [], "states": [], "observations": []}
    if filas is None or filas == []:
        salida.update({"result": RESULTADO_SIN_RESOLVER, "states": [SIN_INVENTARIO]})
        return salida
    # 🔴 Una fila tiene las DOS mitades -homologacion y version-, cada una del control que la
    # produce y con un estado de G1. Si falta una, o no se reconoce, no se agrega sobre la mitad.
    if not isinstance(filas, list) or not all(fila_legible(f) for f in filas):
        salida.update({"result": RESULTADO_SIN_RESOLVER, "states": [SIN_CONTROL]})
        return salida

    for fila in filas:
        estados = sorted({(fila.get("homologation") or {}).get("state"),
                          (fila.get("version") or {}).get("state")} - {None})
        salida["technologies"].append({"technology": fila.get("technology"),
                                       "declaredVersion": fila.get("declaredVersion"),
                                       "homologation": (fila.get("homologation") or {}).get("state"),
                                       "version": (fila.get("version") or {}).get("state"),
                                       "states": estados})
    todos = [e for t in salida["technologies"] for e in t["states"]]
    if anexo2.NO_HOMOLOGADA in todos:
        salida["result"] = NO_CUMPLE
    elif any(e in PENDIENTES_DE_G1 or e not in (anexo2.HOMOLOGADA, anexo2.DEPRECADA)
             for e in todos):
        salida["result"] = RESULTADO_SIN_RESOLVER
    elif anexo2.DEPRECADA in todos:
        salida["result"] = CUMPLE_CON_OBSERVACIONES
        salida["observations"] = sorted({t["technology"] for t in salida["technologies"]
                                         if anexo2.DEPRECADA in t["states"]})
    else:
        salida["result"] = CUMPLE
    salida["states"] = sorted({e for e in todos
                               if e not in (anexo2.HOMOLOGADA, anexo2.DEPRECADA)})
    salida["technologies"].sort(key=_orden)
    return salida


def evaluar_c3(inventario, base=None, compartidos=None, catalogo=None, desde=None):
    """C3 entero: la puerta de la linea base, la ejecucion compartida y su agregacion.

    🔴 Una `base` que se pasa solo puede RESTRINGIR: la linea base instalada se resuelve igual,
    y C3 pasa solo si las dos estan resueltas. Una base forjada que dice `RESOLVED` no abre una
    puerta que la instalada tiene cerrada.

    🔴 `compartidos` es para quien ya ejecuto los checks de G1 sobre este inventario y no quiere
    ejecutarlos dos veces. Tienen que ser de ESTE inventario, tecnologia por tecnologia, y con
    la forma que devuelve `ejecutar`; si no, no se leen.
    """
    # La puerta mira el MISMO catalogo contra el que despues se ejecuta.
    instalada = resolver_base(catalogo=catalogo, desde=desde)
    resuelta = instalada
    if base is not None and instalada.get("status") == RESUELTA:
        valida = isinstance(base, dict) and base.get("status") == RESUELTA \
            and base.get("version") == instalada.get("version")
        if not valida:
            resuelta = dict(base) if isinstance(base, dict) else {}
            if resuelta.get("status") == RESUELTA or not resuelta.get("states"):
                resuelta.update({"status": DESFASADA if isinstance(base, dict) else SIN_RESOLVER,
                                 "states": [BASE_DESFASADA if isinstance(base, dict)
                                            else BASE_SIN_RESOLVER]})
            resuelta.setdefault("standard", ESTANDAR_DE_DESARROLLO)
            resuelta.setdefault("catalogRef", anexo2.ARCHIVO)
    salida = {"rule": REGLA, "ruleKey": CLAVE, "source": dict(TRAZA),
              "developmentStandardBaseline": {"standard": resuelta.get("standard"),
                                              "version": resuelta.get("version"),
                                              "status": resuelta.get("status"),
                                              "catalogRef": resuelta.get("catalogRef")},
              "sharedControls": {"policies": list(POLICIES), "checks": list(CHECKS)},
              "states": [], "reasons": list(resuelta.get("reasons") or [])}
    if resuelta.get("status") != RESUELTA:
        salida.update({"result": RESULTADO_SIN_RESOLVER,
                       "states": list(resuelta.get("states") or [BASE_SIN_RESOLVER])})
        return salida
    if compartidos is not None:
        if not _coinciden(compartidos, inventario):
            salida.update({"result": RESULTADO_SIN_RESOLVER,
                           "states": [SIN_INVENTARIO if not inventario else SIN_CONTROL]})
            salida["reasons"].append("los resultados compartidos que llegaron no son de este "
                                     "inventario, o no se pueden leer")
            return salida
        ejecutado = compartidos
    else:
        ejecutado = ejecutar(inventario, catalogo, desde)
    agregado = agregar(ejecutado, CLAVE)
    salida.update({"result": agregado["result"], "states": agregado["states"],
                   "technologies": agregado["technologies"],
                   "observations": agregado["observations"],
                   "executions": dict(ejecutado.get("executions") or {})})
    salida["reasons"].extend(ejecutado.get("issues") or [])
    return salida


# -- la regla, para `seguridad.ALGORITMOS` -------------------------------------

def regla_c3(r, evidencia, salida):
    """El resultado de C3 en `seguridad.resultado`.

    La evidencia trae `technologyInventory` -el mismo de G1- y nada mas que cuente.

    🔴 La linea base la resuelve este modulo, contra lo instalado, siempre. Una
    `developmentStandardBaseline` que llega en la evidencia solo puede restringir, y unos
    `sharedControlResults` que llegan en la evidencia no se leen: no hay como saber que salieron
    de los checks de G1, y C3 ejecuta los suyos sobre el inventario.
    """
    ev = evidencia if isinstance(evidencia, dict) else {}
    base = ev.get("developmentStandardBaseline")
    if "sharedControlResults" in ev:
        salida["reasons"].append("`sharedControlResults` llego en la evidencia y no se lee: C3 "
                                 "ejecuta los checks de G1 sobre el inventario")
    c3 = evaluar_c3(ev.get("technologyInventory"), base if base is not None else None)
    salida["developmentStandardBaseline"] = c3["developmentStandardBaseline"]
    salida["sharedControls"] = c3["sharedControls"]
    for e in c3.get("states") or []:
        if e not in salida["states"]:
            salida["states"].append(e)
    salida["reasons"].extend(c3.get("reasons") or [])
    if c3.get("technologies") is not None:
        salida["technologies"] = c3["technologies"]
    if c3.get("observations"):
        salida["observations"] = c3["observations"]
    salida["result"] = c3["result"]
    if c3["result"] == CUMPLE_CON_OBSERVACIONES:
        # `seguridad` no conoce el matiz; la regla cumple y las observaciones viajan al lado.
        salida["result"] = CUMPLE
        salida["compliance"] = CUMPLE_CON_OBSERVACIONES
    return salida


def c3_para_unidad(resultado=None, desde=None):
    """El bloque de C3 de la unidad de trabajo: referencias, no el catalogo."""
    r = resultado if isinstance(resultado, dict) else {}
    # 🔴 La base de la unidad es la instalada, no la que dice el resultado. Y se proyecta solo un
    # resultado de C3 con un estado que C3 emite; si la base instalada no esta resuelta, el
    # resultado tampoco, diga lo que diga.
    resuelta = resolver_base(desde=desde)
    base = {"standard": resuelta.get("standard"), "version": resuelta.get("version"),
            "status": resuelta.get("status"), "catalogRef": resuelta.get("catalogRef")}
    estado = r.get("result") if r.get("ruleKey") == CLAVE else None
    if estado not in RESULTADOS_DE_C3 or resuelta.get("status") != RESUELTA:
        r, estado = {}, None
    return {"result": estado or RESULTADO_SIN_RESOLVER,
            "developmentStandardBaseline": {"standard": base.get("standard"),
                                            "version": base.get("version"),
                                            "status": base.get("status"),
                                            "catalogRef": base.get("catalogRef")},
            "sharedControls": {"policies": list(POLICIES), "checks": list(CHECKS)},
            "evidence": sorted({t.get("technology") for t in
                                (r.get("technologies") if isinstance(r.get("technologies"), list)
                                 else [])
                                if isinstance(t, dict) and isinstance(t.get("technology"), str)}),
            "source": dict(TRAZA)}
