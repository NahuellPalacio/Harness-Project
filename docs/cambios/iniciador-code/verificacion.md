# Verificación — El primer recorrido del código: `dev-iniciador-code`

**Estado:** cerrado · **Fecha:** 21-08-2026, tercera pasada el 30-08-2026 · **Versión:** 0.14.0

Este documento es lo que cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md):
el veredicto por escenario de quien verificó, que no es quien construyó.

**Van tres pasadas de `harness-spec-refuter`.** Las dos primeras, el 21-08-2026: la primera dio 11
sostenidos y 10 sin sustento; en respuesta se atacaron E-10 y E-20 y se corrigió el relato de E-06,
y la segunda —corrida sobre `.\tests\Invoke-Tests.ps1` en 388/388— dejó **13 sostenidos, 0
contradichos, 9 sin sustento**: nada difería de lo que la spec afirma, pero nueve escenarios no
tenían con qué sostenerse, los nueve con sujeto una corrida de un agente con modelo.

**La tercera, el 30-08-2026**, verificó dos cosas nuevas: la firma delegada de ocho de esos nueve
bajo [ADR-0010](../../adr/0010-firma-delegada-de-una-lectura-cuando-son-muchas.md), y el arreglo
del noveno —E-12—, que resultó estar mal marcado y se movió de vuelta a la suite con un test
propio. Corrió `.\tests\Invoke-Tests.ps1` completo (**772/772**), reprodujo el rojo de E-12
mutando `docs/codebase/normativa.md` con backup y restauración verificada por `sha256sum`, y
recontó los `## E-nn` reales de `lectura.md` contra lo que declara su cabecera, en vez de confiar
en el número declarado.

**Resultado: 14 escenarios sostenidos, 8 leídos (delegados), 0 leídos (independientes), 0
contradichos, 0 sin sustento.**

**El cambio cierra.**

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Sin índice y con `desarrollo`, nombra al agente | sostenido | sí | `10_codebase.py::test_e01_avisa_cuando_falta_el_indice` |
| E-02 | Con índice presente, la línea no aparece | sostenido | sí, reproducido | `test_e02_calla_cuando_el_indice_existe` |
| E-03 | Sin `desarrollo` en el lockfile, no aparece | sostenido | sí | `test_e03_calla_sin_desarrollo_en_el_lockfile` |
| E-04 | El aviso agrega exactamente una línea | sostenido | sí, reproducido | `test_e04_el_aviso_agrega_exactamente_una_linea` |
| E-05 | Sale como contexto, nunca como compuerta | sostenido | sí, exclusivo | `test_e05_el_aviso_sale_como_contexto_y_nunca_como_compuerta` |
| E-06 | Una `rutaCodebase` inválida cae al default | sostenido | sí, exclusivo | `test_e06_ruta_invalida_cae_al_default_y_no_se_lleva_el_bloque` |
| E-07 | Terminado un recorrido, existe `indice.md` | leído, delegado | no consta | [`lectura.md`](lectura.md) — Claude (delegado), ADR-0010, 30-08-2026 |
| E-08 | Índice y fichas se corresponden en los dos sentidos | sostenido | sí | `test_e08…` y `test_e08b…` |
| E-09 | Cada ficha tiene sus cuatro secciones | sostenido | sí | `test_e09…` y `test_e09b…` |
| E-10 | Nada escrito por el recorrido matchea un patrón alto | sostenido | sí | Control positivo + salida real |
| E-11 | El recorrido no escribe fuera de `docs/codebase/` | leído, delegado | no consta | [`lectura.md`](lectura.md) |
| E-12 | Lo ignorado por `.gitignore` no produce ficha ni ruta citada | **sostenido** | sí | `test_e12_control_positivo_git_check_ignore_resuelve_la_excepcion` y `test_e12_ninguna_ruta_citada_por_el_recorrido_esta_gitignoreada` |
| E-13 | Un segundo recorrido no duplica fichas | leído, delegado | no consta | [`lectura.md`](lectura.md) |
| E-14 | Una ficha huérfana se reporta y no se borra | leído, delegado | no consta | [`lectura.md`](lectura.md) |
| E-15 | El informe dice cuántas escribió y qué no recorrió | leído, delegado | no consta | [`lectura.md`](lectura.md) |
| E-16 | El informe no contiene código fuente | leído, delegado | no consta | [`lectura.md`](lectura.md) |
| E-17 | Sobre un repo sin código no escribe nada | leído, delegado | no consta | [`lectura.md`](lectura.md) |
| E-18 | El agente queda en `.claude/agents/` | sostenido | sí | `11-codebase-instalador.ps1` |
| E-19 | `harness.config.json` trae `rutaCodebase` | sostenido | sí | `11-codebase-instalador.ps1` |
| E-20 | Sin la clave, el aviso y el check resuelven el default | sostenido | sí, exclusivo | `test_e20…` y `test_e20_el_check…` |
| E-20b | El agente resuelve el mismo default | leído, delegado | no consta | [`lectura.md`](lectura.md) |
| E-21 | `-Uninstall` deja `docs/codebase/` intacto | sostenido | sí | `11-codebase-instalador.ps1` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Aplica a los ocho `leído,
> delegado`: su sujeto es una corrida de un agente con modelo, y eso no se rompe a propósito.

## E-12, el escenario que cambió de grupo dos veces

