---
name: dev-api
description: Use when designing, documenting or reviewing an HTTP endpoint or REST API for a GCBA / DGISIS project — route naming and versioning, request and response shape, JSON keys, pagination, status codes, the error body, Content-Type and encoding headers, CORS, mock data — or when writing, reviewing or filling in an OpenAPI/Swagger or RAML contract, a swagger.yaml, an .raml file, or the endpoint list of an API's documentation.
---

# Diseñar y documentar una API

Todo lo que sigue sale del **ES0903 — Estándar de Desarrollo API v2.2** (ASI, enero 2026).
Aplica a **todas las APIs del GCABA** y el cumplimiento es total: si un proyecto necesita
apartarse de algún punto, **la excepción va por contrato y con aprobación de ASI**
(ES0903 pág. 3). No la decide el equipo.

Donde acá dice **"no lo fija"** no hay permiso para completar con buenas prácticas: es una
definición pendiente, se acuerda con el área y se documenta en el contrato.

## Rutas: nomenclatura y versionado

- **Una URL identifica un recurso. Sustantivos, no verbos** — la acción la dice el método
  HTTP (ES0903 pág. 4).
- **Plural siempre**, por consistencia; nunca singular (ES0903 pág. 4). `/articulo` figura
  como ejemplo NO válido (ES0903 pág. 5).
- **La versión va en la URL y no es opcional: no se debe aceptar ninguna petición que no
  especifique el número de versión** (ES0903 pág. 4). En la URL va **solo la versión mayor**,
  y esa URL cambia cuando cambia el contrato (ES0903 pág. 4).
- **Anidamiento máximo `resource/identifier/resource`** — "no se debe necesitar ir más allá"
  (ES0903 pág. 4); el techo es `POST /api/v1/articulos/1234/comentarios` (ES0903 pág. 5).
- **Los filtros van en el query string**: `?year=2016&sort=desc` es válido,
  `/articulos/2016/desc` figura como NO válido (ES0903 pág. 5). **Campos opcionales, en lista
  separada por comas** (ES0903 pág. 4).
- **No traducir al español lo que DEBE estar en inglés** (ES0903 pág. 4): alcanza a los query
  params —`year`, `sort`, `filter`, `page`, `limit`— y a sus valores —`asc`, `desc`, códigos
  de estado, categorías predefinidas—; `?anio=2016&orden=desc` es el ejemplo explícito de lo
  inválido. El estándar **no fija** el idioma del recurso: sus ejemplos usan `articulos`,
  `comentarios`, `dni` (ES0903 pág. 5, 9).

El check `dev-api-rutas` marca solo tres cosas —ruta sin versión, verbo en la ruta, colección
en singular—; el resto de esta skill no lo ve ninguna máquina.

## Verbos HTTP

Se usan **en cumplimiento de sus definiciones de la norma HTTP/1.1** (ES0903 pág. 5).

| | POST (CREATE) | GET (READ) | PUT/PATCH (UPDATE) | DELETE |
|---|---|---|---|---|
| `/articulos` | Crea nuevo artículo | Lista de artículos | Error | Elimina todos los artículos |
| `/articulos/1234` | Error | Muestra artículo 1234 | Si existe, actualiza; si no, error | Borra 1234 |

El documento la presenta como **ejemplo, no como norma cerrada**: "se comparte un ejemplo...
en un contexto particular" (ES0903 pág. 5). Si una celda es load-bearing —el `DELETE` sobre
la colección, típicamente—, verificala contra el PDF.

## Content-Type y codificación

- **UTF-8 obligatorio**, y "esperar caracteres acentuados o comillas en la salida de la API,
  aun cuando no se esperen" (ES0903 pág. 8).
- **Una API que retorna JSON DEBE usar `Content-Type: application/json; charset=utf-8`**
  (ES0903 pág. 8). El `charset` es cómo la API le informa al cliente que espere UTF-8.
- El formato de respuesta lo indica el header `content-type`, **JSON por defecto**; para XML,
  `Content-Type: application/xml` (ES0903 pág. 4).

