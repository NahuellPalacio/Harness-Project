"""El registro central de capacidades. Lo soportado contra lo disponible.

    registrar / quitar / esta_disponible / disponibles / por_integracion

🔴 La regla que justifica que esto exista: una capacidad no queda habilitada si la
integracion de la que depende no se valido. Sin un lugar donde eso se decida una sola
vez, cada consumidor futuro tendria que acordarse de preguntarlo, y el primero que se
olvide le entrega a un agente una tool que no funciona.

El documento distingue las dos cosas a proposito:

    soportada  -> el harness sabe hacerlo (lo declara la clase de integracion: `CAPACIDADES`
                  de `IntegracionJira` y de `IntegracionGitLab`)
    disponible -> ademas se valido ENABLED en esta maquina (lo decide la corrida)

`capacidadesSoportadas` de `manifest.json` no se lee en tiempo de ejecucion: es una copia que
un test contrasta contra las clases. Lo que corre usa las clases.

Una capacidad soportada cuya integracion esta caida figura DISABLED, nunca ausente:
una lista que se acorta no explica por que se acorto.
"""
import json
import os

ENABLED = "ENABLED"
DISABLED = "DISABLED"

VERSION_DOCUMENTO = "integraciones/1.0"


class RegistroCapacidades(object):
    def __init__(self, soportadas, modo=None):
        """soportadas: {"jira": ("jira.issue.read", ...), "gitlab": (...)}

        modo: de donde salio la configuracion (ENVIRONMENT_FIRST). Va al documento tal cual.
        """
        self._soportadas = {k: tuple(v) for k, v in soportadas.items()}
        self._modo = modo
        self._habilitadas = {}
        self._integraciones = {}

    # -- integraciones ---------------------------------------------------------

    def anotar(self, nombre, resultado):
        """Guarda el estado de una integracion y registra sus capacidades validadas."""
        self._integraciones[nombre] = {
            "estado": resultado["estado"],
            "motivo": resultado["motivo"],
            "verificado_en": resultado["verificado_en"],
            "capacidades": list(resultado["capacidades"]),
            "diagnostico": list(resultado.get("diagnostico") or []),
            # Los nombres de variable del .env que faltan. Nombres, nunca valores: lo lee la
            # bienvenida para decir que completar.
            "faltan": [str(v) for v in (resultado.get("faltan") or [])],
        }
        for capacidad in resultado["capacidades"]:
            self.registrar(capacidad, nombre)

    # -- capacidades -----------------------------------------------------------

    def soportadas(self):
        todas = []
        for nombre in sorted(self._soportadas):
            todas.extend(self._soportadas[nombre])
        return sorted(todas)

    def registrar(self, capacidad, integracion):
        if capacidad not in self._soportadas.get(integracion, ()):
            raise ValueError("%s no es una capacidad soportada por %s" % (capacidad, integracion))
        self._habilitadas[capacidad] = integracion

    def quitar(self, capacidad):
        return self._habilitadas.pop(capacidad, None) is not None

    def esta_disponible(self, capacidad):
        return capacidad in self._habilitadas

    def disponibles(self):
        return sorted(self._habilitadas)

    def por_integracion(self, nombre):
        return sorted(c for c, i in self._habilitadas.items() if i == nombre)

    # -- documento -------------------------------------------------------------

    def como_documento(self, version_harness=""):
        capacidades = {}
        for capacidad in self.soportadas():
            capacidades[capacidad] = ENABLED if self.esta_disponible(capacidad) else DISABLED
        documento = {
            "schema_version": VERSION_DOCUMENTO,
            "version_harness": version_harness,
            "integraciones": self._integraciones,
            "capacidades": capacidades,
        }
        if self._modo:
            documento["configurationMode"] = self._modo
        return documento

    def escribir(self, ruta, version_harness=""):
        documento = self.como_documento(version_harness)
        carpeta = os.path.dirname(os.path.abspath(ruta))
        if carpeta and not os.path.isdir(carpeta):
            os.makedirs(carpeta)
        with open(ruta, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(documento, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return documento
