# Verification Pipeline Performance: un runner paralelo acotado que da lo mismo que `Invoke-Tests.ps1`, en menos tiempo

**Estado:** **CONSTRUIDA — pendiente de refutación independiente** (22-10-2026: construcción, WU03-b y pasada
post-WU03-b hechas; sin veredicto, sin commit) · antes: APPROVED FOR CONSTRUCTION · SPEC REVIEW independiente
aprobado el 20-10-2026 por
`harness-spec-refuter` (invocación nueva, sobre el freeze `FE5748A4DE1B42308DEBB573C5CA75559D6E6FC035F9FB80111D83C5EBDC1C89`):
15/15 decisiones sostenidas, 17/17 invariantes refutables, 25/25 escenarios testeables, 20/20 mutaciones
útiles, 0 bloqueantes, 15 no bloqueantes · aprobación humana para construcción confirmada por Nahuel Palacio
el 20-10-2026, en el encargo que corrigió NB-01 y NB-04 antes de construir (§1.4) · WU03-b hecha (§5.6,
`benchmark-2026-10-22.md`) · **Enmiendas posteriores a la aprobación: D-T1..D-T7, registradas en §1.3**
(autorizadas por Nahuel Palacio el 21-10-2026 y el 22-10-2026; no son un freeze nuevo) · **Fecha:** 20-10-2026 · **Versión de partida:** 0.34.0 (`d86b285a9d0a4610a44a15ba3ca455be42d2edaa`, tag
`v0.34.0`), árbol limpio, huella `FDEF538098DC593B4E3537BB945A8F365A788E7DEC29B80E501A056E58BF4C70`.

Esta spec es la Task 6.1. Consolida las salidas de T61-WU01, WU02, WU04, WU05/12, WU07/09, WU08/13 y WU10, los
once conflictos cruzados K1 a K11 que detectó el orquestador, la revalidación de sus citas sobre la baseline
real (T61-REV, `harness-repo-discoverer`), la alineación con el release 0.34.0 (T61-ALIGN,
`harness-contract-guardian`) y el benchmark serial previo a construir (WU03-a, corrido el 20-10-2026 y
analizado por `harness-runtime-analyst`), y decide cada punto. Se escribió antes de construir: lo que dependía
del runner —WU03-b, el par serial contra paralelo— quedó pendiente **por diseño**, con su regla escrita. El SPEC
REVIEW independiente la aprobó el 20-10-2026 sin bloqueantes y la persona confirmó la aprobación para
construcción (encabezado, §1.4); de los quince hallazgos no bloqueantes, NB-01 y NB-04 se corrigieron antes
de construir y los demás quedan como información para el builder, no como cambios de la spec.

**Después de construir** (20 a 22-10-2026): el código, los tests, el ADR y M1 están escritos (§1); WU03-b se
corrió (§5.6) y su registro es `benchmark-2026-10-22.md`; la pasada post-WU03-b (§1.3) puso cada valor que la
spec esperaba de WU03-b, las marcas `rojo visto` (§26) y las observaciones de la construcción. Falta la
refutación independiente (§29, paso 12).

Abreviaturas:

- **oráculo** es `tests/Invoke-Tests.ps1`; **runner** es `tests/Invoke-Tests-Parallel.ps1` (nuevo);
  **manifest** es `tests/parallel-manifest.json` (nuevo); **comparador** es `tests/Compare-TestRuns.ps1`
  (nuevo); **medidor** es `tests/Measure-TestRuns.ps1` (nuevo);
- **FH** es `Pendientes/Fix-Harness/PENDIENTES-FH.md`; **I** es `Pendientes/Ideas-Harness/PENDIENTES-I.md`;
- **t72**, **t73**, **t74**, **t63c**, **t63h**, **t64**, **t65** son `tests/casos/72_motor_de_ejecucion.py`,
  `73_ejecucion_de_grafo.py`, `74_knowledge_api.py`, `63_compuerta_del_flujo.py`, `63_harness_unico.py`,
  `64_modelo_de_dominio.py` y `65_contrato_de_ejecucion.py`; **t18i**, **t68**, **63-hu** y **74-inst** son
  `18-integraciones-instalador.ps1`, `68-isolated-factory.ps1`, `63-harness-unico-instalador.ps1` y
  `74-knowledge-api-instalador.ps1`;
- **ME** es `docs/cambios/minimal-execution-engine/spec.md`; **GE** es `docs/cambios/graph-execution/spec.md`;
  **nota 0.34.0** es `docs/versiones/0.34.0.md`;
- **suite** es un archivo de `tests/casos/` (`*.ps1` o `*.py`); **corrida** es una ejecución del runner;
  **par** es una corrida del oráculo y una del runner sobre la misma huella; **pata** es cada mitad de un par.

📌 **Las citas.** `archivo:línea` con el nombre completo, o con una abreviatura de arriba. Una cita `NN:línea`
sin nombre es de la **única suite Python** con ese número (`66:474` es `66_integrity_cleanup.py`, `72:875` es
t72); un instalador `.ps1` se cita siempre con su nombre (`72-motor-de-ejecucion-instalador.ps1:41`, nunca
`72:41`). Donde hay dos `.py` con el mismo número (61, 62, 63, 64, 65) se usa el nombre o la abreviatura.

📌 **Los ids.** Escenarios `VP-Enn`, invariantes `VP-Inn`, decisiones `VD-nn`, conflictos y discrepancias
decididos `VC-nn`, mutaciones de rojo `VM-nn`, pendientes `VX-nn`. Para el método de `CLAUDE.md`, un
`VP-Enn` es un `E-nn` con todas sus reglas, `rojo visto` incluido. Las reglas del protocolo del benchmark se
citan `§5.7 B1` a `B6`: salen de los invariantes propuestos VP-B1..B6 del runtime-analyst, son texto del
protocolo y **no** son invariantes `VP-I` ni tienen escenario propio. Los ids provisorios de los especialistas
se citan con su origen (`WU04:fila 6`, `WU13:E-09`, `WU05:INV-07`, `analista:D1`) y no son ids de esta spec.

📌 **Evidencia.** Las citas del borrador las leyó el arquitecto sobre `47f9920` más las 14 entradas sin
commitear de Task 6, que es el mismo árbol que se commiteó como `d86b285`; el discoverer las re-verificó todas
sobre `d86b285` (§2.2). Las citas nuevas de esta pasada las leyó el arquitecto sobre `d86b285`, o llevan su
origen (`discoverer`, `guardián`, `analista`, `WU03-a`). Lo que dijo un especialista y no se releyó está
marcado `(WUnn, no releído)` y no sostiene ninguna decisión. Los números llevan siempre su rótulo:
**MEASURED-BASELINE** (WU03-a, sobre `d86b285`, §5.6); **MEASURED-previa** (corridas viejas, en árboles y
condiciones distintos: **no son baseline** y no alimentan nada); **ESTIMATED** (cuentas o simulaciones sobre
MEASURED-BASELINE, no mediciones); **MEASURED-WU03-b** (los pares serial contra paralelo de WU03-b, sobre el
árbol construido, §5.6). `PENDING_WU03_B` fue el rótulo de lo que esperaba a esos pares; desde la pasada
post-WU03-b (§1.3) ningún valor de esta spec lo lleva: cada uno quedó medido o decidido, con su fuente.

📌 **Lo normativo y lo observado.** Lo que esta spec promete son acciones del código que 6.1 construye. Lo
que depende de Windows, de PowerShell 5.1 o de otro proceso (cuándo suelta el SO un candado, qué hace
PS 5.1 con el stderr de un nativo, si `taskkill /T` alcanza a un nieto) se escribe como **observación**, y
donde importa, un escenario lo fija.

## Índice

1. Estado · 2. Baseline · 3. Problema · 4. AS-IS · 5. Benchmark · 6. Test inventory · 7. Interference model
· 8. Boundary · 9. Execution model · 10. Suite metadata · 11. Resource classes · 12. Isolation ·
13. Scheduling · 14. Worker lifecycle · 15. Result model · 16. Aggregation · 17. Failure semantics ·
18. Cancellation · 19. Resource lock · 20. Determinism · 21. Serial compatibility · 22. Performance
acceptance · 23. Security / repo integrity · 24. Risks · 25. Invariants · 26. Scenarios · 27. Mutations ·
28. Migration · 29. Construction order · 30. Gate · 31. Las decisiones, y por qué · 32. Conflictos y
discrepancias decididos · 33. Pendientes · 34. Matriz de consolidación · 35. Métricas de éxito

---

## 1. Estado

| | |
|---|---|
| Fase de especialistas | WU01, WU02, WU04, WU05/12, WU07/09, WU08/13 y WU10 completas, solo lectura; consolidadas completas |
| Baseline | Real y fijada: 0.34.0, `d86b285`, tag `v0.34.0`, árbol limpio, huella `FDEF5380…` (§2.1) |
| Revalidación sobre la baseline | Hecha: todas las citas IGUAL, inventario igual, 0 contradicciones del release con VD-01..VD-15 (§2.2) |
| WU03-a (benchmark serial previo) | **Hecha** el 20-10-2026, 09:33 → 12:14, con el protocolo de §5.3 (§5.6) |
| WU03-b (serial contra paralelo) | **Hecha**, 21 y 22-10-2026, tres pares N = 2 (§5.6, `benchmark-2026-10-22.md`): el par 1 y el 1b no se aceptaron (§5.6); el par de cierre (22-10, 09:17 → 10:42) dio serial 2976,9 s y paralelo 2110,4 s, exit 0 y 48841/48841 las dos, tres huellas `94999FD9…` iguales, `EQUIVALENTE`, residuos 0 y relación 0,7089: el medidor salió 1 con `-Umbral 0.70` solo por el umbral, y cumple el 0,75 que fijó D-T7 (§1.3, §22.3). N = 3 no se corrió (D-T1) |
| Esta spec | **CONSTRUIDA — pendiente de refutación independiente**: 15 decisiones; 11 conflictos y 24 discrepancias decididos (VC-01..VC-35); 17 invariantes; 25 escenarios, los 25 con `rojo visto` (§26); 20 mutaciones; 29 pendientes (VX-21..VX-29 de la pasada post-WU03-b, §33) |
| SPEC REVIEW independiente | **Aprobado** el 20-10-2026 (`harness-spec-refuter`, invocación nueva, freeze `FE5748A4…`): 15/15 sostenidas, 17/17 refutables, 25/25 testeables, 20/20 útiles, 0 bloqueantes, 15 no bloqueantes; NB-01 y NB-04 corregidos antes de construir (§1.4); NB-02, NB-03, NB-05..NB-15 informan al builder y no cambian la spec |
| Decisión humana | Aprobación para construcción confirmada el 20-10-2026 (encabezado); las tres confirmaciones de §1.2 quedan confirmadas con ella. El umbral de §22: la persona lo fijó en **0,75** el 22-10-2026, por la regla 2 de §22.3 (D-T7, §1.3) |
| Código, tests, ADR | **Escritos** en la construcción (20 a 22-10-2026, sin commit), sobre `d86b285`. Hashes del árbol del par de cierre (`freeze-pre-cierre.txt` del orquestador): `tests/Invoke-Tests-Parallel.ps1` `8EF1A526…`; `tests/parallel-manifest.json` `8D304154…`; `tests/Compare-TestRuns.ps1` `65A7DB07…`; `tests/Measure-TestRuns.ps1` `E02F7E8E…`; `tests/Invoke-Tests.ps1` (M2) `E1834389…`; `tests/casos/75_manifest_paralelo.py` `CF158880…`; `tests/casos/75_runner_paralelo.py` `6F9DC970…`; `docs/adr/0018-dos-corredores-un-oraculo.md` `7CF5866F…`; `.claude/agents/harness-backend-engineer.md` (M1) `0DBC67C6…`; `tests/correr.py` sin cambios `CBFF4198…` |

**La respuesta corta**, que el resto justifica:

- **Dos corredores, un oráculo.** El oráculo sigue siendo la compuerta y lo único que cierra. El runner es
  un acelerador para el builder y la regresión focal; en 6.1 no cierra nada (VD-01);
- **un proceso por suite, y el proceso es el oráculo**: cada worker es `powershell.exe -File
  tests\Invoke-Tests.ps1 -SoloCaso <archivo>`. Mismo preludio, mismas aserciones, misma resolución de
  Python, misma semántica de stderr y de exit, por construcción. Es el único cambio al oráculo: un
  parámetro opt-in con la salida por defecto idéntica (VD-03, VD-04);
- **cada suite con su temporal**: `TEMP`, `TMP` y `TMPDIR` nuevos, iguales entre sí y fuera del árbol; el
  resto del entorno, el cwd y el `PATH`, heredados sin tocar (VD-05);
- **clases explícitas en un manifest**: `parallel`, `lane` (`motor`, `instalador`, `ventana`) y `serial`.
  Una suite sin entrada corre `serial` y la suite de 6.1 se pone roja por la entrada que falta (VD-06);
- **N = 2 suites vivas por defecto**, `-Workers` de 1 a 4; el límite cuenta suites, no nietos (VD-07);
- **73 y 72 no van a una cola serial al final**: forman el carril `motor`, que corre una a la vez **junto
  con** el pool. El carril dura d(73) + d(72) = 947,6 s (15,8 min) MEASURED-BASELINE; con N = 2 el piso del
  wall no lo pone el carril sino el trabajo total, W/N ≈ 25,9 min ESTIMATED (VD-08, VC-09, VC-27);
- **el resultado sale del texto del oráculo**, anclado a la última línea y cruzado con los grupos; sin JSON
  y sin tocar `correr.py` (VD-09);
- **0 verde, 1 rojo, 2 no corrió** (candado). Un error de infraestructura nunca suma pasadas (VD-10);
- **timeout = máx(3 × máximo observado, 1200 s)**, solo con medición; corta con `taskkill /T /F` sobre el
  worker, sin Job Object, sin reintento (VD-11). Con WU03-a, solo t73 pasa el piso: 2187 s (§6);
- **candado del SO** sobre `%LOCALAPPDATA%\gcba-harness\recursos\pesada.lock`, sin esperar, **solo entre
  runners** (lo que no lo toma no queda excluido: §19.2, y para eso hay una regla operativa en §28); el
  mismo mecanismo dice si vive el dueño de un temporal a barrer; nunca un pid (VD-13, VC-03);
- **equivalencia estricta, suite por suite**, sin tolerancia; con huella distinta, `NO_COMPARABLE` (VD-14);
- **el benchmark es un escenario con su test**, `tests/Measure-TestRuns.ps1`, fuera de la suite; el umbral
  normativo es 0,75, fijado por la persona con la regla de §22.3 (VD-15, D-T7).

### 1.1 Las decisiones, en una tabla

| # | Decisión | Elección | § |
|---|---|---|---|
| VD-01 | Rol del runner | Acelerador; el oráculo cierra. ADR nuevo + enmienda de `harness-backend-engineer.md` | 31 |
| VD-02 | Dueño | `harness-backend-engineer` | 31 |
| VD-03 | Modelo de proceso | Un proceso por suite; el worker es el oráculo filtrado; sin hilos ni runspaces | 9, 31 |
| VD-04 | Cambio al oráculo | `-SoloCaso` opt-in; salida por defecto idéntica; `correr.py` sin cambios | 21, 31 |
| VD-05 | Aislamiento | `TEMP=TMP=TMPDIR` por suite; nada más cambia | 12, 31 |
| VD-06 | Clases y manifest | `parallel` / `lane` / `serial`; desconocida ⇒ `serial`; nada se infiere del nombre; el runner valida la forma y la suite la política (§10.3) | 10, 11, 31 |
| VD-07 | Límite | Suites vivas; N = 2; `-Workers` 1..4 | 11, 31 |
| VD-08 | Scheduling | Más largas primero, carriles exclusivos, `serial` al final | 13, 31 |
| VD-09 | Recolección | Texto del oráculo, última línea, cruce con grupos | 15, 31 |
| VD-10 | Fallos y exit | 0 / 1 / 2; motivos cerrados; limpieza incompleta avisa en una corrida funcional (el benchmark exige cero residuos, §22.1); árbol cambiado es rojo | 17, 22, 31 |
| VD-11 | Timeout y corte | Fórmula con medición; `taskkill /T /F`; sin Job Object; sin reintento | 14, 31 |
| VD-12 | Cancelación | Un solo camino de salida para Ctrl-C y la señal inyectable; nunca 0 | 18, 31 |
| VD-13 | Candado | L1 de WU10, solo el runner, exclusivo, sin espera; mismo mecanismo para el barrido | 19, 31 |
| VD-14 | Equivalencia | Estricta por suite; huella del árbol; comparador | 20, 22, 31 |
| VD-15 | Verificación del benchmark y tests del runner | Escenario con test fuera de la suite; dos casos `75_*` | 26, 30, 31 |

### 1.2 Decisiones que se escalan

**Ninguna que bloquee.** Los once conflictos y las veintidós discrepancias se deciden con evidencia leída
(§32). Tres cosas las confirma la persona al revisar, porque cambian un contrato que otros leen, no porque
falte una elección:

1. la enmienda de `.claude/agents/harness-backend-engineer.md:62-73` y el ADR-0018 «dos corredores, un
   oráculo» (VD-01, VC-02, VC-32);
2. el parámetro `-SoloCaso` en el oráculo (VD-04);
3. la obligación nueva para todo builder futuro: un archivo nuevo en `tests/casos/` lleva su línea en el
   manifest, o la suite queda roja (VD-06).

Las tres quedaron confirmadas con la aprobación humana del 20-10-2026 (encabezado, §1.4).

Y una que **no se tomó antes de construir**, a propósito: el umbral normativo de §22. El brief lo dejaba «no
normativo hasta medir»; WU03-a midió el serial, pero la relación paralelo/serial solo la da un par. La regla
para fijarlo estaba escrita (§22.3) y se aplicó con WU03-b: D-T6 lo puso en 70 % con la relación del par 1b,
y D-T7 (la persona, regla 2 de §22.3) lo fijó en **75 %** con la relación comparable del par de cierre (§1.3).

### 1.3 Registro de enmiendas

Una enmienda posterior a la aprobación se registra acá con fecha, quién la pidió, quién la autorizó, qué
cambió y qué escenario la re-verifica. Un cambio de clase en el manifest después de la aprobación (§10.5) es
una enmienda.

**Enmienda 1: D-T1, D-T2 y D-T3 (21-10-2026).** La pidió y la autorizó Nahuel Palacio el 21-10-2026, con la
construcción en curso; la escribió `harness-task-architect`. **Motivo:** acotar el tiempo de máquina (cada
suite completa serial tarda ≈ 50–60 min en esta máquina: 49,4 y 59,5 min en WU03-a, §5.6) sin tocar ninguna
decisión VD-01..VD-15 ni la equivalencia (§20.4). No cambia los conteos (15 VD, 17 VP-I, 25 VP-E, 20 VM,
20 VX) ni ninguna marca `rojo visto`, y no agrega escenarios.

- **D-T1.** El par N = 3 de WU03-b (§5.4 paso 5, informativo) no se corre en 6.1: queda opcional, a pedido.
  Las menciones de N = 3 en §5.6, §22.2, §24 R24, VC-28, §34 y §35 se leen con esta decisión: si se corre, es
  a pedido y sigue siendo informativo; si no, su medición queda `PENDING_WU03_B` y no bloquea el cierre
  (§30 no la pide).
- **D-T2.** El par que cierra puede reutilizar la captura serial del primer par N = 2, con las condiciones de
  §5.4 («El primer par y el que cierra»), §5.7 B4 y §9.6. Es la **única excepción acotada** a «misma huella»
  (§5.1, §20.4, VD-14); la equivalencia estricta no cambia en nada más.
- **D-T3.** La única suite completa oficial de la construcción es la pata serial del primer par N = 2 de
  WU03-b: `.\tests\Invoke-Tests.ps1 -Detallado` lanzado por el medidor, capturado, con sus condiciones
  registradas; vale como compuerta del paso 10 si sale 0 (`-Detallado` no cambia el veredicto). No hay otra
  suite completa separada (§29 paso 10, §8.5, §30). Limita la construcción; no limita lo que corra el
  refutador.
- **Re-verifica:** VP-E25 (`tests/Measure-TestRuns.ps1`), que cubre también el modo de reuso, sin escenario
  nuevo; en ese modo, «las tres huellas son iguales» de VP-E25 se lee como dice §9.6. D-T1 y D-T3 no cambian
  comportamiento de código.

**Quién lee el manifest, para D-T2** (grep de `parallel-manifest` en `tests/` y `tests/casos/`, y revisión de
los barridos de `tests/casos/` —`ls-files`, `rglob`, `os.walk`, `glob`, `iterdir`, `listdir`,
`Get-ChildItem -Recurse`—, 21-10-2026, sobre el árbol en construcción; lo que esos patrones no encuentran no
está comprobado):

| Lector | Qué lee | ¿Su resultado depende del contenido del manifest? |
|---|---|---|
| `tests/Invoke-Tests-Parallel.ps1:1494` (el runner) | el manifest real | Sí, pero solo corre en la pata paralela, que en el par que cierra corre de nuevo sobre el manifest final. El oráculo no lo lee |
| `tests/casos/75_manifest_paralelo.py:22` (VP-E24 parte A) | el manifest real, su política | **Sí** ⇒ condición (2) |
| `tests/casos/63_harness_unico.py` E-61 (`63_harness_unico.py:685-697`) | el texto de **todo** archivo de `tests/` versionado o no ignorado, salvo sus dos propios (`:672`), buscando el parámetro viejo (`:35`) y las formas de análisis (`:297-299`); no nombra el archivo | **Sí**: el manifest entra al barrido ⇒ **la condición (2) incluye también `63_harness_unico.py`** |
| `tests/casos/75_runner_paralelo.py:376, 401-404` | su **propio** manifest sintético, dentro de un layout descartable; del árbol copia solo `Invoke-Tests.ps1`, `correr.py` y el runner (`:388-400`); su huella es la del layout (`:735-751`) | No |
| t63h E-01 y E-58 (`63_harness_unico.py:250-256, 642`); t64 (`64_modelo_de_dominio.py:184`) | la lista de rutas, con los no versionados | No: la ruta no cambia (mismo `git status --porcelain`). t63h E-12 y E-57 (`:317-320, 630-631`) y t64 E-34 y E-40 (`:2653, 2799-2800`) leen texto solo de `manifest.json`, `comun/`, `harnesses/`, `.claude/` y `CLAUDE.md` |
| 65, 72 y 74 (`65_contrato_de_ejecucion.py:1667-1673, 1692`; `72:2297-2302, 2323`; `74:4120-4126, 4156`) | no versionados en sus rutas protegidas | No: ninguna bajo `tests/` |
| t71 E-16 (`71_plan_2_1.py:501-502`) | solo `tests/casos/*.ps1` | No |
| `00-encoding-fuentes.ps1:21, 61`; `03-instalador.ps1:436` | solo `.ps1`, `.psm1` y `.py` | No |
| `30_b4_contabilidad.py:326-327`; `53_context_bar.py:1502-1504`; `61_conocimiento_auto_refresco.py:783-784`; `isolated-factory.ps1:19-22` (68) | JSON o texto de `comun/`, `harnesses/`, `docs/` y otras carpetas fuera de `tests/`; la fábrica aislada no copia el manifest | No |
| Los demás barridos de `tests/casos/` | layouts o proyectos sintéticos, o carpetas fuera de `tests/` | No |

**Enmienda 2: D-T4 (21-10-2026).** La pidió y la autorizó Nahuel Palacio el 21-10-2026, con la construcción en
curso; la escribió `harness-task-architect`.

- **D-T4.** VP-E08 declara `timeoutSeconds: 9` en lugar de `3` en su manifest sintético (§26 «Timeout»,
  §10.3a). El tope «en menos de 20 s» no cambia, ni la suite de 30 s, ni nada más del escenario.
- **Motivo, con evidencia medida en la construcción** (no releída por el arquitecto): en esta máquina un
  `powershell.exe -NoProfile -NonInteractive` frío tarda 2,65–3,25 s en arrancar (`python -c pass`, 0,15 s);
  con 3 s el worker moría por timeout antes de empezar la suite y la precondición del test salía roja (3/3
  con la máquina quieta; `75_runner_paralelo.py` daba 822/823). Con 9 s: el control dio 17/17 dos veces y la
  mutación VM-19a (matar solo al worker) se ve en rojo.
- **Por qué no cambia ninguna decisión:** el 3 cumplía un solo rol, ser un entero > 0 que la fórmula del
  manifest real no admite (§10.3b, VD-11); 9 lo cumple igual, porque la fórmula exige ≥ 1200. VP-I13, VP-E24
  parte B y VD-11 no nombran el valor y siguen igual. No cambia los conteos (15 VD, 17 VP-I, 25 VP-E, 20 VM,
  20 VX) ni ninguna marca `rojo visto`, y no agrega escenarios.
- **Re-verifica:** VP-E08 (`75_runner_paralelo.py`), sin escenario nuevo.

**Enmienda 3: D-T5 y D-T6 (22-10-2026).** La pidió y la autorizó Nahuel Palacio el 22-10-2026, con la
construcción en curso; la escribió `harness-task-architect`.

