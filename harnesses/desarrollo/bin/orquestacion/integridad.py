"""Integridad de repositorio: investigar un compromiso sin destruir la escena.

Cuando se sospecha que a un repositorio le entraron —un commit que nadie reconoce, una dependencia
que cambio de origen, un pipeline que empezo a subir cosas afuera, una credencial en el diff— el
comportamiento por defecto de un asistente es el peor posible: **arreglar**. El commit revertido, el
archivo borrado, la credencial rotada y el `force-push` se llevan puesta la unica evidencia de que
paso.

    preservar
    antes de
    cambiar

🔴 **Esto es una CAPACIDAD, no una regla.** No tiene senal de aplicabilidad, no entra en la matriz
de ES0901 ni en la de ES0902, y no se declara en `control-registry.json`. Puede producir evidencia
para reglas de seguridad; no es una de ellas, y que una revision no encuentre nada NO es una
aprobacion de seguridad.

🔴 **La rama actual no es una linea de base.** Comparar contra la rama por defecto cuando el
problema puede ser que alguien escribio en ella es comparar el repositorio consigo mismo. Adentro de
este modulo no hay ningun nombre de rama, y por eso no puede elegir la mas comoda. Sin procedencia
declarada: `TRUSTED_BASELINE_UNRESOLVED`.

🔴 **Un indicador debil no es malware.** `eval`, `exec`, Base64, un comando de shell, un dominio
nuevo, una dependencia nueva: los seis aparecen todos los dias en codigo legitimo. Ninguno —ni solo
ni los seis juntos— llega a un veredicto de malicioso confirmado. Lo que el harness reporta es
evidencia y confianza; **nunca intencion**, y nunca a una persona por su nombre o por la hora de su
commit.

🔴 **Confianza no es severidad.** Son dos ejes y ninguno se deriva del otro. La severidad sale del
mapeo autoritativo de ES0902 que `evaluacion` ya usa para el umbral de G2, con la misma compuerta;
este modulo **no declara ningun valor de severidad propio**. Sin mapeo: `SECURITY_SEVERITY_UNRESOLVED`.

🔴 **El nucleo no sabe de proveedores.** Los adaptadores traducen la forma de GitLab y de GitHub a
una evidencia normalizada, y ningun campo propio de un proveedor llega a un hallazgo: el dia que
entre el tercero habria que tocar el nucleo, y el nucleo es lo que decide si algo es sospechoso.
"""
import hashlib
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402
from . import evaluacion                         # noqa: E402
from . import seguridad                          # noqa: E402

SCHEMA_DE_HALLAZGO = "repository-integrity-finding.schema.json"
SCHEMA_DE_BASELINE = "trusted-repository-baseline.schema.json"

# -- los modos -----------------------------------------------------------------

NORMAL = "NORMAL"
EVALUACION = "SECURITY_ASSESSMENT"
INCIDENTE = "SECURITY_INCIDENT"
MODOS = (NORMAL, EVALUACION, INCIDENTE)

# Las seis que en incidente NO corren solas. Recomendarlas sigue permitido; ejecutarlas exige
# autorizacion explicita y la compuerta de riesgo que ya existe.
REMEDIACION = "CODE_REMEDIATION"
BORRADO = "FILE_DELETION"
ROTACION = "SECRET_ROTATION"
ACTUALIZACION = "DEPENDENCY_UPGRADE"
REESCRITURA = "HISTORY_REWRITE"
LIMPIEZA = "ARTIFACT_CLEANUP"
ACCIONES_MUTANTES = (REMEDIACION, BORRADO, ROTACION, ACTUALIZACION, REESCRITURA, LIMPIEZA)

# -- los estados ---------------------------------------------------------------

SIN_HALLAZGOS = "NO_SUSPICIOUS_CHANGE_FOUND"
SOSPECHOSO = "SUSPICIOUS_BEHAVIOR_DETECTED"
CONFIRMADO = "MALICIOUS_BEHAVIOR_CONFIRMED_BY_EVIDENCE"
INCOMPLETA = "REVIEW_INCOMPLETE"
SIN_BASELINE = "TRUSTED_BASELINE_UNRESOLVED"
ESTADOS = (SIN_HALLAZGOS, SOSPECHOSO, CONFIRMADO, INCOMPLETA, SIN_BASELINE)

REVISION_HUMANA = "HUMAN_SECURITY_REVIEW_REQUIRED"
SIN_AISLAMIENTO = "DYNAMIC_ANALYSIS_ENVIRONMENT_UNAVAILABLE"
SIN_SEVERIDAD = "SECURITY_SEVERITY_UNRESOLVED"
SIN_PRESERVAR = "EVIDENCE_NOT_PRESERVED"
SIN_AUTORIZACION = "EXPLICIT_AUTHORIZATION_REQUIRED"
HUECO_DE_SKILL = "SPECIALIZED_SKILL_GAP"

# -- la linea de base ----------------------------------------------------------

