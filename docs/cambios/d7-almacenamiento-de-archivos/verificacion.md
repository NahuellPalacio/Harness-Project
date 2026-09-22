# Verificación — D7: los archivos van al storage estándar, el local permanente está prohibido y el temporal se destruye

**Estado:** cerrado · **Fecha:** 21-09-2026 · **Versión:** sin publicar

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 21-09-2026,
en **dos pasadas**, corriendo `python tests/correr.py -k 34_d7` y la compuerta completa
`.\tests\Invoke-Tests.ps1`, y en las dos volvió a correr a mano las proposiciones que los escenarios
afirman en vez de confiar en que el test estuviera verde.

**Resultado: 45 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

La primera pasada rindió **43 sostenidos y 2 contradichos** —E-05 y E-07—, y el cambio no cerró. Los
dos se corrigieron en direcciones distintas y la segunda pasada los sostuvo. Está contado abajo,
porque el número que importa no es el final: es que ninguno de los dos salió de un test en rojo.

## La tabla

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | D7 sigue `CONDITIONAL`, con `dev-backend`, tres policies y tres checks, y la fila tiene exactamente las claves de toda fila de diseño | sostenido | sí | `34_d7`, `test_e01_d7_es_condicional`, más recuento aparte de intersección y unión de claves |
| E-02 | La señal en TRUE hace a D7 aplicable | sostenido | sí | `34_d7`, `test_e02_true_hace_aplicable` |
| E-03 | La señal en FALSE lo deja `NOT_APPLICABLE`, y los tres checks también | sostenido | sí | `34_d7`, `test_e03_false_hace_no_aplicable` |
| E-04 | Sin la señal, `APPLICABILITY_UNRESOLVED` con el nombre de la que falta | sostenido | sí | `34_d7`, `test_e04_sin_senal_no_se_resuelve` |
| E-05 | La ausencia nunca es FALSE por ninguna de las dos clases débiles, y el límite de la etiqueta queda declarado y probado | sostenido | sí, las dos mitades | `34_d7`, `test_e05_la_ausencia_nunca_es_false`, más las cuatro etiquetas corridas a mano |
| E-06 | Las once operaciones sostienen la señal por igual | sostenido | sí | `34_d7`, `test_e06_un_flujo_es_mas_que_una_subida`, los 11 claims difieren en texto |
| E-07 | Ninguna otra señal sustituye: entregada a los checks, `SIGNAL_IDENTITY_MISMATCH` | sostenido | sí | `34_d7`, `test_e07_ninguna_otra_senal_sustituye`, más 13 señales × 3 checks corridas aparte |
| E-08 | D7 resuelve exactamente tres policies | sostenido | sí | `34_d7`, `test_e08_tres_policies` |
| E-09 | D7 resuelve exactamente tres checks | sostenido | sí | `34_d7`, `test_e09_tres_checks` |
| E-10 | Los seis ids son los de la matriz, con su tipo y su regla | sostenido | sí | `34_d7`, `test_e10_los_ids_son_los_de_la_matriz` |
| E-11 | D7 no crea ninguna referencia a skill, y siguen siendo 27 | sostenido | sí | `34_d7`, `test_e11_d7_no_crea_ninguna_skill`, más verificación en disco de los 27 directorios |
| E-12 | Las tres obligaciones se evalúan independientemente, en los seis cruces | sostenido | sí | `34_d7`, `test_e12_las_tres_obligaciones_son_independientes` |
| E-13 | Identidad, contrato y traza dan `PASS`, con blancos incluidos | sostenido | sí | `34_d7`, `test_e13_un_flujo_con_evidencia_pasa` |
| E-14 | Ninguna de las seis clases inertes, sola, da `PASS` | sostenido | sí | `34_d7`, `test_e14_lo_inerte_no_pasa`, una por una |
| E-15 | `OTHER_REMOTE_STORAGE` no satisface el estándar en silencio | sostenido | sí | `34_d7`, `test_e15_otro_repositorio_remoto_no_satisface` |
| E-16 | Sin identidad, `STANDARD_STORAGE_PROVIDER_UNRESOLVED` | sostenido | sí | `34_d7`, `test_e16_sin_identidad_no_se_inventa`, siete formas del hueco |
| E-17 | Con identidad y sin contrato, `STORAGE_INTEGRATION_CONTRACT_MISSING` | sostenido | sí | `34_d7`, `test_e17_sin_contrato_es_otro_hueco` |
| E-18 | El cliente existe y el camino gobernado lo esquiva: `FAIL` | sostenido | sí | `34_d7`, `test_e18_el_cliente_existe_y_el_camino_lo_esquiva` |
| E-19 | Ningún artefacto de D7 lleva el mecanismo ni una duración | sostenido | sí, las tres mitades | `34_d7`, `test_e19_ningun_artefacto_lleva_el_mecanismo`: 10 textos limpios, 49 fugas crudas, 22 textos legítimos |
| E-20 | El local permanente da `FAIL` | sostenido | sí | `34_d7`, `test_e20_el_local_permanente_falla` |
| E-21 | El nombre del path no clasifica un ciclo de vida | sostenido | sí | `34_d7`, `test_e21_el_nombre_del_path_no_clasifica` |
| E-22 | Un temporal no es persistente por ser local, y se deriva | sostenido | sí | `34_d7`, `test_e22_un_temporal_no_es_persistente_por_ser_local` |
| E-23 | Un volumen montado no esquiva la prohibición | sostenido | sí | `34_d7`, `test_e23_un_volumen_montado_no_esquiva_la_prohibicion` |
| E-24 | Los siete datos del ciclo de vida, y `UNRESOLVED` contra `PARTIAL` | sostenido | sí | `34_d7`, `test_e24_los_siete_datos_del_ciclo_de_vida` |
| E-25 | Un temporal con limpieza atada se evalúa y no desaparece | sostenido | sí | `34_d7`, `test_e25_un_temporal_con_limpieza_atada_se_evalua` |
| E-26 | La limpieza del camino feliz no alcanza | sostenido | sí | `34_d7`, `test_e26_la_limpieza_del_camino_feliz_no_alcanza`, más el cuarto camino condicional |
| E-27 | El cron periódico solo da `FAIL` | sostenido | sí | `34_d7`, `test_e27_el_cron_solo_no_pasa` |
| E-28 | El reinicio del contenedor solo da `FAIL` | sostenido | sí | `34_d7`, `test_e28_el_reinicio_solo_no_pasa` |
| E-29 | El TTL, el arranque y lo manual solos dan `FAIL` | sostenido | sí | `34_d7`, `test_e29_el_ttl_el_arranque_y_lo_manual_no_pasan`, las cinco demoradas más `NONE` |
| E-30 | Cobertura completa da `PASS` y la técnica no se exige | sostenido | sí | `34_d7`, `test_e30_la_cobertura_completa_pasa_y_la_tecnica_no_se_exige`, seis técnicas y ninguna |
| E-31 | "Inmediato" no se define con un número | sostenido | sí | `34_d7`, `test_e31_inmediato_no_se_define_con_un_numero`, sin constantes numéricas salvo las dos citas |
| E-32 | Inventario incompleto: `FILE_FLOW_COVERAGE_UNRESOLVED` en los tres | sostenido | sí | `34_d7`, `test_e32_el_inventario_incompleto_no_se_resuelve`, siete formas |
| E-33 | Sin temporales tras clasificación completa, `NOT_APPLICABLE` | sostenido | sí | `34_d7`, `test_e33_sin_temporales_la_limpieza_no_aplica` |
| E-34 | Un temporal solo no falla el storage y no se le pide la identidad | sostenido | sí | `34_d7`, `test_e34_un_temporal_solo_no_falla_el_storage` |
| E-35 | Persistentes y temporales se evalúan por separado | sostenido | sí | `34_d7`, `test_e35_persistentes_y_temporales_se_evaluan_por_separado` |
| E-36 | La clasificación de flujos no es aplicabilidad, con la clase entrando en la señal | sostenido | sí | `34_d7`, `test_e36_la_clasificacion_no_es_aplicabilidad`, las seis clases |
| E-37 | Un flujo que cumple no tapa otro que no, ni un inventario incompleto | sostenido | sí | `34_d7`, `test_e37_un_flujo_que_cumple_no_tapa_otro_que_no` |
| E-38 | S3 es protocolo y no proveedor | sostenido | sí | `34_d7`, `test_e38_s3_es_protocolo_y_no_proveedor` |
| E-39 | Profundidad y concentración medidas se exponen y no dejan `PASS` | sostenido | sí | `34_d7`, `test_e39_lo_medido_que_se_aparta_se_expone`, 21 y 100001 literales |
| E-40 | Lo no medido queda `NOT_MEASURED` y no baja el estado | sostenido | sí | `34_d7`, `test_e40_lo_no_medido_no_se_inventa` |
| E-41 | La unidad propaga las tres policies y los tres checks, y la forma vieja anda | sostenido | sí | `34_d7`, `test_e41_la_unidad_propaga_los_seis_controles` |
| E-42 | Los seis controles dejan de ser un hueco: 24 declarados, sin archivos sueltos | sostenido | sí | `34_d7`, `test_e42_los_controles_dejan_de_ser_un_hueco`, más recuento aparte 12+10+2 |
| E-43 | Todo resultado conserva `ES0901 / 6.3 / 7.1 / D7` | sostenido | sí | `34_d7`, `test_e43_todo_resultado_conserva_la_traza`, todos los caminos de los tres checks |
| E-44 | Los estados declarados se alcanzan y sólo `PASS` aprueba | sostenido | sí | `34_d7`, `test_e44_los_estados_existen_y_solo_pasa_uno`, 9/8/9 |
| E-45 | La ejecución rutea por el registro sin crear una skill | sostenido | sí | `34_d7`, `test_e45_la_ejecucion_rutea_sin_crear_una_skill` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide ADR-0006:
> un test que nunca se vio fallar no probó que puede fallar. Los 45 escenarios de este cambio llevan
> `sí`: la pasada de mutaciones fue de 66 mutaciones y cada escenario se vio en rojo por al menos
> una.

