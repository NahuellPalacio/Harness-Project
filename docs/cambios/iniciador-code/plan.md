# Plan de implementación — el primer recorrido del código

> **For agentic workers:** los pasos usan checkbox (`- [ ]`) para poder seguirlos. Cada Task
> termina en un commit y en un `python tests/correr.py` o `.\tests\Invoke-Tests.ps1` verde.

**Goal:** que un proyecto con `desarrollo` instalado pueda recorrer su código una vez y dejar
escrito qué hay, en `docs/codebase/`, y que `SessionStart` lo sugiera mientras ese índice no
exista.

**Architecture:** un agente de `desarrollo` hace el recorrido en su propio contexto y devuelve un
informe corto; el índice queda en el repo, versionado. El hook de `comun` solo agrega una línea
condicionada por el lockfile y por la existencia del índice. Nada de esto bloquea nada.

**Tech Stack:** markdown para el agente y para lo que escribe. Python 3.9+ y biblioteca estándar
para el hook y los tests, igual que el resto. PowerShell 5.1 solo para los casos del instalador.

**Spec:** [`docs/cambios/iniciador-code/spec.md`](spec.md)

## Global Constraints

Salen de la spec. Los requisitos de cada tarea las incluyen implícitamente.

- **Nada bloquea.** El aviso es `additionalContext`. Los secretos siguen siendo lo único que
  bloquea en todo el harness.
- **El recorrido lo lanza la persona.** El harness sugiere y nunca dispara solo.
- **No se borra lo que quedó viejo.** Una ficha huérfana se reporta, no se elimina. Es la
  invariante de `flush-memoria`.
- **El agente no escribe fuera de `docs/codebase/`.**
- **El default de la ruta es `docs/codebase`, resuelto en el agente y en el hook**, porque
  `harness.config.json` no se reescribe nunca y un proyecto ya instalado jamás verá la clave nueva.
- **El agente y sus instrucciones van en inglés.** Es lo pedido para este cambio. 🔴 El
  `CLAUDE.md` dice hoy que `harnesses/` se entrega en español y los dos refutadores lo están: o se
  ajusta esa regla, o este archivo es una excepción declarada. **Queda sin resolver a propósito y
  no lo decide quien construye.**
- **Lo que escribe el agente va en español**, porque lo lee el equipo del proyecto.
- **Ningún `.py` del harness lleva BOM**, y todo `.md` va UTF-8 sin BOM y con LF.

---

## Estructura de archivos

| Archivo | Responsabilidad | Dueño |
|---|---|---|
| `harnesses/desarrollo/agents/dev-iniciador-code.md` | El agente: recorre, escribe, informa | — |
| `harnesses/desarrollo/manifest.json` | Suma `rutaCodebase` a su `config` | `harness-backend-engineer` |
| `comun/hooks/session-start.py` | La línea que sugiere el recorrido | `harness-hook-engineer` |
| `comun/checks/codebase-forma.py` | La forma de lo escrito: índice, fichas, secretos | `harness-hook-engineer` |
| `tests/casos/10_codebase.py` | E-01 a E-06, E-08 a E-12, E-20 | `harness-backend-engineer` |
| `tests/casos/03-instalador.ps1` | E-18, E-19, E-21 | `harness-backend-engineer` |
| `tests/fixtures/proyecto-codebase/` | Un `docs/codebase/` de mentira, bien y mal formado | `harness-backend-engineer` |
| `docs/mapa/recorrido-mensaje.html` | La caja punteada pasa a llena | — |

---

## El contrato de lo escrito

Todo lo demás se verifica contra esto, así que se fija acá antes de construir nada.

`docs/codebase/indice.md` — una línea por ficha, y nada más:

```markdown
# Índice del código

_(Lo escribe `dev-iniciador-code`. Se regenera entero; no editar a mano.)_

- `comun/hooks` — Los cuatro hooks y su contrato → [`comun-hooks.md`](comun-hooks.md)
- `comun/checks` — Las reglas que corren después de escribir → [`comun-checks.md`](comun-checks.md)
```

`docs/codebase/<modulo>.md` — las cuatro secciones, con esos títulos exactos:

```markdown
# comun/hooks

## Qué es
## Qué expone
## De qué depende
## Dónde está
```

El nombre del archivo sale de la ruta del módulo con `/` reemplazado por `-`. Es lo que hace que
dos módulos con el mismo nombre en distintos directorios no colisionen, y que el nombre sea
derivable en los dos sentidos.

---

## Task 1: El agente

**Files:**
- Create: `harnesses/desarrollo/agents/dev-iniciador-code.md`
- Modify: `harnesses/desarrollo/manifest.json`

