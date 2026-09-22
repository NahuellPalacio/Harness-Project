# La matriz normativa de §7.1: qué regla aplica, y qué todavía no se sabe

**Estado:** construido · **Fecha:** 2026-09-18

## Qué problema resuelve

Las 26 reglas de ES0901 §7.1 entraron en 0.18.0 con su texto citado y su página, y con la
clasificación **vacía a propósito**: `owners`, `skills`, `policies` y `checks` en blanco. La
consecuencia se aceptó y se declaró: `applicableStandards` sale vacío en todo plan real, y ningún
plan cita un estándar. La nota de esa versión lo puso primero en "dónde seguir" — *"clasificar las
26 reglas es lo que destraba todo lo demás"*.

Esta es esa clasificación. Llega como dato: una matriz que dice, por regla, si aplica siempre o
bajo qué señal, qué agentes son sus dueños normativos, y qué policies y qué checks declara.

Lo que el harness todavía no sabe decir, y va a saber:

- **Qué reglas aplican a una unidad de trabajo**, y cuáles no.
- **Cuáles no se pueden decidir todavía** porque falta la señal. Hoy no hay forma de expresar "no
  sé": una regla que no se cita se lee igual que una que no aplica.
- **Qué policies y qué checks exige** lo que aplica, antes de que ninguno exista.

## Qué queda afuera

- **Las policies y los checks de verdad.** Este cambio carga sus ids, valida que sean únicos y los
  propaga. Ninguna implementación se escribe. Un check inventado para que una regla "cierre" es el
  mismo error que una matriz inventada: se lee igual de autoritativo que uno real.
- **Clasificar más allá de §7.1.** ES0902, miBA y ESB no entran.
- **Decidir si una aplicabilidad sin resolver frena la ejecución.** Se hace visible y nada más. Que
  bloquee o no es una decisión de orquestación, y se toma con el dato a la vista.
- **Reemplazar el archivo de reglas citables.** `es0901-7.1.json` se queda: es la fuente con el
  texto literal y la página, en español, y sus 26 filas están bajo test —E-25 y E-26 del Bloque 3
  comparan cada texto contra `normativa/extractos/ES0901.md`—. La matriz clasifica; no cita.
- **Inventar señales.** El resolvedor no deduce si una unidad toca la base o expone un endpoint.
  Si el dato no está, la regla queda sin resolver.

## Las decisiones, y por qué

### La matriz va al lado del texto citado, no encima

Dos archivos y una unión por id de regla:

```
es0901-7.1.json                  26 filas: el texto literal y la pagina, en espanol
es0901-7.1-normative-matrix.json 24 filas: modo, senales, agentes, policies, checks
```

El artefacto que llegó trae `operationalIntentEn`, que es una paráfrasis operativa en inglés.
Sirve para clasificar y no sirve para citar: ADR-0011 dice que una cita traducida deja de ser una
cita. Fundir los dos archivos perdería la fuente o traduciría la cita, y ninguna de las dos se
puede deshacer después.

### `P1` clasifica a sus tres cláusulas, y la herencia se declara

El archivo citable partió `P1` en `P1`, `P1.node` y `P1.plataformas` porque el estándar agrupa tres
cláusulas bajo un id y cada una va a tener dueño distinto. La matriz trae un solo `P1`. Ningún id
se toca: la matriz clasifica 24, y las dos cláusulas derivadas **heredan** la clasificación de su
regla madre. La herencia se escribe como regla del cargador y se testea; no se deduce del punto en
el nombre en ningún lado que no sea ese.

### Tres estados, porque "no sé" no es "no"

`APPLICABLE`, `NOT_APPLICABLE` y `APPLICABILITY_UNRESOLVED`. Convertir una señal ausente en "no
aplica" es la forma más barata de que un plan quede verde: la regla desaparece del reporte y nadie
la busca. La señal ausente tiene que doler un poco.

### El schema se traduce al subconjunto, y el "exactamente 24" se mueve al cargador

El schema que llegó usa `minItems` y `maxItems`, que el intérprete de `contexto-armar.py` no
soporta. Se reescribe en el subconjunto, y el inventario exacto —24 reglas, ids únicos, `G1` a
`M3`— lo comprueba el cargador, que es donde el pedido lo pide igual y donde puede decir **cuál**
falta en vez de sólo cuántas hay.

### La matriz no toca la existencia de nada

