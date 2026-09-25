#!/usr/bin/env python3
"""La Context Bar: la statusLine de la terminal, dibujada con lo que resume el Bloque 4.

El cliente la invoca al empezar la sesion y despues de cada mensaje, con un JSON por stdin.
En cada invocacion hace cinco cosas, en este orden:

    1. lee de stdin `session_id` y `transcript_path`, y nada mas;
    2. ingiere la transcripcion con el adaptador que declara el registro, al libro de la
       sesion (.claude/runtime/accounting/<session_id>/ledger.jsonl). El libro deduplica por
       eventId: ingerir dos veces no suma dos veces;
    3. pide `barra.de(...)` y lo dibuja en UNA linea;
    4. escribe su senal de vida, .claude/runtime/contextbar.json, con
       bienvenida.escribir_senal_de_vida y la huella que el comando le paso como ultimo
       argumento: es lo unico que prueba que la barra esta activa;
    5. sale con 0 siempre, y nunca en blanco: si algo falla dibuja LINEA_SIN_DATOS.

🔴 El costo y el contexto que el cliente manda por stdin NO se usan. Dibujarlos seria una
segunda fuente contable: el Bloque 4 es la unica, y si esos datos hacen falta entran por un
adaptador, no por aca.

🔴 Un campo que el Bloque 4 no tiene no aparece. No sale como 0, ni como `?`: un costo
COST_UNRESOLVED no es `USD 0`, y una ventana sin limite conocido no tiene porcentaje.

🔴 No dibuja texto de la transcripcion. Lo unico que viene de ahi es el nombre del modelo, y
entra solo si tiene forma de identificador y el catalogo de secretos no reconoce nada en el.

🔴 No escribe nada fuera del libro de la sesion y de la senal de vida. Ni bytecode: al correr
como la statusLine no deja __pycache__.

📌 La salida es ASCII. La barra corre en Git Bash o en PowerShell segun la maquina, y
PowerShell 5.1 vuelve a codificar la salida de un programa con la codepage de la consola.
"""
import importlib.util
import json
import os
import re
import sys

INTEGRATION_VERSION = "1.0.0"

LINEA_SIN_DATOS = "HARNESS | sin datos del Bloque 4"
_SEPARADOR = " | "

# Un session_id es el nombre de una carpeta del libro: nada que pueda salir de accounting/.
_SESION_VALIDA = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
# Lo que se muestra de un texto que viene del libro -modelo, tarea, agente-: un
# identificador, no una frase. Un espacio ya no es un identificador, y un prompt no entra.
_IDENTIFICADOR = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/+-]{0,63}$")

# El ultimo argumento del comando registrado: la huella de su propio bloque statusLine.
_HUELLA = re.compile(r"^[0-9a-f]{64}$")

_AQUI = os.path.dirname(os.path.abspath(__file__))
_BIN = os.path.dirname(_AQUI)


# -- donde esta cada cosa ----------------------------------------------------------

def proyecto_de(ruta_del_script):
    """La raiz del proyecto: la carpeta que tiene el `.claude/harness/` del que corre esto.

    None si el script no esta instalado -corre desde el repositorio del harness-. La barra
    no mira el directorio de trabajo: el cliente no promete cual es.
    """
    d = os.path.dirname(os.path.abspath(ruta_del_script))
    while True:
        arriba = os.path.dirname(d)
        if arriba == d:
            return None
        if os.path.basename(d) == "harness" and os.path.basename(arriba) == ".claude":
            return os.path.dirname(arriba)
        d = arriba


def _bloque4():
    """Los modulos del Bloque 4. Un import que falla es SOURCE_UNAVAILABLE, no un traceback."""
    if _BIN not in sys.path:
        sys.path.insert(0, _BIN)
    from contabilidad import barra, libro, presupuesto, tiempo
    from contabilidad.adaptadores import contrato, registro
    from contexto import limpieza
    return {"barra": barra, "libro": libro, "presupuesto": presupuesto, "tiempo": tiempo,
            "contrato": contrato, "registro": registro, "limpieza": limpieza}


_BIENVENIDA = []


