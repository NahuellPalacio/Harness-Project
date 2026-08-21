# El estado del mapa se declara en la nota de versión

**Estado:** especificado · **Fecha:** 2026-08-20

`close-a-version` tiene desde hoy un paso 7 —actualizar `docs/mapa/recorrido-mensaje.html` cuando
la versión movió el flujo— y ese paso no lo mide nadie. Este cambio no intenta medir el paso:
intenta que su ausencia sea **visible**. Es la misma jugada que `rojo visto`.

## Qué problema resuelve

El mapa del harness es un diagrama de flujo publicado, con una URL que la gente comparte. Su
único valor es estar al día: **un mapa desactualizado miente con la autoridad de un diagrama**, y
se lo cree más que a un párrafo desactualizado.

El paso 7 de `close-a-version` pide actualizarlo. Pero `tests/casos/08-bitacora.ps1` —el test que
existe justamente porque *"lo que nadie mide, no se hace"*— manda sobre seis archivos y no sabe
nada del mapa. Hoy una versión puede mover un matcher, cerrar en verde, y dejar el diagrama
mintiendo sin que nada lo note.

No se puede verificar mecánicamente que un diagrama sea correcto. Sí se puede exigir que alguien
haya **mirado** y declarado qué pasó, y que esa declaración esté donde se lee. Es el mismo
razonamiento con el que existe `rojo visto` en las specs: la marca no prueba que el rojo se vio,
pero hace que no verlo cueste escribir que no consta.

## Qué queda afuera

- **Verificar que el mapa sea correcto.** Ninguna máquina puede contrastar un SVG contra el
  comportamiento de cuatro hooks. Si se pudiera, no haría falta el mapa.
- **Rellenar las trece notas existentes.** El mapa no existía cuando se escribieron: poner
  `mapa: sin cambios` en `0.4.0` sería inventar un hecho que nadie comprobó, y la bitácora tiene
  *no inventar* como regla explícita. Se aplica desde un piso hacia adelante.
- **Cruzar la declaración contra git.** Se consideró y se descartó; el motivo está abajo.
- **Tocar las cinco secciones obligatorias.** El marcador va en la cabecera, no en una sexta
  sección. Las cinco secciones están citadas literalmente en el test, en la plantilla, en el
  README de la bitácora y en la skill: cambiar ese número es un cambio caro para meter un renglón.
- **Cualquier verificación de red.** El test no consulta la URL del artifact. Una suite que
  depende de internet falla en el tren y no dice por qué.
- **El mapa en un proyecto instalado.** Esto es de la fábrica. Nada de esto se copia con
  `install.ps1` ni entra en ningún manifiesto.

## Las decisiones, y por qué

### El marcador va en la línea de cabecera, no en una sección nueva

```
> 17-08-2026 · 318 tests en verde · mapa: sin cambios
```

La cabecera ya es el renglón de los hechos declarados y contables: fecha, commit, cantidad de
tests. El estado del mapa es de esa familia. Una sexta sección para un renglón obliga a tocar los
cuatro lugares donde "las cinco secciones" está escrito y deja una sección que casi siempre dice
una línea.

El formato de la cabecera **varía hoy entre notas** —`0.1.0` y `0.7.0` traen `commit`, `0.12.0` y
`0.13.0` no— así que el check no puede exigir una forma completa. Exige que la línea que empieza
con `>` contenga `mapa: <valor>`, y nada más sobre el resto.

### Dos valores, no tres

| | |
|---|---|
| `sin cambios` | La versión no tocó nada de lo que el mapa dibuja |
| `actualizado` | Lo tocó, y el mapa se republicó contra su URL |

Es literal la regla de `rojo visto`: *"ofrecer tres valores invita a elegir el que queda mejor"*.
No hay `no aplica` ni `pendiente`. Una versión que movió el flujo y no actualizó el mapa **no
tiene marcador que la describa**, y esa incomodidad es el punto: la salida es actualizar el mapa,
que cuesta dos cajas.

### Es una declaración, y se dice que lo es

El check verifica que el marcador esté y que su valor sea uno de los dos. No verifica que sea
cierto. Alguien puede escribir `sin cambios` después de haber movido un matcher, igual que alguien
puede escribir `rojo visto: si` sin haber roto nada.

Lo que se compra es que la omisión deje de ser gratis: hoy no actualizar el mapa no cuesta nada;
después de esto cuesta escribir a mano una afirmación falsa en un archivo versionado que alguien
más va a leer.

### Se descartó cruzar la declaración contra git

La idea tentadora: si la nota dice `actualizado`, que el test compruebe que `docs/mapa/*.html`
aparece en el diff de los commits de esa versión. Se descarta por tres motivos, en orden de peso:

1. **El sha de la cabecera es texto escrito a mano**, y hay notas que directamente no lo traen. El
   test tendría que adivinar el rango de commits de una versión.
2. **Ata la suite al historial de git.** Un rebase, un squash o un clon con `--depth 1` la ponen
   en rojo por algo que no tiene nada que ver con lo que se está testeando.
3. Comprobaría que el archivo se tocó, no que el mapa quedó bien. **Un `git diff` no distingue
   corregir el diagrama de arreglarle una coma.** Compra mucha menos verdad de la que aparenta.

### El piso es una constante única en el test

Las notas anteriores al piso pasan sin marcador. El piso es la versión en la que cierre este
cambio, y vive en **una sola línea** de `08-bitacora.ps1`, con su comentario. No se deduce de
fechas ni de la existencia de archivos: se lee.

📌 **El número del piso se completa al cerrar la versión, no ahora.** Escribirlo hoy sería
inventar en qué versión va a entrar esto.

### Se agrega una comprobación que sí es mecánica

