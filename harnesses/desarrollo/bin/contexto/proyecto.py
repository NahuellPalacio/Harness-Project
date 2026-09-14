"""Project Resolver: la Ficha de Proyecto, que es donde vive el conocimiento.

La Ficha no es un issue mas. Es una entidad de primer nivel: Jira guarda ahi el
conocimiento del proyecto -objetivos, alcance, reglas, arquitectura, documentos- mientras
que las HU, los bugs y las tasks son trabajo. Confundirlas hace que el conocimiento herede
el ciclo de vida de una entrega.

Se busca por tipo de issue dentro del mismo proyecto Jira del ticket.

🔴 Si hay mas de una, no se elige ninguna. Elegir la primera por fecha seria inventar un
criterio que nadie escribio, y el contexto saldria con el sello de resuelto sobre una
eleccion invisible. El conflicto se declara y la ficha queda vacia.
"""
from .comun import texto_de_adf

TIPO_POR_DEFECTO = "Ficha de Proyecto"

# Como se busca cada campo adentro de la ficha. La ficha es un issue: su conocimiento
# esta en la descripcion, bajo encabezados. Se parte por encabezado porque es lo unico
# que existe -Jira no tiene un campo "objetivos"- y por eso el bloque sale `inferred`.
ENCABEZADOS = {
    "objectives": ("objetivo", "objetivos", "objective", "objectives"),
    "scope": ("alcance", "scope"),
    "architecture": ("arquitectura", "architecture"),
    "rules": ("regla", "reglas", "reglas de negocio", "business rules"),
}


def ficha_vacia(estado="missing"):
    return {"key": "", "title": "", "summary": "", "objectives": "", "scope": "",
            "rules": [], "architecture": "", "knowledge_status": estado}


def resolver(jira, campos_tarea, catalogo, config, acumulador):
    """La seccion `project`. Nunca levanta: sin ficha, el contexto sale igual."""
    proyecto = campos_tarea.get("project") if isinstance(campos_tarea, dict) else None
    clave_proyecto = ""
    nombre_proyecto = ""
    if isinstance(proyecto, dict):
        clave_proyecto = str(proyecto.get("key") or "")
        nombre_proyecto = str(proyecto.get("name") or "")

    vacio = {"jira_key": clave_proyecto, "name": nombre_proyecto,
             "ficha": ficha_vacia(), "knowledge_status": "missing"}

    if not clave_proyecto:
        acumulador.falta("el proyecto Jira del ticket: el issue no trae el campo `project`")
        return vacio, None

    tipo = str(config.get("fichaTipoDeIssue") or TIPO_POR_DEFECTO)
    if not acumulador.hay("jira.issue.search",
                          "sin eso no se puede buscar la Ficha de Proyecto"):
        return vacio, None

    jql = 'project = "%s" AND issuetype = "%s" ORDER BY created ASC' % (clave_proyecto, tipo)
    respuesta = jira.buscar(jql, maximo=5)
    if not respuesta.ok:
        acumulador.falta("la Ficha de Proyecto: Jira contesto %d al buscarla"
                         % respuesta.codigo)
        return vacio, None

    encontrados = (respuesta.datos() or {}).get("issues") or []
    if not encontrados:
        acumulador.falta('la Ficha de Proyecto: no hay ningun issue de tipo "%s" en el '
                         'proyecto %s' % (tipo, clave_proyecto))
        return vacio, None

    if len(encontrados) > 1:
        claves = ", ".join(str(i.get("key")) for i in encontrados)
        acumulador.conflicto(
            'hay %d issues de tipo "%s" en el proyecto %s (%s). No se elige ninguna: '
            'la Ficha de Proyecto tiene que ser unica.'
            % (len(encontrados), tipo, clave_proyecto, claves))
        vacio["ficha"] = ficha_vacia("conflicted")
        vacio["knowledge_status"] = "conflicted"
        return vacio, None

    issue = encontrados[0]
    clave_ficha = str(issue.get("key") or "")
    campos = issue.get("fields") or {}
    acumulador.fuente("jira:" + clave_ficha, "jira_ficha", clave_ficha)

    # Idem tarea.py: redacta el ensamblador, sobre el documento entero.
    cuerpo = texto_de_adf(campos.get("description"))

    secciones = _por_encabezado(cuerpo)
    ficha = {
        "key": clave_ficha,
        "title": str(campos.get("summary") or ""),
        "summary": secciones.get("_intro", "").strip(),
        "objectives": secciones.get("objectives", "").strip(),
        "scope": secciones.get("scope", "").strip(),
        "rules": _reglas(secciones.get("rules", "")),
        "architecture": secciones.get("architecture", "").strip(),
        # Los campos salen de partir la descripcion por encabezados, que es una
        # heuristica: Jira no tiene un campo "objetivos". Se declara como inferido.
        "knowledge_status": "inferred",
    }
    for clave in ("objectives", "scope", "architecture"):
        if not ficha[clave]:
            acumulador.falta("en la Ficha %s no se encontro una seccion de %s"
                             % (clave_ficha, clave))

    return {"jira_key": clave_proyecto, "name": nombre_proyecto, "ficha": ficha,
            "knowledge_status": "inferred"}, campos


def _reglas(texto):
    """Una regla por linea, sin el guion del bullet: el bullet es formato, no contenido."""
    salida = []
    for linea in (texto or "").splitlines():
        limpia = linea.strip()
        if limpia.startswith(("- ", "* ", "• ")):
            limpia = limpia[2:].strip()
        if limpia:
            salida.append(limpia)
    return salida


def _por_encabezado(texto):
    """Parte un texto plano en secciones, por lineas que parecen encabezado."""
    secciones = {"_intro": ""}
    actual = "_intro"
    for linea in (texto or "").splitlines():
        limpia = linea.strip().strip("#").strip().strip(":").strip().lower()
        destino = None
        for nombre, agujas in ENCABEZADOS.items():
            if limpia and limpia in agujas:
                destino = nombre
                break
        if destino:
            actual = destino
            secciones.setdefault(actual, "")
            continue
        secciones[actual] = secciones.get(actual, "") + linea + "\n"
    return secciones
