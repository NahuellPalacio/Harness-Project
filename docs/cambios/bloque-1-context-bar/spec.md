# Bloque 1 — la Context Bar existe, y el harness sabe si está activa

**Estado:** especificado · **Fecha:** 24-09-2026 · **Bloque:** 1, leyendo al 4

## Qué problema resuelve

El paquete da por hecho que la Context Bar existe y pide mostrar si está activa. **No existe.** El
Bloque 4 tiene el cálculo de la barra, que es `contabilidad/barra.py`: el resumen normalizado de la
sesión activa, con el contexto y el presupuesto por separado, y `dev-harness.py contabilidad <TAREA>
--barra` lo imprime. Pero `settings.json` no registra ningún `statusLine`, así que en una sesión de
Claude Code no se ve nada.

Además, el libro del Bloque 4 no se llena solo. No hay un ejecutor que escriba eventos en vivo: el
libro se llena con `contabilidad --ingerir <transcripción>`, a mano.

Decisiones del usuario del 24-09-2026:
- **Se construye la barra y se mide.** No se reporta el estado de algo que no existe.
- **La barra ingiere y lee.** Cada vez que Claude Code la invoca, pasa la transcripción de la sesión
  por el adaptador del Bloque 4 y dibuja lo que el Bloque 4 resume. El Bloque 4 sigue siendo la
  única fuente contable.

Y encima de eso, lo que pide el paquete: que la instalación, la bienvenida y `harness` distingan
instalada, configurada, activa, pendiente de reinicio y rota, para la Context Bar, la contabilidad
del Bloque 4 y el reporte de seguridad.

## Qué queda afuera

- **Una barra nativa de VS Code.** El `statusLine` es de Claude Code, y su documentación no dice si
  la extensión de VS Code lo muestra. Solo se promete la terminal. Una extensión de VS Code sería
  otro adaptador de presentación que lea el Bloque 4.
- **Un ejecutor del Bloque 3 y la tarea activa.** Nada declara hoy cuál es la tarea en curso. La
  barra contabiliza la sesión, no una tarea, y el campo Tarea sale como no disponible hasta que
  exista quien la declare.
- **Otro libro.** La barra no escribe en ningún lado que no sea el libro del Bloque 4 y su propia
  señal de vida.
- **Los datos de costo que Claude Code manda por stdin.** Usarlos para dibujar sería una segunda
  fuente contable. Si hacen falta, entran por un adaptador del Bloque 4, en otro cambio.
- **OpenShift.** Sigue afuera, como en la bienvenida.
- **Podar `.claude/runtime/accounting/`.** Ya es un pendiente abierto, y la barra lo hace crecer una
  carpeta por sesión.

## Las decisiones, y por qué

### El comando de la barra tiene que correr en los dos shells

Según la documentación de `statusLine` (code.claude.com/docs/en/statusline, consultada el
24-09-2026), la barra se comporta así:
- No acepta el campo `shell`, a diferencia de los hooks.
- En Windows corre en Git Bash si Claude Code lo encuentra, y en PowerShell si no.
- La documentación no dice que exporte `CLAUDE_PROJECT_DIR`.
- Se invoca al empezar la sesión y después de cada mensaje, con 300 ms de debounce.
- Si sale con otro código que 0 o sin salida, la barra queda en blanco.
- Si hay una invocación en vuelo, la cancela.

Es el mismo agujero que el arreglo de los hooks en PowerShell, sin la salida de fijar el shell. El
comando registrado tiene que ser válido en Git Bash y en PowerShell a la vez:
- Arranca con un ejecutable, nunca con una cadena entre comillas.
- Usa barras `/`.
- Lleva sus argumentos entre comillas simples, que los dos shells toman literales.

`install.ps1` lo prueba corriéndolo con `bash -c` y con `powershell.exe -NoProfile -Command`, igual
que prueba los hooks. Si no corre en alguno de los dos, la barra queda `NOT_CONFIGURED` con
`CONTEXT_BAR_CONFIGURATION_INVALID`, y la instalación sigue: la barra no es una compuerta.

### Qué hace la barra en cada invocación

La barra hace cinco cosas, en orden:
1. Lee de stdin el `session_id` y el `transcript_path`.
2. Ingiere la transcripción con el adaptador `claude_code` del Bloque 4, al libro de la sesión. El
   libro deduplica por `eventId`, así que ingerir dos veces no suma dos veces.
3. Pide `contabilidad.barra.de(…)` y lo dibuja en una línea.
4. Escribe su señal de vida.
5. Sale con 0 siempre, y sin salida vacía: si falla, dibuja `HARNESS | sin datos del Bloque 4`.