## Forma del response

- **La respuesta DEBE ser un objeto JSON, no un array** (ES0903 pág. 5): un array de primer
  nivel no deja lugar a la metadata ni a agregar *top-level keys* después.
- **Claves predecibles**: parsear claves impredecibles "es difícil y genera malestar a los
  clientes" (ES0903 pág. 5). Y **no incluir valores en las claves** (ES0903 pág. 6) — válido
  `"tags": [ {"id": "125", "name": "Ciudadano"} ]`, NO válido `"tags": [ {"125": "Ciudadano"} ]`.
- **Claves con guión_bajo, no camelCase** (ES0903 pág. 5) — **pero los ejemplos del propio
  documento la violan**; ver contradicción 2.
- **La metadata solo lleva propiedades directas de la respuesta**, no propiedades
  relacionadas a la información de la respuesta (ES0903 pág. 6).
- **Fechas ISO 8601 en UTC** (ES0903 pág. 6): solo fecha `2016-01-27`, fecha completa
  `2016-01-27T10:00:00Z`.
- El documento deja abierta la nota editorial "Rever estándar Json**" sin nota al pie asociada
  (ES0903 pág. 5): no hay un segundo estándar JSON que buscar.

## Paginación y metadata

- **`limit` y `offset`**: `offset=50` es "evitar los primeros 50 registros" y `limit=25`
  "retornar un máximo de 25" (ES0903 pág. 9); para los registros 51 a 75, `?limit=25&offset=50`.
- **Si el límite no viene, se retorna un valor por defecto** (ES0903 pág. 9). El estándar
  **no fija cuál**: se acuerda y se documenta.
- **Los límites de registros y totales disponibles DEBEN incluirse en la respuesta**
  (ES0903 pág. 9), con esta forma (ES0903 pág. 9-10):

```json
{
  "metadata": { "resultset": { "count": 225874, "offset": 25, "limit": 25 } },
  "results": []
}
```

- **El recurso individual va sin envoltorio**: `GET /articulos/[id]` devuelve el objeto plano,
  sin `metadata` ni `results` (ES0903 pág. 10). El envoltorio es de la colección.
- `POST /articulos/[id]/comentarios`: el documento muestra el request y **no muestra la
  respuesta ni indica el código de estado esperado** (ES0903 pág. 10).

## Códigos de estado

- **Los tres del estándar**: `200 - OK` (éxito), `400 - Bad Request` (problema del cliente),
  `500 - Internal Server Error` (problema del servidor) (ES0903 pág. 7).
- La sección 10.1 publica el **listado completo 1×× a 5××** sin indicar cuáles son de uso
  obligatorio ni en qué caso aplica cada uno (ES0903 pág. 7-8): es una enumeración enlazada,
  sin semántica agregada, y **no incluye 410 Gone**. Antes de responder un 201, un 401 o un
  404, leé la contradicción 3.

## Forma del error

**Las respuestas de error DEBEN incluir** el código de estado HTTP, mensaje para el
desarrollador, mensaje para el usuario final, código de error interno y enlaces con más info
para los desarrolladores (ES0903 pág. 6). Los cinco. El ejemplo del documento, transcripto
tal como está publicado (ES0903 pág. 6-7):

```json
{
    "status": 400,
    "developerMessage": "Detallar una descripción clara del problema. Proveer a los desarrolladores sugerencias de cómo resolver sus problemas.",
    "userMessage": "Este es el mensaje para el usuario final.",
    "errorCode": "444444",
    "moreInfo": "http://www.ejemplo.gob.ar/developer/path/to/help/for/444444, http://drupal.org/node/444444",
}
```

⚠️ Tres avisos sobre ese bloque, que va sin sanear: **lleva una coma final antes de la llave de
cierre** y eso lo vuelve JSON inválido (ES0903 pág. 6-7) — si lo copiás, sacala; **`moreInfo`
trae dos URLs dentro de un mismo string**, así impreso en el PDF; y **cuatro de sus cinco
claves son camelCase** —`developerMessage`, `userMessage`, `errorCode`, `moreInfo`— contra la
regla de guión_bajo de la pág. 5 (ver contradicción 2). `status` es una palabra sola y no
viola la convención.

