# La evidencia cruda de la verificación

Son las salidas que dejó `harness-spec-refuter`, en la parte 2 de la verificación del 03-10-2026,
al reproducir los escenarios por su cuenta. El veredicto y su lectura están en
[../verificacion.md](../verificacion.md). Estos archivos son lo que lo respalda, tal como salió,
sin editar.

Los scripts que las produjeron no están: corrían en un temporal de la sesión, y sus rutas no existen
fuera de esa máquina. Las rutas absolutas que aparecen en las salidas apuntan a ese temporal.

| Archivo | Qué muestra | Escenarios |
|---|---|---|
| `rr_out.txt` | La regla de lectura de un plan guardado: los casos aceptados y los rechazados, con su código de salida y su mensaje | E-16, E-16b, E-16c, E-22 |
| `rr2_out.txt` | La atomicidad del rechazo: las huellas del plan, de `refutaciones/<KEY>/` y de `cache/` antes y después de cada rechazo | E-16b, E-16c |
| `inv_out.txt` | Los invariantes del plan: ids repetidos, dominio fuera del plan y las combinaciones de estados | E-15, E-18 a E-21 |
| `keys_out.txt` | Las claves: TaskKey en `contexto`, `refute`, `seguridad` y `plan`, y la LedgerKey en `contabilidad` y en la `statusLine` | E-25 a E-28 |
| `jira_out.txt` | Jira devolviendo otra clave | E-29 |
| `ref_out.txt` | La refutación contra la línea de base: unidades, caminos de resolución, veredictos, `run.json` y `cacheKey` | E-31 a E-33 |
| `acc_out.txt` | La contabilidad contra la línea de base: el schema y los `eventId` | E-43 |
| `e44_out.txt` | El plan de la fábrica contra el del proyecto instalado, con `4c6f0f3` y con el árbol nuevo | E-44 |
| `e45a_out.txt`, `e45b_out.txt` | Un proyecto instalado con `4c6f0f3`, actualizado con el instalador nuevo | E-45 |
| `run63-mut.txt` | El test 63 adaptado, corrido sobre una copia con un archivo no autorizado mutado: falla en E-16 | adaptación del test de `harness-unico` |
| `rv-m1.txt`, `rv-m2.txt`, `rv-m3.txt` | Las mutaciones que repitió el refutador para el rojo visto | E-16b, E-31, E-17 |
| `gate.out`, `gate.exit` | La compuerta entera, corrida por el refutador al final y sola: 39206/39206, exit 0 | E-49 |

📌 **Una línea de `e45b_out.txt` dice `same units ... as before -Update: False`, y es lo esperado.**
Compara las unidades recompiladas después del `-Update` con las que había antes, y los
`declaredChecks` cambiaron a propósito: ya no llevan los checks del hook (E-31). La comparación que
sostiene E-45 es otra. El refutador recompiló el mismo estado con el código de `4c6f0f3` en una copia
de control, y dio unidades, veredictos, `run.json` y caché idénticos. Esa salida no quedó en un
archivo, y su resultado está en `verificacion.md`, en `## Compatibilidad`.
