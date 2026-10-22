# Benchmark de la Task 6.1: el oráculo contra el runner paralelo

**Fecha del registro:** 22-10-2026 · **Lo escribió:** `harness-task-architect`, a mano, desde los registros del
medidor y del orquestador (§9.6 de la spec: el medidor no escribe en el repo) · **Spec:**
[`spec.md`](spec.md), §5.4 y §5.7.

Es el registro de WU03-a (el serial antes de construir) y de WU03-b (serial contra paralelo, con el runner y el
medidor construidos). Los números llevan el rótulo de la spec: **MEASURED-BASELINE** (WU03-a), **MEASURED-WU03-b**
(los pares) y **ESTIMATED** (cuentas sobre lo medido).

## En corto

| | |
|---|---|
| Resultado | El par de cierre (22-10-2026, N = 2) dio `EQUIVALENTE`, cero residuos, las tres huellas iguales y relación **0,7089** |
| Serial (`.\tests\Invoke-Tests.ps1`) | **49:36** (2976,9 s), exit 0, 48841/48841 |
| Paralelo (`.\tests\Invoke-Tests-Parallel.ps1 -Workers 2`) | **35:10** (2110,4 s), exit 0, 48841/48841 |
| Ahorro | **14,4 min** (866,5 s), **29 %** menos de wall |
| Umbral | 0,75, normativo (D-T7). El par corrió con `-Umbral 0.70` y el medidor salió 1 solo por eso; con 0,75 cumple |
| Pares no aceptados antes | Dos (par 1 y par 1b), por defectos ajenos al runner; se arreglaron y se repitió |

## El árbol medido

| | |
|---|---|
| HEAD | `d86b285a9d0a4610a44a15ba3ca455be42d2edaa` (`main`, 0.34.0, tag `v0.34.0`), sin commit de 6.1 |
| `git status` | 10 líneas: los dos archivos modificados de 6.1 y sus ocho nuevos |
| Huella del par de cierre | `94999FD9DFB3EC1AE9220C4178401C7DF07FC96BDDA24FC9D198AF708B33DE30` (831 archivos no ignorados) |
| Huella de la baseline (WU03-a) | `FDEF538098DC593B4E3537BB945A8F365A788E7DEC29B80E501A056E58BF4C70` |

Hashes del árbol del par de cierre (16 primeros hex; los mismos al escribir este registro):

| Archivo | SHA256 |
|---|---|
| `tests/Invoke-Tests.ps1` (con `-SoloCaso`) | `E1834389F4004C1F` |
| `tests/Invoke-Tests-Parallel.ps1` | `8EF1A526983999BF` |
| `tests/Compare-TestRuns.ps1` | `65A7DB07DC653549` |
| `tests/Measure-TestRuns.ps1` | `E02F7E8E793DE99C` |
| `tests/parallel-manifest.json` | `8D3041543BB16372` |
| `tests/casos/75_runner_paralelo.py` | `6F9DC970AA2E0980` |
| `tests/casos/75_manifest_paralelo.py` | `CF158880F6A6CA04` |
| `tests/correr.py` (sin cambios) | `CBFF41984CA12D48` |

Este registro y la pasada post-WU03-b de la spec cambian la huella del árbol: el par de cierre vale para
`94999FD9…` (spec §30).

## Condiciones

| | WU03-a (20-10, 09:33) | Par 1 (21-10, 20:11) | Par 1b (21-10, 22:36) | Cierre (22-10, 09:17) |
|---|---|---|---|---|
| Máquina | 12 CPUs lógicas, 23,71 GB | igual | igual | igual |
| RAM libre al empezar | 7,61 GB | 15,15 GB | 14,75 GB | 12,43 GB |
| Sesiones abiertas | 2 procesos `claude` | 3 `claude` | 3 `claude` (1 lanzador, 2 sesiones) | 3 `claude` (1 lanzador, 2 sesiones) |
| Otra corrida pesada | no | no | no | no |
| Git Bash al frente del `PATH` | antepuesto con ruta fija | sí, sin tocar el `PATH` | sí, sin tocar el `PATH` | sí, sin tocar el `PATH` |
| `bash` efectivo | `Git\bin\bash.exe` | `Git\bin\bash.exe` | `Git\bin\bash.exe`, igual en las dos patas | `Git\bin\bash.exe`, igual en las dos patas |
| Elevado | no | no | no | no |
| `TEMP` de cada pata | `C:\dev\_build\wu03a\tmp` | `C:\dev\_build\w3b\hpm-…\tmp-*` | `C:\t\hpm-261021-223656\tmp-*` | `C:\t\hpm-261022-091757\tmp-*` |
| Tags y commits base de las suites | presentes | presentes | presentes | presentes |
| Versiones | git 2.55.0.windows.5, Python 3.12 | git 2.55.0.windows.5, Python 3.12.10, bash 5.3.15 | igual | igual |

