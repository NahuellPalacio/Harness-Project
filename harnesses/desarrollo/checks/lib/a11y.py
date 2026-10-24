"""Motor del analisis estatico de accesibilidad: HTML, plantillas y JSX/TSX.

Lo usan dos cosas. El check liviano (dev-accesibilidad-html.py) corre tras cada escritura y solo
dice lo inequivoco. La revision completa (skills/dev-accessibility/scripts/review.py) corre cuando
el alcance de la tarea lo pide y dice todo, incluida la cobertura: que se miro y que no se pudo.

Tres ideas ordenan el modulo:

  1. Un hallazgo tiene un TIPO, y el tipo dice cuanto se puede confiar en el.
       fail            incumple un criterio de WCAG 2.2 por evidencia estatica
       defect          marcado roto, con efecto probable en accesibilidad, sin ser por si solo un fallo
       probable        heuristica: hay que mirarlo
       recommendation  buena practica; WCAG 2.2 no la exige (un solo <h1>, por ejemplo)
       undeterminable  el archivo no alcanza para decidir (una etiqueta puede estar en otra plantilla)
     El check liviano emite solo fail y defect.

  2. Lo que el motor no puede interpretar se dice, no se adivina. Un componente propio
     (<TextField />), un {...props}, un archivo que no se pudo leer: quedan como no analizados.

  3. Un analisis estatico limpio no acredita conformidad. Este modulo no devuelve nunca «aprobado».

Python 3.9. Solo biblioteca estandar. Los recorridos son iterativos: un HTML con diez mil <li>
sin cerrar no puede agotar la recursion.
"""
import bisect
import os
import re


class _Perezosa(object):
    """Una expresion regular que se compila al usarla por primera vez.

    El cargador de checks importa este modulo en cada escritura, sea o no un archivo que el motor
    lea; compilar de entrada una docena de expresiones es latencia que se paga en cada turno.
    """

    def __init__(self, patron, banderas=0):
        self._patron = patron
        self._banderas = banderas
        self._compilada = None

    def __getattr__(self, nombre):
        if self._compilada is None:
            self._compilada = re.compile(self._patron, self._banderas)
        return getattr(self._compilada, nombre)


SENT = chr(0xE000)        # marca de «aca habia una expresion de plantilla o de JSX»

VOID = frozenset(("area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
                  "param", "source", "track", "wbr"))

# Niveles de los criterios que el motor cita. El test los contrasta con wcag22-criteria.json.
NIVELES = {
    "1.1.1": "A", "1.2.2": "A", "1.3.1": "A", "1.3.5": "AA", "1.4.2": "A", "1.4.4": "AA",
    "2.1.1": "A", "2.2.1": "A", "2.2.2": "A", "2.4.2": "A", "2.4.3": "A", "2.4.4": "A",
    "2.4.6": "AA", "3.1.1": "A", "3.3.2": "A", "3.3.8": "AA", "4.1.2": "A",
}

# regla -> (criterios, tipo, origen, liviana, tecnica)
# tecnica: un id que existe en el testigo del W3C y esta asociado a esos criterios, o None.
REGLAS = {
    "html-missing-lang":         (("3.1.1",), "fail", "wcag", True, "H57"),
    "html-invalid-lang":         (("3.1.1",), "fail", "wcag", True, "H57"),
    "document-missing-title":    (("2.4.2",), "fail", "wcag", True, "F25"),
    "img-missing-alt":           (("1.1.1",), "fail", "wcag", True, "F65"),
    "input-image-missing-alt":   (("1.1.1",), "fail", "wcag", True, "F65"),
    "area-missing-alt":          (("1.1.1",), "fail", "wcag", True, "F65"),
    "control-no-accessible-name": (("4.1.2",), "fail", "wcag", True, "F68"),
    "control-label-missing-in-file": (("4.1.2",), "defect", "wcag", True, "H44"),
    "button-no-accessible-name": (("4.1.2",), "fail", "wcag", True, "F68"),
    "link-no-accessible-name":   (("2.4.4", "4.1.2"), "fail", "wcag", True, None),
    "iframe-missing-title":      (("4.1.2",), "fail", "wcag", True, "H64"),
    "aria-reference-broken":     (("4.1.2",), "defect", "wcag", True, "ARIA16"),
    "aria-reference-no-text":    (("4.1.2",), "defect", "wcag", True, "ARIA16"),
    "label-for-broken":          (("1.3.1",), "defect", "wcag", True, "H44"),
    "duplicate-id-referenced":   (("1.3.1",), "defect", "wcag", True, None),
    "viewport-blocks-zoom":      (("1.4.4",), "fail", "wcag", False, None),
    "meta-refresh-delay":        (("2.2.1",), "fail", "wcag", False, "F40"),
    "autocomplete-invalid-token": (("1.3.5",), "fail", "wcag", False, "F107"),
    "password-blocks-paste":     (("3.3.8",), "fail", "wcag", False, "F109"),
    "marquee-or-blink":          (("2.2.2",), "fail", "wcag", False, "F16"),
    "aria-hidden-focusable":     (("4.1.2",), "defect", "wcag", False, None),
    "clickable-not-keyboard":    (("2.1.1",), "probable", "wcag", False, "F54"),
    "autocomplete-missing":      (("1.3.5",), "probable", "wcag", False, "H98"),
    "password-autocomplete-off": (("3.3.8",), "probable", "wcag", False, "H100"),
    "tabindex-positive":         (("2.4.3",), "probable", "wcag", False, "F44"),
    "table-without-headers":     (("1.3.1",), "probable", "wcag", False, "F91"),
    "heading-empty":             (("2.4.6",), "probable", "wcag", False, "G130"),
    "media-autoplay":            (("1.4.2",), "probable", "wcag", False, "F93"),
    "video-no-captions":         (("1.2.2",), "probable", "wcag", False, "H95"),
    "img-alt-filename":          (("1.1.1",), "probable", "wcag", False, "F30"),
    "link-generic-text":         (("2.4.4",), "probable", "obelisco", False, None),
    "control-placeholder-only":  (("3.3.2",), "probable", "obelisco", False, None),
    "control-name-undeterminable": (("4.1.2",), "undeterminable", "wcag", False, None),
    "heading-no-h1":             ((), "recommendation", "harness", False, None),
    "heading-multiple-h1":       ((), "recommendation", "harness", False, None),
    "heading-skipped-level":     ((), "recommendation", "harness", False, None),
    "landmark-missing-main":     ((), "recommendation", "harness", False, None),
    "duplicate-id":              ((), "recommendation", "harness", False, None),
}
ORDEN_TIPO = {"fail": 0, "defect": 1, "probable": 2, "undeterminable": 3, "recommendation": 4}

