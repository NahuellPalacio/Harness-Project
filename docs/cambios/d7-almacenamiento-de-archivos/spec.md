# D7 — Los archivos van al storage estándar, el local permanente está prohibido y el temporal se destruye

**Estado:** verificado y cerrado · **Fecha:** 21-09-2026 · **Regla:** ES0901 6.3 §7.1 D7

## Qué problema resuelve

La regla citable, `ES0901-7.1-D7`, pág. 13:

> *"Si la aplicación gestiona archivos (PDF, DOC, PNG, JPG, etc.) debe almacenarlos en el storage
> estándar del GCABA. No está permitido guardar en forma permanente archivos en forma local. Para
> los casos temporales la destrucción de los mismos debe ser en forma inmediata."*

Y el apartado que la sostiene, **Archivos adjuntos: S3 del GCABA**, pág. 19:

> *"Todo documento adjunto que necesite guardar una aplicación debe resguardarse en el repositorio
> estándar para tal fin del GCABA... La tecnología actual está basada en el protocolo S3 (Simple
> Storage Service)."*

Más las **pautas de estructura de carpetas (HCP)**, págs. 19-20: planificar la estructura antes de
almacenar, evitar concentrar tráfico en una sola carpeta, equilibrar ancho y profundidad, *"no crear
estructuras de carpetas que tengan más de 20 niveles de profundidad"* y *"evitar colocar una gran
cantidad de objetos (más de 100.000) en una sola carpeta"*.

🔴 **Una sola oración del estándar lleva tres obligaciones independientes**, y ése es el problema
central de este cambio:

```
1  archivo persistente     ->  storage estandar del GCBA
2  local permanente        ->  prohibido
3  temporal local          ->  destruccion atada al fin de su proposito
```

Las tres se verifican por separado y ninguna contesta por las otras. Una aplicación puede subir
todos sus adjuntos al storage estándar y dejar los temporales de conversión tirados en el disco. Una
aplicación puede no persistir nada localmente y no tener storage estándar. Colapsarlas en un único
*"¿usa S3?"* es el atajo que este cambio existe para cerrar.

Hoy el harness no puede decir nada de ninguna de las tres. La matriz declara la fila de D7 con su
señal, sus **tres** policies y sus **tres** checks desde que se construyó, y los seis controles **no
existen**: cualquier consulta los reporta como `DECLARED_POLICY_NOT_INSTALLED` y
`DECLARED_CHECK_NOT_INSTALLED`. Son los seis controles declarados y no construidos de una sola
regla — el número más alto de las 24 filas.

Y hay una trampa propia de esta regla, más fina que la de D6. El estándar **sí** nombra la
tecnología —el protocolo S3— y **no** nombra el repositorio: dice *"el repositorio estándar para tal
fin del GCABA"* y ahí se detiene. No hay endpoint, no hay nombre de bucket, no hay región, no hay
tenant, no hay credencial, no hay prefijo de objeto y no hay política de retención en ningún
extracto que este harness tenga. Un check que necesite esos valores y los invente convierte una
regla de cumplimiento en una configuración falsa con sello normativo. Y leer *"protocolo S3"* como
*"el contrato de un proveedor público de nube"* es la otra mitad de la misma invención: el estándar
nombra un protocolo, no un proveedor.

## Qué queda afuera

- **El mecanismo del storage estándar.** No se declara ningún endpoint, nombre de bucket o
  contenedor, región, tenant, credencial, prefijo de objeto, política de retención ni ruta de red.
  El harness no los sabe. La identidad entra como **dato declarado por el proyecto, con su fuente
  citada**; sin eso, `STANDARD_STORAGE_PROVIDER_UNRESOLVED`, y con identidad pero sin contrato,
  `STORAGE_INTEGRATION_CONTRACT_MISSING`.
- **El nombre de un proveedor de almacenamiento, el del GCBA y los de afuera.** Ni como identidad ni
  como contraejemplo — ver la decisión de más abajo. El protocolo **sí** se nombra: lo nombra el
  estándar.
- **Un umbral numérico de "inmediato".** Ninguna duración —ni segundos, ni minutos, ni horas, ni un
  TTL— se declara en ningún artefacto de D7. El pedido lo prohíbe explícitamente y el estándar no da
  un número: da un momento, el fin del propósito temporal.
- **Un cuarto control.** Las pautas de §8.4 —profundidad, concentración de objetos, tráfico— entran
  como **evidencia de `storage-backend-compliance`** y no como una policy ni un check nuevo. La
  matriz declara seis ids y este cambio instala esos seis: ni uno más, ni uno renombrado.
