"""Check normativo: un archivo temporal se destruye al terminar el proposito que lo creo.

    source: ES0901 / 6.3 / 7.1 / D7

Contesta sobre **la estructura de la limpieza**, no sobre cuanto tarda. La oracion del estandar es
*"para los casos temporales la destruccion de los mismos debe ser en forma inmediata"*, y este
modulo la opera asi:

    se crea el temporal
    -> se usa para una operacion acotada
    -> la operacion termina o falla
    -> la limpieza corre como parte de ese mismo ciclo de vida

🔴 **No hay ningun numero adentro de este archivo, y no va a haber.** Ni segundos, ni minutos, ni
horas, ni un TTL. "Inmediato" es un momento -el fin del proposito- y no un umbral: un umbral
inventado se lee tan autoritativo como uno del estandar, y el estandar no da ninguno.

🔴 **Lo demorado no sustituye a la atadura, aunque exista.** Un cron diario, limpiar al arrancar,
confiar en el reinicio del contenedor, un TTL sin especificar, un procedimiento manual: al lado de
una limpieza atada al ciclo de vida son defensa en profundidad y no molestan; como unica limpieza de
un camino material son un incumplimiento.

🔴 **La tecnica no se exige.** `finally`, `defer`, `using`/`dispose`, un context manager, una
primitiva de archivo temporal con borrado determinista: son EJEMPLOS, y este modulo no ramifica por
ninguno. Se registra la que el proyecto declare y no cambia el resultado.

🔴 **La limpieza solo en el camino feliz no alcanza.** Los caminos materiales son cuatro -normal,
falla de validacion, falla del proveedor y cancelacion cuando el runtime permite limpiar- y la forma
mas comun del defecto es cubrir el primero y dejar los otros.

🔴 **Este modulo no borra ningun archivo** y no crea ninguna skill.
"""
import os
import sys

_CONTROLES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_CONTROLES, "lib") not in sys.path:
    sys.path.insert(0, os.path.join(_CONTROLES, "lib"))

import flujos as _f                              # noqa: E402

CONTROL = "temporary-file-cleanup"
TIPO = "CHECK"
REGLA = _f.REGLA
SENAL = _f.SENAL

TRAZA = dict(_f.TRAZA)

PASA = _f.PASA
FALLA = _f.FALLA
PARCIAL = _f.PARCIAL
NO_APLICA = _f.NO_APLICA
SIN_RESOLVER = _f.SIN_RESOLVER
SIN_COBERTURA = _f.SIN_COBERTURA
SIN_CICLO_DE_VIDA = "TEMPORARY_FILE_LIFECYCLE_UNRESOLVED"
SIN_CAMINOS = "CLEANUP_PATH_COVERAGE_UNRESOLVED"
SIN_OBJETIVO = _f.SIN_OBJETIVO

# Nueve, y el unico que aprueba es PASA.
ESTADOS = (PASA, FALLA, PARCIAL, NO_APLICA, SIN_RESOLVER, SIN_COBERTURA, SIN_CICLO_DE_VIDA,
           SIN_CAMINOS, SIN_OBJETIVO)

SIN_LIMPIEZA = "CLEANUP_MISSING"
LIMPIEZA_DEMORADA = "DELAYED_CLEANUP_NOT_IMMEDIATE"
SIN_TRAZA = "CLEANUP_TRACE_MISSING"
CAMINO_SIN_DECLARAR = "CLEANUP_PATH_UNDECLARED"
MECANISMO_SIN_RESOLVER = "CLEANUP_MECHANISM_UNRESOLVED"
CAMINO_DESCONOCIDO = "CLEANUP_PATH_UNKNOWN"
EVIDENCIA_HUERFANA = "EVIDENCE_REFERENCE_MISSING"
EVIDENCIA_DE_OTRA_CORRIDA = "EVIDENCE_OUT_OF_BUILD"

AGENTE = "dev-backend"
SKILL = "dev-storage"


def declarado(valor):
    """El texto declarado, sin los blancos. Vacio si no hay nada."""
    return _f.declarado(valor)


def temporales(caso):
    """Los flujos temporales materiales del inventario.

    Son los de clase temporal, mas cualquier flujo que declare un bloque temporal aunque su clase
    sea otra: un flujo sin clasificar que crea un temporal es el caso que no se puede omitir.
    """
    lista = []
    for f in _f.flujos(caso):
        if f.get("classification") in _f.TEMPORALES or isinstance(f.get("temporary"), dict):
            lista.append(f)
    return lista


def caminos_exigidos(flujo):
    """Los caminos que la limpieza de este flujo tiene que cubrir.

    Tres siempre, y la cancelacion cuando el proyecto declara que el runtime deja limpiar. Hay
    runtimes donde no deja, y exigirlo ahi seria exigir lo imposible — pero el default es NO
    exigirlo solo porque nadie lo declaro, no darlo por cubierto.
    """
    datos = (flujo or {}).get("temporary") or {}
    exigidos = list(_f.CAMINOS_SIEMPRE)
    if datos.get("runtimeCleanupPossible") is True:
        exigidos.append(_f.CAMINO_CANCELACION)
    return exigidos