# La correccion propuesta de cada regla, para el registro de evidencia.
CORRECCION = {
    "html-missing-lang": "Agregar lang=\"es\" (o el idioma real) a <html>.",
    "html-invalid-lang": "Usar un código de idioma BCP 47 válido: \"es\", \"es-AR\".",
    "document-missing-title": "Agregar un <title> que describa la página.",
    "img-missing-alt": "Agregar alt con el equivalente de la imagen, o alt=\"\" si es decorativa.",
    "input-image-missing-alt": "Agregar alt con la acción que dispara el botón de imagen.",
    "area-missing-alt": "Agregar alt a cada <area> del mapa de imagen.",
    "control-no-accessible-name": "Asociar una <label for> con texto, envolver el control en una <label>, o agregar aria-label / aria-labelledby que resuelva a texto.",
    "control-label-missing-in-file": "Agregar la <label for> con el id del control; si ya existe en otro archivo, confirmarlo.",
    "button-no-accessible-name": "Agregar texto al botón o un aria-label con la acción.",
    "link-no-accessible-name": "Agregar texto al enlace o un aria-label; una imagen dentro del enlace necesita alt.",
    "iframe-missing-title": "Agregar title al <iframe>.",
    "aria-reference-broken": "Corregir el id al que apunta la referencia ARIA, o quitarla.",
    "aria-reference-no-text": "Dar texto al elemento referenciado, o apuntar a otro.",
    "label-for-broken": "Hacer que for coincida con el id del control, o quitar la <label>.",
    "duplicate-id-referenced": "Dejar un solo elemento con ese id.",
    "viewport-blocks-zoom": "Quitar user-scalable=no y maximum-scale del meta viewport.",
    "meta-refresh-delay": "Quitar el meta refresh; si hay que redirigir, hacerlo del lado del servidor.",
    "autocomplete-invalid-token": "Usar un token válido de autocomplete (HTML, sección 1.3.5).",
    "password-blocks-paste": "Quitar el bloqueo de pegado del campo de contraseña.",
    "marquee-or-blink": "Reemplazar el elemento por contenido estático o con un control para pausarlo.",
    "aria-hidden-focusable": "Quitar aria-hidden, o sacar el foco de lo que contiene (tabindex=\"-1\", inert).",
    "clickable-not-keyboard": "Usar <button> o <a href>; o agregar role, tabindex=\"0\" y manejo de Enter y Espacio.",
    "autocomplete-missing": "Agregar el token de autocomplete que corresponde al dato.",
    "password-autocomplete-off": "Usar autocomplete=\"current-password\" o \"new-password\".",
    "tabindex-positive": "Usar tabindex=\"0\" o \"-1\" y ordenar el DOM como se lee.",
    "table-without-headers": "Marcar los encabezados con <th scope>; si es de maquetación, role=\"presentation\".",
    "heading-empty": "Dar texto al encabezado o quitarlo.",
    "media-autoplay": "Quitar autoplay, o iniciar sin sonido (muted) con controles.",
    "video-no-captions": "Agregar <track kind=\"captions\"> o confirmar que el reproductor trae subtítulos.",
    "img-alt-filename": "Escribir un alt que describa la imagen, no su archivo.",
    "link-generic-text": "Escribir un texto de enlace que diga adónde va.",
    "control-placeholder-only": "Agregar una <label> visible: el placeholder no la sustituye.",
    "control-name-undeterminable": "Confirmar en el archivo que contiene la etiqueta, o revisar la página completa.",
    "heading-no-h1": "Recomendación: un <h1> con el título de la página.",
    "heading-multiple-h1": "Recomendación: un solo <h1>.",
    "heading-skipped-level": "Recomendación: no saltear niveles de encabezado.",
    "landmark-missing-main": "Recomendación: envolver el contenido principal en <main>.",
    "duplicate-id": "Recomendación: ids únicos.",
}
MAX_POR_ARCHIVO = 5       # avisos del check liviano por archivo; el presupuesto global es de ocho

# -- formatos ---------------------------------------------------------------------------------------

_EXT_JSX = (".jsx", ".tsx")
_EXT_HTML = (".html", ".htm", ".xhtml")
_EXT_PLANTILLA = (".blade.php", ".component.html", ".njk", ".hbs", ".handlebars", ".twig", ".ejs",
                  ".erb", ".jinja", ".jinja2", ".j2")


def formato_de(nombre):
    """'jsx', 'template', 'html' o None si el motor no sabe leer ese archivo."""
    n = nombre.lower()
    if n.endswith(_EXT_JSX):
        return "jsx"
    if n.endswith(_EXT_PLANTILLA):
        return "template"
    if n.endswith(_EXT_HTML):
        return "html"
    return None


# -- el arbol ---------------------------------------------------------------------------------------

class Attr(object):
    __slots__ = ("valor", "dinamico")

    def __init__(self, valor, dinamico=False):
        self.valor = valor
        self.dinamico = dinamico


class Nodo(object):
    __slots__ = ("tag", "attrs", "padre", "hijos", "texto", "linea", "spread", "expr_hijos", "componente")

    def __init__(self, tag, padre, linea):
        self.tag = tag
        self.attrs = {}
        self.padre = padre
        self.hijos = []
        self.texto = []
        self.linea = linea
        self.spread = False
        self.expr_hijos = False
        self.componente = False


def recorrer(raiz):
    """Todos los nodos, en orden de documento, sin recursion."""
    pila = [raiz]
    while pila:
        n = pila.pop()
        yield n
        pila.extend(reversed(n.hijos))


def _estatico(n, nombre):
    a = n.attrs.get(nombre)
    if a is None or a.dinamico or a.valor is None:
        return None
    return a.valor


def _util(valor):
    return isinstance(valor, str) and valor.replace(SENT, "x").strip() != ""


# -- plantillas -------------------------------------------------------------------------------------

_BLADE = ("if", "elseif", "else", "endif", "foreach", "endforeach", "forelse", "endforelse", "for", "endfor",
          "while", "endwhile", "unless", "endunless", "isset", "endisset", "empty", "endempty", "auth", "endauth",
          "guest", "endguest", "can", "endcan", "cannot", "section", "endsection", "show", "yield", "include",
          "includeif", "includewhen", "extends", "push", "endpush", "prepend", "endprepend", "stack", "php",
          "endphp", "switch", "case", "break", "default", "endswitch", "component", "endcomponent", "slot",
          "endslot", "lang", "json", "csrf", "method", "error", "enderror", "production", "endproduction",
          "env", "endenv", "once", "endonce", "class", "checked", "selected", "disabled", "readonly", "required",
          "props", "aware", "vite", "livewire", "lang", "choice")
_PLANTILLA = _Perezosa(
    r"\{\{--.{0,4000}?--\}\}|\{!!.{0,4000}?!!\}|\{\{.{0,4000}?\}\}|\{%.{0,4000}?%\}|\{#.{0,4000}?#\}|<\?(?:php|=).{0,8000}?\?>|<%.{0,4000}?%>"
    r"|@(?:" + "|".join(_BLADE) + r")\b(?:[ \t]*\((?:[^()\n]|\([^()\n]*\))*\))?",
    re.DOTALL)


_INCLUSIONES = _Perezosa(
    r"@(?:include|includeIf|includeWhen|includeFirst|component|livewire|extends|yield|stack|slot)\b|<x-[\w:.-]+"
    r"|\{%-?\s*(?:include|extends|block|import|from|render)\b|\{\{>|<ng-content|<router-outlet|<%[-=]?\s*include",
    re.IGNORECASE)


def tiene_inclusiones(texto):
    """Verdadero si el archivo arma su contenido con partes de otros archivos."""
    return bool(_INCLUSIONES.search(texto))


def _enmascarar(texto):
    """Cada construccion de plantilla pasa a ser SENT, conservando los saltos de linea."""
    def sustituir(m):
        return SENT + "\n" * m.group(0).count("\n")
    return _PLANTILLA.sub(sustituir, texto)


_BINDING = _Perezosa(r"^(?:\[attr\.(.+)\]|\[(.+)\]|:([\w:.-]+)|v-bind:(.+)|x-bind:(.+)|bind-(.+))$")
_EVENTO = _Perezosa(r"^(?:\((\w+)\)|@(\w+)|v-on:(\w+)|x-on:(\w+)|on-(\w+))$")


def _atributos(pares):
    d = {}
    for nombre, valor in pares:
        if SENT in nombre or not nombre:
            continue
        dinamico = valor is not None and SENT in valor
        m = _EVENTO.match(nombre)
        if m:
            nombre = "on" + [g for g in m.groups() if g][0].lower()
            dinamico = True
        else:
            m = _BINDING.match(nombre)
            if m:
                nombre = [g for g in m.groups() if g][0]
                dinamico = True
        d[nombre] = Attr(valor if valor is not None else "", dinamico)
    return d


_CONSTRUCTOR = []


