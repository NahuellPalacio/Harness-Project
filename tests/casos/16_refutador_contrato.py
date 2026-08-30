# Escenarios E-02 a E-07 de docs/cambios/dev-refutador-lee-el-contrato/spec.md.
#
# El sujeto de estos siete no es una corrida de un modelo: es el TEXTO de
# harnesses/desarrollo/agents/dev-refutador.md. ADR-0009 traza la frontera con esa misma
# frase -"si el sujeto es un archivo... hay mecanismo posible y la marca no corresponde"-,
# y por eso estos van por suite y no por lectura.md. Lo que la suite NO puede probar -que
# una corrida real de verdad se comporte asi- son E-08 y E-09 de la misma spec, que
# quedan en docs/cambios/dev-refutador-lee-el-contrato/lectura.md.
#
# E-01, el unico escenario de esta spec que toca codigo real (contexto-armar.py), vive en
# tests/casos/13_contexto.py junto a los demas tests del script, con el slug
# "(refutador-lee-contrato)" en el titulo para no pisar los ids de esa spec.
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
AGENTE = RAIZ / "harnesses" / "desarrollo" / "agents" / "dev-refutador.md"

TEXTO = AGENTE.read_text(encoding="utf-8")


def test_e02_lee_el_contrato_antes_de_grepear(t):
    """E-02 — instruye leer project-context.json antes de invocar una skill o grepear,
    y la seccion que lo dice esta ANTES de "De donde sacas la norma" -no despues-, que es
    donde justamente se invoca una skill o se grepea."""
    t.contiene("E-02: nombra el archivo del contrato",
              "docs/codebase/project-context.json", TEXTO)
    t.contiene("E-02: dice que es ANTES de invocar skill o grepear",
              "Antes de invocar una skill o grepear", TEXTO)

    pos_contrato = TEXTO.find("## De qué proyecto estás hablando")
    pos_norma = TEXTO.find("## De dónde sacás la norma")
    t.verdadero("E-02: la seccion del contrato existe", pos_contrato != -1)
    t.verdadero("E-02: la seccion de la norma existe", pos_norma != -1)
    t.verdadero("E-02: el contrato se lee antes de la norma",
                pos_contrato < pos_norma)


def test_e03_el_contrato_es_evidencia_nunca_norma(t):
    """E-03 — el archivo dice, sin admitir otra lectura, que el contrato es evidencia y
    que la norma sigue saliendo solo de las skills dev-*."""
    t.contiene("E-03: dice evidencia, nunca norma",
              "Es evidencia, nunca norma", TEXTO)
    t.contiene("E-03: y que la norma sigue saliendo de las skills dev-*",
              "sigue saliendo únicamente de las skills `dev-*`", TEXTO)


def test_e04_contrato_ausente_o_roto_es_sin_verificar_nunca_inferencia(t):
    """E-04 — contrato ausente, no parseable o insuficiente: hueco declarado y
    sin-verificar en lo que dependia de el. Nunca "completalo con lo que probablemente
    es el proyecto"."""
    t.contiene("E-04: contempla que no exista o no parsee",
              "no existe, no parsea como JSON", TEXTO)
    t.contiene("E-04: manda declararlo en el resumen",
              "Decilo en tu resumen", TEXTO)
    t.contiene("E-04: y sin-verificar lo que dependia de el",
              "es `sin-verificar`", TEXTO)
    t.contiene("E-04: nunca completar con inferencia",
              "nunca la completes con lo que", TEXTO)


def test_e05_la_fila_de_salida_nombra_el_repo_revision(t):
    """E-05 — el formato de salida suma una columna con el repo_revision del contrato
    usado, o el valor que corresponde cuando no hubo contrato."""
    m = re.search(r"^\| id \|.*\|\s*$", TEXTO, re.MULTILINE)
    t.verdadero("E-05: la tabla de salida existe", m is not None)
    if m:
        t.contiene("E-05: la columna repo_revision esta en el encabezado",
                  "repo_revision", m.group(0))
    t.contiene("E-05: y se explica que hacer sin contrato",
              "si no había contrato", TEXTO)


def test_e06_cumple_sigue_exigiendo_cita_y_linea_sin_excepcion_nueva(t):
    """E-06 — la regla que gobierna todo no gana una excepcion para el contrato: seguir
    exigiendo cita de la norma Y linea del archivo, nunca solo el contrato.

    Dos mitades. La primera -que la regla siga ahi, sin duplicarse mas floja- no alcanza
    sola: se probo rompiendola con una frase nueva agregada AL LADO de la regla, sin
    tocarla, y el primer diseño de este test no lo vio -paso en verde con la excepcion ya
    escrita-. La segunda mitad es la que la atrapa: la seccion que presenta el contrato no
    puede mencionar "cumpl-" en ningun lado, porque su unico trabajo es decir de que
    proyecto se trata, nunca autorizar un veredicto."""
    t.contiene(
        "E-06: la regla sigue exactamente igual",
        "Nunca declares `cumple` sin poder citar la regla con su página y señalar la "
        "línea.", TEXTO)
    t.igual("E-06: la regla aparece una sola vez -no hay una segunda version mas floja",
            1, TEXTO.count("Nunca declares `cumple`"))

    i0 = TEXTO.find("## De qué proyecto estás hablando")
    i1 = TEXTO.find("\n## ", i0 + 1)
    seccion_contrato = TEXTO[i0:i1 if i1 != -1 else len(TEXTO)]
    # La seccion SI menciona "cumple" una vez, a proposito: la frase que reafirma que la
    # linea del archivo sigue haciendo falta. Pin al conteo de hoy -no a la ausencia
    # total- para que una SEGUNDA mencion -una excepcion nueva- se note, sin marcar en
    # rojo la frase legitima que ya esta.
    t.contiene(
        "E-06: la seccion reafirma que la linea del archivo sigue haciendo falta",
        "un `cumple` tiene que poder señalar sigue saliendo del archivo real",
        seccion_contrato)
    t.igual(
        "E-06: 'cumpl' aparece en la seccion del contrato exactamente una vez -la "
        "reafirmacion de arriba, ninguna excepcion nueva al lado",
        1, seccion_contrato.lower().count("cumpl"))


def test_e07_sigue_sin_herramienta_de_ejecucion(t):
    """E-07 — dev-refutador sigue sin Bash, PowerShell ni ninguna herramienta de
    ejecucion en su frontmatter: lee el contrato, no lo valida corriendo nada."""
    m = re.search(r"^tools:\s*(.+)$", TEXTO, re.MULTILINE)
    t.verdadero("E-07: el frontmatter declara tools", m is not None)
    herramientas = [h.strip() for h in m.group(1).split(",")] if m else []
    t.igual("E-07: son exactamente las cuatro de siempre",
            ["Read", "Grep", "Glob", "Skill"], herramientas)
    for prohibida in ("Bash", "PowerShell", "Write", "Edit"):
        t.verdadero("E-07: no tiene %s" % prohibida, prohibida not in herramientas)
