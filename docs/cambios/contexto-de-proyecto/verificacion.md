# Verificación — El contexto del proyecto como contrato: `project-context.json`

**Estado:** cerrado · **Fecha:** 24-08-2026, lectura firmada el 30-08-2026 · **Versión:** 0.14.0

Este documento es lo que cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md):
el veredicto por escenario de quien verificó, que no es quien construyó.

**Van tres pasadas de `harness-spec-refuter`.** Las dos primeras, el 24-08-2026: la primera corrió
sobre `.\tests\Invoke-Tests.ps1` → **554/554 en verde**, y dio 25 sostenidos, 0 contradichos y 3 sin
sustento: E-07, E-12b y E-20. Los dos primeros se atacaron tocando **únicamente**
`tests/casos/13_contexto.py` —ningún archivo de producción cambió, y el refutador lo comprobó—.
La segunda corrió sobre **558/558 en verde** y dejó 27 sostenidos, 0 contradichos, 1 sin sustento
(E-20, por falta de lectura). **La tercera, el 30-08-2026**, verificó la firma de
[`lectura.md`](lectura.md) —`Leyó: Nahue Palacio`— contra el `project-context.json` real de un
recorrido sobre `C:\Users\Asus\lecturas-0.14.0\reservas` y contra el código de ese repositorio.

**Resultado: 27 escenarios sostenidos, 1 leído (independiente), 0 contradichos, 0 sin sustento.**

**El cambio cierra.** Nada quedó contradicho, y E-20 pasó a `leído` con una lectura que cumple las
cuatro condiciones de [ADR-0009](../../adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md).

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Sin fichas no escribe nada, lo dice y sale 0 | sostenido | sí | `13_contexto.py::test_e01…` — las tres proposiciones |
| E-02 | El archivo escrito valida contra el schema | sostenido | sí | `test_e02…` — sobre el archivo en disco, no el doc en memoria |
| E-03 | Dos corridas difieren sólo en `generated_at` | sostenido | sí | `test_e03…` — igualdad JSON completa, más el hash quieto |
| E-04 | El `context_hash` recalculado da lo mismo | sostenido | sí | `test_e04…` |
| E-05 | `meta.repo_revision` es el `HEAD` del repositorio | sostenido | sí | `test_e05…` — contra el `HEAD` real del repo descartable |
| E-06 | Sin repositorio git no escribe y dice por qué | sostenido | sí | `test_e06…` — código 1 + nada escrito + `repo_revision` en stderr |
| E-07 | Un `required` que falta: no escribe, sale ≠ 0 y lo nombra | sostenido | sí | `test_e07…` — unidad **y** punta a punta sobre el bin de mentira |
| E-07b | `enum` y `pattern` también se verifican | sostenido | sí | `test_e07b…` — las dos construcciones existen en el schema real |
| E-08 | Una construcción no soportada falla y la nombra | sostenido | sí | `test_e08…` — y controla que el schema real pase |
| E-08b | Y el script entero sale con código 2 | sostenido | sí | `test_e08b…` — código 2, distinto del 1 de E-07 |
| E-09 | Un componente por ficha, una arista por par | sostenido | sí | `test_e09…` — las mismas cifras que reporta `mapa-codigo.py` |
| E-10 | Una ficha huérfana viaja en `missing[]` | sostenido | sí | `test_e10…` |
| E-11 | Cada ficha produce una entrada en `sources[]` | sostenido | sí | `test_e11…` — `revision`, `status` y cada `source_ref` resolviendo |
| E-11b | El `type` de una fuente describe su `location` | sostenido | sí | `test_e11b…` — seis casos sobre `_tipo_de_fuente(location, ficha)` |
| E-11c | Un bullet de prosa entra entero | sostenido | sí | `test_e11c…` — los dos modos sobre el mismo bullet |
| E-12 | `proyecto.md` no es componente ni nodo | sostenido | sí | `test_e12…` — las dos mitades: componentes y nodos del mapa |
| E-12b | Y sin embargo alimenta los cinco destinos | sostenido | sí | `test_e12b…` — perfil, stack, entrypoints, integraciones y preguntas |
| E-13 | Sin `proyecto.md` el hueco se declara | sostenido | sí | `test_e13…` |
| E-13b | Los cinco bloques sin modelar viajan nombrados | sostenido | sí | `test_e13b…` — uno por aserción |
| E-14 | `proyecto.md` no dispara hallazgos del check | sostenido | sí | `test_e14…` — la ficha y el índice |
| E-15 | El `mapa.html` sale byte a byte igual | sostenido | sí | `test_e15…` — compara bytes, no longitud |
| E-15b | El script no toca el mapa ni las fichas | sostenido | sí | `test_e15b…` — cinco archivos snapshotados |
| E-16 | Con índice y sin contrato, `SessionStart` lo nombra | sostenido | sí | `test_e16…` — y con los dos puestos, ninguna marca |
| E-16b | Sin `desarrollo` en el lockfile, ninguna línea | sostenido | sí | `test_e16b…` — más la fixture de `10_codebase.py`, re-verificada |
| E-17 | El bloque agrega a lo sumo una línea | sostenido | sí | `test_e17…` — cuatro combinaciones, sin rama sin ejercitar |
| E-18 | El schema se reparte y figura en el lockfile | sostenido | sí | `14-contexto-instalador.ps1` — 11/11, con `-Update` y `-Uninstall` |
| E-19 | El contrato versionado no lleva secretos | sostenido | sí | `test_e19…` — con su control positivo, corrido primero |
| E-20 | Un recorrido real describe el proyecto y no lo inventa | leído, independiente | no consta | [`lectura.md`](lectura.md) — Nahue Palacio, 30-08-2026 |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar.

