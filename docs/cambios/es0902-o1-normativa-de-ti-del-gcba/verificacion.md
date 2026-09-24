# Verificación — ES0902 O1: la normativa de TI del GCABA como línea base, y la revisión que la mide

**Estado:** cerrado · **Fecha:** 22-09-2026 · **Versión:** 0.20.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 22-09-2026,
corriendo `python tests/correr.py -k 39_es0902` y la compuerta completa `.\tests\Invoke-Tests.ps1`,
y sondeando por afuera de las aserciones los cuatro puntos donde un test verde puede estar midiendo
otra cosa: el contenido inventado de E-08, la inalcanzabilidad de `COMPLIANT` de E-13 y E-20, el
"no reejecuta" de E-18 y la frontera por ausencia de E-24.

**Resultado: 28 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | O1 sigue `ALWAYS` con cero señales, y aplica con el diccionario vacío | sostenido | sí | `39_es0902_o1/test_e01`, la fila puesta en `CONDITIONAL` |
| E-02 | El dueño sigue siendo `dev-security`, y está declarado | sostenido | sí | `39_es0902_o1/test_e02`, el dueño cambiado a `dev-backend` |
| E-03 | Una policy y una review, con sus ids literales | sostenido | sí | `39_es0902_o1/test_e03`, el id de la policy renombrado |
| E-04 | O1 no declara ni instala ningún check, tampoco en disco | sostenido | sí, las dos mitades | `39_es0902_o1/test_e04`, un check agregado a la fila y un check de O1 al estilo de la casa |
| E-05 | Instalar O1 no agrega una fila ni un tercer estándar | sostenido | sí | `39_es0902_o1/test_e05`, una regla `O3` agregada a la matriz |
| E-06 | La línea base carga, valida, y también instalada | sostenido | sí | `39_es0902_o1/test_e06`, una fuente sacada del archivo |
| E-07 | ES0901 6.3 y ES0902 6.2 son las dos `LOADED`, y las únicas | sostenido | sí | `39_es0902_o1/test_e07`, ES0901 pasado a no cargada |
| E-08 | Las tres resoluciones entran con título y autoridad, sin contenido | sostenido | sí, específico | `39_es0902_o1/test_e08`, una versión y una vigencia agregadas a una resolución |
| E-09 | La línea base no es una matriz normativa ni entra bajo `standards` | sostenido | sí, las dos mitades | `39_es0902_o1/test_e09`, `rules` agregado al archivo, y la línea base metida bajo `standards` |
| E-10 | Un estado o una vigencia que no existen no validan, y el error nombra la fuente | sostenido | sí | `39_es0902_o1/test_e10`, el control de estado anulado |
| E-11 | Fuente sin cargar → `EXTERNAL_NORMATIVE_CONTEXT_REQUIRED` con su id | sostenido | sí | `39_es0902_o1/test_e11`, el estado vaciado |
| E-12 | Sin vigencia, o reemplazada sin decir por cuál → `NORMATIVE_SUPERSESSION_UNRESOLVED` | sostenido | sí | `39_es0902_o1/test_e12`, el default de vigencia puesto en `CURRENT` |
| E-13 | Con la línea base como vino, la review nunca cumple | sostenido | sí | `39_es0902_o1/test_e13`, los estados de la línea base dejados de bloquear |
| E-14 | Una review sin sujeto está incompleta | sostenido | sí | `39_es0902_o1/test_e14`, el control de sujeto anulado |
| E-15 | Línea base ausente, ilegible o inválida → `NORMATIVE_BASELINE_UNRESOLVED` | sostenido | sí, las tres | `39_es0902_o1/test_e15`, el rechazo de línea base anulado y el rechazo de JSON roto anulado |
| E-16 | Los resultados de ES0901 entran como evidencia, con su regla | sostenido | sí | `39_es0902_o1/test_e16`, la regla reemplazada por una constante |
| E-17 | Los de ES0902 entran igual, sin traducir el resultado crudo | sostenido | sí, específico | `39_es0902_o1/test_e17`, la tupla leída sólo de arriba |
| E-18 | O1 no reejecuta ningún control | sostenido | sí, las dos mitades | `39_es0902_o1/test_e18`, una llamada a `seguridad.resultado` metida en la review |
| E-19 | Sin resultados declarados no hay nada que reusar | sostenido | sí | `39_es0902_o1/test_e19`, el control de lista vacía anulado |
| E-20 | Un resultado aplicable que falla impide cumplir y titula | sostenido | sí | `39_es0902_o1/test_e20`, el fallo degradado a incompleto |
| E-21 | Contrato solo no levanta nada; aprobación sola tampoco | sostenido | sí, específico | `39_es0902_o1/test_e21`, la excepción concedida con una sola mitad |
| E-22 | Contrato y ASI conceden, y la excepción queda escrita | sostenido | sí | `39_es0902_o1/test_e22`, la excepción no pegada al resultado |
| E-23 | El mecanismo es el de ES0902, y una excepción no derrama | sostenido | sí | `39_es0902_o1/test_e23`, el id local aceptado además de la clave compuesta |
| E-24 | Cumplir O1 no produce ninguna aprobación oficial | sostenido | sí, específico | `39_es0902_o1/test_e24`, un `officialState: APPROVED` metido en el resultado |
| E-25 | Los cuatro resultados son los de `revisiones`, importados | sostenido | sí | `39_es0902_o1/test_e25`, `CUMPLE` redefinido por literal |
| E-26 | Todo resultado conserva `ES0902 / 6.2 / §3 / O1` | sostenido | sí | `39_es0902_o1/test_e26`, la sección cambiada a `7.1` |
| E-27 | No se crea ni se modifica ningún agente ni ninguna skill | sostenido | sí | `39_es0902_o1/test_e27`, un `dev-normativa` nombrado en el paquete de gobierno |
| E-28 | Los dos controles quedan declarados e instalados, sin sueltos | sostenido | sí | `39_es0902_o1/test_e28`, la review sacada del registro |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Los 28 de esta tabla llevan
> `sí`: la pasada se corrió entera, mutación por mutación, con `__pycache__` borrado antes y después
> de cada una.

