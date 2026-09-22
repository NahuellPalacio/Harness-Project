"""El `ledger.jsonl`: append-only, y append-only por construccion.

Este modulo tiene un solo verbo de escritura y se llama `agregar`. No hay `reemplazar`, no
hay `borrar`, no hay `reescribir`. Enmendar un hecho es agregar un `ACCOUNTING_CORRECTION`
que lo referencia, y el hecho viejo queda donde estaba.

🔴 Lo que hace confiable a un libro contable no es la intencion de quien escribe. Es que
el verbo no exista.

El evento pasa por la limpieza del Bloque 2 antes de tocar el disco: la misma que redacta
el `OrchestrationPlan`, con el mismo catalogo de `comun/reglas/secretos.patrones.json`. No
se escribe una segunda limpieza parecida — un dia una encuentra el catalogo y la otra no.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contexto import limpieza  # noqa: E402

from . import eventos  # noqa: E402

LIBRO = "ledger.jsonl"
RESUMEN = "summary.json"
REPORTE = "execution-cost.md"

# 🔴 Cuanto texto entra en un campo del libro. Es la segunda mitad de la defensa contra
# guardar conversacion: la primera es que `metadata` tiene las claves cerradas, y esta es
# que ningun campo aguanta un parrafo. El motivo mas largo que el harness escribe hoy son
# 120 caracteres; un prompt no entra en 300 y lo que se recorta se dice.
TOPE_DE_TEXTO = 300

# Bajo `.claude/`, al lado de `contextos/` y `planes/`. Un `runtime/` en la raiz ensucia el
# repositorio del proyecto que se esta desarrollando, que no es nuestro.
BASE = (".claude", "runtime", "accounting")


def carpeta_de(proyecto, task_id):
    return os.path.join(proyecto, *(BASE + (str(task_id),)))


def ruta_de(proyecto, task_id, nombre=LIBRO):
    return os.path.join(carpeta_de(proyecto, task_id), nombre)


def _asegurar(ruta):
    carpeta = os.path.dirname(os.path.abspath(ruta))
    if carpeta and not os.path.isdir(carpeta):
        os.makedirs(carpeta)


def es_el_libro(ruta):
    """True si esa ruta es un `ledger.jsonl`.

    Lo usan los dos modulos que SI escriben en modo `w` -el resumen y el reporte- para
    negarse. `agregar` es append-only, pero eso no sirve de nada si el de al lado puede
    truncar el mismo archivo pasandole la ruta equivocada.
    """
    return os.path.basename(str(ruta or "")) == LIBRO


def exigir_que_no_sea_el_libro(ruta, quien):
    if es_el_libro(ruta):
        raise ValueError(
            "%s no escribe sobre %s: el libro es append-only y esto lo truncaria."
            % (quien, LIBRO))
    return ruta


def leer(ruta):
    """Los eventos del libro, en orden de escritura. Una linea rota no voltea el libro.

    Se devuelve lo que se pudo leer y la linea ilegible se cuenta: un libro con una linea
    corrupta sigue siendo la mejor fuente que hay, y perderlo entero por una linea seria
    cambiar un dato malo por ninguno.
    """
    if not os.path.isfile(ruta):
        return []
    leidos = []
    with io.open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue
            try:
                leidos.append(json.loads(linea))
            except ValueError:
                leidos.append({"eventId": "", "eventType": "", "timestamp": "",
                               "taskId": "", "source": {"adapter": "ilegible"},
                               "metadata": {"unreadable": True}})
    return leidos


def ids(ruta):
    return set(str(e.get("eventId") or "") for e in leer(ruta))


def _recortado(nodo, donde="$"):
    """Recorta todo texto largo del evento, en cualquier nivel. Devuelve (nodo, hallazgos).

    La limpieza del Bloque 2 saca secretos; esto saca PROSA, que es otra cosa. Un prompt no
    es un patron de secreto y ningun catalogo lo iba a encontrar: lo que lo detiene es que
    no entre.
    """
    if isinstance(nodo, dict):
        salida, hallazgos = {}, []
        for clave in nodo:
            salida[clave], nuevos = _recortado(nodo[clave], "%s.%s" % (donde, clave))
            hallazgos.extend(nuevos)
        return salida, hallazgos
    if isinstance(nodo, list):
        salida, hallazgos = [], []
        for i, item in enumerate(nodo):
            limpio, nuevos = _recortado(item, "%s[%d]" % (donde, i))
            salida.append(limpio)
            hallazgos.extend(nuevos)
        return salida, hallazgos
    if isinstance(nodo, str):
        texto, recortado = limpieza.recortar(nodo, TOPE_DE_TEXTO)
        if recortado:
            return texto, ["%s: se recorto en %d caracteres. El libro guarda contabilidad, "
                           "no conversacion." % (donde, TOPE_DE_TEXTO)]
        return nodo, []
    return nodo, []


def _limpio(evento):
    """Secretos afuera, prosa recortada. En ese orden y las dos veces."""
    catalogo = limpieza.cargar_catalogo()
    limpiado, hallazgos = (evento, []) if catalogo is None else limpieza.redactar_arbol(
        evento, catalogo, "$")
    limpiado, recortes = _recortado(limpiado)
    return limpiado, hallazgos + recortes


def agregar(ruta, evento):
    """Escribe el evento al final si su `eventId` no esta. Devuelve (escrito, hallazgos).

    Un `eventId` repetido NO se agrega: es lo que hace que reingerir la misma fuente sea
    inofensivo. La deduplicacion vive en dos lados a proposito — acá, para que el libro no
    crezca con lo mismo, y en la agregacion, para que un libro que ya trae repetidos por
    cualquier motivo tampoco los sume dos veces.
    """
    errores = eventos.validar(evento)
    if errores:
        raise eventos.EventoInvalido(
            "el evento no valida y no se escribe:\n  - %s" % "\n  - ".join(errores[:5]))

    eid = str(evento.get("eventId") or "")
    if eid in ids(ruta):
        return False, []

    limpiado, hallazgos = _limpio(evento)
    _asegurar(ruta)
    linea = json.dumps(limpiado, ensure_ascii=False, sort_keys=True) + "\n"
    with io.open(ruta, "a", encoding="utf-8", newline="\n") as f:
        f.write(linea)
    return True, hallazgos


def agregar_varios(ruta, lista):
    """Devuelve (escritos, salteados, hallazgos). Los salteados ya estaban."""
    escritos = salteados = 0
    hallazgos = []
    for evento in lista:
        ok, nuevos = agregar(ruta, evento)
        if ok:
            escritos += 1
        else:
            salteados += 1
        hallazgos.extend(nuevos)
    return escritos, salteados, hallazgos
