# El registro de agentes: la existencia se declara y se valida, no se adivina

**Estado:** construido · **Fecha:** 2026-09-18

## Qué problema resuelve

Hoy la existencia de un agente es una sola línea:

```python
# roster.py
def existe_agente(nombre, desde):
    return any(os.path.isfile(os.path.join(d, "agents", nombre + ".md")) ...)
```

El archivo está o no está. Nadie mira qué tiene adentro. Un `.md` vacío, uno con el `name`
equivocado, o un especialista sin una sola skill instalada pasan los tres como `agentExists: true`,
y el plan los rutea igual.

Y hay tres cosas que el harness no sabe decir:

- **Un archivo de agente que nadie declaró.** `dev-iniciador-code.md` existe en disco desde hace
  cuatro versiones y el roster no lo nombra. No aparece en ningún lado: ni como agente, ni como
  hueco, ni como problema.
- **Una skill declarada que todavía no se puede escribir.** `dev-miba` y `dev-esb` no existen
  porque falta información autoritativa de la integración, no porque nadie las haya escrito. Hoy
  se reportan igual que `dev-ambientes`, que es del set viejo y no va a volver.
- **La diferencia entre que falte una skill y que falte una capacidad.** Las dos son huecos, pero
  una capacidad faltante deriva a `dev-tool-builder` y una skill faltante **no**. Nada en el código
  impide hoy que un hueco de skill termine pidiendo que alguien fabrique una tool.

🔴 **Una corrección al pedido, porque cambia el alcance.** El pedido dice que hay que sacarle a la
matriz normativa de ES0901 el control sobre `agentExists`. En este repositorio **la matriz nunca lo
tuvo**: `normativa.py` sólo llena `applicableStandards`, y la existencia siempre salió del disco.
Tampoco hay arreglos de agentes hardcodeados: `roster.json` ya era la única fuente. Lo que sí
aplica del pedido, y es la mitad que importa, es todo lo demás: **validar** lo declarado en vez de
sólo constatar que el archivo está, darle estados a las skills, detectar huérfanos y separar el
hueco de skill del hueco de capacidad.

## Qué queda afuera

- **Escribir `dev-miba` y `dev-esb`.** El pedido lo prohíbe y la razón es la del harness entero:
  no hay información autoritativa de esas integraciones, y una skill inventada se lee igual de
  autoritativa que una real. Quedan `DECLARED_NOT_INSTALLED` con su motivo escrito.
- **Decidir qué pasa con `dev-iniciador-code`.** Se detecta, se nombra y no se rutea. Adoptarlo o
  borrarlo es una decisión de otra persona y de otro cambio; este sólo deja de disimularlo.
- **La matriz normativa de §7.1.** Sigue sin clasificar. Este cambio la separa de la existencia,
  no la construye.
- **Un sistema de CI.** No hay `.github/`, ni `.gitlab-ci.yml`, ni nada parecido: la compuerta de
  este repositorio es `tests/Invoke-Tests.ps1`, y ahí es donde entra la validación del registro.
  Inventar un pipeline para colgarle esto sería construir la mitad de una herramienta que nadie
  pidió.
- **Los checks y las capacidades locales.** Se quedan en `roster.json`. El registro de agentes
  declara agentes y skills; los checks y `capacidadesLocales` son otra cosa y moverlos sin motivo
  es cambiar dos contratos por el precio de uno.
- **Cambiar el contrato de `WorkUnit`.** `agentExists` y `skills` siguen donde están y con el mismo
  tipo. Lo que cambia es de dónde sale la respuesta, no la forma del documento.

## Las decisiones, y por qué

### Un solo roster, y el viejo pierde la mitad que se va

`roster.json` deja de declarar `agents` y `skills`; `agent-registry.json` pasa a ser la fuente. Lo
que queda en `roster.json` es `checks` y `capacidadesLocales`, que el registro no cubre. Dos
rosters compitiendo es exactamente lo que el pedido prohíbe, y es peor que cualquiera de los dos
solo: el día que difieran, cada módulo va a tener razón.

### El registro necesita el dominio, y el artefacto no lo trae

El Bloque 3 rutea por **dominio**: `agente_de_dominio("backend")` y `skills_para(["backend"])` son
lo que arma cada unidad. El `agent-registry.json` que llegó identifica al agente por `id` y `type`,
y no dice a qué dominio pertenece. Sin eso el registro no puede reemplazar al roster sin dejar un
segundo archivo que haga el mapeo — y eso es el segundo roster otra vez. Se le agrega `domain` a
cada agente. Es la única adición al artefacto y es la que hace posible la migración.