def _constructor():
    """La clase que arma el arbol, creada la primera vez que hace falta.

    Importar html.parser en cada escritura de cada archivo, aunque no sea HTML, es latencia que se
    paga para nada: PostToolUse corre despues de todas, y el cargador de checks importa este modulo
    en cada una.
    """
    if not _CONSTRUCTOR:
        from html.parser import HTMLParser

        class Constructor(HTMLParser):
            def __init__(self, raiz):
                HTMLParser.__init__(self, convert_charrefs=True)
                self.raiz = raiz
                self.actual = raiz

            def _abrir(self, tag, attrs, autocerrado):
                n = Nodo(tag, self.actual, self.getpos()[0])
                n.attrs = _atributos(attrs)
                n.componente = "-" in tag and not tag.startswith("ng-")
                self.actual.hijos.append(n)
                if not autocerrado and tag not in VOID:
                    self.actual = n

            def handle_starttag(self, tag, attrs):
                self._abrir(tag, attrs, False)

            def handle_startendtag(self, tag, attrs):
                self._abrir(tag, attrs, True)

            def handle_endtag(self, tag):
                n = self.actual
                while n is not None and n.tag != tag:
                    n = n.padre
                if n is not None and n.padre is not None:
                    self.actual = n.padre

            def handle_data(self, data):
                self.actual.texto.append(data)

        _CONSTRUCTOR.append(Constructor)
    return _CONSTRUCTOR[0]


def _analizar_html(texto):
    raiz = Nodo("#raiz", None, 1)
    c = _constructor()(raiz)
    c.feed(_enmascarar(texto))
    c.close()
    return raiz


# -- JSX/TSX ----------------------------------------------------------------------------------------

class _ErrorJsx(Exception):
    pass


_NOMBRE_JSX = _Perezosa(r"[A-Za-z_$][\w$.:-]*")
_ATTR_JSX = _Perezosa(r"[A-Za-z_$][\w$:.-]*")
_TOKEN_CODIGO = _Perezosa(r"//|/\*|['\"`]|<|\{|\}|/")
_PALABRAS_ANTES_DE_JSX = frozenset(("return", "case", "default", "yield", "await", "else", "typeof", "in", "of", "do"))
_PALABRA_FINAL = _Perezosa(r"([A-Za-z_$][\w$]*)$")
_NOMBRES_ATTR_JSX = {
    "htmlfor": "for", "classname": "class", "tabindex": "tabindex", "autocomplete": "autocomplete",
    "onclick": "onclick", "readonly": "readonly", "maxlength": "maxlength", "colspan": "colspan",
    "rowspan": "rowspan", "crossorigin": "crossorigin", "autoplay": "autoplay", "contenteditable": "contenteditable",
    "accesskey": "accesskey", "datetime": "datetime", "enctype": "enctype", "srcset": "srcset",
}
MAX_PASOS_JSX = 4000000
MAX_PROFUNDIDAD_JSX = 60


class _Jsx(object):
    def __init__(self, texto):
        self.t = texto
        self.n = len(texto)
        self.pasos = 0
        self.errores = []        # (linea, motivo)
        self.saltos = [m.start() for m in re.finditer("\n", texto)]

    def linea(self, i):
        """La linea de un indice, por biseccion: contar saltos desde el principio en cada elemento
        seria cuadratico en un archivo con miles."""
        return bisect.bisect_left(self.saltos, i) + 1

    def paso(self):
        self.pasos += 1
        if self.pasos > MAX_PASOS_JSX:
            raise _ErrorJsx("archivo demasiado grande o complejo para el tokenizador de JSX")

    # --- codigo ordinario --------------------------------------------------------------
    def puede_empezar_jsx(self, i):
        t = self.t
        j = i - 1
        while j >= 0 and t[j] in " \t\r\n":
            j -= 1
        if j < 0:
            return True
        c = t[j]
        if c in "(,=:?&|{[;!":
            return True
        if c == ">" and j > 0 and t[j - 1] == "=":
            return True
        if c.isalnum() or c in "_$":
            m = _PALABRA_FINAL.search(t[max(0, j - 12):j + 1])
            return bool(m and m.group(1) in _PALABRAS_ANTES_DE_JSX)
        return False

    def escanear(self, i, padre, hasta_llave, prof):
        """Recorre codigo desde i. Si hasta_llave, devuelve el indice del `}` que cierra el contenedor."""
        t, n = self.t, self.n
        nivel = 0
        while True:
            self.paso()
            m = _TOKEN_CODIGO.search(t, i)
            if not m:
                if hasta_llave:
                    raise _ErrorJsx("llave sin cerrar")
                return n
            tok = m.group(0)
            i = m.start()
            if tok == "//":
                f = t.find("\n", i)
                i = n if f < 0 else f + 1
            elif tok == "/*":
                f = t.find("*/", i + 2)
                i = n if f < 0 else f + 2
            elif tok in ("'", '"'):
                i = self.saltar_cadena(i, tok)
            elif tok == "`":
                i = self.saltar_plantilla(i, prof)
            elif tok == "{":
                nivel += 1
                i += 1
            elif tok == "}":
                if hasta_llave and nivel == 0:
                    return i
                nivel = max(0, nivel - 1)
                i += 1
            elif tok == "/":
                i = self.saltar_regex(i)
            else:   # "<"
                nxt = t[i + 1:i + 2]
                if (nxt.isalpha() or nxt in ("_", "$", ">")) and self.puede_empezar_jsx(i):
                    try:
                        nodo, j = self.elemento(i, padre, prof + 1)
                        padre.hijos.append(nodo)
                        i = j
                        continue
                    except _ErrorJsx as e:
                        if "demasiado" in str(e):
                            raise
                        if str(e) != "generico":
                            self.errores.append((self.linea(i), str(e)))
                i += 1

    def saltar_cadena(self, i, q):
        t, n = self.t, self.n
        j = i + 1
        while j < n:
            c = t[j]
            if c == "\\":
                j += 2
                continue
            if c == q or c == "\n":
                return j + 1
            j += 1
        return n

    def saltar_plantilla(self, i, prof):
        t, n = self.t, self.n
        j = i + 1
        while j < n:
            self.paso()
            c = t[j]
            if c == "\\":
                j += 2
            elif c == "`":
                return j + 1
            elif c == "$" and t[j + 1:j + 2] == "{":
                aux = Nodo("#aux", None, 0)
                j = self.escanear(j + 2, aux, True, prof) + 1
            else:
                j += 1
        return n

    def saltar_regex(self, i):
        t, n = self.t, self.n
        j = i - 1
        while j >= 0 and t[j] in " \t":
            j -= 1
        if j >= 0 and t[j] not in "(,=:[!&|?{};\n" and not t[j:j + 1].isspace():
            return i + 1
        k, clase = i + 1, False
        while k < n and t[k] != "\n":
            c = t[k]
            if c == "\\":
                k += 2
                continue
            if c == "[":
                clase = True
            elif c == "]":
                clase = False
            elif c == "/" and not clase:
                return k + 1
            k += 1
        return i + 1

    # --- elementos -------------------------------------------------------------------------
    def elemento(self, i, padre, prof):
        if prof > MAX_PROFUNDIDAD_JSX:
            raise _ErrorJsx("JSX anidado a mas de %d niveles" % MAX_PROFUNDIDAD_JSX)
        t, n = self.t, self.n
        linea = self.linea(i)
        j = i + 1
        if t[j:j + 1] == ">":
            nodo = Nodo("#fragmento", padre, linea)
            return self.hijos(nodo, j + 1, "", prof)
        m = _NOMBRE_JSX.match(t, j)
        if not m:
            raise _ErrorJsx("no es un elemento JSX")
        nombre = m.group(0)
        nodo = Nodo(nombre, padre, linea)
        nodo.componente = nombre[0].isupper() or "." in nombre
        j = m.end()
        if t[j:j + 1] == "," or t.startswith(" extends ", j) or t.startswith("\textends ", j):
            raise _ErrorJsx("generico")
        while True:
            self.paso()
            while j < n and t[j] in " \t\r\n":
                j += 1
            if j >= n:
                raise _ErrorJsx("etiqueta <%s> sin cerrar" % nombre)
            c = t[j]
            if c == "/":
                if t[j + 1:j + 2] != ">":
                    raise _ErrorJsx("«/» inesperada en <%s>" % nombre)
                return nodo, j + 2
            if c == ">":
                return self.hijos(nodo, j + 1, nombre, prof)
            if c == "{":
                fin = self.escanear(j + 1, nodo, True, prof)
                cuerpo = t[j + 1:fin].strip()
                if cuerpo.startswith("..."):
                    nodo.spread = True
                elif cuerpo.startswith("/*") and cuerpo.endswith("*/"):
                    pass
                else:
                    raise _ErrorJsx("expresion suelta en los atributos de <%s>" % nombre)
                j = fin + 1
                continue
            m = _ATTR_JSX.match(t, j)
            if not m:
                raise _ErrorJsx("atributo no valido en <%s>" % nombre)
            anombre = m.group(0)
            j = m.end()
            k = j
            while k < n and t[k] in " \t\r\n":
                k += 1
            if t[k:k + 1] != "=":
                self.poner(nodo, anombre, "", False)
                continue
            k += 1
            while k < n and t[k] in " \t\r\n":
                k += 1
            if k >= n:
                raise _ErrorJsx("atributo sin valor en <%s>" % nombre)
            q = t[k]
            if q in ("'", '"'):
                f = t.find(q, k + 1)
                if f < 0:
                    raise _ErrorJsx("cadena sin cerrar en <%s>" % nombre)
                self.poner(nodo, anombre, t[k + 1:f], False)
                j = f + 1
            elif q == "{":
                fin = self.escanear(k + 1, nodo, True, prof)
                cuerpo = t[k + 1:fin].strip()
                literal = re.fullmatch(r"""(["'])([^"'`\\\n]*)\1|`([^`$\\\n]*)`""", cuerpo)
                if literal:
                    self.poner(nodo, anombre, literal.group(2) if literal.group(2) is not None else literal.group(3), False)
                else:
                    self.poner(nodo, anombre, None, True)
                j = fin + 1
            else:
                raise _ErrorJsx("valor de atributo no valido en <%s>" % nombre)

    def poner(self, nodo, nombre, valor, dinamico):
        base = _NOMBRES_ATTR_JSX.get(nombre.lower(), nombre if "-" in nombre or nombre.islower() else nombre.lower())
        nodo.attrs[base] = Attr(valor if valor is not None else "", dinamico)

    def hijos(self, nodo, j, nombre, prof):
        t, n = self.t, self.n
        buscar = re.compile(r"[<{]")
        while True:
            self.paso()
            m = buscar.search(t, j)
            if not m:
                raise _ErrorJsx("falta </%s>" % (nombre or ""))
            texto = t[j:m.start()]
            if texto.strip():
                nodo.texto.append(" ".join(texto.split()))
            j = m.start()
            if t[j] == "{":
                fin = self.escanear(j + 1, nodo, True, prof)
                cuerpo = t[j + 1:fin].strip()
                if cuerpo and not (cuerpo.startswith("/*") and cuerpo.endswith("*/")):
                    literal = re.fullmatch(r"""(["'])([^"'`\\\n]*)\1""", cuerpo)
                    if literal:
                        nodo.texto.append(literal.group(2))
                    else:
                        nodo.expr_hijos = True
                j = fin + 1
                continue
            if t[j + 1:j + 2] == "/":
                f = t.find(">", j)
                if f < 0:
                    raise _ErrorJsx("cierre sin >")
                if t[j + 2:f].strip() != nombre:
                    raise _ErrorJsx("</%s> no cierra <%s>" % (t[j + 2:f].strip(), nombre or ""))
                return nodo, f + 1
            hijo, j = self.elemento(j, nodo, prof + 1)
            nodo.hijos.append(hijo)


