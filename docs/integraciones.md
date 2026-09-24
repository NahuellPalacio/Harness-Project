# Las integraciones externas

Jira Cloud y GitLab, hoy. El harness las configura, las valida y declara qué se puede
hacer con ellas. Todavía nadie las consume: eso es el bloque siguiente.

## La pregunta que contestan

> ¿Qué integraciones tengo configuradas, cuáles funcionan y qué capacidades puedo usar?

```powershell
python .claude\harness\bin\desarrollo\dev-harness.py estado
```

```
GCBA Development Harness

Integraciones
------------------------------------------------
Jira Cloud    AVAILABLE
GitLab        AUTHENTICATION_FAILED
  El token de GitLab no fue aceptado (401). Puede estar vencido o mal copiado: generá
  uno nuevo y volvé a configurarlo.

Capacidades
------------------------------------------------
  DISABLED  gitlab.branch.read
  DISABLED  gitlab.merge_request.read
  DISABLED  gitlab.project.read
  DISABLED  gitlab.repository.read
  ENABLED   jira.attachment.read
  ENABLED   jira.issue.read
  ENABLED   jira.issue.search

Estado
------------------------------------------------
Harness GCBA ◐ PARCIAL · Conocimiento VIGENCIA SIN VERIFICAR · Jira DISPONIBLE · GitLab SIN CONFIGURAR
```

La última sección es el estado general, el mismo que muestra cada sesión al arrancar: no una
palabra fija. Con una integración caída dice `PARCIAL` y la nombra, y nunca "listo". **Una
integración que no anda deshabilita sus capacidades y nada más:** el comando sale con código 0.
`dev-harness.py harness` muestra el mismo estado con el detalle, sin volver a consultar nada.

## Configurar, la primera vez

```powershell
python .claude\harness\bin\desarrollo\dev-harness.py setup
```

Pregunta solo lo que falta. La base URL y el usuario se escriben en
`.claude/harness.integraciones.json`; el token se pide sin eco y se guarda en el `.env`.

Para cambiar uno solo, después:

```powershell
python .claude\harness\bin\desarrollo\dev-harness.py reconfigurar gitlab
```

Qué tokens hacen falta:

| Integración | Dónde se saca el token | Qué alcanza |
|---|---|---|
| Jira Cloud | `id.atlassian.com` → Security → API tokens | El token va con tu email: el harness arma el Basic |
| GitLab | Preferences → Access Tokens | Scope `read_api`. Con `read_repository` solo queda `gitlab.repository.read` |

> 🔴 **El token no se pasa por la línea de comandos.** `--token` existe para rechazarlo:
> un argumento queda en el historial del shell, en la lista de procesos, en la
> transcripción de la sesión de Claude Code y en el texto que mira el hook de secretos.

## Dónde vive cada cosa

| Archivo | Qué lleva | Quién lo toca |
|---|---|---|
| `.claude/harness.integraciones.json` | `enabled`, `baseUrl`, `usuario` | El setup, y vos a mano si querés |
| `.env` | Solo los `*_TOKEN` | El setup, por el almacén de secretos |
| `.claude/harness.capacidades.json` | El resultado de la última corrida | Se reescribe en cada corrida |

**La configuración no es secreta y el agente la puede leer; el `.env` no.**
`permissions.deny` le tapa a Claude `.env` y `.env.*`, el `.gitignore` lo excluye del
repositorio, y el hook de `PreToolUse` impide escribir un token literal en cualquier
archivo. Ver [secretos.md](secretos.md).

`enabled: null` en la configuración significa *todavía nadie decidió*: es lo que hace que
el setup pregunte la primera vez y no vuelva a preguntar después.

## Los cinco estados

Ninguna integración contesta con un booleano, porque "no anda" se arregla de cuatro
formas distintas.

| Estado | Qué pasó | Qué hacer |
|---|---|---|
| `NOT_CONFIGURED` | Falta la base URL, el token, o nadie la configuró | `setup` |
| `AUTHENTICATION_FAILED` | 401: el token no fue aceptado | Generar uno nuevo y `reconfigurar` |
| `PERMISSION_DENIED` | 403: el token sirve, los permisos no alcanzan | Pedir los permisos de lectura que falten |
| `CONNECTION_FAILED` | Timeout, DNS, TLS, 5xx o una URL que redirige | Revisar la red, la VPN o la `baseUrl` |
| `AVAILABLE` | Contestó | Nada |

El mensaje sale de un diccionario fijo del código y **nunca** del cuerpo de la respuesta:
un servidor puede devolver la credencial que recibió adentro de un mensaje de error.

## Soportada no es lo mismo que disponible

```
soportada   el harness sabe hacerlo       -> capacidadesSoportadas, en el manifiesto
disponible  además está validado ahora    -> harness.capacidades.json, ENABLED
```

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
`capacidadesSoportadas` del manifiesto —hay un test que compara las dos listas—, su
variable al `.env.example` y su bloque a `integraciones.plantilla.json`.

`OPENSHIFT_TOKEN` sigue en el `.env` sin adapter a propósito: es la prueba de que sumar
el tercero no obliga a tocar el núcleo.

## Lo que este bloque no hace

- **No escribe nada en ningún sistema externo.** Todas las capacidades son de lectura.
- **No resuelve tickets, ni arma contexto, ni le entrega tools a un agente.** El registro
  de capacidades es el insumo de eso, no eso.
- **No cachea la validación.** Cada corrida vuelve a preguntar, porque un token que venció
  a la mañana no tiene por qué seguir figurando disponible a la tarde.
