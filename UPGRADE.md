# Upgrade

Qué hacer al pasar de una versión del harness a la siguiente. Cada entrada dice si el
`-Update` alcanza o si hay algo manual.

El procedimiento normal es siempre el mismo:

```powershell
.\install.ps1 -Doctor
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Update
```

**No hay `git pull` en el medio porque todavía no hay remoto:** el repo del harness vive en una
sola máquina. Ahí los cambios ya están, y `-Update` los lleva a cada proyecto. En una segunda
máquina, clonada desde una ruta, el paso previo es `git -C C:\Work\gcba-harness pull` con el
origen accesible.

`-Update` reporta al final los archivos que **no** pisó porque los habías editado a mano.
Quedan como `<archivo>.nuevo` al lado del tuyo, para que hagas el merge vos.

---

## 0.12.0 → 0.13.0

**Rompe.** Agrega un requisito y cambia el contrato de los checks. `-Update` alcanza para
recibir el harness nuevo, pero si escribiste un check propio hay un paso manual.

**Python ≥ 3.9 pasa a ser requisito de instalación**, no solo de ejecución: `install.ps1`
resuelve el intérprete y lo usa para leer las zonas del `CLAUDE.md`. `-Doctor` lo verifica y
falla con instrucciones si no está o es anterior a 3.9. Correr `-Doctor` antes que nada:

```powershell
.\install.ps1 -Doctor
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Update
```

**Si escribiste un check propio en `.ps1`, hay que portarlo.** Los cuatro hooks, los cinco
checks del harness y sus bibliotecas pasaron de PowerShell a Python. El contrato de un check
cambió de forma:

```powershell
param($Evento, $Proyecto, $Config)   ->   devuelve cero o mas strings
```
```python
def verificar(evento, proyecto, config) -> list[str]
```

Un `.ps1` en el directorio de checks deja de descubrirse: `lib/reglas.py` solo carga `.py`. El
detalle completo, con las trampas de Python que hay que conocer para escribirlo, está en
[docs/contrato-hooks.md](docs/contrato-hooks.md).

**Qué no cambia:** el catálogo de secretos, los umbrales, los mensajes y el veredicto de cada
regla — el port se hizo a paridad de comportamiento a propósito, defectos incluidos. Si un
check tuyo depende de algo del harness que no sea el contrato de arriba (una función de
`Zonas.psm1`, por ejemplo), mirá `lib/zonas.py`, que es su reemplazo directo.

**Lo que trae de arrastre:** `run-hook.sh` — el shim que faltaba. Una sesión de Claude Code
sobre WSL, macOS o Linux, contra un proyecto instalado desde Windows, ya arranca los hooks.
Necesita `python3` en el `PATH` de esa sesión.

---

## 0.8.0 → 0.9.0

`-Update` alcanza. Pero después de correrlo puede aparecer un aviso nuevo, y conviene saber
qué significa antes de verlo.

**Si tu `CLAUDE.md` es anterior al harness**, es probable que tenga zonas escritas con otro
nombre. El aviso se ve así:

```
AVISO CLAUDE.md: <!-- CACHÉ --> parece ser tu ZONA CACHE con otro nombre.
->    no se agregó ZONA CACHE para no dejarte dos. Renombrá el marcador
      —el de apertura y el de cierre— y corré -Update.
```

Se arregla en diez segundos: renombrás los dos marcadores y volvés a correr `-Update`. Hasta
que lo hagas, esa zona **no se mide** — pero tu contenido está intacto y nadie lo tocó.

**El otro aviso nuevo mide lo que quedó fuera de toda zona.** Si tenés un `CLAUDE.md` largo
escrito antes del harness, va a decirte cuántas líneas están afuera. No es urgente y no bloquea
nada: fuera de una zona el contenido sigue funcionando, lo que no hace es medirse ni purgarse.

**Clave nueva de configuración:** `techoFueraDeZonas` (12 por defecto). Como
`harness.config.json` no se toca nunca —ni en `-Update`— la clave no va a aparecer en un
proyecto ya instalado. No hace falta hacer nada: el valor por defecto viaja en código. Si querés
otro techo, agregala a mano a tu `harness.config.json`.

---

## Sin versión previa → 0.1.0

Nada que migrar. El repo todavía no instala nada.

---

## 0.6.0 → 0.7.0

`-Update` alcanza. No hay paso manual.

Lo que cambia de comportamiento: **`-Harness` pasa a ser aditivo.** Antes, instalar dejaba el
proyecto con exactamente los harness nombrados en el comando; ahora suma los que ya estaban
y lo anuncia. El cambio arregla el caso incremental —un repo con `analisis` que recibe su
primer código— que antes borraba el primer harness en silencio.

Si algún proyecto quedó en ese estado roto, el síntoma es que el bloque de `CLAUDE.md` no
tiene las reglas del harness que instalaste primero, y `.claude\skills\` o `.claude\agents\`
tienen archivos que el `harness.lock.json` no lista. Se arregla nombrando los dos:

```powershell
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Harness analisis,desarrollo
```

Los archivos huérfanos que hayan quedado de antes **no los borra el instalador**: no están en
ningún inventario, así que no puede probar que son suyos. Se van con un `-Uninstall` seguido
de una instalación limpia, o a mano mirando qué sobra.

---

## Migraciones pendientes, para cuando corresponda

Cosas que quedaron **fuera de alcance** del harness pero que conviene hacer. No las ejecuta
el instalador: son decisiones de cada uno.

### Los subagentes globales sin `tools:` declaradas

En `~\.claude\agents\` hay 19 subagentes y solo 3 declaran `tools:`. Los otros 16 heredan
acceso total de escritura y ejecución sobre cualquier repo. `install.ps1 -Doctor` los lista.

La migración es agente por agente: agregarles `tools:` con lo mínimo que necesitan, y
`model:` cuando la tarea no justifica el modelo más caro. Los tres que ya están bien sirven
de molde.

### `~\.claude\` no tiene control de versiones

Los 19 agentes, las skills propias y el `CLAUDE.md` de usuario viven en un solo disco, sin
git y sin respaldo. Un `git init` ahí adentro es gratis y no rompe nada.

Es independiente de este harness, pero es la red de contención que hoy no existe.

### Los repos de proyecto sin `git`

Fuera de alcance por decisión. El harness lo detecta y lo avisa al abrir sesión, pero no
corre `git init` por su cuenta: crear un repositorio donde hay secretos y binarios pesados es
una decisión que hay que tomar mirando, no automatizar.
