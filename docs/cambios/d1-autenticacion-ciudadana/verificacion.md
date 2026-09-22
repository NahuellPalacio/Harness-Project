# Verificación — D1: la primera regla condicional que necesita una señal de verdad

**Estado:** cerrado · **Fecha:** 19-09-2026 · **Versión:** sin publicar

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 19-09-2026,
en dos pasadas, corriendo `.\tests\Invoke-Tests.ps1` y `python tests/correr.py -k 26_d1`, y
sondeando por mutación los tres escenarios que se le pidió mirar con desconfianza. La primera pasada
dejó **un sin sustento** —E-28—; la segunda, después de reforzar la aserción, lo dio por sostenido.

**Resultado: 31 escenarios sostenidos, 0 contradichos, 0 sin sustento, 0 leídos. Los 31 con
`rojo visto: si`.**

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | `D1` es `CONDITIONAL` con una sola señal y su fila no cambió | sostenido | sí, de módulo | `26_d1_autenticacion_ciudadana.py::test_e01_d1_es_condicional` |
| E-02 | El schema de una señal valida y entra en el subconjunto soportado | sostenido | sí, específico | `::test_e02_el_contrato_de_una_senal` |
| E-03 | `citizenFacing = TRUE` deja `D1` aplicable | sostenido | sí, específico | `::test_e03_true_hace_aplicable` |
| E-04 | `citizenFacing = FALSE` deja `D1` fuera | sostenido | sí, de módulo | `::test_e04_false_hace_no_aplicable` |
| E-05 | Sin señal, `D1` queda sin resolver con la que falta escrita | sostenido | sí, de módulo | `::test_e05_sin_senal_queda_sin_resolver` |
| E-06 | Lo ausente nunca se convierte en `FALSE`, por cuatro caminos | sostenido | sí, específico | `::test_e06_lo_ausente_nunca_es_falso` |
| E-07 | El resultado conserva sus referencias de evidencia | sostenido | sí, específico | `::test_e07_la_senal_conserva_su_evidencia` |
| E-08 | Afirmar `TRUE` o `FALSE` sin evidencia no afirma | sostenido | sí, de módulo | `::test_e08_afirmar_sin_evidencia_no_afirma` |
| E-09 | Dos evidencias que se contradicen dan `SIGNAL_CONFLICT` | sostenido | sí, específico | `::test_e09_dos_evidencias_que_se_contradicen` |
| E-10 | Lo interpretado no pisa lo estructurado | sostenido | sí, específico | `::test_e10_lo_interpretado_no_pisa_lo_estructurado` |
| E-11 | Una señal que la matriz no declara se rechaza | sostenido | sí, específico | `::test_e11_una_senal_que_la_matriz_no_declara` |
| E-12 | La abstracción no es de `citizenFacing`: tres señales, un camino | sostenido | sí, específico | `::test_e12_la_abstraccion_no_es_de_citizen_facing` |
| E-13 | Los booleanos viejos siguen funcionando | sostenido | sí, específico | `::test_e13_los_booleanos_viejos_siguen` |
| E-14 | Flujo ciudadano con el mecanismo del GCBA: `PASS` | sostenido | sí, específico | `::test_e14_mecanismo_del_gcba_pasa` |
| E-15 | Credenciales propias del ciudadano: `FAIL` | sostenido | sí, específico | `::test_e15_credenciales_propias_falla` |
| E-16 | Evidencia incompleta del proveedor: `PARTIAL`, y no aprueba | sostenido | sí, específico | `::test_e16_evidencia_incompleta_es_parcial` |
| E-17 | Aplicación interna: `NOT_APPLICABLE` | sostenido | sí, específico | `::test_e17_app_interna_no_aplica` |
| E-18 | Señal sin resolver: `APPLICABILITY_UNRESOLVED` y no evalúa | sostenido | sí, específico | `::test_e18_senal_sin_resolver_no_evalua` |
| E-19 | Lo institucional no satisface D1 | sostenido | sí, las dos mitades | `::test_e19_lo_institucional_no_satisface` |
| E-20 | Una dependencia de OIDC no alcanza | sostenido | sí, las dos mitades | `::test_e20_una_dependencia_oidc_no_alcanza` |
| E-21 | La afirmación de un agente, sola, no alcanza | sostenido | sí, de módulo | `::test_e21_la_afirmacion_de_un_agente_no_alcanza` |
| E-22 | Evidencia de otra aplicación o de otro ambiente no sostiene | sostenido | sí, específico | `::test_e22_evidencia_de_otro_sistema_no_sostiene` |
| E-23 | De los cinco estados, `PASS` es el único que aprueba | sostenido | sí, de módulo | `::test_e23_solo_pass_aprueba`, y las corridas reales de E-15 a E-21 |
| E-24 | D1 no valida la delegación de credenciales: eso es D2 | sostenido | sí, específico | `::test_e24_d1_no_es_d2` |
| E-25 | Sin `dev-miba`, los controles de D1 existen igual | sostenido | sí, específico | `::test_e25_sin_dev_miba_los_controles_existen` |
| E-26 | La remediación declara el hueco y no hace cumplir a D1 | sostenido | sí, específico | `::test_e26_la_remediacion_declara_el_hueco` |
| E-27 | D1 nunca crea `dev-miba` | sostenido | sí, específico | `::test_e27_d1_no_crea_dev_miba` |
| E-28 | Los artefactos de D1 no inventan internos de miBA | sostenido | sí, las dos mitades | `::test_e28_no_se_inventan_internos_de_miba` |
| E-29 | La unidad lleva el valor, el estado y la evidencia de la señal | sostenido | sí, de módulo | `::test_e29_la_unidad_lleva_la_senal` |
| E-30 | Los controles dejan de faltar sin tocar la fila de la matriz | sostenido | sí, específico | `::test_e30_los_controles_dejan_de_faltar` |
| E-31 | La tupla `ES0901 / 6.3 / 7.1 / D1` se conserva | sostenido | sí, específico | `::test_e31_la_traza_se_conserva` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Los 31 escenarios de este
> cambio se vieron en rojo con 29 mutaciones deliberadas sobre ocho archivos, cada una revertida.

