"""Lectura y medicion de las zonas del CLAUDE.md.

El CLAUDE.md se carga entero al abrir la sesion y ocupa ventana de contexto mientras
dure. Por eso esta partido en zonas con politica distinta, cada una con su techo.

Sin una medicion automatica, "mantener chico el CLAUDE.md" es una intencion. Todo
harness engorda, porque agregar una linea aca siempre va a ser mas facil que escribir
una skill. El techo es la unica defensa que no depende de la disciplina de nadie.
"""
import json
import re
import unicodedata


def definicion_zonas():
    """Las zonas conocidas, su marcador y la clave de su techo en harness.config.json."""
    return [
        {"nombre": "ZONA FIJA", "techo": "techoZonaFija",
         "que": "reglas que se ejecutan cada turno", "alias": []},
        {"nombre": "ZONA MAPA", "techo": "techoZonaMapa",
         "que": "donde esta cada cosa", "alias": []},
        {"nombre": "ZONA INDICE", "techo": "techoZonaIndice",
         "que": "punteros al conocimiento", "alias": ["ZONA ÍNDICE"]},
        {"nombre": "ZONA CACHE", "techo": "techoZonaCache",
         "que": "lo aprendido, todavia sin bajar", "alias": ["ZONA CACHÉ"]},
    ]


def contenido_zona(texto, zona):
    """Devuelve el texto de una zona, o None si el archivo no la tiene.

    Los marcadores son comentarios HTML que ademas llevan la explicacion de la zona,
    asi que se busca por prefijo y no por igualdad. Se aceptan alias para tolerar la
    variante con tilde y la variante sin tilde del mismo nombre.
    """
    nombres = [zona["nombre"]] + list(zona.get("alias") or [])

    for n in nombres:
        i_ini = texto.find("<!-- " + n)
        if i_ini < 0:
            continue

        cierre_ini = texto.find("-->", i_ini)
        if cierre_ini < 0:
            continue
        cierre_ini += 3

        i_fin = texto.find("<!-- /" + n, cierre_ini)
        if i_fin < 0:
            continue

        return texto[cierre_ini:i_fin]
    return None


def a_nombre_plano(nombre):
    """Normaliza para comparar: sin tildes, en mayusculas y sin el prefijo ZONA.
    Sirve para reconocer que CACHÉ y ZONA CACHE son el mismo concepto escrito
    distinto, no para decidir que es canonico."""
    descompuesto = unicodedata.normalize("NFD", nombre)
    plano = "".join(c for c in descompuesto
                    if unicodedata.category(c) != "Mn").upper().strip()
    return re.sub(r"^ZONA\s+", "", plano)


def marcadores_html(texto):
    """Un marcador puede ocupar varias lineas -ya paso- asi que no alcanza con mirar
    linea por linea: se ubican los comentarios sobre el texto completo y recien
    despues se traducen a lineas.

    El nombre se toma por lo que ES -letras, numeros, dos puntos y espacios- y no
    por el separador que venga despues: los archivos generados usan raya larga y
    una persona escribiendo a mano pone un guion comun.
    """
    marcadores = []
    if not texto:
        return marcadores
    lineas = texto.split("\n")
    inicio = []
    acum = 0
    for l in lineas:
        inicio.append(acum)
        acum += len(l) + 1

    def indice_de_linea(offset):
        for k in range(len(lineas) - 1, -1, -1):
            if offset >= inicio[k]:
                return k
        return 0

    for m in re.finditer(r"(?s)<!--.*?-->", texto):
        interior = m.group(0)[4:-3]
        primera = interior.split("\n")[0]
        nom = re.match(r"^\s*(/?)\s*([^\W_]+(?:[:\w]*)(?:\s+[^\W_][:\w]*)*)", primera, re.UNICODE)
        if not nom:
            continue
        nombre = nom.group(2).strip()
        if not nombre:
            continue
        marcadores.append({"nombre": nombre, "es_cierre": nom.group(1) == "/",
                           "linea_ini": indice_de_linea(m.start()),
                           "linea_fin": indice_de_linea(m.end() - 1)})
    return marcadores