- **Un agente y una skill.** El dueño normativo de la fila sigue siendo `dev-backend` y la fila no
  declara ninguna skill. `dev-storage` ya está instalada y el registro de agentes la rutea; lo que
  este cambio hace es **resolverla**, no crearla. La obligación normativa y el procedimiento técnico
  siguen separados.
- **Ejecutar la aplicación.** Este cambio no abre un archivo, no sube nada y no borra nada. La
  corrida entra como dato, igual que en D4 y D6, y quien la ejecute son las skills instaladas.
- **Un segundo sistema de aplicabilidad.** La clasificación de flujos es **evidencia de
  implementación**: no decide si D7 aplica, no cambia el valor de la señal y no reemplaza a la
  matriz. Quien decide la aplicabilidad es `fileHandlingPresent` y nadie más.
- **Un productor específico de `fileHandlingPresent`.** La señal ya está declarada en la matriz y
  `senales.py` es genérico desde D1: produce, valida y resuelve cualquier señal declarada, con
  evidencia y con su productor. Este cambio no agrega una rama por id de señal — lo que agrega es
  qué cuenta como evidencia de un flujo de archivos, y eso va en la policy y en la documentación.
- **Arreglar el instalador.** `install.ps1` no copia `controles/`, así que con D7 son **veinticuatro**
  controles que declaran `INSTALLED` y que fuera de este repositorio serían `CONTROL_FILE_MISSING`.
  Es el ítem 2 de la tabla de prioridades, tiene su propia spec, y este cambio lo empeora en seis y
  lo dice.
- **El eje `REAL`/`MOCKED` de la evidencia de corrida.** D6 lo tiene porque una vista mockeada se
  dibuja igual; acá el pedido no lo pide y agregarlo sería inventar un requisito. Queda anotado en
  los riesgos.

## Las decisiones, y por qué

### Tres obligaciones, tres checks, y ninguno hereda el estado de otro

```
gcba-standard-storage-required              storage-backend-compliance
persistent-local-file-storage-prohibited    persistent-local-file-storage
temporary-file-immediate-destruction-req.   temporary-file-cleanup
```

Cada check contesta sobre su obligación y sólo sobre la suya. Un `PASS` de
`storage-backend-compliance` no dice nada sobre los temporales; un `FAIL` de
`persistent-local-file-storage` no arrastra a los otros dos. Es la propiedad que hace verificable la
frase del estándar: **son tres, y se rompen de a una**.

### Los tres estados de "no hay nada que verificar" no son el mismo estado

Los tres checks comparten la señal y el inventario de flujos, y sobre un inventario **completo** sin
flujos de su clase contestan distinto:

```
storage-backend-compliance     sin flujos persistentes  ->  NOT_APPLICABLE
temporary-file-cleanup         sin flujos temporales    ->  NOT_APPLICABLE
persistent-local-file-storage  sin escrituras locales   ->  PASS
```

La asimetría es deliberada. Las dos primeras son **obligaciones condicionales**: *si persiste, al
storage estándar*; *si crea un temporal, se destruye*. Sin sujeto no hay obligación que verificar, y
un `PASS` afirmaría *"los archivos persistentes van al storage estándar"* sobre una aplicación que no
persiste ninguno. La tercera es una **prohibición**: *no usar el local como repositorio permanente*.
Una prohibición sin sujeto está cumplida, no es inaplicable.

📌 Y la consecuencia importa: una aplicación que sólo maneja temporales **no** sale
`STANDARD_STORAGE_PROVIDER_UNRESOLVED`. La compuerta de identidad corre **después** de saber si hay
flujos persistentes, porque a quien no persiste no le hace falta un storage estándar. Al revés
—preguntar por el proveedor primero— la regla exigiría configuración a una aplicación que no la
necesita, que es exactamente lo que el pedido prohíbe en su punto 28.

### La identidad se declara, el protocolo se cita, y el proveedor no se nombra

El estándar nombra la tecnología y no el repositorio, así que el dato entra así:

```yaml
standardStorage:
  id: <lo que el proyecto declara>
  source: GCBA_NORMATIVE | GCBA_CATALOG_ENTRY | ASI_INTEGRATION_CONTRACT |
          PROJECT_INTEGRATION_AGREEMENT | HUMAN_CONFIRMATION
  reference: <donde lo dice>
  protocol: S3      # lo que el estandar dice, no lo que alguien supone
```

