# D6 — Las visualizaciones georreferenciadas usan el Mapa del GCBA

**Estado:** verificado y cerrado · **Fecha:** 21-09-2026 · **Regla:** ES0901 6.3 §7.1 D6

## Qué problema resuelve

La regla citable, `ES0901-7.1-D6`, pág. 13:

> *"Las visualizaciones georeferenciales de objetos deben utilizar el Mapa del GCABA."*

Y el párrafo que la refuerza, **Georreferenciación**, pág. 19:

> *"Las aplicaciones deben contar con direcciones de calles normalizadas y validadas a través del
> servicio de API GEO disponible en el catálogo."* *"Adicionalmente para el caso de visualización de
> direcciones en mapa, debe utilizarse el mapa del GCABA."*

🔴 **Las dos frases del mismo párrafo son dos reglas distintas**, y ése es el problema central de
este cambio. La primera es D5 —normalizar direcciones con API GEO—; la segunda es D6 —mostrarlas en
el Mapa del GCBA—. Están pegadas en el documento y son independientes: una aplicación puede
normalizar perfecto y dibujar el resultado en un mapa de otro proveedor.

Hoy el harness no puede decir nada de ninguna de las dos. La matriz declara la fila de D6 con su
señal y sus dos controles desde que se construyó, y los dos controles **no existen**: cualquier
consulta los reporta como `DECLARED_POLICY_NOT_INSTALLED` y `DECLARED_CHECK_NOT_INSTALLED`.

Y hay una trampa propia de esta regla: **el mecanismo del Mapa del GCBA no está en ningún extracto
de este repositorio.** No hay SDK, no hay endpoint, no hay tile source, no hay layer id, no hay
CRS. Un check que necesite saberlos y los invente convierte una regla de cumplimiento en una
afirmación falsa con sello normativo.

## Qué queda afuera

- **D5.** Sus cuatro artefactos están en `~/Downloads` desde el 20-09-2026 y **no se instalaron**.
  Este cambio no los instala y no los toca. Lo que sí hace es mantener la frontera verificable: la
  señal de D5 está declarada en la matriz, así que los escenarios de separación se pueden probar
  contra un nombre real.
  📌 Después de este cambio, D5 sigue siendo la única regla con controles declarados y no
  construidos. Eso se ve en el registro y está anotado.
- **El mecanismo del Mapa del GCBA.** No se declara ningún SDK, endpoint, tile source, layer id,
  autenticación, CRS, URL de ambiente ni token. El harness no los sabe. La identidad del proveedor
  entra como **dato declarado por el proyecto, con su fuente citada**; sin eso,
  `GCBA_MAP_PROVIDER_UNRESOLVED`.
- **Renderizar un mapa.** Este módulo no abre un navegador y no ejecuta una vista. La corrida entra
  como dato, igual que en D4, y quien la ejecute son las skills de calidad que ya están instaladas.
- **Crear o modificar una skill.** El pedido lo prohíbe explícitamente y no hay ninguna skill de
  mapas instalada. El hueco se **declara** con el estado que ya existe —`SPECIALIZED_SKILL_GAP`— y
  no se llena.
- **Arreglar el instalador.** `install.ps1` no copia `controles/`, así que los dieciséis controles
  —catorce más los dos de D6— declaran `INSTALLED` y fuera de este repositorio serían
  `CONTROL_FILE_MISSING`. Es el ítem 2 de la tabla de prioridades, es un cambio con su propia spec,
  y este cambio lo empeora en dos y lo dice.
- **Una lista de proveedores prohibidos.** El documento del pedido nombra Leaflet, OpenLayers y
  Google Maps como ejemplos de lo que no alcanza. Acá no se nombra ninguno — ver la decisión de más
  abajo.

## Las decisiones, y por qué

### D5 y D6 no se heredan el resultado

```
D5  ->  normalizacion de direcciones  ->  API GEO
D6  ->  visualizacion georreferenciada ->  Mapa del GCBA
```

El check de D6 trata `GEO_API_CALL` como evidencia **inerte**: que la aplicación llame a API GEO no
dice nada sobre qué mapa dibuja. Y el resultado de D6 lleva sólo la tupla de D6 —`ES0901 / 6.3 /
7.1 / D6`—, nunca la de D5, así que ningún consumidor puede leer un `PASS` de D6 como cumplimiento
de D5.

Es la separación que el párrafo de la pág. 19 hace fácil de perder: las dos frases están una al
lado de la otra, y la primera vez que alguien las opere junto va a escribir un check que pase con
API GEO.