def _analizar_jsx(texto, no_analizado):
    raiz = Nodo("#raiz", None, 1)
    j = _Jsx(texto)
    try:
        j.escanear(0, raiz, False, 0)
    except _ErrorJsx as e:
        no_analizado.append({"line": None, "reason": str(e)})
    except RecursionError:
        no_analizado.append({"line": None, "reason": "JSX anidado demasiado hondo"})
    if j.errores:
        no_analizado.append({"line": j.errores[0][0], "reason": "%d construccion(es) que parecen JSX no se pudieron leer (la primera: %s); pueden ser genericos de TypeScript o JSX mal formado" % (len(j.errores), j.errores[0][1])})
    return raiz


# -- contexto del documento -----------------------------------------------------------------------------

class _Contexto(object):
    def __init__(self, raiz, formato, inclusiones=False):
        self.raiz = raiz
        self.formato = formato
        self.por_tag = {}
        self.ids = {}
        self.labels_for = {}
        self.label_dinamico = False
        self.componentes = {}
        self.spreads = 0
        self.nodos = 0
        self._cache = {}
        for n in recorrer(raiz):
            if n is raiz:
                continue
            self.nodos += 1
            self.por_tag.setdefault(n.tag, []).append(n)
            a = n.attrs.get("id")
            if a is not None and not a.dinamico and a.valor.strip():
                self.ids.setdefault(a.valor.strip(), []).append(n)
            if n.tag == "label":
                f = n.attrs.get("for")
                if f is not None:
                    if f.dinamico:
                        self.label_dinamico = True
                    elif f.valor.strip():
                        self.labels_for.setdefault(f.valor.strip(), []).append(n)
            if n.componente:
                self.componentes.setdefault(n.tag, []).append(n.linea)
            if n.spread:
                self.spreads += 1
        self.inclusiones = inclusiones
        self.html = (self.por_tag.get("html") or [None])[0]
        self.es_documento = self.html is not None
        # Mundo cerrado: el archivo es un documento completo y no arma partes con otros archivos.
        # Solo en un mundo cerrado la ausencia de un id, de una etiqueta o de un <title> es un hecho.
        self.cerrado = self.es_documento and not inclusiones

    def tags(self, *nombres):
        for t in nombres:
            for n in self.por_tag.get(t, ()):
                yield n

    def texto(self, nodo, excluir=None):
        """(texto, dinamico): el texto util de un elemento, sin lo oculto a las tecnologias de asistencia."""
        clave = (id(nodo), id(excluir))
        if clave in self._cache:
            return self._cache[clave]
        partes, dinamico = [], False
        pila = [nodo]
        while pila:
            n = pila.pop()
            if n is excluir:
                continue
            if n is not nodo and _estatico(n, "aria-hidden") == "true":
                continue
            if n.tag in ("script", "style"):
                continue
            if n.texto:
                partes.extend(n.texto)
            if n.expr_hijos or n.spread and n is not nodo:
                dinamico = True
            if n is not nodo:
                al = n.attrs.get("aria-label")
                if al is not None and (al.dinamico or _util(al.valor)):
                    if al.dinamico:
                        dinamico = True
                    else:
                        partes.append(al.valor)
                if n.tag == "img":
                    alt = n.attrs.get("alt")
                    if alt is not None and (alt.dinamico or _util(alt.valor)):
                        if alt.dinamico:
                            dinamico = True
                        else:
                            partes.append(alt.valor)
            pila.extend(n.hijos)
        txt = " ".join(partes)
        if SENT in txt:
            dinamico = True
        res = (txt.replace(SENT, " ").strip(), dinamico)
        self._cache[clave] = res
        return res

    def util(self, nodo, excluir=None):
        t, d = self.texto(nodo, excluir)
        return bool(t) or d


# -- nombre accesible de un control ----------------------------------------------------------------------

_TIPOS_SIN_ETIQUETA = ("hidden",)
_TIPOS_TEXTO = ("text", "email", "tel", "url", "search", "password", "number", "date", "time", "datetime-local",
                "month", "week", "")


def _tipo_input(n):
    t = _estatico(n, "type")
    return (t or "text").strip().lower() if n.tag == "input" else n.tag


