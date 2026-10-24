# Verificación — WCAG 2.2 con Obelisco V2: la accesibilidad del Harness sobre una fuente de criterios, un check que no inventa fallos y un registro que no certifica

**Estado:** cerrado, con la compuerta completa en verde (ver «La compuerta») · **Fecha:** 24-10-2026 (veredictos del 23-10-2026) · **Versión:** sin versión: rama `wcag22-obelisco` sobre `0.35.0`, sin commit

Este documento es lo que cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter`, que no construyó este cambio y no escribe su propio veredicto en un archivo; quien coordinó lo consolidó acá. Rindió dos veces: la primera dejó 61 sostenidos y 2 contradichos (E-19 y E-30); se resolvieron en el código y en los tests, y la segunda vuelta, con los mismos comandos, dejó los 65 sostenidos. La spec sobre la que rige es `docs/cambios/wcag22-obelisco/spec.md` con SHA256 `16724866061CB24686518D604E5693CCA15C3D354606B481EB2ABF63EBD8215C`; el refutador rindió sobre `11CB50F4AE57FD28848CB492E87F2C0878839BD99745C4FF3D8879299C4F0A49`, y las únicas diferencias son una fila de la tabla «Qué se construye» (ver «La compuerta») y una enmienda sobre el cierre de la versión en «Qué queda afuera»: ningún escenario cambió.

**Resultado: 65 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.** E-19 y E-30 fueron contradichos en la primera vuelta y quedaron sostenidos en la segunda.

## Qué se verificó y sobre qué

| | |
|---|---|
| Spec verificada | `11CB50F4AE57FD28848CB492E87F2C0878839BD99745C4FF3D8879299C4F0A49` por el refutador; hoy `16724866…215C` (una fila agregada en «Qué se construye» y una enmienda sobre el cierre de la versión, sin tocar escenarios). Cinco escenarios cambiaron de texto después del primer veredicto; ver «Lo que la verificación encontró» |
| Baseline | rama `main`, `3a2c48db3f083053641629b490a7ed0c67e8d87f`, tag `v0.35.0`, `VERSION` 0.35.0 |
| Estado del árbol | worktree `C:\dev\hp-wcag`, rama `wcag22-obelisco`, 22 entradas sin commitear (13 modificadas, 9 sin seguimiento); el refutador no cambió ninguna |
| Frontera | Sin tocar `C:\dev\Harness-Project`, donde la Task 6.2 espera; su borrador marcado `0.36.0` se renumera a `0.37.0` porque esta versión tomó ese número |

## Método

| Comando | Salida |
|---|---|
| `python tests/correr.py -k 78_wcag22 --detallado` (Python 3.12.10) | `1894/1894 pasaron.` |
| El mismo, con un Python 3.9.25 real y `HARNESS_PYTHON39` | `1896/1896 pasaron.` (dos más: las tres ejecuciones reales de E-39 menos la aserción «SIN HARNESS_PYTHON39») |
| `python tests/correr.py -k 07_checks` | `5/5 pasaron.` |
| `python tests/correr.py -k 08_checks` | `34/34 pasaron.` |
| `tests\Invoke-Tests.ps1 -SoloCaso 78-wcag22-obelisco-instalador.ps1 -Detallado` | `45/45 pasaron (PowerShell).` |

Además, sondeos propios del refutador sobre lo que cambió después de su primer veredicto:

- **W3C en vivo.** Bajó de nuevo `wcag.json` (SHA256 `3a034865…ef5cf75`, igual al del testigo): 86 con nivel (A 31 · AA 24 · AAA 31) y 4.1.1 sin nivel; ids, nombres y niveles coinciden uno por uno con `wcag22-criteria.json`.
- **`contrast.py` contra el original.** 1.344 combinaciones opacas: cero diferencias. El «original» es la copia de `contrast_ratio.py` del scratchpad del constructor, no la skill del usuario.
- **El check real sobre el corpus.** 74 casos, 31 avisos, 0 desvíos; todos traen «(criterio X, nivel Y)». Calla ante ocho entradas rotas, binarias o grandes.
- **Mutaciones propias** sobre copias: quitó 2.4.13 del JSON y `wcag.py count` pasó a 85 con AAA 30; desvió cada uno de los cuatro conteos del `summary` y dio `summary_mismatch`.
- **`-I -B` sin variable de entorno** sobre un árbol con el layout instalado: no quedó ningún `__pycache__`.

## Escenarios

`78_wcag22_obelisco.py` cubre E-01 a E-61 y `78-wcag22-obelisco-instalador.ps1`, E-62 a E-65.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | 86 criterios (A 31 · AA 24 · AAA 31), ids únicos, iguales al testigo del W3C | sostenido | sí, mutación | `test_e01_…` (:88), `wcag22-w3c.json` y W3C en vivo |
| E-02 | 4.1.1 fuera de los 86: en `removed`, sin nivel, con motivo | sostenido | sí, mutación | `test_e02_…` (:102) |
| E-03 | Los nueve criterios nuevos de 2.2 llevan `new_in_22` y ningún otro | sostenido | sí, mutación | `test_e03_…` (:115), contra `versions` del W3C |
| E-04 | Ningún texto afirma un conteo distinto de 86 | sostenido | sí, mutación | `test_e04_…` (:138); el refutador grepeó además JSON y scripts |
| E-05 | `wcag.py count` imprime 86/31/24/31 y los saca del JSON | sostenido | sí, mutación | `test_e05_…` (:152) |
| E-06 | `requires` solo con `browser`, `keyboard`, `screen_reader`; casos fijos | sostenido | sí, mutación | `test_e06_…` (:166) |
| E-07 | `criterion 2.4.11`: nombre, nivel y texto de ese criterio, menos de 6.000 caracteres | sostenido | sí, vuelto a tomar tras el cambio de texto | `test_e07_…` (:180); 3.329 caracteres, una sola sección |
| E-08 | `criterion 4.1.1`: retirado, sin nivel, defectos a 1.3.1 y 4.1.2 | sostenido | sí, mutación | `test_e08_…` (:193) |
| E-09 | `criterion 9.9.9`: código ≠ 0, sin traceback | sostenido | sí, mutación | `test_e09_…` (:204) |
| E-10 | `list --level AA` da los 24; `--up-to AA`, 55 | sostenido | sí, mutación | `test_e10_…` (:212) |
| E-11 | Cada tarea de la tabla se resuelve a una guía que existe | sostenido | sí, mutación | `test_e11_…` (:233) |
| E-12 | `component form-text`: criterios con nivel, requisitos con origen, verificación | sostenido | sí, vuelto a tomar tras endurecer | `test_e12_…` (:252); CLI sobre `form-text`, `custom` y `tabs` |
| E-13 | Sin referencias huérfanas: lo que la tabla nombra existe y todo `references/` está nombrado | sostenido | sí, vuelto a tomar tras endurecer | `test_e13_…` (:270); mira solo filas de tabla |
| E-14 | `SKILL.md` ≤ 8.000 caracteres; la tarea de formularios no pasa de 12.573 | sostenido | sí, mutación | `test_e14_…` (:286); 7.527 y 11.746 |
| E-15 | Los descriptores siempre cargados no crecen más de 20 tokens sobre 591 | sostenido | sí, mutación | `test_e15_…` (:302); 575 con piso por archivo, 577,5 exactos |
| E-16 | Cada requisito lleva `origin`; los de Obelisco, página y fecha | sostenido | sí, mutación | `test_e16_…` (:312) |
| E-17 | Los AAA citados van en `aaa_additional`, nunca en la base AA, con quién los pide | sostenido | sí, mutación | `test_e17_…` (:336) |
| E-18 | El nivel que Obelisco declara es el real, o la discrepancia está registrada | sostenido | sí, mutación | `test_e18_…` (:363) |
| E-19 | La matriz cubre formularios y pantallas de trámite; cada fila con página, requisitos y `verification` | sostenido (contradicho en la primera vuelta) | sí, vuelto a tomar tras el arreglo (1, 5 y 2 rojos) | `test_e19_…` (:378); 34 filas más `custom`, reglas existentes en el motor |
| E-20 | Fila `custom`: nombre, rol, estados, teclado y foco, y las tres pruebas manuales | sostenido | sí, vuelto a tomar tras endurecer | `test_e20_…` (:406) |
| E-21 | `SKILL.md` nombra las tres fuentes, propone AA, los AAA son adicionales, no certifica | sostenido | sí, tras endurecer el test | `test_e21_…` (:418) |
| E-22 | `register template --level AA`: 55 `not_tested`, 4.1.1 `not_applicable`, tres pruebas `not_performed` | sostenido | sí, mutación | `test_e22_…` (:433); CLI: 56 filas |
| E-23 | Falta un criterio del nivel objetivo: falla y lo nombra | sostenido | sí, mutación | `test_e23_…` (:449) |
| E-24 | Un resultado fuera del vocabulario falla | sostenido | sí, mutación | `test_e24_…` (:459) |
| E-25 | `fail` sin ubicación, evidencia o corrección: rechazado, dice cuál | sostenido | sí, mutación | `test_e25_…` (:469) |
| E-26 | `pass` exige las pruebas manuales que el criterio requiere; sin evidencia, nunca | sostenido | sí, mutación | `test_e26_…` (:487) |
| E-27 | `not_applicable` y `not_tested` sin `reason`: rechazados | sostenido | sí, mutación | `test_e27_…` (:512) |
| E-28 | 4.1.1 solo como `not_applicable` | sostenido | sí, mutación | `test_e28_…` (:524) |
| E-29 | El `summary` y `fail_by_level` coinciden con las filas exigidas | sostenido | sí, vuelto a tomar tras endurecer (2 y 10 rojos) | `test_e29_…` (:537); los cuatro conteos y el caso 14/11 contra 13/12 |
| E-30 | `target.additional` pide una fila por adicional; un AAA no pedido se cuenta aparte | sostenido (contradicho en la primera vuelta) | sí, vuelto a tomar tras el arreglo (9 rojos) | `test_e30_…` (:570); `resumir_registro` y la CLI |
| E-31 | `levels` marca «1.3.4 (Level A)», 5.1.1 y 4.1.1 con nivel; acepta el correcto | sostenido | sí, mutación | `test_e31_…` (:604) |
| E-32 | Ningún nivel mal escrito en lo que se carga | sostenido | sí, mutación | `test_e32_…` (:631); 12 archivos y los 9 de `wcag22/` |
| E-33 | `contrast.py`: 21:1, 4,48:1, 4,54:1; igual al original en opacos | sostenido | sí, mutación | `test_e33_…` (:647); 1.344 combinaciones contra el original |
| E-34 | El alfa del primer plano se compone: 3,95:1 y `#808080` | sostenido | sí, mutación | `test_e34_…` (:671) |
| E-35 | Formatos de color: hex, `rgb()`, `hsl()`, nombres básicos | sostenido | sí, mutación | `test_e35_…` (:682) |
| E-36 | Fondo translúcido sin `--backdrop`: código 2; con él, calcula | sostenido | sí, mutación | `test_e36_…` (:699) |
| E-37 | Lo no calculable sale con código 2 y una limitación, sin traceback | sostenido | sí, tras endurecer el test y vuelto a tomar | `test_e37_…` (:717); distingue lo dinámico de lo desconocido |
| E-38 | Tamaño grande: 24 px, o 14 pt (18,67 px) en negrita; 1.4.6 marcado AAA | sostenido | sí, vuelto a tomar tras el cambio de texto (1 y 3 rojos) | `test_e38_…` (:740); CLI en los bordes |
| E-39 | Válido en Python 3.9: AST con `feature_version`, sin `\|` en anotaciones, sin APIs ≥ 3.10; con `HARNESS_PYTHON39`, corrido de verdad | sostenido | sí, mutación | `test_e39_…` (:807); tres ejecuciones reales en 3.9.25 (ver el matiz abajo) |
| E-40 | Un `id` solo no es un nombre accesible | sostenido | sí, mutación | `test_e40_…` (:844) |
| E-41 | `<label for>` y `<label>` envolvente no se reportan; la envolvente sin texto sí | sostenido | sí, mutación | `test_e41_…` (:857) |
| E-42 | `aria-label` con texto no se reporta; en blanco, sí | sostenido | sí, mutación | `test_e42_…` (:866) |
| E-43 | `aria-labelledby`: existe con texto, no existe, sin texto, varios ids | sostenido | sí, tras endurecer el test | `test_e43_…` (:873) |
| E-44 | Fragmentos: defecto `control-label-missing-in-file`; `undeterminable` en la revisión completa | sostenido | sí, mutación | `test_e44_…` (:892) |
| E-45 | Cero o dos `<h1>` no avisa en el liviano; recomendación sin criterio en la completa | sostenido | sí, mutación | `test_e45_…` (:909) |
| E-46 | El liviano emite solo fallos y defectos, con «criterio X, nivel Y» | sostenido | sí, mutación | `test_e46_…` (:932); corre a nivel motor; el refutador corrió el check real |
| E-47 | El liviano ignora lo que no le toca y calla ante lo ilegible | sostenido | sí, mutación | `test_e47_…` (:964); ocho entradas rotas a mano |
| E-48 | Plantillas sin falsos positivos; `<img [src]>` sin `alt` sí | sostenido | sí, mutación | `test_e48_…` (:993) |
| E-49 | JSX y TSX con tokenizador propio | sostenido | sí, tras endurecer el test | `test_e49_…` (:1014) |
| E-50 | `{...props}` y componentes capitalizados no se juzgan; se cuentan como no analizados | sostenido | sí, mutación | `test_e50_…` (:1050) |
| E-51 | La revisión completa informa cobertura y no calla extensiones fuera de alcance | sostenido | sí, mutación | `test_e51_…` (:1069) |
| E-52 | 5.000 controles en menos de 5 s, no cuadrático | sostenido | sí, tras endurecer el test | `test_e52_…` (:1098); 391.759 bytes en 0,17 s; cociente 4,7 (< 8) entre 10.000 y 2.500 controles |
| E-53 | Corpus etiquetado: 0 falsos positivos y 0 falsos negativos de los tipos declarados | sostenido | sí, mutación | `test_e53_…` (:1139), `tests/fixtures/a11y/corpus.json` (74 casos) |
| E-54 | Reglas del motor = criterios del JSON = técnicas del W3C = tabla de `static-coverage.md` | sostenido | sí, mutación | `test_e54_…` (:1168), `wcag22-w3c.json` |
| E-55 | `review.py --register` produce un borrador válido y ningún `pass` | sostenido | sí, vuelto a tomar tras endurecer (6 rojos) | `test_e55_…` (:1198); CLI: 4 `fail` con archivo y línea, 51 `not_tested` con motivo |
| E-56 | `review.py` encuentra el motor en la fábrica y en el árbol instalado; si no, código 2 | sostenido | sí, mutación | `test_e56_…` (:1227) |
| E-57 | Los defectos de la lista quedaron arreglados y cubiertos por E-40 a E-45 | sostenido | sí, tras endurecer el test | `test_e57_…` (:1257) |
| E-58 | `dev-ui` exige `accessibilityLinks` por componente; los del ejemplo existen en la matriz | sostenido | sí, mutación | `test_e58_…` (:1275) |
| E-59 | `dev-responsive` trae 1.4.4, 1.4.10, 1.4.12, 1.3.4 y 2.5.8 como AA, 2.5.5 como AAA, y dice que se verifica en navegador | sostenido | sí, mutación | `test_e59_…` (:1300) |
| E-60 | `dev-frontend-implementation` ordena ui → accessibility → responsive y exige el registro; `dev-frontend` devuelve `accessibilityEvidence` | sostenido | sí, mutación | `test_e60_…` (:1314) |
| E-61 | El registro de agentes sigue válido: cuatro `id` y rutas sin cambios | sostenido | sí, mutación | `test_e61_…` (:1337) |
| E-62 | Instalar: el lock lista skill y motor, todo en disco y con su SHA256 | sostenido | sí, mutación sobre `install.ps1` (26 rojos) | `78-wcag22-obelisco-instalador.ps1`; instaló de verdad, 24 archivos de la skill más el motor |
| E-63 | Desde el árbol instalado, con `python -I -B`, corren los tres scripts | sostenido | sí, mutación | `78-wcag22-obelisco-instalador.ps1` |
| E-64 | `-Update`: borra la referencia retirada sin editar, deja la editada con aviso, instala la nueva | sostenido | sí, mutación | `78-wcag22-obelisco-instalador.ps1` |
| E-65 | `-Uninstall`: no queda archivo del lock, carpeta ni `__pycache__` | sostenido | sí, mutación | `78-wcag22-obelisco-instalador.ps1`; el test borra a mano la referencia editada antes de desinstalar |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide ADR-0006: un test que nunca se vio fallar no probó que puede fallar. En esta spec los 65 escenarios llevan `rojo visto: si`, y es una declaración: el constructor la tomó con 61 mutaciones deliberadas sobre el código (55 pusieron en rojo su escenario a la primera, 6 no y esos tests se endurecieron), 15 más tras los arreglos y 4 sobre el instalador. La palabra «mutación» de la columna remite a eso.

