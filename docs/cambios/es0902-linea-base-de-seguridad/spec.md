# ES0902 v6.2 — la línea base de seguridad como estándar propio

**Estado:** verificado y cerrado · **Fecha:** 22-09-2026 · **Estándar:** ES0902 v6.2, 2025-08

## Qué problema resuelve

El harness sabe resolver un estándar: ES0901 §7.1, 24 filas, con sus señales, sus policies, sus
checks, sus reviews y su registro de controles. Todo el runtime normativo está escrito alrededor
de ese archivo, y en varios lugares **alrededor de que haya uno solo**:

```
matriz.py            ARCHIVO = "es0901-7.1-normative-matrix.json"   una constante de módulo
senales.declaradas   el inventario de señales sale de esa matriz     y de ningún lado más
control-registry     "source": {standard, version, section, rule}    un control, una fuente
                     "rule": pattern ^[GDPCM][0-9]+$                 Vu1, Ve1 y O1 no entran
normativa.resolucion devuelve UN bloque normativo                    sin lugar para el segundo
```

ES0902 v6.2 es un estándar distinto, de la misma autoridad, con 21 reglas propias, que se aplica a
las mismas unidades de trabajo. Hoy no hay manera de instalarlo sin una de dos cosas malas:
meterle las filas a la matriz de ES0901 —y perder de qué estándar salió cada regla— o escribir un
runtime paralelo —y tener dos maneras distintas de decir lo mismo—.

Hay además tres problemas que son de ES0902 y de ningún otro estándar:

1. **`G1` no es único.** ES0901 tiene G1 y G2, ES0902 tiene G1, G2, G3 y G4, y no son la misma
   regla. La clave global tiene que ser compuesta o dos reglas distintas comparten identidad.
2. **La aprobación de seguridad no es del harness.** ES0902 §4 separa el control automatizado del
   circuito interno de DGSEI. Un harness que emite `APPROVED` desde sus propios checks está
   firmando una homologación que no le corresponde, y el resultado se lee igual de autoritativo
   que uno real.
3. **Dos estándares pueden pedir lo mismo y no ser lo mismo.** ES0902 C1 exige OpenID Connect con
   Keycloak de DGSEI; ES0901 D1 exige autenticación ciudadana del GCBA. Reconciliarlas sin
   evidencia autoritativa es inventar una interpretación normativa.

## Qué queda afuera

- **El texto citable de ES0902.** ES0901 tiene dos archivos: `es0901-7.1.json` con el texto citado
  y la página, y la matriz con la clasificación. ES0902 llega con la matriz y sin el archivo
  citable. No se extrae del PDF: una cita mal transcrita se lee igual de autoritativa que una
  bien transcrita, y el paquete dice explícitamente que no se copie contenido normativo.
- **Implementar los controles que la matriz ES0902 declara y el harness no tiene.** Veinte
  policies, dieciseis checks y dos reviews se declaran y
  salen `DECLARED_CHECK_NOT_INSTALLED` / `DECLARED_POLICY_NOT_INSTALLED`, que es el estado
  correcto de un harness que clasificó antes de construir — la misma decisión que ES0901 tomó
  para sus 24 filas y que todavía sostiene para **trece** de ellas. Lo que sí se construye es la
  resolución de **resultado por regla**, que es lo que los invariantes S-27, S-29, S-31, S-44 y
  la familia G exigen.
- **Reconciliar ES0901 D1 con ES0902 C1.** Es exactamente lo que el paquete prohíbe. El cruce
  queda en `CROSS_STANDARD_INTERPRETATION_REQUIRED` y ahí se queda hasta que llegue evidencia.
- **Un agente de seguridad nuevo.** `dev-security` existe con sus cuatro skills y es la capa de
  ejecución. El paquete lo prohíbe y además no hace falta.
- **Deduplicar Vu5 contra ES0901 P5.** P5 no está implementada. El mapa cruzado lo declara
  `CROSS_STANDARD_CONTROL_BINDING_REQUIRED` y no se compara semántica contra algo que no existe.
- **El paquete de evidencia en disco** (`security-assessment/` con su manifest y sus carpetas).
  Se especifica su contrato y se resuelve qué falta; escribirlo al disco es otro cambio, y el
  paquete lo llama "recomendado", no exigido.
