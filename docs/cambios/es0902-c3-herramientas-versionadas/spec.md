# ES0902 C3 — las herramientas versionadas y autorizadas, con los controles de G1 y la línea base viva

**Estado:** verificado y cerrado · **Fecha:** 23-09-2026 · **Regla:** ES0902 6.2 §3 C3 · ES0901 6.3 §6.10, §7.1 G1, Anexo II

## Qué problema resuelve

> `ES0902-3-C3` — *"Las aplicaciones deben respetar las herramientas versionadas y autorizadas que
> se indican en el documento Estándar de Desarrollo, en su sección 'Versiones y Herramientas
> aceptadas por la ASI'."*

C3 no trae su propio catálogo: **delega** en el Estándar de Desarrollo. Y el harness ya tiene lo que
ese estándar dice: el Anexo II de ES0901 6.3 como catálogo, y G1 con sus dos policies y sus dos
checks. La línea base de ES0902 ya declaró esos cuatro controles como compartidos —el registro los
tiene con `ES0901.G1`, `ES0902.C3` y `ES0902.Ve1` como fuentes— y el mapa cruzado ya declara la
relación `CONTROL_REUSE`.

Lo que falta son tres cosas, y ninguna es un catálogo:

```
C3 hoy                                    sale por el camino genérico: cuatro controlResults en
                                          PASS la ponen en COMPLIANT
                                    ->    nada mira si el catálogo es del Estándar de Desarrollo
                                          VIGENTE, o de uno que ya fue reemplazado
                                    ->    nada ejecuta los checks de G1 para C3, ni dice cómo se
                                          agrega C3 sin copiar el resultado de G1
```

La primera es la peligrosa. C3 nombra *el* Estándar de Desarrollo, no *ES0901 6.3*: el día que se
cargue un ES0901 6.4 y el Anexo II siga siendo el de 6.3, C3 seguiría aprobando contra un catálogo
reemplazado, en silencio.

## Qué queda afuera

- **Un segundo catálogo, un segundo inventario, un segundo comparador de versiones.** No se crea
  `es0902-technology-catalog.json` ni nada parecido. El catálogo es `annex-ii-technology-catalog.json`,
  la comparación es `anexo2.py` y los checks son los de G1.
- **Copias de las policies o los checks de G1 para C3.** Se reusan los cuatro, con los mismos ids.
- **Una migración del registro.** Ya soporta varias fuentes (`normativeSources`) y los cuatro
  controles ya declaran `ES0901.G1` y `ES0902.C3`. Se verifica; no se toca.
- **Un productor de inventario.** El inventario de tecnologías lo recibe el check de G1 y lo recibe
  C3, con la misma forma. Sin inventario, C3 queda sin resolver.
- **Ve1.** Ya declara los mismos cuatro controles y la misma relación en el mapa. No se le escribe
  algoritmo: cuando se instale se comparan las semánticas.
- **Seguridad.** C3 no escanea vulnerabilidades, no mira configuración, no es C2, ni Vu7, ni Vu10,
  ni G2, ni una aprobación a producción.
- **Un agente, una skill, una review, una señal.**

## Las decisiones, y por qué

### C3 entra en `ALGORITMOS`, y es la décima

El camino genérico aprobaría C3 con cuatro `controlResults` en `PASS` sin mirar si el catálogo es
del estándar vigente. El paquete pide lo contrario: *"el baseline/catálogo/fuente de control tiene
que migrarse antes de que C3 pueda seguir pasando"*. Eso es una puerta que no está en ningún
control —es la relación entre el estándar vigente y el catálogo instalado—, así que la tiene que
abrir la regla. Es la misma razón por la que O1 entró: el camino genérico no puede contestarla.

La consecuencia se declara: `ALGORITMOS` pasa de nueve a diez, y se reescribe `40_es0902_o2/E-04`,
que contaba nueve.

### El módulo es nuevo, porque `seguridad.py` no puede saber del Anexo II

`37_es0902/E-43` prohíbe que `seguridad.py`, `evaluacion.py` y `cruzada.py` nombren o importen el
Anexo II: el reuso es de los controles declarados, no de la implementación copiada. El resolvedor
y la agregación de C3 viven en `bin/orquestacion/estandar_de_desarrollo.py`, que sí importa `anexo2` y
`linea_base`, y `ALGORITMOS` lo delega por nombre como ya hace con `linea_base` para O1.

### El resolvedor de la línea base

