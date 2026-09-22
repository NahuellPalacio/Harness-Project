"""El registro de agentes: quien existe, con que skills y en que estado.

Reemplaza a "el roster declara y el disco decide". Ahora **el registro declara y decide**, y
el disco pasa a ser diagnostico: un archivo que aparece solo no da de alta nada.

    registro           ->  que agentes y que skills existen
    disco              ->  diagnostico: huerfanos y no declaradas
    matriz normativa   ->  que reglas, policies y checks aplican

🔴 Las tres capas no se cruzan. Que la matriz de ES0901 §7.1 este sin clasificar no puede
hacer que un agente declarado y valido deje de existir: son preguntas distintas y se
contestan en lugares distintos.

🔴 **Tres huecos que no son el mismo hueco.** Confundirlos es como un constructor de tools
termina fabricando conocimiento de miBA que nadie tiene:

    AGENT_NOT_FOUND         el agente no esta declarado
    SPECIALIZED_SKILL_GAP   el agente existe; su skill especializada esta declarada y
                            todavia no se puede escribir. NO deriva a dev-tool-builder
    CAPABILITY_GAP          existe todo, falta una capacidad ejecutable. Este si deriva

🔴 **Se rutea cerrado.** Ruteable es `VALID` o `VALID_WITH_PENDING_SKILLS` con la skill en
`SKILL_AVAILABLE`. Todo lo demas devuelve `routable: false`, y nada se repara solo: una ruta
mal escrita, un id que no coincide o un dominio con dos duenos se reportan, no se arreglan.
Un validador que arregla lo que lee no valida.
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402

ARCHIVO = "agent-registry.json"
ARCHIVO_HUERFANOS = "huerfanos-reconocidos.json"
SCHEMA = "agent-registry.schema.json"

TIPOS = ("ORCHESTRATOR_AGENT", "SPECIALIST_AGENT", "CRITIC_AGENT", "INFRASTRUCTURE_AGENT")
ESTADOS_COMPONENTE = ("INSTALLED", "DECLARED_NOT_INSTALLED", "DEPRECATED")

# Los unicos dos estados de agente que rutean.
AGENTE_RUTEABLE = ("VALID", "VALID_WITH_PENDING_SKILLS")
SKILL_RUTEABLE = ("SKILL_AVAILABLE",)

SEVERIDAD = {
    "VALID": "INFO",
    "SKILL_AVAILABLE": "INFO",
    "VALID_WITH_PENDING_SKILLS": "WARNING",
    "SPECIALIZED_SKILL_GAP": "WARNING",
}

_CACHE = {}


class RegistroInvalido(Exception):
    """El registro no se lee a medias."""


# -- carga ---------------------------------------------------------------------

def _ruta_de_regla(nombre, desde):
    from . import roster
    return roster.ruta_de_regla(nombre, desde)


def cargar(desde=__file__):
    """El registro como dato. Levanta si no esta: sin registro no hay agentes."""
    ruta = _ruta_de_regla(ARCHIVO, desde)
    if ruta is None:
        raise RegistroInvalido(
            "no esta %s. La existencia de un agente sale del registro, y sin registro no se "
            "adivina desde el disco." % ARCHIVO)
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        raise RegistroInvalido("%s no se pudo leer: %s" % (ruta, e))


def huerfanos_reconocidos(desde=__file__):
    """Deuda tecnica ya vista. NO es una declaracion: nada de aca existe ni rutea.

    Lo unico que compra es que un huerfano ya conocido sea aviso y no error, para que uno
    NUEVO se distinga. Vive en su propio archivo a proposito: mezclarlo con la declaracion
    de agentes seria darle a un huerfano media entrada de registro.
    """
    ruta = _ruta_de_regla(ARCHIVO_HUERFANOS, desde)
    if ruta is None:
        return []
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            return (json.load(f) or {}).get("acknowledgedOrphans") or []
    except (OSError, ValueError):
        return []


def cargar_schema(desde=__file__):
    ruta = rutas.localizar(("schemas", SCHEMA), desde)
    if ruta is None:
        raise RegistroInvalido("no esta %s; el registro no se valida sin su contrato." % SCHEMA)
    with io.open(ruta, encoding="utf-8") as f:
        return json.load(f)


def validar_schema(documento, desde=__file__):
    """Lista de errores contra agent-registry/1.0. Vacia es valido."""
    from . import tools
    armador = tools._armador()
    if armador is None:
        raise RegistroInvalido(
            "no esta comun/bin/contexto-armar.py, que es de donde sale el validador.")
    esquema = cargar_schema(desde)
    armador.controlar_soporte(esquema)
    return armador.validar(documento, esquema)


# -- identidad de un archivo ---------------------------------------------------

_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---", re.S)
_NOMBRE = re.compile(r"^name:\s*(\S+)\s*$", re.M)


def identidad(ruta, clase):
    """El id que el archivo dice ser, o "" si no lo dice.

    Dos convenciones conviven y las dos valen: el `name:` del frontmatter, que todos los
    archivos tienen, y el encabezado `# Agent:` / `# Skill:`, que traen los mas nuevos. Si
    estan los dos tienen que coincidir. Lo que NO se acepta es deducir la identidad del
    nombre del archivo: un archivo mal ubicado se validaria a si mismo.
    """
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            texto = f.read()
    except OSError:
        return ""
    del_frente = ""
    m = _FRONTMATTER.match(texto)
    if m:
        n = _NOMBRE.search(m.group(1))
        if n:
            del_frente = n.group(1)
    del_titulo = ""
    t = re.search(r"^#\s*%s:\s*(\S+)\s*$" % clase, texto, re.M)
    if t:
        del_titulo = t.group(1)
    if del_frente and del_titulo and del_frente != del_titulo:
        return "%s|%s" % (del_frente, del_titulo)      # discrepan: nunca va a coincidir
    return del_frente or del_titulo


# -- rutas del harness ---------------------------------------------------------

def raices_de_componentes(desde=__file__):
    """Los directorios que pueden contener agents/ y skills/.

    Son dos y no uno: instalado cuelgan de `.claude/`, en el repositorio de
    `harnesses/desarrollo/`. La busqueda es de `roster._dir_del_harness`, que ya sabia esto;
    no se escribe una segunda.
    """
    from . import roster
    return roster._dir_del_harness(desde)


def _ruta_de(relativa, desde):
    """La primera ruta que exista entre las raices, o la primera candidata si no esta.

    Devolver una candidata cuando no existe ninguna es a proposito: quien llama necesita
    poder nombrar el archivo que falta en el error.
    """
    if not relativa:
        return None
    partes = relativa.split("/")
    candidatas = [os.path.join(r, *partes) for r in raices_de_componentes(desde)]
    for c in candidatas:
        if os.path.exists(c):
            return c
    return candidatas[0] if candidatas else None


# -- validacion estructural ----------------------------------------------------

def validar_agente(agente, vistos_id, duenos_de_dominio, desde=__file__):
    """(estado, detalles) de un agente declarado."""
    detalles = []
    aid = agente.get("id", "")

    if aid in vistos_id:
        return "DUPLICATE_AGENT_ID", ["%s esta declarado dos veces" % aid]
    if agente.get("type") not in TIPOS:
        return "AGENT_TYPE_INVALID", [
            "%s declara el tipo `%s`, que no existe" % (aid, agente.get("type"))]
    if agente.get("status") == "DEPRECATED":
        return "DEPRECATED_AGENT", ["%s esta deprecado" % aid]

    if agente.get("type") == "SPECIALIST_AGENT":
        dominio = agente.get("domain", "")
        otro = duenos_de_dominio.get(dominio)
        if otro and otro != aid:
            return "DUPLICATE_DOMAIN_OWNER", [
                "%s y %s declaran el dominio %s: no se elige uno en silencio"
                % (otro, aid, dominio)]

    ruta = _ruta_de(agente.get("agentFile", ""), desde)
    if not ruta or not os.path.isfile(ruta):
        return "AGENT_FILE_MISSING", ["%s declara %s y no esta" % (aid, agente.get("agentFile"))]

    dice = identidad(ruta, "Agent")
    if dice != aid:
        return "AGENT_ID_MISMATCH", [
            "%s dice ser `%s`" % (agente.get("agentFile"), dice or "nadie")]

    instaladas = [s for s in agente.get("skills", []) if s.get("status") == "INSTALLED"]
    if agente.get("type") == "SPECIALIST_AGENT" and not instaladas:
        return "AGENT_SKILL_POLICY_INVALID", [
            "%s es SPECIALIST_AGENT y no tiene ninguna skill INSTALLED" % aid]

    pendientes = [s["id"] for s in agente.get("skills", [])
                  if s.get("status") == "DECLARED_NOT_INSTALLED"]
    if pendientes:
        detalles = ["pendientes: " + ", ".join(sorted(pendientes))]
        return "VALID_WITH_PENDING_SKILLS", detalles
    return "VALID", detalles


def validar_skill(agente, skill, duenos_de_skill, desde=__file__):
    """(estado, detalles) de una skill declarada bajo un agente."""
    sid = skill.get("id", "")
    otro = duenos_de_skill.get(sid)
    if otro and otro != agente.get("id"):
        return "SKILL_OWNER_CONFLICT", [
            "%s esta declarada bajo %s y bajo %s" % (sid, otro, agente.get("id"))]

    estado = skill.get("status")
    if estado == "DEPRECATED":
        return "DEPRECATED_SKILL", ["%s esta deprecada" % sid]
    if estado == "DECLARED_NOT_INSTALLED":
        if not skill.get("reason"):
            return "SKILL_FILE_MISSING", [
                "%s esta declarada como pendiente y no dice por que. Una pendiente sin motivo "
                "es indistinguible de una que nadie escribio." % sid]
        return "SPECIALIZED_SKILL_GAP", [skill["reason"]]

    ruta = _ruta_de(skill.get("file", ""), desde)
    if not ruta or not os.path.isfile(ruta):
        return "SKILL_FILE_MISSING", ["%s declara %s y no esta" % (sid, skill.get("file"))]
    dice = identidad(ruta, "Skill")
    if dice != sid:
        return "SKILL_ID_MISMATCH", ["%s dice ser `%s`" % (skill.get("file"), dice or "nadie")]
    return "SKILL_AVAILABLE", []


def validar_registro(documento=None, desde=__file__):
    """El estado de cada agente y de cada skill, calculado. Nada de esto se declara."""
    doc = documento if documento is not None else cargar(desde)
    errores = validar_schema(doc, desde)
    agentes = {}
    skills = {}
    vistos_id = set()
    duenos_de_dominio = {}
    duenos_de_skill = {}

    for agente in doc.get("agents", []):
        aid = agente.get("id", "")
        estado, detalle = validar_agente(agente, vistos_id, duenos_de_dominio, desde)
        vistos_id.add(aid)
        if agente.get("type") == "SPECIALIST_AGENT" and estado in AGENTE_RUTEABLE:
            duenos_de_dominio.setdefault(agente.get("domain", ""), aid)
        agentes[aid] = {"id": aid, "type": agente.get("type"), "domain": agente.get("domain"),
                        "state": estado, "details": detalle,
                        "severity": SEVERIDAD.get(estado, "ERROR")}
        for skill in agente.get("skills", []):
            sid = skill.get("id", "")
            est, det = validar_skill(agente, skill, duenos_de_skill, desde)
            duenos_de_skill.setdefault(sid, aid)
            skills[(aid, sid)] = {"agent": aid, "id": sid, "status": skill.get("status"),
                                  "state": est, "details": det,
                                  "severity": SEVERIDAD.get(est, "ERROR")}
    return {"schemaErrors": errores, "agents": agentes, "skills": skills}


# -- diagnostico del disco -----------------------------------------------------

def _listar(subdir, desde, es_directorio=False):
    """Lo que hay en disco, uniendo las dos raices posibles. Diagnostico, nunca alta."""
    salida = set()
    for raiz in raices_de_componentes(desde):
        d = os.path.join(raiz, subdir)
        if not os.path.isdir(d):
            continue
        for n in os.listdir(d):
            ruta = os.path.join(d, n)
            if es_directorio:
                if os.path.isdir(ruta) and os.path.isfile(os.path.join(ruta, "SKILL.md")):
                    salida.add(n)
            elif os.path.isfile(ruta) and n.endswith(".md"):
                salida.add(n[:-3])
    return sorted(salida)


def descubrir_huerfanos(documento=None, desde=__file__):
    """Archivos de agente que el registro no declara. Diagnostico: no dan de alta nada."""
    doc = documento if documento is not None else cargar(desde)
    declarados = {a.get("id") for a in doc.get("agents", [])}
    reconocidos = {h.get("id"): h for h in huerfanos_reconocidos(desde)}
    salida = []
    for nombre in _listar("agents", desde):
        if nombre in declarados:
            continue
        ack = reconocidos.get(nombre)
        salida.append({"id": nombre, "state": "ORPHAN_AGENT", "routable": False,
                       "fileExists": True, "action": "REQUIRES_CLASSIFICATION",
                       "acknowledged": bool(ack),
                       "severity": "WARNING" if ack else "ERROR"})
    return salida


def descubrir_no_declaradas(documento=None, desde=__file__):
    """Directorios de skill que el registro no declara."""
    doc = documento if documento is not None else cargar(desde)
    declaradas = {s.get("id") for a in doc.get("agents", []) for s in a.get("skills", [])}
    return [{"id": n, "state": "UNDECLARED_SKILL", "routable": False, "severity": "ERROR"}
            for n in _listar("skills", desde, es_directorio=True) if n not in declaradas]


# -- consultas deterministas ---------------------------------------------------

def agente(agent_id, documento=None, desde=__file__):
    doc = documento if documento is not None else cargar(desde)
    for a in doc.get("agents", []):
        if a.get("id") == agent_id:
            return a
    return None


def hay_agente(agent_id, documento=None, desde=__file__):
    return agente(agent_id, documento, desde) is not None


def agente_de_dominio(dominio, documento=None, desde=__file__):
    """El especialista de ese dominio, o "" si el registro no declara ninguno."""
    doc = documento if documento is not None else cargar(desde)
    for a in doc.get("agents", []):
        if a.get("type") == "SPECIALIST_AGENT" and a.get("domain") == dominio:
            return a.get("id", "")
    return ""


def skill(agent_id, skill_id, documento=None, desde=__file__):
    a = agente(agent_id, documento, desde)
    for s in (a or {}).get("skills", []):
        if s.get("id") == skill_id:
            return s
    return None


def hay_skill(agent_id, skill_id, documento=None, desde=__file__):
    return skill(agent_id, skill_id, documento, desde) is not None


def skills_de(agent_id, documento=None, desde=__file__):
    a = agente(agent_id, documento, desde)
    return list((a or {}).get("skills", []))


# -- ruteo ---------------------------------------------------------------------

def resolver_ruteo(agent_id, skill_id=None, documento=None, desde=__file__):
    """Si se puede rutear, y si no, exactamente por que.

    Cerrado por defecto: cualquier estado que no sea ruteable devuelve `routable: false`.
    Un `SPECIALIZED_SKILL_GAP` bloquea SOLO la especializacion pedida — el agente dueño
    sigue valido y sus otras skills se rutean igual.
    """
    doc = documento if documento is not None else cargar(desde)
    decl = agente(agent_id, doc, desde)

    if decl is None:
        huerfano = [h for h in descubrir_huerfanos(doc, desde) if h["id"] == agent_id]
        if huerfano:
            return {"requestedAgent": agent_id, "agentExists": False, "fileExists": True,
                    "result": "ORPHAN_AGENT", "routable": False}
        return {"requestedAgent": agent_id, "agentExists": False, "fileExists": False,
                "result": "AGENT_NOT_FOUND", "routable": False}

    informe = validar_registro(doc, desde)
    estado = informe["agents"][agent_id]["state"]
    if estado not in AGENTE_RUTEABLE:
        return {"requestedAgent": agent_id, "agentExists": False,
                "agentValidation": estado, "result": estado, "routable": False}

    salida = {"requestedAgent": agent_id, "agentExists": True, "agentValidation": estado}
    if skill_id is None:
        salida.update({"result": "ROUTABLE", "routable": True})
        return salida

    if not hay_skill(agent_id, skill_id, doc, desde):
        salida.update({"requestedSkill": skill_id, "skillExists": False,
                       "result": "SKILL_NOT_DECLARED_FOR_AGENT", "routable": False})
        return salida

    declarada = skill(agent_id, skill_id, doc, desde)
    est = informe["skills"][(agent_id, skill_id)]["state"]
    salida.update({"requestedSkill": skill_id,
                   "skillExists": declarada.get("status") == "INSTALLED",
                   "skillStatus": declarada.get("status"),
                   "skillValidation": est,
                   "result": "ROUTABLE" if est in SKILL_RUTEABLE else est,
                   "routable": est in SKILL_RUTEABLE})
    return salida


# -- reporte -------------------------------------------------------------------

def reporte(documento=None, desde=__file__):
    """El estado completo, con todas las cuentas CALCULADAS.

    Ninguna cifra esta escrita en el codigo: se cuentan el registro y el disco. Un numero
    hardcodeado en un reporte de validacion es un numero que un dia deja de ser cierto sin
    que nada se ponga en rojo.
    """
    doc = documento if documento is not None else cargar(desde)
    informe = validar_registro(doc, desde)
    huerfanos = descubrir_huerfanos(doc, desde)
    no_declaradas = descubrir_no_declaradas(doc, desde)

    agentes = list(informe["agents"].values())
    skills = list(informe["skills"].values())
    validos = [a for a in agentes if a["state"] in AGENTE_RUTEABLE]
    instaladas = [s for s in skills if s["status"] == "INSTALLED"]
    pendientes = [s for s in skills if s["status"] == "DECLARED_NOT_INSTALLED"]

    estructural = (bool(informe["schemaErrors"])
                   or len(validos) != len(agentes)
                   or any(s["severity"] == "ERROR" for s in skills)
                   or any(h["severity"] == "ERROR" for h in huerfanos)
                   or bool(no_declaradas))

    return {
        "registryVersion": doc.get("version", ""),
        "summary": {
            "declaredAgents": len(agentes),
            "validAgents": len(validos),
            "invalidAgents": len(agentes) - len(validos),
            "orphanAgents": len(huerfanos),
            "installedSkills": len(instaladas),
            "pendingSkills": len(pendientes),
            "undeclaredSkills": len(no_declaradas),
        },
        "agents": sorted(agentes, key=lambda a: a["id"]),
        "skills": sorted(skills, key=lambda s: (s["agent"], s["id"])),
        "orphans": huerfanos,
        "undeclared": no_declaradas,
        "schemaErrors": informe["schemaErrors"],
        "result": {
            "registryValid": not estructural,
            "filesystemClean": not huerfanos and not no_declaradas,
        },
    }
