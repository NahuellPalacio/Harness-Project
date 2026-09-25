# La contabilidad de una tarea

El Bloque 3 decide **qué modelo** usa cada unidad de trabajo. El Bloque 4 mide **qué costó**, y no
toca nada de lo que el 3 decide.

```
Bloque 3                       Bloque 4
plan, tiers, compuerta   →     tokens, tiempo, plata, presupuesto
                         ←     evidencia para la compuerta
```

> 🔴 **El Bloque 4 no aprueba nada.** Devuelve seis estados y ninguno significa "adelante". La
> autoridad para escalar a un modelo caro sigue siendo la compuerta humana de `consumo.py`, que ni
> siquiera sabe que este bloque existe.

## Qué corre

```bash
# ingerir una fuente de uso y ver el resumen
dev-harness.py contabilidad GCBA-1234 --ingerir ~/.claude/projects/<proyecto>/<sesion>.jsonl

# lo mismo, atribuyendo a una unidad y a un agente
dev-harness.py contabilidad GCBA-1234 --ingerir <fuente> --unidad api-de-tramites --agente dev-backend

# generar el reporte administrativo
dev-harness.py contabilidad GCBA-1234 --reporte

# la barra de la sesión activa
dev-harness.py contabilidad GCBA-1234 --barra --sesion <id>
```

Reingerir la misma fuente **no duplica nada**: cada evento derivado lleva un id determinista y el
libro rechaza el que ya tiene.

Lo que el proveedor reporta de la sesión entera —la plata y el tiempo del `cost-state`— es
**acumulado**. Cada estado nuevo entra al libro como un evento nuevo, y el resumen toma el último
de cada sesión y modelo: ni los suma, ni se queda con el primero. Ingerir una transcripción de a
poco o de una vez da lo mismo.

## Dónde queda todo

```
.claude/runtime/accounting/<tarea>/
├── ledger.jsonl        la fuente de verdad, append-only
├── summary.json        el agregado determinista
└── execution-cost.md   el reporte que lee una persona
```

Una sola dirección, siempre:

```
ledger.jsonl  →  summary.json  →  execution-cost.md
```

> 🔴 **El Markdown nunca es la fuente.** Ningún módulo lo lee. Corromperlo a mano no cambia un solo
> número del resumen, y borrarlo no pierde nada: se regenera igual.

## El libro no se edita

No hay una función que reescriba una línea ni una que borre. Enmendar un hecho es agregar un evento
`ACCOUNTING_CORRECTION` que lo referencia; el hecho viejo queda byte a byte donde estaba, y la
agregación usa la corrección en su lugar.

Lo que hace confiable a un libro contable no es la intención de quien escribe: es que el verbo no
exista.

## Las cuatro reglas

### 1. Lo que falta no es cero

| Estado | Cuándo |
|---|---|
| `USAGE_UNRESOLVED` | La fuente no reportó consumo |
| `COST_UNRESOLVED` | No hay cómo calcular la plata |
| `PRICING_UNAVAILABLE` | Falta la fuente de precios |
| `TIME_ATTRIBUTION_UNRESOLVED` | Falta alguna de las tres clases de tiempo |
| `SESSION_ATTRIBUTION_UNRESOLVED` | Hay consumo sin sesión conocida |
| `WORKUNIT_ATTRIBUTION_UNRESOLVED` | Hay consumo sin unidad de trabajo conocida |
| `AGENT_ATTRIBUTION_UNRESOLVED` | Hay consumo sin agente conocido |
| `USAGE_RECONCILIATION_UNRESOLVED` | Lo derivado y lo que reporta el proveedor no coinciden |
| `BUDGET_UNDEFINED` | No hay presupuesto declarado |

Un cero **medido** y un desconocido son dos cosas distintas, y el resumen las distingue. Una tarea
que sale barata porque nadie pudo medirla es la peor clase de reporte.

### 2. La foto de la ventana no es un consumo

