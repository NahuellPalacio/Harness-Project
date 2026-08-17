"""Check: las dependencias se fijan en una version exacta (ES0901).

ES0901 no deja elegir la version de una dependencia: se toma la homologada. Un rango
-^1.2.0, ~1.2.0, >=1.2, *- delega esa eleccion al gestor de paquetes, que va a
resolver distinto en la maquina de quien desarrolla, en el pipeline y en produccion.

Es de los pocos incumplimientos que no se nota nunca hasta que se nota mal: el build
anda meses hasta que una version nueva entra sola y rompe algo en el ambiente donde
duele. Por eso vale un aviso aunque el codigo funcione.

Avisa, no bloquea. Lo unico que este harness bloquea son los secretos.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import dev  # noqa: E402

# Un rango es cualquier cosa que no sea una version completa y unica. Se listan las
# formas y no se niega "lo que no es exacto": asi un valor raro -una ruta, un tag de
# git, un alias de workspace- no se reporta como si fuera un rango.
FORMAS_DE_RANGO = [
    r"^\^",
    r"^~",
    r"^\*$",
    r"^(>=|<=|>|<)",
    r"\|\|",
    r" - ",
    r"^\d+\.(x|\*)",
    r"^\d+\.\d+\.(x|\*)",
]

BLOQUES = ["dependencies", "devDependencies", "peerDependencies", "require", "require-dev"]


def verificar(evento, proyecto, config):
    """Devuelve cero o mas strings. Cada string es un hallazgo."""
    archivo = dev.archivo_escrito(evento)
    if archivo is None:
        return []
    if archivo["nombre"] not in ("package.json", "composer.json"):
        return []
    if dev.es_ruta_generada(archivo["ruta"]):
        return []

    try:
        datos = json.loads(archivo["texto"])
    except ValueError:
        return []

    if not isinstance(datos, dict):
        return []

    sueltas = []

    for b in BLOQUES:
        seccion = datos.get(b)
        if seccion is None or not isinstance(seccion, dict):
            continue

        for nombre, valor in seccion.items():
            valor = "" if valor is None else str(valor)
            if not valor:
                continue

            for patron in FORMAS_DE_RANGO:
                if re.search(patron, valor):
                    sueltas.append("%s %s" % (nombre, valor))
                    break

    if not sueltas:
        return []

    return [
        "[ES0901] %s: %d dependencia(s) con rango en vez de version exacta — %s. "
        "La version la fija el estandar, no el gestor de paquetes: un rango resuelve distinto en tu maquina, "
        "en el pipeline y en produccion, y la diferencia aparece en el ambiente donde mas duele."
        % (archivo["nombre"], len(sueltas), dev.formatear_lista(sueltas))
    ]