### La identidad del proveedor se declara, no se adivina

El check necesita saber **cuál** es el Mapa del GCBA para poder comparar. Ese dato no está en el
harness y no se inventa. Entra así:

```yaml
mapProvider:
  id: <lo que el proyecto declara>
  source: GCBA_NORMATIVE | GCBA_CATALOG_ENTRY | ASI_INTEGRATION_CONTRACT |
          PROJECT_INTEGRATION_AGREEMENT | HUMAN_CONFIRMATION
  reference: <donde lo dice>
```

La lista dice **qué fuentes son defendibles**; no dice cuál es el mecanismo. Sin `id`, sin una
fuente de la lista o sin referencia: `GCBA_MAP_PROVIDER_UNRESOLVED`.

Y aparte de la identidad hace falta el **contrato de integración**: cómo se reconoce que una vista
usa ese mecanismo. Sin eso el check no tiene contra qué comparar una vista, y sale
`MAP_INTEGRATION_CONTRACT_MISSING`.

> 🔴 Son dos estados y no uno porque son dos huecos distintos. *No sé cuál es el mapa* y *sé cuál es
> y no sé cómo se ve usarlo* se arreglan preguntándole a personas diferentes.

### El check compara identificadores, nunca mecanismos

Cada vista declara con qué proveedor se dibuja y la evidencia de corrida declara con qué proveedor
se dibujó. El check compara esos ids contra el declarado. **Nunca mira un endpoint, un paquete ni
una URL.** Es lo que le permite ser correcto sin saber nada del Mapa del GCBA.

### Ningún artefacto de D6 nombra un proveedor de mapas, ni el de acá ni los de afuera

El documento del pedido nombra Leaflet, OpenLayers y Google Maps como contraejemplos. Acá no se
nombra ninguno, por tres motivos y en este orden:

1. Una lista de prohibidos envejece, y el proveedor número cuatro llega diciendo *el mío no está en
   la lista*.
2. La regla no es *no uses estos*: es *usá el del GCBA*. Enumerar a los otros corre el eje.
3. Con la lista adentro, el invariante que verifica que no se inventó el mecanismo del GCBA deja de
   poder distinguir un contraejemplo de una invención.

Lo que se verifica es estructural, sobre los artefactos de la regla —la policy, el check, las filas
del registro, la fila de la matriz, la matriz entera y las dos secciones de
`docs/normativa-7.1.md`—:

```
localizadores de red      con esquema, sin esquema, con puerto -con o sin punto-, o una IP
sistemas de coordenadas   con etiqueta (EPSG/SRID/CRS) o el codigo suelto
servicios geoespaciales   wmts, wms, wfs, tileMatrixSet, tileGrid, geoserver
plantillas de tiles       {z} {x} {y}
credenciales              bearer o token con un numero adentro, api_key, access_token
paquetes                  el gestor, el @scope/nombre, y como se importa
mecanismo declarado       sdk, tile source, endpoint, layer id seguidos de : o =
```

El barrido de nombres de proveedor es la segunda red, y los distintivos se buscan **sin
separadores**: `Open Layers`, `open-layers` y `openlayers` son lo mismo. Los cortos van con borde
de palabra, porque `carto` está adentro de *cartografía* y `esri` se forma entre *materiales* y
*rigen* si se quitan los espacios.

El test tiene **tres** mitades, y la tercera se agregó porque las dos primeras no alcanzan: los
seis textos limpios, **44** formas crudas de fuga que tienen que disparar —15 de ellas son las que
la primera versión dejaba pasar, y nueve más salieron de la segunda— y once textos legítimos que
**no** tienen que disparar. Un barrido que se pone en rojo con texto correcto es un barrido que
alguien apaga la primera vez que lo ve fallar sin motivo.

🔴 **Todos los patrones llevan `(?i)`.** Cuatro no lo llevaban, y en código la forma normal de
escribir esto es una constante en mayúscula: `HTTPS://MAPA.GCBA.GOB.AR/BASE` escapaba entero. Era
una dimensión completa del barrido, no una forma suelta.

### Una vista que cumple no tapa otra que no

Un `FAIL` en cualquier vista gobernada manda sobre cualquier cantidad de vistas que pasen. Es la
misma doctrina que la de D4 —el desktop no tapa al mobile— y acá importa más, porque el caso típico
es justamente el mixto: la pantalla principal con el mapa institucional y una pantalla vieja con
otro.

