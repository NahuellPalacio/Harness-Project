"""El motor minimo de ejecucion: una WorkUnit, un intento, sincronico, por invocacion (MD-02).

docs/cambios/minimal-execution-engine/spec.md; ADR-0015.

    ejecutar    configuracion, recuperacion, admision al pedir, request, Execution, admision al
                entregar, foto, entrega, Host, AgentReport, output, foto, evidencia, resultado
    cancelar    recupera primero y pide despues (MD-24)
    recuperar   cierra las RUNNING huerfanas, barre los residuos y los temporales (§14.1)
    estado      solo lee: los turnos de la tarea, su estado derivado y las huerfanas

🔴 No hay scheduler, cola, hilos, reintento automatico ni reanudacion. Un reintento es otra
Execution con la misma clave, y lo pide una persona.

🔴 La frontera es `entrega.json`. Antes, lo que falla es una admision: REJECTED con su codigo.
Despues, solo un codigo de corrida o CANCELLED: nunca AGENT_UNAVAILABLE ni CAPABILITY_UNAVAILABLE
en FAILED (ME-I29).

🔴 Sin catalogo de secretos no se persiste texto del agente ni del Host (MD-19).
"""
import getpass
import hashlib
import io
import json
import os
import platform
import shutil

from . import admision
from . import contrato
from . import evidencia
from . import host_claude_code
from . import proceso
from . import registro
from contexto import limpieza

LIMITE_POR_DEFECTO = 1800
TOPE_DE_OUTPUT = 1 << 20


class ErrorDelComando(Exception):
    """Sale con codigo 2 y no hay Execution: configuracion, catalogo, disco o un id invalido."""


# -- la configuracion (MD-22) ----------------------------------------------------------------

def configuracion(proyecto):
    """{comando, limite, perfiles, usuario} de `.claude/harness.config.json`, o levanta
    ErrorDelComando. Un archivo que existe y no se lee no cae al default: el motor lanza una
    corrida que cuesta, y el archivo pudo haber dicho otro Host."""
    ruta = os.path.join(proyecto, ".claude", "harness.config.json")
    doc = {}
    if os.path.exists(ruta):
        try:
            with io.open(ruta, encoding="utf-8-sig") as f:
                doc = json.load(f)
        except (OSError, ValueError) as e:
            raise ErrorDelComando("harness.config.json no se puede leer (%s): el motor no cae al "
                                  "default" % type(e).__name__)
        if not isinstance(doc, dict):
            raise ErrorDelComando("harness.config.json no es un objeto JSON")
    ejecucion = doc.get("ejecucion", {})
    if not isinstance(ejecucion, dict):
        raise ErrorDelComando("`ejecucion` de harness.config.json tiene que ser un objeto")

    if "comandoHost" in ejecucion:
        comando = ejecucion["comandoHost"]
        # MD-22′: ni una bandera del adaptador ni una de seguridad; la misma regla que el
        # adaptador vuelve a aplicar.
        motivo = host_claude_code.comando_invalido(comando)
        if motivo:
            raise ErrorDelComando("`ejecucion.comandoHost` %s" % motivo)
        programa = comando[0] if os.path.isfile(comando[0]) else shutil.which(comando[0])
        if not programa:
            raise ErrorDelComando("`ejecucion.comandoHost`: %s no existe ni esta en el PATH"
                                  % comando[0])
        comando = [programa] + comando[1:]
    else:
        programa = host_claude_code.comando_por_defecto()
        if not programa:
            raise ErrorDelComando("no se encontro `claude` en el PATH, y harness.config.json no "
                                  "declara `ejecucion.comandoHost`")
        comando = [programa]

    limite = ejecucion.get("limiteSegundos", LIMITE_POR_DEFECTO)
    if not isinstance(limite, int) or isinstance(limite, bool) or limite <= 0:
        raise ErrorDelComando("`ejecucion.limiteSegundos` tiene que ser un entero positivo")

    ruteo = doc.get("modelRouting") if isinstance(doc.get("modelRouting"), dict) else {}
    # MD-22′: un perfil es un nombre de modelo y no puede volverse una bandera.
    motivo = host_claude_code.perfiles_invalidos(ruteo.get("perfiles"))
    if motivo:
        raise ErrorDelComando("`modelRouting.perfiles`: %s" % motivo)
    perfiles = ruteo.get("perfiles") if isinstance(ruteo.get("perfiles"), dict) else {}
    usuario = doc.get("usuario") if isinstance(doc.get("usuario"), str) else ""
    return {"comando": comando, "limite": limite, "perfiles": perfiles, "usuario": usuario}


