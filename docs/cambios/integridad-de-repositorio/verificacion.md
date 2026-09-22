# Verificación — Integridad de repositorio y revisión de incidentes de seguridad

**Estado:** en curso · **Fecha:** 22-09-2026 · **Versión:** entra en 0.19.0 sin cerrar

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 22-09-2026,
corriendo `python tests/correr.py -k 38_integridad` y la compuerta completa, y **sondeando con
mutaciones**: cada `sostenido` con al menos una que lo pone en rojo, cada `sin sustento` con una que
rompe lo que el escenario afirma y deja la suite verde.

**Resultado de la cuarta pasada: 49 sostenidos, 0 contradichos, 0 leídos, 2 sin sustento**
—E-04 y E-41—.

| Pasada | Árbol | Sostenidos | Sin sustento |
|---|---|---|---|
| Primera | de trabajo | 47 | E-04, E-06, E-41, E-51 |
| Segunda | release de 0.19.0, sin ES0902 O1 ni O2 | 48 | E-04, E-41, E-51 |
| Tercera | release de 0.19.0 | 49 | E-04, E-41 |
| Cuarta | release de 0.19.0 | 49 | E-04, E-41 |

🔴 **El cambio no cierra, y entra al código de 0.19.0 declarado abierto.** Ningún escenario quedó
contradicho y ninguna conducta del módulo está mal: los dos que quedan son huecos del test. Entre
la segunda y la cuarta pasada se barrieron las mutaciones que sobrevivían —las de la segunda en la
tercera, las de la tercera en la cuarta—, y cada pasada encontró otra dimensión que la entrada del
test dejaba fija. Un `sin sustento`, a diferencia de un `contradicho` documentado, no tiene
excepción que lo cierre: se queda `EN CURSO` hasta que un refutador lo sostenga.

