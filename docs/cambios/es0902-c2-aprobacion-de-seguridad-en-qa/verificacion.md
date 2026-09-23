# Verificación — ES0902 C2: la aprobación de seguridad en QA, atada al artefacto y revalidada por el Anexo V

**Estado:** cerrado · **Fecha:** 23-09-2026 · **Versión:** sin publicar

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 23-09-2026
en **cuatro pases**. El primero, sobre los cincuenta y seis, corrió `python tests/correr.py -k
42_es0902` y la compuerta completa `.\tests\Invoke-Tests.ps1`; los tres siguientes, acotados a lo
que el pase anterior contradijo, corrieron sólo el archivo 42, porque en paralelo se integraba
ES0902 C3 al repositorio. El refutador apretó desde el primer pase la **clase** —algo que puede
decir que no llega ilegible y se pierde—, que es la lección que C1 dejó escrita.

**Resultado: 56 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

## Los veredictos

Todos los tests están en `tests/casos/42_es0902_c2_aprobacion_en_qa.py`.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | La clave es exactamente `ES0902.C2`, en la matriz y en el resultado del check | sostenido | sí | `test_e01_la_clave` |
| E-02 | La única señal es exactamente `securityHomologationPresent`, y el check pregunta por ella | sostenido | sí | `test_e02_la_senal` |
| E-03 | El agente es exactamente `dev-security`, la policy `qa-security-approval-required` y… | sostenido | sí | `test_e03_agente_policy_check` |
| E-04 | Ningún agente, skill ni review nuevos | sostenido | sí | `test_e04_nada_inventado` |
| E-05 | Sin la señal, `APPLICABILITY_UNRESOLVED`, en la matriz y en el check | sostenido | sí | `test_e05_sin_senal` |
| E-06 | Con la señal en falso, `NOT_APPLICABLE`, en la matriz y en el check | sostenido | sí | `test_e06_senal_en_falso` |
| E-07 | Que falte la aprobación no vuelve falsa la aplicabilidad | sostenido | sí | `test_e07_sin_aprobacion_no_es_no_aplica` |
| E-08 | Una aprobación de `dev-security` no aprueba | sostenido | sí | `test_e08_dev_security_no_aprueba` |
| E-09 | Un escaneo limpio no aprueba | sostenido | sí | `test_e09_un_escaneo_no_aprueba` |
| E-10 | Un CI en verde no aprueba | sostenido | sí | `test_e10_un_ci_verde_no_aprueba` |
| E-11 | `READY_TO_REQUEST` no satisface C2, ni como estado de la aprobación ni como resultado… | sostenido | sí | `test_e11_ready_to_request_no_alcanza` |
| E-12 | `G2_THRESHOLD_SATISFIED` solo no satisface C2, y el módulo no mira hallazgos | sostenido | sí | `test_e12_el_umbral_de_g2_no_alcanza` |
| E-13 | Hace falta procedencia externa | sostenido | sí | `test_e13_procedencia_externa` |
| E-14 | Una aprobación oficial en QA sigue | sostenido | sí | `test_e14_qa_aprueba` |
| E-15 | En DEV, `SECURITY_APPROVAL_NOT_IN_QA` | sostenido | sí | `test_e15_dev` |
| E-16 | En HML, `SECURITY_APPROVAL_NOT_IN_QA` | sostenido | sí | `test_e16_hml` |
| E-17 | En PRD, `SECURITY_APPROVAL_NOT_IN_QA`, también en el algoritmo de la regla | sostenido | sí | `test_e17_prd` |
| E-18 | Con el ambiente sin resolver, `SECURITY_APPROVAL_ENVIRONMENT_UNRESOLVED`, en el check… | sostenido | sí | `test_e18_ambiente_sin_resolver` |
| E-19 | Una aprobación de otro proyecto o de otra aplicación es `FAIL` | sostenido | sí | `test_e19_otro_proyecto_falla` |
| E-20 | Con el alcance de la aprobación vacío o hecho de textos vacíos, o sin cubrir el del… | sostenido | sí | `test_e20_alcance_sin_resolver` |
| E-21 | La rama sola no alcanza | sostenido | sí | `test_e21_la_rama_no_alcanza` |
| E-22 | El mismo commit, o el mismo digest, establece `EXACT` | sostenido | sí | `test_e22_identidad_exacta` |
| E-23 | Sin relación resoluble —otro commit y sin change set completo—,… | sostenido | sí | `test_e23_relacion_sin_resolver` |
| E-24 | Una aprobación vieja no se reusa a ciegas | sostenido | sí | `test_e24_una_vieja_no_se_reusa_a_ciegas` |
| E-25 | Desarrollo y más de 20 días | sostenido | sí | `test_e25_desarrollo_y_mas_de_20_dias` |
| E-26 | Más de 20 días sin desarrollo no es motivo | sostenido | sí | `test_e26_los_20_dias_van_con_el_desarrollo` |
| E-27 | Remediación de vulnerabilidades | sostenido | sí | `test_e27_remediacion` |
| E-28 | Incidente de seguridad | sostenido | sí | `test_e28_incidente` |
| E-29 | Cambio de funcionalidad | sostenido | sí | `test_e29_funcionalidad` |
| E-30 | Endpoint agregado o modificado | sostenido | sí | `test_e30_endpoint` |
| E-31 | Parámetro de formulario o API | sostenido | sí | `test_e31_parametros` |
| E-32 | Integración externa o webhook | sostenido | sí | `test_e32_integracion_externa` |
| E-33 | Iframe o embed | sostenido | sí | `test_e33_iframe` |
| E-34 | Script de terceros | sostenido | sí | `test_e34_script_de_terceros` |
| E-35 | CORS, CSP o cookies | sostenido | sí | `test_e35_politica_de_seguridad` |
| E-36 | Roles o permisos | sostenido | sí | `test_e36_roles` |
| E-37 | Dependencia, framework o SDK | sostenido | sí | `test_e37_dependencias` |
| E-38 | Migración de infraestructura | sostenido | sí | `test_e38_infraestructura` |
| E-39 | Protocolo de comunicación | sostenido | sí | `test_e39_protocolo` |
| E-40 | Carga o descarga de archivos | sostenido | sí | `test_e40_archivos` |
| E-41 | Flujo sensible | sostenido | sí | `test_e41_flujo_sensible` |
| E-42 | Flujo de autenticación | sostenido | sí | `test_e42_autenticacion` |
| E-43 | Varios motivos salen todos, cada uno con su evidencia, no un booleano | sostenido | sí | `test_e43_varios_motivos_salen_todos` |
| E-44 | Una categoría ambigua o ausente es `ASSESSMENT_TRIGGER_CLASSIFICATION_UNRESOLVED` | sostenido | sí | `test_e44_clasificacion_ambigua` |
| E-45 | Una clasificación de un modelo no suprime un motivo | sostenido | sí | `test_e45_un_modelo_no_suprime` |
| E-46 | Con evidencia completa y ningún motivo, `REUSE_ALLOWED` | sostenido | sí | `test_e46_reuso_permitido` |
| E-47 | Un assessment parcial no aprueba un release cambiado | sostenido | sí | `test_e47_parcial_no_aprueba_un_release_cambiado` |
| E-48 | Parcial, o sin tipo, sin cobertura explícita | sostenido | sí | `test_e48_parcial_sin_cobertura` |
| E-49 | Parcial con cobertura oficial que nombra al candidato sigue | sostenido | sí | `test_e49_parcial_con_cobertura` |
| E-50 | O2 en `PASS` no es C2 en `PASS` | sostenido | sí | `test_e50_o2_no_es_c2` |
| E-51 | C2 en `PASS` no pone ninguna regla Vu en cumplimiento | sostenido | sí | `test_e51_c2_no_es_vu` |
| E-52 | C2 en `PASS` no es aprobación de despliegue a producción | sostenido | sí | `test_e52_c2_no_es_despliegue` |
| E-53 | Lo consumido sale con su huella `sha256`, su id y su referencia, y la huella cambia si… | sostenido | sí | `test_e53_huella` |
| E-54 | Con la huella de una decisión anterior que no coincide, o una decisión anterior que no… | sostenido | sí | `test_e54_evidencia_cambiada` |
| E-55 | La misma evidencia da el mismo resultado, en cualquier orden | sostenido | sí | `test_e55_determinismo` |
| E-56 | El resultado conserva `ES0902 / 6.2 / §3 / C2` y `ES0901 / 6.3 / Anexo V` por todos… | sostenido | sí | `test_e56_traza_y_unidad` |
> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Los cincuenta y seis llevan
> `sí`: la pasada de mutaciones se corrió entera en la construcción, con `__pycache__` borrado
> antes y después de cada una, y cada corrección de los pases siguientes se volvió a ver en rojo con
> la suya. E-47 no se puso en rojo en la primera pasada —su test no pasaba por la razón que
> declaraba— y se reescribió antes del primer veredicto.