**Interfaces:**
- Consume: la raíz del proyecto y, si está, `rutaCodebase` de `harness.config.json`.
- Produce: `docs/codebase/indice.md`, una ficha por módulo, y un informe corto por stdout.

- [ ] **Step 1: El frontmatter, que es lo que decide si lo llaman**

`name: dev-iniciador-code`, `tools: Read, Write, Grep, Glob, PowerShell`. `PowerShell` va porque el
listado sale de `git ls-files` y sin una consola no hay forma de pedirlo; se elige sobre `Bash`
porque es lo que ya usa `leer-docs` y el parque es Windows. La `description` tiene que nombrar
los disparadores reales —primer recorrido, indexar el código, `docs/codebase/`— porque es lo único
que el modelo ve para decidir si invocarlo. Cortarla mal produce un agente que nadie llama y que
cuesta lo mismo.

- [ ] **Step 2: El cuerpo, con las invariantes arriba**

Tres, y van antes que el procedimiento:

1. **Quien te llama nunca ve el código crudo.** Devolvés el informe, no el material. Si volcás
   archivos en la respuesta, fallaste: era más barato no delegar nada.
2. **No escribís fuera de `docs/codebase/`.**
3. **No borrás.** Una ficha cuyo módulo ya no existe se nombra en el informe y se deja.

Después el procedimiento: resolver la ruta, listar lo que `git ls-files` devuelve —así lo ignorado
por `.gitignore` queda afuera sin reimplementar nada—, agrupar en módulos, escribir una ficha por
módulo con las cuatro secciones, escribir el índice al final, informar.

- [ ] **Step 3: Las reglas de escritura, copiadas de `flush-memoria`**

Ningún secreto, ningún dato personal, y `Write`/`Edit` siempre porque los títulos llevan tildes.

- [ ] **Step 4: `rutaCodebase` en el manifiesto**

```json
"config": { "rutaCodebase": "docs/codebase", "umbralCobertura": 80, "...": "..." }
```

- [ ] **Step 5: Commit**

```bash
git add harnesses/desarrollo/agents/dev-iniciador-code.md harnesses/desarrollo/manifest.json
git commit -m "El agente del primer recorrido, y la ruta donde deja el indice"
```

---

## Task 2: El aviso de `SessionStart`

**Files:**
- Modify: `comun/hooks/session-start.py`
- Create: `tests/casos/10_codebase.py`
- Create: `tests/fixtures/proyecto-codebase/`

**Interfaces:**
- Consume: `campo(e, "cwd")`, `config_proyecto(proyecto)` y `.claude/harness.lock.json`, todo lo
  cual el hook ya lee hoy.
- Produce: una línea más en su bloque, o ninguna.

- [ ] **Step 1: La condición, y en este orden**

`desarrollo` en `harness.lock.json` → el índice no existe → una línea. Cualquiera de las dos que
no se cumpla, silencio. El orden importa: el chequeo de disco va último y no corre en un proyecto
de solo análisis.

- [ ] **Step 2: Que un `docs/codebase/` ilegible no rompa nada**

El acceso a disco va adentro del mismo criterio del resto del hook: cualquier excepción sale con
código 0 y el resto del bloque se emite igual. E-06 es exactamente eso.

- [ ] **Step 3: Los tests**

`tests/casos/10_codebase.py`, con el id en el nombre de cada función:

```
test_e01_avisa_cuando_falta_el_indice
test_e02_calla_cuando_el_indice_existe
test_e03_calla_sin_desarrollo_en_el_lockfile
test_e04_no_pasa_las_doce_lineas
test_e05_no_devuelve_deny_ni_ask
test_e06_directorio_ilegible_sale_cero
test_e20_sin_la_clave_usa_el_default
```

Run: `python tests/correr.py -k codebase` · Expected: PASS.

- [ ] **Step 4: Ver los siete en rojo, y anotarlo**

Romper la condición a propósito, ver fallar cada test, restaurar. **Recién ahí** E-01 a E-06 y E-20
pasan de `no consta` a `si` en la spec. Es una declaración: ningún check puede saber si se hizo.

- [ ] **Step 5: Commit**

```bash
git add comun/hooks/session-start.py tests/casos/10_codebase.py tests/fixtures/proyecto-codebase/
git commit -m "SessionStart sugiere el primer recorrido, y se calla en cuanto existe"
```

---

## Task 3: La forma de lo escrito

**Files:**
- Create: `comun/checks/codebase-forma.py`
- Modify: `tests/casos/10_codebase.py`

