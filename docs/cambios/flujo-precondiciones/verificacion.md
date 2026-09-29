# Verificación — Flow Governance, Wave 1 — precondiciones del flujo, identidad del repositorio y localizador de inputs

**Estado:** cerrado · **Fecha:** 29-09-2026 · **Versión:** sin release todavía (base 0.26.0)

Este documento es lo que cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md):
el veredicto por escenario de quien verificó, que no es quien construyó. Los veredictos los emitió
`harness-spec-refuter` el 29-09-2026, en dos pasadas. En la primera corrió
`tests/correr.py -k 61_flujo`, `-k 20_orquestacion`, `-k 55_refutacion`, `-k 53_context_bar` y la
compuerta entera (`.\tests\Invoke-Tests.ps1`, 37387/37387, salida 0). En la segunda volvió a correr
`-k 61_flujo` (182/182) sobre los cinco escenarios que se reforzaron después de la primera.

**Resultado: 23 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | SSH, `ssh://` y HTTPS con usuario son el mismo repositorio: `MATCHED` | sostenido | sí | `61_flujo_precondiciones.py`, `test_e01_…`, tres checkouts reales |
| E-02 | Tarea `grupo/a` en un checkout de `grupo/b`: `MISMATCH` / `REPOSITORY_MISMATCH` | sostenido | sí | `test_e02_…` |
| E-03 | Git sin remotos y carpeta sin git: `UNRESOLVED` / `LOCAL_REPOSITORY_UNRESOLVED` | sostenido | sí | `test_e03_…` |
| E-04 | Sin declaración del repositorio: `REPOSITORY_UNRESOLVED` y plan `BLOCKED` por la CLI | sostenido | sí | `test_e04_…`, por `plan` |
| E-05 | `GITLAB_PROJECT` contra la Ficha, o dos URLs en la Ficha: `REPOSITORY_CONFLICT`, no elige | sostenido | sí | `test_e05_…`, biblioteca y CLI con `.env` |
| E-06 | Un solo `HARD_BLOCKER` (o un `DERIVABLE` bloqueante) sin resolver: plan `BLOCKED` | sostenido | sí | `test_e06_…`; ver abajo, reescrito |
| E-07 | Un `SOFT_DEPENDENCY` sin resolver no bloquea solo | sostenido | sí | `test_e07_…` |
| E-08 | Agente no ruteable: unidad `BLOCKED` con `AGENT_NOT_FOUND`, sin preguntar | sostenido | sí | `test_e08_…` |
| E-09 | Aprobación pendiente: `refute --compile` sale con 2, `PLAN_NOT_READY`, sin `run.json` | sostenido | sí | `test_e09_…`, por la CLI |
| E-10 | TaskContext editado o con otro hash: `CONTEXT_STALE` | sostenido | sí | `test_e10_…`, los dos casos |
| E-11 | Otro checkout: `REPOSITORY_MISMATCH`, `run.json` ni se crea ni cambia | sostenido | sí | `test_e11_…`, byte a byte |
| E-12 | Plan reescrito después de compilar: `--unit` y `--record` dan `REFUTATION_PLAN_STALE` | sostenido | sí | `test_e12_…`, biblioteca y CLI |
| E-13 | El localizador da línea, columna, clave, formato y sensibilidad del contrato | sostenido | sí | `test_e13_…` |
| E-14 | Once campos exactos, ninguno prohibido, ningún valor del `.env` | sostenido | sí | `test_e14_…`, cinco inputs |
| E-15 | Sin la clave, la línea siguiente a la última; sin `.env`, la 1; en JSON, adentro del objeto | sostenido | sí | `test_e15_…` |
| E-16 | `vscode://file/C:/Work/app/.env:12:1`, espacios codificados, determinista | sostenido | sí | `test_e16_…` |
| E-17 | Placeholder en los seis formatos, "No pegues" para un `SECRET`, `INPUT_FORMAT_UNRESOLVED` | sostenido | sí | `test_e17_…`, `renderizar` en los seis |
| E-18 | Nadie escribe el `.env`; `bin/flujo/` no abre nada para escribir | sostenido | sí | `test_e18_…`, bytes y barrido estático |
| E-19 | `harness.integraciones.json` no es destino: `FLOW_INPUT_TARGET_NOT_HUMAN` | sostenido | sí | `test_e19_…` |
| E-20 | `.\tests\Invoke-Tests.ps1` en verde, dos motores | sostenido | no consta | la compuerta sobre el árbol final, 37405/37405 (488 PowerShell + 36917 Python), salida 0 |
| E-21 | El registro valida y el cargador rechaza cinco contradicciones | sostenido | sí | `test_e21_…` |
| E-22 | Misma entrada, mismos bytes: evaluación, identidad y ubicación | sostenido | sí | `test_e22_…`, con varias preguntas |
| E-23 | Un token en el remoto no llega a la identidad ni al plan | sostenido | sí | `test_e23_…`, `oauth2:<token>@` y contraseña con `@` |
| E-24 | Contrato de entorno, `entorno.py` y `base.py` iguales que en `6cff4b4` | sostenido | sí | `test_e24_…`, `git show` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar.

