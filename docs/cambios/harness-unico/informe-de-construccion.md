# Informe de construcción — harness-unico

**Escrito por:** quien construyó el cambio · **Fecha:** 02-10-2026 · **Spec:**
[spec.md](spec.md) · **Línea de base:** 0.28.0 (`e5d7a14`)

📌 Esto no es un veredicto. Dice qué se construyó, cómo se probó y qué quedó abierto, para que
`harness-spec-refuter` lo contraste contra la spec. Quien construyó no verifica.

## Resultado de la compuerta

```
.\tests\Invoke-Tests.ps1
754/754 pasaron (PowerShell).
37583/37583 pasaron.
38337/38337 pasaron.
exit=0 · 1395 s
```

Corrida el 02-10-2026, sobre el árbol de trabajo sin commitear. `VERSION` sigue en 0.28.0;
`CHANGELOG.md` y `UPGRADE.md` no se tocaron: los escribe `close-a-version`.

## Qué se construyó

- **Un solo manifiesto, en la raíz** (`manifest.json`). Tiene `requiereClaudeCode`,
  `requierePython`, `capacidadesSoportadas` y `config`, y nada más. `config` es la de `comun`
  seguida de la de `desarrollo` de 0.28.0, en el mismo orden. `comun/manifest.json`,
  `harnesses/desarrollo/manifest.json` y `harnesses/analisis/` se borraron con `git rm`.
- **`install.ps1` sin la maquinaria de composición.** Se fueron el parámetro `-Harness`,
  `Get-HarnessDisponibles`, la lista de ids y su split, la herencia desde `lock.harness`, el orden
  canónico, la validación de prefijos, `.claude\harness\manifiestos\` y toda condición sobre qué
  id está instalado. Se agregó `PositionalBinding=$false`. La copia es un mapa fijo:
  `harnesses\desarrollo` va a `checks\desarrollo`, `bin\desarrollo`, `reglas\desarrollo`, `skills`
  y `agents`, las mismas rutas instaladas de 0.28.0. El bloque del `CLAUDE.md` son dos fragmentos
  en orden fijo. `statusLine`, `.env`, presupuesto, integraciones y conocimiento pasan a ser
  incondicionales.
- **El lockfile nuevo** tiene exactamente `version`, `instalado`, `backup` y `archivos`. Un lock de
  0.28.0 se lee igual, y su campo `harness` se ignora.
- **La limpieza basada en inventario** (`Read-InventarioPrevio`, `Remove-Huerfanos`). Un huérfano
  es un archivo que el lock anterior lista y el inventario nuevo no. La limpieza corre recién
  cuando los cuatro hooks respondieron:
  - sin editar, se borra, y se nombra en la salida si está fuera de `.claude\harness\`;
  - editado a mano, queda, sin `.nuevo`, se nombra y sale del inventario;
  - en `-Update`, uno editado bajo `.claude\harness\` se restaura con su carpeta;
  - después se borran las carpetas que quedan vacías debajo de `.claude\harness\`,
    `.claude\skills\` y `.claude\agents\`, y nunca esas tres raíces.

  Ninguna línea nombra a `analisis`.
- **`-Doctor`** saca los requisitos de `manifest.json`, dice `harness instalado (v<versión>)` sin
  ids y da la línea de la Context Bar siempre.
- **`comun/hooks/lib/bienvenida.py`**, solo el resolvedor y el registro. El lock es legible si es un
  objeto JSON, no se miran ids, se fue `_sin_desarrollo` y `harnessId` es la constante
  `"desarrollo"`. Los renderizadores no se tocaron.
- **`comun/hooks/session-start.py`.** El encabezado pasa a `<usuario> - harness v<versión>`. El
  aviso del recorrido del código sale con cualquier lockfile legible. Un lock que es JSON y no es
  objeto cuenta como ausente y no levanta.
- **`harnesses/desarrollo/bin/dev-harness.py`.** Se fue la rama `sin el harness de desarrollo`, y
  la condición sobre `knowledge.applies` de las otras dos guardas.

Los únicos archivos instalados que cambian son esos tres (E-16). `dev-refutador.md` no se tocó: su
huella es la clave de la caché de la refutación atómica.

## Cómo se probó

- **Casos nuevos:** `tests/casos/63-harness-unico-instalador.ps1` (188 aserciones) y
  `tests/casos/63_harness_unico.py` (180). Cubren E-01 a E-62, y cada aserción nombra su E-nn. La
  línea de base sale de git en cada corrida: `git archive e5d7a14` para el instalador viejo y para el
  `bienvenida.py` viejo. No se versionó ningún inventario copiado.
- **Casos adaptados que la spec enumera:**
  - `03`, `11`, `14`, `17`, `18`, `19`, `20`, `30`, `54`, `57`, `60`, `61` y `62` de instalador;
  - `05_memoria`, `10_codebase`, `13_contexto`, `18_integraciones`, `51_bienvenida` y
    `53_context_bar`.

  `06-composicion.ps1` se borró. Los casos de "solo analisis" se borraron, o pasaron a probar que el
  campo `harness` del lock no cambia nada.
- **Casos adaptados que la spec no enumera,** porque también codificaban el modelo viejo:
  - `24_g1_tecnologias.py`: el parser de los orígenes de `checks` en `install.ps1`;
  - `60_entorno_primero.py` y `61_conocimiento_auto_refresco.py`: "los mismos agentes y skills que
    en el commit X" descuentan solo un harness cuyo directorio ya no existe;
  - dos aserciones de `03-instalador.ps1`: la invariante de portabilidad se mide sin la
    `statusLine`, que es la excepción documentada, y el aviso de actualización tiene tres líneas con
    el producto entero;
  - el comentario de `tests/Invoke-Tests.ps1`.
- **Rojo visto.** El registro completo está en la spec, en `Cómo se verifica`. Se vio el rojo contra
  0.28.0, antes de construir, y rompiendo el código ya construido sobre seis copias del repositorio
  en un temporal; el árbol versionado no se tocó.
  - 53 escenarios quedaron en `si`.
  - 9 en `no consta`: E-18, E-23, E-24, E-26, E-47, E-48, E-54, E-55 y E-60.
  - El rojo encontró un error del propio test de E-09: pasaba `-Usuario` con nombre, y sacar
    `PositionalBinding=$false` no lo ponía en rojo. Se corrigió para que haga lo que dice el
    escenario.

## Compatibilidad, como quedó

- **`-Harness` ya no existe:** pasarlo sale con 1, con el error de PowerShell, y no escribe nada.
  Un argumento suelto también falla.
- **`analisis` se retira:** `hu-escribir`, `hu-redactor`, `hu-refutador` y las reglas de "Trabajo
  funcional" salen en el `-Update`. `harness.config.json` no se toca.
- **El lockfile no tiene `harness`.**
- **Las rutas públicas se conservan:** `bin\desarrollo\dev-harness.py`, la `statusLine`, `dev-*` y
  `HARNESS:COMUN`.
- **Volver a 0.28.0 no está soportado:** el instalador viejo muere con el lock nuevo, y el camino
  es `-Uninstall`.

## Deuda que el cambio descubrió o actualizó

Está en `Pendientes/Fix-Harness/PENDIENTES-FH.md`, sin resolver:

- el Agent Registry es inválido en todo proyecto instalado (E-53 lo fija como en 0.28.0);
- los defaults de `config` repetidos en Python, fuera de `manifest.json`;
- `docs/codebase/` sigue describiendo un harness que ya no existe;
- los comentarios de `post-tool-use.py` y `lib/reglas.py` que hablan de varios harnesses;
- el comentario de `dev-refutador.md` que apunta a un archivo retirado, sumado al ítem de ADR-0011;
- el ítem de `controles/` se actualizó: ya no hace falta un `<id>`;
- el ítem de `aporta` se sacó: lo cierra el manifiesto único.

## Lo que tiene que resolver el cierre

- `terceros/terceros.lock.json` dice "Retirado en 0.29.0". `close-a-version` tiene que confirmar
  ese número.
- El ítem de `aporta` salió de `PENDIENTES-FH.md` antes del cierre: tiene que aparecer en
  `## Qué se hizo` de la nota de versión.