def _nombre_control(n, ctx):
    """('nombrado'|'dinamico'|'placeholder'|'indeterminado'|'ninguno', [motivos])."""
    motivos = []
    indeterminado = False
    if n.spread:
        return ("indeterminado", ["el elemento recibe {...props}: no se sabe qué atributos trae"])

    lb = n.attrs.get("aria-labelledby")
    if lb is not None:
        if lb.dinamico:
            return ("dinamico", [])
        ids = lb.valor.split()
        if ids:
            faltan, vacios, ok = [], [], False
            for i in ids:
                els = ctx.ids.get(i)
                if not els:
                    faltan.append(i)
                elif ctx.util(els[0]):
                    ok = True
                else:
                    vacios.append(i)
            if ok:
                return ("nombrado", [])
            if faltan:
                if ctx.cerrado:
                    motivos.append("aria-labelledby apunta a #%s, que no existe" % faltan[0])
                else:
                    indeterminado = True
            if vacios:
                motivos.append("aria-labelledby apunta a #%s, que no tiene texto" % vacios[0])
        else:
            motivos.append("aria-labelledby está vacío")

    al = n.attrs.get("aria-label")
    if al is not None:
        if al.dinamico or _util(al.valor):
            return ("dinamico" if al.dinamico else "nombrado", [])
        motivos.append("aria-label está en blanco")

    ident = n.attrs.get("id")
    if ident is not None and ident.dinamico:
        if ctx.label_dinamico:
            return ("dinamico", [])
    elif ident is not None and ident.valor.strip():
        for lab in ctx.labels_for.get(ident.valor.strip(), ()):
            if ctx.util(lab, n):
                return ("nombrado", [])
            motivos.append("la <label for=\"%s\"> no tiene texto" % ident.valor.strip())

    p, prof = n.padre, 0
    while p is not None and prof < 40:
        if p.tag == "label":
            if ctx.util(p, n):
                return ("nombrado", [])
            motivos.append("la <label> que lo envuelve no tiene texto")
            break
        p, prof = p.padre, prof + 1

    ti = n.attrs.get("title")
    if ti is not None and (ti.dinamico or _util(ti.valor)):
        return ("nombrado", [])

    tipo = _tipo_input(n)
    if n.tag == "input" and tipo in ("submit", "reset"):
        return ("nombrado", [])
    if n.tag == "input" and tipo == "button":
        v = n.attrs.get("value")
        if v is not None and (v.dinamico or _util(v.valor)):
            return ("nombrado", [])
    ph = n.attrs.get("placeholder")
    if ph is not None and (ph.dinamico or _util(ph.valor)) and (n.tag == "textarea" or tipo in _TIPOS_TEXTO):
        return ("placeholder", motivos)

    if not ctx.cerrado and ident is not None and (ident.dinamico or ident.valor.strip()):
        if ident.dinamico or ctx.label_dinamico or ctx.inclusiones or _bajo_componente(n):
            return ("indeterminado", ["tiene id, pero la etiqueta puede venir de un componente, de una expresión o de otra plantilla"])
        return ("etiqueta_fuera", ["tiene id=\"%s\" y no hay una <label for=\"%s\"> en este archivo" % (ident.valor.strip(), ident.valor.strip())])
    if indeterminado:
        return ("indeterminado", ["aria-labelledby apunta a un id que no está en este fragmento"])
    if _bajo_componente(n):
        return ("indeterminado", ["lo envuelve un componente propio, que puede traer la etiqueta por dentro"])
    return ("ninguno", motivos)


def _bajo_componente(n):
    """Verdadero si algun ancestro es un componente propio: puede traer la etiqueta por dentro."""
    p, prof = n.padre, 0
    while p is not None and prof < 40:
        if p.componente:
            return True
        p, prof = p.padre, prof + 1
    return False


def _nombre_por_contenido(n, ctx):
    """Botones, enlaces y roles que se nombran por su contenido."""
    if n.spread:
        return True
    for nombre in ("aria-label", "title"):
        a = n.attrs.get(nombre)
        if a is not None and (a.dinamico or _util(a.valor)):
            return True
    lb = n.attrs.get("aria-labelledby")
    if lb is not None:
        if lb.dinamico:
            return True
        if any(i in ctx.ids and ctx.util(ctx.ids[i][0]) for i in lb.valor.split()):
            return True
        if not ctx.cerrado and lb.valor.split():
            return True
    if ctx.util(n):
        return True
    # un <svg> con <title> hijo cuenta: su texto ya entra por ctx.texto. Un hijo con un componente
    # propio (<Icon />) puede traer el nombre: no se juzga.
    for h in n.hijos:
        if h.componente:
            return True
    return False


# -- las reglas -------------------------------------------------------------------------------------------

class _Salida(object):
    def __init__(self):
        self.hallazgos = []

    def add(self, regla, nodo, detalle=None, linea=None):
        sc, tipo, origen, liviana, tecnica = REGLAS[regla]
        self.hallazgos.append({
            "rule": regla, "sc": list(sc), "level": NIVELES[sc[0]] if sc else None, "kind": tipo, "origin": origen,
            "line": linea if linea is not None else (nodo.linea if nodo is not None else None),
            "element": _describir(nodo) if nodo is not None else None,
            "detail": detalle, "technique": tecnica,
        })


def _describir(n):
    if n is None:
        return None
    ident = n.attrs.get("id")
    return "<%s%s>" % (n.tag, (' id="%s"' % ident.valor) if ident is not None and not ident.dinamico and ident.valor else "")


_BCP47 = _Perezosa(r"^[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*$")
_AUTOCOMPLETE = frozenset((
    "on", "off", "name", "honorific-prefix", "given-name", "additional-name", "family-name", "honorific-suffix",
    "nickname", "organization-title", "username", "new-password", "current-password", "one-time-code",
    "organization", "street-address", "address-line1", "address-line2", "address-line3", "address-level4",
    "address-level3", "address-level2", "address-level1", "country", "country-name", "postal-code", "cc-name",
    "cc-given-name", "cc-additional-name", "cc-family-name", "cc-number", "cc-exp", "cc-exp-month",
    "cc-exp-year", "cc-csc", "cc-type", "transaction-currency", "transaction-amount", "language", "bday",
    "bday-day", "bday-month", "bday-year", "sex", "url", "photo", "tel", "tel-country-code", "tel-national",
    "tel-area-code", "tel-local", "tel-local-prefix", "tel-local-suffix", "tel-extension", "email", "impp",
    "webauthn"))
_AUTOCOMPLETE_CALIF = frozenset(("shipping", "billing", "home", "work", "mobile", "fax", "pager"))
_PISTAS_PERSONALES = ("email", "phone", "tel", "name", "address", "postal", "zip", "password", "username",
                      "country", "city", "birthday", "bday")
_GENERICOS = frozenset((
    "click here", "here", "more", "read more", "learn more", "link", "details", "click", "more info",
    "haga clic aqui", "haga clic aquí", "click aqui", "click aquí", "clic aqui", "clic aquí", "hace click aca",
    "hacé click acá", "aca", "acá", "aqui", "aquí", "mas info", "más info", "mas informacion", "más información",
    "ver mas", "ver más", "leer mas", "leer más", "mas", "más"))
_INTERACTIVOS = frozenset(("a", "button", "input", "select", "textarea", "summary", "details", "label", "option", "area"))
_ROLES_INTERACTIVOS = frozenset((
    "button", "link", "checkbox", "radio", "switch", "tab", "menuitem", "menuitemcheckbox", "menuitemradio", "option",
    "slider", "spinbutton", "textbox", "combobox", "searchbox", "treeitem", "gridcell", "scrollbar"))
_NO_INTERACTIVOS = frozenset(("div", "span", "li", "p", "td", "section", "article", "i", "b", "img", "svg", "h1", "h2", "h3"))
_REFERENCIAS_LIVIANAS = ("aria-labelledby", "aria-describedby")
_REFERENCIAS_TODAS = ("aria-labelledby", "aria-describedby", "aria-controls", "aria-owns", "aria-activedescendant",
                      "aria-details", "aria-errormessage", "aria-flowto")


def _es_control(n):
    if n.tag in ("select", "textarea"):
        return True
    if n.tag == "input":
        return _tipo_input(n) not in _TIPOS_SIN_ETIQUETA + ("image",)
    return False


