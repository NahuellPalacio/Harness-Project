# Verificación — El mapa de nodos del código

**Estado:** cerrado · **Fecha:** 30-08-2026 · **Versión:** 0.14.0

Este documento es lo que cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md):
el veredicto por escenario de quien verificó, que no es quien construyó.

**Primera pasada de `harness-spec-refuter`**, el 30-08-2026 — este cambio no tenía `verificacion.md`
todavía. Corrió `python tests/correr.py -k mapa_nodos` (56/56) y `.\tests\Invoke-Tests.ps1` completo
(**772/772**), y verificó los cuatro escenarios de lectura recién firmados en
[`lectura.md`](lectura.md) contra el material real de [`recorrido-real.md`](recorrido-real.md):
contrastó cada `Observado` cifra por cifra —la matriz de aristas, las tres horas de escritura, la
cita textual del informe— contra el registro de la corrida, y confirmó que la lectura es genuina y
no una copia de la prosa de quien construyó.

**Resultado: 23 escenarios sostenidos, 4 leídos (independientes), 0 leídos (delegados), 0
contradichos, 0 sin sustento.**

**El cambio cierra.**

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Todo módulo con ficha propia aparece enlazado | leído, independiente | no consta | [`lectura.md`](lectura.md) — Nahue Palacio, 30-08-2026 |
| E-02 | Una dependencia sin ficha se nombra sin enlace | sostenido | sí | `test_e02_una_dependencia_sin_ficha_se_nombra_sin_enlace_y_no_pasa_nada` |
| E-03 | Ninguna ficha usa un `[[wikilink]]` fuera de código | sostenido | sí | `test_e03_una_ficha_con_wikilinks_se_reporta` |
| E-03b | Un `[[...]]` entre backticks es documentación, no wikilink | sostenido | sí | `test_e03b_un_wikilink_entre_comillas_invertidas_es_documentacion` |
| E-04 | Un enlace roto produce hallazgo con origen y destino | sostenido | sí | `test_e04_un_enlace_a_una_ficha_que_no_existe_se_reporta` |
| E-05 | Ese hallazgo no bloquea | sostenido | sí | `test_e05_el_hallazgo_avisa_y_no_bloquea` |
| E-06 | Un enlace a `indice.md` no es hallazgo | sostenido | sí | `test_e06_el_enlace_al_indice_no_es_un_hallazgo` |
| E-07 | Una escritura fuera del directorio no dispara nada | sostenido | sí | `test_e07_una_escritura_fuera_del_directorio_no_dispara_nada` |
| E-08 | Dos corridas producen el mismo `mapa.html` byte a byte | sostenido | sí | `test_e08_dos_corridas_dan_el_mismo_byte` |
| E-09 | `mapa.html` no referencia nada externo | sostenido | sí | `test_e09_el_html_no_referencia_nada_de_afuera` |
| E-10 | Un nodo por ficha, sin contar `indice.md` | sostenido | sí | `test_e10_un_nodo_por_ficha_sin_contar_el_indice` |
| E-11 | Dos enlaces A→B producen una sola arista | sostenido | sí | `test_e11_dos_enlaces_a_la_misma_ficha_son_una_arista` |
| E-12 | La ficha que nadie enlaza queda marcada huérfana | sostenido | sí | `test_e12_la_ficha_que_nadie_enlaza_queda_marcada` |
| E-13 | Un ciclo A→B→A se dibuja y el generador termina | sostenido | sí | `test_e13_un_ciclo_se_dibuja_y_el_generador_termina` |
| E-14 | Sin fichas no escribe `mapa.html`, y lo dice | sostenido | sí | `test_e14_sin_fichas_no_escribe_y_lo_dice` |
| E-15 | No abre archivos fuera del directorio de fichas | sostenido | sí | `test_e15_e16_solo_toca_el_directorio_de_las_fichas` |
| E-16 | No escribe nada que no sea `mapa.html` | sostenido | sí | `test_e15_e16_solo_toca_el_directorio_de_las_fichas` |
| E-17 | Corre con Python 3.9, solo biblioteca estándar | sostenido | sí | `test_e17_solo_biblioteca_estandar_y_sintaxis_de_39` |
| E-18 | Terminado el recorrido, están fichas, índice y mapa | leído, independiente | no consta | [`lectura.md`](lectura.md) |
| E-19 | El mapa se regenera después del índice, no antes | leído, independiente | no consta | [`lectura.md`](lectura.md) |
| E-20 | El informe dice nodos, aristas y nombra las huérfanas | leído, independiente | no consta | [`lectura.md`](lectura.md) |
| E-21 | Cada ficha va embebida como `<article>` propio | sostenido | sí | `test_e21_cada_ficha_va_embebida_en_la_pagina` |
| E-22 | Cada nodo es un `<a href>` a su ficha | sostenido | sí | `test_e22_cada_nodo_es_un_enlace_a_su_ficha` |
| E-23 | El texto de una ficha sale escapado | sostenido | sí | `test_e23_el_html_de_una_ficha_sale_escapado` |
| E-24 | Un enlace hermano cambia de ficha, uno externo no | sostenido | sí | `test_e24_un_enlace_a_una_hermana_cambia_de_ficha_y_uno_de_afuera_no` |
| E-25 | La rueda desplaza la página, el zoom pide Ctrl | sostenido | sí | `test_e25_el_mapa_no_atrapa_el_desplazamiento_de_la_pagina` |
| E-26 | El puntero no queda capturado por el `<svg>` | sostenido | sí | `test_e26_el_clic_llega_al_nodo_y_el_arrastre_termina` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Aplica a los cuatro `leído,
> independiente`: su sujeto es una corrida de un agente con modelo, y eso no se rompe a propósito.