🔴 **Y la vista de afuera del inventario también cuenta.** Un resultado de una vista que el
inventario no declara, dibujando con otro proveedor, deja el resultado en
`MAP_VIEW_COVERAGE_UNRESOLVED`: o falta una vista gobernada, o esa vista no lo está y nadie lo
declaró. Se mira lo que la vista declara **y** lo que su corrida reporta, porque si sólo se mirara
lo declarado, dejar ese campo vacío desarmaría la guarda entera.

### La cobertura se declara con su fuente, y el inventario es la lista entera

El inventario de vistas materiales entra con su origen —requisito de UX, arquitectura, inventario
de rutas o perfil de prueba aprobado—. Sin inventario, o sin fuente, o con vistas sin id:
`MAP_VIEW_COVERAGE_UNRESOLVED`. Una vista que nadie enumeró es una vista que nadie verificó.

🔴 **No hay un segundo filtro por vista.** El inventario **es** la lista de vistas materiales —eso
es lo que el pedido pide enumerar y lo que su `source` respalda—, así que una etiqueta por vista no
saca a ninguna de la verificación. La materialidad se decide al armar el inventario, que sí tiene
que declarar de dónde sale; una etiqueta que el proyecto pone sola y que nadie tiene que respaldar
sería una puerta de salida de la regla sin fuente.

### Un blanco no es un dato declarado, y se normalizan LOS DOS lados

Todo campo de identidad —el id y la referencia del proveedor, los del contrato, el id de una
vista, el proveedor de un resultado y el de una corrida— se lee sin blancos. Un espacio no
identifica nada y no cita nada: sin esto, un caso con toda la identidad en espacios llegaba a
`PASS`, o sea D6 informaba cumplimiento con un proveedor que no nombra nada.

🔴 **Y normalizar un solo lado de una comparación es peor que no normalizar ninguno.** La primera
versión de este arreglo dejó los dos valores contra los que se compara —el id del proveedor y las
claves del cruce de vistas— en crudo, y produjo dos defectos nuevos:

```
un proveedor con blancos que `proveedor_valido` aceptaba no podia igualar nunca al que la
vista declaraba  ->  un caso correcto salia FAIL por proveedor alterno

una vista con el id padeado se caia por el agujero del medio: `ids` normalizado y
`por_vista` en crudo  ->  no entraba como gobernada ni como de afuera, y un bypass
probado se informaba como GOVERNED_VIEW_NOT_EXECUTED
```

El segundo fue una **regresión**: la versión anterior, con todo en crudo, mandaba ese resultado a
las vistas de afuera y avisaba. Normalizar la mitad convirtió un estado que avisaba en uno que
calla. Por eso el módulo normaliza en **cada** lado de **cada** comparación, y también en lo que
informa: publicar un id distinto del que se compara es como se lee un `FAIL` que no se entiende.

### La corrida también tiene que decir con qué dibujó

Una corrida que no declara su proveedor no prueba nada, igual que una que no declara su modo. Las
dos son la misma regla: **lo que no se dice no se verifica**, y un `PASS` apoyado en una corrida
muda es un `PASS` donde nadie dijo con qué mapa se dibujó.

### La evidencia mockeada no llega a PASS

La corrida declara su modo: `REAL` o `MOCKED`. Una corrida mockeada sirve para desarrollar el caso
y **no prueba** que la aplicación use el mapa institucional: deja la vista sin ejecutar y el
resultado en `PARTIAL`. Se distingue en el resultado, no se descarta en silencio.

### Lo que está instalado no prueba lo que se dibuja

La partición de evidencia es la razón de ser del check:

```
RENDERED_MAP_RUN        prueba. Es la unica que prueba
SCREENSHOT              acompana
HUMAN_CONFIRMATION      acompana

REPOSITORY_DEPENDENCY   inerte: un paquete instalado no es un mapa dibujado
MAP_COMPONENT_PRESENT   inerte: un componente que existe no es un componente que se usa
COORDINATE_DATA         inerte: hay coordenadas en cualquier base de datos
GEO_API_CALL            inerte: eso es D5
TILE_CONFIGURATION      inerte: configurar no es renderizar
AGENT_STATEMENT         inerte: una opinion con formato de evidencia
```

### Se reutiliza la infraestructura, no se construye una segunda

