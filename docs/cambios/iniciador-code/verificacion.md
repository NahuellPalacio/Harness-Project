# Verificación — El primer recorrido del código: `dev-iniciador-code`

**Estado:** en curso · **Fecha:** 21-08-2026 · **Versión:** sin cerrar (`VERSION` sigue en 0.13.0)

Este documento es lo que cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md):
el veredicto por escenario de quien verificó, que no es quien construyó. Los emitió
`harness-spec-refuter` el 21-08-2026, corriendo `.\tests\Invoke-Tests.ps1` —**374/374 en verde**,
126 PowerShell y 248 Python— más comprobaciones propias sobre el `docs/codebase/` real de este
repositorio. Se lo invocó sin la versión de los hechos de quien construyó: sin decirle qué
escenarios se esperaban sostenidos ni qué se había encontrado.

**Resultado: 11 escenarios sostenidos, 0 contradichos, 10 sin sustento.**

🔴 **El cambio no cierra.** No hay nada contradicho —ningún comportamiento difiere de lo que la
spec afirma— pero diez escenarios quedaron sin forma de sostenerse.

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Sin índice y con `desarrollo`, nombra al agente | sostenido | sí | `10_codebase.py::test_e01…` — afirma además que es una sola línea |
| E-02 | Con índice presente, la línea no aparece | sostenido | sí | `10_codebase.py::test_e02…` — re-comprobado a mano sobre un repo git real |
| E-03 | Sin `desarrollo` en el lockfile, no aparece | sostenido | sí | `10_codebase.py::test_e03…` — verifica que el resto del bloque siga saliendo |
| E-04 | El aviso agrega exactamente una línea | sostenido | sí | `10_codebase.py::test_e04…` — el refutador midió el peor caso por su cuenta |
| E-05 | Sale como contexto, nunca como compuerta | sostenido | sí | `10_codebase.py::test_e05…` — mira la forma del JSON, no el texto |
| E-06 | Una `rutaCodebase` inválida cae al default | sostenido | sí | `10_codebase.py::test_e06…` — el refutador reprodujo el rojo él mismo |
| E-07 | Terminado un recorrido, existe `indice.md` | **sin sustento** | no consta | Ningún test lo nombra. El artefacto está en el árbol, y eso no prueba quién lo produjo |
| E-08 | Índice y fichas se corresponden en los dos sentidos | sostenido | sí | `test_e08…` y `test_e08b…`, más el check corrido contra los 14 archivos reales: 0 hallazgos |
| E-09 | Cada ficha tiene sus cuatro secciones | sostenido | sí | `test_e09…` y `test_e09b…`, más las 13 fichas reales |
| E-10 | Nada escrito matchea un patrón de confianza alta | **sin sustento** | no consta | Hay test, pero **su sujeto no es el del escenario**: escanea fixtures escritos a mano |
| E-11 | El recorrido no escribe fuera de `docs/codebase/` | **sin sustento** | no consta | Ningún test lo nombra, y nada lo hace cumplir |
| E-12 | Lo ignorado por `.gitignore` no produce ficha | **sin sustento** | no consta | Ningún test lo nombra desde que salió de la suite el 21-08-2026 |
| E-13 | Un segundo recorrido no duplica fichas | **sin sustento** | no consta | Ningún test lo nombra; requiere un segundo recorrido |
| E-14 | Una ficha huérfana se reporta y no se borra | **sin sustento** | no consta | Ningún test lo nombra, y nada impide borrar |
| E-15 | El informe dice cuántas escribió y qué no recorrió | **sin sustento** | no consta | Ningún test lo nombra; el informe no queda persistido |
| E-16 | El informe no contiene código fuente | **sin sustento** | no consta | Ídem E-15 |
| E-17 | Sobre un repo sin código no escribe nada | **sin sustento** | no consta | Ningún test lo nombra |
| E-18 | El agente queda en `.claude/agents/` | sostenido | sí | `11-codebase-instalador.ps1` |
| E-19 | `harness.config.json` trae `rutaCodebase` | sostenido | sí | `11-codebase-instalador.ps1` — compara el valor, no la presencia |
| E-20 | Sin la clave, **el recorrido y el aviso** usan el default | **sin sustento** | sí | El test cubre **la mitad**: prueba el aviso, no el recorrido |
| E-21 | `-Uninstall` deja `docs/codebase/` intacto | sostenido | sí | `11-codebase-instalador.ps1`, con su contraparte puesta |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar.

