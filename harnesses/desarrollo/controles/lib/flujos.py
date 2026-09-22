"""El inventario de flujos de archivo de D7, y la particion de evidencia. Compartido.

    source: ES0901 / 6.3 / 7.1 / D7

Las tres obligaciones de D7 se verifican con tres checks distintos y los tres leen **el mismo**
inventario: que flujos de archivo hay, de que clase es cada uno y con que evidencia se sostiene.
Sin este modulo la validacion del inventario estaria escrita tres veces, y tres copias de una
validacion se van separando: la primera vez que alguien afloje una, las otras dos siguen firmes y
nadie se entera de que el harness contesta distinto segun a que check se le pregunte.

🔴 **Esto no es un control.** No se declara en `control-registry.json`, no se evalua, no tiene
estado y no aprueba nada. Es vocabulario y validacion, y por eso vive en `controles/lib/` y no en
`controles/checks/`.

🔴 **La clasificacion de un flujo es EVIDENCIA DE IMPLEMENTACION, no aplicabilidad.** Quien decide
si D7 aplica es `fileHandlingPresent`, resuelta por `senales.py` con su evidencia y su productor.
Un inventario de flujos no enciende ni apaga una regla: si lo hiciera, habria dos sistemas de
aplicabilidad y el segundo lo escribiria el proyecto sobre si mismo.

🔴 **Este modulo no sabe cual es el repositorio estandar del GCBA, y no lo inventa.** El estandar
nombra el protocolo -S3- y se detiene ahi: no hay nada mas en ningun extracto que este harness
tenga. La identidad entra como DATO DECLARADO con su fuente citada, y lo que se compara son
identificadores. Nunca un mecanismo.

🔴 **Y no hay ninguna duracion adentro.** "Inmediato" es el fin del proposito temporal, no un
numero: ver `CICLO_DE_VIDA` y lo que NO lo sustituye.
"""
import os
import sys

_BIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_BIN, "bin") not in sys.path:
    sys.path.insert(0, os.path.join(_BIN, "bin"))

from orquestacion import senales as _senales     # noqa: E402

REGLA = "D7"
SENAL = "fileHandlingPresent"

TRAZA = {"standard": "ES0901", "version": "6.3", "section": "7.1", "rule": "D7"}

# El apartado que sostiene a D7. Se nombra por su numero, que es lo que se puede citar.
APOYO = "8.4 Sistema de Archivos"

# -- las clases de flujo -------------------------------------------------------

# Las seis clases, una por flujo material. `UNRESOLVED` es una clase de primera: un flujo que
# nadie pudo clasificar deja la cobertura incompleta, no desaparece del inventario.
ESTANDAR = "PERSISTENT_STANDARD_STORAGE"
LOCAL_PERMANENTE = "PERSISTENT_LOCAL"
LOCAL_TEMPORAL = "TEMPORARY_LOCAL"
OTRO_REMOTO = "OTHER_REMOTE_STORAGE"
SIN_ALMACENAR = "NO_STORAGE"
CLASE_SIN_RESOLVER = "UNRESOLVED"

CLASES = (ESTANDAR, LOCAL_PERMANENTE, LOCAL_TEMPORAL, OTRO_REMOTO, SIN_ALMACENAR,
          CLASE_SIN_RESOLVER)

# Que clase le toca a que obligacion. Las tres listas se cruzan -un persistente local es
# persistente Y local- y eso es a proposito: la misma escritura incumple dos obligaciones
# distintas y las dos lo tienen que decir.
PERSISTENTES = (ESTANDAR, LOCAL_PERMANENTE, OTRO_REMOTO)
LOCALES = (LOCAL_PERMANENTE, LOCAL_TEMPORAL)
TEMPORALES = (LOCAL_TEMPORAL,)

# 🔴 Un flujo de archivos es MAS que una subida. Las once formas estan nombradas porque la unica
# que a todo el mundo se le ocurre es la primera, y una regla que solo mire subidas deja afuera
# un reporte que se genera, se sirve y se queda en el disco.
OPERACIONES = ("RECEIVE", "UPLOAD", "DOWNLOAD", "GENERATE", "TRANSFORM", "STAGE", "STORE",
               "SERVE", "IMPORT", "EXPORT", "TEMPORARY_PROCESSING")

# -- de donde sale un dato declarado -------------------------------------------