En WU03-a las condiciones se tomaron una sola vez (desvío registrado, VC-25); en WU03-b, antes de cada pata.
Cada pata corrió con su `TEMP` nuevo y vacío; la paralela lo usó también como `-TempBase`.

## WU03-a: el serial antes de construir

| Medición | Valor |
|---|---|
| Corrida 1 | 2963,1 s (49:23), exit 0, 47.957/47.957 |
| Corrida 2 | 3568,1 s (59:28), exit 0, 47.957/47.957 |
| Dispersión | 20,4 %; manda el máximo |
| Las 97 suites solas | Σ 3110,8 s (51,8 min); `motor` 947,6 · `instalador` 967,6 · `ventana` 266,0 · `parallel` 929,6 |
| Paridad suite sola contra completa | Py 73/73 grupos, PS 35/35 líneas de grupo (observación previa, no veredicto) |
| Residuos de las suites | 760 entradas por corrida en su temporal |
| RAM libre mínima | 6,70 GB |
| Huella | `FDEF5380…` en las cuatro tomas |

Llenó `maxSeconds` y `timeoutSeconds` de las 97 suites (spec §6).

## WU03-b: los tres pares

Todos con `Measure-TestRuns.ps1 -Workers 2`, serial primero y paralelo después.

| | Par 1 | Par 1b | Par de cierre |
|---|---|---|---|
| Fecha | 21-10, 20:11 → 22:09 | 21-10 22:36 → 22-10 00:07 | 22-10, 09:17 → 10:42 |
| `-Detallado` en las patas | sí | sí | **no** (D-T5) |
| `-Umbral` | — | — | 0.70 |
| Wall serial | 4424,1 s (73:44) | 3280,1 s (54:40) | **2976,9 s (49:36)** |
| Exit y total serial | 1, `971/972` (falso rojo del oráculo) | 0, 48841/48841 | **0, 48841/48841** |
| Wall paralelo | 2638,5 s (43:58) | 2158,2 s (35:58) | **2110,4 s (35:10)** |
| Exit y total paralelo | 1, 26 filas rojas | 0, 48841/48841 | **0, 48841/48841** |
| Huellas (antes, entre patas, después) | `2E9BDA23…` ×3 | `E3CAD0FB…` ×3 | **`94999FD9…` ×3** |
| Comparador | `NO_EQUIVALENTE` | `NO_EQUIVALENTE` (solo el punto 5) | **`EQUIVALENTE`** (35 grupos PS, 75 Py) |
| Residuos contados por el medidor | 2 (raíz y sidecar de una corrida roja: correcto) | 2 (falsos: nombres de fila) | **0** |
| Relación paralelo / serial | 0,596 (no vale: par rojo) | 0,658 (sesgada por `-Detallado`) | **0,7089** |
| Medidor | exit 1 | exit 1 | exit 1, motivo único `UMBRAL` |
| Aceptado | no | no | **sí con 0,75** (D-T7) |

### Por qué no se aceptaron los dos primeros, y qué se arregló

**Par 1.** Dos defectos, ninguno del runner:

1. **El oráculo se engañó solo.** Con `-Detallado`, el oráculo toma como resumen de Python el **primer** texto
   `N/M pasaron.` de la salida, y una fila verde de `75_runner_paralelo.py` se llamaba
   `VP-E04 (a) el 3/4 pasaron. …`. Imprimió `971/972` y salió 1 con todo verde. Es un defecto del oráculo de
   antes (spec §4, VX-21). **Arreglo:** el builder renombró siete filas del test para que no imiten el resumen.
2. **La guarda de `MAX_PATH` del test.** Bajo el runner, el temporal de `75_runner_paralelo.py` quedó en
   `C:\dev\_build\w3b\hpm-…\tmp-paralelo\hpp-…\s099\t61_…`, 79 caracteres contra 70 que admite su guarda: 26
   filas rojas, solo en la pata paralela. **Arreglo:** correr el medidor con un `TEMP` corto (`C:\t`). El
   arreglo de fondo queda en VX-26.

**Par 1b.** Las dos patas verdes; dos falsos positivos de la medición:

1. **El punto 5 de la equivalencia no se puede cumplir en el árbol real.** Con `-Detallado`, el comparador
   compara también las filas verdes, y unas 129 llevan datos que cambian en cada corrida en el nombre (la hora
   en `57_aceptar_fuentes` E-19, rutas del temporal y pids en `63_compuerta_del_flujo` E-28, E-31 y E-65,
   valores observados en `75_runner_paralelo`): ni dos corridas seriales coinciden. Los puntos 1–4 y 6 dieron
   iguales. **Arreglo:** D-T5, los pares corren sin `-Detallado` (VX-29 para la fase B).
2. **El medidor contó como residuo dos nombres de fila** de `75_runner_paralelo.py` que citan el aviso
   `AVISO LIMPIEZA_INCOMPLETA`; el temporal de la pata paralela quedó vacío. **Arreglo del medidor:** solo
   cuenta las líneas que **empiezan** con `AVISO` (medidor `E02F7E8E…`; sondas de la preparación del cierre).

El par 1b igual sirvió: su pata serial fue la única suite completa oficial de la construcción (D-T3), y su pata
paralela alimentó `maxSeconds` (D-T6).

**Par de cierre.** Todo cumplió salvo `-Umbral 0.70`: 2110,4 s contra 2083,8 s permitidos (0,70 × 2976,9).
La relación 0,658 del par 1b no era comparable: `-Detallado` agrandó la salida a 4,5 MB por pata e infló más la
serial (≈ +5 min) que la paralela (≈ +1 min); es una inferencia, porque los dos pares no tienen la misma huella.
La persona fijó 0,75 (D-T7).

## Las decisiones de tiempo y de umbral

Las tomó Nahuel Palacio durante la construcción; están en la spec, §1.3.

| Decisión | Fecha | Qué | Por qué |
|---|---|---|---|
| D-T1 | 21-10 | El par N = 3 no se corre en 6.1 | Era informativo; cada par cuesta ≈ 1,5 h de máquina |
| D-T2 | 21-10 | El par que cierra puede reutilizar la pata serial del primero si solo cambió el manifest | Acortar la cola de máquina sin tocar la equivalencia. **No se usó**: entre el par 1b y el cierre cambió también el medidor |
| D-T3 | 21-10 | La única suite completa oficial de la construcción es la pata serial del primer par | No correr otra suite de ≈ 50 min aparte |
| D-T4 | 21-10 | VP-E08 usa `timeoutSeconds: 9` en vez de 3 | `powershell.exe` arranca en frío en 2,65–3,25 s en esta máquina: con 3 s el worker moría antes de empezar |
| D-T5 | 22-10 | Los pares corren sin `-Detallado` | El punto 5 de la equivalencia no se puede cumplir en el árbol real (par 1b) |
| D-T6 | 22-10 | El par 1b es el primer par: alimenta `maxSeconds` y fija el 70 % | Sus dos patas fueron verdes con la misma huella (regla B1) |
| D-T7 | 22-10 | El umbral normativo es **0,75**; no se repite el par | La relación comparable es 0,7089 (sin `-Detallado`); regla 2 de §22.3. La equivalencia no se relajó |

## El par de cierre, suite por suite

Duraciones de la pata paralela (líneas de progreso del runner), contra la suite sola de WU03-a. Las 99 salieron
`OK`.

**Las 20 más largas** (Σ 3150,0 s, el 75 % del trabajo):