def quien_pide(explicito, config):
    """`--pedido-por`, si no `usuario` de harness.config.json, si no el usuario del sistema."""
    for valor in (explicito, (config or {}).get("usuario")):
        if isinstance(valor, str) and valor.strip():
            return valor.strip()
    try:
        return getpass.getuser()
    except Exception:                            # noqa: BLE001 - sin usuario, la admision lo dice
        return ""


def _catalogo(cargar):
    try:
        return cargar()
    except Exception:                            # noqa: BLE001 - sin catalogo, falla cerrado
        return None


# -- el resultado ----------------------------------------------------------------------------

def _resultado(request, huella, estado, codigo=None, texto=None, catalogo=None, inicio=None,
               evidencia_=None, informe=None, salida=None, host=None):
    return {
        "schema_version": contrato.VERSION_RESULT,
        "executionId": request.get("executionId"),
        "requestFingerprint": huella,
        "status": estado,
        "error": None if codigo is None else admision.error(codigo, texto, catalogo),
        "startedAt": inicio,
        "endedAt": max(registro.ahora(), inicio or "", request.get("createdAt") or ""),
        "agentDeclaredStatus": informe["declaredStatus"] if informe and salida else None,
        "output": salida,
        "evidence": evidencia_,
        "host": host,
    }


def _escribir_resultado(carpeta, resultado, request):
    """Escribe result.json una sola vez. Si ya habia uno, gana el primero y se devuelve ese: un
    resultado tardio no pisa nada (T3 D10)."""
    errores = contrato.validar_resultado(resultado, request)
    if errores:
        raise ErrorDelComando("el motor armo un resultado que no valida: %s" % errores[0])
    try:
        registro.escribir_json(os.path.join(carpeta, registro.RESULT), resultado)
    except FileExistsError:
        previo, _ = registro.leer_json(os.path.join(carpeta, registro.RESULT))
        return previo
    return resultado


def _host_de(entrega):
    host = (entrega or {}).get("host") or {}
    return {"kind": host.get("kind") or host_claude_code.KIND, "sessionRef": host.get("sessionRef"),
            "runRef": None}


def _detalle_de_falla(falla, catalogo):
    """El texto del motor y, solo con catalogo, el del Host **redactado entero antes de
    recortarlo** (MD-19′): `admision.detalle` vuelve a redactar todo y recorta a 300. Sin
    catalogo, solo el texto del motor: nada que venga del Host."""
    texto = falla.get("motor") or falla["code"]
    if catalogo is not None and falla.get("host"):
        del_host, _ = limpieza.redactar(str(falla["host"]), catalogo, "$.error.detail")
        texto += " · %s" % del_host
    return texto


# Lo unico que un Host Adapter puede devolver despues de la entrega (§11.1, ME-I29). Otro codigo
# es una violacion de su contrato, y el motor no la escribe como si fuera del Host (MD-10′).
DE_CORRIDA = ("HOST_FAILURE", "HOST_INTERRUPTED", "PROVIDER_FAILURE", "TIMEOUT", "OUTPUT_INVALID",
              "AGENT_DECLARED_NOT_COMPLETE", "ENGINE_FAILURE")


def _del_adaptador(informe, falla):
    """(informe, falla) tal como los puede usar el motor: un codigo que no es de corrida, o un
    informe que no valida, es ENGINE_FAILURE."""
    if falla is not None and falla.get("code") not in DE_CORRIDA:
        return None, {"code": "ENGINE_FAILURE", "host": None,
                      "motor": "el Host Adapter devolvio despues de la entrega un codigo que no es "
                               "de corrida%s" % (": %s" % falla["code"]
                                                 if falla.get("code") in contrato.CODIGOS else "")}
    if falla is None and informe is not None and contrato.validar_informe(informe):
        return None, {"code": "ENGINE_FAILURE", "host": None,
                      "motor": "el Host Adapter devolvio un AgentReport que no valida"}
    return informe, falla


# -- ejecutar --------------------------------------------------------------------------------