def _reglas_documento(ctx, s, completo):
    html = ctx.html
    if html is None:
        return
    lang = html.attrs.get("lang") or html.attrs.get("xml:lang")
    if lang is None or (not lang.dinamico and not lang.valor.strip()):
        s.add("html-missing-lang", html)
    elif not lang.dinamico and not _BCP47.match(lang.valor.strip()):
        s.add("html-invalid-lang", html, detalle=lang.valor.strip())
    if ctx.formato != "jsx" and ctx.cerrado and not _cabecera_dinamica(ctx):
        titulos = [t for t in ctx.tags("title") if not _dentro_de(t, "svg")]
        if not titulos or not any(ctx.util(t) for t in titulos):
            s.add("document-missing-title", html)
    if not completo:
        return
    for m in ctx.tags("meta"):
        he = (_estatico(m, "http-equiv") or "").lower()
        nombre = (_estatico(m, "name") or "").lower()
        contenido = (_estatico(m, "content") or "").lower().replace(" ", "")
        if he == "refresh":
            demora = re.match(r"^(\d+)", contenido)
            if demora and int(demora.group(1)) > 0:
                s.add("meta-refresh-delay", m, detalle=contenido)
        if nombre == "viewport" and _bloquea_zoom(contenido):
            s.add("viewport-blocks-zoom", m, detalle=contenido)
    if not ctx.cerrado:
        return
    # Recomendaciones de estructura: no son criterios de WCAG 2.2 y no se mezclan con los fallos.
    h1 = list(ctx.tags("h1"))
    if not h1:
        s.add("heading-no-h1", html)
    elif len(h1) > 1:
        s.add("heading-multiple-h1", h1[1], detalle=len(h1))
    if "main" not in ctx.por_tag and not any(_estatico(n, "role") == "main" for n in recorrer(ctx.raiz) if n.attrs):
        s.add("landmark-missing-main", html)
    niveles = [(n, int(n.tag[1])) for n in recorrer(ctx.raiz) if len(n.tag) == 2 and n.tag[0] == "h" and n.tag[1] in "123456"]
    for (a, na), (b, nb) in zip(niveles, niveles[1:]):
        if nb > na + 1:
            s.add("heading-skipped-level", b, detalle="h%d a h%d" % (na, nb))
            break


def _bloquea_zoom(contenido):
    """user-scalable=no (o 0), o un maximum-scale menor a 2: no se llega al 200 % de 1.4.4."""
    if re.search(r"user-scalable=(?:no|0)(?:,|$)", contenido):
        return True
    m = re.search(r"maximum-scale=(\d+(?:\.\d+)?)", contenido)
    return bool(m and float(m.group(1)) < 2.0)


def _cabecera_dinamica(ctx):
    """Verdadero si la cabecera del documento trae algo armado por una plantilla: ahi puede estar el <title>."""
    cabeza = (ctx.por_tag.get("head") or [None])[0]
    zonas = [cabeza] if cabeza is not None else [h for h in ctx.html.hijos if h.tag != "body"]
    for z in zonas:
        for n in recorrer(z):
            if any(SENT in t for t in n.texto):
                return True
    return False


def _dentro_de(n, tag):
    p = n.padre
    prof = 0
    while p is not None and prof < 200:
        if p.tag == tag:
            return True
        p, prof = p.padre, prof + 1
    return False


def _reglas_nombres(ctx, s, completo):
    for img in ctx.tags("img"):
        if img.spread:
            continue
        alt = img.attrs.get("alt")
        rol = _estatico(img, "role")
        if alt is None:
            if rol in ("presentation", "none"):
                continue
            if any(img.attrs.get(a) is not None and (img.attrs[a].dinamico or _util(img.attrs[a].valor))
                   for a in ("aria-label", "aria-labelledby")):
                continue
            s.add("img-missing-alt", img)
        elif completo and not alt.dinamico and re.search(r"\.(png|jpe?g|gif|svg|webp)$", alt.valor.strip(), re.IGNORECASE):
            s.add("img-alt-filename", img, detalle=alt.valor.strip())
    for n in ctx.tags("input"):
        if n.spread or _tipo_input(n) != "image":
            continue
        if not any(n.attrs.get(a) is not None and (n.attrs[a].dinamico or _util(n.attrs[a].valor))
                   for a in ("alt", "aria-label", "aria-labelledby", "title")):
            s.add("input-image-missing-alt", n)
    for n in ctx.tags("area"):
        if n.spread or "href" not in n.attrs:
            continue
        if not any(n.attrs.get(a) is not None and (n.attrs[a].dinamico or _util(n.attrs[a].valor))
                   for a in ("alt", "aria-label", "aria-labelledby")):
            s.add("area-missing-alt", n)

    for n in ctx.nodos_control:
        estado, motivos = _nombre_control(n, ctx)
        if estado == "ninguno":
            s.add("control-no-accessible-name", n, detalle=motivos[0] if motivos else None)
        elif estado == "etiqueta_fuera":
            s.add("control-label-missing-in-file", n, detalle=motivos[0] if motivos else None)
        elif estado == "indeterminado":
            if completo:
                s.add("control-name-undeterminable", n, detalle=motivos[0] if motivos else None)
        elif estado == "placeholder" and completo:
            s.add("control-placeholder-only", n)
    for n in list(ctx.tags("button")) + [x for x in recorrer(ctx.raiz) if _estatico(x, "role") == "button" and x.tag != "button"]:
        if not _nombre_por_contenido(n, ctx):
            s.add("button-no-accessible-name", n)
    for n in ctx.tags("a"):
        if "href" not in n.attrs:
            continue
        if not _nombre_por_contenido(n, ctx):
            s.add("link-no-accessible-name", n)
        elif completo:
            t, d = ctx.texto(n)
            if not d and re.sub(r"[.…!¡¿?:]+$", "", t.strip().lower()) in _GENERICOS:
                s.add("link-generic-text", n, detalle=t.strip())
    for n in ctx.tags("iframe"):
        if n.spread:
            continue
        if not any(n.attrs.get(a) is not None and (n.attrs[a].dinamico or _util(n.attrs[a].valor))
                   for a in ("title", "aria-label", "aria-labelledby")):
            s.add("iframe-missing-title", n)


def _reglas_referencias(ctx, s, completo):
    atributos = _REFERENCIAS_TODAS if completo else _REFERENCIAS_LIVIANAS
    for n in recorrer(ctx.raiz):
        if n is ctx.raiz or not n.attrs:
            continue
        for a in atributos:
            ref = n.attrs.get(a)
            if ref is None or ref.dinamico:
                continue
            ids = ref.valor.split()
            if not ids:
                continue
            # Un control que se queda sin nombre por esta referencia ya sale como control sin nombre,
            # con este motivo: no se dice dos veces.
            cubierto = a == "aria-labelledby" and _es_control(n) and _nombre_control(n, ctx)[0] == "ninguno"
            presentes = [i for i in ids if i in ctx.ids]
            if ctx.cerrado and not presentes:
                if not cubierto:
                    s.add("aria-reference-broken", n, detalle="%s=\"%s\" (falta #%s)" % (a, ref.valor.strip(), ids[0]))
                continue
            if a in _REFERENCIAS_LIVIANAS and presentes and not any(ctx.util(ctx.ids[i][0]) for i in presentes):
                if not cubierto:
                    s.add("aria-reference-no-text", n, detalle="%s=\"%s\"" % (a, ref.valor.strip()))
    if not ctx.cerrado:
        return
    for lab in ctx.tags("label"):
        f = lab.attrs.get("for")
        if f is None or f.dinamico or not f.valor.strip():
            continue
        if f.valor.strip() not in ctx.ids:
            s.add("label-for-broken", lab, detalle=f.valor.strip())
    referenciados = set(ctx.labels_for)
    for n in recorrer(ctx.raiz):
        for a in _REFERENCIAS_TODAS:
            r = n.attrs.get(a) if n.attrs else None
            if r is not None and not r.dinamico:
                referenciados.update(r.valor.split())
    for i, nodos in ctx.ids.items():
        if len(nodos) > 1:
            if i in referenciados:
                s.add("duplicate-id-referenced", nodos[1], detalle=i)
            elif completo:
                s.add("duplicate-id", nodos[1], detalle=i)


