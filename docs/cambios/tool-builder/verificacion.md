# Verificación — Evolutivo del Bloque 3: `dev-tool-builder` construye tools

**Estado:** en curso · **Fecha:** 22-09-2026 · **Versión:** entra en 0.19.0 sin cerrar

Este documento registra el veredicto por escenario de quien verificó, que no es quien construyó,
según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md). Los veredictos los emitió
`harness-spec-refuter` el 22-09-2026, en una pasada, corriendo `python tests/correr.py -k 21_tools
--detallado` sobre el árbol de release de 0.19.0: `73/73 pasaron`.

**Resultado: 26 escenarios sostenidos, 0 contradichos, 0 leídos, 11 sin sustento.**

🔴 **El cambio no cierra, y no es una sorpresa.** La spec dice que 36 de los 37 escenarios pasan
por la suite, y el propio `tests/casos/21_tools.py` declara en su encabezado que esta tanda cubre
el contrato y el registro —E-01 a E-11 y E-17 a E-31— y que el resto es "de las tandas
siguientes". Las tandas siguientes no se construyeron. Ninguno de los once cae en `Qué queda
afuera`: son deuda del cambio, no algo excluido. Entra al código de 0.19.0 **declarado abierto**.

## La tabla

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Sin contrato válido no se registra, y el registro no cambia | sostenido | sí | `21_tools`, `test_e01_sin_contrato_valido_no_se_registra` |
| E-02 | `CONTRACT_INVALID` nombra el campo que falta | sostenido | sí | `21_tools` (E-02) |
| E-03 | `sideEffects` fuera del enum es inválido | sostenido | sí | `21_tools` (E-03) |
| E-04 | `riskLevel` fuera del enum es inválido | sostenido | sí | `21_tools` (E-04) |
| E-05 | `READ_ONLY` sin red ni secretos deriva `LOW` | sostenido | sí | `21_tools` (E-05) |
| E-06 | Con `networkAccess` no queda `LOW` | sostenido | sí | `21_tools` (E-06) |
| E-07 | `DESTRUCTIVE`, o mutar en producción, deriva `CRITICAL` | sostenido | sí | `21_tools` (E-07) |
| E-08 | Un riesgo declarado menor se rechaza y muestra los dos; uno mayor se respeta | sostenido | sí | `21_tools` (E-08) |
| E-09 | El tier del modelo no entra en el riesgo | sostenido | sí | `test_e09_el_tier_de_modelo_no_entra_en_el_riesgo` |
| E-10 | `PERMISSION_SCOPE_TOO_BROAD` nombra el permiso sobrante | sostenido | sí | `21_tools` (E-10) |
| E-11 | Una capacidad fuera del mapa es un hueco, no un permiso | sostenido | sí | `21_tools` (E-11) |
| E-12 | `CRITICAL` arma una aprobación de riesgo aparte y no se registra | **sin sustento** | no consta | ninguno |
| E-13 | `DESTRUCTIVE` exige aprobación humana aunque no sea `CRITICAL` | **sin sustento** | no consta | ninguno |
| E-14 | El presupuesto premium no aprueba riesgo | **sin sustento** | no consta | ninguno |
| E-15 | `HIGH` pregunta según la policy, y la de defecto pregunta | **sin sustento** | no consta | ninguno |
| E-16 | Con una aprobación de riesgo pendiente, el plan no queda `READY_FOR_EXECUTION` | **sin sustento** | no consta | ninguno |
| E-17 | `CAPABILITY_ALREADY_EXISTS`: no se construye nada | sostenido | sí | `21_tools` (E-17) |
| E-18 | Una tool seleccionable se reusa, con strategy distinta de `CREATE` | sostenido | sí | `21_tools` (E-18) |
| E-19 | `CREATE` con `alternativesEvaluated` vacío es inválido | sostenido | sí | `21_tools` (E-19) |
| E-20 | `DEPRECATED` y `RETIRED` no se seleccionan | sostenido | sí | `21_tools` (E-20) |
| E-21 | Entra `EXPERIMENTAL` o `TEMPORARY`, nunca `APPROVED` | sostenido | sí | `21_tools` (E-21) |
| E-22 | `PROMOTION_CANDIDATE` exige evidencia completa | sostenido | sí | `21_tools` (E-22) |
| E-23 | `dev-tool-builder` no da el salto a `APPROVED` | sostenido | sí | `21_tools` (E-23) |
| E-24 | Una transición fuera de la máquina de estados se rechaza con origen y destino | sostenido | sí | `21_tools` (E-24) |
| E-25 | El mismo `name@version` con otro contrato se rechaza | sostenido | sí | `21_tools` (E-25) |
| E-26 | Un cambio incompatible exige major nueva, y conviven las dos | sostenido | sí | `21_tools` (E-26) |
| E-27 | `secretsRequired` guarda el nombre, no el valor | sostenido | sí | `test_e27_el_registro_guarda_el_nombre_del_secreto` |
| E-28 | Un valor con forma de secreto se detecta con el catálogo del hook y no se escribe | sostenido | sí | `test_e28_un_valor_con_forma_de_secreto_no_se_escribe` |
| E-29 | La limpieza recorre el documento entero | sostenido | sí | `test_e29_la_limpieza_recorre_el_documento_entero` |
| E-30 | `NOT_RUN` no cuenta como `PASS` | sostenido | sí | `test_e30_not_run_no_cuenta_como_pass` |
| E-31 | Con una validación en rojo no se registra | sostenido | sí | `test_e31_con_una_validacion_en_rojo_no_se_registra` |
| E-32 | La traza de ejecución, sin secretos ni contenido sensible | **sin sustento** | no consta | ninguno |
| E-33 | `TOOL_BUILD_CAPABILITY_GAP`, sin una segunda construcción | **sin sustento** | no consta | ninguno; el estado no existe en el código |
| E-34 | `CHECK_GAP` no deriva a `dev-tool-builder` | **sin sustento** | no consta | ninguno propio; el E-24 de `agent-registry` es otra proposición |
| E-35 | El constructor no crea ni modifica policies ni checks | **sin sustento** | no consta | ninguno |
| E-36 | `agents/dev-tool-builder.md` está en inglés | **sin sustento** | no consta | ninguno; la spec lo declara determinista |
| E-37 | El agente reusa y extiende antes de crear, con permisos mínimos · verificación: lectura | **sin sustento** | no consta | no hay `lectura.md` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **Las dos compuertas de riesgo no existen.** "Qué se construye" pone en alcance la compuerta de
   riesgo en `consumo.py` y `toolApprovals` en el plan: un grep de `riesgo`, `tool` y
   `toolApprovals` sobre el código no devuelve nada. E-12 a E-16 no tienen ni test ni pieza.
2. **`TOOL_BUILD_CAPABILITY_GAP` no está implementado** (E-33).
3. **E-28 sostiene de verdad**: `registro_tools.py` importa `contexto.limpieza`, que usa el
   detector de `comun/hooks/lib/secretos.py` y no una copia.

## Lo que queda abierto, anotado y no escondido

Los once `sin sustento`. Viven en `Pendientes/Fix-Harness/PENDIENTES-FH.md`, en el ítem "The
tool-builder change is half built and its spec says so", que ya los listaba antes de esta pasada.
E-37 necesita además un `lectura.md` firmado por alguien que no lo construyó: con un solo
escenario pendiente no aplica la firma delegada de ADR-0010.

## Lo que ningún test cubre y se mira con los ojos

E-37: que `dev-tool-builder`, corriendo en una sesión real, reuse y extienda antes de crear y pida
los permisos mínimos. Es una corrida de un modelo, y la suite no la puede invocar.
