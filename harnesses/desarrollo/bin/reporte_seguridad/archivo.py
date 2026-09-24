"""La unica forma en que este paquete escribe un archivo entero, y la guarda que protege al libro.

Solo stdlib y sin imports del harness: lo usan el libro, el resumen y el renderizador, y el
renderizador no puede importar nada que calcule estado.

🔴 **Comparar el nombre no alcanza.** En Windows `SECURITY-LEDGER.NDJSON`,
`security-ledger.ndjson.` y `security-ledger.ndjson ` son el mismo archivo que
`security-ledger.ndjson`: el sistema de archivos no distingue mayusculas y descarta los puntos y
espacios del final de cada componente. `security-ledger.ndjson:x` escribe en un flujo alterno del
mismo archivo. Y un hardlink, un symlink o un nombre corto 8.3 lo alcanzan con otro nombre. La
guarda normaliza el nombre como lo hace Windows y, si el destino existe, lo compara con
`os.path.samefile` contra el libro de la misma carpeta.
"""
import io
import os
import re
import tempfile

LIBRO = "security-ledger.ndjson"


def _componente(nombre):
    """Un componente como lo resuelve Windows: sin flujo alterno, sin puntos ni espacios al final."""
    return os.path.normcase(nombre.split(":", 1)[0].rstrip(". ")).lower()


def es_el_libro(ruta):
    """True si escribir en esa ruta tocaria un `security-ledger.ndjson`."""
    texto = str(ruta or "")
    ultimo = [p for p in re.split(r"[\\/]+", texto) if p]
    if ultimo and _componente(ultimo[-1]) == LIBRO:
        return True
    if ultimo and os.path.exists(texto):
        real = os.path.realpath(texto)
        if _componente(os.path.basename(real)) == LIBRO:
            return True
        hermano = os.path.join(os.path.dirname(real), LIBRO)
        try:
            if os.path.exists(hermano) and os.path.samefile(texto, hermano):
                return True
        except OSError:
            return True  # si no se puede decidir, no se escribe
    return False


def exigir_que_no_sea_el_libro(ruta, quien):
    if es_el_libro(ruta):
        raise ValueError("%s no escribe sobre %s: el libro es append-only y esto lo truncaria."
                         % (quien, LIBRO))
    return ruta


def escribir_atomico(ruta, texto, quien="el reporte"):
    """Escribe a un `.tmp` y lo mueve encima. Nunca sobre el libro, se llame como se llame.

    Abrir el destino en modo `w` lo trunca antes de que la escritura pueda fallar; asi, si algo
    falla, queda el archivo anterior entero.

    🔴 El temporal se CREA con un nombre nuevo (`mkstemp`, O_CREAT|O_EXCL): un `<destino>.tmp` que
    ya existiera -un hardlink al libro, por ejemplo- no se abre nunca para escribir.
    """
    exigir_que_no_sea_el_libro(ruta, quien)
    carpeta = os.path.dirname(os.path.abspath(ruta))
    if carpeta and not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    descriptor, temporal = tempfile.mkstemp(prefix=os.path.basename(ruta) + ".",
                                            suffix=".tmp", dir=carpeta)
    with io.open(descriptor, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
    os.replace(temporal, ruta)
    return ruta
