# Verificación — Integraciones, los adjuntos de Jira Cloud se bajan siguiendo una sola redirección, sin credencial

**Estado:** cerrado · **Fecha:** 25-09-2026 · **Versión:** 0.24.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó.

Los veredictos los emitió `harness-spec-refuter` el 25-09-2026, en dos pasadas:

- **Primera pasada, sobre E-01 a E-13.** Corrió `-k 18_` (297/297), `-k 19_` (165/165) y `-k 45_`
  (265/265), más sondas propias en temporales.
- **Segunda pasada, sobre E-07, E-11 y E-14.** Corrió `-k 18_` (326/326).

E-13 lo sostiene la corrida del constructor sobre el árbol final, `.\tests\Invoke-Tests.ps1`, con
exit 0.

**Resultado: 14 escenarios sostenidos, 0 contradichos, 0 sin sustento, 0 leídos.**

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | 303 a https: dos pedidos, el segundo **sin `Authorization`** | sostenido | sí | `18_integraciones.py`, `test_adj_e01_e02_…` |
| E-02 | Lo mismo con 301, 302, 307 y 308 | sostenido | sí | `test_adj_e01_e02_…` |
| E-03 | 303 a http: rechazado, un pedido, sin archivo | sostenido | sí | `test_adj_e03_…` |
| E-04 | Dos saltos: rechazado sin tercer pedido | sostenido | sí | `test_adj_e04_…` |
| E-05 | Sin `Location` o con un transporte de dos elementos: no se sigue | sostenido | sí | `test_adj_e05_…` |
| E-06 | `Location` relativo: se resuelve y se sigue sin credencial | sostenido | sí | `test_adj_e06_…` |
| E-07 | La API sigue sin redirecciones | sostenido | sí | `test_adj_e07_…` y `test_adj_e07b_…`, contra un servidor local (segunda pasada) |
| E-08 | Tope en los dos pedidos, sin truncar | sostenido | sí | `test_adj_e08_…` y E-12 |
| E-09 | El motivo llega a la evidencia de `fuentes` | sostenido | sí | `test_adj_e09_…` |
| E-10 | El motivo llega al faltante del contexto | sostenido | sí | `test_adj_e10_…` |
| E-11 | Ningún motivo, evidencia o estado escrito lleva la URL firmada | sostenido | sí | `test_adj_e11_…` y `test_adj_e11b_…` (segunda pasada) |
| E-12 | `transporte_bytes_urllib` devuelve el 303 con `Location` y lee el tope + 1 | sostenido | sí | `test_adj_e12_…`, contra un servidor local |
| E-13 | La suite sale con 0 | sostenido | no consta | `.\tests\Invoke-Tests.ps1`, corrida del constructor |
| E-14 | Una URL inválida no levanta ni fuga | sostenido | sí | `test_adj_e14_…` (segunda pasada) |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-07: el test probaba que el abridor existía, no que se usara.** Si se reemplazaba
   `_abridor().open` por `urlopen`, el archivo seguía en verde, porque el doble no devuelve
   `Location`. Ahora hay un test contra un servidor local que redirige: el servidor tiene que ver
   un solo pedido.
2. **E-11: nadie miraba lo que se escribe a disco.** Ahora el estado de fuentes escrito y la salida
   del contexto se revisan después de tres descargas fallidas.
3. **Un traceback que llevaba la URL firmada, fuera de los escenarios.** Si el `Location` trae un
   espacio o un carácter de control, `http.client` levanta `InvalidURL` con el camino y la query en
   el mensaje. Nada lo atrapaba y terminaba en un traceback con el token. Pasó a ser E-14 y se
   corrigió: `pedir` y `pedir_bytes` lo convierten en el error `url`.
4. **Lo central se sostiene por todos los caminos que probó el refutador.** El segundo pedido va sin
   credencial, también con un `Location` relativo al mismo host. El tope no se esquiva, ni truncando.

## Lo que queda abierto, anotado y no escondido

Nada nuevo. La descarga real contra Jira Cloud se va a confirmar con la primera corrida de
`fuentes APPLICDCON-1` en 0.24.0, como dice «Dónde seguir» de la nota de la versión.

## Lo que ningún test cubre y se mira con los ojos

Hay que correr `fuentes APPLICDCON-1` contra el Jira Cloud real y ver bajar los cinco adjuntos, cada
uno con el `size` que declara el issue.