## La tabla

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | No es una regla: ni en las dos matrices, ni en el registro | sostenido | sí | `38_integridad`, `test_e01_no_es_una_regla`, más verificación de mtime aparte |
| E-02 | No crea ningún agente | sostenido | sí | `test_e02_no_crea_ningun_agente` |
| E-03 | Las tres skills de seguridad siguen siendo las autoritativas | sostenido | sí | `test_e03_las_skills_de_seguridad_siguen_siendo_las_autoritativas` |
| E-04 | Un `PASS` no es una aprobación de ES0902 | **sin sustento** | sí | `test_e04_un_pass_no_es_una_aprobacion` |
| E-05 | Los tres modos, y las seis acciones apagadas en incidente | sostenido | sí | `test_e05_el_modo_incidente_desactiva_lo_automatico` |
| E-06 | La evidencia se preserva antes de cualquier mutación | sostenido | sí | `test_e06_la_evidencia_se_preserva_antes` |
| E-07 | La rotación de credenciales no es automática | sostenido | sí | `test_e07_la_rotacion_no_es_automatica` |
| E-08 | El borrado no es automático | sostenido | sí | `test_e08_el_borrado_no_es_automatico` |
| E-09 | La reescritura de historia no es automática | sostenido | sí | `test_e09_la_reescritura_no_es_automatica` |
| E-10 | Recomendar sigue permitido, y nunca queda ejecutado | sostenido | sí | `test_e10_recomendar_sigue_permitido` |
| E-11 | La rama actual no es confiable, y el módulo no nombra ninguna | sostenido | sí | `test_e11_la_rama_actual_no_es_confiable` |
| E-12 | Las cinco formas del hueco de línea de base | sostenido | sí | `test_e12_sin_linea_de_base` |
| E-13 | La confirmación humana exige evidencia y quién | sostenido | sí | `test_e13_la_confirmacion_humana_exige_quien` |
| E-14 | Cambiar la base crea otro contexto | sostenido | sí | `test_e14_cambiar_la_base_crea_otro_contexto` |
| E-15 | Las cinco fuentes sirven, y ninguna otra | sostenido | sí | `test_e15_las_cinco_fuentes` |
| E-16 | Agregados, modificados y borrados; las once clases clavadas | sostenido | sí | `test_e16_los_archivos_agregados_modificados_y_borrados` |
| E-17 | La identidad de los commits, con padres y verificación | sostenido | sí | `test_e17_la_identidad_de_los_commits` |
| E-18 | Los hashes de archivo cuando la evidencia los trae | sostenido | sí | `test_e18_los_hashes_de_archivo` |
| E-19 | Los manifiestos de dependencias | sostenido | sí | `test_e19_los_manifiestos_de_dependencias` |
| E-20 | Los lockfiles | sostenido | sí | `test_e20_los_lockfiles` |
| E-21 | El pipeline | sostenido | sí | `test_e21_el_pipeline` |
| E-22 | El contenedor, el build y la infraestructura | sostenido | sí | `test_e22_el_contenedor_y_el_build` |
| E-23 | Autenticación y autorización | sostenido | sí | `test_e23_la_autenticacion_y_la_autorizacion` |
| E-24 | Los binarios inesperados, con ruta y hash | sostenido | sí | `test_e24_los_binarios_inesperados` |
| E-25 | El inventario es determinista y no depende del orden | sostenido | sí | `test_e25_el_inventario_es_determinista` |
| E-26 | Un archivo sin clase no se adivina; las diez clases clavadas | sostenido | sí | `test_e26_un_archivo_sin_clase_no_se_adivina` |
| E-27 | `eval` y `exec` solos no confirman | sostenido | sí | `test_e27_eval_y_exec_solos` |
| E-28 | Base64 y ofuscación solos tampoco | sostenido | sí | `test_e28_base64_y_ofuscacion_solos` |
| E-29 | Un dominio nuevo solo no es exfiltración | sostenido | sí | `test_e29_un_dominio_nuevo_solo` |
| E-30 | Las 63 combinaciones de los seis débiles, con y sin evidencia directa | sostenido | sí | `test_e30_los_seis_debiles_juntos` |
| E-31 | Las veintiuna categorías nombradas, y el hallazgo con sus claves exactas | sostenido | sí | `test_e31_una_senal_produce_evidencia_y_confianza` |
| E-32 | El confirmado exige evidencia directa citada y confianza alta | sostenido | sí | `test_e32_el_confirmado_exige_evidencia_directa` |
| E-33 | Confianza y severidad son dos ejes: 3 × 4, en los dos sentidos | sostenido | sí | `test_e33_confianza_y_severidad_son_dos_ejes` |
| E-34 | No se inventa una segunda escala (barrido AST) | sostenido | sí | `test_e34_no_se_inventa_una_segunda_escala` |
| E-35 | Las cuatro formas de mapeo no autoritativo | sostenido | sí | `test_e35_sin_mapeo_autoritativo` |
| E-36 | El secreto no entra al hallazgo ni a la revisión | sostenido | sí | `test_e36_el_secreto_no_entra_al_hallazgo` |
| E-37 | Se redacta, se huella y se ubica | sostenido | sí | `test_e37_el_secreto_se_redacta_y_se_huella` |
| E-38 | La contabilidad mide y no guarda nada sensible | sostenido | sí | `test_e38_la_contabilidad_no_guarda_nada_sensible` |
| E-39 | El acceso nuevo a un secreto se expone en el hallazgo | sostenido | sí | `test_e39_el_acceso_nuevo_a_un_secreto` |
| E-40 | La desactivación de un control se expone | sostenido | sí | `test_e40_la_desactivacion_de_un_control` |
| E-41 | Los once hechos del pipeline se exponen en el hallazgo | **sin sustento** | sí | `test_e41_el_despliegue_privilegiado` |
| E-42 | La sustitución de origen o registro se expone | sostenido | sí | `test_e42_la_sustitucion_de_origen_o_registro` |
| E-43 | Los siete hechos de cadena se exponen | sostenido | sí | `test_e43_los_hooks_de_instalacion` |
| E-44 | El binario no se ejecuta solo | sostenido | sí | `test_e44_el_binario_no_se_ejecuta_solo` |
| E-45 | Lo dinámico exige las cuatro | sostenido | sí | `test_e45_lo_dinamico_exige_las_cuatro` |
| E-46 | Sin ambiente aislado, el estado del pedido | sostenido | sí | `test_e46_sin_ambiente_aislado` |
| E-47 | Pasa por la compuerta de riesgo de tools | sostenido | sí | `test_e47_pasa_por_la_compuerta_de_tools` |
| E-48 | Una tool que ejecuta en el host no nace de bajo riesgo | sostenido | sí | `test_e48_una_tool_que_ejecuta_en_el_host` |
| E-49 | Las siete causas de la compuerta humana | sostenido | sí | `test_e49_la_compuerta_humana` |
| E-50 | La remediación es otra unidad y la evidencia no cambia | sostenido | sí | `test_e50_la_remediacion_es_otra_unidad` |
| E-51 | Los dos proveedores normalizan igual y nada propio llega | sostenido | sí | `test_e51_los_dos_proveedores_normalizan_igual` |

