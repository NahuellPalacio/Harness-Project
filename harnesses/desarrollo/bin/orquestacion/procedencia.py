"""El indice inverso: de una fuente a todo lo que sale de ella.

Sin esto, actualizar ES0901 es una busqueda a mano por el arbol, y lo que no aparezca en esa
busqueda queda declarando una version que ya no existe. Con esto, la pregunta "que se cae si
ES0901 pasa a 6.4" tiene una respuesta calculada.

🔴 **La procedencia ya estaba declarada; no se declara de nuevo.** Los 42 controles dicen de
que estandar salen en `normativeSources[]`, cada matriz dice cual clasifica y en que version, y
un agente o una skill pueden decirlo en su frontmatter:

    sources:
      - ES0901@6.3

Lo que este modulo hace es DARLO VUELTA. Una lista `derived[]` escrita a mano en el registro de
fuentes seria una segunda declaracion de lo mismo, que envejece sola y que el dia que difiera
de la primera va a tener razon igual.

🔴 **No inventa impacto.** Un id que nadie declara devuelve vacio. Y un control que no declara
`normativeSources[]` no aparece en ningun impacto: `controles.py` ya lo diagnostica como
`CONTROL_NORMATIVE_SOURCE_MISSING`, y repetirlo aca seria adivinar de que fuente sale.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from . import controles                          # noqa: E402
from . import matriz                             # noqa: E402
from . import registro_agentes                   # noqa: E402
from . import seguridad                          # noqa: E402

# Las clases de activo que el indice sabe nombrar. El prefijo viaja en el impacto aplanado
# para que "ES0901 toca 31 cosas" se pueda leer sin abrir nada mas.
CONTROL = "control"
FILA = "matrix-row"
MATRIZ = "matrix"
AGENTE = "agent"
SKILL = "skill"

_FRONTMATTER = registro_agentes._FRONTMATTER

# `sources:` en el frontmatter, en sus dos formas: bloque de guiones o lista en linea.
_BLOQUE = re.compile(r"^sources:\s*\n((?:[ \t]*-[ \t]*\S+[ \t]*\n?)+)", re.M)
_EN_LINEA = re.compile(r"^sources:[ \t]*\[([^\]]*)\][ \t]*$", re.M)
_ITEM = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:@([0-9][0-9A-Za-z._-]*))?$")


# -- lo que declara un archivo -------------------------------------------------

def declaraciones_de(texto):
    """Los `(fuente, version)` que declara un frontmatter. Sin `@`, la version es None.

    Se lee SOLO el frontmatter: un `sources:` en el cuerpo de un agente es prosa, y tratar
    prosa como metadata es como una linea de ejemplo se vuelve una declaracion.
    """
    m = _FRONTMATTER.match(texto or "")
    if not m:
        return []
    frente = m.group(1)
    crudos = []
    b = _BLOQUE.search(frente)
    if b:
        crudos += [l.strip().lstrip("-").strip() for l in b.group(1).splitlines() if l.strip()]
    e = _EN_LINEA.search(frente)
    if e:
        crudos += [p.strip().strip("'\"") for p in e.group(1).split(",")]
    salida = []
    for crudo in crudos:
        item = _ITEM.match(crudo.strip().strip("'\""))
        if item and (item.group(1), item.group(2)) not in salida:
            salida.append((item.group(1), item.group(2)))
    return salida


def _archivos_de_componentes(desde=None):
    """(clase, id, ruta) de cada agente y cada skill que exista en este arbol."""
    salida = []
    vistas = set()
    for raiz in registro_agentes.raices_de_componentes(desde or __file__):
        dir_agentes = os.path.join(raiz, "agents")
        if os.path.isdir(dir_agentes):
            for nombre in sorted(os.listdir(dir_agentes)):
                if nombre.endswith(".md"):
                    ruta = os.path.join(dir_agentes, nombre)
                    clave = (AGENTE, nombre)
                    if clave not in vistas:
                        vistas.add(clave)
                        salida.append((AGENTE, nombre[:-3], ruta))
        dir_skills = os.path.join(raiz, "skills")
        if os.path.isdir(dir_skills):
            for nombre in sorted(os.listdir(dir_skills)):
                ruta = os.path.join(dir_skills, nombre, "SKILL.md")
                clave = (SKILL, nombre)
                if os.path.isfile(ruta) and clave not in vistas:
                    vistas.add(clave)
                    salida.append((SKILL, nombre, ruta))
    return salida


def componentes(desde=None):
    """{(clase, id): [(fuente, version)]} de lo que cada agente y cada skill declara."""
    salida = {}
    for clase, ident, ruta in _archivos_de_componentes(desde):
        try:
            with io.open(ruta, encoding="utf-8-sig") as f:
                texto = f.read()
        except OSError:
            continue
        declarado = declaraciones_de(texto)
        if declarado:
            salida[(clase, ident)] = declarado
    return salida


# -- las matrices --------------------------------------------------------------

def _estandar_de(documento):
    """(id, version) de la matriz. Las dos matrices lo declaran distinto y las dos valen."""
    estandar = documento.get("standard")
    if isinstance(estandar, dict):
        return str(estandar.get("id") or ""), estandar.get("version")
    return str(estandar or ""), documento.get("version")


def _matrices(desde=None):
    """[(archivo, id_de_estandar, version, filas)] de las matrices que existan."""
    salida = []
    for modulo in (matriz, seguridad):
        try:
            doc = modulo.cargar(desde)
        except Exception:                                    # noqa: BLE001
            continue
        if not doc:
            continue
        sid, version = _estandar_de(doc)
        if not sid:
            continue
        salida.append((modulo.ARCHIVO, sid, version, list(doc.get("rules") or [])))
    return salida


def _clave_de_fila(sid, fila):
    return str(fila.get("ruleKey") or "%s.%s" % (sid, fila.get("id") or ""))


# -- el indice -----------------------------------------------------------------

def _vacio():
    return {"controls": [], "matrices": [], "matrixRows": [], "agents": [], "skills": []}


def indice(desde=None, doc_controles=None):
    """{fuente: impacto}. La fuente es la clave con la que la citan los que la declaran."""
    salida = {}

    documento = doc_controles if doc_controles is not None else controles.cargar(desde)
    for control in documento.get("controls") or []:
        for fuente in controles.fuentes_de(control):
            sid = str(fuente.get("standard") or "")
            if not sid:
                continue
            entrada = salida.setdefault(sid, _vacio())
            registro = {"id": control.get("id"), "type": control.get("type"),
                        "declaredVersion": fuente.get("version")}
            if registro not in entrada["controls"]:
                entrada["controls"].append(registro)

    for archivo, sid, version, filas in _matrices(desde):
        entrada = salida.setdefault(sid, _vacio())
        entrada["matrices"].append({"file": archivo, "declaredVersion": version})
        for fila in filas:
            entrada["matrixRows"].append({
                "id": _clave_de_fila(sid, fila),
                "declaredVersion": version,
                "policies": list(fila.get("policies") or []),
                "checks": list(fila.get("checks") or []),
                "reviews": list(fila.get("reviews") or []),
                "agents": list(fila.get("primaryAgents") or []),
            })

    for (clase, ident), declarado in componentes(desde).items():
        for sid, version in declarado:
            entrada = salida.setdefault(sid, _vacio())
            destino = entrada["agents"] if clase == AGENTE else entrada["skills"]
            registro = {"id": ident, "declaredVersion": version}
            if registro not in destino:
                destino.append(registro)

    for entrada in salida.values():
        entrada["controls"].sort(key=lambda c: str(c["id"]))
        entrada["matrixRows"].sort(key=lambda f: str(f["id"]))
        entrada["agents"].sort(key=lambda a: str(a["id"]))
        entrada["skills"].sort(key=lambda s: str(s["id"]))
    return salida


def impacto(sid, ind=None, desde=None, doc_controles=None):
    """El impacto de UNA fuente. Un id que nadie declara devuelve vacio, no el arbol."""
    completo = ind if ind is not None else indice(desde, doc_controles)
    return completo.get(sid) or _vacio()


def aplanar(uno):
    """El impacto como lista de ids con prefijo, ordenada. Es lo que viaja en el estado."""
    salida = []
    for control in uno.get("controls") or []:
        salida.append("%s:%s" % (CONTROL, control.get("id")))
    for m in uno.get("matrices") or []:
        salida.append("%s:%s" % (MATRIZ, m.get("file")))
    for fila in uno.get("matrixRows") or []:
        salida.append("%s:%s" % (FILA, fila.get("id")))
        for agente in fila.get("agents") or []:
            salida.append("%s:%s" % (AGENTE, agente))
    for agente in uno.get("agents") or []:
        salida.append("%s:%s" % (AGENTE, agente.get("id")))
    for skill in uno.get("skills") or []:
        salida.append("%s:%s" % (SKILL, skill.get("id")))
    return sorted(set(salida))


def desactualizados(sid, version_aceptada, ind=None, desde=None, doc_controles=None):
    """Los derivados que declaran una version distinta de la aceptada.

    🔴 Lo que no declara version no cuenta como viejo. No saber de que version sale un activo
    es otro problema -y lo diagnostica quien corresponde-: contarlo aca lo convertiria en un
    bloqueo permanente que nadie puede levantar.
    """
    if not version_aceptada:
        return []
    uno = impacto(sid, ind, desde, doc_controles)
    salida = []
    for clase, clave in ((CONTROL, "controls"), (MATRIZ, "matrices"),
                         (FILA, "matrixRows"), (AGENTE, "agents"), (SKILL, "skills")):
        for activo in uno.get(clave) or []:
            declarada = activo.get("declaredVersion")
            if declarada and str(declarada) != str(version_aceptada):
                salida.append({
                    "asset": "%s:%s" % (clase, activo.get("id") or activo.get("file")),
                    "kind": clase,
                    "declaredVersion": str(declarada),
                    "sourceVersion": str(version_aceptada),
                })
    return sorted(salida, key=lambda d: d["asset"])
