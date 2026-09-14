"""Lo que comparten los cuatro resolvedores: el acumulador, el reloj y el ADF de Jira.

El acumulador es lo que hace que la incertidumbre viaje adentro del contrato en vez de
perderse: cada resolvedor le anota que leyo, que no encontro y que capacidad le falto, y
el ensamblador arma con eso `sources` y `gaps_and_conflicts`. Sin un lugar comun, cada
resolvedor tendria su propia forma de decir "no pude", y la mitad no lo diria.
"""
import datetime


def ahora():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


class Acumulador(object):
    """Lo leido, lo que falto y lo que se redacto. Uno por resolucion."""

    def __init__(self, registro=None):
        self.registro = registro
        self.sources = []
        self.missing = []
        self.conflicts = []
        self.missing_capabilities = []
        self.redacted_secrets = []
        self.unresolved_questions = []
        self.capabilities_used = []

    # -- capacidades -----------------------------------------------------------

    def hay(self, capacidad, para_que):
        """Se puede usar? Si no, lo declara y devuelve False. Nadie llama sin preguntar."""
        disponible = self.registro is not None and self.registro.get(capacidad) == "ENABLED"
        if not disponible:
            self.missing_capabilities.append(
                "%s no esta disponible: %s. Corre el setup del harness para reconfigurarla."
                % (capacidad, para_que))
            return False
        if capacidad not in self.capabilities_used:
            self.capabilities_used.append(capacidad)
        return True

    # -- trazas ----------------------------------------------------------------

    def fuente(self, source_id, tipo, referencia):
        self.sources.append({
            "source_id": source_id,
            "type": tipo,
            "reference": referencia,
            "retrieved_at": ahora(),
        })

    def falta(self, texto):
        self.missing.append(texto)

    def conflicto(self, texto):
        self.conflicts.append(texto)

    def redactado(self, hallazgos):
        self.redacted_secrets.extend(hallazgos)

    def pregunta(self, texto):
        self.unresolved_questions.append(texto)


def texto_de_adf(nodo):
    """Aplana el Atlassian Document Format a texto plano.

    La API v3 de Jira devuelve la descripcion como un arbol JSON, no como texto: un
    resolvedor que guarde ese objeto tal cual le entrega al agente un arbol de nodos en
    vez de lo que la persona escribio. Lo que se conserva es el texto y los saltos entre
    bloques; el formato -negritas, colores, anchos de tabla- no es contexto.

    Un valor que ya es texto plano -la API v2, o un campo viejo- pasa igual.
    """
    if nodo is None:
        return ""
    if isinstance(nodo, str):
        return nodo
    if isinstance(nodo, list):
        return "\n".join(t for t in (texto_de_adf(n) for n in nodo) if t)
    if not isinstance(nodo, dict):
        return ""

    tipo = nodo.get("type")
    if tipo == "text":
        return nodo.get("text", "")
    if tipo == "hardBreak":
        return "\n"

    adentro = texto_de_adf(nodo.get("content"))
    if tipo == "listItem":
        return "- " + adentro.replace("\n", " ").strip()
    if tipo in ("paragraph", "heading", "blockquote", "codeBlock", "panel",
                "bulletList", "orderedList", "doc", "tableRow", "tableCell", "table"):
        return adentro
    return adentro


def lista_de_adf(nodo):
    """Los items de la primera lista que encuentre, o las lineas si no hay lista.

    Sirve para un campo que tiene criterios de aceptacion: casi siempre vienen como
    bullets, a veces como lineas sueltas.
    """
    texto = texto_de_adf(nodo).strip()
    if not texto:
        return []
    items = []
    for linea in texto.splitlines():
        limpia = linea.strip()
        if not limpia:
            continue
        if limpia.startswith("- "):
            limpia = limpia[2:].strip()
        if limpia:
            items.append(limpia)
    return items
