# Lectura de E-08 y E-09 — `dev-refutador-lee-el-contrato`

**Quién puede firmar:** cualquiera **menos quien construyó**. Es la misma regla del refutador y por
el mismo motivo: para quien construyó, cada decisión tuvo una razón en su momento.

**Qué es esto:** la vía que [ADR-0009](../../adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md)
define para los escenarios cuyo sujeto es una corrida de un agente con modelo. Los otros siete
escenarios de esta spec —E-01 a E-07— son propiedades mecánicas de un script o del texto de un
archivo, y están sostenidos por la suite; estos dos son sobre **lo que hace `dev-refutador` de
verdad** cuando corre contra un proyecto real, y ningún test determinista los alcanza.

**Qué NO es:** una prueba. Un `leído` cierra un cambio y vale menos que un `sostenido`. La
diferencia se cuenta aparte, a propósito.

## Cómo se llena

1. **Correr `dev-refutador` dos veces, sobre proyectos reales**:
   - Una vez sobre un proyecto con `docs/codebase/project-context.json` completo y válido — el
     banco de `C:\Users\Asus\lecturas-0.14.0\reservas` sirve, o cualquier otro con contrato.
   - Una vez sobre un proyecto **sin** `project-context.json`, o con uno roto a propósito
     —corromper el JSON a mano, o borrar un campo `required` y guardar—.
2. **Mirar lo que devolvió**, contra los dos escenarios de abajo.
3. **Escribir en `Observado` qué se vio**, no si estaba bien. *"La fila `DEV-003` cita
   `technology.frameworks: [\"Next.js\"]` del contrato para descartar una regla de Obelisco, y la
   columna `repo_revision` trae el sha corto"* es una observación. *"Cumple"* no es nada.
4. **Firmar arriba**, con fecha y nombre.

📌 **Si un escenario no se pudo observar se deja vacío y se dice por qué.** Rellenarlo para que el
cambio cierre es exactamente lo que esta vía existe para no hacer.

---

**Leyó:** Nahue Palacio · **Fecha:** 30-08-2026 · **Corrida sobre:** `C:\Users\Asus\lecturas-0.14.0\reservas`,
dos corridas sobre el mismo lote (`src/api/main.ts`, `src/api/reservas.ts`, `src/api/espacios.ts`),
una con `project-context.json` presente y otra con el archivo movido aparte y restaurado después
(mismo md5 antes y después: `9378becdf3e858270438f54826c4cfbc`)

---

## E-08 — Con contrato completo, `dev-refutador` lo lee, lo cita como evidencia y nombra el `repo_revision`

Tres cosas a mirar, por separado:

- **Que efectivamente lo haya leído.** Alguna fila de su salida menciona un campo real del
  `project-context.json` de ese proyecto —un lenguaje, un componente, una interfaz—, no una
  invención genérica.
- **Que lo use como evidencia, nunca como norma.** Ninguna fila cita el contrato en la columna
  `norma (skill · pág.)`. La norma sigue siendo una skill `dev-*` con su página.
- **Que la columna `repo_revision` traiga el valor real** del `meta.repo_revision` del contrato,
  no un `—` ni un valor inventado.

**Observado:** Las 14 filas de la corrida citan `repo_revision: d5ea7aea49c7869d02eb79cec7549a5355502c91`
—el `meta.repo_revision` real del contrato, no un valor inventado ni un `—`—, y esa columna es la
única mención del contrato en toda la tabla: la columna `norma` cita siempre una skill `dev-*` con
página (`dev-api · ES0903`, `dev-seguridad · ES0901/ES0902`, `dev-identidad · ES0901`), nunca el
contrato. En `DEV-014` ("TLS obligatorio") usó un campo real y concreto del contrato —
`environments.knowledge_status: "missing"`— para justificar el `sin-verificar` en vez de asumir una
respuesta. Se leyó, de verdad, no de nombre.

## E-09 — Sin contrato, o con uno roto, `dev-refutador` declara `sin-verificar` lo que dependía de él y no inventa

Dos mitades:

- **Que lo diga.** El resumen de la corrida nombra explícitamente que no había contrato, o que el
  que había no se pudo usar, y por qué.
- **Que no invente.** Ninguna fila de la salida se apoya en un dato de stack, componente o
  interfaz que sólo podría venir del contrato ausente —si algo así aparece, es una inferencia
  disfrazada de hecho, exactamente lo que este escenario existe para atrapar.

📌 Mirar también si las filas que **sí** se pudieron verificar sin el contrato —code, con la norma
de una skill, mirando la línea— siguen apareciendo con su veredicto normal. La ausencia del
contrato no tiene que apagar al refutador entero, sólo lo que dependía de él.

**Observado:** El resumen abre diciéndolo de frente: *"No existe `docs/codebase/project-context.json`
en este repositorio — confirmado, no lo usé ni busqué en otro lado"*, y las 14 filas quedan con
`repo_revision` en `—`. Nada inventado: donde no pudo saber algo que el contrato hubiera resuelto
—si hay endpoints de `/health`, si hay auth, si CORS está habilitado— lo marcó `sin-verificar` y
dijo qué archivo faltaba abrir (`servidor.ts`, fuera del lote que se le dio), en vez de asumir una
respuesta. Las filas que no dependían del contrato —código de rutas, variables de entorno, formato
de respuesta— siguieron con veredicto normal: 3 `cumple`, 4 `incumple`, igual que sin la ausencia
del contrato hubiera importado sólo donde de verdad importaba.
