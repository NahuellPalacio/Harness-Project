# Bloque 4 — Contabilidad de ejecución y control de presupuesto

**Estado:** verificado y cerrado · **Fecha:** 20-09-2026 · **Bloque:** 4, conviviendo con el 3

## Qué problema resuelve

El harness decide qué modelo usa cada unidad de trabajo —`modelo.py` rutea por tier, `consumo.py`
detiene lo caro y pregunta— y **no mide nada de lo que después se gasta**. La compuerta humana
pregunta con un `expectedConsumption` que dice `ALTO` o `BAJO`: una etiqueta, no un número. El
presupuesto preautorizado se cuenta en llamadas premium, no en plata ni en tokens.

El resultado es que hoy no se puede contestar ninguna de estas preguntas:

```
cuanto salio la tarea GCBA-1234
cuanto de eso fue de dev-security y cuanto de dev-backend
que unidad de trabajo se llevo la mitad del presupuesto
cuanto tiempo estuvo el modelo trabajando y cuanto fue esperar una tool
el escalamiento a premium que se aprobo, valio lo que costo
```

Y hay una trampa concreta, medida sobre una transcripción real de este repositorio el
**20-09-2026**, `78e07295-f1a9-44c6-b92f-b04b6880a809.jsonl`:

```
lineas de asistente en la transcripcion   : 438
message.id distintos                      : 252
lineas repetidas                          : 186

output_tokens sumados crudos              : 739.096
output_tokens deduplicados por message.id : 370.919
```

Claude Code escribe **una línea por bloque de contenido**, y todas las líneas del mismo mensaje
repiten el mismo `usage`. Cualquier contador que sume línea por línea reporta el doble. Ese es el
error que este bloque tiene que ser incapaz de cometer.

## Qué queda afuera

- **La extensión de VS Code y cualquier renderizado.** Este repositorio no tiene UI: lo que se
  construye es el **resumen normalizado** que la barra consume, con sus umbrales en configuración.
  Un bloque de contabilidad que se valida mirando una barra de estado no se puede testear.
- **La emisión de eventos desde una ejecución real.** El Bloque 3 arma un plan y **no ejecuta
  ninguna unidad de trabajo** —está escrito en `orquestacion/__init__.py`—. No existe todavía el
  ejecutor que emitiría `AGENT_RUN_STARTED`. Se construye el vocabulario de eventos, el libro que
  los recibe y los adaptadores que los derivan de una transcripción; enchufarlos a un ejecutor es
  del bloque que ejecute.
- **La recolección real de Codex.** No hay una fuente local autoritativa de uso de Codex a la que
  este repositorio tenga acceso. Se construye el adaptador contra el mismo contrato y devuelve
  `USAGE_UNRESOLVED`, que es lo que el pedido exige explícitamente que no sea cero.
- **Una tabla de precios adentro del harness.** No se envía ninguna tarifa. Inventar un precio es
  exactamente el error que `COST_UNRESOLVED` existe para evitar, y un precio que envejece adentro
  de un repositorio es peor que ninguno porque nadie lo mira.
- **La agregación a nivel proyecto.** V1 cierra tarea y sesión. El proyecto se agrega sumando
  resúmenes de tareas y no tiene ninguna decisión nueva adentro; lo que falta para hacerlo es
  saber qué tareas pertenecen a qué proyecto, y eso lo contesta el Bloque 2.
- **Los seis no-objetivos que el propio pedido declara**: BI corporativo, chargeback entre
  agencias, conciliación de facturas, scraping de cuentas de facturación, almacén histórico de
  precios y pronóstico por ML.

## Las decisiones, y por qué

### El Bloque 4 observa al 3 y no lo toca

`consumo.py` y `modelo.py` quedan **exactamente como están**. El Bloque 4 no importa a ninguno de
los dos, y ninguno de los dos lo importa a él. La única forma en que la plata llega a una decisión
de escalamiento es que alguien le pase la evidencia al gate, y el gate sigue siendo
`consumo.decidir`.

Se consideró que `consumo.decidir` consultara el presupuesto directamente y quedó afuera: ata la
compuerta humana —que hoy funciona sin ningún estado en disco— a que exista un libro contable, y
convierte un módulo testeable con diccionarios en uno que necesita un sistema de archivos.

### El libro es la verdad, y es append-only por construcción

