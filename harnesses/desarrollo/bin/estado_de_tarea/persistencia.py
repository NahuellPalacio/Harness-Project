"""Guardar el estado del flujo: reconciliar contra lo guardado y escribir sin dejar medio archivo.

    reconciliar(proyecto, clave)   deriva, valida la transicion, escribe si cambio algo
    escribir(proyecto, clave, doc) temporal -> flush -> fsync -> os.replace
    marcar_activa(proyecto, clave) .claude/runtime/active-task.json, solo el puntero

🔴 `reconciliar` es el unico camino que escribe un estado, y el estado que escribe sale de
`flujo.estado.derivar`: nadie lo declara. Un guardado roto no se repara leyendolo, se
reemplaza por uno derivado.

Nada de aca sale a la red ni llama a un modelo.
"""
import io
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flujo import estado                                  # noqa: E402


def _como_texto(doc):
    return json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _escribir_atomico(ruta, texto):
    """Serializar, temporal en la misma carpeta, flush, fsync y reemplazar. Todo o nada.

    Si algo falla en el medio, el temporal se borra y el archivo anterior queda entero: un
    estado a medio escribir que se lee como vigente es peor que ninguno.
    """
    carpeta = os.path.dirname(os.path.abspath(ruta))
    if not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    temporal = os.path.join(carpeta, ".%s.%s.tmp" % (os.path.basename(ruta), uuid.uuid4().hex[:8]))
    try:
        with io.open(temporal, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporal, ruta)
    except BaseException:
        if os.path.exists(temporal):
            os.remove(temporal)
        raise
    return ruta


def escribir(proyecto, clave, doc):
    """Escribe un estado que valida. Levanta TASK_FLOW_STATE_INVALID si no."""
    errores = estado.validar(doc)
    if errores or doc.get("taskKey") != clave:
        raise estado.ErrorDeEstado(estado.INVALIDO, "no se escribe un estado que no valida: %s"
                                   % "; ".join(errores[:3] or ["taskKey"]))
    return _escribir_atomico(estado.ruta(proyecto, clave), _como_texto(doc))


def marcar_activa(proyecto, clave):
    """El puntero a la ultima tarea reconciliada. Nunca una copia de su estado."""
    doc = {"schema_version": estado.VERSION_ACTIVA, "taskKey": estado.validar_clave(clave)}
    ruta = estado.ruta_activa(proyecto)
    texto = _como_texto(doc)
    if os.path.isfile(ruta):
        with io.open(ruta, encoding="utf-8") as f:
            if f.read() == texto:
                return ruta
    return _escribir_atomico(ruta, texto)


def reconciliar(proyecto, clave, harness_version="", proceso=None):
    """Deriva el estado de ahora y lo guarda si cambio. Devuelve el que quedo guardado.

    Un estado logicamente igual no se reescribe: `updatedAt` es la ultima vez que cambio algo.
    """
    derivado = estado.derivar(proyecto, clave, harness_version, proceso)
    guardado, error = estado.leer(proyecto, clave)
    estado.validar_transicion(guardado, derivado, revalidado=True)
    if guardado is not None and estado.logico(guardado) == estado.logico(derivado):
        doc = guardado
    else:
        escribir(proyecto, clave, derivado)
        doc = derivado
    marcar_activa(proyecto, clave)
    return doc
