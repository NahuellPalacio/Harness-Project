# Verificación — Bloque 4, contabilidad de ejecución y control de presupuesto

**Estado:** cerrado · **Fecha:** 20-09-2026 · **Versión:** sin publicar

Este documento es lo que cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md):
el veredicto por escenario de quien verificó, que no es quien construyó. Los emitió
`harness-spec-refuter` el 20-09-2026 en **seis pasadas**, corriendo `.\tests\Invoke-Tests.ps1`,
`python tests/correr.py -k b4_contabilidad`, una instalación real con `install.ps1` en un proyecto
temporal, el adaptador contra la transcripción real de esta máquina, y más de setenta mutaciones
propias sobre el paquete.

**Resultado: 40 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

Entre la primera pasada y la última, el refutador tumbó **seis** escenarios que estaban en verde:
uno contradicho y cinco sin sustento. Los seis se arreglaron subiendo el mecanismo. E-37 volvió
cuatro veces.

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Un evento valida contra su contrato | sostenido | sí | `30_b4_contabilidad.py`, `test_e01_…` |
| E-02 | Los dos schemas pasan por el validador | sostenido | sí | `test_e02_…` |
| E-02b | El validador lee `type` como lista | sostenido | sí | `test_e02b_…`, más las 3.246 restantes |
| E-03 | El libro es append-only | sostenido | sí | `test_e03_…`, barrido sobre el paquete entero |
| E-04 | Un evento repetido no entra dos veces | sostenido | sí | `test_e04_…` |
| E-05 | Una corrección es un evento nuevo | sostenido | sí | `test_e05_…` |
| E-06 | El mismo hecho cuenta una vez | sostenido | sí | `test_e06_…` |
| E-07 | Una línea por bloque no duplica | sostenido | sí | `test_e07_…`, y la transcripción real |
| E-08 | La ventana es una foto | sostenido | sí | `test_e08_…` |
| E-09 | Las cuatro clases van separadas | sostenido | sí | `test_e09_…` |
| E-10 | Un uso desconocido no es cero | sostenido | sí | `test_e10_…` |
| E-11 | Costo real y equivalente son dos | sostenido | sí | `test_e11_…`, los cinco modos |
| E-12 | Una suscripción no es gasto | sostenido | sí | `test_e12_…` |
| E-13 | Sin tarifa el costo no se resuelve | sostenido | sí | `test_e13_…`, todos los json que se instalan |
| E-14 | Todo costo conserva los siete campos | sostenido | sí | `test_e14_…` |
| E-15 | Lo derivado y lo reportado se guardan los dos | sostenido | sí | `test_e15_…` |
| E-16 | Las tres clases de tiempo van separadas | sostenido | sí | `test_e16_…` |
| E-17 | La pared no se disfraza de modelo | sostenido | sí | `test_e17_…` |
| E-18 | La jerarquía agrega | sostenido | sí | `test_e18_…` |
| E-19 | El total cierra | sostenido | sí | `test_e19_…`, las tres dimensiones |
| E-20 | Lo no atribuido no se reparte | sostenido | sí | `test_e20_…` |
| E-21 | El mismo libro da el mismo resumen | sostenido | sí | `test_e21_…`, tres procesos, tres semillas |
| E-22 | Sin política no hay límite | sostenido | sí | `test_e22_…` |
| E-23 | El límite blando avisa | sostenido | sí | `test_e23_…`, con sus bordes |
| E-24 | El límite duro y el proyectado | sostenido | sí | `test_e24_…` |
| E-25 | El Bloque 4 no aprueba | sostenido | sí | `test_e25_…`, más la lectura de `consumo.decidir` |
| E-26 | La decisión queda en el libro | sostenido | sí | `test_e26_…` |
| E-27 | El reporte sale del resumen | sostenido | sí | `test_e27_…` |
| E-28 | El Markdown nunca es la fuente | sostenido | sí | `test_e28_…`, lecturas clavadas por AST |
| E-29 | La barra es de la sesión activa | sostenido | sí | `test_e29_…` |
| E-30 | Cambiar de sesión no borra nada | sostenido | sí | `test_e30_…` |
| E-31 | Contexto y presupuesto son dos cosas | sostenido | sí | `test_e31_…` |
| E-32 | El núcleo no nombra ningún proveedor | sostenido | sí | `test_e32_…`, todo `.py` menos los adaptadores |
| E-33 | El adaptador conserva modelo y sesión | sostenido | sí | `test_e33_…`, y la transcripción real |
| E-34 | Sin fuente autoritativa queda sin resolver | sostenido | sí | `test_e34_…` |
| E-35 | Ningún agente llama a la contabilidad | sostenido | sí | `test_e35_…`, 11 agentes |
| E-36 | Ninguna skill llama a la contabilidad | sostenido | sí | `test_e36_…`, 27 skills |
| E-37 | El libro no puede guardar una conversación | sostenido | sí | `test_e37_…`, cuatro cierres y una medición |
| E-38 | La CLI ingiere, resume, reporta y muestra | sostenido | sí | `test_e38_…`, y desde un proyecto instalado |
| E-39 | Todo llega a un proyecto instalado | sostenido | sí | `test_e39_…` + `30-contabilidad-instalador.ps1` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá los 40 la tienen en
> `si`: la pasada de mutaciones rompió el código a propósito una vez por escenario, vio el rojo y
> revirtió, purgando `__pycache__` antes y después.

## Lo que la verificación encontró y no habría encontrado un test verde

Los seis salieron con la suite en verde. Ninguno se veía leyendo la lista de casos.

