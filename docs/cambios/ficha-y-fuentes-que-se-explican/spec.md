# La Ficha de Proyecto y `fuentes` dicen por qué no encontraron lo que buscaban

**Estado:** APPROVED FOR CONSTRUCTION · **Fecha:** 26-10-2026 · **Versión de partida:** 0.36.0 (`5a2d0ea`, tag `v0.36.0`, igual a
`origin/main`) · **Release previsto:** sin número todavía: 0.37.0 es de la Task 6.2 (en pausa, sin commit), y el que
cierre segundo toma 0.38.0 · **Origen:** el registro de hallazgos del proyecto ASI (APWIGELEC), entradas 2, 3 y 4,
anotadas el 26-10-2026 en `Pendientes/Fix-Harness/PENDIENTES-FH.md` (fila 21 de la tabla) · **Aprobación:** Nahuel
Palacio, 26-10-2026: aprobada como estaba escrita, para construir. La refutación independiente después de construir
sigue siendo obligatoria.

📌 **Convenciones.** **FH** es `Pendientes/Fix-Harness/PENDIENTES-FH.md`. **La Ficha** es la Ficha de Proyecto (un issue
de Jira donde vive el conocimiento del proyecto). **El acumulador** es `contexto.comun.Acumulador`, donde cada resolvedor
anota lo que le faltó. Las citas `archivo:línea` las leí sobre `5a2d0ea`.

## Qué problema resuelve

El 25-09-2026, en el proyecto ASI (0.24.0), `fuentes APWIGELEC-108 --aceptar ES0902` no aceptó nada y la salida fue:

```
evento=fuentes.ficha ficha=ninguna
harness: ES0902 no se puede aceptar (FRESHNESS_UNVERIFIED): no hay canal: no hay nada observado que aceptar.
```

La causa real era otra y estaba a la vista del código, no de la persona: el tipo de issue de la Ficha en el Jira de ASI
es `.ASI Ficha de proyecto` y el harness busca `Ficha de Proyecto`. Tres cosas, verificadas contra `5a2d0ea` el
26-10-2026, hacen que eso cueste una hora en vez de diez segundos:

1. **La causa se anota y se descarta.** `contexto_proyecto.resolver` escribe en el acumulador `la Ficha de Proyecto:
   no hay ningun issue de tipo "…" en el proyecto …` (`bin/contexto/proyecto.py:64`). `_observar_por_ficha`
   (`bin/dev-harness.py:898`) recibe ese acumulador, no lo mira, y devuelve el texto fijo `no se pudo resolver la
   Ficha de Proyecto del ticket %s` (`dev-harness.py:923`), que además `_aceptar` ni siquiera imprime. Para encontrar
   la causa hubo que correr `contexto` y leer el código.
2. **Nadie dice cuál es el tipo con que se busca ni de dónde sale.** `TIPO_POR_DEFECTO = "Ficha de Proyecto"`
   (`proyecto.py:16`) se pisa con la clave `fichaTipoDeIssue` de `.claude/harness.config.json`, y esa clave figura solo
   en `UPGRADE.md` 0.16.0 → 0.17.0. `setup` muestra qué variables del `.env` hay y no muestra este valor.
   Tampoco hay ayuda cuando el ticket que se pasó es la propia Ficha, con su tipo real a la vista.
3. **El aviso de un hash faltante nombra un canal que no se está usando.** `registro_fuentes.hallazgos` escribe siempre
   `(fuentes --archivo <dir> --aceptar <ID>)` (`bin/orquestacion/registro_fuentes.py:188`), también cuando la persona
   corrió `fuentes APWIGELEC-108` y el canal es la Ficha.

## Qué queda afuera

- **Cambiar el default a `.ASI Ficha de proyecto`.** Nadie escribió si todos los proyectos de ese Jira usan ese nombre,
  y un default que sirve a un proyecto y rompe a los demás es peor que uno que se explica. Queda en FH con su
  condición; si se confirma, es un cambio de una línea y el escenario E-03 se mueve con él.
- **Elegir el tipo de la Ficha consultando a Jira** (listar los tipos de issue del proyecto y quedarse con uno que
  parezca). `proyecto.py` ya dice por qué no: elegir por un criterio que nadie escribió deja el contexto con sello de
  resuelto sobre una elección invisible. Esta spec **sugiere** el valor y la persona lo escribe; no lo adivina.
