# Integridad de repositorio y revisión de incidentes de seguridad

**Estado:** construido y testeado · **Fecha:** 22-09-2026 · **Capacidad transversal, no una regla**

## Qué problema resuelve

Cuando alguien sospecha que un repositorio fue comprometido —un commit que nadie reconoce, una
dependencia que cambió de origen, un pipeline que empezó a subir cosas afuera, una credencial que
apareció en el diff— el harness hoy no tiene nada que decir. Y lo peor: **su comportamiento por
defecto es destruir la evidencia**. Un harness que arregla, borra, rota y actualiza automáticamente
es exactamente lo que no se quiere corriendo adentro de una escena que todavía no se investigó.

Esta capacidad instala tres cosas que hoy no existen:

```
un MODO de incidente que cambia los defaults a preservar en vez de arreglar
una LINEA DE BASE confiable contra la cual comparar, que no es "la rama actual"
una separacion entre INVESTIGAR y REMEDIAR, que hoy son el mismo paso implicito
```

Y hay cuatro trampas propias de este terreno.

**La primera: el harness borra la escena.** La forma natural de un asistente es arreglar lo que
encuentra. En un incidente, arreglar es destruir: el commit revertido, el archivo sospechoso
borrado, la credencial rotada y el `force-push` se llevan puesta la única evidencia de qué pasó.

**La segunda: la rama actual no es confiable.** Comparar contra `main` cuando el problema puede ser
que alguien escribió en `main` es comparar el repositorio consigo mismo. La línea de base tiene que
tener **procedencia**, y si no la tiene hay que decirlo en vez de elegir la más cómoda.

**La tercera: un indicador débil no es malware.** `eval`, `exec`, una cadena en Base64, un comando de
shell, un dominio nuevo, una dependencia nueva. Los seis aparecen todos los días en código
legítimo, y un harness que los llame *malicioso* se vuelve ruido que nadie mira — o peor, acusa a
una persona. Lo que el harness reporta es **evidencia y confianza**, nunca intención.

**La cuarta: confianza no es severidad.** *"Estoy muy seguro de que esto pasó"* y *"esto es muy
grave"* son dos ejes, y mezclarlos produce las dos formas del error: lo grave con poca evidencia
tratado como certeza, y lo cierto pero menor tratado como crisis. El harness ya tiene una escala de
riesgo autoritativa —la de ES0902, con su mapeo firmado— y esta capacidad **no inventa una segunda**.

## Qué queda afuera

- **Una regla normativa.** Esto es una **capacidad transversal**, como el Bloque 4 y la gestión de
  ambientes de base de datos: no tiene señal de aplicabilidad, no entra en la matriz de ES0901 ni en
  la de ES0902, y no se declara en `control-registry.json`. Puede **producir evidencia** para reglas
  de seguridad; no es una de ellas, y un `PASS` suyo no es una aprobación de ES0902.
- **Un agente nuevo.** Los dueños son `dev-security` y sus skills ya instaladas
  —`dev-security-assessment`, `dev-appsec-review`, `dev-vulnerability-management`— que el registro
  de agentes ya rutea. No se crea, no se modifica y no se renombra ninguno.
- **Una skill nueva.** Ni siquiera una de análisis de incidentes. Si algún día una capacidad real
  demuestra que las instaladas no alcanzan, eso se rutea con el estado que ya existe
  —`SPECIALIZED_SKILL_GAP`— y se decide aparte.
- **Una segunda escala de severidad.** La autoritativa es la de ES0902: `evaluacion` mapea las
  severidades del escáner a las categorías de riesgo del estándar, y **sólo con el mapeo declarado
  autoritativo y con evidencia**. Sin ese mapeo, `SECURITY_SEVERITY_UNRESOLVED`. Esta capacidad no
  declara ningún valor de severidad propio.
- **Ejecutar código sospechoso.** El análisis por defecto es **estático**: diff, metadata,
  manifiestos, configuración. Lo dinámico exige ambiente aislado, autorización explícita, política
  de contención de red, preservación de evidencia y la compuerta de riesgo de tools que ya existe.
  Sin ambiente aislado, `DYNAMIC_ANALYSIS_ENVIRONMENT_UNAVAILABLE`.
