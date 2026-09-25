# ES0902 Vu7 — el software de base no entrega datos privados

**Estado:** verificado y cerrado · **Fecha:** 24-09-2026 · **Regla:** ES0902 6.2 §6 Vu7 · **Tanda:** Vu7 + Vu8

## Qué problema resuelve

> *"Todo el software de base debe estar configurado para no entregar datos privados."*
> (ES0902 v6.2, §6)

La fila está en la matriz: `ALWAYS`, sin señal, con una policy, un check y cero reviews. Los dos
controles, `base-software-private-data-disclosure-prohibited` y
`base-software-data-disclosure-configuration`, están declarados y no construidos. Vu7 es la primera
regla `ALWAYS` de ES0902 con check propio: no hay señal que la apague.

Vu7 tiene seis formas baratas de ponerse en verde o en rojo, y este cambio las cierra:

1. **El repo por el ambiente.** Un default seguro en el repositorio, pisado por un override inseguro
   en el ambiente, sigue siendo inseguro en ese ambiente.
2. **DEV por PRD.** La configuración de DEV no prueba la de QA, HML ni PRD.
3. **El nombre por la exposición.** Un endpoint que se llama `/actuator` o `/status` no falla por
   su nombre: falla si entrega datos privados a quien no corresponde.
4. **El banner por el dato.** Que el servidor diga su versión es asunto de C3 y Ve1, no de Vu7,
   salvo que eso entregue un dato privado clasificado.
5. **El acceso legítimo por la fuga.** El mismo dato puede estar bien servido a un consumidor
   autorizado y mal servido a uno anónimo.
6. **"Privado" inventado.** ES0902 no da una taxonomía de datos privados, y el check no la crea a
   partir de nombres de campos ni de extensiones de archivo.

Y la peligrosa: probar la fuga accediendo de verdad, sin autorización, a datos privados reales.

## Qué queda afuera

- **Una taxonomía de datos privados.** La clasificación sale de evidencia autoritativa del
  proyecto: seguridad, privacidad, arquitectura, una evaluación o un contrato.
- **Una lista universal de productos o de endpoints prohibidos.** El inventario sale de la
  evidencia del proyecto.
- **La versión y el banner.** Son de C3 y Ve1.
- **Vu6.** Una respuesta de error del software de base puede ser evidencia de las dos reglas, pero
  cada una tiene su resultado.
- **La integridad del repositorio.** Puede detectar un cambio sospechoso de configuración, y su
  veredicto no es el de Vu7.
- **Tocar C1, C3, Ve1, Vu1..Vu6 o `controles/lib/evidencia.py`.** Vu7 reusa la lib y no cambia su
  regla de salida.
- **Ejecutar pruebas.** El check lee la evidencia de una prueba ya hecha y decide si era segura.
- **Cambiar los agentes de la fila.** La matriz declara `dev-security` y `dev-devops`. El paquete
  nombra solo a `dev-security`, y la fila no se migra.
- **Un agente, una skill, una review, un algoritmo nuevo en `seguridad.py` o un subsistema de
  reporte.** Vu7 va por `_generico`, y `ALGORITMOS` sigue en diez.

## Las decisiones, y por qué

### `ALWAYS`: no hay señal, y no hay `NOT_APPLICABLE`

El check nunca emite `NOT_APPLICABLE`. Un registro vacío no quiere decir "no aplica": quiere decir
que no se sabe qué software de base hay, y da `BASE_SOFTWARE_INVENTORY_UNRESOLVED`.

### Un registro por ambiente, y la evidencia tiene que ser de ese ambiente

El registro nombra su `environment` y su `deploymentBinding`. Si `environment` es nulo, todo lo que
dependa de la configuración efectiva da `BASE_SOFTWARE_CONFIGURATION_UNRESOLVED`.

Una evidencia sostiene algo solo si su `environment` es igual en NFC al del registro. Una evidencia
de `DEV` no sostiene nada en un registro de `QA`. Tampoco lo sostiene una sin ambiente, salvo que sea
de una clase que no depende del ambiente: `DATA_CLASSIFICATION`, `BASE_SOFTWARE_INVENTORY` o
`DISCLOSURE_SURFACE_SCOPE`.

