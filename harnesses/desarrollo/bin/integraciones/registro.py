"""El registro central de capacidades. Lo soportado contra lo disponible.

    registrar / quitar / esta_disponible / disponibles / por_integracion

🔴 La regla que justifica que esto exista: una capacidad no queda habilitada si la
integracion de la que depende no se valido. Sin un lugar donde eso se decida una sola
vez, cada consumidor futuro tendria que acordarse de preguntarlo, y el primero que se
olvide le entrega a un agente una tool que no funciona.

El documento distingue las dos cosas a proposito:

    soportada  -> el harness sabe hacerlo (lo declara el manifiesto de `desarrollo`)
    disponible -> ademas esta validado ahora (lo decide la corrida)

Una capacidad soportada cuya integracion esta caida figura DISABLED, nunca ausente:
una lista que se acorta no explica por que se acorto.
"""
import json
import os

ENABLED = "ENABLED"
DISABLED = "DISABLED"

VERSION_DOCUMENTO = "integraciones/1.0"


class RegistroCapacidades(object):
    def __init__(self, soportadas):
        """soportadas: {"jira": ("jira.issue.read", ...), "gitlab": (...)}"""
        self._soportadas = {k: tuple(v) for k, v in soportadas.items()}
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
        return {
            "schema_version": VERSION_DOCUMENTO,
            "version_harness": version_harness,
            "integraciones": self._integraciones,
            "capacidades": capacidades,
        }

    def escribir(self, ruta, version_harness=""):
        documento = self.como_documento(version_harness)
        carpeta = os.path.dirname(os.path.abspath(ruta))
        if carpeta and not os.path.isdir(carpeta):
            os.makedirs(carpeta)
        with open(ruta, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(documento, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return documento
