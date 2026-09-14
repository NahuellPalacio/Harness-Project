"""Lo que se le hace a un texto que viene de afuera antes de escribirlo en disco.

Dos operaciones, y las dos existen por el mismo motivo: el `TaskContext` lo escribe una
maquina y lo lee un agente entero.

1. **Redaccion de secretos.** Una descripcion de Jira puede traer un token pegado por
   alguien. Escribirlo en el contexto seria crear un archivo con un secreto adentro, y
   encima uno que un agente va a cargar completo. El catalogo de patrones NO se duplica:
   es el mismo `comun/reglas/secretos.patrones.json` que usa el hook de PreToolUse, y las
   funciones que deciden si un valor es ignorable y como se lo describe sin repetirlo son
   las de `comun/hooks/lib/secretos.py`.

   🔴 Solo redacta lo de confianza **alta**. En el hook, lo ambiguo pregunta y decide una
   persona; aca no hay a quien preguntar, y un falso positivo que mutile una descripcion
   es peor que un aviso. Lo de confianza media se declara en los huecos y el texto no se
   toca.

2. **Recorte.** Un documento de doscientas paginas no entra en el contexto de nadie. Se
   recorta en un tope declarado y el recorte se dice, que es lo contrario de que el texto
   aparezca completo a medias.
"""
import os
import re
import sys

_CACHE = {}


def _raices_posibles(desde):
    """Las dos formas en que este archivo puede estar parado.

    Instalado: <proyecto>/.claude/harness/bin/desarrollo/contexto/  -> harness/ esta 3 arriba
    En el repo: <repo>/harnesses/desarrollo/bin/contexto/           -> comun/ esta 4 arriba
    """
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


def _localizar(relativa, desde=__file__):
    """La primera ruta que exista, probando el arbol instalado y el del repositorio."""
    for base in _raices_posibles(desde):
        ruta = os.path.join(base, *relativa)
        if os.path.exists(ruta):
            return os.path.normpath(ruta)
    return None


def modulo_secretos():
    """El detector del harness, importado -no copiado-.

    Se importa como parte del paquete `lib` porque `secretos.py` hace `from . import hook`:
    cargarlo suelto por ruta lo rompe.
    """
    if "secretos" in _CACHE:
        return _CACHE["secretos"]
    hooks = _localizar(("hooks", "lib", "secretos.py"))
    if hooks is None:
        _CACHE["secretos"] = None
        return None
    dir_hooks = os.path.dirname(os.path.dirname(hooks))
    if dir_hooks not in sys.path:
        sys.path.insert(0, dir_hooks)
    try:
        from lib import secretos  # noqa: E402
    except ImportError:
        secretos = None
    _CACHE["secretos"] = secretos
    return secretos


def cargar_catalogo():
    """El mismo archivo de patrones que usa el hook. None si no esta."""
    if "catalogo" in _CACHE:
        return _CACHE["catalogo"]
    secretos = modulo_secretos()
    ruta = _localizar(("reglas", "secretos.patrones.json"))
    catalogo = None
    if secretos is not None and ruta is not None:
        try:
            catalogo = secretos.importar_patrones(ruta)
        except (OSError, ValueError):
            catalogo = None
    _CACHE["catalogo"] = catalogo
    return catalogo


def _patrones(catalogo, confianza):
    return [p for p in catalogo["patrones"] if p.get("confianza") == confianza]


def redactar(texto, catalogo, donde=""):
    """Devuelve (texto_limpio, hallazgos). Nunca devuelve el valor encontrado."""
    if not texto or catalogo is None:
        return texto, []
    secretos = modulo_secretos()
    hallazgos = []
    limpio = texto

    for patron in _patrones(catalogo, "alta"):
        def _reemplazo(m, _p=patron):
            valor = m.group(0)
            if secretos.es_valor_ignorable(valor, catalogo):
                return valor
            muestra = secretos.muestra_segura(valor)
            hallazgos.append("%s: %s redactado en %s" % (_p["id"], muestra, donde or "el texto"))
            return "[secreto redactado: %s %s]" % (_p["id"], muestra)
        limpio = re.sub(patron["regex"], _reemplazo, limpio)

    # Confianza media: se declara y no se toca. Es la mitad de la regla que el hook
    # resuelve preguntando, y que aca no tiene a quien preguntarle.
    for patron in _patrones(catalogo, "media"):
        m = re.search(patron["regex"], limpio)
        if m and not secretos.es_valor_ignorable(m.group(0), catalogo):
            hallazgos.append("%s: posible credencial en %s, sin tocar el texto (confianza media)"
                             % (patron["id"], donde or "el texto"))

    return limpio, hallazgos


def redactar_arbol(nodo, catalogo, donde="$"):
    """Redacta CADA string de una estructura anidada. Devuelve (nodo, hallazgos).

    🔴 Esto existe porque la version anterior redactaba campo por campo y dos rutas se
    escapaban: los criterios de aceptacion y el titulo de la Ficha. No era un olvido de
    dos lineas — era la forma equivocada de garantizarlo. Redactar en cada lugar donde se
    arma un campo obliga a acordarse una vez por campo, para siempre, y el campo numero
    veinte lo escribe alguien que no leyo esta discusion.

    Recorriendo el documento entero, "ninguna ruta de entrada esquiva la limpieza" pasa de
    ser una promesa a ser una propiedad de la estructura. El `donde` que sale en el hueco
    es la ruta adentro del documento, que ademas dice mejor que un nombre de campo suelto.
    """
    if isinstance(nodo, str):
        return redactar(nodo, catalogo, donde)
    if isinstance(nodo, list):
        hallazgos = []
        salida = []
        for i, hijo in enumerate(nodo):
            limpio, h = redactar_arbol(hijo, catalogo, "%s[%d]" % (donde, i))
            salida.append(limpio)
            hallazgos.extend(h)
        return salida, hallazgos
    if isinstance(nodo, dict):
        hallazgos = []
        salida = {}
        for clave in nodo:
            limpio, h = redactar_arbol(nodo[clave], catalogo, "%s.%s" % (donde, clave))
            salida[clave] = limpio
            hallazgos.extend(h)
        return salida, hallazgos
    return nodo, []


def recortar(texto, tope):
    """Devuelve (texto, recortado). El recorte se declara, no se disimula."""
    if not texto or tope <= 0 or len(texto) <= tope:
        return texto, False
    return texto[:tope] + "\n\n[...recortado por el harness en %d caracteres]" % tope, True
