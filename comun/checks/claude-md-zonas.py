"""Check: las zonas del CLAUDE.md y sus techos.

Corre despues de cada escritura sobre el CLAUDE.md del proyecto. Avisa -nunca
bloquea- cuando una zona paso su techo o cuando falta alguna.

Sin esto, "mantener chico el CLAUDE.md" es una intencion que dura hasta la primera
semana ocupada.

Contrato de un check: expone verificar(evento, proyecto, config) y devuelve cero o
mas strings. Cada string es un hallazgo que el hook entrega como additionalContext.
Silencio cuando esta todo bien: el costo tiene que ser proporcional a los problemas
reales, no al tamano del reglamento.
"""
import os
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_AQUI, "..", "hooks"))
from lib import hook, zonas  # noqa: E402


def _medir_con_techos(texto, config):
    """Cruza lo que mide lib.zonas con el techo de cada zona en harness.config.json.

    lib.zonas.medir_zonas es medicion pura: no conoce la config del proyecto. El
    calculo del exceso vive aca, en el check, no en la lib.
    """
    claves_de_techo = {z["nombre"]: z["techo"] for z in zonas.definicion_zonas()}
    resultado = []
    for z in zonas.medir_zonas(texto):
        clave = claves_de_techo.get(z["nombre"])
        techo = 0
        if config is not None and clave and clave in config:
            try:
                techo = int(config[clave])
            except (TypeError, ValueError):
                techo = 0
        fila = dict(z)
        fila["techo"] = techo
        fila["excedida"] = techo > 0 and z["lineas"] > techo
        resultado.append(fila)
    return resultado


def _fuera_de_zonas(texto):
    """Cuenta lo mismo que lib.zonas.medir_fuera_de_zonas y ademas junta una muestra:
    el hallazgo necesita mostrar donde empieza el exceso, y la lib solo expone el
    conteo. Se repite aca el mismo recorrido en vez de tocar la lib ya portada."""
    if not texto:
        return 0, []

    lineas = texto.split("\n")
    tapada = [False] * len(lineas)
    marcadores = zonas.marcadores_html(texto)

    for m in marcadores:
        fin = min(m["linea_fin"], len(lineas) - 1)
        for i in range(m["linea_ini"], fin + 1):
            tapada[i] = True

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

    afuera = []
    for i, l in enumerate(lineas):
        if tapada[i]:
            continue
        s = l.strip()
        if s:
            afuera.append(s)

    return len(afuera), afuera[:3]


def verificar(evento, proyecto, config):
    """Devuelve cero o mas strings. Cada string es un hallazgo."""
    ruta = hook.campo(evento, "tool_input.file_path", "")
    if not ruta:
        return []
    if os.path.basename(ruta) != "CLAUDE.md":
        return []
    if not os.path.isfile(ruta):
        return []

    with open(ruta, encoding="utf-8-sig") as f:
        texto = f.read()

    medicion = _medir_con_techos(texto, config)

    # Un CLAUDE.md sin ninguna zona es uno que el harness todavia no organizo. No es
    # un error del turno: no se avisa nada.
    con_zonas = [z for z in medicion if z["existe"]]
    if not con_zonas:
        return []

    hallazgos = []

    # Una zona escrita con otro nombre. Si nadie avisa, el proximo -Update agrega la
    # canonica al lado y quedan dos: una con el contenido y otra vacia, que es la que
    # se mide. Paso al instalar sobre el CLAUDE.md del IGE, y paso en silencio.
    raras = zonas.zonas_no_reconocidas(texto)
    con_otro_nombre = [r["parecida"] for r in raras if r["parecida"]]

    for r in raras:
        if r["parecida"]:
            hallazgos.append(
                "[CLAUDE.md] el marcador '%s' parece ser %s escrita con otro nombre. "
                "Mientras se llame asi el harness no la mide. "
                "Renombrar el marcador de apertura y el de cierre, y correr install.ps1 -Update."
                % (r["marcador"], r["parecida"]))

    # Lo que queda fuera de toda zona no lo mide nadie: no se purga, no baja al
    # conocimiento del proyecto y no cuenta contra ningun techo. Un CLAUDE.md de
    # trescientas lineas sin marcadores pasa la medicion entera sin una palabra.
    techo_fuera = 12
    if config is not None and "techoFueraDeZonas" in config:
        techo_fuera = int(config["techoFueraDeZonas"])
    lineas_fuera, muestra_fuera = _fuera_de_zonas(texto)
    if techo_fuera > 0 and lineas_fuera > techo_fuera:
        muestra = ""
        if muestra_fuera:
            muestra = " Empieza en: \"%s\"." % muestra_fuera[0]
        hallazgos.append(
            "[CLAUDE.md] hay %d lineas fuera de toda zona y el techo es %d.%s "
            "Fuera de una zona no se mide, no se purga y no baja al conocimiento del proyecto: "
            "mover ese contenido a la zona que le corresponda, o a una skill si no se necesita en cada turno."
            % (lineas_fuera, techo_fuera, muestra))

    for z in medicion:
        if z["excedida"]:
            hallazgos.append(
                "[CLAUDE.md] %s tiene %d lineas y su techo es %d. "
                "Este archivo ocupa ventana de contexto toda la sesion: lo que no se necesita en cada turno va en una skill."
                % (z["nombre"], z["lineas"], z["techo"]))

    # Una zona que existe con otro nombre NO esta faltando: esta mal nombrada, y eso
    # ya se aviso arriba. Decir las dos cosas manda a correr un -Update que a proposito
    # no la va a reponer, y un consejo que no funciona gasta la credibilidad de todos
    # los demas.
    faltantes = [z for z in medicion if not z["existe"] and z["nombre"] not in con_otro_nombre]
    if faltantes and con_zonas:
        hallazgos.append(
            "[CLAUDE.md] falta la zona " + ", ".join(z["nombre"] for z in faltantes) + ". "
            "Corre install.ps1 -Update para reponerla.")

    # La cache llena es informacion, no un problema: significa que hay conocimiento
    # sin bajar.
    cache = next((z for z in medicion if z["nombre"] == "ZONA CACHE"), None)
    if (cache and cache["existe"] and cache["techo"] > 0
            and cache["lineas"] > (cache["techo"] * 0.75) and not cache["excedida"]):
        hallazgos.append(
            "[CLAUDE.md] la cache va por %d de %d lineas. "
            "Corresponde correr flush-memoria para bajarla al conocimiento del proyecto."
            % (cache["lineas"], cache["techo"]))

    return hallazgos
