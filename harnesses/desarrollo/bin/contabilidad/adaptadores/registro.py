"""El unico lugar del Bloque 4 donde un proveedor es un nombre.

Todo lo demas -la agregacion, el motor de costos, el de tiempo, el presupuesto, el reporte
y la barra- no menciona a ninguno. Un `if provider == "..."` en el nucleo convierte al
adaptador en una decoracion: la rama vuelve al centro, y el proveedor numero tres se agrega
tocando el centro otra vez.

Agregar un proveedor es escribir su modulo y agregar una fila acá. Nada mas.
"""
from . import claude_code
from . import codex

ADAPTADORES = {
    claude_code.NOMBRE: claude_code,
    codex.NOMBRE: codex,
}

# Los nombres de proveedor que este registro conoce. La contabilidad los usa para
# comprobar que el nucleo no los nombra: la lista sale de acá y no de una copia paralela,
# que el dia que alguien agregue un adaptador quedaria vieja sin que nadie se entere.
PROVEEDORES = tuple(sorted(set(
    [m.PROVEEDOR for m in ADAPTADORES.values()] + list(ADAPTADORES))))


def nombres():
    return tuple(sorted(ADAPTADORES))


def resolver(nombre):
    """El adaptador, o None. Un nombre que nadie declaro no se parece al mas cercano."""
    return ADAPTADORES.get(str(nombre or ""))


def leer(nombre, ruta=""):
    """Los registros normalizados de una fuente. Levanta si el adaptador no existe."""
    adaptador = resolver(nombre)
    if adaptador is None:
        raise KeyError(
            "no hay un adaptador `%s`. Los declarados son: %s."
            % (nombre, ", ".join(nombres())))
    return adaptador.leer(ruta)
