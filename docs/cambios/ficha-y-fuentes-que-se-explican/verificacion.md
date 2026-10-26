# Verificación — La Ficha de Proyecto y `fuentes` dicen por qué no encontraron lo que buscaban

**Estado:** cerrado · **Fecha:** 26-10-2026 · **Versión:** 0.36.1

Este documento es lo que cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto
por escenario de quien verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el
26-10-2026 sobre el árbol sin commitear de la rama `hallazgos-asi` (base `5a2d0ea`, v0.36.0), corriendo el caso nuevo y
mutando copias del árbol. Quien construyó no escribió ninguno de los dieciséis; escribió este archivo con lo que el
refutador devolvió.

**Resultado: 16 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | `setup` sin la clave dice el tipo por defecto, no escribe, no pregunta y `reconfigurar` no lo muestra | sostenido | sí | `79_ficha_y_fuentes_que_se_explican.py`, `test_e01` |
| E-02 | `setup` con la clave dice el tipo y que lo puso el proyecto, sin mostrar otras claves ni reescribir el archivo | sostenido | sí | `79`, `test_e02` |
| E-03 | Sin la clave se sigue buscando `Ficha de Proyecto` | sostenido | sí | `79`, `test_e03` |
| E-04 | `fuentes <CLAVE>` dice el tipo buscado y el proyecto, y solo eso | sostenido | sí | `79`, `test_e04` |
| E-05 | El rechazo de `--aceptar` lleva la causa y no escribe nada | sostenido | sí | `79`, `test_e05` |
| E-06 | Con dos Fichas dice cuántas y cuáles | sostenido | sí | `79`, `test_e06` |
| E-07 | Sin `jira.issue.search` dice que falta | sostenido | sí | `79`, `test_e07` |
| E-08 | Con Jira contestando error dice el código | sostenido | sí | `79`, `test_e08` |
| E-09 | El tipo parecido se nombra, en `fuentes` y en `contexto` | sostenido | sí | `79`, `test_e09` |
| E-10 | Un tipo que no se parece no se sugiere | sostenido | sí | `79`, `test_e10` |
| E-11 | Con Ficha no se agrega causa ni sugerencia | sostenido | sí | `79`, `test_e11` |
| E-12 | Con una clave el aviso sugiere la clave y no `--archivo` | sostenido | sí | `79`, `test_e12` |
| E-13 | Con `--archivo` el aviso es el de siempre | sostenido | sí | `79`, `test_e13` |
| E-14 | Sin canal el aviso nombra las dos formas | sostenido | sí | `79`, `test_e14` |
| E-15 | Los otros avisos de `hallazgos` no cambian | sostenido | sí | `79`, `test_e15` |
| E-16 | Con `--json` la causa no entra en el documento | sostenido | sí | `79`, `test_e16` |

> 📌 **`rojo visto: sí` en los dieciséis.** Salió de tres lugares: veintinueve mutaciones del código hechas por quien
> construyó (cada una rompe una cosa y vuelve atrás), cuarenta y seis hechas por quien verificó sobre una copia, y el caso
> nuevo corrido contra el código de 0.36.0, donde dio 30 de 54: rojo en E-01, E-02, E-04 a E-09, E-12, E-14 y E-15, y verde
> en E-03, E-11 y E-13, que son «lo que no cambia». E-10 y E-16 se pusieron en rojo contra 0.36.0 solo en parte, y por
> mutación en lo que les faltaba.

## Las guardas de Tasks cerradas

La primera corrida de las suites que fijan estos archivos dio cuatro rojos, uno en cada una: `65` EX-G11, `72` ME-E49,
`74` KA-E53 y el instalador de `63` (E-16). Las cuatro se adaptaron con «Pisado por» y el refutador leyó los diffs: no
están aflojadas más allá de lo que la spec declara.

- Las tres de Python salteaban el directorio `orquestacion` entero. Ahora saltean solo `registro_fuentes.py` y exigen, por
  AST contra la base, que cambió únicamente `hallazgos`, que se agregó únicamente `como_aceptar` y que lo que no es una
  función es igual. Cuatro mutaciones sobre ese archivo (cambiar otra función, agregar una, cambiar una constante, agregarle
  un decorador a una existente) ponen en rojo a las tres.
- La de PowerShell saltea en E-16 los dos archivos instalados que el cambio modifica (`contexto\proyecto.py` y
  `orquestacion\registro_fuentes.py`) y exige que lo instalado sea lo que hay en la fábrica. Es más estricta que las seis
  excepciones de accesibilidad de 0.36.0, que solo hacían `continue`. No se la mutó: el cambio que la pondría en rojo es un
  instalador que copie un archivo viejo.

## La compuerta