## Contrato OpenAPI / RAML y documentación

- **Todas las APIs deben contar con documentación clara, accesible, actualizada y centrada en
  el consumidor** (ES0903 pág. 12), armada en `https://repositorio-ce-asi.buenosaires.gob.ar/`
  (ES0903 pág. 4). Herramientas **sugeridas**: Swagger y RAML (ES0903 pág. 4, 13, 14) — el
  cuerpo del texto **no impone** una de las dos ni fija versión de OpenAPI/RAML.
- **Mínimos** (ES0903 pág. 12-13): nombre de la API · descripción de su propósito · versión
  actual y anteriores cuando aplique · contacto (mail) · `environment` para cada ambiente
  (dev, test, prod) · autenticación requerida con sus mecanismos. **Con tokens dinámicos, la
  vigencia no puede superar los 15 minutos** (ES0903 pág. 12), único umbral numérico.
- **Por cada endpoint** (ES0903 pág. 12-13): método HTTP · ruta (`/usuarios/{id}`) ·
  descripción funcional · parámetros de entrada (query, path, header, body) · ejemplo de
  request · ejemplo de response con posibles códigos de estado · definiciones de errores.
- **Esquemas de datos (models)** (ES0903 pág. 13): campos requeridos · tipos de datos ·
  validaciones · relación entre objetos.
- **Versionado de la documentación** (ES0903 pág. 9): nunca liberar una versión sin su número
  · tres niveles `X.Y.Z` —X ante cambio incompatible, Y ante funcionalidad nueva compatible, Z
  ante arreglos— · prefijo `v` · soporte de al menos una versión anterior a la actual. Válido:
  `v1.0.0`, `v2.1.0`, `v3.5.0`. No válido: `v-1.1.0`.

⚠️ **El documento versiona dos objetos distintos** —la URL, solo versión mayor (pág. 4), y la
documentación, `X.Y.Z` (pág. 9)— y **no dice cómo se relacionan**: no asumas que `v1` de la
ruta es `v1.y.z` del contrato. Y **no hay plantilla completa de contrato para copiar**: las dos
que trae el ES0903 están truncadas en el propio PDF (ver abajo).

## Mock, transporte y CORS

- **Cada recurso debe aceptar un parámetro `mock` en el servidor de prueba** y devolver datos
  simulados sin pasar por el backend, implementado en la primera etapa del desarrollo; **en
  producción, `mock` debe mostrar un error** (ES0903 pág. 11) — el estándar **no fija** qué
  código de estado ni qué mensaje.
- **HTTPS (TLS/SSL) obligatorio**, con cifrado que soporte *forward secrecy* y HSTS, y las
  peticiones CORS también por HTTPS para no ser bloqueadas como contenido mixto
  (ES0903 pág. 11). En APIs existentes sobre HTTP el primer paso es agregar HTTPS y actualizar
  la doc; cortar o redirigir HTTP queda como **"evaluar la posibilidad"**, no como obligación.
- **CORS DEBE estar habilitado** para que un front consuma la API (ES0903 pág. 12) — con la
  salvedad de la contradicción 6.
