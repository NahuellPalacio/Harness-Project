# D2: delegar el ingreso de credenciales, y decir qué no se puede verificar

**Estado:** construido · **Fecha:** 2026-09-19

## Qué problema resuelve

D1 dejó construida la infraestructura de señales y sus dos controles. D2 es la regla de al lado:

> "Toda autenticación en las aplicaciones del GCABA deberá delegar el ingreso de credenciales de
> usuarios según lo descripto en el apartado 'Autenticación'." — ES0901 §7.1 D2, pág. 12

Sus dos controles —`credential-entry-delegation-required` y `authentication-delegation`— están
declarados y no existen. Su señal, `authenticationPresent`, es una de las catorce que la matriz
declara y de las que hoy nadie produce.

D2 trae tres problemas que D1 no tuvo:

1. **Dos contextos, no uno.** El apartado de integraciones del estándar manda miBA para el
   ciudadano (pág. 18) y Active Directory a través del portal OpenID de la DGSEI, con Keycloak
   como proveedor obligatorio, para lo que no es ciudadano (pág. 19). D2 gobierna la delegación en
   los dos, y cuál corresponde depende de a quién autentica el flujo.
2. **Una frontera con una norma que el harness no tiene.** El estándar remite a ES0902 para los
   requisitos de seguridad. En `normativa/extractos/ES0902.md` hay un extracto de la v6.2, y es el
   único de los seis que **no cerró como fiel** —su último hallazgo se corrigió a mano y nunca
   volvió a refutación—. No hay ningún `es0902*.json` en `reglas/`: ES0902 no es fuente declarada
   de este harness. Lo que dependa específicamente de ella no se puede verificar, y decirlo es el
   trabajo.
3. **Una señal que una dependencia no alcanza a encender.** Que `angular-oauth2-oidc` esté en
   `package.json` no prueba que la aplicación autentique usuarios. Hoy `senales.py` trata
   `REPOSITORY_CONFIGURATION` como evidencia estructurada y suficiente, y para esta señal no lo es.

## Qué queda afuera

- **Un segundo framework de señales.** Se reusa el de D1 entero: schema, productor, resolución,
  inventario contra la matriz. Lo único que se agrega es una clase de fuente —ver más abajo—, y se
  agrega al genérico, no a D2.
- **`dev-miba`.** Sigue `DECLARED_NOT_INSTALLED`. Ninguna parte de D2 la crea, la instala ni la
  completa. Tampoco se usa `dev-openid-connect` como si supiera de miBA: cubre OpenID
  institucional, que es otra cosa.
- **Los internos de miBA y de cualquier proveedor:** client ids, claims, redirect URIs, endpoints,
  logout, registro, secretos y valores por ambiente. El endpoint viejo de OpenID se identifica por
  un valor declarado —`LEGACY_OPENID_ENDPOINT`—, nunca por su URL: una URL en un artefacto del
  harness es configuración inventada aunque esté puesta para prohibirla.
- **Los requisitos de seguridad de ES0902.** No se citan, no se parafrasean y no se deducen. Lo que
  depende de ellos sale `ES0902_CONTEXT_REQUIRED`. Traer ES0902 como fuente declarada es otro
  cambio, y arranca por cerrar su extracto como fiel.
- **El modelo de autorización.** Roles, permisos y validación de tokens no son D2. El estándar
  manda que los roles se asignen desde el backoffice de la aplicación, y eso tiene su propia regla.
- **D1.** Qué mecanismo le corresponde a una aplicación ciudadana lo decide D1. D2 pregunta si el
  ingreso de credenciales se delega, sea cual sea el mecanismo.
- **Detectar la señal leyendo el repositorio.** Igual que en D1: la evidencia entra como dato.
- **Los otros 62 controles declarados.** Siguen declarados y sin construir.

## Las decisiones, y por qué

### `REPOSITORY_DEPENDENCY` se separa de `REPOSITORY_CONFIGURATION`

Hoy hay una sola clase para todo lo que sale del repositorio, y mezcla dos cosas distintas:

```text
REPOSITORY_CONFIGURATION   como esta configurada la aplicacion       evidencia de lo que hace
REPOSITORY_DEPENDENCY      que paquete esta instalado                evidencia de lo que hay
```

La segunda entra como **fuente débil**, junto a `AGENT_STATEMENT`: sola no sostiene ningún valor de
ninguna señal. No es una regla de D2; es la corrección de una clase que estaba de más ancha, y vale
igual para `citizenFacing` y para las doce que faltan. D2 es el cambio que la hizo evidente porque
es la primera señal donde la confusión cambia el resultado.

