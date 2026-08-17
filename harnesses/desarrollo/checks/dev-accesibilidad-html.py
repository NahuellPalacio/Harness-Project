"""Check: accesibilidad comprobable sobre el marcado (ley 26.653 - WCAG).

La accesibilidad no es una mejora: es condicion de aprobacion, y en el GCBA es
exigible por ley. La mayor parte no se puede verificar con una maquina -si el texto
alternativo describe la imagen, si el orden de foco tiene sentido- pero un punado si,
y son justamente las que se arreglan en diez segundos mientras el archivo esta
abierto, y en dos horas cuando vuelve rebotado de una auditoria.

Lo que mira, todo inequivoco:

  - <html> sin lang. Sin eso el lector de pantalla pronuncia el castellano con
    fonetica inglesa y la pagina es inescuchable.
  - <img> sin atributo alt. Ojo: alt="" es correcto y no se reporta - declara que la
    imagen es decorativa. Lo que falla es que el atributo no este.
  - Un control de formulario que no puede tener etiqueta asociada: sin id, sin
    aria-label y sin aria-labelledby no hay forma de nombrarlo.
  - Mas de un <h1>, o ninguno.

Avisa, no bloquea. Y no intenta juzgar contraste ni orden de lectura: para eso hace
falta renderizar, y un check que adivina es un check que se ignora.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import dev  # noqa: E402


def verificar(evento, proyecto, config):
    """Devuelve cero o mas strings. Cada string es un hallazgo."""
    archivo = dev.archivo_escrito(evento)
    if archivo is None:
        return []
    if dev.es_ruta_generada(archivo["ruta"]):
        return []

    es_html = (archivo["extension"] == ".html"
               or bool(re.search(r"\.blade\.php$", archivo["nombre"]))
               or bool(re.search(r"\.component\.html$", archivo["nombre"])))
    if not es_html:
        return []

    texto = archivo["texto"]
    hallazgos = []

    # -- El idioma del documento -------------------------------------------------
    # Solo si el archivo ES un documento. Un parcial o un componente no llevan <html>.
    html = re.search(r"(?is)<html\b[^>]*>", texto)
    if html and not re.search(r"(?i)\slang\s*=", html.group(0)):
        hallazgos.append(
            "[a11y] %s: <html> sin atributo lang. "
            "El lector de pantalla necesita saber el idioma para elegir la fonetica; sin eso lee el castellano como si fuera ingles."
            % archivo["nombre"])

    # -- Texto alternativo ---------------------------------------------------------
    sin_alt = []
    for m in re.finditer(r"(?is)<img\b[^>]*>", texto):
        if re.search(r"(?i)\salt\s*=", m.group(0)):
            continue
        sin_alt.append("L%d" % dev.linea_de(texto, m.start()))
    if sin_alt:
        hallazgos.append(
            "[a11y] %s: %d <img> sin atributo alt — %s. "
            "Si la imagen es decorativa va alt=\"\" vacio, que es una afirmacion; que el atributo falte no dice nada."
            % (archivo["nombre"], len(sin_alt), dev.formatear_lista(sin_alt)))

    # -- Controles que no pueden ser etiquetados -----------------------------------
    sin_nombre = []
    for m in re.finditer(r"(?is)<(input|select|textarea)\b[^>]*>", texto):
        tag = m.group(0)
        if re.search(r"(?i)type\s*=\s*[\"']?(hidden|submit|button|reset|image)", tag):
            continue
        if re.search(r"(?i)\s(id|aria-label|aria-labelledby|title)\s*=", tag):
            continue
        sin_nombre.append("L%d" % dev.linea_de(texto, m.start()))
    if sin_nombre:
        hallazgos.append(
            "[a11y] %s: %d control(es) de formulario sin forma de nombrarlos — %s. "
            "Sin id que un <label for> pueda apuntar, ni aria-label, el control se anuncia como \"cuadro de edicion\" y nada mas."
            % (archivo["nombre"], len(sin_nombre), dev.formatear_lista(sin_nombre)))

    # -- Jerarquia de encabezados ---------------------------------------------------
    # Solo sobre documentos completos: un parcial puede legitimamente no tener h1.
    if html:
        h1 = len(re.findall(r"(?is)<h1\b[^>]*>", texto))
        if h1 == 0:
            hallazgos.append(
                "[a11y] %s: la pagina no tiene <h1>. Es el titulo con el que se navega el documento."
                % archivo["nombre"])
        elif h1 > 1:
            hallazgos.append(
                "[a11y] %s: hay %d elementos <h1>. Va uno solo: los demas niveles son h2 en adelante, sin saltos."
                % (archivo["nombre"], h1))

    return hallazgos
