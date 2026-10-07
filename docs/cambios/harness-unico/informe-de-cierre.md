# Informe de cierre — harness-unico

**Escrito por:** la sesión que construyó y cierra · **Fecha:** 02-10-2026 · **Versión:** 0.29.0 ·
**Commit:** `f16ce3d` · **Estado:** cerrado

📌 Esto no es un veredicto: el veredicto está en [verificacion.md](verificacion.md). Este informe
dice en qué quedó el pedido de cierre, paso por paso.

## En qué quedamos

**0.29.0 está cerrada en `f16ce3d70b7279c09cbcce501b716d7f81b0d53d`**, con la suite final en
verde sobre el árbol del commit: `38337/38337`, exit 0. Los dos controles que la suite no ve se
hicieron antes del commit.

Este informe no entra en ese commit: un archivo no puede llevar el hash del commit que lo contiene.
Entró en el siguiente, `6c6b24d`.

Después pediste publicar el mapa largo como uno nuevo. Se publicó, y eso va en un tercer commit con
su propia corrida de la suite (ver `## El mapa largo, después del cierre`).

## Los pasos del pedido

| Paso | Qué | Estado |
|---|---|---|
| 1 | Leer los artefactos | Hecho |
| 2.1 | El lockfile del IGE, sin tocarlo | Hecho: no tiene `analisis` |
| 2.2 | Una sesión real, observada por alguien distinto de quien construyó | Hecho: la observó Nahue Palacio |
| 3 | Confirmar la versión | Hecho: 0.29.0 |
| 4 | La entrada de `UPGRADE.md` | Hecho: `0.28.0 → 0.29.0`, con los cuatro puntos |
| 5 | `CHANGELOG.md`, la nota de versión y el índice | Hecho |
| 6 | `VERSION` y referencias | Hecho |
| 7 | El conteo de tests de `CLAUDE.md` | Hecho: 38337 |
| 8 | Que los pendientes sigan abiertos | Hecho: dos notas agregadas, nada cerrado de más |
| 9 | La suite, con stdin redirigido | Hecho: dos corridas en verde, `38337/38337` |
| 10 | `git status` y diff, con `manifest.json` en git | Hecho: `manifest.json` entra en el commit, y no hay cambios fuera de alcance |
| 11 | `close-a-version` completo | Hecho. El mapa largo salió en un artifact nuevo, después del cierre |
| 12 | Este informe | Hecho |

## 2.1 — El lockfile del IGE

Se leyó sin correr nada:

- `C:\Work\GCBA\IGE`, la ruta del ítem de `PENDIENTES-FH.md`, no existe en esta máquina;
- el Portal IGE (`C:\dev\portal-ige-web`) tiene 0.28.0, con `harness: comun, desarrollo`, 261
  archivos y ningún `hu-*`.

Su `-Update` a 0.29.0 no le saca nada. Solo va a pedir que se reinicie la barra. No está registrado
si el Portal IGE es el mismo proyecto que nombra el ítem de FH, y quedó anotado así en el ítem.

## 2.2 — La sesión real

**Preparación,** en `C:\dev\harness-unico-sesion-real`:

- se instaló con el instalador de 0.28.0, sacado de `e5d7a14`;
- se corrió el `-Update` de 0.29.0. Dijo *Actualizado de v0.28.0 a v0.29.0* y *Reiniciá la sesión de
  Claude Code para activarla*, y dejó la barra en `RELOAD_REQUIRED`.

**La primera respuesta no valió.** Contestaste "Todo como se esperaba", pero en disco no había
ninguna sesión:

- `harness.installation.json` no se había vuelto a escribir;
- la bienvenida no se había mostrado nunca;
- no había ninguna transcripción en `~/.claude/projects/` para esa carpeta.

No se tomó como observación, y quedó anotado.

**La segunda sí,** a las 15:12, en la sesión `8a210931`. Se contrastó contra el disco y contra la
transcripción:

- SessionStart salió sin errores, con el encabezado `Sesion Real - harness v0.29.0`;
- la bienvenida mostraba `Context Bar  REQUIERE REINICIO`;
- a las 15:13:27 la barra dibujó y dejó su señal de vida, con la misma huella, la versión `1.2.0` y
  `ansi: ENABLED`;
- `dev-harness.py harness` dio los tres componentes en `✓ ACTIVO` y la barra en `✓ ACTIVA`.

Dos cosas que se vieron y no contradicen la spec:

- **Salió la bienvenida entera, y no el aviso de "actualizado".** Esa carpeta nunca había abierto
  una sesión. La expectativa que te pasé estaba mal escrita.
- **`harness.installation.json` sigue en `RELOAD_REQUIRED`.** Lo escribió SessionStart antes del
  primer dibujo, y se corrige en el próximo SessionStart. Es así desde antes de este cambio.

## Lo que se escribió para la versión

