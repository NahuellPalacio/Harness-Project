---
estado: aceptada
creado: 2026-08-12
---

# ADR-0006 — El método de los proyectos instalados es SDD

## Contexto

El harness sabe **qué** reglas rigen: secretos, zonas del `CLAUDE.md`, formato de historia de
usuario. No sabe **cómo se trabaja**. Un agente puede escribir cuatrocientas líneas sin que
nadie haya escrito antes qué tenían que cumplir, y sin que nadie distinto de quien las escribió
compruebe después que las cumplen.

Eso alcanzaba mientras el harness solo tenía `analisis`. Deja de alcanzar ahora, por dos cosas
que pasaron casi juntas:

1. **`desarrollo` va a hacer cumplir estándares.** ES0901 y ES0903 traen decenas de reglas
   verificables. Sin un método que las incorpore antes de escribir, llegan como avisos sueltos
   *después* de que el código ya está — que es cuando corregir sale caro.
2. **El harness de análisis ya tiene, de hecho, media metodología.** `hu-redactor` escribe y
   `hu-refutador` verifica, y quien verifica no es quien redactó. Eso es una fase de
   especificación y una de verificación, sin nombre y sin ciclo alrededor.

### Lo que esta decisión revisa

El 10 de agosto, al leer gentle-ai, se dejó SDD explícitamente afuera. Está registrado en
[`terceros/gentle-ai/ORIGEN.md`](../../terceros/gentle-ai/ORIGEN.md) y en el lockfile:

> *"SDD y RDD completos. Son una metodología de trabajo entera; adoptarla es una decisión mucho
> más grande que este harness, y no es la que estamos tomando."*

**Esa decisión era correcta y sigue siéndolo.** Lo que se rechazó fue adoptar *el paquete*: ocho
fases, un agente orquestador, un contrato de estado, Engram como memoria y OpenSpec como
almacén. Todo eso sigue afuera.

Lo que se adopta acá es **el método**, que es otra cosa y mucho más chica: escribir qué se va a
construir antes de construirlo, y que alguien distinto verifique contra eso. Cuatro pasos, dos
archivos, ninguna dependencia nueva.

## Decisión

**Los proyectos que instalan el harness trabajan por SDD.**

```
especificar   que se construye y como se prueba que cumple
construir
testear       los tests salen de la spec, con el codigo ya armado
verificar     alguien distinto contrasta contra la spec
```

Cinco reglas de implementación, que importan tanto como la elección:

### 1. No se exige TDD, pero sí ver el rojo una vez

Los tests se escriben con el código ya armado. Lo que no se permite es derivarlos del código:
**los escenarios que prueban ya estaban en la spec, que es anterior**. Esa es toda la diferencia.
La deformación de "escribir tests al final" viene de probar lo que implementaste en vez de lo
que hacía falta; con los escenarios escritos antes, esa deformación no aparece.

Queda una pérdida que el orden no arregla: **un test que nunca se vio fallar no probó que puede
fallar.** Escrito con el código en verde adelante, un test puede pasar por la razón equivocada
—afirmar algo trivialmente cierto, no ejercitar la rama que cree— y nadie se entera.

Por eso la fase de test cierra con un paso: **romper el código a propósito, confirmar que el
test se pone rojo, y restaurar.** Diez segundos, y recupera la única garantía que daba escribir
el test primero.

📌 **Esto no se puede verificar mecánicamente, y no se pretende.** Ningún check sabe si alguien
rompió el código. Lo que se hace es que deje de ser invisible: cada escenario de la spec lleva
la marca `rojo visto`, y el refutador la reporta junto al veredicto. Un `sostenido` con
`rojo visto: no consta` sigue siendo `sostenido` — pero quien lee el veredicto sabe cuánto vale.

Es la misma operación que hacen los techos de zona del `CLAUDE.md`: no impiden pasarse, miden y
avisan. Una práctica que nadie mide dura hasta la primera semana ocupada.

TDD sigue siendo válido y bienvenido donde alguien lo quiera usar — no es el método por defecto.

### 2. El ciclo lo abre la persona

El harness no decide que algo es un cambio. No hay umbral de líneas, ni disparador por tipo de
archivo, ni exigencia por ticket. Quien trabaja abre el cambio cuando le parece.

### 3. Ninguna compuerta bloquea

