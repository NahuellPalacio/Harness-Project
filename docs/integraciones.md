# Las integraciones externas

Jira Cloud y GitLab, hoy. El harness las configura, las valida y declara qué se puede
hacer con ellas. Quien las consume es el Bloque 2: el contexto de una tarea.

## La pregunta que contestan

> ¿Qué integraciones tengo configuradas, cuáles funcionan y qué capacidades puedo usar?

```powershell
python .claude\harness\bin\desarrollo\dev-harness.py estado
```

```
GCBA Development Harness

Configuración
------------------------------------------------
Fuente              .env local
Acceso del modelo   BLOQUEADO

Integraciones
------------------------------------------------
Jira Cloud          AVAILABLE
GitLab              NOT_CONFIGURED
  Faltan: GITLAB_BASE_URL, GITLAB_TOKEN
  Falta configurar GitLab: GITLAB_BASE_URL, GITLAB_TOKEN. Completá las variables faltantes en el .env local.

Capacidades
------------------------------------------------
  DISABLED  gitlab.branch.read
  ...
  ENABLED   jira.issue.search

Estado
------------------------------------------------
Harness GCBA ◐ PARCIAL · Conocimiento VIGENCIA SIN VERIFICAR · Jira DISPONIBLE · GitLab SIN CONFIGURAR
```

La última sección es el estado general, el mismo que muestra cada sesión al arrancar. Con una
integración caída dice `PARCIAL` y la nombra, y nunca "listo". **Una integración que no anda
deshabilita sus capacidades y nada más:** el comando sale con código 0.
`dev-harness.py harness` muestra el mismo estado con el detalle, sin volver a consultar nada.

`estado --resumen` es la versión de una línea por integración que muestra el instalador al
terminar.

## Configurar: el `.env` local, y nada más

Desde [entorno-primero](cambios/entorno-primero/spec.md) hay **un solo archivo que se completa**,
el `.env` de la raíz del proyecto. El instalador lo crea una vez, con la plantilla de
`.env.example`, y después no lo vuelve a tocar:

```dotenv
HARNESS_JIRA_ENABLED=true
JIRA_BASE_URL=https://tu-organizacion.atlassian.net
JIRA_USER=tu.email@buenosaires.gob.ar
JIRA_TOKEN=<tu-api-token-de-jira>

HARNESS_GITLAB_ENABLED=true
GITLAB_BASE_URL=https://gitlab.tu-organizacion.gob.ar
GITLAB_PROJECT=grupo/proyecto
GITLAB_TOKEN=<tu-personal-access-token-de-gitlab>
```

Para ver qué falta, sin que nada te pregunte:

```powershell
python .claude\harness\bin\desarrollo\dev-harness.py setup
python .claude\harness\bin\desarrollo\dev-harness.py reconfigurar gitlab
```

Los dos muestran cada variable como `presente` o `ausente`, con la capa de donde sale, y
revalidan. Ninguno muestra un valor.

| Regla | Qué significa |
|---|---|
| Precedencia | `PROCESS_ENV > DOTENV > LEGACY > SAFE_DEFAULT`. El entorno del proceso le gana al `.env`, y eso no es un conflicto |
| `HARNESS_*_ENABLED` | `true/false`, `1/0`, `yes/no`, `on/off`, sin importar mayúsculas. Otra cosa es `ENV_ENABLED_FLAG_INVALID` |
| Vacío o `<...>` | Es que no está cargado |
| Deshabilitada | No pide variables ni sale a la red |
| Habilitada e incompleta | `NOT_CONFIGURED`, con los nombres de lo que falta |

Qué tokens hacen falta:

| Integración | Dónde se saca el token | Qué alcanza |
|---|---|---|
| Jira Cloud | `id.atlassian.com` → Security → API tokens | El token va con tu email (`JIRA_USER`): el harness arma el Basic |
| GitLab | Preferences → Access Tokens | Scope `read_api`. Con `read_repository` solo queda `gitlab.repository.read` |

> 🔴 **El token no se pasa por la línea de comandos.** `--token` existe para rechazarlo:
> un argumento queda en el historial del shell, en la lista de procesos, en la
> transcripción de la sesión de Claude Code y en el texto que mira el hook de secretos.

## Dónde vive cada cosa

| Archivo | Qué lleva | Quién lo toca |
|---|---|---|
| `.env` | Todo: banderas, URLs, usuario y tokens | Vos, y nadie más |
| `.env.example` | La plantilla, entre `# >>> gcba-harness: integraciones >>>` y su cierre | El instalador reescribe el bloque; lo demás es del proyecto |
| `.claude/harness/reglas/desarrollo/integration-environment-contract.json` | Qué variables hay y cuáles son `SECRET` | El instalador, en cada `-Update` |
| `.claude/harness.integraciones.json` | La proyección sanitizada: `enabled`, `baseUrl`, `usuario`, `gitlabProyecto` | Se regenera en cada `setup`, `estado` o `reconfigurar` |
| `.claude/harness.capacidades.json` | El resultado de la última corrida, con `faltan` por integración | Se reescribe en cada corrida |

