# P1 — Frameworks homologados, nada de lenguaje puro, y NPM en Node

**Estado:** verificado y cerrado · **Fecha:** 22-09-2026 · **Regla:** ES0901 6.3 §7.1 P1

## Qué problema resuelve

P1 es la primera regla de **programación** que se instala, y la primera regla `ALWAYS` con
controles desde G1 y G2. Son **cinco controles** —tres policies y dos checks—, la segunda fila más
grande de las 24 después de D7.

La regla citable son **tres cláusulas** bajo el mismo id, pág. 13:

> `ES0901-7.1-P1` — *"Todo desarrollo debe realizarse utilizando frameworks homologados en este
> documento. No se permite el uso del lenguaje puro ('vanilla') sin el soporte de su respectivo
> framework. Las bibliotecas o componentes de bajo nivel podrán utilizarse únicamente cuando estén
> integrados de forma indirecta a través del framework correspondiente (por ejemplo, conectores de
> base de datos usados por un ORM)."*

> `ES0901-7.1-P1.node` — *"En desarrollos que utilicen tecnologías basadas en Node.js (como Angular,
> React o NestJS), se establece que el administrador de paquetes permitido es NPM (Node Package
> Manager). No está permitido el uso de YARN u otras alternativas, a fin de garantizar la
> compatibilidad y trazabilidad de dependencias en los entornos de GCABA."*

> `ES0901-7.1-P1.plataformas` — *"Para ERP, CRM, FSM, etc., su uso está habilitado bajo los
> lineamientos propios de cada plataforma, siempre que no contradigan los principios contenidos en
> este documento."*

La matriz tiene **una** fila `P1`, y las dos cláusulas derivadas **heredan** su clasificación —lo
resuelve `matriz.regla` desde que la matriz se construyó, y está testeado—. Los cinco controles que
esa fila declara **no existen**.

Y hay tres trampas propias de esta regla.

**La primera: que el framework esté en el manifiesto no dice que gobierne la aplicación.** Es la
forma más común del defecto de P1 y la más fácil de dejar pasar: el paquete instalado, un módulo
manejado por el framework, un README que lo nombra, y al lado un servidor escrito a mano que atiende
la mitad del tráfico. Un check que mire la dependencia se pone verde sobre una aplicación vanilla.

**La segunda: no todo archivo del repositorio es una aplicación entregada.** Un script de build, un
generador, un lanzador de migraciones, un helper de CI: si P1 los trata como desarrollo vanilla,
falla sobre proyectos correctos y alguien lo apaga. Y si los saca por su nombre, se le escapa el
script que *sí* es parte del runtime entregado. La clasificación se declara, no se adivina.

**La tercera: la plataforma de negocio no es una exención del proyecto.** *"Usamos SAP"* no saca a
los tres servicios propios de la obligación de framework. La cláusula habilita un **camino
gobernado**, no una puerta de salida.

Y una frontera que no es trampa: **P1 no homologa nada y no compara versiones.** Eso es G1, está
construido y verificado, y tiene adentro la comparación de parche dentro de la rama, la tolerancia a
lo deprecado y la regla de los dos estándares. Reimplementarlo acá sería tener dos respuestas
distintas a la misma pregunta.

## Qué queda afuera

- **La homologación y la comparación de versiones.** Son de G1. P1 reusa el catálogo del Anexo II
  —el mismo archivo, no una copia— y **consume el veredicto de G1 como evidencia declarada**; si no
  está, `G1_EVIDENCE_REQUIRED`. Ninguna función de comparación de versiones se llama, se copia ni se
  nombra desde P1.
- **Un segundo catálogo de tecnologías.** Ningún artefacto de P1 lleva una lista de frameworks ni de
  versiones. El catálogo es `annex-ii-technology-catalog.json` y es uno solo.
