---
estado: aceptada
creado: 2026-10-01
---

# ADR-0012 — Un solo harness

## Contexto

Desde 0.1.0 el repo estaba armado para varios harnesses. `comun/` era "el harness que siempre
está", `harnesses/<id>/` eran tipos de trabajo, e `install.ps1` los descubría recorriendo
`harnesses/`. Se elegían con `-Harness`, se componían, se validaba que sus prefijos fueran
disjuntos y se copiaban en espacios de nombres separados. Había dos: `analisis`, para relevar y
escribir historias de usuario, y `desarrollo`, para código, APIs y deploy.

En la práctica, `desarrollo` creció hasta ser el producto: integraciones, contexto de tarea,
planificación, Agent Registry, refutación, seguridad, normativa, Context Bar y contabilidad.
`analisis` se quedó en una skill, dos agentes y un bloque del `CLAUDE.md`, sin un solo check.
Y el corte entre `comun` y `desarrollo` nunca fue un corte de capas: era "lo que también
necesitaba `analisis`" contra "lo que solo necesitaba `desarrollo`".

El inventario completo, con la cadena de composición eslabón por eslabón, está en
`docs/cambios/harness-unico/spec.md`.

## Decisión

El producto es **un solo harness**.

1. **`desarrollo` es el harness.** Se instala entero. Nadie elige un tipo al instalar.
2. **`comun` es su base**, no otro producto: los hooks, la regla de secretos, las zonas del
   `CLAUDE.md`, los schemas y el estado de la instalación.
3. **`analisis` se retira.** `hu-escribir`, `hu-redactor`, `hu-refutador` y las reglas de
   "Trabajo funcional" salen. No se portan a `desarrollo`: portarlas sería una capacidad nueva.
4. **La composición sale.** Sin `-Harness`, sin descubrimiento de `harnesses/`, sin ids en el
   lockfile, sin prefijos y sin un manifiesto por harness: hay uno solo, `manifest.json`, en la
   raíz del repo.

Lo que no cambia, y por qué:

- **Las rutas instaladas.** `.claude/harness/bin/desarrollo/dev-harness.py` es la dirección
  pública de la CLI: la usan las personas, los agentes y UPGRADE. El segmento `desarrollo` deja
  de ser un espacio de nombres y pasa a ser un nombre fijo. Que siga ahí no quiere decir que
  sigan existiendo varios harnesses.
- **Los ids `dev-*`, el marcador `HARNESS:COMUN` y `harnessId: "desarrollo"`.** Están guardados
  en planes, en la caché de la refutación, en eventos de contabilidad, en el `CLAUDE.md`
  versionado de cada proyecto y en el estado de la instalación. Renombrarlos no es parte de esta
  decisión.
- **El árbol fuente.** `comun/` y `harnesses/desarrollo/` siguen donde están. Decidir dónde va
  cada cosa es el corte base/dominio, y eso es otra decisión.

## Consecuencias

A favor:

- Una instalación es una sola cosa, y el inventario dice qué es.
- El `-Update` limpia lo que el lock anterior listaba y la versión nueva ya no instala, en vez de
  dejarlo huérfano fuera del inventario.
- Un solo manifiesto es la única fuente de los requisitos de la máquina y de la configuración
  inicial.

En contra, y dicho:

- **Se rompe `-Harness`.** Un script, un `.cmd` o un CI que lo pase recibe el error de
  PowerShell y sale con 1.
- **Todo proyecto con `analisis` pierde esas capacidades** en su próximo `-Update`.
- **El lockfile pierde el campo `harness`**, y el instalador de 0.28.0 ya no puede actualizar un
  proyecto actualizado: volver atrás pide `-Uninstall` y volver a instalar.
- **El repo conserva un `harnesses/` con un solo hijo** hasta que se decida el árbol fuente.
- **Los nombres históricos siguen en contratos públicos.** Sacarlos es un cambio que rompe por su
  cuenta.

## Revisión

Se revisa cuando se decida el corte base/dominio del árbol fuente, o cuando aparezca un tipo de
trabajo que no quepa en el producto. Lo que no se revisa por una sola de las dos: la vuelta de la
composición. Si algún día hace falta, entra por una spec propia, con su costo dicho.
