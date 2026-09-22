# G1: la primera regla de §7.1 que se puede ejecutar

**Estado:** construido · **Fecha:** 2026-09-18

## Qué problema resuelve

La matriz clasifica las 24 reglas y declara 36 policies y 34 checks. **Ninguno existe.** Todo plan
reporta setenta controles `DECLARED_POLICY_NOT_INSTALLED` y `DECLARED_CHECK_NOT_INSTALLED`, que es
el estado honesto de un harness que clasificó antes de construir — y que sólo deja de ser honesto
el día que nadie los construye.

G1 es el primero. Dice que un desarrollo tiene que usar herramientas y versiones homologadas por
la ASI, y hasta ahora el harness no tenía con qué contestarlo: el Anexo II del estándar —142
tecnologías con sus versiones— no estaba en ningún lado.

Además hace falta algo que todavía no existe: **un lugar donde conste qué control está instalado**.
Sin eso, "instalado" es una afirmación de quien lo dice, y `controles_no_instalados` no tiene
contra qué comparar.

## Qué queda afuera

- **Detectar qué tecnologías usa un proyecto.** El inventario entra como dato. Deducirlo de un
  `package.json`, un `pom.xml` y un `requirements.txt` es un detector con sus propias trampas —un
  paquete transitivo no es una tecnología elegida— y merece su propio cambio. Sin inventario, G1
  contesta `UNRESOLVED`, no "cumple".
- **Los otros 68 controles.** Se construyen de a una regla. G2 es el siguiente y ya tiene pedido.
- **Las reglas de P1.** Framework obligatorio, prohibición de desarrollo vanilla y gestor de
  paquetes de Node son de P1, no de G1. G1 contesta si una tecnología y su versión están
  homologadas, y nada más. El propio paquete lo dice: *"G1 must not duplicate those P1 controls"*.
- **Decidir por la ASI.** Una tecnología que no está en el Anexo II no se aprueba ni se rechaza:
  es `ASI_EVALUATION_REQUIRED`. El harness no homologa.
- **El bloqueo "dos estándares atrás".** El Anexo II instalado es el de 6.3 y no trae historia. Sin
  catálogo histórico no se puede afirmar que una versión está dos estándares atrás, así que ese
  bloqueo exige evidencia y no se infiere.
- **Los ejecutores de policy.** Una policy es un contrato que restringe; su aplicación en tiempo de
  ejecución es del bloque de ejecución, que no existe.

## Las decisiones, y por qué

### Un registro de controles, con la misma forma que el de agentes

`reglas/control-registry.json` declara qué controles hay, de qué tipo y de qué regla vienen; el
disco diagnostica. Es la misma lección de `agent-registry`: un archivo que aparece solo no da de
alta un control, y un control declarado sin archivo es un hueco que se ve.

Nace con **dos tipos**, `POLICY` y `CHECK`, y con lugar para el tercero: G2 trae `REVIEW`, y el
pedido de G2 pide explícitamente extender este registro en vez de abrir uno paralelo.

### Los checks normativos no son los checks del hook

El harness ya tiene checks —`dev-api-rutas`, `dev-dependencias`— que corren en `PreToolUse`, con su
contrato de tres salidas, exit 0 siempre y presupuesto de latencia. Un check normativo de §7.1 es
otra cosa: se evalúa contra evidencia, devuelve estados con nombre y nadie lo corre en cada
herramienta. Viven separados —`controles/checks/`— y no entran a `roster.json`. Meterlos en el
mismo cajón sería heredarles un contrato que no pueden cumplir y confundir dos capas que sólo
comparten la palabra.

### Ocho estados, y ningún booleano antes de tiempo

`HOMOLOGATED`, `DEPRECATED_TOLERATED`, `NOT_HOMOLOGATED`, `ASI_EVALUATION_REQUIRED`,
`TOOLCHAIN_AUXILIARY_REVIEW`, `VERSION_CONTEXT_REQUIRED`, `VERSION_HISTORY_REQUIRED`,
`PROVIDER_VERSION_REQUIRED` y `UNRESOLVED`. El paquete lo pide con todas las letras: *"do not
reduce all G1 outcomes to a naive boolean before preserving the evidence and normative reason"*.
Un `false` no distingue "no está homologada" de "no sabemos todavía", y son decisiones opuestas.