# De donde puede salir una linea de base confiable. 🔴 Ninguna es una UBICACION: `main`, `master`,
# `HEAD~1`, el ultimo tag y "el commit anterior al reporte" no son fuentes. Adentro de este modulo
# no hay ningun nombre de rama, y es a proposito.
FUENTES_DE_BASELINE = ("APPROVED_RELEASE", "DEPLOYED_RELEASE", "SECURITY_APPROVED_RELEASE",
                       "HUMAN_CONFIRMED", "OTHER_AUTHORITATIVE")
CONFIRMADA_POR_PERSONA = "HUMAN_CONFIRMED"

# -- el inventario de cambios --------------------------------------------------

CLASES_DE_CAMBIO = ("COMMITS", "FILES_ADDED", "FILES_MODIFIED", "FILES_DELETED",
                    "DEPENDENCY_CHANGES", "LOCKFILE_CHANGES", "CICD_CHANGES", "BUILD_CHANGES",
                    "AUTH_CHANGES", "NETWORK_DESTINATIONS", "BINARY_ARTIFACTS")

# Como llega clasificado un archivo cambiado. 🔴 La clase la DECLARA la evidencia normalizada: que
# un archivo este en una carpeta que se llama como un pipeline no lo hace un pipeline, y deducirlo
# es la misma trampa que `tmp` en un path.
CLASES_DE_ARCHIVO = ("SOURCE", "DEPENDENCY_MANIFEST", "LOCKFILE", "CICD", "BUILD",
                     "AUTHENTICATION", "AUTHORIZATION", "BINARY_ARTIFACT",
                     "INFRASTRUCTURE", "DOCUMENTATION")
SIN_CLASIFICAR = "UNCLASSIFIED_CHANGE"

AGREGADO = "ADDED"
MODIFICADO = "MODIFIED"
BORRADO_ = "DELETED"
OPERACIONES = (AGREGADO, MODIFICADO, BORRADO_)

# -- las categorias sospechosas ------------------------------------------------

# Las veintiuna del documento. Son SENALES DE INVESTIGACION, no veredictos de malware.
CATEGORIAS = (
    "REMOTE_PAYLOAD_DOWNLOAD", "DYNAMIC_CODE_EXECUTION", "OBFUSCATED_CODE",
    "CREDENTIAL_ACCESS", "SECRET_EXFILTRATION", "ENVIRONMENT_EXFILTRATION",
    "NEW_EXTERNAL_NETWORK_DESTINATION", "AUTHENTICATION_BYPASS", "AUTHORIZATION_BYPASS",
    "HARD_CODED_PRIVILEGED_IDENTITY", "BACKDOOR_LIKE_BEHAVIOR", "WEB_SHELL_LIKE_BEHAVIOR",
    "CI_CD_TAMPERING", "BUILD_SCRIPT_TAMPERING", "DEPENDENCY_SUBSTITUTION",
    "LOCKFILE_TAMPERING", "UNEXPECTED_BINARY_ARTIFACT", "INFRASTRUCTURE_TAMPERING",
    "PERSISTENCE_MECHANISM", "SECURITY_CONTROL_DISABLEMENT", "UNRESOLVED_SUSPICIOUS_CHANGE")

# 🔴 Los seis que NO prueban nada. Ni solos ni los seis juntos llegan a confirmado: todos aparecen
# en codigo legitimo todos los dias, y un harness que los llame malicioso es ruido que nadie mira.
INDICADORES_DEBILES = ("EVAL_PRESENT", "EXEC_PRESENT", "BASE64_PRESENT",
                       "SHELL_COMMAND_PRESENT", "NEW_DOMAIN_PRESENT", "NEW_DEPENDENCY_PRESENT")

BAJA = "LOW"
MEDIA = "MEDIUM"
ALTA = "HIGH"
CONFIANZAS = (BAJA, MEDIA, ALTA)

# -- los hechos sensibles del pipeline y de la cadena de suministro -------------

HECHOS_DE_PIPELINE = ("NEW_SECRET_ACCESS", "NEW_EXTERNAL_UPLOAD", "NEW_EXTERNAL_DOWNLOAD",
                      "NEW_SHELL_EXECUTION", "NEW_PUBLICATION_TARGET",
                      "NEW_DEPLOYMENT_TARGET", "DISABLED_SECURITY_GATE",
                      "WEAKENED_APPROVAL_GATE", "PRIVILEGED_RUNNER_CHANGE",
                      "REPOSITORY_TOKEN_CHANGE", "BRANCH_TRIGGER_CHANGE")

HECHOS_DE_CADENA = ("PACKAGE_SOURCE_CHANGE", "REGISTRY_CHANGE", "GIT_URL_DEPENDENCY",
                    "INSTALL_HOOK_CHANGE", "VERSION_JUMP", "PACKAGE_SUBSTITUTION",
                    "TRANSITIVE_LOCKFILE_CHANGE")

# -- el analisis --------------------------------------------------------------

ESTATICO = "STATIC"
DINAMICO = "DYNAMIC"

# -- los proveedores -----------------------------------------------------------

GITLAB = "GITLAB"
GITHUB = "GITHUB"
PROVEEDORES = (GITLAB, GITHUB)