La lista dice **qué fuentes son defendibles**; no dice cuál es el repositorio. Y `protocol: S3` es
evidencia de protocolo: un cliente de ese protocolo no identifica un repositorio, igual que hablar
HTTP no identifica un sitio.

🔴 **Ningún artefacto de D7 nombra un proveedor de almacenamiento.** Ni el institucional, que no está
en ningún extracto, ni los de afuera que un caso podría usar. Tres motivos, en este orden:

1. Una lista de prohibidos envejece, y el proveedor número cuatro llega diciendo *el mío no está en
   la lista*.
2. La regla no es *no uses estos*: es *usá el estándar del GCBA*. Enumerar a los otros corre el eje.
3. Con la lista adentro, el invariante que verifica que no se inventó el mecanismo deja de poder
   distinguir un contraejemplo de una invención.

Lo que se verifica es estructural, sobre los artefactos de la regla:

```
localizadores de red      con esquema, sin esquema, con puerto -con o sin punto-, o una IP
nombres de infraestructura  bucket, contenedor, region, tenant, prefijo, retencion seguidos de : o =
credenciales              access key, secret key, bearer o token con un numero adentro
mecanismo declarado       endpoint, sdk, cliente, adapter seguidos de : o =
paquetes                  el gestor, el @scope/nombre, y como se importa
proveedores               los nombres de proveedor, juntos, partidos o pegados
duraciones                un numero seguido de una unidad de tiempo, o un TTL con valor
```

Las dos excepciones son explícitas y son del estándar: **`S3`** —el protocolo— y los **dos números de
§8.4**, 20 niveles y 100.000 objetos. Están citados, no inventados.

📌 La spec **no** entra en el barrido: es el documento que explica qué formas están prohibidas, y no
puede prohibirse nombrarlas.

### "Inmediato" es un momento, no un número

```
se crea el temporal
-> se usa para una operacion acotada
-> la operacion termina o falla
-> la limpieza corre como parte de ese mismo ciclo de vida
```

Eso es todo, y no hay un número adentro. Lo que **no** sustituye a esa atadura, aunque exista:

```
PERIODIC      un cron diario u horario
STARTUP       limpiar al arrancar
RESTART       confiar en el reinicio del contenedor
TTL           un TTL sin especificar
MANUAL        un procedimiento que alguien ejecuta
NONE          nada
```

Cualquiera de esos, **solo**, en un camino material, es `FAIL`. Al lado de una limpieza atada al
ciclo de vida son defensa en profundidad y no molestan. Es la única forma de leer *"en forma
inmediata"* sin inventar un umbral: el umbral no existe, lo que existe es la estructura.

### La técnica no se exige, la cobertura sí

`finally`, `defer`, `using`/`dispose`, un context manager, una primitiva de archivo temporal con
borrado determinista: son **ejemplos**, y el check no ramifica por ninguno. Lo que exige es que cada
camino material declare que su limpieza está atada al ciclo de vida y que haya traza de esa corrida.

Los caminos materiales son cuatro, y el cuarto es condicional:

```
NORMAL_COMPLETION   siempre
VALIDATION_FAILURE  siempre
PROVIDER_FAILURE    siempre
CANCELLATION        cuando el proyecto declara que el runtime permite limpiar
```

Un camino exigido que no está declarado deja el flujo en `CLEANUP_PATH_COVERAGE_UNRESOLVED`. La
limpieza sólo en el camino feliz es la forma más común del defecto y no llega a `PASS`.

### El ciclo de vida se establece, el nombre del path no clasifica

Para cada escritura local se establecen siete cosas:

```
pathOrAdapter  purpose  creation  consumption  cleanup  expectedLifetime  persistenceBehavior
```

Si falta una, `LOCAL_STORAGE_LIFECYCLE_UNRESOLVED`. Y **`tmp` en un path no prueba un ciclo de vida
temporal**: una escritura cuya única evidencia es cómo se llama la carpeta queda sin resolver, no
temporal. Lo mismo vale para *"corre en un contenedor"*. Los dos son suposiciones con formato de
evidencia, y las dos clases están declaradas inertes.

### El `signalId` se mira, y una señal ajena no sustituye

Los tres checks leen el `signalId` del dato que reciben, no sólo su `value`. Una señal de otra regla
en TRUE los deja en `APPLICABILITY_UNRESOLVED` con `SIGNAL_IDENTITY_MISMATCH` y con
`fileHandlingPresent` en `missingSignals`.