No hay una función que reescriba una línea. No hay una que borre. `agregar` abre en modo `a` y
nada más. Una corrección es un evento `ACCOUNTING_CORRECTION` **nuevo** que referencia al viejo, y
el viejo queda byte a byte donde estaba.

> 🔴 Un libro contable que se puede editar no es un libro contable. Lo que lo hace confiable no es
> la intención de quien escribe sino que no exista el verbo.

### La clave de deduplicación es del evento normalizado, no del adaptador

Cada evento de uso lleva una `dedupKey` estable que el adaptador calcula y el núcleo respeta. El
núcleo no sabe **cómo** se construye —para Claude Code es el id del mensaje—, sabe que dos eventos
con la misma clave son el mismo hecho observado dos veces. Es lo que hace que la trampa de las 186
líneas repetidas sea imposible sin que el núcleo sepa nada del proveedor.

### Se amplió el validador en vez de aflojar el schema

Los dos contratos nuevos tienen campos que admiten `null` —un `sessionId` que no se conoce, un
`actual` que no existe en una suscripción—. El intérprete de subconjunto de `contexto-armar.py` no
leía `type` como lista, y el precedente del repositorio era el de `normative-review.schema.json`:
dejar esos campos **sin tipo declarado**.

Acá no. Un campo sin tipo es un campo que nadie valida, y un entero que llega como string pasaba
verde. En un libro contable eso es plata mal sumada. Se amplió el intérprete para leer
`["integer", "null"]`, que es lo que su propio mensaje de error viene diciendo desde que existe:
*se amplía el validador, no se afloja el schema*.

El agregado es de diez líneas, no cambia nada de lo que ya validaba —el mensaje de un `type`
string sigue palabra por palabra igual— y ahora `controlar_soporte` también rechaza un nombre de
tipo inventado, que antes sólo explotaba si algún documento pasaba por esa rama.

### Para la plata y el tiempo gana lo que reporta el proveedor; para los tokens, ninguno

De los tokens hay dos mediciones: la derivada evento por evento y la del agregado del proveedor. De
la plata y del tiempo hay una sola —la del que factura—, porque una transcripción no dice cuánto
salió cada mensaje ni cuánto tardó.

Así que la regla es asimétrica, y el motivo no es comodidad:

```
tokens  ->  se concilian: se guardan las dos y la diferencia queda visible
plata   ->  gana lo reportado; si no hay, la derivada
tiempo  ->  gana lo reportado; si no hay, la derivada
```

Elegir el agregado para los tokens sería perder la atribución entera: el agregado no sabe a qué
sesión, unidad ni agente pertenece cada consumo, y eso es justo lo que el reporte tiene que
contestar. El resumen dice cuál de las dos usó en `costSource` y `timeSource`.

### La foto del contexto no es un consumo

`contextTokens` se calcula por evento y **no se suma nunca**. El resumen reporta el último valor
con su límite, porque eso es lo que la ventana tiene adentro ahora. Los tokens facturables se
suman por clase —input, output, cache read, cache creation— después de deduplicar.

Sumar fotos de contexto es la forma más fácil de reportar un número enorme y falso, y es la que un
adaptador derivado de una barra de contexto hereda si nadie la corta a propósito.

### Ninguna tarifa vive en el harness: dos métodos de cálculo y ninguno inventa

```
PROVIDER_REPORTED   el proveedor reporta la plata y se la cita con su referencia
RATE_TABLE          el proyecto declaro una tabla de tarifas en su configuracion
```

Sin ninguno de los dos: `COST_UNRESOLVED` con `PRICING_UNAVAILABLE`.

### El modo de facturación decide en qué campo cae la plata

```
API                        -> actual
SUBSCRIPTION / ENTERPRISE  -> apiEquivalentEstimated, y actual queda FIXED_PLAN o UNKNOWN
INTERNAL                   -> apiEquivalentEstimated
UNKNOWN                    -> COST_UNRESOLVED
```

Claude Code reporta dólares en una suscripción. Esa plata **no se gastó**: es lo que habría
costado por API. Presentarla como gasto real es el error que `actual` y `apiEquivalentEstimated`
existen para hacer imposible, y el modo de facturación se declara, no se infiere.

### Lo que no se pudo atribuir se ve, y no se reparte

Un consumo sin `workUnitId` conocido **cuenta en el total de la tarea** —pasó— y no entra en
ninguna fila de unidad. La invariante del resumen es:

```
suma de las unidades  +  lo no atribuido  =  total de la tarea
```

Repartirlo proporcionalmente entre las unidades conocidas daría un reporte que cierra y una
atribución inventada. Un reporte que no cierra y lo dice es más barato.

### Cuando el proveedor y la derivación no coinciden, se registran las dos

En la misma transcripción medida arriba, el agregado que reporta el proveedor es **mayor** que la
suma deduplicada: 603.597 contra 371.963 tokens de salida. La transcripción se compactó y lo
anterior ya no está en el archivo.

La derivación es un **piso**, no la verdad. Cuando las dos fuentes existen y difieren, el resumen
guarda las dos y deja `USAGE_RECONCILIATION_UNRESOLVED`. Elegir una en silencio es la decisión que
nadie después puede auditar.

### El núcleo no nombra ningún proveedor

No hay un `if provider == "claude"` en la contabilidad, y tampoco el nombre de un proveedor en un
comentario del núcleo. Los nombres viven en el registro de adaptadores, que es el único lugar
donde un proveedor existe como string. Se verifica como **invariante sobre el paquete entero**, no
como una lista de ramas prohibidas.

### El libro vive bajo `.claude/`, no en la raíz del proyecto

El pedido sugiere `runtime/accounting/<task-id>/`. Acá va a
`.claude/runtime/accounting/<task-id>/`, al lado de `contextos/` y `planes/`, que es donde el
harness ya escribe. Un directorio `runtime/` en la raíz ensucia el repositorio del proyecto que se
está desarrollando, que no es nuestro.

### El reporte sale en español, aunque el template del pedido esté en inglés

`execution-cost.md` lo lee una persona que rinde cuentas, y por ADR-0011 el idioma de un archivo lo
decide quién lo lee. El `execution-cost-report-template.md` del pedido está en inglés con
`{{placeholders}}`; lo que se construye conserva sus secciones y sus métricas y las escribe en
español. Los identificadores —`PROVIDER_REPORTED`, `BUDGET_WARNING`, `USAGE_UNRESOLVED`— no se
traducen: son contrato.

Es una desviación del pedido, declarada acá para que no haya que descubrirla leyendo el archivo.

### El evento pasa por la limpieza del Bloque 2 antes de escribirse

`contexto/limpieza.redactar_arbol` con el catálogo de secretos del harness, la misma que redacta
el `OrchestrationPlan`. No se escribe una segunda: dos limpiezas parecidas es como un día una
encuentra el catálogo y la otra no.

### `metadata` tiene las claves cerradas, y ningún campo del libro aguanta un párrafo

La limpieza saca **secretos**. No saca **prosa**, y no puede: un prompt no es un patrón de secreto
y ningún catálogo lo iba a encontrar. `metadata` era el único campo libre del contrato, y libre
quiere decir que ahí entra una conversación entera —con lo que la conversación traiga adentro—.

🔴 **Y el cierre es sobre el evento entero, no sobre `metadata`.** Ésa fue la lección cara de este
cambio, y costó tres pasadas del refutador. El intérprete de subconjunto no tiene
`additionalProperties`, así que **`usage`, `time`, `cost`, `source` y la raíz del evento son tan
libres como lo era `metadata`**: cerrar uno de los cinco no cierra nada. Con cuatro campos
cerrados y uno abierto, una conversación entra igual —y entró, cuatro veces seguidas, por caminos
distintos.

Cuatro reglas, y hacen falta las cuatro:

```
claves declaradas    ninguna clave que el schema no nombre, en ningun nivel del evento
CLAVES_DE_METADATA   siete claves para `metadata`, que es el unico objeto sin properties
ESCALARES            el valor de cada una es plano: ni un objeto, ni una lista
TOPE_DE_TEXTO = 300  todo texto del evento se recorta, y el recorte se dice
DIGITOS = 18         ningun numero pasa de dieciocho digitos
```

Las cuatro salen de lo que falló, no de una lista de precauciones:

| Lo que entró | Por dónde |
|---|---|
| `{"reason": {"prompt": "…"}}` | el cierre de claves miraba un solo nivel |
| veinte turnos de 200 caracteres | una lista: el recorte es por string, y ninguno pasaba de 300 |
| 2.000 caracteres en el **nombre** de un campo de `usage` | el recorte mira valores, no claves |
| una conversación entera como `int` de 3.901 dígitos | `int` es escalar y el recorte sólo toca `str` |

