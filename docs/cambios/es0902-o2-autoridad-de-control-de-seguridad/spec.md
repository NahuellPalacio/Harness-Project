# ES0902 O2 — quién controla la seguridad, y por qué el harness no puede ser

**Estado:** verificado y cerrado · **Fecha:** 22-09-2026 · **Regla:** ES0902 6.2 §3 O2

## Qué problema resuelve

O2 es la segunda fila de ES0902:

> `ES0902-3-O2` — *"El control de la seguridad informática debe estar a cargo de un organismo
> perteneciente al GCABA."*

No es una regla sobre el código. Es una regla sobre **quién responde**, y la pregunta que contesta
no es *"¿el harness corre controles de seguridad?"* sino *"¿la responsabilidad del control de
seguridad de este alcance está asignada a un organismo del que consta que es del GCABA?"*.

La fila está clasificada desde que se instaló la línea base de ES0902 —`ALWAYS`, cero señales,
`dev-security`, una policy, un check, cero reviews— y sus dos controles **no existen**. El agujero
es distinto del de O1 y es peor de leer:

```
sin O2 construido   ->  DECLARED_POLICY_NOT_INSTALLED
                        DECLARED_CHECK_NOT_INSTALLED
                    ->  nadie pregunta de quién es el control de seguridad,
                        y el harness es lo único que está corriendo controles
```

Un harness que corre `dev-security`, que tiene cuatro skills de seguridad y que emite resultados por
regla **se parece mucho** a la autoridad de control de seguridad del proyecto. No lo es, y la única
manera de que eso quede escrito es que exista un control que lo diga.

Y hay tres trampas propias de esta regla:

**La primera: ejecutar se confunde con controlar.** Un proveedor que corre el escaneo, un equipo que
remedia, un agente que prepara la evidencia: los tres *hacen* seguridad y ninguno *responde* por
ella. Un check que mire quién ejecuta se pone verde sobre un proyecto cuya seguridad no controla
ningún organismo del GCABA.

**La segunda: la pertenencia al GCABA se adivina de seis formas y ninguna sirve.** El nombre de la
organización, el dominio del correo, el namespace del repositorio, el texto del README, el empleador
que alguien declara, la ubicación de red. Las seis están al alcance de la mano y las seis las puede
escribir cualquiera.

**La tercera: una autoridad no dura para siempre.** Un acta de 2019 que asignó el control a un
organismo no dice nada sobre hoy, y reusarla en silencio es la forma más cómoda de que O2 quede en
verde durante años sin que nadie mire.

## Qué queda afuera

- **Una autoridad precargada.** El harness se instala con `security-control-authority.json`
  **vacío**. Quién controla la seguridad de un proyecto es dato del proyecto, y un harness que llega
  con una respuesta puesta es un harness que contestó por el proyecto. Sin registro,
  `SECURITY_CONTROL_AUTHORITY_UNRESOLVED`, que no es ni aprobar ni reprobar.
- **Cablear `DGSEI`.** El §4 de ES0902 describe el circuito interno de DGSEI y eso es contexto del
  proceso oficial, no el contenido de O2. O2 pide *un organismo del GCABA*; cuál es lo dice la
  evidencia del proyecto. Escribir `DGSEI` adentro del check lo volvería normativa que ES0902 no da.
- **Deducir la pertenencia al GCABA.** No se mira el nombre, el dominio, el namespace, el README, el
  empleador declarado ni la red. La pertenencia la sostiene evidencia de una de las seis clases
  autoritativas, o queda `GCABA_MEMBERSHIP_UNRESOLVED`.
- **Un orden entre los tipos de alcance.** No se asume que `PROJECT` contiene a `APPLICATION` ni que
  `GLOBAL` contiene a todo. La contención **la declara el objetivo** y no la deduce el check: un
  orden inventado es exactamente cómo la autoridad de un proyecto termina cubriendo a otro.
- **Un algoritmo propio en `seguridad.py`.** O2 sale por el camino genérico y `ALGORITMOS` sigue
  teniendo nueve entradas. La diferencia con O1 es la que importa: O1 no tiene check y sus dos
  controles son ella misma, así que el camino genérico la aprobaba sola. O2 **tiene** un check
  determinista que produce el `PASS`, igual que G1, D1 a D8 y P1. Agregarle una décima rama sería el
  estándar reinterpretándose en el código.
- **Resolver C2.** O2 dice quién controla; C2 dice si hay aprobación oficial de seguridad en QA. Que
  la misma evidencia pueda sostener la procedencia de las dos no las hace la misma, y O2 en `PASS`
  no mueve nada de C2 ni del estado oficial de la evaluación.
