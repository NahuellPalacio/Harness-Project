"""Check normativo: el almacenamiento local no se usa como repositorio permanente.

    source: ES0901 / 6.3 / 7.1 / D7

Contesta sobre **el ciclo de vida de cada escritura local**, no sobre como se llama la carpeta. La
oracion del estandar es *"no esta permitido guardar en forma permanente archivos en forma local"*, y
la palabra que decide es **permanente**: un temporal local no esta prohibido, esta gobernado por la
otra obligacion.

🔴 **El nombre del path no clasifica nada.** Que una carpeta se llame `tmp` no prueba un ciclo de
vida temporal, y que la aplicacion corra en un contenedor no prueba que el archivo se vaya. Las dos
son suposiciones con formato de evidencia, y las dos estan declaradas inertes. Una escritura cuya
unica evidencia es de esa clase queda `LOCAL_STORAGE_LIFECYCLE_UNRESOLVED`, no temporal.

🔴 **Siete datos, no uno.** Para cada escritura local se establecen el path o adaptador, el
proposito, donde se crea, donde se consume, donde se limpia, cuanto se espera que viva y como se
comporta. "Es temporal" sin consumo ni limpieza declarados es una afirmacion, no un ciclo de vida.

🔴 **Una prohibicion sin sujeto esta cumplida.** Sin escrituras locales materiales, sobre una
clasificacion completa, este check PASA -no queda inaplicable-: la obligacion es no usar el local
como repositorio, y no usarlo es cumplirla. Las otras dos obligaciones de D7 son condicionales y
por eso contestan `NOT_APPLICABLE` cuando les falta el sujeto.

🔴 **Este modulo no escribe ni borra un archivo** y no crea ninguna skill.
"""
import os
import sys

_CONTROLES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_CONTROLES, "lib") not in sys.path:
    sys.path.insert(0, os.path.join(_CONTROLES, "lib"))

import flujos as _f                              # noqa: E402

CONTROL = "persistent-local-file-storage"
TIPO = "CHECK"
REGLA = _f.REGLA
SENAL = _f.SENAL

TRAZA = dict(_f.TRAZA)

PASA = _f.PASA
FALLA = _f.FALLA
PARCIAL = _f.PARCIAL
NO_APLICA = _f.NO_APLICA
SIN_RESOLVER = _f.SIN_RESOLVER
SIN_CICLO_DE_VIDA = "LOCAL_STORAGE_LIFECYCLE_UNRESOLVED"
SIN_COBERTURA = _f.SIN_COBERTURA
SIN_OBJETIVO = _f.SIN_OBJETIVO

# Ocho, y el unico que aprueba es PASA.
ESTADOS = (PASA, FALLA, PARCIAL, NO_APLICA, SIN_RESOLVER, SIN_CICLO_DE_VIDA, SIN_COBERTURA,
           SIN_OBJETIVO)

LOCAL_PERMANENTE = "PERSISTENT_LOCAL_STORAGE"
SIN_DATOS_DEL_CICLO = "LOCAL_LIFECYCLE_EVIDENCE_MISSING"
CLASE_CONTRADICHA = "LOCAL_CLASSIFICATION_CONTRADICTED"
EVIDENCIA_HUERFANA = "EVIDENCE_REFERENCE_MISSING"
EVIDENCIA_DE_OTRA_CORRIDA = "EVIDENCE_OUT_OF_BUILD"

# Lo que sostiene una afirmacion de ciclo de vida: la traza de la escritura, o el apoyo. Lo inerte
# no entra, y esa es toda la diferencia entre "es temporal" y "se probo que es temporal".
EVIDENCIA_QUE_SOSTIENE = (_f.TRAZA_DE_ESCRITURA_LOCAL,) + _f.EVIDENCIA_DE_APOYO

DERIVADO_A = "temporary-file-cleanup"

AGENTE = "dev-backend"
SKILL = "dev-storage"


def declarado(valor):
    """El texto declarado, sin los blancos. Vacio si no hay nada."""
    return _f.declarado(valor)


def locales(caso):
    """Las escrituras locales materiales del inventario.

    Son las de clase local, mas cualquier flujo que declare una escritura local aunque su clase
    sea otra. 🔴 Lo segundo no es generosidad: un flujo sin clasificar que escribe en el disco es
    exactamente el caso que no se puede omitir, y omitirlo lo dejaria fuera de las dos redes.
    """
    lista = []
    for f in _f.flujos(caso):
        if f.get("classification") in _f.LOCALES or isinstance(f.get("local"), dict):
            lista.append(f)
    return lista


def campos_faltantes(flujo):
    """Cuales de los siete datos del ciclo de vida no estan declarados."""
    datos = (flujo or {}).get("local") or {}
    return [c for c in _f.CAMPOS_LOCALES if not declarado(datos.get(c))]


