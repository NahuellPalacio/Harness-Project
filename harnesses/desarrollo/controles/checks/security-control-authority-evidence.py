"""Check normativo: la seguridad de este alcance la controla un organismo del GCABA.

    source: ES0902 / 6.2 / 3 / O2

Contesta sobre **quien responde**, no sobre que se hizo. La pregunta no es "el harness corre
controles de seguridad" -los corre- sino "la responsabilidad del control de seguridad de este
alcance esta asignada a un organismo del que CONSTA que es del GCABA".

🔴 **Autoridad no es ejecucion, y este modulo solo mira una.** Un proveedor que escanea, un equipo
que remedia, un agente que prepara la evidencia: los tres hacen seguridad y ninguno responde por
ella. Este check no tiene ningun campo de ejecutor y no lo va a tener — asi "quien ejecuta no puede
volverse quien responde" es una propiedad de la forma del archivo y no una costumbre que alguien
tenga que acordarse de respetar.

🔴 **El harness no puede ser la autoridad.** Ni `dev-security`, ni sus skills, ni un escaner, ni un
job de CI, ni el dueno del repositorio. Adentro de este archivo no hay -y no va a haber- el nombre
de ningun agente: no existe camino de un id de agente a una autoridad.

🔴 **La pertenencia al GCABA no se deduce.** Ni del nombre del organismo, ni del dominio de un
correo, ni del namespace del repositorio, ni del texto del proyecto, ni del empleador que alguien
declara, ni de la red. `gcabaMembership: VERIFIED` es una ETIQUETA que escribe quien edita el
archivo; lo que la establece es evidencia de una de las seis clases autoritativas. Sin eso,
`GCABA_MEMBERSHIP_UNRESOLVED`.

🔴 **No hay orden entre los tipos de alcance.** `GLOBAL` no contiene a `PROJECT` y `PROJECT` no
contiene a `APPLICATION`: la contencion la declara el objetivo en su cadena `within`. Un orden
implicito es exactamente como la autoridad de un proyecto termina cubriendo a otro.

🔴 **Sin fecha de fin no hay vigencia.** Ausente o nula no es "para siempre": es una autoridad
sobre la que nadie dijo hasta cuando, y es la que lleva anios sin que nadie mire.

🔴 **Falta de evidencia NUNCA es FAIL.** `FAIL` tiene un unico camino: consta que la autoridad
controlante es ajena al GCABA y no hay ningun organismo del GCABA controlando ese alcance. Un
`FAIL` inventado acusa a un organismo de algo que nadie probo.

🔴 **PASS no aprueba nada mas.** No es la evaluacion de seguridad aprobada, no es C2, no son
vulnerabilidades aceptadas y no es la homologacion de DGSEI. Es una sola cosa: que el requisito
organizacional de O2 tiene evidencia.

📌 **Este check no lee el binding de la matriz.** O2 es `ALWAYS` con cero senales, asi que no hay
ninguna senal que preguntar — a diferencia de D8, que depende de una y por eso lo lee. Agregar la
lectura seria agregar un estado de error que el paquete no declara.
"""
import io
import json
import os
import re
import sys

_BIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_BIN, "bin") not in sys.path:
    sys.path.insert(0, os.path.join(_BIN, "bin"))

import rutas                                        # noqa: E402
from orquestacion import roster as _roster          # noqa: E402

CONTROL = "security-control-authority-evidence"
TIPO = "CHECK"
REGLA = "O2"
CLAVE = "ES0902.O2"

ARCHIVO = "security-control-authority.json"
SCHEMA = "security-control-authority.schema.json"

TRAZA = {"standard": "ES0902", "version": "6.2", "section": "3", "rule": REGLA}

# -- los nueve estados, con el nombre exacto que declara el paquete ------------

PASA = "PASS"
FALLA = "FAIL"
SIN_AUTORIDAD = "SECURITY_CONTROL_AUTHORITY_UNRESOLVED"
SIN_PERTENENCIA = "GCABA_MEMBERSHIP_UNRESOLVED"
SIN_ALCANCE = "SECURITY_AUTHORITY_SCOPE_UNRESOLVED"
SIN_VIGENCIA = "SECURITY_AUTHORITY_CURRENT_STATUS_UNRESOLVED"
VENCIDA = "SECURITY_AUTHORITY_EVIDENCE_EXPIRED"
EN_CONFLICTO = "CONFLICTING_SECURITY_AUTHORITY_EVIDENCE"
INSUFICIENTE = "AUTHORITY_EVIDENCE_INSUFFICIENT"

# Nueve, y el unico que aprueba es PASA. Los otros ocho dicen cosas distintas y ninguno cumple.
ESTADOS = (PASA, FALLA, SIN_AUTORIDAD, SIN_PERTENENCIA, SIN_ALCANCE, SIN_VIGENCIA, VENCIDA,
           EN_CONFLICTO, INSUFICIENTE)

