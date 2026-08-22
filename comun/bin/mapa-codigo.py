#!/usr/bin/env python
"""
mapa-codigo - el grafo de las fichas del indice del codigo.

Lee las fichas que escribio dev-iniciador-code, saca las aristas de los enlaces que
tienen entre si, y escribe un `mapa.html` autocontenido al lado del indice.

    python mapa-codigo.py <directorio-de-fichas>

El resumen sale como JSON por stdout: cuantos nodos, cuantas aristas, cuales quedaron
huerfanas. Eso es lo que el recorrido pone en su reporte.

La pagina se recorre: Ctrl + rueda para acercar, arrastrar el fondo para desplazar, arrastrar un
nodo para correrlo, clic en un nodo para abrir su ficha en un panel al costado. Todo eso
es efimero -al recargar vuelve el acomodo del script- porque un archivo local no puede
escribir en disco, y un boton que promete guardar y no guarda es peor que no tenerlo.

Tres cosas que este script NO hace, y cada una es una decision:

  - No infiere. El nodo es la ficha y la arista es el enlace. Si una dependencia no
    esta enlazada, no aparece en el dibujo: se arregla en la ficha, no aca. Un
    generador que dedujera aristas por su cuenta pondria en el mapa cosas que ninguna
    ficha afirma, y nadie sabria cual de los dos esta mal.

  - No lee el codigo del proyecto. Solo los .md del directorio que se le pasa. Por eso
    no puede filtrar un secreto que las fichas no tengan ya adentro.

  - No usa nada de afuera. Biblioteca estandar, y la pagina no referencia ningun recurso
    remoto: es un archivo local que se abre con doble clic, a veces sin red y casi
    siempre en una maquina donde no se instala nada. El texto de cada ficha va EMBEBIDO
    por el mismo motivo: sobre `file://` un `fetch` lo bloquea CORS, asi que embeber no
    es una opcion entre varias, es la unica que funciona.

El layout es determinista a proposito. El archivo se versiona: si cada corrida
acomodara los nodos distinto, cada regeneracion seria un diff de mil lineas y el cambio
real quedaria tapado adentro del ruido. Por eso la semilla es una grilla entera y no un
circulo -cos y sin dependen de la libm de cada maquina, y ahi se va el determinismo-, y
por eso las posiciones salen redondeadas a entero. El script que lleva la pagina es
texto fijo: no toca el determinismo.
"""
import argparse
import io
import json
import math
import os
import re
import sys

INDICE = "indice.md"

# El mismo enlace que mira el check: se lee el destino del parentesis, que es lo que
# alguien va a seguir de verdad.
ENLACE = re.compile(r"\]\(\s*([^)\s]+\.md)\s*\)")

TITULO = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)

ANCHO, ALTO = 1600, 1000
ITERACIONES = 300
MARGEN = 60


# ── Leer ─────────────────────────────────────────────────────────────────────────

def leer_fichas(directorio):
    """Devuelve [(nombre_archivo, titulo, texto)] ordenado por nombre. Solo .md, solo
    de este directorio, sin recursion: una subcarpeta adentro del indice no es una
    ficha, y bajar a buscarla convertiria cualquier cosa en un nodo."""
    try:
        nombres = sorted(n for n in os.listdir(directorio)
                         if n.lower().endswith(".md") and n.lower() != INDICE)
    except OSError:
        return []

    fichas = []
    for nombre in nombres:
        ruta = os.path.join(directorio, nombre)
        if not os.path.isfile(ruta):
            continue
        with io.open(ruta, encoding="utf-8") as f:
            texto = f.read()
        m = TITULO.search(texto)
        titulo = m.group(1).strip() if m else os.path.splitext(nombre)[0]
        fichas.append((nombre, titulo, texto))
    return fichas


def armar_grafo(fichas):
    """Nodos y aristas. Una arista por par (origen, destino), aunque el enlace aparezca
    tres veces en la misma ficha: en el dibujo es la misma flecha."""
    conocidas = dict((n.lower(), n) for n, _t, _x in fichas)
    aristas = []
    vistas = set()

    for nombre, _titulo, texto in fichas:
        for destino in ENLACE.findall(texto):
            # Un enlace con ruta apunta afuera del indice -a un ADR, a una spec- y no
            # es una arista de este grafo. Uno a si misma tampoco.
            if "/" in destino or "\\" in destino:
                continue
            real = conocidas.get(destino.lower())
            if real is None or real == nombre:
                continue
            par = (nombre, real)
            if par not in vistas:
                vistas.add(par)
                aristas.append(par)

    return [n for n, _t, _x in fichas], aristas


