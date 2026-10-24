#!/usr/bin/env python3
"""Contraste WCAG 2.2 de un par de colores, componiendo la transparencia.

  contrast.py "#333333" "#ffffff"
  contrast.py "rgba(0,0,0,0.5)" "#ffffff"                  el alfa se compone sobre el fondo
  contrast.py "#1a1a1a" "rgba(255,255,255,0.8)" --backdrop "#003366"
  contrast.py "#767676" "#fff" --size 16 --json

Un primer plano con alfa se compone sobre el fondo, en sRGB y redondeando cada canal a 8 bits como
hace un navegador. Un fondo con alfa menor a 1 necesita `--backdrop`, el color opaco que hay debajo:
sin él no hay número que dar y el script lo dice, no lo inventa. Lo mismo para `currentColor`,
`var(--x)`, `inherit` y los formatos de color que no conoce.

Criterios que informa: 1.4.3 (AA), 1.4.6 (AAA), 1.4.11 (AA, componentes y gráficos) y, como dato,
el 3:1 de 2.4.13 (AAA). El texto grande es de 24 px (18 pt) o de 14 pt (18,67 px) en negrita.

Código de salida: 0 calculado, 2 no se pudo calcular (limitación) o uso incorrecto.
Compatible con Python 3.9.
"""
import argparse
import json
import re
import sys

NOMBRES = {
    "white": (255, 255, 255), "black": (0, 0, 0), "red": (255, 0, 0),
    "green": (0, 128, 0), "blue": (0, 0, 255), "gray": (128, 128, 128),
    "grey": (128, 128, 128), "yellow": (255, 255, 0), "orange": (255, 165, 0),
    "purple": (128, 0, 128), "silver": (192, 192, 192), "navy": (0, 0, 128),
    "teal": (0, 128, 128), "maroon": (128, 0, 0), "olive": (128, 128, 0),
    "lime": (0, 255, 0), "aqua": (0, 255, 255), "cyan": (0, 255, 255),
    "fuchsia": (255, 0, 255), "magenta": (255, 0, 255),
}
DINAMICOS = ("currentcolor", "inherit", "initial", "unset", "revert", "var(", "env(", "attr(", "calc(", "color-mix(")
OTROS_ESPACIOS = ("color(", "lab(", "lch(", "oklab(", "oklch(", "hwb(", "light-dark(")
GRANDE_PX = 24.0
GRANDE_NEGRITA_PX = 14.0 * 4.0 / 3.0


class Limitacion(Exception):
    """Lo que el script no puede calcular, dicho con el motivo."""


def _numero(texto, maximo=None):
    """Un número CSS; si lleva %, una fracción (o esa fracción de `maximo`)."""
    texto = texto.strip()
    if texto.endswith("%"):
        valor = float(texto[:-1]) / 100.0
        return valor * maximo if maximo is not None else valor
    return float(texto)


def _alfa(texto):
    if texto is None:
        return 1.0
    return min(1.0, max(0.0, _numero(texto)))


def _hsl_a_rgb(h, s, l):
    h = (h % 360.0) / 360.0
    if s == 0:
        v = l
        return (v, v, v)

    def f(p, q, t):
        t = t % 1.0
        if t < 1.0 / 6:
            return p + (q - p) * 6 * t
        if t < 0.5:
            return q
        if t < 2.0 / 3:
            return p + (q - p) * (2.0 / 3 - t) * 6
        return p

    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    return (f(p, q, h + 1.0 / 3), f(p, q, h), f(p, q, h - 1.0 / 3))


