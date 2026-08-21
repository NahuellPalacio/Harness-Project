# Verificación — El primer recorrido del código: `dev-iniciador-code`

**Estado:** en curso · **Fecha:** 21-08-2026 · **Versión:** sin cerrar (`VERSION` sigue en 0.13.0)

Este documento es lo que cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md):
el veredicto por escenario de quien verificó, que no es quien construyó.

**Van dos pasadas de `harness-spec-refuter`, las dos el 21-08-2026.** La primera dio 11 sostenidos y
10 sin sustento; en respuesta se atacaron E-10 y E-20 y se corrigió el relato de E-06. Lo que sigue
es **la segunda**, corrida sobre `.\tests\Invoke-Tests.ps1` → **388/388 en verde** (126 PowerShell +
262 Python), con todos los rojos declarados reproducidos sobre una copia del repositorio.

**Resultado: 13 escenarios sostenidos, 0 contradichos, 9 sin sustento.**

🔴 **El cambio no cierra.** Nada quedó contradicho —ningún comportamiento difiere de lo que la spec
afirma— y aun así nueve escenarios no tienen con qué sostenerse. Uno de los dos que se atacaron
**no se cubrió: se volvió a cortar**, y eso está abajo con nombre y apellido.

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Sin índice y con `desarrollo`, nombra al agente | sostenido | sí | `10_codebase.py::test_e01…` |
| E-02 | Con índice presente, la línea no aparece | sostenido | sí, reproducido | `test_e02…` — rojo reproducido rompiendo el default |
| E-03 | Sin `desarrollo` en el lockfile, no aparece | sostenido | sí | `test_e03…` |
| E-04 | El aviso agrega exactamente una línea | sostenido | sí, reproducido | `test_e04…` — delta 0 en vez de 1 |
| E-05 | Sale como contexto, nunca como compuerta | sostenido | sí, exclusivo | `test_e05…` — 261/262, falla solo E-05 |
| E-06 | Una `rutaCodebase` inválida cae al default | sostenido | sí, exclusivo | `test_e06…` — sin la guarda, `TypeError` y se pierde el bloque |
| E-07 | Terminado un recorrido, existe `indice.md` | **sin sustento** | no consta | Ningún test lo nombra. Nadie invoca al agente desde la suite |
| E-08 | Índice y fichas se corresponden en los dos sentidos | sostenido | sí | `test_e08…` y `test_e08b…` |
| E-09 | Cada ficha tiene sus cuatro secciones | sostenido | sí | `test_e09…` y `test_e09b…` |
| E-10 | Nada escrito por el recorrido matchea un patrón alto | sostenido | sí | Control positivo + snapshot real. **Con reparos, ver 3 y 4** |
| E-11 | El recorrido no escribe fuera de `docs/codebase/` | **sin sustento** | no consta | Ningún test lo nombra; nada lo hace cumplir |
| E-12 | Lo ignorado por `.gitignore` no produce ficha | **sin sustento** | no consta | Sin test desde que salió de la suite |
| E-13 | Un segundo recorrido no duplica fichas | **sin sustento** | no consta | Requiere un segundo recorrido |
| E-14 | Una ficha huérfana se reporta y no se borra | **sin sustento** | no consta | Ningún test lo nombra; nada impide borrar |
| E-15 | El informe dice cuántas escribió y qué no recorrió | **sin sustento** | no consta | El informe no queda persistido |
| E-16 | El informe no contiene código fuente | **sin sustento** | no consta | Ídem E-15 |
| E-17 | Sobre un repo sin código no escribe nada | **sin sustento** | no consta | Ningún test lo nombra |
| E-18 | El agente queda en `.claude/agents/` | sostenido | sí | `11-codebase-instalador.ps1` |
| E-19 | `harness.config.json` trae `rutaCodebase` | sostenido | sí | `11-codebase-instalador.ps1` — compara el valor |
| E-20 | Sin la clave, el aviso y el check resuelven el default | sostenido | sí, exclusivo | `test_e20…` y `test_e20_el_check…` — **tal como quedó escrito hoy, ver 1** |
| E-20b | El agente resuelve el mismo default | **sin sustento** | no consta | **El test que lleva el id prueba otra cosa, ver 2** |
| E-21 | `-Uninstall` deja `docs/codebase/` intacto | sostenido | sí | `11-codebase-instalador.ps1`, con su contraparte |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar.

## Lo que la verificación encontró y no habría encontrado un test verde

