"""Check normativo: la visualizacion georreferenciada usa el Mapa del GCBA.

    source: ES0901 / 6.3 / 7.1 / D6

Contesta sobre **que dibuja cada vista**, no sobre que esta instalado. Que haya una libreria de
mapas en el manifiesto, que existan coordenadas en la base, que haya un componente que se llame
mapa, que se configure una capa: todo eso se detecta en segundos y ninguno dice con que mapa se
renderizo la pantalla. Un check que los mire se pone verde siempre.

🔴 **Este modulo no sabe cual es el Mapa del GCBA, y no lo inventa.** No hay un SDK, un endpoint,
un tile source, un layer id, una autenticacion, un CRS, una URL de ambiente ni un token adentro de
este archivo, y no los va a haber: ninguno esta en ningun extracto que este harness tenga. La
identidad del proveedor entra como DATO DECLARADO con su fuente citada, y lo que el check compara
son identificadores. Nunca un mecanismo.

    sin identidad declarada  ->  GCBA_MAP_PROVIDER_UNRESOLVED
    sin contrato declarado   ->  MAP_INTEGRATION_CONTRACT_MISSING

Son dos huecos y no uno: "no se cual es el mapa" y "se cual es y no se como se ve usarlo" se
arreglan preguntandole a personas distintas.

🔴 **Esto no es D5.** El parrafo de la pagina 19 lleva las dos reglas pegadas -normalizar
direcciones con API GEO, y mostrarlas en el mapa del GCBA- y son independientes. Que la aplicacion
llame a API GEO no dice nada sobre que mapa dibuja: `GEO_API_CALL` es evidencia INERTE para D6. Y
el resultado de este check lleva solo la tupla de D6, asi que nadie puede leer su PASS como
cumplimiento de D5.

🔴 **Una vista que cumple no tapa otra que no.** Un FAIL en cualquier vista gobernada manda sobre
cualquier cantidad de vistas que pasen. La forma tipica del defecto es justamente la mixta: la
pantalla principal con el mapa institucional y una pantalla vieja con otro.

🔴 **Este modulo no renderiza nada** y no crea ninguna skill. La corrida entra como dato y quien la
ejecute son las skills que ya estan instaladas.
"""
import os
import sys

_BIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_BIN, "bin") not in sys.path:
    sys.path.insert(0, os.path.join(_BIN, "bin"))

from orquestacion import senales as _senales     # noqa: E402

CONTROL = "gcba-map-usage"
TIPO = "CHECK"
REGLA = "D6"
SENAL = "georeferencedVisualizationPresent"

TRAZA = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "D6"}

# Las senales que NO hacen aplicable a D6, por mas que esten en TRUE. Un frontend no es un mapa, y
# un campo de direccion tampoco. Estan nombradas para que el error tenga nombre, no para usarlas.
SENALES_QUE_NO_SUSTITUYEN = ("frontendPresent", "frontendAddressInputPresent")

PASA = "PASS"
FALLA = "FAIL"
PARCIAL = "PARTIAL"
NO_APLICA = "NOT_APPLICABLE"
SIN_RESOLVER = "APPLICABILITY_UNRESOLVED"
SIN_COBERTURA = "MAP_VIEW_COVERAGE_UNRESOLVED"
SIN_PROVEEDOR = "GCBA_MAP_PROVIDER_UNRESOLVED"
SIN_CONTRATO = "MAP_INTEGRATION_CONTRACT_MISSING"
SIN_OBJETIVO = "TEST_TARGET_UNAVAILABLE"

# Nueve, y el unico que aprueba es PASA. Los otros ocho dicen cosas distintas y ninguno cumple.
ESTADOS = (PASA, FALLA, PARCIAL, NO_APLICA, SIN_RESOLVER, SIN_COBERTURA, SIN_PROVEEDOR,
           SIN_CONTRATO, SIN_OBJETIVO)

# De donde puede salir la identidad del Mapa del GCBA. La lista dice que fuentes son defendibles;
# NO dice cual es el mecanismo, que es lo que este harness no sabe.
FUENTES_DE_PROVEEDOR = ("GCBA_NORMATIVE", "GCBA_CATALOG_ENTRY", "ASI_INTEGRATION_CONTRACT",
                        "PROJECT_INTEGRATION_AGREEMENT", "HUMAN_CONFIRMATION")

