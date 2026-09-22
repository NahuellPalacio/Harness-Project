# Verificación — G1: la primera regla de §7.1 que se puede ejecutar

**Estado:** cerrado con un contradicho documentado · **Fecha:** 22-09-2026 · **Versión:** 0.19.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el
22-09-2026, en **seis pasadas**, corriendo `python tests/correr.py -k 24_g1 --detallado`, `-k 36_p1`
y `-k 25_g2` sobre el árbol de release de 0.19.0, sin ES0902 O1 ni O2. Desde la segunda pasada, cada
una barrió en memoria todas las entradas del Anexo II que llevan calificativo, contra todas las
formas de escribirlo.

**Resultado: 25 escenarios sostenidos, 1 contradicho (E-17), 0 leídos, 0 sin sustento.**

🔴 **El cambio cierra con E-17 contradicho, por decisión de la autora de la spec y a la vista.** Es
la excepción que el método admite y que tiene precedente en E-29 de 0.13.0: el
incumplimiento queda escrito con su número, acá y en el `CHANGELOG`. La autora fijó el criterio
antes de la sexta pasada: *una pasada más; si sale algo nuevo, se cierra con E-17 contradicho
documentado*. Salió algo nuevo.

| Pasada | Sostenidos | Contradichos | Sin sustento | Qué quedó |
|---|---|---|---|---|
| Primera | 22 | E-17 | E-15, E-22, E-23 | El calificativo no entraba en la comparación: `6.0 SP2` homologaba contra `6.0 SP1` |
| Segunda | 25 | — | E-17 | Cuatro formas sin aserción; dos preguntas de semántica |
| Tercera | 25 | — | E-17 | La condición "que su tecnología usa" no la probaba nada |
| Cuarta | 25 | E-17 | — | Fuera de rama y edición entre paréntesis |
| Quinta | 25 | E-17 | — | Debajo del piso de una rama; formas no canónicas; otro tipo de calificativo |
| Sexta | 25 | E-17 | — | Cero adelante y dígitos no ASCII en el número |

