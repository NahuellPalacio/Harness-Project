# Verificación — ES0902 v6.2, la línea base de seguridad como estándar propio

**Estado:** cerrado · **Fecha:** 22-09-2026 · **Versión:** 0.19.0 (sin publicar)

Este documento es lo que cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md):
el veredicto por escenario de quien verificó, que no es quien construyó. Los emitió
`harness-spec-refuter` el 22-09-2026, corriendo `python tests/correr.py -k es0902` y
`.\tests\Invoke-Tests.ps1`, y sondas propias de fuerza bruta sobre la frontera de la aprobación,
la excepción aprobada por ASI, el umbral de G2 y el resultado por regla.

**Resultado: 71 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

## La tabla

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | ES0902 6.2, 2025-08, 21 reglas; otra versión se rechaza | sostenido | sí | `37_es0902_seguridad.py`, `test_e01_…` |
| E-02 | El inventario exacto reporta el **id**, no un conteo | sostenido | sí | `test_e02_…`, falta/repetida/sobrante |
| E-03 | `ruleKey` se declara y se controla contra `ES0902.<id>` | sostenido | sí | `test_e03_…` |
| E-04 | `ES0901.G1` y `ES0902.G1` no son la misma regla | sostenido | sí | `test_e04_…` |
| E-05 | Un id fuera del inventario no se resuelve | sostenido | sí | `test_e05_…`, seis formas |
| E-06 | ES0902 no entra en la matriz de ES0901 | sostenido | sí | `test_e06_…` |
| E-07 | Los dos estándares devuelven el mismo contrato | sostenido | sí | `test_e07_…` |
| E-08 | El bloque viejo conserva su forma; `standards` se suma al lado | sostenido | sí | `test_e08_…` |
| E-09 | Toda fila conserva su traza | sostenido | sí | `test_e09_…`, las 21 |
| E-10 | Las quince señales de ES0902 quedan declaradas | sostenido | sí | `test_e10_…` |
| E-11 | Los agentes que nombra existen en el registro | sostenido | sí | `test_e11_…` |
| E-12 | Un control conserva todas sus fuentes normativas | sostenido | sí | `test_e12_…`, los seis compartidos |
| E-13 | La forma vieja `source` sigue valiendo | sostenido | sí | `test_e13_…`, los 25 sin migrar |
| E-14 | Un control compartido se declara una vez | sostenido | sí | `test_e14_…` |
| E-15 | El resultado no se propaga entre estándares | sostenido | sí | `test_e15_…` |
| E-16 | El patrón de `rule` acepta los ids de ES0902 | sostenido | sí | `test_e16_…` |
| E-17 | Un control sin fuente es inválido | sostenido | sí | `test_e17_…` |
| E-18 | La configuración local nunca exime | sostenido | sí | `test_e18_…`, las cinco fuentes locales |
| E-19 | Contrato sin ASI no exime | sostenido | sí | `test_e19_…` |
| E-20 | ASI sin contrato tampoco | sostenido | sí | `test_e20_…` |
| E-21 | Las dos mitades eximen y conservan los cuatro campos | sostenido | sí | `test_e21_…` |
| E-22 | Una excepción no derrama | sostenido | sí | `test_e22_…` |
| E-23 | Un escaneo automático no aprueba | sostenido | sí | `test_e23_…` |
| E-24 | Una review interna no aprueba | sostenido | sí | `test_e24_…` |
| E-25 | Lo oficial exige procedencia externa y evidencia | sostenido | sí | `test_e25_…` |
| E-26 | La guarda es estructural: 5 productores × 5 estados | sostenido | sí | `test_e26_…`, 25 celdas |
| E-27 | Los diez principios en PASS no mueven lo oficial | sostenido | sí | `test_e27_…` |
| E-28 | Los doce estados, y ninguno más | sostenido | sí | `test_e28_…` |
| E-29 | C2 fuera de QA no cumple | sostenido | sí | `test_e29_…` |
| E-30 | C2 cumple en QA con aprobación oficial | sostenido | sí | `test_e30_…` |
| E-31 | `READY_TO_REQUEST` exige todo resuelto | sostenido | sí | `test_e31_…` |
| E-32 | E1–E5 por tipo de activo, anclados al texto del estándar | sostenido | sí | `test_e32_…` |
| E-33 | Varios tipos dan la unión | sostenido | sí | `test_e33_…` |
| E-34 | El servicio web exige WAF | sostenido | sí | `test_e34_…` |
| E-35 | La aplicación web exige WAF | sostenido | sí | `test_e35_…` |
| E-36 | Sin plantilla, `WAF_FORM_CONTEXT_REQUIRED` bloquea | sostenido | sí | `test_e36_…` |
| E-37 | Ningún campo del formulario se inventa | sostenido | sí | `test_e37_…` |
| E-38 | Entregables faltantes con su estado | sostenido | sí | `test_e38_…` |
| E-39 | C1 reusa los controles de D2 | sostenido | sí | `test_e39_…` |
| E-40 | C1 exige evidencia de OIDC con Keycloak | sostenido | sí | `test_e40_…` |
| E-41 | D1 y C1 juntas no se reconcilian solas | sostenido | sí | `test_e41_…` |
| E-42 | No se inventa ninguna reconciliación | sostenido | sí | `test_e42_…` |
| E-43 | C3 reusa los cuatro controles de ES0901 G1 | sostenido | sí | `test_e43_…` |
| E-44 | Ve1 reusa los mismos | sostenido | sí | `test_e44_…` |
| E-45 | Ve2 exige consenso de Infraestructura | sostenido | sí | `test_e45_…` |
| E-46 | Vu1 a Vu10 son diez reglas distintas | sostenido | sí | `test_e46_…`, producto |
| E-47 | Vu2: texto plano no cumple | sostenido | sí | `test_e47_…` |
| E-48 | Vu4 es independiente del token | sostenido | sí | `test_e48_…` |
| E-49 | Vu5: sólo cliente no cumple | sostenido | sí | `test_e49_…` |
| E-50 | Vu9 no inventa ningún umbral | sostenido | sí | `test_e50_…` |
| E-51 | Vu9 acepta cualquier mecanismo con evidencia | sostenido | sí | `test_e51_…`, los siete |
| E-52 | Vu10 resuelve la guía por tipo de activo | sostenido | sí | `test_e52_…` |
| E-53 | Vu10: una referencia desconocida queda explícita | sostenido | sí | `test_e53_…` |
| E-54 | G2 con algo por encima de LOW no da | sostenido | sí | `test_e54_…` |
| E-55 | G2 con más de diez LOW no da | sostenido | sí | `test_e55_…` |
| E-56 | G2 con hasta diez LOW da | sostenido | sí | `test_e56_…`, el borde |
| E-57 | Sin mapeo autoritativo no se calcula | sostenido | sí | `test_e57_…` |
| E-58 | El umbral nunca produce aprobación | sostenido | sí | `test_e58_…` |
| E-59 | G3 exige el 100% | sostenido | sí | `test_e59_…` |
| E-60 | G3 sigue evaluando G2 | sostenido | sí | `test_e60_…` |
| E-61 | G4 exige alcance completo | sostenido | sí | `test_e61_…` |
| E-62 | G4 sigue evaluando G2 | sostenido | sí | `test_e62_…` |
| E-63 | No se crea ningún agente | sostenido | sí | `test_e63_…` |
| E-64 | Las skills de seguridad siguen siendo la capa | sostenido | sí | `test_e64_…` |
| E-65 | Los ocho estados globales, emitidos de verdad | sostenido | sí | `test_e65_…` |
| E-66 | Un estado desconocido falla cerrado | sostenido | sí | `test_e66_…` |
| E-67 | Un estándar roto no se lleva al otro | sostenido | sí | `test_e67_…`, árbol temporal |
| E-68 | Los tres módulos arrancan instalados | sostenido | sí | `test_e68_…`, árbol temporal |
| E-69 | Los módulos no tienen cómo conseguir un secreto | sostenido | sí | `test_e69_…`, por AST |
| E-70 | Lo declarado no finge estar instalado | sostenido | sí | `test_e70_…`, 20/16/2 |
| E-71 | Un id con dos tipos se reporta | sostenido | sí | `test_e71_…` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá los setenta y uno
> llevan `sí`, de **tres pasadas de mutación — 79 mutaciones entre las tres**.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **Una aserción que no podía fallar.** `E-06` tenía `... or True)` pegado al final: quedaba
   verde pasara lo que pasara. No cambiaba el veredicto —las otras aserciones del mismo test
   sostienen la proposición: las 24 filas, el `no_contiene("ES0902")` sobre el JSON entero y el
   solapamiento `["C1","C2","C3","G1","G2"]` fijado con una comparación real— pero era peso
   muerto que inflaba el conteo de 1459 y engañaba a quien lo leyera. Eliminada.

