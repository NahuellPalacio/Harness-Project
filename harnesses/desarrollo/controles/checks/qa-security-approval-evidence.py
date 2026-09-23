"""Check normativo: la aplicacion homologada tiene el aprobado de seguridad EN QA, y sigue valiendo.

    source: ES0902 / 6.2 / 3 / C2
    source: ES0901 / 6.3 / Anexo V (el resolvedor de revalidacion)

Contesta si hay una aprobacion oficial de seguridad, emitida en QA por la autoridad del GCABA que
controla la seguridad de este alcance, para ESTA aplicacion y ESTE artefacto, y si nada de lo que
paso desde el assessment obliga a repetirlo.

🔴 **Esto no es un check del hook.** No corre en `PreToolUse`, no tiene presupuesto de latencia
y no devuelve las tres salidas del contrato de `comun/checks/`. Es un control normativo.

🔴 **Nada interno aprueba.** Ni `dev-security`, ni sus skills, ni un escaner, ni el CI, ni un check
o una review del harness, ni la configuracion del proyecto, ni lo que afirme alguien del equipo. La
procedencia del registro solo admite la autoridad externa del GCABA o `UNRESOLVED`, y los resultados
internos -revision interna completa, listo para pedir, listo para reenviar, el umbral de G2- no
entran a ninguna decision.

🔴 **QA, o no.** Una aprobacion o un escaneo en DEV, HML o PRD no sustituye a la de QA. Y no saber
el ambiente no es lo mismo que saber que es otro.

🔴 **La procedencia se ata a O2, que no se vuelve a resolver.** O2 dice que organismo del GCABA
controla la seguridad de este alcance; C2 exige que la aprobacion cite a esa autoridad. O2 en PASS
sin aprobacion no es C2 en PASS.

🔴 **El artefacto se identifica por lo que no cambia.** Commit, build, digest del artefacto, digest
de la imagen, release. La rama y el repositorio se informan y no deciden: son lo mismo para dos
releases distintos.

🔴 **Una aprobacion vieja no se reusa a ciegas.** El resolvedor del Anexo V devuelve TODOS los
motivos de revalidacion con su evidencia. Los 20 dias van con el desarrollo: el Anexo no dice que
las aprobaciones vencen a los 20 dias. Y una clasificacion de un modelo no puede suprimir un motivo.

🔴 **Un assessment parcial no es total.** Cubre la remediacion; para aprobar el release hace falta
una cobertura oficial explicita que nombre al candidato.

🔴 **Lo consumido lleva huella.** Si la aprobacion cambio desde la decision anterior, se vuelve a
evaluar. Este modulo no escribe nada.

🔴 **PASS es C2 y nada mas.** No son las reglas Vu, no es G2, G3 ni G4, no es la aprobacion de un
despliegue a produccion ni la homologacion de usuario.
"""
import hashlib
import io
import json
import os
import re
import sys
import unicodedata
from datetime import date

_BIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_BIN, "bin") not in sys.path:
    sys.path.insert(0, os.path.join(_BIN, "bin"))

import rutas                                        # noqa: E402
from orquestacion import roster as _roster          # noqa: E402
from orquestacion import senales as _senales        # noqa: E402

CONTROL = "qa-security-approval-evidence"
TIPO = "CHECK"
REGLA = "C2"
CLAVE = "ES0902.C2"
SENAL = "securityHomologationPresent"

ARCHIVO = "security-approval-evidence.json"
SCHEMA = "security-approval-evidence.schema.json"

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "3", "rule": REGLA}
TRAZA_ANEXO_V = {"standard": "ES0901", "version": "6.3", "section": "Anexo V"}

# -- los estados ----------------------------------------------------------------

