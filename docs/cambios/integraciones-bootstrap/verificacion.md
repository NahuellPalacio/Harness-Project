# Verificación — Bloque 1 — Bootstrap e integraciones: Jira Cloud y GitLab

**Estado:** cerrado · **Fecha:** 14-09-2026 · **Versión:** 0.16.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 14-09-2026,
en dos pasadas, corriendo la suite completa (`.\tests\Invoke-Tests.ps1`) y mutando el código sobre
una copia del árbol para comprobar que cada test podía fallar. La primera pasada dejó un
`contradicho` y un `sin sustento`; la segunda, después de corregirlos, los dio por sostenidos.

**Resultado: 38 escenarios sostenidos, 0 contradichos, 0 sin sustento, 0 leídos. Los 38 con
`rojo visto: si`.**

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | `get` devuelve lo que hay, y `None` lo que no está | sostenido | sí | `18_integraciones.py::test_e01_get_devuelve_lo_que_hay` |
| E-01b | Un placeholder entre ángulos se lee como ausente | sostenido | sí | `::test_e01b_placeholder_es_ausente` |
| E-02 | El entorno del proceso le gana al `.env` | sostenido | sí | `::test_e02_el_entorno_le_gana_al_archivo` |
| E-03 | `set` deja comentarios, orden y variables ajenas intactos | sostenido | sí | `::test_e03_set_no_mueve_el_resto_del_archivo` |
| E-04 | `set` de una clave nueva la agrega sin mover el resto | sostenido | sí | `::test_e04_set_de_una_clave_nueva_la_agrega` |
| E-05 | `remove` borra la línea y `exists` da falso | sostenido | sí | `::test_e05_remove_borra_la_linea` |
| E-06 | Ni el `repr` ni las excepciones llevan el valor | sostenido | sí | `::test_e06_el_almacen_no_muestra_el_valor` |
| E-07 | Config inexistente es config vacía, no error | sostenido | sí | `::test_e07_config_inexistente_no_es_error` |
| E-08 | Una clave con forma de secreto se rechaza | sostenido | sí | `::test_e08_la_config_rechaza_una_clave_con_forma_de_secreto` |
| E-09 | Guardar una integración no toca las otras | sostenido | sí | `::test_e09_guardar_no_pisa_lo_ajeno` |
| E-10 | El cliente real devuelve código y cuerpo, 200 y 401 | sostenido | sí | `::test_e10_cliente_real_contra_servidor_local`, con `http.server` en `127.0.0.1` |
| E-11 | Un error de red vuelve como respuesta, no como excepción | sostenido | sí | `::test_e11_un_error_de_red_no_sale_del_modulo` |
| E-12 | Sin configuración, `NOT_CONFIGURED` y sin salir a la red | sostenido | sí | `::test_e12_sin_configuracion_no_sale_a_la_red` |
| E-13 | `enabled` en falso, `NOT_CONFIGURED` y sin red | sostenido | sí | `::test_e13_deshabilitada_no_sale_a_la_red` |
| E-14 | 200, 401, 403, timeout, DNS y 5xx dan sus estados | sostenido | sí | `::test_e14_el_codigo_de_respuesta_decide_el_estado` |
| E-15 | Jira manda Basic, GitLab `PRIVATE-TOKEN`, ninguno en la URL | sostenido | sí | `::test_e15_cada_integracion_manda_su_credencial_donde_va` |
| E-16 | Ningún motivo lleva el token, ni con el cuerpo traidor | sostenido | sí | `::test_e16_ningun_motivo_lleva_el_token` |
| E-17 | Lo que no está `AVAILABLE` no descubre ni sondea | sostenido | sí | `::test_e17_lo_que_no_esta_disponible_no_descubre_nada` |
| E-18 | Jira con adjuntos en 403 declara solo lo que contestó | sostenido | sí | `::test_e18_jira_declara_solo_lo_que_contesta` |
| E-18b | Con `/search/jql` en 410 se cae a `/search` | sostenido | sí | `::test_e18b_jira_cae_al_endpoint_viejo_de_busqueda` |
| E-19 | GitLab deriva de los scopes reales del token | sostenido | sí | `::test_e19_gitlab_deriva_de_los_scopes` |
| E-20 | Sin endpoint de scopes se cae al sondeo | sostenido | sí | `::test_e20_gitlab_viejo_cae_al_sondeo` |
| E-21 | Lo soportado sin validar figura `DISABLED`, no ausente | sostenido | sí | `::test_e21_lo_soportado_sin_validar_figura_disabled` |
| E-22 | `disponibles` y `por_integracion` contestan lo suyo | sostenido | sí | `::test_e22_el_registro_contesta_por_capacidad_y_por_integracion` |
| E-23 | El manifiesto y los adapters declaran lo mismo | sostenido | sí | `::test_e23_el_manifiesto_y_el_codigo_declaran_lo_mismo` |
| E-24 | Con Jira caído: código 0, READY, GitLab `ENABLED` | sostenido | sí | `::test_e24_una_integracion_caida_no_voltea_el_harness` |
| E-25 | Con todo cargado, `setup` no lee de stdin | sostenido | sí | `::test_e25_con_todo_configurado_el_setup_no_pregunta` |
| E-26 | `reconfigurar gitlab` no toca nada de Jira | sostenido | sí | `::test_e26_reconfigurar_uno_no_toca_al_otro`, contra la CLI real |
| E-26b | El asistente completo: pregunta, guarda, valida, descubre | sostenido | sí | `::test_e26b_el_setup_carga_lo_que_falta` |
| E-27 | `--token` se rechaza, con motivo y sin escribir nada | sostenido | sí | `::test_e27_el_token_por_linea_de_comandos_se_rechaza` |
| E-28 | Config ilegible: código 2, nombra el archivo y qué hacer | sostenido | sí | `::test_e28_config_ilegible_sale_con_2` y `::test_e28b_config_ilegible_levanta` |
| E-29 | El `bin` y la configuración quedan instalados | sostenido | sí | `18-integraciones-instalador.ps1`, 10 assertions |
| E-30 | Sin `desarrollo`, nada de eso se instala | sostenido | sí | `18-integraciones-instalador.ps1` |
| E-31 | `-Update` repone el `bin` y no pisa la configuración | sostenido | sí | `18-integraciones-instalador.ps1` |
| E-32 | `-Uninstall` borra el `bin` y deja `.env` y la config | sostenido | sí | `18-integraciones-instalador.ps1` |
| E-33 | El lockfile no inventaría bytecode | sostenido | sí | `18-integraciones-instalador.ps1`, con precondición que compila el origen |
| E-33b | `-Uninstall` no deja `.claude/harness` en pie | sostenido | sí | `18-integraciones-instalador.ps1` y, de rebote, E-27 de `03-instalador.ps1` |
| E-34 | El `.env.example` reducido no dispara ningún patrón | sostenido | sí | `04_secretos.py::test_e09_env_example_no_dispara_nada` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. En este cambio no hay
> ninguna: las 38 mutaciones se aplicaron y las 38 pusieron en rojo el test de su escenario.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-28 estaba contradicho, y el escenario tenía razón.** El mensaje de configuración ilegible
   decía qué había pasado y no qué hacer: *"no es un JSON valido (Expecting property name…)"*, y
   ahí terminaba. El escenario pide las dos cosas, y el resto de los mensajes de este mismo cambio
   sí traen el imperativo. Se agregó la constante `QUE_HACER` y dos assertions. **El umbral no se
   movió: se movió el código.**

