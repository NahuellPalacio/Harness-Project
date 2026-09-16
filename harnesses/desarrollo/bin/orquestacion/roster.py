"""Quien deberia existir para orquestar una tarea, y quien existe de verdad.

🔴 El roster declara; el disco decide. `reglas/roster.json` dice que `dev-backend` es el
especialista de backend; que exista o no lo contesta el sistema de archivos. Al reves -una
lista de lo que hay- envejece sola: el dia que alguien escribe el agente, tiene que
acordarse de anotarlo, y si no se acuerda el harness sigue diciendo que no esta.

Asi, un agente declarado y sin archivo es un hueco que se ve en cada plan, y deja de serlo
el dia que aparece el archivo, sin tocar un dato.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas  # noqa: E402

_CACHE = {}


def _raices_de_reglas(desde):
    """Donde puede estar reglas/ de este harness.

    Instalado, el instalador lo deja en `.claude/harness/reglas/desarrollo/`. En el
    repositorio vive en `harnesses/desarrollo/reglas/`. Las dos cuelgan a distinta altura,
    asi que se prueban las dos formas.
    """
    aqui = os.path.dirname(os.path.abspath(desde))
    bin_dev = os.path.dirname(aqui)
    extra = [os.path.join(os.path.dirname(bin_dev), "desarrollo")]
    harness = rutas.raiz_del_harness(desde)
    if harness:
        extra.append(os.path.join(harness, "reglas"))
    extra.append(os.path.dirname(os.path.dirname(bin_dev)))
    return extra


def ruta_de_regla(nombre, desde=__file__):
    """La ruta de un archivo de `reglas/` de este harness, o None."""
    for relativa in ((nombre,), ("reglas", nombre), ("desarrollo", nombre)):
        ruta = rutas.localizar(relativa, desde, _raices_de_reglas(desde))
        if ruta:
            return ruta
    return None


def cargar(desde=__file__):
    """El roster como dato. Vacio si no se encontro: el plan lo declara y sigue."""
    if "roster" in _CACHE:
        return _CACHE["roster"]
    ruta = ruta_de_regla("roster.json", desde)
    datos = {}
    if ruta:
        try:
            with io.open(ruta, encoding="utf-8-sig") as f:
                datos = json.load(f)
        except (ValueError, OSError):
            datos = {}
    _CACHE["roster"] = datos
    return datos


def _dir_del_harness(desde=__file__):
    """El directorio que contiene agents/ y skills/ de este harness.

    Instalado, los agentes van a `.claude/agents/` y las skills a `.claude/skills/`: no
    cuelgan del harness sino de `.claude`. En el repositorio cuelgan de
    `harnesses/desarrollo/`. Se devuelven las dos para que quien busca pruebe las dos.
    """
    aqui = os.path.dirname(os.path.abspath(desde))
    bin_dev = os.path.dirname(aqui)
    del_repo = os.path.dirname(bin_dev)
    harness = rutas.raiz_del_harness(desde)
    instalado = os.path.dirname(harness) if harness else None
    return [d for d in (del_repo, instalado) if d]


def existe_agente(nombre, desde=__file__):
    return any(os.path.isfile(os.path.join(d, "agents", nombre + ".md"))
               for d in _dir_del_harness(desde))


def existe_skill(nombre, desde=__file__):
    return any(os.path.isfile(os.path.join(d, "skills", nombre, "SKILL.md"))
               for d in _dir_del_harness(desde))


def existe_check(nombre, desde=__file__):
    for d in _dir_del_harness(desde):
        if os.path.isfile(os.path.join(d, "checks", nombre + ".py")):
            return True
        # Instalado, los checks de un harness van a checks/<id>/
        if os.path.isfile(os.path.join(d, "harness", "checks", "desarrollo", nombre + ".py")):
            return True
    return False


# -- consultas que usa el planificador -----------------------------------------

def agentes_para(dominios, desde=__file__):
    """Los agentes de esos dominios, con si existen. Los transversales no entran solos."""
    datos = cargar(desde)
    salida = []
    for agente in datos.get("agents", []):
        if agente.get("role") == "specialist" and agente.get("domain") in dominios:
            salida.append({"name": agente["name"], "domain": agente["domain"],
                           "role": agente["role"],
                           "exists": existe_agente(agente["name"], desde)})
    return sorted(salida, key=lambda a: a["name"])


def agente_de_dominio(dominio, desde=__file__):
    """El especialista de un dominio, o "" si el roster no declara ninguno."""
    for agente in cargar(desde).get("agents", []):
        if agente.get("role") == "specialist" and agente.get("domain") == dominio:
            return agente["name"]
    return ""


def skills_para(dominios, desde=__file__):
    salida = []
    for skill in cargar(desde).get("skills", []):
        if set(skill.get("domains", [])) & set(dominios):
            salida.append({"name": skill["name"], "exists": existe_skill(skill["name"], desde)})
    return sorted(salida, key=lambda s: s["name"])


def checks_para(dominios, desde=__file__):
    salida = []
    for check in cargar(desde).get("checks", []):
        if set(check.get("domains", [])) & set(dominios):
            salida.append({"name": check["name"], "exists": existe_check(check["name"], desde)})
    return sorted(salida, key=lambda c: c["name"])


def capacidades_locales(desde=__file__):
    """Las que da el runtime. Es una declaracion, no una comprobacion."""
    return list(cargar(desde).get("capacidadesLocales", []))


def huecos(agentes, skills, checks):
    """Lo declarado que todavia no existe, en el orden en que se lee un plan."""
    salida = []
    for a in agentes:
        if not a["exists"]:
            salida.append("el agente %s esta declarado en el roster y no tiene su .md todavia"
                          % a["name"])
    for s in skills:
        if not s["exists"]:
            salida.append("la skill %s esta declarada en el roster y no existe todavia" % s["name"])
    for c in checks:
        if not c["exists"]:
            salida.append("el check %s esta declarado en el roster y no existe todavia" % c["name"])
    return salida
