"""Check normativo: cada superficie entregada la gobierna un framework homologado.

    source: ES0901 / 6.3 / 7.1 / P1

Contesta sobre **qué ejecuta cada superficie que se entrega**, no sobre qué está instalado. Que el
framework este en el manifiesto, que exista un modulo manejado por el, que el README lo nombre: los
tres se detectan en segundos y ninguno dice que la aplicacion corra a traves de su modelo. Un check
que los mire se pone verde sobre una aplicacion vanilla con un paquete instalado al lado.

🔴 **P1 es ALWAYS y este check NUNCA contesta NOT_APPLICABLE.** No hay senal de aplicabilidad y no
se inventa una: Node y plataforma de negocio son RAMAS INTERNAS de evaluacion, no reglas normativas
nuevas. La unica forma de "esto no te toca" que existe en P1 es `NOT_RELEVANT`, y vive en el otro
check.

🔴 **Este modulo no homologa y no compara versiones.** Eso es G1, esta construido y tiene adentro el
parche dentro de la rama, la tolerancia a lo deprecado y la regla de los dos estandares. Aca se
REUSA el catalogo del Anexo II —el mismo archivo, no una copia— y se CONSUME el veredicto que G1
produjo, declarado como evidencia:

    sin veredicto de G1        ->  G1_EVIDENCE_REQUIRED
    con un veredicto que no es el homologado  ->  se conserva ese estado, y no pasa

Adentro de este archivo no hay -ni va a haber- una lista de tecnologias, un numero de version, una
comparacion de ramas ni una tolerancia. Si alguna vez hacen falta, lo que hay que hacer es llamar a
G1.

🔴 **Una superficie es lo que se entrega, y se declara.** Un script de build no es una aplicacion
vanilla y una herramienta auxiliar no se deduce: se declara, igual que la auxiliar de la cadena de
herramientas de G1. Deducirla seria la forma mas comoda de sacarse de encima cualquier superficie
incomoda.

🔴 **La plataforma de negocio es un CAMINO, no una exencion del proyecto.** Habilita una superficie
con su evidencia; las otras superficies del mismo proyecto siguen debiendo framework homologado.

🔴 **Este modulo no ejecuta nada.** La evidencia entra como dato y quien la produzca son las skills
que ya estan instaladas.
"""
import os
import sys

_BIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_BIN, "bin") not in sys.path:
    sys.path.insert(0, os.path.join(_BIN, "bin"))

from orquestacion import anexo2                  # noqa: E402

CONTROL = "framework-homologation"
TIPO = "CHECK"
REGLA = "P1"

TRAZA = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "P1"}

# Las dos clausulas derivadas que esta regla cubre. Se nombran para que el resultado diga de donde
# sale cada rama; NO son filas de la matriz y no se clasifican aparte.
CLAUSULAS = ("P1", "P1.node", "P1.plataformas")

PASA = "PASS"
FALLA = "FAIL"
PARCIAL = "PARTIAL"
SIN_FRAMEWORK = "FRAMEWORK_CONTEXT_UNRESOLVED"
SIN_CLASIFICAR = "DEVELOPMENT_SURFACE_CLASSIFICATION_UNRESOLVED"
SIN_GOBERNANZA = "BUSINESS_PLATFORM_GOVERNANCE_UNRESOLVED"
CONFLICTO_DE_PLATAFORMA = "BUSINESS_PLATFORM_STANDARD_CONFLICT"
FALTA_G1 = "G1_EVIDENCE_REQUIRED"
SIN_OBJETIVO = "TEST_TARGET_UNAVAILABLE"

# Nueve, y el unico que aprueba es PASA. 🔴 `NOT_APPLICABLE` NO esta: P1 es ALWAYS.
ESTADOS = (PASA, FALLA, PARCIAL, SIN_FRAMEWORK, SIN_CLASIFICAR, SIN_GOBERNANZA,
           CONFLICTO_DE_PLATAFORMA, FALTA_G1, SIN_OBJETIVO)

# -- las superficies -----------------------------------------------------------

GOBERNADA_POR_FRAMEWORK = "FRAMEWORK_GOVERNED"
GOBERNADA_POR_PLATAFORMA = "BUSINESS_PLATFORM_GOVERNED"
AUXILIAR = "AUXILIARY_TOOLING"
VANILLA = "VANILLA_APPLICATION"
CLASE_SIN_RESOLVER = "UNRESOLVED"

