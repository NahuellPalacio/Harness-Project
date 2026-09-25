# Verificación — Integraciones, la sonda de Jira usa una consulta acotada y sondea cada capacidad

**Estado:** cerrado · **Fecha:** 25-09-2026 · **Versión:** 0.24.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó.

Los veredictos los emitió `harness-spec-refuter` el 25-09-2026, en dos pasadas, corriendo
`python tests/correr.py -k 18_`:

- **Primera pasada, sobre E-01 a E-15.** Dio 202/202, con mutaciones en memoria.
- **Segunda pasada, sobre E-10 y E-11.** Dio 205/205.

E-15 lo sostiene la corrida del constructor sobre el árbol final, `.\tests\Invoke-Tests.ps1`, con
exit 0.

**Resultado: 15 escenarios sostenidos, 0 contradichos, 0 sin sustento, 0 leídos.**

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | La sonda usa `created >= -30d …` y ninguna llamada es ilimitada | sostenido | sí | `18_integraciones.py`, `test_sonda_e01_…` |
| E-02 | 400 a la ilimitada, 200 a la acotada: hay búsqueda | sostenido | sí | `test_sonda_e02_e03_…` |
| E-03 | `issues: []` sigue siendo búsqueda disponible | sostenido | sí | `test_sonda_e02_e03_…` |
| E-04 | Un 400 no cae a `/search` y se explica con `errorMessages` | sostenido | sí | `test_sonda_e04_…` |
| E-05 | 404/410 tampoco caen; el diagnóstico nombra el código | sostenido | sí | `test_sonda_e05_e06_…` |
| E-06 | `buscar` devuelve el 410 sin caer | sostenido | sí | `test_sonda_e05_e06_…` |
| E-07 | `issue.read` sale de `GET /issue/<KEY>` | sostenido | sí | `test_sonda_e07_…` |
| E-08 | Con la búsqueda rota, `issue.read` por `BROWSE_PROJECTS` | sostenido | sí | `test_sonda_e08_e09_…` |
| E-09 | Permiso en false, 403 o sin JSON: sin `issue.read`, con diagnóstico | sostenido | sí | `test_sonda_e08_e09_…` |
| E-10 | El diagnóstico no fuga, y respeta el tope y el texto fijo | sostenido | sí | `test_sonda_e10_…` (segunda pasada) |
| E-11 | `estado` muestra el diagnóstico debajo de Jira Cloud | sostenido | sí | `test_sonda_e11_…` (segunda pasada) |
| E-12 | `buscar` no sale con una JQL ilimitada | sostenido | sí | `test_sonda_e12_…` |
| E-13 | La JQL de la Ficha está acotada | sostenido | sí | `test_sonda_e13_…` |
| E-14 | La tabla de la corrida real da las tres capacidades | sostenido | sí | `test_sonda_e14_…` |
| E-15 | La suite sale con 0 | sostenido | no consta | `.\tests\Invoke-Tests.ps1`, corrida del constructor |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-10: el tope de 200 caracteres no se ejercitaba.** El único mensaje largo era el cuarto, y el
   tope de tres mensajes lo descartaba antes de que llegara a recortarse. Con un tope de un millón,
   el test pasaba verde. Ahora el mensaje largo va primero.
2. **E-11: la posición del diagnóstico no se afirmaba.** El test buscaba el texto en toda la salida.
   Ahora exige que el diagnóstico aparezca entre «Jira Cloud» y «GitLab».
3. **Sin fugas del diagnóstico.** El refutador corrió `estado` y `estado --json` con `errorMessages`
   que traían el token, la credencial y el usuario, en respuestas 400 y 403. Ninguno de los tres
   aparece en la salida ni en `harness.capacidades.json`.

## Lo que queda abierto, anotado y no escondido

En `Pendientes/Fix-Harness/PENDIENTES-FH.md`, en *GitLab was never called for real, and Jira only
once*: `mypermissions` nunca contestó frente a nadie.

## Lo que ningún test cubre y se mira con los ojos

Correr `estado` contra el Jira Cloud del organismo después del `-Update` a 0.24.0, y confirmar las
tres capacidades y la respuesta de `mypermissions`.