`contextTokens` es cuánto ocupa la conversación **ahora**. No se suma nunca: cada llamada vuelve a
mandar la conversación entera, así que sumar las fotos crece como el cuadrado de los turnos y no
significa nada. El resumen reporta la última, con su límite.

Lo facturable se suma aparte y por clase: input, output, cache read y cache creation, cuatro
números que no se colapsan en uno.

### 3. Un hecho visto dos veces cuenta una

Medido el **20-09-2026** sobre una transcripción real de este repositorio:

```
438 líneas de asistente · 252 ids de mensaje distintos · 186 repetidas

sumando línea por línea   739.096 tokens de salida
deduplicando por mensaje  370.919
```

Claude Code escribe una línea por bloque de contenido y todas repiten el mismo `usage`. Cada evento
lleva una `dedupKey` que el adaptador calcula —para una transcripción, el id del mensaje— y el
núcleo cuenta cada clave una sola vez. El núcleo no sabe cómo se construye la clave: no sabe
siquiera de qué proveedor viene.

### 4. Lo que no se pudo atribuir no se reparte

```
suma de las unidades  +  lo no atribuido  =  total de la tarea
```

Un consumo sin unidad conocida cuenta en el total —pasó— y no entra en ninguna fila. Repartirlo
proporcionalmente daría un reporte que cierra y una atribución inventada.

## La plata

El harness **no trae ninguna tarifa adentro** y no inventa ninguna. Hay dos métodos y nada más:

| Método | De dónde sale |
|---|---|
| `PROVIDER_REPORTED` | El proveedor reportó el monto, y se lo cita con su referencia |
| `RATE_TABLE` | El proyecto declaró una tabla en `harness.presupuesto.json` |

Sin ninguno de los dos: `PRICING_UNAVAILABLE`. Un precio inventado en un reporte administrativo se
convierte en *el* precio, y nadie vuelve a preguntar de dónde salió.

Todo cálculo monetario conserva siete campos, y sin los siete no es un costo:

```
provider · model · pricingSource · pricingVersionOrDate · currency · billingMode · calculationMethod
```

### Gasto real contra equivalente de API

| Modo | Dónde cae la plata |
|---|---|
| `API` | `actual` |
| `SUBSCRIPTION` · `ENTERPRISE` | `apiEquivalentEstimated`, y `actual` queda en `FIXED_PLAN` |
| `INTERNAL` | `apiEquivalentEstimated` |
| `UNKNOWN` | `COST_UNRESOLVED` |

> 🔴 **Los dos campos nunca tienen un número a la vez.** Con una suscripción, los dólares que
> informa el proveedor **no se gastaron**: es lo que habría costado por API. Presentarlo como gasto
> real es mentirle a quien firma el presupuesto. El modo de facturación se **declara**, no se
> infiere.

### Cuando las dos fuentes no coinciden

El agregado del proveedor y la suma derivada de la transcripción pueden diferir —una transcripción
compactada perdió lo anterior—. La derivación es un **piso**, no la verdad.

```
tokens  →  se guardan los dos y la diferencia queda visible
plata   →  gana lo reportado; si no hay, la derivada
tiempo  →  gana lo reportado; si no hay, la derivada
```

Para los tokens no gana ninguno porque la derivación es la única que sabe a qué sesión, unidad y
agente pertenece cada consumo: elegir el agregado sería perder la atribución entera. El resumen dice
cuál usó en `costSource` y `timeSource`.

## El tiempo

Tres clases y ninguna se deduce de otra:

| | |
|---|---|
| `wallMs` | Cuánto pasó en el reloj de la pared |
| `modelMs` | Cuánto estuvo el modelo trabajando |
| `toolMs` | Cuánto tardaron las tools |

Entre el principio y el final de una unidad hay tools, red, esperas y una persona leyendo. Sin
evidencia de tiempo de modelo, `modelMs` queda vacío y el bloque sale
`TIME_ATTRIBUTION_UNRESOLVED`. No se rellena con la pared.

## El presupuesto

Se declara en `.claude/harness.presupuesto.json`. El harness no trae uno, y que no exista es la
respuesta correcta hasta que alguien lo escriba.