def _evaluar_camino(camino, indice, build):
    """El estado de un camino de limpieza declarado, con su motivo."""
    nombre = declarado(camino.get("path"))
    mecanismos = [declarado(m) for m in camino.get("mechanisms") or [] if declarado(m)]
    salida = {"path": nombre, "mechanisms": mecanismos, "evidenceUsed": [], "issues": []}

    usadas, huerfanas, ajenas = _f.usables(camino.get("evidenceRefs"), indice, build)
    salida["evidenceUsed"] = [e.get("evidenceId") for e in usadas]
    if huerfanas:
        salida["issues"].append("%s: %s no existe" % (EVIDENCIA_HUERFANA, ", ".join(huerfanas)))
    if ajenas:
        salida["issues"].append("%s: %s es de otro build o de otro runtime"
                                % (EVIDENCIA_DE_OTRA_CORRIDA, ", ".join(ajenas)))

    if not mecanismos or _f.SIN_LIMPIEZA in mecanismos:
        salida.update({"state": FALLA, "reason": SIN_LIMPIEZA,
                       "detail": "el camino no limpia el temporal"})
        return salida

    # 🔴 La atadura al ciclo de vida se mira ANTES que lo demorado. Un camino que la tiene cumple
    # aunque encima haya un cron: eso es defensa en profundidad y el pedido la permite.
    if _f.CICLO_DE_VIDA not in mecanismos:
        demorados = [m for m in mecanismos if m in _f.DEMORADAS]
        if demorados:
            salida.update({"state": FALLA, "reason": LIMPIEZA_DEMORADA,
                           "detail": "la unica limpieza del camino es demorada, y una limpieza "
                                     "demorada no es la destruccion al terminar el proposito"})
            return salida
        salida.update({"state": SIN_CAMINOS, "reason": MECANISMO_SIN_RESOLVER,
                       "detail": "el camino no declara un mecanismo de limpieza de los "
                                 "declarados"})
        return salida

    if not _f.pruebas(usadas, _f.TRAZA_DE_LIMPIEZA):
        salida.update({"state": PARCIAL, "reason": SIN_TRAZA,
                       "detail": "el camino dice limpiar atado al ciclo de vida y no lo sostiene "
                                 "ninguna traza de esa limpieza"})
        return salida

    salida.update({"state": PASA, "reason": "",
                   "detail": "la limpieza corre como parte del ciclo de vida del temporal"})
    return salida


def _evaluar_flujo(flujo, indice, build):
    """El estado de un flujo temporal, con sus caminos."""
    datos = (flujo or {}).get("temporary") or {}
    salida = {"flowId": declarado(flujo.get("id")),
              "classification": flujo.get("classification"),
              "boundedPurpose": declarado(datos.get("boundedPurpose")),
              # La tecnica se registra y no se exige: ningun camino de este modulo la mira.
              "technique": declarado(datos.get("technique")),
              "paths": [], "issues": []}

    if not declarado(datos.get("boundedPurpose")):
        salida.update({"state": SIN_CICLO_DE_VIDA, "reason": SIN_CICLO_DE_VIDA,
                       "detail": "el flujo no declara para que operacion acotada se crea el "
                                 "temporal, y sin proposito acotado no hay un fin al que atar la "
                                 "destruccion"})
        return salida

    declarados = list(datos.get("cleanupPaths") or [])
    por_nombre = {}
    for c in declarados:
        por_nombre.setdefault(declarado(c.get("path")), []).append(c)

    desconocidos = sorted(n for n in por_nombre if n and n not in _f.CAMINOS)
    for n in desconocidos:
        salida["issues"].append("%s: %s no es uno de los caminos declarados"
                                % (CAMINO_DESCONOCIDO, n))

    exigidos = caminos_exigidos(flujo)
    salida["requiredPaths"] = list(exigidos)
    faltan = [n for n in exigidos if not por_nombre.get(n)]
    salida["missingPaths"] = faltan

    evaluados = []
    for nombre in exigidos:
        for c in por_nombre.get(nombre) or []:
            evaluados.append(_evaluar_camino(c, indice, build))
    salida["paths"] = evaluados
    for c in evaluados:
        salida["issues"].extend(c.get("issues") or [])

    estados = [c["state"] for c in evaluados]
    if FALLA in estados:
        salida.update({"state": FALLA, "reason": next(
            c["reason"] for c in evaluados if c["state"] == FALLA)})
        return salida
    if faltan:
        salida.update({"state": SIN_CAMINOS, "reason": CAMINO_SIN_DECLARAR,
                       "detail": "no se declaro la limpieza de %s, y la limpieza del camino feliz "
                                 "sola no alcanza cuando las fallas ordinarias pueden dejar "
                                 "archivos" % ", ".join(faltan)})
        return salida
    if SIN_CAMINOS in estados:
        salida.update({"state": SIN_CAMINOS, "reason": next(
            c["reason"] for c in evaluados if c["state"] == SIN_CAMINOS)})
        return salida
    if PARCIAL in estados:
        salida.update({"state": PARCIAL, "reason": next(
            c["reason"] for c in evaluados if c["state"] == PARCIAL)})
        return salida
    salida.update({"state": PASA, "reason": "",
                   "detail": "todos los caminos materiales destruyen el temporal como parte del "
                             "mismo ciclo de vida"})
    return salida