Cada `.html` de `docs/mapa/` tiene que llevar la URL de su artifact en un comentario de cabecera.
Eso no es cosmético: es lo único que permite republicar contra la misma dirección desde otra
sesión. Sin esa URL, la próxima actualización crea un artifact nuevo y **deja huérfano el link que
alguien ya compartió** — el modo de falla real de todo este arreglo, y el único verificable de
verdad.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `tests/casos/08-bitacora.ps1` | Tres aserciones nuevas: el marcador existe en las notas ≥ piso, su valor es uno de los dos, y cada `.html` de `docs/mapa/` lleva su URL |
| `docs/versiones/_plantilla.md` | La cabecera trae el marcador, con los dos valores a la vista |
| `docs/versiones/README.md` | El marcador, sus dos valores y el piso, en «Cómo se escribe una» |
| `.claude/skills/close-a-version/SKILL.md` | El paso 2 pide el marcador; el paso 7 deja de decir que nada lo mide |
| `docs/versiones/<piso>.md` | La primera nota que lo lleva |

## Escenarios verificables

### El marcador en la nota

- **E-01** — Una nota de versión posterior o igual al piso, sin `mapa:` en su línea de cabecera,
  pone la suite en rojo y el mensaje nombra la nota. · rojo visto: no consta
- **E-02** — Un marcador con un valor que no es `sin cambios` ni `actualizado` —`mapa: n/a`,
  `mapa: pendiente`— pone la suite en rojo. · rojo visto: no consta
- **E-03** — Las dos formas válidas pasan, y pasan con el resto de la cabecera en cualquiera de
  las variantes que hay hoy: con `commit`, sin `commit`, y con el detalle de motores entre
  paréntesis de `0.13.0`. · rojo visto: no consta
- **E-04** — Las trece notas anteriores al piso pasan sin marcador y sin aviso. La suite queda en
  verde con el repo tal como está el día que esto entra. · rojo visto: no consta
- **E-05** — El marcador solo cuenta en la línea de cabecera: un `mapa: actualizado` escrito en
  medio del cuerpo de la nota **no** satisface el check. Sin esto, cualquier prosa que hable del
  mapa lo satisface por accidente. · rojo visto: no consta
- **E-06** — El piso vive en una sola línea del test: cambiarlo mueve el corte y no hay que tocar
  nada más. · rojo visto: no consta
- **E-07** — El mensaje de falla dice **qué escribir y dónde** —el marcador, sus dos valores, la
  línea de cabecera—, no solo que falta. Es la misma regla que el motivo de un `deny`.
  · rojo visto: no consta

### La URL del mapa

- **E-08** — Un `.html` de `docs/mapa/` sin una URL de artifact en sus primeras líneas pone la
  suite en rojo. · rojo visto: no consta
- **E-09** — Los dos archivos que hay hoy —`recorrido-mensaje.html` y `mapa-harness.html`—
  pasan. · rojo visto: no consta
- **E-10** — Un `.html` nuevo dejado en `docs/mapa/` queda cubierto sin registrarlo en ningún
  lado. Es el mismo contrato de descubrimiento que tienen los checks. · rojo visto: no consta

### La plantilla y la documentación

- **E-11** — `_plantilla.md` no se evalúa como nota: el filtro de notas sigue siendo
  `^\d+\.\d+\.\d+$` y la plantilla no matchea. Pero su cabecera trae el marcador, así que quien
  copia la plantilla arranca con él puesto. · rojo visto: no consta

## Cómo se verifica

Todo va en `tests/casos/08-bitacora.ps1`, que ya está en PowerShell y ya lee las notas: son
aserciones sobre el mismo texto que el test carga hoy. No se agrega un caso nuevo ni se toca
`tests/correr.py`.

E-01, E-02, E-05 y E-08 se prueban rompiendo a propósito: se le saca el marcador a la nota del
piso, se le pone un valor inválido, se lo mueve al cuerpo, y se le saca la URL a un `.html`. Los
cuatro se restauran. 🔴 **Van con `finally`, y con la advertencia que el `CLAUDE.md` del repo ya
tiene escrita**: `03-instalador.ps1` rompe archivos versionados a propósito y su `finally` no
sobrevive a que maten el proceso. Si esta suite se corta a la mitad, revisar el árbol antes que
nada.

E-04 se verifica corriendo la suite contra el repo tal cual, sin tocar ninguna nota vieja.

E-07 lo lee una persona: que un mensaje sea útil no lo decide una aserción.

## Riesgos conocidos

- **`sin cambios` se vuelve el valor que se tipea sin pensar.** Es el riesgo central y no tiene
  defensa mecánica — es exactamente el que ADR-0006 le reconoce a `rojo visto`. Lo único que lo
  contiene es que el marcador se escribe en el mismo turno en que se mira el mapa, y que el paso 7
  de la skill dice qué mirar. Si dentro de tres versiones todas dicen `sin cambios` y el flujo se
  movió dos veces, el mecanismo falló y hay que discutir otro, no endurecer éste.
- **Un renglón más en el ritual de cierre.** Seis archivos ya son muchos. Se acepta porque el
  costo es una declaración de dos palabras en una línea que ya se escribe igual.
- **El piso se olvida en su única línea.** Si el cambio cierra en una versión y el piso quedó
  apuntando a otra, el corte queda mal y nadie se entera: las notas viejas siguen pasando y la
  nueva también. E-06 lo cubre como comportamiento, pero que el valor sea el correcto el día del
  cierre es parte del paso, no del test.
- **Dos mapas, un solo marcador.** El marcador no distingue cuál de los dos archivos se tocó. Se
  acepta: el que se mueve con el flujo es `recorrido-mensaje.html`, y partir el marcador en dos
  duplica el ritual para cubrir un caso que todavía no pasó.
