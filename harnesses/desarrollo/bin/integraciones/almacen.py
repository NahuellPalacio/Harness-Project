"""El almacen de secretos. Una interfaz, un backend, y la promesa de que el valor no sale.

    get(nombre) / set(nombre, valor) / exists(nombre) / remove(nombre)

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

    def _escribir(self, lineas):
        try:
            with open(self.ruta, "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(lineas))
                if lineas:
                    f.write("\n")
        except OSError as e:
            raise ErrorDeAlmacen("no se pudo escribir %s (%s)" % (self.ruta, e.strerror))

    def set(self, nombre, valor):
        """Reescribe solo la linea de esa variable. El resto del archivo no se mueve.

        Comentarios, orden y variables ajenas quedan como estaban: el `.env` es de la
        persona, y un archivo reordenado por una herramienta es un archivo que la
        persona deja de reconocer.
        """
        if valor is None:
            raise ErrorDeAlmacen("no se puede guardar un valor vacio en %s" % nombre)
        lineas = self._lineas()
        escrito = False
        for i, linea in enumerate(lineas):
            m = _LINEA.match(linea)
            if m and m.group(1) == nombre:
                lineas[i] = "%s=%s" % (nombre, valor)
                escrito = True
                break
        if not escrito:
            lineas.append("%s=%s" % (nombre, valor))
        self._escribir(lineas)

    def remove(self, nombre):
        """Saca la linea. Devuelve si habia algo que sacar."""
        lineas = self._lineas()
        quedan = [l for l in lineas if not (_LINEA.match(l) and _LINEA.match(l).group(1) == nombre)]
        if len(quedan) == len(lineas):
            return False
        self._escribir(quedan)
        return True

    def __repr__(self):
        return "AlmacenSecretos(%s)" % os.path.basename(self.ruta)
