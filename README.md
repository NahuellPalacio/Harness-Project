# Project-Harness

Andamiaje de trabajo con IA para los proyectos de DGISIS / GCBA.

Un harness es lo que hace que el agente produzca resultados correctos **sin depender de que
se acuerde de las reglas**. Tiene tres capas: lo que el agente tiene que **saber**, lo que lo
**obliga** a hacerlo, y lo que **comprueba** que lo hizo. Un `CLAUDE.md` bien escrito es solo
la primera.

## Un solo harness

El harness es **un solo producto**, para el trabajo técnico: código, APIs y deploy. Trae
ES0901, ES0902, ES0903, Obelisco y accesibilidad, las versiones homologadas, las integraciones
con Jira y GitLab, el contexto de una tarea, la planificación, la refutación del plan contra la
normativa, el reporte de seguridad, la Context Bar y la contabilidad de ejecución. Se instala
entero: no hay nada que elegir.

En el repo vive en dos árboles por historia: `comun/` es la base —los hooks, la regla de
secretos, las zonas del `CLAUDE.md`, el estado de la instalación— y `harnesses/desarrollo/` es
el producto. La decisión está en [ADR-0012](docs/adr/0012-un-solo-harness.md).

📌 **Hasta 0.28.0 había un segundo harness, `analisis`, y se podían componer.** Ya no: un proyecto
que lo tenía pasa a tener el producto entero en su próximo `-Update`. Qué sale y qué hacer está en
[docs/instalacion.md](docs/instalacion.md#6-actualizar-y-desinstalar).

## Requisitos

| | |
|---|---|
| Windows | 10 u 11, para instalar. Los hooks corren en Python: con el shim `.sh`, la sesión funciona también desde WSL, macOS o Linux |
| Claude Code | ≥ 2.1.0 |
| PowerShell | ≥ 5.1 (el que viene con Windows; no hace falta PowerShell 7) |
| Python | ≥ 3.9 (el de la máquina; no se empaqueta ningún intérprete) |
| Git | cualquiera |

Esa tabla es **todo lo que hay que instalar**. El harness no depende de ninguna herramienta
externa: es la regla de [ADR-0008](docs/adr/0008-lo-externo-nunca-es-requisito.md) — *puede
aprovechar una, nunca depender de ella*. Sin la herramienta, el trabajo sigue por el camino
que ya existía.

## Lo que no hace falta instalar

Dos preguntas que aparecen siempre, contestadas acá para no volver a discutirlas:

| | |
|---|---|
| **Obsidian** | Opcional y personal. `docs/conocimiento/` del proyecto es markdown plano y por lo tanto **es un vault**: quien quiera enlaces `[[wiki]]` y vista de grafo abre esa carpeta con Obsidian y los tiene. Sin plugin REST, sin MCP, sin ruta configurada — el harness no se entera. Ver [ADR-0003](docs/adr/0003-obsidian-fuera-del-harness.md) |
| **Un índice de código externo** — `codebase-memory-mcp`, `graphify` | Ninguno se instala, y no es olvido: los dos se evaluaron. `graphify` registra un hook en el `.claude/settings.json` del proyecto, y cada `-Update` regenera ese archivo entero: el hook se borraría solo. `codebase-memory-mcp` es un binario sin firma Authenticode que Defender marca como falso positivo. El índice del proyecto lo escribe el propio harness, con el primer recorrido del código (ver [Qué recuerda](#qué-recuerda)). El detalle de cada evaluación está en `Pendientes/Ideas-Harness/PENDIENTES-I.md` |

## Instalación

El paso a paso completo, por PowerShell y por bash, con los problemas frecuentes y su salida,
está en **[docs/instalacion.md](docs/instalacion.md)**. La versión corta:

```powershell
git clone https://github.com/NahuellPalacio/Harness-Project.git C:\Work\Project-Harness
cd C:\Work\Project-Harness

# 1. Revisar que la máquina esté en condiciones. No escribe nada.
.\install.ps1 -Doctor

# 2. Ver exactamente qué se va a escribir, antes de escribirlo.
#    No pide nada: como no escribe, no puede exigir.
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -WhatIf

# 3. Instalar. El harness te trata por tu nombre; si no lo pasás, te lo pregunta.
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Usuario "Tu Nombre"
```

Lo mismo desde bash — Git Bash sobre Windows — es el mismo instalador con otro prefijo:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./install.ps1 \
  -Project 'C:/Work/GCBA/MiProyecto' -Usuario 'Tu Nombre'
```

Después:

```powershell
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Update      # traer cambios del harness
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Uninstall   # sacar lo que instaló; lo tuyo queda
```

`-Update` **nunca pisa un archivo que hayas editado a mano**: escribe la versión nueva al
lado, con extensión `.nuevo`, y te avisa al final. `harness.config.json` no se toca jamás.

Después de instalar queda un paso más — conectar Jira y GitLab: completar el
`.env` local, que el instalador crea con la plantilla de `.env.example` y que Claude no puede leer.
`setup` no pregunta nada: dice qué variable falta, por nombre, y valida.

```powershell
python .claude\harness\bin\desarrollo\dev-harness.py setup
python .claude\harness\bin\desarrollo\dev-harness.py estado   # qué quedó disponible
```

Con eso conectado, el harness puede resolver el contexto de una tarea: de una clave de Jira arma un
documento con el ticket, el conocimiento del proyecto, su documentación y su estado técnico.

```powershell
python .claude\harness\bin\desarrollo\dev-harness.py contexto GCBA-1234
```

Y con el contexto resuelto, planificarla: qué hay que hacer, quién debería hacerlo, en qué orden y
con cuánto modelo.

```powershell
python .claude\harness\bin\desarrollo\dev-harness.py plan GCBA-1234 --plantilla
python .claude\harness\bin\desarrollo\dev-harness.py plan GCBA-1234 --propuesta propuesta.json
```

La plantilla la completa el agente `dev-orchestrator`, y `--propuesta` la valida y la guarda en
`.claude/planes/` como `orchestration-plan/2.0`. **El harness planifica y no ejecuta:** nada toma
una unidad de trabajo y la lleva a cabo. Execution está reservado en el
[modelo de dominio](docs/dominio/modelo-canonico.md), sin implementar.

Y con la tarea corriendo, contar lo que costó: tokens, tiempo y plata, con lo que no se pudo medir
dicho en vez de puesto en cero.

```powershell
python .claude\harness\bin\desarrollo\dev-harness.py contabilidad GCBA-1234 --ingerir <fuente> --reporte
```

Los demás comandos de la misma CLI:

| Comando | Para qué |
|---|---|
| `harness` | El estado de la instalación: cada componente y la Context Bar |
| `reconfigurar jira` | Rehacer una integración, `jira` o `gitlab` |
| `fuentes` | Las fuentes normativas del proyecto, como ES0902 y ES0903: resolverlas, aceptarlas y refrescarlas |
| `refute GCBA-1234 --compile` | Partir el plan en unidades de refutación para `dev-refutador` |
| `seguridad GCBA-1234 --reporte` | El libro de seguridad de la tarea, y su reporte en md y html |
| `presupuesto --context-defaults` | Los umbrales de contexto de la Context Bar, si faltan |

El detalle está en [docs/integraciones.md](docs/integraciones.md),
[docs/contexto-de-tarea.md](docs/contexto-de-tarea.md),
[docs/orquestacion.md](docs/orquestacion.md),
[docs/contabilidad.md](docs/contabilidad.md) y
[docs/reporte-de-seguridad.md](docs/reporte-de-seguridad.md).

> ⚠️ **Cloná, no descargues el ZIP.** Windows le pone *Mark-of-the-Web* a todo archivo bajado
> de internet, y la política de ejecución por defecto (`RemoteSigned`) bloquea los `.ps1`
> marcados. El síntoma es un error de permisos que no menciona en ningún momento la causa
> real, y se pierde media tarde.

## Qué instala en tu proyecto

```
MiProyecto/
├── CLAUDE.md              # se le inyecta un bloque marcado y sus zonas; el resto no se toca
├── .gitignore             # se le agrega un bloque: .claude/ y los secretos
├── .env.example           # la plantilla de las integraciones, en un bloque marcado
├── .env                   # tus credenciales: se crea una vez y no se toca nunca más
└── .claude/
    ├── settings.json              # permisos + registro de hooks
    ├── harness/                   # los hooks, los checks, las reglas, la CLI y los extractos
    ├── skills/  agents/           # las skills y los agentes del harness
    ├── harness.lock.json          # qué versión, qué archivos, SHA256
    ├── harness.installation.json  # el estado de la instalación y de la Context Bar
    ├── harness.config.json        # tus ajustes: nunca se pisan
    ├── harness.presupuesto.json   # los umbrales de la Context Bar: se crea si no existe
    ├── harness.integraciones.json # Jira y GitLab sin ningún secreto, generado desde el .env
    ├── harness.capacidades.json   # qué integraciones andan, de la última corrida
    ├── harness.fuentes.json       # el estado de las fuentes normativas
    ├── contextos/  planes/  refutaciones/   # el trabajo de cada tarea
    ├── runtime/                   # la contabilidad, la seguridad y la Context Bar
    └── .harness-backup/           # copia de todo lo que se pisó
```

La regla que ordena todo: **`.claude/` va gitignoreado y `CLAUDE.md` se versiona.** Lo que trae el
harness —`settings.json`, `harness/`, las skills, los agentes y el lockfile— se regenera
reinstalando. Lo que es tuyo o de tu trabajo —la configuración, los contextos, los planes, las
refutaciones y los libros de `runtime/`— no lo toca `-Update`, y `-Uninstall` lo deja: borra solo
lo que lista el lockfile, el estado de la instalación y los bloques que agregó.

## Cómo se comporta

**Avisa. Casi nunca bloquea.**

Un harness que bloquea de más el primer día está desactivado la primera semana. Cuando algo
no cumple una norma, el harness lo dice en el contexto y el agente corrige en el turno
siguiente. Nadie queda trabado.

**La única excepción son los secretos**, que sí bloquean. Dos mecanismos, complementarios:

- `permissions.deny` en `settings.json` impide **leer** rutas sensibles (`secrets/`, `.env`,
  claves privadas, keystores).
- Un hook impide **escribir** un secreto literal en un archivo o un comando.

> ⚠️ **Límite honesto:** `permissions.deny` cubre lo que Claude Code puede resolver como una
> ruta. Una lectura indirecta —construir el path en una variable y leerlo desde ahí— puede
> escapar. Es *best-effort*, no una garantía. No lo uses como único control sobre material
> que no puede filtrarse.

## Qué recuerda

Al abrir una sesión te dice en qué quedaron: qué versión del harness rige, el estado de git, el
último trabajo, lo que alguien dejó anotado en la caché y cuántas definiciones quedaron abiertas.

> **Se lee lo que alguien decidió dejar anotado. No se captura nada.**

Es la diferencia con una memoria que graba todo por las dudas: un capturador automático
persiste también la cadena de conexión que el agente leyó hace un rato. Esta memoria es más
pobre a propósito — no sabe qué se habló, solo lo que quedó escrito — y por eso no puede
filtrar un secreto.

La primera sesión después de instalar muestra además una bienvenida con el estado de la
instalación —lista, parcial o bloqueada— y el de la Context Bar. Y mientras el proyecto no tenga
índice, sugiere el **primer recorrido del código**: el agente `dev-iniciador-code` lo camina entero
y escribe el índice en `docs/codebase/`, versionado, para que el agente no arranque cada sesión a
ciegas.

El detalle completo, con las zonas del `CLAUDE.md` y sus techos, está en
[docs/memoria.md](docs/memoria.md).

## Estructura del repo

| Carpeta | Qué hay |
|---|---|
| `manifest.json` | El único manifiesto: los requisitos de la máquina y la configuración inicial de cada proyecto |
| `comun/` | La base del harness: hooks, secretos, zonas del `CLAUDE.md`, schemas y estado de la instalación |
| `harnesses/desarrollo/` | El producto: la CLI, los checks, los controles normativos, las reglas, las skills y los agentes |
| `normativa/` | Los estándares del GCBA destilados a markdown, en `extractos/`. Los extractos se instalan en el proyecto, dentro de `.claude/harness/`, porque la frescura de cada fuente mira la versión de su encabezado. Los PDF originales son documentación interna del GCBA y **no se publican acá**: van en `normativa/fuentes/`, que está gitignoreada — cada quien pone los suyos |
| `docs/adr/` | Por qué cada decisión es como es |
| `docs/dominio/` | El modelo de dominio canónico: qué conceptos tiene el harness, qué significa cada uno y dónde termina. Está en [docs/dominio/modelo-canonico.md](docs/dominio/modelo-canonico.md) |
| `docs/cambios/` | Cada cambio con su spec, sus escenarios y el veredicto de quien lo verificó. El método está en [ADR-0006](docs/adr/0006-sdd-como-metodo-de-los-proyectos.md) |
| `docs/versiones/` | La nota de cada versión: qué se hizo, qué se decidió y qué quedó abierto |
| `tests/` | Payloads reales de cada evento de hook, y los casos que los verifican |
| `Pendientes/` | Lo que falta: los defectos en `Fix-Harness/` y las ideas en `Ideas-Harness/` |
| `terceros/` | Material de repositorios públicos. Nunca se instala directo: ver [terceros/LEEME.md](terceros/LEEME.md) |
| `.claude/` | Los agentes y las skills de esta fábrica, no los del producto |

## Estado

En construcción. La versión vigente está en [VERSION](VERSION). Ver [CHANGELOG.md](CHANGELOG.md)
para lo que ya funciona y [UPGRADE.md](UPGRADE.md) para migrar entre versiones.