🔴 Sin eso, pasarle `frontendPresent` en TRUE hacía que dos de los tres dieran `PASS` y que los tres
publicaran `signal: fileHandlingPresent` al lado del resultado: **cumplimiento atribuido a una señal
que nunca llegó.** Es el mismo defecto que D5 ya cerró un nivel abajo, en su derivación —*"la
derivación mentía de dónde salió"*—, y acá estaba un nivel más arriba, en la puerta común de las
tres obligaciones.

Y se lee también el mapa `{id: resuelta}`, que es la forma en la que las señales viajan dentro de la
unidad de trabajo: se busca la de D7 por id, y un mapa que no la trae no resuelve.

### No saber nada y saber la mitad no son el mismo estado

En `persistent-local-file-storage`, que **ninguna** escritura local tenga su ciclo de vida
establecido es `LOCAL_STORAGE_LIFECYCLE_UNRESOLVED`; que lo tengan algunas y otras no es `PARTIAL`
con el mismo motivo. Un solo estado para los dos casos hace que remediar la mitad no se vea en
ningún lado, y eso es el incentivo exacto para no remediar la otra.

### Lo que está instalado no prueba lo que se guarda

La partición de evidencia es la razón de ser de los tres checks:

```
PERSISTENCE_PATH_TRACE   prueba el camino de persistencia gobernado
LOCAL_WRITE_TRACE        prueba una escritura local
CLEANUP_PATH_TRACE       prueba la limpieza de un camino

HUMAN_CONFIRMATION       acompana
CODE_PATH_REVIEW         acompana

REPOSITORY_DEPENDENCY    inerte: una libreria del protocolo no es un archivo guardado
ENVIRONMENT_VARIABLE_NAME inerte: una variable que se llama como el protocolo no es el protocolo
BUCKET_CONFIGURATION     inerte: configurar no es escribir
REMOTE_HTTP_CALL         inerte: hablar con algo remoto no dice con que
UPLOAD_SUCCEEDED         inerte: que la subida devuelva 200 no dice a donde
PATH_NAMING              inerte: como se llama una carpeta no es su ciclo de vida
PERIODIC_CLEANUP_JOB     inerte para la inmediatez
RESTART_POLICY           inerte para la inmediatez
TTL_CONFIGURATION        inerte para la inmediatez
MANUAL_PROCEDURE         inerte para la inmediatez
CONTAINER_ASSUMPTION     inerte: el runtime no es el diseno de la aplicacion
AGENT_STATEMENT          inerte: una opinion con formato de evidencia
```

Y la traza se ata al build: una corrida sobre otro build es una corrida sobre otro sistema. Es la
doctrina que D6 ya fija y acá se reusa entera.

### Un flujo que cumple no tapa otro que no

Un `FAIL` en cualquier flujo gobernado manda sobre cualquier cantidad de flujos que pasen, y manda
**también** sobre un inventario incompleto: un bypass probado es un bypass aunque falte enumerar
flujos. El caso típico del defecto es el mixto —los adjuntos nuevos al storage estándar y los
reportes viejos en el disco del servidor—, y un agregado que promedie lo esconde.

### La clasificación de flujos es evidencia, no aplicabilidad

```
PERSISTENT_STANDARD_STORAGE
PERSISTENT_LOCAL
TEMPORARY_LOCAL
OTHER_REMOTE_STORAGE
NO_STORAGE
UNRESOLVED
```

Seis clases, una por flujo material, con el origen del inventario declarado. No decide si D7 aplica
—eso lo hace la señal—, no cambia el valor de la señal y un flujo `UNRESOLVED` deja la cobertura
incompleta en vez de desaparecer.

### §8.4 entra como evidencia y no inventa un número

Donde la aplicación controla la estructura de claves u objetos se recoge lo medible: estructura
planificada, riesgo de concentración de tráfico, equilibrio de ancho y profundidad, profundidad de
carpetas y objetos por carpeta. Lo que **no** está medido queda `NOT_MEASURED` y no baja el estado:
fabricar un conteo de objetos es peor que no tenerlo.

🔴 Y lo medido que se aparta de una pauta del estándar **no llega a `PASS`**: queda `PARTIAL` con
`STORAGE_STRUCTURE_GUIDANCE_DEVIATION`. Un `PASS` con una profundidad medida de 30 niveles adentro es
un `PASS` que nadie puede leer. No se crea un control nuevo para eso: es el mismo check, con su
evidencia.