Las claves permitidas salen del **propio schema** —`properties` en cada nivel—, no de una lista
paralela: un campo nuevo del contrato queda permitido solo, y uno que nadie declaró no entra
nunca. El cierre vive en `eventos.validar`, la misma puerta que el schema, para que no queden dos
llaves y una sola cerradura.

📌 Cerrar la estructura destapó un hueco del contrato: `cost.provider` y `cost.model` son dos de
los siete campos que todo cálculo monetario conserva y el schema no los declaraba. Ahora sí.

El techo no se calcula multiplicando constantes: se **mide**, sobre un evento **armado desde el
contrato** —los 26 campos de texto en su tope, los 11 numéricos en dieciocho dígitos, cada `enum`
en su valor más largo—.

🔴 **Y lo que se mide es el CONTENIDO, no el archivo.** Ni los bytes ni el largo de la línea
sirven como techo, y esto costó dos pasadas del refutador. El recorte cuenta caracteres, el libro
se escribe con `ensure_ascii=False`, y `json.dumps` escapa: una barra invertida ocupa dos
caracteres de línea, un carácter de control ocupa seis. El mismo evento máximo, cambiando sólo
qué hay adentro de los campos:

```
relleno                  linea    bytes   contenido
ascii                    10266    10266        9643
ruta de Windows          11046    11046        9643
castellano con tildes    10266    18066        9643
emoji                    10266    33666        9643
comillas                 18066    18066        9643
barras invertidas        18066    18066        9643
caracteres de control    49266    49266        9643
```

La única columna que no se mueve es la última. **9.643 caracteres** es el techo, medido el
20-09-2026 con siete rellenos distintos, y el test afirma que los siete dan el mismo número —que
es lo que hace que sea un techo y no una foto—. Una conversación de una sesión real son cientos de
miles.

El número sale también de la aritmética del contrato, sin creerle a la medición:

```
26 campos de texto x 349 (300 + la marca de recorte)   =  9074
48 nombres de campo del schema mas las siete de metadata =   459
6 valores de enum, cada uno el mas largo                 =   110
                                                   total =  9643
```

9.643 es el techo de **texto**. Contando además los literales numéricos —11 campos, 219
caracteres— da 9.862. La diferencia no cambia nada: dieciocho dígitos son unos siete bytes de
carga útil, ochenta por evento entero, y un número no transporta prosa.

Y la de la ruta de Windows no es un relleno inventado: es la forma que tiene `rawReference` en
esta plataforma, y `contrato.a_evento` la copia además en `pricingSource`.

📌 El evento máximo se arma recorriendo `properties`, no a mano. La primera versión del test lo
escribía a mano, se olvidaba `eventId`, `timestamp`, `taskId` y `source.adapter`, y medía 8.848.
Un campo nuevo del contrato entra en la medición solo, y la cuenta de 26 campos de texto está
clavada para que subirlo obligue a volver a medir.

📌 **Lo que esto no cierra**, y está clavado con una aserción en verde: un **fragmento de hasta
300 caracteres en un campo declarado** pasa, con lo que traiga adentro, salvo que sea un secreto
de confianza alta. Es la doctrina del Bloque 2 —sólo se redacta eso, porque un falso positivo que
mutila un texto es peor que un aviso y acá no hay a quién preguntarle—. El día que alguien la
cambie, el test obliga a hablarlo.

### El libro no se puede acortar desde ningún módulo del paquete

Que `agregar` abra en modo `a` no sirve de nada si el módulo de al lado puede truncar el mismo
archivo. Dos cierres:

- Ningún `.py` del paquete usa `os.remove`, `os.unlink`, `os.truncate`, `os.rename`, `os.replace`,
  `shutil.rmtree`, `shutil.move` ni `.truncate(`. Se verifica sobre el **paquete entero**, por lo
  que el código hace y no por cómo se llama la función: un `def compactar(ruta): os.remove(ruta)`
  no lo agarra ninguna lista de verbos prohibidos, y borra el libro igual.
