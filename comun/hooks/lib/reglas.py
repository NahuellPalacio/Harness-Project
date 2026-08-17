"""Carga y ejecucion de los checks que aportan comun y los harness instalados.

Los hooks son cuatro y son infraestructura. Los checks son N y son reglas. La
separacion existe para que agregar una regla no pueda romper el manejo de stdin,
el encoding ni el control de errores.

Contrato de un check: un .py con verificar(evento, proyecto, config) que devuelve
cero o mas strings. Cada string es un hallazgo.
"""
import importlib.util
import json
import os

# Presupuesto de salida. PostToolUse corre despues de cada escritura de cada sesion:
# una tanda larga de avisos deja de leerse y el harness se vuelve ruido de fondo.
MAX_HALLAZGOS = 8


def config_proyecto(proyecto):
    if not proyecto:
        return None
    ruta = os.path.join(proyecto, ".claude", "harness.config.json")
    if not os.path.exists(ruta):
        return None
    try:
        with open(ruta, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _cargar(ruta):
    """Por ruta y no por nombre de modulo: los checks se llaman dev-api-rutas.py y
    un guion no es un nombre importable. El descubrimiento sigue siendo estar en
    el directorio."""
    nombre = "check_" + os.path.basename(ruta).replace("-", "_")[:-3]
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def correr_checks(evento, dir_checks, proyecto, config):
    hallazgos = []
    if not dir_checks or not os.path.isdir(dir_checks):
        return hallazgos

    rutas = []
    for raiz, _dirs, archivos in os.walk(dir_checks):
        for a in archivos:
            if a.endswith(".py") and not a.startswith("__"):
                rutas.append(os.path.join(raiz, a))
    rutas.sort()

    for ruta in rutas:
        try:
            modulo = _cargar(ruta)
            salida = modulo.verificar(evento, proyecto, config)
            for s in (salida or []):
                if s and str(s).strip():
                    hallazgos.append(str(s).strip())
        except BaseException:      # noqa: BLE001
            # Un check roto se saltea en silencio. Reportarlo en cada escritura
            # seria peor que el problema que quiso evitar.
            pass
        if len(hallazgos) >= MAX_HALLAZGOS:
            break

    return hallazgos[:MAX_HALLAZGOS]
