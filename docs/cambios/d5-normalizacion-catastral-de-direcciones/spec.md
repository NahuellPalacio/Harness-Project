# D5 — Las direcciones del frontend se normalizan con la opción catastral del GCBA

**Estado:** verificado y cerrado · **Fecha:** 21-09-2026 · **Regla:** ES0901 6.3 §7.1 D5

## Qué problema resuelve

La regla citable, `ES0901-7.1-D5`, pág. 13:

> *"Toda busqueda o carga de direcciones en un frontend tiene que validarse y normalizarse con la
> opcion catastral del GCABA."*

Y la primera frase del párrafo **Georreferenciación**, pág. 19:

> *"Las aplicaciones deben contar con direcciones de calles normalizadas y validadas a través del
> servicio de API GEO disponible en el catálogo."*

Es el párrafo que ya trabajó D6, leído por la otra punta: su **primera** frase es D5 y la segunda es
D6. Están pegadas en el documento y son independientes.

La matriz declara la fila de D5 con su señal y sus dos controles desde que se construyó, y los dos
controles **no existen**: hoy cualquier consulta los reporta como `DECLARED_POLICY_NOT_INSTALLED` y
`DECLARED_CHECK_NOT_INSTALLED`, y está afirmado **en verde** en `31_d6/E-26`.

📌 Y es la única regla **cuyo paquete de gobernanza llegó y no se instaló**. Las otras dieciséis
reglas condicionales también declaran controles que no existen —son 24 filas y 16 controles
construidos—, pero eso es el estado normal de una instalación de a una regla: su paquete todavía no
llegó. D5 es la que quedó colgada.

### Lo que hace difícil a esta regla, y no es lo mismo que en D6

D6 pregunta **con qué se dibujó** una vista: una comparación de identificadores. D5 pregunta algo
estructuralmente más difícil:

```
input crudo  →  request al proveedor  →  response del proveedor  →  resultado normalizado
                                                                    →  valor CONSUMIDO
```

El defecto que D5 existe para atrapar no es *no se llamó al servicio*. Es **se llamó, y después se
guardó el valor crudo**. Un check que verifique la llamada se pone verde sobre una aplicación que no
cumple, y es el error más natural de todos: la llamada es lo visible.

🔴 **Y la segunda mitad del problema es la cobertura.** El camino de búsqueda con autocompletado es
el que alguien construye bien y el que alguien enumera. La carga manual de texto libre y la edición
de una dirección guardada son los que nadie menciona. Un check que verifique los caminos que le
declaran se pone verde por omisión.

## Qué queda afuera

- **El contrato técnico de la opción catastral.** No se declara endpoint, campo de request, campo de
  response, identificador catastral, campo de coordenadas, autenticación, timeout, reintento ni URL
  de ambiente. El harness no los tiene. Sin ellos: `INTEGRATION_CONTRACT_MISSING`.
- **Ejecutar un frontend.** Este módulo no abre un navegador y no carga una dirección. La corrida
  entra como dato, igual que en D4 y D6, y quien la ejecute son las skills que ya están instaladas.
- **Crear o modificar una skill.** El pedido lo prohíbe explícitamente (§1). La fila de D5 en la
  matriz tiene cero referencias a skills y sigue así.
- **D6.** Que una dirección normalizada traiga coordenadas no dice nada sobre qué mapa las dibuja.
  Este cambio no toca el check de D6 salvo el test que se nombra más abajo.
- **P5.** La validación duplicada en frontend y backend es otra regla, con su propia señal y sus
  propios controles. D5 mira **el frontend**, y no informa nada sobre el backend.
- **Arreglar el instalador.** `install.ps1` no copia `controles/`, así que después de este cambio
  son dieciocho controles que declaran `INSTALLED` y que fuera de este repositorio serían
  `CONTROL_FILE_MISSING`. Es el ítem 2 de la tabla de prioridades, tiene su propia spec, y este
  cambio lo empeora en dos y lo dice.

## Qué le toca a D6

Dos tests de D6 se ponen en rojo al instalar D5, y los dos estaban escritos así a propósito:

| Test de D6 | Qué afirmaba | Qué afirma ahora |
|---|---|---|
| `E-26` | los dos controles de D5 **no** están en el registro | están instalados, y el resultado de D6 sigue sin decir nada sobre ellos |
| `E-30` | son **dieciséis** controles declarados | son **dieciocho** |

La proposición de E-26 era *el hueco de D5 se ve*. Ese hueco se cierra acá, así que el test se
**reescribe a su proposición sucesora** y no se borra: lo que E-26 cuidaba era la frontera, y la
frontera sigue viva. La función pasa a llamarse `test_e26_d5_esta_instalado_y_d6_no_cambio`, y suma
el barrido sobre los nueve caminos de D6 para afirmar que ninguno nombra a D5 ni a sus controles.

E-30 clava un número exacto a propósito: una banda floja dejaría instalar la regla siguiente sin que
nadie tenga que mirar este test.