# De donde puede salir el inventario de vistas. Una vista que nadie enumero es una vista que nadie
# verifico, y eso no se disimula contando solo las que alguien eligio mirar.
FUENTES_DE_COBERTURA = ("PROJECT_UX_REQUIREMENT", "PROJECT_ARCHITECTURE", "ROUTE_INVENTORY",
                        "TEAM_APPROVED_TEST_PROFILE")

# Que prueba cada clase de evidencia. La particion es la razon de ser del check: las seis ultimas
# son evidencia de lo que HAY, no de lo que se DIBUJO, y no sostienen nada.
EVIDENCIA_DE_CORRIDA = ("RENDERED_MAP_RUN",)
EVIDENCIA_DE_APOYO = ("SCREENSHOT", "HUMAN_CONFIRMATION")
EVIDENCIA_QUE_NO_PRUEBA = ("REPOSITORY_DEPENDENCY", "MAP_COMPONENT_PRESENT", "COORDINATE_DATA",
                           "GEO_API_CALL", "TILE_CONFIGURATION", "AGENT_STATEMENT")

EJECUTADO = "EXECUTED"
NO_EJECUTADO = "NOT_EXECUTED"

# El modo de la corrida. Una corrida mockeada sirve para armar el caso y no prueba que la
# aplicacion use el mapa institucional: se distingue en el resultado, no se descarta en silencio.
REAL = "REAL"
MOCKEADO = "MOCKED"
MODOS = (REAL, MOCKEADO)

PROVEEDOR_ALTERNO = "ALTERNATE_MAP_PROVIDER"
SIN_EJECUTAR = "GOVERNED_VIEW_NOT_EXECUTED"
SIN_EVIDENCIA_DE_CORRIDA = "RENDERED_EVIDENCE_MISSING"
EVIDENCIA_DE_OTRA_CORRIDA = "EVIDENCE_OUT_OF_BUILD"
EVIDENCIA_HUERFANA = "EVIDENCE_REFERENCE_MISSING"
EVIDENCIA_MOCKEADA = "MOCKED_EVIDENCE_ONLY"
PROVEEDOR_SIN_DECLARAR = "VIEW_PROVIDER_UNDECLARED"
CORRIDA_SIN_PROVEEDOR = "RUN_PROVIDER_UNDECLARED"

HUECO_DE_SKILL = "SPECIALIZED_SKILL_GAP"
AGENTE_DE_INTEGRACION = "dev-integration"
SKILL_DE_MAPA = "dev-gcba-map"


def _valor_de_senal(senal):
    """El valor de la senal, venga resuelta, cruda o como booleano viejo."""
    if isinstance(senal, dict):
        return senal.get("value") or _senales.SIN_RESOLVER
    if isinstance(senal, bool):
        return _senales.VERDADERA if senal else _senales.FALSA
    if senal in (_senales.VERDADERA, _senales.FALSA):
        return senal
    return _senales.SIN_RESOLVER


def declarado(valor):
    """El texto declarado, sin los blancos. Vacio si no hay nada.

    🔴 Un espacio NO es un dato declarado. La primera version comparaba contra la cadena vacia
    y `" "` es truthy, asi que un caso con toda la identidad en blancos -proveedor, contrato,
    id de vista- llegaba a PASS: D6 informaba cumplimiento con una identidad que no nombra nada
    y no cita en ningun lado. Todo campo de identidad de este modulo pasa por acá.
    """
    return str(valor or "").strip()


def proveedor_valido(caso):
    """(ok, motivo) de la identidad del Mapa del GCBA declarada.

    Exige un id, una fuente de la lista y una referencia. Sin los tres no identifica nada: un id
    sin fuente es un nombre que alguien escribio, y de eso se trata todo esto.
    """
    proveedor = (caso or {}).get("mapProvider") or {}
    if not declarado(proveedor.get("id")):
        return False, "no hay una identidad declarada del Mapa del GCBA"
    if proveedor.get("source") not in FUENTES_DE_PROVEEDOR:
        return False, ("la identidad no declara de donde sale, y una identidad sin origen es un "
                       "nombre que alguien escribio")
    if not declarado(proveedor.get("reference")):
        return False, "la identidad no dice donde esta declarada"
    return True, ""