PASA = "PASS"
FALLA = "FAIL"
NO_APLICA = "NOT_APPLICABLE"
SIN_APLICABILIDAD = "APPLICABILITY_UNRESOLVED"
REQUERIDA = "SECURITY_APPROVAL_REQUIRED"
EVIDENCIA_SIN_RESOLVER = "SECURITY_APPROVAL_EVIDENCE_UNRESOLVED"
AMBIENTE_SIN_RESOLVER = "SECURITY_APPROVAL_ENVIRONMENT_UNRESOLVED"
FUERA_DE_QA = "SECURITY_APPROVAL_NOT_IN_QA"
AUTORIDAD_SIN_RESOLVER = "SECURITY_APPROVAL_AUTHORITY_UNRESOLVED"
ALCANCE_SIN_RESOLVER = "SECURITY_APPROVAL_SCOPE_UNRESOLVED"
ARTEFACTO_SIN_RESOLVER = "SECURITY_APPROVAL_ARTIFACT_UNRESOLVED"
REEVALUAR = "SECURITY_REASSESSMENT_REQUIRED"
PARCIAL_SIN_RESOLVER = "PARTIAL_ASSESSMENT_SCOPE_UNRESOLVED"
EDAD_SIN_CONTEXTO = "ASSESSMENT_AGE_CONTEXT_UNRESOLVED"
MOTIVO_SIN_CLASIFICAR = "ASSESSMENT_TRIGGER_CLASSIFICATION_UNRESOLVED"
EVIDENCIA_CAMBIADA = "SECURITY_APPROVAL_EVIDENCE_CHANGED"
VALIDEZ_SIN_RESOLVER = "ASSESSMENT_VALIDITY_UNRESOLVED"

# Diecisiete, y el unico que aprueba es PASA.
ESTADOS = (PASA, FALLA, NO_APLICA, SIN_APLICABILIDAD, REQUERIDA, EVIDENCIA_SIN_RESOLVER,
           AMBIENTE_SIN_RESOLVER, FUERA_DE_QA, AUTORIDAD_SIN_RESOLVER, ALCANCE_SIN_RESOLVER,
           ARTEFACTO_SIN_RESOLVER, REEVALUAR, PARCIAL_SIN_RESOLVER, EDAD_SIN_CONTEXTO,
           MOTIVO_SIN_CLASIFICAR, EVIDENCIA_CAMBIADA, VALIDEZ_SIN_RESOLVER)

# -- lo que el registro declara ---------------------------------------------------

QA = "QA"
AMBIENTES_AJENOS = ("DEV", "HML", "PRD", "OTHER")
APROBADA = "APPROVED"
RECHAZADA = "REJECTED"
EXTERNA = "EXTERNAL_GCABA_SECURITY_AUTHORITY"
TOTAL = "FULL"

# Los cinco que identifican un artefacto sin ambiguedad. La rama y el repositorio NO estan.
INMUTABLES = ("commitSha", "buildId", "artifactDigest", "imageDigest", "releaseId")

# -- las relaciones con el artefacto ----------------------------------------------

EXACTA = "EXACT"
DESCENDIENTE = "DESCENDANT_WITH_NO_REASSESSMENT_TRIGGER"
SUPERADA = "SUPERSEDED_BY_CHANGE"
RELACION_SIN_RESOLVER = "UNRESOLVED"

# -- el Anexo V --------------------------------------------------------------------

REUSO_PERMITIDO = "REUSE_ALLOWED"
REEVALUACION = "REASSESSMENT_REQUIRED"

DESARROLLO_MAS_DE_20 = "DEVELOPMENT_OVER_20_DAYS"
DIAS = 20

# Los dieciocho que el paquete deriva del Anexo V. No hay un decimonoveno sin otra fuente.
MOTIVOS = (DESARROLLO_MAS_DE_20, "VULNERABILITY_REMEDIATION", "SECURITY_INCIDENT",
           "FUNCTIONALITY_CHANGED", "ENDPOINT_ADDED_OR_MODIFIED",
           "FRONTEND_OR_BACKEND_SECTION_REMOVED", "FORM_OR_API_PARAMETER_CHANGED",
           "EXTERNAL_INTEGRATION_CHANGED", "IFRAME_OR_EXTERNAL_EMBED_ADDED",
           "THIRD_PARTY_SCRIPT_ADDED", "SECURITY_POLICY_CHANGED", "ROLE_OR_PERMISSION_CHANGED",
           "DEPENDENCY_CHANGED", "INFRASTRUCTURE_MIGRATED", "COMMUNICATION_PROTOCOL_CHANGED",
           "FILE_UPLOAD_OR_DOWNLOAD_ADDED", "SENSITIVE_FLOW_CHANGED",
           "AUTHENTICATION_FLOW_CHANGED")