### Se reutiliza la infraestructura, no se construye una segunda

`senales.py` resuelve la señal, `matriz.py` la aplicabilidad, `controles.py` el registro y
`registro_agentes.resolver_ruteo` el ruteo. No se agrega ningún módulo de orquestación y no se abre
un segundo inventario de controles.

Lo único compartido que se agrega es `controles/lib/flujos.py`: el vocabulario del inventario de
flujos y la validación de la evidencia, que los tres checks usan igual. Sin él, los tres archivos
repetirían la misma validación tres veces y las tres se irían separando. **No es un control**: no se
declara en el registro, no se evalúa y no tiene estado.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/controles/policies/gcba-standard-storage-required.md` | La policy del storage estándar, con su frontera de proveedor y de protocolo |
| `harnesses/desarrollo/controles/policies/persistent-local-file-storage-prohibited.md` | La policy del local permanente, y su frontera con el temporal |
| `harnesses/desarrollo/controles/policies/temporary-file-immediate-destruction-required.md` | La policy de la destrucción inmediata, sin un número adentro |
| `harnesses/desarrollo/controles/checks/storage-backend-compliance.py` | El check del camino de persistencia gobernado, más la evidencia de §8.4 |
| `harnesses/desarrollo/controles/checks/persistent-local-file-storage.py` | El check de las escrituras locales y su ciclo de vida |
| `harnesses/desarrollo/controles/checks/temporary-file-cleanup.py` | El check de la limpieza atada al ciclo de vida, en éxito y en falla |
| `harnesses/desarrollo/controles/lib/flujos.py` | El inventario de flujos y la partición de evidencia, compartidos |
| `harnesses/desarrollo/reglas/control-registry.json` | Los seis controles de D7, declarados |
| `docs/normativa-7.1.md` | D7, las tres obligaciones, el repositorio que no se sabe y §8.4 |
| `tests/casos/34_d7_almacenamiento_de_archivos.py` | Los escenarios de acá abajo |

La matriz **no se toca**: su fila de D7 ya declara la señal, las tres policies y los tres checks
desde que se construyó.

Y se reescriben tres afirmaciones que hoy están en verde y dejan de ser ciertas: el conteo de
controles declarados en `31_d6/E-30`, en `32_d5/E-36` y en `33_bases/E-32` pasa de **18** a **24**.
Está así a propósito, igual que cuando D5 tocó a D6: quien instala una regla tiene que tocar un test
que pasaba.

## Escenarios verificables

Entre paréntesis, el `D7-nn` del pedido de instalación o la sección que lo pide.

### La señal y la aplicabilidad

- **E-01** — D7 sigue `CONDITIONAL` sobre `fileHandlingPresent`, con `dev-backend` como dueño, sus
  tres policies y sus tres checks, y la fila tiene exactamente las claves que tiene toda fila de
  diseño —ni una agregada—. (D7-01) · rojo visto: si
- **E-02** — La señal en TRUE hace a D7 aplicable. (D7-02) · rojo visto: si
- **E-03** — La señal en FALSE lo deja `NOT_APPLICABLE`, y los tres checks contestan
  `NOT_APPLICABLE`. (D7-03) · rojo visto: si
- **E-04** — Sin la señal, `APPLICABILITY_UNRESOLVED` en la matriz y en los tres checks, con el
  nombre de la señal que falta. (D7-04) · rojo visto: si
- **E-05** — La ausencia nunca es FALSE: una señal que afirma FALSE sin evidencia se degrada a
  UNRESOLVED, una que la matriz no declara se rechaza, y ninguna de las tres frases de ausencia
  —no hay un literal `.pdf`, no hay un componente de subida, no se encontró una llamada al
  filesystem en un archivo— la baja a FALSE **por ninguna de las dos clases débiles**, con los tres
  checks quedando sin resolver. Y el límite queda dicho y probado: la misma frase etiquetada como
  dato estructurado **sí** apaga la regla, porque el harness confía en la etiqueta de la fuente.
  (D7-05) · rojo visto: si
- **E-06** — Un flujo de archivos es más que una subida: las once operaciones declaradas
  —recibir, subir, bajar, generar, transformar, stagear, guardar, servir, importar, exportar y
  procesar temporalmente— sostienen la señal por igual. (§1) · rojo visto: si
- **E-07** — Ninguna otra señal de la matriz sustituye a `fileHandlingPresent`: con cualquiera de
  las otras en TRUE **entregada a los checks**, los tres quedan `APPLICABILITY_UNRESOLVED` con
  `SIGNAL_IDENTITY_MISMATCH` y siguen pidiendo la suya; y el mapa `{id: resuelta}` con el que la
  unidad de trabajo transporta sus señales se lee por id. (§1) · rojo visto: si

### Las tres obligaciones, y los seis ids

- **E-08** — D7 resuelve exactamente tres policies. (D7-06) · rojo visto: si
- **E-09** — D7 resuelve exactamente tres checks. (D7-07) · rojo visto: si
- **E-10** — Los seis ids son exactamente los que la matriz instalada declara, con su tipo y su
  regla, y ninguno se renombró. (D7-08) · rojo visto: si
- **E-11** — D7 no crea ninguna referencia a skill: la fila de la matriz no declara `skills`,
  ninguno de los siete archivos de D7 declara una, y siguen siendo 27 las instaladas. (D7-09)
  · rojo visto: si
- **E-12** — Las tres obligaciones se evalúan independientemente: para el mismo caso, romper una
  no cambia el estado de las otras dos, en los seis cruces. (§2, D7-29) · rojo visto: si

### El storage estándar, que no se inventa

- **E-13** — Un flujo persistente con la identidad del storage estándar declarada con su fuente, su
  contrato y traza del camino de persistencia da `PASS`. (D7-10) · rojo visto: si
- **E-14** — Ninguna de las seis clases inertes, sola, da `PASS`: una librería del protocolo, el
  nombre de una variable de ambiente, una configuración de bucket, una llamada HTTP remota, una
  subida exitosa y la palabra de un agente. (D7-11) · rojo visto: si
- **E-15** — Un flujo persistente clasificado `OTHER_REMOTE_STORAGE` no satisface el storage
  estándar en silencio: `FAIL`. (D7-12) · rojo visto: si
- **E-16** — Sin identidad del storage estándar —o sin fuente de la lista, o sin referencia, o con
  cualquiera de las tres en blancos—, `STANDARD_STORAGE_PROVIDER_UNRESOLVED`. (D7-13)
  · rojo visto: si
- **E-17** — Con identidad y sin contrato de integración, `STORAGE_INTEGRATION_CONTRACT_MISSING`, y
  son dos estados distintos porque son dos huecos distintos. (D7-14) · rojo visto: si
- **E-18** — Un cliente del storage estándar declarado mientras el camino gobernado lo esquiva da
  `FAIL`, lo diga el flujo o lo diga sólo su traza. (§7) · rojo visto: si
- **E-19** — Ninguno de los artefactos de D7 —las tres policies, los tres checks, el módulo
  compartido, las seis filas del registro, la fila de la matriz y la sección de
  `docs/normativa-7.1.md`— lleva un localizador de red, un nombre de infraestructura, una
  credencial, un mecanismo declarado, un especificador de paquete, el nombre de un proveedor de
  almacenamiento ni una duración; y tampoco los lleva ningún resultado que los checks produzcan.
  (§3, D7-30, D7-32) · rojo visto: si

### El local permanente

- **E-20** — Almacenamiento local permanente de archivos de la aplicación da `FAIL`. (D7-15)
  · rojo visto: si
- **E-21** — Un path que se llama `tmp` con ciclo de vida desconocido queda
  `LOCAL_STORAGE_LIFECYCLE_UNRESOLVED`, y una escritura cuya única evidencia es el nombre del path
  o el runtime tampoco se resuelve. (D7-16) · rojo visto: si
- **E-22** — Un temporal local con su ciclo de vida establecido no se trata como persistente por
  ser local: `persistent-local-file-storage` no lo hace fallar y lo deriva a
  `temporary-file-cleanup`. (D7-17) · rojo visto: si
- **E-23** — Un volumen montado usado como repositorio permanente de la aplicación no esquiva la
  prohibición: `FAIL`. (D7-18) · rojo visto: si
- **E-24** — Para cada escritura local se establecen las siete cosas, y si falta cualquiera de las
  siete el flujo queda `LOCAL_STORAGE_LIFECYCLE_UNRESOLVED`; con todas sin establecer el resultado
  es ése, y con una establecida y otra no es `PARTIAL`. (§8) · rojo visto: si

### La destrucción inmediata

- **E-25** — Un temporal con limpieza atada al ciclo de vida en el camino normal se evalúa y no
  desaparece. (D7-19) · rojo visto: si
- **E-26** — Limpieza sólo en el camino feliz, con los caminos de falla sin declarar, no llega a
  `PASS`: `CLEANUP_PATH_COVERAGE_UNRESOLVED`. (D7-20) · rojo visto: si
- **E-27** — Un cron periódico como única limpieza de un camino material da `FAIL`. (D7-21)
  · rojo visto: si
- **E-28** — El reinicio del contenedor como única limpieza da `FAIL`. (D7-22)
  · rojo visto: si
- **E-29** — Un TTL sin especificar como única limpieza da `FAIL`, y lo mismo el arranque y un
  procedimiento manual. (D7-23) · rojo visto: si
- **E-30** — Cobertura completa de éxito y falla, con traza, da `PASS`; una limpieza demorada **al
  lado** de una atada al ciclo de vida no lo rompe; y la técnica no se exige: seis técnicas
  distintas y ninguna declarada dan el mismo resultado. (D7-25, §9) · rojo visto: si
- **E-31** — "Inmediato" no se define con un número: ningún artefacto de D7 declara una duración,
  el check no tiene un umbral y la única forma de aprobar es la atadura estructural. (D7-24)
  · rojo visto: si

### La cobertura de flujos

- **E-32** — Inventario incompleto —sin flujos, sin fuente, con flujos sin id, sin clasificación,
  con una clasificación `UNRESOLVED` o declarado incompleto— deja
  `FILE_FLOW_COVERAGE_UNRESOLVED`, en los tres checks. (D7-26) · rojo visto: si
- **E-33** — Sin flujos temporales tras una clasificación completa, `temporary-file-cleanup` queda
  `NOT_APPLICABLE`. (D7-27) · rojo visto: si
- **E-34** — Un flujo sólo temporal no hace fallar a `storage-backend-compliance` por no persistir:
  queda `NOT_APPLICABLE` y **no** pide la identidad del storage estándar. (D7-28)
  · rojo visto: si
- **E-35** — Flujos persistentes y temporales en la misma aplicación se evalúan independientemente:
  el resultado de cada check nombra sólo los flujos de su clase. (D7-29) · rojo visto: si
- **E-36** — La clasificación de flujos no es un segundo sistema de aplicabilidad: con la clase
  **entrando en la señal**, para las seis clases la aplicabilidad de D7 y el valor de la señal no
  cambian. (§6) · rojo visto: si
- **E-37** — Un `FAIL` probado manda sobre un inventario incompleto, y un flujo que cumple no tapa
  otro que no. (§7) · rojo visto: si

### §8.4, citado y no inventado

- **E-38** — El protocolo S3 es evidencia de protocolo y no de un proveedor: declararlo no resuelve
  la identidad, y ningún artefacto atribuye un proveedor a la regla. (D7-30)
  · rojo visto: si
- **E-39** — Una profundidad medida mayor a 20 niveles, y una concentración medida mayor a 100.000
  objetos en una carpeta, se exponen en la evidencia del check y no lo dejan en `PASS`. (D7-31)
  · rojo visto: si
- **E-40** — Sin evidencia, los hechos de §8.4 quedan `NOT_MEASURED`, no se inventan y no bajan el
  estado. (D7-32) · rojo visto: si

### La propagación, el registro y la trazabilidad

- **E-41** — La unidad de trabajo propaga la señal resuelta, las tres policies y los tres checks, y
  la forma vieja —booleanos— sigue funcionando. (D7-33) · rojo visto: si
- **E-42** — Después de instalar, los seis controles dejan de figurar como no instalados, son
  veinticuatro los declarados y no queda ningún archivo de control sin declarar. (D7-34)
  · rojo visto: si
- **E-43** — Todo resultado de los tres checks conserva `ES0901 / 6.3 / 7.1 / D7`, en todos sus
  caminos. (D7-35) · rojo visto: si
- **E-44** — Los estados exigidos existen en cada check, el único que aprueba es `PASS`, y ningún
  estado sin resolver se convierte en `PASS`. (§14) · rojo visto: si
- **E-45** — La ejecución rutea por el registro de agentes: `dev-backend` con `dev-storage` resuelve
  `ROUTABLE` sin que este cambio cree ni modifique una skill. (§11) · rojo visto: si

## Cómo se verifica

Los 45 pasan por `.\tests\Invoke-Tests.ps1`. Ninguno lleva la marca `· verificación: lectura`: todo
lo que este cambio construye es determinista.

E-19 tiene **tres** mitades, como el guard de D6: la primera afirma que los diez textos están
limpios; la segunda inyecta las formas de fuga **en crudo** —sin acomodarlas al patrón— y afirma que
el barrido las encuentra; y la tercera afirma que los textos legítimos, incluidos `S3`, *20 niveles*
y *100.000 objetos*, **no** lo disparan. Sin la segunda, la primera se degrada en silencio el día
que alguien afloje un patrón. Sin la tercera, el barrido se pone en rojo con las dos citas del
estándar y alguien lo apaga.

📌 E-05 y E-07 son los dos escenarios que el primer veredicto contradijo, y por la misma razón: su
test elegía la entrada en la que el sistema no podía fallar —la clase débil en E-05, `None` en E-07,
que era la entrada idéntica a la de E-04—. E-07 se arregló en el **código**, porque la afirmación era
cierta y el mecanismo no estaba; E-05 se arregló en la **spec**, porque la afirmación era más ancha
que el mecanismo y el hueco que queda es uno que este repositorio ya tiene anotado.

E-07, E-12, E-24, E-30, E-32, E-36, E-43 y E-44 son **invariantes sobre un producto**, no ejemplos
elegidos: recorren todas las señales de la matriz, los seis cruces de obligaciones, los siete campos
del ciclo de vida, las técnicas, las seis formas de inventario incompleto, las seis clases de flujo
y todos los caminos de cada check. Donde la cobertura es combinatoria, el ejemplo elegido a mano es
el que deja pasar la forma que nadie pensó.

## Riesgos conocidos

- **La identidad del storage estándar no se puede resolver en ningún proyecto todavía.** El
  repositorio no está en ningún extracto ni en el catálogo del Anexo II —el estándar nombra el
  protocolo y se detiene ahí—. En cualquier corrida real de hoy, `storage-backend-compliance` de una
  aplicación que persiste va a salir `STANDARD_STORAGE_PROVIDER_UNRESOLVED`, que es lo correcto y
  también significa que ese camino no se va a ejercitar de punta a punta hasta que alguien consiga
  ese dato.
- **El harness confía en la etiqueta de la fuente.** Un FALSE de `fileHandlingPresent` apaga D7
  entera. Una observación de ausencia —*no hay ningún literal `.pdf`*— no lo sostiene cuando entra
  como la palabra de un agente o como una dependencia declarada, porque las dos clases son débiles;
  pero la misma frase etiquetada `TASK_CONTEXT` o `PROJECT_DOCUMENTATION` **sí** lo sostiene, y
  `senales.py` no tiene cómo distinguir una observación de ausencia de un alcance declarado
  completo. Queda citada y es refutable, y es una afirmación de quien la etiqueta. Cerrarlo pide
  exigir completitud de alcance declarada para todo FALSE, que hoy está cerrado **sólo para D5** y
  sigue abierto para las otras quince reglas condicionales. Está dicho en `docs/normativa-7.1.md`
  y E-05 lo prueba en las dos direcciones.
- **No hay eje `REAL`/`MOCKED`.** Una traza mockeada de un camino de persistencia se ve igual que
  una real. D6 distingue las dos; acá no, porque el pedido no lo pide. Un caso que declare trazas
  mockeadas como reales pasa, y eso es una afirmación de quien las declara.
- **La evidencia la junta nadie todavía.** Los tres checks reciben un inventario de flujos ya
  clasificado, y hoy no hay ningún productor que lo arme desde un repositorio. Es la misma deuda
  que arrastran G1, G2, D1 a D6, y lo que la destraba es el análisis de impacto.
- **`controles/` no llega a un proyecto instalado.** Con D7 son veinticuatro controles que declaran
  `INSTALLED` y que fuera de este repositorio serían `CONTROL_FILE_MISSING`. Este cambio no lo
  arregla y empeora la cuenta en seis.
- **`controles/lib/` es un directorio nuevo.** `controles.descubrir_no_declarados` sólo mira
  `controles/policies` y `controles/checks`, así que `flujos.py` no se reporta como archivo de
  control sin declarar — que es lo correcto, porque no es un control. Pero es una carpeta que
  ningún inventario mira, y el día que alguien guarde ahí algo que sí debería declararse, nadie se
  va a enterar.
- **Que los archivos vayan de verdad al storage estándar lo dice una corrida real.** Lo que estos
  checks verifican es que la evidencia de esa corrida exista, esté atada al build y no sea de una
  clase inerte.