`verificacion.md` de D6 queda como está: es un registro fechado, y lo que cambió después se cuenta
acá.

## Las decisiones, y por qué

### D5 sí puede citar el nombre del servicio; lo que no tiene es su contrato

Acá hay una diferencia real con D6 y conviene no perderla. El mecanismo del Mapa del GCBA **no está
en ningún extracto** de este repositorio: D6 no puede resolver su proveedor en ningún proyecto de
hoy. D5 sí: el párrafo de la pág. 19 nombra el servicio, está transcripto en
`normativa/extractos/ES0901.md`, y un proyecto puede citarlo como fuente de la identidad con
`GCBA_NORMATIVE`.

```
D6   que mecanismo es el Mapa del GCBA           no esta en ningun extracto
D5   que servicio es la opcion catastral         lo nombra la pag. 19
D5   como se ve usarlo                           no esta en ningun extracto
```

Así que para D5 el hueco vivo es el **contrato**, no la identidad. Los dos estados siguen siendo dos
porque son dos preguntas, y las contestan personas distintas:

```
CADASTRAL_PROVIDER_UNRESOLVED   cual es la integracion que hace de opcion catastral aca
INTEGRATION_CONTRACT_MISSING    esta identificada, y como se ve usarla no se sabe
```

🔴 **Citar el nombre no es tenerlo.** Que la norma escriba el nombre del servicio no le da al harness
un endpoint, un campo ni una autenticación, y el check no infiere identidad de una URL genérica, de
un nombre de paquete ni de que haya autocompletado. La identidad entra como dato declarado con su
fuente citada, igual que en D6.

### El check compara identificadores de valor, nunca contenidos de dirección

La cadena se verifica comparando **tokens opacos**. Cada resultado declara, por etapa, un `valueId`
—un hash, una etiqueta, lo que la corrida produzca—:

```yaml
chain:
  RAW_INPUT:         v-a1
  PROVIDER_REQUEST:  v-a1
  PROVIDER_RESPONSE: v-b7
  NORMALIZED_RESULT: v-b7
  CONSUMED_VALUE:    v-b7
consumedFrom: NORMALIZED_RESULT
```

El check no mira qué dice una dirección, no parsea una calle y no sabe qué campos trae un response.
Compara si el token consumido es el normalizado o es el crudo. Es la misma doctrina que hace correcto
al check de D6 sin saber qué es el Mapa del GCBA: **identificadores, nunca mecanismos**.

Las cinco etapas son las que nombra el §8 del pedido. No son campos del proveedor: son el modelo que
el check tiene de la cadena, y por eso pueden estar escritos acá sin inventar nada.

### Se exigen las dos cosas: el token y la etapa declarada

```
consumido == normalizado  y  consumedFrom == NORMALIZED_RESULT   ->  se consume
consumido == crudo        (y crudo != normalizado)               ->  FAIL, valor crudo
consumedFrom == RAW_INPUT y el token lo confirma o no discrimina  ->  FAIL, valor crudo
consumedFrom == RAW_INPUT y el token dice que se uso el normalizado
                                                                  ->  PARTIAL, incoherente
consumido no es ninguno de los dos                                ->  PARTIAL, sin rastro
consumedFrom no dice NORMALIZED_RESULT y el token si              ->  PARTIAL, etapa sin declarar
falta el RESPONSE **y** el resultado normalizado, y hay consumido  ->  FAIL, crudo como
                                                                     normalizado
falta cualquier otra etapa                                        ->  PARTIAL, cadena incompleta
```

Pedir sólo la etapa declarada deja que una corrida diga la palabra correcta; pedir sólo el token deja
pasar una corrida que consume el normalizado por casualidad y no lo declara. Se piden las dos, y la
que manda cuando discrepan es **el token**.

🔴 **El orden de las guardas es parte de la decisión, no un detalle de implementación.** La primera
versión evaluaba «cadena incompleta» antes que las guardas del valor crudo, y con eso un bypass
**probado** —la llamada ocurrió, hay respuesta, y el token consumido es el crudo— se informaba como
`NORMALIZATION_CHAIN_INCOMPLETE`: el estado de lo que no se sabe, puesto sobre algo que sí se sabe.
Es la especie contra la que avisa el propio módulo un nivel más abajo.

🔴 **Y `RAW_INPUT_TREATED_AS_NORMALIZED` exige que falten las dos etapas, no una.** Con un `or`, una
cadena que llega al resultado normalizado y no declara la respuesta salía `FAIL` con un detalle que
decía *"no hay resultado normalizado"* cuando sí lo había: una afirmación de incumplimiento contra
los propios tokens del caso.

🔴 **Y cuando la etapa declarada contradice al token, manda el token y el resultado lo dice.** El
flujo declara que usa el crudo y sus tokens muestran que usa el normalizado: eso no es un
incumplimiento probado —afirmarlo sería una afirmación falsa con la tupla normativa adosada, que es
justo lo que E-20 prohíbe— y tampoco está confirmado, así que no pasa. Estado `PARTIAL`, motivo
`CHAIN_DECLARATION_INCOHERENT`.