def evaluar(caso, senal=None, desde=None):
    """El estado de la obligacion de destruccion inmediata, con su motivo y su trazabilidad.

    `caso` es el mismo reporte que leen los otros dos checks de D7. Lo que este mira de cada
    flujo es su bloque `temporary`:

        {"id", "classification",
         "temporary": {"boundedPurpose", "runtimeCleanupPossible", "technique",
                       "cleanupPaths": [{"path", "mechanisms": [...], "evidenceRefs": [...]}]},
         "evidenceRefs": [...]}

    🔴 Para un build, un inventario y unos datos fijos, esto devuelve siempre lo mismo.
    """
    build = (caso or {}).get("build") or {}
    salida = {"control": CONTROL, "source": dict(TRAZA), "signal": SENAL,
              "build": dict(build), "flows": [], "issues": []}
    salida["signalValue"] = _f.valor_de_senal(senal)

    corte, extra = _f.aplicabilidad(caso, senal)
    if corte is not None:
        salida.update(extra)
        salida["state"] = corte
        return salida

    ok, motivo = _f.inventario_valido(caso)
    if not ok:
        salida.update({"state": SIN_COBERTURA, "reason": SIN_COBERTURA, "detail": motivo,
                       "temporaryFlows": []})
        return salida

    salida["fileFlows"] = {"source": caso["fileFlows"].get("source"),
                           "flows": [declarado(f.get("id")) for f in _f.flujos(caso)]}
    completa, motivo_cobertura = _f.clasificacion_completa(caso)

    materiales = temporales(caso)
    salida["temporaryFlows"] = [declarado(f.get("id")) for f in materiales]

    # 🔴 Sin temporales, la obligacion no tiene sujeto: NOT_APPLICABLE. Pero solo sobre una
    # clasificacion COMPLETA — decirlo sobre un inventario incompleto seria convertir "no
    # enumeramos los flujos" en "no hay temporales".
    if not materiales:
        if not completa:
            salida.update({"state": SIN_COBERTURA, "reason": SIN_COBERTURA,
                           "detail": motivo_cobertura})
            return salida
        salida.update({"state": NO_APLICA, "reason": "NO_TEMPORARY_FILE_FLOW",
                       "detail": "no hay flujos de archivo temporales en alcance"})
        return salida

    indice = _f.evidencias(caso)
    evaluados = [_evaluar_flujo(f, indice, build) for f in materiales]
    salida["flows"] = evaluados
    for f in evaluados:
        salida["issues"].extend(f.get("issues") or [])

    estados = [f["state"] for f in evaluados]
    if FALLA in estados:
        salida.update({"state": FALLA, "reason": next(
            f["reason"] for f in evaluados if f["state"] == FALLA)})
    elif not completa:
        salida.update({"state": SIN_COBERTURA, "reason": SIN_COBERTURA,
                       "detail": motivo_cobertura})
    elif SIN_CICLO_DE_VIDA in estados:
        salida.update({"state": SIN_CICLO_DE_VIDA, "reason": SIN_CICLO_DE_VIDA,
                       "detail": "hay temporales sin un proposito acotado declarado"})
    elif SIN_CAMINOS in estados:
        salida.update({"state": SIN_CAMINOS, "reason": next(
            f["reason"] for f in evaluados if f["state"] == SIN_CAMINOS)})
    elif PARCIAL in estados:
        salida.update({"state": PARCIAL, "reason": next(
            f["reason"] for f in evaluados if f["state"] == PARCIAL)})
    else:
        salida.update({"state": PASA, "reason": ""})
    return salida


def aprueba(resultado):
    """El unico estado que aprueba."""
    return (resultado or {}).get("state") == PASA


def skills_de_ejecucion(desde=None):
    """Quien ejecutaria la verificacion, resuelto contra el registro de agentes.

    🔴 Esto no crea skills y no las modifica.
    """
    from orquestacion import registro_agentes as reg
    pedidos = ((AGENTE, SKILL), (AGENTE, "dev-backend-implementation"),
               ("dev-quality", "dev-test-automation"))
    return [dict(reg.resolver_ruteo(agente, skill, None, desde or __file__),
                 requestedFor=CONTROL)
            for agente, skill in pedidos]