NO_ES_MOTIVO = "NOT_A_TRIGGER"
# 🔴 Quien puede decir que un cambio NO es motivo. Un modelo no esta: su clasificacion puede
# sumar un motivo, nunca sacarlo.
CLASIFICADORES_QUE_SUPRIMEN = ("DETERMINISTIC", "HUMAN")

FECHA = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")

# 🔴 Lo que entra por el caso y no pasa por el schema del registro se controla aca: un campo que no
# tiene la forma declarada no cuenta. Un cambio mal formado sigue siendo un cambio -no se puede
# suprimir- y queda sin clasificar; una cobertura parcial mal formada no cubre nada.


def canonico(valor):
    """El sujeto sin como esta escrito: sin acentos, caracteres de formato, caja ni separadores.

    Sirve para UNA cosa: reconocer que dos ids son el mismo sujeto escrito de otra forma, y fallar
    cerrado. Nunca para aceptar uno en lugar del otro.
    """
    if not isinstance(valor, str):
        return None
    descompuesto = unicodedata.normalize("NFKD", valor)
    return "".join(c for c in descompuesto
                   if unicodedata.category(c)[0] in ("L", "N")).casefold()


def _texto(valor):
    return isinstance(valor, str) and bool(valor.strip())


def _textos(valor):
    """La lista de textos, o `None` si no tiene esa forma. Un string suelto NO es una lista."""
    if isinstance(valor, list) and all(isinstance(v, str) for v in valor):
        return valor
    return None


def _cambio_bien_formado(cambio):
    return (isinstance(cambio, dict) and _texto(cambio.get("category"))
            and _texto(cambio.get("evidence"))
            and all(cambio.get(k) is None or isinstance(cambio.get(k), str)
                    for k in ("changeId", "classifiedBy", "date")))


# -- el registro ------------------------------------------------------------------

def cargar(desde=None):
    """El registro del proyecto. Vacio si no esta: sin aprobaciones, `SECURITY_APPROVAL_REQUIRED`."""
    ruta = _roster.ruta_de_regla(ARCHIVO, desde or __file__)
    if ruta is None:
        return {"version": "0.0", "approvals": []}
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def validar_schema(doc, desde=None):
    """Errores contra el contrato. Vacio es valido; `None` es que no se pudo validar."""
    ruta = rutas.localizar(("schemas", SCHEMA), desde or __file__)
    if ruta is None:
        return None
    from orquestacion import tools
    armador = tools._armador()
    if armador is None:
        return None
    with io.open(ruta, encoding="utf-8") as f:
        esquema = json.load(f)
    armador.controlar_soporte(esquema)
    return armador.validar(doc, esquema)


def aprobaciones(caso, desde=None):
    """(lista, problema). Las del caso si vienen; si no, las del registro instalado."""
    declarado = (caso or {}).get("registry")
    doc = declarado if declarado is not None else cargar(desde)
    if doc is None:
        return [], "el registro de aprobaciones no se pudo leer"
    errores = validar_schema(doc, desde)
    if errores is None:
        return [], "el registro de aprobaciones no se pudo validar: falta su schema o el validador"
    if errores:
        return [], "el registro de aprobaciones no valida: %s" % "; ".join(errores)
    return [a for a in (doc.get("approvals") or []) if isinstance(a, dict)], ""


# -- la huella --------------------------------------------------------------------