### Cuando el crudo y el normalizado son el mismo valor, la comparación no discrimina, y se dice

Si el proveedor devuelve exactamente lo que la persona escribió, los tres tokens son iguales y
*consumir el crudo* y *consumir el normalizado* son indistinguibles. Es un caso legítimo y frecuente,
así que **pasa**; y el resultado lleva `NORMALIZATION_INDISTINGUISHABLE` para que se lea que la
comparación fue degenerada.

📌 Bajarlo a `PARTIAL` sería poner en rojo a todo proyecto que valide una dirección ya normalizada, y
un check que se pone en rojo sin motivo es un check que alguien apaga. El residuo queda **clavado en
verde**: el día que se quiera cerrar, el test obliga a hablarlo.

### Los cinco tipos de camino se declaran todos, y el silencio no es ausencia

El pedido enumera cinco (§5, §7):

```
SEARCH           busqueda
MANUAL_ENTRY     carga manual
SELECTION        seleccion de una sugerencia
EDIT_UPDATE      edicion de una direccion guardada
ALTERNATE_INPUT  camino alternativo o de respaldo
```

El inventario declara, **para cada uno de los cinco**, o sus flujos, o una ausencia con su fuente.
Un tipo en silencio deja el resultado en `ADDRESS_FLOW_COVERAGE_UNRESOLVED`.

🔴 Es la misma doctrina que sostiene la señal —*la ausencia de una palabra no es evidencia de
ausencia*— aplicada a la cobertura. Sin esto, el bypass de carga manual se disimula no
mencionándolo, que es exactamente la forma que tiene el defecto en la vida real: el camino
compliant enumerado, el otro no.

Acá la enumeración es correcta porque **los cinco tipos los fija el pedido**, no yo. Lo que no se
enumera es el inventario de flujos dentro de cada tipo: eso lo declara el proyecto, con su fuente.

### Un camino inactivo exige fuente, aparece en la salida, y no puede vaciar el conjunto gobernado

Un flujo declarado inactivo —detrás de un flag apagado, código muerto— no debería bloquear. Pero un
flujo que el proyecto saca de la verificación declarándolo solo es **la puerta de salida que D6 ya
tuvo que sacar**: ahí fue `materiality: MINOR`, y una vista marcada menor dibujando con otro mapa
daba `PASS` y no aparecía en ningún campo de la salida.

Así que la puerta existe con tres cerrojos:

```
1. inactivo exige `source` de la lista de fuentes de cobertura; sin fuente se trata como ACTIVO
2. todo inactivo aparece en `inactiveFlows` de la salida
3. si no queda NINGUN flujo activo con la senal en TRUE, el resultado es
   ADDRESS_FLOW_COVERAGE_UNRESOLVED
```

El tercero es el que cierra el bypass completo: la señal afirma que hay un flujo de direcciones en
alcance, y declararlos todos inactivos contradice la señal. No se sabe, y eso no es `PASS`.

**El defecto por omisión es activo.** Lo que no se declara, se verifica.

🔴 **Y el cuarto cerrojo: un resultado sobre un flujo declarado inactivo es evidencia de que ese
flujo corrió.** La primera versión sacaba esos resultados de la cuenta entera —no estaban en
`flows`, no estaban en `ignoredResults`, no los nombraba ningún aviso—, así que un flujo declarado
inactivo cuya corrida reportaba otro normalizador y consumía el valor crudo daba `PASS` sin un solo
rastro. Era la última forma que le quedaba a la puerta que D6 tuvo que sacar. Ahora esos resultados
pasan por la misma pregunta que los de afuera del inventario; uno limpio se lista y no acusa nada,
porque probar un camino muerto no es un incumplimiento.

### Las cuatro puertas se cierran con `is True`, no con un truthy

```
scopeCompleteness.complete    saca a D5 del reporte
addressFlows.paths[].absent   saca un tipo de camino entero de la verificacion
testTarget.available          habilita la evaluacion
flows[].active: False         saca un flujo de la verificacion  (ya exigia el False literal)
```

Las cuatro son campos booleanos que un proyecto declara, y con un truthy cualquiera un
`"absent": "false"` —escrito por quien quería decir que el camino **no** está ausente— sacaba ese
tipo de la verificación, y un `"available": "no"` daba `PASS`. La primera es la peor de las cuatro
porque su sentido de falla **hace desaparecer la regla del reporte**, y una regla que desaparece no
se vuelve a buscar.

### La derivación tiene que ser de `frontendPresent`, y publica la señal que entró

La primera versión no le miraba el `signalId` a la señal que recibía en ese lugar y publicaba la
constante como origen: pasarle **cualquier** otra señal en FALSE derivaba igual y le atribuía el
FALSE a `frontendPresent`. La derivación decía de dónde salió y no era cierto.

