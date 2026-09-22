"""Check normativo: la interfaz se adapta al dispositivo con el que se la mira.

    source: ES0901 / 6.3 / 7.1 / D4

Contesta sobre **lo que se renderiza**, no sobre lo que esta instalado. Que Bootstrap este en el
manifiesto, que el design system este aprobado, que haya media queries: todo eso se detecta en
segundos y ninguno dice si la aplicacion se ve bien en un telefono. Un check que los mire se pone
verde siempre.

🔴 **Esto no es un check del hook.** No corre en `PreToolUse`, no tiene presupuesto de latencia y
no devuelve las tres salidas del contrato de `comun/checks/`. Es un control normativo.

🔴 **Este modulo no renderiza nada.** No abre un navegador, no ejecuta un caso y no crea un
segundo framework de automatizacion. La corrida entra como dato -un reporte con su build, su
runtime y su resultado por viewport-, y quien la ejecute son las skills de calidad que ya estan
instaladas.

🔴 **La matriz de viewports no se inventa.** El estandar no define ningun breakpoint, ningun
modelo de dispositivo y ninguna cantidad de tamanos. Un default escrito aca se leeria normativo, y
la primera persona que lo viera asumiria que la norma pide esos numeros. Sin matriz declarada, con
su fuente: `VIEWPORT_MATRIX_UNRESOLVED`.

🔴 **El desktop no tapa al mobile.** Un `FAIL` en un viewport requerido manda sobre cualquier
cantidad de viewports que pasen, y un caso que no se ejecuto deja el resultado en `PARTIAL` aunque
todos los demas pasen.

🔴 **D4 no es accesibilidad ni es G1.** Que la interfaz se adapte al ancho de pantalla no dice
nada sobre lectores de pantalla, y que el design system este homologado es otra regla.
"""
import os
import sys

_BIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_BIN, "bin") not in sys.path:
    sys.path.insert(0, os.path.join(_BIN, "bin"))

from orquestacion import senales as _senales     # noqa: E402

CONTROL = "responsive-behavior"
TIPO = "CHECK"
REGLA = "D4"
SENAL = "frontendPresent"

TRAZA = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "D4"}

PASA = "PASS"
FALLA = "FAIL"
PARCIAL = "PARTIAL"
NO_APLICA = "NOT_APPLICABLE"
SIN_RESOLVER = "APPLICABILITY_UNRESOLVED"
SIN_MATRIZ = "VIEWPORT_MATRIX_UNRESOLVED"
SIN_OBJETIVO = "TEST_TARGET_UNAVAILABLE"

# Siete, y el unico que aprueba es PASA. Los otros seis dicen cosas distintas y ninguno cumple.
ESTADOS = (PASA, FALLA, PARCIAL, NO_APLICA, SIN_RESOLVER, SIN_MATRIZ, SIN_OBJETIVO)

# De donde puede salir una matriz de viewports. La lista dice que fuentes son defendibles; NO dice
# que tamanos, que es lo que el estandar no define y este harness no inventa.
FUENTES_DE_MATRIZ = ("PROJECT_UX_REQUIREMENT", "GCBA_DESIGN_SYSTEM_GUIDANCE",
                     "SUPPORTED_DEVICE_REQUIREMENT", "TEAM_APPROVED_TEST_PROFILE")

# Que prueba cada clase de evidencia. La particion es la razon de ser del check: las tres ultimas
# son evidencia de lo que HAY instalado, no de lo que se VE, y no sostienen nada. La captura y la
# confirmacion humana acompanan: una captura de desktop es exactamente como pasa un frontend roto
# en mobile.
EVIDENCIA_DE_CORRIDA = ("RENDERED_BEHAVIOR_RUN",)
EVIDENCIA_DE_APOYO = ("SCREENSHOT", "HUMAN_CONFIRMATION")
EVIDENCIA_QUE_NO_PRUEBA = ("REPOSITORY_DEPENDENCY", "STYLESHEET_CONFIGURATION",
                           "DESIGN_SYSTEM_USAGE", "AGENT_STATEMENT")

EJECUTADO = "EXECUTED"
NO_EJECUTADO = "NOT_EXECUTED"

MATERIAL = "MATERIAL"
MENOR = "MINOR"

SIN_EJECUTAR = "REQUIRED_VIEWPORT_NOT_EXECUTED"
DEFECTO_MATERIAL = "MATERIAL_RESPONSIVE_DEFECT"
MATERIALIDAD_SIN_DECLARAR = "DEFECT_MATERIALITY_UNRESOLVED"
SIN_EVIDENCIA_DE_CORRIDA = "RENDERED_EVIDENCE_MISSING"
EVIDENCIA_DE_OTRA_CORRIDA = "EVIDENCE_OUT_OF_BUILD"
EVIDENCIA_HUERFANA = "EVIDENCE_REFERENCE_MISSING"