CLASES = (GOBERNADA_POR_FRAMEWORK, GOBERNADA_POR_PLATAFORMA, AUXILIAR, VANILLA,
          CLASE_SIN_RESOLVER)

# De donde puede salir el inventario de superficies entregadas.
FUENTES_DE_COBERTURA = ("PROJECT_ARCHITECTURE", "DELIVERY_INVENTORY", "IMPACT_ANALYSIS",
                        "BUILD_PIPELINE_INVENTORY", "TEAM_APPROVED_TEST_PROFILE")

# De donde puede salir un dato de identidad declarado: los lineamientos de una plataforma.
FUENTES_DE_IDENTIDAD = ("GCBA_NORMATIVE", "PLATFORM_VENDOR_GUIDELINE",
                        "ASI_INTEGRATION_CONTRACT", "PROJECT_INTEGRATION_AGREEMENT",
                        "HUMAN_CONFIRMATION")

# -- el uso de un componente de bajo nivel -------------------------------------

# La clausula del estandar es precisa: vale cuando esta integrado de forma INDIRECTA a traves del
# framework. El mismo paquete detras de un ORM y usado como la arquitectura de persistencia son dos
# cosas distintas, y cual de las dos es no se deduce del nombre.
POR_EL_FRAMEWORK = "THROUGH_FRAMEWORK"
REEMPLAZO_DIRECTO = "DIRECT_REPLACEMENT"
USO_SIN_RESOLVER = "UNRESOLVED"
USOS = (POR_EL_FRAMEWORK, REEMPLAZO_DIRECTO, USO_SIN_RESOLVER)

# -- la particion de evidencia -------------------------------------------------

GOBERNANZA = "FRAMEWORK_GOVERNANCE_TRACE"
EVIDENCIA_QUE_PRUEBA = (GOBERNANZA,)
EVIDENCIA_DE_APOYO = ("CODE_PATH_REVIEW", "HUMAN_CONFIRMATION")

# 🔴 Lo que esta instalado no prueba lo que ejecuta. Las cinco son evidencia de lo que HAY o de lo
# que alguien DICE, y ninguna sostiene nada.
EVIDENCIA_QUE_NO_PRUEBA = ("REPOSITORY_DEPENDENCY", "PACKAGE_MANIFEST_ENTRY",
                           "SINGLE_MANAGED_MODULE", "PROJECT_DOCUMENTATION", "AGENT_STATEMENT")

# -- los motivos ---------------------------------------------------------------

# 🔴 Los dos que el pedido lista como estados y aca son MOTIVOS de un FAIL: describen por que falla
# una superficie, no un resultado distinto de fallar. Una aplicacion con las dos cosas no esta en
# dos estados. Estan declarados, se alcanzan, se informan y ninguno aprueba.
RUNTIME_VANILLA = "VANILLA_RUNTIME_PATH_DETECTED"
BYPASS_DE_BAJO_NIVEL = "LOW_LEVEL_DIRECT_USE_BYPASS"

SIN_TRAZA = "FRAMEWORK_GOVERNANCE_UNPROVEN"
G1_NO_HOMOLOGADO = "G1_STATE_NOT_HOMOLOGATED"
G1_CONTRADICHO = "G1_STATE_CONTRADICTED_BY_CATALOG"
USO_DE_BAJO_NIVEL_SIN_RESOLVER = "LOW_LEVEL_USE_UNRESOLVED"
EVIDENCIA_HUERFANA = "EVIDENCE_REFERENCE_MISSING"
EVIDENCIA_DE_OTRA_CORRIDA = "EVIDENCE_OUT_OF_BUILD"

AGENTES = ("dev-architecture", "dev-devops")


def declarado(valor):
    """El texto declarado, sin los blancos. Vacio si no hay nada.

    🔴 Un espacio NO es un dato declarado, y se aplica a LOS DOS LADOS de cada comparacion. Es la
    leccion de D6.
    """
    return str(valor or "").strip()


# -- el inventario -------------------------------------------------------------

