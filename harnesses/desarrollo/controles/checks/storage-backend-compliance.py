"""Check normativo: los archivos persistentes van al storage estandar del GCBA.

    source: ES0901 / 6.3 / 7.1 / D7   ·   apoyo: 8.4 Sistema de Archivos

Contesta sobre **por donde pasa cada archivo que se queda**, no sobre que esta instalado. Que haya
una libreria del protocolo en el manifiesto, que exista una variable de ambiente con el nombre del
protocolo adentro, que este configurado algo que parece un almacen de objetos, que una subida
devuelva 200: todo eso se detecta en segundos y ninguno dice donde quedo el archivo. Un check que
los mire se pone verde siempre.

🔴 **Este modulo no sabe cual es el repositorio estandar del GCBA, y no lo inventa.** El estandar
nombra la tecnologia -*"La tecnologia actual esta basada en el protocolo S3"*- y NO nombra el
repositorio: dice *"el repositorio estandar para tal fin del GCABA"* y se detiene ahi. Adentro de
este archivo no hay -ni va a haber- un localizador de red, un nombre de infraestructura, una
credencial, una region, un tenant, un prefijo ni una politica de resguardo. La identidad entra como
DATO DECLARADO con su fuente citada, y lo que se compara son identificadores. Nunca un mecanismo.

    sin identidad declarada  ->  STANDARD_STORAGE_PROVIDER_UNRESOLVED
    sin contrato declarado   ->  STORAGE_INTEGRATION_CONTRACT_MISSING

Son dos huecos y no uno: "no se cual es el repositorio" y "se cual es y no se como se ve usarlo" se
arreglan preguntandole a personas distintas.

🔴 **El protocolo no es un proveedor.** Que el estandar nombre S3 es evidencia de protocolo:
hablarlo no identifica un repositorio, igual que hablar HTTP no identifica un sitio. Leerlo como el
contrato de un proveedor publico de nube es inventar la mitad que falta.

🔴 **A quien no persiste no se le exige un storage estandar.** La compuerta de identidad corre
DESPUES de saber si hay flujos persistentes. Al reves, una aplicacion que solo maneja temporales
saldria sin resolver por no tener una configuracion que no necesita.

🔴 **Un flujo que cumple no tapa otro que no**, y un FAIL probado manda tambien sobre un inventario
incompleto: un bypass probado es un bypass aunque falte enumerar flujos.

🔴 **Este modulo no escribe ni lee un archivo** y no crea ninguna skill. La corrida entra como dato
y quien la ejecute son las skills que ya estan instaladas.
"""
import os
import sys

_CONTROLES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_CONTROLES, "lib") not in sys.path:
    sys.path.insert(0, os.path.join(_CONTROLES, "lib"))

import flujos as _f                              # noqa: E402

CONTROL = "storage-backend-compliance"
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
SIN_PROVEEDOR = "STANDARD_STORAGE_PROVIDER_UNRESOLVED"
SIN_CONTRATO = "STORAGE_INTEGRATION_CONTRACT_MISSING"
SIN_OBJETIVO = _f.SIN_OBJETIVO

# Nueve, y el unico que aprueba es PASA. Los otros ocho dicen cosas distintas y ninguno cumple.
ESTADOS = (PASA, FALLA, PARCIAL, NO_APLICA, SIN_RESOLVER, SIN_COBERTURA, SIN_PROVEEDOR,
           SIN_CONTRATO, SIN_OBJETIVO)

# Los motivos por los que un flujo persistente no pasa.
NO_ES_EL_ESTANDAR = "PERSISTENT_PATH_NOT_STANDARD_STORAGE"
MECANISMO_ALTERNO = "ALTERNATE_STORAGE_MECHANISM"
MECANISMO_SIN_DECLARAR = "STORAGE_MECHANISM_UNDECLARED"
SIN_TRAZA = "PERSISTENCE_TRACE_MISSING"
TRAZA_SIN_MECANISMO = "TRACE_MECHANISM_UNDECLARED"
EVIDENCIA_HUERFANA = "EVIDENCE_REFERENCE_MISSING"
EVIDENCIA_DE_OTRA_CORRIDA = "EVIDENCE_OUT_OF_BUILD"
CLASIFICACION_CONTRADICHA = "FLOW_CLASSIFICATION_CONTRADICTED"

# -- las pautas de estructura de §8.4 ------------------------------------------

# Los dos numeros son CITAS del estandar, pag. 19 y pag. 20: *"No crear estructuras de carpetas
# que tengan mas de 20 niveles de profundidad"* y *"Evitar colocar una gran cantidad de objetos
# (mas de 100.000) en una sola carpeta"*. No se inventa ninguno y no se agrega un tercero.
LIMITE_DE_PROFUNDIDAD = 20
LIMITE_DE_OBJETOS = 100000