### La audiencia no se adivina

D2 aplica por `authenticationPresent` y por nada más. Pero para saber **a qué mecanismo** debía
delegarse hay que saber a quién autentica el flujo, y eso puede no estar. Entonces:

```text
audiencia declarada en el flujo          se usa
audiencia ausente + citizenFacing        se usa citizenFacing como contexto secundario
ninguna de las dos                       AUTHENTICATION_CONTEXT_UNRESOLVED
```

`citizenFacing` se **reusa**, no se redefine: es la misma señal que produce D1, con su misma
evidencia. Un segundo detector de lo mismo, con otro nombre, es la forma más rápida de que dos
reglas contesten distinto sobre el mismo sistema.

`AUTHENTICATION_CONTEXT_UNRESOLVED` es un estado del check y no un `PARTIAL`. Un `PARTIAL` dice
"falta evidencia de esto que estoy mirando"; esto dice "no sé qué tengo que mirar".

### `ES0902_CONTEXT_REQUIRED` es un estado, no una excusa

El check contesta lo que ES0901 dice por sí mismo —que las credenciales se delegan, y a qué
proveedor autorizado— y se declara incompetente para lo que ES0901 delega en ES0902. Las dos mitades
conviven en un mismo resultado: una validación pedida sobre seguridad no anula la verificación de
la delegación.

Lo que el harness **no** hace es clasificar temas por su cuenta. Una validación pedida sale
`ES0902_CONTEXT_REQUIRED` si quien la pide la declara de ES0902, o si su id está en la lista corta
que el check declara. Deducir "esto suena a seguridad, debe ser de ES0902" sería inventar el
alcance de una norma que no está.

### Delegar es dónde se escriben las credenciales, no quién las valida después

El patrón prohibido más caro es el formulario propio que después llama a una API: la aplicación ve
la contraseña del usuario, y que la mande a otro lado no la vuelve delegada. Por eso el flujo
declara `credentialEntry` —`DELEGATED`, `APPLICATION_OWNED`, `UNRESOLVED`— como un hecho separado
del proveedor: un `APPLICATION_OWNED` con proveedor declarado sigue siendo `FAIL`.

### El endpoint viejo no es proveedor actual

El estándar dice que no se dan más credenciales sobre el OpenID anterior y que las aplicaciones
nuevas tienen que apuntar al portal actual. `LEGACY_OPENID_ENDPOINT` es delegación —el usuario no
escribe la credencial en la aplicación— y no es el proveedor autorizado: `FAIL`, no `PASS`.

### `PASS` sigue siendo el único que aprueba

Siete estados, uno aprueba:

```text
PASS                         se delega, al mecanismo que corresponde, sin camino directo activo
FAIL                         la evidencia contradice la regla
PARTIAL                      la evidencia falta o no alcanza
NOT_APPLICABLE               authenticationPresent = FALSE
APPLICABILITY_UNRESOLVED     authenticationPresent = UNRESOLVED
AUTHENTICATION_CONTEXT_UNRESOLVED   hay autenticacion y no se sabe de quien
ES0902_CONTEXT_REQUIRED      lo pedido depende de una norma que el harness no tiene
```

Es la misma doctrina que D1 y se repite acá porque acá hay cuatro maneras nuevas de no saber, y
cada una es una tentación distinta de dar por bueno lo que nadie miró.

### D1 y D2 aplican juntas y no se pisan

Una aplicación ciudadana dispara las dos, y ninguna contesta por la otra. El caso que lo muestra es
un flujo ciudadano delegado al proveedor institucional: las dos fallan y **por motivos distintos**
—D1 dice que el mecanismo no es el del ciudadano; D2, que el destino de la delegación no es el que
corresponde al contexto—. Ninguno de los dos resultados nombra el control del otro.