## E-28, el escenario que la primera pasada dejó sin sustento

El escenario afirma seis clases de internos de miBA que los artefactos de D1 no pueden traer:
client ids, claims, redirect URIs, endpoints, URLs de proveedor y configuración por ambiente. Los
nueve patrones de la primera versión patrullaban las que se escriben como código. El refutador lo
sondeó inyectando fugas verosímiles:

```
client id (forma codigo)   clientId: portal-tramites-prd                -> ROJO
URL de proveedor           issuer: https://id.miba.gob.ar               -> ROJO
discovery                  GET /.well-known/openid-configuration        -> ROJO
claim (tabla de mapeo)     | cuil | documento del ciudadano |           -> PASA VERDE
claims (bloque yaml)       claims:\n  sub: ...                          -> PASA VERDE
config por ambiente        DEV: miba-dev  UAT: miba-uat  PRD: miba-prod -> PASA VERDE
endpoint sin URL           token endpoint: /protocol/.../token          -> PASA VERDE
redirect uri (kebab)       redirect-uri: /callback                      -> PASA VERDE
```

Cinco fugas entraban en verde, y tres de ellas eran clases que el escenario nombra.

**La causa.** Los propios artefactos nombran esas palabras **en prosa para negarlas** —*"It does not
name client identifiers, claims, redirect URIs, logout behaviour, token endpoints, registration
procedures or environment-specific provider values"*—, así que un patrón literal `claims` se habría
puesto rojo contra el descargo. En vez de resolver esa tensión, la lista se recortó a las formas de
código.

**La decisión: el escenario no se movió.** No se achicó el texto de E-28 a lo que el test
verificaba, que era la salida barata. Se subió la verificación:

1. Cuatro patrones anclados a principio de línea, que distinguen un dato de una mención en prosa:
   `^\s*claims\s*:`, `^\s*(sub|preferred_username|given_name|family_name|email|cuil|documento)\s*:`,
   `^.*\bendpoints?\s*:` y `^\s*(DEV|UAT|HML|PRD)\s*:`. Más `redirect-uri` en kebab.