- La entrada de `UPGRADE.md` tiene que llevar lo que fija `Cómo se verifica`:
  - que `-Harness` desapareció, con su error;
  - qué sale de un proyecto con `analisis`;
  - que la Context Bar pide reiniciar;
  - que volver a 0.28.0 pide `-Uninstall`.
- El `CLAUDE.md` de la fábrica dice 24875 tests, y la corrida dio 38337.
- Antes de publicar, hay que mirar el lockfile del IGE (`Cómo se verifica`, punto 1).

## Archivos

| | |
|---|---|
| Creados | `manifest.json`, `docs/adr/0012-un-solo-harness.md`, `tests/casos/63-harness-unico-instalador.ps1`, `tests/casos/63_harness_unico.py`, este informe |
| Borrados | `comun/manifest.json`, `harnesses/desarrollo/manifest.json`, `harnesses/analisis/`, `docs/agregar-un-harness.md`, `tests/casos/06-composicion.ps1` |
| Código | `install.ps1`, `comun/hooks/lib/bienvenida.py`, `comun/hooks/session-start.py`, `harnesses/desarrollo/bin/dev-harness.py` |
| Documentación | `README.md`, `docs/instalacion.md`, `docs/memoria.md`, `docs/mapa/mapa-harness.html`, `terceros/terceros.lock.json`, `Pendientes/Fix-Harness/PENDIENTES-FH.md` |
| Fábrica | `CLAUDE.md`, `.claude/agents/harness-backend-engineer.md`, `.claude/agents/harness-budget-auditor.md`, `.claude/skills/note-a-pending/SKILL.md` |
| Spec | `docs/cambios/harness-unico/spec.md`: marcas de rojo visto, su registro y el estado "construido y testeado" |

## Estado

READY FOR SPEC VERIFICATION. No hay ninguna contradicción abierta contra la spec que yo conozca.