### Qué hay que cubrir

- **El inventario.** Un componente cita una evidencia autoritativa y legible
  `BASE_SOFTWARE_INVENTORY` que nombra los componentes del ambiente. Cada uno de esos componentes
  necesita una entrada en el registro. Sin esa evidencia, o con un componente nombrado sin entrada,
  da `BASE_SOFTWARE_INVENTORY_UNRESOLVED`.
- **Las superficies de cada componente.** El componente cita una evidencia autoritativa
  `DISCLOSURE_SURFACE_SCOPE` que nombra sus superficies, y cada una necesita una entrada. Si no, da
  `DISCLOSURE_SURFACE_COVERAGE_UNRESOLVED`.
- **Entradas que sobran.** Una entrada que no está en el inventario, o una superficie que no está en
  su alcance, también se evalúa, y además impide el `PASS` con el mismo estado. Estar afuera nunca
  hace `FAIL` por sí solo.

### La clasificación es del proyecto

Una clase `PRIVATE` o `NOT_PRIVATE` cuenta solo si cita una evidencia autoritativa y legible
`DATA_CLASSIFICATION` con ese mismo valor. `UNRESOLVED`, o una clase sin ese sostén, da
`PRIVATE_DATA_CLASSIFICATION_UNRESOLVED` en toda superficie que la nombre. Un nombre de campo, una
extensión o la metadata de la infraestructura no clasifican nada.

### El resultado de una superficie sale de estos pasos

Se recorren los pasos. Una falla en cualquiera de ellos le gana a un sin resolver de un paso
anterior. Si no hay ninguna falla, gana el primer sin resolver en el orden de la lista.

1. **La configuración.** `configurationStatus: UNRESOLVED` en el componente da
   `BASE_SOFTWARE_CONFIGURATION_UNRESOLVED`.
2. **La fuga.** `UNAUTHORIZED_PRIVATE_DATA_DISCLOSURE` es `FAIL` si se cumplen las tres cosas:
   - lo establece una evidencia citada, legible, de configuración efectiva o de comportamiento, del
     ambiente del registro;
   - la superficie nombra en `dataClassRefs` una clase resuelta en `PRIVATE`;
   - `authorizationContext` es `UNAUTHORIZED` o `PUBLIC`.

   Si la clase no está resuelta, da `PRIVATE_DATA_CLASSIFICATION_UNRESOLVED`. Si es `NOT_PRIVATE`,
   no es una fuga de Vu7.
3. **El acceso autorizado.** `AUTHORIZED_PRIVATE_DATA_ACCESS` cumple solo con
   `authorizationContext: AUTHORIZED` y una evidencia citada `AUTHORIZATION_CONTEXT` que lo
   establece para esa superficie. Si no, da `BASE_SOFTWARE_CONFIGURATION_UNRESOLVED`.
4. **Sin fuga.** `NO_PRIVATE_DATA_DISCLOSURE` cumple solo si una evidencia citada, legible, de
   configuración efectiva o de comportamiento y del ambiente del registro lo establece. Si no, da
   `BASE_SOFTWARE_CONFIGURATION_UNRESOLVED`.

Las clases de configuración efectiva y de comportamiento son estas:
- `EFFECTIVE_CONFIGURATION`, `DEPLOYED_MANIFEST` y `ENVIRONMENT_OVERRIDE`;
- `CONFIGURATION_TEST` y `AUTHORIZED_QA_RUNTIME_TEST`;
- `ASSESSMENT_FINDING` y `OTHER_AUTHORITATIVE_EVIDENCE`.

No sostienen nada:
- `REPOSITORY_DEFAULT_CONFIGURATION`, que es la intención del repositorio y no lo desplegado;
- `SOURCE_CODE`;
- `ENDPOINT_NAME`, `VERSION_BANNER` y `PRODUCT_DOCUMENTATION`;
- un README, un agente o una skill.

Un `ENVIRONMENT_OVERRIDE` citado que establece una fuga le gana a un
`REPOSITORY_DEFAULT_CONFIGURATION` que dice que no hay fuga.

### El banner, el nombre y el error