- **Remediar.** La investigación es de sólo lectura. Una remediación aprobada es **otra unidad de
  trabajo**, enlazada a los hallazgos del incidente, y el registro original no se borra.
- **Detectar secretos de verdad.** Lo que esta capacidad hace con un secreto potencial es
  **redactarlo, huellarlo y ubicarlo**. Quién lo detecta —un escáner, una persona— es otro cambio;
  lo que acá se garantiza es que el valor en claro no llega a un hallazgo, a un log, a la
  contabilidad del Bloque 4 ni a un reporte.
- **Adaptadores reales de GitLab y GitHub.** Se define el contrato de evidencia normalizada y se
  construyen los dos adaptadores como **traducción de forma**, no como clientes de API. Conectarse
  de verdad es del Bloque 1, que ya existe.

## Las decisiones, y por qué

### El modo cambia los defaults, no agrega una opción

```
NORMAL                el flujo de siempre
SECURITY_ASSESSMENT   analisis de seguridad interno y preparacion de evidencia de ES0902
SECURITY_INCIDENT     se sospecha compromiso: los defaults se invierten
```

En `SECURITY_INCIDENT` **ninguna** de estas seis corre automáticamente:

```
remediacion de codigo        borrado de archivos        rotacion de credenciales
actualizacion de dependencias   reescritura de historia    limpieza de artefactos sospechosos
```

🔴 **Recomendar sigue permitido, y es lo único que queda permitido.** Una recomendación es un dato
con su motivo; ejecutarla exige autorización explícita y la compuerta de riesgo que ya existe. La
diferencia entre las dos cosas es toda la capacidad: un harness que recomienda revertir un commit es
útil, y uno que lo revierte solo destruyó la evidencia de qué se revirtió.

### La línea de base tiene procedencia, y `HEAD` no es procedencia

```
APPROVED_RELEASE            DEPLOYED_RELEASE           SECURITY_APPROVED_RELEASE
HUMAN_CONFIRMED             OTHER_AUTHORITATIVE
```

Hacen falta las cinco cosas del contrato —repositorio, ref, commit, fuente de la lista y evidencia—
y sin alguna: `TRUSTED_BASELINE_UNRESOLVED`. El análisis puede seguir en modo degradado, y la
limitación viaja en el resultado.

🔴 **La rama por defecto no es confiable por ser la actual.** `main`, `master`, `HEAD~1`, el último
tag y *"el commit anterior al reporte"* no son fuentes: son ubicaciones. Este módulo **no tiene** una
noción de rama confiable adentro, y por eso no puede elegirla por comodidad.

🔴 **`HUMAN_CONFIRMED` exige quién.** Una confirmación humana sin la persona que la firmó es una
afirmación sin dueño, y es justo la fuente que más fácil se escribe sola.

Y la línea de base es **evidencia inmutable de esa revisión**: cambiarla no actualiza la revisión,
**crea otra**. El id del contexto se deriva del repositorio, del commit y de la fuente, así que dos
líneas de base distintas no pueden compartir contexto ni por accidente.

### El inventario de cambios es determinista, o no sirve

La misma línea de base y la misma evidencia del repositorio tienen que producir **el mismo
inventario**, siempre. Sin eso, dos corridas de la misma investigación se contradicen y ninguna de
las dos se puede citar.

```
COMMITS              FILES_ADDED         FILES_MODIFIED      FILES_DELETED
DEPENDENCY_CHANGES   LOCKFILE_CHANGES    CICD_CHANGES        BUILD_CHANGES
AUTH_CHANGES         NETWORK_DESTINATIONS                    BINARY_ARTIFACTS
```

Once clases, todas ordenadas, ninguna derivada de un conjunto sin orden y ninguna con una marca de
tiempo de *ahora*. El orden de entrada no cambia la salida.

🔴 **La clase de un archivo la declara la evidencia normalizada, no la deduce el módulo del nombre
del archivo.** Deducir que algo es un pipeline porque está en una carpeta que se llama así es la
misma trampa que `tmp` en un path: funciona hasta el repositorio donde no. Un archivo cambiado sin
clase declarada queda `UNCLASSIFIED_CHANGE` y deja la revisión en `REVIEW_INCOMPLETE`.

### Las categorías son señales, y la confirmación exige evidencia directa

