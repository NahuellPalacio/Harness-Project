# Verificación — Bloque 1: la bienvenida y el estado del harness en cada sesión

**Estado:** cerrado · **Fecha:** 24-09-2026 · **Versión:** 0.21.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 24-09-2026
en **dos pases**, y cada pase corrió la compuerta completa una sola vez, con el árbol quieto. El
segundo dio:
- `-k 51_bienvenida`: `659/659`;
- `18_integraciones`: `142/142`;
- la compuerta: `32896/32896`, EXIT=0.

**Resultado: 26 escenarios sostenidos, 0 contradichos, 0 leídos (0 independientes, 0 delegados), 0 sin sustento.**

`E-nn` es `WLC-nn` del pedido; E-21..E-26 los agrega la spec. E-03, E-07 y E-21 se angostaron
después del primer pase, y la spec lo dice en cada uno. E-22 se amplió y E-26 es nuevo.

## Los veredictos

Salvo lo marcado "03" (`tests/casos/03-instalador.ps1`), los tests están en
`tests/casos/51_bienvenida.py`.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Una instalación que termina bien deja `.claude/harness.installation.json` con `installed: true`,… | sostenido | sí | 03: `bienvenida E-01 …` |
| E-02 | El archivo que escribe el instalador, y el que reescribe el hook, validan contra… | sostenido | sí | `test_e02_el_estado_que_escribe_el_hook_valida`, 03: `bienvenida E-02 …` |
| E-03 | La primera sesión muestra la bienvenida completa como `systemMessage`, con los cinco bloques del formato… | sostenido | sí | `test_e03_la_primera_sesion_muestra_la_bienvenida_completa` |
| E-04 | La segunda sesión muestra una sola línea y ninguna parte de la bienvenida completa | sostenido | sí | `test_e04_la_segunda_sesion_muestra_una_sola_linea` |
| E-05 | `session-start.py` no abre ninguna conexión de red | sostenido | sí | `test_e05_session_start_no_abre_ninguna_conexion` |
| E-06 | `session-start.py` y `bienvenida.py` no importan ningún cliente de modelo ni ningún módulo de `integraciones/` | sostenido | sí | `test_e06_no_importa_clientes_de_modelo_ni_integraciones` |
| E-07 | Los tres estados salen con su etiqueta, y `BLOCKED` nunca dice "listo" | sostenido | sí | `test_e07_ready_…`, `test_e07_partial_…`, `test_e07_blocked_…`, `test_e07_el_nombre_del_proyecto_queda_afuera_de_la_busqueda` |
| E-08 | Una integración en `NOT_CONFIGURED`, `CONNECTION_FAILED` o nunca verificada no sale con `✓` ni con… | sostenido | sí | `test_e08_integracion_no_disponible_sin_tilde_ni_disponible` |
| E-09 | El conocimiento sale del `state` de cada fuente de `harness.fuentes.json`: cambiar ese archivo cambia lo… | sostenido | sí | `test_e09_el_conocimiento_sale_del_state_de_cada_fuente` |
| E-10 | Una fuente en `SOURCE_INTEGRITY_ALERT` da `BLOQUEADO` y sale nombrada, con su id, en la bienvenida y en la… | sostenido | sí | `test_e10_alerta_de_integridad_bloquea_y_se_nombra` |
| E-11 | Con un token en el `.env` y en el almacén, `harness.installation.json` no contiene ningún valor que el… | sostenido | sí | `test_e11_el_estado_no_guarda_ningun_secreto` |
| E-12 | Con lo mismo, ni la bienvenida, ni la línea, ni `harness`, ni `harness --json`, ni `--verbose` imprimen el… | sostenido | sí | `test_e12_la_bienvenida_y_la_linea_no_imprimen_el_token`, `test_e12_la_cli_no_imprime_el_token` |
| E-13 | `dev-harness.py harness` muestra el estado que dan los archivos de ahora, sin red, y no cambia `firstRunShown` | sostenido | sí | `test_e13_harness_muestra_lo_de_ahora_…`, `test_e13_verbose_agrega_el_detalle` |
| E-14 | `harness --json` usa los ids en inglés (`READY`, `NOT_CONFIGURED`, `FRESHNESS_UNVERIFIED`) y valida contra… | sostenido | sí | `test_e14_harness_json_usa_los_ids_en_ingles_y_valida` |
| E-15 | La salida humana está en castellano: las etiquetas de la tabla, y ningún id en inglés de los que la tabla… | sostenido | sí | `test_e15_la_salida_humana_esta_en_castellano` |
| E-16 | Con `project-context.json` y su nombre, la bienvenida dice "Proyecto detectado: <nombre>" | sostenido | sí | `test_e16_con_contexto_dice_el_nombre` |
| E-17 | Sin contexto de proyecto, la bienvenida no inventa un nombre: dice que el proyecto no se detectó, sin `✓`,… | sostenido | sí | `test_e17_sin_contexto_no_inventa_un_nombre` |
| E-18 | Un `-Update` a una versión nueva sobre un proyecto con `firstRunShown: true` no repite la bienvenida | sostenido | sí | `test_e18_la_actualizacion_se_avisa_una_vez`, 03: `bienvenida E-18 …` |
| E-19 | `harness --reiniciar-bienvenida`, o borrar el archivo, hace que la sesión siguiente muestre la bienvenida… | sostenido | sí | `test_e19_borrar_el_estado_…`, `test_e19_reiniciar_bienvenida_…`, 03: `bienvenida E-19 …` |
| E-20 | Todo lo que `session-start.py` escribía al contexto antes de este cambio sigue saliendo igual y en el… | sostenido | sí | `test_e20_el_bloque_de_siempre_sale_igual_despues_de_la_bienvenida` |
| E-21 | `dev-harness.py setup` ya no imprime `HARNESS READY` fijo: imprime el estado del resolvedor | sostenido | sí | `test_e21_setup_imprime_el_estado_del_resolvedor` |
| E-22 | Un `harness.installation.json`, `harness.capacidades.json` o `harness.fuentes.json` roto o con un tipo… | sostenido | sí | `test_e22_un_archivo_roto_no_rompe_el_hook_ni_da_ready` |
| E-23 | Un proyecto de solo `analisis` no lista integraciones ni conocimiento, y no queda en `PARTIAL` por eso | sostenido | sí | `test_e23_solo_analisis_no_lista_integraciones_ni_conocimiento` |
| E-24 | `-Uninstall` borra `harness.installation.json` | sostenido | sí | 03: `bienvenida E-24 -Uninstall borra harness.installation.json` |
| E-25 | Un estado de fuente que no está en la tabla de etiquetas sale con su id y nunca como `ACTUAL` | sostenido | sí | `test_e25_un_estado_desconocido_sale_con_su_id_y_nunca_como_actual` |
| E-26 | Con `desarrollo`, un `harness.fuentes.json` sin ninguna fuente da `PARTIAL`, no `READY` | sostenido | sí | `test_e26_sin_fuentes_es_parcial`, `test_e26_actual_solo_si_todas_estan_al_dia` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá los 26 la declaran `sí`.
> Las mitades del hook de E-02, E-12 y E-19 se vieron en rojo mutando una copia de `comun/`, sin
> tocar los hooks del árbol.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-22.** Un campo con un tipo inesperado terminaba en `LISTO`. Las cinco pruebas pasaron por el
   `session-start.py` real:
   - `bootstrap: 5`;
   - un `harness.installation.json` vacío;
   - `verificado_en: 5`;
   - `blocking: "si"`;
   - `verified_at: 5`.

   El resolvedor anulaba esos campos en silencio. Ahora cada archivo se compara contra la forma que
   escribe su dueño. Para las fuentes es `source-state.schema.json`, leído de disco.