2. **E-10 estaba sin sustento, y era la mitad frágil de urllib.** El escenario dice "el código y el
   cuerpo, para 200 y para 401"; el test asertaba el cuerpo del 200 y del 401 solo el código. El
   cuerpo de un 4xx llega adentro de `HTTPError` y es exactamente lo que es fácil tirar sin querer
   — y es lo que lee el descubrimiento de capacidades de GitLab. Un `transporte_urllib` que
   devolvía `(e.code, "")` dejaba la suite entera verde.

3. **Dos assertions de E-24 eran decorativas.** Las que comprueban que el token no aparece ni en la
   salida ni en el documento no se ponían en rojo con ninguna mutación de fuga: en ese escenario
   Jira cae por timeout y no hay cuerpo que filtrar. Se cambió el servidor falso para que GitLab
   devuelva el token adentro del cuerpo del 200, y ahora sí atrapan.

4. **La cláusula "el orden" de E-03 no la agarraba nadie.** Un `_escribir` que ordenara las líneas
   dejaba el escenario verde. Se agregó la assertion del orden.

5. **El 📌 de E-33 atribuía mal los doce `.pyc`.** Decía que los compila la corrida de los cuatro
   hooks; son cinco de `hooks/lib` y siete de la corrida de los checks. Corregido en la spec.

6. **El conteo de la spec estaba corrido.** `## Cómo se verifica` decía treinta y siete: son treinta
   y ocho — los 34 numerados más los cuatro con sufijo.

7. **La primera tanda de mutaciones mezcló resultados por el caché de bytecode.** Restaurar un
   archivo al mismo tamaño dentro del mismo segundo deja el `.pyc` de la versión mutada como válido
   a ojos de Python, y dos escenarios se reportaron con el rojo de otro. Se rehízo con `-B` y
   `PYTHONDONTWRITEBYTECODE=1`. Es el mismo tipo de trampa que el `rojo visto` dependiente del reloj
   que documentó `dev-refutador-lee-el-contrato`, y conviene que quede escrito: **una tanda de
   mutaciones sin bytecode apagado no prueba lo que dice.**

## Lo que queda abierto, anotado y no escondido

- **Nada quedó contradicho ni sin sustento.** Los dos hallazgos de la primera pasada se corrigieron
  y la segunda los dio por sostenidos, sin tocar el texto de ningún escenario.
- **La reserva de E-28 se cerró después del veredicto.** El refutador anotó que `ConfigIlegible`
  tiene tres variantes y los tests recorrían una sola, atadas por compartir una constante. Se agregó
  una assertion sobre la variante "no es un objeto JSON" —y se la vio en rojo sacándole la
  constante—. **Esa assertion no es parte de lo que el refutador verificó**: E-28 está sostenido por
  las otras dos, y esto es cobertura extra agregada por quien construyó.
- **Ningún escenario prueba contra un Jira o un GitLab real.** Está declarado en
  `## Riesgos conocidos` de la spec y no es un hallazgo de la verificación: es el límite conocido
  del cambio. La primera corrida contra una instancia real del GCBA es lo que puede desmentirlo, y
  queda anotada en `Pendientes/Fix-Harness/PENDIENTES-FH.md`.

## Lo que ningún test cubre y se mira con los ojos

- **El asistente contra una instancia real.** La suite prueba el mapeo de estados con un transporte
  falso. Que `/rest/api/3/search/jql` sea el endpoint correcto para el Jira que usa el organismo, y
  que `/api/v4/personal_access_tokens/self` exista en el GitLab del GCBA, solo lo contesta correrlo.
- **Que el token no aparezca en la pantalla.** `getpass` no hace eco, y los tests comprueban que la
  salida no lo contiene — pero la sesión real de una consola de Windows, con su historial y su
  buffer, la mira una persona.
- **Que el flujo se entienda.** Si el asistente es amigable para alguien que acaba de bajar el
  proyecto no lo dice ningún assert.
