# Verificación — El sustrato de conocimiento confiable: fuentes, integridad y frescura

**Estado:** cerrado · **Fecha:** 23-09-2026 · **Versión:** 0.20.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 23-09-2026
en **dos pases**. Los dos corrieron `python tests/correr.py -k conocimiento_fuentes` y la compuerta
completa `.\tests\Invoke-Tests.ps1`: el primero sobre `29604/29604` y el segundo sobre
`29610/29610`, los dos motores, EXIT=0. El primer pase dejó dos contradichos —E-02 y E-12—; los dos
volvieron a trabajo, se cerraron **moviendo el código hacia la spec** y el segundo pase los volvió a
refutar de cero, con sonda propia y mutación propia.

**Resultado: 36 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

## Los veredictos

Todos los tests están en `tests/casos/45_conocimiento_fuentes.py`.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | El registro valida contra `source-registry/1.1` y sin original aceptado el hash es `null` | sostenido | sí, específico | `test_e01_el_registro_valida_y_no_inventa_hashes`, las dos mitades |
| E-02 | Dos entradas con el mismo `id` hacen que el registro no cargue | sostenido | sí, específico | `test_e02_una_entrada_por_fuente`, sobre un árbol falso y con el control contrario |
| E-03 | El registro no persiste ninguna lista de derivados | sostenido | sí, específico | `test_e03_sin_lista_de_derivados`, por `additionalProperties: false` |
| E-04 | La línea base no declara la versión de una fuente gestionada: la lee del registro | sostenido | sí, específico | `test_e04_la_linea_base_toma_la_version_del_registro` |
| E-05 | Con el árbol como viene, O1 sale igual y por las mismas razones | sostenido | sí, específico | `test_e05_o1_no_cambia`, valores absolutos |
| E-06 | Un extracto que no está se diagnostica con su id y su ruta | sostenido | sí, específico | `test_e06_un_extracto_que_no_esta_se_dice` |
| E-07 | Desde una fuente, sus controles, y ninguno de los que no la declaran | sostenido | sí, específico | `test_e07_de_una_fuente_a_sus_controles`, en las dos direcciones |
| E-08 | Desde una fuente, las filas de su matriz con policies, checks y reviews | sostenido | sí, específico | `test_e08_de_una_fuente_a_las_filas_de_su_matriz` |
| E-09 | Un agente y una skill que declaran `sources:` salen en el índice | sostenido | sí, específico | `test_e09_un_agente_y_una_skill_que_declaran_su_fuente`, árbol falso |
| E-10 | Un derivado que declara otra versión sale viejo, con las dos versiones | sostenido | sí, específico | `test_e10_un_derivado_que_declara_otra_version` |
| E-11 | Un id que nadie declara devuelve impacto vacío | sostenido | sí, específico | `test_e11_un_id_que_nadie_declara` |
| E-12 | Con la metadata sin cambios no se baja ningún adjunto | sostenido | sí, específico | `test_e12_metadata_sin_cambios_no_baja_nada`, con y sin hash previo |
| E-13 | Versión observada mayor: `UPDATE_AVAILABLE` | sostenido | sí, específico | `test_e13_una_version_posterior` |
| E-14 | Sin versión resoluble: `VERSION_UNRESOLVED`, nunca «sin cambios» | sostenido | sí, específico | `test_e14_sin_version_resoluble`, y la Ficha como segundo camino |
| E-15 | Misma versión con otra identidad: se baja y se hashea antes de resolver | sostenido | sí, específico | `test_e15_misma_version_con_otra_identidad` |
| E-16 | La fuente que no está en la Ficha deja `SOURCE_MISSING` | sostenido | sí, específico | `test_e16_la_fuente_no_esta_en_la_ficha` |
| E-17 | `--archivo` resuelve sin Jira y sin tocar la red | sostenido | sí, específico | `test_e17_el_modo_local_no_necesita_jira`, más la firma |
| E-18 | El descubrimiento no escribe en Jira: sólo verbos de lectura | sostenido | sí, específico | `test_e18_la_ficha_es_de_lectura`, sobre las llamadas y los imports |
| E-19 | El descubrimiento devuelve datos y no imprime | sostenido | sí, específico | `test_e19_el_descubrimiento_no_imprime`, y el refutador lo corrió en dinámico |
| E-20 | Misma versión y otro contenido: `SOURCE_INTEGRITY_ALERT`, nunca `CURRENT` | sostenido | sí, específico | `test_e20_misma_version_y_otro_contenido`, cinco variantes |
| E-21 | Misma versión y mismo contenido puede quedar `CURRENT` | sostenido | sí, específico | `test_e21_misma_version_y_mismo_contenido` |
| E-22 | Versión anterior: `VERSION_REGRESSION`, y no se promueve sola | sostenido | sí, específico | `test_e22_una_version_anterior` |
| E-23 | El hash es el del original, no el del markdown del extracto | sostenido | sí, de módulo | `test_e23_el_hash_es_el_del_original`; el rojo salió con la mutación de integridad |
| E-24 | `CURRENT` exige las cinco condiciones | sostenido | sí, específico | `test_e24_las_cinco_condiciones`, siete casos |
| E-25 | Sin canal: `FRESHNESS_UNVERIFIED`, nunca `CURRENT` | sostenido | sí, específico | `test_e25_sin_canal_no_hay_frescura`, ausente y caído |
| E-26 | Un derivado viejo impide `CURRENT` con la fuente intacta | sostenido | sí, específico | `test_e26_un_derivado_viejo_impide_current` |
| E-27 | La misma evidencia da el mismo resultado | sostenido | sí, específico | `test_e27_la_misma_evidencia_da_lo_mismo`, con el reloj aislado |
| E-28 | Todo estado se puede trazar a id, versiones, hashes y evidencia | sostenido | sí, específico | `test_e28_todo_estado_se_puede_contradecir`, sobre las seis fuentes reales |
| E-29 | Ningún camino desde la evidencia ausente hasta `CURRENT` | sostenido | sí, de módulo | `test_e29_ningun_camino_desde_la_ausencia_hasta_current`, 144 combinaciones |
| E-30 | El estado valida contra `sources-state/1.1` y el inventado no se escribe | sostenido | sí, específico | `test_e30_el_estado_valida_contra_su_contrato` |
| E-31 | El validador interpreta `additionalProperties` con schema, o lo declara | sostenido | sí, específico | `test_e31_el_validador_interpreta_un_mapa`, las dos mitades |
| E-32 | El estado se escribe redactado | sostenido | sí, específico | `test_e32_el_estado_se_escribe_redactado` |
| E-33 | `pending_count` sale de los estados, no de quien escribe | sostenido | sí, específico | `test_e33_pending_count_sale_de_los_estados`, y no hay parámetro |
| E-34 | Ninguna ruta de lo que se construye nombra SharePoint | sostenido | sí, específico | `test_e34_ninguna_ruta_nombra_sharepoint`, más un grep del refutador |
| E-35 | La CLI escribe el estado y sale 0 con fuentes en alerta | sostenido | sí, específico | `test_e35_la_cli_escribe_y_sale_cero` |
| E-36 | Con `--json` el documento va por stdout y el resto por stderr | sostenido | sí, específico | `test_e36_con_json_el_documento_va_por_stdout` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá no hay ninguno: los 36
> se vieron fallar con el código roto a propósito, 34 con una mutación dedicada y dos —E-23 y
> E-29— con la mutación que apaga la comparación de integridad, que los arrastra a los dos.