La compuerta, al cierre:

```
.\tests\Invoke-Tests.ps1
  250/250 pasaron (PowerShell)
  24336/24336 pasaron (python), de los cuales 387 son 39_es0902_o1_normativa_gcba
  24586/24586 pasaron
```

## Lo que la verificación encontró y no habría encontrado un test verde

Tres deudas, **las tres cerradas antes de este documento**, y las tres de la misma familia: una
aserción que se satisface con algo más débil que lo que el escenario afirma.

1. **E-04 barría una grafía que este repositorio no escribe.** La tercera cláusula —*"no hay
   archivo bajo `controles/checks/` que cite O1"*— buscaba `rule: O1` y `"rule": "O1"` en el texto
   de cada check. Los trece checks del harness declaran la regla por constante —`REGLA = "D8"`— y
   la tupla por referencia —`{"rule": REGLA}`—, así que un check de O1 escrito como se escriben
   todos los demás pasaba el barrido. La cláusula quedaba sostenida por E-28 —`filesystemClean`—
   y no por sí misma, y el día que alguien afloje ese reporte se quedaba sin guardia.

   Cerrada: el barrido pasó a ser sobre los literales del módulo por AST, más el cruce contra el
   registro —cada `.py` de `controles/checks/` tiene que estar declarado y su regla no puede ser
   O1—. Se comprobó con un check de O1 escrito al estilo de la casa: la aserción vieja lo dejaba
   pasar, la nueva lo agarra con tres fallas.

2. **E-15 decía "ilegible" y no tenía ninguna aserción que lo nombrara.** Cubría *ausente* y
   *inválida*; un JSON corrupto no se probaba. Cerrada con un archivo roto en el árbol instalado, y
   puesta en rojo anulando el rechazo de `cargar`.

3. **Una cláusula de E-09 vivía bajo el id vecino.** *"No aparece bajo `standards` en el bloque
   normativo"* se afirmaba en el test de E-05, no en el de E-09. Está probada, pero estaba probada
   con otra etiqueta, y un escenario que se apoya en su vecino se queda sin prueba el día que el
   vecino cambie. Cerrada: la cláusula se afirma ahora en E-09, y se puso en rojo metiendo la línea
   base bajo `standards` en `normativa.resolucion`.

Y una nota que el refutador dejó y no es una deuda: **E-10 promete en "Cómo se verifica" un
invariante sobre todos los valores inválidos de estado y de vigencia, y el test muestrea uno de
cada uno.** No se cambió: el mecanismo es pertenencia —`not in ESTADOS_DE_FUENTE`, `not in
VIGENCIAS`— más el `enum` del schema, o sea universal por construcción y no una lista negra. Un
bucle sobre valores inventados no agregaría cobertura, agregaría ejemplos.

## Lo que queda abierto, anotado y no escondido

1. **`descubrir_no_declarados` no mira adentro de `controles/reviews/`.** Recorre `policies` con
   `.md` y `checks` con `.py`, y nada más. Un documento de review tirado ahí y no declarado en el
   registro no aparece en `reporte()["undeclared"]` y `filesystemClean` sigue en `true`. Hoy no
   hay nada mal —las tres reviews que existen están declaradas y reportan `INSTALLED`—, pero
   *"sin archivos sueltos"* cubre menos superficie de la que suena, en este cambio y en los cuatro
   anteriores que lo afirman. Anotado en `Pendientes/Fix-Harness/PENDIENTES-FH.md`, bajo
   *Incomplete capabilities*, con el arreglo: el tercer par en el mismo bucle.

2. **La review de O1 no puede cumplir, y va a quedar así mucho tiempo.** No es un defecto: es lo
   que la spec declara y lo que E-13 sostiene. Queda escrito acá porque es lo que más invita a que
   alguien "arregle" `gcba-it-normative-baseline.json` declarando `LOADED` o `CURRENT` sin
   evidencia. Lo que lo destraba es que llegue el contenido autoritativo de las tres resoluciones
   de la ASI, y eso no sale del harness.

3. **Los resultados que O1 reusa no los produce nadie todavía.** La review los recibe declarados,
   igual que la evidencia de G1 a D8 y de todo ES0902. Es la misma deuda de siempre y lo que la
   destraba es el análisis de impacto.

## Lo que ningún test cubre y se mira con los ojos

- **Que el paquete de gobierno, la policy y la review digan lo mismo que el módulo.** Los tests
  comprueban que los ids coincidan, que los cuatro resultados sean los de `revisiones` y que
  ningún artefacto nombre un agente que no existe. Que la prosa de los tres documentos describa el
  algoritmo que `linea_base.py` efectivamente corre es lectura, y ningún test lo puede contradecir.
- **Que el estado `DECLARED_EXTERNAL_NOT_LOADED` de las tres resoluciones siga siendo cierto.** El
  día que alguien cargue el contenido autoritativo de una de ellas, el archivo cambia y la review
  empieza a dar otra cosa. Que ese contenido sea el real y no una transcripción aproximada no lo
  puede comprobar el harness: es exactamente la frontera que este cambio existe para no cruzar.
