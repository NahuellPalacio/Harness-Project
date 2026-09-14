"""Jira Task Resolver: de una clave a los campos que describen que hay que hacer.

Lo que entra es un issue -HU, Bug, Task, Epic o lo que el proyecto tenga-. Lo que sale es
la seccion `task` del contrato, normalizada y limpia.

🔴 El padre y los enlaces entran como REFERENCIAS, nunca resueltos. Un resolvedor que
sigue enlaces termina bajando el proyecto entero desde un ticket cualquiera, y el contexto
deja de ser de esta tarea.

🔴 Los criterios de aceptacion salen del campo configurado y de ningun otro lado. Si no
hay campo, la lista queda vacia y el hueco se declara: derivarlos de la descripcion es
inventarlos, y un criterio inventado se lee igual que uno escrito.
"""
from .comun import lista_de_adf, texto_de_adf


class TareaNoResuelta(Exception):
    """Sin esto no hay contexto posible. La CLI sale con codigo 2."""


def _campo(campos, nombre, defecto=""):
    valor = campos.get(nombre)
    return defecto if valor is None else valor


def _nombre_de(valor, clave="name"):
    if isinstance(valor, dict):
        return str(valor.get(clave) or "")
    return str(valor or "")


def resolver(jira, clave, catalogo, config, acumulador):
    """La seccion `task`. Levanta TareaNoResuelta si el issue no se pudo leer."""
    if not acumulador.hay("jira.issue.read", "sin eso no hay tarea que resolver"):
        raise TareaNoResuelta(
            "el registro de capacidades no tiene jira.issue.read habilitada. "
            "Corre el setup del harness y volve a intentar.")

    respuesta = jira.issue(clave)
    if not respuesta.ok:
        raise TareaNoResuelta(_motivo(respuesta, clave))

    datos = respuesta.datos() or {}
    campos = datos.get("fields") or {}
    acumulador.fuente("jira:" + clave, "jira_issue", clave)

    # La redaccion no pasa por aca: la hace el ensamblador sobre el documento entero.
    # Ver ensamblador.armar — el motivo es que este archivo no puede garantizar que el
    # campo que alguien agregue manana tambien pase por la limpieza.
    descripcion = texto_de_adf(campos.get("description"))
    criterios = _criterios(campos, config, acumulador)
    titulo = str(_campo(campos, "summary"))

    padre = ""
    if isinstance(campos.get("parent"), dict):
        padre = str(campos["parent"].get("key") or "")

    enlaces = []
    for enlace in (campos.get("issuelinks") or []):
        if not isinstance(enlace, dict):
            continue
        tipo = _nombre_de(enlace.get("type"))
        for direccion in ("inwardIssue", "outwardIssue"):
            otro = enlace.get(direccion)
            if isinstance(otro, dict) and otro.get("key"):
                enlaces.append({"type": tipo, "key": str(otro["key"])})

    return {
        "key": str(datos.get("key") or clave),
        "type": _nombre_de(campos.get("issuetype")),
        "title": titulo,
        "description": descripcion,
        "acceptance_criteria": criterios,
        "status": _nombre_de(campos.get("status")),
        "priority": _nombre_de(campos.get("priority")),
        "labels": [str(e) for e in (campos.get("labels") or [])],
        "parent": padre,
        "links": enlaces,
        "knowledge_status": "confirmed",
    }, campos


def _criterios(campos, config, acumulador):
    campo = str(config.get("campoCriteriosAceptacion") or "").strip()
    if not campo:
        acumulador.falta(
            "los criterios de aceptacion: no hay `campoCriteriosAceptacion` en "
            "harness.config.json, asi que no se sabe de que campo de Jira leerlos")
        acumulador.pregunta(
            "En que campo de Jira viven los criterios de aceptacion de este proyecto?")
        return []
    if campo not in campos:
        acumulador.falta(
            "los criterios de aceptacion: el issue no trae el campo `%s`" % campo)
        return []
    criterios = lista_de_adf(campos.get(campo))
    if not criterios:
        acumulador.falta("los criterios de aceptacion: el campo `%s` vino vacio" % campo)
    return criterios


def _motivo(respuesta, clave):
    if respuesta.error:
        return ("no se pudo leer %s: %s. Revisa la red o la VPN."
                % (clave, respuesta.error))
    if respuesta.codigo == 404:
        return ("%s no existe, o el token no tiene permiso para verlo (404)." % clave)
    if respuesta.codigo == 401:
        return ("el token de Jira no fue aceptado al leer %s (401). Puede haber vencido "
                "despues del ultimo setup: corre `estado` para revalidar." % clave)
    if respuesta.codigo == 403:
        return "el token de Jira no tiene permisos para leer %s (403)." % clave
    return "Jira contesto %d al leer %s." % (respuesta.codigo, clave)