def bienvenida():
    """hooks/lib/bienvenida.py, cargado por ruta como lo carga dev-harness.py: es quien sabe
    escribir la senal de vida y calcular la huella con la que despues se la compara."""
    if _BIENVENIDA:
        return _BIENVENIDA[0]
    if _BIN not in sys.path:
        sys.path.insert(0, _BIN)
    import rutas
    raiz = rutas.raiz_del_harness(__file__)
    ruta = os.path.join(raiz, "hooks", "lib", "bienvenida.py") if raiz else None
    if not ruta or not os.path.isfile(ruta):
        raise OSError("no esta hooks/lib/bienvenida.py al lado del harness")
    spec = importlib.util.spec_from_file_location("harness_bienvenida", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    _BIENVENIDA.append(modulo)
    return modulo


# -- 1. la entrada -------------------------------------------------------------------

def leer_entrada(crudo):
    """(session_id, transcript_path) de lo que llego por stdin, o (None, None).

    Del JSON se leen esas dos claves y ninguna otra: ni `cost`, ni el contexto, ni el modelo.
    """
    try:
        datos = json.loads((crudo or b"").decode("utf-8-sig"))
    except (ValueError, UnicodeDecodeError):
        return None, None
    if not isinstance(datos, dict):
        return None, None
    sesion = datos.get("session_id")
    transcripcion = datos.get("transcript_path")
    if not isinstance(sesion, str) or not _SESION_VALIDA.match(sesion) \
            or sesion in (".", ".."):
        return None, None
    if not isinstance(transcripcion, str) or not transcripcion.strip():
        transcripcion = None
    return sesion, transcripcion


# -- 2. la ingesta -------------------------------------------------------------------

def ultima_linea(leidos, archivo):
    """Hasta que linea de `archivo` ya llego el libro, segun las referencias de sus eventos.

    Es el cursor de la barra, y no vive en otro archivo: el libro ya dice de que linea salio
    cada evento (`source.rawReference`, `<archivo>#L<n>`). Lo que queda despues se vuelve a
    leer, y lo que se repite lo descarta el eventId.
    """
    prefijo = str(archivo) + "#L"
    hasta = 0
    for evento in leidos:
        ref = str((evento.get("source") or {}).get("rawReference") or "")
        if ref.startswith(prefijo) and ref[len(prefijo):].isdigit():
            hasta = max(hasta, int(ref[len(prefijo):]))
    return hasta


def ingerir(b4, proyecto, sesion, transcripcion, politica):
    """Pasa lo nuevo de la transcripcion al libro de la sesion y devuelve el libro leido.

    Se saltea antes de convertir lo que el libro ya tiene: el id del evento se sabe desde el
    registro, y convertir y validar cientos de registros viejos en cada mensaje era lo que
    hacia lenta a la barra. Un registro sin resolver -la transcripcion todavia no tiene
    consumo- no se escribe: su id se inventa en cada corrida, y la barra dejaria uno por
    mensaje.
    """
    libro, contrato, registro = b4["libro"], b4["contrato"], b4["registro"]
    ruta = libro.ruta_de(proyecto, sesion)
    leidos = libro.leer(ruta)
    if transcripcion and os.path.isfile(transcripcion):
        adaptador = registro.DE_LA_BARRA
        conocidos = set(str(e.get("eventId") or "") for e in leidos)
        leidas = registro.resolver(adaptador).leer(
            transcripcion, rapido=True,
            desde_linea=ultima_linea(leidos, os.path.basename(transcripcion)))
        nuevos = [r for r in leidas
                  if r.get("state") != contrato.SIN_RESOLVER
                  and contrato.id_de(r, adaptador) not in conocidos]
        if nuevos:
            eventos_ = contrato.a_eventos(nuevos, sesion, adaptador, politica, sessionId=sesion)
            escritos, _, _ = libro.agregar_varios(ruta, eventos_)
            if escritos:
                leidos = libro.leer(ruta)
    return leidos


# -- 3. el dibujo --------------------------------------------------------------------

def _cantidad(n):
    n = int(n)
    if n >= 1000000:
        return "%.1fM" % (n / 1000000.0)
    if n >= 1000:
        return "%dk" % int(round(n / 1000.0))
    return str(n)


def _porcentaje(fraccion):
    return "%d%%" % int(round(float(fraccion) * 100))


def _identificador(valor, catalogo, limpieza):
    """El texto si es un identificador que el catalogo de secretos no reconoce; si no, None."""
    if not isinstance(valor, str) or not _IDENTIFICADOR.match(valor):
        return None
    limpio, hallazgos = limpieza.redactar(valor, catalogo, "la barra")
    if hallazgos or limpio != valor:
        return None
    return valor


def dibujar(estado, b4, politica_ilegible=False):
    """La linea, con solo lo que `estado` -el de barra.de- tiene. Lo que falta no aparece."""
    limpieza = b4["limpieza"]
    catalogo = limpieza.cargar_catalogo()
    abiertos = set(estado.get("unresolved") or ())
    partes = ["HARNESS"]

    modelo = _identificador(estado.get("model"), catalogo, limpieza)
    if modelo:
        partes.append(modelo)

    contexto = estado.get("context") or {}
    if contexto.get("fraction") is not None:
        partes.append("Ctx " + _porcentaje(contexto["fraction"]))
    elif contexto.get("tokens") is not None:
        partes.append("Ctx %s" % _cantidad(contexto["tokens"]))

    tokens = estado.get("tokens") or {}
    entrada = sum(int(tokens.get(c) or 0) for c in ("inputTokens", "cacheReadTokens",
                                                   "cacheCreationTokens"))
    salida = int(tokens.get("outputTokens") or 0)
    if "USAGE_UNRESOLVED" not in abiertos and (entrada or salida):
        partes.append("Tok %s in / %s out" % (_cantidad(entrada), _cantidad(salida)))

    # Un total con algo sin resolver adentro es un piso, no un total: no se muestra como uno.
    presupuesto = estado.get("budget") or {}
    monto = presupuesto.get("amount")
    if monto is not None and "COST_UNRESOLVED" not in abiertos:
        moneda = presupuesto.get("currency") or ""
        marca = "" if presupuesto.get("field") == "actual" else " eq"
        partes.append(("%s %.2f%s" % (moneda, float(monto), marca)).strip())

    tiempo_ = (estado.get("time") or {}).get("wallMs")
    if tiempo_ is not None:
        partes.append(b4["tiempo"].como_texto(tiempo_))

    if presupuesto.get("fraction") is not None:
        partes.append("Budget " + _porcentaje(presupuesto["fraction"]))
    elif politica_ilegible:
        partes.append("presupuesto ilegible")

    niveles = (contexto.get("level"), presupuesto.get("level"))
    if "ERROR" in niveles:
        partes.append("ERROR")
    elif "WARNING" in niveles:
        partes.append("WARNING")

    # La sesion es la tarea mientras nadie declare una: la tarea aparece solo si es otra.
    tarea = _identificador(estado.get("taskId"), catalogo, limpieza)
    if tarea and tarea != estado.get("sessionId"):
        partes.append("Tarea " + tarea)
    agente = _identificador(estado.get("agentId"), catalogo, limpieza)
    if agente:
        partes.append("Agente " + agente)

    if len(partes) == 1:
        return LINEA_SIN_DATOS
    return _SEPARADOR.join(partes)


# -- todo junto ------------------------------------------------------------------------

def huella_del_comando(argv):
    """La huella que el comando registrado se paso a si mismo como ultimo argumento, o None.

    Es la que va a la senal de vida, tal cual: prueba que corrio ESTE comando. Leerla de
    settings.json al escribir haria que un comando viejo, que sigue corriendo en una sesion
    sin reiniciar, probara la configuracion nueva (E-41). Un comando sin huella -uno de antes
    de este cambio- deja null, que no prueba nada.
    """
    ultimo = argv[-1] if len(argv) > 1 else ""
    return ultimo if _HUELLA.match(str(ultimo)) else None


def correr(crudo, proyecto, momento=None, huella=None):
    """(linea, block4 o None). Nunca levanta.

    block4 es lo que queda en la senal de vida: OK si el Bloque 4 respondio -con o sin datos
    todavia-, SOURCE_UNAVAILABLE si no se pudo cargar, ingerir o leer. None si no hubo senal:
    sin sesion no hay a quien atribuirla.
    """
    sesion, transcripcion = leer_entrada(crudo)
    if not proyecto or not sesion:
        return LINEA_SIN_DATOS, None

    linea, block4 = LINEA_SIN_DATOS, "SOURCE_UNAVAILABLE"
    try:
        b4 = _bloque4()
        # El session_id se vuelve el nombre de una carpeta del libro y queda en la senal de
        # vida. Uno que el catalogo de secretos reconoce no va a ninguno de los dos lados.
        if _identificador(sesion, b4["limpieza"].cargar_catalogo(), b4["limpieza"]) is None:
            return LINEA_SIN_DATOS, None
        politica_ilegible = False
        try:
            politica = b4["presupuesto"].cargar(
                os.path.join(proyecto, ".claude", "harness.presupuesto.json"))
        except (ValueError, OSError, b4["presupuesto"].PoliticaInvalida):
            politica, politica_ilegible = None, True
        libro_leido = ingerir(b4, proyecto, sesion, transcripcion, politica)
        block4 = "OK"
        if b4["barra"].de_sesion(libro_leido, sesion):
            estado = b4["barra"].de(libro_leido, sesion, politica)
            linea = dibujar(estado, b4, politica_ilegible)
    except Exception:                   # noqa: BLE001 - la barra no se cae nunca
        linea = LINEA_SIN_DATOS

    try:
        bienvenida().escribir_senal_de_vida(proyecto, sesion, block4, INTEGRATION_VERSION,
                                            momento=momento, huella=huella)
    except Exception:                   # noqa: BLE001 - sin senal la barra dibuja igual
        block4 = None
    return linea, block4


def _stdin():
    try:
        if sys.stdin is None or sys.stdin.isatty():
            return b""
        return sys.stdin.buffer.read()
    except (OSError, ValueError, AttributeError):
        return b""


def main():
    linea = LINEA_SIN_DATOS
    try:
        linea = correr(_stdin(), proyecto_de(__file__),
                       huella=huella_del_comando(sys.argv))[0] or LINEA_SIN_DATOS
    except Exception:                   # noqa: BLE001 - salida vacia es barra en blanco
        linea = LINEA_SIN_DATOS
    try:
        sys.stdout.buffer.write(linea.encode("ascii", "replace") + b"\n")
        sys.stdout.flush()
    except Exception:                   # noqa: BLE001
        pass
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    sys.path[0] = _BIN
    sys.exit(main())