La compuerta, en el último pase que la corrió entera (el primero):

```
.\tests\Invoke-Tests.ps1
  250/250 pasaron (PowerShell)
  28552/28552 pasaron (python)
  28802/28802 pasaron
```

Y el cuarto, sobre el archivo 42 sólo: `282/282`.

## Los cuatro pases

```
pase 1   56 escenarios   E-24, E-26 y E-55 contradichos; seis de la misma clase fuera de la letra
pase 2   9 escenarios    E-13 contradicho
pase 3   E-13 E-24 E-56  E-24 contradicho
pase 4   E-13 E-24 E-56  sostenidos
```

| Pase | Qué encontró | Qué se hizo |
|---|---|---|
| 1 | Una rechazada más nueva con la fecha mal escrita se ordenaba por texto y la vieja aprobaba (E-24). Un `development` no reconocido salteaba los 20 días (E-26). Dos aprobaciones del mismo día se elegían por el orden de la entrada (E-55). Y seis de la misma clase: un O2 de otro alcance, otro commit con el change set vacío, la huella anterior torcida, una cobertura que se contradice, entradas que rompían, la unidad copiando cualquier estado | Todas las fechas del sujeto se leen; `development` por identidad, y otro commit es desarrollo; los empates no se eligen; O2 tiene que ser de este alcance; la huella torcida obliga a reevaluar; la cobertura sigue la regla del artefacto; la unidad sólo proyecta un resultado del check |
| 2 | Un O2 de la aplicación **hermana** del mismo proyecto servía de procedencia, porque se aceptaba cualquier eslabón de la cadena (E-13) | Cuenta la cabeza de la cadena, con su tipo |
| 3 | Una rechazada con el sujeto escrito con un carácter invisible, un acento o otro separador desaparecía (E-24) | Se ensanchó el mecanismo y no la letra: una forma canónica —sin acentos, formato, caja ni separadores— que sólo falla cerrado |
| 4 | —sostenidos— | — |

