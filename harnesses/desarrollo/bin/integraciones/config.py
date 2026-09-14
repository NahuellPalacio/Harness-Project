"""La configuracion de las integraciones. Lo que NO es secreto.

    .claude/harness.integraciones.json

    {
      "jira":   { "enabled": true, "baseUrl": "...", "usuario": "..." },
      "gitlab": { "enabled": true, "baseUrl": "..." }
    }

Vive separado del `.env` por un motivo que no es prolijidad: `permissions.deny` le
impide a Claude leer `.env` y `.env.*`. Con la baseUrl adentro del `.env`, el agente
no puede saber ni con que instancia de Jira habla el proyecto -que no es un secreto y
es informacion util-. Separandolos, cada archivo queda del lado correcto de una
frontera que ya existia.

Para que la separacion no dependa de que alguien se acuerde, `guardar` rechaza toda
clave que tenga forma de secreto.
"""
import json
import os

CLAVES_PROHIBIDAS = ("TOKEN", "SECRET", "PASSWORD", "PASSWD", "CREDENTIAL", "APIKEY", "API_KEY")


class ConfigIlegible(Exception):
    """El archivo existe y no se pudo leer. La persona tiene que arreglarlo.

    🔴 El mensaje dice QUE HACER, no solo que algo salio mal. Es la misma regla que
    docs/secretos.md le impone al detector: "usa una variable de entorno" sirve,
    "operacion denegada" no. Un mensaje que describe el sintoma deja a la persona
    exactamente donde estaba.
    """


QUE_HACER = ("Corregilo a mano, o borralo y corre el setup del harness: se vuelve a "
             "crear vacio y no lleva ningun secreto adentro.")


class ClaveProhibida(Exception):
    """Alguien intento guardar un secreto adentro de la configuracion."""


def es_clave_de_secreto(clave):
    arriba = clave.upper()
    return any(p in arriba for p in CLAVES_PROHIBIDAS)


class ConfigIntegraciones(object):
    def __init__(self, ruta):
        self.ruta = ruta

    def leer(self):
        """El documento entero. Un archivo que no existe es una configuracion vacia."""
        if not os.path.isfile(self.ruta):
            return {}
        try:
            with open(self.ruta, "r", encoding="utf-8-sig") as f:
                datos = json.load(f)
        except ValueError as e:
            raise ConfigIlegible("%s no es un JSON valido (%s). %s" % (self.ruta, e, QUE_HACER))
        except OSError as e:
            raise ConfigIlegible("no se pudo leer %s (%s). %s"
                                 % (self.ruta, e.strerror, QUE_HACER))
        if not isinstance(datos, dict):
            raise ConfigIlegible("%s tiene que ser un objeto JSON, y no lo es. %s"
                                 % (self.ruta, QUE_HACER))
        return datos

    def de(self, nombre):
        """La configuracion de una integracion. Vacia si no figura."""
        bloque = self.leer().get(nombre)
        return bloque if isinstance(bloque, dict) else {}

    def guardar(self, nombre, datos):
        """Reemplaza el bloque de una integracion y deja el resto del archivo igual.

        Lo que el harness no conoce -una integracion futura, una clave agregada a
        mano- sobrevive: este archivo es del proyecto, no de esta version del codigo.
        """
        for clave in datos:
            if es_clave_de_secreto(clave):
                raise ClaveProhibida(
                    "'%s' tiene forma de secreto y la configuracion no guarda secretos. "
                    "Los tokens van al .env, por el almacen." % clave)
        documento = self.leer()
        documento[nombre] = dict(datos)
        carpeta = os.path.dirname(os.path.abspath(self.ruta))
        if carpeta and not os.path.isdir(carpeta):
            os.makedirs(carpeta)
        texto = json.dumps(documento, ensure_ascii=False, indent=2, sort_keys=True)
        with open(self.ruta, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto + "\n")
