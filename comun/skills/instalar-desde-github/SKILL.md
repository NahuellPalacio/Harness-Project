---
name: instalar-desde-github
description: Use when installing, evaluating or removing a tool, plugin, CLI or MCP server that lives in a GitHub repository — including "instalá esto", a bare GitHub URL, "probemos este repo", "conviene adoptar esto", or choosing between npx / npm -g / a marketplace command. Applies before running any installer that touches the machine, and before copying third-party material into the repo.
---

# Instalar desde GitHub

## La idea

**Los datos duros salen de la API. El README solo se lee filtrado. El repo no se clona.**

Un repo cualquiera cuesta decenas de miles de tokens si se clona, y unos miles si se lee el
README entero. Los datos que deciden si se instala —si está vivo, si la licencia sirve, qué
comando es el bueno— son quince líneas. Traelas y nada más.

## El procedimiento

### 1. Datos duros, una llamada

```powershell
$r = Invoke-RestMethod "https://api.github.com/repos/OWNER/REPO" -Headers @{ "User-Agent" = "ps" }
$r | Select-Object stargazers_count, forks_count, @{n='lic';e={$_.license.spdx_id}}, pushed_at, archived, open_issues_count
```

Si `gh` está instalado, `gh api repos/OWNER/REPO --jq '...'` hace lo mismo y respeta la
autenticación. Comprobalo antes de asumirlo — no está en todas las máquinas del equipo:

```powershell
if (Get-Command gh -ErrorAction SilentlyContinue) { ... } else { ... Invoke-RestMethod ... }
```

🔴 **`archived: true` frena todo.** Un repo archivado no recibe parches de seguridad.

### 2. README crudo y filtrado, nunca la página

