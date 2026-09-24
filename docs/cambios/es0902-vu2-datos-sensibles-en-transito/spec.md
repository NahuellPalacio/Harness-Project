# ES0902 Vu2 — ningún dato sensible en texto plano, salto por salto y con evidencia

**Estado:** verificado y cerrado, con E-08, E-13 y E-43 contradichos documentados · **Fecha:** 23-09-2026 · **Regla:** ES0902 6.2 §6 Vu2

## Qué problema resuelve

> *"Todo dato sensible no puede ser enviado en texto plano."* (ES0902 v6.2, pág. 7)

La fila ya está en la matriz —`CONDITIONAL` sobre `sensitiveDataTransmissionPresent`,
`dev-security`, una policy, un check, cero reviews— y sus dos controles están declarados y no
construidos (`sensitive-data-plaintext-transmission-prohibited`,
`sensitive-data-transport-protection`). Nada produce la señal.

El estándar no define qué es un dato sensible, y Vu2 tiene seis formas baratas de ponerse en verde:

1. **El nombre del campo por la clasificación.** Que no haya un campo `password` no dice que no viaje
   nada sensible; que haya un campo `dni` no dice que lo sea.
2. **El borde por el camino.** `cliente --HTTPS--> proxy --HTTP--> backend` tiene un salto en claro.
3. **La codificación por el cifrado.** Base64, URL, hex, compresión, serialización, un JWT sólo
   firmado, la ofuscación: todo eso viaja legible. Y un hash no es cifrar el transporte.
4. **`https://` por la protección.** Con la validación de certificado apagada, o con la configuración
   real diciendo otra cosa, la URL no prueba nada.
5. **El requisito criptográfico inventado.** Versión mínima de TLS, suites, tamaño de clave, mTLS:
   Vu2 no dice ninguno.
6. **La prueba con el dato real.** Mandar un dato sensible para probar que viaja cifrado es mandarlo.

## Qué queda afuera

- **Una taxonomía de datos sensibles.** La clasificación la trae el proyecto con su fuente; el módulo
  no tiene ninguna lista de nombres de campo ni de categorías.
- **Cifrado en reposo, retención, enmascaramiento, logs.** Vu2 es confidencialidad en tránsito.
- **Endurecimiento de TLS.** Se mira lo necesario para decir en claro o protegido: transporte
  explícitamente sin cifrar, validación de certificado o de hostname apagada. Nada de versiones ni
  suites.
- **Ejecutar pruebas o capturar tráfico.** El check lee evidencia de una prueba ya hecha y decide si
  era segura.
- **Reusar el inventario de C1.** No tiene nada que ver: Vu2 trae su propio registro de clases de
  datos y caminos, del proyecto, instalado vacío.
- **Tocar Vu1.** Vu1 cerró con E-39 y E-42 contradichos. Vu2 escribe su regla de secretos con los
  arreglos que Vu1 dejó anotados, y la unificación de las dos es trabajo aparte.
- **Un algoritmo en `seguridad.py`, un agente, una skill o una review.** Camino genérico, como Vu1;
  `ALGORITMOS` sigue en diez.

## Las decisiones, y por qué

### La evidencia es un catálogo cerrado, y cada ítem nombra a qué se refiere

Como en C1 y Vu1, los strings de `classificationEvidence` y `evidence` son ids de un catálogo que
viaja en el caso. La forma del ítem la controla el check, y esta vez es **cerrada**: un campo que no
está declarado —`payload`, `sample`— deja el ítem mal formado. Así no hay dónde guardar un valor
sensible.

```
evidenceId, sourceType, reference, establishes[], scope
targets[]          los dataClassId o pathId de los que habla. Obligatorio
hop                "from->to", para lo que habla de un salto
value              el valor que establece, de un enum por dimensión
outcome            CONFIRMED | UNAVAILABLE | otro
syntheticData, authorized, payloadCaptured   sólo para una prueba
```

### La clasificación sale de una autoridad, y se contradice en las dos direcciones

Una clase cuenta como `SENSITIVE` o `NOT_SENSITIVE` cuando lo declara el registro **y** una evidencia
citada de una clase autoritativa —política de clasificación del GCBA, política de ASI, requisito de
seguridad del proyecto, documentación de arquitectura, hallazgo de assessment, contrato del proyecto,
otra evidencia autoritativa— establece `DATA_CLASSIFICATION` con ese mismo valor. El nombre del
campo, un escáner de secretos, un README o un agente no clasifican. Lo declarado contra lo que dice
una evidencia legible —en cualquier dirección, citada o no— queda sin resolver.