- **Una señal de aplicabilidad.** P1 es `ALWAYS` con cero señales, y no se agregan
  `nodePresent`, `businessPlatformPresent` ni `frameworkPresent`. Node y plataforma de negocio son
  **ramas internas de evaluación**, no reglas normativas nuevas.
- **Una fila nueva en la matriz.** `P1.node` y `P1.plataformas` heredan de `P1` y no se duplican sus
  policies ni sus checks bajo un id hijo.
- **Una versión de NPM.** El estándar dice que el administrador permitido es NPM y no fija versión.
  La versión de Node es de G1.
- **Una lista de administradores de paquetes prohibidos.** El estándar dice *"NPM"* y *"no está
  permitido YARN u otras alternativas"*: lo que el check compara es contra **el permitido**, y todo
  lo demás es alternativa. Una lista de prohibidos envejece y deja entrar a la número cuatro.
- **Ejecutar una aplicación.** Este cambio no levanta nada, no instala dependencias y no corre un
  build. La evidencia entra como dato, igual que en D4, D6, D7 y D8.
- **Un agente y una skill.** Los dos dueños de la fila —`dev-architecture` y `dev-devops`— no se
  tocan, la fila no declara skills, y este cambio no crea, modifica ni renombra ninguna de las dos
  cosas.
- **Un módulo compartido.** Los tres ayudantes de evidencia siguen duplicados; el pendiente ya está
  escrito para `harness-staff-engineer` y este cambio lo empeora en uno más y lo dice.

## Las decisiones, y por qué

### P1 no tiene compuerta de aplicabilidad, y eso cambia la forma del check

Los cinco checks condicionales instalados abren igual: señal sin resolver, señal en FALSE, objetivo.
P1 no: es `ALWAYS`, así que **nunca contesta `NOT_APPLICABLE`**. Lo que sí tiene es una rama que
puede no aplicar:

```
P1 entero                  ALWAYS. Siempre se evalua
la clausula de Node        NOT_RELEVANT cuando no hay superficie Node
la clausula de plataforma  se evalua cuando hay una superficie de plataforma declarada
```

🔴 `NOT_RELEVANT` y `NOT_APPLICABLE` **no son la misma palabra y no significan lo mismo**. La segunda
dice *"esta regla no te toca"*; la primera dice *"esta regla te toca y esta cláusula no tiene sujeto
en tu proyecto"*. Un proyecto sin Node sigue debiendo frameworks homologados.

### P1 consume el veredicto de G1, no lo vuelve a calcular

```
P1 resuelve   la identidad del framework contra el Anexo II -el mismo archivo de G1-
P1 consume    el estado que G1 produjo para esa tecnologia, declarado como evidencia
P1 NO hace    comparar versiones, tolerar lo deprecado, contar estandares hacia atras
```

Sin el veredicto de G1 para el framework de una superficie: `G1_EVIDENCE_REQUIRED`. Con un veredicto
que no es `HOMOLOGATED` —lo que la ASI todavía no evaluó, o una versión que no llega— P1 **conserva
ese estado** y no pasa: el problema es de G1 y P1 lo dice sin traducirlo.

🔴 Y es verificable estructuralmente: el check de P1 no nombra ninguna de las funciones de
comparación de `anexo2`, no lleva un literal con forma de versión y no tiene una lista de
tecnologías adentro. Si alguna vez las necesita, lo que hay que hacer es llamar a G1.

### Una superficie es lo que se entrega, y se declara

```
FRAMEWORK_GOVERNED          la gobierna un framework homologado
BUSINESS_PLATFORM_GOVERNED  la gobierna una plataforma estructurada, con su evidencia
AUXILIARY_TOOLING           herramienta auxiliar: no es aplicacion entregada
VANILLA_APPLICATION         lenguaje puro sin el framework que le corresponde
UNRESOLVED                  no se pudo establecer
```