```json
{
  "policyId": "gcba-tramites",
  "currency": "USD",
  "billingMode": "SUBSCRIPTION",
  "task":    { "softLimit": 5.0, "hardLimit": 20.0 },
  "project": { "softLimit": 100.0, "hardLimit": 400.0 },
  "premiumModel": {
    "requiresHumanApproval": true,
    "projectedOverrunRequiresApproval": true
  },
  "statusBar": { "warningAt": 0.5, "errorAt": 0.9,
                 "contextWarningAt": 0.7, "contextErrorAt": 0.9 }
}
```

El gate calcula `consumido + incremento estimado = proyectado` y contesta uno de seis estados, con
la precedencia escrita y en ese orden:

| # | Situación | Estado |
|---|---|---|
| 1 | No hay política | `BUDGET_UNDEFINED` |
| 2 | No hay plata comparable | `COST_UNRESOLVED` |
| 3 | Ya se pasó el límite duro | `BUDGET_EXCEEDED` |
| 4 | Es premium y la política pide gente | `HUMAN_APPROVAL_REQUIRED` |
| 5 | El proyectado pasa el duro | `HUMAN_APPROVAL_REQUIRED` o `BUDGET_EXCEEDED` |
| 6 | El proyectado pasa el blando | `BUDGET_WARNING` |
| 7 | Lo demás | `WITHIN_BUDGET` |

El 3 va antes que el 4 a propósito: **lo que ya se gastó no se puede aprobar**. Y un límite blando
avisa y no bloquea — un aviso que bloquea deja de ser un aviso.

## La barra

Representa la **sesión activa**, no la tarea entera. Cambiar de sesión cambia los números; el libro
sigue teniendo todas, y la sesión anterior se vuelve a pedir igual.

```
m-grande · Ctx 61% · Budget 46% · USD 2.84 eq · 18m
```

Cuando no entra, se cae lo menos informativo primero —el tiempo, después la plata, después el
modelo— y **el estado de aviso o de error no se cae nunca**.

> 🔴 **Contexto y presupuesto son dos cosas.** Una ventana al 78% no dice nada sobre la plata, y una
> tarea al 90% del presupuesto puede tener la ventana vacía.

Los umbrales salen de `statusBar` en la política. Sin umbrales declarados el nivel es `UNRESOLVED` y
el número se muestra igual: un verde inventado es peor que un signo de pregunta.

### La Context Bar, en la terminal de Claude Code

La Context Bar es la `statusLine` de Claude Code: una línea al pie de la terminal que se dibuja al
empezar la sesión y después de cada mensaje. La registra `install.ps1` en `.claude/settings.json`
cuando está el harness de `desarrollo`, y la dibuja `bin/desarrollo/contabilidad/statusline.py`.

```
HARNESS | m-grande | Ctx 122k | Tok 1.2M in / 34k out | USD 2.84 eq | 18m 03s | Budget 46%
```

> 🔴 **Es de la terminal, y nada más.** La extensión de VS Code no tiene una integración nativa con
> la barra de estado: el harness no la provee. La documentación de `statusLine` no dice si la
> extensión la muestra, y no se promete. Una barra en VS Code sería otro adaptador de presentación
> que lea el Bloque 4, y no existe.

Cada vez que Claude Code la invoca, la barra:
1. lee de stdin el `session_id` y el `transcript_path`, y nada más;
2. ingiere la transcripción con el adaptador del Bloque 4 al libro de la sesión,
   `.claude/runtime/accounting/<session_id>/ledger.jsonl`. El libro deduplica por `eventId`, así que
   dibujar dos veces no suma dos veces;
3. dibuja lo que resume `barra.de`, en una línea;
4. escribe su señal de vida, `.claude/runtime/contextbar.json`, que es lo que `harness` y la
   bienvenida usan para decir si está activa. Lleva la huella que el comando registrado le pasa
   como último argumento: la del comando que corrió, no la del `settings.json` de ahora;