MEDIDO = "OBSERVED"
NO_MEDIDO = "NOT_MEASURED"
DESVIO = "DEVIATION"
DESVIO_DE_ESTRUCTURA = "STORAGE_STRUCTURE_GUIDANCE_DEVIATION"

CONCENTRADO = "CONCENTRATED"

AGENTE = "dev-backend"
SKILL = "dev-storage"


def declarado(valor):
    """El texto declarado, sin los blancos. Vacio si no hay nada."""
    return _f.declarado(valor)


def proveedor_valido(caso):
    """(ok, motivo) de la identidad del repositorio estandar del GCBA declarada."""
    return _f.identidad_valida((caso or {}).get("standardStorage"),
                               "la identidad del storage estandar del GCBA")


def contrato_valido(caso):
    """(ok, motivo) del contrato de integracion declarado.

    El contrato es lo que permite reconocer que un camino de persistencia usa ese mecanismo. Este
    modulo no mira que dice adentro -ahi es donde estarian los valores que no inventa-: mira que
    exista, que diga de donde sale y que este citado.
    """
    return _f.identidad_valida((caso or {}).get("integrationContract"),
                               "el contrato de integracion del storage estandar")


# -- la estructura de §8.4 -----------------------------------------------------

def _observacion(hecho, valor, limite=None, mayor_es_desvio=True):
    """Una observacion de estructura: medida, no medida, o apartada de la pauta.

    🔴 Lo que no esta medido queda NO_MEDIDO. Fabricar un conteo de objetos o una profundidad es
    peor que no tenerlos: un numero inventado se lee igual que uno medido.
    """
    if valor is None or valor == "":
        return {"fact": hecho, "state": NO_MEDIDO}
    salida = {"fact": hecho, "state": MEDIDO, "value": valor}
    if limite is not None and mayor_es_desvio and isinstance(valor, int) and valor > limite:
        salida.update({"state": DESVIO, "limit": limite})
    return salida


def estructura(caso):
    """Las observaciones de §8.4, con su estado. Evidencia del check, no un control nuevo."""
    datos = (caso or {}).get("storageStructure") or {}
    trafico = datos.get("trafficConcentration")
    observaciones = [
        _observacion("PLANNED_STRUCTURE", declarado(datos.get("plannedStructure")) or None),
        _observacion("FOLDER_DEPTH", datos.get("folderDepth"), LIMITE_DE_PROFUNDIDAD),
        _observacion("OBJECTS_PER_FOLDER", datos.get("objectsPerFolder"), LIMITE_DE_OBJETOS),
        _observacion("WIDTH_DEPTH_BALANCE", declarado(datos.get("widthDepthBalance")) or None),
    ]
    if not declarado(trafico):
        observaciones.append({"fact": "TRAFFIC_CONCENTRATION", "state": NO_MEDIDO})
    else:
        observaciones.append({"fact": "TRAFFIC_CONCENTRATION",
                              "state": DESVIO if trafico == CONCENTRADO else MEDIDO,
                              "value": trafico})
    return {"source": datos.get("source") or "", "observations": observaciones,
            "deviations": [o["fact"] for o in observaciones if o["state"] == DESVIO]}


# -- un flujo persistente ------------------------------------------------------