2. **E-26.** Un `harness.fuentes.json` sin fuentes daba `LISTO`. Y con ES0902 en alerta y el resto al
   día, la línea decía `Conocimiento ACTUAL` al lado de la alerta.
3. **E-03.** Un proyecto de solo `analisis` no mostraba los comandos. Se angostó la letra, porque los
   cuatro comandos son de `dev-harness.py` y ese harness no lo trae.
4. **E-21.** La telemetría `evento=harness.listo` sale en cualquier estado. Se angostó la letra al
   texto para la persona.

## Lo que queda abierto, anotado y no escondido

- **`evento=harness.listo`** se emite aunque el estado sea `PARTIAL` o `BLOCKED`. Arreglarlo exige
  enmendar primero la spec de `integraciones-bootstrap`. Está en
  `Pendientes/Fix-Harness/PENDIENTES-FH.md`.
- **OpenShift** no se muestra, porque el harness no tiene su adaptador. Así lo declara la spec.
- **El aviso de conocimiento con `aplicar` / `posponer`** sigue sin construir, como en
  `conocimiento-fuentes-y-frescura`.

## Lo que ningún test cubre y se mira con los ojos

- **Que el `systemMessage` de SessionStart aparezca en la pantalla** de Claude Code. La suite prueba
  que el hook lo emite, pero no puede abrir una sesión y verlo.
- **Que la bienvenida se lea bien en una terminal real de Windows**, con las rayas `━` y las marcas
  `✓ ◐ ✕`.