# Lo unico que el nucleo consume. Un campo propio de un proveedor que no este aca no llega.
CAMPOS_NORMALIZADOS = ("repository", "ref", "commitSha", "parents", "author", "committer",
                       "timestamp", "changedFiles", "diffMeta", "verified", "provider")

# Lo unico que pasa del resumen del diff. 🔴 Copiar `stats` entero dejaba viajar cualquier campo que
# el proveedor pusiera adentro —una URL, un id— hasta la instantanea sellada: la lista de arriba
# cerraba el primer nivel y no el segundo.
CAMPOS_DE_DIFF = ("additions", "deletions", "total")

AGENTE = "dev-security"
SKILLS = ("dev-security-assessment", "dev-appsec-review", "dev-vulnerability-management")


class IntegridadInvalida(Exception):
    """Un contrato roto no se interpreta a medias."""


def declarado(valor):
    """El texto declarado, sin los blancos. Vacio si no hay nada."""
    return str(valor or "").strip()


# -- el modo -------------------------------------------------------------------

def modo_valido(modo):
    return modo in MODOS


def automatico_permitido(accion, modo):
    """Si esta accion mutante puede correr sola en este modo.

    🔴 En incidente NINGUNA de las seis. Recomendarlas sigue permitido, y esa diferencia es toda
    la capacidad: recomendar revertir un commit es util, y revertirlo solo destruye la evidencia
    de que se revirtio.
    """
    if accion not in ACCIONES_MUTANTES:
        return True
    return modo != INCIDENTE


def defensas(modo):
    """{accion: permitida} en este modo. Lo que un plan publica para que se vea."""
    return {"mode": modo if modo_valido(modo) else NORMAL,
            "automatic": {a: automatico_permitido(a, modo) for a in ACCIONES_MUTANTES},
            "evidencePreservingDefaults": modo == INCIDENTE}


def recomendar(accion, motivo, modo=INCIDENTE):
    """Una recomendacion: nunca ejecutada, siempre con revision humana pendiente."""
    return {"action": accion, "reason": declarado(motivo), "mode": modo,
            "executed": False, "requiresHumanReview": True,
            "state": REVISION_HUMANA}


# -- la linea de base ----------------------------------------------------------

def baseline(declarada):
    """(datos, motivo) de la linea de base confiable declarada.

    Exige las cinco cosas del contrato, y una sexta para la fuente que mas facil se escribe sola:
    una confirmacion humana sin la persona que la firmo es una afirmacion sin dueno.
    """
    datos = declarada if isinstance(declarada, dict) else {}
    for campo in ("repository", "ref", "commitSha"):
        if not declarado(datos.get(campo)):
            return None, "la linea de base no declara %s" % campo
    if datos.get("source") not in FUENTES_DE_BASELINE:
        return None, ("la linea de base no declara una procedencia de la lista: una rama, un tag "
                      "o `el commit anterior` son ubicaciones, no fuentes")
    evidencia = [declarado(e) for e in datos.get("evidence") or [] if declarado(e)]
    if not evidencia:
        return None, "la linea de base no cita ninguna evidencia"
    if datos.get("source") == CONFIRMADA_POR_PERSONA and not declarado(datos.get("establishedBy")):
        return None, ("una linea de base confirmada por una persona tiene que decir quien la "
                      "firmo")
    return {"repository": declarado(datos.get("repository")),
            "ref": declarado(datos.get("ref")),
            "commitSha": declarado(datos.get("commitSha")),
            "source": datos.get("source"),
            "evidence": sorted(evidencia),
            "establishedAt": declarado(datos.get("establishedAt")) or None,
            "establishedBy": declarado(datos.get("establishedBy")) or None}, ""


def contexto_de_revision(base):
    """El id del contexto de revision, derivado de la linea de base.

    🔴 Cambiar la linea de base NO actualiza una revision: crea otra. El id sale del repositorio,
    del commit y de la procedencia, asi que dos lineas de base distintas no pueden compartir
    contexto ni por accidente.
    """
    datos = base or {}
    semilla = "|".join([declarado(datos.get("repository")), declarado(datos.get("commitSha")),
                        declarado(datos.get("source"))])
    return "ri-" + hashlib.sha256(semilla.encode("utf-8")).hexdigest()[:16]


# -- la evidencia, y el secreto que no sale ------------------------------------

def huella(valor):
    """El hash de un valor. Sirve para correlacionar sin exponer."""
    return "sha256:" + hashlib.sha256(str(valor or "").encode("utf-8")).hexdigest()[:32]


def redactar(valor, visibles=4):
    """Un secreto potencial, sin el valor: redactado, huellado y medido.

    🔴 El valor en claro NO viaja. Lo que sirve para arreglarlo es donde esta y poder reconocer si
    es el mismo de otro lado; para las dos cosas alcanza la huella.
    """
    texto = str(valor or "")
    prefijo = texto[:visibles] if len(texto) > visibles else ""
    return {"redacted": (prefijo + "***") if prefijo else "***",
            "fingerprint": huella(texto), "length": len(texto)}