2. **Un barrido que se sostenía de casualidad.** `E-69` buscaba llamadas a `open` con
   `getattr(n.func, "attr", "")`, que ve `io.open(...)` y **no** ve un `open(...)` pelado, donde
   `n.func` es un `ast.Name` sin `attr`. Los tres módulos usan `io.open`, así que la proposición
   estaba sostenida; lo que no se sostenía era el barrido el día que alguien escribiera la forma
   corta. Ahora mira las dos formas y hay una aserción que prohíbe la pelada.

3. **`authoritative` se evaluaba por verdad y no por identidad.** `{"authoritative": "false"}`
   —el string— habilitaba el cálculo del umbral de G2 con las etiquetas crudas del escáner, que
   es exactamente lo que ese bloque existe para impedir. Pasó a `is True`, y `E-57` recorre ahora
   el string `"false"`, el string `"true"` y el entero `1`.

4. **Un número heredado que ningún test miraba.** `docs/normativa-7.1.md` decía *"ocho reglas
   están completas y dieciséis siguen con controles declarados y no construidos"*. Medido: son
   **once y trece** —G1, G2, D1 a D8 y P1 están completas—. El número era correcto cuando cerró
   D5 y quedó viejo cuando entraron D7, D8 y P1. Estaba también en la spec de este cambio.
   Corregido en los dos lugares, y ahora el documento dice **cómo recontarlo**, no sólo el número.

