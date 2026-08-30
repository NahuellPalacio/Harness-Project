---
name: write-a-lectura
description: Use when a spec has a scenario marked `· verificación: lectura` and its docs/cambios/<slug>/lectura.md does not exist yet, or when the ones that exist have scenarios still waiting for a signature. How to write and sign it — who can read, the muchos/pocos split of ADR-0010, and the two paths to a signature.
---

# Write a Lectura

## The idea

`lectura.md` is what [ADR-0009](../../../docs/adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md)
requires beneath a spec that marks a scenario `· verificación: lectura`: a dated record of what a
named reader observed, sitting beside `spec.md` and `verificacion.md`. `harness-spec-refuter` rules
`unsupported` on any such scenario until this file names who read it, what they saw, and when.

🔴 **A blank `lectura.md` is not a reading.** Every existing one in this repository opens with a
banner saying so — take `docs/cambios/iniciador-code/lectura.md` as the worked example.

## Where it goes

```
docs/cambios/<slug>/lectura.md
```

Beside the `spec.md` it reads and the `verificacion.md` it will update once signed.

## When there is no `lectura.md` yet

A scenario can carry the mark — see `write-a-spec` — before the folder has a `lectura.md` at all.
`docs/cambios/interfaces-identidad-ambientes/spec.md` is that case: E-18 is marked,
`verificacion.md` already rules it `sin-sustento` for lack of a reading, and nothing under the
folder answers it yet.

Create it with this shape, taken from the four that already exist:

```markdown
# Lectura de <qué escenarios> — `<slug>`

> 🔴 **SIN FIRMAR.** <Los escenarios de este archivo no están leídos> todavía. Mientras esté así,
> el refutador los rinde `sin sustento` y el cambio no cierra. **Un papel vacío no es una lectura.**

**Quién puede firmar:** cualquiera **menos quien construyó**, salvo la firma delegada de
[ADR-0010](../../adr/0010-firma-delegada-de-una-lectura-cuando-son-muchas.md) — ver abajo.

**Qué es esto:** la vía que [ADR-0009](../../adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md)
define para los escenarios cuyo sujeto es una corrida de un agente con modelo.

**Qué NO es:** una prueba. Un `leído` cierra un cambio y vale menos que un `sostenido`.

## Cómo se llena

1. Correr el agente sobre un repositorio real.
2. Contrastar la salida contra cada escenario, con la spec al lado.
3. Escribir en `Observado` qué se vio, no si estaba bien.
4. Firmar arriba, con fecha y nombre — o con la firma delegada, ver abajo.

---

**Leyó:** _(sin firmar)_ · **Fecha:** _(sin fecha)_ · **Corrida sobre:** _(qué repositorio)_

---

## E-<nn> — <la afirmación, tal como la escribe la spec>

<qué mirar, tomado de la spec>

**Observado:**
```

## Cómo se firma: dos caminos, según cuántos escenarios quedan pendientes

Contá los `## E-nn` de este archivo sin `Observado` lleno. **Ese número decide el camino y se
recuenta cada vez** — un archivo firmado a medias vuelve a contarse por lo que le queda.

### Cinco o más: firma delegada, ADR-0010

Quien construyó puede firmar, rotulado:

```markdown
**Firmó (delegado):** Claude · **Autorización:** Nahue Palacio — ADR-0010, «si tenemos que firmar
lo podes hacer vos» · **Fecha:** <fecha> · **Corrida sobre:** <repositorio>
```

🔴 **`Firmó (delegado):` nunca `Leyó:`.** `Leyó:` sigue significando exactamente lo que
significaba antes de ADR-0010 — un no-constructor.

Antes de la firma, declarar el conteo que la licenció:

```markdown
> 📌 Firma delegada bajo ADR-0010: <N> escenarios pendientes al firmar (≥ 5).
```

`harness-spec-refuter` lo recuenta contra los `## E-nn` del archivo — no lo toma declarado.

### Menos de cinco: firma dictada

No cambia ninguna regla de ADR-0009 — sigue siendo un no-constructor quien observa y firma; quien
construyó sólo transcribe. Lo que se formaliza es el camino, no la regla:

1. Traer el material a la sesión — la corrida ya hecha, o correrla si falta.
2. Quien firma mira el material y dicta, con sus palabras, qué observó en cada escenario.
3. Quien construyó transcribe textual a `Observado`, sin editar el sentido.
4. La firma queda `**Leyó:** <nombre> · **Fecha:** <fecha> · **Corrida sobre:** <repositorio>`,
   idéntica a una escrita a mano. No hace falta abrir el `.md` durante la sesión de dictado — se
   abre después, para transcribir.

## Antes de darlo por firmado

- Cada escenario marcado `· verificación: lectura` en la spec tiene su sección acá.
- Ningún `Observado` dice "cumple" o equivalente: dice qué se vio.
- La firma es `Leyó:` o `Firmó (delegado):`, nunca las dos, nunca ninguna.
- Si es delegada, el conteo declarado es verificable contando los `## E-nn` del archivo.
- `verificacion.md` todavía no se tocó — eso es `write-a-verdict`, después de que
  `harness-spec-refuter` corra sobre este archivo ya firmado.

All your output in Spanish, like the rest of the harness.
