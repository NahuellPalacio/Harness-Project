# Un solo harness: `desarrollo` es el producto, `comun` es su base y `analisis` se retira

**Estado:** verificado y cerrado · **Fecha:** 01-10-2026 · **Versión de partida:** 0.28.0 (`e5d7a14`)

## Qué problema resuelve

El producto es un solo harness. El repositorio y el instalador todavía están armados para varios:
`comun/` como "el harness que siempre está", `harnesses/<id>/` como tipos de trabajo que se
descubren, se eligen con `-Harness` y se componen. Las decisiones de producto que este cambio
ejecuta son seis: `desarrollo` es el harness; lo útil de `comun` es su base; `analisis` es legado y
se va; componer harnesses deja de ser parte del producto; nadie elige un tipo al instalar; y nada de
esto agrega una capacidad funcional.

### La cadena de composición, eslabón por eslabón

Leída en `install.ps1` y en el código instalado de 0.28.0. A la derecha, qué pasa con cada eslabón.

```
install.ps1  (despacho, 2373-2376)
├─ sin -Harness no instala: "falta -Harness. Disponibles: …"                 → desaparece
└─ Invoke-Instalar -Ids
   ├─ parte "a,b" cuando llega por -File (1704-1706)                         → desaparece
   ├─ hereda los ids del lock previo: instalar es aditivo (1717-1729)         → desaparece
   ├─ ordena los ids, orden canónico (1735)                                   → desaparece
   ├─ Get-HarnessDisponibles: descubre harnesses/*/manifest.json (130-144)    → desaparece
   ├─ Read-Manifiesto de comun + uno por id (1746-1749)                       → lee un solo manifiesto
   ├─ valida prefijos disjuntos entre manifiestos (1751-1757)                 → desaparece
   ├─ copia comun a .claude\harness\{hooks,reglas,schemas,checks,bin},
   │  .claude\{skills,agents} y normativa\extractos (1812-1828)               → se conserva igual
   ├─ copia cada id a checks\<id>, bin\<id>, reglas\<id>, skills, agents
   │  (1831-1838)                                                             → copia fija de harnesses\desarrollo
   │                                                                            a checks\desarrollo, bin\desarrollo,
   │                                                                            reglas\desarrollo; sin bucle
   ├─ escribe .claude\harness\manifiestos\<id>.json (1840-1847)               → desaparece: nadie lo lee
   ├─ siembra harness.config.json con la config de cada manifiesto (752-758)  → la config de un manifiesto
   ├─ "$Ids -contains 'desarrollo'": statusLine, .env, presupuesto, prueba de
   │  la barra, integraciones, conocimiento, mensajes (1776, 1861, 1902, 1928,
   │  2044, 2060, 2085, 2109)                                                 → incondicional
   ├─ bloque del CLAUDE.md = comun + claude-md\bloque.md de cada id (1939-1943) → dos fragmentos fijos, mismo texto
   └─ lock.harness = 'comun' + ids (2020)                                     → el campo desaparece
Invoke-Actualizar: reinstala los ids de lock.harness (2128)                   → reinstala el producto; el campo se ignora
Invoke-Doctor: "harness disponibles" (466-473), "harness instalado: <ids>"
  (1585), Context Bar solo si el lock dice desarrollo (1624)                  → sin lista de ids; la barra siempre
Invoke-Desinstalar: borra lo que lista el lock                                → se conserva igual
```

La composición no termina en el instalador. Tres lugares del código instalado leen los ids del
lockfile y cambian de comportamiento según lo que dice:

| Dónde | Qué hace con los ids | Qué pasa |
|---|---|---|
| `comun/hooks/lib/bienvenida.py:1243-1249` | Un lock sin la lista `harness` cuenta como `LOCKFILE_UNREADABLE`: con el lock nuevo, toda instalación saldría `BLOCKED` | Legible es "JSON que es un objeto"; `harness` no se mira |
| `comun/hooks/session-start.py:102-114` | Encabezado `harness: comun, desarrollo v0.28.0`. Un lock que es JSON pero no objeto levanta `AttributeError`, que no se atrapa | Sin ids; misma definición de legible |
| `comun/hooks/session-start.py:174` | El aviso del recorrido del código, solo con `desarrollo` | Con lockfile legible, siempre |
| `comun/hooks/lib/bienvenida.py:1263-1275` | Sin `desarrollo`: sin integraciones, `knowledge.applies: false`, runtime `NOT_CONFIGURED` (`_sin_desarrollo`, 1171-1181) | Siempre como con `desarrollo` |
| `comun/hooks/lib/bienvenida.py:1297` | `harnessId` = los ids sin `comun`, unidos con `+` | Constante `"desarrollo"` |
| `comun/hooks/lib/bienvenida.py:1387` | Las huellas de la barra, solo con `desarrollo` | Siempre |
| `harnesses/desarrollo/bin/dev-harness.py:341-343, 440, 600` | `sin el harness de desarrollo: no hay Bloque 4…` | Rama muerta: se va |
| `bienvenida.py:1551` (`_con_desarrollo`) y los renderizadores en `1657, 1699, 1720, 1754, 1796`; `dev-harness.py:391, 403` | Muestran secciones según `knowledge.applies` del documento | **No cambian.** Leen el documento, no el lock, y con el resolvedor nuevo `applies` es siempre `true` |

### Lo que la composición rompía sin que se viera

Se instaló 0.28.0 de verdad en un directorio descartable, el 01-10-2026, para tener la línea de base:

| Instalación 0.28.0 | Archivos en el lock | Tiempo |
|---|---|---|
| `-Harness desarrollo` | 261 | 16,0 s |
| `-Harness analisis` | 78 | 6,9 s |
| `analisis` y después `desarrollo` | 265 | 13,0 s el segundo paso |

Y aparecieron dos defectos que existen **por** la separación en varios harnesses:

- **El registro de agentes no conoce lo que instala `comun`.** En un proyecto instalado,
  `registro_agentes.reporte()` da `registryValid: false`: `flush-memoria` y `leer-docs` salen
  `ORPHAN_AGENT` con severidad `ERROR` e `instalar-desde-github` sale `UNDECLARED_SKILL`. En la
  fábrica da `true`, porque ahí solo mira `harnesses/desarrollo/`. Hoy no se nota porque ninguna
  CLI llama a `reporte()`. Este cambio **no** lo arregla (ver `Qué queda afuera`).
