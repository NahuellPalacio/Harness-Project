"""El Host Adapter de Claude Code: una sesion headless, `claude -p`, con salida estructurada.

docs/cambios/minimal-execution-engine/spec.md, MD-08 a MD-10 y MD-18, enmendados en §34 (MD-08′,
MD-10′, MD-18′, MD-19′, MD-22′). docs/cambios/graph-execution/spec.md, GD-21: `provee` conoce la
plataforma.

    resolver_agente   la definicion del agente en el Host, antes de la entrega
    provee            que capabilities de la unidad le puede dar al agente, en esta plataforma
    entregar          lanza el Host, espera y devuelve (informe, falla, como)

🔴 HARNESS lanza el Host, nunca un modelo: el agente y el modelo los corre Claude Code. Nunca con
`--bare` ni salteando permisos, y la configuracion no puede meter esas banderas (MD-22′): los hooks
del proyecto, la SecretGate y la compuerta del flujo, siguen activos durante la corrida.

🔴 El agente se materializa con su propio texto como prompt de sistema (`prompt-de-sistema.md`
del registro de la Execution), sin `--agent`: con
`--agent`, Claude Code toma las herramientas del `tools:` del agente y no suma `StructuredOutput`,
y el AgentReport no llega (§34.2). `--tools` y `--allowedTools` llevan el conjunto minimo de la
unidad, y `--strict-mcp-config` saca las herramientas MCP que el Host suma por su cuenta.

🔴 El AgentReport sale solo de `structured_output`, que el Host valida contra un schema. El campo
`result` no se lee nunca, aunque diga COMPLETE, y el `artifact` es texto opaco: nadie interpreta
texto (T3 D8).

🔴 Lo que no se reconoce es HOST_FAILURE. El adaptador no adivina.
"""
import io
import json
import os
import re
import shutil
import sys
import tempfile
import uuid

from . import contrato
from . import proceso
from . import registro

KIND = "claude-code"
# El texto del agente que el Host recibe como prompt de sistema: un archivo mas del registro de la
# Execution, escrito una sola vez al entregar (MD-08′).
PROMPT_DE_SISTEMA = "prompt-de-sistema.md"

# Capability -> herramientas del Host. Las cuatro capacidades locales, y ninguna mas: las de
# integracion (jira.*, gitlab.*) el adaptador no las provee (MD-18, EC-08).
HERRAMIENTAS = {
    "repository.read": ("Read", "Glob", "Grep"),
    "repository.search": ("Grep", "Glob"),
    "repository.write": ("Edit", "Write"),
    "tests.run": ("Bash",),
}
SKILL = "Skill"

# Las herramientas que el Host no ofrece en una plataforma aunque se las pidan, y aunque el agente las
# tenga en su `tools:` (GD-21, R5). Un hecho observado de Claude Code: en Windows la sesion no trae
# `Bash`. Medido el 09-10-2026 con 2.1.295 (T4 §34.2, E8) y comprobado de nuevo el 13-10-2026 con
# 2.1.296 (`--tools Read,Bash` da solo `Read`). Envejece con una version nueva del Host: no se
# descubre a la corrida, se corrige aca, con fecha. `herramientas` no la mira (ME-E40): una unidad
# que `provee` rechazo nunca llega a armar `--tools`.
NO_OFRECIDAS = {"win32": ("Bash",)}

# Las banderas que arma el adaptador o que tocan la seguridad de la sesion. La configuracion no
# puede traer ninguna, ni como `--opcion=valor`, ni con otras mayusculas (MD-22′).
RESERVADAS = ("--print", "--agent", "--agents", "--output-format", "--json-schema", "--session-id",
              "--tools", "--allowedtools", "--allowed-tools", "--disallowedtools",
              "--disallowed-tools", "--permission-mode", "--permission-prompts", "--model",
              "--system-prompt", "--system-prompt-file", "--append-system-prompt",
              "--append-system-prompt-file", "--settings", "--setting-sources", "--bare",
              "--mcp-config", "--strict-mcp-config",
              "--dangerously-skip-permissions", "--allow-dangerously-skip-permissions")
# Lo que nunca puede aparecer, en ningun lugar de un argumento.
PROHIBIDOS = ("dangerously", "bypasspermissions")
# Un nombre de modelo conservador: sin `-` adelante, sin espacios. No es una lista de modelos.
MODELO = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@/\[\]-]{0,127}")