def _reglas_completas(ctx, s):
    for n in recorrer(ctx.raiz):
        if n is ctx.raiz:
            continue
        tag = n.tag
        if tag in ("marquee", "blink"):
            s.add("marquee-or-blink", n, detalle=tag)
            continue
        if n.spread:
            continue
        # -- foco y teclado
        ti = _estatico(n, "tabindex")
        if ti is not None and re.fullmatch(r"\d+", ti.strip()) and int(ti) > 0:
            s.add("tabindex-positive", n, detalle=ti)
        rol = _estatico(n, "role")
        if "onclick" in n.attrs and (tag in _NO_INTERACTIVOS) and rol not in _ROLES_INTERACTIVOS \
                and (ti is None or (re.fullmatch(r"-?\d+", ti.strip()) and int(ti) < 0)):
            s.add("clickable-not-keyboard", n)
        # -- formularios
        if tag == "input" or tag == "select" or tag == "textarea":
            ac = n.attrs.get("autocomplete")
            tipo = _tipo_input(n)
            if ac is not None and not ac.dinamico and ac.valor.strip():
                malos = [t for t in ac.valor.lower().split()
                         if t not in _AUTOCOMPLETE and t not in _AUTOCOMPLETE_CALIF and not t.startswith("section-")]
                if malos:
                    s.add("autocomplete-invalid-token", n, detalle=", ".join(malos))
            elif ac is None and tag == "input" and tipo in ("text", "email", "tel", "url", "password"):
                pista = (_estatico(n, "name") or "") + " " + (_estatico(n, "id") or "")
                hit = next((k for k in _PISTAS_PERSONALES if k in pista.lower()), None)
                if hit:
                    s.add("autocomplete-missing", n, detalle=hit)
            if tag == "input" and tipo == "password":
                if "onpaste" in n.attrs or (_estatico(n, "onpaste") or "").lower().find("false") >= 0:
                    s.add("password-blocks-paste", n)
                if ac is not None and not ac.dinamico and ac.valor.strip().lower() == "off":
                    s.add("password-autocomplete-off", n)
        # -- aria-hidden con foco adentro
        if _estatico(n, "aria-hidden") == "true" and not _bajo_aria_hidden(n):
            for d in recorrer(n):
                dt = _estatico(d, "tabindex")
                if (d.tag in ("a", "button", "input", "select", "textarea") and not (d.tag == "a" and "href" not in d.attrs)
                        and _tipo_input(d) != "hidden") or (dt is not None and dt.strip() != "-1" and re.fullmatch(r"-?\d+", dt.strip() or "x")):
                    s.add("aria-hidden-focusable", d)
                    break
        # -- estructura
        if tag == "table" and rol not in ("presentation", "none"):
            tiene_th = any(x.tag == "th" for x in recorrer(n))
            tiene_td = any(x.tag == "td" for x in recorrer(n))
            if tiene_td and not tiene_th:
                s.add("table-without-headers", n)
        if re.fullmatch(r"h[1-6]", tag) and not ctx.util(n):
            s.add("heading-empty", n)
        # -- medios
        if tag in ("audio", "video"):
            if "autoplay" in n.attrs and "muted" not in n.attrs:
                s.add("media-autoplay", n)
            if tag == "video" and not any(h.tag == "track" and (_estatico(h, "kind") or "subtitles") in ("captions", "subtitles") for h in n.hijos):
                s.add("video-no-captions", n)


def _bajo_aria_hidden(n):
    p, prof = n.padre, 0
    while p is not None and prof < 200:
        if _estatico(p, "aria-hidden") == "true":
            return True
        p, prof = p.padre, prof + 1
    return False


# -- la revision ------------------------------------------------------------------------------------------

class Resultado(object):
    def __init__(self, nombre, formato):
        self.nombre = nombre
        self.formato = formato
        self.es_documento = False
        self.cerrado = False
        self.hallazgos = []
        self.no_analizado = []
        self.componentes = {}
        self.spreads = 0
        self.nodos = 0

    @property
    def completo(self):
        return not self.no_analizado


def revisar(texto, nombre, modo="liviano"):
    """Analiza un archivo. modo: 'liviano' (solo fail y defect de la lista liviana) o 'completo'."""
    formato = formato_de(nombre)
    res = Resultado(nombre, formato)
    if formato is None:
        res.no_analizado.append({"line": None, "reason": "extensión fuera de alcance: el motor lee HTML, plantillas y JSX/TSX"})
        return res
    completo = modo == "completo"
    try:
        if formato == "jsx":
            raiz = _analizar_jsx(texto, res.no_analizado)
        else:
            raiz = _analizar_html(texto)
    except Exception as e:      # un archivo que no se puede leer: se dice, no se explota
        res.no_analizado.append({"line": None, "reason": "no se pudo leer el archivo: %s" % e.__class__.__name__})
        return res
    ctx = _Contexto(raiz, formato, formato != "jsx" and tiene_inclusiones(texto))
    ctx.nodos_control = [n for n in recorrer(raiz) if n is not raiz and _es_control(n)]
    res.es_documento = ctx.es_documento
    res.cerrado = ctx.cerrado
    res.componentes = {k: v for k, v in ctx.componentes.items()}
    res.spreads = ctx.spreads
    res.nodos = ctx.nodos
    if ctx.componentes:
        for k, lineas in sorted(ctx.componentes.items()):
            res.no_analizado.append({"line": lineas[0], "reason": "componente <%s> no resuelto (%d vez/veces): sus etiquetas, roles y atributos no se juzgan" % (k, len(lineas))})
    if ctx.spreads:
        res.no_analizado.append({"line": None, "reason": "%d elemento(s) con {...props}: no se juzgan los atributos que el spread podria traer" % ctx.spreads})
    s = _Salida()
    _reglas_documento(ctx, s, completo)
    _reglas_nombres(ctx, s, completo)
    _reglas_referencias(ctx, s, completo)
    if completo:
        _reglas_completas(ctx, s)
    hs = s.hallazgos
    if not completo:
        hs = [h for h in hs if REGLAS[h["rule"]][3]]
    hs.sort(key=lambda h: (ORDEN_TIPO[h["kind"]], h["line"] or 0))
    res.hallazgos = hs
    return res


# -- mensajes -------------------------------------------------------------------------------------------

def _criterios_txt(sc):
    if not sc:
        return "recomendación del harness: WCAG 2.2 no lo exige"
    niveles = sorted(set(NIVELES[c] for c in sc))
    if len(sc) == 1:
        return "criterio %s, nivel %s" % (sc[0], NIVELES[sc[0]])
    return "criterios %s, nivel %s" % (" y ".join(sc), "/".join(niveles))


def _lineas(hs, maximo=3):
    ls = ["L%d" % h["line"] for h in hs if h["line"]]
    txt = ", ".join(ls[:maximo])
    if len(ls) > maximo:
        txt += " (+%d más)" % (len(ls) - maximo)
    return txt


def _plural(n, uno, varios):
    return "%d %s" % (n, uno if n == 1 else varios)


