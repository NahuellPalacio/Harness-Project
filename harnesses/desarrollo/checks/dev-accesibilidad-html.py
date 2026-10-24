"""Check: accesibilidad comprobable sobre el marcado (ley 26.653 - WCAG 2.2).

La accesibilidad no es una mejora: es condicion de aprobacion, y en el GCBA es exigible por ley.
La mayor parte no se puede verificar con una maquina -si el texto alternativo describe la imagen,
si el orden de foco tiene sentido- pero un punado si, y son justamente las que se arreglan en
diez segundos mientras el archivo esta abierto, y en dos horas cuando vuelve rebotado de una
auditoria.

Este check corre despues de CADA escritura, asi que es el liviano: solo dice lo que el archivo
decide por si mismo, y lo dice una vez.

  - Lee HTML, plantillas (Blade, Angular, Twig, Jinja, Handlebars, EJS...) y JSX/TSX, cada uno
    con el tokenizador que le corresponde (lib/a11y.py).
  - Solo emite `fallo` (incumple un criterio de WCAG 2.2) y `defecto` (marcado roto con efecto
    probable). Una heuristica, o una recomendacion que WCAG no exige -un solo <h1>-, queda para la
    revision completa: skills/dev-accessibility/scripts/review.py.
  - Un control con `id` sin una <label for> que lo apunte NO tiene nombre: el id solo no es una
    etiqueta. Un control envuelto en una <label> con texto SI lo tiene, aunque no tenga id.
  - En un fragmento (un parcial, un componente, un JSX) una etiqueta puede vivir en otro archivo:
    no se decide. Un componente propio (<TextField />) o un {...props} no se juzgan.
  - Un archivo que no puede leer produce silencio, nunca una excepcion.

Avisa, no bloquea. Y no intenta juzgar contraste, orden de foco ni lectura en voz alta: para eso
hace falta renderizar, y un check que adivina es un check que se ignora. Un analisis estatico
limpio no acredita conformidad.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import a11y  # noqa: E402
import dev  # noqa: E402


def verificar(evento, proyecto, config):
    """Devuelve cero o mas strings. Cada string es un hallazgo."""
    try:
        archivo = dev.archivo_escrito(evento)
        if archivo is None:
            return []
        if dev.es_ruta_generada(archivo["ruta"]):
            return []
        if a11y.formato_de(archivo["nombre"]) is None:
            return []
        resultado = a11y.revisar(archivo["texto"], archivo["nombre"], "liviano")
        return a11y.mensajes_livianos(resultado, archivo["nombre"])
    except Exception:      # un archivo ilegible o un fallo del motor se callan: el contrato es el silencio
        return []