def _evaluar_flujo(flujo, indice, build):
    """El estado de una escritura local, con su motivo y su evidencia."""
    datos = (flujo or {}).get("local") or {}
    salida = {"flowId": declarado(flujo.get("id")),
              "classification": flujo.get("classification"),
              "pathOrAdapter": declarado(datos.get("pathOrAdapter")),
              "expectedLifetime": declarado(datos.get("expectedLifetime")),
              "persistenceBehavior": declarado(datos.get("persistenceBehavior")),
              "evidenceUsed": [], "issues": []}

    usadas, huerfanas, ajenas = _f.usables(flujo.get("evidenceRefs"), indice, build)
    salida["evidenceUsed"] = [e.get("evidenceId") for e in usadas]
    if huerfanas:
        salida["issues"].append("%s: %s no existe" % (EVIDENCIA_HUERFANA, ", ".join(huerfanas)))
    if ajenas:
        salida["issues"].append("%s: %s es de otro build o de otro runtime"
                                % (EVIDENCIA_DE_OTRA_CORRIDA, ", ".join(ajenas)))

    # 🔴 Lo declarado persistente FALLA antes de mirar si los siete campos estan completos. Una
    # escritura local permanente ya es el incumplimiento que la regla nombra, y pedirle mas datos
    # seria darle una forma de quedar sin resolver en vez de fallar.
    persistencia = declarado(datos.get("persistenceBehavior"))
    if flujo.get("classification") == _f.LOCAL_PERMANENTE or persistencia == "PERSISTENT":
        if (flujo.get("classification") == _f.LOCAL_TEMPORAL
                and persistencia == "PERSISTENT"):
            salida["issues"].append("%s: el flujo se clasifica temporal y declara comportamiento "
                                    "persistente" % CLASE_CONTRADICHA)
        salida.update({"state": FALLA, "reason": LOCAL_PERMANENTE,
                       "detail": "el almacenamiento local se usa como repositorio permanente de "
                                 "archivos de la aplicacion"})
        return salida

    faltan = campos_faltantes(flujo)
    if faltan:
        salida.update({"state": SIN_CICLO_DE_VIDA, "reason": SIN_CICLO_DE_VIDA,
                       "missingFields": faltan,
                       "detail": "no se establecio el ciclo de vida de la escritura local: falta "
                                 "%s" % ", ".join(faltan)})
        return salida

    if persistencia not in _f.PERSISTENCIA or persistencia == "UNRESOLVED":
        salida.update({"state": SIN_CICLO_DE_VIDA, "reason": SIN_CICLO_DE_VIDA,
                       "detail": "el comportamiento de persistencia de la escritura local no esta "
                                 "resuelto"})
        return salida

    # 🔴 Y la afirmacion tiene que estar sostenida por algo que no sea el nombre del path. Sin
    # esto, `./tmp` con los siete campos escritos a mano pasaba, que es literalmente el caso que
    # el pedido nombra: `tmp` en un path no prueba un ciclo de vida temporal.
    if not [e for e in usadas if e.get("sourceType") in EVIDENCIA_QUE_SOSTIENE]:
        salida.update({"state": SIN_CICLO_DE_VIDA, "reason": SIN_DATOS_DEL_CICLO,
                       "detail": "el ciclo de vida declarado no lo sostiene ninguna traza de la "
                                 "escritura ni ninguna evidencia de apoyo: como se llama el path "
                                 "y en que runtime corre no alcanzan"})
        return salida

    salida.update({"state": PASA, "reason": "", "deferredTo": DERIVADO_A,
                   "detail": "la escritura local es temporal con su ciclo de vida establecido; su "
                             "destruccion la verifica %s" % DERIVADO_A})
    return salida


def evaluar(caso, senal=None, desde=None):
    """El estado de la prohibicion del local permanente, con su motivo y su trazabilidad.

    `caso` es el mismo reporte que leen los otros dos checks de D7. Lo que este mira de cada
    flujo es su bloque `local`:

        {"id", "classification",
         "local": {"pathOrAdapter", "purpose", "creation", "consumption", "cleanup",
                   "expectedLifetime", "persistenceBehavior"},
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
                       "localFlows": []})
        return salida

    salida["fileFlows"] = {"source": caso["fileFlows"].get("source"),
                           "flows": [declarado(f.get("id")) for f in _f.flujos(caso)]}
    completa, motivo_cobertura = _f.clasificacion_completa(caso)

    materiales = locales(caso)
    salida["localFlows"] = [declarado(f.get("id")) for f in materiales]

    indice = _f.evidencias(caso)
    evaluados = [_evaluar_flujo(f, indice, build) for f in materiales]
    salida["flows"] = evaluados
    for f in evaluados:
        salida["issues"].extend(f.get("issues") or [])

    estados = [f["state"] for f in evaluados]
    # El orden es el mismo en los tres checks de D7, y es de lo grueso a lo fino: un FAIL probado
    # manda sobre todo, despues no saber cuantos flujos hay, despues no saber de uno, y al final
    # lo que paso.
    if FALLA in estados:
        salida.update({"state": FALLA, "reason": LOCAL_PERMANENTE})
    elif not completa:
        salida.update({"state": SIN_COBERTURA, "reason": SIN_COBERTURA,
                       "detail": motivo_cobertura})
    elif SIN_CICLO_DE_VIDA in estados:
        # 🔴 Dos estados y no uno. Que NINGUNA escritura local tenga su ciclo de vida establecido
        # es no saber nada; que lo tengan algunas y otras no es saber una parte. Un solo estado
        # para los dos casos hace que remediar la mitad no se vea en ningun lado, y ese es el
        # incentivo exacto para no remediar la otra.
        motivo = next(f["reason"] for f in evaluados if f["state"] == SIN_CICLO_DE_VIDA)
        if all(e == SIN_CICLO_DE_VIDA for e in estados):
            salida.update({"state": SIN_CICLO_DE_VIDA, "reason": motivo,
                           "detail": "ninguna escritura local tiene su ciclo de vida "
                                     "establecido"})
        else:
            salida.update({"state": PARCIAL, "reason": motivo,
                           "detail": "hay escrituras locales con su ciclo de vida establecido y "
                                     "otras sin establecer"})
    elif not materiales:
        salida.update({"state": PASA, "reason": "",
                       "detail": "no hay escrituras locales materiales en alcance, y la "
                                 "prohibicion no tiene sujeto que la incumpla"})
    else:
        salida.update({"state": PASA, "reason": "",
                       "detail": "ninguna escritura local se usa como repositorio permanente"})
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
