# Verificación — Bloque 2 — Context Resolution: de una clave de Jira a un `TaskContext`

**Estado:** cerrado · **Fecha:** 14-09-2026 · **Versión:** 0.17.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 14-09-2026,
en dos pasadas, corriendo la suite completa y mutando el código sobre una copia para comprobar que
cada test podía fallar. La primera pasada dejó un `contradicho` y un `sin sustento`; la segunda,
después de corregirlos, los dio por sostenidos.

**Resultado: 36 escenarios sostenidos, 0 contradichos, 0 sin sustento, 0 leídos. Los 36 con
`rojo visto: si`.**

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Los campos de la tarea salen del issue | sostenido | sí | `19_contexto.py::test_e01_la_tarea_sale_del_issue` |
| E-01b | El ADF de Jira se aplana a texto plano | sostenido | sí | `::test_e01b_el_adf_se_aplana_a_texto` |
| E-02 | Los criterios salen del campo configurado, y no se inventan | sostenido | sí | `::test_e02_los_criterios_no_se_inventan`, las dos mitades |
| E-03 | Sin `jira.issue.read`: código 2, sin una sola llamada | sostenido | sí | `::test_e03_sin_capacidad_no_hay_llamada`, resolvedor y CLI |
| E-04 | Un issue que no existe sale nombrando la clave | sostenido | sí | `::test_e04_un_issue_que_no_existe` |
| E-05 | El padre y los enlaces son referencias, no se siguen | sostenido | sí | `::test_e05_el_padre_y_los_enlaces_son_referencias` |
| E-06 | Con una sola ficha, sus campos entran con su clave | sostenido | sí | `::test_e06_la_ficha_entra_entera` |
| E-07 | Con dos fichas no se elige ninguna | sostenido | sí | `::test_e07_dos_fichas_es_un_conflicto` |
| E-08 | Sin ficha, el hueco dice qué se buscó y dónde | sostenido | sí | `::test_e08_sin_ficha_se_declara_el_hueco` |
| E-09 | El tipo de ficha es configurable, con default | sostenido | sí | `::test_e09_el_tipo_de_ficha_es_configurable`, sobre el JQL |
| E-10 | Sin `jira.issue.search` no se busca, y el resto sigue | sostenido | sí | `::test_e10_sin_busqueda_no_se_busca_la_ficha` |
| E-11 | Los adjuntos entran ordenados y sin duplicados | sostenido | sí | `::test_e11_los_adjuntos_entran_ordenados_y_sin_duplicados` |
| E-12 | Sin `jira.attachment.read` no se baja nada | sostenido | sí | `::test_e12_sin_capacidad_no_se_baja_nada` |
| E-13 | Con markitdown el texto entra; sin él se declara | sostenido | sí | `::test_e13_markitdown_presente_y_ausente`, sin invocarlo |
| E-14 | La clasificación es inferida y se declara | sostenido | sí | `::test_e14_la_clasificacion_es_inferida` |
| E-15 | El recorte se declara en el documento y en los huecos | sostenido | sí | `::test_e15_el_texto_se_recorta_y_se_dice` |
| E-16 | Sin referencia al repo no se busca nada | sostenido | sí | `::test_e16_sin_referencia_no_se_busca_nada`, los dos orígenes |
| E-17 | Solo entran las ramas y MR que nombran la clave | sostenido | sí | `::test_e17_solo_lo_que_nombra_la_clave` |
| E-18 | Cada capacidad de GitLab degrada por su cuenta | sostenido | sí | `::test_e18_cada_capacidad_degrada_por_su_cuenta`, las dos direcciones |
| E-19 | El contexto del código se referencia, no se copia | sostenido | sí | `::test_e19_el_contexto_de_codigo_se_referencia` |
| E-20 | Cada lectura deja su fuente con tipo y momento | sostenido | sí | `::test_e20_cada_lectura_deja_su_fuente` |
| E-21 | Un 401 en el medio degrada su sección | sostenido | sí | `::test_e21_un_fallo_en_el_medio_degrada_su_seccion` |
| E-22 | Con GitLab caído el comando sale con 0 | sostenido | sí | `::test_e22_con_gitlab_caido_el_documento_sale`, contra la CLI |
| E-23 | Lo que no se resolvió sale vacío, nunca por defecto | sostenido | sí | `::test_e23_lo_que_no_se_resolvio_sale_vacio` |
| E-24 | Un token en la descripción no llega al contexto | sostenido | sí | `::test_e24_un_token_en_la_descripcion_no_llega_al_contexto` |
| E-25 | Ninguna ruta de entrada esquiva la limpieza | sostenido | sí | `::test_e25_...` y `::test_e25b_las_dos_rutas_que_se_escapaban` |
| E-26 | El catálogo es el mismo archivo del hook | sostenido | sí | `::test_e26_el_catalogo_es_el_mismo_archivo_del_hook` |
| E-26b | La confianza media se declara y no toca el texto | sostenido | sí | `::test_e26b_la_confianza_media_se_declara...` |
| E-27 | El documento valida contra `task-context/1.0` | sostenido | sí | `::test_e27_el_documento_valida` |
| E-28 | Un schema no soportado falla en vez de pasar | sostenido | sí | `::test_e28_un_schema_no_soportado_falla` |
| E-29 | El hash es el del contenido y se puede recomputar | sostenido | sí | `::test_e29_el_hash_identifica_la_corrida`, tres mutaciones |
| E-30 | La CLI escribe el contexto y lo resume | sostenido | sí | `::test_e30_la_cli_escribe_el_contexto_y_lo_resume`, stdout y stderr |
| E-30b | Una clave que no es clave sale con 2 | sostenido | sí | `::test_e30b_una_clave_que_no_es_clave` |
| E-31 | La segunda corrida pisa y no acumula | sostenido | sí | `::test_e31_la_segunda_corrida_pisa_y_no_acumula` |
| E-32 | `-Update` y `-Uninstall` no borran los contextos | sostenido | sí | `19-contexto-tarea-instalador.ps1` |
| E-33 | Los módulos y el schema quedan instalados | sostenido | sí | `19-contexto-tarea-instalador.ps1`, schema byte a byte |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. En este cambio no hay
> ninguna: cada escenario tuvo su mutación y cada mutación puso en rojo el test de su escenario.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **🔴 E-25 estaba contradicho, y era una fuga de secretos de verdad.** La redacción se hacía campo
   por campo y dos rutas nombradas en la propia spec no estaban: los criterios de aceptación y el
   `title` de la Ficha. El refutador corrió la CLI, leyó el archivo escrito y encontró el token
   adentro. La suite no lo veía porque ningún test configuraba el campo de criterios con texto
   sucio — el hueco era estructural, no un olvido de una aserción.

   **El arreglo no fue agregar dos llamadas.** Redactar en cada lugar donde se arma un campo obliga
   a acordarse una vez por campo, para siempre. La redacción se movió al ensamblador y recorre el
   documento entero. Que era el arreglo correcto se notó enseguida: **al escribir el test apareció
   una tercera fuga que nadie había nombrado —`sources`, donde la referencia de una fuente es el
   nombre de una rama—** y quedó cubierta por existir, no por acordarse.

