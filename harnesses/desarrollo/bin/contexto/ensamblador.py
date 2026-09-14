"""Context Assembler: junta las cuatro resoluciones en un documento y lo valida.

Su trabajo no es resolver nada: es armar el contrato, calcular su hash y no dejar salir un
documento que no valide. Lo que ningun resolvedor pudo resolver llega hasta aca como hueco
declarado y sale como hueco declarado.

🔴 El validador de JSON Schema NO se escribe de nuevo. El harness ya tiene uno
-`comun/bin/contexto-armar.py`, el que valida `project-context`- y se importa por ruta.
Dos validadores del mismo subconjunto en el mismo repositorio son la misma decision tomada
dos veces, con dos comportamientos.
"""
import importlib.util
import io
import json
import os

from . import limpieza
from .comun import ahora

VERSION_SCHEMA = "task-context/1.0"


class ContratoInvalido(Exception):
    """El documento no valida. No se escribe: un contrato roto con el sello puesto es peor
    que no tener contrato."""


def _armador():
    """`contexto-armar.py`, importado por ruta: su nombre tiene un guion."""
    ruta = limpieza._localizar(("bin", "contexto-armar.py"))
    if ruta is None:
        return None
    spec = importlib.util.spec_from_file_location("contexto_armar", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def cargar_schema():
    ruta = limpieza._localizar(("schemas", "task-context.schema.json"))
    if ruta is None:
        raise ContratoInvalido(
            "no esta task-context.schema.json. El contrato no se escribe sin poder validarlo.")
    with io.open(ruta, encoding="utf-8") as f:
        return json.load(f)


def armar(clave, task, project, documentation, repository, acumulador, version_harness="",
          catalogo=None):
    """El documento entero, con su hash. No valida: eso lo hace `validar`.

    🔴 La redaccion de secretos pasa por aca y no por cada resolvedor. Recorrer las cuatro
    secciones enteras es lo que vuelve estructural la promesa de que ninguna ruta de
    entrada se escapa: un campo nuevo queda cubierto por existir, no por acordarse.

    La unica redaccion que sigue estando antes es la del texto de un documento, en
    `documentos.py`, y por un motivo: ahi se recorta, y un recorte puede partir un token
    al medio y dejar un pedazo que ya no matchea ningun patron.
    """
    documento = {
        "meta": {
            "schema_version": VERSION_SCHEMA,
            "context_id": "",
            "context_hash": "",
            "generated_at": ahora(),
            "harness_version": version_harness,
            "task_key": clave,
            "capabilities_used": sorted(acumulador.capabilities_used),
        },
        "sources": acumulador.sources,
        "task": task,
        "project": project,
        "documentation": documentation,
        "repository": repository,
        "gaps_and_conflicts": {
            "missing": acumulador.missing,
            "conflicts": acumulador.conflicts,
            "missing_capabilities": acumulador.missing_capabilities,
            "redacted_secrets": acumulador.redacted_secrets,
            "unresolved_questions": acumulador.unresolved_questions,
        },
    }
    _limpiar(documento, catalogo)

    armador = _armador()
    if armador is None:
        raise ContratoInvalido(
            "no esta comun/bin/contexto-armar.py, que es de donde sale el validador.")
    # 🔴 El id se escribe ANTES del hash y no depende de el. Al reves -el id con los
    # primeros caracteres del hash, como hace project-context con repo_revision- el
    # documento cambia despues de hashearse y el hash deja de ser recomputable: un
    # consumidor que quiera verificarlo obtiene otro numero. `canonico` saca del calculo
    # `context_hash` y `generated_at`, no el id, y esa es la unica forma de que
    # hash_de(documento) sobre el archivo escrito devuelva lo que el archivo dice.
    documento["meta"]["context_id"] = "tsk_" + clave
    documento["meta"]["context_hash"] = armador.hash_de(documento)
    return documento


# Todo menos `meta`, que lo escribe esta funcion y no tiene texto de afuera. `sources`
# entra: la referencia de una fuente es el nombre de una rama o de un adjunto, y ahi ya
# se escapo un token una vez.
_SECCIONES = ("sources", "task", "project", "documentation", "repository",
              "gaps_and_conflicts")


def _limpiar(documento, catalogo):
    """Redacta el documento entero, en su lugar. Los hallazgos nuevos van a los huecos."""
    if catalogo is None:
        return
    nuevos = []
    for clave in _SECCIONES:
        limpio, hallazgos = limpieza.redactar_arbol(documento[clave], catalogo, "$." + clave)
        documento[clave] = limpio
        nuevos.extend(hallazgos)
    # Se suman despues de redactar: una muestra segura no vuelve a pasar por el detector.
    documento["gaps_and_conflicts"]["redacted_secrets"].extend(nuevos)


def validar(documento):
    """Lista de errores. Vacia es valido. Levanta si el schema usa algo no soportado."""
    armador = _armador()
    esquema = cargar_schema()
    armador.controlar_soporte(esquema)
    return armador.validar(documento, esquema)


def escribir(documento, ruta):
    errores = validar(documento)
    if errores:
        raise ContratoInvalido(
            "el TaskContext no valida contra task-context/1.0:\n  - %s"
            % "\n  - ".join(errores[:5]))
    carpeta = os.path.dirname(os.path.abspath(ruta))
    if carpeta and not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    with io.open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(documento, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return ruta