Solo dibuja lo que da el Bloque 4: contexto %, tokens, costo, tiempo, agente, tarea, presupuesto % y
tier del modelo. Un campo que el Bloque 4 no tiene no aparece: nunca sale como 0. Un costo
`COST_UNRESOLVED` no es `USD 0`.

La latencia se mide con una transcripción de 5 MB. Si el p50 pasa de 400 ms, queda a la vista en
`-Doctor` y en la verificación, sin mover el umbral.

### La activación se prueba con la señal de vida, no con el archivo

La barra escribe `.claude/runtime/contextbar.json` con estos campos:
- `sessionId`;
- `configurationFingerprint`, el sha256 del bloque `statusLine` registrado;
- `integrationVersion`;
- `lastRenderedAt`;
- `block4`: `OK` o `SOURCE_UNAVAILABLE`.

No guarda ningún número contable, porque esos viven en el libro.

```
ACTIVE          hay senal de vida de la sesion actual, con el fingerprint registrado y block4 OK
RELOAD_REQUIRED el fingerprint registrado cambio en un install o -Update, y no hay senal de vida
                con el nuevo
CONFIGURED      registrada y probada por el instalador, sin senal de vida de esta sesion y sin
                cambio pendiente
ERROR           senal de vida de esta sesion con block4 SOURCE_UNAVAILABLE
                (CONTEXT_BAR_BLOCK4_SOURCE_UNAVAILABLE)
NOT_CONFIGURED  no hay statusLine registrado, o el comando no corre en los dos shells
INSTALLED       el renderizador esta en disco y no registrado
UNRESOLVED      la senal de vida o el settings.json no se pueden leer
```

- **Qué es "la sesión actual".** Para `session-start.py` es el `session_id` de su evento. Para
  `dev-harness.py harness`, que no tiene sesión, es la última sesión vista: sale `ACTIVE (última
  sesión: <id corto>)`, y `activeInCurrentSession` queda en `false`.
- **Por qué no se asume que la barra se recarga sola.** Claude Code vigila los settings, pero la
  documentación no garantiza que la barra se recargue a mitad de sesión. Por eso, después de un
  cambio, el estado es `RELOAD_REQUIRED` hasta que la señal de vida lo desmienta. Si la barra se
  recarga sola, el aviso se va en el primer mensaje, sin que nadie reinicie.
- **Qué muestra.** Con `RELOAD_REQUIRED`, la persona ve "Context Bar configurada. Reiniciá la sesión
  de Claude Code para activarla.", sin `✓`.

### Los tres componentes y el estado general

`harness.installation.json` pasa a `harness-installation/1.1` con `runtimeComponents`:
- **`block4Accounting`:**
  - `ACTIVE` si el paquete `contabilidad/` está en disco y la carpeta del libro se puede escribir;
  - `ERROR` si un libro existente no se puede leer;
  - `NOT_CONFIGURED` sin `desarrollo`.
- **`contextBar`:** la tabla de arriba, más `renderer: claude-code-statusline`, `source: block4`,
  `reloadRequired`, `activeInCurrentSession`, `configurationFingerprint` e `integrationVersion`.
- **`securityReporting`:**
  - `ACTIVE` si `reporte_seguridad/` y sus tres schemas están en disco y se cargan;
  - `ERROR` si alguno falta o no se carga;
  - `NOT_CONFIGURED` sin `desarrollo`.

  `ACTIVE` quiere decir que el pipeline está disponible, no que haya aprobación de seguridad.

Un componente que no está `ACTIVE` suma una condición a `pendingConditions`: `CONTEXT_BAR_…`,
`BLOCK4_…` o `SECURITY_REPORTING_…`. Así el estado general queda `PARTIAL`, nunca `BLOCKED`. La
observabilidad caída no hace inseguro al harness, así que un `Block 4 ERROR` es `PARCIAL`, no
`BLOQUEADO` como en el ejemplo del paquete, y la divergencia se declara acá. Ninguno de los tres
estados usa `AVAILABLE`, que es de las integraciones.

### La migración de 1.0 a 1.1

El resolvedor lee un archivo `1.0`, conserva todos sus campos y lo escribe como `1.1` la próxima
vez que escribe. Si un `1.0` no se puede migrar, se trata como ilegible:
`INSTALLATION_STATE_UNREADABLE`, igual que hoy.

El schema del paquete usa `allOf`, que el validador de subconjunto no interpreta. `contextBar` se
escribe con sus propiedades aplanadas en un solo objeto. Esa es la divergencia de schema, más
`pendingConditions` y `welcome.upgradeFrom`, que ya estaban.

### El `-Update` compara, y no churnea

`install.ps1` guarda la huella de lo que la barra necesita para correr:
- el `configurationFingerprint`;
- la versión del renderizador;
- el sha256 del adaptador `claude_code`;
- el sha256 de `session-start.py`.

