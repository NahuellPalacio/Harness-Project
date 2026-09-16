# Verificación — Bloque 3 — El núcleo de orquestación

**Estado:** cerrado · **Fecha:** 16-09-2026 · **Versión:** 0.18.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 16-09-2026,
en dos pasadas, corriendo la suite completa y reproduciendo a mano lo que los tests no cubrían. La
primera pasada dejó **cuatro contradichos**; la segunda, después de corregirlos, los dio por
sostenidos.

**Resultado: 36 escenarios sostenidos, 0 contradichos, 0 sin sustento, 0 leídos. Los 36 con
`rojo visto: si`.**

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | El plan valida contra `orchestration-plan/1.0` | sostenido | sí | `20_orquestacion.py::test_e01_el_plan_valida` |
| E-02 | El estado se calcula, y el hueco le gana a la aprobación | sostenido | sí | `::test_e02_el_estado_se_calcula` |
| E-03 | Una dependencia inexistente no se escribe | sostenido | sí | `::test_e03_una_dependencia_que_no_existe` |
| E-04 | Un ciclo se rechaza nombrando las unidades | sostenido | sí | `::test_e04_un_ciclo_de_dependencias` |
| E-05 | El orden es topológico y determinista | sostenido | sí | `::test_e05_el_orden_es_topologico_y_determinista` |
| E-06 | Una capacidad del registro sale disponible | sostenido | sí | `::test_e06_una_capacidad_del_registro` |
| E-07 | Una capacidad local del runtime también | sostenido | sí | `::test_e07_una_capacidad_local_del_runtime` |
| E-08 | Lo que no está en ninguna fuente es hueco | sostenido | sí | `::test_e08_una_capacidad_que_no_esta_en_ninguna_fuente` |
| E-09 | El hueco se deriva y la tool nace temporal | sostenido | sí | `::test_e09_el_hueco_se_deriva` |
| E-10 | `DISABLED` es faltante, no disponible | sostenido | sí | `::test_e10_una_capacidad_deshabilitada_es_faltante` |
| E-11 | Un agente sin `.md` es hueco, y la unidad lo dice | sostenido | sí | `::test_e11_un_agente_declarado_sin_md` |
| E-12 | Una skill declarada sin archivo es hueco | sostenido | sí | `::test_e12_una_skill_declarada_sin_archivo` |
| E-13 | La existencia la dice el disco | sostenido | sí | `::test_e13_la_existencia_la_dice_el_disco` |
| E-14 | El ruteo por dominio no trae a todos | sostenido | sí | `::test_e14_el_ruteo_no_trae_a_todos` |
| E-15 | Sin señales, el tier más barato | sostenido | sí | `::test_e15_sin_senales_el_tier_mas_barato` |
| E-16 | Las señales suben el tier | sostenido | sí | `::test_e16_las_senales_suben_el_tier` |
| E-17 | El motivo nombra las señales | sostenido | sí | `::test_e17_el_motivo_nombra_las_senales` |
| E-18 | La escalada es explícita y no saltea | sostenido | sí | `::test_e18_la_escalada_es_explicita_y_no_saltea` |
| E-19 | Un perfil sin modelo es un hueco | sostenido | sí | `::test_e19_un_perfil_sin_modelo_es_un_hueco` |
| E-20 | Los baratos se autoaprueban | sostenido | sí | `::test_e20_los_baratos_se_autoaprueban` |
| E-21 | `premium` detiene el plan | sostenido | sí | `::test_e21_premium_detiene_el_plan` |
| E-22 | La solicitud trae la alternativa más barata | sostenido | sí | `::test_e22_la_solicitud_trae_la_alternativa` |
| E-23 | El presupuesto se gasta | sostenido | sí | `::test_e23_el_presupuesto_se_gasta` |
| E-24 | La política sale de la configuración | sostenido | sí | `::test_e24_la_politica_sale_de_la_configuracion` |
| E-25 | Las 26 reglas, con id, texto y página | sostenido | sí | `::test_e25_las_reglas_estan` |
| E-25b | El texto de las 26 es el del extracto | sostenido | sí | `::test_e25b_las_reglas_salen_del_extracto_citable` |
| E-26 | Una regla sin condiciones no se cita | sostenido | sí | `::test_e26_una_regla_sin_condiciones_no_se_cita` |
| E-27 | Una regla con condición se cita | sostenido | sí | `::test_e27_una_regla_con_condicion_se_cita` |
| E-28 | El plan declara la matriz pendiente | sostenido | sí | `::test_e28_el_plan_declara_la_matriz_pendiente` |
| E-29 | Cada unidad lleva lo suyo; un dominio ajeno no pasa | sostenido | sí | `::test_e29_cada_unidad_lleva_lo_suyo` y `::test_e29b_...` |
| E-30 | Ningún token llega al plan, venga de donde venga | sostenido | sí | `::test_e30_ningun_token_llega_al_plan` |
| E-31 | Sin contexto, código 2 y nada escrito | sostenido | sí | `::test_e31_sin_contexto_no_hay_plan` |
| E-32 | La plantilla trae lo que hace falta | sostenido | sí | `::test_e32_la_plantilla_trae_lo_que_hace_falta` |
| E-33 | Replanificar sube la versión y guarda el motivo | sostenido | sí | `::test_e33_replanificar_...` y `::test_e33b_...` |
| E-34 | Los módulos, el schema y las reglas se instalan | sostenido | sí | `20-orquestacion-instalador.ps1` |
| E-35 | `-Update` y `-Uninstall` no borran los planes | sostenido | sí | `20-orquestacion-instalador.ps1` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. En este cambio no hay
> ninguna.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **🔴 E-30 estaba contradicho y era una fuga de secretos de verdad.** Un PAT de GitLab escrito con
   `--motivo` quedaba **en claro** en `.claude/planes/<CLAVE>.json`. Dos causas: `_limpiar` recorría
   cuatro campos **por nombre** y `planHistory` no estaba en la lista, y además `replanificar` corría
   **después** de la limpieza, así que el motivo no existía cuando se limpiaba.

   **Y es exactamente el error que el Bloque 2 había cometido y corregido un bloque antes.** Ahí la
   redacción era campo por campo, se escapaban tres rutas, y la corrección fue recorrer el documento
   entero. Un bloque después se escribió de nuevo una lista de cuatro campos. Peor: **la primera
   corrección fue otra lista**, de dieciséis nombres, y el refutador lo señaló en la segunda pasada —
   *"la lección está enunciada; la estructura sigue siendo una lista de nombres"*. Recién ahí
   `_limpiar` pasó a recorrer las claves del documento, con un test que mete una sección que no
   existía y comprueba que queda cubierta por existir.