Compuerta en la que se rindieron los veredictos:

```
python tests/correr.py -k 34_d7             ->  1134/1134
.\tests\Invoke-Tests.ps1                    ->  9327/9327, exit 0
                                                (34_d7: 1134 · 250 PowerShell · 9077 python)
```

## Lo que la verificación encontró y no habría encontrado un test verde

Los dos hallazgos de la primera pasada **no salieron de un test en rojo**. Los 945 tests estaban
verdes y la compuerta cerraba en 9138. Salieron de correr a mano la proposición que el escenario
afirma, y en los dos casos el test verde probaba una proposición vecina y más débil, elegida —sin
querer— porque su entrada era la que el sistema no podía fallar.

1. **E-07 era un defecto del código, y el peor de los dos.** `flujos.valor_de_senal` leía `value` y
   no miraba `signalId`. Pasándole `frontendPresent` en TRUE, `storage-backend-compliance` y
   `persistent-local-file-storage` daban **`PASS`** y `temporary-file-cleanup` daba
   `NOT_APPLICABLE`, y los tres publicaban `"signal": "fileHandlingPresent"` al lado del resultado:
   cumplimiento de D7 atribuido a una señal que nunca llegó. El test no lo veía porque le pasaba
   `None`, que es **entrada idéntica** a la de E-04 — la cláusula distintiva de E-07, *"con
   cualquiera de las otras en TRUE"*, no llegaba nunca a un check.

   Es el mismo defecto que D5 ya había cerrado un nivel más abajo, en su derivación
   —`address-normalization-integration.py:275`, *"la derivación mentía de dónde salió"*—, y acá
   estaba un nivel más arriba: en la puerta común de las tres obligaciones. Se arregló el código:
   `valor_de_senal` compara el `signalId`, `aplicabilidad` publica `SIGNAL_IDENTITY_MISMATCH` con su
   detalle, y el mapa `{id: resuelta}` con el que las señales viajan dentro de la unidad se lee por
   id. La refutación se repitió sobre las 13 señales × 3 checks: ningún estado distinto de
   `APPLICABILITY_UNRESOLVED`, ningún motivo distinto, y la señal propia sigue resolviendo.

