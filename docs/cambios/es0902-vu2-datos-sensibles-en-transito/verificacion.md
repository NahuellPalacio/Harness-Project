# Verificación — ES0902 Vu2: ningún dato sensible en texto plano, salto por salto y con evidencia

**Estado:** cerrado, con tres contradichos documentados · **Fecha:** 23-09-2026 · **Versión:** 0.20.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 23-09-2026
en **tres pases**. Los tres corrieron `python tests/correr.py -k 46_es0902` y la compuerta completa
`.\tests\Invoke-Tests.ps1`, con el árbol quieto; la del tercero: `29692/29692` y `29942/29942`,
EXIT=0. El tercero fue el pase final por regla de la casa.

**Resultado: 44 escenarios sostenidos, 3 contradichos (E-08, E-13, E-43), 0 leídos, 0 sin sustento.**

Los escenarios los escribió quien construyó —el pedido de Vu2 no traía lista—, y el refutador los
contrastó también contra el paquete: de ahí salieron E-45 (redirect y downgrade) y la evidencia que
la señal tiene que conservar (E-05).

## Los veredictos

Todos los tests están en `tests/casos/46_es0902_vu2_datos_sensibles_en_transito.py`.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | La clave es `ES0902.Vu2` | sostenido | sí | `test_e01_la_clave` |
| E-02 | La señal es `sensitiveDataTransmissionPresent` | sostenido | sí | `test_e02_la_senal` |
| E-03 | Agente, policy y check exactos | sostenido | sí | `test_e03_los_ids` |
| E-04 | Nada nuevo | sostenido | sí | `test_e04_nada_nuevo` |
| E-05 | La señal enciende con autoridad y conserva la evidencia | sostenido | sí | `test_e05_la_senal_enciende_con_autoridad` |
| E-06 | Un nombre de campo no enciende | sostenido | sí | `test_e06_un_nombre_de_campo_no_enciende` |
| E-07 | Apagar exige autoridad | sostenido | sí | `test_e07_apagar_exige_autoridad` |
| E-08 | La ausencia no apaga | **contradicho** | sí | `test_e08_la_ausencia_no_apaga` |
| E-09 | Sensible sin autoridad no pasa | sostenido | sí | `test_e09_sensible_sin_autoridad_no_pasa` |
| E-10 | Lo declarado contra la evidencia, en las dos direcciones | sostenido | sí | `test_e10_…`, `test_e46_…` |
| E-11 | Ninguna taxonomía | sostenido | sí | `test_e11_ninguna_taxonomia` |
| E-12 | Un camino detectado que no está | sostenido | sí | `test_e12_un_camino_detectado` |
| E-13 | Referencias, repetidos, sin saltos, saltos ambiguos | **contradicho** | sí | `test_e13_referencias_repetidos_y_sin_saltos` |
| E-14 | La cadena entera | sostenido | sí | `test_e14_la_cadena_entera` |
| E-15 | El salto interno en claro es `FAIL` | sostenido | sí | `test_e15_el_salto_interno_en_claro` |
| E-16 | Cada salto solo | sostenido | sí | `test_e16_cada_salto_solo` |
| E-17 | Todo protegido pasa | sostenido | sí | `test_e17_todo_protegido_pasa` |
| E-18 | La terminación no cubre lo de atrás | sostenido | sí | `test_e18_la_terminacion_no_cubre_lo_de_atras` |
| E-19 | La frontera no material, sólo con arquitectura | sostenido | sí | `test_e19_la_frontera_no_material` |
| E-20 | Codificar sobre `http` es `FAIL` | sostenido | sí | `test_e20_codificar_sobre_http_es_fail` |
| E-21 | Codificar sobre lo que no se sabe no es protegido | sostenido | sí | `test_e21_codificar_sobre_lo_que_no_se_sabe` |
| E-22 | Un hash no es cifrar | sostenido | sí | `test_e22_un_hash_no_es_cifrar` |
| E-23 | Cifrado de aplicación sobre `http` | sostenido | sí | `test_e23_cifrado_de_aplicacion_sobre_http` |
| E-24 | La forma de la URL no alcanza | sostenido | sí | `test_e24_la_forma_de_la_url` |
| E-25 | Protegido contra en claro | sostenido | sí | `test_e25_protegido_contra_en_claro`, `test_e46_…` |
| E-26 | Validación apagada impide el `PASS` sin ser `FAIL` | sostenido | sí | `test_e26_validacion_apagada` |
| E-27 | El código fuente solo no alcanza | sostenido | sí | `test_e27_el_codigo_fuente_solo` |
| E-28 | Nada criptográfico | sostenido | sí | `test_e28_nada_criptografico` |
| E-29 | Ningún número | sostenido | sí | `test_e29_ningun_numero` |
| E-30 | La prueba sintética sostiene | sostenido | sí | `test_e30_la_prueba_sintetica` |
| E-31 | La prueba insegura no aprueba ni hace `FAIL` | sostenido | sí | `test_e31_la_prueba_insegura` |
| E-32 | Sin objetivo no es `FAIL` | sostenido | sí | `test_e32_sin_objetivo` |
| E-33 | No ejecuta nada | sostenido | sí | `test_e33_no_ejecuta_nada` |
| E-34 | El registro vacío y cerrado | sostenido | sí | `test_e34_el_registro_vacio` |
| E-35 | El catálogo cerrado | sostenido | sí | `test_e35_el_catalogo_cerrado` |
| E-36 | Ningún secreto sale | sostenido | sí | `test_e36_ningun_secreto_sale` |
| E-37 | Lo ilegible sobre el camino | sostenido | sí | `test_e37_lo_ilegible_sobre_el_camino` |
| E-38 | Vu2 no es Vu7, D8 ni C1 | sostenido | sí | `test_e38_vu2_no_es_otras_reglas` |
| E-39 | No nombra otros controles | sostenido | sí | `test_e39_no_nombra_otros_controles` |
| E-40 | Uno en `FAIL` | sostenido | sí | `test_e40_uno_en_fail` |
| E-41 | Uno sin resolver | sostenido | sí | `test_e41_uno_sin_resolver` |
| E-42 | Lo no sensible no se evalúa | sostenido | sí | `test_e42_lo_no_sensible_no_se_evalua` |
| E-43 | El mismo resultado en cualquier orden | **contradicho** | sí | `test_e43_el_mismo_resultado` |
| E-44 | La trazabilidad | sostenido | sí | `test_e44_la_trazabilidad` |
| E-45 | Un redirect que expone el payload | sostenido | sí | `test_e45_un_redirect_que_expone_el_payload` |
| E-46 | Todo id se compara igual | sostenido | sí | `test_e46_la_misma_regla_para_todo_id` |
| E-47 | Un "no" que no dice de qué salto habla | sostenido | sí | `test_e47_un_no_que_no_dice_de_que_salto_habla` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Acá no hay ninguno: los
> cuarenta y siete se vieron en rojo con una pasada de mutaciones, y lo que agregó cada pase se vio en
> rojo con mutaciones puntuales.