- **`VERSION_BANNER`** nunca hace `FAIL` en Vu7, salvo que la misma evidencia establezca la entrega
  de una clase `PRIVATE` a un consumidor no autorizado.
- **`ENDPOINT_NAME`** nunca hace `FAIL`.
- **Una respuesta de error del software de base** que entrega un dato privado es evidencia para Vu7
  y para Vu6. El check de Vu7 no lee ni escribe el resultado de Vu6.

### La prueba es segura o no cuenta

Una `AUTHORIZED_QA_RUNTIME_TEST` cuenta si cumple todo esto:
- `authorized: true`;
- el ambiente es `DEV`, `QA`, `HML` u `OTHER`, y es el del registro;
- `syntheticFixtures: true`;
- `destructive` no es `true`;
- `realPrivateDataAccessed` no es `true`;
- `rawSecretsLogged` no es `true`.

Si no, da `BASE_SOFTWARE_DISCLOSURE_TEST_UNSAFE`. Con `outcome: UNAVAILABLE`, da
`TEST_TARGET_UNAVAILABLE`. Ninguna de las dos es `FAIL`.

### La evidencia no guarda el dato

El registro no tiene campo para un valor, y el schema se cierra con `additionalProperties: false` en
todas sus capas. La salida, `rules.Vu7` y el libro de seguridad llevan ids, clases y estados, nunca
el texto de una evidencia ni una muestra del dato.

### Las reglas que ya costaron pases, desde el primer día

Son las seis de Vu6, sin cambios:
1. Lo que dice "no" pasa por la misma compuerta que lo que dice "sí".
2. Lo ilegible que nombra el componente o la superficie impide el `PASS`, citado o no, y lo no
   citado nunca hace `FAIL`. Un id que no es texto es ilegible, nunca una excepción.
3. La falla establecida gana siempre: una fuga citada y legible es `FAIL` diga lo que diga el
   registro. Una no citada deja la superficie sin resolver.
4. Todo id se normaliza a NFC antes de comparar y antes de contar repetidos.
5. Hay un solo paso de bloqueo. Bloquea una prueba insegura o sin objetivo que nombra algo del
   registro y que está citada o dice que hay fuga. Nunca tapa un `FAIL` y nunca reemplaza un sin
   resolver anterior.
6. Hay una sola regla de salida de secretos, la de `controles/lib/evidencia.py`, sin tocarla.

### El agregado, la unidad y el reporte

- **`PASS`** exige inventario entero, clases resueltas, superficies y configuraciones resueltas, y
  ninguna fuga.
- **Una fuga** hace `FAIL`.
- **Un sin resolver material** impide el `PASS`.