# De donde puede salir el inventario de flujos. Un flujo que nadie enumero es un flujo que nadie
# verifico, y eso no se disimula contando solo los que alguien eligio mirar.
FUENTES_DE_COBERTURA = ("PROJECT_ARCHITECTURE", "IMPACT_ANALYSIS", "CODE_PATH_INVENTORY",
                        "ROUTE_INVENTORY", "TEAM_APPROVED_TEST_PROFILE")

# De donde puede salir la identidad del repositorio estandar del GCBA, y su contrato. La lista
# dice que fuentes son defendibles; NO dice cual es el repositorio, que es lo que este harness
# no sabe.
FUENTES_DE_IDENTIDAD = ("GCBA_NORMATIVE", "GCBA_CATALOG_ENTRY", "ASI_INTEGRATION_CONTRACT",
                        "PROJECT_INTEGRATION_AGREEMENT", "HUMAN_CONFIRMATION")

# -- la particion de evidencia -------------------------------------------------

# Las tres que prueban, una por obligacion. Cada check exige la suya: una traza de limpieza no
# prueba un camino de persistencia y viceversa.
TRAZA_DE_PERSISTENCIA = "PERSISTENCE_PATH_TRACE"
TRAZA_DE_ESCRITURA_LOCAL = "LOCAL_WRITE_TRACE"
TRAZA_DE_LIMPIEZA = "CLEANUP_PATH_TRACE"
EVIDENCIA_QUE_PRUEBA = (TRAZA_DE_PERSISTENCIA, TRAZA_DE_ESCRITURA_LOCAL, TRAZA_DE_LIMPIEZA)

EVIDENCIA_DE_APOYO = ("HUMAN_CONFIRMATION", "CODE_PATH_REVIEW")

# 🔴 Lo que esta instalado no prueba lo que se guarda. Las doce son evidencia de lo que HAY o de
# lo que se SUPONE, no de lo que la aplicacion hizo con un archivo, y ninguna sostiene nada.
EVIDENCIA_QUE_NO_PRUEBA = ("REPOSITORY_DEPENDENCY", "ENVIRONMENT_VARIABLE_NAME",
                           "BUCKET_CONFIGURATION", "REMOTE_HTTP_CALL", "UPLOAD_SUCCEEDED",
                           "PATH_NAMING", "PERIODIC_CLEANUP_JOB", "RESTART_POLICY",
                           "TTL_CONFIGURATION", "MANUAL_PROCEDURE", "CONTAINER_ASSUMPTION",
                           "AGENT_STATEMENT")

# -- el ciclo de vida de un temporal -------------------------------------------

# La unica atadura que cumple, y las seis que no la sustituyen. No hay un numero en ninguna de
# las siete: "inmediato" es el fin del proposito, y un umbral inventado se lee autoritativo.
CICLO_DE_VIDA = "LIFECYCLE_BOUND"
DEMORADAS = ("PERIODIC", "STARTUP", "RESTART", "TTL", "MANUAL")
SIN_LIMPIEZA = "NONE"
LIMPIEZA_SIN_RESOLVER = "UNRESOLVED"
MECANISMOS = (CICLO_DE_VIDA,) + DEMORADAS + (SIN_LIMPIEZA, LIMPIEZA_SIN_RESOLVER)

# Los caminos que una limpieza tiene que cubrir. El cuarto es condicional: hay runtimes donde una
# cancelacion no deja correr nada, y exigirlo ahi seria exigir lo imposible.
CAMINO_NORMAL = "NORMAL_COMPLETION"
CAMINOS_SIEMPRE = (CAMINO_NORMAL, "VALIDATION_FAILURE", "PROVIDER_FAILURE")
CAMINO_CANCELACION = "CANCELLATION"
CAMINOS = CAMINOS_SIEMPRE + (CAMINO_CANCELACION,)

# Los siete datos de una escritura local. Falta uno y el ciclo de vida no esta establecido: son
# siete y no uno porque "es temporal" sin consumo ni limpieza declarados es una afirmacion.
CAMPOS_LOCALES = ("pathOrAdapter", "purpose", "creation", "consumption", "cleanup",
                  "expectedLifetime", "persistenceBehavior")

PERSISTENCIA = ("PERSISTENT", "TEMPORARY", "UNRESOLVED")

# -- los estados que comparten los tres checks ---------------------------------

