"""ExecutionEvidence: dos fotos del arbol y una regla de atribucion por ruta.

docs/cambios/minimal-execution-engine/spec.md, MD-20.

    instantanea(proyecto)   la revision y cada ruta sucia con la huella de su contenido
    armar(...)              la evidencia de una corrida: lo que cambio entre las dos fotos
    comparar(...)           la de una huerfana: la foto de ahora contra la de la entrega

🔴 El repo sucio se permite. El motor no limpia, no hace `stash`, ni `reset`, ni `checkout`: lo
sucio que no cambio no es de la Execution, lo limpio que cambio si, y lo sucio que cambio otra vez
no se puede separar.

🔴 La evidencia no es contabilidad: no lleva tiempos, tokens ni costo.
"""
import hashlib
import io
import os
import re

from . import proceso
from . import registro

RESUELTO = "RESOLVED"
SIN_RESOLVER = "CHANGES_UNRESOLVED"
NO_ATRIBUIBLE = "CHANGES_UNATTRIBUTABLE"

EXCLUIDA = "/".join(registro.RAIZ) + "/"
REVISION = re.compile(r"[0-9a-f]{40,64}")


def huella_de(ruta):
    """`sha256:` del contenido de un archivo, o None si no hay un archivo ahi."""
    if not os.path.isfile(ruta):
        return None
    sha = hashlib.sha256()
    with io.open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            sha.update(bloque)
    return "sha256:" + sha.hexdigest()


def _rutas_z(crudo):
    return [p for p in crudo.decode("utf-8", "surrogateescape").split("\0") if p]


def instantanea(proyecto):
    """{ok, revision, sucios: {ruta: huella o None}}. `ok` es False si no se pudo observar: sin
    git, fuera de un repositorio o sin respuesta a tiempo."""
    foto = {"ok": False, "revision": None, "sucios": {}}
    codigo, prefijo = proceso.git(proyecto, "rev-parse", "--show-prefix")
    if codigo != 0:
        return foto
    prefijo = prefijo.decode("utf-8", "surrogateescape").strip()
    codigo, revision = proceso.git(proyecto, "rev-parse", "--verify", "-q", "HEAD")
    if codigo is None:
        return foto
    revision = revision.decode("ascii", "replace").strip() if codigo == 0 else ""
    foto["revision"] = revision if REVISION.fullmatch(revision) else None
    codigo, crudo = proceso.git(proyecto, "status", "--porcelain=v1", "-z",
                                "--untracked-files=all", "--", ".")
    if codigo != 0:
        return foto
    entradas = _rutas_z(crudo)
    sucios = {}
    i = 0
    while i < len(entradas):
        entrada = entradas[i]
        xy, ruta = entrada[:2], entrada[3:]
        rutas = [ruta]
        if xy[:1] in ("R", "C") and i + 1 < len(entradas):
            rutas.append(entradas[i + 1])
            i += 1
        i += 1
        for r in rutas:
            if not r.startswith(prefijo):
                continue
            r = r[len(prefijo):]
            if not r or r == EXCLUIDA[:-1] or r.startswith(EXCLUIDA):
                continue
            sucios[r] = huella_de(os.path.join(proyecto, *r.split("/")))
    foto.update(ok=True, sucios=sucios)
    return foto


def _de(antes, despues, estado, archivos):
    return {"repoRevisionBefore": antes.get("revision"),
            "repoRevisionAfter": despues.get("revision"),
            "changes": {"state": estado, "files": archivos}}


def _commiteadas(proyecto, antes, despues):
    """Las rutas que tocaron los commits de la corrida, o None si git no contesto."""
    if antes == despues or not antes or not despues:
        return [] if antes == despues else None
    codigo, crudo = proceso.git(proyecto, "diff", "--name-only", "-z", "--no-renames", antes,
                                despues, "--", ".")
    if codigo != 0:
        return None
    codigo, prefijo = proceso.git(proyecto, "rev-parse", "--show-prefix")
    if codigo != 0:
        return None
    prefijo = prefijo.decode("utf-8", "surrogateescape").strip()
    return [r[len(prefijo):] for r in _rutas_z(crudo) if r.startswith(prefijo)]


def _versionadas(proyecto, revision, rutas):
    """Las de `rutas` que existen en `revision`. None si git no contesto."""
    if not revision or not rutas:
        return set()
    salida = set()
    rutas = sorted(rutas)
    for i in range(0, len(rutas), 200):
        codigo, crudo = proceso.git(proyecto, "ls-tree", "-r", "-z", "--name-only", "--full-name",
                                    revision, "--", *rutas[i:i + 200])
        if codigo != 0:
            return None
        salida |= set(_rutas_z(crudo))
    codigo, prefijo = proceso.git(proyecto, "rev-parse", "--show-prefix")
    if codigo != 0:
        return None
    prefijo = prefijo.decode("utf-8", "surrogateescape").strip()
    return set(r[len(prefijo):] for r in salida if r.startswith(prefijo))


def armar(proyecto, antes, despues, otras_corriendo=False):
    """La ExecutionEvidence de una corrida, de la foto de la entrega y la de ahora."""
    if not antes.get("ok") or not despues.get("ok"):
        return _de(antes, despues, SIN_RESOLVER, [])
    sucios_antes, sucios_despues = antes["sucios"], despues["sucios"]
    commiteadas = _commiteadas(proyecto, antes.get("revision"), despues.get("revision"))
    if commiteadas is None:
        return _de(antes, despues, SIN_RESOLVER, [])
    ahora = {}
    for ruta in set(sucios_antes) | set(sucios_despues) | set(commiteadas):
        ahora[ruta] = sucios_despues[ruta] if ruta in sucios_despues else \
            huella_de(os.path.join(proyecto, *ruta.split("/")))
    cambiadas = set(r for r in commiteadas if not r.startswith(EXCLUIDA))
    for ruta in set(sucios_antes) | set(sucios_despues):
        if ruta not in sucios_antes or sucios_antes[ruta] != ahora[ruta]:
            cambiadas.add(ruta)
    if otras_corriendo or any(r in sucios_antes for r in cambiadas):
        return _de(antes, despues, NO_ATRIBUIBLE, [])
    malas = [r for r in cambiadas if registro.ruta_mala(proyecto, r)]
    if malas or registro.repetidas(sorted(cambiadas)):
        return _de(antes, despues, SIN_RESOLVER, [])
    estaban = _versionadas(proyecto, antes.get("revision"), cambiadas)
    if estaban is None:
        return _de(antes, despues, SIN_RESOLVER, [])
    archivos = []
    for ruta in sorted(cambiadas):
        existia = ruta in estaban
        existe = ahora[ruta] is not None
        if not existia and not existe:
            continue
        archivos.append({"path": ruta, "fingerprint": ahora[ruta],
                         "change": "MODIFIED" if existia and existe else
                         ("ADDED" if existe else "DELETED")})
    return _de(antes, despues, RESUELTO, archivos)


def comparar(antes, despues):
    """La evidencia de una huerfana: sin el motor no hay a quien atribuir. Si las dos fotos son
    iguales no cambio nada; si no, no se puede atribuir. Sin una de las dos, no se observo."""
    if not antes.get("ok") or not despues.get("ok"):
        return _de(antes, despues, SIN_RESOLVER, [])
    if antes.get("revision") == despues.get("revision") and antes["sucios"] == despues["sucios"]:
        return _de(antes, despues, RESUELTO, [])
    return _de(antes, despues, NO_ATRIBUIBLE, [])