### La señal enciende con autoridad y apaga con más autoridad

```
TRUE        un camino con saltos lleva una clase SENSITIVE con autoridad
FALSE       todas las clases que viajan son NOT_SENSITIVE con autoridad, la cobertura consta y no
            hay ninguna clase sin resolver; o el inventario está vacío y una evidencia autoritativa
            establece NO_SENSITIVE_TRANSMISSION para el alcance del caso
UNRESOLVED  cualquier otra cosa, con SENSITIVE_DATA_CLASSIFICATION_UNRESOLVED o
            TRANSMISSION_PATH_COVERAGE_UNRESOLVED como motivo
```

A diferencia de Vu1, acá encender también exige autoridad: el paquete dice que la sensibilidad no
sale de un nombre de campo. Una clase declarada sensible sin fuente no enciende ni apaga.

### Salto por salto

Cada salto de un camino que lleva una clase sensible se evalúa solo, y sale `PROTECTED`, `PLAINTEXT`
o sin resolver. El camino falla si un salto está en claro, pasa si todos están protegidos, y si no
queda con el estado del que falta. Los saltos tienen que encadenarse —el `to` de uno es el `from`
del siguiente—: un hueco en la cadena es un salto que nadie declaró, y deja la cobertura sin
resolver.

Un salto no se evalúa sólo si una evidencia **de arquitectura** establece `NOT_MATERIAL_BOUNDARY`
para ese salto: es la excepción que el paquete nombra, y el paquete dice arquitectura. Dos saltos
del mismo camino con el mismo `from->to` no se distinguen —una evidencia valdría para los dos— y
dejan la cobertura sin resolver.

### En claro es un hecho, no una ausencia

`PLAINTEXT` tiene tres caminos, y los tres son hechos: el registro lo declara, el transporte es
explícitamente sin cifrar —`http` o `ws`— sin cifrado de aplicación con evidencia, o una evidencia
citada y legible lo establece: `TRANSPORT_CONFIDENTIALITY` en `PLAINTEXT`, o `REDIRECT_DOWNGRADE` en
`EXPOSES_PAYLOAD` —un redirect o un downgrade que expone el payload, que el paquete nombra—. Un "en
claro" que no se confirmó (`outcome` que no es `CONFIRMED`) no hace `FAIL` y tampoco se descarta:
impide el `PASS`. Una codificación sobre un transporte en claro también es en claro. Lo
que no se sabe queda `TRANSPORT_PROTECTION_UNRESOLVED`.

### Protegido quiere decir evidencia de ese salto

`PROTECTED` exige que el registro lo declare y que el salto cite una evidencia legible, de una clase
de configuración o de ejecución —configuración de despliegue, de transporte en ejecución, de red o de
la aplicación, metadata de conexión, documentación de arquitectura, hallazgo de assessment, prueba
sintética autorizada, otra evidencia autoritativa—, que establezca `TRANSPORT_CONFIDENTIALITY` con
`value: PROTECTED`, nombre el camino en `targets` y el salto en `hop`. La forma de la URL y el código
fuente solo no alcanzan. Una codificación o un hash como mecanismo nunca es protección. Validación
de certificado o de hostname en `DISABLED` impide el `PROTECTED` y no es `FAIL`; en `UNRESOLVED` o
ausente no bloquea: el paquete pide mirarlo *donde haya evidencia*.

### Las tres reglas que Vu1 dejó

1. **Lo que dice que no pasa por la misma compuerta que lo que dice que sí.** Una prueba insegura o
   sin objetivo no aprueba ni hace `FAIL`, diga lo que diga.
2. **Lo ilegible que nombra el camino impide el `PASS`, citado o no; lo no citado nunca hace
   `FAIL`.** "Nombra" se decide por igualdad de texto contra el `pathId`, recorriendo los textos del
   ítem —no por subcadena del JSON escapado, que es el E-42 de Vu1—.
3. **Nada con forma de credencial sale, venga de donde venga.** Regla de salida única, con la forma
   corregida del E-39 de Vu1: la clave termina en la palabra y un `:` o una `/` antes no la esconde.
   De un ARN se saca **sólo** el prefijo de un secreto de un gestor
   (`arn:aws:secretsmanager:<región>:<cuenta>:secret:`) y el resto se mira igual: `arn:password=` no
   es un ARN, y un ARN con `password=` adentro sigue siendo una credencial. (Refutador, pase 1.) Los
   ids se comparan en NFC. Y la `description` de una clase no sale nunca.

### La regla del segundo pase: todo id se compara con la misma función