2. **E-29 estaba contradicho, y la mitad peligrosa nadie la había mirado.** Un dominio fuera de la
   tabla caía a un default que se llevaba las cuatro categorías con `omitted` vacío, indistinguible
   de un dominio con derecho a todo. Alcanzaba con que el agente escribiera un dominio inventado — y
   **tres dominios del propio `roster.json` estaban en ese caso**: `tooling`, `orchestration` y
   `refutation`. Ahora tienen su fila, un dominio desconocido levanta, y un test recorre el roster y
   falla si alguno queda sin fila.

   La otra mitad era del escenario: decía "una unidad de backend no lleva los criterios de
   accesibilidad", y eso no se puede cumplir filtrando por dominio — los criterios de aceptación son
   una lista plana de la tarea, sin marca de disciplina. El texto se corrigió y **quedó pidiendo más
   que antes**: "un dominio que nadie declaró no arma plan" no estaba escrito en ninguna parte.

3. **E-11 estaba contradicho por dónde vivía el dato.** El hueco lo decía el plan —en `warnings` y en
   `agents[].exists`— y la unidad no. Importa porque un especialista recibe **su unidad suelta**: el
   aviso estaba tres niveles más arriba de donde se lee. Se agregó `agentExists` a la unidad y al
   contrato.

4. **E-25b estaba contradicho y el test era la mitad del problema.** Comprobaba el puntero al
   extracto, la versión y **una** ancla de 37 caracteres; el escenario dice "el texto de cada regla".
   El refutador comparó las 26 y encontró dos paráfrasis; al escribir la comparación completa
   aparecieron dos omisiones más — `P1` había perdido "(por ejemplo, conectores de base de datos
   usados por un ORM)" y `M3` "(skill transfer)".