EXITO = "success"
SIN_SALIDA_VALIDA = "error_max_structured_output_retries"
# Los subtype que el adaptador conoce por su nombre: los puede decir el motor. Otro es texto del
# Host (MD-19′).
SUBTIPOS = (EXITO, SIN_SALIDA_VALIDA, "error_max_turns", "error_during_execution")
# 130 es SIGINT y 143 SIGTERM, los codigos documentados de un Host cortado desde afuera; en POSIX
# un hijo muerto por una senal sale con un codigo negativo.
CORTADO = (130, 143)
# El proveedor se identifica asi en el resultado real de Claude Code (§34.2, ME-E50).
FALLA_DE_API = "api_error"

NOMBRE = re.compile(r"dev-[a-z0-9-]+")
TOPE_DE_STDERR = 1 << 20


def esquema_del_informe():
    """El schema del AgentReport que valida el Host: dos claves, ninguna de mas."""
    return {"type": "object", "additionalProperties": False,
            "required": list(contrato.CLAVES_DEL_INFORME),
            "properties": {"declaredStatus": {"type": "string",
                                              "enum": list(contrato.DECLARACIONES_DEL_AGENTE)},
                           "artifact": {"type": "string"}}}


def esquema_en_argv():
    """El schema como un argumento: JSON compacto, sin espacios ni caracteres que `cmd`
    interprete, para que llegue intacto a traves de un shim .cmd en Windows (ME-19)."""
    texto = json.dumps(esquema_del_informe(), sort_keys=True, separators=(",", ":"))
    if re.search(r"[\s&|<>^%]", texto):
        raise ValueError("el schema del AgentReport no puede ir por argv: %s" % texto)
    return texto


# -- la configuracion (MD-22′) ---------------------------------------------------------------

def argumento_reservado(argumento):
    """Si un argumento de `comandoHost` es, o mete, una bandera que no le toca a la configuracion."""
    texto = argumento.strip().lower()
    if texto == "--" or any(p in texto for p in PROHIBIDOS):
        return True
    if re.search(r"(^|[\s\"'])-[^-\s]", texto):
        return True
    return any(re.search(r"(^|[\s\"'])" + re.escape(r) + r"($|[=\s])", texto) or
               texto.split("=", 1)[0].startswith(r) for r in RESERVADAS)


def comando_invalido(comando):
    """Por que `ejecucion.comandoHost` no se puede usar, o None. No mira si el programa existe."""
    if not isinstance(comando, list) or not comando or not all(
            isinstance(c, str) and c.strip() for c in comando):
        return ("tiene que ser una lista no vacia de textos no vacios: el programa y sus primeros "
                "argumentos")
    if comando[0].strip().startswith("-"):
        return "el programa no puede empezar con -"
    reservados = [c for c in comando[1:] if argumento_reservado(c)]
    if reservados:
        return ("los argumentos no pueden traer banderas del adaptador ni de seguridad, ni "
                "opciones cortas (%d rechazado(s))" % len(reservados))
    return None


def perfiles_invalidos(perfiles):
    """Por que `modelRouting.perfiles` no se puede usar, o None. Vacio o null es no declarado."""
    if perfiles is None:
        return None
    if not isinstance(perfiles, dict):
        return "tiene que ser un objeto"
    for tier, valor in sorted(perfiles.items(), key=lambda par: str(par[0])):
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            continue
        if not isinstance(valor, str) or not MODELO.fullmatch(valor.strip()):
            return ("el perfil de %s no es un nombre de modelo: empieza con letra o digito, sin "
                    "espacios, y no puede ser una bandera" % tier)
    return None


def _frente(texto):
    """({clave: valor} del frente `---` de un archivo de agente, cuerpo), o (None, None)."""
    lineas = texto.replace("\r\n", "\n").split("\n")
    if not lineas or lineas[0].strip() != "---":
        return None, None
    campos = {}
    for i, linea in enumerate(lineas[1:], 1):
        if linea.strip() == "---":
            return campos, "\n".join(lineas[i + 1:]).strip("\n") + "\n"
        if ":" in linea and not linea.startswith((" ", "\t")):
            clave, valor = linea.split(":", 1)
            campos[clave.strip()] = valor.strip()
    return None, None