def secreto(ubicacion, valor, categoria="CREDENTIAL_ACCESS"):
    """La evidencia de un secreto potencial: ubicacion, categoria y valor redactado."""
    datos = redactar(valor)
    datos.update({"location": declarado(ubicacion), "category": categoria})
    return datos


def instantanea(evidencia, modo=INCIDENTE):
    """La evidencia preservada ANTES de tocar nada, con su sello.

    El sello es lo que hace inmutable a la instantanea: cambiar lo que devuelve no cambia lo que
    la revision guardo, y `sello_valido` lo dice.
    """
    datos = evidencia if isinstance(evidencia, dict) else {}
    cuerpo = {
        "repository": declarado(datos.get("repository")),
        "ref": declarado(datos.get("ref")),
        "commitSha": declarado(datos.get("commitSha")),
        "parents": sorted(declarado(p) for p in datos.get("parents") or [] if declarado(p)),
        "changedFiles": sorted(declarado(f.get("path")) for f in datos.get("changedFiles") or []
                               if declarado((f or {}).get("path"))),
        "hashes": {declarado(f.get("path")): declarado(f.get("afterHash"))
                   for f in datos.get("changedFiles") or []
                   if declarado((f or {}).get("path")) and declarado((f or {}).get("afterHash"))},
        "diffMeta": dict(datos.get("diffMeta") or {}),
        "manifests": sorted(declarado(m) for m in datos.get("manifests") or [] if declarado(m)),
        "pipelines": sorted(declarado(p) for p in datos.get("pipelines") or [] if declarado(p)),
        "timestamp": declarado(datos.get("timestamp")) or None,
        "mode": modo,
    }
    cuerpo["seal"] = huella(json.dumps(cuerpo, sort_keys=True, ensure_ascii=False))
    return cuerpo


def sello_valido(preservada):
    """Si la instantanea sigue siendo la que se sello."""
    datos = dict(preservada or {})
    sello = datos.pop("seal", None)
    return bool(sello) and sello == huella(json.dumps(datos, sort_keys=True, ensure_ascii=False))


def autorizar_mutacion(accion, modo, preservada=None, autorizacion=None):
    """Si una accion que toca el repositorio puede ejecutarse, y por que no.

    🔴 Dos compuertas independientes y ninguna alcanza sola: la evidencia tiene que estar
    preservada ANTES, y en incidente ademas hace falta una autorizacion explicita. Sin las dos,
    lo unico que queda es recomendar.
    """
    salida = {"action": accion, "mode": modo, "allowed": False, "reasons": [],
              "requiresHumanReview": False}

    if accion in ACCIONES_MUTANTES and not (preservada and sello_valido(preservada)):
        salida["reasons"].append(SIN_PRESERVAR)
    if not automatico_permitido(accion, modo):
        explicita = isinstance(autorizacion, dict) and autorizacion.get("explicit") is True
        citada = declarado((autorizacion or {}).get("reference"))
        if not explicita or not citada:
            salida["reasons"].append(SIN_AUTORIZACION)
        salida["requiresHumanReview"] = True
        salida["state"] = REVISION_HUMANA

    salida["allowed"] = not salida["reasons"]
    return salida


# -- el inventario determinista ------------------------------------------------

def _archivos(evidencia, operacion):
    return [f for f in (evidencia or {}).get("changedFiles") or []
            if isinstance(f, dict) and f.get("operation") == operacion]


def _por_clase(evidencia, clases):
    salida = []
    for f in (evidencia or {}).get("changedFiles") or []:
        if isinstance(f, dict) and f.get("kind") in clases and declarado(f.get("path")):
            salida.append(declarado(f.get("path")))
    return sorted(set(salida))