`senales.py` resuelve la señal, `matriz.py` la aplicabilidad, `controles.py` el registro y
`registro_agentes.resolver_ruteo` el ruteo. El cambio no agrega ni un módulo de orquestación.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/controles/policies/gcba-map-required.md` | La policy de D6, con su frontera de proveedor |
| `harnesses/desarrollo/controles/checks/gcba-map-usage.py` | El check: nueve estados, cobertura, bypass y corrida |
| `harnesses/desarrollo/reglas/control-registry.json` | Los dos controles de D6, declarados |
| `docs/normativa-7.1.md` | D6, el mecanismo que no se sabe y la frontera con D5 |
| `tests/casos/31_d6_visualizacion_georreferenciada.py` | Los escenarios de acá abajo |

La matriz **no se toca**: su fila de D6 ya declara la señal, la policy y el check desde que se
construyó.

## Escenarios verificables

Entre paréntesis, el `D6-nn` del pedido de instalación.

### La señal y la aplicabilidad

- **E-01** — D6 sigue `CONDITIONAL` sobre `georeferencedVisualizationPresent`, y la matriz lo
  declara sin que este cambio la edite. (D6-01) · rojo visto: si
- **E-02** — La señal en TRUE hace a D6 aplicable. (D6-02) · rojo visto: si
- **E-03** — La señal en FALSE lo deja `NOT_APPLICABLE`. (D6-03) · rojo visto: si
- **E-04** — Sin evidencia, `APPLICABILITY_UNRESOLVED`. (D6-04) · rojo visto: si
- **E-05** — La ausencia nunca es FALSE: una señal que afirma FALSE sin evidencia se degrada a
  UNRESOLVED, y una que la matriz no declara se rechaza. (D6-05) · rojo visto: si
- **E-06** — `frontendPresent` en TRUE, sola, no hace aplicable a D6. (D6-06) · rojo visto: si
- **E-07** — `frontendAddressInputPresent` en TRUE, sola, no hace aplicable a D6. (D6-07)
  · rojo visto: si
- **E-08** — La señal sólo sale de evidencia de una visualización de objetos georreferenciados: una
  dependencia o la palabra de un agente no la sostienen. · rojo visto: si

### El proveedor, que no se inventa

- **E-09** — Sin identidad de proveedor declarada, `GCBA_MAP_PROVIDER_UNRESOLVED`. (D6-12)
  · rojo visto: si
- **E-10** — Sin contrato de integración declarado, `MAP_INTEGRATION_CONTRACT_MISSING`. (D6-13)
  · rojo visto: si
- **E-11** — Un proveedor declarado sin fuente de la lista, sin referencia o **con cualquiera de
  los dos en blancos** no identifica nada, y lo mismo vale para el contrato y para el id de una
  vista. · rojo visto: si
- **E-12** — Ninguno de los artefactos de D6 —la policy, el check, las filas del registro, la fila
  de la matriz, la matriz entera y las dos secciones de `docs/normativa-7.1.md`— lleva un localizador
  de red, un sistema de coordenadas, una plantilla de tiles, un servicio geoespacial, una
  credencial, un especificador de paquete, una declaración de mecanismo ni el nombre de un
  proveedor de mapas, esté escrito junto, partido o pegado. (§5) · rojo visto: si

### Lo que no prueba nada

- **E-13** — Coordenadas solas no dan `PASS`. (D6-08) · rojo visto: si
- **E-14** — Una librería de mapas en el manifiesto, sola, no da `PASS`. (D6-09)
  · rojo visto: si
- **E-15** — Usar API GEO, solo, no da `PASS`: eso es D5. (D6-10) · rojo visto: si
- **E-16** — Una captura de pantalla, sola, no da `PASS`. (D6-11) · rojo visto: si
- **E-17** — La afirmación de un agente, sola, no da `PASS`, ni un componente declarado, ni una
  configuración de tiles. · rojo visto: si

### La cobertura, el bypass y la corrida

- **E-18** — Todas las vistas materiales usando el Mapa del GCBA con evidencia de corrida real dan
  `PASS`, incluso con blancos alrededor de un identificador en cualquiera de los tres lados.
  (D6-14) · rojo visto: si
- **E-19** — Un mapa alterno en un camino gobernado da `FAIL` —también cuando el id de la vista
  trae blancos de cualquiera de los dos lados—, la corrida manda sobre lo que la vista declare, y
  una vista o una corrida que **no dicen** con qué se dibujó no pasan. (D6-15) · rojo visto: si
- **E-20** — Un mapa que cumple no tapa otro que no: un `FAIL` manda sobre cualquier cantidad de
  vistas que pasen, y una vista **fuera del inventario** con un bypass probado —lo declare o lo
  diga sólo su corrida— deja el resultado sin resolver. (D6-16) · rojo visto: si
- **E-21** — Cobertura incompleta: sin inventario o sin fuente,
  `MAP_VIEW_COVERAGE_UNRESOLVED`; con una vista enumerada y sin ejecutar, `PARTIAL`. Y **el
  inventario es la lista entera**: ninguna etiqueta por vista saca a una vista de la
  verificación. (D6-17) · rojo visto: si
- **E-22** — La evidencia mockeada se distingue de la real y no llega a `PASS`. (D6-18)
  · rojo visto: si
- **E-23** — Sin objetivo donde correr, `TEST_TARGET_UNAVAILABLE`. · rojo visto: si
- **E-24** — Los nueve estados existen, y el único que aprueba es `PASS`. (§9)
  · rojo visto: si

### La frontera con D5

- **E-25** — D6 no afirma nada sobre D5 en **ninguno de sus nueve caminos**: todos llevan sólo la
  tupla de D6 y ninguno nombra la regla, sus controles ni su señal; `GEO_API_CALL` es inerte; y
  resolver D6 no cambia la aplicabilidad de D5. (D6-19) · rojo visto: si
- **E-26** — D5 sigue con sus dos controles declarados y no instalados, y el registro lo dice con
  los estados que ya existen. · rojo visto: si

### Las skills y el ruteo

- **E-27** — D6 no crea ni declara ninguna skill: no hay ninguna de mapas instalada, siguen
  siendo 27, ningún artefacto de D6 declara una, y las únicas que sus artefactos nombran son las
  que resuelve el registro de agentes —incluida la que no existe—. (D6-20) · rojo visto: si
- **E-28** — La remediación rutea por el registro de agentes y, sin una skill de mapas instalada,
  deja el hueco visible con `SPECIALIZED_SKILL_GAP` sin inventarla y sin hacer cumplir a D6.
  · rojo visto: si

### La propagación, el registro y la trazabilidad

- **E-29** — La unidad de trabajo propaga la señal, la policy y el check, y la forma vieja
  —booleanos— sigue funcionando. (D6-21) · rojo visto: si
- **E-30** — Después de instalar, los dos controles dejan de figurar como no instalados, y no queda
  ningún archivo de control sin declarar. (D6-22) · rojo visto: si
- **E-31** — Todo resultado del check conserva `ES0901 / 6.3 / 7.1 / D6`. (D6-23)
  · rojo visto: si

## Cómo se verifica

Los 31 pasan por `.\tests\Invoke-Tests.ps1`. Ninguno lleva la marca `· verificación: lectura`: todo
lo que este cambio construye es determinista.

E-12 tiene **tres** mitades, una más que el guard de D4: la primera afirma que los seis textos
están limpios; la segunda inyecta 44 fugas **en su forma cruda** —sin acomodarlas al patrón— y
afirma que el barrido las encuentra; y la tercera afirma que once textos legítimos **no** lo
disparan. Sin la segunda, la primera se degrada en silencio el día que alguien afloje un patrón.
Sin la tercera, el barrido se pone en rojo con texto correcto y alguien lo apaga.

## Riesgos conocidos

- **El proveedor no se puede resolver en ningún proyecto todavía.** El Mapa del GCBA no está en
  ningún extracto ni en el catálogo del Anexo II. En cualquier corrida real de hoy, D6 va a salir
  `GCBA_MAP_PROVIDER_UNRESOLVED`, que es lo correcto y también significa que el check no se va a
  ejercitar de punta a punta hasta que alguien consiga ese dato.
- **La frontera con D5 se prueba contra un D5 que no existe.** `frontendAddressInputPresent` está
  declarada en la matriz, así que E-07 y E-25 son verificables; lo que no se puede probar todavía es
  que el check de D5 y el de D6 no se contaminen entre sí, porque uno de los dos no está.
- **`controles/` no llega a un proyecto instalado.** Con D6 son dieciséis controles que declaran
  `INSTALLED` y que fuera de este repositorio serían `CONTROL_FILE_MISSING`. Este cambio no lo
  arregla y empeora la cuenta en dos.
- **Que la aplicación use el Mapa del GCBA de verdad lo dice una corrida real.** Lo que este check
  verifica es que la evidencia de esa corrida exista, esté atada al build y no venga mockeada.
