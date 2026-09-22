"""Que hay para orquestar una tarea: checks, capacidades locales y el puente al registro.

🔴 **Los agentes y las skills ya no se declaran aca.** Viven en
`reglas/agent-registry.json` y los resuelve `registro_agentes.py`. Este modulo conserva sus
funciones -`agentes_para`, `skills_para`, `existe_agente`...- como la unica puerta que el
resto del bloque ya usaba, pero la respuesta sale del registro. Dos rosters compitiendo es
peor que cualquiera de los dos solo: el dia que difieran, cada modulo va a tener razon.

Lo que sigue siendo de `roster.json` son los checks y las capacidades locales, que el
registro de agentes no cubre.

La regla vieja era "el roster declara y el disco decide". Ahora el registro declara y
tambien decide, y el disco diagnostica: un archivo que aparece solo no da de alta nada.
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


def _registro():
    """Import diferido: `registro_agentes` necesita de aca las rutas de reglas."""
    from . import registro_agentes
    return registro_agentes


def existe_agente(nombre, desde=__file__):
    """Declarado en el registro Y estructuralmente valido.

    No es "hay un archivo con ese nombre". Un `.md` que aparece solo es un huerfano, y un
    agente cuyo archivo dice ser otro, o un especialista sin una sola skill instalada, no
    existen a los efectos de rutear: se rutea cerrado.
    """
    reg = _registro()
    try:
        doc = reg.cargar(desde)
    except reg.RegistroInvalido:
        return False
    if not reg.hay_agente(nombre, doc, desde):
        return False
    informe = reg.validar_registro(doc, desde)
    return informe["agents"][nombre]["state"] in reg.AGENTE_RUTEABLE


def existe_skill(nombre, desde=__file__):
    """Declarada INSTALLED en el registro y con su SKILL.md donde el registro dice."""
    reg = _registro()
    try:
        doc = reg.cargar(desde)
    except reg.RegistroInvalido:
        return False
    informe = reg.validar_registro(doc, desde)
    return any(s["id"] == nombre and s["state"] == "SKILL_AVAILABLE"
               for s in informe["skills"].values())


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
    """Los especialistas de esos dominios, con si existen. Sale del registro."""
    reg = _registro()
    try:
        doc = reg.cargar(desde)
    except reg.RegistroInvalido:
        return []
    informe = reg.validar_registro(doc, desde)
    salida = []
    for agente in doc.get("agents", []):
        if agente.get("type") != "SPECIALIST_AGENT":
            continue
        if agente.get("domain") not in dominios:
            continue
        estado = informe["agents"][agente["id"]]["state"]
        salida.append({"name": agente["id"], "domain": agente["domain"], "role": "specialist",
                       "exists": estado in reg.AGENTE_RUTEABLE, "validation": estado})
    return sorted(salida, key=lambda a: a["name"])


def agente_de_dominio(dominio, desde=__file__):
    """El especialista de un dominio, o "" si el registro no declara ninguno."""
    reg = _registro()
    try:
        return reg.agente_de_dominio(dominio, None, desde)
    except reg.RegistroInvalido:
        return ""


def skills_para(dominios, desde=__file__):
    """Las skills de los agentes de esos dominios, con su estado del registro."""
    reg = _registro()
    try:
        doc = reg.cargar(desde)
    except reg.RegistroInvalido:
        return []
    informe = reg.validar_registro(doc, desde)
    salida = []
    for agente in doc.get("agents", []):
        if agente.get("domain") not in dominios:
            continue
        for skill in agente.get("skills", []):
            estado = informe["skills"][(agente["id"], skill["id"])]["state"]
            salida.append({"name": skill["id"], "exists": estado == "SKILL_AVAILABLE",
                           "status": skill.get("status"), "validation": estado,
                           "agent": agente["id"]})
    return sorted(salida, key=lambda s: s["name"])


def validacion_de_agente(nombre, desde=__file__):
    """El estado que el registro le dio, o AGENT_NOT_FOUND si no esta declarado."""
    if not nombre:
        return "AGENT_NOT_FOUND"
    reg = _registro()
    try:
        doc = reg.cargar(desde)
    except reg.RegistroInvalido:
        return "AGENT_NOT_FOUND"
    if not reg.hay_agente(nombre, doc, desde):
        return "AGENT_NOT_FOUND"
    return reg.validar_registro(doc, desde)["agents"][nombre]["state"]


def dominios_declarados(desde=__file__):
    """Los dominios que tienen especialista declarado. Salen del registro."""
    reg = _registro()
    try:
        doc = reg.cargar(desde)
    except reg.RegistroInvalido:
        return []
    return sorted({a.get("domain", "") for a in doc.get("agents", [])
                   if a.get("type") == "SPECIALIST_AGENT"})


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