def leer_color(texto):
    """(r, g, b, alfa) con r, g, b en 0..255 y alfa en 0..1. Lanza Limitacion si no puede."""
    t = texto.strip()
    bajo = t.lower()
    if any(d in bajo for d in DINAMICOS):
        raise Limitacion("«%s» depende de la cascada o de una variable: el script no la ve. Pasá el color ya resuelto (el valor computado en el navegador)." % t)
    if any(bajo.startswith(o) for o in OTROS_ESPACIOS):
        raise Limitacion("«%s» está en un espacio de color que el script no convierte. Pasá su equivalente en #rrggbb o rgb()." % t)
    if bajo == "transparent":
        return (0.0, 0.0, 0.0, 0.0)
    if bajo in NOMBRES:
        r, g, b = NOMBRES[bajo]
        return (float(r), float(g), float(b), 1.0)
    m = re.fullmatch(r"#?([0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})", bajo)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        a = int(h[6:8], 16) / 255.0 if len(h) == 8 else 1.0
        return (float(r), float(g), float(b), a)
    m = re.fullmatch(r"rgba?\(\s*([^,/\s)]+)\s*[, ]\s*([^,/\s)]+)\s*[, ]\s*([^,/\s)]+)\s*(?:[,/]\s*([^)\s]+)\s*)?\)", bajo)
    if m:
        try:
            canales = [min(255.0, max(0.0, _numero(m.group(i), maximo=255.0))) for i in (1, 2, 3)]
            return (canales[0], canales[1], canales[2], _alfa(m.group(4)))
        except ValueError:
            pass
    m = re.fullmatch(r"hsla?\(\s*([^,/\s)]+)\s*[, ]\s*([^,/\s)]+)\s*[, ]\s*([^,/\s)]+)\s*(?:[,/]\s*([^)\s]+)\s*)?\)", bajo)
    if m:
        try:
            h = float(re.sub(r"deg$", "", m.group(1)))
            s = _numero(m.group(2))
            l = _numero(m.group(3))
            s, l = (s / 100.0 if s > 1.0 else s), (l / 100.0 if l > 1.0 else l)
            r, g, b = _hsl_a_rgb(h, min(1.0, max(0.0, s)), min(1.0, max(0.0, l)))
            return (r * 255.0, g * 255.0, b * 255.0, _alfa(m.group(4)))
        except ValueError:
            pass
    raise Limitacion("No reconozco el color «%s». Entiendo #rgb, #rgba, #rrggbb, #rrggbbaa, rgb(), rgba(), hsl(), hsla() y los nombres básicos." % t)


def _redondear(v):
    return int(min(255, max(0, int(v + 0.5))))


def componer(frente, fondo):
    """El color opaco que resulta de poner `frente` (con su alfa) sobre `fondo` (opaco)."""
    a = frente[3]
    return tuple(_redondear(a * frente[i] + (1.0 - a) * fondo[i]) for i in range(3))