### Deprecada no es homologada

El Anexo II lista, por tecnología, versiones homologadas **y** versiones deprecadas. Una deprecada
se tolera con observación formal de actualización; no pasa a ser homologada y no desaparece del
reporte. Es tolerancia de despliegue, no homologación vigente.

### El parche sube dentro de su rama, y nada más

Homologada `8.2.30` significa que `8.2.30` y `8.2.31` valen, y que `8.2.29` no. Una rama distinta
—`8.1`, `8.4`— no se vuelve válida sola: la menor no listada es `NOT_HOMOLOGATED` y la mayor no
listada es `ASI_EVALUATION_REQUIRED`, porque nadie la evaluó todavía.

### `latest` no es una versión homologada

No hay ninguna entrada del Anexo II que diga "la última". Una dependencia declarada como `latest`,
`*` o una rama sin fijar no se puede contrastar contra nada: `UNRESOLVED`.

### El calificativo es parte de lo que se compara

*Nota del 2026-09-22.* El refutador encontró que el calificativo se conservaba en el resultado pero
no entraba a la comparación: `1.1.0 EE` contra la homologada `1.1.0 CE` daba `HOMOLOGATED`, y
`19c (LTR)`, la única entrada LTR del Anexo II, no se podía leer. E-17 dice que el calificativo "no
se recorta al comparar", y no dice más que eso. Después de cinco pasadas del refutador, la autora
de la spec ratificó el 2026-09-22 **un solo orden de evaluación**, que reemplaza las decisiones
sueltas. Donde la spec calla, lo que se eligió nunca homologa.

**El orden** *(ratificado por la autora de la spec el 2026-09-22)*:

1. **La forma.** Lo que no está escrito como lo escribe el Anexo II es `UNRESOLVED`, dentro o fuera
   de cualquier rama. La forma canónica es: el número, un sufijo pegado en minúscula si lo tiene
   (`19c`) y, si hay calificativo, **un** espacio y el calificativo en mayúscula (`1.1.0 CE`,
   `6.0 SP1`, `8.2.30 LTS`), o `(LTS)` / `(LTR)` con un espacio o sin espacio (`19.2.18 (LTS)`,
   `19.2.18(LTS)`). Es `UNRESOLVED` todo lo demás:
   - la minúscula (`1.1.0 ce`, `php 7.4.0 lts`);
   - el calificativo pegado (`1.1.0CE`, `19C`);
   - la edición o el service pack entre paréntesis (`1.1.0 (CE)`, `6.0(SP1)`);
   - el paréntesis suelto (`1.1.0 CE)`, `19.2.18 (LTS`);
   - el número con cero adelante (`SP01`);
   - dos espacios, un tabulador, o cualquier otro espacio que no sea uno solo antes del
     calificativo, incluso adelante o atrás de la versión.
2. **El calificativo contra una rama listada.** Si el número cae en una rama listada, en su piso,
   arriba **o abajo**, el calificativo se mira antes que el número:
   - Es `UNRESOLVED` un calificativo de soporte que la tecnología no usa: `php 8.2.28 LTS`,
     `angular 19.2.14 (LTR)`, `dotnet 8.0.19 (LTR)`, `cib-seven 1.1 LTS`.
   - También es `UNRESOLVED` uno de otro tipo que el del catálogo para esa rama: `jws 6.0 CE` y
     `jws 6.1 CE`, `jws 6.1 SP1`, `cib-seven 1.1.0 SP1`, `X1`, `LTS1`.
   - Un calificativo sólo da `NOT_HOMOLOGATED` cuando es otra edición del mismo tipo (`EE` contra
     `CE`) o un service pack anterior.
3. **Recién entonces la rama y el número**, como hasta ahora. Fuera de toda rama listada, un
   calificativo canónico no cambia nada: `php 7.4.0 LTS` es `NOT_HOMOLOGATED` y `php 9.0.0 LTS` es
   `ASI_EVALUATION_REQUIRED`, igual que sin calificativo.

**Las seis decisiones ratificadas antes, el mismo día, y dónde quedan en el orden:**