def _valor_de_senal(senal):
    """El valor de `frontendPresent`, venga resuelto, crudo o como booleano viejo."""
    if isinstance(senal, dict):
        return senal.get("value") or _senales.SIN_RESOLVER
    if isinstance(senal, bool):
        return _senales.VERDADERA if senal else _senales.FALSA
    if senal in (_senales.VERDADERA, _senales.FALSA):
        return senal
    return _senales.SIN_RESOLVER


def matriz_valida(caso):
    """(ok, motivo) de la matriz de viewports declarada.

    Exige que haya viewports y que diga de donde salen. La fuente es parte del contrato: una
    matriz sin origen es un numero que alguien escribio, y de eso se trata todo esto.
    """
    matriz = (caso or {}).get("viewportMatrix") or {}
    viewports = matriz.get("viewports") or []
    if not viewports:
        return False, "no hay matriz de viewports declarada"
    if matriz.get("source") not in FUENTES_DE_MATRIZ:
        return False, ("la matriz no declara de donde sale, y una matriz sin origen es un "
                       "numero que alguien escribio")
    sin_id = [v for v in viewports if not v.get("id")]
    if sin_id:
        return False, "hay viewports sin identificar en la matriz"
    return True, ""


def _evidencias(caso):
    return {e.get("evidenceId"): e for e in (caso or {}).get("evidence") or []
            if e.get("evidenceId")}


def _de_esta_corrida(evidencia, build):
    """Si la evidencia pertenece al build y al runtime que se probaron.

    Una corrida sobre otro build es una corrida sobre otro sistema. Lo que no declara de cual es,
    es de este; lo que declara otro, no cuenta.
    """
    for campo in ("buildId", "runtime"):
        esperado = (build or {}).get("id" if campo == "buildId" else "runtime")
        declarado = evidencia.get(campo)
        if declarado and esperado and declarado != esperado:
            return False
    return True


def _evaluar_caso(resultado, evidencias, build):
    """El estado de un caso -un viewport por un flujo-, con su motivo y su evidencia."""
    salida = {"viewportId": resultado.get("viewportId", ""),
              "flowId": resultado.get("flowId", ""),
              "evidenceUsed": [], "issues": []}

    usadas, ajenas, huerfanas = [], [], []
    for ref in resultado.get("evidenceRefs") or []:
        e = evidencias.get(ref)
        if e is None:
            huerfanas.append(ref)
        elif not _de_esta_corrida(e, build):
            ajenas.append(ref)
        else:
            usadas.append(e)
    salida["evidenceUsed"] = [e.get("evidenceId") for e in usadas]
    if huerfanas:
        salida["issues"].append("%s: %s no existe"
                                % (EVIDENCIA_HUERFANA, ", ".join(sorted(huerfanas))))
    if ajenas:
        salida["issues"].append("%s: %s es de otro build o de otro runtime"
                                % (EVIDENCIA_DE_OTRA_CORRIDA, ", ".join(sorted(ajenas))))

    if resultado.get("execution") != EJECUTADO:
        salida.update({"state": PARCIAL, "reason": SIN_EJECUTAR,
                       "detail": "el caso requerido no se ejecuto, y lo que no se ejecuto no "
                                 "pasa por que el resto haya pasado"})
        return salida

    defectos = list(resultado.get("defects") or [])
    materiales = [d for d in defectos if d.get("materiality") == MATERIAL]
    sin_declarar = [d for d in defectos if d.get("materiality") not in (MATERIAL, MENOR)]

    if materiales:
        salida.update({"state": FALLA, "reason": DEFECTO_MATERIAL,
                       "defects": [d.get("id") or d.get("dimension") for d in materiales],
                       "detail": "hay un defecto material en un viewport requerido"})
        return salida

    if sin_declarar:
        # No se ablanda: elegir "habra sido menor" por defecto es como un FAIL se convierte en
        # una observacion sin que nadie lo decida.
        salida.update({"state": PARCIAL, "reason": MATERIALIDAD_SIN_DECLARAR,
                       "detail": "hay un defecto y nadie dijo cuanto pesa"})
        return salida

    de_corrida = [e for e in usadas if e.get("sourceType") in EVIDENCIA_DE_CORRIDA]
    if not de_corrida:
        salida.update({"state": PARCIAL, "reason": SIN_EVIDENCIA_DE_CORRIDA,
                       "detail": "el caso dice haber pasado y no lo sostiene ninguna evidencia "
                                 "de comportamiento renderizado: una captura sola, una "
                                 "dependencia instalada o una afirmacion no alcanzan"})
        return salida

    salida.update({"state": PASA, "reason": "",
                   "detail": "el caso corrio sin defecto material, con evidencia de la corrida"})
    return salida