1. **E-37, contradicho — `metadata` era un campo libre y ahí entraba una conversación.** El
   refutador escribió un prompt entero en el libro, con una IP interna y una clave de admin
   adentro, y la limpieza devolvió cero hallazgos: un prompt no es un patrón de secreto.

2. **E-37, segunda vez — cerrar las claves de un nivel no cierra nada.** Con el vocabulario ya
   cerrado, `{"reason": {"prompt": "…"}}` pasaba limpio y una lista de veinte turnos guardaba
   4.200 caracteres sin que el recorte —que es por string— disparara una sola vez.

3. **E-37, tercera vez — la premisa del arreglo era falsa.** Yo había escrito que `metadata` era
   el único campo libre del contrato. El intérprete de subconjunto no tiene `additionalProperties`,
   así que **los cinco objetos son libres**: raíz, `usage`, `time`, `cost` y `source`. El
   refutador entró por cuatro caminos nuevos, incluido guardar dos mil caracteres en el **nombre**
   de un campo y una conversación codificada como un entero de 3.901 dígitos.

4. **E-37, cuarta y quinta vez — la medición, no el mecanismo.** El test armaba *un* evento grande
   a mano y lo llamaba *el máximo*, olvidándose cuatro campos; y después medía la línea
   serializada, que no es estable porque `json.dumps` escapa. El mismo evento pesa 10.266
   caracteres con relleno ASCII y 49.266 con caracteres de control.

5. **E-03 — el barrido de once nombres de función.** El refutador agregó
   `def compactar(ruta): os.remove(ruta)` y la suite pasó en verde. Encontró además que
   `agregacion.escribir` abre en modo `w` y truncaría el ledger si alguien le pasa esa ruta.

6. **E-13 — el barrido de tarifas miraba dos formas de una palabra y tres archivos.**
   `TARIFAS_USD = {"m-1": {"input": 3.0}}` pasaba, y `comun/reglas/`, `comun/schemas/` y el harness
   de análisis quedaban afuera del barrido.

7. **E-21 — dos llamadas en el mismo proceso no prueban determinismo.** Con
   `return list(abiertos)` en vez de `sorted`, la suite quedaba verde y el `summary.json` cambiaba
   entre corridas.

8. **E-28 — la mitad conductual no discriminaba.** `resumir` recibe eventos, no una ruta, así que
   corromper el `.md` no podía cambiar nada aunque otro módulo lo leyera. El refutador le agregó
   un lector de Markdown a `barra.py` y la suite pasó.

9. **E-32 — la lista fija de once archivos, y la excepción que tapaba lo que buscaba.** Un
   `nucleo_extra.py` con `if adapter == "claude-code"` adentro pasaba en verde, y la excepción de
   `.claude` seguía tapando `.claude-code` y `.claude.code`.

10. **Una banda floja deja bajar un techo en silencio.** Con `8.000 < techo < 10.000`, dos
    mutaciones que hacían medir de menos pasaban en verde y el número publicado quedaba mal. El
    número exacto clavado es, de las seis pasadas, lo que más va a durar.

Y dos que encontraron los propios invariantes al construirse:

11. **El barrido de E-32 encontró un nombre de modelo real en un docstring de `costos.py`.** El
    invariante funcionando sobre su propio autor.

12. **Cerrar la estructura destapó un hueco del contrato.** `cost.provider` y `cost.model` son dos
    de los siete campos que todo cálculo monetario conserva y el schema no los declaraba. La
    validación nueva los rechazó en la primera corrida.

## Lo que queda abierto, anotado y no escondido

Todo en `Pendientes/Fix-Harness/PENDIENTES-FH.md`, con su repro y su fecha:

| Qué | Por qué está abierto |
|---|---|
| Un campo declarado puede llevar un fragmento sensible que ningún catálogo reconoce | La limpieza del Bloque 2 sólo redacta lo de confianza alta, y esa decisión es de ese bloque. **Afirmado en verde** en E-37 |
| Trece tipos de evento y un solo productor | No existe el ejecutor que emitiría `AGENT_RUN_STARTED`. Declarado en `Qué queda afuera` |
| `.claude/runtime/accounting/` crece y nadie lo poda | No hay retención ni rotación |
| Un número absurdo del proveedor corta la ingesta entera | Defecto introducido por el tope numérico de hoy. **No se arregló**: no hay escenario que cubra esa conducta, y agregar comportamiento sin test es lo que el método prohíbe |
| Cuatro residuos en los barridos de E-03, E-13, E-28 y E-32 | Formas que nadie escribe hoy: `Path.write_text`, una tarifa como string, `Path.read_text`, un nombre de proveedor concatenado |

## Lo que ningún test cubre y se mira con los ojos

- **El reporte, leído por alguien que rinde cuentas.** `execution-cost.md` tiene las cifras que la
  suite verifica; si son las cifras que una persona necesita para explicar un gasto, eso lo dice
  quien tenga que explicarlo.
- **La barra, en una barra de verdad.** Lo que se construyó es el resumen normalizado que la barra
  consume. Que la línea degradada se lea bien en el ancho real de una barra de estado no lo puede
  decir un test de este repositorio.
- **Una tarea real, de punta a punta.** Todo lo que se midió salió de transcripciones: una
  sintética con la forma real y la de esta máquina. Lo que todavía no pasó es una tarea del
  harness, planificada por el Bloque 3 y contabilizada por el 4, con sus unidades de trabajo
  atribuidas. Hasta que eso pase, la atribución por agente y por unidad es un contrato sin
  llamador.