### Un tipo de camino declarado dos veces no se sobrescribe

`por_clase[clase] = camino` dejaba la primera entrada sin validar mientras el recorrido de flujos
seguía viendo las dos. Con eso, un flujo **sin id** llegaba a ser gobernado con el id vacío:
la validación se evadía duplicando el tipo. Si un tipo tiene dos grupos de flujos, van en una
entrada.

### Un dato malformado sale por uno de los nueve estados, no por una excepción

Un `paths` que viene como diccionario, un camino que viene como texto, un `flows` que viene como
lista de strings: la forma se controla **antes** de recorrerla. Un dato que rompe el módulo no es un
dato que falló cerrado — es un dato sobre el que el módulo no contestó nada.

### El alcance de la señal y el de la evaluación tienen que ser el mismo, o la relación se declara

Esto es propio de D5 (§4) y no tiene análogo en D6. La señal y la evaluación llevan su alcance:

```yaml
scope: {id: <cual>, kind: PROJECT | WORKUNIT | TASK, reference: <donde lo dice>}
```

```
alguno sin declarar                      ->  APPLICABILITY_UNRESOLVED / SCOPE_UNDECLARED
una senal que no es un documento         ->  APPLICABILITY_UNRESOLVED / SCOPE_UNDECLARED
distintos, sin relacion declarada        ->  APPLICABILITY_UNRESOLVED / SCOPE_MISMATCH
distintos, con relacion y referencia     ->  se evalua, y la relacion va en la salida
```

El check **no adjudica la lógica** de la contención: exige que la relación esté declarada y citada,
y la publica en `scopeRelation` para que nadie lea un `PASS` sin ver que se apoyó en una afirmación
entre alcances. Una evidencia de todo el proyecto sosteniendo la aplicabilidad de una unidad de
trabajo es defendible o no según el caso, y el que sabe es quien la declara — pero no puede ser
invisible.

`scope` se agrega como campo **opcional** de `normative-signal.schema.json`: toda señal tiene un
alcance de orquestación, ninguna otra regla lo exige hoy, y las señales que ya existen siguen
validando.

🔴 **Y `senales.resolver_una` tiene que conservarlo.** Sin eso, el campo existe en el documento y
desaparece en la resolución, así que la única forma de que el check lo vea es pasarle el documento
crudo — y toda corrida real, que llega por `normativa.resolucion`, sale `SCOPE_UNDECLARED`. El
mecanismo quedaría **estricto donde el dato no puede cumplir y laxo donde no se declaró nada**, que
es exactamente al revés. Es un cambio de una línea en `senales.py`, al lado de la que ya conserva
la tupla normativa, y es el único que este cambio le hace a un módulo compartido.

🔴 **Y la forma vieja de una señal —un booleano suelto, un string— no puede declarar alcance**, así
que su alcance es ambiguo por construcción y eso es `SCOPE_UNDECLARED`, no un salteo. La primera
versión hacía `continue` sobre lo que no fuera un diccionario, y con eso `evaluar(caso, True)` salía
`PASS`: la guarda entera se evadía con la forma que el propio módulo declara soportar.

### `frontendPresent` en FALSE puede resolver a D5, y sólo con completitud declarada

El pedido lo dice en las dos direcciones (§3, D5-06, D5-07):

```
frontendPresent = TRUE   ->  NO implica nada. Un frontend no es un campo de direccion
frontendPresent = FALSE  +  completitud de alcance declarada  ->  D5 puede resolver FALSE
frontendPresent = FALSE  sin completitud                      ->  UNRESOLVED
```

La derivación vive en el check de D5, no en `senales.py`: es la única regla que la tiene, y montar un
marco genérico de derivaciones para un caso es construir de más. Entra como
`scopeCompleteness: {complete, source, reference}`, con `source` de la lista de fuentes de cobertura
—un booleano suelto sería otra puerta sin fuente—, y la salida registra
`DERIVED_FROM_FRONTEND_ABSENT` cuando la usó.

📌 Esto toca un pendiente viejo: *nada exige «unless project coverage is known to be complete»*.
Acá queda exigido para D5. Para las demás reglas sigue abierto.

### Lo que está instalado no prueba lo que se consume

La partición de evidencia es la razón de ser del check, y sale del §5 de la policy y del §7 del
pedido, uno a uno:

```
NORMALIZED_ADDRESS_RUN         prueba. Es la unica que prueba
SCREENSHOT                     acompana
HUMAN_CONFIRMATION             acompana
INTEGRATION_TEST               acompana

AUTOCOMPLETE_COMPONENT_PRESENT inerte: un autocompletado que existe no es una direccion normalizada
ADDRESS_API_CALL               inerte: que se llame a una API de direcciones no dice cual, ni que
                               su resultado se use
COORDINATE_DATA                inerte: hay coordenadas en cualquier base de datos, y ademas eso
                               apunta a D6
REGEX_VALIDATION               inerte: un regex valida una forma, no valida una direccion
POSTAL_CODE_LIBRARY            inerte: un paquete instalado no es una integracion
FRONTEND_FIELD_VALIDATION      inerte: validar un campo no es normalizarlo
REPOSITORY_DEPENDENCY          inerte: lo que HAY no es lo que se HACE
AGENT_STATEMENT                inerte: una opinion con formato de evidencia
```

