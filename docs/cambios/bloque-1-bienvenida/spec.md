# Bloque 1 — la bienvenida y el estado del harness en cada sesión

**Estado:** verificado y cerrado · **Fecha:** 24-09-2026 · **Bloque:** 1

## Qué problema resuelve

Hoy una instalación exitosa es silenciosa. `install.ps1` termina con "los cuatro hooks responden
correctamente" y la siguiente sesión de Claude Code abre con el bloque de `session-start.py`:
- el usuario;
- la línea `harness: <ids> v<versión>`;
- el estado de git;
- la cache y las definiciones pendientes.

Ese bloque va al contexto del modelo (`additionalContext`), no a la persona. Nadie le dice a quien
instaló:

```
el harness quedo instalado?
que proyecto detecto?
esta listo, a medias o bloqueado?
que integraciones estan disponibles?
la normativa esta vigente?
que comando corro ahora?
```

Además, `dev-harness.py setup` imprime `HARNESS READY` aunque Jira y GitLab estén caídas: la
palabra no depende de ningún estado.

## Qué queda afuera

- **OpenShift.** El Bloque 1 no tiene adaptador de OpenShift. Mostrarlo como "sin configurar"
  sugeriría que hay algo que configurar. Solo se listan las integraciones que el harness implementa:
  Jira Cloud y GitLab. OpenShift entra cuando exista su adaptador.
- **El aviso de conocimiento con `aplicar` / `posponer`.** Lo postergó
  `conocimiento-fuentes-y-frescura`, y en `session-start.py` no existe ningún aviso de conocimiento.
  "Preservar la compatibilidad" quiere decir que todo lo que el hook ya escribe al contexto sigue
  saliendo igual, y que la bienvenida lee el mismo `harness.fuentes.json` que va a leer ese aviso
  cuando se construya. No se construye acá.
- **Un resolvedor nuevo de integraciones o de frescura.** La bienvenida lee lo que ya persistieron
  `setup` (`harness.capacidades.json`) y `fuentes` (`harness.fuentes.json`). No consulta Jira, no
  consulta GitLab y no recalcula la frescura.
- **Un bloque nuevo.** Es Bloque 1.

## Las decisiones, y por qué

### Un solo resolvedor del estado general, y lo usan todos

Hay un solo módulo, en `comun/hooks/lib/`, que junta el estado de la instalación y calcula
`READY`, `PARTIAL` o `BLOCKED`. Lo usan tres:
- `session-start.py`;
- `dev-harness.py harness`;
- `dev-harness.py setup`, que deja de imprimir `HARNESS READY` fijo.

Vive en la lib de los hooks porque el hook tiene que poder leerlo sin importar `harnesses/`, y un
proyecto de solo `analisis` también tiene hooks.

El resolvedor lee cuatro fuentes:
- `harness.lock.json`, para la versión y los harness instalados;
- `harness.installation.json`, el estado de la instalación;
- `harness.capacidades.json`, con el `estado` por integración que dejó el último `setup`;
- `harness.fuentes.json`, con el `state` y el `blocking` por fuente que dejó el último `fuentes`.

No hace red ni llama a ningún modelo: solo lee esos cuatro archivos.

### Qué es cada estado

```
BLOCKED   el lockfile falta o no se lee; o harness.installation.json dice installed: false; o
          alguna fuente de harness.fuentes.json esta en SOURCE_INTEGRITY_ALERT,
          SOURCE_CHANGED_SAME_VERSION o VERSION_REGRESSION
PARTIAL   no hay ninguna condicion de BLOCKED, y queda algo pendiente: una integracion que no
          esta en AVAILABLE (tambien si setup nunca corrio), una fuente que no esta en CURRENT
          ni en RETIRED, o harness.fuentes.json que no existe
READY     nada de lo anterior
```

Una fuente en `FRESHNESS_UNVERIFIED` es `PARTIAL`, no `BLOCKED`. Hoy las seis fuentes gestionadas
tienen `sha256: null` y están en ese estado, y declarar el harness bloqueado en cada instalación
por eso diría que no puede operar cuando sí puede. Lo pendiente se muestra. Las integraciones y el
conocimiento se evalúan solo con `desarrollo` instalado: un proyecto de solo `analisis` no los
tiene y no queda `PARTIAL` por eso.

Cada condición se guarda con un id en inglés:
- las de `BLOCKED` van a `blockingConditions`, por ejemplo `SOURCE_INTEGRITY_ALERT:ES0902` o
  `LOCKFILE_MISSING`;
