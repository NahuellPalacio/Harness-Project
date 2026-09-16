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
texto y su página.

> 🔴 **Están sin clasificar, y por eso todavía no se citan.** `owners`, `skills`, `policies` y
> `checks` están vacíos: clasificarlas es trabajo de criterio que alguien tiene que validar contra
> el estándar, y una matriz inventada se lee igual de autoritativa que una real. Una regla sin
> `conditions` nunca se cita, y cada plan dice cuántas quedan.

Cuando la matriz exista, una regla clasificada se ve así:

```json
{
  "id": "ES0901-7.1-P1.node",
  "conditions": { "domains": ["frontend", "backend"] },
  "policies": ["npm-only"],
  "checks": ["dev-dependencias"]
}
```

y el plan empieza a citarla en `applicableStandards` sin que cambie una línea de código.

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