def zonas_no_reconocidas(texto):
    """Marcadores con forma de zona que el harness no reconoce.

    Un par de comentarios HTML de apertura y cierre con el mismo nombre ES una zona,
    la haya escrito el harness o una persona. Si el nombre no coincide con ninguna
    zona canonica, agregar la zona canonica al lado deja el archivo con dos: una con
    el contenido real y otra vacia, y el check mide la vacia.

    Ya paso, y paso en silencio: el CLAUDE.md del IGE traia INDICE y CACHE sin el
    prefijo ZONA, el instalador no los reconocio y agrego duplicados sin decir nada.
    Callarse fue peor que equivocarse.
    """
    hallazgos = []

    canonicos = []
    for z in definicion_zonas():
        canonicos.append(z["nombre"])
        canonicos.extend(z.get("alias") or [])
    # El bloque comun lo genera el instalador y tambien es un par apertura/cierre.
    canonicos.append("HARNESS:COMUN")

    marcadores = marcadores_html(texto)
    aperturas = [m for m in marcadores if not m["es_cierre"]]
    cierres = [m["nombre"] for m in marcadores if m["es_cierre"]]

    ya_vistos = []
    for a in aperturas:
        if a["nombre"] in canonicos:
            continue
        if a["nombre"] not in cierres:      # sin cierre no es una zona
            continue
        if a["nombre"] in ya_vistos:
            continue
        ya_vistos.append(a["nombre"])

        plano = a_nombre_plano(a["nombre"])
        parecida = ""
        for z in definicion_zonas():
            if a_nombre_plano(z["nombre"]) == plano:
                parecida = z["nombre"]
                break

        hallazgos.append({"marcador": a["nombre"], "parecida": parecida})

    return hallazgos


def medir_fuera_de_zonas(texto):
    """Cuenta las lineas con contenido que no estan dentro de ningun bloque marcado.

    medir_zonas mide lo que esta ADENTRO de las zonas. Lo que queda afuera no lo mide
    nadie: no se puede purgar, no se puede bajar al conocimiento del proyecto y no
    cuenta contra ningun techo. Un CLAUDE.md de trescientas lineas sin un solo
    marcador pasa la medicion entera sin que el harness diga una palabra.

    No es un pecado tener algo afuera: el titulo del archivo y dos lineas de
    presentacion van afuera y esta bien. Es un problema cuando es mucho, porque
    entonces el mecanismo entero es decorativo.
    """
    if not texto:
        return 0

    lineas = texto.split("\n")
    tapada = [False] * len(lineas)

    marcadores = marcadores_html(texto)

    # El marcador en si no es contenido.
    for m in marcadores:
        fin = min(m["linea_fin"], len(lineas) - 1)
        for i in range(m["linea_ini"], fin + 1):
            tapada[i] = True

    # Todo lo que va entre una apertura y su cierre esta adentro de un bloque.
    for k in range(len(marcadores)):
        a = marcadores[k]
        if a["es_cierre"]:
            continue
        for j in range(k + 1, len(marcadores)):
            c = marcadores[j]
            if c["es_cierre"] and c["nombre"] == a["nombre"]:
                fin = min(c["linea_ini"], len(lineas) - 1)
                for i in range(a["linea_fin"], fin + 1):
                    tapada[i] = True
                break

    contador = 0
    for i, l in enumerate(lineas):
        if tapada[i]:
            continue
        if l.strip():
            contador += 1
    return contador


def medir_zonas(texto):
    """Mide cada zona de un CLAUDE.md: si existe y cuantas lineas con contenido tiene.

    Se cuentan lineas con contenido. Las vacias son formato, no informacion, y
    castigarlas empujaria a escribir CLAUDE.md ilegibles para pasar la medicion.
    """
    resultado = []

    for zona in definicion_zonas():
        contenido = contenido_zona(texto, zona)

        lineas = 0
        if contenido is not None:
            lineas = len([l for l in contenido.split("\n") if l.strip()])

        resultado.append({
            "nombre": zona["nombre"],
            "que": zona["que"],
            "existe": contenido is not None,
            "lineas": lineas,
        })

    return resultado


def _imprimir_json(objeto):
    """Como lib.hook._emitir: bytes UTF-8 al buffer, nunca print(). install.ps1 va a
    leer este stdout en una consola que puede estar en cualquier codepage -en Windows,
    sin PYTHONUTF8, el default no es UTF-8- y un nombre de zona con tilde alcanza para
    corromper la salida o directamente reventar el parseo del lado de quien invoca."""
    import sys
    crudo = json.dumps(objeto, ensure_ascii=False)
    sys.stdout.buffer.write(crudo.encode("utf-8"))
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    import sys
    verbo = sys.argv[1] if len(sys.argv) > 1 else ""
    if verbo == "definicion":
        _imprimir_json(definicion_zonas())
    elif verbo == "contenido":
        texto = open(sys.argv[2], encoding="utf-8-sig").read()
        zona = next(z for z in definicion_zonas() if z["nombre"] == sys.argv[3])
        _imprimir_json({"contenido": contenido_zona(texto, zona)})
    elif verbo == "no-reconocidas":
        texto = open(sys.argv[2], encoding="utf-8-sig").read()
        _imprimir_json(zonas_no_reconocidas(texto))
    else:
        sys.stderr.write("verbo desconocido: %s\n" % verbo)
        sys.exit(2)