## E-08, E-13 y E-43, los escenarios contradichos

Los tres tienen una sola causa: la regla del segundo pase —todo id se compara en NFC— quedó afuera
de los **conteos** de `derivar`.

```
dos caminos "trámites", NFC y NFD                    PASS, duplicatedPaths = []       (E-13)
saltos x->ñ (NFC) y x->ñ (NFD) en el mismo camino    PASS, ambiguousHops = []         (E-13)
dos clases "salúd", NFC y NFD                        duplicatedClasses = []           (E-13)
clase NFC con fuente + gemela NFD sin fuente         [NFC, NFD] APPLICABILITY_UNRESOLVED
                                                     [NFD, NFC] PASS                  (E-43)
clase NFC no sensible + gemela NFD sin resolver      [NFC, NFD] UNRESOLVED
                                                     [NFD, NFC] FALSE                 (E-08)
```

**Causa.** `ids_clase.count(...)`, `ids_camino.count(...)`, `missing` y los ids de salto (`hids`) se
calculan sobre el texto crudo, mientras que el diccionario de clases se indexa en NFC: dos clases
iguales en NFC no se marcan repetidas y la segunda pisa a la primera según el orden. Con los mismos
bytes, las tres cosas funcionan.

**Decisión.** Cierra contradicho por la regla del tercer pase. El arreglo es normalizar en NFC los
ids **antes** de contar, en un solo lugar; es chico y queda escrito en `PENDIENTES-FH.md`. Vu3 nace
con esa regla en `controles/lib/evidencia.py`. La exposición real es baja —hace falta el mismo id
escrito en dos normalizaciones distintas en un registro del proyecto— pero dos de los tres fallan
abierto.

## Los tres pases

| Pase | Resultado | Qué encontró |
|---|---|---|
| 1 | 40 sostenidos, 1 contradicho, 3 sin sustento | El prefijo `arn:` eximía el texto entero; tests que no probaban lo que decían (clase repetida, prueba sin objetivo que dice en claro, D8); del paquete, el redirect y la evidencia de la señal |
| 2 | 41 sostenidos, 3 contradichos, 1 sin sustento | NFC en lo ilegible y no en lo legible: un "no" legible en NFD pesaba menos que uno mal formado |
| 3 | 44 sostenidos, 3 contradichos | NFC afuera de los conteos de repetidos |

## Lo que la verificación encontró y no habría encontrado un test verde

1. **El `arn:` como salvoconducto.** La exención de los ARN dejaba pasar `arn:password=…` entero.
2. **La prueba que no podía fallar.** El "no es `FAIL`" de E-32 se probaba con una prueba que decía
   protegido.
3. **Lo que el paquete pedía y la spec no.** Redirect y downgrade, la evidencia que la señal
   conserva, y que la frontera no material sea de arquitectura.
4. **NFC a medias**, dos veces: primero entre lo legible y lo ilegible, después en los conteos.

## Lo que queda abierto, anotado y no escondido

En `Pendientes/Fix-Harness/PENDIENTES-FH.md`:

- E-08, E-13 y E-43: NFC en los conteos de `derivar`.
- E-47 bloquea de más: un "sí" sin `hop`, una evidencia compartida entre dos caminos, un redirect que
  dice que no expone, y lo hace sin filtrar la fuente —con lo que tensiona E-45— y sin rotular las
  pruebas inseguras o sin objetivo.
- La regla de salida y el catálogo cerrado están en Vu2 y ahora también en `controles/lib/`; Vu1 y
  Vu2 se migran aparte.
- `reglas/` se sobrescribe en cada `-Update`.

## Lo que ningún test cubre y se mira con los ojos

- Que un proyecto real pueda escribir su clasificación de datos con las clases de fuente que este
  cambio eligió. La tabla es del harness.
- Que nadie "arregle" el registro vacío declarando `PROTECTED` sin evidencia.
