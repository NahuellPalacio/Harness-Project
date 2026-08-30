# Lectura de los cuatro escenarios de contrato — `mapa-de-nodos`

> 📌 **Firmada el 30-08-2026, dictada.** Cuatro escenarios — por debajo del umbral de cinco de
> [ADR-0010](../../adr/0010-firma-delegada-de-una-lectura-cuando-son-muchas.md) — así que no hay
> firma delegada acá: la lee y la firma Nahue, sobre el material real de
> [`recorrido-real.md`](recorrido-real.md), que quedó sin correr un segundo proyecto porque no
> había uno a mano hoy y el mecanismo ya está probado con esa corrida. Decisión tomada en esta
> sesión, reemplazando la del 22-08-2026 de esperar a un proyecto propio.

**Quién puede firmar:** cualquiera **menos quien construyó**. Es la misma regla del refutador y por
el mismo motivo: para quien construyó, cada decisión tuvo una razón en su momento.
[`recorrido-real.md`](recorrido-real.md) **no sirve** para esto, y lo dice en su propio encabezado:
es el registro de la corrida, escrito por quien construyó.

**Qué es esto:** la vía que [ADR-0009](../../adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md)
define para los escenarios cuyo sujeto es una corrida de un agente con modelo. La suite de este
repositorio son 455 tests deterministas y sin red: no invoca modelos, y por eso ninguno de estos
cuatro va a tener test nunca.

**Qué NO es:** una prueba. Un `leído` cierra un cambio y vale menos que un `sostenido`. La
diferencia se cuenta aparte, a propósito.

## La corrida

`dev-iniciador-code`, lanzado a mano el **22-08-2026** sobre un clon de `ProtfolioPersonal`
—40 archivos versionados, Next.js con TypeScript— con el harness instalado por `install.ps1`
(`-Harness desarrollo`, v0.13.0, 50 archivos en el lockfile). Costó 85.719 tokens y 7 min 38 s.

Se eligió un proyecto ajeno y no este repositorio por dos motivos: las fichas de acá ya estaban
enlazadas **a mano por quien construyó**, así que no habrían probado nada sobre el agente; y el
proyecto no es Python, de modo que el recorredor no puede apoyarse en lo que ya conoce de la
fábrica.

**El material está en el repo.** El clon vive en un directorio temporal de sesión, así que las
nueve fichas y el índice se copiaron enteros a [`recorrido-real.md`](recorrido-real.md), con la
matriz de aristas y las horas de escritura. `mapa.html` no se copió y no hace falta: el layout es
determinista, y `python comun/bin/mapa-codigo.py` sobre esas fichas lo reproduce byte por byte.

## Cómo se llena

1. **Abrir el material**: las nueve fichas y el índice están en
   [`recorrido-real.md`](recorrido-real.md), junto con lo que costó la corrida y lo que el agente
   reportó.
2. **Contrastar contra cada escenario**, uno por uno, con la spec al lado.
3. **Escribir en `Observado` qué se vio**, no si estaba bien. *"`components-sections.md` enlaza
   cinco fichas hermanas y nombra `framer-motion` y `zod` sin enlace"* es una observación.
   *"Cumple"* no es nada.
4. **Firmar acá abajo**, con fecha y nombre.

📌 **Un escenario que no se pudo observar se deja vacío y se dice por qué.** Rellenarlo para que el
cambio cierre es exactamente lo que esta vía existe para no hacer.

---

**Leyó:** Nahue Palacio · **Fecha:** 30-08-2026 · **Corrida sobre:** clon de `ProtfolioPersonal`
(22-08-2026), material completo en [`recorrido-real.md`](recorrido-real.md)

---

## E-01 — Todo módulo con ficha propia aparece enlazado

Abrir dos o tres fichas y mirar sus secciones `Qué expone` y `De qué depende`. Lo que hay que ver
es que un módulo del proyecto que tiene ficha esté escrito como enlace relativo a esa ficha
—`[data](data.md)`— y no mencionado al pasar.

El contrafáctico importa tanto como el caso: una dependencia **sin** ficha propia —una librería de
`node_modules`, el runtime— tiene que estar nombrada **sin** enlace. Si todo está enlazado o nada
lo está, el agente no está distinguiendo.

**Observado:** La matriz de aristas real: `app.md` enlaza a `components-layout.md`,
`components-sections.md`, `config.md`, `i18n.md`; `components-sections.md` enlaza a
`components-ui.md`, `data.md`, `i18n.md`, `lib.md`, `types.md` — los nueve enlaces son relativos,
sobre módulos con ficha propia. El contrafáctico se cumple: `config.md` nombra `next`,
`next-intl`, `tailwindcss` sin enlace (de `node_modules`, sin ficha); `components-sections.md`
nombra `framer-motion`, `zod`, `react-hook-form` igual, sin enlace.

## E-18 — Terminado un recorrido completo, están las fichas, `indice.md` y `mapa.html`

Listar el directorio del índice. Los tres, no dos. El caso que incumple es el mapa faltando con el
índice presente: significa que el paso 6 del procedimiento no corrió y nadie se entera.

**Observado:** Terminado el recorrido, `docs/codebase/` tiene los tres: las nueve fichas de
módulo, `indice.md` y `mapa.html` — diez archivos en total.

## E-19 — El mapa se regenera después del índice, no antes

Mirar la hora de modificación de `indice.md` y la de `mapa.html`. El orden importa porque el mapa
se arma leyendo las fichas y el índice se escribe último a propósito: un mapa generado antes
dibujaría un estado que el recorrido todavía no terminó de escribir.

**Observado:** Las nueve fichas se escribieron entre las 01:46:02 y las 01:48:05; `indice.md` a
las 01:48:14, después de todas las fichas; `mapa.html` a las 01:48:25, después del índice. El
orden se cumple: fichas, índice, mapa.

## E-20 — El reporte dice cuántos nodos y aristas quedaron, y nombra las huérfanas

Se lee el informe que devolvió el agente. Las tres cosas: nodos, aristas y **cuáles** son las
huérfanas, por nombre. Un informe que dice "hay una huérfana" sin nombrarla no sirve — la huérfana
es el hallazgo del mapa, y el que lee tiene que poder ir a mirarla.

**Observado:** El informe dice las tres cosas: "9 nodos, 20 aristas, 1 huérfana", y nombra la
huérfana con motivo: "La huérfana es `app.md` ... el App Router es el punto de entrada, lo invoca
Next.js y no lo importa ningún módulo del proyecto."