Nació en la suite, se movió a lectura el 2026-08-21 con un razonamiento que mezclaba dos cosas: que
un check en `PostToolUse` sería caro —cierto— con que ningún mecanismo mecánico era posible —falso—.
`harness-spec-refuter` lo encontró el 30-08-2026, verificando la firma delegada de
`dev-refutador-lee-el-contrato` (un cambio distinto): la condición 4 de ADR-0009 pregunta si el
sujeto tiene forma de test determinista, y la tiene, con la misma técnica que ya usa E-10 sobre este
mismo archivo — correr sobre la salida real y versionada de `docs/codebase/*.md`, después de
escrita, no sobre un fixture y no en cada `PostToolUse`.

El test usa `git check-ignore` y no un grep de patrones sobre `.gitignore`: el patrón
`normativa/fuentes/*` tiene una excepción, `!normativa/fuentes/LEEME.md`, y esa ruta está citada de
verdad en `docs/codebase/normativa.md` — un grep de patrones la marcaría ignorada y estaría mal.
Extrae del texto de cada ficha los spans entre backticks con al menos una `/` —para no levantar
ruido de nombres de archivo sueltos, tipo `dev.py`, que no representan una ruta completa— y corre
`git check-ignore` sobre cada uno desde la raíz del repo. Sobre las 67 rutas reales que hoy citan
las fichas de este repositorio, ninguna está ignorada.

**El rojo se vio dos veces, por dos personas distintas.** Yo lo reproduje agregando una cita a
`normativa/fuentes/ES0901.pdf` (gitignoreada de verdad) en `docs/codebase/normativa.md`, vi caer el
test con el mensaje exacto, y restauré con `md5`/diff verificados. `harness-spec-refuter` repitió la
misma mutación de forma independiente durante esta verificación, con su propio backup y su propio
hash, y obtuvo la misma caída.

`docs/cambios/iniciador-code/spec.md` documenta el cambio de grupo con fecha y motivo, y el texto
original del escenario —"Un archivo ignorado por `.gitignore` no produce ficha ni aparece en el
índice"— no se tocó ni una letra: sólo cambiaron la marca de `verificación: lectura` (retirada), el
`rojo visto` (de `no consta` a `sí`) y la nota explicativa. Ninguna proposición desapareció.
`docs/cambios/iniciador-code/lectura.md` ya no tiene su sección y la cabecera lo anota.

## La firma delegada de los ocho restantes

Firmada el 30-08-2026, `Firmó (delegado): Claude`, con la autorización de Nahue Palacio citada bajo
ADR-0010 y fecha. `harness-spec-refuter` recontó los `## E-nn` reales de `lectura.md` dos veces: la
versión que se firmó tenía 9 pendientes (declarado y recontado por `git diff` contra el commit
anterior), y la de hoy, después de que E-12 salió, tiene 8 — ambos números por encima del umbral de
cinco de ADR-0010, así que la licencia de delegación se sostiene tanto en el momento de la firma
como después. Los ocho `Observado` describen hechos concretos —hashes de commit, listas de archivo,
citas textuales del informe del agente— y no juicios de valor, que es la condición 2 de ADR-0009. El
sujeto de los ocho es, en cada caso, una corrida real de `dev-iniciador-code` con modelo, corrida
sobre `C:\Users\Asus\lecturas-0.14.0\reservas` y `...\manual-operativo`: ninguno tiene forma de test
determinista, así que el techo de lectura está bien puesto para los ocho que quedan.

## Lo que la verificación encontró y no habría encontrado un test verde

1. 🔴 **E-20 no se cubrió en su momento: se volvió a cortar, y la mitad difícil se mudó a E-20b.**
   Hallazgo de la segunda pasada, ya cerrado por el corte declarado: cambió de número y de grupo,
   no de estado, y hoy E-20b cierra por lectura delegada.
2. **El id `E-20b` estuvo pisado por un test más viejo**, liberado renombrando el test que no le
   correspondía. Ya resuelto en la segunda pasada.
3. **La afirmación de exclusividad de E-10 en la spec era falsa** y se corrigió en la spec misma;
   no es un hallazgo de esta pasada.
4. **E-12 estaba mal marcado desde el 2026-08-21**, y nadie lo vio hasta que un refutador,
   verificando otro cambio, aplicó la misma pregunta —¿tiene forma de test determinista?— sobre un
   escenario que se había dado por resuelto. Es la razón de ser de la condición 4 de ADR-0009: la
   marca de lectura no se toma declarada, se juzga si corresponde.
5. **Los ocho restantes no tenían con qué sostenerse hasta ADR-0010**, y ahora cierran por una vía
   rotulada como lo que es, contada aparte de `sostenido` y de `leído independiente`.

## Lo que queda abierto, anotado y no escondido

Nada de este cambio queda abierto. `Pendientes/Fix-Harness/PENDIENTES-FH.md` pierde la entrada de
E-12 —se resolvió, no se parkeó— y lo que había ahí pasa a `docs/versiones/0.14.0.md`.

## Lo que ningún test cubre y se mira con los ojos

Los ocho escenarios firmados delegados —E-07, E-11, E-13, E-14, E-15, E-16, E-17, E-20b— dependen
de que un agente con modelo recorra un repositorio real, y la suite de este repositorio son tests
deterministas y sin red. La evidencia está en [`lectura.md`](lectura.md), firmada bajo ADR-0010.

Y lo que solo confirma una persona abriendo una sesión de verdad: que la línea de `SessionStart`
aparezca en un proyecto con `desarrollo` instalado y sin índice, que se entienda qué sugiere, y que
desaparezca sola después de correr el recorrido.