def contrato_valido(caso):
    """(ok, motivo) del contrato de integracion declarado.

    El contrato es lo que permite reconocer que una vista usa ese mecanismo. Este modulo no mira
    que dice adentro -ahi es donde estarian los endpoints que no inventa-: mira que exista, que
    diga de donde sale y que este citado.
    """
    contrato = (caso or {}).get("integrationContract") or {}
    if not declarado(contrato.get("id")):
        return False, "no hay un contrato de integracion declarado para el Mapa del GCBA"
    if contrato.get("source") not in FUENTES_DE_PROVEEDOR:
        return False, "el contrato de integracion no declara de donde sale"
    if not declarado(contrato.get("reference")):
        return False, "el contrato de integracion no dice donde esta declarado"
    return True, ""


def cobertura_valida(caso):
    """(ok, motivo) del inventario de vistas georreferenciadas materiales."""
    cobertura = (caso or {}).get("mapViews") or {}
    vistas = cobertura.get("views") or []
    if not vistas:
        return False, "no hay un inventario de vistas georreferenciadas declarado"
    if cobertura.get("source") not in FUENTES_DE_COBERTURA:
        return False, ("el inventario no declara de donde sale, y un inventario sin origen no "
                       "dice cuantas vistas hay")
    sin_id = [v for v in vistas if not declarado(v.get("id"))]
    if sin_id:
        return False, "hay vistas sin identificar en el inventario"
    return True, ""


def gobernadas(caso):
    """Las vistas del inventario. TODAS.

    🔴 El inventario ES la lista de vistas materiales -eso es lo que el pedido pide enumerar, y
    lo que su `source` respalda-. Una version anterior aceptaba ademas un `materiality: MINOR`
    por vista y la sacaba de la verificacion: era un segundo filtro, declarado unilateralmente
    por el proyecto, sin fuente exigida y sin estar en ninguna parte del pedido ni de la spec.
    Con eso, una vista marcada menor dibujando con otro mapa daba PASS y no aparecia en ningun
    campo de la salida. La materialidad se decide al armar el inventario, no despues.
    """
    return list(((caso or {}).get("mapViews") or {}).get("views") or [])


def _evidencias(caso):
    return {e.get("evidenceId"): e for e in (caso or {}).get("evidence") or []
            if e.get("evidenceId")}


def _de_esta_corrida(evidencia, build):
    """Si la evidencia pertenece al build y al runtime que se probaron.

    Una corrida sobre otro build es una corrida sobre otro sistema. Lo que no declara de cual es,
    es de este; lo que declara otro, no cuenta.
    """
    # 🔴 La variable NO se llama `declarado`: ese es el nombre de la funcion del modulo, y
    # pisarla en un alcance donde algun dia se la necesite es exactamente la trampa que ya rompio
    # la comparacion de la corrida una vez. El nombre largo cuesta menos que volver a buscarlo.
    for campo, clave in (("buildId", "id"), ("runtime", "runtime")):
        esperado = (build or {}).get(clave)
        por_la_evidencia = evidencia.get(campo)
        if por_la_evidencia and esperado and por_la_evidencia != esperado:
            return False
    return True


def _proveedores_de_la_corrida(resultado, evidencias, build):
    """Con que proveedores dice la CORRIDA que se dibujo esa vista.

    Sirve para las vistas de afuera del inventario, donde no hay evaluacion por vista y la
    unica forma de ver un bypass probado es preguntarle a la evidencia.
    """
    vistos = set()
    for ref in resultado.get("evidenceRefs") or []:
        evidencia = evidencias.get(ref)
        if evidencia is None or not _de_esta_corrida(evidencia, build):
            continue
        if evidencia.get("sourceType") not in EVIDENCIA_DE_CORRIDA:
            continue
        if declarado(evidencia.get("provider")):
            vistos.add(declarado(evidencia.get("provider")))
    return vistos