> 📌 **Matiz de E-39.** Sin `HARNESS_PYTHON39` la prueba de Python 3.9 real no corre: la advertencia es una aserción siempre verdadera cuyo nombre lo dice («SIN HARNESS_PYTHON39 … NO con un Python 3.9 real») y solo se ve con `--detallado`, porque el framework no tiene un mecanismo de omisión. Lo que el refutador sostuvo corrió con un 3.9.25 real. En una máquina sin ese intérprete, E-39 se sostiene por el lint de AST y no por la ejecución.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-19 contradicho en la primera vuelta.** Las filas de `obelisco-matrix.json` no traían `verification`, y el test verde comprobaba los requisitos y no ese campo. Se resolvió en los datos y en el código, no en la spec: el generador emite `verification` con `static` y `manual` por fila, `wcag.py component` imprime «Verificación:» desde esa clave y el test afirma la clave, que cada regla existe en el motor y que las pruebas manuales salen de los criterios de la fila. El refutador lo confirmó sobre las 34 filas más `custom`: cero reglas inexistentes, cero desvíos.
2. **E-30 contradicho en la primera vuelta.** Un criterio AAA que el objetivo no pedía se mezclaba con los conteos del objetivo, y un registro AA con una fila 1.4.6 extra daba números que no eran los de las filas exigidas. `resumir_registro` ahora cuenta aparte lo que el objetivo no exige, el `summary` que lo mezcla da `summary_mismatch` y `fail_by_level` ignora los extras. Se resolvió en el código.
3. **Salvedades de la primera vuelta que se endurecieron en los tests:** E-13 miraba el texto y no las filas de tabla, E-29 no recorría los cuatro conteos ni `fail_by_level`, E-37 no distinguía lo dinámico de lo desconocido, E-38 decía 18,66 px en la spec y en los textos, y 14 pt son 18,67 px según el W3C, y E-55 no afirmaba la nota «estática sin hallazgos».
4. **Seis tests flojos vistos por el rojo, no por el verde.** Una mutación deliberada no puso en rojo a E-21, E-37, E-43, E-49, E-52 ni E-57: sus tests pasaban de todos modos. Se endurecieron y la segunda mutación sí los puso en rojo. La mutación de E-43 estaba además mal escrita (sintácticamente inválida) y habría dado un rojo falso.
5. **Python 3.9 real.** Contra un 3.9.25 real, `wcag.py` y `review.py` fallaban por `Path.write_text(newline=)`, una API de 3.10 que el lint de AST no veía. Se reemplazó por `open(..., newline="\n")` y el lint se amplió (`write_text` con `newline`, `pairwise`, `isinstance` con `|`, `bisect` con `key`). El `contrast_ratio.py` original de la skill adjunta también revienta en 3.9 (`TypeError` por el `|` en una anotación).
6. **Un parche silencioso que no se aplicó.** `_Jsx.linea` seguía siendo cuadrático porque el parche con `bisect` no había entrado. Lo encontró la medición de E-52, no un test de corrección; ahora usa `bisect_left` sobre las posiciones de salto de línea y el cociente de 10.000 contra 2.500 controles es 4,7 (< 8).
7. **Cinco escenarios cambiaron de texto después del primer veredicto**, y se declara acá porque es lo que el rol manda mirar: E-07 («nada de 2.4.10 ni de 2.4.12» pasó a «ninguna de las secciones de…», porque el texto de 2.4.11 nombra a 2.4.12 como criterio relacionado), E-29 (suma `fail_by_level` y la restricción a las filas exigidas), E-38 (18,66 px pasó a «14 pt (18,67 px)»), E-44 (el identificador pasó a `undeterminable` por ADR-0011) y E-46 (el ejemplo pasó a «criterio 4.1.2, nivel A»). Ninguna proposición se movió ni desapareció, salvo en E-07, donde la ausencia literal de la cadena ya no se exige: **es el único recorte de la spec y queda a criterio de quien revise aceptarlo.**

