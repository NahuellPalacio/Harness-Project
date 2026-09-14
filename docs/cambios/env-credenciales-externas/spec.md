# Las credenciales externas del proyecto: `.env` y `.env.example`

**Estado:** verificado y cerrado en 0.15.0 · **Fecha:** 02-09-2026

## Qué problema resuelve

La trazabilidad de un proyecto —qué ticket motivó qué commit, qué MR corresponde a qué deploy—
necesita hablar con Jira, GitLab y OpenShift, y hoy no hay ningún lugar donde un desarrollador deje
sus credenciales para eso. Cada uno improvisaría su propio archivo, con su propio nombre de
variable, sin `.gitignore` que lo cubra si el proyecto no lo tenía ya. Este cambio es el primer
paso —el andamiaje— de una funcionalidad más grande: dejar el lugar donde esas credenciales viven,
antes de escribir nada que las use.

## Qué queda afuera

- **Ningún agente ni skill lee estas variables todavía.** El consumidor —lo que efectivamente
  consulta Jira, GitLab u OpenShift para armar trazabilidad— es trabajo futuro, no de este cambio.
  Construirlo ahora sería adelantarse a una decisión de diseño (qué agente, qué formato de salida)
  que no está tomada.
- **Sin patrón de detección para tokens de Jira.** GitLab (`glpat-…`) y OpenShift (`sha256~…`)
  tienen un prefijo fijo y reconocible, igual que `token-github` o `token-slack` ya en el catálogo.
  Un token de Jira Cloud es una cadena aleatoria sin prefijo distintivo: un patrón para eso o no
  dispara nunca, o dispara sobre cualquier cadena aleatoria del repo. Ninguna de las dos sirve.
- **Sin generalizar el mecanismo a otros harnesses.** `comun` y `analisis` no reciben la capacidad
  de aportar su propio `.env.example` de proyecto en este cambio. Si un segundo harness lo necesita,
  ahí se generaliza; hoy sería una abstracción para un caso que no existe.
- **Sin URLs ni namespaces por defecto.** `JIRA_BASE_URL`, `GITLAB_BASE_URL` y
  `OPENSHIFT_SERVER_URL` quedan con un placeholder instructivo, nunca con una URL real de GCBA
  precargada: cada proyecto habla con su propia instancia, y adivinar una equivocada es peor que no
  poner ninguna.

## Las decisiones, y por qué

### `.env` y `.env.example`, no un JSON nuevo

El harness ya tiene `harness.config.json` para configuración no secreta. Esto es distinto:
credenciales, por persona, que no tienen que viajar ni siquiera adentro de un `.json` que alguien
podría copiar sin pensar. `.env` es el formato que cualquier herramienta que llegue a consumir esto
—un script, una CLI, una librería de terceros— ya sabe leer sin que el harness le enseñe nada.

### Reparte `desarrollo`, no `comun`

Jira, GitLab y OpenShift son herramientas del ciclo de desarrollo. Un proyecto de solo `analisis`
no las necesita, y repartirlas desde `comun` las instalaría igual, sin nadie que las use —el mismo
argumento por el que `rutaCodebase` quedó en el manifiesto de `desarrollo` y no en el de `comun`.

### `.env.example` se pisa en cada `-Update`; `.env` no se toca nunca

`.env.example` es contenido del harness: si mañana se agrega una cuarta integración, todo proyecto
instalado tiene que verla en la próxima actualización, igual que cualquier otra plantilla. `.env` es
del desarrollador —sus tokens reales, si llegó a completarlo— y sigue exactamente la regla ya
probada de `harness.config.json`: se crea una vez, si no existe, y nunca se vuelve a tocar. Pisarlo
en un `-Update` borraría credenciales reales sin aviso.

### `.env` se siembra con las mismas variables que `.env.example`, vacías

Sin esto, el primer paso de cada desarrollador sería copiar `.env.example` a mano. Con esto, el
archivo ya existe con los nombres correctos la primera vez que se instala `desarrollo`, listo para
completar.

### Ningún token real pasa por esta conversación ni por el disco de este repositorio

`.env` se genera vacío. Nadie —ni quien construye este cambio, ni el agente que lo revise después—
escribe un token real en ningún archivo. Rellenarlo es tarea de cada desarrollador, en su propia
máquina, fuera de cualquier sesión de Claude Code: `permissions.deny` ya le impide a Claude *leer*
`.env` (`Read(./.env)`, `Read(./.env.*)`), así que un token puesto ahí queda fuera del alcance del
harness por partida doble.

### Se suman dos patrones al catálogo de secretos: GitLab y OpenShift, no Jira