## Los dos que volvieron de la primera pasada

Ninguno de los dos cerró moviendo la spec. El refutador comparó en el segundo pase el texto de los
dos escenarios contra el que había citado en el primero y los encontró **iguales palabra por
palabra**, con el mismo `rojo visto`; el conteo de aserciones del grupo pasó de 259 a 265 sin
restar ninguna.

### E-02 — el registro se diagnosticaba y seguía

El escenario dice «hacen que el registro no cargue» y el registro cargaba:

```
cargar() NO levanto. Entradas: 7
ids: ['ES0901','ES0902','ES0903','PC0901','GuiaDGISIS','Obelisco','ES0901']
version_de('ES0901') -> 6.3   (silenciosamente la primera)
validar_schema() errores -> []
```

**Causa.** `cargar()` sólo hacía `json.load`. El duplicado se reportaba por `validar()` como
`DUPLICATE_SOURCE_ID` —que es la proposición vecina— y `buscar()` devolvía la primera de dos sin
que nadie se enterara: exactamente el «dos lugares que el día que difieran van a tener razón los
dos» que este registro existe para que no pase.

**Decisión.** Se movió el código: `_sin_repetidas` corre adentro de `cargar`, antes del `return`, y
levanta `RegistroInvalido` nombrando la fuente repetida. `dev-harness.py fuentes` lo convierte en
salida 2, que es el código de lo que la persona tiene que arreglar antes de seguir. No contradice
E-35: un registro que no se puede leer entero no es una fuente en alerta, es el insumo roto.