2. **E-05 era una afirmación más ancha que el mecanismo.** El escenario prometía que las tres frases
   de ausencia nunca bajan la señal a FALSE. El test las envolvía en `AGENT_STATEMENT`, que está en
   `senales.FUENTES_DEBILES`, así que `_por_clase` las saltea **antes de mirar el `claim`**: el texto
   de la frase no lo leía nadie, y lo que el test probaba era "una fuente débil no sostiene ningún
   valor" —cierto para cualquier claim, de ausencia o no—. Con una fuente de la lista, la misma frase
   apaga D7 entera.

   Se arregló la spec, no el código, y la decisión está en `## Riesgos conocidos`: cerrarlo pide
   exigir completitud de alcance declarada para todo FALSE, que hoy está cerrado **sólo para D5** y
   sigue abierto para las otras quince reglas condicionales. Construirlo para D7 sola habría dejado
   la matriz diciendo `NOT_APPLICABLE` y el check diciendo `APPLICABILITY_UNRESOLVED` sobre el mismo
   plan.

   🔴 Un escenario reescrito después de un `contradicho` es el movimiento por el que este repositorio
   ya se quemó, así que lo que separa esto de un recorte está clavado: **ninguna proposición
   desapareció**. La mitad que cae quedó afirmada en positivo y en verde —`TASK_CONTEXT` con la misma
   frase apaga la regla—, el límite tiene que estar escrito en `docs/normativa-7.1.md` para que el
   test pase, y el escenario no se movió de número ni de grupo. El día que alguien construya la
   compuerta, **este test se pone en rojo y hay que venir a tocarlo**.