## Lo que queda abierto, anotado y no escondido

Todo vive en `Pendientes/Fix-Harness/PENDIENTES-FH.md`, sección «What the WCAG 2.2 integration with Obelisco left open», y en `Pendientes/Ideas-Harness/PENDIENTES-I.md`:

- **FH, no hay un ejecutor de las pruebas manuales.** El registro las deja en `not_performed` y no hay nada que las corra por navegador, teclado o lector de pantalla.
- **FH, la matriz es una foto.** Sale de las páginas de Obelisco consultadas el 23-10-2026; si Obelisco cambia, la matriz no se entera.
- **FH, los pares de contraste nunca se leen del código.** `contrast.py` calcula los pares que le dan; el check no los extrae de CSS ni de JSX.
- **FH, el testigo de paridad del check se reescribió a mano.** El caso de `dev-accesibilidad-html` en `paridad-checks.json` ya no es la paridad con PowerShell: se rompió a propósito y lo dice la nota del archivo.
- **I, correr los evals de `wcag22` sobre el Harness integrado.** Los del HTML adjunto tienen n = 1 por eval y miden la skill adjunta, no esta integración.
- **I, soporte de Vue, Svelte y Razor.** Hoy el check cubre HTML, plantillas y JSX/TSX, y lo demás se lista como no analizado.
- **La versión se cerró después de esta verificación**, como `0.36.0` y con `close-a-version` (decisión del usuario, 24-10-2026), y la limpieza de la Task 6.1 (6.2, en pausa) pasa a `0.37.0`. Se esperan conflictos con la 6.2 en `tests/parallel-manifest.json`, los dos `Pendientes/*`, `CHANGELOG.md`, `UPGRADE.md` y el índice de versiones.
- **El corpus lo etiquetó el constructor.** Sus 74 casos miden que el check hace lo que el constructor entiende que debe hacer; no es una verdad externa.
- **El «original» de E-33 es una copia.** El refutador comparó contra el `contrast_ratio.py` del scratchpad del constructor, no contra el archivo del usuario.

