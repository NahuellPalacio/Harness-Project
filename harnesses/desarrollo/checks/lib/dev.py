"""Ayudantes que comparten los checks de desarrollo.

Todos los checks de este harness empiezan igual: averiguar que archivo se acaba de
escribir, decidir si les incumbe, y leerlo. Repetir eso cuatro veces multiplica por
cuatro las chances de que uno lo haga distinto.

La regla que ordena a todos: SALIR TEMPRANO. PostToolUse corre despues de cada
escritura de cada sesion. Un check que se pone a analizar archivos que no le tocan
paga latencia en cada turno, y el presupuesto de avisos es de ocho en total: los que
gasta un check con ruido no los tiene el que encontro algo de verdad.

Se mantiene sin depender de comun/hooks/lib: cada check se carga por ruta (ver
lib.reglas._cargar), no como parte de un paquete, asi que resolver esa ruta relativa
seria fragil. El acceso a un campo del evento se resuelve aca mismo, chico como es.
"""
import os
import re


def _campo(evento, ruta, default=None):
    actual = evento
    for parte in ruta.split("."):
        if not isinstance(actual, dict) or parte not in actual:
            return default
        actual = actual[parte]
    return default if actual is None else actual


def archivo_escrito(evento):
    """Ruta y contenido del archivo que la herramienta acaba de escribir, o None.

    Se lee del disco y no del evento: MultiEdit manda las ediciones sueltas y Edit
    manda solo el fragmento, asi que el evento no tiene el archivo entero. Lo que
    importa es como quedo, que es lo que va a compilar y lo que va a leer el proximo.
    """
    ruta = _campo(evento, "tool_input.file_path", "")
    if not ruta:
        return None
    if not os.path.isfile(ruta):
        return None

    # Un archivo enorme no se analiza: el costo no lo justifica y suele ser generado.
    try:
        if os.path.getsize(ruta) > 512 * 1024:
            return None
    except OSError:
        return None

    try:
        with open(ruta, encoding="utf-8-sig") as f:
            texto = f.read()
    except OSError:
        return None

    return {
        "ruta": ruta,
        "nombre": os.path.basename(ruta),
        "extension": os.path.splitext(ruta)[1].lower(),
        "texto": texto,
    }


def es_ruta_generada(ruta):
    """Verdadero si la ruta cae en un directorio que nadie escribe a mano.

    Avisar sobre node_modules o vendor es garantia de que el harness se apague: el
    hallazgo es correcto y no hay nada que la persona pueda hacer al respecto.
    """
    return bool(re.search(
        r"[\\/](node_modules|vendor|dist|build|out|bin|obj|\.git|\.venv|__pycache__|coverage|target)[\\/]",
        ruta))


def linea_de(texto, aguja):
    """Numero de linea (1-based) donde cae un indice de caracter.

    Un aviso sin numero de linea obliga a buscar a mano lo que el check ya encontro.
    """
    indice = aguja
    if indice <= 0:
        return 1
    if indice > len(texto):
        indice = len(texto)
    return texto[:indice].count("\n") + 1


def formatear_lista(items, maximo=3):
    """Une hasta N ejemplos y dice cuantos quedaron afuera.

    Un aviso que enumera cuarenta ocurrencias no se lee. Tres y el total si.
    """
    items = list(items)
    muestra = items[:maximo]
    texto = ", ".join(muestra)
    if len(items) > maximo:
        texto += " (+%d mas)" % (len(items) - maximo)
    return texto