Las veintiuna categorías del documento entran como están. Y arriba de ellas, la regla que hace que
esto sirva:

```
indicador debil solo        ->  confianza LOW, SUSPICIOUS_BEHAVIOR_DETECTED. Nunca confirmado
varios indicadores          ->  la confianza sube, y el estado NO
evidencia DIRECTA declarada ->  recien ahi puede haber MALICIOUS_BEHAVIOR_CONFIRMED_BY_EVIDENCE
```

Los seis débiles están nombrados —`eval`, `exec`, Base64, un comando de shell, un dominio nuevo, una
dependencia nueva— y ninguno, solo ni acumulado con los otros cinco, llega a confirmado. Lo que
habilita la confirmación es `directEvidence`, que es una declaración con su evidencia citada, más
confianza alta.

🔴 **El harness no reporta intención.** No dice *quién* ni *para qué*: dice qué cambió, con qué
evidencia y con cuánta confianza. La metadata de identidad es evidencia, no prueba, y esta capacidad
no declara a un autor malicioso por su nombre ni por la hora en la que hizo un commit.

### Confianza y severidad son dos ejes, y sólo uno es del harness

```
confianza   LOW / MEDIUM / HIGH   cuanto sostiene la evidencia
severidad   la de ES0902          cuanto pesa, y la firma el mapeo autoritativo
```

La severidad sale de `evaluacion`, con la **misma** compuerta que usa el umbral de G2: el mapeo tiene
que declararse autoritativo y traer evidencia. Sin eso, `SECURITY_SEVERITY_UNRESOLVED`, que es la
forma local del estado que ES0902 ya tiene.

🔴 Y no se derivan una de la otra en ninguna dirección. Es verificable como producto: para las tres
confianzas y todas las categorías del mapeo, la severidad no cambia cuando cambia la confianza, y al
revés.

### El hecho viaja al hallazgo, o la categoría sola no alcanza

Los indicadores entran al hallazgo, y los hechos sensibles se separan por su vocabulario:

```
indicators         todo lo que la senal declaro
pipelineFacts      los que son hechos sensibles del pipeline
supplyChainFacts   los de la cadena de suministro
weakIndicators     los seis que no prueban nada
```

🔴 Sin esto, las dos listas de hechos serían **declaraciones muertas** —nada las leería— y un acceso
nuevo a un secreto en el pipeline saldría con su categoría y sin el hecho que lo originó, que es
justamente lo que quien remedia necesita para saber **dónde** mirar.

### El secreto no entra en claro a ningún lado

```
se redacta      el valor nunca viaja
se huella       un hash, para poder correlacionar sin exponer
se ubica        archivo y posicion, que es lo que sirve para arreglarlo
```

Y el alcance de la prohibición es todo lo que sale: el hallazgo, el reporte, los avisos y **la
contabilidad del Bloque 4**, que puede medir tiempo, tokens y costo del análisis y no puede guardar
ni un secreto, ni un payload sospechoso entero, ni el cuerpo de un script.

### Investigar y remediar no son el mismo paso

La investigación es de sólo lectura y preserva. La remediación aprobada es **otra unidad de trabajo**
que conserva el enlace a los hallazgos que la originaron, y el registro del incidente **no se
borra** cuando la remediación termina. Mutar y averiguar en el mismo paso implícito es cómo se
pierde la respuesta a *"qué había antes"*.

### El núcleo no sabe de proveedores

El contrato de evidencia normalizada es provider-independiente y los adaptadores traducen. Un campo
propio de GitLab o de GitHub **no llega al hallazgo**: si llegara, el día que entre el tercer
proveedor habría que tocar el núcleo, y el núcleo es lo que decide si algo es sospechoso.

### La compuerta humana es el default, no la excepción

`HUMAN_SECURITY_REVIEW_REQUIRED` en las siete: comportamiento confirmado, sospecha de confianza alta,
propuesta de remediación, rotación de credenciales, ejecución dinámica, línea de base en disputa y
evidencia contradictoria.

### Se reutiliza lo que ya está, y no se construye un segundo de nada