### Las rutas de las skills se corrigen, porque acá una skill es un directorio

El registro declara `skills/dev-api.md`. En este repositorio una skill es `skills/dev-api/SKILL.md`.
Tomadas literales, las 27 skills instaladas darían `SKILL_FILE_MISSING`. Se corrigen las rutas en el
dato, no en el validador: un validador que "arregla" la ruta que lee es un validador que no valida.

### El schema se traduce al subconjunto, no se afloja el validador

`agent-registry.schema.json` usa `const`, que el intérprete de `contexto-armar.py` no soporta —y
que rechaza a propósito, para no sellar partes del documento que nunca miró—. `const: "x"` y
`enum: ["x"]` afirman lo mismo, así que el schema se escribe con `enum`. La regla del repositorio es
que se amplía el validador y no se afloja el schema; acá no hace falta ninguna de las dos.

### El disco diagnostica, el registro decide

La regla vieja era "el roster declara y el disco decide". Se invierte a medias: el registro declara
y **también** decide, y el disco pasa a ser diagnóstico. Un archivo que aparece solo no se adopta
—`ORPHAN_AGENT`— y una skill en disco que nadie declaró es `UNDECLARED_SKILL`, no una skill nueva.
Es lo que impide que el harness crezca por acumulación de archivos.

### Un hueco de skill no llama al constructor de tools

`SPECIALIZED_SKILL_GAP` bloquea la especialización pedida y nada más: el agente dueño sigue siendo
válido y sus otras skills se rutean. Sólo un `CAPABILITY_GAP` —una capacidad ejecutable que no
está— deriva a `dev-tool-builder`. Confundirlos es pedirle a un constructor de tools que fabrique
conocimiento de miBA que nadie tiene.

### Se rutea cerrado

Todo estado que no sea `VALID`, `VALID_WITH_PENDING_SKILLS` o `SKILL_AVAILABLE` bloquea el ruteo.
Un registro con un error estructural no rutea "lo que se pueda": un especialista sin skills
instaladas o un `.md` cuyo `name` no coincide con su id son estados en los que nadie puede decir
qué se ejecutó.

### Seis huecos viejos desaparecen con la migración

`dev-ambientes`, `dev-identidad`, `dev-repositorio`, `dev-seguridad`, `dev-tramites-asi` y
`dev-versiones` están declarados en `roster.json` y **no** en el registro. Migrar los borra como
declaración. Es la limpieza que veníamos haciendo de a una, pero conviene que esté escrito acá y no
que aparezca como efecto secundario: el día que alguien busque `dev-tramites-asi` el registro no lo
nombra.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/reglas/agent-registry.json` | El registro: 10 agentes con su tipo, su dominio, su archivo y sus skills con estado |
| `comun/schemas/agent-registry.schema.json` | Su contrato, escrito en el subconjunto que valida `contexto-armar.py` |
| `harnesses/desarrollo/bin/orquestacion/registro_agentes.py` | Carga, validación, descubrimiento de huérfanos y de skills no declaradas, y el reporte |
| `harnesses/desarrollo/bin/orquestacion/roster.py` | Pasa a leer el registro para agentes y skills; conserva checks y capacidades locales |
| `harnesses/desarrollo/bin/orquestacion/plan.py` | `agentExists` y las skills de cada unidad salen del registro; la unidad lleva el estado de cada skill |
| `harnesses/desarrollo/reglas/roster.json` | Pierde `agents` y `skills` |
| `docs/orquestacion.md` | El registro, los estados y la frontera con el hueco de capacidad |
| `tests/casos/22_registro_agentes.py` | Los escenarios de este cambio |

## Escenarios verificables

### El registro es la fuente

- **E-01** — Los 10 agentes declarados resuelven desde el registro, y ninguno depende de que la
  matriz de §7.1 esté clasificada: con la matriz vacía, los 10 siguen existiendo.
  · rojo visto: si
- **E-02** — Un agente que el registro no declara no es ruteable. Si además no tiene archivo en
  disco, devuelve `AGENT_NOT_FOUND`; si su archivo existe, es el `ORPHAN_AGENT` de E-18. En los
  dos casos, `routable` es falso. · rojo visto: si
  > Redacción corregida el 2026-09-22, después de la verificación. La anterior decía que un agente
  > no declarado devolvía `AGENT_NOT_FOUND` "aunque su archivo exista en disco", y eso contradecía
  > a E-18 de esta misma spec, que para ese caso pide `ORPHAN_AGENT`. El comportamiento buscado es
  > el de E-18; el código ya lo cumplía y el test ahora cubre las dos mitades.
- **E-03** — Ningún agente entra al registro por aparecer en disco: agregar un `.md` no lo declara.
  · rojo visto: si
- **E-04** — El registro valida contra su schema, y el schema entra entero en el subconjunto que
  `contexto-armar.py` interpreta. · rojo visto: si
- **E-05** — Hay un solo roster de agentes y skills: `roster.json` ya no los declara, y ningún
  módulo los lee de ahí. · rojo visto: si

### Los tipos y su política de skills

- **E-06** — `dev-tool-builder`, `INFRASTRUCTURE_AGENT` con cero skills, es `VALID`. Ninguna skill
  se inventa para que cierre la validación estructural. · rojo visto: si
- **E-07** — `dev-orchestrator` (`ORCHESTRATOR_AGENT`) y `dev-refutador` (`CRITIC_AGENT`) son
  `VALID` con cero skills. · rojo visto: si
- **E-08** — Un `SPECIALIST_AGENT` sin ninguna skill `INSTALLED` es `AGENT_SKILL_POLICY_INVALID`.
  · rojo visto: si
- **E-09** — Un tipo que no está en `agentTypes` es `AGENT_TYPE_INVALID`. · rojo visto: si
- **E-10** — Un agente declarado cuyo archivo no está es `AGENT_FILE_MISSING`; uno cuyo
  `# Agent:` no coincide con su id es `AGENT_ID_MISMATCH`. La identidad no se infiere del nombre
  del archivo. · rojo visto: si