## Lo que ningún test cubre y se mira con los ojos

- **Las tres pruebas manuales** (navegador, teclado, lector de pantalla) sobre un formulario real de Obelisco. Nada de esta verificación las corrió, y un análisis estático limpio no es conformidad.
- **Que un modelo siga bien la entrada nueva.** E-58 a E-60 verifican el texto de las instrucciones, no cómo las sigue un modelo; ningún escenario es de lectura. La medición dice que la entrada de `dev-accessibility` bajó de 3.143 a 1.863 tokens (−40,7 %) y la unidad de frontend subió 0,4 %; no dice nada sobre la calidad de lo que produce.
- **Que la matriz siga vigente** contra las páginas vivas de Obelisco, de las que once componentes tienen la pestaña de accesibilidad vacía.
- **Que `docs/accesibilidad.md` se entienda**, con su ejemplo de formulario, para quien nunca vio el cambio.

## La compuerta

**Primera corrida completa** de `.\tests\Invoke-Tests.ps1` (57 minutos, sin elevar, `TEMP=C:\t\hpw-gate`, Git Bash al frente): **50.866 de 50.877, 11 fallos.** El refutador había corrido los casos de este cambio y no la compuerta; ninguno de los 11 era de un escenario de esta spec: eran guardas de Tasks cerradas que este cambio toca a propósito y que ningún escenario nombraba.