def inventario(base, evidencia):
    """El inventario de cambios entre la linea de base y el estado actual.

    🔴 Determinista: todo ordenado, nada derivado de un conjunto sin orden, y ninguna marca de
    tiempo de *ahora*. La misma linea de base y la misma evidencia producen el mismo inventario,
    y el orden de entrada no lo cambia. Sin eso, dos corridas de la misma investigacion se
    contradicen y ninguna se puede citar.
    """
    datos = evidencia if isinstance(evidencia, dict) else {}
    commits = []
    for c in datos.get("commits") or []:
        if not isinstance(c, dict) or not declarado(c.get("sha")):
            continue
        commits.append({"sha": declarado(c.get("sha")),
                        "parents": sorted(declarado(p) for p in c.get("parents") or []
                                          if declarado(p)),
                        "author": declarado(c.get("author")) or None,
                        "timestamp": declarado(c.get("timestamp")) or None,
                        "verified": c.get("verified")})

    hashes = {}
    for f in datos.get("changedFiles") or []:
        if not isinstance(f, dict) or not declarado(f.get("path")):
            continue
        antes, despues = declarado(f.get("beforeHash")), declarado(f.get("afterHash"))
        if antes or despues:
            hashes[declarado(f.get("path"))] = {"beforeHash": antes or None,
                                                "afterHash": despues or None}

    sin_clasificar = sorted(declarado(f.get("path"))
                            for f in datos.get("changedFiles") or []
                            if isinstance(f, dict) and declarado(f.get("path"))
                            and f.get("kind") not in CLASES_DE_ARCHIVO)

    salida = {
        "baselineCommit": declarado((base or {}).get("commitSha")) or None,
        "currentCommit": declarado(datos.get("commitSha")) or None,
        "COMMITS": sorted(commits, key=lambda c: c["sha"]),
        "FILES_ADDED": sorted(declarado(f.get("path")) for f in _archivos(datos, AGREGADO)),
        "FILES_MODIFIED": sorted(declarado(f.get("path")) for f in _archivos(datos, MODIFICADO)),
        "FILES_DELETED": sorted(declarado(f.get("path")) for f in _archivos(datos, BORRADO_)),
        "DEPENDENCY_CHANGES": _por_clase(datos, ("DEPENDENCY_MANIFEST",)),
        "LOCKFILE_CHANGES": _por_clase(datos, ("LOCKFILE",)),
        "CICD_CHANGES": _por_clase(datos, ("CICD",)),
        "BUILD_CHANGES": _por_clase(datos, ("BUILD", "INFRASTRUCTURE")),
        "AUTH_CHANGES": _por_clase(datos, ("AUTHENTICATION", "AUTHORIZATION")),
        "NETWORK_DESTINATIONS": sorted(set(declarado(d) for d in
                                           datos.get("networkDestinations") or []
                                           if declarado(d))),
        "BINARY_ARTIFACTS": _por_clase(datos, ("BINARY_ARTIFACT",)),
        "fileHashes": hashes,
        SIN_CLASIFICAR: sin_clasificar,
    }
    return salida


def inventario_completo(inv):
    """(completo, motivo): sin archivos sin clasificar."""
    sueltos = (inv or {}).get(SIN_CLASIFICAR) or []
    if sueltos:
        return False, ("hay archivos cambiados sin clase declarada: %s" % ", ".join(sueltos))
    return True, ""


# -- las senales y la confirmacion ---------------------------------------------

def confianza(senal):
    """Cuanto sostiene la evidencia esta senal.

    🔴 Los indicadores debiles no suben mas alla de BAJA por muchos que sean. Acumular seis
    coincidencias que aparecen en cualquier repositorio no produce una septima cosa: produce seis
    coincidencias.
    """
    datos = senal if isinstance(senal, dict) else {}
    indicadores = [declarado(i) for i in datos.get("indicators") or [] if declarado(i)]
    fuertes = [i for i in indicadores if i not in INDICADORES_DEBILES]
    if datos.get("directEvidence") is True and fuertes:
        return ALTA
    if fuertes:
        return MEDIA if len(fuertes) < 2 else ALTA
    return BAJA


def estado_de_senal(senal):
    """El veredicto de una senal: sospechoso, confirmado o revision incompleta.

    🔴 `MALICIOUS_BEHAVIOR_CONFIRMED_BY_EVIDENCE` exige evidencia DIRECTA declarada con su cita y
    confianza alta. No se llega ahi por tener `eval`, Base64, un shell o una dependencia rara, ni
    por tener los seis.
    """
    datos = senal if isinstance(senal, dict) else {}
    if datos.get("category") not in CATEGORIAS:
        return INCOMPLETA
    if not [declarado(e) for e in datos.get("evidence") or [] if declarado(e)]:
        return INCOMPLETA
    if (datos.get("directEvidence") is True and confianza(datos) == ALTA
            and declarado(datos.get("directEvidenceReference"))):
        return CONFIRMADO
    return SOSPECHOSO


# -- la severidad, que es la de ES0902 -----------------------------------------

def severidad(senal, mapeo=None):
    """La severidad de seguridad de una senal, con su fuente. O por que no se pudo mapear.

    🔴 Sale del mapeo autoritativo de ES0902 y de ningun lado mas: la MISMA compuerta que
    `evaluacion.umbral` —el mapeo tiene que declararse autoritativo y traer evidencia— porque
    decidir que un `medium` de una herramienta es el `LOW` del estandar lo tiene que firmar
    alguien. Este modulo no declara ningun valor de severidad propio.
    """
    if (not isinstance(mapeo, dict) or mapeo.get("authoritative") is not True
            or not mapeo.get("evidence")):
        return {"value": None, "source": None, "state": SIN_SEVERIDAD,
                "reason": seguridad.MAPEO_DE_RIESGO_SIN_RESOLVER}
    categoria = evaluacion._categoria({"scannerSeverity": (senal or {}).get("scannerSeverity")},
                                      mapeo)
    if categoria is None:
        return {"value": None, "source": None, "state": SIN_SEVERIDAD,
                "reason": seguridad.MAPEO_DE_RIESGO_SIN_RESOLVER}
    return {"value": categoria, "source": declarado(mapeo.get("source")) or seguridad.ESTANDAR,
            "state": None, "reason": ""}


# -- los hallazgos -------------------------------------------------------------