| Archivo | Qué |
|---|---|
| `VERSION` | 0.29.0 |
| `CHANGELOG.md` | `## [0.29.0] — 2026-10-02`, con 🔴 en `-Harness`, en `analisis` y en el lock, y una sección de lo que no cambia y de lo que sigue abierto |
| `UPGRADE.md` | `## 0.28.0 → 0.29.0`: el error de `-Harness` y el comando nuevo, qué sale de `analisis`, el reinicio de la barra y la vuelta a 0.28.0 con `-Uninstall` |
| `docs/versiones/0.29.0.md` | Las cinco secciones. El ítem de `aporta` va como cerrado en *Qué se hizo* |
| `docs/versiones/README.md` | La fila de 0.29.0 |
| `docs/instalacion.md` | "Desde la versión que sigue a 0.28.0" pasa a "Desde 0.29.0" |
| `CLAUDE.md` | 24875 pasa a 38337 |
| `Pendientes/Fix-Harness/PENDIENTES-FH.md` | Notas en el ítem del conteo, que sigue abierto, y en el del IGE |
| `docs/cambios/harness-unico/verificacion.md` | Versión 0.29.0, y los dos controles de *Lo que ningún test cubre* |
| `docs/mapa/recorrido-mensaje.html` | Sin la elección de harness, `dev-api` en lugar de `hu-escribir`, los checks de `comun` y `desarrollo`, y la ventana del stdin en la caja de la barra. **Republicado** en `claude.ai/artifact/Tp6E8Fx1KQxmJ3ps1dtsRb`, versión 4 |

`terceros/terceros.lock.json` ya decía "Retirado en 0.29.0", y el número quedó confirmado.

## La suite

| Corrida | PowerShell | Python | Total | Exit | Duración |
|---|---|---|---|---|---|
| Cierre 1, con stdin redirigido desde un archivo vacío | 754/754 | 37583/37583 | **38337/38337** | **0** | 910 s |
| Cierre 2, sobre el árbol definitivo, el del commit | 754/754 | 37583/37583 | **38337/38337** | **0** | 1342 s |
| Mapa largo, sobre el árbol del tercer commit | 754/754 | 37583/37583 | **38337/38337** | **0** | 1506 s |

Después de cada corrida, `pre-tool-use.py` y `zonas.py` tenían el mismo hash que al principio
(`61567f3` y `e996067`).

## El árbol antes del commit

- **`manifest.json` en git.** Entra en `f16ce3d` como `R080 harnesses/desarrollo/manifest.json →
  manifest.json`, con el blob `8f62ff1`.
- **No hay cambios fuera de alcance:**
  - el código que cambia es solo `install.ps1`, `comun/hooks/lib/bienvenida.py`,
    `comun/hooks/session-start.py` y `harnesses/desarrollo/bin/dev-harness.py`;
  - no tienen diff `dev-refutador.md`, `post-tool-use.py`, `lib/reglas.py`, `docs/codebase/`,
    `harness-installation-state.schema.json` ni los ADR 0001 a 0011;
  - no se tocó ningún otro `docs/cambios/` ni ninguna nota vieja de `docs/versiones/`;
  - `CHANGELOG.md` (+43 −0) y `UPGRADE.md` (+46 −0) solo suman arriba;
  - el único renombre es el del manifiesto;
  - `install.ps1` no nombra `controles`.
- **El commit:** `f16ce3d 0.29.0 cierra: un solo harness, desarrollo es el producto y analisis se
  retira`, con 62 archivos (+3694 −1327). No se pusheó.

## El mapa largo, después del cierre

Al cerrar, `docs/mapa/mapa-harness.html` no se pudo republicar. Su URL vieja
(`claude.ai/code/artifact/e11c6e31-…`) devolvió que no existe o que no está compartida con esta
cuenta. No se publicó uno nuevo sin preguntar, porque eso cambia la URL de la cabecera.

Después lo pediste, y se hizo así:

- se corrigió la Figura 4: SessionStart dice la versión del harness, no "el harness que rige";
- se publicó como artifact nuevo, en `https://claude.ai/artifact/9TVbAjZD1fco4GGB45Gm3Q`;
- la cabecera del archivo pasó a la URL nueva, y se republicó para que la copia publicada coincida
  con la del repo (versión 2);
- en `docs/versiones/0.29.0.md`, el mapa pasó de *Lo que quedó abierto* a *Qué se hizo*. En lo
  abierto quedó solo que quien tenía el link viejo tiene que pasar al nuevo.

El artifact es privado: para que lo vea alguien más hay que compartirlo desde su menú. Las chips del
mapa siguen diciendo `v0.14.0` y `772 tests`, porque es la lectura de 0.13.0 que dice su pie.

## Estado

No queda nada que bloquee. Lo que falta en otros proyectos es correr el `-Update` del Portal IGE, y
eso lo decide quien lo usa.

TASK 1 CLOSED