- **Un vocabulario de responsabilidades.** No se escribe una taxonomía de seguridad. El valor que
  cuenta como control es **uno**, `SECURITY_CONTROL`, que es lo que la regla nombra; las cinco
  formas de ejecución que el paquete nombra —desarrollo, hosting, consultoría, escaneo y
  remediación— se declaran para poder decir *por qué* no alcanzan, y todo lo demás no cuenta.
- **Un agente y una skill.** `dev-security` es el dueño de la fila y sigue siendo el mismo, con sus
  cuatro skills. Este cambio no crea, no modifica y no renombra ninguna de las dos cosas.

  Y lo que el check garantiza sobre ellos es preciso: **el nombre no abre ningún camino**. Una
  autoridad llamada `dev-security` vale exactamente lo mismo que una llamada `Pepe` —sin evidencia
  autoritativa no establece nada, con evidencia la establece la evidencia—. El harness no puede
  *nombrarse* autoridad, y tampoco puede juzgar un acta del GCABA que nombre a quien sea: eso lo
  firma quien la firma. Lo que el check cierra es el camino automático, no el criterio de quien
  emite la evidencia.

## Las decisiones, y por qué

### El registro es del proyecto y se instala vacío, como los perfiles de base

Ya hay precedente y se sigue al pie:

```
reglas/database-environment-access-policy.json   del HARNESS. Un proyecto no la edita
reglas/database-profiles.json                    del PROYECTO. Se instala VACIO
reglas/security-control-authority.json           del PROYECTO. Se instala VACIO
```

Un harness que pudiera declarar quién controla la seguridad de un proyecto ajeno no está
verificando nada: está rellenando el casillero que después va a leer. Vacío es la única posición
honesta, y `SECURITY_CONTROL_AUTHORITY_UNRESOLVED` es el estado correcto de un proyecto que todavía
no lo declaró.

### Autoridad y ejecución son dos cosas, y el check sólo mira una

```
CONTROL AUTHORITY   responde por el control de seguridad del alcance
EJECUCIÓN           escanea, revisa, remedia, prepara evidencia
```

El check no tiene ningún campo de ejecutor y no lo va a tener. No es una omisión: es la forma de que
*"quién ejecuta no puede volverse quién responde"* sea una propiedad del archivo y no una costumbre
que alguien tenga que acordarse de respetar. Un proveedor que escanea puede estar declarado como
autoridad con la responsabilidad `SECURITY_SCANNING` y no va a contar, porque la única
responsabilidad que cuenta es `SECURITY_CONTROL`.

La alternativa era aceptar una lista de ejecutores y verificar que no se cuelen. Se descartó: un
campo que existe para ser ignorado es un campo que alguien va a terminar leyendo.

### `VERIFIED` es una etiqueta, y una etiqueta no es evidencia

`organization.gcabaMembership` puede decir `VERIFIED`, y por sí solo eso no establece nada: lo
escribe quien edita el archivo. La pertenencia queda establecida cuando además hay **al menos una
evidencia de una de las seis clases autoritativas con su referencia**. Sin eso,
`GCABA_MEMBERSHIP_UNRESOLVED` aunque el archivo diga `VERIFIED`.

Es el mismo mecanismo que ya sostiene la excepción de ES0902 —las dos mitades, y lo local que no
cuenta nunca—: una declaración que se valida a sí misma no valida nada.

### La contención de alcance la declara el objetivo, y `GLOBAL` no es una excepción

El objetivo trae su alcance y, si quiere que lo cubra una autoridad más ancha, la cadena que lo
contiene:

```json
{"scope": {"type": "APPLICATION", "value": "tramites-web"},
 "within": [{"type": "PROJECT", "value": "tramites"},
            {"type": "GLOBAL", "value": "GCABA"}]}
```

Una autoridad cubre al objetivo cuando su alcance es el del objetivo o está en esa cadena. No hay
orden implícito entre `GLOBAL`, `PROJECT`, `SYSTEM`, `APPLICATION`, `COMPONENT` y `ASSESSMENT`, y
`GLOBAL` no cubre a quien no lo declaró.

La alternativa era darle a `GLOBAL` el significado obvio —cubre todo—. Se descartó porque sería el
camino más barato a `PASS`: una sola línea con `type: GLOBAL` y el alcance deja de medir. La
consecuencia se acepta y se declara: un proyecto que quiere que su autoridad global aplique tiene
que decirlo en cada objetivo.