### Un blanco no es un dato declarado, y se normalizan LOS DOS lados

Todo campo de identidad —proveedor, contrato, id de flujo, tokens de la cadena, alcance— se lee sin
blancos, **en cada lado de cada comparación**. Es la lección de D6/E-11 y de su arreglo: normalizar
un solo lado produjo dos defectos nuevos, y uno fue una regresión que convirtió un estado que
avisaba en uno que calla.

### Ningún artefacto de D5 lleva el contrato, y sí puede llevar la cita

El barrido de D5 es distinto del de D6 en una cosa importante: **el nombre que la norma escribe está
permitido**. Una cita no es una invención, y prohibirla pondría en rojo a la propia transcripción del
extracto. Lo que se prohíbe es el contrato:

```
localizadores de red      con esquema, sin esquema, con puerto -con o sin punto-, o una IP
credenciales              bearer o token con un numero adentro, api_key, access_token, client_secret
paquetes                  el gestor, el @scope/nombre, y como se importa
sistemas de coordenadas   con etiqueta (EPSG/SRID/CRS) o el codigo suelto
campos de contrato        request. response. body. payload. seguidos de un nombre
vocabulario catastral     los nombres reales de los campos del catastro porteno
tiempos y reintentos      timeout o retry seguidos de un numero con unidad
mecanismo declarado       endpoint, base url, sdk, client id seguidos de : o =
```

Los nombres del vocabulario catastral viven **en el test, no en los artefactos** — la misma
resolución que tomó D6 con los nombres de proveedores de mapas. Todos los patrones llevan `(?i)`:
cuatro de los de D6 no lo llevaban y una constante en mayúscula escapaba entera, que era una
dimensión completa del barrido y no una forma suelta.

El test tiene **tres** mitades, como el de D6: los seis textos limpios; las formas crudas de fuga
—sin acomodarlas al patrón— que tienen que disparar; y los textos legítimos que **no** tienen que
disparar, entre ellos la cita de la pág. 19 y la fila citable de la regla.

### Se reutiliza la infraestructura, no se construye una segunda

`senales.py` resuelve la señal, `matriz.py` la aplicabilidad, `controles.py` el registro y
`registro_agentes` el ruteo y los agentes primarios. El cambio no agrega ni un módulo de
orquestación.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `controles/policies/gcba-cadastral-address-normalization-required.md` | La policy de D5, con su frontera de proveedor y contrato |
| `controles/checks/address-normalization-integration.py` | El check: nueve estados, cinco caminos, la cadena de cinco valores y el alcance |
| `reglas/control-registry.json` | Los dos controles de D5, declarados |
| `comun/schemas/normative-signal.schema.json` | `scope` opcional, para §4 |
| `harnesses/desarrollo/bin/orquestacion/senales.py` | conserva `scope` al resolver — una línea, y el único cambio a un módulo compartido |
| `docs/normativa-7.1.md` | D5, la cadena que se verifica y la frontera con D6 y P5 |
| `tests/casos/32_d5_normalizacion_catastral.py` | Los escenarios de acá abajo |
| `tests/casos/31_d6_…py` | E-26, reescrito a su proposición sucesora |

La matriz **no se toca**: su fila de D5 ya declara la señal, los dos agentes, la policy y el check
desde que se construyó, y su `status: CLASSIFIED` no cambia.

## Escenarios verificables

Entre paréntesis, el `D5-nn` del pedido de instalación.

### La señal, la aplicabilidad y el alcance

- **E-01** — D5 sigue `CONDITIONAL` sobre `frontendAddressInputPresent`, declara exactamente los ids
  de policy y de check que ya estaban, y la matriz lo dice sin que este cambio la edite.
  (D5-01, D5-08) · rojo visto: si
- **E-02** — La señal en TRUE hace a D5 aplicable. (D5-02) · rojo visto: si
- **E-03** — La señal en FALSE lo deja `NOT_APPLICABLE`. (D5-03) · rojo visto: si
- **E-04** — Sin evidencia, `APPLICABILITY_UNRESOLVED`. (D5-04) · rojo visto: si
- **E-05** — La ausencia nunca es FALSE: una señal que afirma FALSE sin evidencia se degrada a
  UNRESOLVED, la ausencia de una palabra no sostiene FALSE, y una señal que la matriz no declara se
  rechaza. (D5-05) · rojo visto: si
- **E-06** — `frontendPresent` en TRUE, sola, no hace aplicable a D5. (D5-06)
  · rojo visto: si