1. 🔴 **E-20 no se cubrió: se volvió a cortar, y la mitad difícil se mudó.** El E-20 original decía
   **el recorrido y el aviso**. El aviso ya tenía test; el recorrido no tenía nada, y por eso quedó
   `sin sustento`. El E-20 de hoy dice **el aviso y el check** —el check nunca fue parte del
   escenario— y el recorrido salió y se fue a E-20b, asignado al grupo de lectura, donde no hay que
   probar nada. **La proposición que hizo fallar a E-20 la primera vez sigue sin tener quien la
   sostenga: cambió de número y de grupo, no de estado.** El trabajo sobre el check es real y tiene
   rojo propio exclusivo, pero cubre algo que E-20 no pedía.

2. **El id `E-20b` está pisado, y el test que lo lleva prueba lo contrario.**
   `test_e20b_con_la_clave_respeta_la_ruta_declarada` existe desde `fdfb726`, **antes de que E-20b
   fuera un escenario**: su premisa es **con** la clave y su sujeto es el hook. El E-20b de la spec
   dice **sin** la clave y su sujeto es el agente. Quien greppee `E-20b` encuentra tres
   afirmaciones verdes que no dicen nada del escenario. Un test que nombra un id prueba que una
   cadena matcheó.

3. **El rojo exclusivo que declara E-10 es falso.** La spec dice *"neutralizar `buscar_secreto`
   hace fallar este escenario y ninguno más"*. Corrido: la suite Python cae a **185/193** — también
   rompe `04_secretos.py` y `02_hook_contrato.py::test_deny_con_secreto_alto`. El rojo existe y es
   real; **la exclusividad no**. No cambia el veredicto y sí lo que vale la afirmación.

4. **E-10 quedó bien, y sostiene menos de lo que la frase sugiere.** El sujeto ahora sí es salida
   del recorrido y el control positivo saca lo vacuo —las dos cosas verificadas, incluida una
   credencial sintética plantada en una copia para ver la mitad negativa en rojo—. Pero corre sobre
   un **snapshot congelado** de 14 archivos: es una guarda de regresión, no dice nada sobre
   recorridos que todavía no se corrieron. Y que esos 14 sean salida del agente **sin editar**
   sigue apoyándose en prosa: `dd9f5bb` los trajo mezclados con lo que escribió la persona.

5. **El test del check no reproduce la premisa del escenario.** E-20 dice *"con
   `harness.config.json` **preexistente** y sin la clave"*; el test llama al check con
   `config=None`, que en producción significa **que el archivo no existe**. Hoy da igual —las dos
   ramas caen en el mismo `.get()`— así que no degrada el veredicto, pero no ejercita la premisa
   que el escenario nombra.

6. **Los ocho restantes no se movieron y siguen teniendo una sola causa.** E-07 y E-11 a E-17: nada
   hace cumplir las tres invariantes del agente. `recorrido-real.md` sigue siendo evidencia leída
   por quien construyó y no los convierte en `sostenido`.

7. **Lo que se corrigió bien, y se dice:** el relato de E-06 ahora cuenta la sustitución en la
   dirección en que ocurrió, y los números de `CHANGELOG.md`, la nota de versión y el mapa
   —388 = 126 + 262— coinciden exactamente con lo que imprimió la suite.

## Lo que queda abierto, anotado y no escondido

Todo va a `Pendientes/Fix-Harness/PENDIENTES-FH.md`:

- **E-20, la mitad que se mudó.** Es el hallazgo con más filo de esta pasada y no se resuelve
  escribiendo: o el recorrido tiene con qué verificarse, o el escenario dice que esa mitad se lee y
  no se prueba. Lo que no vale es que el corte la haga desaparecer.
- **El id `E-20b` pisado**, que se arregla renombrando un test y no se hizo para no meter trabajo
  nuevo debajo de un veredicto recién emitido.
- **La afirmación de exclusividad de E-10 en la spec**, que es falsa y hay que corregir.
- **Los nueve `sin sustento`**, con su motivo por escenario, que es esta misma tabla.
- **Las tres invariantes que no hace cumplir nada**, ya anotadas, que son la causa de ocho de los
  nueve.

## Lo que ningún test cubre y se mira con los ojos

Los escenarios que dependen de que un agente con modelo recorra un repositorio real —E-07, E-11,
E-12, E-15, E-16, y ahora E-20b— y que la suite no puede tocar porque es determinista y sin red. La
evidencia de haberlos leído está en [`recorrido-real.md`](recorrido-real.md). **Esa evidencia no los
convierte en `sostenido`**: fue leída por quien construyó.

Y lo que solo confirma una persona abriendo una sesión de verdad: que la línea de `SessionStart`
aparezca en un proyecto con `desarrollo` instalado y sin índice, que se entienda qué sugiere, y que
desaparezca sola después de correr el recorrido.