# Los siete que no aprueban y no acusan: son lo que falta, no un veredicto contra nadie.
SIN_RESOLVER = (SIN_AUTORIDAD, SIN_PERTENENCIA, SIN_ALCANCE, SIN_VIGENCIA, VENCIDA,
                EN_CONFLICTO, INSUFICIENTE)

# -- lo que cuenta como controlar, y lo que no --------------------------------

# 🔴 UNA sola, y es la que la regla nombra. Una taxonomia de responsabilidades de seguridad que
# ES0902 no da seria normativa inventada, y cada valor de mas es una puerta de entrada.
CONTROL_DE_SEGURIDAD = "SECURITY_CONTROL"
RESPONSABILIDADES_DE_CONTROL = (CONTROL_DE_SEGURIDAD,)

# Las cinco formas de ejecucion que el paquete nombra. No cuentan, y estan escritas para que el
# motivo pueda decir POR QUE no cuentan en vez de decir solo que no.
RESPONSABILIDADES_DE_EJECUCION = ("SECURITY_SCANNING", "SECURITY_REMEDIATION", "DEVELOPMENT",
                                  "HOSTING", "CONSULTING")

# -- la pertenencia -----------------------------------------------------------

DEL_GCABA = "VERIFIED"
PERTENENCIA_SIN_RESOLVER = "UNRESOLVED"
AJENA = "NOT_GCABA"
PERTENENCIAS = (DEL_GCABA, PERTENENCIA_SIN_RESOLVER, AJENA)

# Las seis clases autoritativas. Un archivo del harness, la afirmacion de un agente, un README o
# una etiqueta escrita a mano no son ninguna de las seis, y por eso no entran.
CLASES_DE_EVIDENCIA = ("OFFICIAL_GCBA_DOCUMENT", "OFFICIAL_GCBA_ORGANIZATIONAL_SOURCE",
                       "OFFICIAL_SECURITY_WORKFLOW", "PROJECT_CONTRACT_OR_ACTA",
                       "ASI_DGSEI_PROJECT_EVIDENCE", "OTHER_AUTHORITATIVE_GCBA_SOURCE")

# -- el alcance ---------------------------------------------------------------

TIPOS_DE_ALCANCE = ("GLOBAL", "PROJECT", "SYSTEM", "APPLICATION", "COMPONENT", "ASSESSMENT")

# -- las fechas ---------------------------------------------------------------

# `YYYY-MM-DD` y nada mas. En ese formato el orden de texto es el orden cronologico, asi que no
# hace falta interpretar una fecha para compararla — y lo que no cumple el formato no se
# interpreta: queda sin resolver.
FECHA = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


# -- el registro --------------------------------------------------------------