El harness recuerda en qué fase está, avisa si se está construyendo sin spec y avisa si un
escenario no aparece nombrado en ningún test. Nada de eso frena una herramienta.

**Los secretos siguen siendo lo único que bloquea en todo el harness.** Un ciclo de trabajo que
frena a la gente el primer día está desactivado la primera semana, y se lleva puesto el
prestigio de las reglas que sí importan.

### 4. La spec vive en el repositorio

`docs/cambios/<nombre>/spec.md`, versionada y diffeable, al lado de `docs/conocimiento/` y por
el mismo motivo de [ADR-0003](0003-obsidian-fuera-del-harness.md): viaja con el proyecto y no
depende de que una persona esté disponible. Una spec en `.claude/` se borraría en el próximo
`-Update`, y algo que se puede perder no es una fuente.

### 5. Rige para los proyectos instalados, no para este repositorio

`gcba-harness` no adopta SDD para su propio desarrollo por ahora. Se decide después de haberlo
visto funcionar en un proyecto real, y esa decisión será su propio ADR.

## Consecuencias

**A favor:**

- Las reglas de los estándares dejan de llegar sueltas y tarde: entran a la spec del cambio como
  escenarios verificables, antes de que exista el código que tienen que gobernar.
- Quien verifica no es quien construyó. Es el principio que ya funciona en `analisis`, extendido
  al resto.
- La trazabilidad existe, está en el repo y es diffeable. Se puede contestar qué tenía que
  cumplir un cambio y quién comprobó que cumplía.
- **No entra ninguna dependencia nueva.** Ni Engram, ni OpenSpec, ni un runtime, ni un binario.
  Todo se apoya en lo que el harness ya tiene: hooks, checks, subagentes y git.
- El costo cuando nadie lo usa son unos 100 tokens del descriptor de una skill y un check que
  calla. Es barato estar equivocado.

**En contra:**

- 🔴 **La garantía del rojo pasa de estructural a declarada.** Con TDD era imposible saltearla:
  no había código antes del test rojo. Acá depende de que alguien rompa el código a propósito y
  lo anote. El harness lo pide, deja el lugar donde anotarlo y lo reporta en cada veredicto —
  pero no puede comprobarlo. **Es la pérdida real de esta decisión: una garantía que era del
  método pasa a ser una disciplina de quien trabaja.**
- El ciclo puede no usarse nunca, precisamente porque lo abre la persona. Es el precio de no
  bloquear, y está aceptado.
- Es un método más que explicarle a quien entra a un proyecto.
- **El harness pasa a opinar sobre cómo se trabaja, no solo sobre qué reglas rigen.** Es un salto
  de alcance real y conviene nombrarlo: hasta acá el harness hacía cumplir normas ajenas; a
  partir de acá propone una forma de trabajar que no está en ninguna norma del organismo.

**Riesgo residual:** una spec escrita para pasar el check — escenarios tan vagos que cualquier
test los satisface. No hay defensa mecánica posible. La defensa es la skill que enseña a
especificar y el refutador que contrasta contra la fuente.

## La regla general que deja

📌 **Adoptar un método no es adoptar el paquete que lo trae.**

Lo que se rechazó en agosto fue un binario en Go, una memoria persistente, un almacén de
artefactos y ocho fases con su orquestador. Ninguna de esas piezas era el método: eran la forma
en que otro proyecto lo implementó, con sus propias restricciones, que no son las nuestras.

Separar las dos cosas es lo que permite tomar la idea sin heredar el andamiaje. Es la misma
operación que [ADR-0005](0005-terceros-separados-de-lo-propio.md) prevé para el material de
terceros, aplicada a una metodología en vez de a un archivo.

## Revisión

Se revisa **si a los seis meses no hay ninguna carpeta en `docs/cambios/` en ningún proyecto
instalado.** Eso significaría que el ciclo no servía o que estorbaba, y la respuesta correcta
sería sacarlo o rediseñarlo — **nunca empezar a bloquear para forzar su uso**. Un método que
necesita coerción para que lo usen ya se contestó a sí mismo.

También se revisa si aparece una forma de **comprobar** el rojo en vez de declararlo —una
herramienta de mutación que no exija configuración por lenguaje, o cualquier mecanismo que no
dependa de la disciplina de quien escribe. Mientras eso no exista, `rojo visto: no consta` es
un dato visible y nada más.