# ── Acomodar ─────────────────────────────────────────────────────────────────────

def acomodar(nodos, aristas, cajas):
    """Fruchterman-Reingold con semilla de grilla. Solo +, -, *, / y raiz cuadrada:
    todas exactas segun IEEE 754, asi que dos maquinas dan el mismo resultado."""
    n = len(nodos)
    if n == 1:
        return {nodos[0]: (ANCHO // 2, ALTO // 2)}

    cols = int(math.ceil(math.sqrt(n)))
    filas = int(math.ceil(float(n) / cols))
    pos = {}
    for i, nombre in enumerate(nodos):
        fila, col = divmod(i, cols)
        pos[nombre] = [float(ANCHO) * (col + 1) / (cols + 1),
                       float(ALTO) * (fila + 1) / (filas + 1)]

    # El 0.72 junta el grafo. Con el k puro de Fruchterman-Reingold trece nodos piden
    # mas lugar del que hay y terminan todos pegados al marco, que es un dibujo que no
    # dice nada: lo que informa es cuales estan cerca de cuales.
    k = math.sqrt(float(ANCHO * ALTO) / n) * 0.72
    centro_x, centro_y = ANCHO / 2.0, ALTO / 2.0
    temp = ANCHO / 10.0
    enfriar = temp / (ITERACIONES + 1)

    for _ in range(ITERACIONES):
        desp = dict((nombre, [0.0, 0.0]) for nombre in nodos)

        for i in range(n):
            for j in range(i + 1, n):
                a, b = nodos[i], nodos[j]
                dx = pos[a][0] - pos[b][0]
                dy = pos[a][1] - pos[b][1]
                d2 = dx * dx + dy * dy
                if d2 == 0.0:
                    # Dos nodos exactamente encima: se separan por una cantidad que
                    # depende del indice, no del azar, para no perder el determinismo.
                    dx, dy = 0.01 * (j - i), 0.01
                    d2 = dx * dx + dy * dy
                d = math.sqrt(d2)
                fuerza = k * k / d
                ux, uy = dx / d, dy / d
                desp[a][0] += ux * fuerza
                desp[a][1] += uy * fuerza
                desp[b][0] -= ux * fuerza
                desp[b][1] -= uy * fuerza

        for origen, destino in aristas:
            dx = pos[origen][0] - pos[destino][0]
            dy = pos[origen][1] - pos[destino][1]
            d2 = dx * dx + dy * dy
            if d2 == 0.0:
                continue
            d = math.sqrt(d2)
            fuerza = d * d / k
            ux, uy = dx / d, dy / d
            desp[origen][0] -= ux * fuerza
            desp[origen][1] -= uy * fuerza
            desp[destino][0] += ux * fuerza
            desp[destino][1] += uy * fuerza

        for nombre in nodos:
            # Gravedad al centro: sin esto la repulsion empuja todo hacia afuera y el
            # recorte los deja apoyados contra el borde, en fila.
            desp[nombre][0] -= (pos[nombre][0] - centro_x) * 0.30
            desp[nombre][1] -= (pos[nombre][1] - centro_y) * 0.30

            dx, dy = desp[nombre]
            d = math.sqrt(dx * dx + dy * dy)
            if d > 0.0:
                paso = d if d < temp else temp
                pos[nombre][0] += dx / d * paso
                pos[nombre][1] += dy / d * paso
            # El recorte cuenta la mitad de la caja: recortar el centro deja el
            # rectangulo cortado por el marco, que fue lo que paso la primera vez.
            mitad_x = cajas[nombre][0] / 2.0
            mitad_y = cajas[nombre][1] / 2.0
            pos[nombre][0] = max(mitad_x, min(ANCHO - mitad_x, pos[nombre][0]))
            pos[nombre][1] = max(mitad_y, min(ALTO - mitad_y, pos[nombre][1]))

        temp -= enfriar

    return dict((nombre, (int(round(p[0])), int(round(p[1])))) for nombre, p in pos.items())


def encuadrar(pos, cajas):
    """Corre todo para que el dibujo arranque en el margen y devuelve el lienzo que
    realmente ocupa. Sin esto el viewBox es siempre el lienzo teorico y el grafo queda
    con una franja vacia de un lado."""
    izq = min(pos[n][0] - cajas[n][0] / 2.0 for n in pos)
    arr = min(pos[n][1] - cajas[n][1] / 2.0 for n in pos)
    corrido = dict((n, (int(round(x - izq + MARGEN)), int(round(y - arr + MARGEN))))
                   for n, (x, y) in pos.items())
    ancho = max(corrido[n][0] + cajas[n][0] / 2.0 for n in corrido) + MARGEN
    alto = max(corrido[n][1] + cajas[n][1] / 2.0 for n in corrido) + MARGEN
    return corrido, int(round(ancho)), int(round(alto))


# ── Markdown, el subconjunto que las fichas usan ─────────────────────────────────
#
# No es un renderer de markdown: es el de ESTA ficha, cuya forma garantiza el check
# dev-codebase-forma -cuatro titulos fijos, listas, negrita, codigo y enlaces-. Traer
# una libreria para esto seria un requisito nuevo por cuatro construcciones.

CODIGO_SPAN = re.compile(r"`([^`\n]*)`")
NEGRITA = re.compile(r"\*\*([^*]+)\*\*")
ENLACE_MD = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
ITEM = re.compile(r"^[-*]\s+(.*)$")
SUBTITULO = re.compile(r"^##+\s+(.*)$")


def _escapar(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def _en_linea(texto, fichas_conocidas):
    """Escapa primero y recien despues arma las etiquetas: al reves, un `<` de la ficha
    se comeria el marcado propio. El codigo se guarda aparte para que un `**` adentro de
    comillas invertidas no se vuelva negrita."""
    guardados = []

    def guardar(m):
        guardados.append(_escapar(m.group(1)))
        return "\x00%d\x00" % (len(guardados) - 1)

    texto = CODIGO_SPAN.sub(guardar, texto)
    texto = _escapar(texto)

    def enlace(m):
        etiqueta, destino = m.group(1), m.group(2)
        if destino in fichas_conocidas:
            # Un enlace a una ficha hermana no navega: cambia el panel. Asi se recorre
            # el grafo leyendo, sin volver al dibujo en cada salto.
            return ('<a href="%s" class="a-ficha" data-ficha="%s">%s</a>'
                    % (_escapar(destino), _escapar(destino), etiqueta))
        return '<a href="%s">%s</a>' % (_escapar(destino), etiqueta)

    texto = ENLACE_MD.sub(enlace, texto)
    texto = NEGRITA.sub(r"<strong>\1</strong>", texto)

    for i, guardado in enumerate(guardados):
        texto = texto.replace("\x00%d\x00" % i, "<code>%s</code>" % guardado)
    return texto


def md_a_html(texto, fichas_conocidas):
    """El cuerpo de una ficha, sin su titulo de nivel 1."""
    partes = []
    lista = []
    parrafo = []
    cercado = []
    en_cercado = False

    def cerrar_lista():
        if lista:
            partes.append("<ul>%s</ul>" % "".join("<li>%s</li>" % x for x in lista))
            del lista[:]

    def cerrar_parrafo():
        if parrafo:
            partes.append("<p>%s</p>" % " ".join(parrafo))
            del parrafo[:]

    for linea in texto.split("\n"):
        if linea.strip().startswith("```"):
            if en_cercado:
                partes.append("<pre>%s</pre>" % _escapar("\n".join(cercado)))
                del cercado[:]
            else:
                cerrar_lista()
                cerrar_parrafo()
            en_cercado = not en_cercado
            continue
        if en_cercado:
            cercado.append(linea)
            continue

        if linea.startswith("# "):
            continue
        m = SUBTITULO.match(linea)
        if m:
            cerrar_lista()
            cerrar_parrafo()
            partes.append("<h3>%s</h3>" % _en_linea(m.group(1), fichas_conocidas))
            continue

        m = ITEM.match(linea)
        if m:
            cerrar_parrafo()
            lista.append(_en_linea(m.group(1), fichas_conocidas))
            continue

        if not linea.strip():
            cerrar_lista()
            cerrar_parrafo()
            continue

        if lista:
            # Una linea indentada despues de un item lo continua. Cortarla en un
            # parrafo aparte parte una oracion al medio.
            lista[-1] += " " + _en_linea(linea.strip(), fichas_conocidas)
        else:
            parrafo.append(_en_linea(linea.strip(), fichas_conocidas))

    if en_cercado and cercado:
        partes.append("<pre>%s</pre>" % _escapar("\n".join(cercado)))
    cerrar_lista()
    cerrar_parrafo()
    return "\n".join(partes)


# ── Dibujar ──────────────────────────────────────────────────────────────────────

def _caja(titulo):
    """Ancho y alto del rectangulo. El ancho se estima por caracter: no hay forma de
    medir texto sin un motor de fuentes, y una estimacion generosa es preferible a un
    rectangulo que corta el nombre."""
    ancho = 26 + int(round(7.6 * len(titulo)))
    return max(96, ancho), 38


def _borde(cx, cy, ancho, alto, hacia_x, hacia_y):
    """Donde la recta que va del centro de la caja hacia (hacia_x, hacia_y) cruza el
    borde. Es lo que hace que la flecha termine tocando la caja y no en su centro."""
    dx, dy = hacia_x - cx, hacia_y - cy
    if dx == 0 and dy == 0:
        return cx, cy
    mx = (ancho / 2.0) / abs(dx) if dx else float("inf")
    my = (alto / 2.0) / abs(dy) if dy else float("inf")
    escala = mx if mx < my else my
    return cx + dx * escala, cy + dy * escala


def dibujar(titulos, cajas, nodos, aristas, pos, huerfanas):
    partes = []
    for origen, destino in aristas:
        ox, oy = pos[origen]
        dx, dy = pos[destino]
        aw, ah = cajas[origen]
        bw, bh = cajas[destino]
        x1, y1 = _borde(ox, oy, aw, ah, dx, dy)
        x2, y2 = _borde(dx, dy, bw, bh, ox, oy)
        partes.append(
            '  <line class="arista" data-de="%s" data-a="%s" '
            'x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" marker-end="url(#punta)">'
            '<title>%s → %s</title></line>'
            % (_escapar(origen), _escapar(destino), x1, y1, x2, y2,
               _escapar(titulos[origen]), _escapar(titulos[destino])))

    for nombre in nodos:
        cx, cy = pos[nombre]
        ancho, alto = cajas[nombre]
        clase = "nodo huerfano" if nombre in huerfanas else "nodo"
        salen = sum(1 for o, _d in aristas if o == nombre)
        entran = sum(1 for _o, d in aristas if d == nombre)
        # El nodo va adentro de un <a>: si el script no corre -o alguien lo abre con
        # JavaScript apagado- el clic igual lleva a la ficha. El script lo intercepta
        # para abrir el panel, que es mejor, pero no es la unica puerta.
        partes.append(
            '  <a href="%s" class="ir">\n'
            '    <g class="%s" data-id="%s" data-cx="%d" data-cy="%d" data-w="%d" '
            'data-h="%d" transform="translate(%d,%d)">\n'
            '      <title>%s — %d que la enlazan, %d que enlaza</title>\n'
            '      <rect x="%d" y="%d" width="%d" height="%d" rx="8"/>\n'
            '      <text x="0" y="5">%s</text>\n'
            '    </g>\n'
            '  </a>'
            % (_escapar(nombre), clase, _escapar(nombre), cx, cy, ancho, alto, cx, cy,
               _escapar(titulos[nombre]), entran, salen,
               -(ancho // 2), -(alto // 2), ancho, alto,
               _escapar(titulos[nombre])))

    return "\n".join(partes)


def armar_panel(fichas, nodos, huerfanas):
    """Una ficha por article, oculto. El texto va embebido y no en un JSON adentro del
    script: asi no hay una segunda capa de escapado que romper, y lo que se muestra es
    HTML comun."""
    conocidas = set(n for n, _t, _x in fichas)
    articulos = []
    for nombre, titulo, texto in fichas:
        if nombre not in nodos:
            continue
        marca = ('<p class="huerfana">Ninguna otra ficha la enlaza.</p>'
                 if nombre in huerfanas else "")
        articulos.append(
            '<article class="ficha" data-ficha="%s" hidden>\n'
            '  <h2>%s</h2>\n  %s\n%s\n'
            '  <p class="archivo"><a href="%s">Abrir %s</a></p>\n'
            '</article>'
            % (_escapar(nombre), _escapar(titulo), marca,
               md_a_html(texto, conocidas), _escapar(nombre), _escapar(nombre)))
    return "\n".join(articulos)


PAGINA = """<!doctype html>
<html lang="es">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mapa del código — %(titulo)s</title>
<style>
:root{
  --papel:#F0F1EF; --sup:#FFFFFF; --tinta:#141A19; --apagado:#5F6D69;
  --linea:#A9B4B0; --acento:#0D6E62; --acento-suave:#DCEBE8; --alerta:#9A5B1F;
}
@media (prefers-color-scheme: dark){
  :root{
    --papel:#121716; --sup:#1B2321; --tinta:#E8EDEB; --apagado:#9AA8A4;
    --linea:#4A5754; --acento:#5FC2B2; --acento-suave:#1E3A36; --alerta:#D89B5A;
  }
}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--papel);color:var(--tinta);
     font-family:"Segoe UI",system-ui,-apple-system,sans-serif;line-height:1.5}
header{max-width:1100px;margin:0 auto 12px}
h1{font-size:20px;margin:0 0 4px}
p.resumen{margin:0;color:var(--apagado);font-size:14px}
p.nota{margin:8px 0 0;color:var(--apagado);font-size:13px}
.barra{max-width:1100px;margin:0 auto 8px;display:flex;gap:10px;align-items:center;
       flex-wrap:wrap;font-size:13px;color:var(--apagado)}
button{font:inherit;font-size:13px;padding:5px 12px;border-radius:7px;cursor:pointer;
       border:1px solid var(--linea);background:var(--sup);color:var(--tinta)}
button:hover{border-color:var(--acento)}
.lienzo{max-width:1100px;margin:0 auto;background:var(--sup);border:1px solid var(--linea);
        border-radius:12px;overflow:hidden}
svg{display:block;width:100%%;height:auto;touch-action:pan-y}
svg.agarrando{cursor:grabbing}
.arista{stroke:var(--linea);stroke-width:1.6}
.nodo rect{fill:var(--acento-suave);stroke:var(--acento);stroke-width:1.6}
.nodo text{fill:var(--tinta);font-size:13px;font-weight:600;text-anchor:middle;
           font-family:"Consolas","IBM Plex Mono",ui-monospace,monospace}
.huerfano rect{fill:none;stroke:var(--alerta);stroke-dasharray:5 4}
a.ir{cursor:pointer}
a.ir:hover rect{stroke-width:2.6}
.nodo.activo rect{stroke-width:2.6;fill:var(--acento)}
.nodo.activo text{fill:var(--sup)}
.leyenda{max-width:1100px;margin:12px auto 0;display:flex;gap:20px;flex-wrap:wrap;
         font-size:13px;color:var(--apagado)}
.leyenda span{display:flex;align-items:center;gap:7px}
.muestra{width:22px;height:13px;border-radius:3px;border:1.6px solid var(--acento);
         background:var(--acento-suave)}
.muestra.h{background:none;border-color:var(--alerta);border-style:dashed}

#panel{position:fixed;top:0;right:0;width:min(460px,92vw);height:100%%;overflow-y:auto;
       background:var(--sup);border-left:1px solid var(--linea);padding:20px 24px 40px;
       transform:translateX(100%%);transition:transform .18s ease}
#panel.abierto{transform:none;box-shadow:-12px 0 30px rgba(0,0,0,.13)}
#panel h2{font-size:17px;margin:0 0 12px;
          font-family:"Consolas","IBM Plex Mono",ui-monospace,monospace}
#panel h3{font-size:13px;margin:18px 0 6px;text-transform:uppercase;
          letter-spacing:.06em;color:var(--apagado)}
#panel p,#panel li{font-size:14px}
#panel ul{padding-left:20px;margin:6px 0}
#panel li{margin-bottom:6px}
#panel code{font-size:12.5px;background:var(--acento-suave);padding:1px 5px;
            border-radius:4px}
#panel pre{background:var(--papel);border:1px solid var(--linea);border-radius:8px;
           padding:10px;overflow-x:auto;font-size:12.5px}
#panel a{color:var(--acento)}
#panel .huerfana{color:var(--alerta);font-weight:600;font-size:13px;margin:0 0 4px}
#panel .archivo{margin-top:22px;padding-top:12px;border-top:1px solid var(--linea);
                font-size:13px}
#cerrar{position:absolute;top:14px;right:16px}
</style>

<header>
  <h1>Mapa del código — %(titulo)s</h1>
  <p class="resumen">%(nodos)d fichas · %(aristas)d dependencias enlazadas%(huerfanas_txt)s</p>
  <p class="nota">Cada caja es una ficha del índice; cada flecha, un enlace de una ficha
  a otra. El mapa dibuja lo que las fichas dicen: una dependencia que la ficha no enlaza
  no aparece acá. Lo regenera <code>mapa-codigo.py</code> en cada recorrido.</p>
</header>

<div class="barra">
  <button id="acercar" type="button" aria-label="Acercar">+</button>
  <button id="alejar" type="button" aria-label="Alejar">&minus;</button>
  <button id="reencuadrar" type="button">Reencuadrar</button>
  <span>Ctrl + rueda para acercar · arrastrar el fondo para mover · clic en una ficha para leerla</span>
</div>

<div class="lienzo">
<svg id="grafo" viewBox="0 0 %(ancho)d %(alto)d" data-vista="0 0 %(ancho)d %(alto)d"
     role="img" aria-label="Grafo de dependencias entre las fichas del código">
  <defs>
    <marker id="punta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--linea)"/>
    </marker>
  </defs>
%(cuerpo)s
</svg>
</div>

<div class="leyenda">
  <span><i class="muestra"></i> ficha que alguien enlaza</span>
  <span><i class="muestra h"></i> nadie la enlaza todavía</span>
</div>

<aside id="panel" aria-live="polite">
  <button id="cerrar" type="button">Cerrar</button>
%(fichas)s
</aside>

<script>
(function () {
  "use strict";
  var svg = document.getElementById("grafo");
  var panel = document.getElementById("panel");
  if (!svg || !panel) { return; }

  // ── El estado, que es poco: la vista y las posiciones de los nodos ──
  var vistaInicial = svg.getAttribute("data-vista").split(" ").map(Number);
  var vista = vistaInicial.slice();
  var nodos = {};
  var inicial = {};

  Array.prototype.forEach.call(svg.querySelectorAll("g.nodo"), function (g) {
    var id = g.getAttribute("data-id");
    nodos[id] = {
      g: g,
      x: Number(g.getAttribute("data-cx")),
      y: Number(g.getAttribute("data-cy")),
      w: Number(g.getAttribute("data-w")),
      h: Number(g.getAttribute("data-h"))
    };
    inicial[id] = { x: nodos[id].x, y: nodos[id].y };
  });

  var aristas = Array.prototype.slice.call(svg.querySelectorAll("line.arista"));

  function aplicarVista() {
    svg.setAttribute("viewBox", vista.join(" "));
  }

  // El mismo recorte que hace el generador en Python: la flecha termina tocando la
  // caja, no en su centro. Si las dos formulas se separan, la punta queda flotando.
  function borde(a, hx, hy) {
    var dx = hx - a.x, dy = hy - a.y;
    if (dx === 0 && dy === 0) { return [a.x, a.y]; }
    var mx = dx ? (a.w / 2) / Math.abs(dx) : Infinity;
    var my = dy ? (a.h / 2) / Math.abs(dy) : Infinity;
    var e = Math.min(mx, my);
    return [a.x + dx * e, a.y + dy * e];
  }

  function redibujarAristas(id) {
    aristas.forEach(function (l) {
      var de = l.getAttribute("data-de"), a = l.getAttribute("data-a");
      if (id && de !== id && a !== id) { return; }
      var n1 = nodos[de], n2 = nodos[a];
      if (!n1 || !n2) { return; }
      var p1 = borde(n1, n2.x, n2.y);
      var p2 = borde(n2, n1.x, n1.y);
      l.setAttribute("x1", p1[0]); l.setAttribute("y1", p1[1]);
      l.setAttribute("x2", p2[0]); l.setAttribute("y2", p2[1]);
    });
  }

  function moverNodo(id, x, y) {
    var n = nodos[id];
    n.x = x; n.y = y;
    n.g.setAttribute("transform", "translate(" + x + "," + y + ")");
    redibujarAristas(id);
  }

  // ── Coordenadas: de la pantalla al lienzo ──
  function aLienzo(ev) {
    var caja = svg.getBoundingClientRect();
    return {
      x: vista[0] + (ev.clientX - caja.left) / caja.width * vista[2],
      y: vista[1] + (ev.clientY - caja.top) / caja.height * vista[3]
    };
  }

  function nodoDe(ev) {
    return ev.target && ev.target.closest ? ev.target.closest("g.nodo") : null;
  }

  // ── Acercar ──
  //
  // La rueda SOLA no hace zoom: desplaza la pagina, como en cualquier otro lado. Atrapar
  // la rueda deja al lector encerrado en el mapa -pasa por encima y ya no puede seguir
  // bajando- y es lo primero que se siente al abrirlo. El zoom pide Ctrl, que es ademas
  // lo que manda el navegador cuando alguien pellizca en un trackpad, y hay dos botones
  // en la barra para el que no quiera atajos.
  function zoom(f, px, py) {
    var ancho = vista[2] * f;
    var limite = vistaInicial[2];
    if (ancho < limite / 8 || ancho > limite * 4) { return; }
    vista[0] = px - (px - vista[0]) * f;
    vista[1] = py - (py - vista[1]) * f;
    vista[2] = ancho;
    vista[3] = vista[3] * f;
    aplicarVista();
  }

  svg.addEventListener("wheel", function (ev) {
    if (!ev.ctrlKey && !ev.metaKey) { return; }
    ev.preventDefault();
    var p = aLienzo(ev);
    zoom(ev.deltaY < 0 ? 0.85 : 1.18, p.x, p.y);
  }, { passive: false });

  function zoomAlCentro(f) {
    zoom(f, vista[0] + vista[2] / 2, vista[1] + vista[3] / 2);
  }

  // ── Arrastrar: el fondo desplaza la vista, un nodo mueve el nodo ──
  //
  // Sin setPointerCapture, a proposito. Capturar el puntero en el <svg> hace que el
  // `click` posterior se despache al <svg> y no al nodo: `closest("g.nodo")` devuelve
  // null y el clic sobre una ficha no abre nada. Paso, y leyendo el codigo no se ve.
  // El seguimiento va en la ventana, que ademas es lo que permite arrastrar mas alla
  // del borde del dibujo sin perder el nodo.
  var arrastre = null;
  var ultimoMovio = false;

  svg.addEventListener("pointerdown", function (ev) {
    if (ev.button !== 0) { return; }
    var g = nodoDe(ev);
    var p = aLienzo(ev);
    var id = g ? g.getAttribute("data-id") : null;
    arrastre = {
      id: id,
      desdeX: p.x, desdeY: p.y,
      vista0: vista[0], vista1: vista[1],
      nodoX: id ? nodos[id].x : 0,
      nodoY: id ? nodos[id].y : 0,
      movio: false
    };
    if (!g) { svg.classList.add("agarrando"); }
  });

  window.addEventListener("pointermove", function (ev) {
    if (!arrastre) { return; }
    // Red de seguridad: si el boton ya no esta apretado, el arrastre termino aunque el
    // pointerup se haya perdido -fuera de la ventana, en otra pestana, en un menu-. Sin
    // esto el mapa se sigue moviendo con solo pasar el mouse y no hay forma de salir.
    if (ev.buttons === 0) { terminar(); return; }
    var p = aLienzo(ev);
    var dx = p.x - arrastre.desdeX, dy = p.y - arrastre.desdeY;
    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) { arrastre.movio = true; }
    if (arrastre.id) {
      moverNodo(arrastre.id, Math.round(arrastre.nodoX + dx),
                Math.round(arrastre.nodoY + dy));
    } else {
      vista[0] = arrastre.vista0 - dx;
      vista[1] = arrastre.vista1 - dy;
      aplicarVista();
    }
  });

  function terminar() {
    ultimoMovio = !!(arrastre && arrastre.movio);
    arrastre = null;
    svg.classList.remove("agarrando");
  }
  window.addEventListener("pointerup", terminar);
  window.addEventListener("pointercancel", terminar);
  window.addEventListener("blur", terminar);

  // ── El panel ──
  function abrir(id) {
    var visto = false;
    Array.prototype.forEach.call(panel.querySelectorAll("article.ficha"), function (a) {
      var suya = a.getAttribute("data-ficha") === id;
      a.hidden = !suya;
      if (suya) { visto = true; }
    });
    if (!visto) { return; }
    Array.prototype.forEach.call(svg.querySelectorAll("g.nodo"), function (g) {
      if (g.getAttribute("data-id") === id) {
        g.classList.add("activo");
      } else {
        g.classList.remove("activo");
      }
    });
    panel.classList.add("abierto");
    panel.scrollTop = 0;
  }

  function cerrar() {
    panel.classList.remove("abierto");
    Array.prototype.forEach.call(svg.querySelectorAll("g.nodo"), function (g) {
      g.classList.remove("activo");
    });
  }

  // El <a> del nodo se intercepta: sin script llevaria al .md, que el navegador baja
  // o muestra crudo. Con script abre el panel, que es la version que se quiere.
  svg.addEventListener("click", function (ev) {
    var g = nodoDe(ev);
    if (!g) { return; }
    ev.preventDefault();
    if (ultimoMovio) { ultimoMovio = false; return; }
    abrir(g.getAttribute("data-id"));
  });

  // Un enlace a otra ficha adentro del panel no navega: cambia de ficha.
  panel.addEventListener("click", function (ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest("a.a-ficha") : null;
    if (!a) { return; }
    ev.preventDefault();
    abrir(a.getAttribute("data-ficha"));
  });

  document.getElementById("cerrar").addEventListener("click", cerrar);
  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") { cerrar(); }
  });

  document.getElementById("acercar").addEventListener("click", function () {
    zoomAlCentro(0.8);
  });
  document.getElementById("alejar").addEventListener("click", function () {
    zoomAlCentro(1.25);
  });

  document.getElementById("reencuadrar").addEventListener("click", function () {
    vista = vistaInicial.slice();
    aplicarVista();
    Object.keys(inicial).forEach(function (id) {
      moverNodo(id, inicial[id].x, inicial[id].y);
    });
  });
})();
</script>
</html>
"""


# ── Generar ──────────────────────────────────────────────────────────────────────

def generar(directorio):
    """Escribe `mapa.html` en el directorio y devuelve el resumen. Si no hay fichas no
    escribe nada: un mapa vacio es la promesa de que habia algo que mirar."""
    directorio = os.path.abspath(directorio)
    fichas = leer_fichas(directorio)
    if not fichas:
        return {"escrito": False,
                "motivo": "no hay fichas en %s: el recorrido no paso por aca todavia"
                          % directorio,
                "nodos": 0, "aristas": 0, "huerfanas": []}

    nodos, aristas = armar_grafo(fichas)
    titulos = dict((n, t) for n, t, _x in fichas)
    cajas = dict((n, _caja(titulos[n])) for n in nodos)
    pos, ancho, alto = encuadrar(acomodar(nodos, aristas, cajas), cajas)
    con_entrada = set(d for _o, d in aristas)
    huerfanas = sorted(n for n in nodos if n not in con_entrada)

    if huerfanas:
        huerfanas_txt = " · %d que nadie enlaza" % len(huerfanas)
    else:
        huerfanas_txt = ""

    pagina = PAGINA % {
        "titulo": os.path.basename(directorio),
        "nodos": len(nodos), "aristas": len(aristas),
        "huerfanas_txt": huerfanas_txt,
        "ancho": ancho, "alto": alto,
        "cuerpo": dibujar(titulos, cajas, nodos, aristas, pos, set(huerfanas)),
        "fichas": armar_panel(fichas, set(nodos), set(huerfanas)),
    }

    salida = os.path.join(directorio, "mapa.html")
    with io.open(salida, "w", encoding="utf-8", newline="\n") as f:
        f.write(pagina)

    return {"escrito": True, "salida": salida, "nodos": len(nodos),
            "aristas": len(aristas), "huerfanas": huerfanas}


def main():
    ap = argparse.ArgumentParser(
        description="Dibuja el grafo de las fichas del indice del codigo.")
    ap.add_argument("directorio", help="el directorio de las fichas, normalmente docs/codebase")
    args = ap.parse_args()

    resumen = generar(args.directorio)
    sys.stdout.write(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