### Sin fecha de fin no hay vigencia, y eso es a propósito

```
effectiveTo vencido para la fecha de evaluación   ->  SECURITY_AUTHORITY_EVIDENCE_EXPIRED
effectiveTo ausente, nulo o mal formado           ->  SECURITY_AUTHORITY_CURRENT_STATUS_UNRESOLVED
effectiveFrom posterior a la fecha                ->  SECURITY_AUTHORITY_CURRENT_STATUS_UNRESOLVED
```

Es incómodo: obliga a que un acta de asignación traiga hasta cuándo vale. Y es lo que el paquete
pide cuando dice *"no reusar en silencio una asignación vieja para siempre"*. Una autoridad sin
fecha de fin no es una autoridad vigente: es una autoridad sobre la que nadie dijo nada, y ésa es
exactamente la que lleva años sin que nadie mire.

Las fechas son `YYYY-MM-DD` y se comparan como texto, que para ese formato es el orden correcto.
Una fecha que no cumple el formato no se interpreta: queda sin resolver.

### Un conflicto es de organización, y el alcance no lo desarma

Hay conflicto cuando **dos registros vigentes, los dos con responsabilidad de control, cubren al
mismo objetivo y son organizaciones distintas**. No importa que sus alcances declarados sean
distintos —uno a nivel de proyecto y otro global—: si los dos alcanzan al objetivo, el check no
tiene con qué decir cuál responde, y elegir el más específico exigiría el orden entre tipos de
alcance que este cambio se niega a inventar.

Lo que **no** es conflicto: dos registros de la misma organización, y dos registros de los cuales
sólo uno está vigente para la fecha. En el segundo caso resuelve el vigente, que es lo que
*"current assignment"* quiere decir.

La multiplicidad que el paquete pide soportar —control de aplicación a un organismo, control de
infraestructura a otro— se expresa por **alcance**, no por responsabilidad: son dos objetivos
distintos y cada uno resuelve contra el suyo. Repartirla por responsabilidad exigiría una taxonomía
de seguridad que ES0902 no da.

### Falta de evidencia nunca es `FAIL`