5. **La frontera de la aprobación resistió la fuerza bruta.** El refutador barrió 18 productores
   × 13 estados × 7 formas de evidencia contra `estado_oficial`: **ningún** estado oficial
   alcanzado por un productor que no sea externo. Y la guarda no depende de la lista de internos
   —`productor not in PRODUCTORES_EXTERNOS` sola ya alcanza—, así que un productor nuevo que
   nadie declare queda afuera por construcción.

6. **La excepción de ASI también.** Producto de las 13 fuentes en las dos mitades: conceden
   **exactamente tres pares**, todos `<fuente de contrato> + ASI_APPROVAL`. Los comodines `*`,
   `ALL`, `ES0902`, `Vu` y `""` no alcanzan ninguna regla.

## Lo que queda abierto, anotado y no escondido

Todo esto vive en `Pendientes/Fix-Harness/PENDIENTES-FH.md`, con su entrada propia.

1. **Treinta y ocho controles declarados y sin construir** —veinte policies, dieciséis checks y
   dos reviews—. Es el estado correcto y es el hueco más grande que tuvo el harness. `E-70` fija
   los conteos exactos, así que un control que aparezca mueve el número y alguien tiene que mirar.

2. **Nadie produce el mapeo autoritativo de severidades.** Toda corrida real de G2 sale
   `VULNERABILITY_RISK_MAPPING_UNRESOLVED`. El umbral está instalado y no se puede usar hasta que
   ese mapeo exista, y de dónde sale no es una pregunta de código.

3. **ES0901 P5 no existe**, así que la equivalencia con Vu5 queda
   `CROSS_STANDARD_CONTROL_BINDING_REQUIRED`. El día que P5 se implemente hay que comparar
   semántica de verdad antes de deduplicar nada.

4. **La matriz provista declara un id con dos tipos.** No se corrige acá: se reporta
   `SECURITY_CONTROL_ID_TYPE_COLLISION` y aparece dos veces en el reporte de huecos.

5. **Una colisión de nombre de señal entre estándares no está impedida.** Hoy pasa una vez y a
   propósito —`authenticationPresent`, que el paquete manda reusar—, pero una señal futura podría
   chocar con otro significado y nadie se enteraría.

6. **G2 es la única regla donde `COMPLIANT` no implica evidencia de control.** `regla_g2` decide
   por el umbral y no mira `controlResults`; es lo que `E-56` prescribe y lo que el estándar
   declara, pero conviene decirlo en voz alta porque sus dos controles son el id colisionado y
   **no están instalados**.

## Lo que ningún test cubre y se mira con los ojos

- **Que la paráfrasis operativa de la matriz sea fiel al texto de ES0902 v6.2.** Los tests
  comprueban que el archivo esté completo y coherente consigo mismo; que lo que dice corresponda
  al PDF lo tiene que leer una persona contra el estándar. Es la misma frontera que ES0901 §7.1.
- **Que la reconstrucción de `docs/normativa-7.1.md` no haya perdido nada.** El archivo se
  truncó por accidente durante este cambio y se reconstruyó contra las aserciones de los cinco
  grupos que lo leen. Todas pasan y el número que estaba mal se corrigió, pero **el texto no es
  el original** y nadie tiene el original contra el cual compararlo.
- **Que los estados del flujo correspondan al circuito real de DGSEI.** El harness modela doce
  estados y se prohíbe emitir cinco; si el circuito real tiene otros, eso se ve usándolo.