def cargar_schema(nombre, desde=None):
    ruta = rutas.localizar(("schemas", nombre), desde or __file__)
    if ruta is None:
        raise IntegridadInvalida("no esta %s" % nombre)
    with io.open(ruta, encoding="utf-8") as f:
        return json.load(f)


def validar_hallazgo(hallazgo, desde=None):
    """Lista de problemas estructurales contra el contrato. Vacia es bien formado."""
    from . import tools
    armador = tools._armador()
    if armador is None:
        raise IntegridadInvalida("no esta contexto-armar.py, de donde sale el validador.")
    esquema = cargar_schema(SCHEMA_DE_HALLAZGO, desde)
    armador.controlar_soporte(esquema)
    return list(armador.validar(hallazgo, esquema))


def validar_baseline(base, desde=None):
    from . import tools
    armador = tools._armador()
    if armador is None:
        raise IntegridadInvalida("no esta contexto-armar.py, de donde sale el validador.")
    esquema = cargar_schema(SCHEMA_DE_BASELINE, desde)
    armador.controlar_soporte(esquema)
    return list(armador.validar(base, esquema))


def hallazgo(senal, revision, base=None, mapeo=None):
    """Un hallazgo completo: evidencia, confianza, severidad y que hacer, sin un secreto adentro.

    🔴 La evidencia entra ya redactada. Este modulo no tiene con que reconocer un secreto en una
    cadena arbitraria, y fingir que si lo tiene seria peor que no hacer nada: lo que garantiza es
    que lo que se declaro secreto viaja redactado y huellado.
    """
    datos = senal if isinstance(senal, dict) else {}
    estado = estado_de_senal(datos)
    nivel = confianza(datos)
    riesgo = severidad(datos, mapeo)
    # 🔴 Los indicadores VIAJAN al hallazgo, y los hechos sensibles se separan por su vocabulario.
    # Sin esto, `HECHOS_DE_PIPELINE` y `HECHOS_DE_CADENA` eran declaraciones muertas —nada las
    # leia— y un acceso nuevo a un secreto en el pipeline no se exponia en ningun campo: el
    # hallazgo salia con su categoria y sin el hecho que lo origino, que es lo que quien remedia
    # necesita para saber DONDE mirar.
    indicadores = sorted(set(declarado(i) for i in datos.get("indicators") or []
                             if declarado(i)))
    salida = {
        "findingId": declarado(datos.get("id")) or huella(json.dumps(datos, sort_keys=True,
                                                                     ensure_ascii=False))[:20],
        "reviewId": declarado(revision),
        "repository": declarado((base or {}).get("repository")),
        "baselineCommit": declarado((base or {}).get("commitSha")) or None,
        "currentCommit": declarado(datos.get("currentCommit")) or None,
        "commits": sorted(declarado(c) for c in datos.get("commits") or [] if declarado(c)),
        "file": declarado(datos.get("file")) or None,
        "location": declarado(datos.get("location")) or None,
        "beforeHash": declarado(datos.get("beforeHash")) or None,
        "afterHash": declarado(datos.get("afterHash")) or None,
        "category": datos.get("category"),
        "indicators": indicadores,
        "pipelineFacts": [i for i in indicadores if i in HECHOS_DE_PIPELINE],
        "supplyChainFacts": [i for i in indicadores if i in HECHOS_DE_CADENA],
        "weakIndicators": [i for i in indicadores if i in INDICADORES_DEBILES],
        "status": estado,
        "confidence": nivel,
        "severity": {"value": riesgo["value"], "source": riesgo["source"]},
        "evidence": sorted(declarado(e) for e in datos.get("evidence") or [] if declarado(e)),
        "reasoningSummary": declarado(datos.get("reasoningSummary")) or None,
        "recommendedNextAction": declarado(datos.get("recommendedNextAction")) or None,
        "requiresHumanReview": estado == CONFIRMADO or nivel == ALTA,
        # 🔴 Siempre presente, `None` cuando la severidad se resolvio. Un campo que aparece y
        # desaparece obliga a quien lo consume a preguntar si existe antes de leerlo, y el que
        # se olvida lee un hueco como si fuera un valor.
        "severityState": riesgo["state"],
    }
    return salida


# -- la compuerta humana -------------------------------------------------------

CAUSAS_DE_REVISION = ("CONFIRMED_MALICIOUS_BEHAVIOR", "HIGH_CONFIDENCE_SUSPICION",
                      "REMEDIATION_PROPOSED", "SECRET_ROTATION_PROPOSED",
                      "DYNAMIC_EXECUTION_PROPOSED", "BASELINE_DISPUTED",
                      "CONTRADICTORY_EVIDENCE")