| Guarda | Qué fijaba | Qué pasó |
|---|---|---|
| `63-harness-unico-instalador.ps1` E-15 (dos) y E-16 | El inventario exacto del lock (298) y que cada archivo instalado fuera el de la base | 23 archivos nuevos y seis modificados (el agente de frontend, el check y cuatro skills) |
| `61_conocimiento_auto_refresco.py` E-02 | Mismos archivos de skills que en 0.26.0 | Las carpetas `references/` y `scripts/` de `dev-accessibility` |
| `64_modelo_de_dominio.py` E-16 y `65_contrato_de_ejecucion.py` EX-E41 | La misma unidad de refutación que en la base | `skillFingerprint` de las ocho unidades de `dev-accessibility`: la huella de una skill invalida lo cacheado, y la skill cambió |
| `72_motor_de_ejecucion.py` ME-E49 y `74_knowledge_api.py` KA-E53 | Agentes y skills iguales a la base, sin archivos nuevos | Las mismas cinco piezas |

Se resolvieron adaptando cada guarda con «Pisado por docs/cambios/wcag22-obelisco/spec.md», saltando **solo** lo que este cambio toca a propósito: el agente de frontend y las carpetas de las cuatro skills de frontend (en 61, solo las dos carpetas nuevas de `dev-accessibility`), y no el resto de los agentes ni de las skills; ninguna guarda se aflojó ni se borró. La guarda de Knowledge API sobre el literal `E-15 son 298:` se respetó: el 298 se cuenta sin los 23 nuevos y una línea aparte cuenta los 321. La fila de la spec que lo registra es una enmienda posterior a la construcción, hallada por la compuerta y no por la spec, y se declara acá.