Cinco clases, una por superficie material, con el origen del inventario declarado. Un inventario sin
fuente, sin ids, con una clase desconocida o declarado incompleto deja
`DEVELOPMENT_SURFACE_CLASSIFICATION_UNRESOLVED`.

🔴 **`AUXILIARY_TOOLING` se declara y no se deduce.** Es la misma doctrina que G1 ya fija para la
cadena de herramientas: deducir que algo es auxiliar es la forma más cómoda de sacarse de encima
cualquier superficie incómoda. Y al revés: un script que participa del runtime entregado es una
superficie de aplicación aunque se llame `script`, y el que lo sepa lo declara.

### El framework tiene que gobernar, no estar

Para una superficie `FRAMEWORK_GOVERNED` hacen falta tres cosas, y la tercera es la que casi nunca
está:

```
identidad del framework declarada
el veredicto de G1 para esa tecnologia
evidencia de que la superficie EJECUTA a traves del modelo del framework
```

La tercera entra como evidencia de una clase que prueba —una traza del arranque gobernado, una
revisión del camino de código— y lo que **no** prueba nada está declarado inerte:

```
FRAMEWORK_GOVERNANCE_TRACE   prueba. Es la unica que prueba
CODE_PATH_REVIEW             acompana
HUMAN_CONFIRMATION           acompana

REPOSITORY_DEPENDENCY        inerte: un paquete instalado no es una aplicacion gobernada
PACKAGE_MANIFEST_ENTRY       inerte: aparecer en el manifiesto es lo mismo
SINGLE_MANAGED_MODULE        inerte: un modulo gobernado no gobierna la superficie
PROJECT_DOCUMENTATION        inerte: el README no ejecuta nada
AGENT_STATEMENT              inerte: una opinion con formato de evidencia
```

### El bypass de bajo nivel es una tercera cosa, ni framework ni vanilla

La cláusula del estándar es precisa: un componente de bajo nivel vale **cuando está integrado de
forma indirecta a través del framework**. Entonces cada componente de bajo nivel declarado dice cómo
se usa:

```
THROUGH_FRAMEWORK   detras de la arquitectura que el framework maneja  ->  puede cumplir
DIRECT_REPLACEMENT  usado directamente en lugar del camino del framework  ->  FAIL
UNRESOLVED          no se establecio como se usa  ->  no se resuelve
```

Y no se deduce del nombre del paquete: un conector de base de datos detrás de un ORM y el mismo
conector usado como la arquitectura de persistencia de la aplicación son el mismo paquete y dos
cosas distintas. La forma de uso se declara con evidencia, como todo lo demás acá.

### La plataforma de negocio es un camino, no una exención

Para que una superficie sea `BUSINESS_PLATFORM_GOVERNED` hacen falta **las cuatro**:

```
un entorno de desarrollo estructurado de la plataforma
lineamientos autoritativos, con su fuente y su referencia
la customizacion ocurre adentro de ese entorno
ninguna contradiccion declarada con ES0901
```

Falta alguna de las tres primeras: `BUSINESS_PLATFORM_GOVERNANCE_UNRESOLVED`. Hay una contradicción
declarada: `BUSINESS_PLATFORM_STANDARD_CONFLICT`, y no pasa.

🔴 **El nombre del producto no alcanza**, y la plataforma **no exime a las otras superficies**. Un
proyecto con una customización de plataforma y tres servicios propios evalúa las cuatro superficies,
y las tres propias siguen debiendo framework homologado.

### Se compara contra el permitido, no contra una lista de prohibidos

El estándar nombra uno: NPM. El check compara el administrador **activo** contra ése y nada más, así
que YARN, pnpm, Bun y el que salga el mes que viene son la misma respuesta sin que nadie tenga que
agregarlos. Ningún artefacto de P1 lleva una lista de administradores prohibidos.

### Lo histórico se investiga, no se ignora ni falla solo

