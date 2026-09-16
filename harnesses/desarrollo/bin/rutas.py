"""Donde esta cada cosa, segun el harness este instalado o corriendo desde el repositorio.

Los modulos de `bin/` tienen que encontrar archivos que viven en dos arboles distintos:

    instalado:  <proyecto>/.claude/harness/{hooks,reglas,schemas,bin}/...
    repositorio: <repo>/comun/{hooks,reglas,schemas,bin}/...  y  harnesses/desarrollo/reglas/...

La profundidad relativa cambia entre los dos, asi que no se puede escribir una ruta y ya.
Lo que se hace es subir hasta seis niveles desde quien pregunta, probando en cada nivel el
directorio tal cual y su subdirectorio `comun`, y quedarse con la primera ruta que exista.

Estaba adentro de `contexto/limpieza.py` y lo necesitaba tambien orquestacion. Vive aca
para que haya una sola: dos busquedas de rutas con criterios parecidos es como un dia una
encuentra el catalogo de secretos y la otra no.
"""
import os


def raices(desde):
    """Los directorios donde vale la pena buscar, del mas cercano al mas lejano."""
    d = os.path.dirname(os.path.abspath(desde))
    arriba = [d]
    for _ in range(6):
        d = os.path.dirname(d)
        arriba.append(d)
    candidatas = []
    for base in arriba:
        candidatas.append(base)
        candidatas.append(os.path.join(base, "comun"))
    return candidatas


def localizar(relativa, desde, extra=()):
    """La primera ruta que exista. `relativa` es una tupla de segmentos.

    `extra` son raices adicionales a probar primero: es lo que permite buscar algo que en
    el arbol instalado cuelga de un harness -reglas/<id>/- y en el repositorio de
    harnesses/<id>/.
    """
    for base in list(extra) + raices(desde):
        ruta = os.path.join(base, *relativa)
        if os.path.exists(ruta):
            return os.path.normpath(ruta)
    return None


def raiz_del_harness(desde):
    """El directorio que contiene hooks/ y reglas/, o None.

    Instalado es `.claude/harness`; en el repositorio es `comun`. Sirve para resolver lo
    que cuelga de ahi sin repetir la busqueda entera.
    """
    ruta = localizar(("reglas", "secretos.patrones.json"), desde)
    if ruta is None:
        return None
    return os.path.dirname(os.path.dirname(ruta))
