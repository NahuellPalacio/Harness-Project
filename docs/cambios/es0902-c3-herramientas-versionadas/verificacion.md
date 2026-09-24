# Verificación — ES0902 C3: las herramientas versionadas y autorizadas, con los controles de G1 y la línea base viva

**Estado:** cerrado · **Fecha:** 23-09-2026 · **Versión:** 0.20.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 23-09-2026
en **cinco pases**. Los cuatro primeros corrieron `python tests/correr.py -k 43_es0902` y la
compuerta completa `.\tests\Invoke-Tests.ps1`; el quinto, sobre E-16 sólo, corrió el archivo 43, y
la compuerta la corrió en paralelo quien construyó: `29058/29058`.

**Resultado: 40 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

## Los veredictos

Todos los tests están en `tests/casos/43_es0902_c3_herramientas_versionadas.py`.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | La clave es `ES0902.C3`, en la matriz y en el resultado | sostenido | sí | `test_e01_la_clave` |
| E-02 | C3 sigue `ALWAYS` | sostenido | sí | `test_e02_always` |
| E-03 | C3 tiene cero señales | sostenido | sí | `test_e03_cero_senales` |
| E-04 | Los agentes son exactamente `dev-architecture` y `dev-security` | sostenido | sí | `test_e04_agentes` |
| E-05 | Las dos policies son exactamente `approved-technology-required` y… | sostenido | sí | `test_e05_policies` |
| E-06 | Los dos checks son exactamente `technology-homologation` y `technology-version-compliance` | sostenido | sí | `test_e06_checks` |
| E-07 | Cero reviews | sostenido | sí | `test_e07_cero_reviews` |
| E-08 | Ningún agente ni skill nuevos | sostenido | sí | `test_e08_ningun_agente_ni_skill` |
| E-09 | Hay un solo catálogo de tecnologías en `reglas/`, el del Anexo II | sostenido | sí | `test_e09_un_solo_catalogo` |
| E-10 | No hay un segundo inventario | sostenido | sí | `test_e10_un_solo_inventario` |
| E-11 | No hay un segundo comparador | sostenido | sí | `test_e11_un_solo_comparador` |
| E-12 | Las policies de G1 se reusan | sostenido | sí | `test_e12_las_policies_de_g1` |
| E-13 | Los checks de G1 se reusan | sostenido | sí | `test_e13_los_checks_de_g1` |
| E-14 | Los cuatro controles declaran `ES0901.G1` y `ES0902.C3` entre sus fuentes | sostenido | sí | `test_e14_las_dos_fuentes` |
| E-15 | ES0901 6.3 cargado y el catálogo de 6.3 resuelven | sostenido | sí | `test_e15_resuelve` |
| E-16 | Sin un ES0901 cargado, con dos cargados y ninguno o dos `CURRENT`, con una fuente que… | sostenido | sí | `test_e16_sin_resolver` |
| E-17 | ES0901 6.4 vigente y el catálogo de 6.3 | sostenido | sí | `test_e17_desfase_de_version` |
| E-18 | Un catálogo de otro estándar, o con un `status` de otra versión, es… | sostenido | sí | `test_e18_otro_estandar` |
| E-19 | Sin catálogo, o ilegible, `TECHNOLOGY_CATALOG_UNAVAILABLE` | sostenido | sí | `test_e19_sin_catalogo` |
| E-20 | Un control compartido no instalado o sin archivo, `SHARED_TECHNOLOGY_CONTROL_UNAVAILABLE` | sostenido | sí | `test_e20_sin_control` |
| E-21 | Sin inventario, o vacío, C3 queda `UNRESOLVED` con `TECHNOLOGY_INVENTORY_UNAVAILABLE`,… | sostenido | sí | `test_e21_sin_inventario` |
| E-22 | Con la misma evidencia, `technology-homologation` corre una vez por tecnología aunque… | sostenido | sí | `test_e22_homologacion_una_vez` |
| E-23 | Lo mismo para `technology-version-compliance` | sostenido | sí | `test_e23_version_una_vez` |
| E-24 | El resultado de G1 no se copia en C3 | sostenido | sí | `test_e24_g1_no_se_copia` |
| E-25 | C3 se agrega de los resultados compartidos | sostenido | sí | `test_e25_c3_sale_de_los_compartidos` |
| E-26 | La misma evidencia da el mismo resultado, en cualquier orden del inventario | sostenido | sí | `test_e26_determinismo` |
| E-27 | Una versión homologada sale `HOMOLOGATED` y la regla `COMPLIANT` | sostenido | sí | `test_e27_homologada` |
| E-28 | Una deprecada sale `DEPRECATED_TOLERATED`, no `HOMOLOGATED`, y la regla… | sostenido | sí | `test_e28_deprecada` |
| E-29 | Una rama más nueva no se autoriza | sostenido | sí | `test_e29_mas_nueva` |
| E-30 | Una tecnología principal que no figura sigue en `ASI_EVALUATION_REQUIRED` | sostenido | sí | `test_e30_no_figura` |
| E-31 | Una auxiliar de toolchain sigue en `TOOLCHAIN_AUXILIARY_REVIEW` | sostenido | sí | `test_e31_auxiliar` |
| E-32 | Keycloak y OpenID Connect sin evidencia del proveedor siguen en… | sostenido | sí | `test_e32_version_del_proveedor` |
| E-33 | Una versión que depende del framework sigue pidiendo su contexto | sostenido | sí | `test_e33_contexto_de_framework` |
| E-34 | C3 conforme no pone a C2 en cumplimiento | sostenido | sí | `test_e34_no_es_c2` |
| E-35 | Ni a Vu7 | sostenido | sí | `test_e35_no_es_vu7` |
| E-36 | Ni a Vu10 | sostenido | sí | `test_e36_no_es_vu10` |
| E-37 | Ni a G2 | sostenido | sí | `test_e37_no_es_g2` |
| E-38 | C3 no escanea vulnerabilidades | sostenido | sí | `test_e38_no_escanea` |
| E-39 | El resultado de C3 conserva `ES0902 / 6.2 / §3 / C3` por todos los caminos, y la… | sostenido | sí | `test_e39_la_traza_de_c3` |
| E-40 | Los controles reusados conservan a la vez `ES0901 / 6.3 / 7.1 / G1` | sostenido | sí | `test_e40_la_traza_de_g1` |
> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Los cuarenta llevan `sí`:
> la pasada de mutaciones se corrió entera en la construcción, con `__pycache__` borrado antes y
> después de cada una, y cada corrección de los pases siguientes se volvió a ver en rojo con la
> suya. E-08 no se puso en rojo en la primera pasada —su test sólo contaba agentes y directorios—
> y se reforzó antes del primer veredicto.

