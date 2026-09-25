# Integraciones — la sonda de Jira usa una consulta acotada y sondea cada capacidad

**Estado:** verificado y cerrado · **Fecha:** 25-09-2026 · **Bloque:** 1

## Qué problema resuelve

El 25-09-2026 el harness habló por primera vez con un Jira Cloud real del organismo
(`asi-jira-cloud.atlassian.net`), con un token válido. `integraciones/jira.py`
`descubrir_capacidades()` sondea la búsqueda con esta consulta:

```
GET /rest/api/3/search/jql?jql=order+by+created+DESC&maxResults=1
```

Jira Cloud contesta **400**: «Aquí no se permiten las consultas JQL ilimitadas». La caída a
`/rest/api/3/search` solo se intenta ante 404 o 410, y ese endpoint en Cloud da **410** igual.
Además, `jira.issue.read` se declara por el resultado de esa búsqueda, que es otra capacidad.

Resultado:

- `jira.issue.read` y `jira.issue.search` quedan `DISABLED`, sin decir por qué.
- `estado` muestra `Jira Cloud AVAILABLE` con una sola capacidad.
- `fuentes <KEY>` y `contexto <KEY>` abortan, así que la Ficha de Proyecto no se puede usar por Jira.

La evidencia es la del reporte, con solo GET y el mismo token:

| Pedido | Código |
|---|---|
| `/rest/api/3/myself` | 200 |
| `/rest/api/3/search/jql?jql=order by created DESC` | 400 (JQL ilimitada) |
| `/rest/api/3/search?maxResults=0` | 410 |
| `/rest/api/3/search/jql?jql=created >= -30d order by created DESC` | 200 |
| `/rest/api/3/search/jql?jql=project = <PROYECTO>` | 200 |
| `/rest/api/3/search/jql?jql=key = <KEY>` | 200 |
| `/rest/api/3/attachment/meta` | 200 |
| `/rest/api/3/issue/<KEY>?fields=...` | 200 |

## Qué queda afuera

- **Jira Data Center o Server.** El adapter es de Jira Cloud: usa la API v3 y Basic con un API
  token. La caída a `/search` era para instancias viejas de Cloud, y hoy Cloud contesta 410 ahí.
- **GitLab.** La corrida no lo tocó y su sonda no cambia.
- **Los proxies corporativos.** Siguen siendo un riesgo abierto, y el pendiente lo sigue diciendo.

## Las decisiones, y por qué

### La sonda de búsqueda usa `created >= -30d order by created DESC`

Es la consulta verificada contra el Jira Cloud real. Otras candidatas, como `project = X` o
`key = X`, necesitan conocer un proyecto o un issue, y en el bootstrap no se conoce ninguno.

Un 200 con `issues: []` sigue contando como búsqueda disponible. Una instancia sin issues en los
últimos 30 días puede buscar igual: lo que se sondea es el permiso, no el contenido.

### No hay caída a `/search`, ni en la sonda ni en `buscar`

Un 400 de `/search/jql` es la consulta rechazada, no un endpoint inexistente, así que no se cae a
ningún lado. En Jira Cloud, `/search` contesta 410: caer ahí nunca ayuda y además tapa el código
verdadero.

Se sacan las dos caídas, la de la sonda y la de `IntegracionJira.buscar`. Un 404 o un 410 en
`/search/jql` es el diagnóstico que se muestra. Esto pisa el E-18b de
`docs/cambios/integraciones-bootstrap/spec.md`, que probaba la caída contra el transporte falso. Su
test se reemplaza por el comportamiento nuevo y nombra este cambio.

### `jira.issue.read` se sondea sola

La sonda sigue este orden:

1. **Si la búsqueda devolvió un issue**, se pide `GET /rest/api/3/issue/<KEY>?fields=summary`.
   Con 200 la capacidad está disponible; con cualquier otro código, no.
2. **Si la búsqueda falló o no devolvió ningún issue**, se pide
   `GET /rest/api/3/mypermissions?permissions=BROWSE_PROJECTS`. La capacidad está disponible solo
   si ese permiso trae `havePermission: true`.

Así, un issue que se puede leer con la búsqueda rota queda `jira.issue.read` habilitada, y
`contexto <KEY>` puede leer el ticket.

🔴 **`mypermissions` no figura en la evidencia real.** Es un endpoint documentado de la API v3 de
Cloud, pero esta corrida no lo pidió. Queda anotado en el pendiente, para confirmarlo en la próxima
corrida real.

### El diagnóstico dice por qué, sin fugar nada

El estado de la integración suma `diagnostico`: una línea por capacidad que no quedó habilitada, con
el pedido que falló y el código. Sale en `estado`, abajo de la integración.

`base.py` declara que un motivo nunca sale del cuerpo de la respuesta, porque un servidor puede
devolver adentro la credencial que recibió. Para un **400** se hace una excepción acotada, porque es
el único caso en que el cuerpo es lo que explica el rechazo. Se incluyen los `errorMessages` de Jira,
así:

- **qué entra:** solo los strings de `errorMessages`, como mucho tres;
- **qué se saca:** el token exacto, la credencial Basic en base64 y el `usuario` configurado, cada
  uno reemplazado por una marca; después pasa el catálogo de secretos del Bloque 2;
- **cuánto:** hasta 200 caracteres por mensaje.

Si el cuerpo no es JSON o no trae `errorMessages`, queda solo el texto fijo. Para cualquier otro
código, el motivo sigue siendo solo el texto fijo, como hoy.

### `buscar` rechaza una JQL sin restricción

`IntegracionJira.buscar` no sale a la red con una JQL que no tenga una cláusula antes de
`ORDER BY`. Devuelve una respuesta de error local, con código 0 y el error
`JQL_UNBOUNDED`. La única JQL que arma `contexto/`, la de la Ficha (`project = … AND issuetype = …`),
ya está acotada, y un escenario lo fija.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/bin/integraciones/jira.py` | Sonda acotada, sin caídas, `issue.read` propia, diagnóstico, `buscar` que rechaza JQL sin restricción |
| `harnesses/desarrollo/bin/integraciones/base.py` | `mensajes_de_rechazo`, `diagnostico` en `estado()`, la excepción del 400 escrita en el docstring |
| `harnesses/desarrollo/bin/integraciones/registro.py` | Guarda `diagnostico` |
| `harnesses/desarrollo/bin/dev-harness.py` | `estado` muestra el diagnóstico |
| `tests/casos/18_integraciones.py` | Un transporte que distingue la JQL, y los escenarios de abajo |

## Escenarios verificables

- **E-01** — La sonda de búsqueda pide `search/jql` con la JQL `created >= -30d order by created DESC`
  y `maxResults=1`, y ninguna llamada de la sonda lleva una JQL sin restricción. · rojo visto: si
- **E-02** — Con un transporte que contesta 400 a una JQL sin restricción y 200 a una acotada,
  `jira.issue.search` queda habilitada. · rojo visto: si
- **E-03** — Un 200 con `issues: []` deja `jira.issue.search` habilitada. · rojo visto: si
- **E-04** — Con 400 en `search/jql`, no hay ninguna llamada a `/rest/api/3/search?`,
  `jira.issue.search` queda deshabilitada, y el diagnóstico dice que Jira rechazó la consulta (400)
  con el texto de `errorMessages`. · rojo visto: si
- **E-05** — Con 404 o 410 en `search/jql`, tampoco hay llamada a `/search`, y el diagnóstico nombra
  el código. · rojo visto: si
- **E-06** — `buscar` con una JQL acotada que da 410 devuelve ese 410, sin llamar a `/search`.
  · rojo visto: si
- **E-07** — Si la búsqueda devuelve un issue, `jira.issue.read` sale de `GET /issue/<KEY>`: con 200
  queda habilitada, y con 403 queda deshabilitada aunque la búsqueda ande. · rojo visto: si
- **E-08** — Con la búsqueda rota (400) y `mypermissions` con `BROWSE_PROJECTS.havePermission: true`,
  queda `jira.issue.read` habilitada y `jira.issue.search` deshabilitada. · rojo visto: si
- **E-09** — Con la búsqueda rota y `mypermissions` en `false`, en 403 o sin JSON, `jira.issue.read`
  queda deshabilitada, con su línea de diagnóstico. · rojo visto: si
- **E-10** — Si los `errorMessages` de un 400 traen el token, la credencial Basic o el usuario, el
  diagnóstico no los contiene. Además no pasa de 200 caracteres por mensaje, y un 400 sin JSON deja
  solo el texto fijo. · rojo visto: si
- **E-11** — `dev-harness.py estado` muestra el diagnóstico en español abajo de Jira Cloud.
  · rojo visto: si
- **E-12** — `buscar` con una JQL sin restricción (`order by created DESC`, vacía o solo espacios) no
  hace ninguna llamada y devuelve el error `JQL_UNBOUNDED`. · rojo visto: si
- **E-13** — La JQL con que `contexto` busca la Ficha de Proyecto está acotada: tiene cláusula antes
  del `ORDER BY`. · rojo visto: si
- **E-14** — Con un transporte que reproduce la tabla de la corrida real, quedan habilitadas las tres
  capacidades de Jira. · rojo visto: si
- **E-15** — `.\tests\Invoke-Tests.ps1` sale con 0. · rojo visto: no consta

## Cómo se verifica

- E-01 a E-14 van por `tests/casos/18_integraciones.py`, con un transporte falso que contesta según
  la JQL decodificada y no solo según el camino.
- E-15 es la suite.

Ninguno lleva la marca de lectura: lo que sí queda para una corrida real está en los riesgos.

## Riesgos conocidos

- **`mypermissions` no se probó contra Cloud real.** Si se comporta distinto, `issue.read` solo se va
  a habilitar cuando la búsqueda devuelva un issue. El pendiente lo lista para la próxima corrida.
- **30 días es una ventana.** Una instancia que rechace `created >= -30d` por otra política va a dar
  400, pero con su motivo a la vista.
- **La excepción del 400 abre el cuerpo de la respuesta.** Está acotada, redactada y recortada, pero
  es una ruta que antes no existía.