> 📌 La tabla es la de la cuarta pasada. E-06 quedó sostenido en la segunda y E-51 en la tercera.

Compuerta:

```
python tests/correr.py -k 38_integridad     ->  3523/3523   (eran 3368)
.\tests\Invoke-Tests.ps1                    ->  24216/24216, exit 0
```

## Lo que la verificación encontró y no habría encontrado un test verde

Ningún escenario quedó contradicho: ninguna conducta construida estaba mal. Los cuatro
`sin sustento` describen conductas que el módulo **no** tiene, y tres de los cuatro eran huecos de
verificación. **El cuarto no: era del módulo.**

1. **E-41 destapó dos declaraciones muertas.** `HECHOS_DE_PIPELINE` y `HECHOS_DE_CADENA` no las leía
   ninguna función, y `hallazgo()` no copiaba los indicadores: un acceso nuevo a un secreto en el
   pipeline salía con su categoría y **sin el hecho que lo originó**, que es justamente lo que quien
   remedia necesita para saber dónde mirar. El test verificaba pertenencia a una tupla en vez de
   mirar la salida. Ahora el hallazgo lleva `indicators`, `pipelineFacts`, `supplyChainFacts` y
   `weakIndicators`, y los once hechos se verifican uno por uno contra el hallazgo.

2. **E-04 era una tautología.** `antes = estado_oficial(None)` se capturaba **después** de la
   revisión y se comparaba contra otra llamada a la misma función pura. El refutador metió un
   secuestro literal de lo que `evaluacion` resuelve adentro de `revisar` y la suite quedó verde.

3. **E-06 muestreaba 1 de 6.** Restringir la compuerta de preservación a `FILE_DELETION` dejaba que
   las otras cinco acciones —las que borran la escena— se ejecutaran sin evidencia preservada, con
   la suite entera en verde.

4. **E-51 barría claves de primer nivel.** Un campo propio de GitLab metido adentro de *cada* archivo
   normalizado viaja al inventario y a la instantánea, y el barrido no lo veía. Es la lección de
   D8/E-34 que la propia spec cita y que igual se repitió.

5. **E-51 destapó una fuga real, en la segunda pasada.** `diffMeta` copiaba `stats` entero, y la
   URL del proveedor —`web_url` en GitLab, `html_url` en GitHub— viajaba al evento normalizado y a
   la instantánea sellada. Ahora `_diff_normalizado()` deja sólo `additions`, `deletions` y
   `total`. Con E-41 de la primera, son dos los hallazgos que eran del módulo.