## La tabla

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | El catálogo valida contra su schema | sostenido | sí | `24_g1`, `test_e01_el_catalogo_valida` |
| E-02 | La fuente es ES0901 6.3 y otra versión no se carga | sostenido | sí | `test_e02_es_el_anexo_ii_de_6_3` |
| E-03 | 142 ids únicos, búsqueda por id o alias | sostenido | sí | `test_e03_ids_unicos_y_busqueda_por_alias` |
| E-04 | La versión exacta es `HOMOLOGATED` | sostenido | sí | `test_e04_la_version_homologada_exacta` |
| E-05 | Un parche mayor en la misma rama pasa | sostenido | sí | `test_e05_un_parche_mayor_en_la_misma_rama` |
| E-06 | Un parche menor da `NOT_HOMOLOGATED` | sostenido | sí | `test_e06_un_parche_menor_en_la_misma_rama` |
| E-07 | Una rama menor sin listar no pasa | sostenido | sí | `test_e07_una_rama_menor_sin_listar` |
| E-08 | Una rama mayor sin listar es `ASI_EVALUATION_REQUIRED` | sostenido | sí | `test_e08_una_rama_mayor_sin_listar` |
| E-09 | Dos ramas se evalúan por separado | sostenido | sí | `test_e09_dos_ramas_se_evaluan_por_separado` |
| E-10 | `latest`, `*` o algo que no compara dan `UNRESOLVED` | sostenido | sí | `test_e10_latest_no_es_una_version` |
| E-11 | Una deprecada es `DEPRECATED_TOLERATED`, con observación | sostenido | sí | `test_e11_una_version_deprecada_se_tolera` |
| E-12 | Una deprecada nunca termina en homologada | sostenido | sí | `test_e12_deprecada_no_se_vuelve_homologada` |
| E-13 | Sin historia, `VERSION_HISTORY_REQUIRED` | sostenido | sí | `test_e13_dos_estandares_atras_pide_historia` |
| E-14 | Fuera del Anexo II, `ASI_EVALUATION_REQUIRED` | sostenido | sí | `test_e14_una_tecnologia_que_no_esta` |
| E-15 | `FRAMEWORK_DEPENDENT` y `CONTEXT_DEPENDENT` piden contexto, y con él resuelven | sostenido | sí | `test_e15_version_dependiente_del_framework` — segunda pasada |
| E-16 | `PROVIDER_ASSIGNED_BY_DGSEI` da `PROVIDER_VERSION_REQUIRED` | sostenido | sí | `test_e16_version_asignada_por_el_proveedor` |
| E-17 | LTS, LTR, SP y CE se conservan y no se recortan al comparar | **contradicho** | sí | `test_e17_los_calificativos_se_conservan` — ver abajo |
| E-18 | Una auxiliar declarada es `TOOLCHAIN_AUXILIARY_REVIEW` | sostenido | sí | `test_e18_una_auxiliar_declarada` |
| E-19 | Una desconocida no pasa a auxiliar en silencio | sostenido | sí | `test_e19_una_desconocida_no_se_vuelve_auxiliar` |
| E-20 | El registro declara los cuatro controles de G1 y valida | sostenido | sí | `test_e20_el_registro_declara_los_cuatro` |
| E-21 | Declarado sin archivo es un hueco; un archivo suelto no se adopta | sostenido | sí | `test_e21_declarado_sin_archivo_y_archivo_sin_declarar` |
| E-22 | G1 deja de faltar sin tocar la matriz | sostenido | sí | `test_e22_g1_deja_de_faltar_sin_tocar_la_matriz` — aserción estructural desde la segunda pasada |
| E-23 | Los checks normativos no entran al roster ni al contrato del hook | sostenido | sí | `test_e23_los_checks_normativos_no_son_los_del_hook` — las dos mitades desde la segunda pasada |
| E-24 | G1 no verifica nada de P1 | sostenido | sí | `test_e24_g1_no_verifica_nada_de_p1` |
| E-25 | Todo resultado lleva ES0901 / 6.3 / 7.1 / G1 | sostenido | sí | `test_e25_todo_resultado_conserva_la_traza` |
| E-26 | Mismo inventario, mismo resultado | sostenido | sí | `test_e26_mismo_inventario_mismo_resultado` |

Todos los tests están en `tests/casos/24_g1_tecnologias.py`.

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá no hay ninguno.

## E-17, el escenario contradicho

La primera pasada encontró un bug real: el calificativo no participaba de la comparación.

```
anexo2.parsear('19c (LTR)')      {'kind': 'SENTINEL', 'qualifier': '', ...}
cib-seven 1.1.0 EE  vs 1.1.0 CE  HOMOLOGATED
cib-seven 1.1.0     vs 1.1.0 CE  HOMOLOGATED
jws 6.0 SP2         vs 6.0 SP1   HOMOLOGATED
```

Eso está corregido desde la segunda pasada, y las cinco siguientes ya no encontraron un calificativo
equivocado que homologara. Lo que fueron encontrando es que la frase del escenario —"no se recortan
al comparar"— no alcanza para decidir cada forma de escribir una versión, y la spec no lo decía.
La autora ratificó el 22-09-2026 un **orden único de evaluación**, que la spec escribe en la sección
"El calificativo es parte de lo que se compara":

```
1. La forma.       Lo que no está escrito como lo escribe el Anexo II es UNRESOLVED,
                   dentro o fuera de cualquier rama.
2. El calificativo contra una rama listada, en el piso, arriba o abajo.
                   Soporte que la tecnología usa: cuenta como ausente.
                   Soporte que no usa, u otro tipo que el del catálogo: UNRESOLVED.
                   Otra edición del mismo tipo, o un SP anterior: NOT_HOMOLOGATED.
3. Recién ahí, la rama y el número.
```

