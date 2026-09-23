"""La frescura de una fuente: si el harness puede tratar como vigente lo que sabe de ella.

Esta es la mitad que decide, y la unica regla que la gobierna es esta:

    ESTAR DESACTUALIZADO Y SABERLO se tolera.
    ESTAR DESACTUALIZADO Y CREERSE AL DIA no puede pasar.

🔴 **`CURRENT` exige las cinco condiciones.** La fuente se descubrio, su version se resolvio,
su integridad se acepto, el extracto activo declara esa misma version y no hay un derivado
declarando otra. Falta una y el estado es otro, con su motivo. No hay camino desde evidencia
ausente hasta `CURRENT`: eso no es un detalle de implementacion, es lo unico que este modulo
promete.

🔴 **Lo que no se pudo mirar no esta al dia.** Si el canal configurado no contesta, el estado
es `FRESHNESS_UNVERIFIED`. El harness garantiza frescura RELATIVA al canal que tiene
configurado, y nunca afirma que un documento sea el mas nuevo que existe.

🔴 **Misma version con otro contenido es una alerta, no una novedad.** `SOURCE_INTEGRITY_ALERT`
es el caso que la metadata sola no ve: un documento reemplazado sin que nadie suba el numero.

🔴 **La resolucion es una funcion de la evidencia.** Misma evidencia, mismo resultado, en el
mismo orden. Sin eso, dos corridas seguidas dicen cosas distintas y ninguna se puede auditar.

Lo que hoy sostiene la cuarta condicion es la linea que el propio extracto declara en su
encabezado (`> Version 6.3 ...`). Cuando exista el registro de conocimiento, la procedencia
promovida la reemplaza: es mas fuerte, porque la escribe la promocion y no la prosa.
"""
import datetime
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402
from contexto import limpieza                    # noqa: E402
from . import procedencia                        # noqa: E402
from . import registro_fuentes                   # noqa: E402

VERSION_SCHEMA = "sources-state/1.1"
SCHEMA = "source-state.schema.json"
ARCHIVO = "harness.fuentes.json"

# Los doce estados. El unico que habilita a tratar el conocimiento como vigente es el primero.
CURRENT = "CURRENT"
NUEVA = "NEW_SOURCE"
HAY_ACTUALIZACION = "UPDATE_AVAILABLE"
CAMBIO_MISMA_VERSION = "SOURCE_CHANGED_SAME_VERSION"
ALERTA_DE_INTEGRIDAD = "SOURCE_INTEGRITY_ALERT"
REGRESION = "VERSION_REGRESSION"
FALTA = "SOURCE_MISSING"
SIN_VERSION = "VERSION_UNRESOLVED"
SIN_VERIFICAR = "FRESHNESS_UNVERIFIED"
RETIRADA = "RETIRED"
POSPUESTA = "ACKNOWLEDGED_PENDING"
PROMOCION_INCOMPLETA = "KNOWLEDGE_PROMOTION_INCOMPLETE"

ESTADOS = (CURRENT, NUEVA, HAY_ACTUALIZACION, CAMBIO_MISMA_VERSION, ALERTA_DE_INTEGRIDAD,
           REGRESION, FALTA, SIN_VERSION, SIN_VERIFICAR, RETIRADA, POSPUESTA,
           PROMOCION_INCOMPLETA)

# No bloquean: uno porque esta al dia y el otro porque ya no se sigue. Todo lo demas si.
NO_BLOQUEAN = (CURRENT, RETIRADA)

# -- riesgo --------------------------------------------------------------------

RIESGOS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
SIN_RIESGO = "UNRESOLVED"

# El piso por tipo de fuente. Una norma y un proceso obligan; una tecnologia documenta.
PISO_POR_TIPO = {"norma": "MEDIUM", "proceso": "MEDIUM", "tecnologia": "LOW"}

# Lo que sube el riesgo por como cambio la fuente.
RIESGO_DE_MUTACION = {
    ALERTA_DE_INTEGRIDAD: "HIGH",
    CAMBIO_MISMA_VERSION: "HIGH",
    REGRESION: "HIGH",
    NUEVA: "MEDIUM",
}