6. **E-04 se podía burlar desde adentro de `revisar`** —reasignar los productores de `evaluacion`,
   reemplazar `estado_oficial`, cambiar sus `__defaults__` o el módulo en `sys.modules`— y una
   clave inventada como `securityApproved` pasaba. Todo eso ya pone la suite en rojo.
7. **E-41 perdía los hechos justo en el hallazgo más grave** sin que nada lo notara: en el
   `CONFIRMADO`, con la severidad resuelta, desde el segundo hallazgo de una revisión o fuera del
   modo incidente. Ahora un producto de 560 señales lo cubre.

Y cinco reservas que el refutador dejó y también se cerraron: las veintiuna categorías se contaban
pero no se nombraban; las once clases de cambio, las diez de archivo y los siete hechos de cadena,
igual; y dos aserciones de E-38 no podían fallar porque el secreto nunca entraba en crudo a la
entrada. Además, `severityState` pasó a estar siempre presente: un campo que aparece y desaparece
obliga a preguntar si existe antes de leerlo.

## Lo que queda abierto, anotado y no escondido

- **E-04 y E-41, sin sustento en la cuarta pasada.** Van a `Pendientes/Fix-Harness/PENDIENTES-FH.md`
  con las mutaciones que sobreviven. E-04: `reason: "ES0902_APPROVED"` o `verdict: "ES0902_PASSED"`
  en la revisión limpia pasan, porque el barrido de valores ignora a propósito los tokens compuestos
  para no confundir la procedencia `APPROVED_RELEASE`. E-41: el producto deja fijos `location`,
  `evidence` y la validez de la categoría, y condicionar los hechos a cualquiera de los tres pasa.
- **`instantanea()` copia el `diffMeta` que recibe.** Hoy no fuga porque lo que le llega ya viene
  normalizado; si algún día recibe evidencia sin normalizar, fuga.
- **La compuerta no es determinista.** Ítem nuevo de `Pendientes/Fix-Harness/PENDIENTES-FH.md`, con
  tres síntomas medidos el mismo día: siete fallas de instalador que no se reprodujeron a mano, los
  conteos de tests de python derivando entre corridas del mismo árbol —`33_bases` dio 3565, 3586 y
  3604—, y `19_contexto/E-29`, cuyo título declara *"el reloj no cuenta"* y falló con dos hashes
  distintos para la misma entrada. Casi provoca un diagnóstico equivocado: una bisección apuntó a
  los archivos nuevos y estaba mal.
- **Esta capacidad no detecta nada por sí sola.** Recibe evidencia normalizada y la clasifica. Los
  adaptadores reales contra las APIs, el escáner de secretos y el analizador de dependencias son del
  Bloque 1 y son otro cambio.
- **`AUXILIARY`, `active`, la clase de archivo y `directEvidence` son datos declarados.** El módulo
  exige que estén y los cita; que sean honestos no lo puede saber.
- **El modo no lo enciende nadie todavía.** `SECURITY_INCIDENT` se pasa como dato.
- **`control-registry.json` está sin versionar.** El refutador no pudo comparar bytes contra una
  base para afirmar que no se tocó; lo verificó por contenido. Un `git add` lo cierra.

## Lo que ningún test cubre y se mira con los ojos

- **Que la evidencia preservada alcance para reconstruir qué pasó.** El módulo garantiza que está
  sellada y que nadie la pisa; si el conjunto de campos es suficiente para una investigación real lo
  dice quien investigue una de verdad.
- **Que la redacción cubra lo que importa.** Lo que se garantiza es que un valor **declarado**
  secreto no aparece en ninguna parte de la salida. Si un valor sensible entra por un campo que
  nadie marcó, la redacción no lo ve.
- **Que la doctrina se lea como doctrina.** `docs/seguridad-de-repositorio.md` es lo que una persona
  lee cuando sospecha un compromiso a las tres de la mañana. Si ahí no queda claro que preservar va
  antes que arreglar, el resto no sirve.