- las de `PARTIAL` van a `pendingConditions`, por ejemplo `INTEGRATION_NOT_CONFIGURED:jira` o
  `SOURCE_FRESHNESS_UNVERIFIED:ES0902`.

`pendingConditions` es un campo nuevo en el schema del paquete, y es la única divergencia con él.

### `harness.installation.json`

- **Cuándo se escribe.** `install.ps1` lo escribe solo cuando la instalación terminó bien, después
  de verificar los hooks. Una instalación revertida no lo deja. Si esa escritura falla, el
  instalador avisa y termina igual, porque los hooks ya respondieron, y la sesión siguiente se
  comporta como una primera vez.
- **Qué contiene.** Todo lo que pide el schema del paquete, más `pendingConditions`, y
  `welcome.upgradeFrom` cuando corresponde.
- **Instalación nueva y actualización.**
  - Si el archivo no existe, es una instalación nueva: `firstRunShown: false`.
  - En un `-Update`, el archivo existe. Se conserva `firstRunShown`, y si la versión cambió se anota
    `welcome.upgradeFrom` con la versión anterior.
- **El proyecto.** `project.name` sale del nombre del contexto de proyecto
  (`docs/codebase/project-context.json`, `project_profile`) si existe. Si no, es `null` con
  `detected: false`. El nombre de la carpeta no es el nombre del proyecto y no se inventa.
- **Quién lo reescribe.** `session-start.py` reescribe el estado calculado y la marca de la
  bienvenida. Escribe con `.tmp` y `os.replace`, y un error de escritura no rompe el hook.
- **Qué no guarda.** Ningún secreto: ni tokens, ni URLs con credenciales, ni el contenido del
  `.env`. Solo estados e ids.
- **Cuándo se borra.** `-Uninstall` lo borra.

### La primera sesión, las siguientes y la actualización

```
firstRunShown: false          la bienvenida completa, una vez; despues firstRunShown: true
welcome.upgradeFrom presente  "Harness GCBA actualizado: <vieja> → <nueva> ✓" mas la linea compacta,
                              una vez; despues se borra upgradeFrom
en cualquier otro caso        una sola linea compacta
```

La bienvenida y la línea compacta se le muestran a la persona como `systemMessage`. Van además al
principio del contexto del modelo, antes del bloque que `session-start.py` ya escribe, que sigue
saliendo igual. Si la marca no se pudo escribir, la bienvenida vuelve a salir en la próxima sesión.
Eso es mejor que perderla.

`dev-harness.py harness --reiniciar-bienvenida` pone `firstRunShown: false` a propósito. Borrar el
archivo tiene el mismo efecto.

### Qué dice cada estado

Los ids se guardan en inglés, y solo se traduce la etiqueta:

| Id | Etiqueta |
|---|---|
| `READY` | `LISTO` |
| `PARTIAL` | `PARCIAL` |
| `BLOCKED` | `BLOQUEADO` |
| `AVAILABLE` | `DISPONIBLE` |
| `NOT_CONFIGURED` | `SIN CONFIGURAR` |
| `AUTHENTICATION_FAILED` | `FALLA DE AUTENTICACIÓN` |
| `CONNECTION_FAILED` | `SIN CONEXIÓN` |
| `PERMISSION_DENIED` | `SIN PERMISOS` |
| integración nunca verificada | `SIN VERIFICAR` |
| `CURRENT` | `ACTUAL` |
| `UPDATE_AVAILABLE` | `ACTUALIZACIÓN DISPONIBLE` |
| `ACKNOWLEDGED_PENDING` | `PENDIENTE ACEPTADO` |
| `SOURCE_INTEGRITY_ALERT` | `ALERTA DE INTEGRIDAD` |
| `FRESHNESS_UNVERIFIED` | `VIGENCIA SIN VERIFICAR` |

Un estado de `frescura.ESTADOS` que no está en la tabla sale con su id tal cual. Nunca sale como
`ACTUAL`.

Tres reglas sobre lo que se escribe:
- La tilde de éxito `✓` va solo delante de lo que está disponible.
- **`BLOCKED`** no dice "listo", "Harness listo" ni "listo para trabajar" en ninguna forma. Dice
  qué lo bloquea.
- **`PARTIAL`** nombra cada cosa pendiente.

La frase final "El Harness está listo para trabajar." sale solo con `READY`.

La bienvenida completa sigue el formato del paquete. La línea compacta es una sola línea, por
ejemplo:

```
Harness GCBA ◐ PARCIAL · Conocimiento VIGENCIA SIN VERIFICAR · Jira SIN CONFIGURAR · GitLab DISPONIBLE
```

### `dev-harness.py harness`

- **Sin argumentos:** la bienvenida completa, con el estado de ahora, y sin tocar
  `firstRunShown`.
- **`--json`:** el mismo estado con los ids en inglés, en `harness-installation/1.0`.
- **`--verbose`:** agrega la versión, la fecha de instalación, cada condición con su id y la ruta
  de cada archivo leído.
- **`--reiniciar-bienvenida`:** pone `firstRunShown: false`, como dice la sección anterior.

El comando no hace red: lee el mismo estado local. Para verificar las integraciones de nuevo está
`setup`.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/harness-installation-state.schema.json` | El contrato, con `pendingConditions` |
| `comun/hooks/lib/bienvenida.py` | El resolvedor único y los dos renderizadores (completo y compacto) |
| `comun/hooks/session-start.py` | Muestra la bienvenida o la línea, y actualiza la marca |
| `install.ps1` | Escribe `harness.installation.json` al terminar bien, lo conserva en `-Update` y lo borra en `-Uninstall` |
| `harnesses/desarrollo/bin/dev-harness.py` | `harness [--json] [--verbose] [--reiniciar-bienvenida]`; `setup` usa el resolvedor |
| `tests/casos/51_bienvenida.py` | Los escenarios del lado Python |
| un caso del instalador en `tests/casos/` | Los escenarios de instalación, actualización y desinstalación |

## Escenarios verificables

Numerados como el pedido: `E-nn` es `WLC-nn`. Los que agrega esta spec van después del 20.

- **E-01** — Una instalación que termina bien deja `.claude/harness.installation.json` con
  `installed: true`, `firstRunShown: false` y la versión de `VERSION`. Una instalación revertida no
  lo deja. · rojo visto: si
- **E-02** — El archivo que escribe el instalador, y el que reescribe el hook, validan contra
  `harness-installation-state.schema.json`. · rojo visto: si
- **E-03** — La primera sesión muestra la bienvenida completa como `systemMessage`, con los cinco
  bloques del formato (estado general, integraciones, conocimiento, comandos iniciales, y proyecto
  cuando se conoce), y deja `firstRunShown: true`. Integraciones, conocimiento y comandos iniciales
  salen cuando `desarrollo` está instalado: los cuatro comandos son de `dev-harness.py`, que
  `analisis` no instala (enmendado el 24-09-2026, después del primer pase). · rojo visto: si
- **E-04** — La segunda sesión muestra una sola línea y ninguna parte de la bienvenida completa.
  · rojo visto: si
- **E-05** — `session-start.py` no abre ninguna conexión de red. El test lo corre con el módulo de
  sockets y `urllib` reemplazados por unos que fallan. · rojo visto: si
- **E-06** — `session-start.py` y `bienvenida.py` no importan ningún cliente de modelo ni ningún
  módulo de `integraciones/`. · rojo visto: si
- **E-07** — Los tres estados salen con su etiqueta:
  - `READY` dice `LISTO` y la frase final;
  - `PARTIAL` dice `PARCIAL` y nombra cada pendiente;
  - `BLOCKED` dice `BLOQUEADO` y la condición que lo bloquea, y ni la bienvenida ni la línea
    contienen "listo" en ninguna forma, sin distinguir mayúsculas. El nombre del proyecto es un
    dato y queda afuera de la búsqueda: un proyecto que se llama "Portal Listo" se muestra igual.

  · rojo visto: si
- **E-08** — Una integración en `NOT_CONFIGURED`, `CONNECTION_FAILED` o nunca verificada no sale
  con `✓` ni con `DISPONIBLE`, y deja el estado en `PARTIAL`. · rojo visto: si
- **E-09** — El conocimiento sale del `state` de cada fuente de `harness.fuentes.json`: cambiar ese
  archivo cambia lo que se muestra, y `bienvenida.py` no calcula ninguna frescura. · rojo visto: si
- **E-10** — Una fuente en `SOURCE_INTEGRITY_ALERT` da `BLOQUEADO` y sale nombrada, con su id, en
  la bienvenida y en la línea compacta. · rojo visto: si
- **E-11** — Con un token en el `.env` y en el almacén, `harness.installation.json` no contiene
  ningún valor que el catálogo de secretos reconozca ni el valor del token. · rojo visto: si
- **E-12** — Con lo mismo, ni la bienvenida, ni la línea, ni `harness`, ni `harness --json`, ni
  `--verbose` imprimen el token. · rojo visto: si
- **E-13** — `dev-harness.py harness` muestra el estado que dan los archivos de ahora, sin red, y
  no cambia `firstRunShown`. · rojo visto: si
- **E-14** — `harness --json` usa los ids en inglés (`READY`, `NOT_CONFIGURED`,
  `FRESHNESS_UNVERIFIED`) y valida contra el schema. · rojo visto: si
- **E-15** — La salida humana está en castellano: las etiquetas de la tabla, y ningún id en inglés
  de los que la tabla traduce. · rojo visto: si
- **E-16** — Con `project-context.json` y su nombre, la bienvenida dice "Proyecto detectado:
  <nombre>". · rojo visto: si
- **E-17** — Sin contexto de proyecto, la bienvenida no inventa un nombre: dice que el proyecto no
  se detectó, sin `✓`, y `project.detected` queda en `false`. · rojo visto: si
- **E-18** — Un `-Update` a una versión nueva sobre un proyecto con `firstRunShown: true` no repite
  la bienvenida. La sesión siguiente muestra "Harness GCBA actualizado: <vieja> → <nueva> ✓" y la
  línea, una vez. · rojo visto: si
- **E-19** — `harness --reiniciar-bienvenida`, o borrar el archivo, hace que la sesión siguiente
  muestre la bienvenida completa otra vez. · rojo visto: si
- **E-20** — Todo lo que `session-start.py` escribía al contexto antes de este cambio sigue saliendo
  igual y en el mismo orden, después de la línea de la bienvenida: usuario y harness, git, cache,
  definiciones pendientes y el aviso del recorrido del código. · rojo visto: si
- **E-21** — `dev-harness.py setup` ya no imprime `HARNESS READY` fijo: imprime el estado del
  resolvedor. Con una integración caída, el texto para la persona no dice `READY` ni "listo". Las
  líneas `evento=` son la telemetría estable de `integraciones-bootstrap` y quedan afuera; que
  `harness.listo` se emita en cualquier estado queda anotado en `PENDIENTES-FH.md`.
  · rojo visto: si
- **E-22** — Un `harness.installation.json`, `harness.capacidades.json` o `harness.fuentes.json`
  roto o con un tipo inesperado no rompe el hook: sale con código 0, y el estado resultante nunca es
  `READY`. "Un tipo inesperado" es cualquier campo, en cualquier nivel, con un tipo distinto del que
  escribe su dueño, decida o no el estado: queda como `*_STATE_UNREADABLE` en `pendingConditions`.
  · rojo visto: si
- **E-23** — Un proyecto de solo `analisis` no lista integraciones ni conocimiento, y no queda en
  `PARTIAL` por eso. · rojo visto: si
- **E-24** — `-Uninstall` borra `harness.installation.json`. · rojo visto: si
- **E-25** — Un estado de fuente que no está en la tabla de etiquetas sale con su id y nunca como
  `ACTUAL`. · rojo visto: si
- **E-26** — Con `desarrollo`, un `harness.fuentes.json` sin ninguna fuente da `PARTIAL`, no
  `READY`. El resumen del conocimiento dice `ACTUAL` solo si todas las fuentes están en `CURRENT` o
  `RETIRED`: con una en alerta y el resto al día, no dice `Conocimiento ACTUAL`.
  · rojo visto: si

## Cómo se verifica

Todos los escenarios van por la suite. Los del hook, el resolvedor y la CLI van en
`tests/casos/51_bienvenida.py`. E-01, E-18, E-19 (la mitad del borrado), E-24 y la mitad de E-02 van
en un caso del instalador que arma un proyecto temporal. Ninguno lleva `· verificación: lectura`,
porque la bienvenida es determinista.

## Riesgos conocidos

- **Lo que muestra la bienvenida es tan viejo como el último `setup` y el último `fuentes`.** Si
  Jira se cayó ayer y nadie corrió `setup`, la línea sigue diciendo `DISPONIBLE`. Es el precio de no
  hacer red en SessionStart, y `--verbose` muestra de cuándo es cada dato.
- **El hook escribe un archivo en cada sesión.** Es un archivo chico y la escritura es atómica. Si
  el disco no deja escribir, la bienvenida se repite.
- **El `systemMessage` de SessionStart** es una salida que el hook no usaba hasta hoy para esto. El
  contrato de tres salidas no cambia: sigue siendo un aviso, y no bloquea ni pregunta.