**Interfaces:**
- Consume: el contrato de arriba, `comun/reglas/secretos.patrones.json`.
- Produce: cero o más hallazgos, como cualquier check.

- [ ] **Step 1: El check**

Contrato de siempre: `verificar(evento, proyecto, config)` devuelve strings. Comprueba la
biyección índice↔fichas (E-08), las cuatro secciones de cada ficha (E-09) y que nada matchee un
patrón de bloqueo del catálogo de secretos (E-10). Avisa, nunca bloquea.

- [ ] **Step 2: Los fixtures, uno bien y uno mal por escenario**

Un `docs/codebase/` completo, uno con una ficha que no está en el índice, uno con una línea del
índice que apunta a un archivo inexistente, uno con una ficha a la que le falta una sección.

- [ ] **Step 3: Tests E-08, E-09, E-10, E-12, verlos en rojo, commit**

```bash
git add comun/checks/codebase-forma.py tests/
git commit -m "Un check para la forma del indice: biyeccion, cuatro secciones, ningun secreto"
```

---

## Task 4: El instalador

**Files:**
- Modify: `tests/casos/03-instalador.ps1`

🔴 Este archivo rompe archivos versionados a propósito y los restaura en un `finally` que **no
sobrevive a que maten el proceso**. Si la corrida se interrumpe, mirar el árbol antes que nada.

- [ ] **Step 1: E-18** — instalado `desarrollo`, existe `.claude/agents/dev-iniciador-code.md`.
- [ ] **Step 2: E-19** — instalado de cero, `harness.config.json` trae `rutaCodebase`.
- [ ] **Step 3: E-21** — `-Uninstall` deja `docs/codebase/` intacto. Es del proyecto, no del
  harness.
- [ ] **Step 4: Verlos en rojo y commitear**

Run: `.\tests\Invoke-Tests.ps1` · Expected: verde, dos motores, un exit code.

---

## Task 5: El primer recorrido de verdad

Los once escenarios que la suite no puede cubrir. Ninguno se declara cumplido sin haberlo mirado.

- [ ] **Step 1: Correr `dev-iniciador-code` sobre este mismo repositorio**

- [ ] **Step 2: Anotar el costo, que hoy nadie sabe**

Tokens y minutos del recorrido, y sobre cuántos archivos. Va a `docs/cambios/iniciador-code/` y es
el dato que decide si la sugerencia de `SessionStart` es razonable o está empujando a la gente a un
gasto que no anunció.

- [ ] **Step 3: Leer E-07 a E-17 contra lo que quedó escrito**

Con atención especial a E-16 —que el informe no traiga código— y al riesgo que E-09 no cubre: las
cuatro secciones pueden estar y no decir nada. Si las fichas son generalidades, el escenario pasa y
el cambio no sirve; eso se ve leyendo, no corriendo.

- [ ] **Step 4: Commitear `docs/codebase/` de este repo**

Es la primera prueba de que el mecanismo produce algo que vale, y queda diffeable.

---

## Task 6: Cerrar el cambio

- [ ] **Step 1: El mapa** — en `docs/mapa/recorrido-mensaje.html`, la caja punteada del primer
  recorrido pasa a caja llena y el chip baja de «2 pasos todavía sin escribir» a 1. Se republica
  **pasando la URL del comentario de cabecera** como parámetro `url`; publicar sin ella crea un
  artifact nuevo y rompe el link que la gente ya tiene.
- [ ] **Step 2: `harness-budget-auditor`** — pesar la pieza catorce. Hoy son 926 tokens entre 13.
- [ ] **Step 3: El veredicto** — `harness-spec-refuter` corre la suite y falla contra la spec. Va a
  `docs/cambios/iniciador-code/verificacion.md`. **Quien construyó no verifica.**
- [ ] **Step 4: La versión** — nota en `docs/versiones/`, `CHANGELOG.md`, `VERSION`, y el ítem de
  Ideas sale del archivo y aterriza en la nota.

---

## Verificación final

```powershell
.\tests\Invoke-Tests.ps1                     # verde, dos motores
.\install.ps1 -Doctor                        # el aviso nuevo no movió la latencia
```

Y lo que ningún test cubre: **abrir una sesión en un proyecto con `desarrollo` instalado y sin
índice, y ver que la línea aparece; correr el recorrido; abrir otra sesión y ver que la línea ya no
está.** Que el hook conteste bien a un payload lo prueba la suite. Que Claude Code lo invoque y que
la persona entienda qué le están sugiriendo es otra cosa, y se mira con los ojos.

Un `verificacion.md` con cualquier `contradicho` o `sin-sustento` no cierra el cambio.