- **Que `setup` vuelva a preguntar.** `setup` dejó de preguntar en 0.26.0 (la configuración salió al `.env`) y no hay
  `input()` en el harness. El hallazgo 1 del registro, el `EOFError`, ya no se reproduce y no se reabre.
- **Mostrar en `setup` otras claves de `harness.config.json`** (`prefijoApi`, `topeTextoDocumento`, …). Solo el tipo de
  la Ficha, que es la que falló; el resto no tiene un hallazgo detrás.
- **Los hallazgos 5 a 12 del registro** (tags, licencia, `[ES0903]` en un test, la salida del `-Update`, el árbol que no
  dice su versión, el `[a11y]`): cada uno es su propio cambio y está en FH.
- **El texto de los otros avisos de `hallazgos`** (`el registro de fuentes no valida`, `esta declarada dos veces`,
  `declara el extracto … y no esta en este arbol`). Solo cambia el del hash faltante.

## Las decisiones, y por qué

### La sugerencia del tipo vive en el resolvedor de la Ficha, no en `fuentes`

`_observar_por_ficha` llama a `contexto_proyecto.resolver`, el mismo del Bloque 2, y su docstring dice por qué: «una
segunda búsqueda con un criterio parecido es como un día una encuentra la Ficha y la otra no». Poner la sugerencia en
`fuentes` dejaría `contexto` sin ella, que es el comando donde la persona ya mira esa causa. En el resolvedor sale en un
solo lugar y la ven los dos comandos.

### «Se parece» es contención del nombre, sin mayúsculas, y distinto

Se compara el nombre del tipo del ticket que se pasó con el tipo buscado, ambos en minúsculas: se parece si uno contiene
al otro y los dos nombres no son iguales. Es decidible sin red, cubre el caso real (`.asi ficha de proyecto` contiene
`ficha de proyecto`) y no se dispara con `Historia`, `Bug` o `Task`. Se descartaron tres alternativas: una lista
cerrada de palabras («ficha»), que el próximo nombre ajeno ya no cumple; una distancia de edición, que hay que
calibrar y no tiene un número que defender; y preguntarle a Jira, que es la opción que quedó afuera arriba.
**Falso negativo aceptado:** un tipo con otro nombre (`Project Card`) no dispara la sugerencia, y la causa de siempre
sigue diciendo qué tipo se buscó.

### La causa que sale es la que el acumulador anotó, sin reescribirla

Lo que `fuentes` imprime y lo que el rechazo de `--aceptar` agrega sale del acumulador: lo que faltó, los conflictos y
las capacidades que no estaban. No se redacta una causa nueva en `dev-harness.py`: dos redacciones de lo mismo son la
manera de que un día digan cosas distintas. Si el acumulador no tiene nada, el mensaje es el de hoy.

### La causa no entra en el canal que se guarda

Se descubrió al construir: lo que `_observar_por_ficha` devuelve como canal se escribe tal cual en
`harness.fuentes.json` (`"ficha": canal`, `frescura.py:473`) y sale por `--json`. Meter la causa en su `reason` habría
cambiado ese documento, y la causa es de esta corrida, no del estado. Por eso viaja por una lista que pasa quien llama
(`causas`), que `resolver_fuentes` imprime y `_aceptar` agrega al rechazo; el canal queda como en 0.36.0 (E-16). El
camino `--auto`, el otro llamador de `_observar_por_ficha`, no pasa la lista y no cambia.

### `hallazgos` recibe el canal que la persona pidió

`registro_fuentes.hallazgos` solo tiene el documento y hoy escribe un texto fijo. Con una clave de Jira, el aviso sugiere
`fuentes <CLAVE> --aceptar <ID>`; con `--archivo`, queda como hoy; sin ninguno de los dos, nombra las dos formas. Fuera de
los tests, su único llamador es `resolver_fuentes` (`dev-harness.py:793`); los tests que la llaman directo son lo que el
cambio de firma puede tocar, y el builder los revisa.

### `setup` muestra una línea con el tipo y su origen