### E-12 — el test elegía el caso donde el sistema no podía fallar

El escenario dice «con la metadata sin cambios no se baja ningún adjunto» y se bajaba. El fixture
del test siempre traía hash en el estado anterior, así que la salida temprana cortaba antes de
llegar a la regla que la pisaba. Sacando ese hash:

```
metadata identica? True   identity_changed: False
se llamo a bajar: 1 vez   downloaded: True
evidencia: 'hay un hash aceptado y no hay con que compararlo todavia'
```

**Causa.** Una cuarta regla en `hay_que_bajar` —que no está en el escenario ni en la tabla de
diseño— pisaba a la primera cuando el estado anterior no tenía hash. Es alcanzable: el `previo`
sale del estado escrito, y ahí `observed_sha256` queda en `null` cada vez que una descarga falla.
En ese estado el harness volvía a bajar el adjunto **todas las sesiones**, con la metadata sin
mover, que es la llamada de red por documento por sesión que la decisión de diseño existe para
evitar.

**Decisión.** Se movió el código: la identidad igual manda sola, tenga o no hash el estado
anterior, y la evidencia dice en ese caso que la integridad queda sin verificar. Reintentar una
descarga que falló es una decisión de alguien, no un efecto de abrir una sesión; mientras tanto la
fuente queda bloqueante y a la vista, que es el invariante del cambio entero.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **Un test que pasaba porque su entrada elegía el caso imposible de fallar** (E-12). Las 259
   aserciones estaban verdes y la conducta del harness era la contraria a la que la spec declara.
   Es la tercera vez que aparece esta clase en este repositorio y la primera en que el defecto
   real —rebajar todas las sesiones— vive en el camino caliente.
2. **Una proposición vecina haciéndose pasar por la del escenario** (E-02). «Se diagnostica» y «no
   carga» son dos cosas, y el test afirmaba la primera mientras la spec pedía la segunda.
3. **Una spec ajena que quedó contradiciendo al árbol.** `gestion-de-ambientes-de-base-de-datos`
   E-36 enumera lo que el validador tiene que rechazar y nombra «un `additionalProperties` con un
   schema como valor», que este cambio hace soportado. La suite quedaba verde igual porque el test
   se había actualizado; el archivo que nadie corrige es el que hace fallar con razón a la próxima
   refutación. Se anotó abajo de E-36, fechado, sin tocar el escenario, y la sección de esta spec
   se retituló: ese ajeno no cambia de mecanismo, cambia de exigencia.

## Lo que queda abierto, anotado y no escondido

En `Pendientes/Fix-Harness/PENDIENTES-FH.md`, bajo *Incomplete capabilities*:

- Las seis fuentes gestionadas tienen `sha256: null`: sin un original aceptado, la integridad de
  ninguna se puede verificar y ninguna corrida las va a declarar `CURRENT`. Es el estado honesto y
  no se levanta solo.
- `normativa/` es de la fábrica y no se instala: en un proyecto instalado, las seis fuentes
  declaran un extracto que no está en ese árbol. Es la misma clase que el pendiente de
  `controles/`.
- Cuatro estados del contrato —`NEW_SOURCE`, `RETIRED`, `ACKNOWLEDGED_PENDING`,
  `KNOWLEDGE_PROMOTION_INCOMPLETE`— y la lógica de `_pospuesta` están construidos y ningún
  escenario de esta spec habla de ellos. Los cubren los slices que siguen; hasta entonces es código
  sin refutar.

## Lo que ningún test cubre y se mira con los ojos

- **Que la Ficha de Proyecto exista en un Jira real.** Sigue siendo el pendiente número 17: el
  descubrimiento contra la Ficha se probó con transporte falso, igual que los dos adapters.
- **Que `filenamePattern` acierte contra los nombres que la DGISIS usa de verdad.** Los seis
  patrones se escribieron contra los nombres que cita `normativa/fuentes/LEEME.md`; el día que la
  convención cambie, las seis fuentes caen juntas a `VERSION_UNRESOLVED`.
- **Que una persona lea la línea del comando y entienda que «sin verificar» no es «al día».** Es la
  frontera que el cambio entero defiende y la única que no se puede testear.