| # | Suite | Clase | Paralelo (s) | Sola en WU03-a (s) | Cociente |
|---|---|---|---|---|---|
| 1 | `73_ejecucion_de_grafo.py` | motor | 758,8 | 728,8 | 1,04 |
| 2 | `75_runner_paralelo.py` | ventana | 364,3 | — (nueva) | — |
| 3 | `72_motor_de_ejecucion.py` | motor | 263,9 | 218,8 | 1,21 |
| 4 | `63-harness-unico-instalador.ps1` | instalador | 240,9 | 223,5 | 1,08 |
| 5 | `03-instalador.ps1` | instalador | 240,4 | 269,1 | 0,89 |
| 6 | `64_interaccion_humana.py` | parallel | 158,6 | 116,4 | 1,36 |
| 7 | `63_compuerta_del_flujo.py` | ventana | 127,2 | 102,0 | 1,25 |
| 8 | `64_modelo_de_dominio.py` | parallel | 125,4 | 123,5 | 1,02 |
| 9 | `66_integrity_cleanup.py` | parallel | 100,5 | 118,2 | 0,85 |
| 10 | `55_refutacion_atomica.py` | ventana | 89,9 | 68,5 | 1,31 |
| 11 | `70_r11_glob_de_autoridad.py` | ventana | 89,7 | 95,5 | 0,94 |
| 12 | `62-context-bar-consumo-instalador.ps1` | instalador | 87,1 | 58,5 | 1,49 |
| 13 | `74_knowledge_api.py` | parallel | 76,5 | 24,3 | 3,15 |
| 14 | `14-contexto-instalador.ps1` | instalador | 70,9 | 26,1 | 2,72 |
| 15 | `62_estado_del_flujo.py` | parallel | 70,1 | 58,5 | 1,20 |
| 16 | `65_contrato_de_ejecucion.py` | parallel | 66,6 | 71,4 | 0,93 |
| 17 | `57-aceptar-fuentes-instalador.ps1` | instalador | 61,3 | 29,7 | 2,06 |
| 18 | `15_contexto_paso4.py` | parallel | 54,1 | 21,5 | 2,52 |
| 19 | `30-contabilidad-instalador.ps1` | instalador | 52,1 | 24,5 | 2,13 |
| 20 | `64-modelo-de-dominio-instalador.ps1` | instalador | 51,7 | 52,7 | 0,98 |

**Total por clase:**

| Clase | Suites | Paralelo (s) | Sola en WU03-a (s) | Cociente |
|---|---|---|---|---|
| `motor` | 2 | 1022,7 | 947,6 | 1,08 |
| `instalador` | 21 | 1247,0 | 967,6 | 1,29 |
| `ventana` | 4 | 671,1 (306,8 sin `75_runner`) | 266,0 (3) | 1,15 sin `75_runner` |
| `parallel` | 72 | 1259,7 (1258,4 sin `75_manifest`) | 929,6 (71) | 1,35 sin `75_manifest` |
| **Total** | **99** | **4200,5** (3834,9 de las 97 de la baseline) | **3110,8** (97) | **1,23** de las 97 |

- **f ≈ 1,23**: cuánto más tardan las suites cuando corren de a dos (cociente de sumas, ESTIMATED sobre lo
  medido; incluye la sobrecarga de lanzar cada suite en su proceso).
- **Sobrecarga por suite ≈ 1 s** en las triviales: `04_secretos.py` 0,1 → 1,2 s; `16_refutador_contrato.py`
  0,1 → 1,1; `06_reglas.py` 0,2 → 1,1; `08-bitacora.ps1` 0,8 → 1,0.
- **Los dos lugares estuvieron ocupados el 99,5 % del wall** (4200,5 s de trabajo sobre 2 × 2110,4).
- **El orden de lanzamiento** fue el de §13.1: arrancaron primero `73_ejecucion_de_grafo.py` y
  `75_runner_paralelo.py` (las dos con más `maxSeconds`), y las suites cortas quedaron para el final.
- `75_runner_paralelo.py`, el test del propio runner, es la segunda suite más larga: 6 min (VX-24).

## Cambios del manifest

El par 1b alimentó `tests/parallel-manifest.json` (D-T6, regla B1): `maxSeconds = máx(sola de WU03-a, pata
paralela del par 1b)` y `timeoutSeconds` recalculado. El par de cierre no lo realimenta (regla B4), y el manifest
no cambió después de él (mismo hash).

| | Cuántas |
|---|---|
| `maxSeconds` que subieron | 80 |
| Iguales (la sola de WU03-a era mayor) | 17 (entre ellas t73, t72, `03-instalador.ps1`, 66 y 70) |
| Llenadas por primera vez | 2: `75_manifest_paralelo.py` 1,1 s y `75_runner_paralelo.py` 299,1 s |
| `timeoutSeconds` cambiados | solo esas dos, de `null` a 1200; t73 sigue en 2187 y las demás en 1200 |
| Σ `maxSeconds` | 3110,8 → 3629,7 s |

Las subas más grandes: `64_interaccion_humana.py` 116,4 → 131,0; `62-context-bar-consumo-instalador.ps1`
58,5 → 73,1; `38_integridad_de_repositorio.py` 1,3 → 15,8; `35_d8_proteccion_con_token.py` 1,3 → 12,4;
`55_refutacion_atomica.py` 68,5 → 78,0. Ninguna suite cambió de clase.

## Las reglas del protocolo (spec §5.7)