- Los dos módulos que sí escriben en modo `w` —el resumen y el reporte— se niegan a escribir sobre
  un archivo que se llame `ledger.jsonl`.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/execution-accounting-event.schema.json` | El contrato de un evento de contabilidad |
| `comun/schemas/budget-policy.schema.json` | El contrato de una política de presupuesto |
| `comun/bin/contexto-armar.py` | El intérprete de subconjunto, ampliado para leer `type` como lista |
| `bin/contabilidad/__init__.py` | La doctrina del bloque, en la cabecera |
| `bin/contabilidad/eventos.py` | Arma y valida un evento; el vocabulario de los trece tipos |
| `bin/contabilidad/libro.py` | El `ledger.jsonl` append-only, con deduplicación por `eventId` |
| `bin/contabilidad/agregacion.py` | Del libro al `summary.json`, determinístico |
| `bin/contabilidad/costos.py` | El motor de costos: dos métodos, siete campos, ninguna tarifa |
| `bin/contabilidad/tiempo.py` | El motor de tiempo: pared, modelo y tool separados |
| `bin/contabilidad/presupuesto.py` | La política, el gate y sus seis estados |
| `bin/contabilidad/reporte.py` | `execution-cost.md` generado del resumen |
| `bin/contabilidad/barra.py` | El resumen de la sesión activa que consume la barra |
| `bin/contabilidad/adaptadores/contrato.py` | El contrato normalizado y su validación |
| `bin/contabilidad/adaptadores/claude_code.py` | De una transcripción JSONL a eventos normalizados |
| `bin/contabilidad/adaptadores/codex.py` | El mismo contrato, sin fuente autoritativa |
| `bin/contabilidad/adaptadores/registro.py` | El único lugar donde un proveedor es un nombre |
| `bin/dev-harness.py` | Comando `contabilidad` con sus cuatro acciones |
| `docs/contabilidad.md` | Cómo se lee todo esto, para una persona |
| `tests/casos/30_b4_contabilidad.py` | Los escenarios de acá abajo |
| `tests/casos/30-contabilidad-instalador.ps1` | E-39 contra una instalación real |

Las rutas de `bin/` cuelgan de `harnesses/desarrollo/`.

## Escenarios verificables

Entre paréntesis, el `B4-nn` del pedido de instalación cuando corresponde.

### El contrato del evento y el libro

- **E-01** — Un evento válido pasa el schema, y uno al que le falta `eventId`, `eventType`,
  `timestamp`, `taskId` o `source` no se escribe. (B4-01) · rojo visto: si
- **E-02** — Los dos schemas pasan enteros por `controlar_soporte` del validador de subconjunto:
  ningún campo usa una palabra que el intérprete no lea. · rojo visto: si
- **E-02b** — El intérprete lee `type` como lista: un entero y un `null` pasan donde el contrato
  dice `["integer", "null"]`, un string y un booleano no, un nombre de tipo inventado se rechaza al
  controlar el soporte, y lo que ya validaba sigue dando el mismo mensaje. · rojo visto: si
- **E-03** — El libro es append-only: después de agregar, los bytes anteriores quedan idénticos;
  ningún `.py` del paquete usa una operación que acorte o borre un archivo; y los dos módulos que
  escriben en modo `w` se niegan a escribir sobre un `ledger.jsonl`. (B4-02) · rojo visto: si
- **E-04** — Un `eventId` que ya está en el libro no entra dos veces. (B4-02) · rojo visto: si
- **E-05** — Una corrección es un evento `ACCOUNTING_CORRECTION` nuevo: la línea corregida queda
  byte a byte igual y la agregación aplica la corrección encima. (B4-22) · rojo visto: si

### La deduplicación y la ventana de contexto

- **E-06** — El mismo registro crudo del proveedor observado dos veces cuenta una sola vez: la
  clave de deduplicación es estable entre corridas. (B4-03) · rojo visto: si
- **E-07** — Sobre una transcripción con líneas repetidas por bloque de contenido, el total es el
  deduplicado y no la suma cruda. (B4-25) · rojo visto: si
- **E-08** — `contextTokens` es una foto: no se suma nunca entre eventos, y el resumen reporta el
  último valor con su límite. (B4-04) · rojo visto: si
- **E-09** — input, output, cache read y cache creation llegan al resumen separados y ninguno se
  pisa con otro. (B4-05) · rojo visto: si
- **E-10** — Un uso desconocido queda `USAGE_UNRESOLVED` y no se convierte en cero. (B4-06)
  · rojo visto: si

### El motor de costos

- **E-11** — `actual` y `apiEquivalentEstimated` son dos campos distintos y ninguno se copia al
  otro. (B4-07) · rojo visto: si
- **E-12** — Con `billingMode: SUBSCRIPTION` la plata reportada entra como equivalente de API y
  `actual` queda sin resolver: un plan fijo no se presenta como gasto incremental. (B4-08)
  · rojo visto: si
- **E-13** — Sin fuente de precios declarada el costo sale `COST_UNRESOLVED` con
  `PRICING_UNAVAILABLE`; ningún JSON que el instalador copia declara una clave de tarifa en
  ningún nivel; y ningún contenedor público del paquete guarda un número. (B4-09) · rojo visto: si
- **E-14** — Todo cálculo monetario conserva los siete campos —provider, model, pricingSource,
  pricingVersionOrDate, currency, billingMode, calculationMethod—; sin uno de los siete no hay
  costo. · rojo visto: si
- **E-15** — Cuando el proveedor reporta su agregado y la derivación queda por debajo, el resumen
  guarda las dos y deja `USAGE_RECONCILIATION_UNRESOLVED`. · rojo visto: si

### El motor de tiempo

- **E-16** — Pared, modelo y tool llegan separados al resumen y ninguno es la suma de los otros.
  (B4-10) · rojo visto: si
- **E-17** — Tiempo de pared sin evidencia de tiempo de modelo no se rotula como tiempo de modelo:
  queda `TIME_ATTRIBUTION_UNRESOLVED`. · rojo visto: si

### La agregación

- **E-18** — La jerarquía ModelCall/ToolCall → AgentRun → WorkUnit → Session → Task agrega, y cada
  nivel es la suma de lo que tiene abajo. · rojo visto: si
- **E-19** — El total de la tarea es igual a la suma de lo atribuido deduplicado más lo no
  atribuido. (B4-13) · rojo visto: si
- **E-20** — Una atribución de unidad desconocida queda `WORKUNIT_ATTRIBUTION_UNRESOLVED` y su
  consumo no se reparte entre las unidades conocidas. (B4-14) · rojo visto: si
- **E-21** — El mismo libro produce el mismo `summary.json`, byte a byte, en **procesos
  distintos y con el hash sembrado al azar**; y las filas no dependen del orden del libro.
  (B4-27) · rojo visto: si

### El presupuesto

- **E-22** — Sin política declarada el estado es `BUDGET_UNDEFINED` y no se inventa ningún límite.
  (B4-28) · rojo visto: si
- **E-23** — Pasar el límite blando da `BUDGET_WARNING`. (B4-15) · rojo visto: si
- **E-24** — El proyectado que supera el límite duro da `HUMAN_APPROVAL_REQUIRED` cuando la
  política lo pide, y `BUDGET_EXCEEDED` cuando ya se pasó. (B4-16) · rojo visto: si
- **E-25** — El Bloque 4 no aprueba: no devuelve ningún estado de aprobación, y la compuerta de
  `consumo.decidir` sigue rechazando premium igual con `WITHIN_BUDGET` adelante. (B4-17)
  · rojo visto: si
- **E-26** — La decisión de presupuesto queda en el libro como `BUDGET_DECISION_RECORDED`.
  · rojo visto: si

### El reporte y la barra

- **E-27** — `execution-cost.md` se genera del `summary.json` y sus números son los del resumen.
  (B4-20) · rojo visto: si
- **E-28** — Ningún módulo de contabilidad lee un `.md`: las cinco lecturas del paquete están
  clavadas con su módulo y su función, y ninguna está en el reporte, la barra, la agregación, los
  costos ni el tiempo. Corromper el `.md` no mueve un número. (B4-21) · rojo visto: si
- **E-29** — La barra representa la sesión activa: cambiar de sesión cambia los números. (B4-11)
  · rojo visto: si
- **E-30** — Cambiar de sesión no borra nada: la anterior sigue en el libro y su resumen se vuelve
  a pedir igual. (B4-12) · rojo visto: si
- **E-31** — La barra separa contexto de presupuesto, y sus umbrales salen de configuración, no de
  constantes en el renderizado. · rojo visto: si

### Los adaptadores

- **E-32** — El núcleo de contabilidad no nombra ningún proveedor ni ninguna familia de modelo.
  Se barre **todo `.py` del paquete menos el registro y los adaptadores que el registro declara**,
  así que un módulo nuevo entra al barrido solo. (B4-23) · rojo visto: si
- **E-33** — El adaptador de transcripción conserva modelo y sesión cuando la fuente los trae, y
  los deja sin resolver cuando no. (B4-24) · rojo visto: si
- **E-34** — El adaptador sin fuente autoritativa cumple el mismo contrato y devuelve
  `USAGE_UNRESOLVED` en vez de cero. · rojo visto: si

### El desacople y los secretos

- **E-35** — Ningún `agents/*.md` nombra un módulo de contabilidad ni una función suya. (B4-18)
  · rojo visto: si
- **E-36** — Ningún `skills/*/SKILL.md` nombra un módulo de contabilidad ni una función suya.
  (B4-19) · rojo visto: si
- **E-37** — El libro no puede guardar una conversación: un evento con una clave que nadie declaró
  —en la raíz o adentro de `usage`, `time`, `cost` o `source`— **no se escribe**; `metadata` acepta
  siete claves y sólo valores escalares; ningún número pasa de 18 dígitos; todo texto se recorta a
  300 y el recorte se dice; el evento pasa por la limpieza del Bloque 2 y `rawReference` es una
  referencia local. El evento más grande que el contrato permite se arma **desde el contrato** y
  su **contenido** no llega a 10.000 caracteres, con siete rellenos distintos dando el mismo
  número. Lo que el mecanismo **no** cierra —un fragmento de hasta 300 caracteres en un campo
  declarado, con un dato que no sea un secreto de confianza alta— queda afirmado en verde.
  (B4-26) · rojo visto: si

### La CLI y la instalación

- **E-38** — `dev-harness.py contabilidad` ingiere, resume, reporta y muestra la barra, y sale con
  código 2 y un mensaje útil cuando falta lo que necesita. · rojo visto: si
- **E-39** — Los dos schemas y las catorce piezas del paquete `contabilidad/` llegan a un
  proyecto **instalado de verdad**, el comando corre desde ahí con la trampa del doble conteo
  adentro, y el libro sobrevive a un `-Update` y a un `-Uninstall`. · rojo visto: si

## Cómo se verifica

Los 40 pasan por `.\tests\Invoke-Tests.ps1`. Ninguno lleva la marca `· verificación: lectura`:
todo lo que este bloque hace es determinista, y un escenario sobre una corrida de un modelo sería
justamente lo que ADR-0009 dice que no se marca así.

E-07 y E-33 usan una transcripción sintética armada con la forma real medida el 20-09-2026, no la
transcripción de la sesión: un test que depende de un archivo en el `~/.claude` de una máquina no
corre en otra.

## Riesgos conocidos

- **Los eventos no los emite nadie todavía.** El vocabulario de trece tipos existe y el libro los
  recibe, pero el único productor real es un adaptador leyendo una transcripción. Hasta que haya
  un ejecutor, `AGENT_RUN_STARTED` y `WORKUNIT_STARTED` son un contrato sin llamador, y la
  atribución por agente y por unidad va a salir sin resolver en cualquier corrida real.
- **El adaptador de transcripción se ata a una forma que el proveedor puede cambiar.** Lo que lo
  contiene es que está solo en `adaptadores/`, y que el contrato normalizado no cambia si la forma
  cambia. Lo que no lo contiene es que la forma cambie en silencio: un campo que se renombra sale
  como `USAGE_UNRESOLVED`, que es lo correcto, pero nadie se entera hasta que mira el reporte.
- **`.claude/runtime/accounting/` crece sin nadie que lo pode.** No hay retención ni rotación. Un
  proyecto con mil tareas tiene mil directorios.
- **El modo de facturación se declara y nadie lo audita.** Alguien que declare `API` sobre una
  suscripción va a ver gasto real donde no lo hay. La defensa es la misma que la del scoring de
  `modelo.py`: no hay scoring, hay una persona que lo declara y queda escrito.
- **Un campo declarado puede llevar un fragmento con un dato sensible que no es un secreto
  reconocible.** Las claves cerradas, los valores escalares y el tope de 300 caracteres impiden
  guardar una conversación; no impiden que alguien escriba una IP interna en un motivo de veinte
  palabras. La limpieza del Bloque 2 sólo redacta lo de confianza alta, por una decisión que es de
  ese bloque y no de éste. Está afirmado en verde en E-37 para que se vea, y anotado en
  `PENDIENTES-FH.md`.