def _evaluar_vista(resultado, evidencias, build, proveedor_id):
    """El estado de una vista gobernada, con su motivo y su evidencia."""
    salida = {"viewId": declarado(resultado.get("viewId")),
              "declaredProvider": declarado(resultado.get("provider")),
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

    # El nombre es largo a proposito: `declarado` es la funcion del modulo y pisarla acá
    # rompia la comparacion de la corrida sin que nada lo dijera.
    por_la_vista = declarado(resultado.get("provider"))

    # 🔴 El bypass se decide ANTES de mirar si se ejecuto. Una vista que declara otro proveedor ya
    # es un incumplimiento: que ademas no se haya corrido no lo mejora.
    if por_la_vista and por_la_vista != proveedor_id:
        salida.update({"state": FALLA, "reason": PROVEEDOR_ALTERNO,
                       "detail": "la vista declara un proveedor distinto del Mapa del GCBA "
                                 "declarado para este proyecto"})
        return salida

    if not por_la_vista:
        salida.update({"state": PARCIAL, "reason": PROVEEDOR_SIN_DECLARAR,
                       "detail": "la vista no dice con que se dibuja, y lo que no se dice no se "
                                 "verifica"})
        return salida

    if resultado.get("execution") != EJECUTADO:
        salida.update({"state": PARCIAL, "reason": SIN_EJECUTAR,
                       "detail": "la vista gobernada no se ejecuto, y lo que no se ejecuto no "
                                 "pasa por que el resto haya pasado"})
        return salida

    de_corrida = [e for e in usadas if e.get("sourceType") in EVIDENCIA_DE_CORRIDA]
    if not de_corrida:
        salida.update({"state": PARCIAL, "reason": SIN_EVIDENCIA_DE_CORRIDA,
                       "detail": "la vista dice usar el mapa institucional y no lo sostiene "
                                 "ninguna evidencia de renderizado: una dependencia instalada, "
                                 "una captura, unas coordenadas o una llamada a API GEO no "
                                 "alcanzan"})
        return salida

    # La corrida tiene que haber dibujado con el proveedor declarado, no solo existir.
    ajenos = [e for e in de_corrida if declarado(e.get("provider"))
              and declarado(e.get("provider")) != proveedor_id]
    if ajenos:
        salida.update({"state": FALLA, "reason": PROVEEDOR_ALTERNO,
                       "detail": "la corrida reporta que la vista se dibujo con otro proveedor, "
                                 "sin importar lo que declare la vista"})
        return salida

    # 🔴 Y tiene que DECIR con que dibujo. Una corrida muda no prueba nada, igual que una que no
    # declara su modo: la version anterior la dejaba pasar porque el filtro de ajenos se salteaba
    # cuando el campo venia vacio, asi que un PASS podia apoyarse en una corrida que nunca dijo
    # con que mapa se habia dibujado.
    if [e for e in de_corrida if not declarado(e.get("provider"))]:
        salida.update({"state": PARCIAL, "reason": CORRIDA_SIN_PROVEEDOR,
                       "detail": "la corrida no declara con que proveedor se dibujo, y lo que no "
                                 "se dice no se verifica"})
        return salida

    reales = [e for e in de_corrida if e.get("mode") == REAL]
    if not reales:
        salida.update({"state": PARCIAL, "reason": EVIDENCIA_MOCKEADA,
                       "detail": "la unica evidencia de corrida esta declarada como mockeada: "
                                 "documenta el caso y no prueba que la aplicacion use el mapa "
                                 "institucional"})
        return salida

    salida.update({"state": PASA, "reason": "",
                   "detail": "la vista corrio de verdad y dibujo con el Mapa del GCBA declarado"})
    return salida


def evaluar(caso, senal=None, desde=None):
    """El estado de D6 para una aplicacion, con su motivo, su evidencia y su trazabilidad.

    `caso` es el reporte de una corrida:

        {"application": {"id", "environment"},
         "build": {"id", "runtime"},
         "testTarget": {"available": bool},
         "mapProvider": {"id", "source", "reference"},
         "integrationContract": {"id", "source", "reference"},
         "mapViews": {"source", "views": [{"id", "materiality"}]},
         "results": [{"viewId", "provider", "execution", "evidenceRefs"}],
         "evidence": [{"evidenceId", "sourceType", "reference", "claim",
                       "buildId", "runtime", "provider", "mode"}]}

    🔴 Para un build, un proveedor, un inventario y unos datos fijos, esto devuelve siempre lo
    mismo.
    """
    build = (caso or {}).get("build") or {}
    salida = {"control": CONTROL, "source": dict(TRAZA), "signal": SENAL,
              "build": dict(build), "views": [], "issues": []}

    valor = _valor_de_senal(senal)
    salida["signalValue"] = valor

    if valor == _senales.SIN_RESOLVER:
        salida.update({"state": SIN_RESOLVER, "missingSignals": [SENAL],
                       "reason": "no se sabe si hay una visualizacion georreferenciada, y lo que "
                                 "no se sabe no se convierte en que no aplica"})
        return salida

    if valor == _senales.FALSA:
        salida.update({"state": NO_APLICA,
                       "reason": "no hay visualizacion georreferenciada en alcance"})
        return salida

    objetivo = (caso or {}).get("testTarget") or {}
    if not objetivo.get("available"):
        salida.update({"state": SIN_OBJETIVO,
                       "reason": "no hubo donde correr la verificacion. No se ejecuto nada, y lo "
                                 "que no se ejecuto no pasa"})
        return salida

    ok, motivo = proveedor_valido(caso)
    if not ok:
        salida.update({"state": SIN_PROVEEDOR, "reason": SIN_PROVEEDOR, "detail": motivo})
        return salida

    proveedor = caso["mapProvider"]
    # El id que se informa es el normalizado: es el que el modulo usa para comparar, y
    # publicar uno distinto del que se compara es como se lee un FAIL que no se entiende.
    salida["mapProvider"] = {"id": declarado(proveedor.get("id")),
                             "source": proveedor.get("source")}

    ok, motivo = contrato_valido(caso)
    if not ok:
        salida.update({"state": SIN_CONTRATO, "reason": SIN_CONTRATO, "detail": motivo})
        return salida

    salida["integrationContract"] = {"id": declarado(caso["integrationContract"].get("id")),
                                     "source": caso["integrationContract"].get("source")}

    ok, motivo = cobertura_valida(caso)
    if not ok:
        salida.update({"state": SIN_COBERTURA, "reason": SIN_COBERTURA, "detail": motivo,
                       "governedViews": []})
        return salida

    inventario = gobernadas(caso)
    salida["governedViews"] = [declarado(v.get("id")) for v in inventario]
    salida["mapViews"] = {"source": caso["mapViews"].get("source"),
                          "views": [declarado(v.get("id"))
                                    for v in caso["mapViews"]["views"]]}

    # 🔴 `declarado` se aplica a LOS DOS LADOS de cada comparacion, siempre. Normalizar un solo
    # lado es peor que no normalizar ninguno: con el id del proveedor en crudo acá y normalizado
    # en la vista, una identidad con padding que `proveedor_valido` acepta no podia igualar nunca
    # a la que la vista declara, y un caso correcto salia FAIL por proveedor alterno. Y con el
    # cruce de vistas a medias -`ids` normalizado, `por_vista` en crudo- una vista con el id
    # padeado se caia por el agujero del medio: no entraba como gobernada ni como de afuera, y un
    # bypass probado se informaba como GOVERNED_VIEW_NOT_EXECUTED.
    proveedor_id = declarado(proveedor.get("id"))
    evidencias = _evidencias(caso)
    resultados = list((caso or {}).get("results") or [])
    por_vista = {}
    for r in resultados:
        por_vista.setdefault(declarado(r.get("viewId")), []).append(r)

    # Una vista del inventario sin ningun resultado es una vista que no se verifico: se cuenta,
    # no se omite. Omitirla seria dejar pasar una corrida que probo solo lo que le convenia.
    vistas = []
    for v in inventario:
        vid = declarado(v.get("id"))
        if not por_vista.get(vid):
            vistas.append({"viewId": vid, "declaredProvider": "", "state": PARCIAL,
                           "reason": SIN_EJECUTAR, "evidenceUsed": [], "issues": [],
                           "detail": "la vista esta en el inventario y no tiene ningun resultado"})
            continue
        for r in por_vista[vid]:
            vistas.append(_evaluar_vista(r, evidencias, build, proveedor_id))

    # Un resultado de una vista que el inventario no declara no cuenta como vista gobernada.
    # 🔴 Pero si declara OTRO proveedor, el inventario deja de ser creible y el resultado no
    # puede ser PASA: o falta una vista gobernada, o la vista no lo es y nadie lo dijo. No se
    # sabe, y eso es exactamente MAP_VIEW_COVERAGE_UNRESOLVED. Dejarlo en PASA con un aviso en
    # una lista es, literalmente, un mapa que cumple tapando otro que no.
    # 🔴 Y se mira TAMBIEN la corrida, no solo lo que la vista declara. La version anterior
    # miraba unicamente `provider` del resultado, asi que dejar ese campo vacio desarmaba la
    # guarda: una vista de afuera con el campo en blanco y una corrida real que reportaba otro
    # mapa terminaba en PASS, sin un solo aviso. Es la misma doctrina que fija E-19 -la corrida
    # manda sobre lo declarado-, que hasta acá solo valia para las vistas gobernadas.
    ids = {declarado(v.get("id")) for v in caso["mapViews"]["views"]}
    afuera = [r for r in resultados if declarado(r.get("viewId")) not in ids]
    salida["ignoredResults"] = [declarado(r.get("viewId")) for r in afuera]
    alternos_afuera = []
    for r in afuera:
        candidatos = ({declarado(r.get("provider"))}
                      | _proveedores_de_la_corrida(r, evidencias, build))
        candidatos.discard("")
        if candidatos - {proveedor_id}:
            alternos_afuera.append(declarado(r.get("viewId")))
    for vid in alternos_afuera:
        salida["issues"].append(
            "%s: la vista %s no esta en el inventario y declara otro proveedor"
            % (SIN_COBERTURA, vid))

    salida["views"] = vistas
    for v in vistas:
        salida["issues"].extend(v.get("issues") or [])

    estados = [v["state"] for v in vistas]
    if FALLA in estados:
        salida.update({"state": FALLA, "reason": PROVEEDOR_ALTERNO})
    elif alternos_afuera:
        salida.update({"state": SIN_COBERTURA, "reason": SIN_COBERTURA,
                       "detail": "hay una vista fuera del inventario dibujando con otro "
                                 "proveedor: o el inventario esta incompleto, o esa vista no "
                                 "esta gobernada y nadie lo declaro"})
    elif estados and all(e == PASA for e in estados):
        salida.update({"state": PASA, "reason": ""})
    else:
        salida.update({"state": PARCIAL,
                       "reason": next((v["reason"] for v in vistas if v["state"] != PASA),
                                      SIN_EJECUTAR)})
    return salida


def aprueba(resultado):
    """El unico estado que aprueba. Existe para que nadie tenga que acordarse de cual era."""
    return (resultado or {}).get("state") == PASA


def remediacion(resultado, desde=None):
    """Que hace falta para arreglarlo, cuando arreglarlo exige saber como se integra el mapa.

    El estado sale del registro de agentes -`SPECIALIZED_SKILL_GAP` ya existe y no se inventa
    otro-. 🔴 Que el hueco este nombrado NO hace cumplir a D6: el control sigue sin pasar y esto
    dice por que no se puede cerrar hoy.

    🔴 Esto no crea la skill del mapa, no la instala y no la completa con informacion inventada.
    El pedido de D6 lo prohibe explicitamente, y el mecanismo tampoco se sabe.
    """
    estado = (resultado or {}).get("state")
    if estado not in (FALLA, PARCIAL, SIN_PROVEEDOR, SIN_CONTRATO):
        return None

    from orquestacion import registro_agentes as reg
    ruteo = reg.resolver_ruteo(AGENTE_DE_INTEGRACION, SKILL_DE_MAPA, None, desde or __file__)
    if ruteo.get("routable"):
        return None

    return {"control": CONTROL, "source": dict(TRAZA), "state": HUECO_DE_SKILL,
            "skill": SKILL_DE_MAPA, "agent": AGENTE_DE_INTEGRACION,
            "skillValidation": ruteo.get("result"),
            "compliant": False,
            "reason": "la remediacion de D6 exige conocimiento especifico de como se integra el "
                      "Mapa del GCBA, y esa skill no esta instalada. El hueco queda visible y D6 "
                      "sigue sin cumplir"}


def skills_de_ejecucion(desde=None):
    """Quien ejecutaria la verificacion, resuelto contra el registro de agentes.

    🔴 Esto no crea skills: dice cuales de las instaladas cubren la ejecucion. Si alguna no esta,
    se ve; no se inventa una.
    """
    from orquestacion import registro_agentes as reg
    pedidos = ((AGENTE_DE_INTEGRACION, "dev-external-integration"),
               ("dev-frontend", "dev-frontend-implementation"),
               ("dev-quality", "dev-test-automation"))
    return [dict(reg.resolver_ruteo(agente, skill, None, desde or __file__),
                 requestedFor=CONTROL)
            for agente, skill in pedidos]
