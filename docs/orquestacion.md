# El plan de trabajo de una tarea

Una tarea ya tiene su contexto resuelto. Lo que nadie decidió todavía es qué hacer con ella,
quién debería hacerlo y en qué orden. Eso es el plan.

```powershell
python .claude\harness\bin\desarrollo\dev-harness.py plan GCBA-1234 --plantilla
python .claude\harness\bin\desarrollo\dev-harness.py plan GCBA-1234 --propuesta propuesta.json
```

El plan queda en `.claude/planes/GCBA-1234.json` y valida contra
`comun/schemas/orchestration-plan.schema.json`.

> 🔴 **Este bloque no ejecuta nada.** `READY_FOR_EXECUTION` es un estado del documento, no una
> invocación. Orquestar decide qué, quién, con qué y en qué orden; ejecutar modifica, y eso es
> otro bloque.

## Quién decide qué

El bloque está partido en dos por quién decide, no por qué hace.

```
dev-orchestrator                          el núcleo, en Python
────────────────────────────────          ────────────────────────────────
qué hay que hacer y por qué               qué capacidades hay y cuáles faltan
qué dominios toca la tarea                qué tier de modelo necesita cada unidad
cómo se parte en unidades                 si hace falta aprobación humana
qué señales de complejidad tiene          en qué orden se puede ejecutar
                                          qué contexto ve cada especialista
                                          validar el contrato y versionarlo
```

La costura entre las dos mitades es un archivo: el agente escribe una **propuesta** y el núcleo
la convierte en plan. Sin esa costura, el ruteo de modelo viviría adentro de un prompt y nadie
podría testearlo.

```
.claude/contextos/GCBA-1234.json
        ↓  lo lee dev-orchestrator
    propuesta.json                  objective, domains, workUnits, signals
        ↓  dev-harness.py plan --propuesta
.claude/planes/GCBA-1234.json       capacidades, tiers, política, orden, validado
```

## Una unidad de trabajo

```json
{
  "id": "implementar-endpoint",
  "objective": "Agregar el filtro al endpoint del listado",
  "domain": "backend",
  "assignedAgent": "dev-backend",
  "requiredCapabilities": ["repository.write"],
  "dependencies": ["analizar-api"],
  "signals": ["novelty"]
}
```

Todo lo demás lo completa el núcleo: el agente asignado si no se declaró, las skills y los checks
del dominio, el contexto aislado, el tier de modelo con su motivo y el estado.

## El registro de agentes

Qué agentes y qué skills existen sale de **`reglas/desarrollo/agent-registry.json`**, y de ningún
otro lado. El disco no da de alta nada: diagnostica.

| Capa | Qué contesta |
|---|---|
| el registro | qué agentes y qué skills existen, y en qué estado |
| el disco | huérfanos y skills no declaradas — diagnóstico, nunca alta |
| la matriz normativa | qué reglas, policies y checks aplican |

🔴 **Las tres no se cruzan.** Que la matriz de §7.1 esté sin clasificar no puede hacer que un
agente declarado y válido deje de existir.

Un agente lleva su tipo, y el tipo decide cuántas skills necesita: `ORCHESTRATOR_AGENT`,
`CRITIC_AGENT` e `INFRASTRUCTURE_AGENT` valen con cero; un `SPECIALIST_AGENT` necesita al menos una
`INSTALLED`. No se inventa una skill para que cierre la validación.

Una skill declarada puede estar `INSTALLED`, `DECLARED_NOT_INSTALLED` —con el motivo escrito— o
`DEPRECATED`. Sólo la primera rutea.

### Tres huecos que no son el mismo

```
AGENT_NOT_FOUND         el agente no está declarado
SPECIALIZED_SKILL_GAP   el agente existe; su skill especializada está declarada y todavía no
                        se puede escribir. NO deriva a dev-tool-builder
CAPABILITY_GAP          existe todo, falta una capacidad ejecutable. Este sí deriva
```

`dev-miba` y `dev-esb` son el primer caso de `SPECIALIZED_SKILL_GAP`: falta información
autoritativa de esas integraciones. Pedirle a un constructor de tools que las reemplace sería
pedirle que fabrique conocimiento que nadie tiene.

Se rutea **cerrado**: cualquier estado que no sea `VALID`, `VALID_WITH_PENDING_SKILLS` o
`SKILL_AVAILABLE` devuelve `routable: false`, y nada se repara solo.

## Capacidades, nunca tools

Una unidad pide `repository.read`, no `Glob`. Atar el plan al nombre de una tool lo ata a un
runtime, y el mismo plan deja de servir el día que la capacidad la provea otra cosa.

Se resuelven contra dos fuentes:

| Fuente | Qué trae |
|---|---|
| `.claude/harness.capacidades.json` | Lo que el bootstrap validó contra un servidor |
| `reglas/desarrollo/roster.json` | Lo que da el propio runtime — leer, escribir, correr tests |

Lo que no está en ninguna es un **hueco**, y un hueco se deriva a `dev-tool-builder` con la tool
clasificada `TEMPORARY`. **Nunca se improvisa con una tool parecida.**

## El tier de modelo

Perfiles, nunca nombres: `low_cost`, `standard`, `reasoning`, `premium`. El nombre concreto lo
resuelve el runtime, y un perfil sin modelo declarado es un hueco declarado, no un default.

El principio es **el modelo menos costoso que pueda hacer la unidad de forma confiable**. Por eso
el default es `low_cost` y hay que justificar subir. Lo que justifica son las señales:

| Señal | Peso | Señal | Peso |
|---|---|---|---|
| `ambiguity` | 3 | `capability_gap` | 2 |
| `architectural_impact` | 3 | `needs_tool_creation` | 2 |
| `security_impact` | 3 | `previous_failures` | 2 |
| `novelty` | 2 | `many_components` | 1 |
| `cross_domain` | 2 | `dependency_complexity` | 1 |
| | | `large_context` | 1 |

El motivo que queda escrito nombra las señales, no dice "corresponde": una decisión de consumo que
no se puede discutir no se puede corregir.

**La escalada sube un tier por vez** y deja escrito qué falló y cuántos intentos hubo. Un tier que
se saltea es una decisión de consumo que nadie vio.

## La compuerta humana

`automatic` no significa que el harness pueda usar cualquier modelo automáticamente. Significa que
elige el tier solo, y que los baratos los ejecuta solo.

```json
"consumptionPolicy": {
  "mode": "automatic",
  "autoApprove": ["low_cost", "standard"],
  "requireHumanApproval": ["reasoning", "premium"],
  "sessionBudget": { "premiumCallsAllowed": 0, "maxRetries": 3 }
}
```

Lo que requiere aprobación deja el plan en `WAITING_FOR_HUMAN_APPROVAL` con la solicitud armada:

```
Solicitud de escalamiento de modelo

  Agente:            dev-security
  Unidad de trabajo: analisis-seguridad
  Tier recomendado:  PREMIUM
  Modelo propuesto:  lo resuelve el runtime
  Motivo:            premium: toca seguridad, la tarea es ambigua, toca la arquitectura.
  Consumo esperado:  ALTO
  Alternativa:       reasoning, con menor nivel de confianza en el resultado

  Acciones: APROBAR · USAR LA ALTERNATIVA · CANCELAR
```

> 🔴 **La solicitud siempre trae una alternativa más barata.** Una compuerta que ofrece "aprobar o
> cancelar" fuerza a aprobar: la decisión útil es entre dos formas de hacer la tarea.

El presupuesto preautorizado es la única forma de saltear la pregunta, **y se gasta**: dos llamadas
premium autorizadas son dos, y la tercera vuelve a preguntar.

## El estado se calcula

No lo declara quien arma el plan. Con huecos, un plan no puede decir que está listo.

| Estado | Cuándo |
|---|---|
| `CAPABILITY_RESOLUTION` | Falta una capacidad, o una unidad quedó bloqueada |
| `WAITING_FOR_HUMAN_APPROVAL` | Una unidad necesita un modelo que requiere aprobación |
| `READY_FOR_EXECUTION` | No queda nada pendiente |

## El aislamiento de contexto

Cada especialista ve lo de su dominio, y lo que no ve **queda declarado** en `omitted`. No es una
optimización de tokens: es que una unidad de backend no tenga adelante los criterios de
accesibilidad, porque lo que está adelante se usa.

| Dominio | Ve |
|---|---|
| `backend` | criterios, reglas, documentos, repositorio |
| `frontend` | criterios, documentos |
| `architecture` | reglas, documentos, repositorio |
| `integration` | criterios, reglas, repositorio |
| `devops` | repositorio |
| `quality` | criterios, repositorio |
| `security` | reglas, documentos, repositorio |

## La normativa

Las 26 reglas de ES0901 §7.1 están como dato en `reglas/desarrollo/es0901-7.1.json`, con su id, su
texto y su página. Al lado, `es0901-7.1-normative-matrix.json` clasifica las 24: cuándo aplica cada
una, quién es su dueño, y qué policies y qué checks exige. Los dos archivos se unen por id de regla,
y el citable es el único que se cita: la paráfrasis operativa en inglés sirve para clasificar y no
para citar.

Cada unidad de trabajo lleva su resolución en `normative`:

