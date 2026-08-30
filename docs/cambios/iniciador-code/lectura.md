# Lectura de los ocho escenarios de contrato — `iniciador-code`

> 📌 Firma delegada bajo [ADR-0010](../../adr/0010-firma-delegada-de-una-lectura-cuando-son-muchas.md):
> 9 escenarios pendientes al firmar (≥ 5). **E-12 salió del grupo el 30-08-2026** — pasó a la
> suite, ver `spec.md` — y esta firma queda con los ocho que restan; su sección de abajo se retiró
> con él, la firma en sí no se reabre.

**Quién puede firmar:** cualquiera **menos quien construyó** — salvo la firma delegada de arriba,
que ADR-0010 autoriza exactamente para este caso. Es la misma regla del refutador y por el mismo
motivo: para quien construyó, cada decisión tuvo una razón en su momento.
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

**Firmó (delegado):** Claude · **Autorización:** Nahue Palacio — ADR-0010, «si tenemos que firmar
lo podes hacer vos» · **Fecha:** 30-08-2026 · **Corrida sobre:** `C:\Users\Asus\lecturas-0.14.0\reservas`
(E-07, E-11, E-13, E-14, E-20b) y `C:\Users\Asus\lecturas-0.14.0\manual-operativo` (E-17);
E-15 y E-16 son sobre el informe de la corrida 3 en `reservas`. E-12 tenía su sección acá también
al firmar; salió el 30-08-2026 cuando pasó a la suite — ver `spec.md`.

---

## E-07 — Terminado un recorrido, existe `docs/codebase/indice.md`

Mirar que el recorrido haya terminado y que el archivo esté. El caso interesante es el contrario:
si el agente cortó a la mitad, quedan fichas sin índice.

**Observado:** `docs/codebase/indice.md` existe en `reservas` (672 bytes, 28-08-2026), junto con
`mapa.html`, `project-context.json`, `proyecto.md` y seis fichas de módulo. No quedó ninguna ficha
sin línea de índice ni ninguna línea de índice sin ficha — las diez fueron parte del mismo commit,
`156146d`.

## E-11 — El recorrido no escribe ni modifica nada fuera de `docs/codebase/`

`git status` después de la corrida, sobre un árbol que estaba limpio antes. Cualquier archivo
tocado afuera del directorio del índice incumple, incluido un `TODO` en un archivo ajeno.

**Observado:** `git show --stat 156146d` sobre `reservas` — el commit del primer recorrido — lista
diez archivos, los diez bajo `docs/codebase/`: `indice.md`, `mapa.html`, `project-context.json`,
`proyecto.md`, `scripts.md`, `src-api.md`, `src-db.md`, `src-legado.md`, `src-web.md`, `worker.md`.
960 líneas insertadas, ninguna eliminación, ningún archivo fuera del directorio.

## E-13 — Un segundo recorrido no duplica fichas

Requiere correr el agente **dos veces** sobre el mismo repositorio sin cambios. El conjunto de
nombres de archivo tiene que ser el mismo: ni `comun-hooks-1.md`, ni `comun-hooks (2).md`.

**Observado:** el commit `751d8fb` ("El segundo recorrido, sin cambios en el medio") modifica cinco
archivos existentes —`mapa.html`, `project-context.json`, `proyecto.md`, `src-api.md`,
`src-web.md`— y no agrega ninguno. El conjunto de nombres de `docs/codebase/` es idéntico antes y
después de la segunda corrida.

## E-14 — Una ficha huérfana se reporta y no se borra

Preparar el caso: renombrar o borrar un módulo que ya tenía ficha, y volver a recorrer. La ficha
vieja tiene que seguir en su lugar y estar nombrada en el informe.

**Observado:** tras borrar `src/legado/importador.ts` (commit `084cdfa`) y recorrer de nuevo,
`docs/codebase/src-legado.md` no aparece en el `git status` de la corrida —quedó sin tocar, con su
fecha del 24-08— y sigue en `indice.md:10`, marcada: *"🔴 Ficha vieja: el módulo ya no está en el
repositorio"*. El informe del agente la nombra explícitamente: *"El módulo ya no existe y la ficha
sigue ahí, sin tocar (...) Borrarla no me corresponde."* Las dos mitades se dan.

## E-15 — El informe dice cuántas escribió, cuántas dejó igual y qué no recorrió

Se lee el informe que devolvió el agente. Las tres cosas, no dos.

**Observado:** el informe de la corrida 3 (`corrida-3-informe.md`) dice las tres, por separado:
*"Escribí 5 fichas de módulo (...) Dejé 1 sin tocar: `src-legado.md`"* — escritas y dejadas
iguales, con números — y bajo "Lo que no recorrí" nombra `node_modules/`, `dist/`, `.env`,
`docs/adr/` y los `.md` de raíz, con el motivo de cada exclusión.

## E-16 — El informe no contiene código fuente del proyecto

Ni un bloque de código, ni una línea citada de un archivo recorrido. Es la invariante que hace que
delegar el recorrido valga la pena: si el material vuelve en la respuesta, se pagó la ventana que
el recorrido venía a ahorrar.

**Observado:** releído el informe completo de la corrida 3 —el que más material maneja, con
`.env`, secretos y el pipeline de por medio—: no hay un solo bloque de código ni una línea citada
de `src/*.ts`. Nombra archivos y rutas (`src/legado/importador.ts`, `.env`, `src-db.md`) pero
nunca su contenido.

## E-17 — Sobre un repositorio sin código no escribe nada, y lo dice

Requiere un repositorio vacío o de sola documentación. Lo que incumple es un `indice.md` vacío:
promete que había algo que mirar.

**Observado:** sobre `manual-operativo` (6 archivos versionados, ninguno código —confirmado
filtrando por extensión, resultado 0), el árbol quedó `git status` vacío después de la corrida y
`docs/codebase/` **no existe**. El informe lo dice de frente: *"No escribí nada. El repositorio no
tiene código"*, y nombra por qué no indexó `docs/` (prosa de mesa de ayuda, no un módulo).

## E-20b — Sin `rutaCodebase`, el agente escribe en `docs/codebase`

Correr sobre un proyecto **sin** la clave en `harness.config.json` —o sin el archivo— y mirar
dónde quedó el índice. El default del agente es una línea de su contrato, no código.

**Observado:** `reservas/.claude/harness.config.json` no tiene la clave `rutaCodebase` —cero
ocurrencias— y el índice quedó igual en `docs/codebase/indice.md`, el default declarado en el
prompt del agente.