Ya que este cambio le da nombre y lugar a estos tres tokens, es el momento barato de enseñarle al
detector a reconocer dos de los tres si aparecen sueltos en un commit. GitLab y OpenShift tienen
forma fija (`glpat-…`, `sha256~…`); Jira no la tiene, y se deja afuera con su motivo — ver arriba.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/.env.example` | La plantilla versionada: las seis variables, comentadas, con placeholder instructivo |
| `install.ps1` — `New-EnvProyecto` | Escribe `.env.example` en la raíz del proyecto en cada instalación/actualización; crea `.env` una sola vez, sembrado con las mismas variables vacías, y nunca lo vuelve a tocar. Corre solo si `desarrollo` está entre los harnesses instalados |
| `comun/reglas/secretos.patrones.json` | Dos patrones nuevos, confianza alta: `token-gitlab` (`glpat-…`) y `token-openshift` (`sha256~…`) |
| `tests/casos/17-env-instalador.ps1` | Escenarios de instalador: creación, `-Update`, `-Uninstall`, y el caso sin `desarrollo` |
| `tests/fixtures/paridad-secretos.json` + `tests/casos/04_secretos.py` | Casos positivos y negativos de los dos patrones nuevos |

## Escenarios verificables

### La plantilla

- **E-01** — Con `desarrollo` entre los harnesses instalados, una instalación nueva deja
  `.env.example` en la raíz del proyecto, idéntico byte a byte al de `harnesses/desarrollo/`.
  · rojo visto: no consta
- **E-02** — Sin `desarrollo` entre los harnesses instalados, no se escribe `.env.example` ni
  `.env`. · rojo visto: no consta
- **E-03** — Un `-Update` sobre un proyecto que ya tiene `.env.example` lo pisa con la versión
  actual de la plantilla. · rojo visto: si

### El archivo del desarrollador

- **E-04** — Con `desarrollo` instalado y sin `.env` previo, una instalación nueva lo crea con las
  mismas seis variables que `.env.example`, todas vacías o con placeholder, nunca con un valor de
  ejemplo que parezca un token real. · rojo visto: no consta
- **E-05** — Un `.env` preexistente con contenido cualquiera —incluida una línea que un
  desarrollador ya completó a mano— queda byte a byte idéntico después de `-Update`.
  · rojo visto: si
- **E-06** — `-Uninstall` no borra `.env` ni `.env.example`. · rojo visto: si

  📌 **Una sola mutación confirmó dos escenarios a la vez.** Volver a sumar `.env.example` a
  `$instalados` —el error obvio a cometer, calcado del resto del código de instalación— rompió
  E-03 **y** E-06 juntos: entrar al inventario del lockfile lo vuelve "editado a mano" a ojos de
  `-Update` (que entonces lo preserva como `.nuevo` en vez de pisarlo) y lo vuelve borrable para
  `-Uninstall`. Las dos consecuencias vienen de la misma causa, y los dos escenarios la atrapan.

### El catálogo de secretos

- **E-07** — Un texto que contiene un token con forma `glpat-` seguido de veinte o más caracteres
  alfanuméricos dispara `token-gitlab`, confianza alta. · rojo visto: si
- **E-08** — Un texto que contiene un token con forma `sha256~` seguido de veinte o más caracteres
  dispara `token-openshift`, confianza alta. · rojo visto: si
- **E-09** — El placeholder instructivo que trae `.env.example` para cada una de las seis variables
  no dispara ningún patrón del catálogo. · rojo visto: si

## Cómo se verifica

Los nueve son deterministas: E-01 a E-06 corren sobre un proyecto descartable con
`tests/casos/17-env-instalador.ps1`, igual que el resto de la suite de instalador; E-07 a E-09
corren sobre el catálogo real con `tests/casos/04_secretos.py`. Ninguno depende de un agente con
modelo — no hay escenario de lectura en este cambio.

## Riesgos conocidos

- **Un desarrollador puede llenar `.env` con un token y commitearlo igual**, si tiene un
  `.gitignore` propio que no hereda el bloque del harness (por ejemplo, un proyecto que ya excluía
  `.env` de otra forma incompatible). `.gitignore` es la primera defensa, no la única: el catálogo
  de secretos es la segunda, y por eso E-07/E-08 importan.
- **Un cuarto sistema con auth por token no tiene dónde caer.** Este cambio no deja un mecanismo
  genérico de "agregar una integración"; agregar una quinta variable hoy es editar
  `.env.example` a mano. Aceptado: generalizarlo antes de tener dos casos reales sería adivinar la
  forma correcta.