- **Evidencia** (par 1b de WU03-b, 21/22-10-2026, medido por el orquestador, no releído por el arquitecto
  salvo `registro.txt` y `comparador.txt`; capturas en `C:\t\hpm-261021-223656\`, copia en
  `C:\dev\_respaldos\task6.1\construccion\wu03b-par1b\`): `Measure-TestRuns.ps1 -Workers 2`, con `-Detallado`
  en las dos patas. Serial **3280,1 s**, exit 0, 48841/48841; paralelo **2158,2 s**, exit 0, 48841/48841; las
  tres huellas iguales (`E3CAD0FB…`, 831 archivos, 10 líneas de status); relación **0,658**. El comparador dio
  `NO_EQUIVALENTE` **solo** por el punto 5 de §20.4: ~129 nombres de filas `ok` de suites existentes llevan
  datos volátiles (la hora en `57_aceptar_fuentes` E-19; rutas del temporal de la pata en
  `63_compuerta_del_flujo` E-28, E-31 y E-65; valores observados en `75_runner_paralelo`), así que dos corridas
  cualesquiera, aun serial contra serial, nunca tienen el mismo multiconjunto de filas. Los puntos 1–4 y 6
  dieron iguales. El medidor contó además como residuo dos líneas `AVISO LIMPIEZA_INCOMPLETA` que eran nombres
  de filas `ok` de `75_runner_paralelo` (VP-E20, VP-E21 citan el aviso de runners anidados); `tmp-paralelo`
  quedó vacío. Eso es un defecto del medidor, que corrige el builder; no cambia la spec.
- **D-T5.** Los pares de WU03-b corren las dos patas **sin `-Detallado`**: la serial es exactamente
  `.\tests\Invoke-Tests.ps1` (el comando de la compuerta, §30) y la paralela
  `.\tests\Invoke-Tests-Parallel.ps1 -Workers <n>` (§5.4, §9.6, VP-E25). El punto 5 de §20.4 sigue definido
  para el comparador (VP-E15..VP-E17 lo siguen probando sobre layouts sintéticos), pero **no se evalúa en el
  benchmark**: en el árbol real es insatisfacible por construcción. Los puntos 1–4 y 6 siguen estrictos, sin
  tolerancia; VC-05 y VD-14 no cambian. D-T3 se lee con D-T5: la única suite completa oficial de la
  construcción es la pata serial del primer par válido. Las menciones de `.\tests\Invoke-Tests.ps1 -Detallado`
  como pata del benchmark que quedan en el texto de D-T3 (arriba) y en §35 se leen con D-T5.
- **D-T6.** El par 1b es **el primer par N = 2** a efectos de §10.2 y §5.7 B1 (sus duraciones por suite de la
  pata paralela alimentan `maxSeconds`: corrida con exit 0, `ok == total`, misma huella antes y después,
  condiciones registradas; B1 no exige `EQUIVALENTE`) y de §22.3 (relación 0,658 ≤ 0,70 ⇒ **el 70 % pasa a
  normativo** y VP-E25 se verifica con `-Umbral 0.70` sobre el par que cierra). Su pata serial (exit 0,
  48841/48841) es la única suite completa oficial (D-T3). El próximo par es **el que cierra**, sobre la huella
  final, **sin reuso de la pata serial**: el medidor cambia, así que la condición de D-T2 (único cambio
  `tests/parallel-manifest.json`) no se cumple; sus duraciones no realimentan el manifest (§5.7 B4). Las
  menciones del 70 % como candidato (§1.2, §22.2) se leen con D-T6.
- **§30 con D-T5 y D-T6** (la única lectura coherente de las dos, con la misma autorización): el punto 1 de
  §30 («`.\tests\Invoke-Tests.ps1` sale 0 sobre el árbol final») lo sostiene la pata serial del par que
  cierra, que es exactamente el comando de la compuerta sobre la huella final (D-T5); la pata serial del par
  1b fue la única suite completa oficial de los pasos 1–10 de la construcción (D-T3, D-T6), no la del árbol
  final; las dos se registran en el benchmark. El punto 3 lo sostiene el par que cierra.
- **Por qué no cambia ninguna decisión:** VD-01..VD-15, la equivalencia del comparador (§20.4) y su prueba
  (VP-E15..VP-E18) quedan iguales; cambia qué se le pide al benchmark y se aplica la regla escrita de §22.3. No
  cambia los conteos (15 VD, 17 VP-I, 25 VP-E, 20 VM, 20 VX) ni ninguna marca `rojo visto`, y no agrega
  escenarios.
- **Re-verifica:** VP-E25 (`tests/Measure-TestRuns.ps1`), sin escenario nuevo.

**Enmienda 4: D-T7 (22-10-2026).** La decidió Nahuel Palacio el 22-10-2026 («vamos con la 1»), con la
construcción terminada, aplicando la regla 2 de §22.3; la escribió `harness-task-architect`.

- **Evidencia** (par de cierre de WU03-b, 22-10-2026 09:17 → 10:42, medido por el orquestador; capturas en
  `C:\t\hpm-261022-091757\`, copia en `C:\dev\_respaldos\task6.1\construccion\wu03b-cierre\`; leídos por el
  arquitecto `registro.txt`, `comparador.txt` y `w3b-cierre.meta.txt`): `Measure-TestRuns.ps1 -Workers 2
  -Umbral 0.70`, las dos patas sin `-Detallado` (D-T5). Serial **2976,9 s** (49:36), exit 0, 48841/48841;
  paralelo **2110,4 s** (35:10), exit 0, 48841/48841; las tres huellas `94999FD9…` iguales; `EQUIVALENTE`
  (35 grupos PS, 75 Py); residuos atribuibles 0; mismo `bash` en las dos patas; relación **0,7089**. El
  medidor salió 1 con un único motivo, `UMBRAL` (2110,4 > 0,70 × 2976,9 = 2083,8 s).
- **Por qué la relación de D-T6 no era comparable:** el 0,658 del par 1b salió con `-Detallado` en las dos
  patas, que agranda la salida (4,5 MB por pata contra 5,6 y 10,5 KB sin él) y la serial más que la paralela:
  3280,1 contra 2976,9 s (≈ +5 min) y 2158,2 contra 2110,4 s (≈ +1 min). Los dos pares no tienen la misma
  huella (entre ellos cambiaron el manifest y el medidor, D-T6), así que la atribución es una inferencia, no
  una medición; la relación que vale para el umbral es la del par sin `-Detallado`, la del cierre.
- **D-T7.** La regla 1 de §22.3 no aplica con la relación comparable (0,7089 > 0,70). Por la regla 2, la
  persona acepta un umbral cercano a la relación medida: **0,75 es el umbral normativo** y VP-E25 se verifica
  con `-Umbral 0.75`. Reemplaza el «70 % normativo» de D-T6; el resto de D-T6 (el par 1b como primer par para
  `maxSeconds`, el par que cierra sin reuso) sigue igual. **No se repite el par de cierre:** con 0,75 cumple
  (0,7089 ≤ 0,75; 2110,4 ≤ 2232,7 s) y todas las demás condiciones de VP-E25 ya se cumplieron en él. **La
  equivalencia no se relajó:** los puntos 1–4 y 6 de §20.4 siguen estrictos (VD-14, VC-05).
- **Por qué no cambia ninguna decisión:** §22.3 preveía exactamente esta salida (regla 2); VD-01..VD-15,
  VP-I01..VP-I17 y los escenarios quedan iguales; cambia el número que recibe `-Umbral`. No cambia los conteos
  (15 VD, 17 VP-I, 25 VP-E, 20 VM) ni agrega escenarios.
- **Re-verifica:** VP-E25 (`tests/Measure-TestRuns.ps1 -Workers 2 -Umbral 0.75`), sin escenario nuevo. El
  comando con `0.75` no se corrió en la construcción: el 0 se deduce del registro del par de cierre, y quien
  refuta corre VP-E25 (§26, «Cómo se verifica»).

**Pasada post-WU03-b (22-10-2026).** La pidió el orquestador con WU03-b terminada; la escribió
`harness-task-architect`. No es una enmienda de decisiones: pone lo que la spec esperaba de WU03-b (§5.6,
§29 paso 10). Cambió:

- cada valor que esperaba a WU03-b, medido o decidido, con su fuente (§1, §1.2, §5, §11, §13.3, §22, §24,
  §29 paso 10, §31 VD-07 en su línea de RAM, §32 VC-09, §34, §35); el piso de RAM **no se fija** en 6.1 (§5.2):
  se registran los mínimos observados; en §30, la nota sobre la huella del par de cierre;
- las marcas `rojo visto` de VP-E01..VP-E25 (§26) y la columna «Visto en rojo» de §27, desde los registros de
  las etapas 2, 3, 8, 8b, 9 y 9c y de la preparación del cierre;
- correcciones de texto que no cambian ninguna VD: el orden real de §9.1; observaciones en §4 (combinación del
  oráculo), §5.2 (`TEMP` corto), §14.1 (`MUERTA` contra `SIN_RESUMEN`), §17 (F6b y F9) y §27 (VM-02, VM-16,
  VM-19); la línea de medición de §35 con D-T5;
- §33: VX-07 y VX-12 ampliados; **VX-21 a VX-29 nuevos** (observaciones de la construcción). Conteos: 15 VD,
  17 VP-I, 25 VP-E, 20 VM, **29 VX**.
- **La huella cambia con esta pasada.** El par de cierre midió la huella `94999FD9…`; esta pasada cambia
  `spec.md` y agrega `benchmark-2026-10-22.md`, los dos en `docs/cambios/verification-pipeline-performance/`, y
  los pendientes de §29 paso 11 cambiarán FH e I. Ver §30.

### 1.4 Historial pre-aprobación

Las pasadas anteriores a la aprobación no son enmiendas (§1.3 registra solo lo posterior a la aprobación):
ninguna cambió una decisión. Después de esta tabla hay enmiendas posteriores a la aprobación, D-T1..D-T7
(21-10-2026 y 22-10-2026), y la pasada post-WU03-b, registradas en §1.3; no son pasadas pre-aprobación ni un
freeze nuevo.

| Pasada | Fecha | Qué cambió | Dónde quedó | SHA256 |
|---|---|---|---|---|
| Borrador | 19-10-2026 16:09 | Consolidación de los especialistas y de K1-K11 | Fuera del repo | `87B0A6496A2C07C42790E34D95CBBD735CC14447AA1BC4BC6AFC2779E1C068E8` |
| Consistencia | 19-10-2026 | Cuatro correcciones de consistencia, sin decisiones nuevas | `C:\dev\_respaldos\task6.1\spec.md` | `85E32D405ECB8F3BFD9590D3CAC772D6B099C8568313F25859B243C290B52B1B` |
| Baseline real + WU03-a | 20-10-2026 | Baseline `d86b285`; §2.2 revalidada; WU03-a incorporada (§5.6, §6 con tiempos, §13.3, §22, §24, §35); D1-D9 del analista decididas dentro de las VD; VC-20..VC-33; VX-19 y VX-20; precisión de VP-E23 | Esta spec, en el repo (primera versión) | `B3A3E633B5D6F1C3C2633731D54EFA3031094B5605FFDB3AA6BCA2B431B8DBDA` |
| Pre-review | 20-10-2026 | Cuatro correcciones de consistencia, sin decisiones nuevas: el freeze del SPEC REVIEW; §29 sin suite completa antes del paso 10; el ciclo de vida de `hpp-<id>.lock` (§19.5, §16.5, VP-E21, VP-E25, §35); `reason` separado en política ejecutable y revisión semántica (§10.2, §10.3b, VP-E24, VP-I17) | Esta spec, en el repo | `FE5748A4DE1B42308DEBB573C5CA75559D6E6FC035F9FB80111D83C5EBDC1C89` — **el freeze sobre el que se hizo el SPEC REVIEW independiente** (aprobado, 0 bloqueantes, 15 no bloqueantes) |
| Pre-construction clarification (esta) | 20-10-2026 | Dos correcciones locales señaladas por el SPEC REVIEW, sin cambio de VD-01..VD-15 ni de los conteos: **NB-01** VP-E24 reparte su evidencia entre `75_manifest_paralelo.py` (parte A, política, sin procesos) y `75_runner_paralelo.py` (parte B, forma en el runner, con procesos), un solo escenario (§10.3, §10.4, §6 fila 98, VP-I17, VP-E24, §26 «Cómo se verifica», §29 pasos 3-4, VD-15, VC-34); **NB-04** §8.3 dice la regla real de `00-encoding-fuentes.ps1`: BOM en `.ps1`/`.psm1` con no ASCII, nunca BOM en `.py` (E-28) (VC-35). Registra además el resultado del SPEC REVIEW y la aprobación humana (encabezado, §1) | Esta spec, en el repo | **El FINAL PRE-CONSTRUCTION SPEC FREEZE es el SHA256 que reporta el orquestador al terminar esta pasada**, calculado sobre este archivo y no insertado acá |

---

## 2. Baseline

### 2.1 Versión de partida

Leído por el arquitecto sobre `d86b285` el 20-10-2026, solo con git de lectura:

| Hecho | Valor |
|---|---|
| Rama | `main` |
| HEAD | `d86b285a9d0a4610a44a15ba3ca455be42d2edaa`, «0.34.0 cierra: Knowledge Access, una frontera de lectura de conocimiento con cita y revisión», 19-10-2026 22:12:19 -0300 |
| `VERSION` | `0.34.0` |
| Tag | `v0.34.0`, anotado, pela a `d86b285` (`git rev-parse "v0.34.0^{commit}"`) |
| `git status --porcelain --untracked-files=all` | vacío |
| `git ls-files` | 823 archivos |
| Huella de §5.1 | `FDEF538098DC593B4E3537BB945A8F365A788E7DEC29B80E501A056E58BF4C70`; la calculó el orquestador con la herramienta de WU03-a, idéntica en sus cuatro tomas (§5.6); el arquitecto no la recalculó (la guarda no deja hashear) |

Es la versión de partida de 6.1 y la de VP-E23. La nota 0.34.0 la fija como base de 6.1 («parte de la
baseline de este cierre: no de la de 0.33.0», `docs/versiones/0.34.0.md:218-219`). No existe en el repo una
marca «TASK 6.1 BASELINE READY» (discoverer): la baseline queda fijada en esta sección.

### 2.2 La revalidación sobre la baseline real

Hecha el 20-10-2026 sobre `d86b285`. **Ninguna decisión cambió**: no hay enmienda y §1.3 sigue vacío.

| Qué se re-verificó | Resultado | Origen |
|---|---|---|
| Cada cita `archivo:línea` de la spec (más de 180) | **IGUAL**: 0 movidas, 0 cambiadas, 0 no encontradas. El borrador ya había leído el árbol que se commiteó. t72 tiene +2 líneas netas (`CONCEPTOS = 85` → `89` y un comentario, `72:2251-2256`), anteriores a las citas `72:2297-2302` y `72:2330-2335` y ya contadas | discoverer §A; guardián |
| La lista de `tests/casos/` | **IGUAL**: 24 `.ps1` + 73 `.py` = 97, más `.gitkeep` (versionado) y `__pycache__/` (ignorado); mismos nombres, mismo orden y mismos conteos por clase que §6, filas 1-97. Las filas 98-99 (`75_*`) no existen todavía | discoverer §B; WU03-a (97 suites solas) |
| Las listas de protegidos de t72 (`72:2297-2302`, `PROTEGIDOS`) y t74 (`74:4120-4128`, `PROTEGIDOS_DE_KNOWLEDGE_API`) | **IGUAL**: ninguna nombra `tests/`, `.claude/agents/`, `.claude/`, `tests/Invoke-Tests.ps1`, `CLAUDE.md` ni `docs/cambios/**` (`harnesses/desarrollo/agents` es del producto). Protegen `install.ps1` y `manifest.json`, que 6.1 no toca. `65_contrato_de_ejecucion.py:1667` tampoco. VD-01 y VD-04 no chocan | discoverer §C; guardián |
| El texto que piden 66 y t72 del oráculo | **IGUAL**: `sys.executable` en `Invoke-Tests.ps1:245` (bloque 240-248) y `correr.py` en `Invoke-Tests.ps1:237`, exigidos por `66_integrity_cleanup.py:474` (E-22) y `72:2335` (ME-E51); `66_integrity_cleanup.py:475-476` prohíbe la línea `Get-Command` | discoverer §D; leído por el arquitecto |
| El número libre del ADR | **Dato nuevo**: `0017` es de Task 6; el siguiente libre es **0018**. `0007` es un hueco deliberado (`docs/codebase/docs.md:33`) con un ítem que propone llenarlo (`PENDIENTES-I.md:67`): **no se usa** (VC-32) | discoverer §E; guardián |
| El tag de la versión de partida | **Dato nuevo**: `v0.34.0`. El blob de `tests/Invoke-Tests.ps1` es el mismo en `v0.33.0`, `v0.34.0` y el árbol (`3d078493df6983d66488ed0277bab3a88d5aaf85`), pero el blob es LF y el archivo del árbol CRLF (`git ls-files --eol` = `i/lf w/crlf`; `.gitattributes:11`, `*.ps1 text eol=crlf`, leído): VP-E23 compara la identidad por blob id, no por sha256 de bytes crudos (VC-20) | discoverer §F |
| Las mediciones de §5 | **Dato nuevo**: WU03-a hecha (§5.6); `maxSeconds` y `timeoutSeconds` de las 97 llenos (§6); lo paralelo quedaba para WU03-b, medido el 21 y 22-10-2026 (§5.6) | WU03-a; analista |
| Las afirmaciones del AS-IS | **IGUAL**: ninguna quedó falsa. Datos nuevos: dependencias de t74 (§6 fila 97), de 74-inst (§6 fila 24), las precondiciones del oráculo de la nota 0.34.0 (Git Bash al frente, no elevado: §5.2, VC-26) y la falla única de t72 E34 en el cierre (`docs/versiones/0.34.0.md:149-158`: §10.5, VC-30) | discoverer §G |
| El release 0.34.0 contra VD-01..VD-15 | **0 contradicciones.** La nota repite el diseño de FH («staff», «grupo serial al final», `docs/versiones/0.34.0.md:221-223`) sin decidirlo y dice que no tocó la spec de 6.1 (`:224`) | guardián |

### 2.3 Lo medido antes (MEASURED-previa, no baseline)

| Fecha | Árbol | Total | Exit | Wall | Condiciones |
|---|---|---|---|---|---|
| 16-10 | 0.33.0 release, copia | 45.534 (PS 932, Py 44.602) | 0 | sin registrar | sin elevar, TEMP propio |
| Verificación de Task 5 | 0.33.0, copias | 45.534 | 0 | 66, 74, 44, 57, 45 min | con otras cargas (FH:2262-2264) |
| 18-10 21:03→21:51 | Task 6 construida, copia | 47.571 | 0 | 47 min | builder, etapa 8 (FH:2264-2265) |
| 19-10 | Task 6 etapa 9, copia | 47.682 | 0 | 51 min | coordinador |
| 19-10 10:18→11:59 | Task 6 F1 | 47.682 | 0 | 1:40:54 | refutador en paralelo con otras cinco corridas |
| Cierre de 0.34.0 | 0.34.0, copia idéntica por hash al árbol | 47.957 (PS 968, Py 46.989) | 0 | 43,7 min | una sola corrida; antes, una falla de t72 E34 aislada y no reproducida (`docs/versiones/0.34.0.md:149-158`) |
| 0.34.0, resumen de la nota | 0.34.0 | — | — | 47 a 101 min | 47 quieta, 84 con otras sesiones, 101 con cinco refutadores (`docs/versiones/0.34.0.md:191-192`; `CHANGELOG.md:65`) |

Por suite, serial, 18-10 (FH:2265-2268): t73 ≈ 20 min; t72 ≈ 6; 63-hu ≈ 5,4; t64 ≈ 3,3; t65 ≈ 1,8; t74 ≈ 40 s.
Prueba de concepto del coordinador, 3 workers, con contención (19-10, del orquestador, no releída): t72
110,9 s; t65 56,4 s; t64 101,8 s; 71 24,2 s; t63c 75 s; `72-motor-de-ejecucion-instalador.ps1` 12,1 s;
63-hu 128,7 s.

**Contra la MEASURED-BASELINE** (§5.6), la serie por suite del 18-10 es **0,61-0,69× más lenta**: t73 0,61×,
t72 0,61×, 63-hu 0,69×, t64 0,62×, t65 0,66×, t74 0,61× (analista). No es el código: Task 6 no tocó t73 y da
0,61×. Esas seis cifras no salen de la corrida de 47 minutos (sumarían 36,5 de 47 y dejarían 10,5 para las
otras 91 suites, que hoy tardan 28,6; FH:2264-2268 dice «about» y «the same day»). Hipótesis compatibles, sin
demostrar: otra carga y un `%TEMP%` global con miles de entradas (FH:2124-2125: `me72-*` de 5143 a 10107). La
PoC de 3 workers da valores **menores** que la suite sola de hoy (otro árbol u otro método): no sirve para
estimar f. Nada de esta sección alimenta `maxSeconds`, `timeoutSeconds` ni un umbral (§5.7 B1, VC-23). Las
tres cifras de rango que circulan para la misma medición —«45 to 70» (FH:2260), «47 a 101»
(`docs/versiones/0.34.0.md:191`) y «45 a 85» (`docs/cambios/knowledge-api/verificacion.md:192`)— se citan tal
cual y no deciden nada (VC-31).

---

## 3. Problema

- La suite completa tarda **49,4 y 59,5 minutos** en dos corridas seguidas, sin otra corrida pesada, sobre
  `d86b285` (MEASURED-BASELINE, §5.6), y entre **43,7 y 101 minutos** según la carga (MEASURED-previa, §2.3).
  Una Task la corre muchas veces: el builder, el coordinador después de cada etapa, el refutador y el closer
  (FH:2268-2270). La persona que encarga las Tasks lo pidió el 18-10-2026: «no podemos tardar tanto con los
  tests» (FH:2272-2273).
- Los dos motores corren **un archivo a la vez**, en dos procesos en serie: los `.ps1` por dot-source en el
  proceso del oráculo (`Invoke-Tests.ps1:174-182`) y los `.py` importados por `correr.py` en otro
  (`correr.py:57-76`, lanzado en `Invoke-Tests.ps1:256`).
- **No hay timeout**: si un caso se cuelga, la compuerta se cuelga (`Invoke-Tests.ps1:256` sin límite).
- **No hay coordinación entre corridas pesadas**: tres o cuatro suites completas a la vez en la misma
  máquina (copias en `%TEMP%\rt6-*`, `C:\dev\_build\*`) compiten por CPU y RAM; el 19-10 Claude Code mató
  por memoria tres corridas lanzadas juntas (del orquestador, no releído), y en el cierre de 0.34.0 una
  corrida se perdió por un corte de la máquina y de memoria (`docs/versiones/0.34.0.md:159-160`). Bajo carga,
  los casos del instalador fallan al azar (FH:1002-1017) y E-58 de 55 falló una vez (FH:1042). 6.1 coordina
  técnicamente solo a los runners entre sí (§19.2); para el resto de los trabajos pesados deja una regla
  operativa (§28), no un candado.
- Paralelizar sin diseño rompe: hay cuatro choques demostrados entre procesos y cinco ventanas de tiempo
  fijas (WU04, §7).

Lo que esta Task tiene que contestar: **la arquitectura mínima y verificable para correr en paralelo las
suites que se pueden, aislar sus temporales, separar las incompatibles y dar un resultado semánticamente
equivalente al oráculo**: mismo árbol, mismas suites, mismas aserciones, misma semántica pasa/falla, mismo
total, mismo exit, menos wall clock.

---

## 4. AS-IS

| Aspecto | Hoy | Evidencia |
|---|---|---|
| Enumeración PS | `Get-ChildItem casos -Filter '*.ps1' \| Sort-Object Name`; ninguno ⇒ `exit 1` | `Invoke-Tests.ps1:166-172` |
| Enumeración Py | `sorted((RAIZ/"tests"/"casos").glob("*.py"))`; `-k` por subcadena del nombre | `correr.py:57-59` |
| Orden dentro de un `.py` | `sorted(dir(modulo))` filtrado por `test_` | `correr.py:70-72` |
| Ejecución PS | Dot-source de cada `.ps1` en el mismo scope y proceso; excepción ⇒ una fila «el archivo de casos se pudo cargar» con grupo `$caso.BaseName`, leído de la variable del bucle | `Invoke-Tests.ps1:174-182` |
| Ejecución Py | `exec_module` por archivo en un proceso; falla al cargar ⇒ una fila; un `test_` que tira ⇒ una fila con su nombre | `correr.py:61-76` |
| Grupos | PS: los pone `Set-Grupo`, no el archivo; se juntan con `Group-Object` | `Invoke-Tests.ps1:33-36, 188` |
| | Py: `t.grupo = caso.stem`, un grupo por archivo | `correr.py:62` |
| Resumen PS | `OK g (n)` / `FALLA g (m/n)`, `Fallos:`, `ok/total pasaron (PowerShell).` | `Invoke-Tests.ps1:190-223` |
| Resumen Py | `OK g (n)` / `FALLA g (n)`, líneas `MAL g / nombre detalle`, `ok/total pasaron.`; exit 1 si falló algo | `correr.py:85-93` |
| Combinación | Regex `(\d+)/(\d+) pasaron\.` sobre toda la salida Py, **primer** match; sin match ⇒ falla propia. **Observado en WU03-b (par 1, 21-10-2026):** con `-Detallado`, el nombre de una fila `ok` que contiene ese texto (`75_runner_paralelo`, `VP-E04 (a) el 3/4 pasaron. …`) se toma como resumen: el oráculo imprimió `971/972` y salió 1 con todo verde (PS 968/968, Py 47873/47873). Lo mismo puede pasar sin `-Detallado` con el detalle de una fila `MAL`, que sale antes del resumen. Defecto del oráculo, no de 6.1: VX-21 | `Invoke-Tests.ps1:262-270`; `wu03b-par1\comparador.txt` |
| Exit | 0 solo si no falló nada PS, `correr.py` dio 0 y `ok == total` | `Invoke-Tests.ps1:282-292` |
| Stderr de Python | `$ErrorActionPreference='Stop'` + `2>&1`: una línea en stderr corta la corrida con exit 1 | `Invoke-Tests.ps1:20, 256`; `61_conocimiento_auto_refresco.py:1077` («Invoke-Tests.ps1 lo toma como error y corta»). Observación de PS 5.1; VP-E07 la fija |
| Python | Prueba `python`, `py`, `python3` y exige `sys.executable`; lanza `correr.py` por ruta | `Invoke-Tests.ps1:237, 240-254` (`sys.executable` en `:245`); lo exigen `66_integrity_cleanup.py:474` y `72:2335` |
| Marcas | `Clear-MarcasHarness` borra `%TEMP%\gcba-harness\*.avisado` una vez, al empezar | `Invoke-Tests.ps1:128-142, 164` |
| Temporal | El runner no fija `TEMP`/`TMP`/`TMPDIR` | `Invoke-Tests.ps1` entero |
| Residuos de las suites | Una corrida completa deja **760 entradas** en su temporal (más la carpeta de marcas); 256 son de t72 y t73; ninguna de un `.ps1` | WU03-a, recuento del analista (§5.6); FH:2119-2133 |
| Fábrica aislada | Copias en el temporal con marca `{pid, arranque}`; barrido de dueños muertos en cada `New-FabricaAislada` | `isolated-factory.ps1:27-85` |
| Timeouts | Ninguno en el runner; dentro de casos, hasta 300 s (`WaitForExit(300000)`, p. ej. `63-harness-unico-instalador.ps1:70`, `74-knowledge-api-instalador.ps1:46`) y 600 s (`64_modelo_de_dominio.py:235`) | grep leído |
| `install.ps1` y la suite | **No la corre**: sin `Invoke-Tests` ni `correr.py`; su compuerta es `Test-HooksInstalados` | `install.ps1:1081, 1814, 2160` (grep) |
| Salida estructurada | Ninguna | `Invoke-Tests.ps1`, `correr.py` |

---

## 5. Benchmark

Esta sección es el **protocolo**, reproducible, para dos usos: **WU03-a** (antes de construir, sobre la
baseline real: cuánto tarda el oráculo y cada suite), **hecha** el 20-10-2026 (§5.3, §5.6), y **WU03-b** (al
cerrar la fase A: serial contra paralelo), **hecha** el 21 y 22-10-2026 con el runner y el medidor construidos
(§5.4, §5.6).

### 5.1 La huella del árbol

Una corrida se compara con otra **solo si tienen la misma huella**:

```
huella = HEAD (git rev-parse HEAD)
       + sha256 de `git status --porcelain --untracked-files=all`
       + sha256 de la lista ordenada (ruta, tamaño, sha256) de `git ls-files -c -o --exclude-standard`
```

Lo ignorado (`__pycache__/`, `*.pyc`: `.gitignore:42-43`) no entra. El HEAD solo no alcanza: t63h y t64
cuentan los no versionados (`63_harness_unico.py:65`, `64_modelo_de_dominio.py:184`, discoverer).
La huella se toma antes y después de cada corrida; si cambia, el par no se compara. La de la baseline es
`FDEF5380…` (§2.1).

### 5.2 Condiciones y precondiciones

**Precondiciones del oráculo, y por lo tanto del benchmark.** No las impone el runner (VC-04: hereda el
entorno); las cumple quien lanza, y el medidor las registra:

- **Git Bash al frente del `PATH` del proceso que lanza la suite.** Con el stub de WSL primero,
  t63c E-38 falla incluso sobre `v0.33.0` (`docs/versiones/0.34.0.md:163-166, 249-250`; lo dice la nota, no lo
  verificó el arquitecto). Si quien lanza antepone algo al `PATH`, lo **deriva de `(Get-Command git).Source`**
  (la carpeta `bin` de esa instalación de Git), **nunca de una ruta fija de usuario** como la que usó la
  herramienta de WU03-a (`medir.ps1:15`, analista).
- **No elevado.** La nota lo pide (`docs/versiones/0.34.0.md:249-250`); la premisa de QG1 E-05b es que el
  arranque de System (pid 4) sea ilegible (`68-isolated-factory.ps1:170-181`, leído).
- **Un clon con los tags y commits base que leen las suites**: `v0.33.0` para t74 (`74:3643`), `fdca5ce`
  para t72, y `ea2dff7`, `4c6f0f3` y `f9393cf` para t63h, t64 y t65 (discoverer). Una copia por
  `git archive` no los tiene.

**Condiciones, antes de cada corrida**: cada pata de un par y cada tramo de un protocolo (VC-25):

- RAM libre (CIM `FreePhysicalMemory`) y total; CPUs lógicas;
- procesos `claude`, `python` y `powershell` con pid, padre y línea de comando, separando los del medidor;
- si hay otra corrida pesada (el candado y una inspección de procesos);
- `Get-Command bash -All` en el proceso lanzador, sin tocar el `PATH`; el `bash` efectivo del proceso que corre
  la suite y la primera línea de su `--version`; `shutil.which("bash")` con ese mismo entorno; si se antepuso
  algo al `PATH`, qué y derivado de dónde; cuál es el proceso lanzador;
- `git --version`; `TEMP`, `TMP`, `TMPDIR` y su formato (largo o 8.3); elevado o no; workers; versión de
  partida y huella.

**Piso de RAM: no se fija en 6.1** (decisión de la pasada post-WU03-b). La regla era «el pico de una corrida
paralela más 2 GB de margen», y hasta medirlo los pares corrían sin piso y solo registraban (analista:D5).
WU03-b no midió ese pico: el medidor muestrea `FreePhysicalMemory`, que es de toda la máquina, sin muestreo por
proceso (§5.5), y con tres procesos `claude` vivos. Ningún escenario ni §30 piden el piso, así que quedan los
mínimos registrados y el piso pasa a VX-28. Mínimos de RAM libre (de 23,71 GB), MEASURED-WU03-b:

| Par | Pata serial | Pata paralela | Caída en la paralela (primera − mínima) |
|---|---|---|---|
| 1 (21-10, 20:11) | 14,00 GB | 14,31 GB | 0,82 GB |
| 1b (21/22-10, 22:36) | 13,67 GB | 14,10 GB | 0,79 GB |
| Cierre (22-10, 09:17) | 11,55 GB | **3,20 GB** (a los 2001,7 s) | 8,91 GB, **sin atribuir**: al terminar la pata quedaban 5,5 GB libres con ningún proceso de la corrida vivo, así que la caída no es solo del runner |

Evidencia serial, MEASURED-BASELINE (WU03-a, 20-10): con el oráculo solo y dos sesiones de Claude Code
abiertas, la RAM libre nunca bajó de **6,70 GB**. No es el consumo del oráculo (sin muestreo por proceso; no
verificado si `FreePhysicalMemory` cuenta la memoria en espera). El 19-10 hubo cortes con ~4,3 GB libres (del
orquestador, no releído).

**`TEMP` corto, observado en WU03-b** (par 1, 21-10-2026): con el temporal del medidor en
`C:\dev\_build\w3b\…`, la pata paralela dio 26 filas rojas de `75_runner_paralelo.py` en su guarda de
`MAX_PATH` (`…\tmp-paralelo\hpp-<id>\s099\t61_…`: 79 caracteres > 70), que en el oráculo no salen porque no
hay `hpp-<id>\s<nnn>` en el medio. Los pares siguientes corrieron con `C:\t`. No es una precondición nueva:
es R14 materializado, y el arreglo de fondo es VX-26.

### 5.3 WU03-a: el serial y cada suite — hecha

1. Máquina sin otra corrida pesada (ni la verificación de una Task ni lotes de mutaciones).
2. Dos corridas de `.\tests\Invoke-Tests.ps1 -Detallado` sobre la misma huella, con `Stopwatch` alrededor,
   salida entera a un archivo fuera del repo. Se registran wall, total, exit.
3. Duración de cada suite sola, en serie: los `.py` con `python tests\correr.py -k <archivo>`; los `.ps1`,
   antes de VD-04 con una copia del preludio fuera del repo (la de la PoC, rotulada como herramienta de
   medición), después con `Invoke-Tests.ps1 -SoloCaso <archivo>`.
4. Resultado: la tabla `suite → segundos` que llena `maxSeconds` del manifest (§10.2) y el baseline de §35.

**Cómo se hizo** (20-10-2026, 09:33 → 12:14, el orquestador): sobre el árbol real `d86b285`, con
`TEMP=TMP=TMPDIR` propios, nuevos y vacíos (`C:\dev\_build\wu03a\tmp`), Git Bash primero, sin elevar y sin otra
corrida pesada; los `.ps1` con la copia del preludio (`runner-ps.ps1`, herramienta de medición), los `.py` con
`correr.py -k` (`medir.ps1:115-135`). **Desvío registrado:** las condiciones se tomaron una sola vez, antes de la
corrida 1 (`medir.ps1:45-71`, fuera del bucle), y no antes de cada corrida como pide §5.2. La medición vale
como baseline igual (las cuatro huellas coinciden y nada de lo que no se registró decide un número); desde
WU03-b rige §5.2 tal cual (VC-25).

🔴 La regla de 12 corridas del staff engineer (`harness-staff-engineer.md:66-67`, p50 de al menos 12) no se
aplica: doce corridas de 50 minutos no son viables (WU05:R8). Se reemplaza por: dos seriales, y para cada
dato que alimenta un umbral, el **máximo** observado, nunca la media.

### 5.4 WU03-b: serial contra paralelo

Con el medidor (`tests/Measure-TestRuns.ps1`, §9.6), sobre la versión final del árbol de 6.1:

1. condiciones (§5.2) y huella;
2. `.\tests\Invoke-Tests.ps1`, exactamente el comando de la compuerta, sin `-Detallado` (D-T5, §1.3),
   capturado; wall;
3. huella; condiciones; `.\tests\Invoke-Tests-Parallel.ps1 -Workers 2`, sin `-Detallado` (D-T5), capturado;
   wall; huella;
4. el comparador sobre las dos salidas;
5. lo mismo con `-Workers 3`, en otro par (informativo: el que cierra es N = 2). **En 6.1 no se corre**: queda
   opcional, a pedido (D-T1, §1.3);
6. registro en `docs/cambios/verification-pipeline-performance/benchmark-<fecha>.md`.

**Cada pata** corre con `TEMP=TMP=TMPDIR` **nuevos y vacíos, propios de esa pata y del mismo formato**: la del
oráculo, en una carpeta nueva; la del runner, con esa carpeta como `TempBase` (§5.7 B2). Así la pata serial no
arrastra los 760 residuos por corrida de §5.6 ni el `%TEMP%` global, que sesgaría el par a favor del paralelo
(R26, analista:D3). Las dos patas heredan **el mismo entorno del medidor**: el medidor no toca el `PATH`
(VC-04) y registra en cada pata el `bash` efectivo, que tiene que ser el mismo (§5.7 B2, analista:D4).

**El candado:** lo toma el runner en su pata (§19.2); el medidor no lo toma en la pata serial (analista:D7). Lo
que cubre la pata serial es la regla operativa de §28: mientras corre el benchmark no se lanza otro trabajo
pesado.

**Sesgo de orden:** la segunda corrida aprovecha la caché de disco (en WU03-a el efecto fue ≤ 2 %, analista).
Se registra el orden; si hay un segundo par, se alterna. **El primer par y el que cierra** (analista:D1): el
primer par N = 2 actualiza `maxSeconds` y `timeoutSeconds` (§10.2, §5.7 B1); si eso cambia el manifest, cambia
la huella y hace falta otro par sobre la huella final, que es el que cierra y cuyas duraciones se registran y
**no realimentan** el manifest (§5.7 B4). Si el primer par no sube ningún `maxSeconds`, el manifest no cambia y
ese mismo par puede ser el que cierra. **El par que cierra puede reutilizar la pata serial del primer par**
(D-T2, §1.3) cuando, entre la huella final del primer par y la del árbol de cierre, el único cambio en la lista
`(ruta, tamaño, sha256)` de §5.1 es `tests/parallel-manifest.json`, con el mismo HEAD y el mismo
`git status --porcelain`. Entonces:

- (1) el medidor lo verifica él mismo, contra la lista, el HEAD y el `status` que registró del primer par; si
  cambió cualquier otra cosa, no reutiliza y sale «no se pudo medir», nunca 0;
- (2) re-verifica en el árbol de cierre las suites cuyo resultado depende del contenido del manifest:
  `75_manifest_paralelo.py` y `63_harness_unico.py` (E-61 lee todo `tests/`; el grep está en §1.3), cada una con
  `.\tests\Invoke-Tests.ps1 -SoloCaso <archivo>`, y exige en cada una el mismo grupo y la misma cuenta (su línea
  de grupo y sus `ok` y `total`) que en la captura serial reutilizada, y la huella del árbol de cierre igual
  antes y después; si algo difiere, no reutiliza y sale «no se pudo medir»;
- (3) al comparador le pasa, para las dos patas, la huella calculada sin esa ruta, y el registro dice
  explícitamente que la pata serial es reutilizada, de qué captura, qué ruta se excluyó y las dos huellas
  completas;
- (4) la equivalencia estricta (§20.4, VD-14) no cambia en nada más. La pata paralela corre entera sobre el
  árbol de cierre, con sus condiciones y sus huellas antes y después; el wall serial que usa `-Umbral` es el de
  la captura reutilizada; no hay alternancia de orden, porque no hay pata serial nueva.

**Mínimo para cerrar 6.1:** un par N = 2 equivalente y sin residuos
atribuibles sobre la huella final. **Para pasar a la fase B** (§28): lo que pide WU12 (≥ 5 pares sobre
≥ 2 huellas, ≥ 2 en rojo inducido, 1 con stderr inyectado, 1 corrida paralela matada).

### 5.5 Qué se mide

Wall de cada corrida; wall de cada suite (líneas de progreso del runner); intervalos de cada suite (para
el pico de concurrencia por carril); total, aprobadas, fallidas, exit; huella antes/después; restos en
`<TempBase>\hpp-*` después de la corrida; procesos `python`/`powershell` vivos atribuibles a la corrida al
terminar; RAM libre mínima durante la corrida (muestreo del medidor). **El muestreo de CPU por proceso no se
exige** (analista:D6): sin él la dispersión de §5.6 no se atribuye (R21), pero agregarlo suma alcance que no
decide nada; si el medidor lo hace, es diagnóstico y no cambia su exit.

### 5.6 Resultados

La evidencia cruda vive **fuera del repo**, en `C:\dev\_respaldos\task6.1\wu03a\` (`condiciones.txt`,
`serial-1.meta.txt`, `serial-2.meta.txt`, `suites.csv`, `wu03a-manifest-timing.csv`, `wu03a-analisis.md`,
`wu03a-analisis-runtime-analyst.md`, `ram.csv`, `restos-tmp.txt`, `huella-*.txt`, `marcas.txt`, `scripts\`); su
resumen, con el de WU03-b, está en `benchmark-2026-10-22.md` (§29, paso 10). Los residuos de las suites
quedaron en `C:\dev\_build\wu03a\tmp`, también fuera del repo. La de WU03-b, en
`C:\dev\_respaldos\task6.1\construccion\wu03b-par1\`, `wu03b-par1b\` y `wu03b-cierre\` (registro del medidor,
comparador y capturas comprimidas).

| Medición | Valor | Rótulo y fuente |
|---|---|---|
| Condiciones | 20-10-2026 09:33:34; RAM total 23,71 GB, libre 7,61; 12 CPUs lógicas; 2 procesos `claude`, 0 `python`, 2 `powershell` (el medidor y su lanzador; uno, pid 28032, con la línea de comando vacía, sin identificar); `bash` por defecto `…\Git\usr\bin\bash.exe` (porque se lanzó desde Git Bash), efectivo `…\Git\bin\bash.exe` (antepuesto con ruta fija, `medir.ps1:15`); git 2.55.0.windows.5; Python 3.12; `TEMP=TMP=TMPDIR=C:\dev\_build\wu03a\tmp`, nuevo y vacío; no elevado; `main`, `d86b285`, 0.34.0, `v0.34.0`, status 0 líneas | MEASURED-BASELINE; `condiciones.txt`; tomadas una vez (VC-25) |
| Huella | `FDEF5380…` antes, tras la corrida 1, tras la corrida 2 y al final: idéntica | MEASURED-BASELINE; `huella-*.txt` |
| Wall serial, corrida 1 | **2963,1 s (49:23)**, 09:33:37 → 10:23:00 | MEASURED-BASELINE; `serial-1.meta.txt` |
| Wall serial, corrida 2 | **3568,1 s (59:28)**, 10:23:01 → 11:22:29 | MEASURED-BASELINE; `serial-2.meta.txt` |
| Dispersión | **20,4 %**; el máximo, 59,5 min, es el que manda (§5.3). La diferencia (+605 s) cae entera después del arranque de t63h en la corrida 2; el bloque PS de la corrida 2 fue 61 s **más rápido**. Descartados: caché de disco, agentes, muestreo, recolección de basura, suspensión (`ram.csv` sin huecos). Lo más consistente, sin atribuir: contención transitoria ajena entre 10:46 y 11:22 | MEASURED-BASELINE el número; la ubicación es inferida por `LastWriteTime` de residuos (analista), no medida |
| Totales | **47.957/47.957** (PS 968/968, Py 46.989/46.989), exit 0, en las dos | MEASURED-BASELINE |
| Duración por suite (97) | Σ **3110,8 s = 51,8 min** (PS 994,8; Py 2116,0); las 97 con exit 0 y `ok == total`; aserciones sumadas 47.957. Cada valor, en §6 | MEASURED-BASELINE; `suites.csv`, `wu03a-manifest-timing.csv` |
| Por clase de §6 | `motor` 947,6 s (15,8 min); `instalador` 967,6 (16,1); `ventana` 266,0 (4,4); `parallel` 929,6 (15,5) | MEASURED-BASELINE |
| Pareto | El 80 % lo explican 20 suites (Σ 2495,5 s = 80,22 %; corte frágil: la 20.ª aporta 0,84 pp): 8 `instalador`, 2 `motor`, 3 `ventana`, 7 `parallel`. Las cinco primeras, el 50,3 %: t73 728,8 s; `03-instalador.ps1` 269,1; 63-hu 223,5; t72 218,8; t64 123,5 | MEASURED-BASELINE; `wu03a-analisis.md`, confirmado por el analista |
| Corrida completa contra suma de solas | −147,7 s (−4,7 %) la 1; +457,3 s (+14,7 %) la 2. Por marcadores, los tramos pesados de la corrida 2 duraron 1,27-1,45× la suite sola (t73 ≈ 975 s) | MEASURED-BASELINE la resta; ESTIMATED los tramos (analista): no alimentan `maxSeconds` (§5.7 B1, R22) |
| Paridad suite sola contra completa | Py **73/73** grupos iguales (contra la corrida 1); PS **35/35** líneas de grupo iguales (`serial-1.log` contra `suites\*.ps1.log`: ningún `.ps1` asierta antes de su `Set-Grupo`); totales iguales. **Observación pre-construcción**: condición necesaria a esta huella; **no es `rojo visto`, ni veredicto, ni prueba de VP-I09** (VC-22). No cubre el multiconjunto de filas (las solas corrieron sin `-Detallado`, `medir.ps1:122, 131`), las fallas (todo verde) ni la corrida 2 por grupos | MEASURED-BASELINE (analista, a mano) |
| Residuos de las suites | **760 entradas por corrida** en el temporal aislado: 2282 = 3 × 760 + 2 (la carpeta de marcas `gcba-harness` y un `me72-hijo-<pid>.py` de más). t72 y t73, 256 por corrida (236 `me72-*`, 20 `ge73-vuelta-*`); el resto de unas 20 suites Python; ninguna de un `.ps1`; ≈ 7 sin atribuir. Son de las suites, no de un runner | MEASURED-BASELINE; recuento del analista, que corrige el agrupado de `wu03a-analisis.md` (VC-21) |
| RAM libre | Mínima **6,70 GB** (11:19:07, corrida 2, tramo final de t73); máxima 9,61; primera 7,58; 314 muestras cada ≈ 30 s, sin huecos | MEASURED-BASELINE; no es el consumo del oráculo (§5.2) |
| Wall paralelo, N = 2 y N = 3 | ESTIMATED con f = 1 y sin sobrecarga: ≈ 25,9 y ≈ 17,3 min (§13.3). **Medido, N = 2:** 2110,4 s (35:10) en el par de cierre, sin `-Detallado`; 2158,2 s (35:58) en el par 1b, con `-Detallado`. **N = 3: no medido** (D-T1) | ESTIMATED / MEASURED-WU03-b; `wu03b-cierre\registro.txt`, `wu03b-par1b\registro.txt` |
| f (desaceleración bajo carga paralela) | **≈ 1,23**: Σ de las duraciones de las 97 suites de la baseline en la pata paralela del par de cierre, 3834,9 s, contra su Σ sola en WU03-a, 3110,8 s. Por clase: `motor` 1,08; `instalador` 1,29; `ventana` 1,15 (sin `75_runner`); `parallel` 1,35 (sin `75_manifest`). Incluye la sobrecarga por suite. Con N = 2, la pata paralela ocupó los dos lugares el 99,5 % del wall (Σ 4200,5 s de 99 suites sobre 2 × 2110,4) | MEASURED-WU03-b el cociente de dos sumas medidas; no es una medición por suite de f |
| Sobrecarga por suite (`-SoloCaso`) | **≈ 1 s por suite trivial**: en el par de cierre, `04_secretos.py` 0,1 → 1,2 s; `16_refutador_contrato.py` 0,1 → 1,1; `06_reglas.py` 0,2 → 1,1; `08-bitacora.ps1` 0,8 → 1,0 (sola en WU03-a → worker con `-SoloCaso` en la paralela). Unos 99 s de trabajo en las 99, ≈ 0,8 min de wall con N = 2, ESTIMATED. El arranque en frío de `powershell.exe -NoProfile -NonInteractive` medido en la construcción fue 2,65–3,25 s (D-T4): con la máquina caliente, en la corrida real, pesa menos | MEASURED-WU03-b contra MEASURED-BASELINE (métodos distintos: `correr.py -k` o la copia del preludio contra el worker); el total, ESTIMATED |
| Equivalencia de los pares | **Par de cierre: `EQUIVALENTE`** (35 grupos PS, 75 grupos Py, 48841/48841, exit 0), sin `-Detallado` (D-T5). Par 1b: `NO_EQUIVALENTE` solo por el punto 5 de §20.4 (≈ 129 nombres de fila con datos volátiles; D-T5). Par 1: `NO_EQUIVALENTE` por dos defectos ajenos al runner (§4 «Combinación», VX-21; guarda de `MAX_PATH`, §5.2, VX-26) | MEASURED-WU03-b; `comparador.txt` de cada par |
| Residuos atribuibles a la corrida paralela | **0 en el par de cierre** (ninguna raíz `hpp-*`, `s<nnn>` ni `hpp-<id>.lock`; ninguna línea que empiece con `AVISO LIMPIEZA_INCOMPLETA`); 0 procesos `python`/`powershell` nuevos y vivos al terminar la pata | MEASURED-WU03-b; `wu03b-cierre\registro.txt` |
| Relación paralelo / serial, N = 2 | **0,7089** en el par de cierre (2110,4 / 2976,9): la que vale para el umbral (D-T7). 0,658 en el par 1b, sesgada por `-Detallado`; 0,596 en el par 1, que no vale (par rojo) | MEASURED-WU03-b |
| Wall serial del árbol construido | 2976,9 s (49:36) sin `-Detallado` (cierre); 3280,1 s (54:40) con `-Detallado` (par 1b, la suite completa oficial de D-T3) | MEASURED-WU03-b |
| Piso de RAM | **No se fija en 6.1**; mínimos de RAM libre por pata en §5.2; la de la pata paralela del cierre (3,20 GB) no es atribuible al runner (VX-28) | MEASURED-WU03-b los mínimos; la decisión, pasada post-WU03-b |

### 5.7 Reglas del protocolo

Salen de VP-B1..B6 del runtime-analyst. Son texto del protocolo: las cumple el medidor o quien mide, las
registra `benchmark-<fecha>.md`, y un par que no las cumple no se acepta. No son invariantes `VP-I` ni tienen
escenario propio.

- **B1.** Una duración alimenta `maxSeconds` solo si sale de un `Stopwatch` **por suite** (la suite sola, o la
  línea de progreso del runner, §16.6) en una corrida con exit 0, `ok == total`, la misma huella antes y
  después y las condiciones de §5.2 tomadas antes de esa corrida. Nada inferido la alimenta: ni las
  MEASURED-previa de §2.3, ni los tramos estimados por marcadores de §5.6 (analista:D8, VC-23).
- **B2.** Las dos patas de un par corren con el mismo `bash` efectivo, registrado en cada una, y con
  `TEMP=TMP=TMPDIR` nuevos y vacíos por pata, del mismo formato (§5.4).
- **B3.** La paridad suite sola contra completa se registra antes de construir como condición necesaria, nunca
  como veredicto ni como `rojo visto` (§5.6, VC-22).
- **B4.** El manifest no cambia después del par que cierra; las duraciones de ese par se registran en
  `benchmark-<fecha>.md` y no realimentan `maxSeconds` (§5.4, VC-29). **Nota (D-T2, §1.3):** el par que cierra
  puede reutilizar la pata serial del primer par N = 2 solo con las condiciones (1)-(4) de §5.4; B1, B2 y B3
  rigen igual, y B2 se cumple contra el `bash` efectivo registrado en la captura reutilizada.
- **B5.** El muestreador de RAM del medidor no sobrevive al medidor: vive en su proceso, o se corta en su
  `finally` (analista:CW1, CW3; R28).
- **B6.** En `-SoloCaso`, el grupo de la fila «el archivo de casos se pudo cargar» sale del objeto de la
  enumeración, nunca de una variable que un caso dot-sourced pueda pisar (§21, VX-19).

---

## 6. Test inventory

97 suites sobre `d86b285`: **24 `.ps1` + 73 `.py`** (Glob de `tests/casos/` leído; más `.gitkeep`; confirmado
por el discoverer y por las 97 suites solas de WU03-a). El brief decía 100 y WU04 «75 `.py`»: VC-12. 6.1 suma
dos: `75_manifest_paralelo.py` y `75_runner_paralelo.py`. Esta tabla **es el manifest inicial, con sus
tiempos**; el orden es el canónico (PS por `Sort-Object Name`, después Py por `sorted`).

- **`maxSeconds`** = los segundos de la suite sola en WU03-a (`suites.csv`, `Stopwatch` redondeado a 0,1 s con
  `[math]::Round`, al par), MEASURED-BASELINE, **una medición**. Ninguna de las 97 queda en `null`: las 97
  dieron exit 0 y `ok == total` sobre la misma huella (`null` es solo para una suite sin medición válida). El
  máximo real puede quedar hasta 0,05 s arriba del valor escrito por el redondeo; no cambia ningún timeout.
- **`timeoutSeconds`** = `max(ceil(3 × maxSeconds), 1200)` (VD-11). Solo t73 pasa el piso: 3 × 728,8 =
  2186,4 → **2187**. La siguiente es `03-instalador.ps1`, con 269,1 → 808 → 1200.
- Las filas 98-99 (`75_*`) **no existen todavía** y no cuentan como existentes: `null` / `null` hasta que una
  medición válida las llene (§5.7 B1).

Claves de evidencia:

- **P** — sin cota superior de tiempo ni carrera entre procesos demostrada (WU02, inventario; WU04, tabla);
  el choque por temporal compartido lo resuelve VD-05.
- **P·árbol** — además lee qué archivos hay en el árbol. Seguro porque ninguna suite escribe archivos no
  ignorados en el árbol (grep léxico de escrituras sobre `RAIZ` y `$script:Raiz` en `tests/casos`: 0;
  WU02 «Repo: 0», D por grep; las cuatro huellas de WU03-a iguales) y VP-I08 lo vigila en cada corrida.
- **P·git** — corre git sobre el árbol o contra una base fija (un tag o un commit que tiene que estar en el
  clon, §5.2).
- **I** — corre `install.ps1` (WU02: «Corren el instalador: 21»). Carril `instalador`: dos instaladores
  nunca a la vez, como en el oráculo, donde corren en un solo proceso. Fallan al azar bajo carga
  (FH:1002-1017) y FH pide medirlos bajo carga antes de sacarlos del grupo serial (FH:2281-2283): esa
  medición es WU03-b, antes de adoptar (§10.5). `install.ps1` recorre árboles con `Get-ChildItem -Recurse`
  bajo `Stop` (`install.ps1:333-336`).
- **M** — carril `motor`: t72 y t73 tienen ventanas de pocos segundos y carreras de procesos reales, y t73
  carga t72: ME-E05, un Ctrl-C simulado a los 4 s (`72:875-900`); ME-E31, límite de 3 s y `< 40 s`
  (`72:910-923`); ME-E18, dos procesos con encuentro y veinte carreras de a diez procesos (`72:550-593`);
  GD-27, dos motores que tienen que solaparse dentro de ~3 s (`73:2167-2183`); FH:2276-2278.
- **V** — carril `ventana`: cota superior de tiempo estrecha o falla observada bajo carga.

| # | Suite | Motor | Clase | `maxSeconds` | `timeoutSeconds` | Evidencia |
|---|---|---|---|---|---|---|
| 1 | `00-encoding-fuentes.ps1` | ps | parallel | 1.0 | 1200 | P·árbol: recorre el repo (WU02, no releído) |
| 2 | `03-instalador.ps1` | ps | lane `instalador` | 269.1 | 1200 | I; fábricas aisladas (`isolated-factory.ps1:68-85`); la segunda más larga |
| 3 | `08-bitacora.ps1` | ps | parallel | 0.8 | 1200 | P·árbol: lee CHANGELOG y `docs/versiones` (WU02) |
| 4 | `11-codebase-instalador.ps1` | ps | lane `instalador` | 14.0 | 1200 | I |
| 5 | `14-contexto-instalador.ps1` | ps | lane `instalador` | 26.1 | 1200 | I; nombrada en la falla del 22-09 (FH:1011) |
| 6 | `17-env-instalador.ps1` | ps | lane `instalador` | 23.9 | 1200 | I |
| 7 | `18-integraciones-instalador.ps1` | ps | lane `instalador` | 24.0 | 1200 | I; compila el bin del repo para E-33 (`18-integraciones-instalador.ps1:35-48`) |
| 8 | `19-contexto-tarea-instalador.ps1` | ps | lane `instalador` | 24.9 | 1200 | I |
| 9 | `20-orquestacion-instalador.ps1` | ps | lane `instalador` | 25.5 | 1200 | I |
| 10 | `30-contabilidad-instalador.ps1` | ps | lane `instalador` | 24.5 | 1200 | I |
| 11 | `54-context-bar-instalador.ps1` | ps | lane `instalador` | 39.1 | 1200 | I; `WaitForExit(60000)` (`54-context-bar-instalador.ps1:49`); Git Bash (WU02) |
| 12 | `57-aceptar-fuentes-instalador.ps1` | ps | lane `instalador` | 29.7 | 1200 | I |
| 13 | `60-entorno-instalador.ps1` | ps | lane `instalador` | 18.3 | 1200 | I |
| 14 | `61-auto-refresco-instalador.ps1` | ps | lane `instalador` | 18.1 | 1200 | I |
| 15 | `62-context-bar-consumo-instalador.ps1` | ps | lane `instalador` | 58.5 | 1200 | I; `WaitForExit(60000)` (`62-context-bar-consumo-instalador.ps1:54`); Git Bash (WU02) |
| 16 | `63-harness-unico-instalador.ps1` | ps | lane `instalador` | 223.5 | 1200 | I; `WaitForExit(300000)` (`63-harness-unico-instalador.ps1:70`); 223,5 s MEASURED-BASELINE (≈ 5,4 min MEASURED-previa) |
| 17 | `64-modelo-de-dominio-instalador.ps1` | ps | lane `instalador` | 52.7 | 1200 | I; `WaitForExit(300000)` (`64-modelo-de-dominio-instalador.ps1:51`) |
| 18 | `65-contrato-de-ejecucion-instalador.ps1` | ps | lane `instalador` | 11.6 | 1200 | I; `65-contrato-de-ejecucion-instalador.ps1:38`; pisa `$nombre` en `:97` (VX-19) |
| 19 | `66-integrity-instalador.ps1` | ps | lane `instalador` | 10.6 | 1200 | I; `-Doctor` (WU02); pisa `$nombre` en `:18, 46` (VX-19) |
| 20 | `68-isolated-factory.ps1` | ps | parallel | 25.4 | 1200 | P·árbol: compara `git status --untracked-files=all` (`68-isolated-factory.ps1:15-21, 53`); enumera `harness-fabrica-*` del temporal (`:23-33`), que con VD-05 es el de la suite; QG1 E-05b exige no elevado (`:170-181`) |
| 21 | `69-instalador-sin-consola.ps1` | ps | lane `instalador` | 30.3 | 1200 | I; consola oculta real, 180 s (WU02, no releído) |
| 22 | `72-motor-de-ejecucion-instalador.ps1` | ps | lane `instalador` | 13.3 | 1200 | I; `WaitForExit(300000)` (`72-motor-de-ejecucion-instalador.ps1:41`) |
| 23 | `73-ejecucion-de-grafo-instalador.ps1` | ps | lane `instalador` | 17.5 | 1200 | I; `WaitForExit(300000)` (`73-ejecucion-de-grafo-instalador.ps1:42`) |
| 24 | `74-knowledge-api-instalador.ps1` | ps | lane `instalador` | 12.4 | 1200 | I: corre el `install.ps1` real (`:97-98`); su carpeta por `GetTempPath()` (`:21`), sin mutar `TEMP`; quita `PYTHONPATH` y `CLAUDE_PROJECT_DIR` del hijo (`:37-40`); lanza `python -I -B` por nombre (`:54`); `WaitForExit(300000)` (`:46`); `Set-Grupo` (`:17`); sin junctions, git ni bash (leído; discoverer) |
| 25 | `01_hook_lib.py` | py | parallel | 1.9 | 1200 | P; marcas con `session_id` fijo, en su propio temporal (VC-11) |
| 26 | `02_hook_contrato.py` | py | parallel | 0.5 | 1200 | P |
| 27 | `04_secretos.py` | py | parallel | 0.1 | 1200 | P |
| 28 | `05_memoria.py` | py | parallel | 5.0 | 1200 | P; git en temporal |
| 29 | `06_reglas.py` | py | parallel | 0.2 | 1200 | P |
| 30 | `07_checks.py` | py | parallel | 0.2 | 1200 | P |
| 31 | `08_checks_borde.py` | py | parallel | 0.2 | 1200 | P |
| 32 | `09_zonas.py` | py | parallel | 0.2 | 1200 | P |
| 33 | `10_codebase.py` | py | parallel | 11.1 | 1200 | P; `git check-ignore` con cwd = raíz (WU02) |
| 34 | `12_mapa_nodos.py` | py | parallel | 0.4 | 1200 | P |
| 35 | `13_contexto.py` | py | parallel | 33.0 | 1200 | P |
| 36 | `15_contexto_paso4.py` | py | parallel | 21.5 | 1200 | P |
| 37 | `16_refutador_contrato.py` | py | parallel | 0.1 | 1200 | P |
| 38 | `18_integraciones.py` | py | parallel | 1.3 | 1200 | P; `HTTPServer` en `127.0.0.1`, puerto 0 (WU02) |
| 39 | `19_contexto.py` | py | parallel | 1.0 | 1200 | P; E-29 depende del reloj (defecto, FH:1028-1033): la carga lo hace más probable, el carril no lo arregla (VX-10) |
| 40 | `20_orquestacion.py` | py | parallel | 10.5 | 1200 | P |
| 41 | `21_tools.py` | py | parallel | 0.3 | 1200 | P |
| 42 | `22_registro_agentes.py` | py | parallel | 2.0 | 1200 | P |
| 43 | `23_matriz_normativa.py` | py | parallel | 1.4 | 1200 | P |
| 44 | `24_g1_tecnologias.py` | py | parallel | 0.8 | 1200 | P |
| 45 | `25_g2_buenas_practicas.py` | py | parallel | 0.7 | 1200 | P |
| 46 | `26_d1_autenticacion_ciudadana.py` | py | parallel | 1.4 | 1200 | P |
| 47 | `27_d2_delegacion_credenciales.py` | py | parallel | 1.3 | 1200 | P |
| 48 | `28_d3_diseno_orientado_a_objetos.py` | py | parallel | 1.1 | 1200 | P |
| 49 | `29_d4_comportamiento_responsive.py` | py | parallel | 0.9 | 1200 | P |
| 50 | `30_b4_contabilidad.py` | py | parallel | 1.5 | 1200 | P·árbol: una aserción por `*.json` de `comun/` y `harnesses/` (WU02); deriva del 22-09 (VC-05) |
| 51 | `31_d6_visualizacion_georreferenciada.py` | py | parallel | 2.0 | 1200 | P |
| 52 | `32_d5_normalizacion_catastral.py` | py | parallel | 1.5 | 1200 | P |
| 53 | `33_bases_de_datos.py` | py | parallel | 1.8 | 1200 | P·árbol: cinco aserciones por `*.md` de agents/skills (WU02); deriva del 22-09 (VC-05) |
| 54 | `34_d7_almacenamiento_de_archivos.py` | py | parallel | 2.1 | 1200 | P |
| 55 | `35_d8_proteccion_con_token.py` | py | parallel | 1.3 | 1200 | P |
| 56 | `36_p1_frameworks_homologados.py` | py | parallel | 0.8 | 1200 | P |
| 57 | `37_es0902_seguridad.py` | py | parallel | 1.2 | 1200 | P |
| 58 | `38_integridad_de_repositorio.py` | py | parallel | 1.3 | 1200 | P; mira `sys.modules` (WU02): un proceso propio no lo cambia |
| 59 | `39_es0902_o1_normativa_gcba.py` | py | parallel | 1.0 | 1200 | P |
| 60 | `40_es0902_o2_autoridad_de_control.py` | py | parallel | 0.5 | 1200 | P |
| 61 | `41_es0902_c1_openid_connect.py` | py | parallel | 0.6 | 1200 | P |
| 62 | `42_es0902_c2_aprobacion_en_qa.py` | py | parallel | 1.0 | 1200 | P |
| 63 | `43_es0902_c3_herramientas_versionadas.py` | py | parallel | 2.4 | 1200 | P |
| 64 | `44_es0902_vu1_proteccion_de_autenticacion.py` | py | parallel | 1.2 | 1200 | P |
| 65 | `45_conocimiento_fuentes.py` | py | parallel | 3.4 | 1200 | P |
| 66 | `46_es0902_vu2_datos_sensibles_en_transito.py` | py | parallel | 0.9 | 1200 | P |
| 67 | `47_es0902_vu3_cierre_de_sesion.py` | py | parallel | 1.6 | 1200 | P |
| 68 | `48_reporte_de_seguridad.py` | py | parallel | 4.8 | 1200 | P |
| 69 | `49_es0902_vu4_vencimiento_por_inactividad.py` | py | parallel | 5.4 | 1200 | P |
| 70 | `50_es0902_vu5_validacion_espejada.py` | py | parallel | 5.1 | 1200 | P |
| 71 | `51_bienvenida.py` | py | parallel | 20.3 | 1200 | P·árbol: suma una aserción si existe `RAIZ/.claude/harness.fuentes.json` (`51:865-867`) |
| 72 | `52_es0902_vu6_mensajes_de_error.py` | py | parallel | 3.8 | 1200 | P |
| 73 | `53_context_bar.py` | py | parallel | 21.2 | 1200 | P; `sleep(1.1)` es cota inferior, no superior (WU02) |
| 74 | `54_es0902_vu7_software_de_base.py` | py | parallel | 4.0 | 1200 | P |
| 75 | `55_refutacion_atomica.py` | py | lane `ventana` | 68.5 | 1200 | V: E-58 falló una vez bajo carga ajena (FH:1042); la causa es el `remotos` de 10 s no estricto (VC-06) |
| 76 | `56_es0902_vu8_perfiles_y_roles.py` | py | parallel | 9.9 | 1200 | P; carga 55 como módulo (WU02) |
| 77 | `57_aceptar_fuentes.py` | py | parallel | 19.2 | 1200 | P·git: `git archive` de un SHA fijo (WU01) |
| 78 | `58_es0902_vu9_control_de_uso_publico.py` | py | parallel | 15.9 | 1200 | P; carga 55 |
| 79 | `59_es0902_vu10_guia_owasp.py` | py | parallel | 7.8 | 1200 | P; carga 55 |
| 80 | `60_entorno_primero.py` | py | parallel | 2.6 | 1200 | P |
| 81 | `61_conocimiento_auto_refresco.py` | py | parallel | 8.6 | 1200 | P; ocho hilos propios (WU02) |
| 82 | `61_flujo_precondiciones.py` | py | parallel | 24.0 | 1200 | P; carga 55 |
| 83 | `62_context_bar_consumo.py` | py | parallel | 11.2 | 1200 | P; `os.environ.clear()` con restauración, en su proceso (WU02) |
| 84 | `62_estado_del_flujo.py` | py | parallel | 58.5 | 1200 | P; carga 55 |
| 85 | `63_compuerta_del_flujo.py` | py | lane `ventana` | 102.0 | 1200 | V: `demora < limite + 1.5` y `< limite + 3` (`63_compuerta_del_flujo.py:1732-1733, 1779-1780`, discoverer); límite de 1,5 s de la compuerta (`flow_gate.py:38-42`); E-38 necesita Git Bash primero (§5.2, VX-09) |
| 86 | `63_harness_unico.py` | py | parallel | 23.2 | 1200 | P·árbol: `git ls-files --others` del repo (WU02); E-61 recorre `tests/` (`63_harness_unico.py:678-697`); P·git: base `ea2dff7` (discoverer) |
| 87 | `64_interaccion_humana.py` | py | parallel | 116.4 | 1200 | P; cuatro procesos propios a la vez, espera 120 s (`64_interaccion_humana.py:904`) |
| 88 | `64_modelo_de_dominio.py` | py | parallel | 123.5 | 1200 | P·árbol; subproceso con `timeout=600` (`64_modelo_de_dominio.py:235`); P·git: base `4c6f0f3` (discoverer); 123,5 s MEASURED-BASELINE (≈ 3,3 min MEASURED-previa) |
| 89 | `65_contrato_de_ejecucion.py` | py | parallel | 71.4 | 1200 | P; P·git: bases `f9393cf` y `fdca5ce` (discoverer); 71,4 s MEASURED-BASELINE (≈ 1,8 min MEASURED-previa) |
| 90 | `65_fail_closed.py` | py | parallel | 23.3 | 1200 | P |
| 91 | `66_integrity_cleanup.py` | py | parallel | 118.2 | 1200 | P; lee el texto del oráculo (`66_integrity_cleanup.py:471-476`) |
| 92 | `67_integracion_frescura.py` | py | parallel | 31.9 | 1200 | P |
| 93 | `70_r11_glob_de_autoridad.py` | py | lane `ventana` | 95.5 | 1200 | V: `perf_counter < 1,0 s` (`70:465-469`, discoverer) |
| 94 | `71_plan_2_1.py` | py | parallel | 24.7 | 1200 | P·árbol: `glob` de `casos/*.ps1` (`71_plan_2_1.py:501`) |
| 95 | `72_motor_de_ejecucion.py` | py | lane `motor` | 218.8 | 1200 | M; `_matar` sin árbol (`72:299-305`) y `_terminar` por pid (`72:355-357`); P·git: base `fdca5ce` (discoverer); una falla única de E34 en el cierre de 0.34.0 (`docs/versiones/0.34.0.md:149-158`, VC-30); 218,8 s MEASURED-BASELINE (≈ 6 min MEASURED-previa) |
| 96 | `73_ejecucion_de_grafo.py` | py | lane `motor` | 728.8 | 2187 | M; carga t72; **la más larga**: 728,8 s MEASURED-BASELINE (≈ 20 min MEASURED-previa), pero con N = 2 no es el camino crítico (§13.3) |
| 97 | `74_knowledge_api.py` | py | parallel | 24.3 | 1200 | P·git: depende de git y del tag `v0.33.0` (`BASE`, `74:3643`; KA-E47 compara `19_contexto.py` contra la base, `74:3735`; KA-E53 `cat-file`, `ls-tree`, `diff` y `ls-files --others` restringido a las protegidas, `74:4146-4157`, discoverer); **carga como módulo** `tests/correr.py` (`74:3737, 4319`), `19_contexto.py` (`74:3738`) y `64_modelo_de_dominio.py` (`74:4219`); junctions con `mklink /J` (`_enlace`, `74:222-233`); su carpeta con `mkdtemp` y `atexit` (`74:94-95`); muta `TEMP`, `TMP`, `TMPDIR` y `tempfile.tempdir` y los repone (KA-E42, `74:3357-3381`); KA-E56 busca «GraphRun» en `adr` (`74:4402-4446`); sin bash, hilos, `sleep` ni medición de tiempo (leído; discoverer). Ninguna escritura en `RAIZ` (guardián): proceso y temporal propios no lo cambian |
| 98 | `75_manifest_paralelo.py` (no existe todavía) | py | parallel | null | null | Unidad pura, sin procesos: VP-E24 parte A (VD-15, VC-34); la parte B, con procesos, va en la fila 99 |
| 99 | `75_runner_paralelo.py` (no existe todavía) | py | lane `ventana` | null | null | Lanza runners anidados y procesos reales (VD-15) |

**Conteo:** `parallel` 71 + 1 nueva; `instalador` 21; `motor` 2; `ventana` 3 + 1 nueva; `serial` 0.
**Tiempo por clase** (MEASURED-BASELINE, §5.6): `motor` 947,6 s; `instalador` 967,6; `ventana` 266,0;
`parallel` 929,6; total 3110,8. `serial` queda vacía a propósito: es la clase de toda suite sin entrada y el
destino de una suite que en WU03-b dé rojo en paralelo y verde en serial sobre la misma huella (§10.5). Ninguna
de las 97 tiene hoy un choque demostrado que el aislamiento no resuelva (§7).

---

## 7. Interference model

Los 27 mecanismos de WU04, con su destino. «Leído» = lo releyó el arquitecto.

| WU04 | Mecanismo | Estado | Lo resuelve |
|---|---|---|---|
| 1 | Barrido de `harness-fabrica-*` en el temporal raíz (03, 68) | Demostrado (WU04); `isolated-factory.ps1:44-65` leído | VD-05: temporal por suite |
| 2 | `Clear-MarcasHarness` sobre un temporal compartido; E-08 de 01 | Demostrado (WU04); `Invoke-Tests.ps1:128-142` leído | VD-05 |
| 3 | .NET lee `TMP`, Python `TMPDIR`, el oráculo `$env:TEMP` | Demostrado (WU04); la nota 0.34.0 lo repite (`docs/versiones/0.34.0.md:163-164`) | VD-05: las tres iguales |
| 4 | `me72-hijo-<pid>.py` fijo en el temporal, no se borra | Leído (`72:263-267`); con un temporal compartido y un pid reusado puede ejecutar un guion viejo (analista:RC1) | VD-05: temporal descartable |
| 5 | Guiones y ecos en `Path(proy).parent` | Leído (`72:133-138`) | VD-05 |
| 6 | `_terminar` mata por pid un Host que pudo morir | Leído (`72:355-357`) | Carril `motor` lo acota; riesgo residual (§24, VX-11) |
| 7 | Ctrl-C simulado a los 4 s (ME-E05) | Leído (`72:875-900`) | Carril `motor` + N = 2 |
| 8 | `limiteSegundos: 3` y `< 40 s` (ME-E31) | Leído (`72:910-923`) | Carril `motor` + N = 2 |
| 9 | GD-27, solape de ~3 s | Leído (`73:2167-2183`) | Carril `motor` + N = 2 |
| 10 | `git remote -v` con 1,5 s en la compuerta de hooks | Leído (`flow_gate.py:38-42`) | N = 2 (margen 6× sobre el máximo medido en reposo, según el comentario); t63c al carril `ventana` |
| 11 | `context_hash` con reloj (19 E-29) | Demostrado como defecto (WU04) | Ninguno: VX-10 |
| 12 | `git status` de todo el árbol en 68 | Leído (`68-isolated-factory.ps1:15-21`) | VP-I08 + ningún escritor de no ignorados |
| 13 | E-58: `remotos` de 10 s no estricto | Leído (`repositorio.py:168-198, 253`) | Carril `ventana` para 55 (VC-06) |
| 14 | `__pycache__` del repo | Leído (`.gitignore:42-43`, `18-integraciones-instalador.ps1:35-48`) | Ignorado por la huella; no se cambia el entorno (VC-08) |
| 15 | `install.ps1` recorre con `-Recurse` bajo `Stop` | Leído (`install.ps1:333-336`) | Carril `instalador`; ninguna suite borra `__pycache__` del repo (WU04, no releído entero) |
| 16 | Límites internos del instalador (30 s, 5 s, 120 s) | WU04, no releído | Carril `instalador` + N = 2 |
| 17 | Esperas amplias (60, 120, 300, 600 s) | Leído en parte (§4) | Ninguno necesario; alimentan el piso del timeout (VD-11) |
| 18 | `perf_counter < 1,0 s` (70) | `70:465-469` (discoverer) | Carril `ventana` |
| 19 | Conteo que depende de `PATH`, env o del repo (51, t63c, 63-hu, 74) | `51:865-867` leído | VD-05: entorno heredado sin cambios |
| 20 | cwd y `CLAUDE_PROJECT_DIR` | WU04, no releído; 74-inst lo quita de su hijo (`74-knowledge-api-instalador.ps1:40`) | cwd = raíz, entorno heredado |
| 21 | Temporal 8.3 y `MAX_PATH` | WU04; la PoC y WU03-a usaron rutas cortas | Raíz corta, formato del `TEMP` heredado (§12) |
| 22-26 | Payloads con cwd fijo, kill por nombre, puertos, ubicaciones globales, `index.lock` | Sin evidencia de choque (WU04) | — |
| 27 | Deriva de conteos de 30 y 33 | Sin evidencia de la fuente (WU04); en WU03-a, los conteos de las dos corridas y de las solas coinciden | VD-14 la hace visible, no la tolera (VC-05) |

Lo que un proceso por suite **cambia** respecto del serial, y no se neutraliza sino que se detecta por la
paridad suite por suite (§22): `HOST_FALSO_GUION` que t72 deja puesto en el proceso compartido
(`72:137`, leído) y heredan las suites siguientes; el grupo actual de PowerShell que pasa de un `.ps1` al
siguiente si el segundo no llama a `Set-Grupo` antes de su primera aserción (`Invoke-Tests.ps1:30, 42`);
variables sin `$script:` y funciones homónimas entre `.ps1` (VC-13); `sys.path`, `sys.modules` y
`os.environ` acumulados en `correr.py`. Una suite que pasa en un modo y no en el otro por eso es un defecto
de esa suite y se reporta (VX), nunca se absorbe.

**Lo que ya mostró WU03-a, como observación pre-construcción** (§5.6, VC-22): a la huella `FDEF5380…`, las 97
suites solas dieron los mismos conteos por grupo que la corrida completa (Py 73/73, PS 35/35 líneas de grupo):
ninguno de los efectos de arriba cambió un conteo en verde. No prueba nada sobre fallas ni sobre el paralelo.
De paso apareció un defecto latente **del oráculo**, solo en el camino de falla: `03-instalador.ps1:846` reusa
`$caso` como variable de un `foreach` dentro del `try` de nivel superior de `:767`, en el scope del oráculo; si
03 tirara después, el `catch` de `Invoke-Tests.ps1:178-180` leería `$caso.BaseName` de ese otro objeto y no del
archivo. 65-inst y 66-inst pisan `$nombre` (`65-contrato-de-ejecucion-instalador.ps1:97`,
`66-integrity-instalador.ps1:18, 46`), que no lee el oráculo pero sí una copia del preludio que lo use. Va a FH
(VX-19) y es una regla para M2 (§21, §5.7 B6).

---

## 8. Boundary

### 8.1 Qué entra

| Pieza | Qué es |
|---|---|
| `tests/Invoke-Tests-Parallel.ps1` | El runner: candado, barrido, huella, scheduler, pool, workers, agregación, reporte |
| `tests/parallel-manifest.json` | La clase de cada suite, con su evidencia y sus tiempos |
| `tests/Compare-TestRuns.ps1` | Compara una salida del oráculo con una del runner sobre la misma huella |
| `tests/Measure-TestRuns.ps1` | El protocolo de §5.4: condiciones, huellas, las dos corridas, el comparador, el registro |
| `tests/Invoke-Tests.ps1` | Solo `-SoloCaso` (VD-04) |
| `tests/casos/75_manifest_paralelo.py`, `75_runner_paralelo.py` | Los tests de 6.1 (VD-15) |
| `docs/adr/0018-dos-corredores-un-oraculo.md` | VD-01 |
| `.claude/agents/harness-backend-engineer.md:62-73` | La enmienda M1 (VD-01) |
| `docs/cambios/verification-pipeline-performance/` | Esta spec, `benchmark-<fecha>.md`, después `verificacion.md` |

### 8.2 Qué queda afuera, y por qué

- **Cambiar tests productivos para volverlos parallel-safe.** Una suite que no lo es va a una clase más
  estricta; tocarla para que pase cambia lo que prueba (brief; `harness-backend-engineer.md:109-111`).
- **Rearquitecturar Tasks 2 a 6.** Son contrato estable; su código no se toca.
- **Promover el runner a oráculo o compuerta.** Fase D, con ADR propio y aprobación de una persona (§28).
- **Candado en el oráculo y en los lotes de mutaciones.** El oráculo queda intacto salvo `-SoloCaso`; un
  candado le agrega un exit nuevo (WU10:C4). VX-07.
- **Job Object.** El precedente lo difiere «cuando un caso real lo pida» (ME:1697) y los huérfanos existen
  igual en serial (VC-07). VX-08.
- **JSON en `correr.py` (M3).** El texto alcanza (VD-09); un segundo canal es más código que probar.
- **Hilos o runspaces.** Comparten proceso: t68 E-06 identifica sus copias por el proceso dueño
  (`68-isolated-factory.ps1:23-33`), y `sys.modules`/`os.environ` se mezclarían.
- **Exclusiones de Defender.** Requiere política o admin. VX-01.
- **CI/CD, GitHub Actions, Docker, containers, ejecución remota o sharding.** Otro problema, otra máquina.
  VX-02, VX-03.
- **Eliminar suites lentas, reducir cobertura, mockear integraciones, cambiar la semántica de un test.**
  Contradice «mismas aserciones».
- **Optimizar t73 o t72.** Es trabajo sobre suites, no sobre el runner. VX-05.
- **Limpiar los residuos que las suites dejan en su temporal** (760 por corrida, §5.6). Son de las suites
  (FH:2119-2133, VX-20); en el runner caen en el temporal de la suite y se borran con él (§16.5).
- **La regex cuadrática de secretos** (FH:2285). VX-06.
- **Arreglar la deriva de 30/33 y el reloj de 19 E-29.** Son de sus suites (FH:1023-1039). VX-10.
- **Arreglar el `$caso` pisado por `03-instalador.ps1:846` en el camino por defecto del oráculo.** VD-04 deja
  la salida por defecto idéntica; va a FH (VX-19).
- **Elegir suites por archivos tocados y reusar resultados por huella** (FH:2280). VX-15.
- **Corregir los textos que dicen que `install.ps1` corre la suite.** No es de esta Task. VX-12.
- **POSIX, PowerShell 7.** La fábrica corre en Windows PowerShell 5.1 (`harness-backend-engineer.md:29-31`).

### 8.3 File scope

| Tipo | Archivos |
|---|---|
| Nuevos | `tests/Invoke-Tests-Parallel.ps1`, `tests/parallel-manifest.json`, `tests/Compare-TestRuns.ps1`, `tests/Measure-TestRuns.ps1`, `tests/casos/75_manifest_paralelo.py`, `tests/casos/75_runner_paralelo.py`, `docs/adr/0018-dos-corredores-un-oraculo.md` (0018 es el siguiente libre; 0007 es un hueco deliberado y no se usa: VC-32), `docs/cambios/verification-pipeline-performance/{spec,benchmark-<fecha>}.md` |
| Modificados | `tests/Invoke-Tests.ps1` (solo `-SoloCaso`); `.claude/agents/harness-backend-engineer.md` (solo §«The suite: one command, two engines», :62-73); FH e I (los VX, con `note-a-pending`; el ítem de FH:2260-2283 sale al cerrar); al cerrar, lo que pide `close-a-version` |
| Protegidos | `tests/correr.py` (lo cargan como módulo t65, t72 y t74: `74:3737, 4319`); `tests/isolated-factory.ps1`; las 97 suites existentes; `tests/fixtures/**`, `tests/payloads/**`; `install.ps1`; `manifest.json`; `comun/**`; `harnesses/**`; `CLAUDE.md`; `harness-spec-refuter.md`; `harness-staff-engineer.md`; `close-a-version/SKILL.md`; los ADR 0001-0017 (0013-0016 los fijan t72 y t74); las specs de Tasks anteriores (incluida la cita corrida de GE:771, VC-18); `.gitignore`; las rutas de ME-E49 (`72:2297-2302`, base `fdca5ce`) y KA-E53 (`74:4120-4128`, base `v0.33.0`) |

**Restricciones que la suite ya impone a lo nuevo** (guardián, PI-1..PI-6; las citas, leídas sobre `d86b285`):

- M2 conserva en `Invoke-Tests.ps1` los textos `correr.py` (`72:2335`) y `sys.executable`
  (`66_integrity_cleanup.py:474`) y no reintroduce la línea `Get-Command` que prohíbe
  `66_integrity_cleanup.py:475-476`;
- ningún archivo nuevo bajo `tests/` contiene el parámetro viejo de la composición (`PARAMETRO_VIEJO`,
  `63_harness_unico.py:35`) ni las formas de `FORMAS_ANALISIS` (`63_harness_unico.py:297-299`): E-61 recorre
  `tests/`, también lo no versionado no ignorado (`63_harness_unico.py:678-697`);
- M1 no nombra `comun/manifest.json` ni `harnesses/<x>/manifest.json` y no tiene un comando con el parámetro
  viejo (E-57, `63_harness_unico.py:621-635`); `tests/parallel-manifest.json` no cae en esa regex;
- ningún `casos/*.ps1` salvo el 63 nombra el parámetro viejo (`71_plan_2_1.py:496-503`);
- el runner y sus tests no dejan archivos no ignorados en el árbol: E-57, E-61, ME-E49 y KA-E53 los verían, y
  bajo paralelismo sería una carrera;
- con el ADR-0018 en el árbol, KA-E56 sigue verde: busca «GraphRun» en el corpus `adr` de la fábrica real y
  espera un ítem de ADR-0016 (`74:4402-4446`), con un tope de 20 ítems (`TOPE_ITEMS`,
  `harnesses/desarrollo/bin/conocimiento/acceso.py:62, 418`). **El texto del ADR-0018 no nombra «GraphRun»**;
- el encoding lo impone `00-encoding-fuentes.ps1` con **dos reglas distintas**, leídas sobre `d86b285`:
  (1) todo `.ps1` o `.psm1` bajo la raíz (fuera de `.git`) que contenga un byte no ASCII lleva BOM UTF-8
  (`00-encoding-fuentes.ps1:21-46`; la alternativa válida es no tener no ASCII); (2) **ningún `.py`** bajo la
  raíz lleva BOM, tenga o no no ASCII (E-28, `00-encoding-fuentes.ps1:49-72`; excluye `.git`, `tests\out` y
  `__pycache__`). No controla `.md` ni `.json`. Para lo nuevo: `Invoke-Tests-Parallel.ps1`,
  `Compare-TestRuns.ps1` y `Measure-TestRuns.ps1` llevan BOM si tienen acentos; `75_manifest_paralelo.py` y
  `75_runner_paralelo.py` se guardan **sin BOM** (VC-35; corrige NB-04 del SPEC REVIEW).

### 8.4 Dueño

`harness-backend-engineer` construye y mantiene el runner, el manifest, el comparador, el medidor y los dos
casos (VD-02). `harness-staff-engineer` puede después hacerlo más rápido con el comportamiento congelado.

### 8.5 Relación con el método de verificación optimizado

El runner **complementa** el método, no lo reemplaza: un dueño por escenario, refutación focal, muestreo de
mutaciones y **una** suite completa final con el oráculo. Lo focal sigue siendo `python tests\correr.py -k`
o `Invoke-Tests.ps1 -SoloCaso`; el runner sirve para la regresión ancha intermedia (después de una etapa,
antes de pedir refutación) y para el feedback del builder. La corrida final que cierra es siempre
`.\tests\Invoke-Tests.ps1`. En la construcción de 6.1 eso se traduce así: los pasos 1 a 9 de §29 se
sostienen con evidencia **focal** (`correr.py -k`, `-SoloCaso` y, desde que existe, el runner como
acelerador), y la **única** suite completa oficial de la construcción es la del paso 10, sobre el árbol
final previo a WU03-b: la pata serial del primer par N = 2 de WU03-b, lanzada por el medidor (D-T3, §1.3). No
hay otra suite completa separada.

---

## 9. Execution model

### 9.1 Componentes

```
Invoke-Tests-Parallel.ps1
  ├─ argumentos y manifest  ── ilegible o de forma inválida (§10.3a) ⇒ exit 1, sin correr nada
  ├─ candado pesada.lock    ── ocupado por otro runner / ilegible ⇒ exit 2, sin correr nada (§19.2)
  ├─ barrido                ── raíces hpp-* de corridas muertas (§19.4)
  ├─ raíz de la corrida     ── hpp-<id>.lock tomado, después hpp-<id>\
  ├─ huella inicial
  ├─ enumeración            ── las mismas llamadas que el oráculo (§20.1)
  ├─ scheduler              ── un solo hilo; N lugares; carriles; serial al final
  │    └─ worker ×N         ── powershell.exe -File tests\Invoke-Tests.ps1 -SoloCaso <archivo>
  │                            TEMP=TMP=TMPDIR=<raíz>\s<nnn>; stdout/stderr a <raíz>\logs\
  ├─ limpieza               ── reintento de los temporales de suite (§16.5)
  ├─ huella final
  ├─ agregador              ── registros por suite (§15.1), huellas y avisos → reporte canónico + exit;
  │                            costura interna (§16.7)
  ├─ raíz entera            ── se borra si todo verde y limpio (§16.5)
  └─ salida                 ── imprime el reporte; después de los hijos: suelta hpp-<id>.lock (y lo borra si la
                               raíz quedó limpia), después suelta pesada.lock (§19.5); exit 0 / 1
```

El orden de arriba es el que se construyó (etapa 4a): la limpieza de los `s<nnn>` y la huella final van
**antes** del agregador porque §15.3 le pasa las dos huellas y los avisos como entrada; el borrado de la raíz
entera va después, porque depende del veredicto. La versión aprobada dibujaba el agregador antes de la huella
final y de la limpieza; §15.3, §16.5 y §19.5 ya decían este orden. Corrección de texto de la pasada
post-WU03-b, sin cambio de VD.

### 9.2 Modelo de proceso

- **Un proceso por suite**, siempre `powershell.exe` de Windows (`$env:SystemRoot\System32\
  WindowsPowerShell\v1.0\powershell.exe`, como `Invoke-Tests.ps1:98`) con `-NoProfile -NonInteractive
  -ExecutionPolicy Bypass -File <raíz>\tests\Invoke-Tests.ps1 -SoloCaso <archivo>` y `-Detallado` si el
  runner lo recibió. Para un `.py`, ese oráculo filtrado lanza `correr.py -k <archivo>` como hoy.
- **Un worker por vez por lugar**; el lugar se libera cuando su proceso termina. No hay hilos, runspaces
  ni jobs de PowerShell.
- **El runner es un solo hilo** que lanza, espera con plazos cortos (nunca un `WaitForExit()` sin límite:
  retrasaría el Ctrl-C, WU13) y recolecta.
- **stdin vacío** (cerrado al lanzar); stdout y stderr del worker van a `<raíz>\logs\<nnn>.out` y
  `<nnn>.err`, en UTF-8; la consola es la del runner (el worker la hereda, y con ella el Ctrl-C).
- El runner **mantiene abierto el handle** de cada worker hasta recolectarlo: mientras tanto Windows no
  reusa su pid (observación de plataforma), y el corte por árbol (§14.3) no puede caer en un proceso ajeno
  con ese número.

### 9.3 Lifecycle de una corrida

`PREPARANDO` (argumentos, manifest) → `ADMITIDA` (candado) → `BARRIDA` → `CORRIENDO` → `RECOLECTADA` →
`LIMPIA` → `TERMINADA` (exit 0/1). Desde `CORRIENDO`, una cancelación lleva a `CANCELANDO` → `LIMPIA` →
`TERMINADA` (exit ≠ 0). `NO_ADMITIDA` (exit 2) no crea nada salvo el mensaje.

### 9.4 Identidad

La corrida se identifica por `<id>`: 8 hex aleatorios (como el GUID de `isolated-factory.ps1:72`). Nada de
la identidad entra al reporte comparable (VP-I11). Cada suite se identifica por su **nombre de archivo
exacto**, con extensión; su índice canónico `<nnn>` (orden de §20.1) nombra su temporal y sus logs.

### 9.5 El comparador

`Compare-TestRuns.ps1 -Serial <salida-del-oráculo> -Paralelo <salida-del-runner> -HuellaSerial <h>
-HuellaParalelo <h>` sale `EQUIVALENTE` (exit 0), `NO_EQUIVALENTE` nombrando cada campo que difiere (exit
1) o `NO_COMPARABLE` (exit 1) si las huellas difieren. Reglas en §20.4.

### 9.6 El medidor

`Measure-TestRuns.ps1 [-Workers <n>] [-Umbral <fracción>]` corre el protocolo de §5.4, imprime el registro
(condiciones de cada pata, huellas, walls, veredicto del comparador, intervalos, residuos) y sale 0 solo si las
tres huellas son iguales, el comparador da `EQUIVALENTE`, la corrida paralela **no dejó residuos atribuibles**
(ninguna raíz `hpp-<id>` ni `s<nnn>` suya en `TempBase`, ningún `hpp-<id>.lock` de esa corrida, ni
`AVISO LIMPIEZA_INCOMPLETA` en su salida: §22.1, más estricto que el exit 0 del runner, §16.5;
`pesada.lock` y `pesada.json` no cuentan) y, si se pasó `-Umbral`, wall paralelo ≤ umbral × wall serial.
Corre las dos patas **sin `-Detallado`** (D-T5, §1.3): la serial es exactamente `.\tests\Invoke-Tests.ps1` y
la paralela `.\tests\Invoke-Tests-Parallel.ps1 -Workers <n>`; por eso el punto 5 de §20.4 no se evalúa en el
benchmark, y los puntos 1–4 y 6 sí, sin tolerancia.
Corre cada pata con su temporal nuevo y vacío y con el entorno que heredó, sin tocar el `PATH` (§5.4, §5.7 B2);
su muestreador de RAM no lo sobrevive (§5.7 B5). No escribe en el repo: el registro se copia a
`benchmark-<fecha>.md` a mano.

**Modo de reuso de la pata serial** (D-T2, §1.3; el parámetro que lo activa lo nombra el builder). Recibe la
carpeta de un registro anterior del medidor (el del primer par N = 2), que guarda fuera del repo la captura
serial, sus condiciones, su wall y su exit, y la lista `(ruta, tamaño, sha256)`, el HEAD y el
`git status --porcelain` de su huella final. En ese modo no corre la pata serial: aplica las condiciones
(1)-(4) de §5.4, corre la pata paralela entera y, si alguna condición falla, sale «no se pudo medir», nunca 0.
Las «tres huellas iguales» de arriba y de VP-E25 se leen así: las huellas completas antes y después de la pata
paralela son iguales entre sí; la huella final del primer par y la del árbol de cierre difieren solo en
`tests/parallel-manifest.json`; y las huellas sin esa ruta, las que recibe el comparador, son iguales. El
registro lo dice explícitamente. VP-E25 cubre también este modo.

---

## 10. Suite metadata

### 10.1 Dónde vive y quién lo mantiene

`tests/parallel-manifest.json`, versionado, al lado del runner. Lo mantiene `harness-backend-engineer`;
**lo actualiza el builder de cualquier Task que agregue, renombre o borre un archivo de `tests/casos/`**, en
el mismo cambio. El inventario de §6 es su contenido inicial, con sus tiempos.

### 10.2 Campos

```json
{
  "schema": "parallel-manifest/1",
  "suites": [
    { "suite": "73_ejecucion_de_grafo.py", "class": "lane", "lane": "motor",
      "maxSeconds": 728.8, "timeoutSeconds": 2187,
      "reason": "M: ventanas de pocos segundos (72:875-923, 73:2167-2183); 728,8 s en WU03-a" }
  ]
}
```

| Campo | Valores | Regla |
|---|---|---|
| `suite` | nombre exacto de un archivo de `tests/casos/` | único |
| `class` | `parallel` · `lane` · `serial` | — |
| `lane` | nombre (`motor`, `instalador`, `ventana`) si `class` = `lane`; `null` si no | — |
| `maxSeconds` | número > 0 o `null` (forma) | en el manifest real: el máximo de las duraciones válidas (§5.7 B1) de las corridas que lo alimentan: la suite sola de WU03-a y el primer par de WU03-b; las del par que cierra no realimentan (§5.7 B4) (política) |
| `timeoutSeconds` | entero > 0 o `null` (forma) | en el manifest real: `null` si `maxSeconds` es `null`; si no, **exactamente** `max(ceil(3 × maxSeconds), 1200)` (VD-11) (política). La fórmula es del manifest productivo, no del runner: un manifest sintético de un test puede declarar cualquier entero > 0 (VP-E08) |
| `reason` | texto (forma) | en el manifest real, **política ejecutable** (VP-E24, VP-I17): es un string y no está vacío ni es solo espacios en blanco. **Revisión semántica humana**, no ejecutable: que explique correctamente la clase, que la evidencia citada la sostenga y que el lenguaje sea apropiado; eso lo revisa el SPEC REVIEW y cada revisión posterior del manifest. Convención documental, no condición de test: los `reason` se redactan en español, con su cita |

«Forma» es lo que el runner valida antes de correr; «política», lo que la suite valida sobre el manifest
real (§10.3).

**Los valores iniciales** son los de §6: `maxSeconds` = la suite sola de WU03-a, MEASURED-BASELINE; ninguna de
las 97 en `null`; `timeoutSeconds` por la fórmula, y solo t73 pasa 1200 (2187). **Cómo se actualizan**
(analista:D1, VC-29): el primer par N = 2 de WU03-b lleva cada `maxSeconds` a `max(valor actual, duración de la
suite en la pata paralela)` cuando esa duración es válida (§5.7 B1), y se recalcula `timeoutSeconds`; las filas
98-99 se llenan ahí. Ese cambio cambia la huella, y el par que cierra corre sobre el manifest ya actualizado:
sus duraciones se registran y no vuelven al manifest. El lazo termina en un paso, por construcción. Una suite
que en el par que cierra pasa su `timeoutSeconds` sale `TIMEOUT`, roja: el par no es equivalente y se registra
(§17, F7); no se sube el timeout para que pase sin un par nuevo.

### 10.3 Validación: dos niveles

El manifest se valida en dos lugares distintos, por dos razones distintas, y no se duplica la lógica.

**10.3a Validación de forma, en el runner (runtime).** Antes de correr nada, el runner valida **solo lo
que necesita para ejecutar de forma segura**: el archivo existe y es JSON; `schema` = `parallel-manifest/1`;
`suites` es una lista; cada entrada tiene `suite` (texto no vacío, sin repetir dentro del manifest),
`class` ∈ {`parallel`, `lane`, `serial`}, `lane` (texto no vacío si y solo si `class` = `lane`, `null` si
no), `maxSeconds` (`null` o número > 0), `timeoutSeconds` (`null` o entero > 0) y `reason` (texto). Un
manifest que no pasa esto es `MANIFEST_INVALIDO`, exit 1, **sin lanzar ninguna suite** (§10.4): sin forma
confiable no hay scheduling seguro. El runner **no** comprueba la cobertura contra `tests/casos/`, ni que
los archivos nombrados existan, ni que `reason` diga algo, ni la fórmula de `timeoutSeconds`, ni los
nombres por subcadena: usa el entero de `timeoutSeconds` que recibe, tal cual. Por eso un manifest
sintético de un test puede declarar `timeoutSeconds: 9` (D-T4, §1.3) para probar el corte sin esperar 20 minutos
(VP-E08). No hay ningún parámetro ni modo «de prueba» para esto: es la validación normal. La prueba esta
validación la parte B de VP-E24, en `75_runner_paralelo.py`, con procesos reales (VC-34).

**10.3b Validación de política, en la suite.** `75_manifest_paralelo.py` (VP-E24, parte A: unidad, sin
procesos), sobre el manifest **real**, `tests/parallel-manifest.json`, tomando la forma de 10.3a como
precondición de sus datos (no la reimplementa como política):

1. cada `tests/casos/*.ps1` y `*.py` tiene **exactamente una** entrada (cobertura 1:1), sin entradas
   duplicadas y sin entradas que nombren un archivo inexistente;
2. `reason` es un string y no está vacío ni es solo espacios en blanco (política ejecutable; lo demás de
   `reason` es revisión semántica humana, §10.2: el test no juzga el idioma ni si la cita prueba la clase,
   sin heurísticas ni NLP);
3. `timeoutSeconds` cumple la fórmula **exacta** `max(ceil(3 × maxSeconds), 1200)` cuando `maxSeconds` no
   es `null`, y es `null` cuando lo es (VD-11);
4. ningún nombre de archivo `.py` de `tests/casos/` es subcadena de otro: `-k` es por subcadena
   (`correr.py:58-59`), y el worker de uno correría también el otro. En el runner eso sale
   `GRUPO_AJENO`, rojo; esta regla impide que llegue a pasar en el árbol real;
5. las demás reglas de §10.2 marcadas «política».

Corre en el oráculo y en el runner: un archivo nuevo sin entrada, una entrada de más o un `timeoutSeconds`
fuera de la fórmula ponen en rojo a los dos por igual, y la equivalencia no se rompe. La fórmula pertenece
al manifest real, no a las fixtures sintéticas de VP-E08.

### 10.4 Fail-closed en el runner

| Situación | Qué hace el runner | Por qué |
|---|---|---|
| Manifest ausente, no JSON, `schema` distinto, o una entrada que no cumple la **forma** de §10.3a (tipo, rango, `class`, `lane`, `suite` repetido) | `MANIFEST_INVALIDO`, exit 1, **antes** de correr nada | Sin forma confiable no hay scheduling seguro. Fail-closed ante un manifest realmente ilegible. Lo prueba VP-E24 parte B (`75_runner_paralelo.py`) |
| Entrada con la forma correcta pero fuera de la **política** de §10.3b (`timeoutSeconds` que no sigue la fórmula, `reason` vacío o solo espacios) | La usa tal cual; no dice nada | La política es del manifest real y la pone en rojo VP-E24 parte A en las dos corridas; en un manifest sintético es lo que VP-E08 necesita, y que el runner corre con ese valor lo prueba VP-E24 parte B |
| Suite de `tests/casos/` sin entrada | La corre como `serial` y lo dice con `AVISO SUITE_NO_CLASIFICADA <suite>`; no la pone roja por eso | `serial` es la condición del oráculo (sola): no puede dar un resultado distinto por convivir. El rojo lo pone VP-E24 en las dos corridas |
| Entrada que nombra un archivo inexistente | `AVISO SUITE_INEXISTENTE <suite>`, se ignora | Ídem: lo pone rojo VP-E24 |

🔴 **No se infiere nada del nombre de archivo.** Que un archivo termine en `-instalador.ps1` no lo hace
`instalador`: la clase está escrita o es `serial`.

### 10.5 Cómo cambia una clase

- **Hacia más estricta** (`parallel` → `lane` → `serial`): basta una corrida donde la suite dio rojo en
  paralelo y verde en serial sobre la misma huella, registrada en el benchmark. Después de la aprobación
  es una enmienda (§1.3).
- **Un caso con una falla serial documentada** (analista:D2, VC-30). Si el rojo en paralelo es de un caso que
  ya falló alguna vez en una corrida serial del oráculo, con su cita —hoy, solo t72 E34
  (`docs/versiones/0.34.0.md:149-158`)—: el par es `NO_EQUIVALENTE` igual y se registra (VD-14: sin tolerancia;
  §14.2: nunca se relanza la suite); **la regla de arriba se aplica igual** y la suite pasa a la clase más
  estricta, porque una clase más estricta nunca rompe la equivalencia; pero la reclasificación se registra como
  **precautoria, con la causa no demostrada**, y ese rojo **no cuenta** como falso rojo atribuible al runner
  (§35) mientras no se demuestre la causa. La suite vuelve a su clase solo por la regla de abajo. Si el caso
  falla en la pata **serial**, ninguna regla de clase aplica: el par se registra y se repite con un par nuevo.
- **Hacia menos estricta**: exige pares de WU03-b en verde y equivalentes con la clase nueva (al menos
  dos, sobre la huella del cambio), registrados. Nunca por defecto.

---

## 11. Resource classes

La hipótesis del brief, NORMAL / ISOLATED / HEAVY / SERIAL, **no se adopta tal cual**. ISOLATED no es una
clase: el aislamiento de §12 es para todas. HEAVY como «a lo sumo una pesada a la vez» junta en una sola
cola a t73, t72, los instaladores y las de ventana: con WU03-a, esa cola suma 2181,2 s (36,4 min)
MEASURED-BASELINE y ya pasa los 30 minutos (VC-09). Lo que explican las restricciones reales es **qué no puede
convivir con qué**:

| Clase | Qué limita | Quiénes | Por qué |
|---|---|---|---|
| `parallel` | Solo el límite global N | 71 + `75_manifest` | Sin ventana demostrada; el aislamiento resuelve el resto |
| `lane motor` | A lo sumo una del carril viva; convive con el resto | t72, t73 | Carreras de procesos y ventanas de segundos que se suman si corren juntas; t73 carga t72 |
| `lane instalador` | Ídem | 21 instaladores | Dos instaladores nunca a la vez, como en el oráculo; FH:1002 y FH:2281-2283 |
| `lane ventana` | Ídem | 55, t63c, 70, `75_runner` | Cotas superiores estrechas o falla bajo carga |
| `serial` | Ninguna otra suite viva | ninguna hoy; toda suite sin entrada | La condición del oráculo |

**Las respuestas del brief:**

- **Qué entra al pool:** todo lo que no es `serial`; los carriles son parte del pool.
- **Qué limita la concurrencia:** N (suites vivas) y la exclusión dentro de cada carril.
- **Qué corre solo:** `serial`; hoy, solo una suite que no esté en el manifest.
- **72 y 73:** no seriales al final; **una con otra, nunca juntas**, en el carril `motor`, que arranca
  primero (t73 es la más larga) y convive con el pool. Si WU03-b muestra que una de las dos da rojo así y
  verde en serial, pasa a `serial` (§10.5) y el piso se recalcula con la regla de §22.3.
- **Los instaladores:** ni HEAVY ni SERIAL: carril propio.
- **Worker count:** N = 2 por defecto (VD-07); WU03-b iba a evaluar 2 y 3, y en 6.1 midió solo 2 (D-T1). Con N = 2, mientras el carril `motor`
  ocupa un lugar, el otro corre lo demás de a una, y los carriles `instalador` y `ventana` no cambian
  nada: importan desde N = 3. Con N = 2 el stretch de 25 min es inalcanzable (§22.2, VC-28).
- **Qué cuenta el límite:** suites vivas, es decir procesos worker; no los nietos (VC-10).

---

## 12. Isolation

| Aspecto | Decisión | Evidencia |
|---|---|---|
| `TEMP`, `TMP`, `TMPDIR` | **Obligatorio**: los tres con el mismo valor, `<TempBase>\hpp-<id>\s<nnn>`, **nuevo y vacío por suite**, distinto de toda otra suite y corrida, fuera del árbol | .NET lee `TMP` primero, Python `TMPDIR` (WU04:fila 3, `isolated-factory.ps1:53`; `docs/versiones/0.34.0.md:163-164`); las marcas (`Invoke-Tests.ps1:137`) |
| `TempBase` | El valor de `$env:TEMP` del runner **tal cual**, sin expandir a formato largo; inyectable con `-TempBase` | Hoy es 8.3 (`C:\Users\204350~1\…`, del orquestador) y `LongPathsEnabled = 0` (WU04:fila 21): una raíz corta (+18 caracteres) cuida `MAX_PATH` |
| Resto del entorno | **Heredado sin cambios**: ni `PYTHONHASHSEED`, ni `PYTHONPYCACHEPREFIX`, ni `PYTHONDONTWRITEBYTECODE`, ni `PATH`, ni `CLAUDE_*`, ni `USERPROFILE` | VC-04, VC-08; los tests que necesitan una variable la ponen ellos (`72:273`; `74-knowledge-api-instalador.ps1:37-40`) |
| Precondiciones del entorno | **No las impone el runner**: Git Bash al frente, no elevado y un clon con los tags y commits base son del oráculo y de quien lanza (§5.2) | VC-04, VC-26 |
| cwd | La raíz del repo | `correr.py:5`; `Invoke-Tests.ps1:28` |
| Intérprete | El que resuelve el oráculo dentro del worker, con su regla | `Invoke-Tests.ps1:240-248`; `66_integrity_cleanup.py:471-476` |
| Preludio PS | El del oráculo, porque el worker **es** el oráculo | `Invoke-Tests.ps1:20-155` |
| Copia del árbol | **No**: rompe «mismo árbol» | Las suites corren git sobre `RAIZ` y contra bases fijas (§6, P·git, P·árbol) |
| cwd por worker | **No** | Nada lo pide; rutas relativas sin auditar |
| stdout/stderr | A `<raíz>\logs\`, nunca en el repo | VP-I08 |
| Puertos | Nada | t18 usa el puerto 0 (WU02) |

---

## 13. Scheduling

### 13.1 El algoritmo

1. **Lista de listas**: todas las suites que no son `serial` ni desconocidas, ordenadas por `maxSeconds`
   descendente (`null` al final) y, a igualdad, por orden canónico.
2. **Mientras haya un lugar libre** (menos de N vivas), se lanza la **primera** de la lista cuyo carril no
   tenga otra viva. Si ninguna se puede lanzar, se espera a que termine alguna.
3. **Cuando la lista se vacía y no queda ninguna viva**, se corren las `serial` y las desconocidas, de a
   una, en orden canónico.
4. Una cancelación (§18) corta en cualquier punto.

### 13.2 Por qué así

- **Más largas primero**: t73 es la suite más larga (728,8 s MEASURED-BASELINE); si arranca última, el wall
  es su duración más todo lo anterior.
- **`serial` al final y no al principio**: da lo mismo en tiempo total, y al principio retrasaría el
  arranque de t73.
- **Sin interbloqueo**: un carril solo puede estar ocupado por una suite viva; si no hay ninguna viva,
  ningún carril está ocupado y la primera de la lista se lanza. El paso 2 no puede esperar para siempre.
- **El orden de lanzamiento no tiene que ser determinista**; el reporte sí (§20).

### 13.3 El camino crítico (K9)

**MEASURED-BASELINE** (WU03-a, §5.6): carril `motor` = d73 + d72 = 728,8 + 218,8 = 947,6 s (15,8 min); carril
`instalador` 967,6 s (16,1); `ventana` 266,0 (4,4); `parallel` 929,6 (15,5); trabajo total W = 3110,8 s.

**La cota inferior** del wall, con f = 1 y empaquetado perfecto, es `máx(W/N, carril más largo)` más la
sobrecarga: N = 2 → máx(25,9; 16,1) = **25,9 min**; N = 3 → máx(17,3; 16,1) = **17,3**; N = 4 → máx(13,0; 16,1) =
16,1 (manda el carril `instalador`). **Con N = 2 manda W/N, no el carril `motor`** (VC-27): el borrador
suponía un carril de ≈ 26 min con las cifras MEASURED-previa, y hoy dura 15,8.

**ESTIMATED** (simulación a mano del algoritmo de §13.1 sobre los `maxSeconds` de §6, f = 1, sin sobrecarga,
analista):

| N | Secuencia clave | Wall con f = 1 | Con f de 1,0 a 1,3 |
|---|---|---|---|
| 2 | Lugar A: t73 de 0 a 728,8 s, t72 de 728,8 a 947,6, después el pool. Lugar B: `03-instalador.ps1` → 63-hu → t64 → 66 → `64_interaccion_humana.py` → t63c…; el carril `instalador` termina con 66-inst a ≈ 1533 s; sin lugares ociosos | ≈ 1556 s = **25,9 min** (≈ 26,5 con la sobrecarga de un worker por suite, R18) | 25,9 a 33,7 min |
| 3 | El carril `instalador` deja un lugar ocioso 71,4 s (de 492,6 a 564,0) más 1,6 s; termina a 1040,6 s | ≈ 1041 s = **17,3 min** (= la cota) | 17,3 a 22,5 min |

**Lo que midió WU03-b** (§5.6): f ≈ 1,23 en el par de cierre y una sobrecarga de ≈ 1 s por suite trivial
(R18). Con N = 2, ≤ 30 min se alcanzaba **solo si f ≲ 1,13-1,15** (ESTIMATED): con f ≈ 1,23, más
`75_runner_paralelo.py` (364,3 s en la pata paralela) y la sobrecarga, la pata paralela tardó **35,2 min**
(MEASURED-WU03-b), coherente con la tabla de arriba (f de 1,0 a 1,3: 25,9 a 33,7 min sin las dos suites
nuevas). La corrida 2 de WU03-a había mostrado tramos de 1,27-1,45× sin carga conocida (R21, R22). **Margen de
limpieza:** con N = 2 t72 termina a ≈ 15,8 min y la corrida a ≈ 26: los Hosts de t72 que viven hasta 60 s
(`72:299-305, 316-341`) mueren antes del reintento final de limpieza (§16.5); con N = 3 el margen baja a ≈ 93 s
y con N = 4 a ≈ 50-90 s (R24). La cola estrictamente serial de WU04:opción C (73 + 72 + 63-hu = 1170,1 s
MEASURED-BASELINE, solas al final, y el resto en el pool) da con N = 2 al menos (3110,8 − 1170,1)/2 + 1170,1 ≈
2140 s = **35,7 min** ESTIMATED con f = 1: queda descartada porque supera el target por construcción.

---

## 14. Worker lifecycle

### 14.1 Estados de una suite

`PENDIENTE` → `LANZADA` → `TERMINADA` (salió sola) · `MATADA_TIMEOUT` · `MATADA_CANCELACION` ·
`MUERTA` (desapareció sin que el runner la matara, o su salida no se puede leer). Una suite sin lanzar al
cancelar queda `SIN_LANZAR`.

**Observación de la construcción** (etapa 4b): desde afuera, un proceso que terminó con exit 0 o 1 no se
distingue de uno que salió solo. El runner decide con lo que ve: línea final, marca de resumen ausente o mensaje
propio del oráculo ⇒ `TERMINADA`; si no, el contrato de exit del oráculo (solo 0 o 1): exit fuera de {0, 1} o
ilegible ⇒ `MUERTA` (`Stop-Process` da −1); exit 0 o 1 con stderr no vacío ⇒ `TERMINADA` con `SIN_RESUMEN`;
exit 0 o 1 sin nada dicho ⇒ `MUERTA`. Queda una ambigüedad que la plataforma no deja cerrar: un worker matado
desde afuera con exit 1 (`taskkill /F` da 1) y stderr no vacío sale `SIN_RESUMEN`, no `WORKER_MUERTO`. Las dos
son `INFRA`, rojas y con exit 1: no cambia el exit, la equivalencia ni el conjunto cerrado de motivos (§17).

### 14.2 Lanzamiento y recolección

1. Se crea `<raíz>\s<nnn>` vacío y se fijan `TEMP`, `TMP`, `TMPDIR` del proceso hijo.
2. Se lanza (§9.2) y se registra el inicio en su intervalo.
3. Al salir: se cierra la captura, se registra el fin, se parsea (§15), se intenta borrar `s<nnn>`. Si no
   se puede (un proceso vivo tiene un archivo abierto), se reintenta al final de la corrida (§16.5).
4. **Nunca se relanza una suite.** Ni por timeout, ni por muerte, ni por falla (FH:1019-1021).

### 14.3 Timeout y corte

- Si `timeoutSeconds` no es `null` y la suite lo pasa: `taskkill /PID <worker> /T /F` mientras el handle
  sigue abierto, y la suite queda `MATADA_TIMEOUT`, roja con `TIMEOUT <suite> <límite> s`.
- Si `timeoutSeconds` es `null`: **no se mata**; desde los 1200 s, cada 600 s, una línea
  `LENTA <suite> <t> s`, fuera del reporte comparable.
- El corte alcanza al worker y a los descendientes cuya cadena de padres sigue viva. **Un nieto cuyo padre
  ya murió no se alcanza** (observación: `taskkill /T` recorre por padre; WU04). Lo que quede vivo y
  retenga el temporal de la suite aparece como `LIMPIEZA_INCOMPLETA` (§16.5).
- **El runner nunca mata un proceso que no sea un worker suyo o un descendiente vivo de uno**: ni por
  nombre de imagen ni por un pid guardado.

---

## 15. Result model

### 15.1 El registro por suite

| Campo | Origen | Uso |
|---|---|---|
| `suite`, `engine` (`ps`/`py`, por extensión), `index` | Enumeración | Orden canónico, conjunto de casos |
| `state` | §14.1 | Rojo si no es `TERMINADA` |
| `exitCode` | El proceso | Cruce con los conteos |
| `reported` | ¿Hay línea final válida? (§15.2) | Rojo si falta |
| `ok`, `total` | Línea final | Suma |
| `groups[]` (nombre, n, malos) | Líneas de grupo de su motor | Reagrupar; cruce con `total`; grupos ⊆ {stem} en Py |
| `failedRows[]` (grupo, nombre, detalle) | `Fallos:` (PS) o `MAL` (Py) | Lista de fallos |
| `rows[]` (grupo, nombre, ok) | Solo con `-Detallado` | Comparador |
| `infra` | Runner (§17) | Motivo propio; nunca suma pasadas |
| `stdoutPath`, `stderrPath`, `seconds`, intervalo | Runner | Diagnóstico, progreso y la duración que puede alimentar `maxSeconds` (§5.7 B1); **fuera** del reporte comparable |

### 15.2 Qué se lee de la salida

- **La línea final** es la última línea no vacía y tiene que ser exactamente
  `^(\d+)/(\d+) pasaron\.$` o `^(\d+)/(\d+) pasaron\. (\d+) fallaron\.$`. Es la línea combinada que el
  propio oráculo imprime (`Invoke-Tests.ps1:287, 290`), así que la cuenta y el exit los decidió el código
  del oráculo dentro del worker.
- **Las líneas de grupo** de su motor (§4): `OK`/`FALLA` con la cuenta entre paréntesis.
- **La marca de resumen ausente**: si la salida contiene `No se pudo leer el resumen de python
  tests/correr.py.` (`Invoke-Tests.ps1:268`), la suite es `SIN_RESUMEN`.
- **El stderr del worker se muestra, nunca decide.** El rojo por stderr de Python ya lo decidió el oráculo
  dentro del worker (VD-03): se ve como una línea final ausente y un exit 1.

### 15.3 Quién produce los registros y quién los consume

```
workers (procesos) ──► recolección / parser ──► registros por suite (§15.1) ──► agregador ──► reporte canónico + exit
                                                     ▲
                                 enumeración, manifest, huellas, estados del scheduler (§14.1)
```

El scheduler y la recolección producen **un registro por suite** con los campos de §15.1, a partir de la
salida capturada, del estado del proceso (§14.1) y de lo que el scheduler sabe (lanzada, cortada, sin
lanzar). El agregador (§16) consume **exclusivamente** esos registros, la lista enumerada (§20.1), las dos
huellas y el resultado de la validación de forma del manifest (§10.3a): no lee logs, no consulta procesos,
no vuelve a parsear nada. El reporte canónico y el exit se derivan **solo** de ahí. Los registros son
internos del runner: no son un archivo de intercambio, ni un JSON público, ni un contrato versionado, y
pueden cambiar con el runner.

---

## 16. Aggregation

### 16.1 Regla de exit

El runner sale **0** solo si, todo a la vez:

1. el conjunto de suites con registro es **exactamente** el enumerado: ninguna falta, sobra ni se repite;
2. toda suite está `TERMINADA`, `reported`, sin `infra`, con `exitCode` 0;
3. para cada suite, `ok == total` y la suma de `n` de sus grupos es `total`;
4. la huella final es igual a la inicial;
5. el manifest pasó la validación de forma (§10.3a);
6. ningún paso del runner levantó una excepción.

Imprimir `ok/total pasaron.` en su forma verde y salir 0 es lo **último** que hace. Cualquier excepción
antes da ≠ 0 (VP-I01). Cualquier otra cosa: exit 1.

### 16.2 El reporte canónico

Reproduce las formas del oráculo, en este orden: encabezado del oráculo; los grupos PS **reagrupados
globalmente** por nombre sin distinguir mayúsculas, en orden de primera aparición siguiendo el orden
canónico de archivos, con sus cuentas sumadas (lo que hace `Group-Object` en `Invoke-Tests.ps1:188`);
`Fallos:` con las filas PS en orden canónico; `ok/total pasaron (PowerShell).`; el bloque de Python con sus
grupos y líneas `MAL` (o `ok` con `-Detallado`) en orden canónico y `ok/total pasaron.`; el bloque de
infraestructura; la línea final.

### 16.3 El bloque de infraestructura y los avisos

Antes de la línea final: una línea `INFRA <MOTIVO> <suite> [detalle]` por error, en orden canónico; las
líneas `AVISO …` (§10.4, §16.5); y si hubo al menos un `INFRA`, `N suites con error de infraestructura.`

### 16.4 La línea final

- Verde: `ok/total pasaron.` — aparece **si y solo si** el exit es 0.
- Rojo: `ok/total pasaron. N fallaron.` con N = total − ok, **también si N es 0** (como el oráculo,
  `Invoke-Tests.ps1:290`). `total` y `ok` suman solo aserciones reales: un error de infraestructura no es
  una fila (WU07:D4, campo aparte).

### 16.5 Limpieza y su aviso

Al terminar todas las suites se reintenta borrar cada `s<nnn>` pendiente. Lo que no se pudo borrar sale en
`AVISO LIMPIEZA_INCOMPLETA <ruta>` y **no cambia el exit** (WU13:D-T2, rama a): t72 deja Hosts vivos a
propósito hasta 60 s (`72:299-305`, «el motor muere y el Host puede seguir»), y ponerlo en rojo daría
rojos falsos en corridas reales. Con todo verde y limpio, se borra la raíz entera **y su sidecar
`hpp-<id>.lock`** (§19.5, caso 1): de esa corrida no queda nada en `TempBase`. Si algo fue rojo o quedó un
residuo declarado, se conservan `<raíz>\logs\` (o lo que no se pudo borrar) hasta la próxima corrida, el
resumen imprime su ruta, y el `hpp-<id>.lock` **queda, liberado, junto a la raíz** (§19.5, caso 2), para que
la corrida siguiente lo tome y barra las dos cosas juntas (§19.4).

**Los residuos de las suites** (760 entradas por corrida completa en WU03-a, §5.6) caen, en el runner, dentro
del `s<nnn>` de cada suite y se borran con él: no son `LIMPIEZA_INCOMPLETA`, salvo que un Host de t72 o t73
siga vivo y retenga algo (analista:RC3, R24). No son «residuos atribuibles a la corrida paralela» en el sentido
de §22.1 mientras se borren con su `s<nnn>` (VC-21).

Esa es la semántica de una **corrida funcional**: sale 0 aunque exista `AVISO LIMPIEZA_INCOMPLETA`, si se
sostienen las seis condiciones de §16.1 y el residuo es de los permitidos (un handle tardío de un hijo
que la suite dejó a propósito). Un handle tardío conocido no se convierte en falso rojo. **El benchmark y
la adopción son más estrictos** (§22.1, VP-E25, §28): un par con cualquier residuo atribuible a la corrida
paralela (una raíz `hpp-<id>`, un `s<nnn>`, el sidecar `hpp-<id>.lock` de esa corrida o un
`AVISO LIMPIEZA_INCOMPLETA` en su salida) **no se acepta**, aunque el runner haya salido 0. Las dos cosas conviven: el aviso no cambia el exit, y el medidor
no acepta un par con aviso.

### 16.6 Progreso

Mientras corre, una línea por suite terminada: `[<k>/<total>] OK|FALLA|INFRA <suite> (<n>) <seg> s`, y al
fallar una, sus líneas de fallo y la ruta de sus logs. El runner es el único que escribe en la consola; la
salida de cada worker va a su archivo: no hay intercalado.

### 16.7 La costura de testabilidad del agregador

VP-E13 exige probar el agregador con registros armados a mano. Para eso el runner mantiene la separación de
§15.3 de forma que **la agregación se pueda invocar con registros sintéticos sin lanzar procesos**: sin
workers, sin tocar `TempBase`, el candado, el manifest real ni el árbol, y sin falsificar un stdout entero.
Cargar el runner para alcanzar esa parte **no ejecuta ninguna corrida** (el cuerpo que corre queda detrás
de una guarda de invocación, de modo que un dot-source no tiene efectos laterales). Cómo se llama esa parte
y cómo se organiza el script lo decide el builder: la spec no fija nombres de función ni módulos.

Es una costura **interna, de testabilidad**. No es una CLI pública, ni un parámetro documentado, ni un
archivo de intercambio, ni un servicio, ni un JSON público, ni un proceso nuevo, ni un contrato de usuario:
la forma de los registros es la de §15.1 y puede cambiar con el runner, y VP-E13 cambia con ella.

---

## 17. Failure semantics

| Evento (WU08) | Qué ve la persona | Suite | Exit |
|---|---|---|---|
| F1 aserciones rojas | `FALLA` del grupo, filas en `Fallos:`/`MAL`; el resto sigue | roja, `reported` | 1 |
| F2 rojas en los dos motores | Las dos listas, PS primero | rojas | 1 |
| F3 worker muerto (Stop-Process externo) | `INFRA WORKER_MUERTO <suite>` | `MUERTA` | 1 |
| F4 nieto huérfano | Nada si no retiene el temporal; si lo retiene, `AVISO LIMPIEZA_INCOMPLETA` | la de sus aserciones | según el resto |
| F5 salida cortada, sin línea final o con la marca de resumen ausente | `INFRA SIN_RESUMEN <suite>` (nunca `0/0 pasaron.`) | roja | 1 |
| F6 stderr de una suite Py | Lo que haga el oráculo dentro del worker: hoy, corta ⇒ `SIN_RESUMEN`, con el stderr mostrado | roja | 1 |
| F6b stderr nativo dentro de una suite PS | Se muestra; decide lo mismo que el oráculo sobre ese árbol. Observado en VP-E07 (etapa 4b): con `cmd /c "echo x 1>&2"`, verde en el oráculo copiado y `OK` en el runner, con el bloque `stderr del worker:` visible | la del oráculo | según el resto |
| F7 timeout | `INFRA TIMEOUT <suite> <límite> s`; árbol cortado; sin reintento | roja | 1 |
| F8 Ctrl-C o señal inyectable | `CANCELADO`: terminadas, abortadas (`INFRA CANCELADA`), sin lanzar; resumen `INCOMPLETO` | abortadas rojas | ≠ 0, nunca 0 |
| F9 exit y conteo incoherentes (exit 0 con `N fallaron.`, exit 1 con la forma verde, grupos que no suman `total`) | `INFRA EXIT_INCOHERENTE` o `INFRA RESUMEN_INCOHERENTE <suite> <valores>`. Observado en la construcción (etapa 4b): con el oráculo como worker, la mitad de exit no la produce un proceso real, porque la línea combinada del oráculo ya viene coherente con su exit (VP-E04 (b) sale `FALLA`, roja, no `INFRA`); esa rama la prueba VP-E13 con registros sintéticos. La de grupos sí es alcanzable (VP-E04 (a)) | roja | 1 |
| F9b resumen válido `0/0 pasaron.` con exit 0 | Verde, como el oráculo (WU07:D10, rama a) | verde | según el resto |
| F10 el agregador falla | `INFRA ERROR_INTERNO` y la pila | — | 1 |
| F11 el scheduler pierde o repite una suite, o una `serial` convive | `INFRA SUITE_AUSENTE` / `SUITE_DUPLICADA` / `ERROR_INTERNO violación de clase` (por los intervalos) | — | 1 |
| F12 limpieza incompleta | `AVISO LIMPIEZA_INCOMPLETA <ruta>`; en el benchmark, el par no se acepta (§16.5, §22.1) | sin cambio | según el resto (corrida funcional) |
| F13 candado ocupado por otro runner | `LOCK_OCUPADO desde <hora> (pid <x>, informativo)`; ninguna línea de suite | no corre nada | **2** |
| F14 dueño del candado muerto | Corre normal | — | normal |
| F15 candado ilegible (ruta inválida, directorio, permisos) | `LOCK_ILEGIBLE <causa>` | no corre nada | **2** |
| F16 manifest ilegible o de forma inválida (§10.3a) | `MANIFEST_INVALIDO <causa>` | no corre nada | 1 |
| F16b suite sin entrada | `AVISO SUITE_NO_CLASIFICADA`, corre `serial` | la suya | según el resto |
| F17 sin Python, `tests/casos` vacío | Lo que diga el oráculo en cada worker; `casos` vacío lo dice el runner como el oráculo (`Invoke-Tests.ps1:169-172`) | rojas | 1 |
| F18 sin Git Bash al frente, elevado, o un clon sin las bases | Las suites que lo necesitan fallan como en el oráculo (VC-04, §5.2) | rojas | 1 |
| F19 la huella cambió durante la corrida | `INFRA ARBOL_CAMBIADO` con las líneas de `git status` que difieren | — | 1 |
| F20 no se pudo calcular la huella | `INFRA HUELLA_NO_DISPONIBLE` | — | 1 |

**Códigos de motivo, cerrados:** `WORKER_MUERTO`, `SIN_RESUMEN`, `TIMEOUT`, `CANCELADA`,
`EXIT_INCOHERENTE`, `RESUMEN_INCOHERENTE`, `GRUPO_AJENO`, `SUITE_AUSENTE`, `SUITE_DUPLICADA`,
`ERROR_INTERNO`, `ARBOL_CAMBIADO`, `HUELLA_NO_DISPONIBLE`; avisos `SUITE_NO_CLASIFICADA`,
`SUITE_INEXISTENTE`, `LIMPIEZA_INCOMPLETA`; de admisión `LOCK_OCUPADO`, `LOCK_ILEGIBLE`,
`MANIFEST_INVALIDO`. `GRUPO_AJENO`: una suite Py que reporta un grupo distinto de su stem (`-k` es por
subcadena, `correr.py:58-59`: correría otra suite también).

---

## 18. Cancellation

- **Un solo camino de salida.** El bucle del scheduler vive dentro de un `try/finally`; Ctrl-C (PowerShell
  5.1 corre los `finally` al detener el pipeline: observación de plataforma) y la **señal inyectable**
  (`-CancelFile <ruta>`: si el archivo aparece, el bucle levanta una excepción propia) llegan al mismo
  `finally`. Lo que se prueba con la señal es el mismo código que corre ante Ctrl-C; lo único que no se
  prueba es el disparo del propio Ctrl-C (§24, R7).
- **Orden:** (1) el scheduler deja de lanzar; (2) cada worker vivo: `taskkill /PID <w> /T /F` con el handle
  abierto; (3) se espera su salida con plazo corto; (4) se recolecta lo que haya; (5) limpieza (§16.5);
  (6) reporte `CANCELADO … INCOMPLETO`, sin la forma verde de la línea final; (7) se sueltan los candados
  (§19.5); (8) exit ≠ 0.
- **Los workers comparten la consola**, así que un Ctrl-C real también les llega a ellos y a sus hijos
  (como en serial); el paso (2) cubre a los que lo ignoran.
- **Sin Job Object** (VD-11, VC-07). Un nieto huérfano puede sobrevivir a la cancelación; si retiene el
  temporal, queda declarado y lo barre la próxima corrida (§19.4).

---

## 19. Resource lock

### 19.1 Mecanismo

L1 de WU10, el precedente del repo para «¿vive el dueño?»: **un candado del SO sobre un archivo estable**,
sin esperar (`registro.py:35-36`, «nunca una fecha ni un pid»; MD-06 en ME:630-640; §14.1 de GE:767-787;
`registro.py:925-945`). En PowerShell: `[IO.File]::Open(<ruta>, OpenOrCreate, ReadWrite, ReadWrite)` y
`FileStream.Lock(0, 1)`; un fallo de bloqueo es «ocupado».

### 19.2 Qué, dónde, quién

- **Ruta:** `%LOCALAPPDATA%\gcba-harness\recursos\pesada.lock` (por usuario y por máquina, fuera de todo
  árbol: ve las copias de `%TEMP%\rt6-*` y `C:\dev\_build`); inyectable con `-LockPath` para los tests.
- **Al lado**, `pesada.json` `{pid, desde, raíz del repo, workers}`, **informativo**: se escribe después de
  tomar, con temporal y renombrado; nunca decide nada.
- **El archivo `.lock` no se borra nunca** (evita el *delete pending* y la forma de N1, GE:773-776).
- **Lo toma solo el runner.** El oráculo no (VD-04: su salida y su exit no cambian); `correr.py -k`
  tampoco; los lotes de mutaciones de los refutadores tampoco; el medidor tampoco: en su pata paralela lo toma
  el runner que lanza, y en la pata serial no lo toma nadie (analista:D7). Esa decisión se mantiene en 6.1: no
  se ensancha el código para coordinar todos los procesos de prueba (VX-07).
- **Una sola clase, exclusiva.** Un segundo runner, en cualquier árbol del mismo usuario, sale con 2.
- **Qué garantiza y qué no.** 6.1 garantiza **exclusión entre dos runners paralelos que toman
  `pesada.lock`**: de dos, corre uno. 6.1 **no garantiza exclusión técnica** contra el oráculo serial, las
  ejecuciones focales (`correr.py -k`, `-SoloCaso`), los lotes de mutaciones, el tramo serial del medidor,
  procesos externos ni ninguna herramienta que no tome el candado: nada de eso ve el candado ni lo espera.
  Es una **limitación conocida**, no una propiedad implícita; lo que la cubre mientras tanto es la regla
  operativa de §28, que es del workflow y no del código.

### 19.3 Espera

**Ninguna.** Falla rápido: `LOCK_OCUPADO desde <hora> (pid <x>, informativo)` con exit 2, sin correr nada.
No hay sonda que tome y suelte (N1, GE:872-899): una sola operación «intentar tomar». Esperar con plazo es
VX-16.

### 19.4 El barrido, con el mismo mecanismo

Cada corrida crea **primero** `<TempBase>\hpp-<id>.lock`, lo toma, y **después** crea la carpeta
`hpp-<id>\`: no hay instante en que la carpeta exista con su candado libre y su dueño vivo. Con el candado
global tomado, el runner barre: para cada `hpp-*.lock` del `TempBase` que **puede tomar**, su dueño murió:
borra `hpp-<id>\` y después suelta y borra el `.lock`. Si no puede tomarlo, vive: no lo toca. Si la carpeta
no se pudo borrar entera (un huérfano retiene algo), deja el `.lock` para reintentar la próxima vez. Una
carpeta `hpp-*` sin su `.lock` no se toca y se avisa. **El borrado no sigue reparse points y se niega a
borrar fuera del `TempBase` o algo que no tenga el nombre `hpp-<8 hex>`** (como `Remove-FabricaAislada`,
`isolated-factory.ps1:88-98`).

### 19.5 Al salir: el ciclo de vida de `hpp-<id>.lock`

El sidecar de una corrida nace tomado antes que su raíz (§19.4) y termina de una de tres formas. En todas,
el dueño lo dice el candado del SO: nunca un pid, una fecha ni que el archivo exista.

- **Caso 1, la corrida termina y su raíz quedó limpia.** En este orden: (1) terminan todos los workers, o se
  cortan; (2) se limpia la raíz (§16.5) y se emite el reporte; (3) se libera el `FileStream` de
  `hpp-<id>.lock`; (4) se borra `hpp-<id>.lock`; (5) se suelta `pesada.lock`. Resultado: de esa corrida no
  queda ni raíz ni sidecar en `TempBase`.
- **Caso 2, la corrida termina con `logs\` o un residuo declarado que se conserva** (`LIMPIEZA_INCOMPLETA`,
  corrida roja o cancelada): los mismos pasos, salvo el (4): el `FileStream` se libera y el archivo
  `hpp-<id>.lock` **se mantiene**, liberado, junto a la raíz, para que una corrida posterior pueda tomarlo y
  ejecutar §19.4 sobre las dos cosas. Una raíz que se conserva nunca queda sin su sidecar.
- **Caso 3, el runner muere.** El SO libera el candado por rango de bytes; el archivo y la raíz quedan como
  estén, y §19.4 los barre en la corrida siguiente, que sabrá que el dueño murió porque puede tomar el
  sidecar.

`pesada.lock` no sigue este ciclo: es estable por diseño y no se borra nunca (§19.2); `pesada.json` es
metadata informativa, estable y no decide nada. Ninguno de los dos es un residuo (§22.1).

### 19.6 Ilegible

No poder abrir el candado (ruta que es un directorio, permisos, disco) **no** es «lo tiene otro», pero el
runner **no corre**: `LOCK_ILEGIBLE` con exit 2. Es la regla del precedente («ante la duda, vivo»,
ME:640; `registro.py:932-933`).

---

## 20. Determinism

### 20.1 Enumeración y orden canónico

- PS: `Get-ChildItem <casos> -Filter '*.ps1' | Sort-Object Name`, **las mismas llamadas** que
  `Invoke-Tests.ps1:166-167`, con su cultura.
- Py: el orden de `sorted()` de `correr.py:57`: el runner se lo pide al mismo intérprete o reproduce su
  regla exacta (comparación ordinal de los nombres en minúsculas); VP-E14 lo fija con dos nombres que
  separan esa regla de `OrdinalIgnoreCase` (`a_b.py` y `ab.py`).
- Una sola enumeración al principio. El reporte sale en orden canónico, **nunca en orden de llegada**.

### 20.2 Lo que no entra al reporte comparable

Pids, ids de corrida o de worker, rutas de temporal, duraciones, horas, líneas de progreso, `LENTA`. Los
detalles de una fila se muestran pero no se comparan.

### 20.3 Lo que no se fija

`PYTHONHASHSEED` (30 y 74 lo siembran en sus hijos a propósito, WU05), la colación de cada motor, el orden
de lanzamiento.

### 20.4 La equivalencia, y el comparador

Sobre la **misma huella** (§5.1), el oráculo y el runner son equivalentes si, todo a la vez:

1. mismo exit;
2. misma secuencia de líneas de grupo PS (nombre, n, malos) y Py (stem, n), en el mismo orden;
3. mismos `ok`, `total` y fallidas, por motor y combinados;
4. mismo multiconjunto de filas fallidas (grupo, nombre), en los dos motores;
5. con `-Detallado` en los dos, mismo multiconjunto de filas (grupo, nombre, ok);
6. el runner no tiene `INFRA`.

Una fila `MAL` de Python no separa nombre y detalle sin ambigüedad (`correr.py:91`): el comparador corta en
el primer prefijo de detalle conocido (`esperado <`, `no contiene <`, `contiene <`, `no esta vacio: <`,
`es falso`, `Traceback`; `correr.py:16-30, 68, 76`); si no encuentra uno, esa fila es `NO_COMPARABLE` y el
resultado no puede ser `EQUIVALENTE`. **No hay tolerancia**: ni lista de suites que derivan, ni margen, ni
opción para pedirlo (VC-05). Con huellas distintas: `NO_COMPARABLE`, nunca `EQUIVALENTE`.

---

## 21. Serial compatibility

- **El oráculo cambia en una sola cosa**: el parámetro opcional `-SoloCaso <archivo>` (M2), en el `param` de
  `Invoke-Tests.ps1:15-18`, que hoy tiene solo `-Detallado`. Sin él, la salida estándar y el exit son
  **idénticos byte a byte** a los del oráculo de la versión de partida, `v0.34.0` (VP-E23).
- **Por qué `-SoloCaso` y no `-Caso`:** `$caso` ya es la variable del bucle (`Invoke-Tests.ps1:174`) y
  PowerShell no distingue mayúsculas: un parámetro `$Caso` se pisaría.
- **Con `-SoloCaso`:** la primera línea es `Corrida parcial (-SoloCaso <archivo>): no es la compuerta.`;
  corre exactamente ese archivo: si es `.ps1`, solo el motor PS sobre él y no el de Python; si es `.py`,
  ningún `.ps1` y `correr.py -k <archivo>`; si no existe en `tests/casos/`, lo dice y sale 1. La última
  línea sigue siendo la combinada (§15.2).
- **Regla para M2** (§5.7 B6, VX-19): en `-SoloCaso`, si el `.ps1` no carga, el grupo de la fila «el archivo de
  casos se pudo cargar» sale **del objeto de la enumeración** (el archivo pedido), nunca de una variable que un
  caso dot-sourced pueda pisar: `03-instalador.ps1:846` reusa `$caso` en el scope del oráculo, y 65-inst y
  66-inst reusan `$nombre`. Así se sostiene VP-I05 también en ese camino. El camino por defecto no se toca
  (VD-04): su defecto latente es VX-19.
- Se conservan `sys.executable` (`Invoke-Tests.ps1:245`) y la regla de candidatos
  (`66_integrity_cleanup.py:471-476`, E-22), y la mención de `correr.py` (`Invoke-Tests.ps1:237`;
  `72:2330-2335`, ME-E51).
- **`tests/correr.py` no cambia**: ni `-k` (lo usa el refutador por subcadena,
  `harness-spec-refuter.md:57`), ni `Resultados` ni `filas` (las importan 65, 72 y 74: `74:3737-3747,
  4319-4327`, guardián).
- Los comandos del refutador y de `close-a-version` siguen siendo los de hoy.
- **Sin parámetros, `Invoke-Tests.ps1` es la compuerta, como dice `CLAUDE.md` §«The gate».**

---

## 22. Performance acceptance

### 22.1 Lo que es duro, sin medición

Diferencia de casos 0; de totales 0; falsos verdes 0; falsos rojos atribuibles al runner 0; restos en el
repo 0; **residuos temporales atribuibles a la corrida paralela del benchmark 0** (ni raíz `hpp-<id>`, ni
`s<nnn>`, ni el sidecar `hpp-<id>.lock` de esa corrida, ni `AVISO LIMPIEZA_INCOMPLETA` en su salida al
terminar el protocolo; `pesada.lock` y `pesada.json` no son residuos: son estables por diseño, §19.5). Se
miden con los pares de §5.4 (VP-E25). Esto último es más estricto que el exit del runner: en una corrida funcional el aviso de
limpieza no cambia el exit (§16.5); en el benchmark y la adopción, un residuo deja el par sin aceptar. Los
residuos que la pata **serial** deja en su propio temporal (760 por corrida, §5.6) son de las suites y del
oráculo, no de la corrida paralela: se registran y no rechazan el par (VC-21).

### 22.2 Los targets, con la baseline medida

| Target | Valor del brief | Estado |
|---|---|---|
| Wall serial | ~51 min limpio | **Medido**: 49,4 y 59,5 min, MEASURED-BASELINE (§5.6); para umbrales, el máximo |
| Wall paralelo, preferencia | ≤ 30 min | No normativo. ESTIMATED: con N = 2, solo si f ≲ 1,13-1,15 (§13.3). **No alcanzado:** 35,2 min en el par de cierre, con f ≈ 1,23 (MEASURED-WU03-b, §5.6) |
| Wall paralelo, stretch | ≤ 25 min | No normativo. **Inalcanzable con N = 2**: la cota con f = 1 es 25,9 min (§13.3, VC-28). Con N = 3, ESTIMATED 17,3 min con f = 1; N = 3 no se midió en 6.1 (D-T1) y no cambia el valor por defecto (VD-07) |
| Relación | ≤ 70 % del serial, «a validar» | **Normativo: ≤ 75 %** (D-T7, §22.3 regla 2). Medida: 0,7089 en el par de cierre (§5.6). El ESTIMATED previo era 70 % de 49,4 min (≤ 34,6) con f ≲ 1,30 |

### 22.3 La regla para fijar el umbral

Con WU03-a y el primer par de WU03-b (la relación es la de las dos patas de ese par):

1. si con el manifest inicial y N = 2 la relación es ≤ 70 %, **70 % pasa a normativo** y lo verifica
   VP-E25 con `-Umbral 0.70` sobre el par que cierra;
2. si no, la persona decide entre aceptar la relación medida como umbral o pedir un cambio de clase con
   evidencia (§10.5); **nunca se relaja la equivalencia para ganar tiempo**;
3. si una suite de `motor` tiene que pasar a `serial`, el piso pasa a ser
   **máx(W_resto/N, carril más largo del resto) + d(serial)**, donde W_resto es el trabajo de todas las demás y
   d(serial) la duración de la que pasó; el piso se recalcula con los `maxSeconds` vigentes, y si con f = 1
   supera 30 min, el target de 30 min se declara inalcanzable con esa clase, en el benchmark y en §1.3. Con los
   valores de WU03-a y N = 2 (ESTIMATED, f = 1): t72 a `serial` → máx(2892,0/2; 967,6) + 218,8 = 1664,8 s =
   **27,7 min**; t73 a `serial` → máx(2382,0/2; 967,6) + 728,8 = 1919,8 s = **32,0 min**, inalcanzable; las dos →
   máx(2163,2/2; 967,6) + 947,6 = 2029,2 s = **33,8 min**, inalcanzable. Con N = 3, t73 a `serial` da
   máx(794,0; 967,6) + 728,8 = 1696,4 s = 28,3 min.

**Resultado del primer par** (D-T6, §1.3): el par 1b de WU03-b (21/22-10-2026, N = 2), serial 3280,1 s y
paralelo 2158,2 s, los dos con exit 0 y 48841/48841, misma huella: relación **0,658 ≤ 0,70**. Aplica la regla 1:
**el 70 % es normativo** y VP-E25 se verifica con `-Umbral 0.70` sobre el par que cierra. La regla 2 no se
activa. *(Reemplazado por D-T7: ver el párrafo siguiente.)*

**Resultado del par de cierre y decisión de la persona** (D-T7, §1.3): el par de cierre (22-10-2026, N = 2,
sin `-Detallado`), serial 2976,9 s y paralelo 2110,4 s, los dos con exit 0 y 48841/48841, misma huella,
`EQUIVALENTE` y residuos 0: relación **0,7089 > 0,70**. La relación de D-T6 venía de patas con `-Detallado`, que
infla más la serial; la comparable es la del cierre, y con ella la regla 1 no aplica. Se aplicó la **regla 2**:
la persona (Nahuel Palacio, 22-10-2026) aceptó **0,75** como umbral normativo, y VP-E25 se verifica con
`-Umbral 0.75`. No se pidió un cambio de clase y la equivalencia no se relajó. La regla 3 no se activa: ninguna
suite pasó a `serial`.

---

## 23. Security / repo integrity

- **El runner no escribe en el árbol**: temporales, logs y reporte viven en `TempBase`; la huella lo
  comprueba en cada corrida (VP-I08), y t68 lo vigila desde adentro.
- **Borra solo lo suyo**: dentro de `TempBase`, con el nombre `hpp-<8 hex>`, sin seguir reparse points
  (t72 y t74 crean junctions en sus temporales: `72:1569-1575`, `74:222-233`, discoverer).
- **Mata solo lo suyo**: el árbol vivo de sus workers, con el handle abierto; nunca por nombre ni por un
  pid guardado.
- **No eleva, no usa red, no lee secretos**; los logs contienen lo que los tests imprimen, igual que la
  consola del oráculo, en el temporal del usuario.
- **No cambia el entorno salvo el temporal**; `-NoProfile` y `-ExecutionPolicy Bypass` como
  `Invoke-Tests.ps1:99`.
- **El candado y su `.json` viven en `%LOCALAPPDATA%\gcba-harness\recursos\`**, la única escritura fuera
  del temporal, y no contienen nada sensible.
- **`pre-tool-use.py` no se rompe en el árbol**: 03 rompe copias aisladas (`isolated-factory.ps1:1-11`); el
  runner no cambia eso. En WU03-a la huella quedó igual en las cuatro tomas, también con 03 corriendo tres
  veces.

---

## 24. Risks

| # | Riesgo | Qué lo acota | Lo que queda |
|---|---|---|---|
| R1 | **Resource contention**: N suites + carga ajena (otras sesiones, Edge) | N = 2; candado **solo entre runners** (§19.2); el medidor registra la RAM libre de cada pata (el piso no se fija en 6.1: §5.2, VX-28); la regla operativa de §28 para los trabajos pesados de cierre | Lo que no toma el candado (oráculo, focal, lotes de mutaciones, tramo serial del medidor, procesos externos) no queda excluido técnicamente; la regla operativa es del workflow, no del código (VX-07) |
| R2 | **Suite interference** | Temporal por suite; carriles; huella | Lo no demostrado; lo detecta la paridad por suite (§22) |
| R3 | **Hidden global state**: lo que en serial pasa de una suite a otra (`72:137`, grupo PS, `sys.modules`) | Detección por paridad; nunca se absorbe. WU03-a no vio ningún cambio de conteo en verde (§5.6) | Una suite que depende de otra: rojo en un modo, defecto de la suite (VX-11) |
| R4 | **Process leaks** | Corte por árbol; limpieza declarada; barrido por candado | Nietos huérfanos tras un corte (VX-08) |
| R5 | **Output interleaving** | Un archivo por worker; solo el runner escribe en consola | Un proceso que abre `CONOUT$` por su cuenta (69 usa su propia consola oculta) |
| R6 | **Flaky timing tests** | Carriles `motor` y `ventana`; N = 2 | f ≈ 1,23 en el par de cierre (§5.6), sin una falla de tiempo en las 99 suites de los pares 1b y de cierre; 19 E-29 (VX-10); t72 E34 (R25); VP-E08 y VP-E20 sensibles a la carga de la máquina (VX-25) |
| R7 | **Windows process tree termination** y Ctrl-C | `taskkill /T /F` con handle abierto; un solo `finally` | El disparo real de Ctrl-C no tiene test (§26, nota de VP-E19); nietos huérfanos |
| R8 | **PATH / Bash**: el `bash` que resuelve **depende del proceso lanzador**, no de la máquina: desde Git Bash, `…\Git\usr\bin\bash.exe` (`condiciones.txt` de WU03-a); desde PowerShell, en esta máquina, el stub de WSL (`docs/versiones/0.34.0.md:164-166`) | Herencia sin cambios en el runner y el medidor (VC-04); el encabezado del runner y el medidor registran el `bash` efectivo de cada pata, que tiene que ser el mismo (§5.7 B2); si quien lanza antepone Git Bash, lo deriva de `(Get-Command git).Source` (§5.2) | Reproducibilidad desde PowerShell; la precondición está escrita en una nota de versión, no en `CLAUDE.md` §«The gate» (VX-09); no verificado si `Git\bin\bash.exe` y `Git\usr\bin\bash.exe` se comportan distinto |
| R9 | **New suite without metadata** | `serial` + aviso en runtime; rojo por VP-E24 en los dos | Un builder que agrega la línea con una clase optimista: se ve en WU03-b o en el primer rojo |
| R10 | **Scheduler deadlock** | Argumento de §13.2; VP-E11 y VP-E12 | — |
| R11 | **Parallel runner masking failures** | El worker es el oráculo; regla de exit de §16.1; VP-I01 a VP-I06; 20 mutaciones | Una fuga de estado que en serial da rojo y por proceso verde: solo la ve la paridad real (§22) |
| R12 | **El oráculo no es determinista** (30/33 el 22-09; 19 E-29; t72 E34) | El comparador no tolera: lo reporta por suite | Pares en rojo sin defecto del runner: se registran, no se descartan |
| R13 | **Corte por memoria** de Claude Code | El medidor registra la RAM libre de cada pata; N chico; la regla operativa de §28 (un trabajo pesado de cierre a la vez) | El runner no mide RAM (VD-07); la regla depende de quien orquesta; el piso no se fijó (§5.2, VX-28): en la pata paralela del cierre la RAM libre bajó a 3,20 GB, sin atribuir |
| R14 | **MAX_PATH** con temporales anidados | Raíz corta; formato del `TEMP` heredado | Un `TEMP` largo: **pasó en el par 1 de WU03-b** (`75_runner_paralelo.py` rojo en el runner y verde en el oráculo por su guarda de 70 caracteres, §5.2); se corrió con `C:\t`; VX-26 |
| R15 | **Defender o el indexador** sobre temporales y candado | Archivo `.lock` estable | Sin medir (VX-01) |
| R16 | **PID reusado** que t72 mata con `_terminar` (`72:355-357`) | Carril `motor`, N = 2 | Más procesos en la máquina que en serial (VX-11) |
| R17 | **`-SoloCaso` usado como compuerta** | Primera línea que lo dice; la enmienda y el ADR | Disciplina |
| R18 | **Sobrecarga por suite** (un `powershell.exe` y la resolución de Python por suite) | Medida en WU03-b: ≈ 1 s por suite trivial, ≈ 0,8 min de wall con N = 2, ESTIMATED (§5.6); el arranque en frío medido, 2,65–3,25 s (D-T4) | Si pesa, es trabajo del staff engineer con el comportamiento congelado; el costo que más pesa es el de `75_runner_paralelo.py`, dominado por el arranque de cada worker de sus runners anidados (etapa 4b; VX-24) |
| R19 | **Restos de una corrida paralela matada** solo los barre otra corrida paralela | §19.4 | `CLAUDE.md:52-55` promete «a later run» (VX-18) |
| R20 | **El runner muere y sus workers no** (WU10:CW4): el SO suelta los dos candados con carga viva | El barrido no fuerza archivos abiertos y deja el `.lock` para reintentar (§19.4) | Una corrida nueva puede arrancar con la carga de la muerta; sin Job Object no se evita (VX-08) |
| R21 | **Dispersión serial ≥ 20 %** sin carga conocida, concentrada en los Python pesados (t63h a t74) de la corrida 2 (§5.6) | El máximo manda (§5.3); condiciones antes de cada pata (§5.2); orden registrado y alternado (§5.4) | f y el par de WU03-b pueden heredar un transitorio no atribuible: sin muestreo de CPU por proceso (§5.5) no se atribuye |
| R22 | **La duración de una suite en una corrida completa puede superar la de la suite sola** (inferido 1,27-1,45× en la corrida 2) | `maxSeconds` se actualiza con el primer par (§10.2); lo inferido no alimenta nada (§5.7 B1) | Un `maxSeconds` de una sola muestra quieta subestima hasta el primer par |
| R23 | **Falso TIMEOUT de t73 bajo contención** como la del 19-10 | 2187 s = 3,0× la suite sola, que cubre la peor dispersión conocida (2,15×) sobre la sola y la corrida 2 inferida (≈ 1,34×); la regla operativa de §28 | Contra la MEASURED-previa no cubre: 2187 < 1200 × 2,15 = 2580 (VC-24). Si pasa, es `TIMEOUT` rojo, visible, y el par no se acepta; nunca se sube el timeout sin un par |
| R24 | **`LIMPIEZA_INCOMPLETA` por Hosts de t72 con N ≥ 3** | Con N = 2 el margen es de minutos (§13.3); el par que cierra es N = 2 | Con N = 3 (≈ 93 s) o N = 4 (≈ 50-90 s) un Host vivo puede rechazar un par informativo por un residuo legítimo |
| R25 | **t72 E34, falla serial conocida** (`docs/versiones/0.34.0.md:149-158`), que en paralelo puede ser más probable | §10.5: reclasificación precautoria, sin contar como falso rojo del runner (VC-30) | Atribuir al runner algo preexistente, o perder tiempo por una reclasificación que no era necesaria: t72 a `serial` cuesta ≈ 1,8 min con f = 1 (§22.3) |
| R26 | **Sesgo de temporal en el par**: oráculo con un `TEMP` sucio o global contra un runner con `s<nnn>` vacíos | `TEMP` nuevo y vacío por pata (§5.4, §5.7 B2) | La previa 0,61× (§2.3) muestra cuánto puede pesar un `TEMP` cargado; sin demostrar |
| R27 | **El lazo `maxSeconds` → huella → par nuevo** | El primer par actualiza; el que cierra no realimenta (§10.2, §5.7 B4) | Un timeout en el par que cierra obliga a otro par, con causa registrada |
| R28 | **Muestreador del medidor huérfano** (como el de WU03-a, `medir.ps1:76, 140`) | §5.7 B5 | Diseño del medidor |

---

## 25. Invariants

| Id | Invariante | Escenarios |
|---|---|---|
| VP-I01 | El runner sale 0 solo si se cumplen las seis condiciones de §16.1; imprimir la forma verde y salir 0 es lo último; toda excepción interna da ≠ 0 | E01, E02, E04, E13 |
| VP-I02 | Cada suite enumerada corre exactamente una vez (un solo inicio); faltante, sobrante o repetida ⇒ exit 1 con su nombre; nunca se relanza | E01, E05, E13 |
| VP-I03 | Un error de infraestructura nunca suma a `ok`, nunca se cuenta como `0/0` y sale con su motivo, aparte de «fallaron» | E05, E06, E08 |
| VP-I04 | El resumen de una suite es su última línea no vacía con la forma exacta de §15.2; si sus grupos no suman su `total`, es roja | E04, E06 |
| VP-I05 | Un archivo que no carga aporta exactamente una fila «el archivo de casos se pudo cargar», con grupo `BaseName` o `stem`, `reported` y sin `INFRA`; una suite Py solo reporta su stem | E01, E03, E16 |
| VP-I06 | Pasa o falla una suite lo decide el código del oráculo dentro del worker; el stderr de una suite Python la pone roja como en el oráculo, y el del worker se muestra y nunca vuelve verde un rojo | E07 |
| VP-I07 | Dentro de una suite, `TEMP`, `TMP`, `TMPDIR`, `tempfile.gettempdir()` y `[IO.Path]::GetTempPath()` dan el mismo directorio, vacío al empezar, distinto del de toda otra suite y corrida, fuera del árbol; el resto del entorno, el cwd, el `PATH` y el intérprete son los del runner | E09 |
| VP-I08 | La huella del árbol al terminar es la del principio, también al cancelar; logs y reporte viven fuera; si cambió, exit 1 con `ARBOL_CAMBIADO` | E10, E19 |
| VP-I09 | Mientras corre una `serial` o una desconocida no hay otra suite viva; dos suites del mismo carril nunca están vivas a la vez | E11 |
| VP-I10 | Nunca hay más de N suites vivas, y hay N cuando hay trabajo que puede lanzarse | E12 |
| VP-I11 | El reporte comparable es idéntico byte a byte para cualquier orden de terminación y para N = 1, 2 y 4; sale en orden canónico y no contiene pid, ruta de temporal, id de corrida ni hora | E14 |
| VP-I12 | Con la misma huella, el comparador da `EQUIVALENTE` solo si se cumplen los seis puntos de §20.4; con huella distinta o una fila ambigua, `NO_COMPARABLE`; no existe tolerancia | E15, E16, E17, E18 |
| VP-I13 | Una suite con `timeoutSeconds` (el entero del manifest que el runner recibió, §10.3a, sea el de la fórmula o uno sintético) que lo pasa se corta con su árbol vivo, sale `TIMEOUT` y no se relanza; con `null` no se corta nunca | E08 |
| VP-I14 | Al terminar o cancelar no queda vivo ningún proceso del árbol vivo de un worker; el temporal de cada suite se borra o se declara (declarado vale para una corrida funcional, no para el benchmark: §22.1); una raíz limpia se borra junto con su `hpp-<id>.lock`, y una raíz que se conserva queda junto con su `hpp-<id>.lock` liberado (§19.5); la corrida siguiente barre la raíz de una corrida muerta y nunca la de una viva; el borrado no sigue reparse points ni sale de `TempBase`; el runner no mata un proceso ajeno | E19, E20, E21 |
| VP-I15 | «Ocupado» lo dice solo el candado del SO; de dos runners que toman el mismo candado corre uno y el otro sale 2 sin lanzar ninguna suite; un proceso que no toma el candado no queda excluido (§19.2); un dueño muerto libera; `pesada.lock` no se borra; uno ilegible sale 2 con su motivo; el candado se suelta después del último worker | E22 |
| VP-I16 | Sin `-SoloCaso`, la salida estándar y el exit del oráculo son idénticos a los de la versión de partida; con `-SoloCaso`, corre exactamente ese archivo y dice que no es la compuerta | E23 |
| VP-I17 | Cada archivo de `tests/casos/` tiene exactamente una entrada en el manifest real que cumple la política ejecutable de §10.3b (fórmula de `timeoutSeconds` y `reason` string no vacío ni solo espacios incluidos; la calidad semántica de `reason` es revisión humana, no de este invariante) y ningún nombre `.py` es subcadena de otro; si no, la suite es roja en el oráculo y en el runner (VP-E24 parte A, unidad); en runtime el runner exige solo la forma de §10.3a: un manifest ilegible o de forma inválida no corre nada (VP-E24 parte B, procesos), y una suite sin entrada corre `serial` | E11, E24 |

La paridad suite sola contra completa que registró WU03-a (§5.6) **no** sostiene ninguno de estos
invariantes: es una observación pre-construcción (VC-22). Las reglas del protocolo de §5.7 tampoco son
invariantes.

---

## 26. Scenarios

VP-E01 a VP-E24 corren en `75_runner_paralelo.py` o `75_manifest_paralelo.py` sobre **layouts sintéticos** en el
temporal: una carpeta `<tmp>\tests\` con copias del runner, del oráculo, de `correr.py` y de un manifest
sintético, y `tests\casos\` con fixtures generadas en el test (ASCII, rutas cortas, fuera del árbol: no
tocan las reglas de 00, t63h E-61, 71 E-16 ni el `git status` de t68). Los runners de prueba usan
`-LockPath` y `-TempBase` propios. La copia del runner y del oráculo **del árbol** se verifica por hash contra
el archivo del árbol antes de usarla; la del oráculo **de la versión de partida**, por blob id (VP-E23). Las
fixtures escriben un archivo de eventos por suite (inicio, fin, pid, hora de pared) para los intervalos. Cero
escenarios por lectura: el sujeto de todos es un script determinista, no una corrida de un modelo (ADR-0009).

**Las marcas `rojo visto`** las puso la pasada post-WU03-b desde los registros de la construcción, no de una
lectura: cada una nombra la mutación de §27 (con la variante del builder), la etapa, la fecha y las filas del
escenario que quedaron verdes sobre el total con la mutación aplicada, contra el control verde. Las mutaciones
se aplicaron a copias fuera del repo y se restauraron (etapa 9: 59 registros con `restaurado OK`). Se vieron
sobre versiones del test anteriores a la del árbol final (`75_runner_paralelo.py` `1944077A…` en la etapa 9,
`9EB38586…` en la 9c); después solo cambiaron los nombres de siete filas (`6F9DC970…`). Evidencia: `registro.md`
y `t61-etapa9-informe-builder.md` del orquestador; diffs y salidas en `C:\dev\_build\t61\e9\`, `e9c\`,
`e8\out\`, `e8b\out\` y `cierre\out\`.

### Camino feliz

- **VP-E01** — Con seis suites sintéticas verdes, dos `.ps1` y cuatro `.py` (dos donde el stem de una es
  prefijo del de la otra, `caso_a.py` y `caso_a_extra.py`), y N = 2, el runner sale 0; su última línea es
  `<ok>/<total> pasaron.` con `ok == total` igual a la suma de las aserciones de las seis; cada suite tiene
  un solo inicio en su archivo de eventos; cada suite Py reporta solo su stem. · rojo visto: sí (VM-01a 7/15,
  VM-01b 6/15, VM-02a 14/15 y VM-02b 14/15; etapa 9, 21-10-2026)

### Fallos

- **VP-E02** — Con una suite PS con 2 de 5 aserciones rojas, una Py con 1 de 7 y cuatro verdes, el runner
  sale 1; la línea final dice `N fallaron.` con N = 3; `Fallos:` y las líneas `MAL` contienen exactamente
  esas tres filas (grupo, nombre), PS antes que Py; las cuatro verdes salen `OK`. · rojo visto: sí (VM-03
  13/14; etapa 9, 21-10-2026)
- **VP-E03** — Un `.ps1` con error de sintaxis y un `.py` con `ImportError` aportan cada uno exactamente una
  fila roja «el archivo de casos se pudo cargar» con grupo igual a su nombre base o stem; ninguno sale como
  `INFRA` ni como suite ausente; exit 1. · rojo visto: sí (VM-12b, fila de carga del `.py` 14/15 y del `.ps1`
  13/15; etapa 9, 21-10-2026)
- **VP-E04** — (a) Una suite Py cuya fila roja tiene en el detalle el texto `3/4 pasaron.` y cuyo grupo
  cuenta 10 sale `INFRA RESUMEN_INCOHERENTE` con los dos valores, nunca verde; (b) una suite Py cuyo
  proceso imprime `5/5 pasaron.` y termina con exit 1 por un `atexit`, y otra que imprime `3/5 pasaron.` y
  termina con exit 0, salen las dos rojas en el runner, y el oráculo copiado da exit 1 sobre cada una.
  · rojo visto: sí (VM-04a 18/24 y VM-04b 16/24; etapa 9, 21-10-2026)
- **VP-E05** — Si un worker se mata con `Stop-Process` a mitad de su suite (el pid sale del árbol del
  runner por `ParentProcessId`), esa suite sale `INFRA WORKER_MUERTO`, no suma a `ok`, no se relanza (un
  solo inicio) y las demás se reportan con sus resultados; exit 1. · rojo visto: sí (VM-03 19/20, VM-13a 17/20
  y VM-13b 17/20; etapa 9, 21-10-2026)
- **VP-E06** — Una suite Py que termina con `os._exit(0)` sin imprimir resumen, otra que imprime `12/` y
  corta, y otra con la salida vacía salen cada una `INFRA SIN_RESUMEN`, nunca `0/0 pasaron.`; exit 1. Una
  suite Py sin ningún `test_`, que imprime `0/0 pasaron.` con exit 0, es verde, como en el oráculo.
  · rojo visto: sí (VM-12a 15/22; etapa 9, 21-10-2026)

### Stderr

- **VP-E07** — Una suite Py verde que escribe una línea en stderr sale roja en el runner, con ese texto
  visible en su bloque, y el oráculo copiado sobre el mismo layout sale 1; una suite PS verde que lanza
  `cmd /c "echo x 1>&2"` da en el runner el mismo resultado (verde o rojo) que en el oráculo copiado.
  · rojo visto: sí (VM-11 9/15; etapa 9, 21-10-2026)

### Timeout

- **VP-E08** — Con un manifest sintético que pasa la validación de forma del runner (§10.3a) y declara
  `timeoutSeconds: 9` (D-T4, §1.3) para una suite (un valor que la política del manifest real no admite, §10.3b, y que
  acá no aplica: no hay parámetro ni modo de prueba, es un manifest como cualquier otro para el runner),
  una suite que duerme 30 s y tiene un hijo vivo con su padre vivo sale `INFRA TIMEOUT` en menos de 20 s;
  el hijo ya no existe; su archivo de eventos tiene un solo inicio; un proceso testigo lanzado por el test
  fuera del runner, con la misma imagen, sigue vivo; exit 1. La misma suite de 10 s con `timeoutSeconds:
  null` termina sola y sale verde. · rojo visto: sí (VM-19a 16/17, con `timeoutSeconds: 9`, etapa 9c,
  21-10-2026 19:58; VM-19b 14/16, VM-19c 12/16 y VM-19d 15/16, etapa 9, 21-10-2026, sobre la versión del
  escenario con `timeoutSeconds: 3`, anterior a D-T4)

### Aislamiento

- **VP-E09** — Cuatro suites que corren a la vez (N = 4) vuelcan `TEMP`, `TMP`, `TMPDIR`,
  `tempfile.gettempdir()` y `[IO.Path]::GetTempPath()`: los cinco valores son el mismo directorio dentro de
  cada suite, distintos entre suites y respecto de una segunda corrida, vacíos al empezar, fuera de la
  raíz; una marca `.avisado` que escribe una suite no la ve otra. Otra suite vuelca el entorno entero
  (ordenado, sin esas tres variables), el cwd, `sys.executable`, `PATH` y `shutil.which("bash")`, y da los
  mismos valores que el runner le pasó a su proceso, sin `PYTHONHASHSEED`, `PYTHONPYCACHEPREFIX` ni
  `PYTHONDONTWRITEBYTECODE` agregados. · rojo visto: sí (VM-07a 33/50, VM-07b 46/50, VM-08a 48/50, VM-08b
  44/50, VM-08c 47/50 y VM-08d 49/50; etapa 9, 21-10-2026)
- **VP-E10** — Sobre un layout sintético con repo git y `.gitignore` con `__pycache__/`, después de una
  corrida verde y de una cancelada, la huella (§5.1) es la misma que antes y los logs están fuera de la
  raíz; si una fixture crea un archivo no ignorado en la raíz durante la corrida, el runner sale 1 con
  `INFRA ARBOL_CAMBIADO` nombrando ese archivo. · rojo visto: sí (VM-09a 7/17 y VM-09b 13/17; etapa 9,
  21-10-2026)

### Clases y scheduling

- **VP-E11** — Con un manifest sintético que marca dos suites `serial`, dos del mismo carril y deja una sin
  entrada, en los intervalos registrados: durante cada `serial` y durante la desconocida no hay otra suite
  viva; las dos del carril nunca se solapan; la desconocida corre, sale `AVISO SUITE_NO_CLASIFICADA` y su
  resultado es el de sus aserciones. · rojo visto: sí (VM-05a 7/10, VM-05b 8/10 y VM-06a 8/10; etapa 9,
  21-10-2026; VM-06a solo se vio con la fixture `par_corto.py` a 9 s, cambio del builder en esa etapa)
- **VP-E12** — Con N = 2 y cuatro suites de encuentro (cada una espera ver dos marcas vivas y las sostiene
  2 s), el máximo de suites vivas a la vez es exactamente 2, y la corrida termina; con `-Workers 0` o
  `-Workers 5`, el runner sale 1 sin correr nada. · rojo visto: sí (VM-14a 13/14 y VM-14b 11/14; etapa 9,
  21-10-2026)

### Agregador

- **VP-E13** — El agregador del runner, invocado por la costura interna de §16.7 con registros de suite
  armados a mano (§15.1) y sin lanzar ningún worker (ningún proceso nuevo, nada en `TempBase`, ningún
  candado tomado, ningún stdout falsificado), sale ≠ 0 y nombra: una suite faltante, una sobrante, una
  repetida, una con `INFRA`, una con exit 0 y `N fallaron.`, una con grupo ajeno (`GRUPO_AJENO`) y una con
  `total` nulo (`ERROR_INTERNO`, sin tragarse la excepción); con el conjunto completo y coherente sale 0 y
  produce el reporte canónico; cargar el runner para alcanzar esa costura no ejecuta ninguna corrida.
  · rojo visto: sí (VM-01c 30/39 y VM-02c 38/39; etapa 9, 21-10-2026)

### Determinismo

- **VP-E14** — Con fixtures cuyas demoras invierten el orden de terminación respecto del canónico, con
  `a_b.py` y `ab.py` entre ellas, y con N = 1, 2 y 4, el reporte comparable de las seis corridas es
  idéntico byte a byte, sale en el orden canónico (el de `Sort-Object Name` y el de `sorted()` de Python) y
  ninguna línea suya contiene un pid, la ruta del temporal, el id de corrida ni una hora. · rojo visto: sí
  (VM-10a 14/18, VM-10b con pid 12/18 y con ruta 12/18; etapa 9, 21-10-2026)

### Equivalencia

- **VP-E15** — Sobre un layout sintético verde, con nombres de grupo con tildes, el oráculo copiado y el
  runner, los dos con `-Detallado`, dan al comparador `EQUIVALENTE`: mismo exit, mismas líneas de grupo en
  el mismo orden, mismos conteos y mismo multiconjunto de filas. · rojo visto: sí (VM-02a 16/21; etapa 9,
  21-10-2026)
- **VP-E16** — Con fallos inyectados (una fila roja PS, una Py y un `.py` que no carga), el oráculo copiado
  y el runner salen 1 los dos y el comparador da `EQUIVALENTE` con el mismo multiconjunto de filas
  fallidas (grupo, nombre). · rojo visto: sí (VM-02a con `fallaronPs = 0`, 10/14; etapa 9, 21-10-2026)
- **VP-E17** — El comparador, con pares adulterados a mano, sale `NO_EQUIVALENTE` y nombra el campo en cada
  uno de: total distinto en 1; un grupo de más; mismo número de fallos con otro nombre; exit distinto;
  grupos permutados; una línea `INFRA` en el runner; sale `NO_COMPARABLE` con huellas distintas y con una
  fila `MAL` sin prefijo de detalle conocido; sale `EQUIVALENTE` con el par idéntico. · rojo visto: sí (VM-18a
  solo totales 175/237, sin grupos 206/237, sin fallidas 223/237, y VM-18c 225/237; etapa 9, 21-10-2026)
- **VP-E18** — Deriva: una fixture cuyo conteo depende de cuántos archivos hay en una carpeta externa que el
  test cambia entre la corrida del oráculo y la del runner; con la misma huella del layout, el comparador
  sale `NO_EQUIVALENTE` nombrando esa suite y los dos conteos; el comparador no tiene ningún parámetro que
  acepte una diferencia. · rojo visto: sí (VM-18b 13/19; etapa 9, 21-10-2026)

### Cancelación y limpieza

- **VP-E19** — Al crear el archivo de `-CancelFile` mientras corren dos suites con hijos marcados con un
  token y quedan suites sin lanzar: no se lanza ninguna más; en menos de 30 s no queda vivo ningún proceso
  con el token; el temporal de cada suite se borró o figura en `LIMPIEZA_INCOMPLETA`; el candado inyectado
  queda libre; el exit es ≠ 0; la salida dice `CANCELADO`, lista terminadas, abortadas y sin lanzar, y no
  contiene la forma verde de la línea final. · rojo visto: sí (VM-16a 19/21, VM-16b 20/21, VM-16c 18/21 y
  VM-16d 19/21; etapa 9, 21-10-2026)
- **VP-E20** — Una suite que lanza A, A lanza B y A termina con `os._exit` (B huérfano), cortada por
  timeout: la suite sale `TIMEOUT`; si B sigue vivo y retiene un archivo del temporal, la salida trae
  `AVISO LIMPIEZA_INCOMPLETA` con esa ruta; el exit sigue la regla de §16.1; un proceso ajeno con la misma
  imagen que B sigue vivo; la huella no cambió. · rojo visto: sí (VM-19d 9/13; etapa 9, 21-10-2026). VM-19a
  no la ve: 13/13; la ve VP-E08
- **VP-E21** — (a) Con un proceso que tiene abierto un archivo del temporal de una suite verde, la salida
  trae `AVISO LIMPIEZA_INCOMPLETA <ruta>` y el exit es 0 (corrida funcional, §16.5; para el benchmark ese
  mismo par no se acepta, §22.1, VP-E25). (b) Un runner matado con `Stop-Process` deja su
  raíz y su `hpp-<id>.lock` (liberado por el SO); la corrida siguiente con el mismo `TempBase` toma ese
  `.lock`, borra la raíz y después borra el `.lock` (§19.4, §19.5 caso 3). (c) Una raíz cuyo `.lock`
  tiene tomado otro proceso vivo no se toca. (d) Un junction dentro de una raíz a barrer, que apunta a una
  carpeta testigo fuera del `TempBase`, deja la testigo intacta con su contenido. (e) Una corrida verde y
  limpia no deja en `TempBase` ni su raíz ni su `hpp-<id>.lock` (§19.5 caso 1); la corrida de (a), que
  conserva algo, deja la raíz **y** su `hpp-<id>.lock` liberado (§19.5 caso 2), y la corrida siguiente los
  barre juntos. · rojo visto: sí (VM-17a 25/30, VM-17b 19/20 y VM-17c 29/30; etapa 9, 21-10-2026; VM-17b
  se ve por una excepción que corta el resto de las filas, no por una fila: VX-25)

### Candado

- **VP-E22** — Dos runners lanzados a la vez contra el mismo `-LockPath`: exactamente uno corre sus suites;
  el otro sale 2 en menos de 10 s con `LOCK_OCUPADO`, sin ninguna línea de suite ni `pasaron.` y sin
  eventos en ninguna fixture. Con `-LockPath` apuntando a un directorio, sale 2 con `LOCK_ILEGIBLE`. Si se
  mata al dueño con `Stop-Process`, un runner nuevo toma el candado en menos de 10 s; `pesada.lock` sigue
  existiendo y un `pesada.json` viejo sobre un candado libre no se muestra como dueño. Con el dueño
  cancelado por la señal inyectable mientras uno de sus workers tarda en morir, un segundo runner ve
  `LOCK_OCUPADO` hasta que ese worker murió. El candado no frena a quien no lo toma: un
  `python correr.py -k` que el test lanza sobre el layout mientras el dueño corre termina normalmente, con
  su resumen (§19.2). · rojo visto: sí (VM-15a: carrera 19/28, ilegible y dueño matado 34/40; VM-15b que
  borra `pesada.lock` 26/28 y 37/40; VM-15b que decide por la existencia del archivo 32/38; VM-15c 9/11 en la
  cancelación con workers lentos; etapa 9, 21-10-2026)

### Compatibilidad del oráculo

- **VP-E23** — Sobre un layout sintético con suites PS y Py, verdes y rojas, el `Invoke-Tests.ps1` del repo
  y el de la versión de partida (`git show v0.34.0:tests/Invoke-Tests.ps1`), sin parámetros y con
  `-Detallado`, dan la misma salida estándar byte a byte y el mismo exit; con `-SoloCaso <x.py>` y con
  `-SoloCaso <y.ps1>` corre exactamente ese archivo (un solo archivo de eventos) y la primera línea es la
  de corrida parcial; con `-SoloCaso` de un archivo inexistente sale 1. El texto del oráculo sigue
  conteniendo `sys.executable` y `correr.py`. La identidad de la copia de la versión de partida se comprueba
  por blob id (`git rev-parse v0.34.0:tests/Invoke-Tests.ps1`) o con `git diff` con fin de línea normalizado,
  **nunca por sha256 de bytes crudos** contra el archivo del árbol: el blob es LF y el árbol CRLF
  (`.gitattributes:11`, VC-20). · rojo visto: sí (VM-20 72/76, y la regla B6 de §5.7 74/76; etapa 2,
  20-10-2026, en un clon fuera del repo)

### Manifest

- **VP-E24** — Un solo escenario, con la evidencia repartida entre dos suites (VC-34). **Parte A, política
  del manifest real, en `75_manifest_paralelo.py`, unidad, sin lanzar el runner ni workers:** sobre
  `tests/parallel-manifest.json` (política de §10.3b), cada `tests/casos/*.ps1` y `*.py` tiene exactamente una
  entrada (cobertura 1:1), no hay entradas duplicadas ni de archivos inexistentes, cada `class` y cada `lane`
  son válidas, ningún `reason` deja de ser string ni es vacío ni solo espacios en blanco (la calidad de su
  texto no la juzga el test: §10.2, revisión humana), cada `timeoutSeconds` cumple **exactamente**
  `max(ceil(3 × maxSeconds), 1200)` cuando `maxSeconds` no es `null` y es `null` cuando lo es, y ningún
  nombre `.py` es subcadena de otro; sobre manifests y listas sintéticas como datos de unidad, falta de una
  entrada, entrada duplicada, entrada de un archivo inexistente, `class` desconocida, `lane` sin nombre,
  `reason` vacío o solo espacios (`"   "`), `reason` que no es string, `timeoutSeconds` fuera de la fórmula y
  un par `caso_b.py` / `xcaso_b.py` ponen la suite en rojo nombrando el caso. **Parte B, forma en el
  runner, en `75_runner_paralelo.py`, con procesos reales sobre un layout sintético:** con un manifest que
  no es JSON, y con una entrada de forma inválida (`class` desconocida, `timeoutSeconds` que no es entero > 0,
  §10.3a), el runner sale 1 con `MANIFEST_INVALIDO` y no lanza ninguna suite (cero archivos de eventos);
  con un `timeoutSeconds` entero > 0 fuera de la fórmula productiva, corre (es la costura que usa VP-E08: la
  fórmula es del manifest real, no del runner). Sin `testMode`, flag oculto ni ruta especial.
  · rojo visto, parte A: sí (VM-06, tres mutaciones del chequeo de política: 42/46, 44/46 y 45/46; etapa 3,
  20-10-2026, en una copia fuera del repo) · rojo visto, parte B: sí (VM-06 en la forma del runner: sin
  `MANIFEST_INVALIDO` 12/36, rechazo de un `timeoutSeconds` fuera de la fórmula 32/36; etapa 9, 21-10-2026)

### Benchmark acceptance (aparte de la suite)

- **VP-E25** — Sobre el árbol real de 6.1, en una máquina que cumple las condiciones de §5.2,
  `tests\Measure-TestRuns.ps1 -Workers 2 -Umbral 0.75` (el valor que fijó la persona por §22.3, regla 2,
  D-T7) sale 0: las tres
  huellas son iguales, el comparador da `EQUIVALENTE` entre `.\tests\Invoke-Tests.ps1` y
  `.\tests\Invoke-Tests-Parallel.ps1 -Workers 2`, los dos sin `-Detallado` (D-T5: el punto 5 de §20.4 no se
  evalúa; los puntos 1–4 y 6, sí), **residuos atribuibles a la corrida paralela = 0** al terminar el protocolo
  (ninguna raíz `hpp-<id>` ni `s<nnn>` suya en `TempBase`, ningún `hpp-<id>.lock` de esa corrida, y ningún
  `AVISO LIMPIEZA_INCOMPLETA` en su salida: un aviso deja el par sin aceptar aunque el runner haya salido 0,
  §16.5, §22.1; `pesada.lock` y `pesada.json` no cuentan: son estables por diseño, §19.5), y el wall
  paralelo cumple el umbral. · rojo visto: sí (sondas rojas sobre layouts sintéticos contra la verde, que sale 0:
  raíz `hpp-*` plantada, archivo retenido con su aviso, huella distinta y `-Umbral 0.01` salen 1, etapa 8,
  21-10-2026; VM-18 del lado del medidor, tres mutaciones del conteo de residuos que hacen salir 0 a sondas que
  con el medidor sano salen 1, etapa 9, 21-10-2026; modo de reuso, siete sondas que salen 2, etapa 8b,
  21-10-2026; medidor con `^AVISO`, un aviso real sigue saliendo 1, preparación del cierre, 22-10-2026). Sobre el
  árbol real: el par de cierre (22-10-2026) salió 1 con `-Umbral 0.70` solo por el umbral y cumple todas las
  demás condiciones; con `-Umbral 0.75` no se corrió (D-T7)

### Cómo se verifica

| Escenarios | Cómo |
|---|---|
| VP-E01 a VP-E23, y VP-E24 parte B | `75_runner_paralelo.py`, procesos reales sobre layouts sintéticos; corre en el oráculo y en el runner |
| VP-E24 parte A | `75_manifest_paralelo.py`, unidad, sin procesos: nunca lanza el runner ni workers. Es un solo escenario con dos partes; su `rojo visto` se registra por parte (VC-34) |
| VP-E25 | `tests/Measure-TestRuns.ps1`, que nombra VP-E25 en su ayuda; **fuera de la suite** (dura un par de serial + paralelo: con WU03-a, unos 50 a 60 minutos de serial más el paralelo). Lo corre el refutador y cita lo que imprimió: es un test que nombra el escenario, corrido y pasado (`harness-spec-refuter.md:68`), no una lectura |

**El disparo real de Ctrl-C no tiene escenario propio.** VP-E19 prueba el camino de salida con la señal
inyectable, que es el mismo `finally`; que PowerShell 5.1 llegue a ese `finally` ante un Ctrl-C es
comportamiento de plataforma. Un smoke manual con Ctrl-C real se registra en `benchmark-<fecha>.md` como
evidencia no vinculante, y el hueco queda en §24, R7. No se marca `lectura`: el sujeto no es un modelo.

📌 Los intervalos «en menos de N s» llevan márgenes holgados para correr bajo carga; ningún escenario se
reintenta en silencio.

---

## 27. Mutations

Cada una se aplica a una **copia** fuera del repo, una vez, y su resultado se registra en la marca
`rojo visto` del escenario (ADR-0006). La columna «Visto en rojo» la agregó la pasada post-WU03-b con lo que
registró la construcción (etapas 2, 3, 8, 9 y 9c; filas verdes sobre el total del escenario con la mutación).

| Id | Mutación | La ven en rojo | Visto en rojo (construcción) |
|---|---|---|---|
| VM-01 | El scheduler pierde una suite, o la lanza dos veces | E01, E13 | E01 (pierde 7/15, duplica 6/15), E13 (30/39) |
| VM-02 | El agregador suma mal, descarta la última fila de cada suite, o se traga una excepción y sale 0 | E01, E13, E15, E16 | E01 (14/15, 14/15), E13 (excepción 38/39), E15 (16/21), E16 (`fallaronPs = 0`, 10/14: E02 y E13 no la ven) |
| VM-03 | Una suite roja o un worker muerto dan exit 0 si todos los workers terminaron | E02, E05 | E02 (13/14), E05 (19/20) |
| VM-04 | El resumen se toma del primer match y no de la última línea, o no se cruza con los grupos | E04 | E04 (18/24, 16/24) |
| VM-05 | Una `serial` entra al pool, o el carril se ignora | E11 | E11 (7/10, 8/10) |
| VM-06 | Una suite sin entrada corre como `parallel`, o el chequeo del manifest acepta un archivo sin entrada | E11, E24 | E11 (8/10, con `par_corto.py` a 9 s; con 1 s no se veía), E24 parte A (42/46, 44/46, 45/46), E24 parte B (12/36, 32/36) |
| VM-07 | Dos suites comparten temporal, o solo se fija `TEMP` | E09 | E09 (33/50, 46/50) |
| VM-08 | El worker recibe `PYTHONHASHSEED`, `PYTHONPYCACHEPREFIX` o un `PATH` reordenado, o corre en otro cwd | E09 | E09 (48/50, 44/50, 47/50, 49/50) |
| VM-09 | Los logs se escriben bajo la raíz del repo, o la huella final no se compara | E10 | E10 (7/17, 13/17) |
| VM-10 | El reporte sale en orden de llegada, o incluye el pid o la ruta del temporal | E14 | E14 (14/18, 12/18, 12/18) |
| VM-11 | El worker Py llama a `correr.py -k` directo y manda su stderr a un archivo sin juzgarlo | E07 | E07 (9/15) |
| VM-12 | Un resumen ausente cuenta `0/0` verde, o la fila de carga se pierde | E03, E06, E16 | E03 (14/15, 13/15), E06 (15/22); contra E16 no se aplicó |
| VM-13 | La muerte de un worker se omite, o la suite se relanza | E05 | E05 (17/20, 17/20) |
| VM-14 | El límite N no se aplica, o se ignora (todo de a una) | E12 | E12 (13/14, 11/14) |
| VM-15 | El candado se ignora, se decide por la existencia del archivo (o se borra el `.lock`), o se suelta antes del último worker | E22 | E22 (las cuatro variantes; ver la marca del escenario) |
| VM-16 | La cancelación deja un hijo vivo, no limpia, no suelta el candado, o sale 0 | E19 | E19 (19/21, 20/21, 18/21, 19/21). «No suelta el candado» **no es observable** por un test: el SO libera el candado cuando el runner sale y los handles no se heredan; lo que sí se ve es soltarlo antes del último worker (VM-15c) |
| VM-17 | La limpieza se traga un error, barre una raíz con su `.lock` tomado, o sigue un junction | E21 | E21 (25/30, 19/20 por excepción, 29/30) |
| VM-18 | El comparador mira solo totales, acepta una diferencia, o ignora la huella; o el medidor acepta un par con una raíz `hpp-*` residual o con `AVISO LIMPIEZA_INCOMPLETA` | E17, E18, E25 | E17 (175, 206, 223 y 225 de 237), E18 (13/19), E25 (lado medidor: tres mutaciones, la sonda roja pasa a salir 0) |
| VM-19 | El timeout mata solo al worker y no a su árbol, relanza la suite, corta con `timeoutSeconds: null`, o mata por nombre de imagen | E08 (las cuatro variantes), E20 (solo por nombre de imagen) | E08 (solo al worker 16/17 en la 9c, con `timeoutSeconds: 9`; relanza 14/16, `null` 12/16, imagen 15/16 en la 9, con `timeoutSeconds: 3`), E20 (imagen 9/13; solo al worker: 13/13, no la ve) |
| VM-20 | `-SoloCaso` cambia la salida por defecto (la línea de corrida parcial siempre, o el motor de Python salteado sin el parámetro) | E23 | E23 (72/76; y la regla B6, 74/76) |

Lo que ninguna mutación sintética alcanza: una fuga de estado de una suite real que en serial da rojo y
por proceso verde. La ve solo la paridad de VP-E25 sobre el árbol real.

---

## 28. Migration

| Fase | Entrada | Evidencia exigida | Qué cambia |
|---|---|---|---|
| **A** (6.1): el runner existe y no reemplaza nada | Task 6 cerrada (0.34.0, hecho); baseline fijada (`d86b285`, hecho); WU03-a hecha (hecho, §5.6); spec aprobada por una persona; ADR-0018 aceptado; M1 hecha | VP-E01 a VP-E24 con test, `rojo visto` registrado; refutación de alguien que no construyó; VP-E25 con al menos un par N = 2, equivalente y sin residuos atribuibles (§22.1); **6.1 cierra con `.\tests\Invoke-Tests.ps1` en verde** | Archivos nuevos en `tests/`; el oráculo solo con `-SoloCaso` |
| **B**: Task 7 lo usa como fast gate | A cerrada sin `contradicho` ni `sin sustento`; registro de equivalencia de A | Cada corrida del runner con su huella; cada cierre de etapa con el oráculo; una discrepancia sin explicar ⇒ se deja de usar y se abre un ítem en FH | La spec de Task 7 lo declara solo para feedback del builder y regresión focal |
| **C**: Task 8 lo suma a la refutación | B sin discrepancias | La regla del refutador (VX-14): explora con el runner; un `sostenido` que cierra cita el oráculo o `correr.py -k` | Nota en `harness-spec-refuter.md` solo si VX-14 se decide |
| **D**: evaluar promoción (fuera de 6.1) | Pares suficientes sobre ≥ 2 Tasks y árboles; deriva resuelta o contemplada | ADR nuevo que reemplace al de A, refutación, aprobación de la persona | `CLAUDE.md` §«The gate», refutador, staff, `close-a-version`; `install.ps1` no cambia |

**Las migraciones de archivos de 6.1:** M1, la enmienda de `harness-backend-engineer.md:62-73`, en inglés
(ADR-0011): «One command closes: `.\tests\Invoke-Tests.ps1`. `tests/Invoke-Tests-Parallel.ps1` is an
accelerator that runs the same case files through the same runner, one file per process; it never closes a
change, a verdict or a release, and it reports in the same shapes.» M2, `-SoloCaso` en el oráculo, con la regla
de §21. Nada más se migra: no hay Tasks previas cuyo contrato cambie.

**Regla operativa para las fases B y C (Task 7 y Task 8), sin tocar el oráculo.** El candado de §19 solo
coordina runners entre sí (§19.2). Lo demás lo cubre una regla del workflow, que quien orquesta aplica y
que no es un candado impuesto a `Invoke-Tests.ps1`: **mientras se ejecuta un trabajo pesado de cierre, el
orquestador no lanza otro trabajo pesado que compita por CPU, RAM o disco.** Son trabajos pesados, como
mínimo: `.\tests\Invoke-Tests.ps1` completo; `tests\Invoke-Tests-Parallel.ps1`; un lote grande de
mutaciones (decenas de `correr.py -k` sobre una copia); el benchmark de WU03 y `Measure-TestRuns.ps1`. Lo
focal (`correr.py -k <suite>`, `-SoloCaso`) no cuenta. Si dos trabajos pesados tienen que correr, corren
uno después del otro, y el que cierra (el oráculo) corre solo. Esta regla se cita en la spec de Task 7 y
en la de Task 8 junto con el uso del runner; la coordinación técnica más amplia sigue siendo deuda
(VX-07).

---

## 29. Construction order

0. **Precondición.** Hecho: Task 6 release-closed (0.34.0); versión de partida fijada (`d86b285`, `v0.34.0`,
   §2.1); §2.2 re-verificada; WU03-a corrida (20-10-2026) y §5.6, `maxSeconds` y `timeoutSeconds` (§6, §10.2)
   llenos; SPEC REVIEW independiente aprobado y aprobación humana confirmada el 20-10-2026 (encabezado, §1.4).
   **Hecho todo.**
1. **ADR** `docs/adr/0018-dos-corredores-un-oraculo.md` (fija VD-01, que el runner nunca cierra y que la
   promoción pide un ADR que lo reemplace; su texto no nombra «GraphRun», §8.3) y **M1**. Antes del código: la
   regla que se enmienda prohíbe lo que sigue.
2. **M2** en `tests/Invoke-Tests.ps1` (`-SoloCaso`, con la regla de §21) y VP-E23 en `75_runner_paralelo.py`.
   Evidencia **focal**, sin suite completa: VP-E23 (sin `-SoloCaso`, salida estándar idéntica byte a byte a la
   de `v0.34.0` y mismo exit; con `-SoloCaso`, exactamente un archivo; `sys.executable` y `correr.py`
   conservados); las guardas focales que protegen el texto y el contrato del oráculo:
   `66_integrity_cleanup.py` (E-22, `66:471-476`), `72_motor_de_ejecucion.py` (ME-E51, `72:2330-2335`);
   las que barren `tests/` y el agente enmendado en el paso 1: `63_harness_unico.py` (E-57 y E-61,
   `63:622-626, 678-697`), `71_plan_2_1.py` (E-16, `71:496-503`), `00-encoding-fuentes.ps1` (BOM); y toda
   otra guarda que §8.3 o §21 nombren para M2. Se corren con `python tests\correr.py -k <archivo>` y, para
   los `.ps1`, con el propio `-SoloCaso`. **No se corre `Invoke-Tests.ps1` completo en este paso.**
3. **Manifest** con las 99 entradas de §6, con sus tiempos, y **`75_manifest_paralelo.py`** (VP-E24, parte
   A: política, unidad, sin procesos). Evidencia focal: `python tests\correr.py -k 75_manifest_paralelo.py`
   sobre el manifest real, más las guardas de `tests/` del paso 2 (E-61, E-16, E-28 sin BOM en el `.py`) por
   el archivo nuevo. Sin suite completa.
4. **Runner, núcleo:** argumentos, validación de forma del manifest (§10.3a), enumeración (§20.1),
   scheduler, workers con su temporal, agregación, reporte. VP-E01 a VP-E07, VP-E09, VP-E11 a VP-E14, y
   VP-E24 parte B (`75_runner_paralelo.py`: manifest no JSON o de forma inválida ⇒ `MANIFEST_INVALIDO`, exit 1,
   cero suites; `timeoutSeconds` entero fuera de la fórmula ⇒ corre).
5. **Runner, bordes:** huella, timeout y corte, cancelación, limpieza, barrido. VP-E08, VP-E10, VP-E19 a
   VP-E21.
6. **Candado.** VP-E22.
7. **Comparador.** VP-E15 a VP-E18.
8. **Medidor**, con las reglas de §5.7. VP-E25 sobre un layout sintético primero, para ver su rojo (VM-18).
9. **Rojo visto:** VM-01 a VM-20 sobre copias; se registra cada marca. **Pasos 1 a 9: solo feedback focal**
   (`correr.py -k`, `-SoloCaso`, los escenarios de cada paso y, desde el paso 4, el runner sobre el árbol real
   como acelerador que no cierra nada, VD-01).
10. **La única suite completa oficial de la construcción**, con el oráculo, sobre el árbol final previo a
    WU03-b: verde (§8.5, §30). Es **la pata serial del primer par N = 2 de WU03-b** (D-T3, §1.3), que es el
    par 1b (D-T6): `.\tests\Invoke-Tests.ps1` lanzado por `Measure-TestRuns.ps1 -Workers 2`, capturado y con sus
    condiciones registradas; el par 1b la corrió con `-Detallado`, que no cambia el veredicto, y salió 0 con
    48841/48841. Desde D-T5 los pares corren las dos patas sin `-Detallado`. No hay otra suite completa
    separada. **Runner** sobre el árbol real: verde. **WU03-b**: se copia a
    `benchmark-<fecha>.md` la evidencia de WU03-a que hoy vive en `C:\dev\_respaldos\task6.1\wu03a\` (§5.6); el
    primer par N = 2 (el 1b) actualiza `maxSeconds`/`timeoutSeconds` (§10.2) y fijó el umbral en 70 % (§22.3,
    D-T6); el par N = 3 no se corre en 6.1: queda opcional, a pedido (D-T1); toda suite con rojo en paralelo y
    verde en serial pasa a una clase más estricta (§10.5); el par que cierra corre sobre la huella final, con
    `-Umbral 0.70`, no realimenta el manifest (§5.7 B4) y **no reutiliza** la pata serial del primer par: cambia
    el medidor, así que D-T2 no aplica (D-T6). **Hecho** (§5.6): el par 1b actualizó el manifest (80 `maxSeconds`
    subieron, 17 quedaron iguales, las filas 98-99 se llenaron con 1,1 y 299,1 s; los `timeoutSeconds` solo
    cambiaron en 98-99, de `null` a 1200; t73 sigue en 2187); en los pares 1b y de cierre ninguna suite dio rojo
    en paralelo, así que ninguna cambió de clase. En el par 1, `75_runner_paralelo.py` dio rojo en paralelo y
    verde dentro de la serial, por su guarda de `MAX_PATH` con el `TEMP` largo del medidor (§5.2); no se aplicó
    §10.5 porque la pata serial de ese par salió roja (`971/972`, §4) y porque el `s<nnn>` que alarga la ruta es
    el mismo en cualquier clase, así que un cambio de clase no lo arregla (VX-26; queda para el refutador). El
    par de cierre salió `EQUIVALENTE`, sin residuos, con relación
    0,7089: el medidor dio 1 solo por el 0,70, y la persona fijó 0,75 (D-T7).
11. **Pendientes**: cada VX con `note-a-pending`.
12. **Refutación** independiente (`harness-spec-refuter`), escrita por otro en `verificacion.md`.
13. **Cierre** con `close-a-version`; el ítem de FH:2260-2283 sale a la nota de versión.

---

## 30. Gate

6.1 cierra cuando, todo a la vez:

1. `.\tests\Invoke-Tests.ps1` sale 0 sobre el árbol final;
2. el veredicto del refutador sobre VP-E01 a VP-E25 no tiene `contradicho` ni `sin sustento`, con los
   `rojo visto` informados;
3. `benchmark-<fecha>.md` registra WU03-a y al menos un par N = 2 de WU03-b, equivalente, sobre la huella
   final, **sin residuos atribuibles a la corrida paralela** (§22.1), con la tabla de §35 completa y el
   umbral decidido por §22.3;
4. `git status` y la huella después de las corridas son los de antes: el runner no dejó nada en el repo;
5. el ADR está aceptado y M1 aplicada;
6. los pendientes están registrados y el ítem de FH salió a la nota de versión.

**Cómo se sostienen 1 y 3 en la construcción** (D-T3, D-T5, D-T6, §1.3): el punto 1
(«`.\tests\Invoke-Tests.ps1` sale 0 sobre el árbol final») lo sostiene **la pata serial del par que cierra**,
que es exactamente el comando de la compuerta sobre la huella final (D-T5). La pata serial del par 1b fue la
única suite completa oficial de los pasos 1–10 de la construcción (D-T3, D-T6), no la del árbol final. Las dos
se registran en `benchmark-<fecha>.md`. El punto 3 lo sostiene el par que cierra. Nada de esto limita lo que
corra el refutador.

**La huella del par que cierra ya no es la del árbol** (pasada post-WU03-b, sin decisión nueva). El par de
cierre corrió sobre `94999FD9…`. Después de él cambian, por el propio §29, archivos que entran a la huella
(§5.1): esta spec y `benchmark-2026-10-22.md` (paso 10), FH e I (paso 11) y, al cerrar, lo de `close-a-version`.
Ninguno está bajo `tests/`, y según el grep de §1.3 ninguna suite lee su contenido; pero t63h y t64 listan las
rutas no versionadas (§1.3, tabla de lectores), y eso no se re-verificó para una ruta nueva. Lo que se puede
afirmar es esto: el par de cierre sostiene los puntos 1 y 3 sobre la huella `94999FD9…`, y quien refuta, al
correr VP-E25 sobre el árbol que tenga (§26), produce un par nuevo, con su pata serial, sobre esa huella. Si
eso alcanza para el punto 1 o hace falta otra cosa, lo decide la persona al cerrar, no esta pasada.

**El runner en verde no cierra nada**: ni este cambio ni ninguno (VD-01).

---

## 31. Las decisiones, y por qué

Ninguna decisión cambió con la baseline real ni con WU03-a (§2.2). Donde hay números nuevos, son evidencia
del «por qué», no una decisión distinta.

### VD-01 — Dos corredores, un oráculo

El oráculo es la compuerta y lo único que cierra un cambio, un veredicto o un release. El runner es un
acelerador. Se escribe el ADR-0018 y se enmienda `harness-backend-engineer.md:62-73` (M1) antes de
construir. Es lo que pide el brief (`Invoke-Tests.ps1` oráculo, el paralelo acelerador, la promoción
afuera), y respeta las dos cosas que protege la regla «Do not add a third way to run the tests, and do not
let the two report in different shapes» (`harness-backend-engineer.md:70-71`): un solo comando de cierre y
una sola forma de reporte. El release 0.34.0 no la contradice: ADR-0017 no habla de la compuerta ni del runner
(guardián).

- **Descartada:** el runner como compuerta. Es la fase D; sin pares acumulados, un verde que nadie
  contrastó cerraría cambios.
- **Descartada:** construir sin enmendar. Viola por omisión un contrato escrito.
- **Descartada:** el paralelo como modo del oráculo (`Invoke-Tests.ps1 -Paralelo`). Mete el acelerador en
  el camino de la compuerta y vuelve más riesgoso cada cambio del runner.

### VD-02 — El dueño es `harness-backend-engineer`

`CLAUDE.md:62` le da `tests/` y su agente dice «`tests/` — both runners» (`harness-backend-engineer.md:20`).
El ítem de FH que lo asigna al staff (FH:2278-2279) es una nota de pendiente, no un contrato, y la nota 0.34.0
solo lo repite (`docs/versiones/0.34.0.md:221-223`). La regla 2 del staff, «Not one character of what a person
sees» (`harness-staff-engineer.md:22-25`), le impide producir una salida nueva. Lo que el contrato le deja al
staff —«making working code faster — the staff engineer's» (`harness-backend-engineer.md:21`); «Performance,
size, simplicity — behaviour frozen» (`CLAUDE.md:63`)— es acelerar código que ya funciona sin cambiar lo que se
ve; el runner es una herramienta nueva con salidas nuevas (`INFRA`, `LOCK_OCUPADO`, exit 2), y esa parte del
contrato le toca después, sobre el runner ya hecho (§8.4).

- **Descartada:** el staff engineer. Su contrato le prohíbe el cambio que la Task pide.
- **Descartada:** dueño compartido. «Two engineers editing the same contract from opposite ends»
  (`harness-backend-engineer.md:24-25`).

### VD-03 — Un proceso por suite, y el proceso es el oráculo

Cada worker es `Invoke-Tests.ps1 -SoloCaso <archivo>`, para los dos motores. El preludio, los cinco verbos,
el `try/catch` de carga, la resolución de Python, el `2>&1` bajo `Stop` y el cálculo de `$pasoTodo` son los
del oráculo **por construcción**: la equivalencia no depende de una reimplementación.

- **Descartada:** worker Py directo, `python correr.py -k`. Más rápido (sin un `powershell.exe` por suite),
  pero obliga a reimplementar en el runner la semántica del stderr (`Invoke-Tests.ps1:20, 256`;
  WU05:R3) y la regla de E-22 (`66_integrity_cleanup.py:471-476`): dos implementaciones de la misma regla
  divergen (`harness-staff-engineer.md:45-48`). La sobrecarga se mide (R18).
- **Descartada:** extraer el preludio a un helper compartido (WU07:opción B). Cambia la estructura del
  oráculo y mueve `$PSScriptRoot` de `Get-Payload`/`Get-Fixture` (`Invoke-Tests.ps1:147, 154`).
- **Descartada:** copiar el preludio (la PoC, WU07:opción C). Duplica, y la copia ya diverge (WU07:R2): la de
  WU03-a, por ejemplo, arma la fila de carga con `$nombre`, que 65-inst y 66-inst pisan (§7, VX-19).
- **Descartada:** hilos o runspaces. t68 E-06 identifica sus copias por el proceso
  (`68-isolated-factory.ps1:23-33`); se mezclarían `sys.modules`, `os.environ` y la sesión de PowerShell.

### VD-04 — `-SoloCaso`, opt-in, y nada más en el oráculo

El único cambio al oráculo es el parámetro de §21, con la salida por defecto idéntica (VP-E23). `correr.py`
no cambia: t74, además de 65 y 72, lo carga como módulo (`74:3737, 4319`). Se descarta `-Caso` por el choque
con `$caso` (`Invoke-Tests.ps1:174`).

- **Descartada:** sin tocar el oráculo. Obliga a VD-03 descartada (copia o reimplementación).
- **Descartada:** M3, JSON en `correr.py`. Ver VD-09.
- **Descartada:** el candado en el oráculo. Le agrega un exit nuevo al contrato 0/1 (WU10:C4).

### VD-05 — El temporal por suite; todo lo demás, heredado

`TEMP=TMP=TMPDIR=<TempBase>\hpp-<id>\s<nnn>`, nuevo por suite. Resuelve los tres choques demostrados de
temporal (WU04:filas 1-3) y deja a cada suite en el estado que `Clear-MarcasHarness` existe para garantizar
(`Invoke-Tests.ps1:133-135`). Por suite y no por worker: un worker reusado pasaría restos de una suite a la
siguiente, y WU03-a muestra que hay muchos (760 entradas por corrida, §5.6).

- **Descartada:** `PYTHONPYCACHEPREFIX` por worker (WU04:opción D). Rompe la precondición de t18i E-33,
  que compila el bin **en el árbol de origen** y afirma que hay `.pyc` ahí
  (`18-integraciones-instalador.ps1:35-48`), y aleja el entorno del oráculo (VC-08).
- **Descartada:** reordenar el `PATH` para que gane Git Bash. Cambia lo que encuentra `which`: el runner
  daría verde donde el oráculo da rojo, o al revés (VC-04). Git Bash al frente es una precondición de quien
  lanza, no algo que el runner fija (§5.2, VC-26).
- **Descartada:** copia del árbol por worker. Las suites corren git sobre `RAIZ`: otro árbol, otra corrida.

### VD-06 — Clases explícitas: `parallel`, `lane`, `serial`; desconocida ⇒ `serial`

§11. La clase está escrita en el manifest con su evidencia; nada se infiere del nombre. Desconocida corre
`serial`, la condición del oráculo; el rojo por la entrada faltante lo pone la suite en los dos corredores.
El runner valida solo la **forma** del manifest (§10.3a, fail-closed si es ilegible); la **política** del
manifest real (cobertura, fórmula de `timeoutSeconds`, `reason`, subcadenas) la valida la suite (§10.3b):
la lógica normativa no se duplica dentro del runner.

- **Descartada:** NORMAL / ISOLATED / HEAVY / SERIAL. ISOLATED es de todas; HEAVY con «una a la vez» es una
  cola serial que pasa el target (VC-09).
- **Descartada:** desconocida ⇒ rojo en el runner. Daría rojo donde el oráculo da verde: un falso rojo
  atribuible al runner.
- **Descartada:** desconocida ⇒ `parallel`. Fail-open.
- **Descartada:** inferir por nombre (`*-instalador.ps1`). El nombre no es evidencia; 68 no corre el
  instalador y 69 sí.

### VD-07 — El límite cuenta suites vivas; N = 2

§11. El runner solo puede admitir o retener suites: no puede frenar lo que una suite lanza adentro (ME-E18
lanza diez motores por diseño, `72:575-580`). Contar nietos haría depender la admisión de ruido y no se
puede probar de forma determinista. El riesgo de procesos por suite lo cubren los carriles. `-Workers` de 1
a 4: 4 es lo más alto que prueba VP-E14; más, sin medición, se rechaza. Con WU03-a, N = 2 da una cota de
25,9 min (§13.3): deja el stretch de 25 min fuera de alcance (VC-28), y aun así sigue siendo el valor por
defecto: N = 3 tiene RAM paralela sin medir, menos margen de limpieza (R24) y más carga sobre las carreras de
t72 (R25); WU03-b lo evalúa y la persona decide con números.

- **Descartada:** `cpu_count` (brief).
- **Descartada:** contar procesos vivos con nietos (WU02:INV-6). Ver arriba.
- **Descartada:** N lugares de RAM (WU10:C-B). La RAM por corrida paralela no está medida: WU03-b registró solo la
  RAM libre de la máquina, sin muestreo por proceso (§5.2, VX-28).
- **Descartada:** subir el valor por defecto a 3 ahora, para alcanzar el stretch. Sin un par medido es elegir
  por comodidad.

### VD-08 — Más largas primero, carriles exclusivos, `serial` al final

§13. El carril `motor` arranca primero y convive con el pool.

- **Descartada:** cola serial al final con 72, 73, 63-hu, 19, t63c, 70, 55 y sus cargadores (WU04:opción C,
  FH:2277-2278): solo con las tres primeras, ≈ 35,7 min ESTIMATED con N = 2 y f = 1 (§13.3).
- **Descartada:** HEAVY limitando el pool a una pesada. Misma cola: 36,4 min de trabajo en serie (§11).
- **Descartada:** `serial` al principio. Retrasa el arranque de t73.

### VD-09 — El resultado sale del texto, anclado a la última línea

§15. El texto ya es el contrato que el oráculo parsea (`Invoke-Tests.ps1:262`), no toca `correr.py` ni sus
importadores (65, 72, 74: WU07; `74:3737, 4319`), y con el worker siendo el oráculo, la línea final ya trae la
decisión de pasa/falla. El ancla a la última línea y el cruce con los grupos cierran el engaño del primer match
(VP-E04).

- **Descartada:** JSON con sentinel (WU07:b). Segundo canal, M3 en `correr.py`, más código que probar; lo
  que gana (filas exactas) lo da `-Detallado` para la comparación.

### VD-10 — 0 verde, 1 rojo, 2 no corrió

§16, §17. El 2 es solo de admisión (candado ocupado o ilegible): «no corrió» no es ni verde ni rojo de una
suite (WU10:I4). Los demás errores previos (manifest, argumentos) son 1, como las precondiciones del oráculo
(`Invoke-Tests.ps1:169-172, 250-254`). Limpieza incompleta avisa y no cambia el exit en una corrida
funcional (§16.5); el benchmark y la adopción exigen cero residuos atribuibles (§22.1, VP-E25): las dos
cosas conviven porque el exit es del runner y la aceptación es del medidor. Un árbol que cambió durante
la corrida es rojo: el resultado no corresponde a ningún árbol.

- **Descartada:** exit 1 con un marcador para «ocupado» (WU08:C4-b). Un agente que reintenta ante el 1 no
  distingue «otra corrida» de «rojo».
- **Descartada:** limpieza incompleta en rojo (WU13:D-T2 rama b). t72 deja Hosts vivos a propósito.
- **Descartada:** fila sintética por error de infraestructura (WU07:D4). Cambia el total frente al oráculo.

### VD-11 — Timeout con medición; corte por árbol; sin Job Object; sin reintento

`timeoutSeconds = max(ceil(3 × maxSeconds), 1200)`. El **3** cubre la peor dispersión medida de la suite
completa: 1:40:54 contra 47 min, 2,15× (§2.3), y 44 a 74 min entre corridas (1,68×, FH:2262-2264); la de
WU03-a fue 1,20× (§5.6). El **1200** es dos veces la espera interna más larga de una suite (`timeout=600`,
`64_modelo_de_dominio.py:235`): el runner nunca le gana al diagnóstico propio de una suite. Con WU03-a, solo t73
queda por encima del piso (2187 s = 3,0× su duración sola); contra la MEASURED-previa de t73 no cubriría la
peor dispersión (R23, VC-24), y por eso la previa no alimenta el manifest (§5.7 B1) y el primer par lo
actualiza (§10.2). Sin `maxSeconds`, no se mata. El corte es `taskkill /T /F` con el handle abierto: el patrón
del repo (`repositorio.py:201-215`; `68-isolated-factory.ps1:113`, discoverer). La fórmula es política del manifest
**real** y la verifica VP-E24 (§10.3b); el runner usa el entero de `timeoutSeconds` que recibe, así que un
manifest sintético puede traer uno chico para probar el corte (VP-E08) sin ningún modo de prueba.

- **Descartada:** un número fijo global. Arbitrario, y con t73 en 728,8 s MEASURED-BASELINE cualquier número
  chico la mata.
- **Descartada:** Job Object con `KILL_ON_JOB_CLOSE` (WU04:opción b). ME lo difirió «cuando un caso real lo
  pida» (ME:1697) y lo repite para el Host (ME:1775); pide `Add-Type` con P/Invoke en PS 5.1, deja una
  carrera entre lanzar y asignar, y su único beneficio son los nietos huérfanos, que existen igual en serial
  (t72 los deja a propósito, `72:299-305`). VX-08 lo deja anotado.
- **Descartada:** reintentar. FH:1019-1021.

### VD-12 — Cancelación por un solo `finally`

§18. Lo que se prueba con la señal inyectable es el mismo código que corre con Ctrl-C.

- **Descartada:** probar el Ctrl-C real con `GenerateConsoleCtrlEvent` (WU13:opción 2) como escenario. Pide
  sesión de escritorio y sondas no hechas (WU13:P-1 a P-3); queda como smoke manual no vinculante.
- **Descartada:** marcar el Ctrl-C real `lectura`. ADR-0009: el sujeto no es un modelo.

### VD-13 — El candado del SO, para admitir y para barrer

§19. Un solo mecanismo, el precedente del repo, en dos usos: `pesada.lock` para que corra un runner a la
vez (**solo entre runners**: lo que no lo toma no queda excluido, §19.2; el resto es la regla operativa de
§28), y `hpp-<id>.lock` para saber si vive el dueño de una raíz a barrer. El medidor no lo toma en la pata
serial (analista:D7): tomarlo y soltarlo antes de lanzar el runner sería la forma de N1.

- **Descartada:** pid + arranque para el barrido (WU05:INV-07, WU04). Es la forma de N1 que GE §14.1 y
  `registro.py:35-36` cerraron; «dueño ilegible = vivo» deja raíces para siempre. Sigue vigente **solo** en
  `isolated-factory.ps1`, que no se toca.
- **Descartada:** mutex con nombre (WU10:L4), `FileShare.None` (L2), `mkdir` + pid (L5).
- **Descartada:** N lugares (WU10:C-B). RAM sin medir.
- **Descartada:** espera por defecto. Esconde la contención; falla rápido y lo dice.

### VD-14 — Equivalencia estricta, suite por suite, con huella

§20.4, §5.1. Es el objetivo duro del brief (diferencias 0) y no se relaja porque simplifique. **Única excepción
acotada:** D-T2 (§1.3, §5.4), que deja reutilizar la pata serial del primer par cuando lo único que cambió es
`tests/parallel-manifest.json`, re-verificando las suites que lo leen; fuera de eso, nada de esta decisión cambia.

- **Descartada:** tolerancia para 30 y 33 (WU05:D2). Esconde exactamente la clase de falla que FH:1023-1026
  pide encontrar.
- **Descartada:** fijar la fuente de la deriva en los dos (WU05:D3). Toca el oráculo y tapa no determinismo.
- **Descartada:** arreglar la deriva antes (WU05:D1). Es trabajo de las suites, afuera (VX-10); además, entre
  el release 0.33.0 y F1 no reapareció (del orquestador), y en WU03-a los conteos de 30 y 33 coinciden entre
  las dos corridas y las solas (§5.6).
- **Descartada:** tolerar un caso con falla serial documentada (t72 E34). El par es `NO_EQUIVALENTE` igual; lo
  que se decide es la clase, no la equivalencia (§10.5, VC-30).

### VD-15 — El benchmark es un escenario con test, fuera de la suite; los tests de 6.1 son dos casos `75_*`

VP-E25 lo sostiene `tests/Measure-TestRuns.ps1`, que nombra el escenario y que el refutador corre: es la
definición de `sostenido` (`harness-spec-refuter.md:68`), sin ADR nuevo. No entra a la suite porque dura un
par de serial + paralelo. Los tests de comportamiento van en `tests/casos/`: `75_manifest_paralelo.py`
(unidad, `parallel`) y `75_runner_paralelo.py` (procesos, carril `ventana`), en Python porque el control de
procesos es más simple y los dos motores lo leen igual. VP-E24 reparte su evidencia entre las dos sin
dejar de ser un escenario: la política del manifest real en la primera (parte A), la forma en el runner en
la segunda (parte B), porque esa última lanza procesos y la primera no (VC-34).

- **Descartada:** criterio de aceptación fuera de los E-nn (WU13:D-T4 opción 1). Quedaría sin veredicto.
- **Descartada:** marca nueva «medición registrada» (opción 2). Pide un ADR para algo que un test resuelve.
- **Descartada:** un solo archivo de test. El chequeo del manifest es instantáneo y no tiene por qué
  esperar al carril.

---

## 32. Conflictos y discrepancias decididos

| Id | K | Tema | Quién dijo qué | Decisión y evidencia |
|---|---|---|---|---|
| VC-01 | K1 | Dueño | FH:2278-2279 (orquestador de Task 6): staff; la nota 0.34.0 lo repite (`docs/versiones/0.34.0.md:221-223`). Del lado del staff, también `harness-backend-engineer.md:21` y `CLAUDE.md:63` (guardián). WU05/12:B1 y WU07/09:B1/D11: el contrato dice backend | **Backend** (VD-02): `CLAUDE.md:62`; `harness-backend-engineer.md:20`; `harness-staff-engineer.md:22-25`. `harness-backend-engineer.md:21` y `CLAUDE.md:63` le dan al staff acelerar código que ya funciona con el comportamiento congelado, no crear una herramienta con salidas nuevas; la nota no decide («no tocó la spec de 6.1», `:224`) |
| VC-02 | K2 | «No third way» | `harness-backend-engineer.md:70-71` contra el brief; matiz: `correr.py -k` ya es una segunda forma (`harness-spec-refuter.md:57`) | **Enmienda M1 + ADR-0018** (VD-01). El brief de la persona ya eligió; la regla protege un comando de cierre y una forma de reporte, y las dos se conservan |
| VC-03 | K3 | Dueño vivo | WU10: candado del SO, nunca un pid. WU05:INV-07 y WU04: pid + arranque para barrer | **Un mecanismo, el candado**, en dos usos (VD-13): `registro.py:35-36, 925-945`; GE:767-787; el orden lock → carpeta cierra N1 (§19.4). pid + arranque sigue solo en `isolated-factory.ps1` |
| VC-04 | K4 | PATH y Bash | Brief §17: validar, fijar, heredar o documentar. WU02:R-c y WU01: 54i, 62i y t63c dependen de Git Bash; el stub de WSL gana. WU05: reordenar es innecesario. Orquestador: las corridas verdes pusieron Git Bash primero | **Heredar sin tocar y registrar**: el encabezado del runner y el medidor dicen qué `bash` resolvió; la precondición se documenta (§5.2). Validar agregaría un rojo que el oráculo no tiene; fijar, un verde. 54i y 62i buscan Git Bash desde `git.exe` (WU01 §12, no releído); el defecto de t63c E-38 es VX-09. Con la nota 0.34.0, ver VC-26 |
| VC-05 | K5 | «Mismo total» y deriva | Brief: diferencia 0. WU05:R5, WU07:g, WU04:fila 27, WU02:R-b: el oráculo deriva (22-09). Orquestador: 30 y 33 idénticos entre 0.33.0 y F1 | **Estricta, sin tolerancia** (VD-14). La deriva, si aparece, sale `NO_EQUIVALENTE` con la suite y los dos conteos (VP-E18); el par se registra y no cuenta como equivalente; la fuente sigue en FH (VX-10). El dato del orquestador no se releyó y no sostiene la decisión: la sostiene el brief |
| VC-06 | K6 | Causa de E-58 | FH:1042, WU02, WU05/12: el límite de 1,5 s de la compuerta. WU04:C1/fila 13: `remotos` de 10 s no estricto | **WU04 tiene razón, por el código**: `identidad` llama `remotos(proyecto)` sin límite propio (`repositorio.py:253`), es decir 10 s y no estricto (`:168, 182-187`): un timeout o un error de `git` da `None` y no hay identidad local. El 1,5 s es de los hooks: «La CLI sigue con los 10 s de `remotos`» (`flow_gate.py:38-42`). 55 va al carril `ventana` por la falla observada, no por la hipótesis; el texto de FH:1042 se corrige (VX-13) |
| VC-07 | K7 | Timeout, árbol, Job Object | WU05: timeout solo con motivo propio y umbral medido. WU02:INV-4: cortar matando el árbol, sin reintentar. WU04: `taskkill /T` no alcanza huérfanos; Job Object pide P/Invoke. WU10:D8: reabre MP-01 | **Fórmula medida, `taskkill /T /F` con handle, sin Job Object, sin reintento** (VD-11). MP-01 (ME:1697, :1775) lo difiere hasta un caso real; los huérfanos existen igual en serial (`72:299-305`); el residuo se declara (§16.5) y se barre (§19.4) |
| VC-08 | K8 | Bytecode | WU04:opción D: `PYTHONPYCACHEPREFIX`. WU05: entorno heredado; WU02:INV-5: t18i E-33 depende de los `.pyc` | **No se fija nada**: `18-integraciones-instalador.ps1:35-48` compila en el origen y afirma que hay bytecode; `.gitignore:42-43` saca los `.pyc` de la huella; `install.ps1:333-336` los descarta después de enumerar, y el síntoma del 22-09 vino con un pase que **borró** miles de `__pycache__` (FH:1004-1006), cosa que ninguna suite hace (WU04:fila 15, no releído entero) |
| VC-09 | K9 | Cola serial contra 30 min | WU04:C y WU02:B/C: colas seriales. Orquestador: 73 + 72 + 63-hu ≈ 31 min (MEASURED-previa) | **Carriles que conviven con el pool** (VD-08). Con WU03-a: carril `motor` 15,8 min; la cola de WU04:C da ≈ 35,7 min ESTIMATED con N = 2 y f = 1, y la cota con carriles, 25,9 min (§13.3); el target dependía de f: WU03-b midió f ≈ 1,23 y 35,2 min con N = 2 (§5.6), así que la preferencia de 30 min no se alcanzó y el umbral lo fijó la regla de §22.3 (D-T7) |
| VC-10 | K10 | Qué cuenta el límite | Brief: workers, default 2. WU02:INV-6/D y WU04:E: procesos vivos. WU10:C-B: RAM | **Suites vivas** (VD-07); la carga interna la contienen los carriles |
| VC-11 | K11 | Marcas `.avisado` | WU02:R-d: con temporal por suite la semántica cambia. WU05: igual al estado inicial del serial, se pierde el estado entre suites. WU04:fila 2: E-08 es dentro de una suite | **Temporal por suite**: es el estado que el oráculo dice necesitar («Un test que verifica ese aviso tiene que arrancar sin marcas previas, o pasa o falla segun lo que haya corrido antes», `Invoke-Tests.ps1:133-135`). Una suite que solo pasa con marcas de otra es un defecto suyo; lo muestra la paridad, no se esconde |
| VC-12 | — | Cantidad de suites | Brief 100; WU01 98 con `.gitkeep`; WU02 97; WU04 «75 `.py`» | **97 = 24 + 73** (Glob leído; confirmado sobre `d86b285` por el discoverer y por WU03-a) |
| VC-13 | — | Funciones compartidas entre `.ps1` | WU02: ninguna usada en otro. WU01: homónimas en 11/54 y 14/19 | Las dos ciertas: se definen dos veces y cada archivo usa la suya, porque la segunda definición llega después de que el primero corrió. Por proceso, cada uno ve la propia: equivalente. WU03-a no vio diferencias de grupo PS (35/35, §5.6) |
| VC-14 | — | `Invoke-HookEnProceso` | WU02: sin usos; WU01: lo agrupó con otros helpers | Irrelevante: el worker es el oráculo y conserva todos los helpers (`Invoke-Tests.ps1:83-125`) |
| VC-15 | — | ¿`install.ps1` corre la suite? | Cinco documentos dicen que sí; WU01:C1, WU05/12, WU07/09, WU10:C1 dicen que no | **No la corre**: grep de `Invoke-Tests` y `correr.py` en `install.ps1`: 0; su compuerta es `Test-HooksInstalados` (`install.ps1:1081, 2160`). Los textos (`CLAUDE.md:49-50`, `Invoke-Tests.ps1:9`, `harness-backend-engineer.md:55`) quedan en VX-12. `install.ps1` no cambia |
| VC-16 | — | ¿03 rompe el árbol? | `close-a-version/SKILL.md:137-142` y el `CLAUDE.md` de `C:\Work` dicen que sí | **No**: rompe una copia (`isolated-factory.ps1:1-11`); `CLAUDE.md:52-55` de `C:\dev` ya lo dice; en WU03-a la huella quedó igual con 03 corrido tres veces. VX-12 |
| VC-17 | — | `__pycache__` | WU01: no verificado | **Ignorado** (`.gitignore:42-43`) |
| VC-18 | — | Cita de `_bloquear` | GE:771 cita `registro.py:226-231` | Hoy está en `registro.py:259-264` (leído; igual en `d86b285`). Spec histórica: no se edita; anotado (VX-17) |
| VC-19 | — | Conteos de 30 y 33 | Orquestador: idénticos entre 0.33.0 y F1 | No releído; no sostiene ninguna decisión (VC-05) |
| VC-20 | — | VP-E23 y los fines de línea | Spec: la copia se verifica «por hash». Discoverer: el blob de `Invoke-Tests.ps1` es LF y el árbol CRLF (`git ls-files --eol` = `i/lf w/crlf`) | **Identidad de la versión de partida por blob id** (`git rev-parse v0.34.0:tests/Invoke-Tests.ps1`, hoy `3d07849…`) o `git diff` con fin de línea normalizado; nunca por sha256 de bytes crudos contra el archivo del árbol: con `*.ps1 text eol=crlf` (`.gitattributes:11`, leído) daría distinto para el mismo contenido. Precisión de VP-E23, mismo id; la comparación de salidas sigue byte a byte |
| VC-21 | — | Residuos de las suites contra «residuos atribuibles» | `wu03a-analisis.md`: ranking por prefijo, sin t72 ni t73 arriba. Analista: el agrupado parte `me72-*` (709) y `ge73-vuelta-*` (60) en cientos de prefijos; 760 por corrida. §22.1: cero residuos atribuibles a la corrida paralela | **Manda el recuento del analista** (`restos-tmp.txt`; FH:2126-2127 lo confirma para t72 y t73). Esos residuos son de las suites: en la pata serial se registran y no rechazan el par; en el runner caen en `s<nnn>` y se borran con él (§16.5, §22.1). Solo un `s<nnn>`, una raíz `hpp-<id>` o un `AVISO LIMPIEZA_INCOMPLETA` son atribuibles a la corrida paralela. Limpiar lo de las suites es VX-20 |
| VC-22 | — | Qué es la paridad de WU03-a | Brief: registrarla. Analista: la sostienen §22.1, §20.4.2-3, VP-I02, VP-I12, VP-E25 y §35; no VP-I09 | **Observación pre-construcción** (§5.6, §5.7 B3): condición necesaria a esta huella, sin `rojo visto` ni veredicto; **no** prueba VP-I09, que es de carriles e intervalos del runner, ni ningún otro invariante: el sujeto de los VP-I es el runner, que no existe |
| VC-23 | — | La previa 0,61× | §2.3, §6 y §13.3 del borrador usaban la serie por suite del 18-10. WU03-a: la sola de hoy tarda 0,61-0,69× de esa serie | **La previa no alimenta nada** (§5.7 B1, analista:D8): ni `maxSeconds`, ni `timeoutSeconds`, ni umbrales. Se conserva en §2.3 como contexto, con su hipótesis sin demostrar (carga, `%TEMP%` cargado) |
| VC-24 | — | Dispersión y VD-11 | WU03-a: 20,4 % entre dos seriales seguidas. Analista: el 3 de VD-11 cubre la peor dispersión contra la suite sola, no contra la previa × 2,15 | **VD-11 se sostiene**: 2187 s = 3,0× la sola de t73 cubre 2,15× sobre la sola (1567 s) y la corrida 2 inferida (≈ 1,34×). Contra la previa no cubriría (2580 s): la previa no entra (VC-23); el riesgo queda en R23 y el primer par actualiza el manifest (§10.2) |
| VC-25 | — | Condiciones una sola vez | §5.2: «antes de cada corrida». WU03-a: una toma, antes de la corrida 1 (`medir.ps1:45-71`) | **WU03-a vale como baseline**, con el desvío registrado (§5.3): las huellas coinciden y ningún número depende de lo no registrado. Desde WU03-b, condiciones **antes de cada pata y de cada tramo** (§5.2), y el medidor las toma así |
| VC-26 | — | Git Bash y elevación: ¿precondición o herencia? | Borrador §5.2: «hoy el stub de WSL». WU03-a: el `bash` por defecto fue el de Git porque se lanzó desde Git Bash, y el efectivo, otro, antepuesto con ruta fija (`medir.ps1:15`). Nota 0.34.0: Git Bash al frente y no elevado (`docs/versiones/0.34.0.md:163-166, 249-251`) | **VC-04 se mantiene para el runner y el medidor**: heredan, no fijan. Git Bash al frente, no elevado y el clon con sus bases son **precondiciones del oráculo y del benchmark**, que cumple quien lanza (§5.2); si antepone algo al `PATH`, lo deriva de `(Get-Command git).Source`. Las dos patas, con el mismo `bash` efectivo registrado (§5.7 B2). R8 reescrito; VX-09 ampliado |
| VC-27 | — | Qué manda en el camino crítico | Borrador §13.3: el carril `motor` (≈ 26 min MEASURED-previa). WU03-a: el carril dura 15,8 min | **Con N = 2 manda W/N** (25,9 min de cota con f = 1), no el carril; con N = 4 manda el carril `instalador` (16,1). §13.3 reescrito; las decisiones de VD-08 no cambian |
| VC-28 | — | Stretch ≤ 25 min contra N = 2 | Brief: stretch ≤ 25. VD-07: N = 2. WU03-a: cota 25,9 con f = 1 | **El stretch se declara inalcanzable con N = 2** (§22.2); N = 2 sigue por defecto (VD-07); N = 3 se evalúa en WU03-b (§5.4, paso 5) y su adopción como valor por defecto sería una decisión de la persona con un par medido |
| VC-29 | — | `maxSeconds` contra la huella final | §10.2 del borrador: «el máximo de cualquier corrida». VP-E25: el par sobre la huella final. Analista: actualizar el manifest cambia la huella, y un par nuevo trae máximos nuevos | **El primer par actualiza; el que cierra no realimenta** (§10.2, §5.4, §5.7 B4, analista:D1 opción a). El lazo termina en un paso; si el primer par no sube nada, puede ser el que cierra |
| VC-30 | — | «Basta una corrida» contra una falla serial documentada | §10.5: basta una corrida roja en paralelo y verde en serial. Nota 0.34.0: t72 E34 falló una vez en serial, carrera del fixture no reproducida (`docs/versiones/0.34.0.md:149-158`) | **§10.5 se aplica igual, con la causa registrada**: el par es `NO_EQUIVALENTE` (VD-14), la suite no se relanza, y pasa a la clase más estricta como medida precautoria; ese rojo no cuenta como falso rojo del runner mientras la causa no se demuestre; vuelve a su clase solo con dos pares verdes (§10.5). Elegir «exigir más antes de reclasificar» haría depender la clase de cuántos pares rojos se toleran, que es una tolerancia |
| VC-31 | — | Tres rangos para la misma medición | «45 to 70» (FH:2260), «47 a 101» (`docs/versiones/0.34.0.md:191`, `CHANGELOG.md:65`), «45 a 85» (`docs/cambios/knowledge-api/verificacion.md:192`) | **Ninguno decide nada**: son MEASURED-previa, se citan tal cual (§2.3); el baseline es WU03-a |
| VC-32 | — | Número del ADR | Borrador: «provisorio 0018». Discoverer: 0007 no existe a propósito (`docs/codebase/docs.md:33`) y un ítem propone llenarlo (`PENDIENTES-I.md:67`) | **ADR-0018.** Usar 0007 tomaría el lugar que un pendiente abierto reserva para otro ADR |
| VC-33 | — | Evidencia de t74 en §6 | Borrador: «P; junction y temporal propio». Discoverer: además depende de git y del tag `v0.33.0`, carga `correr.py`, 19 y t64, y observa las protegidas con `ls-files --others` | **La clase no cambia** (`parallel`): ninguna de esas dependencias es una ventana de tiempo ni una escritura en el árbol (guardián: sin escrituras en `RAIZ`); la evidencia se completa (§6, fila 97) y el tag pasa a ser precondición del clon (§5.2) |
| VC-34 | NB-01 | VP-E24 y «sin procesos» | SPEC REVIEW (refutador): VP-E24 incluía la cláusula del runner (manifest no JSON ⇒ `MANIFEST_INVALIDO`; timeout fuera de fórmula ⇒ corre), que lanza procesos, mientras §26 y §6 fila 98 lo asignaban entero a `75_manifest_paralelo.py`, «unidad, sin procesos»; era la única cobertura de F16 y de la mitad runtime de VP-I17 | **Un escenario, dos partes, dos suites** (VD-15 intacto, VD-06 intacto): la parte A (política del manifest real, §10.3b) sigue en `75_manifest_paralelo.py` sin procesos; la parte B (forma en el runner, §10.3a/§10.4) pasa a `75_runner_paralelo.py` con procesos reales. Sin escenario nuevo ni `testMode`; el `rojo visto` se registra por parte (§26) |
| VC-35 | NB-04 | BOM en `.py` | Borrador §8.3 (WU07, no releído): «un `.ps1` o `.py` nuevo con no ASCII lleva BOM». `00-encoding-fuentes.ps1` leído sobre `d86b285`: BOM obligatorio solo en `.ps1`/`.psm1` con no ASCII (`:21-46`); **ningún `.py` con BOM**, E-28 (`:49-72`) | **La spec dice la regla real** (§8.3): `.ps1` nuevos con acentos llevan BOM; `75_manifest_paralelo.py` y `75_runner_paralelo.py` se guardan sin BOM. No se agrega política: es lo que la suite ya exige |

---

## 33. Pendientes

Se registran con `note-a-pending` al construir; no se resuelven en 6.1.

| Id | Qué | Dónde va |
|---|---|---|
| VX-01 | Benchmark con y sin exclusiones de Defender | I |
| VX-02 | Paralelización en CI | I |
| VX-03 | Ejecución remota o por shards | I |
| VX-04 | Promoción del runner a oráculo (fase D, ADR nuevo, persona) | I |
| VX-05 | Optimizar las suites lentas (t73 728,8 s y t72 218,8 s MEASURED-BASELINE) | FH |
| VX-06 | La regex cuadrática de secretos (FH:2285) — ya registrada; se nombra para que no se confunda con 6.1 | FH (existente) |
| VX-07 | Coordinación técnica más amplia que la de §19.2: candado opt-in en el oráculo, en los lotes de mutaciones y en el tramo serial del medidor (WU10:D2, D4); hasta entonces rige la regla operativa de §28. **Ampliado en la pasada post-WU03-b** (guardián, 20-10-2026, G-b): un `-SoloCaso` o un `correr.py -k` lanzado a mano con el `%TEMP%` compartido corre `Clear-MarcasHarness` y borra los `*.avisado` de un oráculo completo que esté corriendo (de ellos dependen 01, `65_fail_closed.py` y `61_conocimiento_auto_refresco.py`); la regla operativa a escribir: lo focal a mano corre con `TEMP`/`TMP`/`TMPDIR` propios | FH |
| VX-08 | Job Object por worker si aparece un huérfano real después de un corte (MP-01 aplicado a tests) | I |
| VX-09 | Las precondiciones del oráculo no están en `CLAUDE.md` §«The gate»: Git Bash al frente del `PATH` (t63c E-38 usa `shutil.which("bash")` y cae en el stub de WSL), no elevado (QG1 E-05b, `68-isolated-factory.ps1:170-181`) y un clon con los tags y commits base que leen las suites (§5.2). Hoy solo las escribe la nota 0.34.0 (`docs/versiones/0.34.0.md:249-251`) | FH |
| VX-10 | Deriva de 30 y 33 y reloj de 19 E-29 (FH:1023-1033): siguen en FH; el comparador los hace visibles | FH (existente) |
| VX-11 | t72 deja `HOST_FALSO_GUION` en el proceso (`72:137`) y `_terminar` mata por pid (`72:355-357`) | FH |
| VX-12 | Textos que dicen que `install.ps1` corre la suite (`CLAUDE.md:49-50`, `Invoke-Tests.ps1:9`, `harness-backend-engineer.md:55`, `docs/contrato-hooks.md:272` —«`install.ps1` usa `Invoke-Tests.ps1` como compuerta», agregado por el guardián, G-b—, más dos que nombra WU05 sin releer) y que 03 rompe el árbol (`close-a-version/SKILL.md:137-142`, `CLAUDE.md` de `C:\Work`) | FH |
| VX-13 | FH:1042 atribuye E-58 al límite de 1,5 s; el código dice `remotos` de 10 s no estricto | FH (corrección del ítem) |
| VX-14 | Rol del runner en la refutación (Task 8; WU05:B3) | I |
| VX-15 | Elegir suites por archivos tocados y reusar resultados por huella (FH:2280) | I |
| VX-16 | Espera opcional del candado y testigo de reentrada (WU10:D5, D6) | I |
| VX-17 | La cita corrida de GE:771 | FH |
| VX-18 | Los restos de una corrida paralela matada solo los barre otra corrida paralela; `CLAUDE.md:52-55` habla de «a later run» | FH |
| VX-19 | Defecto latente del oráculo, solo en el camino de falla: `03-instalador.ps1:846` reusa `$caso` en un `foreach` dentro del `try` de nivel superior de `:767`, en el scope del oráculo; si 03 tirara después, el `catch` de `Invoke-Tests.ps1:178-180` tomaría `$caso.BaseName` de otro objeto y no del archivo. 65-inst (`:97`) y 66-inst (`:18, 46`) pisan `$nombre`, que rompe cualquier copia del preludio que lo use. El camino `-SoloCaso` ya no depende de eso (§21); el camino por defecto no se toca en 6.1 (VD-04) | FH |
| VX-20 | Las suites Python dejan residuos en su temporal: 760 entradas por corrida completa, 256 de t72 y t73 (FH:2119-2133) y ≈ 504 de unas 20 suites más (51, 10, 53, 60, 13, 15, 19, 55 y sus cargadores, 18, 56, 58, 59 y otras, §5.6). Amplía el ítem existente | FH (ampliación) |

**Nuevos en la pasada post-WU03-b** (22-10-2026), de las observaciones de la construcción y de WU03-b:

| Id | Qué | Dónde va |
|---|---|---|
| VX-21 | Defecto del oráculo: la combinación toma el **primer** `N/M pasaron.` de la salida de `correr.py` (`Invoke-Tests.ps1:262-270`). Con `-Detallado`, el nombre de una fila `ok` con ese texto lo engaña: en el par 1 de WU03-b imprimió `971/972` y salió 1 con todo verde (§4). Sin `-Detallado` puede pasar con el detalle de una fila `MAL`, que sale antes del resumen. En 6.1 se esquivó renombrando siete filas de `75_runner_paralelo.py`; la suite no lo impide | FH |
| VX-22 | ADR-0018 §4 (`0018:53`) dice que quien refuta puede explorar con el runner sin la condición «desde la fase C» que pone su §2 (`:42`) y la spec (§28, VX-14) (guardián, G-b) | FH |
| VX-23 | `harness-backend-engineer.md:3` («its two runners») y `:20` («both runners») llaman runner a los motores, mientras `:72` llama runner al oráculo y 6.1 llama runner a `Invoke-Tests-Parallel.ps1`: vocabulario a unificar (guardián, G-b) | FH |
| VX-24 | `75_runner_paralelo.py` cuesta 5 a 10 minutos: 364,3 s en la pata paralela del cierre (la segunda más larga después de t73), 299,1 s en la del 1b, 592 s solo en la etapa 9c; lo domina el arranque de cada worker de sus runners anidados. Trabajo del staff engineer con el comportamiento congelado | FH |
| VX-25 | Robustez de `75_runner_paralelo.py`: VP-E08 y VP-E20 son sensibles a la carga de la máquina (en la etapa 9 la precondición de E08 salió roja 8/8 con una sesión ajena al 50 % de CPU; fallan «inconcluso», no pasan vacíos), y VP-E21 (c) ve VM-17b por una excepción que corta el resto de las filas, no por una fila | FH |
| VX-26 | La guarda de `MAX_PATH` de `75_runner_paralelo.py` (70 caracteres para su `TEMP`) salta bajo el runner cuando quien lanza tiene un `TEMP` largo, porque el runner agrega `hpp-<id>\s<nnn>`: en el par 1 de WU03-b dio 26 filas rojas en paralelo con la suite verde en el oráculo (§5.2). Un rojo así es del test bajo el runner, no del código que prueba; hoy se evita lanzando con un `TEMP` corto (`C:\t`) | FH |
| VX-27 | El progreso del runner imprime, para una suite Python roja, una línea de estilo PS (`[py_b] fila-01 …`) que sale de aplicarle `Get-LineasDeFallosPs` a un registro Py (etapa 4b). Cosmético, fuera del reporte comparable | FH |
| VX-28 | El piso de RAM del medidor no se fijó (§5.2): `FreePhysicalMemory` es de toda la máquina y no hay muestreo por proceso; en la pata paralela del cierre la RAM libre bajó a 3,20 GB sin poder atribuirlo. Fijarlo pide medir el consumo propio de una corrida | I |
| VX-29 | Unas 129 filas `ok` de suites existentes llevan datos volátiles en el nombre (la hora en `57_aceptar_fuentes` E-19; rutas del temporal y pids en t63c E-28, E-31 y E-65; valores observados en `75_runner_paralelo`), y eso hace insatisfacible el punto 5 de §20.4 en el árbol real (D-T5). Para la fase B: normalizar esos nombres en sus suites o declarar que el punto 5 no aplica al árbol real | I |

---

## 34. Matriz de consolidación

| Tema | Evidencia | Decisión |
|---|---|---|
| Ownership | `CLAUDE.md:62, 63`; `harness-backend-engineer.md:20, 21, 24-25`; `harness-staff-engineer.md:22-25`; FH:2278-2279; `docs/versiones/0.34.0.md:221-224`; WU05/12:B1; WU07/09:D11; guardián | Backend (VD-02, VC-01); la contradicción FH y nota 0.34.0 (staff) contra el contrato (backend) se decide por el contrato; `harness-backend-engineer.md:21` no la cambia |
| Lifecycle | WU07/09; WU08 (F1-F18); `Invoke-Tests.ps1:174-182`; `correr.py:61-76` | Corrida: §9.3; suite: §14.1; nunca se relanza (VP-I02) |
| Scheduling | WU02 (opciones A-D); WU04 (A-E); orquestador K9; `72:550-593, 875-923`; `73:2167-2183`; FH:2276-2283; WU03-a (carriles, Pareto, cota); analista (simulación de §13.1) | Carriles que conviven con el pool, más largas primero, `serial` al final (VD-08, VC-09); con N = 2 manda W/N, 25,9 min de cota (VC-27); WU04:C y WU02:B/C descartadas con número |
| Concurrency | WU02:INV-6; WU04:E; WU10:C-B; brief (2 workers, sin `cpu_count`); WU03-a (cota N = 2 y N = 3); analista:D9 | Suites vivas, N = 2, `-Workers` 1..4 (VD-07, VC-10); stretch inalcanzable con N = 2 (VC-28); N = 3 informativo en WU03-b |
| Recovery | `isolated-factory.ps1:44-65`; WU05:INV-07 y WU04 (pid + arranque) contra WU10 (candado); `registro.py:35-36`; GE:767-787, 872-902; analista:CW1-CW3 | Barrido por candado de la raíz, bajo el candado global (VD-13, VC-03); pid + arranque solo en la fábrica; el muestreador del medidor no lo sobrevive (§5.7 B5) |
| Admission | WU10 (L1-L5, C-A a C-D, D1-D9); ME:630-640; `registro.py:259-264, 925-945`; analista:D7 | `pesada.lock` exclusivo, sin espera, exit 2, **solo entre runners** (§19.2); el oráculo no lo toma (VD-13, VD-04); el medidor no lo toma en la pata serial; lo demás, regla operativa (§28) y VX-07 |
| Persistence | WU02 (PERSISTENCE); WU04 (filas 4-5, 14); `.gitignore:42-43`; `72:263-267`; WU03-a (760 residuos por corrida, huella igual en cuatro tomas) | Nada en el repo; temporales y logs en `TempBase`; candado en `%LOCALAPPDATA%`; logs de una corrida roja hasta la siguiente (§16.5); los residuos de las suites caen en `s<nnn>` (VC-21) |
| Tests | WU08/13 (16 invariantes, 25 escenarios, 20 mutaciones, PR, CR, fixtures); ADR-0009; `harness-spec-refuter.md:68`; discoverer §F | 24 escenarios en dos casos `75_*` sobre layouts sintéticos + VP-E25 con el medidor; 0 lecturas (VD-15); VP-E13 por la costura interna del agregador (§16.7), sin procesos; VP-E23 por blob id (VC-20) |
| Isolation | WU05 (tabla); WU04 (filas 1-3, 19-21); `18-integraciones-instalador.ps1:35-48`; `docs/versiones/0.34.0.md:163-164` | Solo el temporal; WU04:D (`PYTHONPYCACHEPREFIX`) contra WU05 (heredar) decidido por t18i (VC-08) |
| Equivalencia | WU05:R5/D1-D4; WU07:g; WU04:C3; orquestador K5; nota 0.34.0 (t72 E34) | Estricta, por suite, con huella (VD-14, VC-05); una falla serial documentada no se tolera: se reclasifica con la causa registrada (VC-30) |
| Resultado | WU07 (a)-(f); `Invoke-Tests.ps1:262-292`; `correr.py:85-93` | Texto del oráculo, última línea, cruce con grupos (VD-09); WU07:b (JSON) descartada |
| Cancelación | WU02 (CANCELLATION); WU04 (opciones a-c); WU13 (PR-3, opciones 1-4) | Un `finally`, señal inyectable, `taskkill /T /F`, sin Job Object (VD-12, VD-11, VC-07) |
| PATH/Bash | WU01 §12; WU02:R-c; WU05; orquestador K4; `condiciones.txt` de WU03-a; nota 0.34.0; analista:D4 | Heredar y registrar (VC-04); Git Bash al frente, no elevado y las bases, precondiciones de quien lanza (VC-26) |
| Oráculo | WU05 (M2, ME-E51, E-22); WU07/09 (opciones A-C); `66_integrity_cleanup.py:471-476`; `72:2330-2335`; `Invoke-Tests.ps1:237, 245`; `03-instalador.ps1:846` | Solo `-SoloCaso` (VD-04), con el grupo de la fila de carga desde la enumeración (§21); el defecto del camino por defecto, a FH (VX-19) |
| Benchmark | WU03-a (§5.6); analista (D1-D9, R21-R28, VP-B1..B6); `medir.ps1`; WU03-b (tres pares N = 2, §5.6, `benchmark-2026-10-22.md`) | Baseline medida; protocolo con las reglas de §5.7; lazo de un paso (VC-29), cerrado con el par 1b; umbral 0,75 por la regla 2 de §22.3 (D-T7) |

---

## 35. Métricas de éxito

| Metric | Baseline | Target | How measured |
|---|---|---|---|
| Serial wall clock | **MEASURED-BASELINE**: 2963,1 s (49,4 min) y 3568,1 s (59,5 min) sobre `d86b285`, dispersión 20,4 % (§5.6). MEASURED-previa: 43,7 a 101 min según carga (§2.3). **MEASURED-WU03-b**, árbol construido: 2976,9 s (49:36) sin `-Detallado` | Sin cambio: el oráculo no se acelera | `Stopwatch` del medidor alrededor de `.\tests\Invoke-Tests.ps1`, sin `-Detallado` desde D-T5 (WU03-a y el par 1b lo corrieron con él), §5.2 cumplido antes de cada pata |
| Parallel wall clock | **MEASURED-WU03-b**, N = 2: 2110,4 s (35:10) en el par de cierre; relación 0,7089; ahorro 866,5 s (14,4 min, 29 %) sobre la serial del mismo par | ≤ 75 % del serial (**normativo**, D-T7): **cumple**; preferencia ≤ 30 min: no alcanzada; stretch ≤ 25 min, inalcanzable con N = 2 (§22.2) | Medidor, misma huella, N = 2 (N = 3 no se midió, D-T1) |
| Case count (suites) | **97** sobre `d86b285` (24 `.ps1` + 73 `.py`; discoverer y WU03-a) + 2 de 6.1 | Diferencia 0 | Enumeración del runner = enumeración del oráculo (VP-I02); comparador por grupos |
| Assertion total | **MEASURED-BASELINE**: 47.957 = PS 968 + Py 46.989, igual en las dos corridas completas y en la suma de las 97 solas | Diferencia 0 | Comparador: `total` PS, Py y combinado |
| Failed count | 0 en verde | Diferencia 0; mismo multiconjunto de filas | Comparador |
| Exit code | 0 (las dos corridas de WU03-a) | Igual al del oráculo | Comparador |
| Repo mutations | 0 (huella igual en las cuatro tomas de WU03-a) | 0 | Huella antes y después de cada corrida (§5.1) |
| Temp residues | **Oráculo** (de las suites, no de un runner): 760 entradas por corrida completa en un temporal aislado, más la carpeta de marcas (§5.6). **Runner**: no existe | **Corrida funcional:** puede avisar `LIMPIEZA_INCOMPLETA` sin cambiar el exit (§16.5); en roja o cancelada, solo residuos declarados. **Benchmark / adopción (VP-E25, pares de WU03-b):** 0 residuos atribuibles a la corrida paralela, obligatorio (§22.1): sin raíz `hpp-<id>`, sin `s<nnn>`, sin el sidecar `hpp-<id>.lock` de esa corrida, sin aviso. Los residuos de la pata serial se registran y no cuentan (VC-21); `pesada.lock` y `pesada.json` no son residuos (§19.5) | Medidor: listado de `<TempBase>\hpp-*` **y `<TempBase>\hpp-*.lock`** antes y después de la pata paralela, del temporal de cada pata, y la salida del runner |
| Workers | — (serial = 1) | 2 por defecto; 3 no evaluado en 6.1 (D-T1) | Encabezado del runner |
| Peak concurrent heavy jobs | 1 (serial) | ≤ 1 por carril; ≤ N en total, dentro de una corrida. Entre corridas, el candado solo excluye a otro runner (§19.2); el resto lo cubre la regla operativa de §28 | Intervalos de las líneas de progreso; condiciones de §5.2 |
| False greens | — | 0 | Pares de WU03-b; VP-E01 a VP-E24 |
| False reds attributable to the runner | — | 0 | Pares: suite roja en paralelo y verde en serial sobre la misma huella ⇒ clase más estricta (§10.5); un caso con falla serial documentada no cuenta mientras la causa no se demuestre (VC-30) |
| Per-suite parity | **Observación pre-construcción** (no veredicto): 97/97 en conteos entre la suite sola y la corrida completa (Py 73/73 grupos, PS 35/35 líneas de grupo; §5.6, VC-22) | 97/97 (99/99 con 6.1) entre el oráculo y el runner | Comparador, grupos PS y stems Py |
| Overhead por suite | **≈ 1 s por suite trivial** (MEASURED-WU03-b contra la sola de WU03-a, §5.6) | Registrado; si pesa, trabajo del staff (R18, VX-24) | Duración de una suite trivial con `-SoloCaso` contra su duración sola |
| RAM libre mínima | **MEASURED-BASELINE, serial**: 6,70 GB de 23,71, con dos sesiones de Claude Code (no es el consumo del oráculo). **MEASURED-WU03-b**, patas paralelas: 14,31, 14,10 y 3,20 GB (la última sin atribuir, §5.2) | Sin piso en 6.1 (§5.2, VX-28) | Muestreo CIM del medidor |
| Equivalencia del par que cierra | — | `EQUIVALENTE`, residuos 0 | **Cumplido** en el par de cierre (§5.6) |