No es que D2 ignore el contexto: el paquete dice que `PASS` exige que el mecanismo delegado
corresponda al contexto de autenticación aplicable, así que D2 lo mira. Lo que **no** hace es
decidir si la aplicación debe ser ciudadana —eso es D1— ni emitir el veredicto de mecanismo de D1.
La diferencia se ve en que D2 aplica y resuelve con `citizenFacing` en `UNRESOLVED`, donde D1 ni
siquiera puede decir si le toca.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `comun/schemas/normative-signal.schema.json` | Suma `REPOSITORY_DEPENDENCY` a las clases de fuente |
| `harnesses/desarrollo/bin/orquestacion/senales.py` | `REPOSITORY_DEPENDENCY` entra como fuente débil; nada más cambia |
| `harnesses/desarrollo/controles/policies/credential-entry-delegation-required.md` | El contrato de la policy |
| `harnesses/desarrollo/controles/checks/authentication-delegation.py` | El check: delegación, proveedor, contexto y las dos fronteras |
| `harnesses/desarrollo/reglas/control-registry.json` | Suma los dos controles de D2 |
| `docs/normativa-7.1.md` | Los dos contextos de autenticación y la frontera con ES0902 |
| `tests/casos/27_d2_delegacion_credenciales.py` | Los escenarios de este cambio |

La fila de `D2` en la matriz **no se toca**: ya declara su modo, su señal, su policy y su check.

## Escenarios verificables

Entre paréntesis, el `D2-nn` del pedido de instalación.

### La señal

- **E-01** — `D2` sigue siendo `CONDITIONAL` sobre `authenticationPresent`, y su fila no cambia.
  (D2-01) · rojo visto: si
- **E-02** — `authenticationPresent = TRUE` con evidencia deja `D2` en `applicableRules` y exige sus
  dos controles. (D2-02) · rojo visto: si
- **E-03** — `FALSE` con evidencia deja `D2` en `notApplicableRules`. (D2-03)
  · rojo visto: si
- **E-04** — Sin señal, `D2` queda `APPLICABILITY_UNRESOLVED` con `authenticationPresent` escrita al
  lado, y nunca en no aplicable. (D2-04) · rojo visto: si
- **E-05** — Una dependencia declarada en el repositorio, sola, no pone la señal en `TRUE`: queda
  `UNRESOLVED` con `SIGNAL_EVIDENCE_MISSING`. (D2-05) · rojo visto: si
- **E-06** — La misma dependencia acompañada de evidencia de que participa de un flujo sí resuelve.
  · rojo visto: si
- **E-07** — No hay un segundo framework de señales: `authenticationPresent` pasa por el mismo
  módulo, el mismo schema y el mismo inventario que `citizenFacing`, y la clase nueva vale para
  cualquier señal. · rojo visto: si
- **E-08** — El resultado de la señal conserva su evidencia y el modo de su productor. (D2-18)
  · rojo visto: si

### La delegación

- **E-09** — Validación de credenciales en la propia aplicación, con D2 aplicable: `FAIL`. (D2-06)
  · rojo visto: si
- **E-10** — Autenticación institucional delegada, con evidencia del portal de la DGSEI y Keycloak:
  `PASS`. (D2-07) · rojo visto: si
- **E-11** — El endpoint viejo de OpenID no se acepta como proveedor actual: `FAIL`, aunque haya
  delegación. (D2-08) · rojo visto: si
- **E-12** — Flujo ciudadano con evidencia de miBA a nivel gobierno: satisface la delegación sin que
  el resultado nombre ningún interno de miBA. (D2-09) · rojo visto: si
- **E-13** — Un formulario propio no se vuelve delegación porque después llame a una API: si la
  aplicación recibe la credencial, `FAIL`. · rojo visto: si
- **E-14** — Una dependencia de OIDC no prueba que las credenciales se deleguen. (D2-05)
  · rojo visto: si
- **E-15** — Las tres formas de que falte evidencia dan `PARTIAL` y ninguna aprueba: un redirect
  sin proveedor identificado, un flujo que no dice dónde escribe la credencial el usuario, y una
  aplicación que declara autenticación sin ningún flujo que mirar. · rojo visto: si
- **E-16** — La afirmación de un agente, sola, no alcanza. · rojo visto: si
- **E-17** — `PARTIAL` no se sube a `PASS` por suposición, y de los siete estados `PASS` es el único
  que aprueba. · rojo visto: si
- **E-18** — Un camino de credenciales directas activo convive con un flujo delegado y el resultado
  es `FAIL`: el que cumple no tapa al que no. · rojo visto: si

### El contexto y las fronteras

- **E-19** — Autenticación presente y audiencia que no se puede resolver:
  `AUTHENTICATION_CONTEXT_UNRESOLVED`, sin adivinar. (D2-12) · rojo visto: si
- **E-20** — Con la audiencia ausente en el flujo, `citizenFacing` se usa como contexto secundario y
  no se redefine: es la misma señal, con su evidencia. (D2-12) · rojo visto: si