def ejecutar(proyecto, clave, unidad, pedido_por, adaptador=None, config=None,
             catalogo=None, compuerta=None, cargar_registro=None, antes_de_reservar=None,
             antes_de_entregar=None, execution_id=None, huella_esperada=None):
    """(resultado, None) o (None, ExecutionError). Levanta ErrorDelComando sin crear nada.

    `catalogo` carga el catalogo de secretos (por defecto, el de la SecretGate); `compuerta` y
    `cargar_registro` son los duenos de las condiciones 9 y 10. `antes_de_reservar` y
    `antes_de_entregar` son los puntos de encuentro de los tests: la ventana de la carrera (MD-04b)
    y la de un cambio entre la creacion y la entrega.

    Task 5 (GD-16, GD-27 paso 4), los dos opcionales y sin ellos igual que en Task 4:
    `execution_id` es el id preasignado del intento, el que `al_pedir` ya acepta de afuera: quien lo
    pasa sabe cual es su Execution aunque el comando falle. Uno invalido o ya usado no se inventa
    nada: lo dicen `al_pedir` y el registro. `huella_esperada` es la huella del plan a la que esta
    atado quien pide; llega hasta `al_entregar`, que rechaza con PLAN_CHANGED si la request se armo
    con otra.
    """
    config = config or configuracion(proyecto)
    if adaptador is None:
        try:
            adaptador = host_claude_code.Adaptador(config["comando"], config["limite"],
                                                   config["perfiles"])
        except ValueError as e:
            raise ErrorDelComando("la configuracion del Host no se puede usar: %s" % e)
    cargar_catalogo = catalogo or limpieza.cargar_catalogo
    if _catalogo(cargar_catalogo) is None:
        raise ErrorDelComando("no esta el catalogo de secretos: sin el no se persiste nada")
    if not registro.es(registro.CLAVE_DE_TAREA, clave):
        return None, admision.error("CONTRACT_INVALID", "%r no es una TaskKey" % (clave,),
                                    _catalogo(cargar_catalogo))
    recuperar(proyecto, clave)
    try:
        request, error, leido, huella = admision.al_pedir(
            proyecto, clave, unidad, pedido_por, _catalogo(cargar_catalogo), compuerta,
            cargar_registro, execution_id)
    except admision.SinCatalogo as e:
        raise ErrorDelComando(str(e))
    if error is not None:
        return None, error
    try:
        vida = registro.crear(proyecto, request, leido, antes_de_reservar)
    except OSError as e:
        raise ErrorDelComando("no se pudo crear la Execution (%s): el motor no sigue sin la "
                              "escritura de una sola vez" % type(e).__name__)
    if vida is None:
        return None, admision.error(
            "DUPLICATE_EXECUTION", "otra admision de la misma clave reservo el turno %d" % (
                leido + 1), _catalogo(cargar_catalogo))
    try:
        return _correr(proyecto, request, huella, adaptador, cargar_catalogo, compuerta,
                       cargar_registro, antes_de_entregar, huella_esperada), None
    finally:
        vida.soltar()