def mensaje(regla, hs, archivo):
    """Un aviso en castellano para todos los hallazgos de una regla en un archivo."""
    n = len(hs)
    c = _criterios_txt(REGLAS[regla][0])
    ls = _lineas(hs)
    det = [h["detail"] for h in hs if h["detail"]]
    cola = " (%s)" % c
    M = {
        "html-missing-lang": lambda: "<html> sin atributo lang%s. El lector de pantalla necesita saber el idioma para elegir la fonética; sin eso lee el castellano como si fuera inglés. Agregá lang=\"es\"." % cola,
        "html-invalid-lang": lambda: "<html lang=\"%s\"> no es una etiqueta de idioma válida%s. Usá un código BCP 47: \"es\", \"es-AR\"." % (det[0] if det else "", cola),
        "document-missing-title": lambda: "el documento no tiene <title> o está vacío%s. Es lo primero que anuncia un lector de pantalla al abrir la página." % cola,
        "img-missing-alt": lambda: "%s sin atributo alt — %s%s. Si la imagen es decorativa va alt=\"\" vacío, que es una afirmación; que el atributo falte no dice nada." % (_plural(n, "<img>", "<img>"), ls, cola),
        "input-image-missing-alt": lambda: "%s sin texto alternativo — %s%s. Necesita alt con la acción que dispara." % (_plural(n, "<input type=\"image\">", "<input type=\"image\">"), ls, cola),
        "area-missing-alt": lambda: "%s sin alt — %s%s." % (_plural(n, "<area>", "<area>"), ls, cola),
        "control-no-accessible-name": lambda: "%s sin nombre accesible — %s%s. Un id no es un nombre: hace falta una <label for> que lo apunte y tenga texto, una <label> que lo envuelva, un aria-label o un aria-labelledby que resuelva a texto.%s" % (
            _plural(n, "control de formulario", "controles de formulario"), ls, cola, (" Por ejemplo: %s." % det[0]) if det else ""),
        "control-label-missing-in-file": lambda: "%s con id y sin <label for> en este archivo — %s%s. Un id solo no es un nombre. Si la etiqueta vive en otro archivo, confirmalo; si no, falta." % (
            _plural(n, "control", "controles"), ls, cola),
        "button-no-accessible-name": lambda: "%s sin nombre accesible — %s%s. Un botón solo con ícono necesita un aria-label con la acción." % (_plural(n, "botón", "botones"), ls, cola),
        "link-no-accessible-name": lambda: "%s sin nombre accesible — %s%s. Un enlace vacío, o con solo una imagen sin alt, no dice adónde va." % (_plural(n, "enlace", "enlaces"), ls, cola),
        "iframe-missing-title": lambda: "%s sin title — %s%s. Es lo que anuncia el lector de pantalla para el marco." % (_plural(n, "<iframe>", "<iframe>"), ls, cola),
        "aria-reference-broken": lambda: "%s ARIA a un id que no existe — %s%s. Una referencia rota no nombra ni describe nada." % (_plural(n, "referencia", "referencias"), "; ".join(det[:3]) or ls, cola),
        "aria-reference-no-text": lambda: "%s ARIA a un elemento sin texto — %s%s. Apunta a algo que existe pero no dice nada." % (_plural(n, "referencia", "referencias"), "; ".join(det[:3]) or ls, cola),
        "label-for-broken": lambda: "%s <label for> apuntan a un id que no existe — %s%s." % (n, ", ".join("#" + d for d in det[:3]) or ls, cola),
        "duplicate-id-referenced": lambda: "id repetido y referenciado: %s%s. Una <label for> o un aria-* puede resolver al elemento equivocado." % (", ".join("#" + d for d in det[:3]), cola),
        "viewport-blocks-zoom": lambda: "el viewport bloquea el zoom (%s)%s. Quien necesita agrandar el texto no puede." % (det[0] if det else "", cola),
        "meta-refresh-delay": lambda: "meta refresh con demora (%s)%s: impone un límite de tiempo y recarga la página." % (det[0] if det else "", cola),
        "autocomplete-invalid-token": lambda: "%s con autocomplete inválido (%s) — %s%s." % (_plural(n, "campo", "campos"), "; ".join(det[:3]), ls, cola),
        "password-blocks-paste": lambda: "el campo de contraseña bloquea pegar — %s%s. Impide los gestores de contraseñas." % (ls, cola),
        "marquee-or-blink": lambda: "<%s>: contenido que se mueve o parpadea sin forma de pausarlo — %s%s." % (det[0] if det else "marquee", ls, cola),
        "aria-hidden-focusable": lambda: "elemento enfocable dentro de aria-hidden=\"true\" — %s%s: se enfoca con el teclado y la tecnología de asistencia no lo ve." % (ls, cola),
        "clickable-not-keyboard": lambda: "%s con onclick que no se alcanza por teclado — %s%s. Usá <button>, o agregá role, tabindex y manejo de Enter/Espacio." % (_plural(n, "elemento", "elementos"), ls, cola),
        "autocomplete-missing": lambda: "%s que parecen pedir datos de la persona (%s) sin autocomplete — %s%s." % (_plural(n, "campo", "campos"), ", ".join(sorted(set(det))[:3]), ls, cola),
        "password-autocomplete-off": lambda: "el campo de contraseña tiene autocomplete=\"off\" — %s%s. Usá current-password o new-password." % (ls, cola),
        "tabindex-positive": lambda: "tabindex positivo (%s) — %s%s: altera el orden natural del foco." % (", ".join(sorted(set(det))[:3]), ls, cola),
        "table-without-headers": lambda: "%s sin celdas <th> — %s%s. Si es de datos, marcá los encabezados; si es de maquetación, role=\"presentation\"." % (_plural(n, "tabla", "tablas"), ls, cola),
        "heading-empty": lambda: "%s sin texto — %s%s." % (_plural(n, "encabezado", "encabezados"), ls, cola),
        "media-autoplay": lambda: "audio o video con autoplay y sin muted — %s%s: el audio de más de 3 s necesita pausa o volumen propio." % (ls, cola),
        "video-no-captions": lambda: "%s sin <track kind=\"captions\"> — %s%s. Verificá si los subtítulos vienen del reproductor." % (_plural(n, "<video>", "<video>"), ls, cola),
        "img-alt-filename": lambda: "%s con un alt que parece un nombre de archivo — %s%s." % (_plural(n, "imagen", "imágenes"), ls, cola),
        "link-generic-text": lambda: "%s con texto genérico (%s) — %s%s. El texto tiene que decir adónde va." % (_plural(n, "enlace", "enlaces"), "; ".join(sorted(set(det))[:3]), ls, cola),
        "control-placeholder-only": lambda: "%s con solo placeholder como etiqueta — %s%s. Obelisco: el placeholder no sustituye a la <label> ni lleva información crucial." % (_plural(n, "campo", "campos"), ls, cola),
        "control-name-undeterminable": lambda: "%s cuyo nombre este archivo no puede decidir — %s. %s" % (_plural(n, "control", "controles"), ls, (det[0][:1].upper() + det[0][1:] + ".") if det else ""),
        "heading-no-h1": lambda: "el documento no tiene <h1> (%s). Es una recomendación de estructura, no un fallo." % _criterios_txt(()),
        "heading-multiple-h1": lambda: "el documento tiene %s <h1> (%s). HTML y WCAG 2.2 lo permiten; un solo <h1> es una recomendación." % (det[0] if det else n, _criterios_txt(())),
        "heading-skipped-level": lambda: "salto de nivel de encabezado, %s (%s)." % (det[0] if det else "", _criterios_txt(())),
        "landmark-missing-main": lambda: "el documento no tiene un landmark <main> (%s). Ayuda a saltar los bloques repetidos." % _criterios_txt(()),
        "duplicate-id": lambda: "id repetido: %s (%s). No lo referencia nada, así que no afecta a un criterio." % (", ".join("#" + d for d in det[:3]), _criterios_txt(())),
    }
    return "[a11y] %s: %s" % (archivo, M[regla]())


def mensajes(res, archivo=None):
    """Los avisos agrupados por regla, en el orden de gravedad."""
    archivo = archivo or os.path.basename(res.nombre)
    grupos = {}
    for h in res.hallazgos:
        grupos.setdefault(h["rule"], []).append(h)
    orden = sorted(grupos, key=lambda r: (ORDEN_TIPO[REGLAS[r][1]], min(h["line"] or 0 for h in grupos[r])))
    return [mensaje(r, grupos[r], archivo) for r in orden]


def mensajes_livianos(res, archivo=None):
    return mensajes(res, archivo)[:MAX_POR_ARCHIVO]