El segundo pase encontró tres contradichos con una sola causa: lo ilegible se comparaba en NFC y lo
legible no, así que un "no" legible con el id en NFD pesaba menos que el mismo ítem mal formado. La
respuesta es una regla y no tres arreglos: **toda** comparación de ids —`targets`, `hop`, alcance,
`dataClassId`, `dataClassRefs`, `pathId`— pasa por la misma función, en NFC. Y un "no" sobre el
camino que no dice de qué salto habla, o que no dice qué valor establece, bloquea el camino en vez de
descartarse.

### La prueba es sintética o no cuenta

Una evidencia `AUTHORIZED_SYNTHETIC_TEST` cuenta si `syntheticData: true`, `authorized: true` y
`payloadCaptured` no es `true`. Si no, `SENSITIVE_DATA_TRANSPORT_TEST_UNSAFE`. Con `outcome:
UNAVAILABLE`, `TEST_TARGET_UNAVAILABLE`. Ninguna de las dos es `FAIL`.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/reglas/sensitive-data-transmission.json` | El registro del proyecto, instalado vacío |
| `comun/schemas/sensitive-data-transmission.schema.json` | Su contrato, el provisto con `additionalProperties: false` en las cuatro capas |
| `harnesses/desarrollo/reglas/es0902-vu2-governance.md` | El gobierno, como vino |
| `harnesses/desarrollo/reglas/es0902-vu2-sensitive-data-transmission-present-signal.md` | La señal, como vino |
| `harnesses/desarrollo/reglas/es0902-vu2-sensitive-data-transport-protection-check.md` | El procedimiento, como vino |
| `harnesses/desarrollo/controles/policies/sensitive-data-plaintext-transmission-prohibited.md` | La policy |
| `harnesses/desarrollo/controles/checks/sensitive-data-transport-protection.py` | La señal derivada y el check |
| `harnesses/desarrollo/reglas/control-registry.json` | Los dos controles, declarados |
| `docs/seguridad-es0902.md` | Vu2 |
| `tests/casos/46_es0902_vu2_datos_sensibles_en_transito.py` | Los escenarios |

Se reescriben los conteos clavados: controles 42 → 44, los de forma singular 36 → 38, checks en
disco 17 → 18, huecos de ES0902 27 → 25.

## Escenarios verificables

### La fila

- **E-01** — La clave es exactamente `ES0902.Vu2`, en la fila y en todo resultado.
  · rojo visto: si
- **E-02** — La única señal es `sensitiveDataTransmissionPresent`, y es la que el check produce.
  · rojo visto: si
- **E-03** — `dev-security`, `sensitive-data-plaintext-transmission-prohibited` y
  `sensitive-data-transport-protection`, con esos ids en la matriz, el registro y el módulo.
  · rojo visto: si
- **E-04** — Ningún agente, skill ni review nuevos. · rojo visto: si

### La señal

- **E-05** — Un camino con saltos que lleva una clase sensible con autoridad pone la señal en `TRUE`,
  la cita con la fuente de su clasificación, la clase, los saltos y el alcance, y pasada por
  `senales` enciende la fila; sin inventario, o con uno que no valida, es `UNRESOLVED`. · rojo visto: si
- **E-06** — Un nombre de campo no enciende: una clase declarada sensible con evidencia
  `FIELD_NAME_PATTERN`, `README_STATEMENT` o `AGENT_STATEMENT` deja la señal `UNRESOLVED` con
  `SENSITIVE_DATA_CLASSIFICATION_UNRESOLVED`. · rojo visto: si
- **E-07** — Todas las clases que viajan no sensibles con autoridad, o el inventario vacío con
  `NO_SENSITIVE_TRANSMISSION` autoritativa para el alcance, ponen la señal en `FALSE` y el check en
  `NOT_APPLICABLE`; la misma afirmación de una fuente débil, no. · rojo visto: si
- **E-08** — La ausencia no apaga: el inventario vacío, un escáner sin hallazgos
  (`SECRET_SCANNER`), una clase sin resolver al lado de las no sensibles, o un camino detectado que
  el inventario no tiene dejan la señal `UNRESOLVED`. · rojo visto: si

### La clasificación

- **E-09** — Una clase declarada sensible sin evidencia autoritativa, en un camino al lado de uno
  sensible con autoridad, deja el check en `SENSITIVE_DATA_CLASSIFICATION_UNRESOLVED`, no en `PASS`.
  · rojo visto: si
- **E-10** — Lo declarado contra una evidencia legible que dice lo contrario —sensible contra no
  sensible y al revés, citada o no— queda sin resolver. · rojo visto: si
- **E-11** — El harness no inventa una taxonomía: ningún literal operativo del módulo es un nombre
  de campo o una categoría de dato (`dni`, `cuit`, `cuil`, `email`, `telefono`, `tarjeta`, `card`,
  `phone`). · rojo visto: si

### La cobertura

- **E-12** — Un camino detectado que el inventario no tiene deja
  `TRANSMISSION_PATH_COVERAGE_UNRESOLVED`. · rojo visto: si
- **E-13** — Un camino que referencia una clase que no existe, ids de camino o de clase repetidos, un
  camino sin saltos, o dos saltos con el mismo `from->to` dejan la cobertura sin resolver, y la
  cobertura nombra cuál. · rojo visto: si
- **E-14** — Saltos que no se encadenan —el `to` de uno no es el `from` del siguiente— dejan la
  cobertura sin resolver. · rojo visto: si

### Salto por salto

- **E-15** — `https` en el borde y `http` en el salto interno es `FAIL` con
  `PLAINTEXT_SENSITIVE_TRANSMISSION_DETECTED`, nombrando ese salto; un salto declarado `PLAINTEXT`
  también. · rojo visto: si
- **E-16** — Cada salto se evalúa solo: uno protegido no cubre al de al lado sin resolver, y el
  camino queda con el estado del que falta. · rojo visto: si
- **E-17** — Todos los saltos protegidos con evidencia dan `PASS`. · rojo visto: si
- **E-18** — La terminación de TLS en el ingreso no cubre lo de atrás: una evidencia que nombra el
  salto del borde no sostiene el salto interno. · rojo visto: si
- **E-19** — Un salto con `NOT_MATERIAL_BOUNDARY` de documentación de arquitectura no se evalúa y no
  falla; con una fuente débil, con configuración de red o con un hallazgo de assessment, sí se
  evalúa. · rojo visto: si

### Qué no es cifrar

- **E-20** — Base64, codificación URL, hex, compresión, serialización, JWT sólo firmado y ofuscación
  como mecanismo sobre `http` son `FAIL`, las siete. · rojo visto: si
- **E-21** — Las mismas codificaciones sobre un transporte que no se conoce no son `PROTECTED`,
  aunque el registro lo declare. · rojo visto: si
- **E-22** — Un hash nunca es `PROTECTED` y solo no es `FAIL`: queda sin resolver.
  · rojo visto: si
- **E-23** — El cifrado de aplicación sobre `http`, con evidencia autoritativa, es `PROTECTED`.
  · rojo visto: si

### `https` no es prueba

- **E-24** — `https` con sólo evidencia `URL_SCHEME` queda sin resolver. · rojo visto: si
- **E-25** — `PROTECTED` declarado contra una evidencia legible que dice `PLAINTEXT`: citada es `FAIL`,
  no citada queda sin resolver; `PLAINTEXT` declarado contra evidencia que dice `PROTECTED` también
  queda sin resolver; y un `PLAINTEXT` citado sin confirmar impide el `PASS`. · rojo visto: si
- **E-26** — Validación de certificado o de hostname en `DISABLED` impide el `PASS` sin ser `FAIL`;
  en `UNRESOLVED`, ausente o `NOT_APPLICABLE` no bloquea. · rojo visto: si
- **E-27** — El código fuente solo (`SOURCE_CODE`) no prueba la protección en ejecución.
  · rojo visto: si

### Nada inventado

- **E-28** — Ningún literal operativo ni campo de salida nombra una versión de TLS, una suite, un
  tamaño de clave, mTLS o una rotación de certificado. · rojo visto: si
- **E-29** — El módulo no tiene números salvo 0 y 1. · rojo visto: si

### La prueba

- **E-30** — Una prueba sintética, autorizada y sin captura de payload sostiene el salto.
  · rojo visto: si
- **E-31** — Con datos reales, con el payload capturado o sin autorización:
  `SENSITIVE_DATA_TRANSPORT_TEST_UNSAFE`, y no es `FAIL` aunque la prueba diga `PLAINTEXT`.
  · rojo visto: si
- **E-32** — Una prueba sin objetivo es `TEST_TARGET_UNAVAILABLE`, no `FAIL`, también cuando dice
  `PLAINTEXT` y también cuando además es insegura. · rojo visto: si
- **E-33** — El módulo no ejecuta nada: no importa red ni procesos, de `os` sólo usa `os.path`, y no
  abre ningún archivo para escribir. · rojo visto: si

### La evidencia y los secretos

- **E-34** — El registro se instala vacío y valida; el schema rechaza una clave de más en las cuatro
  capas; con la señal en `TRUE` y el registro vacío, la cobertura no consta. · rojo visto: si
- **E-35** — Un ítem del catálogo con un campo no declarado —`payload`, `sample`— no cuenta, y si
  nombra el camino impide el `PASS`. · rojo visto: si
- **E-36** — Nada con forma de credencial sale en ningún campo del resultado ni de la señal —ids de
  camino o de clase, transportes, mecanismos, caminos detectados, ids de evidencia, errores de
  schema—, también con prefijo (`app:password=`, `env/DB_PASSWORD=`, `arn:password=`, un ARN con
  `password=` adentro); el ARN de un secreto de un gestor o `tokenLifespan=` no tienen esa forma; y la `description` de una clase no sale nunca.
  · rojo visto: si
- **E-37** — Una evidencia ilegible —repetida o mal formada— que nombra el camino impide el `PASS`,
  citada o no, también con un `pathId` con acentos o comillas, y en NFD contra NFC; no citada nunca hace `FAIL`; y una
  sobre otro camino cuyo id contiene a éste no lo bloquea. · rojo visto: si

### Los límites

- **E-38** — `PASS` de Vu2 no es Vu7, D8 ni C1, ni al revés: con los controles de Vu2 en `PASS`, Vu7
  y C1 no cumplen, y con los de las tres en `PASS` Vu2 no cumple. D8 es de ES0901, que no tiene
  resultado de regla: su independencia se prueba por la fila —la de D8 no declara controles de Vu2,
  ni la de Vu2 los de D8—. · rojo visto: si
- **E-39** — Ningún literal operativo del módulo nombra los controles de Vu7, D8 o C1.
  · rojo visto: si

### El agregado

- **E-40** — Un camino en `FAIL` pone todo en `FAIL`, aunque los otros pasen. · rojo visto: si
- **E-41** — Un camino sin resolver impide el `PASS`. · rojo visto: si
- **E-42** — Un camino que sólo lleva clases no sensibles con autoridad no se evalúa y no bloquea,
  aunque tenga un salto en `http`. · rojo visto: si
- **E-43** — La misma evidencia da el mismo resultado: desordenar clases, caminos, saltos no (el
  orden de los saltos es la cadena), evidencia y referencias no cambia nada, también con ids
  repetidos. · rojo visto: si
- **E-44** — La trazabilidad `ES0902 / 6.2 / 6 / Vu2` y `ES0902.Vu2` viaja en todo resultado y en
  el bloque normativo de la unidad. · rojo visto: si

### Redirect y downgrade

- **E-45** — Un redirect o un downgrade que expone el payload (`REDIRECT_DOWNGRADE` en
  `EXPOSES_PAYLOAD`, de una fuente de transporte) es `FAIL` citado, impide el `PASS` no citado, y de
  una fuente débil no cuenta. (Agregado por el primer pase: el paquete lo pide.) · rojo visto: si

### La regla del segundo pase

- **E-46** — Todo id se compara igual: un `PLAINTEXT` legible que nombra el camino en NFD es `FAIL`
  citado y bloquea no citado; lo mismo un redirect, y un `hop` con acentos en NFD; una clasificación
  contraria con el id de la clase en NFD deja la clase sin resolver y no apaga la señal; y una
  referencia a la clase en NFD es la misma clase. (Agregado por el segundo pase.) · rojo visto: si
- **E-47** — Un en claro o un redirect sobre el camino sin `hop`, con un `hop` que el camino no tiene,
  o sin `value`, impide el `PASS` y no hace `FAIL`. (Fuera de la letra del segundo pase.)
  · rojo visto: si

## Cómo se verifica

Los cuarenta y siete por `.\tests\Invoke-Tests.ps1`; ninguno por lectura. El archivo de tests arma
un camino de tres saltos que aprueba —navegador a ingreso, ingreso a backend, backend a proveedor—
y lo rompe salto por salto. Ids y estados clavados por literal.

## Riesgos conocidos

- **Nadie produce la evidencia todavía.** El registro llega vacío y toda corrida real da
  `APPLICABILITY_UNRESOLVED`.
- **La tabla de clases de fuente es del harness**, no del estándar.
- **`http` y `ws` son los únicos transportes que el módulo reconoce como en claro.** Otros (FTP,
  LDAP sin StartTLS) quedan sin resolver, no en `FAIL`: nombrarlos es empezar un catálogo de
  protocolos que el estándar no trae.
- **La regla de secretos está dos veces**, en Vu1 y en Vu2, con formas distintas hasta que Vu1 se
  arregle. Anotado.
- **`reglas/` se sobrescribe en cada `-Update`.**
