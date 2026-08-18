"""Deteccion de secretos. La unica regla del harness que impide algo.

Dos niveles de confianza, y la distincion es lo importante:

  alta  -> se bloquea. Formas inequivocas: una clave privada PEM no es otra cosa.
  media -> se pregunta. Formas plausibles pero ambiguas: decide la persona.

El falso positivo es el riesgo existencial de este harness. Uno que traba trabajo
legitimo se desinstala esa misma semana, y ahi se pierde tambien la proteccion que
si servia. Por eso lo ambiguo pregunta en vez de bloquear.

Este modulo es solo el detector. Quien decide que hacer con el hallazgo es el hook.
"""
import json
import os
import re

from . import hook


def importar_patrones(ruta):
    """Carga el catalogo de patrones desde reglas/secretos.patrones.json."""
    if not os.path.isfile(ruta):
        raise FileNotFoundError("no se encontro el catalogo de patrones: %s" % ruta)
    with open(ruta, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def valor_de_asignacion(coincidencia):
    """De "password = xxxxx" devuelve "xxxxx". Si no hay asignacion, devuelve todo.

    Entre los delimitadores que se descartan esta la comilla invertida, y no es
    estilo: es el delimitador de codigo de markdown. Sin eso, documentar el propio
    detector lo dispara. Paso al escribir docs/versiones/0.4.0.md.
    """
    m = re.search(r"[:=]\s*[\"'`]?\s*(.+?)\s*[\"'`]?\s*$", coincidencia)
    return m.group(1) if m else coincidencia


def es_valor_ignorable(valor, catalogo):
    """Se prueba contra el valor aislado Y contra la coincidencia entera: hay
    patrones de ignorar anclados al valor (^x{3,}$) y otros que aparecen en
    cualquier lado (process.env).

    re.IGNORECASE en las dos comparaciones: en PowerShell, -match es case-insensitive
    siempre, tenga o no (?i) el patron. Catorce de los quince patrones de ignorar
    traen (?i) -alli redundante-, pero \\$env: no lo trae porque alli nunca hizo
    falta. Sin IGNORECASE aca, "$Env:" o "$ENV:" dejan de matchear ese patron y un
    valor benigno como "password = $Env:DB_PASSWORD" se bloquea como si fuera un
    secreto real.
    """
    if not valor or not valor.strip():
        return True
    aislado = valor_de_asignacion(valor)
    if not aislado or not aislado.strip():
        return True
    for p in catalogo["ignorar"]["patrones"]:
        if re.search(p, aislado, re.IGNORECASE) or re.search(p, valor, re.IGNORECASE):
            return True
    return False


def muestra_segura(valor):
    """Describe el hallazgo sin repetir el secreto: entra al contexto de Claude y
    queda en la transcripcion."""
    limpio = re.sub(r"\s+", " ", valor).strip()
    if len(limpio) <= 12:
        return limpio[:4] + "..."
    return "%s... (%d caracteres)" % (limpio[:12], len(limpio))


def texto_de_herramienta(evento):
    """Extrae de un evento lo que la herramienta esta por escribir o ejecutar.

    Cada herramienta trae su carga en un campo distinto. Se juntan todos los que
    pueden llevar contenido en vez de asumir la forma de uno.
    """
    if evento is None:
        return ""

    partes = []
    for campo_nombre in ("content", "new_string", "command", "new_source", "prompt"):
        valor = hook.campo(evento, "tool_input." + campo_nombre, "")
        if valor:
            partes.append(str(valor))

    # MultiEdit trae una lista de ediciones en vez de un solo new_string.
    ediciones = hook.campo(evento, "tool_input.edits", None)
    if ediciones:
        for e in ediciones:
            valor = hook.campo(e, "new_string", "")
            if valor:
                partes.append(str(valor))

    return "\n".join(partes)


def buscar_secreto(texto, catalogo):
    """Los de confianza alta primero: si hay uno, gana sobre cualquier ambiguo."""
    if not texto or not texto.strip():
        return None
    for nivel in ("alta", "media"):
        for patron in catalogo["patrones"]:
            if patron.get("confianza") != nivel:
                continue
            m = re.search(patron["regex"], texto)
            if not m:
                continue
            if es_valor_ignorable(m.group(0), catalogo):
                continue
            return {"id": patron["id"], "confianza": patron["confianza"],
                    "motivo": patron["motivo"], "muestra": muestra_segura(m.group(0))}
    return None