5. **La prosa de la spec afirmaba dos cosas falsas.** Que el presupuesto preautorizado era "la única
   forma" de saltear la compuerta —poner `premium` en `autoApprove` también lo hace, sin tocar el
   contador— y la frase de los criterios de accesibilidad, que quedó viva en una sección después de
   declararse incumplible en otra. Las dos corregidas; la segunda la señaló el refutador en la
   pasada final.

6. **Un residuo que se cerró en vez de dejarse anotado.** La validación de dominio corría sobre el de
   cada unidad y no sobre la lista `domains` del plan: una propuesta podía declarar un dominio
   inventado y tener todas sus unidades en otro. El refutador lo dictó sostenido y lo dejó escrito
   como decisión; se cerró igual, porque un plan que declara dos cosas distintas es un plan que
   después nadie sabe leer.

7. **La tanda de mutaciones se colgó un día entero y dejó el árbol mutado.** La mutación de E-04
   —sacarle al orden topológico el guardia de ciclos— deja el `while` sin condición de salida. El
   subproceso nunca terminó, el `finally` que restaura nunca corrió, y `plan.py` quedó con un
   `if False:` en el árbol durante veinticuatro horas. Es la misma trampa que `CLAUDE.md` ya declara
   para `03-instalador.ps1`, en otra forma: **un `finally` no sobrevive a un proceso que no
   termina.** El script de mutaciones tiene timeout desde entonces, y una mutación que cuelga la
   suite se reporta roja — que es lo correcto: el test nunca se pone verde.

8. **La tanda encontró un escenario que no podía fallar.** Sacarle a `estado_de` la rama de los
   huecos de capacidad dejaba la suite verde, porque cada hueco deja además una unidad `BLOCKED` y
   la tercera rama la atrapaba. El caso que las distingue —una unidad que pide una capacidad que no
   existe **y** además necesita aprobación— no estaba escrito. Al escribirlo apareció una decisión
   que el código ya tomaba y nadie había declarado: **gana el hueco**, porque ninguna aprobación
   arregla una capacidad que falta.

## Lo que queda abierto, anotado y no escondido

- **Nada quedó contradicho ni sin sustento.**
- **El agente `dev-orchestrator` no se corrió nunca.** Se escribió su archivo y nadie lo invocó. Que
  produzca una propuesta razonable a partir de un `TaskContext` real es una corrida de un modelo y se
  verifica por lectura, en otro cambio y con ADR-0009 adelante.
- **Los siete especialistas y la skill `dev-data` siguen declarados sin archivo.** Es el alcance
  declarado: su existencia se valida contra la matriz normativa de §7.1, que no está construida.
- **Las 26 reglas están sin clasificar**, así que `applicableStandards` sale vacío en todo plan real.
  El plan lo declara en cada corrida.
- **`dev-refutador.md` y los dos `hu-*.md` de `analisis` incumplen ADR-0011** desde el día que se
  escribió la regla. Anotado en `Pendientes/Fix-Harness/PENDIENTES-FH.md`.

## Lo que ningún test cubre y se mira con los ojos

- **Que las señales de complejidad que declare el agente sean honestas.** Un agente que declare todo
  `ambiguity` consigue `premium` para cualquier cosa. La defensa es la compuerta humana, no el
  scoring — pero que la compuerta alcance lo dice una persona mirando qué le piden aprobar.
- **Que el plan sirva para ejecutar.** Que valide y sea consistente está probado; que con eso alcance
  para repartir trabajo lo contesta el bloque siguiente.
- **Que los tiers correspondan a modelos reales.** Ningún perfil tiene modelo declarado todavía: el
  primero que configure uno es el que va a descubrir si el mapeo tiene sentido.