El orden es registro de agentes → resolución estructural → matriz. Un agente que la matriz nombra
y el registro no declara es `NORMATIVE_AGENT_REFERENCE_INVALID`: la matriz no lo crea, no lo
instala y no lo vuelve existente. Lo mismo con una skill pendiente — `dev-miba` sigue
`DECLARED_NOT_INSTALLED` después de resolver cualquier regla.

### Los ids declarados no fingen estar implementados

Una regla aplicable exige policies y checks que todavía no existen. Se reportan
`DECLARED_POLICY_NOT_INSTALLED` y `DECLARED_CHECK_NOT_INSTALLED`, y eso **no** invalida la matriz:
es el estado correcto de un harness que clasificó antes de construir. Cuando G1 instale los suyos,
esos cuatro ids dejan de estar en esa lista sin que la matriz cambie.

### `applicableStandards` no cambia de tipo

Sigue siendo la lista de estándares que ya consume el plan. Al lado entra `normative`, con las
reglas, las que no se resolvieron y los ids declarados. Cambiarle el tipo a un campo que alguien ya
lee es romper a distancia.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/reglas/es0901-7.1-normative-matrix.json` | Las 24 reglas clasificadas: modo, señales, agentes, policies, checks |
| `comun/schemas/es0901-7.1-normative-matrix.schema.json` | Su contrato, en el subconjunto que valida `contexto-armar.py` |
| `harnesses/desarrollo/bin/orquestacion/matriz.py` | Carga, valida, resuelve aplicabilidad y junta los ids declarados |
| `harnesses/desarrollo/bin/orquestacion/normativa.py` | Expone el resultado nuevo sin romper `applicableStandards` |
| `docs/normativa-7.1.md` | Regla, policy, check, evidencia y aplicabilidad, y la frontera con el registro |
| `tests/casos/23_matriz_normativa.py` | Los escenarios de este cambio |

## Escenarios verificables

Entre paréntesis, el `N-nn` del pedido que cubre cada uno.

### El contrato de la matriz

- **E-01** — La matriz carga y valida contra su schema, y el schema entra entero en el subconjunto
  que el intérprete soporta. (N-01) · rojo visto: si
- **E-02** — Hay exactamente 24 reglas y ningún id repetido. (N-02) · rojo visto: si
- **E-03** — El inventario es exactamente `G1`…`M3`: ni una de más, ni una de menos, ni una
  renombrada. (N-03) · rojo visto: si
- **E-04** — Una regla duplicada devuelve `NORMATIVE_MATRIX_INVALID` y nombra el id repetido.
  (N-09) · rojo visto: si
- **E-05** — Una matriz de otra versión del estándar devuelve
  `NORMATIVE_STANDARD_VERSION_MISMATCH` y no se carga. · rojo visto: si
- **E-06** — Pedir una regla que no existe devuelve `NORMATIVE_RULE_NOT_FOUND`.
  · rojo visto: si

### La aplicabilidad

- **E-07** — Una regla `ALWAYS` resuelve `APPLICABLE` sin que haga falta ninguna señal. (N-04)
  · rojo visto: si
- **E-08** — Una `CONDITIONAL` con su señal en `true` resuelve `APPLICABLE`. (N-05)
  · rojo visto: si
- **E-09** — La misma con la señal en `false` resuelve `NOT_APPLICABLE`. (N-06)
  · rojo visto: si
- **E-10** — Sin la señal, resuelve `APPLICABILITY_UNRESOLVED` y dice qué señal le falta. (N-07)
  · rojo visto: si
- **E-11** — Una señal ausente **nunca** se convierte en `NOT_APPLICABLE`: ninguna de las 17
  condicionales cae a "no aplica" con el contexto vacío. (N-08) · rojo visto: si
- **E-12** — Hoy ninguna condicional declara más de una señal, y el cargador lo afirma; una regla
  con dos señales y sin modo de combinación declarado devuelve
  `APPLICABILITY_EXPRESSION_UNRESOLVED` en vez de inventar un AND o un OR.
  · rojo visto: si

  > **Nota (2026-09-22).** El refutador encontró que "el cargador lo afirma" no era cierto: el
  > conteo de reglas con más de una señal lo hacía el test, y `matriz.validar()` aceptaba una
  > matriz con `D1` en dos señales y sin `combination`. Se subió el mecanismo, no se angostó el
  > escenario: ahora el validador devuelve `NORMATIVE_MATRIX_INVALID` y nombra la regla, y el
  > resolvedor sigue fallando cerrado con `APPLICABILITY_EXPRESSION_UNRESOLVED` si una regla así
  > le llega sin pasar por el validador.
- **E-13** — `D8` con `serviceEndpointPresent` en `true` es `APPLICABLE`, en `false` es
  `NOT_APPLICABLE`, y ausente es `APPLICABILITY_UNRESOLVED`. (N-14, N-15, N-16)
  · rojo visto: si

### Las referencias

- **E-14** — Una regla que nombra un agente que el registro no declara devuelve
  `NORMATIVE_AGENT_REFERENCE_INVALID`, y el agente no se crea. (N-10) · rojo visto: si
- **E-15** — Una skill desconocida devuelve `NORMATIVE_SKILL_REFERENCE_INVALID`; una
  `DECLARED_NOT_INSTALLED` es referencia válida y **sigue** pendiente después de resolver.
  (N-17) · rojo visto: si
- **E-16** — Resolver la matriz no cambia nada del registro de agentes: los mismos 10 válidos y
  las mismas 2 pendientes antes y después. (N-11) · rojo visto: si

### Las policies y los checks

- **E-17** — `G1` resuelve sus dos policies y sus dos checks declarados. (N-12)
  · rojo visto: si
- **E-18** — `D7` resuelve varias policies y varios checks de una sola regla. (N-13)
  · rojo visto: si
- **E-19** — Los ids se juntan sin fingir que existen: se reportan
  `DECLARED_POLICY_NOT_INSTALLED` y `DECLARED_CHECK_NOT_INSTALLED`, y eso no invalida la matriz.
  (N-18) · rojo visto: si

### La unión con el texto citado

- **E-20** — Las 24 filas de la matriz tienen su cita en `es0901-7.1.json`, y ninguna cita quedó
  sin fila. · rojo visto: si
- **E-21** — `P1.node` y `P1.plataformas` heredan la clasificación de `P1`, y la herencia está
  declarada en el cargador: una cláusula derivada que no encuentre su madre no hereda nada.
  · rojo visto: si
- **E-22** — El texto de una regla sigue saliendo del archivo citable, no de la matriz: la
  paráfrasis en inglés no reemplaza a la cita. · rojo visto: si

### Compatibilidad y determinismo

- **E-23** — `applicableStandards` sigue siendo lo que era para quien ya lo consume, y el bloque
  `normative` entra al lado. (N-19) · rojo visto: si

  > **Nota (2026-09-22).** "Al lado" era impreciso. En el `OrchestrationPlan` los dos no viven en
  > el mismo nivel: `applicableStandards` queda en la raíz del plan, con su forma de antes —una
  > lista de ids, la que contesta `normativa.aplicables` para los dominios del plan—, y
  > `normative` entra en **cada** `workUnit`, resuelto con las señales de esa unidad. Lo que el
  > escenario afirma es que agregar uno no desplazó al otro, y así se prueba: con un plan real
  > armado por `plan.armar`, no solo con las funciones sueltas.
- **E-24** — La misma matriz con las mismas señales da exactamente el mismo resultado: ninguna
  parte de la resolución depende de un modelo. (N-20) · rojo visto: si

## Cómo se verifica

Los 24 pasan por la suite. No hay ninguno por lectura: cargar un JSON, contar reglas, mirar un
booleano y juntar ids son operaciones de dato, y el pedido lo dice con todas las letras — ningún
modelo participa en decidir si una regla existe, si es `ALWAYS` o si una señal es verdadera.

Los casos negativos —id duplicado, versión distinta, agente desconocido, dos señales— se arman con
matrices fabricadas en memoria. La matriz instalada no se rompe para probar que el validador anda.

## Riesgos conocidos

- **La clasificación es criterio de alguien, y el harness no puede juzgarla.** Se valida que sea
  estructuralmente coherente —ids, señales, referencias— y nada más. Que `D1` sea de
  `dev-integration` y no de `dev-security` es una afirmación que ningún test puede contradecir.
- **Diecisiete de las 24 son condicionales, y hoy nadie produce las señales.** Sin un productor de
  señales, un plan real va a salir con casi todo `APPLICABILITY_UNRESOLVED`. Es el estado honesto y
  es incómodo a propósito; el trabajo que lo destraba es el análisis de impacto que las complete.
- **La herencia de `P1` es una regla nuestra.** Si mañana el artefacto se regenera con `P1` partido
  en tres, la herencia deja de aplicar y hay que sacarla: una herencia que sigue activa cuando ya
  no hace falta clasifica dos veces la misma cláusula.
- **36 policies y 34 checks declarados, cero implementados.** Todo plan va a reportar setenta
  controles no instalados hasta que se construyan de a uno. La lista va a ser larga antes de ser
  corta.