def _evaluar_flujo(flujo, indice, build, proveedor_id):
    """El estado de un flujo persistente, con su motivo y su evidencia."""
    salida = {"flowId": declarado(flujo.get("id")),
              "classification": flujo.get("classification"),
              "declaredMechanism": declarado(flujo.get("storageMechanism")),
              "evidenceUsed": [], "issues": []}

    usadas, huerfanas, ajenas = _f.usables(flujo.get("evidenceRefs"), indice, build)
    salida["evidenceUsed"] = [e.get("evidenceId") for e in usadas]
    if huerfanas:
        salida["issues"].append("%s: %s no existe"
                                % (EVIDENCIA_HUERFANA, ", ".join(huerfanas)))
    if ajenas:
        salida["issues"].append("%s: %s es de otro build o de otro runtime"
                                % (EVIDENCIA_DE_OTRA_CORRIDA, ", ".join(ajenas)))

    # 🔴 La clase decide primero. Un persistente local y un persistente en otro repositorio ya
    # son incumplimientos: que ademas tengan traza no los mejora, y preguntarles por su mecanismo
    # seria darles una forma de contestar que si.
    if flujo.get("classification") in (_f.LOCAL_PERMANENTE, _f.OTRO_REMOTO):
        salida.update({"state": FALLA, "reason": NO_ES_EL_ESTANDAR,
                       "detail": "el flujo persiste fuera del storage estandar del GCBA"})
        return salida

    por_el_flujo = declarado(flujo.get("storageMechanism"))
    if por_el_flujo and por_el_flujo != proveedor_id:
        salida.update({"state": FALLA, "reason": MECANISMO_ALTERNO,
                       "detail": "el flujo declara un mecanismo distinto del storage estandar "
                                 "declarado para este proyecto"})
        return salida

    if not por_el_flujo:
        salida.update({"state": PARCIAL, "reason": MECANISMO_SIN_DECLARAR,
                       "detail": "el flujo no dice por donde persiste, y lo que no se dice no se "
                                 "verifica"})
        return salida

    trazas = _f.pruebas(usadas, _f.TRAZA_DE_PERSISTENCIA)
    if not trazas:
        salida.update({"state": PARCIAL, "reason": SIN_TRAZA,
                       "detail": "el flujo dice persistir en el storage estandar y no lo sostiene "
                                 "ninguna traza del camino de persistencia: una dependencia "
                                 "instalada, el nombre de una variable, una configuracion, una "
                                 "llamada remota o una subida exitosa no alcanzan"})
        return salida

    # 🔴 La traza manda sobre lo que el flujo declare. Un cliente del storage estandar puede
    # existir mientras el camino gobernado lo esquiva, y ese es el defecto que el pedido nombra.
    ajenos = [e for e in trazas if declarado(e.get("mechanism"))
              and declarado(e.get("mechanism")) != proveedor_id]
    if ajenos:
        salida.update({"state": FALLA, "reason": MECANISMO_ALTERNO,
                       "detail": "la traza reporta que el flujo persistio por otro mecanismo, sin "
                                 "importar lo que declare el flujo"})
        return salida

    # Y la traza tiene que DECIR por donde persistio. Una traza muda no prueba nada.
    if [e for e in trazas if not declarado(e.get("mechanism"))]:
        salida.update({"state": PARCIAL, "reason": TRAZA_SIN_MECANISMO,
                       "detail": "la traza no declara por que mecanismo se persistio, y lo que no "
                                 "se dice no se verifica"})
        return salida

    salida.update({"state": PASA, "reason": "",
                   "detail": "el camino de persistencia gobernado pasa por el storage estandar "
                             "declarado"})
    return salida


# -- el check ------------------------------------------------------------------