🔴 **E-20 es el caso que mejor muestra para qué sirve la marca al revés.** Lleva `rojo visto: si` y
aun así quedó `sin sustento`: la mitad que tiene test está bien hecha y vista en rojo, y la otra
mitad —que el **recorrido** también resuelva el default— no la prueba nadie. Una marca puede ser
cierta sobre el test que existe y no decir nada sobre el escenario completo.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-10 tiene un test que por diseño no puede fallar.** El escenario habla de los archivos
   *escritos por el recorrido*; el test escanea tres fichas de fixture escritas a mano por quien
   construyó, sobre un corpus donde la propia spec declara que nunca se va a meter un secreto. La
   guarda contra el catálogo vacío está bien puesta y no alcanza: el sujeto del test no es el
   sujeto del escenario.

2. **E-06 no es una corrección, es una sustitución, y la spec la cuenta al revés de como pasó.** El
   E-06 que se especificó antes de construir desapareció; lo que hoy lleva ese número es el
   escenario que nació el 21-08-2026, durante la construcción, en `fdfb726`. La spec lo presenta
   como que E-06 absorbió a E-06b, y la dirección real es la inversa: **el que sobrevivió es el
   nuevo**. El reemplazo es más fuerte que el original y el original era genuinamente vacuo —el
   refutador reprodujo el rojo él mismo— así que no hubo aflojamiento. Pero el relato de la spec
   no coincide con lo que ocurrió, y eso es exactamente lo que un refutador tiene que decir.

3. **E-20 no figura en la sección «Cómo se verifica» de la spec**, ni en el grupo de la suite ni en
   el de lectura. Es el único de los 21. Un escenario que no está asignado a ninguna vía de
   verificación es el que más fácil se da por cubierto.

4. **Las tres invariantes del agente no las hace cumplir nada.** No escribir fuera de
   `docs/codebase/`, no borrar, no devolver código: viven en la prosa del prompt. El agente lleva
   `PowerShell` entre sus herramientas y el harness no tiene ningún hook que lo limite. Es una
   decisión libre —ningún escenario pide lo contrario— pero es **la razón de fondo** por la que
   E-11, E-14 y E-16 no tienen forma de verificarse sin una persona leyendo.

5. **El commit del recorrido mezcla lo que escribió el agente con lo que escribió la persona.**
   `dd9f5bb` trae `docs/codebase/` y además `PENDIENTES-FH.md` y `recorrido-real.md`. Desde el
   repositorio no hay forma de distinguir una cosa de la otra, que es justo lo que E-11 necesitaría.

6. **La corrección de E-04 es honesta y deja un agujero.** El refutador midió el peor caso por su
   cuenta: 13 líneas sin el aviso, 14 con él, contra un presupuesto declarado de 12. Confirma que
   el escenario original ya era falso por una razón anterior a este cambio. Pero al pasar de un
   techo absoluto a un delta, **desaparece la única cota sobre el tamaño total de la salida**.

## Lo que queda abierto, anotado y no escondido

Todo lo de abajo va a `Pendientes/Fix-Harness/PENDIENTES-FH.md`, que es donde se resuelve:

- **Los diez `sin sustento`**, con su motivo por escenario, que es esta misma tabla.
- **E-10 y E-20**, que son los dos que sí se pueden cerrar sin esperar nada: el primero necesita un
  test cuyo sujeto sea lo que el recorrido escribe, o un escenario reescrito; el segundo, cubrir la
  mitad que falta o partirse en dos.
- **E-06 contado al revés en la spec.** No cambia el veredicto y sí el registro: se corrige el
  texto de la spec para que diga lo que pasó.
- **El presupuesto de `SessionStart`**, ya anotado bajo *«`SessionStart` declares a 12-line budget
  it already exceeds»* — el refutador verificó que la entrada existe.
- **`aporta` decorativo** y **`generar-testigo.ps1` inejecutable**, los dos hallazgos que salieron
  de este cambio sin ser de este cambio.

## Lo que ningún test cubre y se mira con los ojos

Los cinco escenarios que dependen de que un agente con modelo recorra un repositorio real —E-07,
E-11, E-12, E-15, E-16— y que la suite no puede tocar porque es determinista y sin red. La
evidencia de haberlos leído está en [`recorrido-real.md`](recorrido-real.md), con el costo medido y
las observaciones. **Esa evidencia no los convierte en `sostenido`**: fue leída por quien
construyó, y el refutador la deja donde está.

Y lo que solo confirma una persona abriendo una sesión de verdad: que la línea de `SessionStart`
aparezca en un proyecto con `desarrollo` instalado y sin índice, que se entienda qué está
sugiriendo, y que desaparezca sola después de correr el recorrido.