def _canal(c8):
    c = c8 / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminancia(rgb):
    r, g, b = (_canal(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def relacion(c1, c2):
    l1, l2 = luminancia(c1), luminancia(c2)
    alto, bajo = max(l1, l2), min(l1, l2)
    return (alto + 0.05) / (bajo + 0.05)


def es_grande(tam_px, negrita):
    if tam_px is None:
        return None
    return tam_px >= GRANDE_PX - 1e-9 or (bool(negrita) and tam_px >= GRANDE_NEGRITA_PX - 1e-9)


def hexa(rgb):
    return "#%02x%02x%02x" % tuple(rgb)


def calcular(frente, fondo, base=None, tam_px=None, negrita=False):
    """Resuelve capas y relación. Lanza Limitacion si falta información."""
    f, b = leer_color(frente), leer_color(fondo)
    notas = []
    if b[3] < 1.0:
        if base is None:
            raise Limitacion("El fondo «%s» es translúcido (alfa %.2f) y no sé qué hay debajo: sin la base no hay un contraste que calcular. Pasá `--backdrop` con el color opaco de abajo." % (fondo.strip(), b[3]))
        base_c = leer_color(base)
        if base_c[3] < 1.0:
            raise Limitacion("La base «%s» tampoco es opaca: hace falta el color opaco que está al fondo de todo." % base.strip())
        fondo_efectivo = componer(b, base_c)
        notas.append("fondo %s compuesto sobre la base %s = %s" % (fondo.strip(), base.strip(), hexa(fondo_efectivo)))
    else:
        fondo_efectivo = tuple(_redondear(b[i]) for i in range(3))
    if f[3] < 1.0:
        frente_efectivo = componer(f, fondo_efectivo)
        notas.append("primer plano %s (alfa %.2f) compuesto sobre %s = %s" % (frente.strip(), f[3], hexa(fondo_efectivo), hexa(frente_efectivo)))
    else:
        frente_efectivo = tuple(_redondear(f[i]) for i in range(3))
    ratio = relacion(frente_efectivo, fondo_efectivo)
    grande = es_grande(tam_px, negrita)
    r = {
        "foreground": hexa(frente_efectivo),
        "background": hexa(fondo_efectivo),
        "ratio": round(ratio, 2),
        "ratio_text": "%.2f:1" % ratio,
        "large_text": grande,
        "composition": notas,
        "criteria": {
            "1.4.3": {"level": "AA", "normal_text": ratio >= 4.5, "large_text": ratio >= 3.0},
            "1.4.6": {"level": "AAA", "normal_text": ratio >= 7.0, "large_text": ratio >= 4.5},
            "1.4.11": {"level": "AA", "non_text": ratio >= 3.0},
            "2.4.13": {"level": "AAA", "focus_change": ratio >= 3.0},
        },
    }
    if grande is not None:
        r["criteria"]["1.4.3"]["this_text"] = ratio >= (3.0 if grande else 4.5)
        r["criteria"]["1.4.6"]["this_text"] = ratio >= (4.5 if grande else 7.0)
    return r


def _pf(b):
    return "cumple" if b else "NO cumple"


def informe(r):
    c = r["criteria"]
    out = ["Contraste %s sobre %s: %s" % (r["foreground"], r["background"], r["ratio_text"].replace(".", ","))]
    out.extend("  " + n for n in r["composition"])
    out.append("  1.4.3  (AA)  texto normal 4,5:1 %s · texto grande 3:1 %s" % (_pf(c["1.4.3"]["normal_text"]), _pf(c["1.4.3"]["large_text"])))
    out.append("  1.4.11 (AA)  componentes de interfaz y gráficos 3:1 %s" % _pf(c["1.4.11"]["non_text"]))
    out.append("  1.4.6  (AAA) texto normal 7:1 %s · texto grande 4,5:1 %s — es AAA, no forma parte de AA" % (_pf(c["1.4.6"]["normal_text"]), _pf(c["1.4.6"]["large_text"])))
    if r["large_text"] is not None:
        tipo = "grande" if r["large_text"] else "normal"
        out.append("  Para este texto (%s): 1.4.3 %s · 1.4.6 (AAA) %s" % (tipo, _pf(c["1.4.3"]["this_text"]), _pf(c["1.4.6"]["this_text"])))
    else:
        out.append("  No se dio el tamaño (`--size`): el veredicto del texto depende de si es grande.")
    return "\n".join(out)


def main(argv=None):
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            try:
                flujo.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("foreground")
    p.add_argument("background")
    p.add_argument("--backdrop", help="color opaco que hay debajo de un fondo translúcido")
    p.add_argument("--size", type=float, help="tamaño de fuente en px CSS (con --pt, en puntos)")
    p.add_argument("--pt", action="store_true", help="interpreta --size como puntos")
    p.add_argument("--bold", action="store_true", help="font-weight 700 o más")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    tam = a.size * 4.0 / 3.0 if (a.size is not None and a.pt) else a.size
    try:
        r = calcular(a.foreground, a.background, a.backdrop, tam, a.bold)
    except Limitacion as e:
        if a.json:
            sys.stdout.write(json.dumps({"error": "limitation", "reason": str(e)}, ensure_ascii=False) + "\n")
        else:
            sys.stderr.write("Limitación: %s\n" % e)
        return 2
    if a.json:
        sys.stdout.write(json.dumps(r, ensure_ascii=False, indent=1) + "\n")
    else:
        sys.stdout.write(informe(r) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