2. Una segunda mitad en el caso: ocho fugas inyectadas en el texto real de la policy, exigiendo que
   cada una lo ponga rojo. Es lo que impide que E-28 vuelva a patrullar sólo lo que alguien se
   acordó de escribir.

Las dos mitades se sondearon por mutación, en los dos sentidos: sacar los patrones nuevos deja sin
atrapar las cuatro fugas de forma de dato, y sacar los ocho viejos deja sin atrapar las otras
cuatro. Ninguna fuga se atrapa de rebote.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-28 pasaba en verde patrullando la mitad de lo que afirmaba.** El test corría, no fallaba
   nunca, y tres de las seis clases del escenario no tenían patrón. Es exactamente el riesgo
   residual que nombra ADR-0006 —*una spec escrita para pasar el check*— del lado del test: una
   aserción que se lee severa y comprueba menos de lo que dice.
2. **El riesgo estructural de la segunda mitad.** La aserción es
   `any(re.search(p, base + fuga) for p in PROHIBIDOS)`: si el texto base ya matcheara algún patrón,
   `any()` daría verdadero para cualquier fuga y las ocho aserciones serían decorado. El refutador
   comprobó que la base no matchea nada, que es lo que las hace válidas — y anotó que esa validez
   depende de que la primera mitad siga corriendo en el mismo caso.
3. **`APPLICABILITY_UNRESOLVED` nunca pasaba por `aprueba()` desde una corrida real.** E-23 afirmaba
   que `PASS` es el único estado que aprueba "en ningún camino"; cuatro de los cinco estados se
   ejercían sobre salidas reales de `evaluar` y el quinto sólo sobre diccionarios sintéticos. Se
   cerró sumando la aserción a E-18.
4. **La fila de la matriz no tiene historia contra la cual diferenciarse.**
   `es0901-7.1-normative-matrix.json` figura sin trackear en git, así que "la fila no cambió" lo
   sostiene la aserción de valores y no un diff. No es un hallazgo contra el cambio; es lo que hay
   hasta que ese archivo se commitee.

## Lo que queda abierto, anotado y no escondido

1. **`controles/` nunca llega a un proyecto instalado.** `install.ps1` copia una lista fija por
   harness —`checks`, `bin`, `reglas`, `skills`, `agents`— y `controles/` no está. Acá la suite está
   verde porque la fábrica lee el árbol del repositorio; fuera de él, los ocho controles de G1, G2 y
   D1 dicen `INSTALLED` y resuelven a `CONTROL_FILE_MISSING`. Es defecto de G1, no de D1, y necesita
   su propia spec: toca `install.ps1`, `controles.py` y un caso de instalador nuevo. Anotado en
   `Pendientes/Fix-Harness/PENDIENTES-FH.md`, ítem 2 de la tabla de prioridades.
2. **La segunda mitad de E-28 se degrada en silencio si alguien borra la primera.** Hoy las dos
   corren y el caso es correcto. El día que se afloje el primer bucle, `any()` se vuelve
   trivialmente satisfacible y las ocho fugas dejan de comprobar nada, en verde. Anotado en
   `Pendientes/Fix-Harness/PENDIENTES-FH.md`.
3. **Nadie consume todavía el resultado de `citizen-authentication-mechanism`.** `aprueba()` sólo se
   llama desde los tests. La spec no promete ese cableado —lo declara bajo riesgos conocidos, junto
   con que nadie produce las señales— así que es una decisión libre y no un incumplimiento.

## Lo que ningún test cubre y se mira con los ojos

- **Que la evidencia que alguien cargue diga lo que el `claim` afirma.** El contrato exige que la
  referencia esté escrita; que el Jira referenciado efectivamente describa un trámite del ciudadano
  es criterio de quien la carga, y ningún test lo puede contradecir.
- **Que `PARTIAL` no se vuelva el estado cómodo.** Se ve corriendo D1 sobre proyectos reales y
  mirando la distribución de resultados, no en la suite.
- **Que el mecanismo declarado sea el que la aplicación usa de verdad.** D1 verifica gobierno, no
  integración, y esa distancia sólo la cierra el material autoritativo de miBA que todavía no
  existe.