```powershell
$md = (Invoke-WebRequest "https://raw.githubusercontent.com/OWNER/REPO/main/README.md" -UseBasicParsing).Content
($md -split "`n") | Select-String -Pattern "npx |npm i|install|uninstall|require|prerequis"
```

Si `main` no existe, probá `master`. La página HTML de GitHub trae navegación, íconos y
comentarios: es varias veces el README y no agrega nada.

### 3. Las cinco preguntas

No se ejecuta nada hasta poder responderlas. Si el README no alcanza, buscá el archivo puntual
(`INSTALL.md`, la docs oficial) — **nunca clonando**.

| # | Pregunta | Por qué |
|---|---|---|
| 1 | ¿Cuál es el comando **oficial**? | Suele haber varios y **no son equivalentes** |
| 2 | ¿Qué prerrequisitos exige? | Versión de runtime, PATH, permisos |
| 3 | ¿Qué escribe en disco y **dónde**? | Es lo que hay que mirar para revertir |
| 4 | ¿Instala **algo más** por su cuenta? | Runtimes, gestores de paquetes, servicios |
| 5 | ¿Cómo se **desinstala**? | Si no está documentado, es un dato en sí mismo |

En el GCBA la pregunta 2 tiene una consecuencia extra: **un runtime nuevo tiene que estar en la
tabla de versiones homologadas de ES0901.** Que la herramienta funcione no alcanza si el runtime
que exige no está aprobado.

### 4. Colisiones

Antes de ejecutar, dos chequeos rápidos:

- **Con lo instalado.** ¿Pisa un plugin, un hook o una config que ya existe? El caso peor es dos
  herramientas que se creen dueñas del mismo archivo — típicamente `.claude/settings.json`.
- **Con lo ya decidido.** Si hay un ADR o una regla del `CLAUDE.md` sobre el tema, decilo. Una
  herramienta puede ser buena y aun así contradecir una decisión tomada.

### 5. Parar y mostrar

**Instalar toca la máquina del usuario y es la parte difícil de deshacer.** Presentá las cinco
respuestas más las colisiones, en un bloque corto, y esperá. No es una pregunta de cortesía: el
usuario es el único que sabe si el costo permanente le sirve.

### 6. Ejecutar y verificar

Después de instalar, comprobá que quedó donde el README dijo que iba a quedar. Si aparecieron
archivos o servicios que no estaban declarados, reportalo.

### 7. Si en vez de instalar se **toma** material

A veces la conclusión no es "instalar" sino "de acá nos sirven dos ideas". Eso no es gratis: pasa
a ser código de terceros dentro de un repo del GCBA, y tiene su propio procedimiento.

- **Se lee entero lo que se toma.** No se copia un archivo que no se leyó completo.
- **El commit va exacto**, los 40 caracteres. Nunca una rama: las ramas se mueven.
- **La licencia se registra**, y se conserva el archivo `LICENSE` del origen.
- **Se anota también lo que se dejó y por qué.** Es lo que evita que dentro de seis meses alguien
  vuelva a evaluar lo mismo desde cero.
- **Lo de terceros vive separado de lo propio**, nunca mezclado en la misma carpeta.

## 🔴 Cuatro trampas que ya aparecieron

**El camino obvio no es el oficial.** `claude-mem` documenta que `npm install -g claude-mem`
instala *solo la librería*: no registra los hooks ni levanta el servicio. Instala, no falla, y
no funciona. **Usá el comando que el README señala como oficial, aunque conozcas otro que
"hace lo mismo".**

**Puede haber una vía nativa mejor.** Si la herramienta se ofrece como plugin del entorno
(`/plugin install ...`), esa vía suele ser más limpia y más fácil de sacar que el instalador
genérico. Mirala antes de elegir.

**Un instalador puede instalar otras cosas.** `claude-mem` baja Bun y uv si faltan. Eso son
runtimes nuevos en la máquina que nadie pidió: entra en la pregunta 4 y se avisa **antes**.

**En Windows puede directamente no haber binario.** `gentle-ai` retuvo su distribución para
Windows por falta de firma Authenticode: el README ofrece la instalación, y en esta plataforma
no existe. Verificá que el artefacto exista para **tu** sistema operativo, no que el proyecto lo
soporte en general.

## 🔴 Que la función exista no significa que esté activa

El README de `claude-mem` anuncia *"Cloud Sync — back up your memories to cmem.ai, the worker
syncs on write"*. Leído solo, parece que la herramienta sincroniza a un servicio externo. La
documentación del feature dice lo contrario: se activa **únicamente** si tres valores están
completos, los tres vienen vacíos, y no existe flag de encendido.

**Un README enumera capacidades; no dice cuáles vienen prendidas.** Antes de reportar una
función como riesgo, abrí su página y buscá el default. Si no lo encontrás, decí *"no pude
determinar si viene activo"* — nunca lo des por activo.

Vale al revés también: una función tranquilizadora anunciada en el README tampoco está activa
por el solo hecho de estar listada.

## Errores comunes

| Error | Qué hacer |
|---|---|
| `git clone` para ver qué hace | API + README crudo. El clon es el último recurso, no el primero |
| WebFetch de la página de GitHub | `raw.githubusercontent.com`, y filtrado |
| Creerle al resumen sobre un número | Estrellas, licencia y fechas salen de la API, que no interpreta |
| Ejecutar y después contar | Las cinco respuestas van **antes** |
| No registrar cómo se saca | Anotá el comando de desinstalación junto al de instalación |
| Copiar material sin dejar rastro | Origen, commit exacto y licencia, o no entra |

## Antes de dar por terminada la instalación

- [ ] Los datos duros salieron de la API, no de un resumen
- [ ] Las cinco preguntas están respondidas
- [ ] Las colisiones —técnicas y de decisiones ya tomadas— están dichas
- [ ] El usuario aprobó **después** de ver eso
- [ ] Se verificó contra lo que el README prometía
- [ ] El comando de desinstalación quedó anotado
- [ ] Si se tomó material: origen, commit exacto, licencia y lo descartado quedaron registrados