def _correr(proyecto, request, huella, adaptador, cargar_catalogo, compuerta, cargar_registro,
            antes_de_entregar, huella_esperada=None):
    """Desde la Execution publicada hasta su resultado. Con el candado de vida tomado.

    `request` y `huella` son las que el motor persistio. Al entregar no se confia en lo guardado:
    se relee request.json, su huella tiene que ser la de lo que el motor escribio (MD-11′), y se le
    aplica la regla entera (ME-I06). Al Host se le entrega la request del disco, ya probada igual.
    Si alguien la cambio, el resultado REJECTED lleva la huella de lo que el motor escribio: la
    diferencia queda a la vista, y no se falsifica ninguna huella (R6).

    `huella_esperada` (Task 5) llega a `al_entregar` tal cual, y ahi se compara con la huella del plan
    con la que se armo la request del disco.
    """
    carpeta = registro.carpeta_de(proyecto, request["taskKey"], request["executionId"])

    def cancelada():
        return os.path.exists(os.path.join(carpeta, registro.CANCELACION))

    if antes_de_entregar is not None:
        antes_de_entregar(carpeta)
    if cancelada():
        return _escribir_resultado(carpeta, _resultado(
            request, huella, "CANCELLED", "CANCELLED", "cancelada a pedido antes de entregarla",
            _catalogo(cargar_catalogo)), request)
    guardada, _ = registro.leer_json(os.path.join(carpeta, registro.REQUEST))
    rechazo, derivado = admision.al_entregar(
        proyecto, guardada if isinstance(guardada, dict) else {}, adaptador, compuerta,
        cargar_registro, huella, huella_esperada)
    if rechazo is not None:
        catalogo = _catalogo(cargar_catalogo)
        texto = rechazo.detalle if catalogo is not None else "rechazada al entregar: %s" % \
            rechazo.codigo
        return _escribir_resultado(carpeta, _resultado(
            request, huella, "REJECTED", rechazo.codigo, texto, catalogo), request)
    # La request del disco es, por su huella, la que el motor escribio: es la que se entrega.
    request = guardada

    antes = evidencia.instantanea(proyecto)
    host = adaptador.nueva_sesion()
    if cancelada():
        return _escribir_resultado(carpeta, _resultado(
            request, huella, "CANCELLED", "CANCELLED", "cancelada a pedido antes de entregarla",
            _catalogo(cargar_catalogo)), request)
    inicio = registro.ahora()
    registro.escribir_json(os.path.join(carpeta, registro.ENTREGA), {
        "deliveredAt": inicio, "repoRevisionBefore": antes["revision"], "antes": antes,
        "host": {"kind": host["kind"], "sessionRef": host["sessionRef"]},
        "motor": {"pid": os.getpid(), "maquina": platform.node()}})

    # Desde aca la Execution esta RUNNING: solo codigos de corrida o CANCELLED.
    try:
        return _entregada(proyecto, request, huella, carpeta, adaptador, derivado, host, antes,
                          inicio, cargar_catalogo, cancelada)
    except KeyboardInterrupt:
        codigo = None if cancelada() else "HOST_INTERRUPTED"
        return _cerrar_sin_host(proyecto, request, huella, carpeta, antes, inicio, host, codigo,
                                "Ctrl-C sobre el motor", cargar_catalogo)
    except Exception as e:                       # noqa: BLE001 - no se disfraza de falla del Host
        return _cerrar_sin_host(proyecto, request, huella, carpeta, antes, inicio, host,
                                "ENGINE_FAILURE", "el motor fallo despues de la entrega (%s)"
                                % type(e).__name__, cargar_catalogo)


def _cerrar_sin_host(proyecto, request, huella, carpeta, antes, inicio, host, codigo, texto,
                     cargar_catalogo):
    """Un final sin AgentReport, despues de la entrega. Sin codigo es CANCELLED (MD-24)."""
    ev = evidencia.armar(proyecto, antes, evidencia.instantanea(proyecto),
                         registro.otras_entregadas(proyecto, request["executionId"],
                                                   registro.entregada_en(carpeta)))
    estado = "CANCELLED" if codigo is None else "FAILED"
    return _escribir_resultado(carpeta, _resultado(
        request, huella, estado, codigo or "CANCELLED",
        texto if codigo else "cancelada a pedido (cancelacion.json)",
        _catalogo(cargar_catalogo), inicio, ev, host=host), request)


def _entregada(proyecto, request, huella, carpeta, adaptador, derivado, host, antes, inicio,
               cargar_catalogo, cancelada):
    def al_lanzar(pid):
        registro.escribir_json(os.path.join(carpeta, registro.PROCESO), {"pid": pid})

    informe, falla, como = adaptador.entregar(proyecto, request, carpeta, derivado["definicion"],
                                              host, cancelada, al_lanzar)
    informe, falla = _del_adaptador(informe, falla)
    if como == proceso.CANCELADO:
        return _cerrar_sin_host(proyecto, request, huella, carpeta, antes, inicio, host, None,
                                None, cargar_catalogo)
    if como == proceso.INTERRUMPIDO:
        return _cerrar_sin_host(proyecto, request, huella, carpeta, antes, inicio, host,
                                None if cancelada() else "HOST_INTERRUPTED",
                                "Ctrl-C sobre el motor: se mato el arbol del Host",
                                cargar_catalogo)
    if falla is not None and falla["code"] == "HOST_INTERRUPTED" and cancelada():
        return _cerrar_sin_host(proyecto, request, huella, carpeta, antes, inicio, host, None,
                                None, cargar_catalogo)

    catalogo = _catalogo(cargar_catalogo)
    salida = None
    if falla is None:
        if catalogo is None:
            falla = {"code": "ENGINE_FAILURE", "host": None,
                     "motor": "sin catalogo de secretos no se escribe el texto del agente"}
        else:
            salida = _output(proyecto, carpeta, informe["artifact"], catalogo)
    ev = evidencia.armar(proyecto, antes, evidencia.instantanea(proyecto),
                         registro.otras_entregadas(proyecto, request["executionId"],
                                                   registro.entregada_en(carpeta)))
    if falla is not None:
        return _escribir_resultado(carpeta, _resultado(
            request, huella, "FAILED", falla["code"], _detalle_de_falla(falla, catalogo),
            catalogo, inicio, ev, host=host), request)
    if informe["declaredStatus"] == contrato.COMPLETO:
        return _escribir_resultado(carpeta, _resultado(
            request, huella, "SUCCEEDED", None, None, catalogo, inicio, ev, informe, salida,
            host), request)
    return _escribir_resultado(carpeta, _resultado(
        request, huella, "FAILED", contrato.DECLARADO_INCOMPLETO,
        "el agente declaro %s" % informe["declaredStatus"], catalogo, inicio, ev, informe, salida,
        host), request)