La marca `sí` de esta tabla no salió de escribir el test primero: la implementación se escribió
antes que los tests. Se ganó rompiendo el código a propósito, una mutación por escenario, corriendo
`61_flujo` y restaurando. Las 23 mutaciones dieron rojo. E-22 dio verde la primera vez, porque su
test evaluaba una sola pregunta y así el orden no podía fallar: se reforzó y ahí sí dio rojo. Las
aserciones nuevas de E-06 y E-23 que se agregaron después de la primera pasada también se vieron
fallar con su mutación antes de restaurar.

## E-06, reescrito después de quedar sin sustento

En la primera pasada E-06 quedó **sin sustento**. La spec pedía "con repositorio `MATCHED` … y un
solo input `HARD_BLOCKER` sin resolver", y el test dejaba sin resolver `planning.taskContext`, que
es `DERIVABLE`.

La precondición no se podía cumplir: los cuatro `HARD_BLOCKER` de `PLANNING` son de repositorio, y
con el repositorio `MATCHED` ninguno puede estar sin resolver. Se reescribió el escenario sin sacar
nada de lo que afirmaba: sigue exigiendo `BLOCKED` con un solo `HARD_BLOCKER` (`repository.match`) y
que un `READY` puesto a mano no cambie `estado_de`, y suma el caso `DERIVABLE`. El refutador lo
revisó como corrección y no como recorte, y en la segunda pasada lo sostuvo.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-06 no probaba lo que decía.** El test estaba verde y afirmaba otra cosa.
2. **Una contraseña con `@` sin codificar dejaba un pedazo pegado al host.**
   `https://usuario:p@ss@gitlab.example/…` daba el host `ss@gitlab.example`, que iba a parar a
   `localRepositories` en el plan escrito. `_URL` ahora toma el usuario y la contraseña hasta el
   último `@` anterior a la primera barra, y E-23 tiene el caso.
3. **El barrido estático de E-18 tenía huecos:** no veía `write_text`, `write_bytes`, `json.dump`,
   `makedirs` ni `mkdir`. Se amplió.
4. **E-17 probaba los seis formatos solo en `sintaxis()`, no en `renderizar()`**, y el caso de dos
   URLs de E-05 no afirmaba que no se elige ninguna. Se completaron los dos.

## Lo que queda abierto, anotado y no escondido

- **El test de E-06 arma un estado imposible:** su bloque `repository` dice `MATCHED` con
  `repository.match` en `False`. El escenario no depende del bloque. Queda para la limpieza de la
  Wave 6.
- **`refutacion.compilar` como biblioteca no pasa por la compuerta.** Es decisión de la spec: la
  compuerta es del comando. Se cierra por los hooks en la Wave 3.
- **`AlmacenSecretos.set` y `remove` siguen en la interfaz sin que nadie los llame.** Es decisión de
  `entorno-primero`, y se lleva a `Pendientes/Fix-Harness/PENDIENTES-FH.md` si se decide sacarlos.
- **`PlanInvalido` no se atrapa en `main`** de `dev-harness.py`. Es de antes de este cambio: un plan
  inválido termina en un traceback en vez de salir con 2.

## Lo que ningún test cubre y se mira con los ojos

- Que el enlace `vscode://file/…` que da el localizador abra de verdad el archivo en la línea, en
  VS Code sobre Windows, con una ruta con espacios.
- Que la instrucción renderizada se lea bien en el chat de Claude Code y que la persona entienda
  qué editar sin pegar el valor.