- **Primera compuerta completa, 26-10-2026:** `.\tests\Invoke-Tests.ps1` dio **50.959 de 50.959** (PowerShell 1.016,
  Python 49.943), salida 0, en 4.150 s. Corrió sobre el árbol con el caso nuevo y las cuatro guardas adaptadas.
- **Después de esa corrida cambiaron solo tests**, a partir de lo que encontró la verificación (abajo): `79`, y el
  ayudante de AST de `65`, `72` y `74`. Se corrieron los casos que cambiaron y los que los leen: `79` 68/68, `65` 679/679,
  `72` 550/550, `74` 2.378/2.378 y el instalador de `63` 191/191.
- **Segunda compuerta completa, sobre el commit del cierre (`4721de5`):** **50.961 de 50.962**, salida 1, en 4.864 s. El
  único rojo fue `72_motor_de_ejecucion` ME-E18, una carrera entre dos procesos que no es de este cambio (el motor no se
  tocó). `72` solo dio 550/550 en 383 s justo después. Anotado en `PENDIENTES-FH.md`.
- **No hubo una tercera compuerta en verde.** La versión se publicó con ese único rojo sin repetir, a pedido de Nahuel
  Palacio el 26-10-2026, que prefirió no esperar otra corrida de unos 70 minutos. Es la excepción a «verde antes de dar
  algo por hecho»: lo que la sostiene es la primera compuerta (50.959 de 50.959), `72` solo en verde y los casos focales
  de lo que cambió, no una compuerta completa verde sobre el commit publicado.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **El test de E-11 dejaba pasar una mutación** (la encontró quien construyó, antes de pedir el veredicto): con la condición
   de «no hay Ficha» reemplazada por `True`, el test seguía en verde, porque la Ficha de prueba no tenía huecos propios y
   no miraba que el canal fuera el de siempre. Se endureció con una Ficha que sí tiene un hueco y con el canal de `--json`.
2. **«Registro que no valida» estaba clavado solo por prefijo** (E-15, lo encontró el refutador). Una cola agregada después
   del prefijo no se detectaba. Ahora se clava la lista entera de avisos que da 0.36.0.
3. **Las aserciones de causa usaban `contiene`** (E-04, E-06 a E-10, lo encontró el refutador): una cola pegada a la causa
   pasaba todos los tests. Ahora la línea de causa se compara entera.
4. **Tres promesas de la spec sin test** (lo encontró el refutador): que `setup` no escribe `harness.config.json`, que no
   agrega otras líneas ni preguntas, y que `reconfigurar` no muestra la línea del tipo. Ahora E-01 y E-02 las prueban.
5. **El ayudante de AST de las tres guardas no veía un decorador agregado** a una función existente (lo encontró el
   refutador). Hoy `registro_fuentes.py` no tiene decoradores y no tenía efecto; se cerró igual.
6. **Los escenarios E-12 a E-14 dependían de que ES0901 siga sin hash en el registro de fábrica** (lo encontró el
   refutador). Hoy lo está, las seis fuentes. El caso ahora busca una fuente sin hash en vez de nombrar ES0901.
7. **La causa no podía ir en el canal que se guarda** (lo encontró quien construyó al escribir el código, antes de los
   tests): el canal se persiste en `harness.fuentes.json` y sale por `--json`. Quedó escrito como decisión en la spec.

## Lo que queda abierto, anotado y no escondido

- **El camino `--auto` no cambia, y ningún test del caso nuevo lo dice.** El refutador lo comparó contra 0.36.0 en cinco
  situaciones y dio idéntico; lo cuida `61_conocimiento_auto_refresco.py`, que pasa.
- **La documentación (`docs/contexto-de-tarea.md`) no tiene test.** Lo que dice se leyó contra el diff.
- **No se cambió el default a `.ASI Ficha de proyecto`:** sigue en `Pendientes/Fix-Harness/PENDIENTES-FH.md`, con su
  condición (saber si todos los proyectos de ese Jira usan ese nombre).
- **Quedan los otros hallazgos del registro de ASI**, en el mismo archivo: `[ES0903]` sobre un test, la salida del
  `-Update`, el aviso de `install.ps1` cuando `VERSION` no coincide con un tag, los tags 0.20.0 a 0.30.0, la licencia y la
  confirmación del `[a11y]` con el archivo real.

## Lo que ningún test cubre y se mira con los ojos

- **Correr `fuentes` contra el Jira real de ASI** con el tipo `.ASI Ficha de proyecto` y sin la clave, y ver la causa y la
  sugerencia en una terminal. Todo el caso corre contra un Jira simulado.
- **Que el texto en pantalla se lea bien** («causa: …», la línea de `setup`): los tests prueban que está, no que sea claro.