def _output(proyecto, carpeta, artifact, catalogo):
    """output.md: el artifact redactado, recortado a 1 MiB, en UTF-8 con LF. {path, fingerprint}."""
    texto, _ = limpieza.redactar(artifact, catalogo, "$.artifact")
    texto, _ = limpieza.recortar(texto.replace("\r\n", "\n").replace("\r", "\n"), TOPE_DE_OUTPUT)
    datos = texto.encode("utf-8")
    ruta = os.path.join(carpeta, registro.OUTPUT)
    relativa = registro.relativa(proyecto, ruta)
    if registro.ruta_mala(proyecto, relativa):
        raise ValueError("la ruta del output no es canonica")
    registro.escribir_una_vez(ruta, datos)
    return {"path": relativa, "fingerprint": "sha256:" + hashlib.sha256(datos).hexdigest()}


# -- recuperar -------------------------------------------------------------------------------

def recuperar(proyecto, clave):
    """Cierra las RUNNING huerfanas, barre los residuos y borra los temporales (§14.1).

    Nunca mata un proceso, nunca reanuda, y no toca una REQUESTED: queda abierta hasta una
    cancelacion explicita (R2). Devuelve [{executionId, status, code, hostVivo}] de lo que cerro.
    """
    cerradas = []
    for _, _, execution_id, _ in registro.nombradas(proyecto, clave):
        if execution_id is None:
            continue
        carpeta = registro.carpeta_de(proyecto, clave, execution_id)
        if os.path.exists(os.path.join(carpeta, registro.RESULT)):
            continue
        tomado = registro.Tomado(carpeta)
        if not tomado:
            continue
        try:
            derivado = registro.estado(proyecto, clave, execution_id)
            if derivado["estado"] != registro.RUNNING:
                continue
            cerrada = _cerrar_huerfana(proyecto, carpeta, derivado)
            if cerrada is not None:
                cerradas.append(cerrada)
        finally:
            tomado.soltar()
    registro.barrer(proyecto, clave)
    registro.limpiar_temporales(proyecto, clave)
    return cerradas


def _cerrar_huerfana(proyecto, carpeta, derivado):
    """Una RUNNING sin motor: CANCELLED si el pedido de cancelar ya estaba persistido, si no
    FAILED con HOST_INTERRUPTED (MD-24). Sin AgentReport, aunque haya quedado un output.md."""
    request, entrega = derivado["request"], derivado["entrega"] or {}
    antes = entrega.get("antes") if isinstance(entrega.get("antes"), dict) else {}
    ev = evidencia.comparar(antes, evidencia.instantanea(proyecto))
    cancelada = os.path.exists(os.path.join(carpeta, registro.CANCELACION))
    inicio = entrega.get("deliveredAt") if isinstance(entrega.get("deliveredAt"), str) else None
    if cancelada:
        resultado = _resultado(request, contrato.huella(request), "CANCELLED", "CANCELLED",
                               "cancelada a pedido; el motor murio antes de cumplirlo", None,
                               inicio, ev, host=_host_de(entrega))
    else:
        resultado = _resultado(request, contrato.huella(request), "FAILED", "HOST_INTERRUPTED",
                               "el motor murio con la Execution RUNNING; la cerro la recuperacion",
                               None, inicio, ev, host=_host_de(entrega))
    escrito = _escribir_resultado(carpeta, resultado, request)
    return {"executionId": request["executionId"], "status": escrito.get("status"),
            "code": (escrito.get("error") or {}).get("code"), "hostVivo": _host_vivo(carpeta)}