- **E-07** — `frontendPresent` en FALSE **más** completitud de alcance declarada con su fuente puede
  resolver D5 en FALSE; sin la completitud, con una fuente que no está en la lista, con `complete`
  en cualquier valor que no sea `True`, o con un FALSE que viene de **otra señal**, queda
  `APPLICABILITY_UNRESOLVED`. Y la derivación publica el `signalId` de la señal que entró, no una
  constante. (D5-07) · rojo visto: si
- **E-08** — La señal sólo sale de evidencia de un flujo de direcciones del frontend: una dependencia
  declarada o la palabra de un agente no la sostienen. · rojo visto: si
- **E-09** — La señal y la evaluación tienen que ser del mismo alcance: alguno sin declarar deja
  `APPLICABILITY_UNRESOLVED`, alcances distintos sin relación declarada y citada también, y con la
  relación declarada se evalúa y la relación **aparece en la salida**. Una señal que **no es un
  documento** —un booleano, un string— no declara alcance y tampoco resuelve. Y el camino por el que
  una señal viaja de verdad llega con su alcance: `senales.resolver_una` y `normativa.resolucion` lo
  conservan, así que la cláusula de la relación declarada es alcanzable desde una resolución real y
  no sólo desde un documento escrito a mano. (§4) · rojo visto: si

### El proveedor y el contrato, que no se inventan

- **E-10** — Sin identidad del proveedor catastral, `CADASTRAL_PROVIDER_UNRESOLVED`. (D5-13)
  · rojo visto: si
- **E-11** — Sin contrato de integración declarado, `INTEGRATION_CONTRACT_MISSING`. (D5-14)
  · rojo visto: si
- **E-12** — Una identidad sin fuente de la lista, sin referencia o **con cualquiera de las dos en
  blancos** no identifica nada, y lo mismo vale para el contrato, para el id de un flujo y para los
  tokens de la cadena. Y se normaliza **cada lado de cada comparación del módulo**, no la lista que
  esta spec enumera: las fuentes del proveedor, del contrato, del inventario, de una ausencia, de un
  inactivo y de la completitud; la relación de alcance; el id y la clase del alcance; el `buildId`,
  el `runtime`, el `mode`, el `sourceType` y el id de una evidencia con su referencia; la ejecución
  y la etapa consumida de un resultado. Padear cualquiera de ellos en un caso **correcto** lo deja
  correcto. · rojo visto: si
- **E-13** — Ninguno de los artefactos de D5 —la policy, el check, las filas del registro, la fila de
  la matriz, la matriz entera y las secciones de D5 de `docs/normativa-7.1.md`— lleva un localizador
  de red, una credencial, un especificador de paquete, un sistema de coordenadas, un campo de
  contrato, un nombre del vocabulario catastral, un valor de timeout o reintento ni una declaración
  de mecanismo; y **sí** puede citar el nombre del servicio que la norma escribe, sin que el barrido
  dispare. El barrido cubre además las doce formas que la refutación probó y que la primera versión
  no agarraba —un tiempo escrito en palabras, una duración con unidad corta, un verbo HTTP con una
  ruta, una URL como valor de JSON, `Basic` y un JWT, una contraseña o un usuario declarados, un CRS
  por su nombre, otros códigos de proyección, cuatro gestores de paquetes más, un paquete con
  versión, y un nombre de campo catastral en mayúscula—. (§6) · rojo visto: si

### Lo que no prueba nada

- **E-14** — Un autocompletado, solo, no da `PASS`. (D5-10) · rojo visto: si
- **E-15** — Una llamada a una API de direcciones, sola, no da `PASS`. (D5-11)
  · rojo visto: si
- **E-16** — Un regex o una validación de string, solos, no dan `PASS`. (D5-12)
  · rojo visto: si
- **E-17** — Una librería de códigos postales, una validación de campo del frontend, unas coordenadas
  y la afirmación de un agente tampoco. · rojo visto: si

### La cadena de cinco valores

- **E-18** — Cadena completa, proveedor declarado y valor normalizado consumido dan `PASS`, incluso
  con blancos alrededor de un identificador en cualquiera de los lados. (D5-15)
  · rojo visto: si
- **E-19** — La llamada ocurre y el valor crudo sigue siendo el autoritativo: `FAIL` con
  `RAW_VALUE_CONSUMED`, tanto cuando los tokens lo demuestran como cuando el flujo lo declara y los
  tokens no lo desmienten. Y un bypass **probado** sigue informándose como bypass aunque a la cadena
  le falte otra etapa. (D5-16) · rojo visto: si
- **E-20** — Un valor consumido que no es ni el crudo ni el normalizado no pasa: `PARTIAL` con
  `CONSUMED_VALUE_UNTRACED`. · rojo visto: si