# Las clases de activo cuyo cambio cambia lo que el harness EXIGE. Que una fuente las toque
# sube el riesgo de cualquier derivacion, sin importar el tipo de la fuente.
IMPACTO_QUE_EXIGE = (procedencia.CONTROL, procedencia.FILA, procedencia.MATRIZ,
                     procedencia.AGENTE)


def _mayor(*riesgos):
    presentes = [r for r in riesgos if r in RIESGOS]
    if not presentes:
        return SIN_RIESGO
    return max(presentes, key=RIESGOS.index)


def riesgo_de(entrada, estado, impacto_aplanado):
    """El riesgo efectivo que se puede derivar en este punto.

    Son tres de las cuatro dimensiones: el piso del tipo de fuente, el radio de lo que toca y
    la forma de la mutacion. La cuarta -el tipo de artefacto que se va a construir- la agrega
    el contrato del candidato. El riesgo efectivo es un maximo, asi que agregar una dimension
    solo puede SUBIRLO: lo que sale de aca es un piso y nunca contradice lo que venga despues.
    """
    piso = PISO_POR_TIPO.get(str(entrada.get("kind") or ""), SIN_RIESGO)
    mutacion = RIESGO_DE_MUTACION.get(estado)
    radio = None
    if any(a.split(":", 1)[0] in IMPACTO_QUE_EXIGE for a in impacto_aplanado):
        radio = "HIGH"
    return _mayor(piso, mutacion, radio)


# -- versiones -----------------------------------------------------------------

_NUMERO = re.compile(r"^[0-9]+(?:\.[0-9]+)*$")

# Como declara su procedencia un extracto: la linea del encabezado, en el mismo formato en que
# la escribieron los seis que hay. Se lee esa linea y nada mas: buscar "6.3" en el cuerpo
# encontraria la version de cualquier cosa que el extracto cite.
_VERSION_DEL_EXTRACTO = re.compile(
    r"(?im)^>\s*versi[o\u00f3]n\s*:?\s*v?([0-9]+(?:\.[0-9]+)*)\b")


def _tupla(version):
    if not version or not _NUMERO.match(str(version)):
        return None
    return tuple(int(p) for p in str(version).split("."))


def comparar(observada, aceptada):
    """-1, 0, 1, o None si no se pueden ordenar. None falla cerrado: nadie adivina el orden."""
    a, b = _tupla(observada), _tupla(aceptada)
    if a is None or b is None:
        return 0 if (observada is not None and str(observada) == str(aceptada)) else None
    return (a > b) - (a < b)


def version_de_extracto(ruta):
    """La version que el extracto activo declara en su encabezado, o None."""
    if not ruta:
        return None
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            cabeza = f.read(4096)
    except OSError:
        return None
    m = _VERSION_DEL_EXTRACTO.search(cabeza)
    return m.group(1) if m else None


# -- la resolucion de una fuente -----------------------------------------------

def resolver_una(entrada, observacion, canal_disponible=True, decision=None,
                 ind=None, desde=None):
    """El estado de UNA fuente, con su evidencia. Funcion pura de lo que recibe."""
    sid = str(entrada.get("id") or "")
    obs = observacion or {"found": False, "evidence": []}
    evidencia = list(obs.get("evidence") or [])

    version_registro = entrada.get("version")
    version_observada = obs.get("observed_version")
    sha_registro = entrada.get("sha256")
    sha_observado = obs.get("observed_sha256")

    uno = procedencia.impacto(sid, ind, desde)
    impacto = procedencia.aplanar(uno)
    viejos = procedencia.desactualizados(sid, version_registro, ind, desde)

    estado = _estado_de(entrada, obs, canal_disponible, evidencia,
                        version_registro, version_observada, sha_registro, sha_observado,
                        viejos, desde)
    estado = _pospuesta(estado, obs, decision, evidencia)

    salida = {
        "state": estado,
        "registry_version": version_registro,
        "observed_version": version_observada,
        "attachmentId": obs.get("attachmentId"),
        "filename": obs.get("filename"),
        "size": obs.get("size"),
        "created": obs.get("created"),
        "observed_sha256": sha_observado,
        "registry_sha256": sha_registro,
        "downloaded": bool(obs.get("downloaded")),
        "effectiveRisk": riesgo_de(entrada, estado, impacto),
        "derived_impact": impacto,
        "stale_derived": [v["asset"] for v in viejos],
        "blocking": estado not in NO_BLOQUEAN,
        "evidence": evidencia,
    }
    return salida