def inventario_valido(caso):
    """(ok, motivo) del inventario de superficies entregadas materiales."""
    inventario = (caso or {}).get("surfaces") or {}
    lista = inventario.get("items") or []
    if not lista:
        return False, "no hay un inventario de superficies entregadas declarado"
    if inventario.get("source") not in FUENTES_DE_COBERTURA:
        return False, ("el inventario no declara de donde sale, y un inventario sin origen no "
                       "dice cuantas superficies hay")
    if [s for s in lista if not declarado(s.get("id"))]:
        return False, "hay superficies sin identificar en el inventario"
    if [s for s in lista if s.get("kind") not in CLASES]:
        return False, "hay superficies sin una clase de las cinco declaradas"
    return True, ""


def superficies(caso, clases=None):
    """Las superficies del inventario, o solo las de las clases pedidas. TODAS las del inventario.

    🔴 No hay un segundo filtro. El inventario ES la lista de superficies entregadas —eso es lo que
    su `source` respalda—, asi que una etiqueta que el proyecto ponga sola no saca a ninguna.
    """
    lista = list(((caso or {}).get("surfaces") or {}).get("items") or [])
    if clases is None:
        return lista
    return [s for s in lista if s.get("kind") in clases]


def clasificacion_completa(caso):
    """(completa, motivo): sin superficies sin resolver, y declarada completa."""
    inventario = (caso or {}).get("surfaces") or {}
    sin_clase = [declarado(s.get("id")) for s in superficies(caso)
                 if s.get("kind") == CLASE_SIN_RESOLVER]
    if sin_clase:
        return False, "hay superficies sin clasificar: %s" % ", ".join(sorted(sin_clase))
    if inventario.get("complete") is False:
        return False, "el inventario de superficies se declara incompleto"
    return True, ""


def identidad_valida(bloque, que):
    """(ok, motivo) de un dato de identidad declarado: id, fuente de la lista y referencia."""
    datos = bloque or {}
    if not declarado(datos.get("id")):
        return False, "no hay %s declarado" % que
    if datos.get("source") not in FUENTES_DE_IDENTIDAD:
        return False, ("%s no declara de donde sale, y una identidad sin origen es un nombre que "
                       "alguien escribio" % que)
    if not declarado(datos.get("reference")):
        return False, "%s no dice donde esta declarado" % que
    return True, ""


# -- la evidencia --------------------------------------------------------------

def _evidencias(caso):
    return {e.get("evidenceId"): e for e in (caso or {}).get("evidence") or []
            if e.get("evidenceId")}


def _de_esta_corrida(evidencia, build):
    """Si la evidencia pertenece al build y al runtime que se probaron."""
    for campo, clave in (("buildId", "id"), ("runtime", "runtime")):
        esperado = (build or {}).get(clave)
        por_la_evidencia = evidencia.get(campo)
        if por_la_evidencia and esperado and por_la_evidencia != esperado:
            return False
    return True


def _usables(refs, indice, build):
    """(usadas, huerfanas, ajenas) de una lista de referencias a evidencia."""
    usadas, huerfanas, ajenas = [], [], []
    for ref in refs or []:
        e = indice.get(ref)
        if e is None:
            huerfanas.append(ref)
        elif not _de_esta_corrida(e, build):
            ajenas.append(ref)
        else:
            usadas.append(e)
    return usadas, sorted(huerfanas), sorted(ajenas)


# -- una superficie ------------------------------------------------------------

def _bajo_nivel(superficie):
    """(directos, sin_resolver) de los componentes de bajo nivel declarados."""
    directos, sin_resolver = [], []
    for c in superficie.get("lowLevelComponents") or []:
        cid = declarado(c.get("id"))
        uso = c.get("usage")
        if uso == REEMPLAZO_DIRECTO:
            directos.append(cid)
        elif uso != POR_EL_FRAMEWORK:
            # 🔴 Lo que no declara como se usa NO se da por integrado. La forma de uso no se
            # deduce del nombre del paquete: el mismo conector detras de un ORM y usado como la
            # arquitectura de persistencia son el mismo paquete y dos cosas distintas.
            sin_resolver.append(cid)
    return sorted(directos), sorted(sin_resolver)