```
activo y es NPM                  cumple
activo y no es NPM               FAIL
declarado historico, no activo   se informa como observacion. No falla y no desaparece
sin declarar si esta activo      NODE_PACKAGE_MANAGER_EVIDENCE_UNRESOLVED
dos activos distintos            NODE_PACKAGE_MANAGER_CONFLICT
```

Un `yarn.lock` viejo en el repositorio no es un incumplimiento y tampoco es nada: es una pregunta
—*¿está vivo en el build gobernado?*— y el check la deja escrita en vez de contestarla solo.

### Dos motivos que el pedido lista como estados, y acá son motivos

`VANILLA_RUNTIME_PATH_DETECTED` y `LOW_LEVEL_DIRECT_USE_BYPASS` aparecen en la lista de estados
requeridos del pedido (§12) y **no** aparecen en la lista de estados del check que el propio pedido
adjunta. Acá son **motivos de un `FAIL`**, no estados, y por tres razones:

1. El artefacto que define los estados del check es el check, y su lista no los incluye.
2. Los dos describen **por qué** falla una superficie, no un resultado distinto de fallar: una
   aplicación con las dos cosas no está en dos estados.
3. Como estados serían dos formas de `FAIL` que nadie puede ordenar contra `FAIL`.

Están declarados, son alcanzables, se informan en el resultado y ninguno aprueba. La decisión queda
acá para que se juzgue la decisión y no el silencio.

### Se reutiliza la infraestructura, no se construye una segunda