- **Un `-Update` que deja de instalar algo fuera de `.claude\harness\` lo deja huérfano.** El
  `-Update` regenera `.claude\harness\` entero, pero `.claude\skills\` y `.claude\agents\` no: lo
  que el lock anterior listaba ahí y la versión nueva no copia queda en disco, fuera del inventario,
  invisible para `-Doctor` y para `-Uninstall`. Retirar `analisis` es exactamente ese caso, con
  `hu-escribir`, `hu-redactor` y `hu-refutador`. Este cambio **sí** lo arregla, porque sin eso el
  retiro de `analisis` deja basura en cada proyecto que lo tenía.

## Arquitectura fuente e instalada

Son dos estructuras, y no tienen por qué tener la misma forma.

| | Fábrica (este repo) | Instalado (`.claude\` del proyecto) |
|---|---|---|
| Base | `comun/{hooks,reglas,schemas,checks,bin,skills,agents,claude-md,settings}` | `harness\{hooks,reglas,schemas,checks,bin}`, `skills\`, `agents\` |
| Producto | `harnesses/desarrollo/{bin,checks,reglas,skills,agents,claude-md,.env.example}` | `harness\bin\desarrollo\`, `harness\checks\desarrollo\`, `harness\reglas\desarrollo\`, `skills\`, `agents\` |
| Controles | `harnesses/desarrollo/controles/` | **no se instala** (FH #4) |
| Normativa | `normativa/extractos/` | `harness\normativa\extractos\` |
| Manifiesto | `comun/manifest.json` + uno por harness | `harness\manifiestos\<id>.json`, sin lector |

**Después de este cambio**, la fábrica conserva `comun/` y `harnesses/desarrollo/` donde están,
con un solo `manifest.json` en la raíz, y sin `harnesses/analisis/`. Lo instalado queda con la
misma forma, sin `harness\manifiestos\`. El instalador lleva un mapa fijo de origen a destino, y ese
mapa vive en un solo lugar: `install.ps1`.

Los resolvedores que buscan un archivo "instalado o en la fábrica" —`bin/rutas.py`,
`roster._raices_de_reglas`, `roster._dir_del_harness`, `roster.existe_check`,
`bienvenida.ruta_de_la_politica`, `bienvenida._rutas_de_runtime`,
`registro_agentes.raices_de_componentes`— **no son maquinaria de composición**. Existen porque
la fábrica y lo instalado tienen formas distintas, y esa diferencia no cambia acá. Se conservan
sin tocar.

## Rutas: contrato público y detalle interno

| Ruta o nombre | Quién la ve | Clase | Qué pasa |
|---|---|---|---|
| `.claude\harness\bin\desarrollo\dev-harness.py` | Personas (README, `docs/`, UPGRADE, `.env.example`, mensajes del instalador y de la bienvenida) y modelos (`dev-orchestrator.md` la ejecuta) | **Pública** | Se conserva |
| `.claude\harness\bin\desarrollo\contabilidad\statusline.py` | `statusLine` de `settings.json`, y su huella en `harness.installation.json` | **Pública** | Se conserva |
| `.claude\harness\run-hook.cmd` y `.sh` | Los cuatro hooks de `settings.json` | **Pública** | Se conserva |
| Ids `dev-*` de agentes y skills | Claude Code, `agent-registry.json`, planes en `.claude\planes\`, eventos de contabilidad, la caché de refutación (`dev-refutador/2.0`) | **Pública** | Se conserva |
| `flush-memoria`, `leer-docs`, `instalar-desde-github` | Claude Code | **Pública** | Se conserva |
| `hu-escribir`, `hu-redactor`, `hu-refutador` | Claude Code, en proyectos con `analisis` | **Pública** | **Desaparece** |
| Marcador `<!-- HARNESS:COMUN -->` | El `CLAUDE.md` versionado de cada proyecto | **Pública** | Se conserva |
| `harness.installation.json` y su `harnessId` | Schema `harness-installation/1.1` | **Pública** | Se conserva; `harnessId` queda `"desarrollo"` |
| `harness.config.json`, `.env`, `.env.example`, `harness.presupuesto.json` | La persona | **Pública** | Se conserva |
| `.claude\harness\reglas\desarrollo\` | `roster`, `bienvenida`, `bases` | Interna | Se conserva |
| `.claude\harness\checks\desarrollo\` | `post-tool-use.py` (`os.walk`) y `roster.existe_check` | Interna | Se conserva |
| `.claude\harness\bin\desarrollo\**` (el resto) | La CLI y la barra, por `sys.path` | Interna | Se conserva |
| `.claude\harness.lock.json` | El instalador, `bienvenida`, `session-start`, `contexto-armar.version_initiator` | Interna | Se conserva **sin** `harness` |
| `.claude\harness\manifiestos\` | Nadie | Interna | **Desaparece** |
| `.claude\{contextos,planes,refutaciones,runtime}\`, `harness.{capacidades,fuentes,integraciones}.json` | La CLI | Interna | No guardan ids de harness: no cambian |

📌 **El segmento `desarrollo` de las rutas instaladas deja de ser un espacio de nombres y pasa a ser
un nombre fijo.** Ya no hay un `$id` que lo produzca. Su único motivo original era separar
harnesses, pero hoy es parte de la dirección pública de la CLI. Mudarlo es un cambio aparte, con su
propio costo, y no hace falta para eliminar la composición.

## Hallazgos de dominio (contexto, no alcance)

**El corte `comun` / `desarrollo` nunca fue un corte de capas.** Fue "lo que también necesitaba
`analisis`" contra "lo que solo necesitaba `desarrollo`". Con `analisis` afuera, ese corte se queda
sin criterio. Eso explica todo lo que sigue:

- **`comun` es base, pero no solo base.** Infraestructura de verdad: los cuatro hooks y
  `lib/hook.py`, el ejecutor de checks (`lib/reglas.py`), el bloqueo de secretos (`lib/secretos.py`
  y `reglas/secretos.patrones.json`), las zonas del `CLAUDE.md` (`lib/zonas.py`,
  `checks/claude-md-zonas.py`), `settings/` y la plantilla del `CLAUDE.md`. Lo que no es
  infraestructura: `lib/bienvenida.py` resuelve integraciones, fuentes, Bloque 4, Context Bar y
  reporte de seguridad, y conoce `bin/desarrollo/contabilidad/statusline.py` por ruta. Es la vista
  de estado de toda la aplicación, y vive en la base porque el hook la importa sin poder importar
  `harnesses/`. `schemas/` tiene los 46 contratos del producto, casi todos de dominio
  (`task-context`, `orchestration-plan`, `refutation-*`, `es0902-*`). Y `bin/contexto-armar.py` es a
  la vez el validador de schemas que usa todo `bin/` y el armador del `project-context` de
  `dev-iniciador-code`.
- **`desarrollo` es dominio y aplicación, con infraestructura adentro.** `dev-harness.py` es la
  entrada de la aplicación: un caso de uso por subcomando (`setup`, `estado`, `contexto`, `plan`,
  `fuentes`, `seguridad`, `refute`, `contabilidad`, `presupuesto`, `harness`). `orquestacion/`
  mezcla 28 módulos de servicios y reglas: registro de agentes, controles, matriz normativa,
  refutación, frescura. `integraciones/` y `contabilidad/adaptadores/` son adaptadores de
  infraestructura. `bin/rutas.py` es infraestructura pura y vive en el producto. `reglas/` es dato
  de dominio.
- **`comun` instala agentes y skills que el registro del producto no declara.** Es el primer
  defecto de arriba, y es el síntoma más claro de dos fuentes: `agent-registry.json` dice ser la
  fuente de existencia de los agentes, pero el producto instala dos agentes y una skill que no
  figuran ahí.
- **Una función de `comun` que solo sembraba `analisis`.** `session-start.py` cuenta las
  definiciones pendientes abiertas si `harness.config.json` trae `rutaDefinicionesPendientes`, y esa
  clave solo la sembraba `harnesses/analisis/manifest.json`. Se conserva: es comportamiento de
  `comun`, y sigue andando en todo proyecto que la tenga.
- **Nombres históricos que llegaron a contratos externos.** `bin/desarrollo/` en la ruta de la CLI;
  `HARNESS:COMUN` en el `CLAUDE.md` versionado de cada proyecto; `harnessId: "desarrollo"`; el
  prefijo `dev-` en ids de agentes y skills que guardan los planes, la caché de refutación y los
  eventos de contabilidad; el campo `harness` del lockfile, que este cambio saca.
- **Falsos positivos de la búsqueda**, que no se tocan: `bin/contexto/comun.py` (`from contexto
  import comun`) es "común" de "compartido", no el harness; `contexto-armar.py:530`
  (`("desa", "desarrollo", "dev")`) son alias de nombres de ambiente.

## Qué queda afuera

- **Renombrar `dev-*` o `dev-harness.py`.** No es un rebranding. Los ids están guardados en planes,
  en la caché de refutación, en eventos de contabilidad y en el registro; renombrarlos es un cambio
  con su propia migración.
- **Mudar las rutas instaladas** `bin\desarrollo\`, `reglas\desarrollo\` y `checks\desarrollo\`.
  La primera es la dirección pública de la CLI. Las otras dos son internas, pero sus lectores caen en
  silencio cuando no las encuentran: `roster.cargar()` devuelve `{}` y "el plan lo declara y
  sigue". Mudarlas no es necesario para eliminar la composición, y queda como deuda.
- **Mover el árbol fuente** (`comun/` y `harnesses/desarrollo/` a un solo árbol). Toca unos 70
  archivos de `tests/casos/` y todos los resolvedores de arriba, y decidir dónde va cada cosa es justamente el
  corte base/dominio que este cambio solo descubre. Es un cambio aparte, con comportamiento
  congelado, para `harness-staff-engineer`. Mientras tanto, el repo conserva un `harnesses/` con un
  solo hijo, y ese es su costo.
- **Instalar `controles/`** (FH #4). Agrega capacidad a los proyectos instalados. Se anota en el
  ítem que, sin composición, el destino ya no necesita un `<id>`.
- **Arreglar el registro de agentes en un proyecto instalado.** Declarar `flush-memoria`,
  `leer-docs` e `instalar-desde-github`, o hacer que el diagnóstico de disco mire solo lo que instaló
  el harness, cambia la semántica del Agent Registry. Va a `PENDIENTES-FH.md` con este hallazgo.
- **Tocar `harnesses/desarrollo/agents/dev-refutador.md`**, aunque su comentario nombre a
  `harnesses/analisis/agents/hu-refutador.md`. La huella de ese archivo es parte de la clave de caché
  de la refutación atómica (`refutacion.py:41-45`): cambiar una coma invalida la caché en cada
  proyecto. El comentario no es funcional y queda como deuda, junto con la traducción de ADR-0011.
- **Regenerar `docs/codebase/`**, el índice de la propia fábrica. Lo escribe `dev-iniciador-code`, es
  una corrida de un modelo, y su encabezado prohíbe editarlo a mano. Queda describiendo `analisis`
  hasta que se regenere, y se anota.
- **Reescribir la historia.** `docs/cambios/*`, `docs/versiones/*`, las entradas viejas de
  `CHANGELOG.md` y `UPGRADE.md` y los ADR son registro de lo que pasó, y nombran `analisis` con
  razón.
- **Renombrar el marcador `HARNESS:COMUN`.** Con otro marcador, `Set-BloqueMarcado` no encuentra el
  bloque viejo y agrega un segundo en cada `CLAUDE.md` existente.
- **Cambiar `harness-installation-state.schema.json`.** El documento persistido no cambia de forma.
- **Llevar a `desarrollo` algo de `analisis`.** `hu-escribir`, el redactor, el refutador de
  historias y las reglas de "Trabajo funcional" se retiran. Portarlas sería una capacidad nueva.
- **Volver a 0.28.0 desde un proyecto actualizado.** No se soporta. Queda dicho en UPGRADE.
- **Los comentarios de `post-tool-use.py` y `lib/reglas.py`** que dicen "los harness instalados".
  Son archivos del camino caliente que este cambio no necesita tocar, y el escenario E-16 los fija
  byte a byte. Quedan como deuda.
- **La duplicación del mapa de instalación en `tests/medir_barra.py` (`ARBOLES`)**, que usa
  `-Doctor`. Existía antes y no viene de la composición; sus rutas siguen valiendo.
- **Que `-WhatIf` no nombre `.env` ni `.env.example`.** Ya era así con `desarrollo`, y se conserva.
- **Los defaults de `config` repetidos en Python.** Cuando a `harness.config.json` le falta una
  clave, el valor no sale de `manifest.json` sino de un default escrito en el código:
  - `rutaCodebase` = `"docs/codebase"` en `bienvenida.py:253`, `session-start.py:190`,
    `dev-harness.py:1132` y `contexto/repositorio.py:63`;
  - `timeoutIntegraciones` = 5 en `dev-harness.py:90` y en `integraciones/http.py:27`;
  - `fichaTipoDeIssue` en `contexto/proyecto.py:16`;
  - `topeTextoDocumento` en `contexto/documentos.py:19`.

  Hoy coinciden con el manifiesto, y E-43 lo fija para los dos valores que leen `harness` y
  `estado`. Hacer que el código lea el manifiesto cambiaría de dónde sale un valor en todos los
  proyectos, y eso no es consolidación. Va a `PENDIENTES-FH.md`.

## Las decisiones, y por qué

### Un manifiesto, en la raíz, con lo que alguien lee

`manifest.json` en la raíz del repo, al lado de `VERSION` y de `install.ps1`, reemplaza a
`comun/manifest.json`, `harnesses/desarrollo/manifest.json` y `harnesses/analisis/manifest.json`.
Lleva solo las claves que tienen un lector: `requiereClaudeCode` y `requierePython` (`-Doctor`),
`capacidadesSoportadas` (E-23 de `18_integraciones.py`) y `config` (la siembra de
`harness.config.json`). `config` es la de `comun` seguida de la de `desarrollo`, en el mismo orden,
para que el archivo sembrado no cambie. Eso incluye `usuario: ""` como primera clave, como la traía
`comun`: el instalador sigue poniendo el nombre real antes y salteando esa clave, igual que hoy
(`install.ps1:748-756`).

Salen `id` y `prefijo`, que solo servían para componer, y `aporta` y `claudeMd`, que nadie lee (FH,
"`aporta` in every manifest is decorative": se cierra por la salida chica, "el directorio es la
declaración"). Sale `descripcion`, que el instalador exigía y nunca mostraba.

Se descartó dejar `comun/manifest.json` como el único: `comun` no es el producto. También se
descartó dejar `harnesses/desarrollo/manifest.json`: un `manifest.json` adentro de `harnesses/` es
exactamente lo que buscaba el descubrimiento.

### `-Harness` desaparece, sin reemplazo, y los posicionales se apagan

`install.ps1` deja de declarar `-Harness`. Quien lo pase recibe el error de PowerShell, que nombra
el parámetro: *No se encuentra ningún parámetro que coincida con el nombre del parámetro
'Harness'*. Sale con código 1 sin correr una línea del script. Se comprobó el 01-10-2026 con
`powershell.exe -File`.

Sacar un parámetro corre la posición de los siguientes. Con `-Project X analisis`, el `analisis`
que hoy cae en `-Harness` caería en silencio en `-Usuario`: también se comprobó. Por eso el script
pasa a `[CmdletBinding(SupportsShouldProcess, PositionalBinding=$false)]`. Es la única forma de que
la desaparición falle a la vista. Ningún documento usa posicionales.

Se descartó un `-Harness` que solo existiera para rechazar con un mensaje propio. Sería una
compatibilidad sin fecha de baja, y el error de PowerShell ya nombra lo que hay que sacar. También
se descartó aceptarlo en silencio, porque mantiene vivo el concepto.

### Las rutas instaladas no cambian

Ver la tabla de rutas. Es la decisión de menos cambio accidental: la CLI sigue donde la buscan las
personas, los agentes y UPGRADE, la huella del `statusLine` no cambia por la ruta y ningún
resolvedor cae en silencio. Se descartó aplanar `bin\`, `reglas\` y `checks\`. Rompe la CLI,
obliga a reiniciar la barra en cada proyecto y no saca ninguna maquinaria de composición que este
cambio no saque igual.

### El árbol fuente no se mueve

Ver `Qué queda afuera`. Lo que desaparece de la fábrica es `harnesses/analisis/` y los manifiestos
viejos. Lo que se queda conserva su ruta, y por eso este cambio no toca ni un resolvedor.

### El lockfile deja de llevar `harness`, y lo que dependía de `desarrollo` pasa a ser incondicional

El lock nuevo lleva `version`, `instalado`, `backup` y `archivos`. Ningún lector sigue mirando
`harness`, y uno viejo que lo tenga se lee igual: el campo se ignora. **Legible**, para
`bienvenida.py` y para `session-start.py`, quiere decir que el archivo se puede leer, es JSON y ese
JSON es un objeto. Cualquier otra cosa es `LOCKFILE_UNREADABLE` para la bienvenida y "sin lockfile"
para SessionStart, que no levanta. Todo lo que hoy depende de
`'desarrollo'` pasa a correr siempre. Del lado del instalador: `statusLine`, `.env`, presupuesto,
prueba de la barra, integraciones y conocimiento. Del lado del código instalado: lo que el resolvedor
de la bienvenida calcula (integraciones, configuración, conocimiento, refresco y los tres
componentes de runtime), las huellas de la barra y el aviso del recorrido del código. Los
renderizadores de `bienvenida.py` no se tocan: siguen mirando `knowledge.applies` del documento, que
el resolvedor nuevo siempre pone en `true`.

Se descartó seguir escribiendo `harness: ["comun", "desarrollo"]`. Sería persistir el vocabulario
de la composición sin nadie que lo lea, y el pedido es no mantener compatibilidad por las dudas.

### `harnessId` queda `"desarrollo"`, constante

El campo es obligatorio en el schema 1.1 y hoy vale `"desarrollo"` en todo proyecto `comun +
desarrollo`. Una constante con ese valor no cambia ni un byte del estado persistido de esos
proyectos y no toca el schema. Se descartó sacarlo, porque cambia el schema por un campo que nadie
lee. También se descartó cambiarlo a otro valor: es un rebranding.

### Instalar ya no es aditivo, y limpia lo que el lock anterior dejaba

Sin ids no hay nada que heredar. Instalar sobre una instalación existente reinstala el producto. Ahí,
y en `-Update`, rige una regla nueva y genérica. Un **huérfano** es un archivo que el lock anterior
lista y el inventario nuevo no:

1. **Cuándo.** La limpieza corre después de que los cuatro hooks respondieron: ya no hay vuelta
   atrás. Si la instalación se revierte o tira antes, no se borra ningún huérfano.
2. **Sin editar** (su sha256 coincide con el del lock anterior): se borra. Si está fuera de
   `.claude\harness\`, la salida lo nombra. Lo de adentro no se nombra, porque `.claude\harness\` se
   regenera entero.
3. **Editado a mano:** queda en disco con su contenido, fuera del inventario y sin `.nuevo`, porque
   no hay versión nueva. La salida lo nombra como un archivo que ya no es parte del harness. En
   `-Update`, si estaba bajo `.claude\harness\`, se restaura desde lo guardado y se recrea su
   carpeta. Hoy el bucle de restauración (`install.ps1:2223-2227`) no recrea la carpeta, y tiraría
   cuando el temporal ya se borró: así se perdería la edición.
4. **Carpetas vacías:** después de borrar, se borra toda carpeta que quedó vacía debajo de
   `.claude\harness\`, `.claude\skills\` o `.claude\agents\`, y una que solo tiene `__pycache__`
   cuenta como vacía. Esas tres raíces no se borran nunca en esta limpieza.

No hay una línea de código que nombre a `analisis`: el lock anterior dice qué había y el inventario
nuevo dice qué hay.

Se descartó abortar el `-Update` de un proyecto con `analisis` y pedir `-Uninstall`. Exige código que
nombre `analisis` para siempre, y la conversión es la decisión de producto.

### Un proyecto con `analisis` pasa a tener el producto entero

`-Update` sobre un lock `["comun", "analisis"]` instala el producto. Crea `.env`, `.env.example` y
`harness.presupuesto.json`, y registra el `statusLine`. Saca `hu-*` y reemplaza las reglas de
"Trabajo funcional" del bloque del `CLAUDE.md` por las de "Trabajo técnico". Antes, el `CLAUDE.md`
queda en el backup, como siempre. `harness.config.json` no se toca: conserva sus claves de
`analisis`, inertes, y le faltan las de `desarrollo`, que el código ya resuelve con su default igual
que en cualquier proyecto instalado antes de que existiera una clave.

### El bloque del `CLAUDE.md` sale igual, byte a byte

El bloque es `comun/claude-md/bloque-comun.md`, dos saltos de línea y
`harnesses/desarrollo/claude-md/bloque.md`, en ese orden fijo y sin bucle. Es el mismo texto que
escribía 0.28.0 con `desarrollo`, así que en esos proyectos el `-Update` no deja diff en un archivo
que se versiona.

### `-Doctor` refleja un producto

Sin la línea `harness disponibles`. Con proyecto: `harness instalado (v<versión>)`, sin ids, y la
línea de la Context Bar siempre. Los requisitos salen de `manifest.json`.

### La bienvenida con el lockfile roto calcula todo

Hoy, sin lockfile legible, los ids quedan vacíos y la bienvenida esconde integraciones,
conocimiento y observabilidad. Con un solo producto no hay qué esconder: el estado sigue `BLOCKED`
con `LOCKFILE_MISSING` o `LOCKFILE_UNREADABLE`, y las secciones se calculan igual. Es el único
caso borde en que cambia lo que se muestra, y queda dicho.

### El registro de agentes se preserva como está, defecto incluido

En la fábrica sigue `registryValid: true`. En un proyecto instalado sigue dando lo que da 0.28.0,
con los mismos tres huérfanos y la misma skill no declarada. "Sigue válido" quiere decir acá **no
empeora**: arreglarlo es un cambio de semántica (ver `Qué queda afuera`).

### Lo que se rompe, dicho

| Qué | Para quién |
|---|---|
| `-Harness` deja de existir; pasarlo sale 1 | Quien lo tenga en un script, un `.cmd` o CI |
| Los argumentos posicionales dejan de bindear | Quien invocara sin nombres (ningún documento lo hace) |
| `analisis` se retira: `hu-escribir`, `hu-redactor`, `hu-refutador` y sus reglas del `CLAUDE.md` salen en el `-Update` | Todo proyecto instalado con `analisis` |
| Instalar deja de ser aditivo | Quien sumaba un segundo harness |
| El lockfile pierde `harness` | Una herramienta externa que lo leyera. El instalador 0.28.0, sobre un proyecto ya actualizado: con `Set-StrictMode 2.0` (`install.ps1:48`), `-Update` (`:2128`) y `-Doctor -Project` (`:1585`) mueren con *No se encuentra la propiedad 'harness'* antes de tocar nada; `-Uninstall` anda. Comprobado el 01-10-2026 |
| `.claude\harness\manifiestos\` desaparece | Nadie lo leía |
| El encabezado de SessionStart pasa de `harness: comun, desarrollo vX` a `harness vX` | El modelo, al abrir sesión |
| `comun/manifest.json` y `harnesses/*/manifest.json` pasan a `manifest.json` | La fábrica: tests, agentes y skills que los nombran |
| `docs/agregar-un-harness.md` desaparece | Quien lo usara |

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `manifest.json` (nuevo) | El único manifiesto: `requiereClaudeCode`, `requierePython`, `capacidadesSoportadas`, `config` |
| `comun/manifest.json`, `harnesses/desarrollo/manifest.json`, `harnesses/analisis/` | Se borran |
| `install.ps1` | Sin `-Harness` y con `PositionalBinding=$false`. Instala con `-Project` y `-Usuario`. Sin `Get-HarnessDisponibles`, sin partir ids, sin herencia, sin orden canónico, sin prefijos y sin `manifiestos\`. `Read-Manifiesto` lee `manifest.json` y exige `requiereClaudeCode`. Copia fija de `harnesses\desarrollo` a `checks\desarrollo`, `bin\desarrollo`, `reglas\desarrollo`, `skills` y `agents`. Las condiciones sobre `'desarrollo'` pasan a incondicionales. El bloque del `CLAUDE.md` sale de dos fragmentos fijos. El lock sin `harness`. La limpieza de lo que el lock anterior lista y el nuevo no, al instalar y en `-Update`. `-Doctor` sin ids. La ayuda (`.PARAMETER`, `.EXAMPLE`) sin `-Harness` |
| `comun/hooks/lib/bienvenida.py` | Solo el resolvedor y el registro: lock legible si es un objeto JSON, sin `ids`, siempre como con `desarrollo`, sin `_sin_desarrollo` y con `harnessId` constante. Los renderizadores no cambian. Sus docstrings ya no hablan de "solo `analisis`" |
| `comun/hooks/session-start.py` | Encabezado `<usuario> - harness v<versión>`. El aviso del recorrido del código con cualquier lockfile legible. Un lock que es JSON pero no objeto cuenta como ausente y no levanta |
| `harnesses/desarrollo/bin/dev-harness.py` | Sin las ramas `sin el harness de desarrollo` |
| `tests/casos/06-composicion.ps1` | Se borra |
| `tests/casos/03-instalador.ps1` | Instala el producto donde instalaba `analisis` |
| `tests/casos/{11,14,17,18,19,20,30,54,57,60,61,62}-*-instalador.ps1` | Instalan sin `-Harness`. 17 y 18 pierden su caso "sin desarrollo" |
| `tests/casos/{05_memoria,10_codebase,13_contexto,51_bienvenida,53_context_bar}.py` | Los casos "solo analisis" se borran, o pasan a probar E-28 y E-31 (el campo `harness` no cambia nada) |
| `tests/casos/18_integraciones.py` | E-23 lee `manifest.json` |
| `tests/casos/63-harness-unico-instalador.ps1`, `tests/casos/63_harness_unico.py` (nuevos) | Los escenarios de esta spec |
| `README.md`, `docs/instalacion.md`, `docs/memoria.md` | Un producto: sin "Los dos harness", sin "Agregar un tercer harness", sin "Sumar el segundo harness", sin `-Harness` |
| `docs/agregar-un-harness.md` | Se borra |
| `docs/mapa/mapa-harness.html` | El mapa de "qué se compone" y "cómo se instala", sin composición |
| `docs/adr/0012-un-solo-harness.md` (nuevo) | La decisión de producto y lo que retira |
| `UPGRADE.md` | La entrada `0.28.0 → <versión>`. La escribe `close-a-version` al cerrar, con lo que pide `Cómo se verifica` |
| `CLAUDE.md` de la fábrica, `.claude/agents/harness-backend-engineer.md`, `.claude/agents/harness-budget-auditor.md`, `.claude/skills/note-a-pending/SKILL.md` | `manifest.json` en vez de `comun/manifest.json` y `harnesses/*/manifest.json`. El comando de prueba sin `-Harness` |
| `terceros/terceros.lock.json` | Las dos adaptaciones en `harnesses/analisis/agents/` quedan registradas como retiradas (ADR-0005) |
| `Pendientes/Fix-Harness/PENDIENTES-FH.md` | Sale el ítem de `aporta`. El de `controles/` pierde el `<id>`. Entran: el registro de agentes en un proyecto instalado, `docs/codebase/` a regenerar, el comentario de `dev-refutador.md`, los comentarios de `post-tool-use.py` y `lib/reglas.py`, y los defaults de `config` repetidos en Python |

## Escenarios verificables

`e5d7a14` es 0.28.0. "Una instalación 0.28.0" es una hecha con el `install.ps1` de `e5d7a14`,
extraído con `git archive` a un temporal. "Una instalación nueva" es una hecha con el
`install.ps1` de este cambio sobre un directorio vacío, con `-Usuario` y nada más. "El mismo
contenido" o "byte a byte" quiere decir iguales después de normalizar CRLF a LF (ver `Riesgos
conocidos`, finales de línea).

### Un solo producto instalable

- **E-01** — `git ls-files` no lista nada bajo `harnesses/analisis/`, y el único `manifest.json`
  versionado del repositorio es el de la raíz. · rojo visto: si
  · se prueba: `63_harness_unico.py`, con `git ls-files`.
- **E-02** — `manifest.json` tiene exactamente las claves `requiereClaudeCode`, `requierePython`,
  `capacidadesSoportadas` y `config`, y ninguna otra. · rojo visto: si
  · se prueba: `63_harness_unico.py`, leyendo el JSON.
- **E-03** — `config` de `manifest.json` es la `config` de `comun/manifest.json` de `e5d7a14` seguida
  de la de `harnesses/desarrollo/manifest.json` de `e5d7a14`: mismas claves, mismos valores, mismo
  orden, con `usuario: ""` primera. · rojo visto: si
  · se prueba: `63_harness_unico.py`, contra `git show e5d7a14:<ruta>`.
- **E-04** — `capacidadesSoportadas` de `manifest.json` es exactamente la unión de las capacidades
  de los adaptadores de Jira y GitLab. · rojo visto: si
  · se prueba: E-23 de `18_integraciones.py`, leyendo `manifest.json`.
- **E-05** — `install.ps1` no declara `-Harness`: `(Get-Command .\install.ps1).Parameters.Keys` no lo
  contiene. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`.
- **E-06** — `.\install.ps1 -Project <vacío> -Usuario 'X'` sale con 0 y deja el harness instalado:
  lockfile, `settings.json` y `harness.installation.json`. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, instalación real por `-File`.
- **E-07** — `-WhatIf` sin `-Harness` sale con 0, no crea nada en el proyecto, lista
  `harness.presupuesto.json` y no nombra `manifiestos`. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, listando el directorio antes y después.

### Lo que desaparece

- **E-08** — `-Harness desarrollo`, `-Harness analisis` y `-Harness analisis,desarrollo`, por `-File`,
  salen con código distinto de 0, la salida nombra `Harness`, y el proyecto queda sin `.claude\`, sin
  `CLAUDE.md` y sin `.gitignore`. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, una corrida por variante.
- **E-09** — `-Project <dir> analisis` (un posicional de más) sale con código distinto de 0 y no
  escribe nada en el proyecto. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`.
- **E-10** — En una copia del repositorio en un temporal, agregar `harnesses/datos/manifest.json`
  con `skills/dat-x/SKILL.md` y `agents/dat-y.md` no cambia nada de lo que se instala: el lockfile
  tiene las mismas rutas que sin ese directorio, y `-Doctor` no nombra `datos`. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, sobre la copia.
- **E-11** — Ninguna salida del instalador, en ninguna ruta (instalar, `-WhatIf`, `-Update`,
  `-Doctor` con y sin proyecto, `-Uninstall`), contiene `harness disponibles`, `se conserva lo ya
  instalado`, `prefijos`, `comun, desarrollo` ni `analisis`. Las salidas de E-08 y E-09 quedan
  afuera: son el error de PowerShell, que repite el argumento que recibió. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, juntando las salidas de los demás casos.
- **E-12** — En `install.ps1` no aparece la palabra `analisis`, en ninguna forma. En `manifest.json`,
  `comun/` y `harnesses/desarrollo/` no aparece ninguno de estos textos: `harnesses/analisis`,
  `harnesses\analisis`, `'analisis'`, `"analisis"`, `` `analisis` ``, `solo analisis`, `hu-escribir`,
  `hu-redactor`, `hu-refutador`, `rutaHU`, `rutaMaquetas`, `gestorTickets`. La única excepción es la
  línea del comentario de `harnesses/desarrollo/agents/dev-refutador.md`, nombrada en el test.
  · rojo visto: si
  · se prueba: `63_harness_unico.py`, recorriendo los archivos versionados.
- **E-13** — `docs/agregar-un-harness.md` no existe. `README.md`, `docs/instalacion.md` y
  `docs/memoria.md` no tienen el parámetro `-Harness` (la expresión `(?<![\w-])-Harness\b`, que no
  agarra `Pendientes/Fix-Harness/` ni `Ideas-Harness`), ni las secciones `Los dos harness`, `Agregar un tercer
  harness` o `Sumar el segundo harness`. · rojo visto: si
  · se prueba: `63_harness_unico.py`.
- **E-14** — Una instalación nueva no tiene `.claude\harness\manifiestos\`, y su lockfile tiene
  exactamente las claves `version`, `instalado`, `backup` y `archivos`. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`.
- **E-62** — `install.ps1` no conserva la maquinaria de composición, ni siquiera sin usar. En el
  texto entero del archivo, comentarios incluidos y sin distinguir mayúsculas, no aparece ninguna de
  estas formas:
  - el nombre `Get-HarnessDisponibles`;
  - una lista de ids de harness: las variables o parámetros `$Ids`, `$id`, `$Harness`, `$heredados`
    y `$disponibles`, y el argumento `-Ids`. Sin lista no hay qué ordenar, así que tampoco queda un
    orden canónico de ids;
  - partir ids por coma: `-split ','` o `-split ","`, con o sin espacios;
  - la herencia desde `lock.harness`: `harness` leído como propiedad de una variable
    (`\$\w+\.harness\b(?![-.])`), `Properties['harness']` o `Properties["harness"]`, y la clave
    `harness =` al armar el lock;
  - la validación de prefijos: `.prefijo`, `['prefijo']`, `$prefijos` y el texto `prefijos
    repetidos`. La palabra `prefijo` suelta sí puede aparecer: el comentario de `Copy-Arbol` la usa
    en otro sentido;
  - `manifiestos`, en cualquier forma: ni la carpeta `.claude\harness\manifiestos\` ni una variable
    con ese nombre;
  - `harnesses` seguido de algo que no sea `\desarrollo` o `/desarrollo` (`harnesses(?![\\/]desarrollo)`).
    No se recorre `harnesses\` ni se arma `harnesses\$id`;
  - una condición sobre qué id está instalado: un operador de comparación o de pertenencia
    (`-contains`, `-notcontains`, `-in`, `-notin`, `-eq`, `-ne`, `-like`, `-match`, también con
    prefijo `c` o `i`) con `'comun'`, `'desarrollo'` o `'analisis'` como operando, de cualquier lado
    y con comillas simples o dobles.

  La palabra `desarrollo` en rutas, como `bin\desarrollo` o `harnesses\desarrollo\.env.example`, no
  cuenta: es parte de los contratos que se conservan. · rojo visto: si
  · se prueba: `63_harness_unico.py`, con una expresión por forma, y cada una nombra E-62 en su
  mensaje.

### Lo que sigue instalado

- **E-15** — El lockfile de una instalación nueva lista exactamente las rutas del de una instalación
  0.28.0 con `-Harness desarrollo`, menos `.claude\harness\manifiestos\comun.json` y
  `.claude\harness\manifiestos\desarrollo.json`: 259 rutas, ni una más ni una menos.
  · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, contra el lock de una instalación 0.28.0 hecha en
  la misma corrida.
- **E-16** — Cada archivo de esas 259 rutas tiene el mismo contenido que en 0.28.0. Hay cinco
  excepciones: `.claude\settings.json` y `.claude\harness\run-hook.cmd`, que llevan rutas de la
  máquina, y los tres que este cambio toca (`.claude\harness\hooks\session-start.py`,
  `.claude\harness\hooks\lib\bienvenida.py` y `.claude\harness\bin\desarrollo\dev-harness.py`).
  · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, archivo por archivo contra la instalación 0.28.0
  de E-15, con los finales de línea normalizados.
- **E-17** — `.claude\settings.json` de una instalación nueva es igual al de una instalación 0.28.0
  con `-Harness desarrollo`, una vez normalizadas la ruta del proyecto y la versión de `$comentario`.
  Eso incluye el mismo `permissions.deny`, los mismos cuatro hooks con `"shell": "powershell"` y el
  mismo `statusLine`, que apunta a `.claude/harness/bin/desarrollo/contabilidad/statusline.py` y
  lleva su huella. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, instalando las dos en el mismo directorio, una
  después de desinstalar la otra.
- **E-18** — El `harness.config.json` de una instalación nueva tiene las mismas claves, los mismos
  valores y el mismo orden que el de una instalación 0.28.0 con `-Harness desarrollo` y el mismo
  `-Usuario`. · rojo visto: no consta
  · se prueba: `63-harness-unico-instalador.ps1`.
- **E-19** — Una instalación nueva crea `.env.example` con su bloque marcado, `.env` y
  `.claude\harness.presupuesto.json`, cada uno byte a byte igual al de 0.28.0 con `desarrollo`. Una
  segunda instalación no cambia `.env` ni una política que ya existía. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, y los casos de 17, 60 y 62 sin `-Harness`.
- **E-20** — El bloque `HARNESS:COMUN` del `CLAUDE.md` de una instalación nueva es byte a byte el de
  una instalación 0.28.0 con `-Harness desarrollo`, marcadores incluidos. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`.
- **E-21** — Una instalación nueva verifica los cuatro hooks con el comando registrado y prueba la
  Context Bar en los shells disponibles. Su salida dice `los cuatro hooks responden correctamente` y
  `Context Bar: el comando registrado corre y dibuja`. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`.
- **E-22** — Una instalación nueva corre el resumen de integraciones y la revisión de fuentes con
  disparador `INSTALL`, y un `-Update`, con `HARNESS_UPDATE`. Se ve en la salida
  (`Integraciones (desde el .env local)`, `Conocimiento:`) y en el `knowledgeRefresh` de
  `harness.installation.json`. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, y 61 sin `-Harness`.
- **E-23** — Los estados de `block4Accounting`, `contextBar` y `securityReporting` en el
  `harness.installation.json` de una instalación nueva, con su `errorCode`, son los mismos que deja
  una instalación 0.28.0 con `-Harness desarrollo`. · rojo visto: no consta
  · se prueba: `63-harness-unico-instalador.ps1`.
- **E-24** — Los casos de instalador 11, 14, 17, 18, 19, 20, 30, 54, 57, 60, 61 y 62 pasan
  instalando sin `-Harness`. Sus aserciones sobre lo que aporta `desarrollo` quedan como estaban. Lo
  único que cambia en cada uno es la línea que instala, los comentarios que nombran `-Harness` o
  `analisis` (como `11-codebase-instalador.ps1:3`) y, en 17 y 18, que se borra el caso "sin
  desarrollo". · rojo visto: no consta
  · se prueba: la suite, y el diff de esos doce archivos.

### Hooks, secretos y checks

- **E-25** — En un proyecto instalado, el comando registrado de `PreToolUse` responde `deny` a una
  escritura con un secreto de confianza alta del catálogo, y a `pre-tool-use-write.json` no le
  responde nada que bloquee. Ninguno de los otros tres hooks responde `deny` a ningún payload de
  `tests/payloads/`. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, por `Invoke-ComandoDeHook`.
- **E-26** — En un proyecto instalado, una escritura de un `.html` sin `lang` hace que el comando
  registrado de `PostToolUse` devuelva el aviso de `dev-accesibilidad-html`, y un `CLAUDE.md` con
  una zona pasada de techo, el de `claude-md-zonas`. · rojo visto: no consta
  · se prueba: `63-harness-unico-instalador.ps1`.

### Bienvenida, estado y SessionStart

- **E-27** — Para un mismo proyecto de prueba y un mismo `momento`, `bienvenida.resolver` de este
  cambio con un lockfile sin `harness` devuelve el mismo documento que el `bienvenida.py` de
  `e5d7a14` con `harness: ["comun", "desarrollo"]`. Entre las dos llamadas solo se reescribe el
  lock. · rojo visto: si
  · se prueba: `63_harness_unico.py`, importando el módulo viejo desde `comun/` de `e5d7a14`
  extraído con `git archive` (ver `Cómo se verifica`).
- **E-28** — El campo `harness` del lockfile no cambia nada: con `["comun", "analisis"]`,
  `["comun", "datos"]`, `[]` o sin el campo, `bienvenida.resolver` devuelve el mismo documento. El
  encabezado y el aviso del recorrido de SessionStart también salen iguales.
  · rojo visto: si
  · se prueba: `63_harness_unico.py`.
- **E-29** — `harnessId` es `"desarrollo"` en todo `harness.installation.json` que escriban el
  instalador o `session-start.py`, diga lo que diga el lockfile, y el documento valida contra
  `harness-installation-state.schema.json`, que no cambia. · rojo visto: si
  · se prueba: `63_harness_unico.py`, y `git diff e5d7a14 -- comun/schemas/` vacío para ese schema.
- **E-30** — Sin lockfile, o con uno ilegible (que no es JSON, o es JSON y no es un objeto), el
  estado es `BLOCKED` con `LOCKFILE_MISSING` o `LOCKFILE_UNREADABLE`. Además, `integrations`,
  `knowledge` (con `applies: true`) y los tres `runtimeComponents` están presentes y se calculan con
  el mismo código que con un lockfile sano. La versión sale de `installedVersion` de
  `harness.installation.json`, como hoy (`bienvenida.py:1255-1256`). Con un lock que es un arreglo
  JSON, `session-start.py` sale con 0 y su bloque no tiene encabezado de harness.
  · rojo visto: si
  · se prueba: `63_harness_unico.py`.
- **E-31** — El encabezado de SessionStart es `<usuario> - harness v<versión>`, sin `comun`,
  `desarrollo` ni `analisis`, también con un lockfile 0.28.0. · rojo visto: si
  · se prueba: `63_harness_unico.py` y `05_memoria.py`.
- **E-32** — SessionStart da el aviso del recorrido del código (sin índice, fichas sin índice, o
  índice sin contrato) con los textos de 0.28.0 en todo proyecto con lockfile legible. Sin lockfile
  no da ninguno. · rojo visto: si
  · se prueba: E-16 y E-17 de `13_contexto.py` sin `desarrollo` en el lock, y un caso sin lock.
- **E-33** — SessionStart sigue contando las definiciones pendientes abiertas cuando
  `harness.config.json` trae `rutaDefinicionesPendientes`. · rojo visto: si
  · se prueba: `05_memoria.py`.
- **E-34** — `dev-harness.py harness`, con y sin `--verbose`, muestra `Runtime / Observabilidad` con
  los tres componentes en cualquier proyecto instalado, y ningún comando de la CLI imprime `sin el
  harness de desarrollo`. · rojo visto: si
  · se prueba: `63_harness_unico.py`.
- **E-35** — Para un mismo documento, los renderizadores de este cambio y los de `e5d7a14` dan el
  mismo texto: la bienvenida completa, el aviso de actualización y la línea compacta. Se compara
  solo el renderizado. Cada documento se arma una vez y se les pasa el mismo a los dos módulos; no
  se pide que los dos resolvedores lleguen a ese documento. Sin lockfile, el resolvedor nuevo
  calcula a propósito más que el viejo (E-30), y esa diferencia no es materia de este escenario. Los
  documentos son tres, armados con el resolvedor nuevo: el de E-27, uno `BLOCKED` sin lockfile (que
  por E-30 trae integraciones, conocimiento y runtime) y uno con un aviso de actualización
  pendiente. · rojo visto: si
  · se prueba: `63_harness_unico.py`, pasándole cada documento a los renderizadores del módulo
  viejo de E-27 y a los del nuevo.

### `-Update` desde 0.28.0

- **E-36** — `-Update` sobre una instalación 0.28.0 con `-Harness desarrollo` sale con 0 y deja el
  inventario de E-15 y el lockfile de E-14. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`.
- **E-37** — Ese `-Update` no cambia ni un byte de `CLAUDE.md`, `.gitignore`, `.env`,
  `.env.example`, `harness.config.json` ni `harness.presupuesto.json`, y su salida no nombra
  ningún archivo sacado. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, con sha256 antes y después.
- **E-38** — Un archivo del harness editado a mano antes de ese `-Update` conserva su contenido, y la
  versión nueva queda al lado como `.nuevo`, igual que en 0.28.0. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, editando una skill `dev-*`.
- **E-39** — Partiendo de una barra que antes del `-Update` no pedía reinicio (con una señal de vida
  válida, posterior a su registro), después de ese `-Update` la Context Bar queda `RELOAD_REQUIRED`,
  porque cambió `session-start.py`, y la salida dice `Reiniciá la sesión de Claude Code para
  activarla`. En `runtimeComponents.contextBar.fingerprints`, `sessionStart` cambió y `statusLine`
  no. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, en el mismo directorio de la instalación 0.28.0
  y no en una copia: el `statusLine` lleva la ruta absoluta del proyecto (`install.ps1:1120`), y en
  otra carpeta su huella cambiaría sola. La señal se escribe como lo hace
  `54-context-bar-instalador.ps1`.
- **E-40** — Después de ese `-Update`, `refutacion.contrato_del_refutador()` devuelve la misma
  `fingerprint` que antes: la caché de la refutación atómica sigue valiendo. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, corriéndolo con el `bin` instalado antes y después.
- **E-41** — `-Update` sobre una instalación 0.28.0 con `-Harness analisis,desarrollo` sale con 0.
  `.claude\skills\hu-escribir\` (con el directorio), `.claude\agents\hu-redactor.md` y
  `.claude\agents\hu-refutador.md` ya no están ni en disco ni en el lockfile, y la salida nombra los
  tres. El bloque del `CLAUDE.md` queda como el de E-20, y el `CLAUDE.md` anterior está en el
  backup de esa corrida. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`.
- **E-42** — Igual que E-41, pero con `hu-redactor.md` editado a mano antes. Queda en disco con su
  contenido, sin `hu-redactor.md.nuevo` y fuera del lockfile, y la salida lo nombra como un archivo
  que ya no es parte del harness. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`.
- **E-43** — `-Update` sobre una instalación 0.28.0 con `-Harness analisis` sale con 0 y deja el
  producto entero: el inventario de E-15, `.env`, `.env.example`, `harness.presupuesto.json` y el
  `statusLine`. Los tres `hu-*` salen. `harness.config.json` queda byte a byte como estaba, así que
  le faltan las claves de `config` que aportaba `desarrollo`. Después, `dev-harness.py harness` y
  `dev-harness.py estado` salen con 0. Además, los valores que esos dos comandos leen de
  `harness.config.json` valen, con ese config legado, lo mismo que los defaults de `config` en
  `manifest.json`. Hoy son dos: `rutaCodebase`, que los dos comandos leen a través del resolvedor
  (`dev-harness.py:284, 400`), y `timeoutIntegraciones`, que lee `estado` (`dev-harness.py:151`).
  Se comprueba de dos formas:
  - `dev-harness.py harness --json` y `dev-harness.py estado --json` dan la misma salida, salvo las
    marcas de tiempo, con el config legado y con ese mismo config completado con las claves que le
    faltan, tomadas de `manifest.json`;
  - con el config legado, `timeout_de` da el `timeoutIntegraciones` de `manifest.json`.

  · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, con el `bin` instalado para `timeout_de`.
- **E-44** — Instalar sin `-Update` sobre una instalación 0.28.0 con `analisis` aplica la misma
  limpieza que E-41: ningún archivo del lockfile anterior queda en disco fuera del nuevo sin estar
  nombrado en la salida. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`.
- **E-45** — `-Update` sobre un proyecto cuyo lockfile lista un id desconocido
  (`["comun", "datos"]`) sale con 0 e instala el producto. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, editando el lock de una instalación nueva.

### `-Uninstall`

- **E-46** — `-Uninstall` sobre una instalación nueva borra exactamente lo que lista el lockfile, más
  `harness.installation.json`, los `.nuevo` y los `__pycache__`. Conserva los backups,
  `harness.config.json`, `.env`, `.env.example` y `harness.presupuesto.json`, saca los bloques de
  `CLAUDE.md` y `.gitignore`, y sale con 0. Es lo mismo que hace 0.28.0. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`.
- **E-47** — `-Uninstall` con el instalador nuevo sobre una instalación 0.28.0 con `-Harness
  analisis,desarrollo` sale con 0 y no deja en `.claude\harness\`, `.claude\skills\` ni
  `.claude\agents\` ningún archivo que ese lockfile listara, `hu-*` incluidos.
  · rojo visto: no consta
  · se prueba: `63-harness-unico-instalador.ps1`.

### `-Doctor`

- **E-48** — `-Doctor` sin proyecto verifica PowerShell, Claude Code contra `requiereClaudeCode` de
  `manifest.json`, Python contra `requierePython`, ExecutionPolicy, Mark-of-the-Web y las dos
  latencias, y nada sobre harnesses disponibles. · rojo visto: no consta
  · se prueba: `63-harness-unico-instalador.ps1`.
- **E-49** — `-Doctor -Project` sobre una instalación nueva dice `harness instalado (v<versión>)`
  sin ids y da la línea de la Context Bar. Sobre una instalación 0.28.0 con `-Harness analisis`
  también da la línea de la barra, y no suma ninguna falla por el contenido del lock.
  · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`.
- **E-50** — `-Doctor -Project` no cambia ni un byte del proyecto. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, con sha256 de todo el árbol antes y después.

### Una sola fuente

- **E-51** — En una copia del repositorio, poner `requiereClaudeCode` de `manifest.json` en
  `99.0.0` hace que `-Doctor` falle por la versión de Claude Code. Cambiar `ramaDesarrollo` y
  `umbralCobertura` en su `config` cambia esos dos valores en el `harness.config.json` de una
  instalación nueva. Ningún otro archivo hace falta tocar para ninguna de las dos cosas.
  · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, sobre la copia.

### Registro de agentes, roster, refutación y controles

- **E-52** — En la fábrica, `registro_agentes.reporte()` da `registryValid: true`, con 10 agentes
  declarados y válidos, 27 skills instaladas y 2 pendientes. · rojo visto: si
  · se prueba: `63_harness_unico.py`.
- **E-53** — En un proyecto instalado, `registro_agentes.reporte()` da el mismo `summary` y el mismo
  `result` que en una instalación 0.28.0 con `-Harness desarrollo`. Los huérfanos son los mismos
  tres (`dev-iniciador-code` `WARNING`, `flush-memoria` y `leer-docs` `ERROR`) y la no declarada es
  la misma (`instalar-desde-github`). Esta spec no lo arregla. · rojo visto: si
  · se prueba: `63-harness-unico-instalador.ps1`, con el `bin` instalado.
- **E-54** — En un proyecto instalado, `roster.existe_check` encuentra los cinco checks `dev-*`, y
  `roster.cargar()` devuelve el roster no vacío. · rojo visto: no consta
  · se prueba: `63-harness-unico-instalador.ps1`, con el `bin` instalado.
- **E-55** — `controles.reporte()` da `registryValid: true` en la fábrica, y en un proyecto instalado
  da el mismo `result` que en una instalación 0.28.0 (FH #4 sigue abierto). · rojo visto: no consta
  · se prueba: `63-harness-unico-instalador.ps1`.

### Documentación y fábrica

- **E-56** — `docs/instalacion.md` dice, en su paso de actualización, que `-Harness` ya no existe
  y qué sale de un proyecto que tenía `analisis` (`hu-escribir`, `hu-redactor`, `hu-refutador` y
  las reglas de "Trabajo funcional"). · rojo visto: si
  · se prueba: `63_harness_unico.py`.
- **E-57** — `.claude/agents/harness-backend-engineer.md` no tiene ningún comando con `-Harness`, y
  ningún archivo de `.claude/`, ni el `CLAUDE.md` de la fábrica, nombra `comun/manifest.json` o
  `harnesses/*/manifest.json`. · rojo visto: si
  · se prueba: `63_harness_unico.py`.
- **E-58** — Cada entrada de `adaptadoEn` en `terceros/terceros.lock.json` que nombra un archivo que
  `git ls-files` no conoce dice que se retiró, en qué versión y con qué cambio. · rojo visto: si
  · se prueba: `63_harness_unico.py`.
- **E-59** — Existe `docs/adr/0012-un-solo-harness.md`, aceptado, y nombra las tres decisiones de
  producto: `desarrollo` es el harness, `analisis` se retira y la composición sale.
  · rojo visto: si
  · se prueba: `63_harness_unico.py`.

### La suite

- **E-60** — `.\tests\Invoke-Tests.ps1` sale con 0. · rojo visto: no consta
  · se prueba: corriéndola entera.
- **E-61** — `tests/casos/06-composicion.ps1` no existe. Fuera de los dos archivos `63-*`, ningún
  archivo de `tests/` pasa el parámetro `-Harness` (la expresión de E-13) ni contiene las formas de
  `analisis` como harness que lista E-12. Las palabras sueltas no cuentan: `analisis_dinamico` de
  `38_integridad_de_repositorio.py`, o la unidad `analisis` de `20_orquestacion.py:384`. Adentro de
  los `63-*`, `-Harness` solo aparece en E-08 y en las instalaciones con el instalador de `e5d7a14`.
  · rojo visto: si
  · se prueba: `63_harness_unico.py`, recorriendo `tests/`.

## Cómo se verifica

Todo por la suite. Los escenarios que instalan van en `63-harness-unico-instalador.ps1`: E-05 a
E-11, E-14 a E-26, E-36 a E-51 y E-53 a E-55. Los demás van en `63_harness_unico.py`. E-24 y E-60 son
la suite entera. Ningún escenario tiene por sujeto una corrida de un modelo, así que no hay
`lectura`.

**Contra qué se compara.** La línea de base es `e5d7a14`. Se saca de git en cada corrida, y no se
versiona ningún inventario copiado: sus sha256 dependerían de los finales de línea de la máquina.

- E-15 a E-20, E-23, E-36 a E-44, E-47, E-49, E-53 y E-55 instalan con el `install.ps1` de
  `e5d7a14`, extraído con `git archive e5d7a14` a un temporal. Para no pagar 16 s por caso, se
  instala una vez por variante (`desarrollo`, `analisis`, `analisis,desarrollo`) y se copia el
  directorio para cada escenario. La excepción es E-39, que corre donde se instaló.
- E-27 y E-35 importan `hooks/lib/bienvenida.py` desde el `comun/` de `e5d7a14` extraído con `git
  archive`, con su `schemas/` al lado. Hay que importarlo de ahí y no de un archivo suelto:
  `_forma_fuentes` (`bienvenida.py:439-443`) busca `source-state.schema.json` relativo a
  `__file__`, y suelto caería en silencio en la forma mínima, más permisiva. El proyecto de prueba
  tiene `.claude\harness\` instalado, para que los dos módulos resuelvan el runtime contra el mismo
  árbol (`bienvenida.raiz_del_harness`). Entre una llamada y otra solo se reescribe el lock.

**Lo que tiene que decir `UPGRADE.md`.** La entrada la escribe `close-a-version` y no la juzga esta
spec, pero no puede faltarle nada de esto:
- que `-Harness` desapareció, con el error que da;
- qué sale de un proyecto con `analisis`;
- que la Context Bar pide reiniciar la sesión;
- que volver a 0.28.0 pide `-Uninstall`, porque el `-Update` viejo muere con el lock nuevo.

**Quién construye qué.** `install.ps1`, `manifest.json` y `tests/` son de
`harness-backend-engineer`. `session-start.py` y `bienvenida.py` son de `harness-hook-engineer`, y
`dev-harness.py` va con ellos, porque las ramas que se sacan leen el mismo documento. Ninguno de los
dos verifica: rule `harness-spec-refuter`.

**El `rojo visto`** sale de romper el código una vez por comportamiento, sobre una copia del
repositorio en un temporal, al menos en estos casos:
- volver a declarar `-Harness`, o sacar `PositionalBinding=$false`;
- seguir escribiendo `harness` en el lock;
- volver a condicionar la barra o el `.env` a un id;
- saltear la limpieza de lo que el lock anterior lista;
- crear un `.nuevo` para un archivo que la versión nueva no instala;
- aplanar `reglas\desarrollo\` a `reglas\`;
- tocar una coma de `dev-refutador.md`;
- invertir el orden de los fragmentos del bloque del `CLAUDE.md`;
- leer los requisitos de `-Doctor` de un archivo que no sea `manifest.json`;
- devolver `_sin_desarrollo` cuando el lock no dice `desarrollo`.

El `rojo visto` salió el 01-10-2026, de dos maneras y nunca sobre el árbol versionado:

- **Contra 0.28.0, antes de construir.** Los dos casos `63-*` corrieron sobre el código de
  `e5d7a14`. El de Python dio 80/171 y el de PowerShell 21/47. Quedaron en rojo E-01 a E-03, E-05 a
  E-09, E-12, E-13, E-27 a E-32, E-34, E-36, E-39, E-56 a E-59, E-61 y E-62.
- **Rompiendo el código ya construido, sobre seis copias del repositorio en un temporal**, cada una
  con su `.git`:
  - A: sin `PositionalBinding=$false`, `.nuevo` para un retirado, los fragmentos del bloque
    invertidos y los requisitos de `-Doctor` fuera de `manifest.json`. Rojo en E-09, E-20, E-37,
    E-42 y E-51.
  - B: sin limpieza de huérfanos, una coma en `dev-refutador.md` y el parámetro viejo de vuelta.
    Rojo en E-05, E-08, E-16, E-40, E-41 a E-44 y E-62.
  - C: `reglas\desarrollo\` aplanado, `harness` en el lock y el `.env` condicionado a un id. Rojo
    en E-14 a E-16, E-19, E-36, E-43, E-45 y E-62.
  - D: `_sin_desarrollo` de vuelta cuando el lock no dice `desarrollo`. Rojo en E-27 y E-28.
  - E: una capacidad menos en `manifest.json`, el schema cambiado, las definiciones pendientes sin
    contar, un renderizador cambiado y una skill menos en el registro. Rojo en E-04, E-29, E-33,
    E-35 y E-52.
  - F: el descubrimiento de `harnesses\` de vuelta, ids en `-Doctor`, un `deny` de más, otro
    mensaje de los hooks, sin revisión de fuentes, sin `.nuevo`, el estado sin borrar al
    desinstalar, `-Doctor` que escribe, una skill menos en el registro instalado y la regla de
    GitLab que no agarra. Rojo en E-10, E-11, E-16, E-17, E-21, E-22, E-25, E-38, E-46, E-49, E-50
    y E-53.

La copia A encontró un error del test, no del código. Sacar `PositionalBinding=$false` no puso a
E-09 en rojo, porque el test pasaba `-Usuario` con nombre, y entonces el posicional no tenía dónde
caer. Se corrigió el test para que haga lo que dice el escenario (`-Project <dir> analisis`, sin
más), y ahí la mutación sí quedó en rojo.

No consta el rojo de E-18, E-23, E-24, E-26, E-47, E-48, E-54, E-55 y E-60. E-54 no se puso en rojo
con `reglas\desarrollo\` aplanado: `roster.cargar()` encuentra `roster.json` igual, por la búsqueda
de varias raíces de `roster._raices_de_reglas`. Es la caída en silencio que nombra `Riesgos
conocidos`, y lo que la detectó fueron E-15 y E-16.

**Lo que ninguna suite ve, y se hace antes de publicar:**
1. Mirar el lockfile del IGE, el único proyecto real conocido. `install.ps1` traía de ejemplo
   `-Project C:\Work\GCBA\IGE -Harness analisis`, y FH #8 dice que le faltan assets de
   `desarrollo`. En el repo no consta qué ids tiene. Si tiene `analisis`, quien lo usa tiene que
   saber antes del `-Update` que pierde `hu-escribir` y sus dos agentes.
2. Una sesión real después del `-Update` en un proyecto descartable. Alguien distinto de quien
   construyó ve la barra pedir reinicio y quedar `ACTIVA` después, y lo anota en
   `verificacion.md` como observación, no como evidencia automática.

## Riesgos conocidos

- **Todo proyecto con `analisis` pierde capacidades en su próximo `-Update`**: `hu-escribir`,
  `hu-redactor`, `hu-refutador` y las reglas de "Trabajo funcional" del `CLAUDE.md`. Es la decisión
  de producto. Lo que este cambio garantiza es que pase a la vista (E-41) y que nada quede huérfano.
- **La suite se vuelve más lenta.** `03-instalador.ps1` usa `analisis` como harness liviano en unas
  diez instalaciones: 6,9 s contra 16,0 s cada una, medido el 01-10-2026. Son alrededor de 90 s más,
  sin contar las instalaciones con el instalador de `e5d7a14`. El número va en `verificacion.md`.
- **Los resolvedores caen en silencio.** `roster.cargar()` devuelve `{}` y `rutas.localizar()`
  devuelve `None` si una ruta no existe. Un error al mover algo no se ve como un error. E-15, E-16 y
  E-54 son la defensa.
- **Los tests de migración necesitan la historia de git.** En un clon superficial `e5d7a14` no
  está, y fallan todos los escenarios que comparan contra esa versión. Tienen que fallar en rojo,
  con el motivo, y nunca saltearse.
- **Volver a 0.28.0 no anda.** Sobre un proyecto ya actualizado, el `-Update` y el `-Doctor
  -Project` del instalador viejo mueren por `StrictMode` al leer el lock sin `harness`, aunque sin
  tocar nada. La bienvenida vieja diría `LOCKFILE_UNREADABLE`. La salida es `-Uninstall`, que sí
  anda, y volver a instalar con `-Harness desarrollo`. Va en UPGRADE.
- **`-Doctor` sobre un proyecto con `analisis` todavía sin actualizar** muestra la línea de la
  Context Bar con *Qué hacer: python .claude\harness\bin\desarrollo\dev-harness.py harness*
  (`install.ps1:1631`), y ese proyecto no tiene la CLI. Es un estado de transición: dura hasta el
  `-Update`.
- **Los finales de línea.** Con `core.autocrlf=true`, los `.py` quedan con CRLF en el árbol de
  trabajo (`git ls-files --eol`: `i/lf w/crlf`), y el instalador copia el árbol de trabajo tal cual.
  Por eso los sha256 de una instalación dependen de la máquina, y las comparaciones de contenido de
  esta spec normalizan CRLF a LF antes de comparar.
- **Los nombres históricos siguen en contratos.** `bin\desarrollo\` en la ruta de la CLI,
  `HARNESS:COMUN`, `harnessId: "desarrollo"` y el prefijo `dev-`. Sacarlos más adelante es un cambio
  que rompe por su cuenta.
- **El registro de agentes sigue inválido en los proyectos instalados**, por lo que instala `comun`.
  Quien lea `registryValid: true` en la fábrica puede creer que vale también afuera. E-53 lo fija
  para que no empeore, y el pendiente lo nombra.
- **`docs/codebase/` de la fábrica sigue describiendo `analisis`** hasta que se regenere.
- **Un default del manifiesto y el del código pueden divergir sin que se vea.** Si cambia un valor
  de `config` en `manifest.json`, lo reciben las instalaciones nuevas, y las que no tienen la clave
  siguen con el valor del código. E-43 lo ve para `rutaCodebase` y `timeoutIntegraciones`; para
  `fichaTipoDeIssue` y `topeTextoDocumento` no hay escenario.
- **El conteo de la suite cambia.** El `CLAUDE.md` de la fábrica dice 24875 y deja de ser cierto. Se
  actualiza al cerrar, con el número que dé la corrida.