- **Identificación de la aplicación cliente**: el estándar enumera `client_id` y
  `client_secret`, `OpenID`, y `app_id` y `app-key` (ES0903 pág. 11), y **no indica cuál usar
  en qué caso ni cuál prefiere**. El *rate limiting* aparece como posibilidad ("se puede
  aplicar"), sin umbral.

## Lo que hay que ir a buscar al PDF

- **Plantilla de contrato OpenAPI/Swagger — PDF pág. 13.** Captura de pantalla sin capa de
  texto **y recortada por el borde**: se corta a mitad, en `components: securitySchemes:`.
  Del render se leen `openapi: 3.0.0`, `version: v1.0.0`, el bloque `info` (title,
  description, termsOfService, contact, license) y tres `servers` (dev/test/prod). **El
  ejemplo completo no existe en el documento**: abrir el PDF ayuda y aun así queda incompleto.
  No prometas "la plantilla del estándar", porque no está entera.
- **Plantilla de contrato RAML — PDF pág. 14.** Idem: captura sin capa de texto, truncada en
  `apiKeyAuth: type: API Key description: |`. Se leen `#%RAML 1.0`, `version: v1.0`,
  `baseUriParameters.environment` con `enum` de tres entornos y `securitySchemes` con
  `bearerAuth` (OAuth 2.0, JWT) y `apiKeyAuth`. También incompleta en el propio PDF.
- **Objetivos de la sección 3 "Requisitos" — PDF pág. 3.** Existen solo dentro de una imagen
  sin capa de texto: cinco nodos alrededor de un centro "APIs" —Calidad, Seguridad,
  Productividad, Desempeño, Homogenización— **sin definición ni redacción normativa**. No
  citarlos como lista normativa sin abrir el PDF.
- **Celdas de la tabla de verbos — PDF pág. 5.** La tabla de arriba está transcrita del PDF
  maquetado; la conversión a texto plano mezcla las columnas. Si una celda es load-bearing,
  verificala contra la página.
- **Valores de ejemplo de `client_id` / `client_secret` — PDF pág. 11.** Impresos en el
  ejemplo de la API de Infracciones; no se reproducen acá: no se copian credenciales al repo,
  aunque sean de ejemplo.

## Contradicciones sin resolver

Registradas, no resueltas. **Elegir un lado en silencio es inventar una norma**: si tu diseño
depende de una de estas, preguntá antes de construir.

1. **La misma URL es ejemplo válido y ejemplo NO válido (pág. 5).** Lado A, entre los válidos:
   "Obtener un artículo en formato JSON: `GET .../api/v1/articulos/1234`". Lado B, doce líneas
   más abajo, entre los NO válidos y bajo el rótulo "Formato de número de versión": la misma
   URL exacta, sin explicación de qué tiene de mal.
2. **camelCase vs guión_bajo (pág. 5 contra pág. 6-7 y 10).** Lado A, la regla: "JSON usa
   *guión_bajo*, no *camelCase*". Lado B, los ejemplos: el error usa `developerMessage`,
   `userMessage`, `errorCode`, `moreInfo`, y las respuestas usan `userId` y `postId`. **El
   formato de error que exige la sección 10 viola la convención de claves de la sección 8.**
3. **"3 simples códigos de respuesta" vs el listado completo.** Lado A (pág. 7): usar 200,
   400 y 500. Lado B: la sección 10.1 publica cerca de 60 códigos sin marcarlos como
   prohibidos ni excepcionales (pág. 7-8), y la sección 18 exige documentar "posibles códigos
   de estado (200, 400, 401, etc.)" (pág. 13), donde 401 no está entre los tres.
4. **`/v1/...` vs `/api/v2/...` (pág. 4).** La misma lista da las dos formas —
   "`http://ejemplo.gob.ar/v1/path/to/resource`" y "el formato puede ser:
   `api/v2/resource/{id}`"— sin indicar cuál prevalece.
5. **Versionado de la doc: enteros vs tres niveles (pág. 9).** Lado A: "expresadas en números
   enteros, no decimales, con el prefijo 'v'" y "se incrementan en 1, comenzando en 1". Lado
   B, misma página: "Válido: v1.0.0, v2.1.0, v3.5.0" — tres niveles, con componentes en `0`.
6. **CORS permisivo vs restrictivo (pág. 12).** Lado A: "habilitar CORS es tan simple como
   incluir esta cabecera HTTP en todas las respuestas: `Access-Control-Allow-Origin: *`". Lado
   B, cierre de la misma sección: "es importante utilizar el CORS solo en casos especiales y
   configurarlo de la manera más restrictiva posible".
7. **Título del documento (menor, editorial).** Portada (pág. 1): "Estándar de Desarrollo
   API". Pie de todas las páginas (pág. 3-14): "Estándar de Desarrollo de APIs".