def _evaluar_plataforma(superficie):
    """El estado de una superficie gobernada por una plataforma de negocio."""
    datos = superficie.get("platform") or {}
    salida = {"platform": declarado(datos.get("id"))}

    # 🔴 La contradiccion se mira primero: un lineamiento que contradice al estandar no se arregla
    # con mas evidencia de gobernanza, y no es lo mismo que no saber.
    if datos.get("conflictsWithStandard") is True:
        salida.update({"state": CONFLICTO_DE_PLATAFORMA, "reason": CONFLICTO_DE_PLATAFORMA,
                       "detail": "el lineamiento de la plataforma contradice a ES0901, y la "
                                 "clausula habilita la plataforma solo mientras no contradiga"})
        return salida

    if datos.get("structuredEnvironment") is not True:
        salida.update({"state": SIN_GOBERNANZA, "reason": SIN_GOBERNANZA,
                       "detail": "no se establecio que la plataforma tenga un entorno de "
                                 "desarrollo estructurado; el nombre del producto no alcanza"})
        return salida

    ok, motivo = identidad_valida(datos.get("guidelines"),
                                  "el lineamiento de desarrollo de la plataforma")
    if not ok:
        salida.update({"state": SIN_GOBERNANZA, "reason": SIN_GOBERNANZA, "detail": motivo})
        return salida

    if datos.get("customizationInside") is not True:
        salida.update({"state": SIN_GOBERNANZA, "reason": SIN_GOBERNANZA,
                       "detail": "no se establecio que la customizacion ocurra adentro del "
                                 "entorno gobernado"})
        return salida

    if datos.get("conflictsWithStandard") is not False:
        salida.update({"state": SIN_GOBERNANZA, "reason": SIN_GOBERNANZA,
                       "detail": "no se declaro si el lineamiento contradice a ES0901, y lo que "
                                 "no se declara no se da por compatible"})
        return salida

    salida.update({"state": PASA, "reason": "", "clause": CLAUSULAS[2],
                   "guidelines": declarado((datos.get("guidelines") or {}).get("id")),
                   "detail": "la superficie la gobierna una plataforma estructurada con sus "
                             "lineamientos citados y sin contradiccion declarada"})
    return salida