EX-E41 quedó oculto detrás del fallo de E-16 de 64 y apareció recién al arreglarlo: pide que esa función sea textualmente la de la base. Ahora acepta la de la base con **ese bloque** cambiado y nada más, y cuenta que el bloque esté una vez en la base.

Casos corridos de nuevo, aislados, tras las adaptaciones: `61_conocimiento_auto_refresco` 292/292, `72_motor_de_ejecucion` 546/546, `74_knowledge_api` 2.374/2.374, `64_modelo_de_dominio` 1.056/1.056, `65_contrato_de_ejecucion` 675/675, `63_harness_unico` 180/180, `71_plan_2_1` 276/276 y el instalador `63-harness-unico-instalador.ps1` 189/189.

**Segunda corrida completa, sobre el árbol final** (24-10-2026, 111 minutos, mismas condiciones, salida 0): **50.880 de 50.880 pasaron** (PowerShell 1.014/1.014, Python 49.866/49.866), incluidos `78_wcag22_obelisco` y el instalador `78-wcag22-obelisco-instalador.ps1`. Sin fallos. Después de esa corrida cambiaron el encabezado de este archivo y esta línea, y se cerró la versión (`VERSION`, nota, índice, `CHANGELOG`, `UPGRADE`, un ítem de `Pendientes`).

**Corridas del cierre de versión** (commit `17a02b2`, 24-10-2026): la tercera dio 50.875 de 50.878, con tres filas rojas de `75_runner_paralelo` VP-E22 (c), un caso del runner paralelo que espera 30 s a que un PowerShell frío escriba `pesada.json` y falló con cuatro sesiones de `claude` abiertas; el mismo caso solo, con la máquina quieta, dio 838/838. La cuarta, completa, dio **50.880 de 50.880** (46 minutos, salida 0). El runner no lo toca este cambio; quedó anotado en `PENDIENTES-FH.md`. Los dos textos que cambiaron después (esta nota y la de la versión) no los lee ningún escenario.