5. sale con 0 siempre. Si algo falla dibuja `HARNESS | sin datos del Bloque 4`, nunca una línea vacía.

Lo que dibuja sale del Bloque 4 y de ningún otro lado:
- **El costo y el contexto que Claude Code manda por stdin no se usan.** Serían una segunda fuente
  contable.
- **Un campo que el Bloque 4 no tiene no aparece.** Sin límite de ventana no hay porcentaje de
  contexto, y sale la ventana en tokens. Sin política de presupuesto no hay plata ni `Budget`. Un
  costo `COST_UNRESOLVED` no sale como `USD 0`: no sale.
- **La tarea no aparece** mientras nadie declare una: la barra contabiliza la sesión.
- **No dibuja texto de la transcripción.** Del libro entran el modelo, la tarea y el agente, y solo
  si tienen forma de identificador y el catálogo de secretos no reconoce nada en ellos.

La latencia se mide con `install.ps1 -Doctor`, sobre una transcripción de 5 MB. El umbral es 400 ms
de p50 y no se mueve: si pasa, `-Doctor` lo dice.

`harness` muestra si está activa en la sección "Runtime / Observabilidad":

```
Runtime / Observabilidad
  Block 4 Accounting        ✓ ACTIVO
  Context Bar               ✓ ACTIVA (última sesión: 6ea09e99)
  Security Reporting        ✓ ACTIVO
  Reinicio de Claude Code   no hace falta
  Última sesión vista       6ea09e99 cargó la Context Bar (último dibujo: 2026-09-24T10:00:01)
```

Después de instalarla o de un `-Update` que la cambia, queda `REQUIERE REINICIO` hasta que se dibuje
con la configuración nueva. La documentación no garantiza que Claude Code la recargue a mitad de
sesión.

## Los adaptadores

```
registro de adaptadores
├── claude-code   lee una transcripción JSONL
└── codex         el mismo contrato, sin fuente autoritativa
```

Todo lo que sabe de un formato concreto vive del lado del adaptador. El núcleo recibe eventos
normalizados y **no nombra a ningún proveedor** —está verificado como invariante sobre el paquete
entero, no como una lista de ramas prohibidas—. Agregar un proveedor es escribir su módulo y
agregar una fila al registro.

`codex` devuelve `USAGE_UNRESOLVED` porque hoy no hay una fuente local que reporte su consumo
facturable. Devolver cero diría que no consumió; devolver una lista vacía diría que no pasó nada.
Las dos son falsas.

## Lo que este bloque no hace

- **No ejecuta nada.** Los trece tipos de evento son un vocabulario; el único productor real hoy es
  un adaptador leyendo una transcripción. `AGENT_RUN_STARTED` es un contrato sin llamador hasta que
  exista el bloque que ejecute.
- **No lo llama ningún agente ni ninguna skill.** Si un agente tuviera que acordarse de registrar su
  consumo, el consumo del agente que se olvide no existiría.
- **No puede guardar una conversación.** Un evento con una clave que nadie declaró —en la raíz o
  adentro de `usage`, `time`, `cost` o `source`— no se escribe; `metadata` acepta siete claves y
  sólo valores planos; ningún número pasa de 18 dígitos; todo texto se recorta a 300 caracteres y
  el recorte se dice; y cada evento pasa por la limpieza de secretos del Bloque 2 antes de tocar
  el disco. El evento más grande que el contrato permite pesa **8.811 bytes**, medidos.

  🔴 Las cinco reglas hacen falta juntas. Con cuatro campos cerrados y uno abierto, una
  conversación entra igual: entró por un objeto anidado, por una lista de turnos, por el **nombre**
  de un campo de dos mil caracteres y por un entero de 3.901 dígitos. Lo que sí queda es un
  fragmento de hasta 300 caracteres en un campo declarado, con un dato que no sea un secreto de
  confianza alta —una IP interna, por ejemplo—: está afirmado en verde en el test y anotado en
  `PENDIENTES-FH.md`.
- **No poda nada.** `.claude/runtime/accounting/` crece con cada tarea y nadie lo rota todavía.
