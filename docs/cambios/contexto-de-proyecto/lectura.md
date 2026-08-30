# Lectura de E-20 — `contexto-de-proyecto`

**Quién puede firmar:** cualquiera **menos quien construyó**. Es la misma regla del refutador y por
el mismo motivo: para quien construyó, cada decisión tuvo una razón en su momento.

**Qué es esto:** la vía de verificación que [ADR-0009](../../adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md)
define para los escenarios cuyo sujeto es una corrida de un agente con modelo. La suite de este
repositorio son 558 tests deterministas y sin red: no invoca modelos, y por eso E-20 no va a tener
test nunca. Los otros 27 escenarios de esta spec están sostenidos por la suite —ver
[`verificacion.md`](verificacion.md)—; este es el único que no.

**Qué NO es:** una prueba. Un `leído` cierra un cambio y vale menos que un `sostenido`. La
diferencia se cuenta aparte, a propósito.

## Cómo se llena

1. **Correr `dev-iniciador-code` una vez** sobre un repositorio real, a mano. El banco de pruebas
   armado el 24-08-2026 está en `C:\Users\Asus\lecturas-0.14.0\` y su `LEEME.md` dice qué mirar;
   `reservas` es el que sirve para este escenario. Cualquier otro repositorio real sirve igual.
2. **Abrir el `project-context.json` que dejó** y contrastarlo contra lo que hay de verdad en el
   repositorio recorrido.
3. **Escribir en `Observado` qué se vio**, no si estaba bien. *"El `purpose` dice `plataforma de
   reservas de espacios` y el repositorio tiene `src/api/reservas.ts` y una tabla `reservas`"* es
   una observación. *"Cumple"* no es nada.
4. **Firmar arriba**, con fecha y nombre.

📌 **Si el escenario no se pudo observar se deja vacío y se dice por qué.** Rellenarlo para que el
cambio cierre es exactamente lo que esta vía existe para no hacer.

---

**Leyó:** Nahue Palacio · **Fecha:** 30-08-2026 · **Corrida sobre:** `C:\Users\Asus\lecturas-0.14.0\reservas`

---

## E-20 — El contrato de un recorrido real describe el proyecto que recorrió y no lo inventa

Las dos mitades que nombra el escenario, y conviene mirarlas por separado:

- **`project_profile.purpose`** — qué dice que es el proyecto, contra lo que el proyecto es. Lo que
  incumple no es una redacción pobre: es un propósito que describe otra cosa, o que está tan vacío
  de contenido que serviría para cualquier repositorio.
- **`technology`** — `languages`, `frameworks`, `package_managers`, `build_commands` y
  `test_commands` contra lo que hay en el árbol. Un framework declarado que no aparece en ningún
  manifiesto ni import es una invención; un comando de test que no existe en `package.json` también.

📌 Mirar también el `knowledge_status` de los dos bloques. Si el agente no encontró algo, lo que
corresponde es que quede `missing` y viaje en `gaps_and_conflicts`, no que se complete con una
inferencia: un hueco declarado es un hueco, y un hueco completado es indistinguible de un hecho
para quien lea después.

**Observado:** El `purpose` describe una plataforma de reservas de espacios con calendario y
conciliación de cobros, y el repo tiene exactamente eso: `src/web/calendario.tsx`,
`src/api/reservas.ts`, `worker/cobros.py`. La tecnología declarada (Next.js, Express, Postgres vía
`pg`, Python) coincide con `package.json` y la estructura real. El `lifecycle_stage` quedó
`unknown` — declarado como hueco, no inventado — y está bien que quede así: se completa después si
hace falta.