def compuerta_humana(revision):
    """Si hace falta una decision humana, y por cual de las siete causas."""
    datos = revision if isinstance(revision, dict) else {}
    causas = []
    hallazgos = datos.get("findings") or []
    if [h for h in hallazgos if (h or {}).get("status") == CONFIRMADO]:
        causas.append(CAUSAS_DE_REVISION[0])
    if [h for h in hallazgos if (h or {}).get("confidence") == ALTA]:
        causas.append(CAUSAS_DE_REVISION[1])
    for bandera, causa in (("remediationProposed", CAUSAS_DE_REVISION[2]),
                           ("secretRotationProposed", CAUSAS_DE_REVISION[3]),
                           ("dynamicExecutionProposed", CAUSAS_DE_REVISION[4]),
                           ("baselineDisputed", CAUSAS_DE_REVISION[5]),
                           ("contradictoryEvidence", CAUSAS_DE_REVISION[6])):
        if datos.get(bandera) is True:
            causas.append(causa)
    return {"required": bool(causas), "causes": sorted(set(causas)),
            "state": REVISION_HUMANA if causas else None}


# -- el analisis dinamico ------------------------------------------------------

def analisis_dinamico(pedido, modo=INCIDENTE, contrato=None, desde=None):
    """Si se puede ejecutar codigo sospechoso, y por que no.

    🔴 Por defecto el analisis es ESTATICO. Lo dinamico exige las cuatro cosas —ambiente aislado,
    autorizacion explicita, contencion de red y preservacion— y ademas pasa por la compuerta de
    riesgo de tools que ya existe. No hay una compuerta propia: tener dos es tener una que un dia
    dice que si.
    """
    from . import tools
    datos = pedido if isinstance(pedido, dict) else {}
    salida = {"analysis": DINAMICO, "allowed": False, "reasons": [],
              "requiresHumanReview": True, "state": REVISION_HUMANA}

    if datos.get("isolatedEnvironment") is not True:
        salida["reasons"].append(SIN_AISLAMIENTO)
        salida["state"] = SIN_AISLAMIENTO
        return salida
    if not (isinstance(datos.get("authorization"), dict)
            and datos["authorization"].get("explicit") is True
            and declarado(datos["authorization"].get("reference"))):
        salida["reasons"].append(SIN_AUTORIZACION)
    if datos.get("networkContainment") is not True:
        salida["reasons"].append("NETWORK_CONTAINMENT_REQUIRED")
    if not (datos.get("evidencePreserved") and sello_valido(datos.get("evidencePreserved"))):
        salida["reasons"].append(SIN_PRESERVAR)

    # La compuerta de riesgo es la del harness, no una de aca.
    if contrato is not None:
        salida["toolRisk"] = tools.derivar_riesgo(contrato)
        salida["toolRiskErrors"] = tools.controlar_riesgo(contrato)
        salida["toolRequiresHumanApproval"] = tools.exige_aprobacion_humana(contrato)
        if salida["toolRiskErrors"]:
            salida["reasons"].append("TOOL_RISK_GATE_REJECTED")

    salida["allowed"] = not salida["reasons"]
    return salida


def ejecucion_automatica_de_binario():
    """Nunca. Existe para que la respuesta tenga un lugar y no sea una omision."""
    return False


# -- la remediacion, que es otra unidad ----------------------------------------

def unidad_de_remediacion(revision, hallazgos, autorizacion=None):
    """La unidad de trabajo de remediacion, enlazada a los hallazgos que la originaron.

    🔴 Investigar y remediar no son el mismo paso. Y el registro del incidente NO se borra: la
    unidad referencia los hallazgos por id y la instantanea sigue sellada.
    """
    ids = sorted(declarado((h or {}).get("findingId")) for h in hallazgos or []
                 if declarado((h or {}).get("findingId")))
    explicita = isinstance(autorizacion, dict) and autorizacion.get("explicit") is True
    return {"workUnitType": "REMEDIATION", "linkedReviewId": declarado(revision),
            "linkedFindings": ids, "authorized": explicita,
            "requiresHumanReview": True, "state": REVISION_HUMANA,
            "originalEvidencePreserved": True}


# -- la contabilidad del Bloque 4 ----------------------------------------------

def contabilidad(revision, uso=None):
    """El evento de contabilidad de un analisis de incidente: metricas y nada mas.

    🔴 Ni un secreto, ni un payload, ni el cuerpo de un script. Lo que el Bloque 4 mide es tiempo,
    tokens, modelo y costo; guardar el contenido del repositorio ahi seria sacar la evidencia del
    lugar donde esta protegida y ponerla en un registro de metricas.
    """
    datos = revision if isinstance(revision, dict) else {}
    return {"eventType": "REPOSITORY_INTEGRITY_REVIEW",
            "reviewId": declarado(datos.get("reviewId")),
            "repository": declarado((datos.get("baseline") or {}).get("repository")),
            "findingCount": len(datos.get("findings") or []),
            "confirmedCount": len([h for h in datos.get("findings") or []
                                   if (h or {}).get("status") == CONFIRMADO]),
            "usage": dict(uso or {})}


# -- los adaptadores de proveedor ----------------------------------------------

def _archivo_normalizado(f):
    return {"path": declarado((f or {}).get("path")),
            "operation": (f or {}).get("operation"),
            "kind": (f or {}).get("kind"),
            "beforeHash": declarado((f or {}).get("beforeHash")) or None,
            "afterHash": declarado((f or {}).get("afterHash")) or None}