PASA = "PASS"
FALLA = "FAIL"
PARCIAL = "PARTIAL"
NO_APLICA = "NOT_APPLICABLE"
SIN_RESOLVER = "APPLICABILITY_UNRESOLVED"
SIN_COBERTURA = "FILE_FLOW_COVERAGE_UNRESOLVED"
SIN_OBJETIVO = "TEST_TARGET_UNAVAILABLE"

# El motivo de un sin resolver que no es "falta la senal" sino "llego otra". Son dos cosas
# distintas y el que lee el resultado tiene que poder pedir la que falta.
SENAL_AJENA = "SIGNAL_IDENTITY_MISMATCH"


# -- los helpers ---------------------------------------------------------------

def declarado(valor):
    """El texto declarado, sin los blancos. Vacio si no hay nada.

    🔴 Un espacio NO es un dato declarado, y se aplica a LOS DOS LADOS de cada comparacion. Es la
    leccion de D6, donde normalizar un solo lado convirtio un caso correcto en un FAIL y un
    bypass probado en un aviso que nadie leia.
    """
    return str(valor or "").strip()


def identidad_de_senal(senal):
    """El `signalId` que el dato trae, o "" si no trae ninguno.

    Entran las tres formas: un documento de senal, un mapa `{id: resuelta}` -que es como viaja
    en `normativa.resolucion`- y un booleano suelto, que no dice de que senal es.
    """
    if not isinstance(senal, dict):
        return ""
    if isinstance(senal.get(SENAL), dict):
        return SENAL
    return declarado(senal.get("signalId"))


def valor_de_senal(senal):
    """El valor de LA senal de D7, venga resuelta, cruda o como booleano viejo.

    🔴 **Se mira el `signalId`.** La version anterior leia `value` y nada mas, asi que pasarle
    `frontendPresent` en TRUE hacia que los tres checks de D7 evaluaran el caso y publicaran
    `signal: fileHandlingPresent` al lado del resultado: informaban cumplimiento atribuido a una
    senal que nunca llego. Es el mismo defecto que D5 ya arreglo un nivel abajo, en su derivacion.
    Una senal de otra regla no sustituye a esta: queda `UNRESOLVED`.
    """
    if isinstance(senal, dict):
        if isinstance(senal.get(SENAL), dict):
            return valor_de_senal(senal[SENAL])
        sid = declarado(senal.get("signalId"))
        if sid and sid != SENAL:
            return _senales.SIN_RESOLVER
        return senal.get("value") or _senales.SIN_RESOLVER
    if isinstance(senal, bool):
        return _senales.VERDADERA if senal else _senales.FALSA
    if senal in (_senales.VERDADERA, _senales.FALSA):
        return senal
    return _senales.SIN_RESOLVER


def aplicabilidad(caso, senal):
    """El estado con el que un check corta antes de mirar nada, o None si sigue.

    Los tres checks abren igual: sin senal no se sabe, en FALSE no aplica, y sin donde correr no
    se ejecuto nada. Que los tres corten en el mismo orden es lo que hace comparables sus
    resultados.
    """
    valor = valor_de_senal(senal)
    if valor == _senales.SIN_RESOLVER:
        extra = {"missingSignals": [SENAL],
                 "reason": "no se sabe si la aplicacion gestiona archivos, y lo que no se sabe no "
                           "se convierte en que no aplica"}
        ajena = identidad_de_senal(senal)
        if ajena and ajena != SENAL:
            extra.update({"reason": SENAL_AJENA,
                          "detail": "el dato que llego es la senal `%s`, que no es la de esta "
                                    "regla y no la sustituye" % ajena,
                          "issues": ["%s: llego `%s` en lugar de `%s`"
                                     % (SENAL_AJENA, ajena, SENAL)]})
        return SIN_RESOLVER, extra
    if valor == _senales.FALSA:
        return NO_APLICA, {"reason": "la aplicacion no gestiona archivos en alcance"}
    if not ((caso or {}).get("testTarget") or {}).get("available"):
        return SIN_OBJETIVO, {
            "reason": "no hubo donde correr la verificacion. No se ejecuto nada, y lo que no se "
                      "ejecuto no pasa"}
    return None, {}


# -- el inventario -------------------------------------------------------------