def evaluar(caso, senal=None, desde=None):
    """El estado de D4 para una aplicacion, con su motivo, su evidencia y su trazabilidad.

    `caso` es el reporte de una corrida:

        {"application": {"id", "environment"},
         "build": {"id", "runtime"},
         "testTarget": {"available": bool},
         "viewportMatrix": {"source": ..., "viewports": [{"id", ...}]},
         "results": [{"viewportId", "flowId", "execution", "defects", "evidenceRefs"}],
         "evidence": [{"evidenceId", "sourceType", "reference", "claim", "buildId", "runtime"}]}

    🔴 Para un build, una matriz, un runtime y unos datos fijos, esto devuelve siempre lo mismo.
    """
    build = (caso or {}).get("build") or {}
    salida = {"control": CONTROL, "source": dict(TRAZA), "signal": SENAL,
              "build": dict(build), "cases": [], "issues": []}

    valor = _valor_de_senal(senal)
    salida["signalValue"] = valor

    if valor == _senales.SIN_RESOLVER:
        salida.update({"state": SIN_RESOLVER, "missingSignals": [SENAL],
                       "reason": "no se sabe si hay un frontend, y lo que no se sabe no se "
                                 "convierte en que no aplica"})
        return salida

    if valor == _senales.FALSA:
        salida.update({"state": NO_APLICA,
                       "reason": "no hay interfaz de usuario en alcance"})
        return salida

    objetivo = (caso or {}).get("testTarget") or {}
    if not objetivo.get("available"):
        salida.update({"state": SIN_OBJETIVO,
                       "reason": "no hubo donde correr la verificacion. No se ejecuto nada, y "
                                 "lo que no se ejecuto no pasa"})
        return salida

    ok, motivo = matriz_valida(caso)
    if not ok:
        salida.update({"state": SIN_MATRIZ, "reason": SIN_MATRIZ, "detail": motivo,
                       "requiredViewports": []})
        return salida

    matriz = caso["viewportMatrix"]
    salida["viewportMatrix"] = {"source": matriz.get("source"),
                                "viewports": [v.get("id") for v in matriz["viewports"]]}

    evidencias = _evidencias(caso)
    resultados = list((caso or {}).get("results") or [])
    por_viewport = {}
    for r in resultados:
        por_viewport.setdefault(r.get("viewportId"), []).append(r)

    # Un viewport de la matriz sin ningun resultado es un caso que no se ejecuto: se cuenta,
    # no se omite. Omitirlo seria dejar pasar un plan que probo solo lo que le convenia.
    casos = []
    for v in matriz["viewports"]:
        vid = v.get("id")
        if not por_viewport.get(vid):
            casos.append({"viewportId": vid, "flowId": "", "state": PARCIAL,
                          "reason": SIN_EJECUTAR, "evidenceUsed": [], "issues": [],
                          "detail": "el viewport esta en la matriz y no tiene ningun resultado"})
            continue
        for r in por_viewport[vid]:
            casos.append(_evaluar_caso(r, evidencias, build))

    # Un resultado de un viewport que la matriz no declara no cuenta para nada: no suma ni resta.
    salida["ignoredResults"] = [r.get("viewportId") for r in resultados
                                if r.get("viewportId") not in
                                {v.get("id") for v in matriz["viewports"]}]

    salida["cases"] = casos
    for c in casos:
        salida["issues"].extend(c.get("issues") or [])

    estados = [c["state"] for c in casos]
    if FALLA in estados:
        salida.update({"state": FALLA, "reason": DEFECTO_MATERIAL})
    elif estados and all(e == PASA for e in estados):
        salida.update({"state": PASA, "reason": ""})
    else:
        salida.update({"state": PARCIAL,
                       "reason": next((c["reason"] for c in casos if c["state"] != PASA),
                                      SIN_EJECUTAR)})
    return salida


def aprueba(resultado):
    """El unico estado que aprueba. Existe para que nadie tenga que acordarse de cual era."""
    return (resultado or {}).get("state") == PASA


def skills_de_ejecucion(desde=None):
    """Quien ejecutaria la verificacion, resuelto contra el registro de agentes.

    🔴 Esto no crea skills ni framework de automatizacion: dice cuales de las instaladas cubren
    la ejecucion. Si alguna no esta, se ve; no se inventa una.
    """
    from orquestacion import registro_agentes as reg
    pedidos = (("dev-frontend", "dev-responsive"),
               ("dev-quality", "dev-test-automation"),
               ("dev-quality", "dev-quality-validation"))
    return [dict(reg.resolver_ruteo(agente, skill, None, desde or __file__),
                 requestedFor=CONTROL)
            for agente, skill in pedidos]