- **E-10b** — Dos agentes con el mismo id son `DUPLICATE_AGENT_ID`. · rojo visto: si
- **E-10c** — Dos `SPECIALIST_AGENT` instalados que declaran el mismo dominio son
  `DUPLICATE_DOMAIN_OWNER`. No se elige uno en silencio. · rojo visto: si

### Los estados de una skill

- **E-11** — Una skill `INSTALLED` con su archivo es `SKILL_AVAILABLE` y se rutea.
  · rojo visto: si
- **E-12** — `dev-miba` y `dev-esb` son `DECLARED_NOT_INSTALLED`, con su motivo escrito, y devuelven
  `SPECIALIZED_SKILL_GAP`. · rojo visto: si
- **E-13** — Una skill `DECLARED_NOT_INSTALLED` no se rutea, y su agente dueño sigue siendo válido:
  `dev-integration` es `VALID_WITH_PENDING_SKILLS` y sus otras cuatro skills se rutean igual.
  · rojo visto: si
- **E-14** — Una skill `INSTALLED` sin su archivo es `SKILL_FILE_MISSING`. · rojo visto: si
- **E-15** — La misma skill declarada bajo dos agentes distintos es `SKILL_OWNER_CONFLICT`.
  · rojo visto: si
- **E-15b** — Una skill `INSTALLED` cuyo `# Skill:` no coincide con su id es
  `SKILL_ID_MISMATCH`. La identidad no se infiere del nombre del directorio.
  · rojo visto: si
- **E-16** — Una skill `DEPRECATED` no se rutea. · rojo visto: si
- **E-17** — Pedir una skill que el agente no declara devuelve `SKILL_NOT_DECLARED_FOR_AGENT`, que
  no es lo mismo que `UNDECLARED_SKILL`. · rojo visto: si

### El disco diagnostica

- **E-18** — `dev-iniciador-code.md` se detecta como `ORPHAN_AGENT`, no se adopta, no se borra y no
  se le rutea ninguna unidad. · rojo visto: si
- **E-18b** — El huérfano ya reconocido sigue visible y no ruteable, y no hace fallar la suite;
  uno nuevo, sin reconocer, es error estructural. El reconocimiento vive fuera de la declaración
  de agentes y nunca vuelve ruteable a un huérfano. · rojo visto: si
- **E-19** — Una skill en disco que el registro no declara es `UNDECLARED_SKILL`.
  · rojo visto: si
- **E-20** — El reporte calcula sus números del registro y del disco: ninguna cuenta está escrita
  en el código. · rojo visto: si

### El ruteo

