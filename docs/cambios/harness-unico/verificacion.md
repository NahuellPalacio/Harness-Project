# Verificación — Un solo harness: `desarrollo` es el producto, `comun` es su base y `analisis` se retira

**Estado:** cerrado · **Fecha:** 02-10-2026 · **Versión:** 0.29.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el
02-10-2026, en un contexto propio, sin el de la construcción. Usó
[informe-de-construccion.md](informe-de-construccion.md) solo como mapa. Revisó el diff y leyó cada
test contra la letra de su escenario. Además corrió chequeos propios en `%TEMP%`:

- instaló con el `install.ps1` de `e5d7a14`, sacado con `git archive`, en las tres variantes:
  `desarrollo`, `analisis,desarrollo` y `analisis`;
- instaló con el instalador de este cambio;
- corrió `-Update`, `-Uninstall` y `-Doctor` sobre copias de esas instalaciones.

Corrió la compuerta entera dos veces. La primera tuvo una falla del entorno desde el que la lanzó;
la segunda, con stdin redirigido, dio `38337/38337` con exit 0 (ver `## La suite`).

**Resultado: 62 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento. Rojo visto: 53 sí,
9 no consta.**

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Nada bajo `harnesses/analisis/`; el único `manifest.json` es el de la raíz | sostenido | sí | `63_harness_unico.py`; propio: `git ls-files harnesses/analisis` vacío |
| E-02 | `manifest.json` con exactamente sus 4 claves | sostenido | sí | `63_harness_unico.py`; propio, leyendo el JSON |
| E-03 | `config` = comun + desarrollo de `e5d7a14`, en orden, con `usuario: ""` primera | sostenido | sí | `63_harness_unico.py`; propio, contra `git show e5d7a14:<ruta>` |
| E-04 | `capacidadesSoportadas` = las de los adaptadores de Jira y GitLab | sostenido | sí | `18_integraciones.py` E-23, leyendo `manifest.json`; propio: igual a `e5d7a14` |
| E-05 | `install.ps1` no declara `-Harness` | sostenido | sí | `63-harness-unico-instalador.ps1`, `Get-Command` |
| E-06 | Instala con `-Project` y `-Usuario`, sale 0 y deja lock, settings y estado | sostenido | sí | `63-harness-unico-instalador.ps1`; propio: exit 0 |
| E-07 | `-WhatIf` sale 0, no crea nada, lista el presupuesto y no nombra `manifiestos` | sostenido | sí | `63-harness-unico-instalador.ps1` |
| E-08 | `-Harness`, en sus tres formas: sale ≠0, nombra `Harness` y no escribe nada | sostenido | sí | `63-harness-unico-instalador.ps1`, por `-File` |
| E-09 | Un posicional de más sale ≠0 y no escribe nada | sostenido | sí | `63-harness-unico-instalador.ps1`, sin `-Usuario`, como dice el escenario |
| E-10 | `harnesses/datos/` en una copia no cambia lo instalado; `-Doctor` no lo nombra | sostenido | sí | `63-harness-unico-instalador.ps1`, sobre una copia del repositorio |
| E-11 | Ninguna salida del instalador habla de varios harnesses | sostenido | sí | `63-harness-unico-instalador.ps1`, juntando las salidas de los demás casos; ver hallazgo 3 |
| E-12 | Sin `analisis` en `install.ps1` ni sus formas en lo que se instala, salvo `dev-refutador.md` | sostenido | sí | `63_harness_unico.py`; propio, sin distinguir mayúsculas, también sobre el árbol instalado |
| E-13 | Sin `agregar-un-harness.md`, sin el parámetro viejo y sin las secciones viejas en los tres docs | sostenido | sí | `63_harness_unico.py`; propio, con la misma expresión |
| E-14 | Sin `manifiestos\`; el lock con sus 4 claves | sostenido | sí | `63-harness-unico-instalador.ps1`; propio |
| E-62 | `install.ps1` no conserva la maquinaria de composición, ni sin usar | sostenido | sí | `63_harness_unico.py`; propio: 20 expresiones, cero coincidencias |
| E-15 | El lock tiene las rutas de 0.28.0 menos los dos manifiestos: 259 | sostenido | sí | `63-harness-unico-instalador.ps1`; propio: de 261 a 259, mismas rutas |
| E-16 | Mismo contenido que 0.28.0, salvo las cinco excepciones | sostenido | sí | `63-harness-unico-instalador.ps1`, normalizado; propio: `git diff --name-status e5d7a14 -- comun harnesses/desarrollo` |
| E-17 | `settings.json` igual al de 0.28.0, normalizado | sostenido | sí | `63-harness-unico-instalador.ps1`, en el mismo directorio |
| E-18 | `harness.config.json` igual al de 0.28.0 | sostenido | no consta | `63-harness-unico-instalador.ps1`; propio: idéntico |
| E-19 | `.env.example`, `.env` y presupuesto iguales; una segunda instalación no los pisa | sostenido | sí | `63-harness-unico-instalador.ps1`, más los casos 17, 60 y 62 |
| E-20 | El bloque `HARNESS:COMUN` igual byte a byte | sostenido | sí | `63-harness-unico-instalador.ps1`; propio |
| E-21 | Verifica los cuatro hooks y prueba la Context Bar | sostenido | sí | `63-harness-unico-instalador.ps1`; propio |
| E-22 | Integraciones y fuentes, con `INSTALL` al instalar y `HARNESS_UPDATE` en `-Update` | sostenido | sí | `63-harness-unico-instalador.ps1` y el caso 61; propio, en `knowledgeRefresh.trigger` |
| E-23 | Los estados de los tres componentes, como en 0.28.0 | sostenido | no consta | `63-harness-unico-instalador.ps1`; propio: los mismos en los dos |
| E-24 | Los doce casos de instalador pasan sin `-Harness`, con solo lo permitido cambiado | sostenido | no consta | la suite; diff de los doce archivos revisado |
| E-25 | `deny` a un secreto de confianza alta; nada más bloquea | sostenido | sí | `63-harness-unico-instalador.ps1`, por el comando registrado |
| E-26 | PostToolUse avisa con `dev-accesibilidad-html` y `claude-md-zonas` | sostenido | no consta | `63-harness-unico-instalador.ps1` |
| E-27 | El resolvedor nuevo sin `harness` da el documento del de `e5d7a14` con desarrollo | sostenido | sí | `63_harness_unico.py`, con el módulo viejo de `git archive` |
| E-28 | El campo `harness` del lock no cambia nada | sostenido | sí | `63_harness_unico.py`, cuatro variantes; también `10_codebase.py` y `51_bienvenida.py` |
| E-29 | `harnessId` constante, valida, y el schema sin cambios | sostenido | sí | `63_harness_unico.py`; propio: `git diff e5d7a14 -- comun/schemas/` vacío |
| E-30 | Sin lock o ilegible: BLOCKED y todo calculado; un lock que es arreglo no rompe SessionStart | sostenido | sí | `63_harness_unico.py`; leído en `_leer` y `session-start.py` |
| E-31 | Encabezado `<usuario> - harness v<versión>`, sin ids | sostenido | sí | `63_harness_unico.py` y `05_memoria.py` |
| E-32 | Aviso del recorrido con cualquier lock legible; sin lock, ninguno | sostenido | sí | `13_contexto.py` E-16, E-16b y E-17, y `63_harness_unico.py` |
| E-33 | SessionStart sigue contando las definiciones pendientes | sostenido | sí | `05_memoria.py` |
| E-34 | La CLI muestra el runtime con los tres; nunca "sin el harness de desarrollo" | sostenido | sí | `63_harness_unico.py`; propio, grep sobre `comun/`, `harnesses/` e `install.ps1` |
| E-35 | Mismos renderizadores que `e5d7a14` para el mismo documento | sostenido | sí | `63_harness_unico.py`: tres documentos por cuatro renderizadores |
| E-36 | `-Update` sobre 0.28.0 con desarrollo: 0, el inventario de E-15 y el lock de E-14 | sostenido | sí | `63-harness-unico-instalador.ps1`; propio |
| E-37 | Ese `-Update` no cambia un byte de los seis archivos ni nombra sacados | sostenido | sí | `63-harness-unico-instalador.ps1`; propio, por sha256 |
| E-38 | Un editado a mano conserva su contenido y deja `.nuevo` | sostenido | sí | `63-harness-unico-instalador.ps1`; propio |
| E-39 | Context Bar `RELOAD_REQUIRED`; cambia la huella de `sessionStart`, no la de `statusLine` | sostenido | sí | `63-harness-unico-instalador.ps1`, en el mismo directorio; no se repitió aparte |
| E-40 | La huella del refutador no cambia | sostenido | sí | `63-harness-unico-instalador.ps1`; propio: `dev-refutador.md` sin diff contra `e5d7a14` |
| E-41 | Con analisis y desarrollo: `hu-*` salen del disco y del lock, se nombran; bloque y backup | sostenido | sí | `63-harness-unico-instalador.ps1`; propio |
| E-42 | `hu-redactor.md` editado queda, sin `.nuevo`, fuera del lock y nombrado | sostenido | sí | `63-harness-unico-instalador.ps1`; propio, también con un retirado editado bajo `.claude\harness\` |
| E-43 | Con analisis solo: producto entero, config intacto, CLI 0 y defaults efectivos del manifiesto | sostenido | sí | `63-harness-unico-instalador.ps1`, más un chequeo propio para `rutaCodebase`; ver hallazgo 1 |
| E-44 | Instalar sin `-Update` sobre analisis limpia como E-41 | sostenido | sí | `63-harness-unico-instalador.ps1` |
| E-45 | `-Update` con un id desconocido sale 0 e instala el producto | sostenido | sí | `63-harness-unico-instalador.ps1`; propio, el inventario completo; ver hallazgo 4 |
| E-46 | `-Uninstall` como en 0.28.0 | sostenido | sí | `63-harness-unico-instalador.ps1`; `Invoke-Desinstalar` sin diff contra `e5d7a14` |
| E-47 | `-Uninstall` nuevo sobre 0.28.0 con analisis y desarrollo no deja nada de lo listado | sostenido | no consta | `63-harness-unico-instalador.ps1`; propio |
| E-48 | `-Doctor` sin proyecto, con los requisitos de `manifest.json` y sin harnesses disponibles | sostenido | no consta | `63-harness-unico-instalador.ps1`; propio, con `requierePython` imposible en una copia; ver hallazgo 4 |
| E-49 | `-Doctor -Project`: `harness instalado (v…)` sin ids y la línea de la barra | sostenido | sí | `63-harness-unico-instalador.ps1`; propio |
| E-50 | `-Doctor -Project` no cambia un byte | sostenido | sí | `63-harness-unico-instalador.ps1` |
| E-51 | `manifest.json` es la única fuente de requisitos y de configuración inicial | sostenido | sí | `63-harness-unico-instalador.ps1`, sobre una copia; `claude` está en el PATH |
| E-52 | Registro de agentes de la fábrica válido: 10/10, 27 y 2 | sostenido | sí | `63_harness_unico.py`; propio |
| E-53 | Registro instalado igual a 0.28.0, defecto incluido | sostenido | sí | `63-harness-unico-instalador.ps1`; propio: idéntico, ni mejora ni empeora |
| E-54 | `existe_check` encuentra los cinco checks; el roster no está vacío | sostenido | no consta | `63-harness-unico-instalador.ps1` |
| E-55 | `controles.reporte()` válido en la fábrica, e instalado igual a 0.28.0 | sostenido | no consta | `63-harness-unico-instalador.ps1`, la mitad instalada; propio, las dos mitades; ver hallazgo 4 |
| E-56 | `instalacion.md` dice que `-Harness` ya no existe y qué sale de `analisis` | sostenido | sí | `63_harness_unico.py`; leído en el paso 6 |
| E-57 | La fábrica no nombra manifiestos viejos ni usa `-Harness` | sostenido | sí | `63_harness_unico.py`; propio, grep |
| E-58 | Las adaptaciones retiradas dicen que se retiraron, la versión y el cambio | sostenido | sí | `63_harness_unico.py`; ver lo abierto, el número de versión |
| E-59 | ADR-0012 aceptado, con las tres decisiones | sostenido | sí | `63_harness_unico.py`, y leído |
| E-60 | `.\tests\Invoke-Tests.ps1` sale con 0 | sostenido | no consta | la corrida del refutador: `38337/38337`, exit 0 |
| E-61 | Sin `06-composicion.ps1`; `tests/` sin el parámetro viejo ni las formas de E-12 | sostenido | sí | `63_harness_unico.py`; propio |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Los 53 `sí` están en el
> registro que el constructor dejó en `Cómo se verifica` de la spec: la corrida contra 0.28.0 y
> las copias mutadas A a F. El refutador comprobó que cada mutación descrita puede, de forma
> plausible, poner en rojo el escenario que nombra; no las recreó. Ninguno de los 9 `no consta`
> figura en ese registro.

## La suite

| Corrida | PowerShell | Python | Total | Exit | Duración |
|---|---|---|---|---|---|
| 1, lanzada con `Start-Process` oculto, sin stdin redirigido | 753/754 | 37583/37583 | 38336/38337 | 1 | unos 16 min |
| 2, con stdin redirigido desde un archivo vacío | 754/754 | 37583/37583 | **38337/38337** | **0** | 20 min 50 s |

La falla de la primera corrida no es de este cambio:

- falló `[Instalador — ciclo completo] y el error dice como resolverlo`;
- `Resolve-Usuario` decide con `[Console]::IsInputRedirected`, y en una consola oculta sin
  redirección va a `Read-Host` y muere con el error de modo no interactivo;
- con 0.28.0 pasa igual, y ni `Resolve-Usuario` ni ese caso cambiaron en este cambio.

Es el ítem 2 de `PENDIENTES-FH.md` (`-NonInteractive` cuando stdin es una consola). Después de las
dos corridas, `pre-tool-use.py` y `zonas.py` tenían el hash del principio y `git status` estaba
igual: no hubo que restaurar nada.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **La primera forma de E-43 no distingue `rutaCodebase` en su fixture.** El proyecto del test no
   tiene `docs/codebase/project-context.json`, y `bienvenida._proyecto` solo lee esa ruta cuando el
   archivo existe. Poner `rutaCodebase: "docs/otro"` no cambia ni `harness --json` ni
   `estado --json`. El refutador lo probó aparte, con el archivo puesto: con el config legado,
   `harness --json` muestra el proyecto, y con `docs/otro` no. El valor efectivo es
   `docs/codebase`, el default del manifiesto. `timeoutIntegraciones` sí lo cubre `timeout_de`.
2. **La compuerta depende de que stdin esté redirigido.** Lanzada desde una consola oculta,
   `03-instalador.ps1` falla. Le pasa igual a 0.28.0.
3. **Un borde de E-11.** Si alguien editó a mano `.claude\harness\manifiestos\analisis.json`, el
   `-Update` lo conserva y lo nombra, como pide la regla de los huérfanos, y esa salida dice
   `analisis`. Queda fuera de lo que E-11 mide, y no lo contradice.
4. **Tres tests prueban menos de lo que dice su escenario.** El refutador cerró los tres huecos con
   chequeos propios:
   - E-45 no mira el inventario;
   - E-48 no prueba que `requierePython` salga del manifiesto, porque el 3.9 coincide con el
     default del código;
   - la mitad "fábrica" de E-55 la sostienen los casos 31 a 40, no un test que nombre E-55.
5. **El descuento de los casos 60 y 61 es genérico.** Ignora cualquier `harnesses/<x>/` que ya no
   exista en disco, no solo `analisis`.

Del diff, el refutador confirmó cada punto de lo que queda afuera:

- `dev-refutador.md` y el schema de instalación no tienen diff contra `e5d7a14`;
- no hubo renombres;
- las rutas instaladas son las mismas;
- `comun/` y `harnesses/desarrollo/` no se fusionaron;
- el Agent Registry instalado sigue como estaba;
- `controles/` no se instala;
- `docs/codebase/` no se regeneró;
- no se portó nada de `analisis`;
- no se reescribió la historia.

Los cambios fuera de `Qué se construye` hacían falta para sostener escenarios existentes:
`24_g1_tecnologias.py`, `60_entorno_primero.py`, `61_conocimiento_auto_refresco.py`, un comentario
de `Invoke-Tests.ps1` y dos aserciones de `03-instalador.ps1`.

## Lo que queda abierto, anotado y no escondido

- **Los hallazgos 1, 3 y 4** quedan en `Pendientes/Fix-Harness/PENDIENTES-FH.md`, bajo
  `harness-unico closed with four tests that prove less than their scenario`.
- **El hallazgo 2** ya estaba en `PENDIENTES-FH.md`, como ítem 2 de la tabla.
- **La deuda que la spec dejó afuera a propósito** también está ahí:
  - el Agent Registry inválido en los proyectos instalados;
  - los defaults de `config` repetidos en Python;
  - `docs/codebase/` a regenerar;
  - los comentarios de `post-tool-use.py` y `lib/reglas.py`;
  - el comentario de `dev-refutador.md`;
  - `controles/`, que sigue sin instalarse.
- **Para el cierre:**
  - `manifest.json` está sin trackear y tiene que entrar en el commit, porque E-01 y todo lo demás
    dependen de él;
  - `terceros/terceros.lock.json` dice "Retirado en 0.29.0" con `VERSION` todavía en 0.28.0, y
    `close-a-version` tiene que confirmar ese número;
  - la entrada de `UPGRADE.md` tiene que llevar los cuatro puntos que pide `Cómo se verifica`;
  - el ítem de `aporta`, que salió de `PENDIENTES-FH.md`, tiene que aparecer en la nota de versión.

## Lo que ningún test cubre y se mira con los ojos

Son los dos pasos de `Cómo se verifica` que la spec deja fuera de la suite:

1. **Mirar el lockfile del IGE antes de actualizarlo.** Si lista `analisis`, quien lo usa tiene que
   saber antes del `-Update` que pierde `hu-escribir`, `hu-redactor` y `hu-refutador`.
2. **Una sesión real después del `-Update`, en un proyecto descartable.** Alguien distinto de quien
   construyó ve la barra pedir el reinicio y quedar `ACTIVA` después, y lo anota acá como
   observación.

### 1. El lockfile del IGE — hecho el 02-10-2026, solo lectura

Lo leyó la sesión que cerró la versión. No se corrió ningún `-Update`, y el proyecto no se tocó.

- `C:\Work\GCBA\IGE`, la ruta que nombra `PENDIENTES-FH.md`, no existe en esta máquina.
- El Portal IGE, en `C:\dev\portal-ige-web`, tiene este `.claude\harness.lock.json`:

  ```
  version=0.28.0
  claves=version,harness,instalado,backup,archivos
  harness=comun,desarrollo
  instalado=2026-10-01 13:46:14
  archivos=261 · ningún hu-* en el inventario
  harness.installation.json: harnessId=desarrollo · installedVersion=0.28.0
  ```

**No lista `analisis`.** Su `-Update` a 0.29.0 no le saca ninguna skill ni ningún agente. Lo que va a
ver es que la Context Bar pide reiniciar. No está registrado si el Portal IGE es el mismo proyecto que
el `C:\Work\GCBA\IGE` del ítem de FH.

### 2. La sesión real — observada el 02-10-2026

**Observó:** Nahue Palacio · **Fecha:** 02-10-2026, 15:12 · **Sesión:** `8a210931` ·
**Proyecto:** `C:\dev\harness-unico-sesion-real`

Abrió Claude Code en el proyecto actualizado, mandó un mensaje, salió y corrió
`dev-harness.py harness`. Lo que dice abajo lo contrastó la sesión que cierra contra el disco y
contra la transcripción de esa sesión, y coincide.

- **SessionStart sin errores.** Los tres adjuntos de SessionStart salieron con código 0, y en la
  transcripción no hay ningún error de hook. El encabezado del contexto dice
  `Sesion Real - harness v0.29.0`.
- **La barra pidió el reinicio.** En la bienvenida, *Observabilidad* decía
  `Context Bar  REQUIERE REINICIO`, con *Context Bar configurada. Reiniciá la sesión de Claude Code
  para activarla.* La bienvenida se calcula antes del primer dibujo.
- **La barra se dibujó.** A las 15:13:27 dejó `.claude\runtime\contextbar.json`, con la sesión
  `8a210931`, la misma huella `e1a27451…` que registró el `-Update`, `integrationVersion` `1.2.0`,
  `block4: OK` y `presentation.ansi: ENABLED`. También escribió el libro del Bloque 4 de esa sesión.
- **Quedó `ACTIVA`.** Después, `dev-harness.py harness` decía:

  ```
  ✓ Harness instalado correctamente (v0.29.0)
  Block 4 Accounting        ✓ ACTIVO
  Context Bar               ✓ ACTIVA (última sesión: 8a210931)
  Security Reporting        ✓ ACTIVO
  Reinicio de Claude Code   no hace falta
  Última sesión vista       8a210931 cargó la Context Bar (último dibujo: 2026-10-02T15:13:27)
  ```

Dos cosas que se vieron y no contradicen la spec. Ninguna es de este cambio:

- **La primera sesión mostró la bienvenida entera, no** *Harness GCBA actualizado: 0.28.0 → 0.29.0*.
  El proyecto descartable nunca había abierto una sesión con 0.28.0, así que `firstRunShown` estaba
  en `false`, y la primera sesión después de instalar muestra la bienvenida entera. Lo que se le
  pidió mirar a la persona decía otra cosa: la expectativa estaba mal escrita, no el harness.
- **`harness.installation.json` sigue diciendo `RELOAD_REQUIRED`** después del dibujo. Lo escribió
  SessionStart a las 15:12:59, antes de que la barra dibujara. `dev-harness.py harness` resuelve el
  estado con la señal de vida, sin volver a escribir el archivo. Se actualiza en el próximo
  SessionStart. Los renderizadores y el registro de la barra no cambiaron en este cambio.

Lo preparó el 02-10-2026 la sesión que construyó y cerró, en `C:\dev\harness-unico-sesion-real` (un
repo git vacío):

- se instaló con el `install.ps1` de `e5d7a14`, sacado con `git archive`, y
  `-Harness desarrollo -Usuario 'Sesion Real'`. Salió con 0: lock 0.28.0, `harness=comun,desarrollo`,
  261 archivos;
- se corrió `-Update` con el instalador de este cambio, ya con `VERSION` en 0.29.0. Salió con 0 y
  dijo *Actualizado de v0.28.0 a v0.29.0.* Dejó el lock con `version,instalado,backup,archivos`
  (259 archivos) y borró `.claude\harness\manifiestos\`. Dijo
  *Reiniciá la sesión de Claude Code para activarla.*, y dejó en `harness.installation.json`
  `contextBar.state = RELOAD_REQUIRED`, con `reloadRequired: true` y
  `activeInCurrentSession: false`. `dev-harness.py harness` decía `Context Bar  REQUIERE REINICIO`.

📌 **Una respuesta que el disco no respalda no cuenta como observación.** Antes de esta, el mismo
02-10-2026, la persona contestó "Todo como se esperaba". Pero a las 13:16 el proyecto seguía igual
que después del `-Update`:

- `harness.installation.json` no se había vuelto a escribir desde las 11:45;
- `contextBar.state` seguía en `RELOAD_REQUIRED`, con `lastSessionId` vacío;
- `welcome.lastShownAt` seguía en `null`;
- en `%USERPROFILE%\.claude\projects\` no había ninguna sesión de Claude Code para esa carpeta.

Una sesión que hubiera corrido ahí habría dejado al menos la marca de SessionStart. Esa respuesta no
se tomó como observación. La que vale es la de las 15:12, que dejó todos esos rastros.
