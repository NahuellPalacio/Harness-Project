# Lectura de los nueve escenarios de contrato — `iniciador-code`

> 🔴 **SIN FIRMAR.** Ningún escenario de este archivo está leído todavía. Mientras esté así, el
> refutador los rinde `sin sustento` y el cambio no cierra. **Un papel vacío no es una lectura.**

**Quién puede firmar:** cualquiera **menos quien construyó**. Es la misma regla del refutador y por
el mismo motivo: para quien construyó, cada decisión tuvo una razón en su momento.
[`recorrido-real.md`](recorrido-real.md) **no sirve** para esto, y lo dice en su propio encabezado.

**Qué es esto:** la vía de verificación que [ADR-0009](../../adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md)
define para los escenarios cuyo sujeto es una corrida de un agente con modelo. La suite de este
repositorio son 399 tests deterministas y sin red: no invoca modelos, y por eso ninguno de estos
nueve va a tener test nunca.

**Qué NO es:** una prueba. Un `leído` cierra un cambio y vale menos que un `sostenido`. La
diferencia se cuenta aparte, a propósito.

## Cómo se llena

1. **Correr el agente una vez** sobre un repositorio real. `dev-iniciador-code`, lanzado a mano.
   El del 21-08-2026 sobre este repo costó 140.840 tokens y 9 min 45 s — el número está en
   `recorrido-real.md` y sirve para saber a qué se entra.
2. **Contrastar la salida contra cada escenario**, uno por uno, con la spec al lado.
3. **Escribir en `Observado` qué se vio**, no si estaba bien. *"Las 13 fichas quedaron en
   `docs/codebase/` y `git status` no muestra ningún otro archivo tocado"* es una observación.
   *"Cumple"* no es nada.
4. **Firmar arriba**, con fecha y nombre.

📌 **Un escenario que no se pudo observar se deja vacío y se dice por qué.** Rellenarlo para que
el cambio cierre es exactamente lo que esta vía existe para no hacer.

---

**Leyó:** _(sin firmar)_ · **Fecha:** _(sin fecha)_ · **Corrida sobre:** _(qué repositorio)_

---

## E-07 — Terminado un recorrido, existe `docs/codebase/indice.md`

Mirar que el recorrido haya terminado y que el archivo esté. El caso interesante es el contrario:
si el agente cortó a la mitad, quedan fichas sin índice.

**Observado:**

## E-11 — El recorrido no escribe ni modifica nada fuera de `docs/codebase/`

`git status` después de la corrida, sobre un árbol que estaba limpio antes. Cualquier archivo
tocado afuera del directorio del índice incumple, incluido un `TODO` en un archivo ajeno.

**Observado:**

## E-12 — Un archivo ignorado por `.gitignore` no produce ficha ni aparece en el índice

Se resuelve por construcción —el agente lista con `git ls-files`— y lo que hay que mirar es que
efectivamente lo haya hecho. Buscar en el índice algo que esté en `.gitignore`:
`.claude/harness/`, `__pycache__/`, cualquier salida de build.

**Observado:**

## E-13 — Un segundo recorrido no duplica fichas

Requiere correr el agente **dos veces** sobre el mismo repositorio sin cambios. El conjunto de
nombres de archivo tiene que ser el mismo: ni `comun-hooks-1.md`, ni `comun-hooks (2).md`.

**Observado:**

## E-14 — Una ficha huérfana se reporta y no se borra

Preparar el caso: renombrar o borrar un módulo que ya tenía ficha, y volver a recorrer. La ficha
vieja tiene que seguir en su lugar y estar nombrada en el informe.

**Observado:**

## E-15 — El informe dice cuántas escribió, cuántas dejó igual y qué no recorrió

Se lee el informe que devolvió el agente. Las tres cosas, no dos.

**Observado:**

## E-16 — El informe no contiene código fuente del proyecto

Ni un bloque de código, ni una línea citada de un archivo recorrido. Es la invariante que hace que
delegar el recorrido valga la pena: si el material vuelve en la respuesta, se pagó la ventana que
el recorrido venía a ahorrar.

**Observado:**

## E-17 — Sobre un repositorio sin código no escribe nada, y lo dice

Requiere un repositorio vacío o de sola documentación. Lo que incumple es un `indice.md` vacío:
promete que había algo que mirar.

**Observado:**

## E-20b — Sin `rutaCodebase`, el agente escribe en `docs/codebase`

Correr sobre un proyecto **sin** la clave en `harness.config.json` —o sin el archivo— y mirar
dónde quedó el índice. El default del agente es una línea de su contrato, no código.

**Observado:**