- *La deprecada con el calificativo de soporte que su tecnología usa se tolera igual que sin él*
  (`angular 19.2.15 (LTS)`, `django 5.2.6 (LTS)`, `dotnet 8.0.20 (LTS)` son `DEPRECATED_TOLERATED`).
  El paso 2 no objeta y el paso 3 decide. La subsume la siguiente.
- *Un calificativo de soporte que la tecnología usa no cambia el artefacto en ninguna comparación*
  (`dotnet 9.0.12 (LTS)` y `moodle 5.1.1 (LTS)` son `HOMOLOGATED`; `dotnet 9.0.10 (LTS)` y
  `9.0.11 (LTS)` son `DEPRECATED_TOLERATED`). Es parte del paso 2.
- *Un calificativo de soporte que la tecnología no usa es `UNRESOLVED` en toda comparación contra
  una rama listada.* Es el paso 2, que ahora dice expresamente que eso vale también por debajo del
  piso.
- *El calificativo en minúscula es `UNRESOLVED`.* Lo subsume el paso 1.
- *La rama primero: fuera de toda rama listada, el calificativo no cambia nada.* Es el paso 3, y
  vale sólo para una forma canónica: una no canónica la resuelve antes el paso 1 (`php 7.4.0 lts`
  es `UNRESOLVED`, no `NOT_HOMOLOGATED`).
- *La edición o el service pack entre paréntesis es `UNRESOLVED`.* Lo subsume el paso 1.

**Lo que decidió quien construyó**, sin ratificar, y que puede cambiar quien escribe la spec:

- **`LTS` y `LTR` sin declarar homologan.** Nombran la línea de mantenimiento de un número que ya
  identifica el artefacto: `19.2.18` de Angular es el mismo paquete con `(LTS)` o sin él, y Oracle
  `19c` sin `(LTR)` es la `19c (LTR)` del catálogo y da `HOMOLOGATED`. El resultado lleva el
  calificativo del catálogo.
- **No declarar la edición o el service pack que el catálogo fija es `UNRESOLVED`**:
  `cib-seven 1.1.0`, `jws 6.0`.
- **El service pack no sube solo.** `6.0 SP2` es posterior a lo listado y nadie lo evaluó:
  `ASI_EVALUATION_REQUIRED`, igual que una rama mayor. `SP0` es canónico (no tiene cero
  adelante) y, contra `SP1`, es un service pack anterior: `NOT_HOMOLOGATED`. La regla "el parche
  sube dentro de su rama" habla del número y no del service pack; extenderla es una decisión de
  quien escribe la spec.
- **El sufijo pegado es parte del número.** `19c (LTR)` es la versión `19c` con calificativo
  `LTR`. `19` no dice cuál 19 es y queda `UNRESOLVED`; `21c` es una rama posterior
  (`ASI_EVALUATION_REQUIRED`) y `18c` una anterior (`NOT_HOMOLOGATED`).

### Lo que el catálogo no fija, el catálogo lo dice

