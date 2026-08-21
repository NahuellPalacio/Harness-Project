---
estado: aceptada
creado: 2026-08-21
---

# ADR-0008 — Lo externo se aprovecha, nunca es requisito

## Contexto

En dos semanas se evaluaron tres herramientas externas y las tres se resolvieron con el mismo
criterio, sin que ese criterio esté escrito en ningún lado:

| Herramienta | Qué prometía | Cómo terminó |
|---|---|---|
| Obsidian | Un vault como disco frío del conocimiento | Afuera, por ADR-0003 |
| graphify | Un grafo del código consultable en vez de grepear | Descartada: exige `uv`, que no está en la tabla homologada de ES0901, y su hook lo borra el `-Update` del harness |
| codebase-memory-mcp | Lo mismo, en un binario estático sin runtime nuevo | Frenada: el binario no está firmado con Authenticode y Defender lo marca como `Trojan:Script/Wacatac.B!ml` |

ADR-0003 dice la regla para Obsidian. ADR-0005 la dice para material de terceros que se copia
adentro del repo. Ninguno la dice para el caso general —una herramienta que se instala en la
máquina y que el harness querría aprovechar— y ahí es donde cayeron las tres.

Sin la regla escrita, cada herramienta nueva se discute de cero y la conclusión depende de
quién esté ese día.

La idea concreta que disparó este ADR fue que un índice de código se encargara del mapeo, que
Obsidian guardara el contexto y que el `CLAUDE.md` quedara con etiquetas apuntando a los dos.
Mirada contra el repo, la mitad ya estaba construida —`ZONA CACHÉ → flush-memoria →
docs/conocimiento/ → ZONA ÍNDICE` es exactamente eso— y la otra mitad choca con la
instalabilidad.

## Decisión

**El harness puede aprovechar una herramienta externa. No puede depender de ella.**

Tres condiciones, y las tres tienen que cumplirse:

1. **No la instala.** El `install.ps1` no la baja, no la configura y no la nombra como
   prerrequisito.
2. **No la asume presente.** Ninguna regla del `CLAUDE.md`, ninguna skill y ningún agente
   escriben una ruta, un comando o un servidor MCP que solo exista si la herramienta está.
3. **Degrada, no falla.** Sin la herramienta el trabajo sigue igual, por el camino que ya
   existía. Lo que aporta es un atajo, nunca el único camino a un dato.

Es la generalización de algo que ADR-0003 ya afirmó como consecuencia y nunca se elevó a
regla: *"el harness es instalable en cualquier máquina sin instalar nada más."*

🔴 **El muro no es técnico, es de máquina ajena.** Los dos casos que motivaron este ADR no
fallan por diseño de la herramienta sino por dónde tiene que correr: un binario sin firma que
el antivirus del organismo come, y un runtime que no está homologado. Ninguna de las dos cosas
las destraba el desarrollador. Una herramienta que anda perfecto en la máquina de quien la
propone no prueba nada sobre la máquina de al lado.

### Aplicación 1 — Obsidian

**ADR-0003 se ratifica. No se revisa.** Su cláusula es explícita: solo se revisaría si Obsidian
pasara a ser una herramienta provista y sostenida por el organismo, y eso no pasó.

Se le agrega una precisión que hoy no está escrita en ningún lado, y que resuelve la queja de
su propia sección "En contra":

> `docs/conocimiento/` es markdown plano, y por lo tanto **es un vault**. Quien quiera los
> enlaces `[[wiki]]` y la vista de grafo sobre el conocimiento del proyecto abre esa carpeta
> con Obsidian y los tiene.

El harness no se entera. No hay ruta al vault, no hay plugin REST, no hay OneDrive en el medio
y no hay una segunda copia del conocimiento: es la misma carpeta del repo, mirada con otra
herramienta. Obsidian queda donde ADR-0003 lo dejó —elección personal— y recupera lo único que
ese ADR había dado por perdido.

### Aplicación 2 — El mapa del código

La `ZONA MAPA` del `CLAUDE.md` sigue siendo la fuente, con su techo de 20 líneas y su check.

Un índice externo del código —`codebase-memory-mcp` es hoy el mejor candidato— queda anotado
como **disparador diferido**: si el binario llega firmado o el organismo lo homologa, entonces
se evalúa una skill opcional que lo consulte, y recién ahí se discute si la `ZONA MAPA` se
achica. Hasta entonces no se escribe esa skill, porque no hay dónde correrla.

Tampoco se decide con un número: no hay ningún proyecto instalado en el que medir cuánto pesan
hoy `ZONA MAPA` más `ZONA ÍNDICE`, y la plantilla viene vacía a propósito. El ahorro real es
desconocido, y eso es en sí mismo un motivo para diferir en vez de construir.

## Consecuencias

**A favor:**

- La próxima herramienta se resuelve contra tres condiciones escritas, no contra el criterio
  de quien esté ese día.
- El harness sigue siendo instalable en cualquier máquina del organismo sin instalar nada más,
  que es la propiedad que lo hace distribuible.
- Nadie queda con un harness a medias porque el antivirus le comió un binario.
- Quien quiera grafo y `[[wiki]]` sobre el conocimiento del proyecto ya los tiene, sin que el
  harness cambie una línea.

**En contra:**

- Se deja plata en la mesa. Un índice del código ahorra tokens de verdad —cinco consultas
  contra grepear el corpus entero, medido por el proyecto en 99,2 % menos— y esta regla dice
  que no se puede apoyar el harness en eso mientras no corra en cualquier máquina.
- Un atajo que degrada tiene dos caminos, y dos caminos se prueban y se mantienen. Es el precio
  de la condición 3.
- La regla es fácil de decir y difícil de sostener el día que una herramienta muy buena pide
  una excepción chica.

## Revisión

Se revisa cuando cambie **la máquina**, no cuando aparezca una herramienta mejor. Es decir:
si el organismo homologa un mecanismo de distribución para binarios de terceros firmados, o si
la tabla de ES0901 incorpora los runtimes que hoy dejan afuera a estas herramientas.

Que una herramienta nueva sea muy buena no es motivo de revisión. Es exactamente el caso que
esta decisión existe para contestar sin volver a discutirlo.