En un `-Update`, si alguna cambió, marca `reloadRequired: true` y `RELOAD_REQUIRED`. Si ninguna
cambió, no toca `runtimeComponents` ni reescribe el archivo por ese motivo.

El aviso de actualización pasa a tener dos líneas. La segunda es "Context Bar actualizada · reinicio
de Claude Code requerido." o "Context Bar activa.", según corresponda.

### Lo que se muestra

- **La bienvenida.** Suma el bloque "Observabilidad" con los tres componentes, solo con
  `desarrollo`:
  - `ACTIVO` o `ACTIVA` llevan `✓`.
  - `REQUIERE REINICIO` va sin `✓`, y abajo "Acción requerida".
  - `ERROR` sale como `ERROR`, sin `✓`.
- **La línea compacta.** Dice el estado de la Context Bar y ningún número de la barra, porque la
  barra ya los muestra siempre y repetirlos es ruido. Con `ACTIVE`, la línea dice solo
  `Context Bar ACTIVA`.
- **`harness`.** Suma la sección "Runtime / Observabilidad":
  - los tres componentes;
  - si hace falta reiniciar;
  - si la última sesión vista cargó la barra.

  `--json` los da con los ids en inglés. `--verbose` agrega fingerprints, versiones y fechas de
  validación, y ningún secreto.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/bin/contabilidad/statusline.py` | La barra: lee stdin, ingiere, pide `barra.de`, dibuja una línea y escribe la señal de vida |
| `comun/settings/` o `install.ps1` | El `statusLine` registrado, válido en Git Bash y en PowerShell |
| `install.ps1` | Prueba el comando en los dos shells, guarda las huellas y marca `RELOAD_REQUIRED` en un `-Update` que las cambia |
| `comun/schemas/harness-installation-state.schema.json` | A `1.1`, con `runtimeComponents` aplanado |
| `comun/hooks/lib/bienvenida.py` | Los tres componentes, la migración, la bienvenida, la línea y las etiquetas |
| `harnesses/desarrollo/bin/dev-harness.py` | La sección "Runtime / Observabilidad" en `harness` |
| `docs/contabilidad.md` | La barra, en la terminal y no en VS Code |
| `tests/casos/53_context_bar.py` y el caso del instalador | Los escenarios |

## Escenarios verificables

Numerados como el pedido: `E-nn` es `CBV-nn`. Los que agrega esta spec van después del 35.

- **E-01** — Un `harness.installation.json` `1.0` pasa a `1.1` sin perder ningún campo.
  · rojo visto: no consta
- **E-02** — El `1.1` que escriben el instalador, el hook y la CLI valida contra el schema.
  · rojo visto: no consta
- **E-03** — Después de instalar, los tres componentes tienen estado. · rojo visto: no consta
- **E-04** — Con el renderizador en disco y el `statusLine` registrado, sin señal de vida, la
  barra no es `ACTIVE`. · rojo visto: no consta
- **E-05** — Registrada y probada, sin señal de vida de la sesión actual, es `CONFIGURED`, o
  `RELOAD_REQUIRED` si el fingerprint cambió. · rojo visto: no consta
- **E-06** — Con la señal de vida de la sesión actual, el fingerprint registrado y `block4: OK`, es
  `ACTIVE` y `activeInCurrentSession: true`. · rojo visto: no consta
- **E-07** — Un `-Update` que cambia el `statusLine` marca `reloadRequired: true`.
  · rojo visto: no consta
- **E-08** — Un `-Update` que no cambia ninguna huella no marca reinicio. · rojo visto: no consta
- **E-09** — Con `block4: SOURCE_UNAVAILABLE`, la barra no es `ACTIVE`: es `ERROR` con
  `CONTEXT_BAR_BLOCK4_SOURCE_UNAVAILABLE`. · rojo visto: no consta
- **E-10** — La barra no escribe ningún archivo fuera del libro del Bloque 4 y de
  `contextbar.json`, y `contextbar.json` no tiene ningún número contable. · rojo visto: no consta
- **E-11** — La bienvenida con `desarrollo` muestra "Observabilidad" con los tres componentes.
  · rojo visto: no consta
- **E-12** — `RELOAD_REQUIRED` sale como `REQUIERE REINICIO`, sin `✓`, con la acción requerida.
  · rojo visto: no consta
- **E-13** — `ACTIVE` sale como `ACTIVA` o `ACTIVO`, con `✓`. · rojo visto: no consta
- **E-14** — `ERROR` sale como `ERROR`, sin `✓`, y deja el estado general en `PARTIAL`.
  · rojo visto: no consta
- **E-15** — `session-start.py` sigue sin abrir ninguna conexión, con la barra incluida.
  · rojo visto: no consta
- **E-16** — Ni `session-start.py` ni la barra importan un cliente de modelo. · rojo visto: no consta
- **E-17** — Con la barra `ACTIVE`, la línea compacta no repite tokens, costo ni contexto.
  · rojo visto: no consta
- **E-18** — `harness` muestra los tres componentes, el reinicio pendiente y la última sesión vista.
  · rojo visto: no consta
- **E-19** — `harness --json` usa los estados en inglés. · rojo visto: no consta
- **E-20** — `harness --verbose` no imprime ningún secreto con un token cargado.
  · rojo visto: no consta
- **E-21** — Un campo que el Bloque 4 no tiene no aparece en la barra, y un `COST_UNRESOLVED` no sale
  como `USD 0`. · rojo visto: no consta
- **E-22** — Los tokens y el costo que dibuja la barra son los de `barra.de` sobre el libro, y
  cambiar el costo de stdin no cambia lo que dibuja. · rojo visto: no consta
- **E-23** — Agente, tarea y presupuesto salen del estado del Bloque 4, y sin tarea declarada la
  tarea no aparece. · rojo visto: no consta
- **E-24** — `docs/contabilidad.md` dice que la barra es de la terminal de Claude Code.
  · rojo visto: no consta
- **E-25** — Ningún texto del harness afirma una integración nativa con la barra de estado de VS
  Code. · rojo visto: no consta
- **E-26** — Una instalación nueva con la barra registrada dice que puede hacer falta reiniciar, si
  no hay señal de vida. · rojo visto: no consta
- **E-27** — El aviso de reinicio desaparece cuando llega la señal de vida con el fingerprint nuevo.
  · rojo visto: no consta
- **E-28** — Un `-Update` normal muestra el aviso compacto de dos líneas. · rojo visto: no consta
- **E-29** — Con el harness `BLOCKED`, nada dice que la barra o el harness estén listos.
  · rojo visto: no consta
- **E-30** — `securityReporting` `ACTIVE` no dice nada de la aprobación de seguridad: C2 y el estado
  oficial no se mueven. · rojo visto: no consta
- **E-31** — Un cambio en el bloque `statusLine` cambia `configurationFingerprint`.
  · rojo visto: no consta
- **E-32** — Un cambio en la versión del renderizador se detecta. · rojo visto: no consta
- **E-33** — Sin cambios, `runtimeComponents` no se reescribe: dos `-Update` iguales dejan el archivo
  igual byte a byte, salvo `updatedAt`. · rojo visto: no consta
- **E-34** — `activeInCurrentSession` va aparte de `installed` y `configured`: una barra instalada y
  configurada de otra sesión no está activa en esta. · rojo visto: no consta
- **E-35** — Los mismos archivos dan los mismos estados. · rojo visto: no consta
- **E-36** — El comando registrado corre con `bash -c` y con `powershell.exe -NoProfile -Command`,
  sale con 0 y dibuja una línea, también con una ruta de proyecto con espacios.
  · rojo visto: no consta
- **E-37** — Con una transcripción rota, sin libro o sin stdin, la barra sale con 0 y dibuja
  `HARNESS | sin datos del Bloque 4`. Nunca una línea vacía. · rojo visto: no consta
- **E-38** — Ingerir la misma transcripción dos veces deja el libro con los mismos eventos.
  · rojo visto: no consta
- **E-39** — La barra no dibuja texto de la transcripción: ni prompts, ni código, ni nada que el
  catálogo de secretos reconozca. · rojo visto: no consta

## Cómo se verifica

Todos van por la suite, en `tests/casos/53_context_bar.py` y en el caso del instalador. Se mira con
los ojos, y se anota en la verificación, lo que la suite no puede hacer:
- abrir una sesión y ver la barra;
- comprobar si se recarga sola a mitad de sesión;
- comprobar si aparece en la extensión de VS Code.

## Riesgos conocidos

- **La latencia.** Ingerir una transcripción larga en cada mensaje puede pasar los 400 ms. Se mide,
  y si pasa, queda a la vista.
- **El libro crece una carpeta por sesión.** Es el pendiente de podar `accounting/`, que ahora duele
  más.
- **La documentación no dice que Claude Code exporte `CLAUDE_PROJECT_DIR` a la barra.** El comando
  se registra con la ruta absoluta del proyecto. Si el proyecto se mueve de carpeta, hace falta un
  `-Update`.
- **Si la barra se recarga sola a mitad de sesión,** `RELOAD_REQUIRED` es un aviso de más que dura
  un mensaje. Se prefirió eso a asumir una recarga que nadie garantiza.