```
1. el Estándar de Desarrollo vigente  gcba-it-normative-baseline.json: las fuentes ES0901 LOADED.
                                      Una sola -> esa. Varias -> la única CURRENT; si no hay una
                                      sola, DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_UNRESOLVED
2. el catálogo                        annex-ii-technology-catalog.json, leído crudo. Ausente o
                                      ilegible -> TECHNOLOGY_CATALOG_UNAVAILABLE
3. que el catálogo sea de ese         source.standard = ES0901, source.version = la vigente, y un
   estándar                           status COMPLETE_FOR_ANNEX_II_V<versión>. Si no ->
                                      DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_MISMATCH
4. que los controles sean de ese      los checks de G1 están escritos para una versión del Anexo
   estándar                           (anexo2.VERSION_ESPERADA): distinta de la vigente ->
                                      DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_MISMATCH
5. que los controles estén            los cuatro INSTALLED en el registro y con archivo. Si no ->
                                      SHARED_TECHNOLOGY_CONTROL_UNAVAILABLE
```

El paso 4 es el que hace que C3 no quede congelado en 6.3: cargar un ES0901 6.4 y un Anexo II 6.4
no alcanza si el comparador sigue siendo el de 6.3. Los tres tienen que moverse juntos.

El catálogo se lee **crudo** y no con `anexo2.cargar`, que levanta ante una versión distinta de la
que espera: el resolvedor tiene que poder decir *cuál* es la diferencia, no sólo que la hay.

### Una ejecución, dos agregaciones

```
inventario  ->  technology-homologation      una vez por tecnología
            ->  technology-version-compliance una vez por tecnología
            ->  los resultados compartidos, anotados con sus fuentes
                   ├─ agregado de ES0901.G1
                   └─ agregado de ES0902.C3   (además, detrás de la puerta de la línea base)
```

La agregación es la misma función para las dos reglas y **no lee el resultado de la otra**: recibe
los resultados compartidos. Por eso G1 en `PASS` con la línea base en `MISMATCH` deja a C3 sin
resolver, y G1 en `FAIL` no pone a C3 en nada que no salga de sus propios controles.

### Cómo se agrega

Cada tecnología trae dos estados, el de homologación y el de versión, y se agregan sin reescribirse:

```
algún NOT_HOMOLOGATED                                        NON_COMPLIANT
algún estado sin resolver -ASI_EVALUATION_REQUIRED,           UNRESOLVED, con los estados
  TOOLCHAIN_AUXILIARY_REVIEW, VERSION_CONTEXT_REQUIRED,
  VERSION_HISTORY_REQUIRED, PROVIDER_VERSION_REQUIRED,
  UNRESOLVED-
todo HOMOLOGATED y alguno DEPRECATED_TOLERATED               COMPLIANT_WITH_OBSERVATIONS
todo HOMOLOGATED                                             COMPLIANT
inventario ausente o vacío                                   UNRESOLVED, TECHNOLOGY_INVENTORY_UNAVAILABLE
```

`DEPRECATED_TOLERATED` no se reescribe: la tecnología sale con ese estado y la regla con
observaciones. Un inventario vacío no es un proyecto sin tecnologías: es un inventario que nadie
llenó.

### Lo que llega en la evidencia no reemplaza lo que el módulo resuelve

El primer pase del refutador contradijo tres escenarios por una sola causa: `regla_c3` tomaba
como verdad la `developmentStandardBaseline` y los `sharedControlResults` que llegaban en la
evidencia. Una base forjada que decía `RESOLVED` aprobaba con la línea base instalada desfasada, y
unos resultados compartidos forjados aprobaban sin inventario o pisaban uno real.

```
developmentStandardBaseline en la evidencia   sólo puede RESTRINGIR: la instalada se resuelve
                                              igual, y C3 pasa sólo si las dos están resueltas y
                                              son de la misma versión
sharedControlResults en la evidencia          no se lee: no hay cómo saber que salieron de los
                                              checks de G1. C3 ejecuta los suyos
compartidos por la API (evaluar_c3)           para quien ya ejecutó sobre ESTE inventario: tienen
                                              que coincidir tecnología por tecnología, y cada fila
                                              traer las dos mitades, del control que las produce
```

Y los cuatro de la misma clase, con la misma regla —lo que no se reconoce no se descarta—:

- **La línea base normativa:** una fuente ilegible, un ES0901 con un `status` o una `currency` que
  no se reconocen, o un ES0901 declarado reemplazado aunque sea el único, dejan la línea base sin
  resolver.
- **La agregación:** una fila sin alguna de sus dos mitades, con un estado que G1 no emite o de
  otro control, no se agrega sobre la mitad.
- **Lo que rompía:** un contexto de framework que no es un diccionario, o un check que se cae,
  dejan C3 sin resolver en vez de tirar abajo el estándar entero.
- **La unidad de trabajo:** proyecta sólo un resultado de `ES0902.C3` con un estado que C3 emite,
  y la base que lleva es la instalada, no la que dice el resultado.

### La unidad de trabajo lleva referencias