## Lo que la verificación encontró y no habría encontrado un test verde

1. **Cinco caminos por los que C2 aprobaba lo que tenía que rechazar**: la rechazada más nueva con
   la fecha mal escrita, la rechazada con el sujeto mal escrito, el empate de fechas, el O2 de otro
   alcance o de la aplicación hermana, y el commit nuevo que esquivaba los 20 días declarando que
   no hubo desarrollo. Los tests del constructor armaban siempre el caso bien formado.
2. **Que `1 == True` en Python.** Un `development: 1` pasaba como "hubo desarrollo" o como valor
   reconocido según dónde se mirara; ahora se compara por identidad.
3. **Que la unidad de trabajo es otra puerta de entrada.** Proyectaba cualquier estado, incluso uno
   oficial, y la referencia con el registro adentro.

## Lo que queda abierto, anotado y no escondido

En `Pendientes/Fix-Harness/PENDIENTES-FH.md`:

- **ES0902 C2 cerró con tres restos de su propia clase fuera de la letra**: un homoglifo cirílico en
  el sujeto, la proyección de la unidad filtrada en dos de cinco campos, y un eslabón de O2 que no
  es un diccionario.
- **ES0902 C2 deja como decidió la spec seis elecciones de identidad y vigencia**: un `releaseId`
  solo alcanza para `EXACT`, un cambio con fecha anterior al assessment se ignora, la huella depende
  del orden de las listas, una aprobación de DEV más nueva tapa a una de QA, una decisión anterior
  de otro id se ignora, y una evaluación anterior al assessment sin desarrollo pasa.
- **La contradicción del hotfix en ES0901** (pág. 29 contra el Anexo V).
- **Los registros del proyecto viven en `reglas/`**, que `-Update` sobrescribe: el de C2 es el
  cuarto, y pierde además el registro contra el que se tomó la huella.

## Lo que ningún test cubre y se mira con los ojos

- **Que una aprobación real se pueda escribir en este registro.** Ninguna acta de DGSEI trae hoy
  el `authorityId` del registro de O2 ni un commit o un digest; la primera corrida real con la señal
  en verdadero va a dar `SECURITY_APPROVAL_REQUIRED`, que es el estado correcto.
- **Que los dieciocho motivos del Anexo V se clasifiquen en la práctica.** El resolvedor recibe los
  cambios clasificados; quién los clasifica —un humano, un determinista— es trabajo que nadie hace
  todavía.