class Adaptador(object):
    """El Host Adapter. `comando` es la lista ya resuelta y validada de `ejecucion.comandoHost`,
    o lo que dio `shutil.which("claude")`; `limite`, los segundos de `ejecucion.limiteSegundos`;
    `perfiles`, el `modelRouting.perfiles` de harness.config.json. Levanta ValueError si el comando
    o los perfiles traen algo que no les toca (MD-22′): la misma regla que la configuracion.

    `plataforma` es la del Host (`sys.platform` por defecto): se inyecta para probar las dos ramas
    de `provee` en cualquier maquina (GD-21). Un valor que no es un texto no vacio es un ValueError."""

    def __init__(self, comando, limite, perfiles=None, plataforma=None):
        motivo = comando_invalido(list(comando)) or perfiles_invalidos(perfiles)
        if motivo:
            raise ValueError(motivo)
        if plataforma is not None and not (isinstance(plataforma, str) and plataforma.strip()):
            raise ValueError("la plataforma tiene que ser un texto no vacio")
        self.comando = list(comando)
        self.limite = limite
        self.perfiles = perfiles if isinstance(perfiles, dict) else {}
        self.plataforma = plataforma if plataforma is not None else sys.platform

    # -- antes de la entrega ----------------------------------------------------------------

    def resolver_agente(self, proyecto, agente):
        """({ruta, tools, cuerpo}, None) o (None, motivo): `.claude/agents/<agente>.md`, con ese
        `name:` y un cuerpo, que es lo que se le da al Host como prompt de sistema."""
        if not isinstance(agente, str) or not NOMBRE.fullmatch(agente):
            return None, "%r no es el nombre de un agente" % (agente,)
        ruta = os.path.join(proyecto, ".claude", "agents", agente + ".md")
        try:
            with io.open(ruta, encoding="utf-8-sig") as f:
                frente, cuerpo = _frente(f.read())
        except OSError:
            return None, "el Host no tiene la definicion de %s: falta .claude/agents/%s.md" % (
                agente, agente)
        if frente is None or frente.get("name") != agente:
            return None, ".claude/agents/%s.md no declara `name: %s`" % (agente, agente)
        if not cuerpo.strip():
            return None, ".claude/agents/%s.md no tiene el texto del agente" % agente
        herramientas = [h.strip() for h in (frente.get("tools") or "").split(",") if h.strip()]
        return {"ruta": ".claude/agents/%s.md" % agente, "tools": herramientas,
                "cuerpo": cuerpo}, None

    def provee(self, capacidades, definicion):
        """Las capabilities de la unidad que el adaptador no le puede dar al agente.

        Una no se da si el Host no ofrece su herramienta en esta plataforma (GD-21), aunque el agente
        la tenga en su `tools:`; si no es una de las cuatro locales; o si al agente le falta alguna de
        sus herramientas. La primera razon va con su explicacion, que la admision junta tal cual en el
        `detail` del rechazo: el id de la capability y, entre parentesis, que herramienta no se ofrece
        y en que plataforma. Las otras dos, con el id solo."""
        tiene = set((definicion or {}).get("tools") or [])
        ausentes = NO_OFRECIDAS.get(self.plataforma, ())
        faltan = []
        for c in capacidades:
            herramientas = HERRAMIENTAS.get(c)
            if herramientas is None:
                faltan.append(c)
            elif any(h in ausentes for h in herramientas):
                faltan.append("%s (el Host no ofrece %s en %s)" % (
                    c, ", ".join(h for h in herramientas if h in ausentes), self.plataforma))
            elif not set(herramientas) <= tiene:
                faltan.append(c)
        return faltan

    def herramientas(self, capacidades, definicion):
        """`--tools` y `--allowedTools`: las de las capabilities, solo las que el agente tiene, y
        Skill. El Host suma `StructuredOutput` por `--json-schema`."""
        tiene = (definicion or {}).get("tools") or []
        pedidas = set(h for c in capacidades for h in HERRAMIENTAS.get(c, ()))
        salida = [h for h in tiene if h in pedidas]
        if SKILL in tiene and SKILL not in salida:
            salida.append(SKILL)
        return salida

    def modelo(self, unidad):
        """El perfil declarado para el tier de la unidad, o None: decide el Host."""
        tier = ((unidad or {}).get("modelPolicy") or {}).get("requiredTier")
        valor = self.perfiles.get(tier) if isinstance(tier, str) else None
        return valor.strip() if isinstance(valor, str) and valor.strip() else None

    # -- la entrega -------------------------------------------------------------------------

    def nueva_sesion(self):
        """La correlacion con el Host, que va a `entrega.json` antes de lanzarlo."""
        return {"kind": KIND, "sessionRef": str(uuid.uuid4()), "runRef": None}

    def argumentos(self, request, definicion, host, prompt_de_sistema):
        """Los argumentos de MD-08′. `prompt_de_sistema` es la ruta del archivo con el cuerpo del
        agente."""
        unidad = request["workUnit"]
        herramientas = ",".join(self.herramientas(unidad["requiredCapabilities"], definicion))
        salida = self.comando + [
            "-p",
            "--output-format", "json",
            "--json-schema", esquema_en_argv(),
            "--session-id", host["sessionRef"],
            "--permission-mode", "dontAsk",
            "--permission-prompts", "none",
            "--system-prompt-file", prompt_de_sistema,
            "--tools", herramientas,
            "--allowedTools", herramientas,
            # `--tools` no alcanza a las herramientas MCP (los conectores de la cuenta, el
            # `.mcp.json`): sin esto la sesion las ofrece igual (§34.2, E9).
            "--strict-mcp-config",
        ]
        modelo = self.modelo(unidad)
        if modelo is not None:
            salida += ["--model", modelo]
        return salida

    def prompt(self, request):
        """La primera linea vincula la sesion a la tarea por el hook que ya existe (MD-17)."""
        clave = request["taskKey"]
        unidad = request["workUnit"]
        return "\n".join([
            "Seguimos con %s." % clave,
            "",
            "Trabajás una sola WorkUnit del plan de la tarea, la que sigue, tal como está en el "
            "plan. Viaja sola: no hay otra.",
            "",
            "```json",
            json.dumps(unidad, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "Cuando termines, devolvé tu resultado en la salida estructurada, con dos claves:",
            "- `declaredStatus`: el `status` de tu bloque `agentResult`: COMPLETE, PARTIAL, "
            "BLOCKED o FAILED;",
            "- `artifact`: tu informe entero, con el bloque `agentResult`.",
            "",
            "Tu resultado lo recibe el motor de ejecución de HARNESS (`dev-harness.py ejecutar`), "
            "no `dev-orchestrator`. No escribas nada bajo `.claude/`.",
            "",
        ])

    def entregar(self, proyecto, request, carpeta, definicion, host, cancelada, al_lanzar=None):
        """(informe, None, como) si hubo un AgentReport valido; (None, falla, como) si no.

        `falla` es {code, motor, host}: el codigo de corrida, un texto hecho solo por el motor, y
        el texto del Host (stderr, un subtype desconocido, `terminal_reason`, un mensaje de
        validacion del payload) entero y sin redactar: lo redacta el motor antes de recortarlo
        (MD-19′). `como` es TERMINO, VENCIDO, CANCELADO o INTERRUMPIDO: lo que decide el motor con
        un pedido de cancelar es suyo (MD-24).

        `carpeta` es la de la Execution. Ahi va, una sola vez, `prompt-de-sistema.md`: el cuerpo del
        agente, que es lo que el Host recibe como prompt de sistema (MD-08′). El prompt, stdout y
        stderr van a temporales anonimos del sistema: en Windows un temporal abierto por el Host no
        se puede leer, y adentro del registro trabaria a quien lo recorre.
        """
        sistema = os.path.join(carpeta, PROMPT_DE_SISTEMA)
        registro.escribir_una_vez(sistema, ((definicion or {}).get("cuerpo") or "").encode("utf-8"))
        argumentos = self.argumentos(request, definicion, host, sistema)
        # Temporales anonimos del sistema, como flujo/repositorio.py: no quedan en el registro, y
        # se borran solos aunque el motor muera.
        with tempfile.TemporaryFile() as entrada, tempfile.TemporaryFile() as salida, \
                tempfile.TemporaryFile() as error:
            entrada.write(self.prompt(request).encode("utf-8"))
            entrada.flush()
            entrada.seek(0)
            try:
                hijo = proceso.lanzar(argumentos, proyecto, entrada, salida, error)
            except (OSError, ValueError) as e:
                return None, _falla("HOST_FAILURE", "el Host no arranco (%s)" % type(e).__name__,
                                    None), proceso.TERMINO
            if al_lanzar is not None:
                al_lanzar(hijo.pid)
            como, codigo = proceso.esperar(hijo, self.limite, cancelada)
            if como == proceso.VENCIDO:
                return None, _falla("TIMEOUT", "el Host no termino en %d s "
                                    "(ejecucion.limiteSegundos)" % self.limite, None), como
            if como != proceso.TERMINO:
                return None, None, como
            salida.seek(0)
            crudo = salida.read()
            error.seek(0)
            stderr = error.read(TOPE_DE_STDERR).decode("utf-8", "replace").strip() or None
        informe, falla = interpretar(crudo, codigo, stderr)
        return informe, falla, proceso.TERMINO


def _falla(codigo, motor, host):
    return {"code": codigo, "motor": motor, "host": host}


def _resultado(crudo):
    """El objeto `type: result` de stdout, o None."""
    texto = crudo.decode("utf-8", "replace").strip()
    for candidato in [texto] + [l for l in reversed(texto.splitlines()) if l.strip()]:
        try:
            doc = json.loads(candidato)
        except ValueError:
            continue
        if isinstance(doc, dict) and doc.get("type") == "result":
            return doc
    return None


def _del_proveedor(doc):
    """Si el resultado identifica una falla de la API del proveedor (§34.2)."""
    estado = doc.get("api_error_status")
    return doc.get("terminal_reason") == FALLA_DE_API or (
        isinstance(estado, int) and not isinstance(estado, bool))


def _texto_del_host(doc, stderr, extra=None):
    """Lo que vino del Host, junto y sin recortar: el motor lo redacta y despues lo recorta."""
    partes = [extra] if extra else []
    subtipo = doc.get("subtype") if doc else None
    if subtipo is not None and subtipo not in SUBTIPOS:
        partes.append("subtype=%s" % subtipo)
    for campo in ("terminal_reason", "api_error_status", "api_error_code", "api_error"):
        if doc and doc.get(campo) not in (None, ""):
            partes.append("%s=%s" % (campo, doc.get(campo)))
    if stderr:
        partes.append("stderr: %s" % stderr)
    return " · ".join(str(p) for p in partes) or None


def interpretar(crudo, codigo, stderr=None):
    """(informe, None) o (None, falla), de la salida de un Host que termino (MD-10′).

    Un codigo de salida distinto de 0 nunca da un informe (ME-I32). El texto del motor dice solo lo
    que el motor conoce por su nombre: el codigo, un subtype conocido, el codigo de salida."""
    doc = _resultado(crudo)
    cortado = codigo in CORTADO or (isinstance(codigo, int) and codigo < 0)
    if doc is None:
        if cortado:
            return None, _falla("HOST_INTERRUPTED", "el Host termino por una senal (codigo de "
                                "salida %s), sin resultado" % codigo, _texto_del_host(None, stderr))
        return None, _falla("HOST_FAILURE", "el Host termino con codigo %s sin un resultado "
                            "JSON legible" % codigo, _texto_del_host(None, stderr))
    subtipo = doc.get("subtype")
    texto_motor = "subtype=%s, codigo de salida %s" % (
        subtipo if subtipo in SUBTIPOS else "otro", codigo)
    host = _texto_del_host(doc, stderr)
    if codigo != 0:
        if _del_proveedor(doc):
            return None, _falla("PROVIDER_FAILURE", "el proveedor fallo (%s)" % texto_motor, host)
        if cortado:
            return None, _falla("HOST_INTERRUPTED", "el Host termino por una senal (%s)"
                                % texto_motor, host)
        return None, _falla("HOST_FAILURE", "el Host termino con un codigo de salida distinto de "
                            "0 (%s)" % texto_motor, host)
    if subtipo == EXITO and doc.get("is_error") is not True:
        informe = doc.get("structured_output")
        if not isinstance(informe, dict):
            return None, _falla("OUTPUT_INVALID", "el Host no devolvio structured_output (%s)"
                                % texto_motor, None)
        errores = contrato.validar_informe(informe)
        if errores:
            return None, _falla("OUTPUT_INVALID", "el AgentReport no valida",
                                _texto_del_host(None, None, "; ".join(errores)))
        return {"declaredStatus": informe["declaredStatus"], "artifact": informe["artifact"]}, None
    if subtipo == SIN_SALIDA_VALIDA:
        return None, _falla("OUTPUT_INVALID", "el Host no logro una salida que valide (%s)"
                            % texto_motor, host)
    if doc.get("is_error") is True and _del_proveedor(doc):
        return None, _falla("PROVIDER_FAILURE", "el proveedor fallo (%s)" % texto_motor, host)
    return None, _falla("HOST_FAILURE", "el Host termino con error (%s)" % texto_motor, host)


def comando_por_defecto():
    """`claude` del PATH, o None."""
    return shutil.which("claude")