2. **E-22 estaba sin sustento: el test no probaba lo que decía.** Simulaba "GitLab caído" sacándole
   las capacidades al registro —que es la condición de E-18, no la de este— y nunca corría el
   comando, así que el código de salida, que es la mitad del escenario, no lo medía nadie. Se
   reescribió: registro en `ENABLED` y GitLab contestando 500 en la llamada real.

3. **E-29 no podía fallar, y al arreglarlo apareció un defecto.** El test comparaba un hash contra
   sí mismo. Al escribir la aserción que sí falla —que el hash escrito es el del contenido— se vio
   que `context_id` se escribía **después** de calcular el hash, y `canonico` no lo saca del
   cálculo: el documento cambiaba después de hashearse y su hash dejaba de ser recomputable por
   quien lo lee. Se corrigió el código; el id se escribe antes y no deriva del hash.

4. **Cinco escenarios tenían aserciones incompletas.** E-03 sólo probaba el resolvedor y no la CLI;
   E-06 miraba el tipo de la fuente y no su clave; E-11 enumera cuatro campos y asertaba dos; E-18
   probaba una sola dirección; E-30 no miraba stderr. Los cinco enunciados quedaron **idénticos
   carácter por carácter**: se movieron los tests, no los escenarios.

5. **La prosa de la spec se contradecía con su propio contrato.** E-20 y E-06 decían `meta.sources`
   cuando el schema declara `sources` en la raíz. Corregido en los dos lugares — el segundo lo
   señaló la segunda pasada, que es cuando se ve si una corrección se hizo a medias.

6. **Un test que pasaba sin ejercitar nada, atrapado antes de que lo viera nadie.** El caso del
   nombre de rama con un token pasaba porque, sin ficha, el resolvedor no busca ramas: no había
   rama que limpiar. Se le puso `gitlabProyecto` para que la rama entrara de verdad, y ahí se puso
   rojo — que era el punto.

## Lo que queda abierto, anotado y no escondido

- **Nada quedó contradicho ni sin sustento.** Los dos hallazgos de la primera pasada se corrigieron
  y la segunda los dio por sostenidos, sin tocar el texto de ningún escenario.
- **La garantía de redacción vive en el ensamblador.** Un consumidor futuro que llame a un
  resolvedor sin pasar por `armar` recibe texto sin redactar. Hoy no existe —la CLI siempre
  ensambla— y el Bloque 3 es otro cambio, pero queda anotado en
  `Pendientes/Fix-Harness/PENDIENTES-FH.md`.
- **Los adjuntos quedan crudos en disco.** `.claude/contextos/<CLAVE>-adjuntos/` guarda el archivo
  original, sin pasar por el detector. Es lo que E-13 manda hacer y lo que hace falta para que
  markitdown lo convierta después; el `.gitignore` del harness no cubre ese directorio.
- **Ni la Ficha de Proyecto ni el campo de criterios existen todavía en ningún Jira real.** La
  primera corrida contra el Jira del organismo es lo que puede desmentir las dos suposiciones, y
  está anotada como pendiente.

## Lo que ningún test cubre y se mira con los ojos

- **Que la Ficha de Proyecto se modele así.** Es un concepto que este bloque introduce. Si el
  organismo termina modelándola distinto —un proyecto Jira aparte, un espacio de Confluence— el
  Project Resolver cambia de estrategia, aunque el contrato que produce no.
- **Que los encabezados de la Ficha se llamen como el código espera.** `Objetivos`, `Alcance`,
  `Reglas`, `Arquitectura` salen de partir la descripción, y eso solo lo confirma una ficha real
  escrita por una persona.
- **Que el contexto le sirva a un agente.** Que el documento valide y traiga lo que dice traer está
  probado; que con eso alcance para entender una tarea lo contesta el Bloque 3.