- **E-21** — La aplicabilidad de `D2` no depende de `citizenFacing`: con `citizenFacing` en
  cualquiera de sus tres valores, `D2` aplica si `authenticationPresent` es `TRUE`. (D2-13)
  · rojo visto: si
- **E-22** — `D1` y `D2` pueden aplicar las dos a la misma unidad, cada una con sus controles.
  (D2-14) · rojo visto: si
- **E-23** — `D2` no duplica la selección de mecanismo de `D1`: el mismo flujo ciudadano delegado
  al proveedor institucional falla en los dos checks **por motivos distintos**, y ninguno de los dos
  resultados nombra el control, el motivo ni la señal del otro. (D2-15) · rojo visto: si
- **E-24** — Una validación que depende de ES0902 devuelve `ES0902_CONTEXT_REQUIRED` y no anula la
  verificación de la delegación. (D2-16) · rojo visto: si
- **E-25** — No se inventa ninguna regla de ES0902: el check nombra lo que no puede contestar y no
  produce ni un requisito. (D2-17) · rojo visto: si
- **E-26** — Una remediación que exige conocimiento operativo de miBA devuelve
  `SPECIALIZED_SKILL_GAP`, y eso no hace cumplir a `D2`. (D2-10) · rojo visto: si
- **E-27** — `dev-openid-connect` está instalada y sirve para lo institucional; no reemplaza a
  `dev-miba` para un flujo ciudadano. (D2-11) · rojo visto: si
- **E-28** — Los artefactos de `D2` no traen client ids, claims, redirect URIs, endpoints, URLs de
  proveedor ni configuración por ambiente, y la guarda se prueba contra fugas de las seis clases.
  · rojo visto: si

### La propagación y la instalación

- **E-29** — La unidad de trabajo lleva `authenticationPresent` con su valor y su evidencia, y
  cuando `citizenFacing` está, la conserva al lado sin redefinirla. (D2-18)
  · rojo visto: si
- **E-30** — Antes de instalar, los dos controles de `D2` son `DECLARED_POLICY_NOT_INSTALLED` y
  `DECLARED_CHECK_NOT_INSTALLED`; después desaparecen de la lista de faltantes **sin tocar la
  declaración normativa de D2**. (D2-19) · rojo visto: si
- **E-31** — Todo resultado de `D2` conserva la tupla `ES0901 / 6.3 / 7.1 / D2`. (D2-20)
  · rojo visto: si

## Cómo se verifica

Los 31 pasan por la suite, en `tests/casos/27_d2_delegacion_credenciales.py`. Ninguno necesita
lectura: todo lo que se afirma es estado, evidencia y trazabilidad.

E-28 se verifica en dos mitades, igual que su par en D1: los patrones sobre los dos archivos de D2,
y una inyección de fugas de las seis clases que exige que cada una ponga el caso rojo. Un test de
patrón que nadie probó contra una fuga real se lee severo y no comprueba nada.

E-23 es el que sostiene la separación con D1 y por eso corre los dos checks sobre **el mismo caso**:
dos motivos distintos sobre la misma evidencia es lo que prueba que no se duplican. E-21 es el otro
lado de lo mismo: D2 resuelve donde D1 no puede.

Las señales, las evidencias y los flujos se arman en memoria. Del árbol se lee sólo lo versionado
—la matriz, los dos registros— y ningún caso escribe.

## Riesgos conocidos

- **`ES0902_CONTEXT_REQUIRED` puede volverse el cajón de lo incómodo.** Es un estado que no obliga a
  nada y que se justifica solo. Lo que lo contiene es que sale únicamente cuando la validación
  pedida se declara de ES0902 o figura en la lista corta del check; lo que no lo contiene es que esa
  lista la escribe alguien y puede crecer.
- **La separación con D1 no la hace cumplir nada.** Está escrita, está testeada con un caso, y el
  día que alguien agregue a D2 una verificación de mecanismo ciudadano el test seguirá verde.
- **Nadie produce las señales todavía.** Se suma la segunda señal declarada y sigue sin haber quien
  releve la evidencia. Una unidad real sale con `D2` sin resolver.
- **El contexto secundario arrastra el error de `citizenFacing`.** Si esa señal está mal producida,
  D2 elige el mecanismo esperado equivocado sin que nada lo note. Es el precio de reusarla, y es
  menor que el de tener dos señales que contestan distinto.
- **El extracto de ES0902 existe y no es fuente.** Alguien puede leerlo y creer que alcanza. La
  frontera está en el código y en la doc; el extracto sigue diciendo en su encabezado que no cerró.