`matriz.py` resuelve la aplicabilidad y la herencia de cláusulas, `anexo2.py` el catálogo,
`controles.py` el registro y `registro_agentes.resolver_ruteo` el ruteo. No se agrega ningún módulo
de orquestación, no se abre un segundo inventario de controles y no se toca la matriz.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/controles/policies/homologated-framework-required.md` | La policy del framework homologado, con su frontera con G1 y su camino de plataforma |
| `harnesses/desarrollo/controles/policies/vanilla-development-prohibited.md` | La policy del lenguaje puro y del bypass de bajo nivel |
| `harnesses/desarrollo/controles/policies/node-package-manager-npm-only.md` | La policy de NPM, sin versión y sin lista de prohibidos |
| `harnesses/desarrollo/controles/checks/framework-homologation.py` | El check de superficies: nueve estados, inventario, framework, vanilla y plataforma |
| `harnesses/desarrollo/controles/checks/node-package-manager-compliance.py` | El check de Node: ocho estados, activo contra histórico, conflicto |
| `harnesses/desarrollo/reglas/control-registry.json` | Los cinco controles de P1, declarados |
| `docs/normativa-7.1.md` | P1, las tres cláusulas, la frontera con G1 y lo que `NOT_RELEVANT` no es |
| `tests/casos/36_p1_frameworks_homologados.py` | Los escenarios de acá abajo |

La matriz **no se toca**: su fila de P1 ya declara `ALWAYS`, cero señales, los dos agentes, las tres
policies y los dos checks desde que se construyó.

Y se reescriben las afirmaciones que hoy están en verde y dejan de ser ciertas: el conteo de
controles —26 → 31— en `31_d6/E-30`, `32_d5/E-36`, `33_bases/E-32`, `34_d7/E-42` y `35_d8/E-37`, y el
conteo de reglas con todos sus controles construidos —diez → once— en `32_d5/E-36` y `35_d8/E-37`.

## Escenarios verificables

Entre paréntesis, el `P1-nn` del pedido de instalación.

### La fila, las cláusulas y la herencia

- **E-01** — P1 sigue `ALWAYS`, con cero señales, y la fila tiene exactamente las claves que tiene
  toda fila clasificada. (P1-01, P1-02) · rojo visto: si
- **E-02** — Los dos agentes dueños siguen siendo `dev-architecture` y `dev-devops`. (P1-03)
  · rojo visto: si
- **E-03** — Las tres policies y los dos checks son exactamente los que la matriz declara. (P1-04,
  P1-05) · rojo visto: si
- **E-04** — P1 no crea ni referencia ninguna skill: la fila no declara `skills`, siguen siendo 27
  las instaladas, y los nombres que los artefactos mencionan ya están en el registro. (P1-06)
  · rojo visto: si
- **E-05** — `P1.node` hereda la clasificación de P1: mismos agentes, mismas policies, mismos
  checks, y lo declara con `inheritedFrom`. (P1-07) · rojo visto: si
- **E-06** — `P1.plataformas` hereda igual. (P1-08) · rojo visto: si
- **E-07** — No hay filas nuevas en la matriz: siguen siendo 24, ninguna con un punto en el id, y
  los controles de P1 no se duplican bajo un id hijo. (P1-09) · rojo visto: si
- **E-08** — Las tres cláusulas citables existen con su página, apuntan a la regla `P1`, y cada
  una dice **un tramo distintivo de su texto**, clavado por literal: que el largo alcance no es que
  el texto sea el del estándar. (§2) · rojo visto: si

### La frontera con G1

- **E-09** — El catálogo del Anexo II es el mismo archivo que usa G1, P1 **lo lee** —con un catálogo
  vacío la misma tecnología deja de resolver— y no lleva una copia ni una lista de tecnologías
  adentro. (P1-10) · rojo visto: si
- **E-10** — P1 no duplica la lógica de versiones de G1: el módulo no nombra ninguna de las
  funciones de comparación, no declara ningún literal con forma de versión y no tiene una lista de
  tecnologías. (P1-11) · rojo visto: si
- **E-11** — Sin el veredicto de G1 para el framework de una superficie, `G1_EVIDENCE_REQUIRED`.
  (§6) · rojo visto: si
- **E-12** — Un framework que G1 resolvió como no homologado o pendiente de evaluación de la ASI
  conserva ese estado **en el campo estructurado** del resultado de P1 y no pasa en silencio.
  (P1-15) · rojo visto: si

### Las superficies

- **E-13** — Inventario incompleto —sin inventario, sin superficies, sin fuente, con superficies sin
  id, con una clase desconocida, con una clase `UNRESOLVED` o declarado incompleto— deja
  `DEVELOPMENT_SURFACE_CLASSIFICATION_UNRESOLVED`, y nunca `PASS`. (P1-21, P1-36)
  · rojo visto: si
- **E-14** — Las cinco clases de superficie entran en el inventario, nombradas una por una. (§5)
  · rojo visto: si
- **E-15** — Un script auxiliar declarado `AUXILIARY_TOOLING` no se clasifica solo como aplicación
  vanilla y no hace fallar a P1. (P1-20) · rojo visto: si
- **E-16** — Las superficies de un proyecto mixto se evalúan independientemente, y el resultado
  nombra cada una con su estado. (P1-35) · rojo visto: si

### El framework, que tiene que gobernar

- **E-17** — Un framework homologado que gobierna una superficie completa, con traza, da `PASS`.
  (P1-13) · rojo visto: si
- **E-18** — Las cinco clases inertes, una por una, no dan `PASS`: la dependencia, la entrada del
  manifiesto, un módulo gobernado, la documentación y la palabra de un agente. (P1-12)
  · rojo visto: si
- **E-19** — Sin identidad de framework declarada, `FRAMEWORK_CONTEXT_UNRESOLVED`. (P1-14)
  · rojo visto: si

### El lenguaje puro y el bajo nivel

- **E-20** — Una superficie entregada en lenguaje puro da `FAIL` con
  `VANILLA_RUNTIME_PATH_DETECTED`. (P1-16) · rojo visto: si
- **E-21** — El framework instalado y el runtime material esquivándolo da `FAIL`: la traza manda
  sobre lo que la superficie declare. (P1-17) · rojo visto: si
- **E-22** — Un componente de bajo nivel integrado a través del framework puede cumplir. (P1-18)
  · rojo visto: si
- **E-23** — El mismo componente usado directamente en lugar del camino del framework da `FAIL` con
  `LOW_LEVEL_DIRECT_USE_BYPASS`. (P1-19) · rojo visto: si
- **E-24** — La forma de uso de un componente de bajo nivel no se deduce del nombre: sin declararla,
  no se resuelve. (§7) · rojo visto: si

### La cláusula de Node

- **E-25** — Node con el camino activo de NPM puede dar `PASS`. (P1-22) · rojo visto: si
- **E-26** — Node con un camino activo de YARN da `FAIL`. (P1-23) · rojo visto: si
- **E-27** — Node con un camino activo de pnpm da `FAIL`. (P1-24) · rojo visto: si
- **E-28** — Cualquier administrador activo que no sea el permitido da `FAIL`, sea cual sea su
  nombre: es un invariante sobre el producto y no una lista de prohibidos. (P1-25)
  · rojo visto: si
- **E-29** — Con el administrador activo sin establecer, `NODE_PACKAGE_MANAGER_EVIDENCE_UNRESOLVED`.
  (P1-26) · rojo visto: si
- **E-30** — Un artefacto alternativo declarado histórico junto a un camino activo de NPM se
  informa como observación: no se ignora y no falla solo. (P1-27) · rojo visto: si
- **E-31** — Dos administradores activos distintos dan `NODE_PACKAGE_MANAGER_CONFLICT`. (§8)
  · rojo visto: si
- **E-32** — Sin superficie Node, el check de Node queda `NOT_RELEVANT`, que **no** es
  `NOT_APPLICABLE`: P1 sigue aplicando. (P1-28) · rojo visto: si
- **E-33** — P1 no inventa un requisito de versión de NPM: ningún artefacto declara una versión de
  administrador de paquetes, y el módulo no tiene constantes numéricas. (P1-29)
  · rojo visto: si

### La plataforma de negocio

- **E-34** — Una plataforma estructurada con lineamientos autoritativos y sin contradicción puede
  satisfacer el camino de plataforma. (P1-30) · rojo visto: si
- **E-35** — El nombre del producto, solo, no satisface el camino: falta cualquiera de las cuatro
  cosas y queda `BUSINESS_PLATFORM_GOVERNANCE_UNRESOLVED`. (P1-31, P1-32)
  · rojo visto: si
- **E-36** — Un lineamiento de plataforma que contradice a ES0901 da
  `BUSINESS_PLATFORM_STANDARD_CONFLICT` y no pasa. (P1-33) · rojo visto: si
- **E-37** — La plataforma no exime a los servicios propios del mismo proyecto: una superficie
  vanilla al lado de una plataforma gobernada sigue dando `FAIL`. (P1-34)
  · rojo visto: si

### La propagación, el registro y la trazabilidad

- **E-38** — La unidad de trabajo propaga las tres policies y los dos checks exactos, sin señal:
  P1 aparece en las aplicables de una unidad que no declara ninguna. (P1-37)
  · rojo visto: si
- **E-39** — Después de instalar, los cinco controles dejan de figurar como no instalados, son
  treinta y uno los declarados, son once las reglas con todos sus controles construidos, y no queda
  ningún archivo de control sin declarar. (P1-38) · rojo visto: si
- **E-40** — Todo resultado de los dos checks conserva `ES0901 / 6.3 / 7.1 / P1`, en todos sus
  caminos. (P1-39) · rojo visto: si
- **E-41** — Los estados de cada check existen, se alcanzan todos, el único que aprueba es `PASS`, y
  ningún estado sin resolver se convierte en `PASS`. Los dos motivos que el pedido lista como
  estados —`VANILLA_RUNTIME_PATH_DETECTED` y `LOW_LEVEL_DIRECT_USE_BYPASS`— son alcanzables, se
  informan y no aprueban. (§12) · rojo visto: si
- **E-42** — Ningún artefacto de P1 lleva una versión, una lista de tecnologías, una lista de
  administradores de paquetes prohibidos, un localizador de red ni un nombre de producto de
  plataforma; y tampoco los lleva ningún resultado que los checks produzcan. (§4, P1-29, P1-31)
  · rojo visto: si

## Cómo se verifica

Los 42 pasan por `.\tests\Invoke-Tests.ps1`. Ninguno lleva la marca `· verificación: lectura`: todo
lo que este cambio construye es determinista.

E-42 tiene **tres** mitades, como los guards de D6, D7 y D8: los textos limpios, las formas de fuga
**en crudo** y los textos legítimos que **no** tienen que disparar. La tercera mitad de P1 es la más
delicada de las cuatro, porque los artefactos de esta regla **tienen** que poder nombrar a NPM, a
YARN y a las cláusulas del estándar: lo que no pueden llevar es una versión, una lista de
tecnologías o un producto de plataforma.

E-07, E-10, E-13, E-14, E-18, E-28, E-40 y E-41 son **invariantes sobre un producto**: recorren las
24 filas de la matriz, las funciones de comparación de `anexo2`, las siete formas de inventario
incompleto, las cinco clases de superficie, las cinco clases inertes, los administradores que no son
el permitido y todos los caminos de los dos checks. Donde la cobertura es combinatoria, el ejemplo
elegido a mano es el que deja pasar la forma que nadie pensó.

🔴 Las constantes que un escenario verifica van **clavadas por literal** en el test, no recorridas
desde el módulo. Es la lección de D8: un bucle sobre la constante se achica junto con lo que
verifica, y renombrar un valor deja el test verde.

📌 El veredicto no contradijo ningún escenario y dejó tres deudas de verificación, **las tres
cerradas antes de este documento**, y las tres de la misma familia —una aserción que se satisface
con algo más débil que lo que el escenario afirma—:

```
E-08  `len(texto) > 80` lo cumple cualquier prosa inventada   -> un tramo de cada clausula, clavado
E-09  "P1 lo lee" no la sostenia ninguna asercion de E-09     -> con el catalogo vacio, cambia
E-12  `estado in repr(...)` lo satisface el detalle           -> el campo estructurado, igualado
```

## Riesgos conocidos

- **La evidencia de que un framework gobierna una superficie no la produce nadie todavía.** El check
  la recibe declarada, y hoy no hay ningún productor que la arme desde un repositorio. Es la misma
  deuda de G1 a D8, y lo que la destraba es el análisis de impacto.
- **`AUXILIARY_TOOLING` es una puerta de salida declarada.** Una superficie entregada clasificada
  como herramienta auxiliar sale de la verificación con una afirmación de quien la clasificó. El
  check exige que el inventario declare de dónde sale; que la clasificación sea honesta no lo puede
  saber. Es el mismo riesgo que G1 ya tiene con `TOOLCHAIN_AUXILIARY` y está aceptado ahí.
- **`active` de un administrador de paquetes es un dato declarado.** Un `yarn.lock` vivo declarado
  histórico sale del conjunto de incumplimientos con una afirmación. Queda citada y es refutable.
- **P1 depende de que G1 haya corrido.** Sin el veredicto de G1, P1 sale `G1_EVIDENCE_REQUIRED` en
  cualquier proyecto real de hoy, porque el inventario de tecnologías tampoco lo junta nadie.
- **`controles/` no llega a un proyecto instalado.** Con P1 son **treinta y uno** los controles que
  declaran `INSTALLED` y que fuera de este repositorio serían `CONTROL_FILE_MISSING`. Es el ítem 2,
  y este cambio lo empeora en cinco.
- **Los tres ayudantes de evidencia se duplican por cuarta vez.** El pendiente ya está escrito; P1 lo
  empeora y no lo arregla, porque hacerlo acá sería tocar tres cambios ya verificados desde adentro
  de un cuarto.