- **E-21** — `dev-backend` rutea: agente válido, skills instaladas. · rojo visto: si
- **E-22** — `dev-quality` con `dev-test-automation` es `ROUTABLE`. · rojo visto: si
- **E-23** — Todo estado de error rutea cerrado: `AGENT_NOT_FOUND`, `ORPHAN_AGENT`,
  `AGENT_FILE_MISSING`, `AGENT_ID_MISMATCH`, `AGENT_TYPE_INVALID`, `AGENT_SKILL_POLICY_INVALID`,
  `DUPLICATE_AGENT_ID`, `DUPLICATE_DOMAIN_OWNER`, `SKILL_FILE_MISSING`, `SKILL_ID_MISMATCH`,
  `SKILL_OWNER_CONFLICT`, `SKILL_NOT_DECLARED_FOR_AGENT`, `UNDECLARED_SKILL`, `DEPRECATED_AGENT`
  y `DEPRECATED_SKILL` devuelven `routable: false`. · rojo visto: si

### La frontera con la capacidad

- **E-24** — Un `SPECIALIZED_SKILL_GAP` no deriva a `dev-tool-builder` ni produce ninguna solicitud
  de tool. · rojo visto: si
- **E-25** — Un `CAPABILITY_GAP` sigue derivando a `dev-tool-builder`, con la skill dueña presente:
  los dos huecos coexisten sin mezclarse en la misma corrida. · rojo visto: si

### El plan

- **E-26** — Una unidad de un dominio recibe su agente y sus skills desde el registro, y el
  `agentExists` de la unidad es el del registro. · rojo visto: si
- **E-27** — La unidad lleva el estado de cada skill, no sólo su nombre: un especialista que recibe
  su unidad suelta puede ver ahí mismo cuál de sus skills está pendiente.
  · rojo visto: si
- **E-28** — Con la matriz de §7.1 vacía, el plan no marca `agentExists: false` a ningún agente
  declarado y válido. · rojo visto: si

### La compuerta

- **E-29** — La suite valida el registro completo: si un `.md` de agente o de skill se agrega, se
  borra o se renombra sin tocar el registro, la corrida se pone en rojo.
  · rojo visto: si

## Cómo se verifica

El cambio se construye en dos fases y no se colapsan: **Fase A** es el registro, su schema,
el validador, el diagnóstico del disco y la migración de `roster.py`; **Fase B** es `plan.py`
y la propagación del estado de cada skill a la unidad de trabajo. E-01 a E-25 son de la Fase A
y E-26 a E-29 de la Fase B. Un refactor de las dos a la vez no se puede verificar por partes.

Los 29 escenarios pasan por la suite. Ninguno es sobre una corrida de un modelo: el registro, la
validación, los estados y el ruteo son dato y código, y la propiedad que el validador promete
—mismo registro más mismo disco, mismo resultado— es justamente lo que un test determinista
comprueba.

E-29 es la integración con la compuerta que el pedido pide como CI: en este repositorio la CI es
`tests/Invoke-Tests.ps1`, así que la validación del registro es un caso más de la suite y corre en
cada cambio de un `.md` de agente, de un `.md` de skill o del registro.

📌 Los escenarios que fabrican estados de error —`AGENT_ID_MISMATCH`, `SKILL_OWNER_MISMATCH`,
`AGENT_SKILL_POLICY_INVALID`— se prueban contra registros fabricados en memoria, no rompiendo el
árbol. Es la lección de E-11 y E-12 del Bloque 3: un test que nombra un sujeto real envejece cuando
ese sujeto cambia, y uno que rompe el árbol deja el árbol roto si la corrida se mata.

## Riesgos conocidos

- **La migración toca el camino que arma cada unidad de trabajo.** `plan.py` pide agente y skills en
  cuatro lugares; si uno queda leyendo el roster viejo, hay dos fuentes otra vez y nadie lo va a ver
  hasta que difieran. Es el riesgo principal y lo cubre E-05.
- **Seis huecos declarados desaparecen.** Están nombrados arriba. Si alguno tenía que sobrevivir,
  se ve cuando ya no está en ningún reporte.
- **El registro repite en `knownOrphans` lo que el descubrimiento calcula.** Se trata la lista como
  acuse de recibo —"este huérfano ya se vio"— y no como fuente: la fuente es el disco. Si alguien la
  usa como fuente, vuelve el problema de la lista que envejece.
- **`domain` es una adición nuestra al artefacto.** Si el registro se regenera desde afuera sin ese
  campo, la migración se rompe entera.
- **El validador no mira el contenido de un agente más allá de su identidad.** Un `.md` con el
  `name` correcto y el cuerpo vacío valida. Que un agente diga algo útil no es estructural y este
  cambio no lo promete.