**El `.env` es sensible entero**, aunque también lleve valores públicos: `permissions.deny` le
tapa a Claude `.env` y `.env.*`, el `.gitignore` lo excluye del repositorio, y el hook de
`PreToolUse` impide escribir un token literal en cualquier archivo. Ver [secretos.md](secretos.md).
Lo que el agente sí puede leer es la proyección, que no lleva ningún campo `SECRET`: el
resolvedor no los copia, y una clave con forma de secreto se rechaza igual.

### Si venís de una versión anterior

El `harness.integraciones.json` que completabas a mano se sigue leyendo, **por debajo del
`.env`**, para que el `-Update` no te deje sin integraciones. En la primera corrida sus valores
públicos pasan al bloque `legado` de la proyección, y `setup` dice qué variables faltan pasar al
`.env` para terminar. Cada una sale de `legado` cuando aparece en el `.env`, y no vuelve.

## Los cinco estados

Ninguna integración contesta con un booleano, porque "no anda" se arregla de cuatro
formas distintas.

| Estado | Qué pasó | Qué hacer |
|---|---|---|
| `NOT_CONFIGURED` | Deshabilitada, o le falta una variable, o el `.env` tiene un valor inválido | Completar el `.env` |
| `AUTHENTICATION_FAILED` | 401: el token no fue aceptado | Generar uno nuevo y cargarlo en el `.env` |
| `PERMISSION_DENIED` | 403: el token sirve, los permisos no alcanzan | Pedir los permisos de lectura que falten |
| `CONNECTION_FAILED` | Timeout, DNS, TLS, 5xx o una URL que redirige | Revisar la red, la VPN o la `baseUrl` |
| `AVAILABLE` | Contestó | Nada |

Antes de salir a la red, el resolvedor puede frenar una integración con `ENV_ENABLED_FLAG_INVALID`,
`ENV_CONFIGURATION_CONFLICT` (una variable definida dos veces en el `.env` con valores distintos),
`ENV_PUBLIC_PROJECTION_REJECTED_SECRET` o `ENV_VALUE_INVALID`. Un `.env` que no se puede leer es
`ENV_FILE_UNREADABLE` y un contrato roto es `ENV_CONTRACT_INVALID`: los dos salen con código 2.

El mensaje sale de un diccionario fijo del código y **nunca** del cuerpo de la respuesta ni del
`.env`: un servidor puede devolver la credencial que recibió adentro de un mensaje de error.

## Soportada no es lo mismo que disponible

```
soportada   el harness sabe hacerlo       -> CAPACIDADES de la clase de integración
disponible  además está validado ahora    -> harness.capacidades.json, ENABLED en esta máquina
```

📌 **Lo soportado lo declaran las clases de integración, no el manifiesto.** `capacidadesSoportadas`
de `manifest.json` no se lee en tiempo de ejecución: es una copia que un test contrasta contra las
clases (`tests/casos/18_integraciones.py`). Lo disponible depende de la validación en esta máquina.

Una capacidad soportada cuya integración está caída figura `DISABLED`, nunca ausente: una
lista que se acorta sola no explica por qué se acortó. La regla que esto hace cumplir es
una sola — **una capacidad no se habilita si su integración no se validó.**

El timeout de cada llamada sale de `timeoutIntegraciones` en `harness.config.json`, y son
5 segundos si la clave no está.

## Agregar una integración nueva

Una subclase de `Integracion` y nada del bootstrap se toca:

```python
class IntegracionSonarQube(Integracion):
    nombre = "sonarqube"
    etiqueta = "SonarQube"
    clave_token = "SONARQUBE_TOKEN"
    campos = ("baseUrl",)
    CAPACIDADES = ("sonarqube.project.read",)
    camino_de_validacion = "/api/system/status"

    def cabeceras(self):
        return {"Authorization": "Bearer " + (self.token() or "")}

    def descubrir_capacidades(self):
        return ["sonarqube.project.read"] if self.pedir("/api/projects/search").ok else []
```

Después: sumarla a `CLASES` en `dev-harness.py`, sus capacidades a
`capacidadesSoportadas` del manifiesto —hay un test que compara las dos listas—, su bloque al
contrato `integration-environment-contract.json` con cada campo clasificado `PUBLIC_CONFIG` o
`SECRET`, y sus variables al `.env.example`. Un contrato y un código que no nombran las mismas
integraciones son `ENV_CONTRACT_INVALID`.

## Lo que este bloque no hace

- **No escribe nada en ningún sistema externo.** Todas las capacidades son de lectura.
- **No escribe el `.env`.** Ni para agregar una variable nueva: la nombra y la tenés que
  copiar de `.env.example`.
- **No cachea la validación.** Cada corrida vuelve a preguntar, porque un token que venció
  a la mañana no tiene por qué seguir figurando disponible a la tarde.