def _pospuesta(estado, obs, decision, evidencia):
    """Posponer silencia el aviso de una identidad exacta; no crea frescura.

    🔴 Se compara la identidad OBSERVADA contra la que se pospuso. Una version nueva, un
    adjunto nuevo o un hash distinto invalidan la postergacion: si no, posponer una vez seria
    posponer para siempre, incluso lo que todavia no habia pasado.

    🔴 Y no alcanza a una alerta de integridad ni a una regresion. Posponer es "ya lo vi, lo
    aplico despues", y eso se puede decir de una version nueva. De un documento reemplazado sin
    cambiar el numero no hay nada que aplicar: hay algo que averiguar.
    """
    if estado not in (HAY_ACTUALIZACION, NUEVA):
        return estado
    if not decision or decision.get("decision") != "POSTPONE":
        return estado
    if (decision.get("observed_version") != obs.get("observed_version")
            or decision.get("observed_sha256") != obs.get("observed_sha256")):
        evidencia.append("hay una postergacion, y es sobre otra identidad de la fuente: no "
                         "alcanza a esta")
        return estado
    evidencia.append("alguien pospuso esta misma identidad: queda reconocida y pendiente, que "
                     "no es lo mismo que estar al dia")
    return POSPUESTA


def _estado_de(entrada, obs, canal_disponible, evidencia, version_registro,
               version_observada, sha_registro, sha_observado, viejos, desde):
    """El arbol de decision, en el orden en que se mira. Cada rama deja su motivo escrito."""
    if entrada.get("status") == registro_fuentes.RETIRADA:
        evidencia.append("la fuente esta retirada: no se sigue")
        return RETIRADA

    if not canal_disponible:
        evidencia.append("el canal configurado no se pudo consultar: la frescura queda sin "
                         "verificar, que no es lo mismo que estar al dia")
        return SIN_VERIFICAR

    if not obs.get("found"):
        evidencia.append("la fuente no aparece en el canal configurado")
        return FALTA

    if version_observada is None:
        evidencia.append("sin version observada no se puede afirmar nada sobre la frescura")
        return SIN_VERSION

    orden = comparar(version_observada, version_registro)
    if version_registro is None:
        evidencia.append("el registro no tiene version aceptada para esta fuente")
        return NUEVA
    if orden is None:
        evidencia.append("la version observada no se puede ordenar contra la aceptada")
        return SIN_VERSION
    if orden < 0:
        evidencia.append("la version observada es anterior a la aceptada: no se baja sola")
        return REGRESION
    if orden > 0:
        evidencia.append("hay una version posterior a la aceptada")
        return HAY_ACTUALIZACION

    # Misma version. Acá es donde la metadata ya no alcanza.
    if sha_registro and sha_observado and sha_observado != sha_registro:
        evidencia.append("misma version y contenido distinto del aceptado: el documento fue "
                         "reemplazado sin cambiar el numero")
        return ALERTA_DE_INTEGRIDAD
    if sha_observado is None and obs.get("identity_changed"):
        evidencia.append("misma version con otra identidad de adjunto, y sin poder hashear el "
                         "documento: no se puede decidir si cambio")
        return CAMBIO_MISMA_VERSION
    if sha_registro is None:
        evidencia.append("no hay hash aceptado para esta fuente: su integridad no se puede "
                         "verificar")
        return SIN_VERIFICAR
    if sha_observado is None:
        evidencia.append("no se pudo obtener el hash del documento observado")
        return SIN_VERIFICAR

    ruta_extracto = registro_fuentes.ruta_de_extracto(entrada, desde)
    if ruta_extracto is None:
        evidencia.append("el extracto activo que la entrada declara no esta en este arbol")
        return SIN_VERIFICAR
    version_extracto = version_de_extracto(ruta_extracto)
    if version_extracto is None:
        evidencia.append("el extracto activo no declara de que version salio")
        return SIN_VERIFICAR
    if comparar(version_extracto, version_registro) != 0:
        evidencia.append("el extracto activo salio de la version %s y la aceptada es %s"
                         % (version_extracto, version_registro))
        return HAY_ACTUALIZACION

    if viejos:
        evidencia.append("hay %d derivados declarando otra version: %s"
                         % (len(viejos), ", ".join(v["asset"] for v in viejos[:3])))
        return HAY_ACTUALIZACION

    evidencia.append("version, hash, extracto activo y derivados coinciden con lo aceptado")
    return CURRENT