- **Números de umbral que el estándar no da.** Vu9 no lleva un límite de peticiones por minuto,
  porque ES0902 no lo da y el que lo invente queda escrito como si fuera normativo.

## Las decisiones, y por qué

### Un módulo por pregunta, no uno por estándar

Tres módulos nuevos, no uno:

| Módulo | La pregunta que contesta |
|---|---|
| `seguridad.py` | Qué regla de ES0902 aplica a esta unidad, y con qué resultado |
| `evaluacion.py` | En qué estado está la evaluación de seguridad, y quién puede moverla |
| `cruzada.py` | Qué relación hay entre una regla de ES0901 y una de ES0902 |

La alternativa era un `es0902.py` con todo adentro. Se descartó porque las tres preguntas tienen
lectores distintos: la primera la consume el plan, la segunda la consume quien prepara una
homologación, y la tercera sólo aparece cuando los dos estándares aplican a la vez. Meterlas
juntas obliga a cargar el mapa cruzado para resolver una regla que no cruza con nada.

### La clave global es compuesta, y el id local se conserva

```
id       "G1"            lo que dice el estándar, y lo que se cita
ruleKey  "ES0902.G1"     lo que identifica globalmente
```

Las dos viajan. Sólo la compuesta sirve para comparar entre estándares, y sólo la local sirve para
volver al texto del estándar sin traducir. Reemplazar una por la otra rompe uno de los dos usos.

🔴 La matriz **declara** su `ruleKey` y no se deriva al vuelo. Derivarlo haría que un `ruleKey`
equivocado en el archivo fuera invisible; declarándolo, la validación lo compara contra
`ES0902.<id>` y una fila mal escrita invalida la matriz.

### El registro de controles pasa a multi-fuente, sin romper el singular

`source` sigue existiendo y sigue valiendo. Se agrega `normativeSources`, y la lectura es:

```
normativeSources   si está, es la lista, entera
source             si no está la lista, es una lista de uno
ninguno de los dos el control no declara de dónde sale -> inválido
```

La alternativa era migrar los 31 controles y borrar `source`. Se descartó: el registro viaja a
proyectos instalados que se actualizan en momentos distintos, y un campo que desaparece rompe a
distancia sin avisar. La compatibilidad se conserva **y se prueba**, no se afirma.

🔴 **Un control se ejecuta una vez y su resultado no se propaga.** `authentication-delegation`
sale de ES0901 D2 y de ES0902 C1; se ejecuta una sola vez y su resultado se anota **por fuente**.
Que D2 dé PASS no pone en PASS a C1: la aplicabilidad de cada regla se resolvió por separado y la
evidencia que satisface a una puede no satisfacer a la otra.

### El resultado de una unidad expone los dos estándares y conserva la forma vieja

```python
normative = {
    ...los mismos campos de siempre, los de ES0901...,   # nadie que ya lee se entera
    "standards": {"ES0901": {...}, "ES0902": {...}},     # lo nuevo, al lado
}
```

`normativa.py` ya declara la regla en su docstring: *"Cambiarle el tipo a un campo que alguien ya
lee es romper a distancia."* Se sostiene. Lo nuevo va al lado, nunca encima.

### La frontera de la aprobación es estructural, no una convención

El harness tiene productores internos —un escaneo automático, una review de `dev-security`, el
cálculo del umbral G2— y ninguno puede emitir un estado oficial. La guarda no es "acordate de no
hacerlo": es que **el estado oficial exige procedencia externa declarada**, y un productor interno
no la tiene por construcción.

```
estado oficial + procedencia interna  ->  se rechaza, y el resultado dice por qué
estado oficial sin procedencia        ->  OFFICIAL_STATUS_UNRESOLVED
```

La alternativa —una lista de estados prohibidos por productor— se descartó por la misma razón por
la que `bases.py` deriva el permiso de la clase en vez de enumerar: una lista se desactualiza en
silencio cuando aparece un productor nuevo, y el productor nuevo queda permitido.

### `G2_THRESHOLD_SATISFIED` es un cálculo, y no es una aprobación

El umbral se calcula sólo si las severidades del escáner están mapeadas de forma autoritativa a
las categorías de riesgo de ES0902. Sin ese mapeo no se calcula: `VULNERABILITY_RISK_MAPPING_UNRESOLVED`.
Y satisfecho el umbral, el estado oficial **no se mueve**. Son dos hechos distintos y el paquete
los separa en dos invariantes (S-37 y S-38) justamente porque colapsarlos es el atajo esperable.