`evaluacion` para la severidad, `tools` para la compuerta de riesgo, `registro_agentes` para el
ruteo, `consumo` para la contabilidad. Un módulo nuevo —`integridad.py`— y dos schemas; ni un
registro paralelo, ni una escala nueva, ni un agente.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/bin/orquestacion/integridad.py` | La capacidad entera: modos, línea de base, inventario, señales, hallazgos, compuertas y adaptadores |
| `comun/schemas/repository-integrity-finding.schema.json` | El contrato de un hallazgo |
| `comun/schemas/trusted-repository-baseline.schema.json` | El contrato de una línea de base confiable |
| `docs/seguridad-de-repositorio.md` | Qué es un incidente para el harness, y por qué preservar va antes que arreglar |
| `tests/casos/38_integridad_de_repositorio.py` | Los escenarios de acá abajo |

**No se toca** la matriz de ES0901, la de ES0902, `control-registry.json`, el registro de agentes ni
ninguna skill.

## Escenarios verificables

Entre paréntesis, el `RI-nn` del pedido. Los cincuenta están cubiertos.

### La frontera: ni regla, ni agente, ni skill

- **E-01** — La capacidad no está en la matriz de ES0902 ni en la de ES0901, y no se declara en el
  registro de controles. (RI-01) · rojo visto: si
- **E-02** — No se crea ningún agente: el registro sigue con los que tenía y el módulo no declara
  uno nuevo. (RI-02) · rojo visto: si
- **E-03** — `dev-security` y sus tres skills de seguridad siguen siendo las autoritativas y
  rutean; siguen siendo 27 las skills instaladas. (RI-03) · rojo visto: si
- **E-04** — Un `PASS` de la revisión no implica aprobación de ES0902: el resultado no lleva ningún
  estado oficial, y el que `evaluacion` resuelve —capturado **antes** de la revisión— no cambia.
  (RI-47) · rojo visto: si

### El modo de incidente

- **E-05** — Los tres modos existen y `SECURITY_INCIDENT` desactiva las seis acciones automáticas.
  (RI-04) · rojo visto: si
- **E-06** — En incidente, la evidencia se preserva **antes** de cualquier mutación: para **las
  seis** acciones, sin instantánea sellada no se autoriza ninguna, y una instantánea adulterada
  tampoco. (RI-05) · rojo visto: si
- **E-07** — La rotación de credenciales no se ejecuta automáticamente. (RI-41)
  · rojo visto: si
- **E-08** — El borrado de un archivo sospechoso no se ejecuta automáticamente. (RI-42)
  · rojo visto: si
- **E-09** — El `force-push` y la reescritura de historia no se ejecutan automáticamente. (RI-43)
  · rojo visto: si
- **E-10** — Recomendar sigue permitido en incidente, y una recomendación nunca queda ejecutada.
  (§3) · rojo visto: si

### La línea de base

- **E-11** — La rama por defecto no es confiable por ser la actual: `main` sin fuente ni evidencia
  no resuelve, y el módulo no nombra ninguna rama adentro. (RI-06) · rojo visto: si
- **E-12** — Sin línea de base, `TRUSTED_BASELINE_UNRESOLVED`, en las cinco formas del hueco.
  (RI-07) · rojo visto: si
- **E-13** — Una línea de base confirmada por una persona exige evidencia **y quién la firmó**.
  (RI-08) · rojo visto: si
- **E-14** — Cambiar la línea de base crea otro contexto de revisión: el id cambia, y dos bases
  distintas no comparten contexto. (RI-09) · rojo visto: si
- **E-15** — Las cinco fuentes declaradas sirven, y ninguna otra. (§4) · rojo visto: si

### El inventario de cambios

- **E-16** — El inventario enumera los archivos agregados, modificados y borrados. (RI-10)
  · rojo visto: si
- **E-17** — Conserva la identidad de los commits, con sus padres. (RI-11)
  · rojo visto: si
- **E-18** — Conserva los hashes de archivo cuando la evidencia los trae. (RI-12)
  · rojo visto: si
- **E-19** — Incluye los cambios de manifiesto de dependencias. (RI-13) · rojo visto: si
- **E-20** — Incluye los cambios de lockfile. (RI-14) · rojo visto: si
- **E-21** — Incluye los cambios de CI/CD. (RI-15) · rojo visto: si
- **E-22** — Incluye los cambios de contenedor y de build. (RI-16) · rojo visto: si
- **E-23** — Incluye los cambios sensibles de autenticación y autorización. (RI-17)
  · rojo visto: si
- **E-24** — Los artefactos binarios inesperados se exponen con su hash y su ruta. (RI-18)
  · rojo visto: si
- **E-25** — La misma línea de base y la misma evidencia producen el mismo inventario, y el orden
  de entrada no lo cambia. (RI-50) · rojo visto: si
- **E-26** — Un archivo cambiado sin clase declarada no se adivina: queda sin clasificar y deja la
  revisión incompleta. (§6) · rojo visto: si

### Las señales y la confirmación

- **E-27** — `eval` y `exec`, solos, no producen un veredicto de malicioso confirmado. (RI-19)
  · rojo visto: si
- **E-28** — Base64 y la ofuscación, solos, tampoco. (RI-20) · rojo visto: si
- **E-29** — Un dominio externo nuevo, solo, no produce un veredicto de exfiltración confirmada.
  (RI-21) · rojo visto: si
- **E-30** — Los seis indicadores débiles, **todos juntos**, siguen sin llegar a confirmado: es un
  invariante sobre el producto, no seis ejemplos. (RI-19, RI-20, RI-21)
  · rojo visto: si
- **E-31** — Una señal sospechosa produce evidencia y confianza; las veintiuna categorías están
  nombradas una por una; y el hallazgo lleva **exactamente** las claves de su contrato, así que una
  señal no se copia en crudo adentro de un campo inventado. (RI-22) · rojo visto: si
- **E-32** — El veredicto confirmado exige evidencia directa declarada y confianza alta. (RI-23)
  · rojo visto: si

### La confianza y la severidad

- **E-33** — La confianza de un hallazgo es un campo distinto de la severidad, y ninguno se deriva
  del otro: para las tres confianzas y todas las categorías del mapeo, cambiar una no mueve a la
  otra. (RI-24) · rojo visto: si
- **E-34** — No se inventa una segunda escala: la severidad sale del mapeo autoritativo de ES0902 y
  el módulo no declara ningún valor de severidad propio. (RI-25) · rojo visto: si
- **E-35** — Sin mapeo autoritativo, o con una severidad que el mapeo no cubre,
  `SECURITY_SEVERITY_UNRESOLVED`. (RI-26) · rojo visto: si

### Los secretos

- **E-36** — El valor en claro de un secreto no se copia a un hallazgo, en ninguno de sus campos.
  (RI-27) · rojo visto: si
- **E-37** — La evidencia de un secreto se redacta y se huella, y conserva su ubicación. (RI-28)
  · rojo visto: si
- **E-38** — La contabilidad del Bloque 4 mide el análisis y no guarda secretos, payloads ni cuerpos
  de script. (RI-46) · rojo visto: si

### El pipeline y la cadena de suministro

- **E-39** — Un acceso nuevo a un secreto en el pipeline se expone. (RI-29)
  · rojo visto: si
- **E-40** — La desactivación de un control de seguridad en el pipeline se expone. (RI-30)
  · rojo visto: si
- **E-41** — Los once hechos sensibles del pipeline, nombrados uno por uno, **se exponen en el
  hallazgo** —en `indicators` y en `pipelineFacts`, sin confundirse con los de cadena ni con los
  débiles—. (RI-31) · rojo visto: si
- **E-42** — La sustitución del origen o del registro de un paquete se expone. (RI-32)
  · rojo visto: si
- **E-43** — Los cambios de hooks de instalación se exponen. (RI-33) · rojo visto: si

### El análisis dinámico

- **E-44** — Un binario sospechoso no se ejecuta automáticamente. (RI-34)
  · rojo visto: si
- **E-45** — El análisis dinámico exige ambiente aislado, autorización, contención de red y
  preservación. (RI-35) · rojo visto: si
- **E-46** — Sin ambiente aislado, `DYNAMIC_ANALYSIS_ENVIRONMENT_UNAVAILABLE`. (RI-36)
  · rojo visto: si
- **E-47** — El análisis dinámico pasa por la compuerta de riesgo de tools que ya existe, y no por
  una propia. (RI-37) · rojo visto: si
- **E-48** — Una tool que ejecuta código sospechoso en el host no puede nacer de bajo riesgo ni por
  defecto. (RI-38) · rojo visto: si

### La compuerta humana, la remediación y los proveedores

- **E-49** — Un hallazgo confirmado o de confianza alta exige revisión humana, y también la
  proponen las otras cinco causas. (RI-39, RI-40) · rojo visto: si
- **E-50** — La remediación es otra unidad, conserva el enlace a los hallazgos, y la evidencia
  original del incidente no cambia después. (RI-48, RI-49) · rojo visto: si
- **E-51** — La evidencia de GitLab y la de GitHub normalizan a la misma forma, y ningún campo
  propio del proveedor llega a ningún nivel de la salida ni **al hallazgo** construido desde esa
  evidencia: el barrido de claves es recursivo, no de primer nivel. (RI-44, RI-45)
  · rojo visto: si

## Cómo se verifica

Los 51 pasan por `.\tests\Invoke-Tests.ps1`. Ninguno lleva la marca `· verificación: lectura`: todo
lo que este cambio construye es determinista.

E-30, E-33, E-25 y E-15 son **invariantes sobre un producto**: los seis indicadores débiles en todas
sus combinaciones, las tres confianzas por todas las categorías del mapeo, el inventario contra el
orden de entrada, y las cinco fuentes de línea de base contra cualquier otra. Donde la cobertura es
combinatoria, el ejemplo elegido a mano es el que deja pasar la forma que nadie pensó.

📌 El primer veredicto dejó cuatro escenarios **sin sustento** —E-04, E-06, E-41 y E-51— y ninguno
contradicho. Los cuatro están cerrados, y **uno de ellos era del módulo y no del test**: E-41 destapó
que `HECHOS_DE_PIPELINE` y `HECHOS_DE_CADENA` no las leía ninguna función y que el hallazgo no
llevaba los indicadores, así que el hecho no se exponía en ningún campo. Los otros tres eran huecos
de verificación:

```
E-04  una tautologia: `antes` se capturaba DESPUES de la revision
E-06  un muestreo de 1 de 6: cinco acciones podian saltarse la preservacion
E-51  un barrido de claves de PRIMER NIVEL: un campo del proveedor adentro de cada archivo pasaba
```

🔴 Las constantes que un escenario verifica van **clavadas por literal** en el test, no recorridas
desde el módulo — la lección de D8 y P1. Y las aserciones por ausencia —que un secreto no esté, que
un campo de proveedor no llegue— se barren sobre **todo lo que sale**, no sobre una muestra: es la
lección de D8/E-34.

## Riesgos conocidos

- **Esta capacidad no detecta nada por sí sola.** Recibe evidencia normalizada y la clasifica. Quién
  produce esa evidencia —un adaptador real contra la API de GitLab o de GitHub, un escáner de
  secretos, un analizador de dependencias— es el Bloque 1 y es otro cambio. Hoy, en una corrida
  real, esto contesta sobre lo que alguien le pasa.
- **La clase de un archivo la declara el adaptador.** Un adaptador que clasifique mal un pipeline
  como código fuente saca ese archivo de la revisión sensible. El módulo exige que la clase esté
  declarada y deja sin clasificar lo que no lo está; que la clasificación sea correcta no lo puede
  saber.
- **`directEvidence` es una declaración.** Lo que habilita el veredicto confirmado es un campo que
  alguien pone en `True` con su evidencia citada. El módulo exige la cita y la confianza alta; que
  la evidencia realmente pruebe lo que dice lo decide una persona, y por eso el mismo camino exige
  revisión humana.
- **La redacción cubre lo que se le declara secreto.** Si un valor sensible entra al hallazgo por un
  campo que nadie marcó, la redacción no lo ve. Lo que el invariante garantiza es que un valor
  declarado como secreto no aparece en ninguna parte de la salida.
- **El modo no lo fija nadie todavía.** `SECURITY_INCIDENT` se pasa como dato. Quién lo enciende
  —una persona, el orquestador del Bloque 3 al recibir un reporte— es otro cambio, y hasta que
  exista alguien tiene que acordarse de encenderlo.
- **Los adaptadores son traducción de forma, no clientes.** Prueban que el núcleo no depende del
  proveedor; no prueban que la evidencia que un proveedor real entrega sea la que el adaptador
  espera.