```json
"normative": {
  "applicableRules": ["G1", "G2", "D1"],
  "notApplicableRules": [],
  "unresolvedRules": [{"rule": "D4", "reason": "APPLICABILITY_UNRESOLVED",
                       "missingSignals": ["frontendPresent"]}],
  "declaredPolicies": ["approved-technology-required", "gcba-citizen-authentication-required"],
  "declaredChecks": ["technology-homologation", "citizen-authentication-mechanism"],
  "declaredReviews": ["technology-practice-review"]
}
```

> 🔴 **Que una policy o un check estén declarados no significa que existan.** Lo que existe lo dice
> el registro de controles, no la matriz. Los que faltan se reportan
> `DECLARED_POLICY_NOT_INSTALLED` y `DECLARED_CHECK_NOT_INSTALLED`, y eso no invalida nada: es el
> estado correcto de un harness que clasificó antes de construir. Hoy están construidos los de
> `G1`, `G2` y `D1`.

## Las señales

Siete de las 24 reglas aplican siempre. Las otras 17 son condicionales: aplican si el trabajo
toca algo en particular —el ciudadano, una base, un frontend, archivos—. Eso lo decide una **señal**.

Una señal no es un booleano:

```json
{
  "signalId": "citizenFacing",
  "value": "TRUE",
  "evidence": [{"evidenceId": "ev-1", "sourceType": "JIRA_FICHA_DE_PROYECTO",
                "reference": "GCBA-1234", "claim": "trámite de inicio para el ciudadano"}],
  "producer": {"type": "HUMAN"}
}
```

Tres valores, y el tercero es el que importa:

```text
TRUE         la regla aplica
FALSE        NOT_APPLICABLE
UNRESOLVED   APPLICABILITY_UNRESOLVED, con la señal que falta escrita al lado
```

> 🔴 **Lo que falta nunca es `FALSE`.** Que nadie haya escrito "ciudadano" en ningún lado no prueba
> que la aplicación no interactúe con el ciudadano: prueba que nadie lo escribió. Convertir lo
> ausente en `FALSE` hace desaparecer la regla del reporte, y una regla que desaparece no se vuelve
> a buscar.

Cuatro reglas más, todas por la misma razón:

- **Sin evidencia no hay valor.** Una señal que afirma `TRUE` o `FALSE` y no cita nada se degrada a
  `UNRESOLVED` con `SIGNAL_EVIDENCE_MISSING`.
- **Dos evidencias que se contradicen no se deciden.** `SIGNAL_CONFLICT`, con las dos conservadas.
- **Lo que interpreta un modelo no pisa un dato estructurado.** Gana lo estructurado y la
  interpretación queda anotada como `SIGNAL_INTERPRETATION_OVERRIDDEN`.
- **La afirmación de un agente, sola, no sostiene nada.** Es una opinión con formato de evidencia.

El inventario de señales válidas sale de la matriz: una que la matriz no declara se rechaza con
`SIGNAL_NOT_DECLARED`.

> 🔴 **La evidencia entra como dato y todavía nadie la junta.** Existe quién produce la señal;
> no existe quién releva el material. Por eso un plan real sigue saliendo casi todo sin resolver,
> y ese es el estado honesto.

## Replanificar

Un plan no es inmutable. Cuando una unidad descubre algo que cambia la forma del trabajo:

```powershell
python .claude\harness\bin\desarrollo\dev-harness.py plan GCBA-1234 `
    --replanificar propuesta-v2.json --motivo "el repositorio usa CQRS"
```

El motivo es obligatorio. Un plan que cambió sin que nadie dijera por qué no se puede auditar, y
`planHistory` es el único lugar donde "por qué este plan es así" tiene respuesta.

## Lo que este bloque no hace

- **No ejecuta ninguna unidad.** Ni delega, ni invoca a un especialista, ni toca un archivo.
- **No crea agentes.** Los siete especialistas están declarados en el roster y todavía no tienen su
  `.md`: su existencia se valida contra la matriz normativa, y no se crean agentes porque exista
  una tecnología.
- **No inventa modelos.** Un perfil sin modelo declarado se dice.
- **No decide qué documento es relevante.** Eso lo declaró el Bloque 2 y lo elige quien tenga un
  modelo.
- **No mide lo que se gasta.** El `expectedConsumption` de la compuerta dice `ALTO` o `BAJO`: una
  etiqueta, no un número. Los tokens, el tiempo y la plata los cuenta el Bloque 4 —
  [la contabilidad de una tarea](contabilidad.md)—, que observa a éste sin tocarlo: no lo importa,
  no lo importan, y la compuerta humana de `consumo.py` sigue siendo la única que aprueba.