def evaluar(caso, senal=None, desde=None):
    """El estado de la obligacion de storage estandar, con su motivo y su trazabilidad.

    `caso` es el reporte de una corrida:

        {"application": {"id", "environment"},
         "build": {"id", "runtime"},
         "testTarget": {"available": bool},
         "standardStorage": {"id", "source", "reference", "protocol"},
         "integrationContract": {"id", "source", "reference"},
         "fileFlows": {"source", "complete", "flows": [{"id", "classification",
                                                        "storageMechanism", "evidenceRefs"}]},
         "storageStructure": {"source", "plannedStructure", "folderDepth", "objectsPerFolder",
                              "widthDepthBalance", "trafficConcentration"},
         "evidence": [{"evidenceId", "sourceType", "reference", "claim", "buildId", "runtime",
                       "mechanism"}]}

    🔴 Para un build, una identidad, un inventario y unos datos fijos, esto devuelve siempre lo
    mismo.
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
                       "persistentFlows": []})
        return salida

    inventario = caso["fileFlows"]
    salida["fileFlows"] = {"source": inventario.get("source"),
                           "flows": [declarado(f.get("id")) for f in _f.flujos(caso)]}
    completa, motivo_cobertura = _f.clasificacion_completa(caso)

    persistentes = _f.flujos(caso, _f.PERSISTENTES)
    salida["persistentFlows"] = [declarado(f.get("id")) for f in persistentes]

    # 🔴 Un flujo que NO se declara persistente y trae una traza de persistencia de esta corrida
    # contradice al inventario: o el flujo persiste y esta mal clasificado, o la traza es de otro
    # flujo. No se sabe, y no saberlo no es un PASS.
    #
    # 🔴 Y se mira ACA, antes de concluir que no hay nada que persistir. Estaba despues, y por
    # ahi se escapaba el caso peor: un inventario declarado todo temporal con una traza de
    # persistencia adentro salia NOT_APPLICABLE, o sea "esta regla no te toca" sobre la evidencia
    # de que si te toca.
    indice = _f.evidencias(caso)
    contradichos = []
    for f in _f.flujos(caso):
        if f.get("classification") in _f.PERSISTENTES:
            continue
        usadas, _h, _a = _f.usables(f.get("evidenceRefs"), indice, build)
        if _f.pruebas(usadas, _f.TRAZA_DE_PERSISTENCIA):
            contradichos.append(declarado(f.get("id")))
    for fid in contradichos:
        salida["issues"].append(
            "%s: el flujo %s no se declara persistente y trae una traza de persistencia"
            % (CLASIFICACION_CONTRADICHA, fid))

    # 🔴 Sin flujos persistentes no hay nada que persistir al storage estandar, y eso NO es un
    # PASS: un PASS afirmaria que los archivos persistentes van al estandar sobre una aplicacion
    # que no persiste ninguno. Y la identidad NO se pide, que es el punto 28 del pedido: un flujo
    # solo temporal no falla por no persistir.
    if not persistentes:
        if contradichos:
            salida.update({"state": SIN_COBERTURA, "reason": CLASIFICACION_CONTRADICHA,
                           "detail": "el inventario no declara ningun flujo persistente y hay "
                                     "una traza de persistencia: o el inventario esta mal, o la "
                                     "traza es de otro flujo"})
            return salida
        if not completa:
            salida.update({"state": SIN_COBERTURA, "reason": SIN_COBERTURA,
                           "detail": motivo_cobertura})
            return salida
        salida.update({"state": NO_APLICA, "reason": "NO_PERSISTENT_FILE_FLOW",
                       "detail": "no hay flujos de archivo persistentes en alcance; los "
                                 "temporales los verifica temporary-file-cleanup"})
        return salida

    ok, motivo = proveedor_valido(caso)
    if not ok:
        salida.update({"state": SIN_PROVEEDOR, "reason": SIN_PROVEEDOR, "detail": motivo})
        return salida

    # El id que se informa es el normalizado: es el que el modulo usa para comparar, y publicar
    # uno distinto del que se compara es como se lee un FAIL que no se entiende.
    almacen = caso["standardStorage"]
    salida["standardStorage"] = {"id": declarado(almacen.get("id")),
                                 "source": almacen.get("source"),
                                 "protocol": declarado(almacen.get("protocol"))}

    ok, motivo = contrato_valido(caso)
    if not ok:
        salida.update({"state": SIN_CONTRATO, "reason": SIN_CONTRATO, "detail": motivo})
        return salida

    salida["integrationContract"] = {"id": declarado(caso["integrationContract"].get("id")),
                                     "source": caso["integrationContract"].get("source")}

    proveedor_id = declarado(almacen.get("id"))
    evaluados = [_evaluar_flujo(f, indice, build, proveedor_id) for f in persistentes]
    salida["flows"] = evaluados
    for f in evaluados:
        salida["issues"].extend(f.get("issues") or [])

    salida["storageStructure"] = estructura(caso)
    desvios = salida["storageStructure"]["deviations"]
    for hecho in desvios:
        salida["issues"].append("%s: %s se aparta de la pauta de §%s"
                                % (DESVIO_DE_ESTRUCTURA, hecho, _f.APOYO.split(" ")[0]))

    estados = [f["state"] for f in evaluados]
    if FALLA in estados:
        salida.update({"state": FALLA, "reason": next(
            f["reason"] for f in evaluados if f["state"] == FALLA)})
    elif contradichos:
        salida.update({"state": SIN_COBERTURA, "reason": CLASIFICACION_CONTRADICHA,
                       "detail": "hay un flujo con traza de persistencia que el inventario no "
                                 "declara persistente: o el inventario esta mal, o la traza es de "
                                 "otro flujo"})
    elif not completa:
        salida.update({"state": SIN_COBERTURA, "reason": SIN_COBERTURA,
                       "detail": motivo_cobertura})
    elif all(e == PASA for e in estados) and not desvios:
        salida.update({"state": PASA, "reason": ""})
    elif all(e == PASA for e in estados):
        salida.update({"state": PARCIAL, "reason": DESVIO_DE_ESTRUCTURA,
                       "detail": "todos los caminos de persistencia pasan por el storage estandar "
                                 "y una pauta medida de §%s se aparta" % _f.APOYO.split(" ")[0]})
    else:
        salida.update({"state": PARCIAL, "reason": next(
            f["reason"] for f in evaluados if f["state"] != PASA)})
    return salida


def aprueba(resultado):
    """El unico estado que aprueba. Existe para que nadie tenga que acordarse de cual era."""
    return (resultado or {}).get("state") == PASA


def skills_de_ejecucion(desde=None):
    """Quien ejecutaria la verificacion, resuelto contra el registro de agentes.

    🔴 Esto no crea skills y no las modifica: dice cuales de las instaladas cubren la ejecucion.
    El dueno normativo de la fila sigue siendo el agente que la matriz declara, y la seleccion de
    una skill es del registro de agentes. La obligacion normativa y el procedimiento tecnico
    quedan separados.
    """
    from orquestacion import registro_agentes as reg
    pedidos = ((AGENTE, SKILL), (AGENTE, "dev-backend-implementation"),
               ("dev-quality", "dev-test-automation"))
    return [dict(reg.resolver_ruteo(agente, skill, None, desde or __file__),
                 requestedFor=CONTROL)
            for agente, skill in pedidos]
