# gcba-harness

Andamiaje de trabajo con IA para los proyectos de DGISIS / GCBA.

Un harness es lo que hace que el agente produzca resultados correctos **sin depender de que
se acuerde de las reglas**. Tiene tres capas: lo que el agente tiene que **saber**, lo que lo
**obliga** a hacerlo, y lo que **comprueba** que lo hizo. Un `CLAUDE.md` bien escrito es solo
la primera.

## Los dos harness

El corte es por **tipo de trabajo**, no por proyecto. Sirve para que nadie cargue reglas que
no le tocan: un analista funcional no necesita las reglas de diseño de APIs, y quien escribe
código no necesita las reglas de redacción de historias de usuario.

| Harness | Para qué | Qué trae |
|---|---|---|
| `analisis` | Relevar, escribir historias de usuario, leer maquetas y normativa | La ley de no inventar, lectura de maquetas, formato de HU con Check IA |
| `desarrollo` | Código, APIs, deploy | ES0901, ES0903, Obelisco y accesibilidad, versiones homologadas |

Los dos se apoyan sobre `comun/`, que se instala siempre: la regla de secretos, los hooks, el
formato de memoria del proyecto y el instalador.

Un proyecto puede tener **los dos a la vez**, nombrándolos juntos o agregando uno después:

```powershell
.\install.ps1 -Project ... -Harness analisis,desarrollo   # los dos de una
.\install.ps1 -Project ... -Harness desarrollo            # sumar el segundo más tarde
```

**Instalar es aditivo**: lo que el proyecto ya tenía se conserva, y el instalador lo anuncia.
Es lo que va a pasar cuando un repo de relevamiento reciba su primer código. Para quedarse con
un conjunto exacto, el camino es `-Uninstall` y volver a instalar.

## Requisitos

| | |
|---|---|
| Windows | 10 u 11, para instalar. Los hooks corren en Python: con el shim `.sh`, la sesión funciona también desde WSL, macOS o Linux |
| Claude Code | ≥ 2.1.0 |
| PowerShell | ≥ 5.1 (el que viene con Windows; no hace falta PowerShell 7) |
| Python | ≥ 3.9 (el de la máquina; no se empaqueta ningún intérprete) |
| Git | cualquiera |

## Instalación

El paso a paso completo, por PowerShell y por bash, con los problemas frecuentes y su salida,
está en **[docs/instalacion.md](docs/instalacion.md)**. La versión corta:

```powershell
git clone https://github.com/NahuellPalacio/Harness-Project.git C:\Work\gcba-harness
cd C:\Work\gcba-harness

# 1. Revisar que la máquina esté en condiciones. No escribe nada.
.\install.ps1 -Doctor

# 2. Ver exactamente qué se va a escribir, antes de escribirlo.
#    No pide nada: como no escribe, no puede exigir.
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Harness analisis -WhatIf

# 3. Instalar. El harness te trata por tu nombre; si no lo pasás, te lo pregunta.
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Harness analisis -Usuario "Tu Nombre"
```

Lo mismo desde bash — Git Bash sobre Windows — es el mismo instalador con otro prefijo:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./install.ps1 \
  -Project 'C:/Work/GCBA/MiProyecto' -Harness analisis -Usuario 'Tu Nombre'
```

Después:

```powershell
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Update      # traer cambios del harness
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Uninstall   # sacarlo, sin dejar rastro
```

`-Update` **nunca pisa un archivo que hayas editado a mano**: escribe la versión nueva al
lado, con extensión `.nuevo`, y te avisa al final. `harness.config.json` no se toca jamás.

> ⚠️ **Cloná, no descargues el ZIP.** Windows le pone *Mark-of-the-Web* a todo archivo bajado
> de internet, y la política de ejecución por defecto (`RemoteSigned`) bloquea los `.ps1`
> marcados. El síntoma es un error de permisos que no menciona en ningún momento la causa
> real, y se pierde media tarde.

## Qué instala en tu proyecto

```
MiProyecto/
├── CLAUDE.md              # se le inyecta un bloque marcado; el resto no se toca
├── .gitignore             # se le agrega un bloque de secretos
└── .claude/
    ├── settings.json      # permisos + registro de hooks     ─┐
    ├── harness/           # los hooks, skills, agentes         │ todo esto es
    ├── harness.lock.json  # qué versión, qué archivos, SHA256  │ regenerable
    ├── harness.config.json# tus ajustes — nunca se pisan       │ y va gitignoreado
    └── .harness-backup/   # copia de todo lo que se pisó      ─┘
```

La regla que ordena todo: **`.claude/` es 100% regenerable y va gitignoreado; `CLAUDE.md` no
lo es y se versiona.** Si algo se rompe, borrás `.claude/` y reinstalás.

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

Al abrir una sesión te dice en qué quedaron: qué harness rige, el estado de git, el último
trabajo, lo que alguien dejó anotado en la caché y cuántas definiciones quedaron abiertas.

> **Se lee lo que alguien decidió dejar anotado. No se captura nada.**

Es la diferencia con una memoria que graba todo por las dudas: un capturador automático
persiste también la cadena de conexión que el agente leyó hace un rato. Esta memoria es más
pobre a propósito — no sabe qué se habló, solo lo que quedó escrito — y por eso no puede
filtrar un secreto.

El detalle completo, con las zonas del `CLAUDE.md` y sus techos, está en
[docs/memoria.md](docs/memoria.md).

## Estructura del repo

| Carpeta | Qué hay |
|---|---|
| `comun/` | El esqueleto. Se instala siempre, con cualquier harness |
| `harnesses/<id>/` | Lo específico de cada tipo de trabajo |
| `normativa/` | Los estándares del GCBA destilados a markdown, en `extractos/`. **Insumo, nunca se copia a un proyecto**. Los PDF originales son documentación interna del GCBA y **no se publican acá**: van en `normativa/fuentes/`, que está gitignoreada — cada quien pone los suyos |
| `docs/adr/` | Por qué cada decisión es como es |
| `tests/` | Payloads reales de cada evento de hook, y los casos que los verifican |

## Agregar un tercer harness

Crear `harnesses/<id>/manifest.json`. Nada más: el instalador descubre los harness recorriendo
`harnesses/`, no hay ningún id que registrar. Está documentado en
[docs/agregar-un-harness.md](docs/agregar-un-harness.md).

Cada harness declara un **prefijo de namespace** obligatorio. Eso hace estructuralmente
imposible que dos harness aporten dos cosas con el mismo nombre, y por lo tanto componer
siempre es seguro.

## Estado

En construcción. Ver [CHANGELOG.md](CHANGELOG.md) para lo que ya funciona y
[UPGRADE.md](UPGRADE.md) para migrar entre versiones.
