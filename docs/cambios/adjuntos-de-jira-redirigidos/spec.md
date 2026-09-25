# Integraciones — los adjuntos de Jira Cloud se bajan siguiendo una sola redirección, sin credencial

**Estado:** verificado y cerrado · **Fecha:** 25-09-2026 · **Bloque:** 1

## Qué problema resuelve

`IntegracionJira.bajar_adjunto` pide la URL `content` del adjunto
(`/rest/api/3/attachment/content/<id>`). Jira Cloud no sirve ahí el binario: contesta **303** y
redirige a una URL firmada en `api.media.atlassian.com`. El cliente, `integraciones/http.py`, no
sigue redirecciones, y eso es a propósito: así el token no viaja a otro host. El resultado es que
`bajar_adjunto` devuelve `(False, 0)` sin decir por qué.

- En `fuentes <KEY>`, todas las fuentes quedan en «el documento no se pudo bajar».
- En `contexto`, cada adjunto sale con «no se pudo bajar el adjunto …».

Ningún adjunto de Jira Cloud se baja nunca.

La evidencia real es del 25-09-2026. Los cinco adjuntos de la Ficha APPLICDCON-1 dieron 303. Fuera
del harness se probó este camino:

1. el GET con la credencial, sin seguir;
2. el `Location`, que es `https` en `api.media.atlassian.com`;
3. el GET sin `Authorization`.

Así bajaron completos, con el `size` que declara el issue.

Aparece además un segundo defecto, vecino de este. `transporte_bytes_urllib` lee con
`r.read(MAXIMO_ADJUNTO)`: un adjunto más grande que el tope se guarda **truncado sin avisar**, y se
hashea como si fuera el original.

## Qué queda afuera

- **Seguir redirecciones en las llamadas a la API.** `pedir` sigue igual. Una baseUrl que redirige
  sigue siendo `CONNECTION_FAILED`, y ese es el principio del cliente.
- **Restringir el host de destino.** Queda afuera a propósito; ver la decisión de abajo.
- **GitLab.** Su adapter no baja binarios.

## Las decisiones, y por qué

### Una función aparte, `http.descargar`, y solo la usa `bajar_adjunto`

`pedir` y `pedir_bytes` no siguen redirecciones, y así quedan. `descargar` sigue **una** y con estas
reglas:

- **Qué se sigue:** solo 301, 302, 303, 307 y 308. Un 3xx sin `Location` no se sigue.
- **A dónde:** el `Location` se resuelve contra la URL original, así que puede ser relativo. El
  destino tiene que ser `https`.
- **Con qué:** el segundo pedido va **sin ningún header**. Ni `Authorization`, ni `PRIVATE-TOKEN`,
  ni una cabecera de las que armó la integración. La URL firmada no necesita la credencial.
- **Cuántos saltos:** uno. Si el segundo pedido contesta otro 3xx, se rechaza; el reporte admitía
  un tope chico y uno alcanza para el caso real.

`descargar` pide los dos pedidos con el mismo transporte. El transporte de bytes pasa a poder
devolver `(código, bytes, cabeceras)`. Uno que devuelva `(código, bytes)` sigue andando: le faltan
las cabeceras, así que un 3xx suyo queda sin `Location` y no se sigue.

### El host de destino no se restringe

El principio que protege «no seguir redirecciones» es que **la credencial no viaje a otro host**. Si
el salto va sin ningún header, eso ya no puede pasar. Al host redirigido le llega un GET anónimo a
una URL que eligió Jira.

Una lista fija como `api.media.atlassian.com` se rompe en cuanto Atlassian mueva el servicio de
media, y no protege nada que la ausencia de credencial no proteja ya. Se descartó.

### El tope se aplica a los dos pedidos, y se detecta, no se trunca

El transporte real lee `MAXIMO_ADJUNTO + 1` bytes. Si llegan más que el tope, la descarga falla con
`ATTACHMENT_TOO_LARGE`, no se escribe nada y el motivo lo dice. Eso vale para el pedido directo y
para el redirigido.

### El motivo llega a quien llama, sin la URL firmada

`bajar_adjunto` devuelve `(ok, bytes, motivo)`. Quien llama acepta también la forma vieja de dos
elementos, porque los dobles de los tests la usan. `fuentes` y `contexto` suman el motivo a su
evidencia:

- `el documento no se pudo bajar: <motivo>`
- `no se pudo bajar el adjunto <nombre>: <motivo>`

El motivo es un texto fijo con el código. Nombra, como mucho, el **host** de la redirección, nunca
su camino ni su query, porque la URL firmada lleva un token en la query.

Si la descarga falla, no se escribe el archivo.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/bin/integraciones/http.py` | `descargar`, las cabeceras en el transporte de bytes, el tope detectado y `motivo_de_descarga` |
| `harnesses/desarrollo/bin/integraciones/jira.py` | `bajar_adjunto` usa `descargar` y devuelve el motivo |
| `harnesses/desarrollo/bin/integraciones/fuentes.py` | El motivo en la evidencia |
| `harnesses/desarrollo/bin/contexto/documentos.py` | El motivo en lo que falta |
| `tests/casos/18_integraciones.py` | Los escenarios, con un transporte de bytes que devuelve cabeceras |

## Escenarios verificables

- **E-01** — Con un 303 a una URL `https`, `bajar_adjunto` hace dos pedidos: el segundo va a esa URL
  y **sin el header `Authorization`** (el test lo afirma por nombre), el archivo queda con los bytes
  del segundo, y devuelve `ok`. · rojo visto: si
- **E-02** — Lo mismo con 301, 302, 307 y 308. · rojo visto: si
- **E-03** — Un 303 a `http` se rechaza: no hay segundo pedido, no se escribe nada, y el motivo dice
  que el destino no es https. · rojo visto: si
- **E-04** — Si el segundo pedido contesta otro 3xx, se rechaza sin tercer pedido, con el motivo de
  demasiadas redirecciones. · rojo visto: si
- **E-05** — Un 303 sin `Location`, o de un transporte que no devuelve cabeceras, se rechaza sin
  segundo pedido. · rojo visto: si
- **E-06** — Un `Location` relativo se resuelve contra la URL original y se sigue sin credencial.
  · rojo visto: si
- **E-07** — Las llamadas a la API siguen sin seguir redirecciones. Con 302 en la validación hay una
  sola llamada y `CONNECTION_FAILED`, y `transporte_urllib` sigue usando el manejador que no
  redirige. · rojo visto: si
- **E-08** — Un adjunto redirigido más grande que `MAXIMO_ADJUNTO` falla con el motivo del tope y no
  escribe nada. El pedido directo, también: nunca se guarda truncado. · rojo visto: si
- **E-09** — En `fuentes`, con un 303 a `http`, la evidencia de la fuente dice «el documento no se
  pudo bajar:» seguido del motivo. · rojo visto: si
- **E-10** — En `contexto`, el faltante del adjunto dice «no se pudo bajar el adjunto <nombre>:»
  seguido del motivo. · rojo visto: si
- **E-11** — Ningún motivo, ninguna evidencia ni ningún estado escrito contiene el camino ni la query
  de la URL redirigida: como mucho, su host. · rojo visto: si
- **E-12** — `transporte_bytes_urllib`, contra un servidor local que contesta 303, devuelve el código
  y el `Location` sin seguirlo. Contra uno que sirve más que el tope, devuelve más de
  `MAXIMO_ADJUNTO` bytes, y así el tope se puede detectar. · rojo visto: si
- **E-13** — `.\tests\Invoke-Tests.ps1` sale con 0. · rojo visto: no consta
- **E-14** — Un `Location` que `http.client` no acepta (con un espacio o un carácter de control)
  no levanta ni deja un traceback con la URL: la descarga falla con el motivo «la URL no es
  válida», sin la query. `pedir` tampoco levanta con una URL así. · rojo visto: si

## Cómo se verifica

- E-01 a E-12 van por `tests/casos/18_integraciones.py`. E-12 usa un servidor HTTP local en un hilo,
  como los tests de transporte que ya hay en ese archivo.
- E-13 es la suite.

## Riesgos conocidos

- **Solo se probó contra el falso y contra un servidor local.** La descarga real contra Jira Cloud la
  hizo el reporte, fuera del harness. La primera corrida de `fuentes APPLICDCON-1` con 0.24.0 es la
  que la confirma.
- **Un GET anónimo a un host que eligió Jira.** Si alguien controlara la respuesta de Jira, podría
  mandar el harness a pedir una URL `https` cualquiera, sin credencial. Hay tope de tamaño, no se
  ejecuta nada, y el contenido solo se hashea y se lee como documento.