3. **Dos mitades sostenidas pero vacías**, que un test verde nunca reporta. En E-01, la mitad
   histórica *"sin que este cambio la edite"* no la alcanza ningún test y la matriz está sin trackear
   en git, así que no había línea de base: se cambió por un invariante estructural —las claves de la
   fila de D7 contra la intersección de las claves de toda fila de diseño—, con su guarda
   anti-vacuidad explícita, porque la intersección es estrictamente menor que la unión. En E-36, la
   resolución se recalculaba idéntica en las seis vueltas del `for`: ahora la clase entra en el
   `claim` de la evidencia y las seis vueltas tienen seis insumos distintos.

4. **El rojo del árbol al empezar no era del cambio.** `33_bases_de_datos` reportaba ocho fallas
   sobre 2667 tests antes de tocar nada, y era **bytecode viejo** en `tests/casos/__pycache__`: el
   `.pyc` conservaba tamaño y mtime, así que corría una versión anterior del archivo de tests. La
   primera edición al archivo lo invalidó y el grupo pasó a 3247 tests en verde. Es la misma trampa
   que ya estaba anotada para la pasada de mutaciones, esta vez sobre un archivo de tests y no sobre
   un módulo.

## Lo que queda abierto, anotado y no escondido

- **`controles/` no llega a un proyecto instalado.** Con D7 son **veinticuatro** controles que
  declaran `INSTALLED` y que fuera de este repositorio serían `CONTROL_FILE_MISSING`. Es el ítem 2 de
  `Pendientes/Fix-Harness/PENDIENTES-FH.md`, ya actualizado con el número nuevo, con su composición
  —doce policies, diez checks, dos reviews— y con el dato nuevo: `controles/lib/` tampoco se copia,
  así que los tres checks de D7 no podrían ni importar su módulo compartido afuera de acá. D7 es el
  salto más grande que tuvo ese pendiente.
- **La compuerta de completitud de alcance para un FALSE.** Abierta para las quince reglas
  condicionales que no son D5, dicha en `docs/normativa-7.1.md` y en `## Riesgos conocidos` de la
  spec, y afirmada en verde por E-05 en las dos direcciones.
- **La identidad del storage estándar no se puede resolver en ningún proyecto todavía.** El estándar
  nombra el protocolo y no el repositorio. Cualquier corrida real de una aplicación que persiste va a
  salir `STANDARD_STORAGE_PROVIDER_UNRESOLVED`, que es lo correcto y también significa que ese camino
  no se ejercita de punta a punta hasta que alguien consiga ese dato.
- **No hay eje `REAL`/`MOCKED`.** Una traza mockeada de un camino de persistencia se ve igual que una
  real. D6 distingue las dos; D7 no, porque el pedido no lo pide. Está en los riesgos de la spec.
- **La evidencia la junta nadie todavía.** Los tres checks reciben un inventario de flujos ya
  clasificado y no hay productor que lo arme desde un repositorio. Es la misma deuda de G1, G2 y
  D1 a D6.

## Lo que ningún test cubre y se mira con los ojos

- **Que una aplicación real mande sus adjuntos al repositorio estándar del GCBA.** Lo que estos tres
  checks verifican es que la evidencia de esa corrida exista, esté atada al build y no sea de una
  clase inerte. La corrida la hace una persona o una skill, y este cambio no abre, sube ni borra un
  archivo.
- **Que las tres policies se lean como obligaciones y no como configuración.** Son el artefacto que
  un modelo carga como instrucciones, y si alguna se lee como un instructivo de integración, el día
  que alguien busque el endpoint adentro lo va a esperar encontrar.
- **Que la asimetría de los tres "no hay nada que verificar" se entienda al leerla.** Dos
  obligaciones condicionales contestan `NOT_APPLICABLE` sin sujeto y la prohibición contesta `PASS`.
  Está argumentada en la spec y en `docs/normativa-7.1.md`; si a quien lee un plan le parece un
  error, el que está mal es el texto, no el código.