# -- el documento --------------------------------------------------------------

def ahora():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def documento(entradas, observaciones, canal=None, decisiones=None, verificado_en=None,
              desde=None, ind=None):
    """El estado runtime completo. `canal` es lo que se sepa de la Ficha, o None."""
    por_id = {str(o.get("id")): o for o in (observaciones or [])}
    decisiones = decisiones or {}
    # 🔴 Sin canal, la frescura no se pudo verificar. El default NO es "no cambio nada": esa
    # es exactamente la afirmacion que este modulo existe para no hacer.
    disponible = bool(canal) and bool(canal.get("reachable", True))
    if ind is None:
        ind = procedencia.indice(desde)

    fuentes = {}
    for entrada in entradas:
        sid = str(entrada.get("id") or "")
        fuentes[sid] = resolver_una(entrada, por_id.get(sid), disponible,
                                    decisiones.get(sid), ind, desde)

    doc = {
        "schema_version": VERSION_SCHEMA,
        "verified_at": verificado_en or ahora(),
        "ficha": canal,
        "sources": fuentes,
        "decisions": decisiones,
        "pending_count": sum(1 for f in fuentes.values() if f["blocking"]),
        "warnings": [],
    }
    return doc


def validar(doc, desde=None):
    from . import tools
    armador = tools._armador()
    if armador is None:
        return ["no esta contexto-armar.py, de donde sale el validador"]
    ruta = rutas.localizar(("schemas", SCHEMA), desde or __file__)
    if ruta is None:
        return ["no esta %s" % SCHEMA]
    with io.open(ruta, encoding="utf-8") as f:
        esquema = json.load(f)
    armador.controlar_soporte(esquema)
    return armador.validar(doc, esquema)


def _limpiar(doc):
    """Redacta el documento entero menos `schema_version`.

    Los nombres de archivo y la evidencia vienen de afuera —de la Ficha, de un directorio que
    alguien eligio—, y lo que viene de afuera puede traer un token adentro. Se recorren las
    claves del documento y no una lista escrita a mano: una lista obliga a acordarse una vez
    por campo, para siempre.
    """
    catalogo = limpieza.cargar_catalogo()
    if catalogo is None:
        return doc
    for clave in [c for c in doc if c != "schema_version"]:
        limpio, hallazgos = limpieza.redactar_arbol(doc[clave], catalogo, "$." + clave)
        doc[clave] = limpio
        if hallazgos:
            doc["warnings"].extend(hallazgos)
    return doc


def ruta_por_defecto(raiz_proyecto):
    return os.path.join(raiz_proyecto, ".claude", ARCHIVO)


def escribir(doc, ruta, desde=None):
    """Lo limpia, lo valida y lo escribe. Un estado que no valida no se escribe."""
    doc = _limpiar(doc)
    errores = validar(doc, desde)
    if errores:
        raise ValueError("el estado de las fuentes no valida contra %s:\n  - %s"
                         % (VERSION_SCHEMA, "\n  - ".join(errores[:5])))
    carpeta = os.path.dirname(os.path.abspath(ruta))
    if carpeta and not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    with io.open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return ruta


def leer(ruta):
    """El estado anterior, o vacio. Nunca levanta: es una entrada, no una fuente de verdad."""
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        return {}
    return doc if isinstance(doc, dict) else {}