La compuerta, al cierre:

```
.\tests\Invoke-Tests.ps1
  250/250 pasaron (PowerShell)
  28808/28808 pasaron (python), de los cuales 199 son 43_es0902_c3_herramientas_versionadas
  29058/29058 pasaron
```

## Los cinco pases

```
pase 1   40 escenarios   E-13, E-21 y E-24 contradichos, una sola causa
pase 2   6 escenarios    sostenidos; tres entradas más que dejaban aprobar contra otro catálogo
pase 3   E-16 E-17       E-16 contradicho
pase 4   E-16            E-16 contradicho
pase 5   E-16            sostenido
```

| Pase | Qué encontró | Qué se hizo |
|---|---|---|
| 1 | `regla_c3` tomaba como verdad la línea base y los resultados compartidos que llegaban **en la evidencia**: con `{"status": "RESOLVED"}` forjado aprobaba con la instalada desfasada, y con compartidos forjados aprobaba sin inventario o pisando uno real. Y cuatro de la misma clase: la línea base con fuentes ilegibles o reemplazadas, filas a medias, excepciones, la unidad sin filtrar | Lo que llega en la evidencia sólo puede restringir; los compartidos de la evidencia no se leen; todo lo ilegible deja sin resolver |
| 2 | Un ES0901 vigente sin cargar no bloqueaba; una fuente con el id mal escrito se descartaba; la puerta miraba un catálogo y la ejecución otro | Los tres bloquean |
| 3 | Un id vacío, o `ES0901` en ancho completo | **Regla que cierra la clase**: id de texto no vacío, y un id canónico que contiene `ES0901` sin serlo bloquea |
| 4 | Una tilde combinada sobre la `E`: NFKC la componía con la letra antes de filtrar | NFKD y sólo letras y números; vacío es vacío en su forma canónica |
| 5 | —sostenido— | — |

## Lo que la verificación encontró y no habría encontrado un test verde

1. **Que la evidencia era una puerta trasera.** El resolvedor y la ejecución compartida estaban
   bien; lo que los salteaba era aceptar su resultado ya hecho por la evidencia. Los tests del
   constructor pasaban siempre la base honesta.
2. **Tres formas de aprobar contra un catálogo reemplazado** —la vigente sin cargar, el id mal
   escrito, el catálogo cambiado por la API—, que es exactamente lo que C3 existe para impedir.
3. **Que "escrito de otra forma" tiene una implementación que depende del orden de las
   normalizaciones Unicode.**

## Lo que queda abierto, anotado y no escondido

En `Pendientes/Fix-Harness/PENDIENTES-FH.md`, en el ítem de C3:

- Identificadores que parecen `ES0901` y Unicode no los cuenta como el mismo: homoglifos, otros
  sistemas de dígitos, letras modificadoras, el relleno Hangul invisible. La misma clase que el
  resto del homoglifo de C2.
- Los resultados compartidos por la API se comparan sólo por tecnología y versión, y no registran
  contra qué catálogo corrieron. Por `seguridad.resultado` no se llega.
- `c3_para_unidad` confía en cualquier resultado que diga ser de C3; `currency: UNRESOLVED`
  explícita resuelve; las observaciones no viajan a la unidad; la carga del catálogo y de los
  checks queda fuera del `try`.
- De otra clase: `role` desconocido en G1, la caché de `_check`, las fuentes vacías sin aviso, y que
  nadie agrega G1 por separado en producción.

## Lo que ningún test cubre y se mira con los ojos

- **Que haya un inventario de tecnologías.** Nadie lo produce todavía; toda corrida real da
  `TECHNOLOGY_INVENTORY_UNAVAILABLE`.
- **Que `controles/` llegue a un proyecto instalado** (ya anotado): instalado, C3 da
  `SHARED_TECHNOLOGY_CONTROL_UNAVAILABLE`, que es el estado correcto hasta que se arregle.
