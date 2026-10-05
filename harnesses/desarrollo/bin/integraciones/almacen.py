"""El almacen de secretos. Una interfaz, un backend, y la promesa de que el valor no sale.

    get(nombre) / exists(nombre)          leen
    set(nombre, valor) / remove(nombre)   levantan: el `.env` es de la persona (Wave 6)

El resto del harness depende de esta interfaz y no sabe donde viven fisicamente los
secretos. Hoy el backend es el `.env` de la raiz del proyecto, que ya viene protegido
por tres capas desde 0.15.0: `.gitignore` lo excluye del repositorio, `permissions.deny`
le impide a Claude leerlo, y el hook de PreToolUse impide escribir un token literal.
Cambiarlo manana por el Credential Manager de Windows o por Vault es reemplazar esta
clase y nada mas.

🔴 Ningun metodo de este modulo imprime, registra ni mete un valor adentro del texto
de una excepcion. Un mensaje de error que dice "no se pudo guardar JIRA_TOKEN=abc123"
acaba de publicar el secreto en la consola, en la transcripcion de la sesion y en el
contexto del modelo.
"""
import os
import re

# Una variable con esta forma no esta cargada: es el placeholder instructivo que
# reparte .env.example. Sin esto, el harness leeria "<tu-token-de-jira>" como un
# token real y saldria a la red a validarlo.
_PLACEHOLDER = re.compile(r"^<[^>]*>$")

_LINEA = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$")


def es_valor_vacio(valor):
    """Vacio, solo espacios, o un placeholder entre angulos."""
    if valor is None:
        return True
    limpio = valor.strip()
    return limpio == "" or bool(_PLACEHOLDER.match(limpio))


def _sin_comillas(valor):
    v = valor.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


class ErrorDeAlmacen(Exception):
    """Algo no se pudo leer o escribir. Nunca lleva el valor adentro."""


def leer_lineas(ruta):
    """Las lineas del `.env`, o [] si no existe. Levanta ErrorDeAlmacen si no se puede leer.

    🔴 Un `.env` que no es UTF-8 levanta sin el `UnicodeDecodeError` adentro: su texto trae el
    byte que fallo y su posicion, y eso es un pedazo del archivo.
    """
    if not os.path.exists(ruta):
        return []
    if not os.path.isfile(ruta):
        raise ErrorDeAlmacen("no se pudo leer %s (no es un archivo)" % ruta)
    try:
        with open(ruta, "r", encoding="utf-8-sig") as f:
            return f.read().splitlines()
    except UnicodeDecodeError:
        raise ErrorDeAlmacen("no se pudo leer %s (no esta en UTF-8)" % ruta)
    except OSError as e:
        raise ErrorDeAlmacen("no se pudo leer %s (%s)" % (ruta, e.strerror))


def asignaciones(lineas):
    """Las asignaciones del `.env`, en orden: [(nombre, valor sin comillas)].

    Es el unico parser del `.env` del harness. Lo usan `get` y el resolvedor de
    `entorno.py`: dos parsers con reglas parecidas terminan leyendo valores distintos.
    Una variable repetida aparece las dos veces; `get` se queda con la primera.
    """
    salida = []
    for linea in lineas:
        m = _LINEA.match(linea)
        if m:
            salida.append((m.group(1), _sin_comillas(m.group(2))))
    return salida


def posiciones(lineas):
    """Donde esta cada asignacion: [(linea, columna, nombre, cargada)], sin ningun valor.

    Las mismas reglas que `asignaciones` -la misma expresion-, con la posicion en vez del
    valor. `linea` y `columna` empiezan en 1; la columna es la del nombre, despues de un
    `export`. `cargada` es si el valor sirve (no vacio ni placeholder): se mira y se tira.
    Lo usa el localizador de `flujo/entrada_humana.py`, que no puede devolver lo que no ve.
    """
    salida = []
    for numero, linea in enumerate(lineas, 1):
        m = _LINEA.match(linea)
        if m:
            salida.append((numero, m.start(1) + 1, m.group(1),
                           not es_valor_vacio(_sin_comillas(m.group(2)))))
    return salida


class AlmacenSecretos(object):
    def __init__(self, ruta_env, entorno=None):
        self.ruta = ruta_env
        self._entorno = os.environ if entorno is None else entorno

    # -- lectura ---------------------------------------------------------------

    def _lineas(self):
        return leer_lineas(self.ruta)

    def _del_archivo(self, nombre):
        for clave, valor in asignaciones(self._lineas()):
            if clave == nombre:
                return valor
        return None

    def get(self, nombre):
        """El valor, o None si no esta cargado.

        El entorno del proceso le gana al archivo: es lo que permite correr esto en
        una maquina donde los secretos los inyecta otra cosa, sin tocar el `.env`.
        """
        del_entorno = self._entorno.get(nombre)
        if not es_valor_vacio(del_entorno):
            return del_entorno.strip()
        valor = self._del_archivo(nombre)
        return None if es_valor_vacio(valor) else valor

    def exists(self, nombre):
        return self.get(nombre) is not None

    # -- escritura -------------------------------------------------------------
    #
    # 🔴 El harness no escribe la configuracion de la persona (entorno primero, 0.26.0). Desde
    # entonces nadie llamaba a set ni a remove; la Wave 6 los cierra para que tampoco los pueda
    # llamar nadie despues. Levantan sin abrir el archivo, y el mensaje no lleva el valor.

    def set(self, nombre, valor):
        raise ErrorDeAlmacen(
            "el harness no escribe %s: el .env es de la persona. Editalo vos y retomá con "
            "`flujo <KEY> --resume`." % nombre)

    def remove(self, nombre):
        raise ErrorDeAlmacen(
            "el harness no borra %s: el .env es de la persona. Editalo vos." % nombre)

    def __repr__(self):
        return "AlmacenSecretos(%s)" % os.path.basename(self.ruta)