def _host_vivo(carpeta):
    doc, _ = registro.leer_json(os.path.join(carpeta, registro.PROCESO))
    return proceso.pid_vivo(doc.get("pid")) if isinstance(doc, dict) else False


# -- cancelar --------------------------------------------------------------------------------

def cancelar(proyecto, clave, execution_id, pedido_por, catalogo=None):
    """{executionId, antes, despues, pedido, resultado}. Recupera primero y pide despues: un
    pedido no llega tarde a una corrida que ya estaba cortada (MD-24). Levanta ErrorDelComando."""
    if not registro.es(registro.CLAVE_DE_TAREA, clave) or not registro.es(registro.ID,
                                                                         execution_id):
        raise ErrorDelComando("la TaskKey o el executionId no se pueden usar")
    cargar_catalogo = catalogo or limpieza.cargar_catalogo
    recuperadas = recuperar(proyecto, clave)
    if execution_id not in set(e for _, _, e, _ in registro.nombradas(proyecto, clave) if e):
        raise ErrorDelComando("%s no es una Execution de %s: ningun turno la nombra"
                              % (execution_id, clave))
    derivado = registro.estado(proyecto, clave, execution_id)
    salida = {"executionId": execution_id, "antes": derivado["estado"],
              "recuperada": any(r["executionId"] == execution_id for r in recuperadas),
              "pedido": False, "resultado": derivado["resultado"]}
    if derivado["estado"] == registro.ILEGIBLE:
        raise ErrorDelComando("%s es ilegible: %s" % (execution_id, derivado["motivo"]))
    if derivado["estado"] not in registro.ABIERTOS:
        salida["despues"] = derivado["estado"]
        return salida

    catalogo_ = _catalogo(cargar_catalogo)
    if catalogo_ is None:
        raise ErrorDelComando("no esta el catalogo de secretos: sin el no se persiste nada")
    carpeta = registro.carpeta_de(proyecto, clave, execution_id)
    por, _ = limpieza.redactar(pedido_por or "?", catalogo_, "$.pedidoPor")
    try:
        registro.escribir_json(os.path.join(carpeta, registro.CANCELACION),
                               {"pedidoEn": registro.ahora(), "pedidoPor": por})
    except FileExistsError:
        pass
    salida["pedido"] = True
    if derivado["estado"] == registro.REQUESTED:
        tomado = registro.Tomado(carpeta)
        if tomado:
            try:
                ahora_ = registro.estado(proyecto, clave, execution_id)
                if ahora_["estado"] == registro.REQUESTED:
                    request = ahora_["request"]
                    _escribir_resultado(carpeta, _resultado(
                        request, contrato.huella(request), "CANCELLED", "CANCELLED",
                        "cancelada a pedido; su motor ya no estaba", catalogo_), request)
            finally:
                tomado.soltar()
    final = registro.estado(proyecto, clave, execution_id)
    salida.update(despues=final["estado"], resultado=final["resultado"])
    return salida


# -- estado ----------------------------------------------------------------------------------

def estado(proyecto, clave):
    """[{clave, turno, executionId, estado, motivo, huerfana, hostVivo}] de cada turno. Solo lee:
    no recupera, no barre y no escribe nada (ME-E35). Una carpeta sin turno no aparece."""
    if not registro.es(registro.CLAVE_DE_TAREA, clave):
        raise ErrorDelComando("%r no es una TaskKey" % (clave,))
    filas = []
    for hexa, numero, execution_id, motivo in registro.nombradas(proyecto, clave):
        fila = {"clave": "sha256:" + hexa, "turno": numero, "executionId": execution_id,
                "estado": registro.ILEGIBLE, "motivo": motivo, "huerfana": False,
                "hostVivo": False}
        if execution_id is not None:
            derivado = registro.estado(proyecto, clave, execution_id)
            carpeta = registro.carpeta_de(proyecto, clave, execution_id)
            fila.update(estado=derivado["estado"], motivo=derivado["motivo"])
            if derivado["estado"] in registro.ABIERTOS:
                fila["huerfana"] = registro.candado_libre(carpeta) is True
            if derivado["estado"] in registro.ABIERTOS + ("FAILED", "CANCELLED"):
                fila["hostVivo"] = _host_vivo(carpeta)
        filas.append(fila)
    return filas