def _evaluar_framework(superficie, indice, build, catalogo, desde):
    """El estado de una superficie gobernada por un framework."""
    datos = superficie.get("framework") or {}
    tecnologia = declarado(datos.get("technology"))
    salida = {"technology": tecnologia, "g1State": declarado(datos.get("g1State"))}

    if not tecnologia:
        salida.update({"state": SIN_FRAMEWORK, "reason": SIN_FRAMEWORK,
                       "detail": "la superficie no dice con que framework se construye"})
        return salida

    # 🔴 El veredicto de G1 se CONSUME, no se vuelve a calcular. Sin el, esta superficie no se
    # puede resolver: la homologacion es de G1 y P1 no la reemplaza.
    estado_g1 = declarado(datos.get("g1State"))
    if not estado_g1 or not declarado(datos.get("g1Reference")):
        salida.update({"state": FALTA_G1, "reason": FALTA_G1,
                       "detail": "no hay un veredicto de G1 citado para esta tecnologia, y P1 no "
                                 "homologa: la pregunta es de G1"})
        return salida

    # Los componentes de bajo nivel se miran antes que la traza: un reemplazo directo es un
    # incumplimiento probado y no mejora porque ademas haya traza.
    directos, sin_resolver = _bajo_nivel(superficie)
    salida["lowLevelDirect"] = directos
    if directos:
        salida.update({"state": FALLA, "reason": BYPASS_DE_BAJO_NIVEL,
                       "detail": "un componente de bajo nivel se usa directamente en lugar del "
                                 "camino del framework: %s" % ", ".join(directos)})
        return salida

    if estado_g1 != anexo2.HOMOLOGADA:
        salida.update({"state": PARCIAL, "reason": G1_NO_HOMOLOGADO,
                       "detail": "G1 resolvio esta tecnologia como `%s`, y ese estado se conserva: "
                                 "el problema es de G1 y P1 no lo traduce" % estado_g1})
        return salida

    # El catalogo se reusa —es el mismo archivo de G1— para corroborar la identidad. No se compara
    # ninguna version acá: eso es de G1 y esta construido.
    if anexo2.buscar(tecnologia, catalogo, desde) is None:
        salida.update({"state": PARCIAL, "reason": G1_CONTRADICHO,
                       "detail": "el veredicto citado dice homologada y la tecnologia no figura "
                                 "en el catalogo: los dos datos no pueden ser ciertos"})
        return salida

    usadas, huerfanas, ajenas = _usables(superficie.get("evidenceRefs"), indice, build)
    salida["evidenceUsed"] = [e.get("evidenceId") for e in usadas]
    salida["issues"] = []
    if huerfanas:
        salida["issues"].append("%s: %s no existe" % (EVIDENCIA_HUERFANA, ", ".join(huerfanas)))
    if ajenas:
        salida["issues"].append("%s: %s es de otro build o de otro runtime"
                                % (EVIDENCIA_DE_OTRA_CORRIDA, ", ".join(ajenas)))

    trazas = [e for e in usadas if e.get("sourceType") in EVIDENCIA_QUE_PRUEBA]
    if not trazas:
        salida.update({"state": PARCIAL, "reason": SIN_TRAZA,
                       "detail": "el framework esta declarado y no hay traza de que gobierne la "
                                 "superficie: una dependencia, una entrada del manifiesto, un "
                                 "modulo gobernado o el README no alcanzan"})
        return salida

    # 🔴 La traza manda sobre lo que la superficie declare: el framework instalado con el runtime
    # material esquivandolo es la forma mas comun del defecto de P1.
    if [e for e in trazas if e.get("governs") is False]:
        salida.update({"state": FALLA, "reason": RUNTIME_VANILLA,
                       "detail": "la traza reporta que el runtime material no pasa por el modelo "
                                 "del framework, sin importar lo que la superficie declare"})
        return salida

    if [e for e in trazas if e.get("governs") is not True]:
        salida.update({"state": PARCIAL, "reason": SIN_TRAZA,
                       "detail": "la traza no declara si el framework gobierna la superficie, y "
                                 "lo que no se dice no se verifica"})
        return salida

    if sin_resolver:
        salida.update({"state": PARCIAL, "reason": USO_DE_BAJO_NIVEL_SIN_RESOLVER,
                       "detail": "hay componentes de bajo nivel que no declaran como se usan: %s"
                                 % ", ".join(sin_resolver)})
        return salida

    salida.update({"state": PASA, "reason": "", "clause": CLAUSULAS[0],
                   "detail": "un framework homologado por G1 gobierna la superficie entregada"})
    return salida


def _evaluar_superficie(superficie, indice, build, catalogo, desde):
    """El estado de una superficie entregada, con su motivo."""
    salida = {"surfaceId": declarado(superficie.get("id")), "kind": superficie.get("kind"),
              "issues": []}

    if superficie.get("kind") == AUXILIAR:
        # 🔴 Declarada auxiliar: no es una aplicacion entregada y no se convierte en vanilla por
        # estar escrita en lenguaje puro. Se DECLARA, no se deduce — es la misma doctrina que G1
        # fija para la auxiliar de la cadena de herramientas.
        salida.update({"state": PASA, "reason": "", "governed": False,
                       "detail": "herramienta auxiliar declarada: no es una superficie de "
                                 "aplicacion entregada"})
        return salida

    if superficie.get("kind") == VANILLA:
        salida.update({"state": FALLA, "reason": RUNTIME_VANILLA,
                       "detail": "una superficie entregada en lenguaje puro sin el soporte de su "
                                 "framework"})
        return salida

    if superficie.get("kind") == GOBERNADA_POR_PLATAFORMA:
        salida.update(_evaluar_plataforma(superficie))
        return salida

    salida.update(_evaluar_framework(superficie, indice, build, catalogo, desde))
    return salida


# -- el check ------------------------------------------------------------------