- **E-21** — Se exigen el token y la etapa, y el estado que se informa tiene que ser cierto: un
  `consumedFrom: NORMALIZED_RESULT` que lleva el token del crudo da `FAIL`; un token normalizado con
  la etapa sin declarar no llega a `PASS`; un `consumedFrom: RAW_INPUT` cuyo token dice lo contrario
  queda `PARTIAL` con `CHAIN_DECLARATION_INCOHERENT`, porque manda el token y eso no es un
  incumplimiento probado; y una cadena sin la respuesta pero **con** el resultado normalizado queda
  `PARTIAL` por cadena incompleta con un detalle que no afirma algo falso — para `FAIL` tienen que
  faltar las dos. · rojo visto: si
- **E-22** — Cuando el crudo y el normalizado son el mismo token la comparación no discrimina: el
  resultado es `PASS` **y lo dice** con `NORMALIZATION_INDISTINGUISHABLE`.
  · rojo visto: si

### Los cinco caminos y el bypass

- **E-23** — Un camino de carga manual de texto libre, sin llamada al proveedor y con el valor
  consumido como si fuera normalizado, da `FAIL`. (D5-17) · rojo visto: si
- **E-24** — Un camino de edición que se saltea la normalización da `FAIL`, y también uno donde la
  llamada al proveedor es condicional y el flujo normal no la hace. (D5-18)
  · rojo visto: si
- **E-25** — Los cinco tipos de camino se declaran todos: uno en silencio deja
  `ADDRESS_FLOW_COVERAGE_UNRESOLVED`, una ausencia declarada sin fuente de la lista tampoco alcanza,
  un `absent` que no es `True` no declara una ausencia, un tipo declarado **dos veces** se rechaza
  —si no, la primera entrada se valida sola y un flujo sin id llega a gobernado—, y una entrada
  **malformada** sale por uno de los nueve estados y no por una excepción. (D5-19)
  · rojo visto: si
- **E-26** — Cobertura incompleta: sin inventario, sin fuente o con flujos sin id,
  `ADDRESS_FLOW_COVERAGE_UNRESOLVED`; con un flujo enumerado y sin ejecutar, `PARTIAL`. (D5-19)
  · rojo visto: si
- **E-27** — Un camino que cumple no tapa otro que no —un `FAIL` manda sobre cualquier cantidad de
  caminos que pasen—, un flujo inactivo exige fuente y aparece en la salida, un inactivo sin fuente
  se verifica como activo, declararlos **todos** inactivos no da `PASS`, y **un resultado sobre un
  flujo declarado inactivo se mira**: si prueba un bypass deja la cobertura sin resolver y aparece
  nombrado en un aviso; si está limpio se lista y no acusa nada. · rojo visto: si

### La corrida

- **E-28** — La evidencia mockeada se distingue de la real y no llega a `PASS`. (D5-20)
  · rojo visto: si
- **E-29** — Sin objetivo donde correr, `TEST_TARGET_UNAVAILABLE`, y `available` se exige `True` y
  no un truthy: un `"no"` no habilita la evaluación. · rojo visto: si
- **E-30** — Los nueve estados existen, y el único que aprueba es `PASS`. (§13)
  · rojo visto: si

### Las fronteras

- **E-31** — D5 no afirma nada sobre D6 en **ninguno de sus nueve caminos**: todos llevan sólo la
  tupla de D5, ninguno nombra la regla, sus controles ni su señal, y un resultado normalizado con
  coordenadas no cambia nada. (D5-21) · rojo visto: si
- **E-32** — D5 no afirma nada sobre P5 en ninguno de sus nueve caminos: no nombra la regla, sus
  controles ni su señal, y no informa nada sobre la validación del backend. (D5-22)
  · rojo visto: si
- **E-33** — D5 no crea ni declara ninguna skill: la cuenta de instaladas no cambia, ningún artefacto
  de D5 declara una, la fila de la matriz sigue con cero referencias, y las únicas que sus artefactos
  nombran son las que resuelve el registro de agentes. (D5-09, §1) · rojo visto: si

### La propagación, el registro y la trazabilidad

- **E-34** — La unidad de trabajo propaga la señal, la policy y el check, y la forma vieja
  —booleanos— sigue funcionando. (D5-23) · rojo visto: si
- **E-35** — Los dos agentes primarios de D5 resuelven contra el registro de agentes, y el check no
  redefine la propiedad. (D5-24) · rojo visto: si
- **E-36** — Después de instalar, los dos controles dejan de figurar como no instalados, no queda
  ningún archivo de control sin declarar, y la clasificación de D5 en la matriz no cambia. Y la
  cuenta de reglas con todos sus controles construidos —ocho, contra dieciséis incompletas— se
  calcula sobre **los tres tipos** que una fila puede declarar, no sobre dos. (D5-25, §12)
  · rojo visto: si
- **E-37** — Todo resultado del check conserva `ES0901 / 6.3 / 7.1 / D5`. (D5-26)
  · rojo visto: si

## Cómo se verifica