## La lectura de los cuatro, firmada hoy

Los cuatro escenarios de lectura tienen por sujeto una corrida real de `dev-iniciador-code` —a qué
enlaza, en qué orden escribe, qué dice su informe— y ninguno tiene forma de test determinista: nada
puede obligar a un modelo a enlazar bien ni a ordenar su escritura. `harnesses/desarrollo/agents/dev-iniciador-code.md`
confirma en el propio contrato del agente las tres reglas que estos escenarios verifican.

El material es [`recorrido-real.md`](recorrido-real.md): una corrida del 22-08-2026 sobre un clon de
`ProtfolioPersonal` (Next.js/TypeScript, ajeno a este repositorio, elegido para que las fichas no
vinieran enlazadas a mano). No hubo un segundo proyecto disponible hoy para correr de nuevo, y el
mecanismo ya está probado con esa corrida — decisión tomada en esta sesión, reemplazando la del
22-08-2026 de esperar a un proyecto propio, que sigue siendo la vía preferida a futuro y no se
descarta.

`recorrido-real.md` dice en su propio encabezado que lo escribió quien construyó, así que no sirve
como lectura por sí solo. La lectura la firmó **Nahue Palacio**, distinto del constructor, el
30-08-2026, con cuatro `Observado` verificados cifra por cifra contra ese material —la matriz de
aristas, las tres horas de escritura, la cita textual del informe, la suma de las veinte aristas—
y no una copia de su prosa.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **Nada.** Es la primera pasada sobre este cambio y los 27 escenarios (26 más E-03b) resultaron
   sólidos: 23 con test que los nombra y rojo visto confirmado por quien construyó, y los cuatro de
   lectura con material real que sostiene lo que afirman, verificado cifra por cifra contra ese
   material y no contra la palabra de nadie.
2. **La firma dictada funcionó según lo previsto.** Con cuatro pendientes —por debajo del umbral de
   cinco de [ADR-0010](../../adr/0010-firma-delegada-de-una-lectura-cuando-son-muchas.md)— no
   correspondía la vía delegada, y no se usó: la firma quedó rotulada `Leyó:`, no
   `Firmó (delegado):`.

## Lo que queda abierto, anotado y no escondido

Nada de este cambio queda abierto. `Pendientes/Fix-Harness/PENDIENTES-FH.md` pierde la entrada de
`mapa-de-nodos` bajo *Verification that was not done* — se firmó, no se parkeó más — y lo que había
ahí pasa a `docs/versiones/0.14.0.md`.

## Lo que ningún test cubre y se mira con los ojos

Los cuatro escenarios firmados —E-01, E-18, E-19, E-20— dependen de que un agente con modelo
recorra un repositorio real, y la suite de este repositorio son tests deterministas y sin red. La
evidencia está en [`lectura.md`](lectura.md), sobre el material de [`recorrido-real.md`](recorrido-real.md).

Y lo que sólo confirma abrir el mapa en un navegador de verdad: que el panel abra al hacer clic en
un nodo, que la rueda desplace la página sin atajo y el zoom pida Ctrl, y que arrastrar el lienzo no
dispare el clic de un nodo. `recorrido-real.md` lo nombra como agujero declarado de la spec y sigue
sin cerrarse leyendo — se cierra abriendo el archivo.