**Lo que la sexta pasada encontró, y por lo que el escenario queda contradicho:** el paso 1 no se
cumple en el número. Un cero adelante o un dígito que no es ASCII se lee como canónico y homologa:

```
php '08.2.30'           HOMOLOGATED    matched 8.2.30
php '8.2.030'           HOMOLOGATED    matched 8.2.30
cib-seven '01.1.0 CE'   HOMOLOGATED    matched 1.1.0 CE
jws '6.00 SP1'          HOMOLOGATED    matched 6.0 SP1
oracle '019c'           HOMOLOGATED    matched 19c (LTR)
php '٨.2.30'       HOMOLOGATED    8 en dígito arábigo-índico
php '８.2.30'       HOMOLOGATED    8 de ancho completo
```

La causa: `_NUM` y la parte numérica de `_CON_CALIFICATIVO` en `anexo2.py` usan `\d+`, que en Python
acepta ceros adelante y dígitos Unicode, y `_tupla` los convierte con `int()`. El service pack ya
estaba cerrado con `(?:0|[1-9]\d*)`: el mismo defecto que se rechaza en el calificativo se acepta en
el número.

**Decisión: se cierra contradicho, y el arreglo es lo primero de `PENDIENTES-FH.md`.** Es el único
caso de las seis pasadas que falla del lado abierto. Hoy no homologa un artefacto equivocado —
`08.2.30` y `8.2.30` son el mismo número—, pero acepta una forma que el orden ratificado rechaza.
El arreglo es acotar el número a `(?:0|[1-9][0-9]*)` en ASCII y afirmarlo con esos casos.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **El calificativo no se comparaba** (primera pasada). La única versión LTR del Anexo II —Oracle
   `19c (LTR)`— no podía homologarse nunca, y una edición o un service pack distintos pasaban.
2. **E-22 afirmaba "siguen los 66", y ningún test lo había sostenido nunca.** El número era la foto
   de cuando cerró G1. Ahora la aserción es estructural: lo que falta es exactamente lo que la
   matriz declara menos lo que el registro instala, calculado aparte.
3. **E-23 probaba sólo la mitad del roster.** Ahora también la del hook: `post-tool-use.py` corre
   `<harness>/checks`, `install.ps1` copia sólo `checks/`, y los checks de G1 exponen `evaluar` y no
   `verificar`.
4. **Una decisión del constructor quedó escrita como ratificada** (tercera pasada): la frase sobre
   `dotnet 9.0.12 (LTS)` estaba adentro de la viñeta marcada. La autora decidió lo contrario y la
   frase salió.

## Lo que queda abierto, anotado y no escondido

Todo en `Pendientes/Fix-Harness/PENDIENTES-FH.md`:

1. **El número acepta ceros adelante y dígitos no ASCII** (E-17, arriba).
2. **Casos que la spec no cubre, y que no homologan:** qué palabra en mayúsculas cuenta como
   edición (`1.1.0 ABC` da `NOT_HOMOLOGATED`, `jws 6.0 SP` da `UNRESOLVED`); un sufijo distinto en
   la misma rama (`oracle 19d`); las ramas de Oracle (`19.1` da `ASI_EVALUATION_REQUIRED`, `19` da
   `UNRESOLVED`); cuántos componentes lleva el número (`php 8.2.30.0` homologa por la regla del
   parche).
3. **"Service pack anterior da `NOT_HOMOLOGATED`" se prueba sólo con `SP0`**, que es una decisión
   del constructor: el catálogo sólo lista `SP1`.
4. **`technology-version-compliance.py` vive en un `checks/`.** El constructor lo editó avisando que
   por su rol ese directorio es del hook engineer. La spec dice que los checks normativos son otra
   capa; que alguien lo revise.

## Lo que ningún test cubre y se mira con los ojos

Que el Anexo II transcripto en el catálogo diga lo mismo que el estándar. E-01 a E-03 prueban la
forma del catálogo y sus 142 ids; que cada versión esté bien copiada sólo se ve leyéndolo contra
ES0901 6.3.