def inventario_valido(caso):
    """(ok, motivo) del inventario de flujos de archivo materiales."""
    inventario = (caso or {}).get("fileFlows") or {}
    lista = inventario.get("flows") or []
    if not lista:
        return False, "no hay un inventario de flujos de archivo declarado"
    if inventario.get("source") not in FUENTES_DE_COBERTURA:
        return False, ("el inventario no declara de donde sale, y un inventario sin origen no "
                       "dice cuantos flujos hay")
    if [f for f in lista if not declarado(f.get("id"))]:
        return False, "hay flujos sin identificar en el inventario"
    fuera = [f for f in lista if f.get("classification") not in CLASES]
    if fuera:
        return False, "hay flujos sin una clasificacion de las seis declaradas"
    return True, ""


def flujos(caso, clases=None):
    """Los flujos del inventario, o solo los de las clases pedidas. TODOS los del inventario.

    🔴 No hay un segundo filtro por flujo. El inventario ES la lista de flujos materiales —eso es
    lo que su `source` respalda—, asi que una etiqueta que el proyecto ponga sola no saca a
    ninguno de la verificacion. La materialidad se decide al armar el inventario.
    """
    lista = list(((caso or {}).get("fileFlows") or {}).get("flows") or [])
    if clases is None:
        return lista
    return [f for f in lista if f.get("classification") in clases]


def clasificacion_completa(caso):
    """(completa, motivo) de la clasificacion: sin flujos sin resolver y declarada completa.

    Son dos condiciones y no una. Un flujo `UNRESOLVED` es un hueco visible; un inventario que
    se declara incompleto es un hueco que alguien tuvo la honestidad de escribir. Los dos dejan
    la cobertura sin resolver, y ninguno se deduce del otro.
    """
    inventario = (caso or {}).get("fileFlows") or {}
    sin_clasificar = [declarado(f.get("id")) for f in flujos(caso)
                      if f.get("classification") == CLASE_SIN_RESOLVER]
    if sin_clasificar:
        return False, ("hay flujos sin clasificar: %s" % ", ".join(sorted(sin_clasificar)))
    if inventario.get("complete") is False:
        return False, "el inventario se declara incompleto"
    return True, ""


# -- la identidad declarada ----------------------------------------------------

def identidad_valida(bloque, que):
    """(ok, motivo) de un dato de identidad declarado: id, fuente de la lista y referencia.

    Sin los tres no identifica nada: un id sin fuente es un nombre que alguien escribio, y de eso
    se trata todo esto.
    """
    datos = bloque or {}
    if not declarado(datos.get("id")):
        return False, "no hay %s declarada" % que
    if datos.get("source") not in FUENTES_DE_IDENTIDAD:
        return False, ("%s no declara de donde sale, y una identidad sin origen es un nombre que "
                       "alguien escribio" % que)
    if not declarado(datos.get("reference")):
        return False, "%s no dice donde esta declarada" % que
    return True, ""


# -- la evidencia --------------------------------------------------------------

def evidencias(caso):
    """{evidenceId: evidencia} de lo que el caso declara."""
    return {e.get("evidenceId"): e for e in (caso or {}).get("evidence") or []
            if e.get("evidenceId")}


def de_esta_corrida(evidencia, build):
    """Si la evidencia pertenece al build y al runtime que se probaron.

    Una corrida sobre otro build es una corrida sobre otro sistema. Lo que no declara de cual es,
    es de este; lo que declara otro, no cuenta.
    """
    for campo, clave in (("buildId", "id"), ("runtime", "runtime")):
        esperado = (build or {}).get(clave)
        por_la_evidencia = evidencia.get(campo)
        if por_la_evidencia and esperado and por_la_evidencia != esperado:
            return False
    return True


def usables(refs, indice, build):
    """(usadas, huerfanas, ajenas) de una lista de referencias a evidencia.

    Una referencia a algo que no existe y una a algo de otra corrida son dos problemas distintos
    y se informan por separado: el primero es un caso mal armado y el segundo es evidencia real
    de otro sistema.
    """
    usadas, huerfanas, ajenas = [], [], []
    for ref in refs or []:
        e = indice.get(ref)
        if e is None:
            huerfanas.append(ref)
        elif not de_esta_corrida(e, build):
            ajenas.append(ref)
        else:
            usadas.append(e)
    return usadas, sorted(huerfanas), sorted(ajenas)


def pruebas(usadas, tipo):
    """Las evidencias usadas que prueban, de la clase que el check exige."""
    return [e for e in usadas if e.get("sourceType") == tipo]