## Lo que la verificación encontró y no habría encontrado un test verde

La suite estaba en **554/554** cuando empezó la primera pasada. Los dos hallazgos son de test, no de
construcción: el código hacía lo que la spec dice, y nadie lo estaba comprobando.

1. **E-07 afirmaba tres cosas y el test probaba una.** El test ejercitaba `validar()` —la función—
   y daba por cubiertas las otras dos proposiciones del escenario: que el script **no escribe** y
   que **sale distinto de 0**. La rama de `main()` que las implementa
   (`contexto-armar.py:747-753`) no la tocaba ningún test de la suite. Es exactamente la distinción
   que la propia spec había elevado a escenario aparte en E-08b —*"no alcanza con que la función
   levante"*— y ahí E-07 no tenía compañero.

   Cerrado con un `required` inventado sobre el bin descartable que E-08b ya armaba. 🔴 El rojo
   exclusivo: neutralizado el `if errores:` de `main()`, caen las tres aserciones nuevas y las tres
   viejas quedan verdes.

2. **E-12b nombraba cinco destinos y el test aseguraba cuatro.** `architecture.external_integrations`
   no tenía ni una aserción en toda la suite, y la fixture **sí** trae el dato
   —`Integraciones: proveedor de pagos sandbox`—. Si el campo dejaba de poblarse, la suite seguía
   verde; y el contrato versionado de este repositorio tampoco lo habría revelado, porque su
   `proyecto.md` declara la lista vacía.

   Cerrado con una línea. 🔴 El rojo: emitiendo `[]`, cae esa aserción y ninguna otra.

📌 **Los dos son el mismo error y ya tiene precedente en esta fábrica:** un escenario que habla de
dos cosas con test para una sola. Es lo que dejó `sin sustento` a E-20 de `iniciador-code`.

## E-20, firmada el 30-08-2026 — y una imprecisión que se anota, no se esconde

`lectura.md` se firmó `Leyó: Nahue Palacio`, sobre un recorrido real de `dev-iniciador-code` contra
`C:\Users\Asus\lecturas-0.14.0\reservas`. `harness-spec-refuter` verificó las cuatro condiciones de
ADR-0009 y contrastó el `Observado` contra el `project-context.json` real y el código: los tres
archivos que nombra (`calendario.tsx`, `reservas.ts`, `cobros.py`) existen tal cual, y
`lifecycle_stage: unknown` coincide con lo declarado.

🔴 **Una imprecisión, no descalificante.** El `Observado` dice que la tecnología "coincide con
`package.json`", pero **Express y React no figuran ahí** —ni en `dependencies` ni en
`devDependencies`—; se importan en tres archivos (`servidor.ts`, `reservas.ts`, `espacios.ts`) y el
propio `project-context.json` ya lo señala como pregunta abierta. E-20 define invención como *"un
framework declarado que no aparece en ningún manifiesto **ni** import"*: aparecen en imports, así
que no están inventados, pero la frase de la lectura sobrestató lo que el manifiesto dice. No se
edita la firma después del hecho —es la observación real de quien la firmó—; queda anotado acá.

## Lo que quedaba abierto, y cómo se cerró

**E-20 era lo único, y ya tiene lectura.** El escenario estaba marcado `· verificación: lectura`
desde que se escribió —el directorio del cambio tenía un solo archivo, `spec.md`, cuando se marcó,
y el texto del escenario no se movió—, y el refutador juzgó la marca merecida las dos veces que la
revisó.

Esta lectura se sumaba a las nueve de [`iniciador-code`](../iniciador-code/lectura.md) y a las
cuatro de [`mapa-de-nodos`](../mapa-de-nodos/lectura.md). Las nueve de `iniciador-code` se firmaron
el 30-08-2026 bajo la firma delegada de
[ADR-0010](../../adr/0010-firma-delegada-de-una-lectura-cuando-son-muchas.md) —ver su propio
`verificacion.md`—; las cuatro de `mapa-de-nodos` siguen diferidas por decisión de Nahue, del
22-08-2026 y ratificada el 28-08-2026 — ver [`docs/versiones/0.14.0.md`](../../versiones/0.14.0.md).

## Lo que ningún test cubre y se mira con los ojos

**Que el contrato describa el proyecto que recorrió.** Es E-20 y es todo lo que hay en esta
categoría: correr `dev-iniciador-code` sobre un repositorio real, abrir el `project-context.json`
que dejó y contrastar `project_profile.purpose` y `technology` contra lo que efectivamente hay en el
repositorio.

🔴 Lo que se escribe es **qué se observó**, no si estaba bien. *"El `purpose` dice `plataforma de
reservas` y el repo tiene `src/api/reservas/`"* es una observación; *"cumple"* no es nada. Un
escenario que no se pudo observar se deja vacío y se dice por qué.