La unidad lleva `rules.Vu7` con `result`, `environment`, `components` y `evidence`, sin
`applicability`, porque la regla es `ALWAYS`. La salida pasada por `seguridad.resultado("Vu7", …)` y
por `desde_regla` entra al mismo libro de seguridad.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/reglas/base-software-data-disclosure.json` | El registro, instalado vacío |
| `comun/schemas/base-software-data-disclosure.schema.json` | Su contrato, cerrado en todas las capas |
| `harnesses/desarrollo/reglas/es0902-vu7-governance.md` y `es0902-vu7-base-software-data-disclosure-configuration-check.md` | Gobierno y procedimiento, como vinieron |
| `harnesses/desarrollo/controles/policies/base-software-private-data-disclosure-prohibited.md` | La policy |
| `harnesses/desarrollo/controles/checks/base-software-data-disclosure-configuration.py` | El check |
| `harnesses/desarrollo/bin/orquestacion/normativa.py` | `rules.Vu7` en la unidad |
| `harnesses/desarrollo/reglas/control-registry.json` | Los dos controles |
| `docs/seguridad-es0902.md` | Vu7 |
| `tests/casos/54_es0902_vu7_software_de_base.py` | Los escenarios |

## Escenarios verificables

El paquete no trae una lista `VU7-nn`. Los escenarios salen del paquete y de las reglas de Vu3 a
Vu6.

### La fila

- **E-01** — La clave es exactamente `ES0902.Vu7`, en la fila y en todo resultado. · rojo visto: si
- **E-02** — `base-software-private-data-disclosure-prohibited` y
  `base-software-data-disclosure-configuration` están exactos en la matriz, el registro de controles
  y el módulo. La fila es `ALWAYS` sin señal. Los agentes son los de la matriz, en este orden:
  `dev-security` y `dev-devops`. · rojo visto: si
- **E-03** — No hay ningún agente, skill, review ni señal nuevos, y `ALGORITMOS` sigue en diez.
  · rojo visto: si

### `ALWAYS`

- **E-04** — El check nunca emite `NOT_APPLICABLE`, con ninguna entrada. · rojo visto: si
- **E-05** — El registro vacío da `BASE_SOFTWARE_INVENTORY_UNRESOLVED`. · rojo visto: si

### El inventario y las superficies

- **E-06** — Un componente nombrado en el `BASE_SOFTWARE_INVENTORY` citado y sin entrada da
  `BASE_SOFTWARE_INVENTORY_UNRESOLVED`. · rojo visto: si
- **E-07** — Sin ninguna `BASE_SOFTWARE_INVENTORY` autoritativa citada, el inventario no está entero.
  · rojo visto: si
- **E-08** — Una superficie nombrada en el `DISCLOSURE_SURFACE_SCOPE` sin entrada da
  `DISCLOSURE_SURFACE_COVERAGE_UNRESOLVED`. · rojo visto: si
- **E-09** — Un componente o una superficie fuera del inventario o del alcance impide el `PASS` y
  no hace `FAIL` por estar afuera. · rojo visto: si
- **E-10** — El módulo no tiene ninguna lista de productos ni de tipos de componente: dos productos
  distintos con la misma evidencia dan el mismo resultado. · rojo visto: si

### La clasificación

- **E-11** — Una clase `PRIVATE` sin `DATA_CLASSIFICATION` autoritativa citada da
  `PRIVATE_DATA_CLASSIFICATION_UNRESOLVED` en la superficie que la nombra. · rojo visto: si
- **E-12** — Un `dataClassId` que parece privado (`dni`, `cuit`, `password`) sin clasificación no
  se trata como privado. · rojo visto: si
- **E-13** — Una fuga establecida de una clase `NOT_PRIVATE` no es `FAIL` de Vu7.
  · rojo visto: si

### La configuración efectiva y el ambiente

- **E-14** — `configurationStatus: UNRESOLVED` da `BASE_SOFTWARE_CONFIGURATION_UNRESOLVED`.
  · rojo visto: si
- **E-15** — Un `REPOSITORY_DEFAULT_CONFIGURATION` que dice que no hay fuga, solo, no cumple.
  · rojo visto: si
- **E-16** — Un `ENVIRONMENT_OVERRIDE` citado que establece la fuga le gana al default del
  repositorio: da `FAIL`. · rojo visto: si
- **E-17** — Una `EFFECTIVE_CONFIGURATION` de `DEV` no sostiene nada en un registro de `QA`.
  · rojo visto: si
- **E-18** — Un registro con `environment` nulo da `BASE_SOFTWARE_CONFIGURATION_UNRESOLVED` en toda
  superficie. · rojo visto: si
- **E-19** — Una `SOURCE_CODE`, sola, no cumple ninguna superficie. · rojo visto: si

### La fuga y el acceso autorizado

- **E-20** — Una fuga de una clase `PRIVATE` a un consumidor `UNAUTHORIZED`, establecida, da
  `UNAUTHORIZED_PRIVATE_DATA_DISCLOSURE` y `FAIL`. · rojo visto: si
- **E-21** — Lo mismo con `authorizationContext: PUBLIC`. · rojo visto: si
- **E-22** — El mismo dato servido a un consumidor `AUTHORIZED`, con `AUTHORIZATION_CONTEXT` citado,
  cumple y no es fuga. · rojo visto: si
- **E-23** — `AUTHORIZED_PRIVATE_DATA_ACCESS` sin `AUTHORIZATION_CONTEXT` citado no cumple.
  · rojo visto: si
- **E-24** — `NO_PRIVATE_DATA_DISCLOSURE` con una `EFFECTIVE_CONFIGURATION` del ambiente citada
  cumple. · rojo visto: si
- **E-25** — Un listado de directorios, una exposición de backups o una interfaz de administración
  cumplen o fallan por lo que la evidencia establece, no por su tipo de superficie.
  · rojo visto: si

### El banner, el nombre y el error

- **E-26** — Un `VERSION_BANNER`, solo, no hace `FAIL`. · rojo visto: si
- **E-27** — Un `ENDPOINT_NAME` como `/actuator`, solo, no hace `FAIL` ni cumple.
  · rojo visto: si
- **E-28** — Una evidencia citada por Vu6 y por Vu7 deja a cada regla con su resultado: el de Vu6 no
  entra ni sale del check de Vu7. · rojo visto: si

### La prueba

- **E-29** — Una prueba en QA con fixtures sintéticos cuenta. · rojo visto: si
- **E-30** — Una prueba en `PRD`, destructiva, con `realPrivateDataAccessed: true`, sin fixtures
  sintéticos o con secretos registrados da `BASE_SOFTWARE_DISCLOSURE_TEST_UNSAFE`. El módulo no
  ejecuta nada. · rojo visto: si
- **E-31** — Una prueba de otro ambiente que el del registro no cuenta. · rojo visto: si
- **E-32** — Una prueba insegura no es `FAIL`, también cuando dice que hay fuga.
  · rojo visto: si

### La evidencia y la salida

- **E-33** — El texto de una evidencia y una muestra de un dato no aparecen en la salida, en
  `rules.Vu7` ni en el libro de seguridad. Solo aparecen sus ids. · rojo visto: si
- **E-34** — Nada con forma de credencial sale, tampoco como clave de un diccionario.
  · rojo visto: si
- **E-35** — El registro vacío instalado valida contra el schema, y una clave de más en cualquier
  capa no valida. · rojo visto: si

### Las reglas de siempre

- **E-36** — Una evidencia ilegible que nombra el componente o la superficie impide el `PASS`, y un
  id que no es texto nunca levanta una excepción. · rojo visto: si
- **E-37** — La falla establecida gana siempre: una fuga citada con el registro en
  `NO_PRIVATE_DATA_DISCLOSURE` da el mismo `FAIL` que con el registro honesto.
  · rojo visto: si
- **E-38** — El bloqueo es uno solo, con la regla 5, y una prueba no citada que dice "sin fuga" no
  bloquea. · rojo visto: si

### Los límites

- **E-39** — El `PASS` de Vu7 no pone en `PASS` a Vu6, a C3, a Ve1 ni a la aprobación oficial.
  · rojo visto: si
- **E-40** — Un veredicto de integridad del repositorio en la evidencia no cambia el resultado de
  Vu7. · rojo visto: si

### El agregado

- **E-41** — Una fuga en cualquier superficie hace `FAIL` el agregado. · rojo visto: si
- **E-42** — Un sin resolver material impide el `PASS`. · rojo visto: si
- **E-43** — La misma evidencia da el mismo resultado en cualquier orden, también con ids iguales en
  NFC. · rojo visto: si
- **E-44** — La trazabilidad `ES0902 / 6.2 / 6 / Vu7` viaja en todo resultado, y la unidad lleva
  `rules.Vu7` sin `applicability`. · rojo visto: si
- **E-45** — La salida pasada por `seguridad.resultado` y `desde_regla` entra como `RULE_EVALUATION`
  de `ES0902.Vu7` al mismo libro, y `reporte_seguridad/` no tiene ningún archivo nuevo.
  · rojo visto: si

## Cómo se verifica

Todos los escenarios van por la suite, en `tests/casos/54_es0902_vu7_software_de_base.py`, con el
id en el título. Ninguno lleva `· verificación: lectura`. Se refuta en tanda con Vu8.

## Riesgos conocidos

- **Casi todo proyecto real va a quedar sin resolver.** Pocos proyectos tienen un inventario
  autoritativo del software de base y una clasificación de datos privados.
- **Un registro por ambiente** obliga a repetir el registro para QA, HML y PRD.
- **La frontera entre `EFFECTIVE_CONFIGURATION` y `REPOSITORY_DEFAULT_CONFIGURATION`** depende de
  quien clasifica la evidencia.