def cargar(desde=None):
    """El registro del proyecto. Vacio si no esta: un proyecto sin autoridad declarada es valido
    y resuelve `SECURITY_CONTROL_AUTHORITY_UNRESOLVED`, que no es ni aprobar ni reprobar."""
    ruta = _roster.ruta_de_regla(ARCHIVO, desde or __file__)
    if ruta is None:
        return {"version": "0.0", "authorities": []}
    try:
        with io.open(ruta, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def validar_schema(doc, desde=None):
    """Errores contra el contrato. Vacio es valido; `None` es que no se pudo validar."""
    ruta = rutas.localizar(("schemas", SCHEMA), desde or __file__)
    if ruta is None:
        return None
    armador = _armador(desde)
    if armador is None:
        return None
    with io.open(ruta, encoding="utf-8") as f:
        esquema = json.load(f)
    armador.controlar_soporte(esquema)
    return armador.validar(doc, esquema)


def _armador(desde=None):
    from orquestacion import tools
    return tools._armador()


def autoridades(caso, desde=None):
    """(lista, problema). Las del caso si vienen; si no, las del registro instalado."""
    declaradas = (caso or {}).get("authorities")
    if declaradas is not None:
        doc = {"version": "1.0", "authorities": declaradas}
    else:
        doc = cargar(desde)
        if doc is None:
            return [], "el registro de autoridades no se pudo leer"
    errores = validar_schema(doc, desde)
    if errores:
        return [], "el registro de autoridades no valida: %s" % "; ".join(errores)
    return [a for a in (doc.get("authorities") or []) if isinstance(a, dict)], ""


# -- las cuatro preguntas sobre un registro -----------------------------------

def identidad(autoridad):
    """Si el registro identifica a alguien. Una etiqueta en blanco no identifica a nadie."""
    org = (autoridad or {}).get("organization") or {}
    return bool((autoridad or {}).get("authorityId")) and bool((org.get("name") or "").strip())


def controla(autoridad):
    """Si la responsabilidad declarada es la de control. Ejecutar no es controlar."""
    declaradas = [r for r in (autoridad or {}).get("responsibilities") or []
                  if isinstance(r, str)]
    return any(r in RESPONSABILIDADES_DE_CONTROL for r in declaradas)


def _evidencias(autoridad):
    """Las evidencias de una clase autoritativa que traen su referencia."""
    return [e for e in (autoridad or {}).get("evidence") or []
            if isinstance(e, dict) and e.get("sourceType") in CLASES_DE_EVIDENCIA
            and (e.get("reference") or "").strip()]


def pertenencia(autoridad):
    """`VERIFIED`, `NOT_GCABA` o sin resolver, y la etiqueta NO alcanza sola.

    🔴 `gcabaMembership: VERIFIED` lo escribe quien edita el archivo. Sin al menos una evidencia
    de una de las seis clases autoritativas, la pertenencia queda sin resolver aunque el archivo
    diga que esta verificada.
    """
    declarada = ((autoridad or {}).get("organization") or {}).get("gcabaMembership")
    if declarada == AJENA:
        return AJENA
    if declarada == DEL_GCABA and _evidencias(autoridad):
        return DEL_GCABA
    return PERTENENCIA_SIN_RESOLVER


def vigencia(autoridad, fecha):
    """`""` si rige a esa fecha, o el estado que lo impide.

    🔴 Sin `effectiveTo` no hay vigencia. Ausente o nulo no es "para siempre": es una autoridad
    sobre la que nadie dijo hasta cuando.
    """
    desde_ = (autoridad or {}).get("effectiveFrom")
    hasta = (autoridad or {}).get("effectiveTo")
    if not isinstance(hasta, str) or not FECHA.match(hasta):
        return SIN_VIGENCIA
    if desde_ is not None:
        if not isinstance(desde_, str) or not FECHA.match(desde_):
            return SIN_VIGENCIA
        if desde_ > fecha:
            return SIN_VIGENCIA
    if hasta < fecha:
        return VENCIDA
    return ""


# -- el alcance ---------------------------------------------------------------

def _par(alcance):
    a = alcance if isinstance(alcance, dict) else {}
    tipo, valor = a.get("type"), a.get("value")
    if tipo not in TIPOS_DE_ALCANCE or not isinstance(valor, str) or not valor.strip():
        return None
    return (tipo, valor)


def cadena(objetivo):
    """El alcance del objetivo y los que el objetivo declara que lo contienen, o `None`.

    🔴 La contencion la declara el objetivo. No hay orden entre los seis tipos y `GLOBAL` no es
    una excepcion: una autoridad global cubre a quien la nombra en su cadena, y a nadie mas.
    """
    obj = objetivo if isinstance(objetivo, dict) else {}
    propio = _par(obj.get("scope"))
    if propio is None:
        return None
    salida = [propio]
    for a in obj.get("within") or []:
        par = _par(a)
        if par is not None and par not in salida:
            salida.append(par)
    return salida


def cubre(autoridad, cadena_del_objetivo):
    par = _par((autoridad or {}).get("scope"))
    return par is not None and par in (cadena_del_objetivo or [])


# -- la evaluacion ------------------------------------------------------------

def evaluar(caso, desde=None):
    """El estado de O2 para un alcance, con su motivo, su autoridad y su trazabilidad.

    `caso` es lo que se sabe del objetivo:

        {"target": {"id", "scope": {"type", "value"},
                    "within": [{"type", "value"}]},
         "evaluationDate": "YYYY-MM-DD",
         "authorities": [...]}      # opcional: reemplaza el registro instalado

    🔴 Para un objetivo, una fecha y un registro fijos, esto devuelve siempre lo mismo.

    El orden de las preguntas es: que haya registro, que algo cubra al objetivo, que lo que
    cubre sea control y no ejecucion, que rija a la fecha, de quien es, y si hay dos que se
    contradicen. Cada una filtra, y el estado que sale es el del primer filtro que deja vacio.
    """
    entrada = caso if isinstance(caso, dict) else {}
    objetivo = entrada.get("target") or {}
    salida = {"control": CONTROL, "rule": REGLA, "ruleKey": CLAVE, "source": dict(TRAZA),
              "target": {"id": objetivo.get("id"), "scope": objetivo.get("scope")},
              "evaluationDate": entrada.get("evaluationDate"),
              "authority": None, "considered": [], "issues": []}

    fecha = entrada.get("evaluationDate")
    if not isinstance(fecha, str) or not FECHA.match(fecha):
        return _con(salida, SIN_VIGENCIA,
                    "sin una fecha de evaluacion en formato YYYY-MM-DD no se puede establecer "
                    "si una autoridad rige")

    cadena_ = cadena(objetivo)
    if cadena_ is None:
        return _con(salida, SIN_ALCANCE,
                    "el objetivo no declara un alcance con un tipo de los seis y un valor")
    salida["scopeChain"] = [{"type": t, "value": v} for t, v in cadena_]

    registro, problema = autoridades(entrada, desde)
    if problema:
        return _con(salida, SIN_AUTORIDAD, problema)
    if not registro:
        return _con(salida, SIN_AUTORIDAD,
                    "no hay ninguna autoridad de control declarada para este proyecto")

    alcanzan = [a for a in registro if cubre(a, cadena_)]
    salida["considered"] = [{"authorityId": a.get("authorityId"),
                             "organization": ((a.get("organization") or {}).get("name")),
                             "scope": a.get("scope"),
                             "covers": a in alcanzan} for a in registro]
    if not alcanzan:
        return _con(salida, SIN_ALCANCE,
                    "ninguna autoridad declarada cubre este alcance, y la contencion la declara "
                    "el objetivo: una autoridad mas ancha cubre solo si el objetivo la nombra")

    identificadas = [a for a in alcanzan if identidad(a)]
    if not identificadas:
        return _con(salida, INSUFICIENTE,
                    "la autoridad que cubre este alcance no identifica a ninguna organizacion")

    controlantes = [a for a in identificadas if controla(a)]
    if not controlantes:
        ejecutan = sorted({r for a in identificadas
                           for r in a.get("responsibilities") or []
                           if r in RESPONSABILIDADES_DE_EJECUCION})
        return _con(salida, INSUFICIENTE,
                    "ninguna autoridad que cubre este alcance declara `%s`%s; ejecutar no es "
                    "controlar" % (CONTROL_DE_SEGURIDAD,
                                   (" y si %s" % ", ".join(ejecutan)) if ejecutan else ""))

    vigentes, vencidas = [], []
    for a in controlantes:
        estado = vigencia(a, fecha)
        if estado == VENCIDA:
            vencidas.append(a)
        elif not estado:
            vigentes.append(a)
    if not vigentes:
        if vencidas:
            return _con(salida, VENCIDA,
                        "la autoridad de control vencio el %s y la evaluacion es del %s"
                        % (vencidas[0].get("effectiveTo"), fecha))
        return _con(salida, SIN_VIGENCIA,
                    "no consta hasta cuando rige la autoridad de control: una asignacion sin "
                    "fecha de fin no es una asignacion vigente")

    # 🔴 El conflicto se mira ANTES de mirar de quien es. Dos organizaciones distintas
    # controlando el mismo objetivo no se resuelven eligiendo la que convenga.
    organizaciones = sorted({_org(a) for a in vigentes})
    if len(organizaciones) > 1:
        return _con(salida, EN_CONFLICTO,
                    "dos organizaciones distintas declaran controlar este alcance y ninguna "
                    "evidencia dice cual rige: %s" % ", ".join(organizaciones))

    propias = [a for a in vigentes if pertenencia(a) == DEL_GCABA]
    ajenas = [a for a in vigentes if pertenencia(a) == AJENA]
    if propias:
        elegida = propias[0]
        salida["authority"] = _resumen(elegida)
        return _con(salida, PASA, "")
    if ajenas:
        # 🔴 El unico camino a FAIL: consta que la controlante es ajena y no hay ninguna del
        # GCABA controlando este alcance.
        salida["authority"] = _resumen(ajenas[0])
        return _con(salida, FALLA,
                    "la unica autoridad de control de este alcance es `%s`, que consta ajena al "
                    "GCABA" % _org(ajenas[0]))
    return _con(salida, SIN_PERTENENCIA,
                "no hay evidencia autoritativa de que `%s` pertenezca al GCABA; la etiqueta del "
                "archivo no establece la pertenencia" % _org(vigentes[0]))


def _org(autoridad):
    return ((autoridad or {}).get("organization") or {}).get("name") or "(sin nombre)"


def _resumen(autoridad):
    """Lo que se informa de la autoridad que resuelve. Sin copiar la evidencia entera."""
    org = (autoridad or {}).get("organization") or {}
    return {"authorityId": autoridad.get("authorityId"), "organization": org.get("name"),
            "gcabaMembership": pertenencia(autoridad),
            "responsibilities": list(autoridad.get("responsibilities") or []),
            "scope": autoridad.get("scope"), "effectiveTo": autoridad.get("effectiveTo"),
            "evidence": [{"sourceType": e.get("sourceType"), "reference": e.get("reference")}
                         for e in _evidencias(autoridad)]}


def _con(salida, estado, motivo):
    salida["state"] = estado
    salida["reason"] = motivo
    if motivo:
        salida["issues"].append("%s: %s" % (estado, motivo))
    return salida


def aprueba(resultado):
    """El unico estado que aprueba. Existe para que nadie tenga que acordarse de cual era."""
    return (resultado or {}).get("state") == PASA