### La ausencia de evidencia es `UNRESOLVED`, y un hallazgo es `NON_COMPLIANT`

El resultado por regla es genérico y no tiene una rama por id:

```
NOT_APPLICABLE   la aplicabilidad lo dijo
NON_COMPLIANT    hay un hallazgo abierto que cita la regla, o un control suyo reportó FAIL
COMPLIANT        todos sus controles declarados tienen evidencia de PASS y no hay hallazgo
UNRESOLVED       cualquier otra cosa
```

Las ramas por regla existen sólo donde el estándar **declara un algoritmo**, y son **ocho**: C2
(QA + aprobación oficial), Ve2 (consenso de Infraestructura), Vu4 (independencia del token), Vu9
(mecanismos alternativos), Vu10 (guía por tipo de activo), G2, G3 y G4. Viven juntas en
`ALGORITMOS` para que se vean de un saque; ninguna otra regla tiene rama.

### Los entregables son la unión, y se declara que la unión es la decisión

Un sistema que es aplicación web **y** servicio web exige E1 ∪ E2. Elegir el conjunto más chico es
el sesgo barato que el paquete nombra en S-15, y es la misma familia de error que `senales.py` ya
tiene escrita: *"Elegir la que deja el plan más corto es el sesgo más barato que puede tener un
productor y no deja rastro."*

### Los dos documentos en inglés viajan a `reglas/`