def huella(aprobacion):
    """`sha256` de la aprobacion serializada con claves ordenadas."""
    texto = json.dumps(aprobacion, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(texto.encode("utf-8")).hexdigest()


# -- el artefacto -----------------------------------------------------------------

def _inmutables(artefacto):
    a = artefacto if isinstance(artefacto, dict) else {}
    return {k: a[k] for k in INMUTABLES if isinstance(a.get(k), str) and a[k].strip()}


def relacion(aprobado, candidato, cambios, resolucion):
    """(relacion, motivo). Por identificadores inmutables, y la rama no cuenta."""
    de_la_aprobacion = _inmutables(aprobado)
    del_candidato = _inmutables(candidato)
    compartidos = sorted(set(de_la_aprobacion) & set(del_candidato))
    if not compartidos:
        return RELACION_SIN_RESOLVER, ("la aprobacion y el candidato no comparten ningun "
                                       "identificador inmutable; la rama y el repositorio no "
                                       "identifican un artefacto")
    distintos = [k for k in compartidos if de_la_aprobacion[k] != del_candidato[k]]
    if not distintos:
        return EXACTA, ""
    if len(distintos) < len(compartidos):
        return RELACION_SIN_RESOLVER, ("la aprobacion y el candidato coinciden en %s y difieren "
                                       "en %s: no es el mismo artefacto ni consta que no lo sea"
                                       % (", ".join(k for k in compartidos if k not in distintos),
                                          ", ".join(distintos)))
    c = cambios if isinstance(cambios, dict) else {}
    desde_, hasta = c.get("from") or {}, c.get("to") or {}
    encadena = (c.get("complete") is True
                and any(_inmutables(desde_).get(k) == de_la_aprobacion.get(k) for k in compartidos)
                and any(_inmutables(hasta).get(k) == del_candidato.get(k) for k in compartidos))
    if not encadena:
        return RELACION_SIN_RESOLVER, ("el candidato es otro artefacto y no hay un change set "
                                       "completo que vaya del aprobado a el")
    if resolucion["result"] == REEVALUACION:
        return SUPERADA, ""
    if resolucion["result"] == REUSO_PERMITIDO:
        return DESCENDIENTE, ""
    # La cadena consta y lo que falta es del Anexo V: `None` como motivo le cede la palabra al
    # resolvedor, que sabe decir QUE falta.
    return RELACION_SIN_RESOLVER, None


# -- el resolvedor del Anexo V ----------------------------------------------------

def _dia(texto):
    if not isinstance(texto, str) or not FECHA.match(texto):
        return None
    try:
        return date(int(texto[:4]), int(texto[5:7]), int(texto[8:]))
    except ValueError:
        return None


def revalidacion(fecha_del_assessment, contexto, otro_artefacto=False):
    """Si la aprobacion puede reusarse para el candidato, con TODOS los motivos que lo impiden.

    `contexto`:

        {"evaluationDate": "YYYY-MM-DD",
         "development": true | false | null,
         "complete": true,
         "changes": [{"changeId", "category", "classifiedBy", "date"?, "evidence"}]}

    🔴 `REUSE_ALLOWED` no es una aprobacion: dice que no se encontro motivo en evidencia completa.
    """
    ctx = contexto if isinstance(contexto, dict) else {}
    salida = {"source": dict(TRAZA_ANEXO_V), "triggers": [], "states": [], "ageDays": None}
    cambios = ctx.get("changes") if isinstance(ctx.get("changes"), list) else []
    if ctx.get("changes") is not None and not isinstance(ctx.get("changes"), list):
        salida["states"].append(MOTIVO_SIN_CLASIFICAR)
    inicio = _dia(fecha_del_assessment)

    for c in cambios:
        if not _cambio_bien_formado(c):
            salida["states"].append(MOTIVO_SIN_CLASIFICAR)
            continue
        categoria = c.get("category")
        cuando = _dia(c.get("date"))
        if cuando is not None and inicio is not None and cuando <= inicio:
            continue            # el assessment ya lo vio
        if categoria == NO_ES_MOTIVO:
            if c.get("classifiedBy") not in CLASIFICADORES_QUE_SUPRIMEN:
                salida["states"].append(MOTIVO_SIN_CLASIFICAR)
            continue
        if categoria in MOTIVOS and categoria != DESARROLLO_MAS_DE_20:
            salida["triggers"].append({"type": categoria, "changeId": c.get("changeId"),
                                       "evidence": c.get("evidence")})
        else:
            salida["states"].append(MOTIVO_SIN_CLASIFICAR)

    # 🔴 Los 20 dias van con el desarrollo. Un change set con cambios es desarrollo aunque no lo
    # diga, y uno que dice que no hubo y trae cambios se contradice.
    # 🔴 Y `otro_artefacto`: si el candidato es otro commit que el aprobado, HUBO desarrollo,
    # diga lo que diga el change set. Sin esto, declarar que no hubo y no listar cambios
    # esquivaba los 20 dias.
    desarrollo = ctx.get("development")
    # Por identidad: `1 == True` en Python, y un 1 no es un "si".
    if not any(desarrollo is v for v in (True, False, None)):
        # Un valor que no se reconoce -"yes", 1, una lista- es no saber si hubo desarrollo.
        salida["states"].append(EDAD_SIN_CONTEXTO)
        desarrollo = None
    if desarrollo is False and (cambios or otro_artefacto):
        salida["states"].append(EDAD_SIN_CONTEXTO)
    else:
        if desarrollo is None and (cambios or otro_artefacto):
            desarrollo = True
        hoy = _dia(ctx.get("evaluationDate"))
        edad = (hoy - inicio).days if (hoy and inicio) else None
        if edad is not None and edad < 0:
            # Una evaluacion anterior al assessment no es una edad: es una fecha equivocada.
            edad = None
        salida["ageDays"] = edad
        if desarrollo is True:
            if edad is None:
                salida["states"].append(EDAD_SIN_CONTEXTO)
            elif edad > DIAS:
                salida["triggers"].insert(0, {"type": DESARROLLO_MAS_DE_20, "changeId": None,
                                              "evidence": "%d dias desde el assessment" % edad})
        elif desarrollo is None:
            if edad is None or edad > DIAS:
                salida["states"].append(EDAD_SIN_CONTEXTO)

    if ctx.get("complete") is not True:
        salida["states"].append(VALIDEZ_SIN_RESOLVER)

    salida["triggers"].sort(key=lambda m: (MOTIVOS.index(m["type"]),
                                           json.dumps(m, sort_keys=True, default=str)))
    salida["states"] = sorted(set(salida["states"]))
    salida["required"] = True if salida["triggers"] else (None if salida["states"] else False)
    salida["result"] = (REEVALUACION if salida["triggers"] else
                        VALIDEZ_SIN_RESOLVER if salida["states"] else REUSO_PERMITIDO)
    return salida


# -- la evaluacion ----------------------------------------------------------------

def _valor_de_senal(senal):
    if isinstance(senal, dict):
        return senal.get("value") or _senales.SIN_RESOLVER
    if isinstance(senal, bool):
        return _senales.VERDADERA if senal else _senales.FALSA
    if senal in (_senales.VERDADERA, _senales.FALSA):
        return senal
    return _senales.SIN_RESOLVER


def _otro_artefacto(aprobado, candidato):
    """Si aprobado y candidato comparten algun identificador inmutable y todos difieren."""
    a, c = _inmutables(aprobado), _inmutables(candidato)
    compartidos = [k for k in a if k in c]
    return bool(compartidos) and all(a[k] != c[k] for k in compartidos)


def _autoridad_de_o2(autoridad, proyecto, aplicacion):
    """El `authorityId` que O2 resolvio PARA ESTE ALCANCE, o `None`.

    🔴 O2 en PASS para otro alcance no es procedencia de esto. Cuenta la CABEZA de la cadena de
    O2 -el alcance que O2 evaluo-, con su tipo: la aplicacion del candidato como `APPLICATION`, o
    su proyecto como `PROJECT`. Un eslabon de mas arriba no alcanza: la aplicacion hermana del
    mismo proyecto tambien lo tiene. Un resultado de O2 torcido no cuenta.
    """
    if not isinstance(autoridad, dict) or autoridad.get("state") != PASA:
        return None
    resuelta = autoridad.get("authority")
    cadena = autoridad.get("scopeChain")
    if not isinstance(resuelta, dict) or not _texto(resuelta.get("authorityId")):
        return None
    if not isinstance(cadena, list) or not cadena or not isinstance(cadena[0], dict):
        return None
    cabeza = (cadena[0].get("type"), cadena[0].get("value"))
    if cabeza not in (("APPLICATION", aplicacion), ("PROJECT", proyecto)):
        return None
    # Y ningun eslabon puede contradecir el proyecto del candidato.
    if any(isinstance(a, dict) and a.get("type") == "PROJECT" and a.get("value") != proyecto
           for a in cadena):
        return None
    return resuelta["authorityId"]


def _cobertura_parcial(aprobacion, candidato, coberturas):
    """Si hay una cobertura oficial explicita que ata esta aprobacion parcial al candidato."""
    propios = _inmutables((candidato or {}).get("artifact"))
    for c in (coberturas if isinstance(coberturas, list) else []):
        if not isinstance(c, dict) or c.get("approvalId") != aprobacion.get("approvalId"):
            continue
        if c.get("provenanceClass") != EXTERNA or not _texto(c.get("evidenceReference")):
            continue
        cubre = _inmutables(c.get("covers"))
        compartidos = [k for k in cubre if k in propios]
        # La misma regla que la relacion con el artefacto: al menos uno compartido, y ninguno
        # compartido que difiera. Un commit ajeno al lado de un release igual no cubre.
        if compartidos and all(propios[k] == cubre[k] for k in compartidos):
            return True
    return False


def evaluar(caso, senal=None, autoridad=None, desde=None):
    """El estado de C2 para un candidato a promocion.

    `caso`:

        {"candidate": {"projectId", "applicationId", "scope": [...],
                       "artifact": {"repository", "branch", <inmutables>}},
         "registry": {"version", "approvals": [...]},      # opcional: reemplaza el instalado
         "changeSet": {"from": {...}, "to": {...}, "complete": true},
         "reassessment": {<contexto del resolvedor>},
         "partialCoverage": [{"approvalId", "covers": {...}, "provenanceClass",
                              "evidenceReference"}],
         "previousDecision": {"approvalId", "fingerprint"},
         "internalResults": [...]}                            # se informan y no deciden

    `senal` es `securityHomologationPresent`; `autoridad` es el resultado de
    `security-control-authority-evidence` (O2) ya ejecutado.
    """
    entrada = caso if isinstance(caso, dict) else {}
    candidato = entrada.get("candidate") if isinstance(entrada.get("candidate"), dict) else {}
    salida = {"control": CONTROL, "rule": REGLA, "ruleKey": CLAVE, "source": dict(TRAZA),
              "supportingSource": dict(TRAZA_ANEXO_V), "signal": SENAL,
              "approvalEvidenceRef": None, "assessedArtifactRelation": RELACION_SIN_RESOLVER,
              "reassessment": {"required": None, "triggers": [], "result": None},
              "evidence": [], "issues": []}

    crudos = entrada.get("internalResults")
    internos = [i for i in (crudos if isinstance(crudos, list) else []) if isinstance(i, str)]
    if internos:
        salida["issues"].append("resultados internos informados y no considerados: %s"
                                % ", ".join(sorted(internos)))

    valor = _valor_de_senal(senal)
    salida["signalValue"] = valor
    if valor == _senales.SIN_RESOLVER:
        return _con(salida, SIN_APLICABILIDAD, "no se sabe si esta aplicacion o release esta "
                    "sujeta a homologacion de seguridad; que falte la aprobacion no lo decide")
    if valor == _senales.FALSA:
        return _con(salida, NO_APLICA, "la evidencia establece que C2 no aplica a esto")

    registro, problema = aprobaciones(entrada, desde)
    if problema:
        return _con(salida, EVIDENCIA_SIN_RESOLVER, problema)
    if not registro:
        return _con(salida, REQUERIDA, "no hay ninguna aprobacion oficial de seguridad registrada")

    proyecto, aplicacion = candidato.get("projectId"), candidato.get("applicationId")
    if not _texto(proyecto) or not _texto(aplicacion):
        return _con(salida, ALCANCE_SIN_RESOLVER, "el candidato no declara proyecto y aplicacion")
    propias = [a for a in registro
               if a.get("projectId") == proyecto and a.get("applicationId") == aplicacion]
    # 🔴 Una aprobacion que es del sujeto salvo por como esta escrito -un espacio, otra
    # grafia- puede ser la rechazada mas nueva. No se la trata como de otro: se falla cerrado.
    casi = [a for a in registro if a not in propias
            and canonico(a.get("projectId")) == canonico(proyecto)
            and canonico(a.get("applicationId")) == canonico(aplicacion)]
    if casi:
        return _con(salida, EVIDENCIA_SIN_RESOLVER,
                    "hay aprobaciones que parecen de este sujeto escritas de otra forma: %s"
                    % ", ".join(sorted(str(a.get("approvalId")) for a in casi)))
    if not propias:
        return _con(salida, FALLA, "las aprobaciones registradas son de otro proyecto o de otra "
                    "aplicacion: ninguna es de %s/%s" % (proyecto, aplicacion))

    # 🔴 Decide la mas reciente, y para saber cual es hacen falta TODAS las fechas. Una aprobacion
    # del sujeto con la fecha mal escrita puede ser la rechazada mas nueva: no se ordena por texto
    # ni se descarta, se falla cerrado.
    ilegibles = sorted(str(a.get("approvalId")) for a in propias
                       if _dia(a.get("assessmentDate")) is None)
    if ilegibles:
        return _con(salida, EVIDENCIA_SIN_RESOLVER,
                    "aprobaciones de este sujeto con la fecha del assessment ilegible: %s. Sin "
                    "todas las fechas no se sabe cual es la mas reciente" % ", ".join(ilegibles))
    ultima = max(_dia(a.get("assessmentDate")) for a in propias)
    empatadas = [a for a in propias if _dia(a.get("assessmentDate")) == ultima]
    ids = [a.get("approvalId") for a in propias]
    if len(empatadas) > 1 or len(ids) != len(set(ids)):
        # Dos del mismo dia, o dos con el mismo id: elegir por el orden de la entrada, o por el
        # orden de un texto, es elegir la que convenga.
        return _con(salida, EVIDENCIA_SIN_RESOLVER,
                    "hay mas de una aprobacion de este sujeto que podria ser la vigente, o ids "
                    "repetidos: no se elige entre ellas")
    elegida = empatadas[0]
    salida["approvalEvidenceRef"] = {"approvalId": elegida.get("approvalId"),
                                     "evidenceReference": elegida.get("evidenceReference"),
                                     "fingerprint": huella(elegida)}
    salida["evidence"] = sorted({elegida.get("evidenceReference")} |
                                {e for e in elegida.get("authorityEvidence") or []})

    resolucion = revalidacion(elegida.get("assessmentDate"), entrada.get("reassessment"),
                              otro_artefacto=_otro_artefacto(elegida.get("artifact"),
                                                             candidato.get("artifact")))
    salida["reassessment"] = {"required": resolucion["required"],
                              "triggers": resolucion["triggers"],
                              "result": resolucion["result"],
                              "states": resolucion["states"],
                              "ageDays": resolucion["ageDays"],
                              "source": resolucion["source"]}


    # -- la procedencia, atada a O2 --
    de_o2 = _autoridad_de_o2(autoridad, proyecto, aplicacion)
    if (elegida.get("provenanceClass") != EXTERNA or de_o2 is None
            or de_o2 not in (elegida.get("authorityEvidence") or [])):
        return _con(salida, AUTORIDAD_SIN_RESOLVER,
                    "la aprobacion no consta emitida por la autoridad del GCABA que O2 resolvio "
                    "para este alcance: hace falta procedencia externa, O2 en PASS y que la "
                    "aprobacion cite esa autoridad")

    # -- el ambiente --
    ambiente = elegida.get("environment")
    if ambiente in AMBIENTES_AJENOS:
        return _con(salida, FUERA_DE_QA, "la aprobacion es de %s; C2 la exige en QA" % ambiente)
    if ambiente != QA:
        return _con(salida, AMBIENTE_SIN_RESOLVER, "no consta en que ambiente se aprobo")

    # -- el estado --
    estado = elegida.get("status")
    if estado == RECHAZADA:
        return _con(salida, FALLA, "la autoridad rechazo el assessment en QA")
    if estado != APROBADA:
        return _con(salida, EVIDENCIA_SIN_RESOLVER, "la aprobacion no trae un estado oficial")

    # -- el alcance --
    cubierto = {s for s in elegida.get("scope") or [] if _texto(s)}
    pedido_crudo = _textos(candidato.get("scope")) or []
    pedido = set(pedido_crudo) if all(_texto(s) for s in pedido_crudo) else set()
    if not cubierto or not pedido or not pedido <= cubierto:
        return _con(salida, ALCANCE_SIN_RESOLVER,
                    "la aprobacion no cubre el alcance del candidato: aprobado %s, pedido %s"
                    % (sorted(cubierto) or "-", sorted(pedido) or "-"))

    # -- el artefacto y el Anexo V --
    rel, motivo = relacion(elegida.get("artifact"), candidato.get("artifact"),
                           entrada.get("changeSet"), resolucion)
    salida["assessedArtifactRelation"] = rel
    if rel == RELACION_SIN_RESOLVER and motivo is not None:
        return _con(salida, ARTEFACTO_SIN_RESOLVER, motivo)
    if resolucion["result"] == REEVALUACION:
        return _con(salida, REEVALUAR, "hay motivos del Anexo V desde el assessment: %s"
                    % ", ".join(m["type"] for m in resolucion["triggers"]))
    if resolucion["result"] != REUSO_PERMITIDO:
        return _con(salida, resolucion["states"][0],
                    "no se pudo establecer si la aprobacion sigue valiendo: %s"
                    % ", ".join(resolucion["states"]))

    # -- el parcial --
    if elegida.get("assessmentType") != TOTAL and not _cobertura_parcial(
            elegida, candidato, entrada.get("partialCoverage")):
        return _con(salida, PARCIAL_SIN_RESOLVER,
                    "el assessment no es total y ninguna cobertura oficial lo ata al candidato")

    # -- la huella --
    # 🔴 La huella anterior puede decir que NO. Si viene y no se puede leer, no se descarta: hay
    # que volver a evaluar.
    anterior = entrada.get("previousDecision")
    if anterior is not None:
        legible = (isinstance(anterior, dict) and _texto(anterior.get("approvalId"))
                   and _texto(anterior.get("fingerprint")))
        if not legible:
            return _con(salida, EVIDENCIA_CAMBIADA, "la decision anterior no se puede leer; hay "
                        "que volver a evaluar")
        if anterior["approvalId"] == elegida.get("approvalId") \
                and anterior["fingerprint"] != salida["approvalEvidenceRef"]["fingerprint"]:
            return _con(salida, EVIDENCIA_CAMBIADA, "la aprobacion cambio desde la decision "
                        "anterior; hay que volver a evaluar")

    return _con(salida, PASA, "")


def _con(salida, estado, motivo):
    salida["state"] = estado
    salida["reason"] = motivo
    salida["issues"].sort()
    return salida


def aprueba(resultado):
    """El unico estado que aprueba. Existe para que nadie tenga que acordarse de cual era."""
    return (resultado or {}).get("state") == PASA