def evaluar(caso, desde=None, catalogo=None):
    """El estado de P1 para un proyecto, con su motivo, su evidencia y su trazabilidad.

    `caso` es el reporte de una revision:

        {"application": {"id", "environment"},
         "build": {"id", "runtime"},
         "testTarget": {"available": bool},
         "surfaces": {"source", "complete",
                      "items": [{"id", "kind",
                                 "framework": {"technology", "g1State", "g1Reference"},
                                 "platform": {"id", "structuredEnvironment", "guidelines",
                                              "customizationInside", "conflictsWithStandard"},
                                 "lowLevelComponents": [{"id", "usage"}],
                                 "evidenceRefs": [...]}]},
         "evidence": [{"evidenceId", "sourceType", "reference", "claim", "buildId", "runtime",
                       "governs"}]}

    🔴 No hay parametro de senal: P1 es ALWAYS. Y no hay estado `NOT_APPLICABLE` por el mismo
    motivo.

    🔴 Para un build, un inventario y unos datos fijos, esto devuelve siempre lo mismo.
    """
    build = (caso or {}).get("build") or {}
    salida = {"control": CONTROL, "source": dict(TRAZA), "rule": REGLA,
              "build": dict(build), "surfaces": [], "issues": []}

    if not ((caso or {}).get("testTarget") or {}).get("available"):
        salida.update({"state": SIN_OBJETIVO,
                       "reason": "no hubo donde correr la verificacion. No se ejecuto nada, y lo "
                                 "que no se ejecuto no pasa"})
        return salida

    ok, motivo = inventario_valido(caso)
    if not ok:
        salida.update({"state": SIN_CLASIFICAR, "reason": SIN_CLASIFICAR, "detail": motivo,
                       "governedSurfaces": []})
        return salida

    inventario = caso["surfaces"]
    salida["inventory"] = {"source": inventario.get("source"),
                           "surfaces": [declarado(s.get("id")) for s in superficies(caso)]}
    completa, motivo_cobertura = clasificacion_completa(caso)

    gobernadas = [s for s in superficies(caso) if s.get("kind") != CLASE_SIN_RESOLVER]
    salida["governedSurfaces"] = [declarado(s.get("id")) for s in gobernadas]

    doc = catalogo if catalogo is not None else anexo2.cargar(desde)
    indice = _evidencias(caso)
    evaluadas = [_evaluar_superficie(s, indice, build, doc, desde) for s in gobernadas]
    salida["surfaces"] = evaluadas
    for s in evaluadas:
        salida["issues"].extend(s.get("issues") or [])

    estados = [s["state"] for s in evaluadas]
    # El orden es de lo probado a lo que falta saber, y de lo grueso a lo fino.
    if FALLA in estados:
        salida.update({"state": FALLA, "reason": next(
            s["reason"] for s in evaluadas if s["state"] == FALLA)})
    elif CONFLICTO_DE_PLATAFORMA in estados:
        salida.update({"state": CONFLICTO_DE_PLATAFORMA, "reason": CONFLICTO_DE_PLATAFORMA})
    elif not completa:
        salida.update({"state": SIN_CLASIFICAR, "reason": SIN_CLASIFICAR,
                       "detail": motivo_cobertura})
    elif FALTA_G1 in estados:
        salida.update({"state": FALTA_G1, "reason": FALTA_G1})
    elif SIN_FRAMEWORK in estados:
        salida.update({"state": SIN_FRAMEWORK, "reason": SIN_FRAMEWORK})
    elif SIN_GOBERNANZA in estados:
        salida.update({"state": SIN_GOBERNANZA, "reason": SIN_GOBERNANZA})
    elif all(e == PASA for e in estados):
        salida.update({"state": PASA, "reason": ""})
    else:
        salida.update({"state": PARCIAL, "reason": next(
            s["reason"] for s in evaluadas if s["state"] != PASA)})
    return salida


def aprueba(resultado):
    """El unico estado que aprueba. Existe para que nadie tenga que acordarse de cual era."""
    return (resultado or {}).get("state") == PASA


def skills_de_ejecucion(desde=None):
    """Quien ejecutaria la verificacion, resuelto contra el registro de agentes.

    🔴 Esto no crea skills y no las modifica: dice cuales de las instaladas cubren la ejecucion.
    Los duenos de la regla son los que la matriz declara.
    """
    from orquestacion import registro_agentes as reg
    pedidos = ((AGENTES[0], "dev-architecture-analysis"),
               (AGENTES[1], "dev-devops-implementation"),
               ("dev-quality", "dev-quality-validation"))
    return [dict(reg.resolver_ruteo(agente, skill, None, desde or __file__),
                 requestedFor=CONTROL)
            for agente, skill in pedidos]