`FAIL` tiene un único camino y es el que el paquete describe: consta que la autoridad controlante es
ajena al GCABA y no hay ningún organismo del GCABA controlando ese alcance. Todo lo demás que falta
tiene su propio estado sin resolver. Es la misma asimetría de siempre —una negación falsa se
discute, un permiso falso no se entera—, sólo que acá corre para el otro lado: un `FAIL` inventado
acusa a un organismo de algo que nadie probó.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/reglas/security-control-authority.json` | El registro del proyecto, instalado vacío |
| `comun/schemas/security-control-authority.schema.json` | Su contrato, con `additionalProperties: false` en las cuatro capas |
| `harnesses/desarrollo/reglas/es0902-o2-governance.md` | El paquete de gobierno de O2, como vino |
| `harnesses/desarrollo/controles/policies/gcba-security-control-authority-required.md` | La policy, con sus nueve resultados y lo que no alcanza |
| `harnesses/desarrollo/controles/checks/security-control-authority-evidence.py` | El check: nueve estados, autoridad contra ejecución, pertenencia, alcance, vigencia y conflicto |
| `harnesses/desarrollo/reglas/control-registry.json` | Los dos controles de O2, declarados |
| `docs/seguridad-es0902.md` | O2, el registro vacío y por qué el harness no puede ser la autoridad |
| `tests/casos/40_es0902_o2_autoridad_de_control.py` | Los escenarios de acá abajo |

La matriz **no se toca**, y `seguridad.ALGORITMOS` **tampoco**: O2 sale por el camino genérico como
las once reglas de ES0901 que ya están construidas.

Y se reescriben las afirmaciones que hoy están en verde y dejan de ser ciertas: el conteo de
controles —33 → 35— en `31_d6/E-30`, `32_d5/E-36`, `33_bases/E-32`, `34_d7/E-42`, `35_d8/E-37`,
`36_p1/E-39`, `37_es0902/E-13` y `E-14` y `39_es0902_o1/E-28`, y el reporte de huecos de ES0902 —36
→ 34— en `37_es0902/E-70`.

## Escenarios verificables

Entre paréntesis, el criterio del paquete de instalación que cubren.

### La fila, que no se toca

- **E-01** — O2 sigue `ALWAYS` con cero señales, y con el diccionario de señales vacío resuelve
  `APPLICABLE`. (matriz, ALWAYS) · rojo visto: si
- **E-02** — El agente dueño sigue siendo `dev-security`, y es el único que la fila nombra.
  (matriz) · rojo visto: si
- **E-03** — La fila declara exactamente una policy y exactamente un check, con estos ids
  literales —`gcba-security-control-authority-required` y `security-control-authority-evidence`—,
  y cero reviews. (matriz) · rojo visto: si
- **E-04** — O2 **no** entra en `ALGORITMOS`: la tabla sigue teniendo nueve entradas, O2 no es una
  de ellas, y el resultado de la fila sale del camino genérico contra el resultado del check.
  · rojo visto: si
- **E-05** — Instalar O2 no agrega filas: ES0902 sigue con 21 reglas y ES0901 con 24.
  · rojo visto: si

### El registro, que es del proyecto

- **E-06** — `security-control-authority.json` se instala **vacío** —cero autoridades— y valida
  contra su schema; y también carga instalado, donde `reglas/` cuelga a otra altura.
  (project-owned, initially empty) · rojo visto: si
- **E-07** — Con el registro vacío el resultado es `SECURITY_CONTROL_AUTHORITY_UNRESOLVED`: ni
  `PASS` ni `FAIL`. (unresolved) · rojo visto: si
- **E-08** — El schema rechaza lo que no declara, y en las cuatro capas: una clave de más, un
  `sourceType` que no es una de las seis clases, una membresía que no es una de las tres, y un tipo
  de alcance que no es uno de los seis. · rojo visto: si

### La autoridad no es quien ejecuta

- **E-09** — Una responsabilidad de ejecución no establece autoridad: escanear, remediar,
  desarrollar, hostear y consultar dan `AUTHORITY_EVIDENCE_INSUFFICIENT`, una por una.
  (authority vs execution) · rojo visto: si
- **E-10** — Un ejecutor externo declarado al lado de una autoridad del GCABA no la invalida: el
  resultado sigue en `PASS`, y la autoridad que se informa es la del organismo. (delegation)
  · rojo visto: si
- **E-11** — El harness no se nombra autoridad: el módulo **no importa ni lee el registro de
  agentes**, ningún literal operativo suyo nombra un agente o una skill, y una autoridad que dice
  ser un agente sin evidencia no establece nada. La prosa **sí** los nombra —es donde la frontera
  queda declarada—, y eso es lo contrario de una fuga. (harness boundary) · rojo visto: si

### La pertenencia al GCABA

- **E-12** — `gcabaMembership: VERIFIED` sin ninguna evidencia autoritativa deja
  `GCABA_MEMBERSHIP_UNRESOLVED`: la etiqueta la escribe quien edita el archivo.
  (membership requires evidence) · rojo visto: si
- **E-13** — La pertenencia no se deduce: el nombre del organismo, el dominio del correo, el
  namespace del repositorio, el texto del proyecto y el empleador declarado no cambian el
  resultado, las cinco formas probadas una por una. · rojo visto: si
- **E-14** — `NOT_GCABA` como única autoridad controlante del alcance da `FAIL`, y es el **único**
  camino a `FAIL`. (external cannot become authority) · rojo visto: si
- **E-15** — Falta de evidencia nunca es `FAIL`: los siete estados sin resolver se emiten donde
  corresponde y ninguno es `FAIL`. · rojo visto: si

### El alcance

- **E-16** — La autoridad de otro proyecto no cubre a éste: `SECURITY_AUTHORITY_SCOPE_UNRESOLVED`.
  (do not apply one project's authority to another) · rojo visto: si
- **E-17** — La contención la declara el objetivo: una autoridad más ancha cubre sólo si el objetivo
  la nombra en su cadena, y `GLOBAL` no es una excepción. · rojo visto: si
- **E-18** — Varias autoridades con alcances explícitos conviven en el mismo registro: cada
  objetivo resuelve contra la que lo alcanza, y ninguna se pisa con la del otro.
  (multiple scoped authorities) · rojo visto: si

### La vigencia

- **E-19** — `effectiveTo` anterior a la fecha de evaluación da
  `SECURITY_AUTHORITY_EVIDENCE_EXPIRED`. (expired) · rojo visto: si
- **E-20** — Sin `effectiveTo`, con `effectiveTo` nulo, con una fecha mal formada o con
  `effectiveFrom` posterior a la fecha, queda `SECURITY_AUTHORITY_CURRENT_STATUS_UNRESOLVED`: no
  hay autoridad para siempre. (do not silently reuse) · rojo visto: si

### El conflicto

- **E-21** — Dos registros vigentes con responsabilidad de control que cubren al mismo objetivo,
  de organizaciones distintas, dan `CONFLICTING_SECURITY_AUTHORITY_EVIDENCE` — también cuando sus
  alcances declarados son distintos y los dos alcanzan. (conflict) · rojo visto: si
- **E-22** — Dos registros de la **misma** organización que cubren al mismo objetivo no son un
  conflicto: no hay nada que resolver. · rojo visto: si
- **E-23** — Si sólo uno de los dos está vigente para la fecha no hay conflicto: resuelve el
  vigente. · rojo visto: si

### El PASS, y lo que no aprueba

- **E-24** — `PASS` exige las siete condiciones a la vez, y sacando cualquiera de ellas deja de
  aprobar: las siete probadas una por una desde el mismo caso que sí aprueba. (PASS criteria)
  · rojo visto: si
- **E-25** — `PASS` de O2 no aprueba nada más: ningún valor del resultado es un estado oficial de
  `evaluacion`, el resultado serializado no dice `APPROVED` ni `C2`, ningún productor interno puede
  mover el estado oficial, y ningún **literal operativo** del módulo nombra `APPROVED` ni `C2` — el
  docstring sí los nombra, para decir que `PASS` no es ninguna de las dos.
  (O2 PASS does not imply C2) · rojo visto: si
- **E-26** — Los nueve estados existen con ese nombre exacto, los nueve se emiten desde un caso
  real, y el único que aprueba es `PASS`. (result semantics) · rojo visto: si
- **E-27** — Todo resultado conserva `ES0902`, `6.2`, `§3`, `O2` y la clave compuesta `ES0902.O2`,
  por todos los caminos. · rojo visto: si
- **E-28** — No se crea ni se modifica ningún agente ni ninguna skill, y los dos controles quedan
  declarados e instalados: 35 en el registro, sin archivos sueltos. (no Agent or Skill is created)
  · rojo visto: si

## Cómo se verifica

Los 28 pasan por `.\tests\Invoke-Tests.ps1`. Ninguno lleva la marca `· verificación: lectura`: todo
lo que este cambio construye es determinista.

E-08, E-09, E-13, E-15, E-20, E-24 y E-26 son **invariantes sobre un producto** y no ejemplos: las
cuatro capas del schema con su valor inválido, las cinco responsabilidades de ejecución, las cinco
formas de deducir pertenencia, los siete estados sin resolver, las cuatro formas de vigencia sin
resolver, las siete condiciones de `PASS` sacadas de a una, y los nueve estados emitidos desde un
caso real.

🔴 Los ids y los estados que un escenario verifica van **clavados por literal** en el test, no
recorridos desde la constante del módulo. Es la lección de D8: un bucle sobre la constante se achica
junto con lo que verifica, y renombrar un valor deja el test verde.

🔴 E-24 es el escenario que sostiene a los otros: se construye **un** caso que aprueba y se lo
rompe de siete maneras. Un test que sólo arma casos que fallan pasa con un check que nunca aprueba.

🔴 **Un escenario que dice "el módulo no nombra X" mide el archivo, no el comportamiento, y es un
mal proxy**: prohíbe la línea de prosa que declara la frontera. E-11 y E-25 dicen `literal
operativo` a propósito, y la mitad que importa de los dos es de comportamiento —que no haya camino
de un agente a una autoridad, que ningún valor del resultado sea un estado oficial—.

## Riesgos conocidos

- **La evidencia de autoridad no la produce nadie todavía.** El check la recibe declarada, igual que
  toda la evidencia de G1 a D8 y de ES0902. Mientras el registro esté vacío, toda corrida real da
  `SECURITY_CONTROL_AUTHORITY_UNRESOLVED` — que es el estado correcto y también el que más invita a
  que alguien llene el archivo con la organización que le parece.
- **`reglas/` se sobrescribe en cada `-Update`.** El registro es del proyecto y vive donde el
  instalador copia con `-Force`, igual que `database-profiles.json`. Un proyecto que lo llene y
  actualice el harness pierde lo que escribió. Es una deuda que O2 hereda y no crea, y queda anotada
  en `Pendientes/`.
- **La exigencia de `effectiveTo` va a rozar.** Ninguna acta de asignación de autoridad que se haya
  escrito hasta hoy tiene por qué traer fecha de fin, así que el estado más frecuente en una corrida
  real con registro lleno va a ser `SECURITY_AUTHORITY_CURRENT_STATUS_UNRESOLVED`. Es lo que el
  paquete pide y es lo primero que alguien va a querer aflojar.