def _diff_normalizado(stats):
    datos = stats if isinstance(stats, dict) else {}
    return {k: datos[k] for k in CAMPOS_DE_DIFF if k in datos}


def normalizar(crudo, proveedor):
    """La evidencia de un proveedor, traducida al contrato del nucleo.

    🔴 Lo que no esta en `CAMPOS_NORMALIZADOS` no pasa. El dia que entre el tercer proveedor, lo
    que no puede pasar es tener que tocar el nucleo — y el nucleo es lo que decide si algo es
    sospechoso.
    """
    if proveedor not in PROVEEDORES:
        raise IntegridadInvalida("proveedor desconocido: %s" % proveedor)
    datos = crudo if isinstance(crudo, dict) else {}
    if proveedor == GITLAB:
        salida = {
            "repository": declarado(datos.get("project_path")),
            "ref": declarado(datos.get("ref")),
            "commitSha": declarado(datos.get("id")),
            "parents": [declarado(p) for p in datos.get("parent_ids") or [] if declarado(p)],
            "author": declarado(datos.get("author_email")) or None,
            "committer": declarado(datos.get("committer_email")) or None,
            "timestamp": declarado(datos.get("committed_date")) or None,
            "changedFiles": [_archivo_normalizado(f) for f in datos.get("diffs") or []],
            "diffMeta": _diff_normalizado(datos.get("stats")),
            "verified": (datos.get("signature") or {}).get("verification_status") == "verified",
        }
    else:
        salida = {
            "repository": declarado(datos.get("full_name")),
            "ref": declarado(datos.get("ref")),
            "commitSha": declarado(datos.get("sha")),
            "parents": [declarado((p or {}).get("sha")) for p in datos.get("parents") or []
                        if declarado((p or {}).get("sha"))],
            "author": declarado(((datos.get("commit") or {}).get("author") or {}).get("email"))
            or None,
            "committer": declarado(((datos.get("commit") or {}).get("committer") or {})
                                   .get("email")) or None,
            "timestamp": declarado(((datos.get("commit") or {}).get("author") or {})
                                   .get("date")) or None,
            "changedFiles": [_archivo_normalizado(f) for f in datos.get("files") or []],
            "diffMeta": _diff_normalizado(datos.get("stats")),
            "verified": ((datos.get("commit") or {}).get("verification") or {})
            .get("verified") is True,
        }
    salida["provider"] = proveedor
    return {k: v for k, v in salida.items() if k in CAMPOS_NORMALIZADOS}


# -- la revision entera --------------------------------------------------------

def revisar(base_declarada, evidencia, senales=None, modo=INCIDENTE, mapeo=None, desde=None):
    """Una revision de integridad completa, con su estado, sus hallazgos y sus limitaciones.

    🔴 Que no encuentre nada NO es una aprobacion de seguridad: el resultado no lleva ningun
    estado oficial de ES0902 y no mueve el que `evaluacion` resuelve.
    """
    salida = {"capability": "repository-integrity-review", "mode": modo,
              "defenses": defensas(modo), "findings": [], "limitations": [], "issues": []}

    base, motivo = baseline(base_declarada)
    if base is None:
        salida.update({"state": SIN_BASELINE, "reason": SIN_BASELINE, "detail": motivo,
                       "baseline": None, "reviewId": None})
        salida["limitations"].append("sin linea de base confiable, las conclusiones son parciales")
        return salida

    salida["baseline"] = dict(base)
    salida["reviewId"] = contexto_de_revision(base)
    salida["snapshot"] = instantanea(evidencia, modo)
    salida["inventory"] = inventario(base, evidencia)

    completo, motivo_cobertura = inventario_completo(salida["inventory"])
    salida["findings"] = [hallazgo(s, salida["reviewId"], base, mapeo) for s in senales or []]
    salida["humanGate"] = compuerta_humana(dict(salida, **{
        "remediationProposed": (evidencia or {}).get("remediationProposed") is True}))

    estados = [h["status"] for h in salida["findings"]]
    if CONFIRMADO in estados:
        salida.update({"state": CONFIRMADO, "reason": CONFIRMADO})
    elif not completo:
        salida.update({"state": INCOMPLETA, "reason": INCOMPLETA, "detail": motivo_cobertura})
        salida["limitations"].append(motivo_cobertura)
    elif INCOMPLETA in estados:
        salida.update({"state": INCOMPLETA, "reason": INCOMPLETA})
    elif SOSPECHOSO in estados:
        salida.update({"state": SOSPECHOSO, "reason": SOSPECHOSO})
    else:
        salida.update({"state": SIN_HALLAZGOS, "reason": ""})
    return salida


def skills_de_ejecucion(desde=None):
    """Quien ejecutaria la revision, resuelto contra el registro de agentes.

    🔴 Esto no crea agentes ni skills: dice cuales de las instaladas cubren la capacidad. Si
    alguna faltara, el hueco se declara con el estado que ya existe y se decide aparte.
    """
    from . import registro_agentes as reg
    return [dict(reg.resolver_ruteo(AGENTE, skill, None, desde or __file__),
                 requestedFor="repository-integrity-review")
            for skill in SKILLS]