`standards.ES0902.rules.C3` lleva el resultado, la línea base (`ES0901` y su versión), los ids de
los cuatro controles compartidos y las referencias de la evidencia. No lleva el catálogo.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/bin/orquestacion/estandar_de_desarrollo.py` | El resolvedor, la ejecución compartida, la agregación y `regla_c3` |
| `harnesses/desarrollo/bin/orquestacion/seguridad.py` | `C3` en `ALGORITMOS`, delegado |
| `harnesses/desarrollo/bin/orquestacion/normativa.py` | `rules.C3` en la unidad |
| `harnesses/desarrollo/reglas/es0902-c3-governance.md` | El gobierno, como vino |
| `harnesses/desarrollo/reglas/es0902-c3-development-standard-technology-binding.md` | La ligadura, como vino |
| `harnesses/desarrollo/reglas/development-standard-technology-baseline-resolver.md` | El resolvedor, como vino |
| `harnesses/desarrollo/reglas/es0902-c3-control-source-binding.json` | La ligadura como dato, como vino |
| `docs/seguridad-es0902.md` | C3 |
| `tests/casos/43_es0902_c3_herramientas_versionadas.py` | Los escenarios |

El registro de controles **no se toca**: los cuatro ya están con sus fuentes. Se reescribe
`40_es0902_o2/E-04` —diez algoritmos— y cualquier conteo que dependa de C3 saliendo por el camino
genérico.

## Escenarios verificables

`E-nn` es `C3-nn` del pedido.

### La fila

- **E-01** — La clave es `ES0902.C3`, en la matriz y en el resultado. · rojo visto: si
- **E-02** — C3 sigue `ALWAYS`. · rojo visto: si
- **E-03** — C3 tiene cero señales. · rojo visto: si
- **E-04** — Los agentes son exactamente `dev-architecture` y `dev-security`. · rojo visto: si
- **E-05** — Las dos policies son exactamente `approved-technology-required` y
  `homologated-version-required`. · rojo visto: si
- **E-06** — Los dos checks son exactamente `technology-homologation` y
  `technology-version-compliance`. · rojo visto: si
- **E-07** — Cero reviews. · rojo visto: si
- **E-08** — Ningún agente ni skill nuevos. · rojo visto: si

### Reusar, no duplicar

- **E-09** — Hay un solo catálogo de tecnologías en `reglas/`, el del Anexo II. · rojo visto: si
- **E-10** — No hay un segundo inventario: C3 recibe el mismo inventario que G1, con la misma forma,
  y el módulo no lee ningún archivo de inventario. · rojo visto: si
- **E-11** — No hay un segundo comparador: el módulo no tiene expresiones regulares ni compara
  versiones; la comparación es de `anexo2.py`. · rojo visto: si
- **E-12** — Las policies de G1 se reusan: una sola vez en el registro, con el archivo de G1. · rojo visto: si
- **E-13** — Los checks de G1 se reusan: los resultados de C3 son los que devuelven esos archivos,
  también por `seguridad.resultado`; unos resultados compartidos que llegan en la evidencia no se
  leen, y por la API no se leen si no son de este inventario. · rojo visto: si
- **E-14** — Los cuatro controles declaran `ES0901.G1` y `ES0902.C3` entre sus fuentes. · rojo visto: si

### La línea base

- **E-15** — ES0901 6.3 cargado y el catálogo de 6.3 resuelven: `RESOLVED`, con la versión, el
  catálogo y los cuatro controles. · rojo visto: si
- **E-16** — Sin un ES0901 cargado, con dos cargados y ninguno o dos `CURRENT`, con una fuente que
  no se puede leer o un estado o una vigencia que no se reconocen, con el único ES0901 declarado
  reemplazado, con un ES0901 declarado vigente y no cargado, con una fuente cuyo id no es un texto
  con al menos una letra o un número, o con una cuyo id —sin espacios, signos, marcas combinadas,
  caja ni ancho— contiene al del ES0901 sin ser exactamente él,
  `DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_UNRESOLVED`. · rojo visto: si
- **E-17** — ES0901 6.4 vigente y el catálogo de 6.3: `DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_MISMATCH`;
  y también con catálogo 6.4 y los controles escritos para 6.3; y la puerta mira el mismo catálogo
  contra el que se ejecuta. · rojo visto: si
- **E-18** — Un catálogo de otro estándar, o con un `status` de otra versión, es
  `DEVELOPMENT_STANDARD_TECHNOLOGY_BASELINE_MISMATCH`. · rojo visto: si
- **E-19** — Sin catálogo, o ilegible, `TECHNOLOGY_CATALOG_UNAVAILABLE`. · rojo visto: si
- **E-20** — Un control compartido no instalado o sin archivo, `SHARED_TECHNOLOGY_CONTROL_UNAVAILABLE`. · rojo visto: si
- **E-21** — Sin inventario, o vacío, C3 queda `UNRESOLVED` con `TECHNOLOGY_INVENTORY_UNAVAILABLE`,
  nunca `NOT_APPLICABLE` — también cuando llegan resultados compartidos en su lugar; y una
  tecnología con una forma que G1 no lee deja C3 sin resolver, sin romper. · rojo visto: si

### Una ejecución, dos agregaciones

- **E-22** — Con la misma evidencia, `technology-homologation` corre una vez por tecnología aunque
  la consuman dos reglas. · rojo visto: si
- **E-23** — Lo mismo para `technology-version-compliance`. · rojo visto: si
- **E-24** — El resultado de G1 no se copia en C3: G1 conforme con la línea base en `MISMATCH` deja
  a C3 sin resolver, y la agregación no recibe el resultado de la otra regla; una línea base que
  llega en la evidencia sólo restringe, nunca abre la que está instalada. · rojo visto: si
- **E-25** — C3 se agrega de los resultados compartidos: cambiar un resultado compartido cambia C3,
  y cambiar un resultado de G1 que no sale de ahí no; una fila sin sus dos mitades, con un estado
  que G1 no emite o de otro control, no se agrega. · rojo visto: si
- **E-26** — La misma evidencia da el mismo resultado, en cualquier orden del inventario. · rojo visto: si

### Las semánticas de G1, intactas

- **E-27** — Una versión homologada sale `HOMOLOGATED` y la regla `COMPLIANT`. · rojo visto: si
- **E-28** — Una deprecada sale `DEPRECATED_TOLERATED`, no `HOMOLOGATED`, y la regla
  `COMPLIANT_WITH_OBSERVATIONS`. · rojo visto: si
- **E-29** — Una rama más nueva no se autoriza: `ASI_EVALUATION_REQUIRED` y la regla sin resolver. · rojo visto: si
- **E-30** — Una tecnología principal que no figura sigue en `ASI_EVALUATION_REQUIRED`. · rojo visto: si
- **E-31** — Una auxiliar de toolchain sigue en `TOOLCHAIN_AUXILIARY_REVIEW`. · rojo visto: si
- **E-32** — Keycloak y OpenID Connect sin evidencia del proveedor siguen en
  `PROVIDER_VERSION_REQUIRED`, sin versión inventada. · rojo visto: si
- **E-33** — Una versión que depende del framework sigue pidiendo su contexto. · rojo visto: si

### Los límites

- **E-34** — C3 conforme no pone a C2 en cumplimiento. · rojo visto: si
- **E-35** — Ni a Vu7. · rojo visto: si
- **E-36** — Ni a Vu10. · rojo visto: si
- **E-37** — Ni a G2. · rojo visto: si
- **E-38** — C3 no escanea vulnerabilidades: el módulo no nombra hallazgos, severidades ni CVE. · rojo visto: si
- **E-39** — El resultado de C3 conserva `ES0902 / 6.2 / §3 / C3` por todos los caminos, y la unidad
  de trabajo lleva `rules.C3` con referencias y sin el catálogo; la unidad sólo proyecta un
  resultado de `ES0902.C3` con un estado que C3 emite, y su línea base es la instalada. · rojo visto: si
- **E-40** — Los controles reusados conservan a la vez `ES0901 / 6.3 / 7.1 / G1`: cada resultado
  compartido trae su traza de G1 y las fuentes de las dos reglas. · rojo visto: si

## Cómo se verifica

Los cuarenta por `.\tests\Invoke-Tests.ps1`. Ninguno es de lectura.

🔴 Las lecciones de C1 y C2 van puestas desde el principio: lo que no tiene la forma declarada no
cuenta, lo que puede decir que no y viene torcido deja la regla sin resolver, y toda lista sale
ordenada por su contenido. Un inventario con una tecnología mal formada no aprueba: queda sin
resolver.

## Riesgos conocidos

- **`ALGORITMOS` crece.** Diez reglas con algoritmo propio. La razón es la misma que la de O1 y se
  declara; la próxima que entre tiene que dar la suya.
- **La vigencia de ES0901 no está declarada.** La línea base normativa no trae `currency` para
  ES0901; con una sola fuente cargada alcanza. El día que se cargue una segunda, hay que declarar
  cuál es `CURRENT` o C3 queda sin resolver — que es lo que se quiere.
- **`controles/` no llega a un proyecto instalado** (ya anotado en `PENDIENTES-FH.md`). Instalado,
  C3 da `SHARED_TECHNOLOGY_CONTROL_UNAVAILABLE`, que es el estado correcto hasta que se arregle.