Tres formas de "no hay número acá", y cada una tiene su estado: `CONTEXT_DEPENDENT` y
`FRAMEWORK_DEPENDENT` devuelven `VERSION_CONTEXT_REQUIRED` —hace falta saber contra qué framework—
y `PROVIDER_ASSIGNED_BY_DGSEI` devuelve `PROVIDER_VERSION_REQUIRED`. Son seis entradas de 142, y
las seis se romperían si se las tratara como si les faltara el dato.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/reglas/annex-ii-technology-catalog.json` | El Anexo II como dato: 142 tecnologías, sus versiones homologadas y deprecadas, su regla de versión y su página |
| `comun/schemas/annex-ii-technology-catalog.schema.json` | Su contrato, en el subconjunto soportado |
| `harnesses/desarrollo/reglas/control-registry.json` | Qué controles normativos existen, de qué tipo y de qué regla |
| `comun/schemas/control-registry.schema.json` | Su contrato |
| `harnesses/desarrollo/bin/orquestacion/controles.py` | El registro de controles: carga, valida, diagnostica y contesta qué está instalado |
| `harnesses/desarrollo/controles/checks/technology-homologation.py` | Evalúa una tecnología contra el Anexo II |
| `harnesses/desarrollo/controles/checks/technology-version-compliance.py` | Evalúa su versión contra la rama homologada |
| `harnesses/desarrollo/controles/policies/approved-technology-required.md` | El contrato de la policy, en inglés |
| `harnesses/desarrollo/controles/policies/homologated-version-required.md` | Ídem |
| `harnesses/desarrollo/bin/orquestacion/matriz.py` | `controles_no_instalados` pasa a consultar el registro de controles |
| `docs/normativa-7.1.md` | El tipo de control, el registro y el ciclo de una regla que se construye |
| `tests/casos/24_g1_tecnologias.py` | Los escenarios de este cambio |

## Escenarios verificables

Entre paréntesis, el `G1-nn` del pedido que cubre cada uno.

### El catálogo

- **E-01** — El catálogo carga y valida contra su schema. (G1-01) · rojo visto: si
- **E-02** — Su fuente es ES0901 6.3, Anexo II, y una de otra versión no se carga. (G1-02)
  · rojo visto: si
- **E-03** — Las 142 entradas tienen id único, y una tecnología se resuelve por su id o por
  cualquiera de sus alias. · rojo visto: si

### La versión dentro de su rama

- **E-04** — La versión homologada exacta pasa: `HOMOLOGATED`. (G1-03) · rojo visto: si
- **E-05** — Un parche mayor en la misma rama pasa. (G1-04) · rojo visto: si
- **E-06** — Un parche menor en la misma rama no pasa: `NOT_HOMOLOGATED`. (G1-05)
  · rojo visto: si
- **E-07** — Una rama menor que no está listada no pasa. (G1-06) · rojo visto: si
- **E-08** — Una rama mayor que no está listada es `ASI_EVALUATION_REQUIRED`, no un rechazo.
  (G1-07) · rojo visto: si
- **E-09** — Dos ramas homologadas de la misma tecnología se evalúan por separado: estar en una no
  valida a la otra. (G1-16) · rojo visto: si
- **E-10** — `latest`, `*` o una versión que no se puede comparar devuelven `UNRESOLVED`, nunca
  `HOMOLOGATED`. · rojo visto: si

### Deprecadas e historia

- **E-11** — Una versión listada como deprecada es `DEPRECATED_TOLERATED` y lleva su observación de
  actualización. (G1-08) · rojo visto: si
- **E-12** — Deprecada no se convierte en homologada en ningún camino. (G1-09)
  · rojo visto: si
- **E-13** — El bloqueo por "dos estándares atrás" exige evidencia histórica: sin catálogo
  histórico devuelve `VERSION_HISTORY_REQUIRED` y no bloquea por inferencia. (G1-10)
  · rojo visto: si

### Lo que el catálogo no fija

- **E-14** — Una tecnología que no está en el Anexo II es `ASI_EVALUATION_REQUIRED`: el harness no
  la aprueba ni la rechaza. (G1-11) · rojo visto: si
- **E-15** — Una entrada `FRAMEWORK_DEPENDENT` o `CONTEXT_DEPENDENT` devuelve
  `VERSION_CONTEXT_REQUIRED`, y con el contexto del framework declarado resuelve. (G1-14)
  · rojo visto: si
- **E-16** — Una entrada `PROVIDER_ASSIGNED_BY_DGSEI` devuelve `PROVIDER_VERSION_REQUIRED`.
  (G1-15) · rojo visto: si
- **E-17** — Los calificativos `LTS`, `LTR`, `SP` y `CE` se conservan en el resultado y no se
  recortan al comparar. (G1-17) · rojo visto: si
  *Nota del 2026-09-22:* lo que "no se recortan al comparar" quiere decir caso por caso está en
  "El calificativo es parte de lo que se compara", ordenado por el orden de evaluación ratificado
  ese día. El rojo se vio primero con el código anterior (fallaban los quince casos nuevos de LTR,
  edición y service pack) y después con una mutación por clase del orden: forma, calificativo
  contra la rama (incluido por debajo del piso) y rama primero para lo canónico.

### La cadena de herramientas

- **E-18** — Una auxiliar declarada como tal es `TOOLCHAIN_AUXILIARY_REVIEW`: no se homologa
  individualmente. (G1-12) · rojo visto: si
- **E-19** — Una herramienta desconocida **no** se clasifica como auxiliar en silencio: sigue
  siendo `ASI_EVALUATION_REQUIRED`. (G1-13) · rojo visto: si

### El registro de controles

- **E-20** — El registro declara los cuatro controles de G1 con su tipo y su regla, y valida
  contra su schema. · rojo visto: si
- **E-21** — Un control declarado sin su archivo es un hueco; un archivo que el registro no declara
  no se adopta. · rojo visto: si
- **E-22** — `controles_no_instalados` deja de reportar los cuatro de G1 **sin que la matriz
  cambie una línea**, y sigue reportando los 66 que faltan. (G1-21 del pedido de G2)
  · rojo visto: si
  *Nota del 2026-09-22:* 66 era la cuenta el día que se construyó G1 —70 declarados menos los
  cuatro de G1—. Después se instalaron las reglas siguientes y la cuenta bajó, que es justamente lo
  que la matriz tiene que permitir sin cambiar. Una cantidad literal de faltantes se rompe con cada
  regla que se instala y deja de probar algo, así que la aserción pasó a ser estructural: los
  cuatro de G1 están pedidos y no faltan; la fila de G1 declara exactamente
  `approved-technology-required`, `homologated-version-required`, `technology-homologation` y
  `technology-version-compliance`; la matriz entera sigue declarando 36 policies, 34 checks y 2
  reviews; y lo que se reporta como faltante es exactamente lo que la matriz declara menos lo que
  el registro declara con su archivo en disco, calculado aparte leyendo los dos JSON. El literal
  que no cambia es el de la matriz, no el de lo que falta.
- **E-23** — Los checks normativos no entran al `roster.json` ni al contrato de los checks del
  hook: son otra capa y no comparten registro. · rojo visto: si
  *Nota del 2026-09-22:* la mitad del hook se prueba así: `post-tool-use.py` corre
  `<harness>/checks`; `install.ps1` llena ese directorio sólo desde `comun/checks` y
  `harnesses/<id>/checks`; ninguno de los dos checks de G1 está ahí con la regla de descubrimiento
  del runner, y ninguno tiene `verificar`, que es el contrato del hook.

### Límites y trazabilidad

- **E-24** — G1 no verifica nada de P1: ni framework obligatorio, ni desarrollo vanilla, ni gestor
  de paquetes de Node. (G1-18) · rojo visto: si
- **E-25** — Todo resultado conserva la tupla `ES0901 / 6.3 / 7.1 / G1`. (G1-19)
  · rojo visto: si
- **E-26** — El mismo inventario contra el mismo catálogo da el mismo resultado. (G1-20)
  · rojo visto: si

## Cómo se verifica

Los 26 pasan por la suite. Comparar una versión contra una rama, buscar un id en un catálogo y
decidir entre ocho estados son operaciones de dato; ninguna necesita un modelo, y el pedido lo
exige: `G1-20` es justamente que la misma entrada dé la misma salida.

Los casos negativos —otra versión del estándar, una entrada inventada, un control declarado sin
archivo— se arman con catálogos y registros fabricados en memoria. El catálogo instalado no se
rompe para probar que el validador anda.

## Riesgos conocidos

- **Sin inventario, G1 no dice nada de un proyecto real.** Los checks evalúan lo que se les pasa, y
  hoy nadie produce la lista de tecnologías. Es el mismo hueco que las señales de la matriz, y se
  destraba con el mismo trabajo.
- **El Anexo II es una foto de 6.3.** El día que salga 6.4, el catálogo queda viejo y nada lo
  detecta solo: la comparación de versión del estándar avisa si alguien carga otro, pero no avisa
  si el estándar cambió y el catálogo no.
- **La tolerancia de la ASI no es mecánica.** El propio Anexo II dice que la ASI puede rechazar
  incluso dentro de la ventana tolerada por vulnerabilidad crítica o incompatibilidad. Eso no se
  puede comprobar acá: el estado dice "tolerada", no "aprobada".
- **142 entradas transcriptas de un PDF.** Un número mal copiado se vuelve una homologación falsa,
  y ningún test lo puede contradecir. La página de cada entrada queda en el dato para que sea
  auditable contra el estándar.
