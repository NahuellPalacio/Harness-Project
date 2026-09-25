# Verificación — Bloque 1, una fuente oficial se puede aceptar en el proyecto

**Estado:** cerrado · **Fecha:** 25-09-2026 · **Versión:** 0.24.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó.

Los veredictos los emitió `harness-spec-refuter` el 25-09-2026, en una pasada:

- Corrió `python tests/correr.py -k 57_` y dio 159/159.
- Corrió solo el caso de instalador `57-aceptar-fuentes-instalador.ps1` y dio 26/26.
- Hizo sondas propias contra `frescura.resolver_una` en temporales.

No corrió la suite entera, a pedido del constructor, porque dos corridas a la vez pueden romper el
árbol (`03-instalador.ps1`). E-23 lo sostiene la corrida del constructor sobre el mismo árbol:
`.\tests\Invoke-Tests.ps1`, 35964/35964, exit 0.

**Resultado: 23 escenarios sostenidos, 0 contradichos, 0 sin sustento, 0 leídos.**

## La tabla

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Aceptar ES0902 6.2 deja `CURRENT` y registra la identidad | sostenido | sí | `57_aceptar_fuentes.py`, `test_e01_e02_…`, por CLI |
| E-02 | La corrida siguiente reusa la aceptación | sostenido | sí | `test_e01_e02_…` |
| E-03 | Otro byte invalida la aceptación | sostenido | sí | `test_e03_…` |
| E-04 | Otra versión invalida la aceptación | sostenido | sí | `test_e04_…` |
| E-05 | Otro adjunto invalida la aceptación | sostenido | sí | `test_e05_…`, a nivel de función (el canal archivo no tiene adjunto) |
| E-06 | Lo que no se puede aceptar sale con 2 y no escribe | sostenido | sí | `test_e06_…`; los casos sin versión y sin hash, sobre `aceptable` |
| E-07 | Sin evidencia no hay camino a `CURRENT` | sostenido | sí | `test_e07_…`; también las sondas del refutador |
| E-08 | La aceptación no tapa `SOURCE_INTEGRITY_ALERT` | sostenido | sí | `test_e08_…` |
| E-09 | Una regresión sin `--regresion` sale con 2 | sostenido | sí | `test_e09_e10_…`, por CLI |
| E-10 | Con `--regresion`: `KNOWLEDGE_PROMOTION_INCOMPLETE`, versión de fábrica visible | sostenido | sí | `test_e09_e10_…` |
| E-11 | La regresión vale solo contra la fábrica que pisó | sostenido | sí | `test_e11_…` |
| E-12 | Aceptar una posterior es promoción pendiente | sostenido | sí | `test_e12_…` |
| E-13 | Sin aceptación, igual que 0.23.0 | sostenido | sí | `test_e13_…`, contra el `dev-harness.py` de `git archive dc0d258` |
| E-14 | `POSTPONE` da `ACKNOWLEDGED_PENDING` sobre la misma identidad | sostenido | sí | `test_e14_…` |
| E-15 | `NEW_SOURCE`, y aceptada da `CURRENT` | sostenido | sí | `test_e15_…` |
| E-16 | Los seis extractos se instalan, sin avisos de faltante | sostenido | sí | `57-aceptar-fuentes-instalador.ps1` |
| E-17 | En un proyecto instalado, aceptar deja `CURRENT` | sostenido | sí | el mismo `.ps1`, con el `dev-harness.py` instalado |
| E-18 | La aceptación sobrevive a `-Update`; `-Doctor` no la marca | sostenido | sí | el mismo `.ps1` |
| E-19 | Reporte sin B-001 y con la procedencia | sostenido | sí | `test_e19_…` |
| E-20 | Sin aceptación, el reporte sigue con la condición de conocimiento | sostenido | sí | `test_e20_…` |
| E-21 | El contrato: con aceptación y el de 0.23.0 validan; una clave de más no | sostenido | sí | `test_e21_…` |
| E-22 | Salida en español; estados canónicos | sostenido | sí | `test_e22_…` |
| E-23 | La suite sale con 0 | sostenido | no consta | `.\tests\Invoke-Tests.ps1`: 35964/35964, corrida del constructor |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **No hay camino de evidencia ausente a `CURRENT`**, más allá de los casos del test. El refutador
   probó estas entradas a propósito, y ninguna dio `CURRENT` ni dejó una aceptación:
   - sin hash en los dos lados, con el hash vacío, no hexadecimal o en mayúsculas;
   - sin versión, o con `found: false`;
   - con una decisión `apply` en minúscula, o con una decisión que no es un objeto;
   - sin canal.
2. **Una versión de fábrica «6.2.0» contra «6.2» observada** da `VERSION_REGRESSION`, no `CURRENT`.
3. **`aceptable` nunca devuelve `SOURCE_CHANGED_SAME_VERSION`.** Un original con la identidad
   cambiada y sin hash se rechaza igual, pero con el código `FRESHNESS_UNVERIFIED`. Ningún escenario
   lo pide, así que no cuenta como falla.
4. **E-10 solo exige que `stale_derived` no esté vacío.** El refutador miró que son 56 derivados,
   todos con `declaredVersion` 6.3: un cálculo contra la fábrica lo dejaría vacío y el test fallaría.

## Lo que queda abierto, anotado y no escondido

En `Pendientes/Fix-Harness/PENDIENTES-FH.md`:

- **Se cierran dos pendientes:** *The six managed sources have no accepted hash…* y *`normativa/`
  never reaches an installed project…*.
- **Uno se achica:** *Four source states…* pasa a *`RETIRED` is built and no scenario refutes it*,
  porque los otros tres estados ya tienen escenario.

## Lo que ningún test cubre y se mira con los ojos

- **licba en serio.** Se hace `-Update` a 0.24.0 y después
  `fuentes --archivo <dir de la Ficha> --aceptar ES0902` con los PDF reales. ES0901 tiene que seguir
  en `VERSION_REGRESSION` hasta que la Ficha traiga la 6.3.
- **El canal Jira.** Hay que ver `fuentes APPLICDCON-1 --aceptar ES0902` contra la Ficha real. Los
  tests usan solo el canal archivo.