Los 37 pasan por `.\tests\Invoke-Tests.ps1`. Ninguno lleva la marca `· verificación: lectura`: todo
lo que este cambio construye es determinista.

E-13 tiene **tres** mitades, igual que el barrido de D6, y la tercera importa más acá: entre los
textos que **no** tienen que disparar están la cita de la pág. 19 y la fila citable de la regla. Un
barrido de D5 que se ponga en rojo con la transcripción del estándar es un barrido que alguien apaga
el primer día.

E-31 y E-32 se prueban sobre **los nueve caminos**, no sobre un resultado. Un solo resultado limpio
no dice que el módulo no pueda hablar de D6 ni de P5: lo dice que ninguno de sus caminos lo haga.

### Lo que encontró la pasada de mutaciones

58 mutaciones, y los 37 escenarios tienen un rojo presenciado. Tres de esas mutaciones **no
encontraron rojo en la primera vuelta**, y las tres eran huecos del test, no del mecanismo:

```
E-06  invertir la guarda de la derivacion no se veia: el caso feliz de E-06 no declaraba
      completitud, asi que caia en SIN_RESOLVER por otro motivo y la asercion pasaba igual.
      Falta el caso que importa: frontendPresent TRUE **con** completitud declarada.
E-34  sacar `scope` del schema no se veia: el validador no rechaza claves que no declara, asi
      que la senal validaba igual. Habia que afirmar sobre el CONTRATO, no sobre el dato.
E-05  hacer entrar lo UNRESOLVED como False no ponia en rojo ningun test de D5 -solo los de
      D1 a D4 y D6-. E-05 lo afirmaba en el check y no en la resolucion, que es por donde la
      senal viaja a un plan.
```

Los tres se cerraron subiendo la aserción. Es el mismo patrón de siempre: **un test verde que
prueba una proposición vecina a la de su escenario**, y acá lo encontró la mutación antes que el
refutador.

### Lo que encontró la primera refutación

Dos escenarios contradichos, **los dos de mecanismo y ninguno con un test que lo mirara**, con los
707 del grupo y los 4747 de la suite en verde:

```
E-09  la guarda de alcance se salteaba con la forma vieja de una senal -evaluar(caso, True)
      salia PASS- y era inalcanzable con la forma resuelta, porque `senales.resolver_una` no
      copiaba `scope`. Estricta donde el dato no podia cumplir, laxa donde no se declaro nada
E-21  el orden de las guardas no implementaba la tabla de decision de esta misma spec: un
      bypass PROBADO salia como cadena incompleta, un `or` producia un detalle falso, y
      cuando la etapa y el token discrepaban mandaba la etapa
```

Y ocho hallazgos más que no contradecían un escenario y sí eran defectos: doce comparaciones sin
normalizar —dos de ellas informando un motivo que no era cierto—, tres puertas que abrían con un
truthy, la derivación publicando una constante como origen, un tipo de camino duplicado que evadía
su validación, un resultado sobre un flujo inactivo que desaparecía de la salida entera, y una
entrada malformada que rompía el módulo en lugar de fallar cerrada. **Los doce hallazgos están
arreglados y cada uno tiene su aserción**; ninguno se cerró achicando un escenario.

📌 De los dos contradichos, **sólo uno podía filtrar un `PASS`** sobre una aplicación que no cumple
—el de E-09 con la señal en forma de booleano—. El otro informaba el estado equivocado, que es lo
que E-20 prohíbe: *afirmar incumplimiento sin saberlo es una afirmación falsa con la tupla normativa
adosada*. Un control que se equivoca en esa dirección se apaga igual de rápido que uno que aprueba
de más.

## Riesgos conocidos

- **El contrato de integración no se puede resolver en ningún proyecto todavía.** El harness no tiene
  cómo se ve usar la opción catastral. Cualquier corrida real de hoy va a salir
  `INTEGRATION_CONTRACT_MISSING`, que es lo correcto y también significa que el check no se va a
  ejercitar de punta a punta hasta que alguien consiga ese dato. La identidad, en cambio, sí es
  citable desde la pág. 19.
- **La cadena la declara la corrida.** El check verifica que los tokens sean coherentes, que la
  etapa declarada coincida y que la evidencia esté atada al build y no venga mockeada. Que el token
  del valor consumido corresponda de verdad al valor que la aplicación guardó lo produce quien
  instrumenta la corrida.
- **El caso degenerado queda abierto a propósito.** Con el crudo y el normalizado en el mismo token,
  la comparación no discrimina y el resultado pasa con su aviso. Está clavado en verde en E-22.
- **La completitud de alcance sigue abierta para las demás reglas.** D5 la exige; el pendiente
  general de *nada exige «unless project coverage is known to be complete»* no se cierra acá.
- **`controles/` no llega a un proyecto instalado.** Con D5 son dieciocho controles que declaran
  `INSTALLED` y que fuera de este repositorio serían `CONTROL_FILE_MISSING`. Este cambio no lo
  arregla y empeora la cuenta en dos.