Una línea al final de lo que `setup` ya muestra: el tipo con que se busca la Ficha y si es el por defecto o lo puso el
proyecto en `.claude/harness.config.json`. No es una pregunta ni un campo que `setup` escriba.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/bin/contexto/proyecto.py` | Cuando no hay ningún issue del tipo buscado y el tipo del ticket se parece, la causa lo dice con el tipo real y nombra `fichaTipoDeIssue` |
| `harnesses/desarrollo/bin/dev-harness.py` | `_observar_por_ficha` lleva la causa del acumulador a la salida y al rechazo de `--aceptar`; `setup` imprime el tipo y su origen; `resolver_fuentes` le pasa a `hallazgos` el canal |
| `harnesses/desarrollo/bin/orquestacion/registro_fuentes.py` | `hallazgos` sugiere el comando del canal en uso |
| `tests/casos/79_ficha_y_fuentes_que_se_explican.py` y su línea en `tests/parallel-manifest.json` | Los escenarios E-01 a E-16, con el Jira simulado de `19_contexto.py` y `dev-harness.py` en proceso como en `67_integracion_frescura.py` |
| `docs/contexto-de-tarea.md` | Dónde se configura `fichaTipoDeIssue` y qué dice el harness cuando no encuentra la Ficha |
| `tests/casos/65_contrato_de_ejecucion.py` (EX-G11), `72_motor_de_ejecucion.py` (ME-E49), `74_knowledge_api.py` (KA-E53) y `63-harness-unico-instalador.ps1` (E-16) | Adaptadas con «Pisado por» como en 0.36.0, sin aflojarlas: las tres de Python saltean solo `orquestacion/registro_fuentes.py` y exigen que, contra la base, solo `hallazgos` cambió, solo `como_aceptar` se agregó y el resto del módulo es igual (por AST); la de PowerShell saltea en E-16 los dos archivos instalados que el cambio modifica y exige que lo instalado sea lo que hay en la fábrica. No se agregan archivos: E-15 sigue igual |
| `CHANGELOG.md`, `UPGRADE.md`, `docs/versiones/` | Al cerrar, con `close-a-version`: `-Update` alcanza, no hay nada manual; el hallazgo sale de FH |

## Escenarios verificables

### El tipo con que se busca la Ficha se ve

- **E-01** — `setup`, sin la clave `fichaTipoDeIssue`, imprime una línea con `Ficha de Proyecto` como tipo de issue y
  dice que es el valor por defecto. · rojo visto: sí
- **E-02** — `setup`, con `fichaTipoDeIssue: ".ASI Ficha de proyecto"` en `.claude/harness.config.json`, imprime esa
  línea con `.ASI Ficha de proyecto` y dice que lo puso el proyecto. · rojo visto: sí
- **E-03** — Sin la clave, la búsqueda de la Ficha sigue siendo por `Ficha de Proyecto`: este cambio no mueve el default.
  · rojo visto: sí

### La causa llega a la persona

- **E-04** — Con un Jira donde el proyecto no tiene ningún issue del tipo buscado, `fuentes <CLAVE>` imprime la causa:
  el tipo buscado y la clave del proyecto, además de `ficha=ninguna`. · rojo visto: sí
- **E-05** — Con `--aceptar`, el rechazo incluye esa misma causa, y sigue sin escribir `harness.fuentes.json` y saliendo
  con el mismo código que hoy. · rojo visto: sí
- **E-06** — Con más de una Ficha en el proyecto, la salida dice el conflicto (cuántas y cuáles claves), no el texto
  genérico. · rojo visto: sí
- **E-07** — Con `jira.issue.search` no disponible, la salida dice que esa capacidad falta. · rojo visto: sí
- **E-08** — Con Jira contestando un error al buscar la Ficha, la salida dice el código que contestó. · rojo visto: sí

### La sugerencia del tipo

- **E-09** — Si no hay Ficha y el ticket que se pasó es de tipo `.ASI Ficha de proyecto` con el tipo buscado por defecto,
  la causa nombra el tipo real del ticket y `fichaTipoDeIssue`, en `fuentes` y en `contexto`. · rojo visto: sí
- **E-10** — Si no hay Ficha y el ticket es de un tipo que no se parece (una historia), la causa es la de hoy y no nombra
  `fichaTipoDeIssue`. · rojo visto: sí
- **E-11** — Si hay una Ficha, ni `fuentes` ni `contexto` agregan causa ni sugerencia, y el resultado es el de hoy.
  · rojo visto: sí

### El aviso del hash faltante nombra el canal en uso

- **E-12** — Con una fuente sin hash y la corrida `fuentes <CLAVE>`, el aviso sugiere `fuentes <CLAVE> --aceptar <ID>` y
  no contiene `--archivo`. · rojo visto: sí
- **E-13** — Con la corrida `fuentes --archivo <dir>`, el aviso es el de hoy, `fuentes --archivo <dir> --aceptar <ID>`.
  · rojo visto: sí
- **E-14** — Sin clave ni `--archivo`, el aviso nombra las dos formas. · rojo visto: sí

### Lo que no cambia

- **E-15** — Los demás avisos de `hallazgos` (registro que no valida, fuente repetida, extracto ausente) salen con el
  mismo texto que en `v0.36.0`. · rojo visto: sí
- **E-16** — Con `--json`, el documento que `fuentes` escribe en la salida estándar es el mismo que en `v0.36.0` para
  los mismos datos: la causa y la sugerencia van a la consola, no al documento. · rojo visto: sí

## Cómo se verifica

Los dieciséis escenarios pasan por la suite y ninguno se lee. Todos corren `dev-harness.py` en proceso
(`main(args, transporte, transporte_bytes)`) contra el `Transporte` falso de `19_contexto.py`, como
`67_integracion_frescura.py`: E-01 y E-02 corren `setup`, E-03 a E-08 y E-12 a E-16 corren `fuentes` y E-09 y E-11
corren además `contexto`. E-09 y E-10 prueban también la relación «se parece» sobre el resolvedor. E-15 y E-16 no
comparan contra el blob de `v0.36.0`: clavan por literal los textos de `v0.36.0` que no deben cambiar, como
`45_conocimiento_fuentes.py` y `61_conocimiento_auto_refresco.py`, y así no piden un clon con tags. Los tests
nombran su escenario en el título o en un comentario. El rojo visto de los dieciséis salió de veinte mutaciones del
código (cada una rompe una cosa y vuelve atrás): cada escenario se puso en rojo con al menos una.

## Riesgos conocidos

- **«Se parece» puede sugerir un tipo equivocado.** Un tipo que contiene `ficha de proyecto` pero es otra cosa (una
  `Ficha de proyecto archivada`) dispara la sugerencia. Solo sugiere, no cambia nada, y la persona es quien escribe el
  valor.
- **El falso negativo de E-10 es real** para un tipo con otro nombre. La causa de siempre sigue diciendo qué tipo se buscó.
- **Guardas de Tasks cerradas pueden fijar estos archivos.** Pasó con 0.36.0: seis guardas (61, 63, 64, 65, 72, 74)
  fijaban «sin cambios» sobre archivos que ese cambio tocaba a propósito y se adaptaron con «Pisado por». Los tres
  archivos de esta spec se instalan en los proyectos, así que la primera corrida completa puede encontrar otras.
- **La causa viene del acumulador y el acumulador no se redacta.** Si un resolvedor futuro anota ahí algo que no debería
  salir por consola, esta spec lo imprime. Hoy lo que anota `proyecto.py` es el tipo, la clave del proyecto y claves de
  issues.
- **Conflictos al unir con la 6.2.** Las dos tocan `CHANGELOG.md`, `UPGRADE.md`, `docs/versiones/README.md`,
  `tests/parallel-manifest.json` y `PENDIENTES-FH.md`, y el cierre del segundo tiene que renumerar.

## Enmienda posterior (26-10-2026)

Posterior a la aprobación, hecha al construir. No cambia ningún escenario, el alcance ni lo que queda afuera; sí
precisa tres cosas de lo que se escribió antes:

- **La causa viaja aparte del canal** (decisión nueva, «La causa no entra en el canal que se guarda»): el canal se
  persiste y el escenario E-16 pide que el documento no cambie.
- **«Cómo se verifica» describe lo construido:** todos los escenarios corren `dev-harness.py` en proceso; E-15 y E-16
  clavan literales de `v0.36.0` y no comparan contra un blob de git.
- **«Qué se construye» suma cuatro guardas de Tasks cerradas** que la primera corrida encontró y se adaptaron con
  «Pisado por» (65, 72, 74 y el instalador de 63), como en 0.36.0.