| Regla | Cumplida | Cómo |
|---|---|---|
| B1: solo alimenta `maxSeconds` una corrida verde, con la misma huella y condiciones | sí | El par 1b: exit 0 las dos, `ok == total`, `E3CAD0FB…` ×3, condiciones antes de cada pata |
| B2: el mismo `bash` en las dos patas y `TEMP` nuevos por pata | sí | `Git\bin\bash.exe` en las dos patas y en el encabezado del runner; `tmp-serial` y `tmp-paralelo` nuevos, formato largo los dos |
| B3: la paridad suite sola contra completa, antes de construir y sin veredicto | sí | WU03-a |
| B4: el manifest no cambia después del par que cierra | sí | `8D304154…` en el cierre y al escribir este registro |
| B5: el muestreo de RAM no sobrevive al medidor | sí | Vive en el proceso del medidor, sin proceso aparte |
| B6: en `-SoloCaso`, el grupo de la fila de carga sale de la enumeración | sí | Rojo visto en la construcción (etapa 2) |

## RAM libre

| Par | Pata serial (mínima) | Pata paralela (mínima) |
|---|---|---|
| 1 | 14,00 GB | 14,31 GB |
| 1b | 13,67 GB | 14,10 GB |
| Cierre | 11,55 GB | **3,20 GB** a los 2001,7 s |

El 3,20 GB **no se puede atribuir al runner**: el medidor mide la RAM libre de toda la máquina, había tres
procesos `claude` vivos y al terminar la pata quedaban 5,5 GB libres sin ningún proceso de la corrida vivo. En
los otros dos pares la paralela bajó menos de 1 GB. El piso de RAM no se fijó en 6.1 (VX-28).

## Lo que no se midió

- **N = 3**: no se corrió (D-T1).
- **Ctrl-C real**: no se hizo el smoke manual que prevé la spec (§26); la cancelación se probó con la señal
  inyectable (VP-E19) y el corte del medidor con `Stop-Job` (etapa 8).
- **`-Umbral 0.75` literal**: el medidor no se corrió con ese valor; el cumplimiento se deduce del par de cierre.
  Quien refuta corre VP-E25.
- **El pico de concurrencia por carril**: el medidor no lo calcula (sus líneas de progreso no traen la hora de
  inicio); registra duraciones y llegadas.
- **CPU por proceso**: no se muestreó (no se exige, §5.5).
- **Pares para la fase B** (≥ 5 sobre ≥ 2 huellas, rojos inducidos, stderr inyectado, una corrida matada): no
  son de 6.1.

## Evidencia

- WU03-a: `C:\dev\_respaldos\task6.1\wu03a\` (`condiciones.txt`, `serial-1.meta.txt`, `serial-2.meta.txt`,
  `suites.csv`, `wu03a-manifest-timing.csv`, `wu03a-analisis.md`, `ram.csv`, `restos-tmp.txt`, `huella-*.txt`).
- Par 1: `C:\dev\_respaldos\task6.1\construccion\wu03b-par1\` (`registro.txt`, `comparador.txt`,
  `w3b-par1.txt`, `w3b-par1.meta.txt`).
- Par 1b: `C:\dev\_respaldos\task6.1\construccion\wu03b-par1b\` (`registro.txt`, `comparador.txt`,
  `w3b-par1b.txt`, `serial.txt.gz`, `paralelo.txt.gz`); capturas completas en `C:\t\hpm-261021-223656\`.
- Par de cierre: `C:\dev\_respaldos\task6.1\construccion\wu03b-cierre\` (`registro.txt`, `comparador.txt`,
  `w3b-cierre.txt`, `w3b-cierre.meta.txt`, `serial.txt.gz`, `paralelo.txt.gz`, `pata-serial.json`,
  `lista-final.txt`); capturas completas en `C:\t\hpm-261022-091757\`.
- Cambios del manifest: `C:\dev\_build\t61\cierre\manifest-cambios.csv`; manifest anterior,
  `C:\dev\_build\t61\cierre\manifest.antes.json`.
- Sondas del medidor: `C:\dev\_build\t61\e8\out\` (etapa 8), `C:\dev\_build\t61\e8b\out\` (modo de reuso),
  `C:\dev\_build\t61\cierre\out\` (medidor con `^AVISO`).
- Hashes antes de cada par: `C:\dev\_respaldos\task6.1\construccion\freeze-pre-par1.txt` y
  `freeze-pre-cierre.txt`.
- Registro de la construcción: `C:\dev\_respaldos\task6.1\construccion\registro.md` y
  `aclaraciones-de-construccion.md`.
