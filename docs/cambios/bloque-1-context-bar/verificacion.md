# Verificación — Bloque 1: la Context Bar existe, y el harness sabe si está activa

**Estado:** cerrado · **Fecha:** 24-09-2026 · **Versión:** 0.22.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 24-09-2026
en **dos pases**. Cada uno corrió la compuerta completa una sola vez, con el árbol quieto, y el
segundo dio:
- `53_context_bar`: `445/445`;
- `30_b4`: `835/835`;
- el caso del instalador: `53/53`;
- la compuerta: `34064/34064`, EXIT=0.

**Resultado: 41 escenarios sostenidos, 0 contradichos, 0 leídos (0 independientes, 0 delegados), 0 sin sustento.**

`E-nn` es `CBV-nn` del pedido. E-36..E-39 los agrega la spec, y E-40 y E-41 salen de lo que encontró
el primer pase.

## Los veredictos

Los tests están en `tests/casos/53_context_bar.py`, y los marcados "54" en
`tests/casos/54-context-bar-instalador.ps1`, que instala de verdad.

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Un `harness.installation.json` `1.0` pasa a `1.1` sin perder ningún campo | sostenido | sí | `test_e01_un_1_0_pasa_a_1_1_sin_perder_ningun_campo`, `test_e01_un_1_0_que_no_se_migra_es_ilegible` |
| E-02 | El `1.1` que escriben el instalador, el hook y la CLI valida contra el schema | sostenido | sí | `test_e02_el_1_1_que_escriben_el_hook_el_registro_y_la_cli_valida` |
| E-03 | Después de instalar, los tres componentes tienen estado | sostenido | sí | `test_e03_despues_de_instalar_los_tres_componentes_tienen_estado` |
| E-04 | Con el renderizador en disco y el `statusLine` registrado, sin señal de vida, la barra no es `ACTIVE` | sostenido | sí | `test_e04_sin_senal_de_vida_la_barra_no_es_active` |
| E-05 | Registrada y probada, sin señal de vida de la sesión actual, es `CONFIGURED`, o `RELOAD_REQUIRED` si el… | sostenido | sí | `test_e05_registrada_y_probada_sin_senal_de_esta_sesion` |
| E-06 | Con la señal de vida de la sesión actual, el fingerprint registrado y `block4: OK`, es `ACTIVE` y… | sostenido | sí | `test_e06_senal_de_esta_sesion_con_la_huella_y_block4_ok_es_active` |
| E-07 | Un `-Update` que cambia el `statusLine` marca `reloadRequired: true` | sostenido | sí | 54: `E-07 …` |
| E-08 | Un `-Update` que no cambia ninguna huella no marca reinicio | sostenido | sí | 54: `E-08 …` |
| E-09 | Con `block4: SOURCE_UNAVAILABLE`, la barra no es `ACTIVE`: es `ERROR` con… | sostenido | sí | `test_e09_block4_no_disponible_es_error` |
| E-10 | La barra no escribe ningún archivo fuera del libro del Bloque 4 y de `contextbar.json`, y… | sostenido | sí | `test_e10_la_barra_escribe_solo_el_libro_y_la_senal` |
| E-11 | La bienvenida con `desarrollo` muestra "Observabilidad" con los tres componentes | sostenido | sí | `test_e11_la_bienvenida_con_desarrollo_muestra_observabilidad` |
| E-12 | `RELOAD_REQUIRED` sale como `REQUIERE REINICIO`, sin `✓`, con la acción requerida | sostenido | sí | `test_e12_reload_required_sale_como_requiere_reinicio` |
| E-13 | `ACTIVE` sale como `ACTIVA` o `ACTIVO`, con `✓` | sostenido | sí | `test_e13_active_sale_como_activa_o_activo_con_tilde` |
| E-14 | `ERROR` sale como `ERROR`, sin `✓`, y deja el estado general en `PARTIAL` | sostenido | sí | `test_e14_error_sale_como_error_sin_tilde_y_deja_partial` |
| E-15 | `session-start.py` sigue sin abrir ninguna conexión, con la barra incluida | sostenido | sí | `test_e15_session_start_no_abre_ninguna_conexion_con_la_barra` |
| E-16 | Ni `session-start.py` ni la barra importan un cliente de modelo | sostenido | sí | `test_e16_ni_la_barra_ni_session_start_importan_un_cliente_de_modelo` |
| E-17 | Con la barra `ACTIVE`, la línea compacta no repite tokens, costo ni contexto | sostenido | sí | `test_e17_la_linea_no_repite_los_numeros_de_la_barra` |
| E-18 | `harness` muestra los tres componentes, el reinicio pendiente y la última sesión vista | sostenido | sí | `test_e18_harness_muestra_los_tres_el_reinicio_y_la_ultima_sesion` |
| E-19 | `harness --json` usa los estados en inglés | sostenido | sí | `test_e19_harness_json_usa_los_estados_en_ingles` |
| E-20 | `harness --verbose` no imprime ningún secreto con un token cargado | sostenido | sí | `test_e20_harness_verbose_no_imprime_secretos` |
| E-21 | Un campo que el Bloque 4 no tiene no aparece en la barra, y un `COST_UNRESOLVED` no sale como `USD 0` | sostenido | sí | `test_e21_lo_que_el_bloque_4_no_tiene_no_aparece` |
| E-22 | Los tokens y el costo que dibuja la barra son los de `barra.de` sobre el libro, y cambiar el costo de… | sostenido | sí | `test_e22_tokens_y_costo_son_los_del_bloque_4_y_no_los_de_stdin` |
| E-23 | Agente, tarea y presupuesto salen del estado del Bloque 4, y sin tarea declarada la tarea no aparece | sostenido | sí | `test_e23_agente_tarea_y_presupuesto_salen_del_bloque_4` |
| E-24 | `docs/contabilidad.md` dice que la barra es de la terminal de Claude Code | sostenido | sí | `test_e24_la_doc_dice_que_la_barra_es_de_la_terminal` |
| E-25 | Ningún texto del harness afirma una integración nativa con la barra de estado de VS Code | sostenido | sí | `test_e25_ningun_texto_afirma_una_integracion_nativa_con_vs_code` |
| E-26 | Una instalación nueva con la barra registrada dice que puede hacer falta reiniciar, si no hay señal de vida | sostenido | sí | 54: `E-26 …` |
| E-27 | El aviso de reinicio desaparece cuando llega la señal de vida con el fingerprint nuevo | sostenido | sí | `test_e27_el_aviso_de_reinicio_se_va_con_la_senal_de_la_huella_nueva` |
| E-28 | Un `-Update` normal muestra el aviso compacto de dos líneas | sostenido | sí | `test_e28_el_aviso_de_actualizacion_tiene_dos_lineas` |
| E-29 | Con el harness `BLOCKED`, nada dice que la barra o el harness estén listos | sostenido | sí | `test_e29_bloqueado_nada_dice_listo` |
| E-30 | `securityReporting` `ACTIVE` no dice nada de la aprobación de seguridad: C2 y el estado oficial no se mueven | sostenido | sí | `test_e30_security_reporting_active_no_dice_nada_de_la_aprobacion` |
| E-31 | Un cambio en el bloque `statusLine` cambia `configurationFingerprint` | sostenido | sí | 54: `E-31 …` |
| E-32 | Un cambio en la versión del renderizador se detecta | sostenido | sí | 54: `E-32 …` |
| E-33 | Sin cambios, `runtimeComponents` no se reescribe: dos `-Update` iguales dejan el archivo igual byte a… | sostenido | sí | `test_e33_dos_registros_iguales_dejan_el_archivo_igual` |
| E-34 | `activeInCurrentSession` va aparte de `installed` y `configured`: una barra instalada y configurada de… | sostenido | sí | `test_e34_active_en_la_sesion_va_aparte_de_installed_y_configured` |
| E-35 | Los mismos archivos dan los mismos estados | sostenido | sí | `test_e35_los_mismos_archivos_dan_los_mismos_estados` |
| E-36 | El comando registrado corre con `bash -c` y con `powershell.exe -NoProfile -Command`, sale con 0 y dibuja… | sostenido | sí | 54: `E-36 …` |
| E-37 | Con una transcripción rota, sin libro o sin stdin, la barra sale con 0 y dibuja `HARNESS \| sin datos del… | sostenido | sí | `test_e37_sin_datos_la_barra_sale_0_y_lo_dice` |
| E-38 | Ingerir la misma transcripción dos veces deja el libro con los mismos eventos | sostenido | sí | `test_e38_ingerir_dos_veces_deja_el_libro_igual` |
| E-39 | La barra no dibuja texto de la transcripción: ni prompts, ni código, ni nada que el catálogo de secretos… | sostenido | sí | `test_e39_la_barra_no_dibuja_texto_de_la_transcripcion` |
| E-40 | El costo y el tiempo acumulados de la sesión siguen al último estado que reporta el proveedor | sostenido | sí | `test_e40_costo_y_tiempo_siguen_al_ultimo_estado` |
| E-41 | La huella de la señal de vida es la del comando que corrió, no la del `settings.json` del momento | sostenido | sí | `test_e41_la_huella_de_la_senal_es_la_del_comando_que_corrio`, 54: `E-41 …` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá los 41 la declaran `sí`.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **El costo y el tiempo se congelaban en el primer estado.** El libro del Bloque 4 deduplicaba el
   agregado del proveedor con una clave fija, así que ingiriendo de a poco la barra quedaba en
   `USD 0.50 · 1m` aunque la sesión fuera por `USD 2.75 · 10m`. El test de E-22 usaba un solo estado,
   que es el caso donde no se ve. Ahora cada estado entra como evento nuevo y el resumen toma el
   último (E-40).
2. **Un comando viejo borraba el aviso de reinicio.** La señal de vida calculaba su huella leyendo
   el `settings.json` del momento, no la del comando que corrió. Ahora el comando registrado lleva su
   huella como último argumento. La comparación con el registro es estricta, así que un dibujo del
   mismo segundo ya no prueba nada (E-41).
3. **La primera construcción del resolvedor se pasaba del presupuesto de SessionStart**: 406–414 ms
   contra 400 ms. Se bajó a 346–350 ms sin `hashlib`, que carga OpenSSL, y abriendo un solo libro en
   vez de todos.

## Lo que queda abierto, anotado y no escondido

Está en `Pendientes/Fix-Harness/PENDIENTES-FH.md`, en el ítem de los seis cabos sueltos de la
Context Bar:
- **Sin Git Bash,** la barra se da por probada con PowerShell solo.
- **Campos del schema** que la spec no declara.
- **Un libro vacío** deja la barra `ACTIVE` mientras dice "sin datos".
- **Un apóstrofo en la ruta** deja la barra sin registrar.
- **Los archivos editados a mano:** el `-Update` los restaura después de registrar.
- **`-Uninstall`** no borra `contextbar.json` ni `accounting/`.
- **La latencia:** `-Doctor` no ve lo que suma PowerShell, unos 180 ms.

## Lo que ningún test cubre y se mira con los ojos

- **Ver la barra en una sesión real** de Claude Code, en la terminal.
- **Comprobar si Claude Code la recarga sola** a mitad de sesión después de un `-Update`.
- **Comprobar si aparece en la extensión de VS Code**, que el harness no promete.

Ninguna de las tres tiene una lectura registrada todavía.