`es0902-security-governance.md` y `es0902-security-assessment-workflow.md` son artefactos
normativos provistos, en inglés, que un modelo lee. Van junto a los JSON en `reglas/`, que es el
directorio que `roster.ruta_de_regla` encuentra igual en el repo y en un árbol instalado. El
documento para personas es `docs/seguridad-es0902.md`, en español, y no es una traducción de
aquellos: dice qué quedó instalado y qué no.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/bin/orquestacion/seguridad.py` | La matriz ES0902: carga, valida el inventario de 21, resuelve aplicabilidad y resultado por regla, y la excepción aprobada por ASI |
| `harnesses/desarrollo/bin/orquestacion/evaluacion.py` | El flujo de evaluación, la frontera de la aprobación oficial, el umbral G2, G3, G4, C2, los entregables E1–E5 y el WAF |
| `harnesses/desarrollo/bin/orquestacion/cruzada.py` | El mapa cruzado: claves compuestas, controles compartidos, conflictos entre estándares |
| `harnesses/desarrollo/reglas/es0902-6.2-normative-matrix.json` | Las 21 reglas. Copia textual de lo provisto |
| `harnesses/desarrollo/reglas/es0902-cross-standard-map.json` | Las ocho relaciones entre ES0901 y ES0902. Copia textual |
| `harnesses/desarrollo/reglas/es0902-security-deliverables.json` | E1–E5 y el WAF. Copia textual |
| `harnesses/desarrollo/reglas/es0902-security-governance.md` | La arquitectura de gobierno provista. Copia textual |
| `harnesses/desarrollo/reglas/es0902-security-assessment-workflow.md` | El flujo provisto. Copia textual |
| `comun/schemas/es0902-normative-matrix.schema.json` | El contrato de la matriz. Copia textual de lo provisto |
| `comun/schemas/es0902-cross-standard-map.schema.json` | El contrato del mapa cruzado, escrito contra el archivo provisto |
| `comun/schemas/es0902-security-deliverables.schema.json` | El contrato de los entregables, escrito contra el archivo provisto |
| `comun/schemas/control-registry.schema.json` | Gana `normativeSources`; `source` queda opcional; `rule` acepta los ids de ES0902 |
| `harnesses/desarrollo/reglas/control-registry.json` | Los seis controles compartidos ganan su segunda fuente normativa |
| `harnesses/desarrollo/bin/orquestacion/controles.py` | Lee las fuentes múltiples y conserva la compatibilidad con la singular |
| `harnesses/desarrollo/bin/orquestacion/senales.py` | El inventario de señales sale de los dos estándares |
| `harnesses/desarrollo/bin/orquestacion/normativa.py` | `resolucion` suma `standards` sin cambiarle el tipo a nada |
| `tests/casos/37_es0902_seguridad.py` | Los escenarios de acá |
| `docs/seguridad-es0902.md` | Qué quedó instalado, en español, para quien lo va a usar |

## Escenarios verificables

### Identidad e inventario

- **E-01** — La matriz ES0902 carga y declara `ES0902`, `6.2`, `2025-08` y `expectedRuleCount: 21`;
  una matriz que dice otra versión del estándar no se usa a medias, se rechaza.
  · rojo visto: sí
- **E-02** — El inventario de 21 se compara contra la lista literal del estándar, y una regla que
  falta, una repetida o una que sobra se reportan **con su id**, no con un conteo.
  · rojo visto: sí
- **E-03** — Cada fila declara `ruleKey` y la validación lo compara contra `ES0902.<id>`: una fila
  cuya clave compuesta no corresponde a su id invalida la matriz. · rojo visto: sí
- **E-04** — `ES0901.G1` y `ES0902.G1` son dos reglas distintas: resolver una no devuelve la otra,
  y ninguna de las dos resoluciones pisa a la otra. · rojo visto: sí
- **E-05** — Un id que no está en el inventario de ES0902 no se resuelve: `NORMATIVE_RULE_NOT_FOUND`,
  y el rechazo no deja media matriz cargada. · rojo visto: sí
- **E-06** — Las reglas de ES0902 no entran en `es0901-7.1-normative-matrix.json`: ese archivo
  sigue con su inventario de 24 y ninguna de sus filas menciona ES0902. · rojo visto: sí

### Runtime compartido

- **E-07** — La resolución de ES0902 devuelve **las mismas claves** que la de ES0901: quien sabe
  leer un bloque normativo sabe leer los dos. · rojo visto: sí
- **E-08** — El bloque `normative` que el plan ya consumía conserva todos sus campos y sus tipos;
  `standards` se suma al lado y no reemplaza a ninguno. · rojo visto: sí
- **E-09** — Toda fila de un resultado de ES0902 lleva su traza `standard`, `version` y `rule`, y
  ninguna la pierde por el camino. · rojo visto: sí
- **E-10** — Las quince señales que declara ES0902 quedan declaradas para `senales.py`: una señal
  de ES0902 no sale `SIGNAL_NOT_DECLARED`, y las de ES0901 siguen declaradas. · rojo visto: sí
- **E-11** — Cada agente que la matriz ES0902 nombra existe en el registro de agentes; uno que no
  esté es `NORMATIVE_AGENT_REFERENCE_INVALID` y no se crea. · rojo visto: sí

### El registro de controles, multi-fuente

- **E-12** — Un control puede declarar varias `normativeSources` y todas se conservan enteras:
  estándar, versión y regla de cada una. · rojo visto: sí
- **E-13** — Un control con la forma vieja —`source` singular— se sigue leyendo y vale como una
  fuente. La migración no rompe lo instalado. · rojo visto: sí
- **E-14** — Un control que dos estándares citan se declara **una vez**: no hay un
  `authentication-delegation` de D2 y otro de C1. · rojo visto: sí
- **E-15** — Un control compartido se ejecuta una vez y su resultado no se propaga: PASS por
  ES0901 D2 no pone en PASS a ES0902 C1. · rojo visto: sí
- **E-16** — El campo `rule` acepta los ids de ES0902 que el patrón anterior rechazaba —`O1`,
  `Vu1`, `Ve1`— y sigue rechazando uno que no es de ninguno de los dos estándares.
  · rojo visto: sí
- **E-17** — Un control sin ninguna de las dos formas de fuente es inválido: no se acepta un
  control que no dice de dónde sale. · rojo visto: sí

### La excepción aprobada por ASI

- **E-18** — Configuración local del proyecto, sola, nunca exime una regla de ES0902.
  · rojo visto: sí
- **E-19** — Evidencia de contrato sin aprobación de ASI no exime: `SECURITY_NORMATIVE_OVERRIDE_UNRESOLVED`.
  · rojo visto: sí
- **E-20** — Aprobación de ASI sin evidencia de contrato tampoco exime: el mismo estado.
  · rojo visto: sí
- **E-21** — Contrato **y** aprobación de ASI producen una excepción con respaldo, y el resultado
  conserva `affectedRules`, `contractEvidence`, `asiApprovalEvidence` y `reason` sin perder nada.
  · rojo visto: sí
- **E-22** — Una excepción alcanza sólo a las reglas que nombra en `affectedRules`: las demás
  siguen exactamente igual que sin excepción. · rojo visto: sí

### La frontera de la aprobación oficial

- **E-23** — Un escaneo automático no puede emitir `APPROVED`: queda en el estado interno que le
  corresponde y el estado oficial no se mueve. · rojo visto: sí
- **E-24** — Una review interna de `dev-security` no puede emitir aprobación oficial, ni siquiera
  declarándola. · rojo visto: sí
- **E-25** — `APPROVED` exige procedencia externa GCBA/DGSEI; sin ella, `OFFICIAL_STATUS_UNRESOLVED`.
  · rojo visto: sí
- **E-26** — La guarda es estructural: recorriendo **todos** los productores internos que el
  módulo declara, ninguno llega a un estado oficial. El barrido sale del módulo, no de una lista
  escrita a mano. · rojo visto: sí
- **E-27** — Con todas las reglas de principios de seguridad en PASS, el estado oficial sigue sin
  moverse: ES0902 G1 como invariante, no como comentario. · rojo visto: sí

### El flujo de evaluación

- **E-28** — Los doce estados del flujo son los declarados, y uno que no está en la lista no se
  acepta: un estado desconocido falla cerrado. · rojo visto: sí
- **E-29** — C2 no puede PASS con aprobación evidenciada fuera de QA. · rojo visto: sí
- **E-30** — C2 puede PASS con ambiente QA **y** evidencia de aprobación oficial; una review
  interna en QA no alcanza. · rojo visto: sí
- **E-31** — `READY_TO_REQUEST` exige que todos los entregables aplicables y el requisito de WAF
  estén resueltos; con alguno sin resolver, no se llega. · rojo visto: sí

### Entregables y WAF

- **E-32** — E1–E5 se resuelven por tipo de activo y los requisitos son exactamente los del
  archivo provisto: ninguno se agrega, ninguno se pierde. · rojo visto: sí
- **E-33** — Dos tipos de activo producen la **unión** de sus requisitos, nunca el conjunto más
  chico ni el del primero. · rojo visto: sí
- **E-34** — `WEB_SERVICE` exige el artefacto de WAF. · rojo visto: sí
- **E-35** — `WEB_APPLICATION` exige el artefacto de WAF. · rojo visto: sí
- **E-36** — Sin la plantilla del formulario de WAF: `WAF_FORM_CONTEXT_REQUIRED`, y ese estado
  bloquea `READY_TO_REQUEST` del activo al que aplica. · rojo visto: sí
- **E-37** — Ningún campo del formulario de WAF se inventa: lo único que el módulo publica del WAF
  es lo que trae el archivo. · rojo visto: sí
- **E-38** — Entregables aplicables faltantes: `SECURITY_DELIVERABLES_INCOMPLETE`, con cuáles
  faltan. · rojo visto: sí

### C1, y el cruce con ES0901 D1

- **E-39** — C1 reusa los dos controles de delegación de credenciales de ES0901 D2 y les agrega
  `ES0902.C1` como segunda fuente normativa. · rojo visto: sí
- **E-40** — C1 exige evidencia de OIDC con Keycloak de DGSEI; sin ella la regla queda sin
  resolver, nunca en PASS. · rojo visto: sí
- **E-41** — ES0901 D1 y ES0902 C1 aplicables a la vez, sin reconciliación autoritativa:
  `CROSS_STANDARD_INTERPRETATION_REQUIRED`. · rojo visto: sí
- **E-42** — No se inventa ninguna reconciliación: ni realm, ni client, ni issuer, ni flow
  aparecen en ninguna salida sin evidencia que los traiga. · rojo visto: sí

### Tecnología y versiones

- **E-43** — C3 reusa los cuatro controles de ES0901 G1 y no duplica ni el Anexo II ni la
  comparación de versiones: el módulo de ES0902 no tiene lógica propia de ninguna de las dos.
  · rojo visto: sí
- **E-44** — Ve1 reusa esos mismos cuatro controles. · rojo visto: sí
- **E-45** — Ve2: una versión más nueva, o alegada más segura, sin consenso de Infraestructura no
  puede PASS. · rojo visto: sí

### Los diez principios de seguridad

- **E-46** — Vu1 a Vu10 son diez reglas distintas y resuelven por separado: ninguna se colapsa en
  una review genérica de seguridad. · rojo visto: sí
- **E-47** — Vu2: transmisión de dato sensible en texto plano no cumple. · rojo visto: sí
- **E-48** — Vu4: el vencimiento por inactividad se evalúa independientemente del tiempo de vida
  del token de OpenID; evidencia del token no satisface la regla. · rojo visto: sí
- **E-49** — Vu5: validación sólo de cliente no puede PASS. · rojo visto: sí
- **E-50** — Vu9: ningún umbral numérico se inventa. Barriendo la salida y el módulo no aparece un
  número de límite que no venga de un contrato del proyecto o de la plataforma.
  · rojo visto: sí
- **E-51** — Vu9: interfaz pública sin autenticar y sin controles de abuso no cumple; y mecanismos
  distintos con evidencia —cuota, anti-bot, tope de recursos, control de gateway— alcanzan igual,
  sin que el límite de tasa sea el único aceptado. · rojo visto: sí
- **E-52** — Vu10: la guía OWASP se resuelve por tipo de activo —Web, API, Mobile— y se conservan
  referencia, versión y fecha. · rojo visto: sí
- **E-53** — Vu10: una referencia OWASP desconocida o vencida queda explícita y no se reemplaza
  por una lista de categorías cacheada. · rojo visto: sí

### Aceptación: G2, G3 y G4

- **E-54** — G2 con algún hallazgo por encima de LOW no satisface el umbral. · rojo visto: sí
- **E-55** — G2 con más de 10 hallazgos LOW no satisface el umbral. · rojo visto: sí
- **E-56** — G2 con hasta 10 LOW y ninguno mayor satisface `G2_THRESHOLD_SATISFIED`.
  · rojo visto: sí
- **E-57** — Severidades del escáner que no se pueden mapear de forma autoritativa:
  `VULNERABILITY_RISK_MAPPING_UNRESOLVED`, y el umbral **no se calcula igual**.
  · rojo visto: sí
- **E-58** — `G2_THRESHOLD_SATISFIED` nunca produce `APPROVED`. · rojo visto: sí
- **E-59** — G3 exige recontrolar el 100% de los hallazgos previos, conservando su identidad y su
  evidencia de retest; con uno sin recontrolar, no alcanza. · rojo visto: sí
- **E-60** — G3 sigue evaluando G2: recontrolar todo no exime del umbral. · rojo visto: sí
- **E-61** — G4 dispara una evaluación de alcance completo, no sólo los hallazgos previos, y
  admite hallazgos nuevos en la evidencia. · rojo visto: sí
- **E-62** — G4 sigue evaluando G2. · rojo visto: sí

### Los activos de seguridad que ya existen

- **E-63** — No se crea ningún agente de seguridad: el registro sigue con los mismos diez agentes
  y `dev-security` sigue siendo el único de seguridad. · rojo visto: sí
- **E-64** — Las skills de seguridad existentes siguen siendo la capa de ejecución y ninguna se
  redefine ni cambia de dueño. · rojo visto: sí

### Fallo cerrado, y el árbol instalado

- **E-65** — Los ocho estados globales que el paquete exige existen con ese nombre exacto y se
  emiten; ninguno se llama parecido. · rojo visto: sí
- **E-66** — Un estado de seguridad desconocido falla cerrado: no cae en PASS, no cae en APPROVED,
  y se dice cuál era. · rojo visto: sí
- **E-67** — Sin la matriz de ES0902 —ausente o ilegible— se falla cerrado con el estado, y la
  resolución de ES0901 sigue andando: un estándar roto no se lleva puesto al otro.
  · rojo visto: sí
- **E-68** — Los tres módulos nuevos arrancan en un árbol instalado, con `reglas/` colgando de
  `.claude/harness/`, no sólo en el repo. · rojo visto: sí
- **E-69** — Los tres módulos no tienen ninguna vía propia de conseguir un secreto: no importan
  el almacén ni ninguna biblioteca de red, no leen el ambiente, y cada uno abre a lo sumo los dos
  archivos que declara. Un valor sólo sale si quien llama lo puso en la evidencia, y eso queda
  dicho. · rojo visto: sí
- **E-71** — `security-vulnerability-acceptance-threshold` lo declara G2 como policy **y** como
  check. El archivo provisto no se corrige: la colisión se reporta como
  `SECURITY_CONTROL_ID_TYPE_COLLISION`, con el id y los dos tipos, y no invalida la matriz.
  · rojo visto: sí
- **E-70** — Los ids que la matriz ES0902 declara y el registro no tiene salen
  `DECLARED_POLICY_NOT_INSTALLED` / `DECLARED_CHECK_NOT_INSTALLED` / `DECLARED_REVIEW_NOT_INSTALLED`,
  con el conteo exacto fijado, y eso no invalida la matriz. · rojo visto: sí

## Cómo se verifica

Los setenta y un escenarios pasan por la suite, en `tests/casos/37_es0902_seguridad.py`, y cada
test nombra su `E-nn` en el título. Son 1459 aserciones. Ninguno lleva `· verificación: lectura`: no hay acá un escenario
cuyo sujeto sea una corrida de un modelo. Todo lo que este cambio construye es resolución
determinística sobre dato declarado, y lo que necesita criterio —si una práctica OWASP fue
efectivamente considerada— queda declarado como REVIEW y sin instalar, que es un hecho
comprobable.

La marca `rojo visto` de los setenta y uno salió de tres pasadas de mutación —79 mutaciones
entre las tres— y no de una afirmación. La primera dio 60 escenarios en rojo y dejó **cinco
huecos reales** que hubo que tapar antes de seguir:

| Mutación sin rojo | Lo que faltaba |
|---|---|
| una señal ausente vuelve `NOT_APPLICABLE` | nada comparába "no se sabe" contra "no" |
| lo local sí exime | la guarda era código muerto: ninguna fuente local estaba admitida |
| una regla sin controles cumple al vacío | ninguna de las 21 está en ese caso; hubo que fabricarlo |
| una excepción pendiente convive con `COMPLIANT` | el estado quedaba a la vista y el verde también |
| una relación cruzada con nada aplicable igual sale | sólo se filtraba el destino, no el origen |

Y encontró tres tests que probaban otra cosa: `E-32` comparába el archivo de entregables **contra
sí mismo**, `E-42` barría sensible a mayúsculas —una constante gritada se escapaba— y esa misma
`E-32` usaba subcadena, así que `"APK firmado"` pasaba por `"APK"`.

El portón es `.\tests\Invoke-Tests.ps1`, verde, con los dos motores.

## Riesgos conocidos

1. **Veinte policies, dieciseis checks y dos reviews declarados y no construidos.** Es el estado
   correcto y es
   también el más grande que tuvo el harness hasta hoy. El riesgo real es que alguien lea
   "ES0902 instalado" y entienda "ES0902 se cumple". Se mitiga con E-70, que fija el conteo
   exacto, y con `docs/seguridad-es0902.md`, que lo dice en la primera pantalla.
2. **La resolución de resultado por regla es genérica y las excepciones son ocho.** Cada rama por
   regla es una oportunidad de que el estándar se interprete en el código. Se mitiga declarando
   las ocho en `ALGORITMOS`, en un solo lugar, para que una novena no aparezca sin que nadie la vea.
3. **El mapa cruzado depende de que ES0901 P5 no exista.** El día que P5 se implemente, la
   relación `EQUIVALENCE_REVIEW_REQUIRED` con Vu5 hay que resolverla de verdad. Queda anotada en
   `Pendientes/Fix-Harness/PENDIENTES-FH.md`.
4. **El umbral G2 depende de un mapeo de severidades que hoy no produce nadie.** Sin productor,
   toda corrida real sale `VULNERABILITY_RISK_MAPPING_UNRESOLVED`. Es el estado correcto y es
   también un hueco: el harness no tiene de dónde sacar el mapeo autoritativo todavía.
5. **Un id de control declarado con dos tipos.** La matriz provista declara
   `security-vulnerability-acceptance-threshold` como policy y como check bajo la misma regla. Se
   reporta y no se corrige: corregir un archivo normativo provisto es inventar normativa. Mientras
   no se corrija en origen, ese id aparece dos veces en el reporte de controles no instalados, con
   un tipo cada vez.
6. **`senales.declaradas` pasa a mirar dos matrices.** Si una regla de ES0902 declara una señal
   con el mismo nombre que una de ES0901 y distinto significado, las dos se resuelven con el mismo
   documento. Hoy pasa con `authenticationPresent`, y es deliberado —el paquete dice reusarla—,
   pero la colisión no está impedida y una señal futura podría chocar sin aviso.
