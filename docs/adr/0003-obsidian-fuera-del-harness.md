---
estado: aceptada
creado: 2026-08-05
---

# ADR-0003 — Obsidian queda afuera del harness

## Contexto

El andamiaje que precede a este harness está construido sobre un vault de Obsidian: el
`CLAUDE.md` del proyecto funciona como caché caliente y un agente baja lo aprendido al vault,
que hace de disco frío. El mecanismo funciona bien y ahorra contexto de verdad.

Pero tiene tres dependencias que no sobreviven al pasaje de una persona a un equipo:

1. **Una ruta absoluta con el usuario de Windows adentro.** El destino del desalojo empieza
   con `C:\Users\<legajo>\`. En otra máquina no existe.
2. **OneDrive corporativo** como mecanismo de sincronización, con el vault adentro de la
   carpeta sincronizada.
3. **Un plugin REST local** para que el MCP de Obsidian funcione, que exige tener Obsidian
   abierto y cuya versión tiene host y puerto hardcodeados — por lo que ni siquiera se puede
   apuntar a un segundo vault en la misma máquina.

La consecuencia práctica: si la persona que tiene el vault se toma vacaciones, el
conocimiento del proyecto está en su disco.

## Decisión

**El harness no depende de Obsidian de ninguna forma.** Ni skill, ni agente, ni ruta, ni MCP.

El conocimiento se reparte en dos lugares, según a quién le sirve:

| Qué | Dónde | Por qué |
|---|---|---|
| Conocimiento **del proyecto** — reglas por módulo, huecos, decisiones | `docs/conocimiento/` del propio repo | Viaja con el proyecto, lo lee cualquiera del equipo, es diffeable |
| Conocimiento **transversal** — normas del GCBA, convenciones, plantillas | Adentro de este repo (`normativa/`, `comun/skills/`) | Se versiona, se revisa y se distribuye con el harness |

Obsidian sigue siendo perfectamente válido como **herramienta personal**: cada uno arma su
vault local si quiere, con lo que quiera adentro. El harness no lo toca, no lo asume y no lo
menciona.

La arquitectura de caché con write-back **se conserva íntegra** — es lo mejor del andamiaje
anterior. Lo único que cambia es el destino del desalojo: de un vault personal a
`docs/conocimiento/` del proyecto. El agente `obsidian-flush` pasa a llamarse
`flush-memoria` y mantiene su invariante, que es lo que lo hace confiable:

> Nunca se desaloja lo que no se escribió. Antes de borrar una sección hay que poder señalar
> el archivo que contiene cada hecho. Ante la duda, no se borra.

## Consecuencias

**A favor:**
- El harness es instalable en cualquier máquina sin instalar nada más.
- El conocimiento del proyecto deja de depender de que una persona esté disponible.
- Se acaba la dependencia de un plugin intermitente y de un OneDrive corporativo.
- **La economía de tokens se conserva intacta**: solo el puntero de una línea vive en el
  contexto; el contenido está en disco y se lee cuando hace falta. Cambió dónde está el
  disco, no cómo funciona la caché.

**En contra:**
- Se pierden los enlaces `[[wiki]]` y la vista de grafo sobre el conocimiento del proyecto.
  `docs/conocimiento/` es markdown plano con links relativos.
- Quien ya tiene su conocimiento en un vault tiene que migrar a mano lo que sea del proyecto.
  No hay script para eso, y no debería haberlo: decidir qué es del proyecto y qué es personal
  es exactamente el trabajo que no se puede automatizar.
- Dos lugares donde buscar, para quien use vault además del repo.

## Revisión

Esta decisión **no se revisa por comodidad**. Se revisaría solo si Obsidian dejara de ser una
elección personal y pasara a ser una herramienta provista y sostenida por el organismo, con
vaults compartidos y sincronización administrada — que hoy no es el caso.
