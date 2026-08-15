---
name: hu-escribir
description: Use when writing, splitting, reviewing or correcting historias de usuario for a GCBA or DGISIS project — ABM de backoffice, épicas, criterios de aceptación, escenarios Gherkin — and especially when the only source is a maqueta, a Figma screen or an especificación prefuncional and the obligatoriedad, límite, mensaje literal or estado of a field is not stated anywhere.
---

# Escribir historias de usuario

Estas historias las toma una IA que después escribe el código. El Gherkin clásico no
alcanza: el `Entonces` describe lo que **ve** el usuario, no lo que tiene que ser cierto en
la implementación. Por eso cada escenario lleva dos bloques más: **Resultado esperado** y
**Check IA**.

## 🔴 La ley: no inventar

Se escribe **únicamente** lo que la maqueta o la documentación sostienen.

- Un campo sin asterisco rojo **no es obligatorio**.
- Si el dato no está, **no se cubre**: va a la lista de definiciones pendientes.
- **Violar la letra es violar el espíritu.**

Una IA que redacta requerimientos produce **ficción plausible** si se la deja. Y la ficción
plausible es peor que un hueco visible: se lee bien, nadie la cuestiona, entra al sprint y
se construye.

### Excusas y realidad

| Excusa | Realidad |
|---|---|
| "Tiene sentido que ese campo sea obligatorio" | Manda la maqueta. Sin asterisco rojo, es opcional. |
| "Todos los ABM tienen filtro por fecha" | Este no. Volvé a mirar la maqueta. |
| "Falta el máximo de caracteres, pongo 255" | No se inventa un número. Va a definiciones pendientes. |
| "El diálogo de borrado seguro advierte que es irreversible" | Si no está maquetado, no se describe. |
| "La pantalla pública muestra esa columna" | La pantalla pública define **qué** produce el backoffice, no **cómo** se ve. |
| "Es obvio que hay un estado Borrador" | Los estados se leen de la maqueta, o no existen. |
| "El otro módulo funciona igual" | Las maquetas se copian entre módulos y arrastran el texto del original. Verificá cada literal. |
| "El Check IA es técnico, ahí puedo precisar" | Precisión de implementación sí; decisiones de producto no. Ver la sección del Check IA. |
| "Sin un criterio el desarrollador no puede avanzar" | Con el hueco señalado, pregunta. Con la regla inventada, no pregunta: la construye. |

### Red flags — parar y volver a la maqueta

- Estás por escribir un mensaje de error que no leíste
- Estás por marcar un campo obligatorio "porque corresponde"
- Estás describiendo una pantalla de la que no viste la imagen
- Estás poniendo un número — MB, caracteres, resultados por página — que no verificaste
- Estás copiando reglas de otro módulo "porque son iguales"
- Estás escribiendo un Check IA que define un comportamiento que la maqueta no muestra

**Todas significan lo mismo: no lo sabés. Va a definiciones pendientes.**

⚠️ Antes de escribir sobre un módulo, **verificá la fecha de sus maquetas**. Se versionan sin
avisar y las nuevas contradicen a las viejas. Listalas con `Glob`, que las devuelve ordenadas
por fecha.

## La forma del entregable

Texto plano, **sin sintaxis markdown**: se pega en el gestor de tickets, que renderiza `##` y
`**` como basura.

```
HU N - <Acción> de <entidad>
Objetivo
<un párrafo>

Historia de Usuario
Como <rol>
Quiero <capacidad>
Para <beneficio>

Descripción Funcional
- <viñeta con guion>

Reglas de Negocio
- <viñeta con guion>

Criterios de Aceptación

Escenario 1 - <título>
Dado <contexto>
Cuando <acción>
Entonces <resultado observable>

Resultado esperado
<en qué estado queda el sistema>

Check IA
- <condición técnica comprobable>
```

- **Un archivo por módulo**, con las historias adentro en bloques recortables.
- **Orden canónico: Alta → Listado → Modificación → Baja.** El alta primero porque define el
  modelo de datos; el resto se apoya en ella.
- **Referencias entre historias por nombre, nunca por número.** Si se reordenan, los números
  quedan colgados. El identificador real es la key del gestor de tickets.

### La historia se entiende sola

Lo que se pega en el ticket **es todo lo que va a tener el que lo lea**. No tiene el repo, no
tiene tus notas. Entonces la historia no nombra ningún artefacto interno: ni archivos, ni
identificadores de registro, ni rutas, ni nombres de maqueta.

Cuando falta una definición, **afirmala en la historia y terminá ahí**:

| ❌ | ✅ |
|---|---|
| El literal del mensaje de rechazo no está maquetado. Ver el registro de huecos. | El literal del mensaje de rechazo no está maquetado para este módulo. |
| Ver H-13 por el archivo vigente. | La maqueta no presenta el archivo actualmente asociado ni un control para quitarlo, y no define si al editar es obligatorio cargar uno nuevo. |

La frase afirmativa ya hace el trabajo: le dice al desarrollador **que no lo invente**. La
remisión no le agrega nada, porque no puede seguirla.

📌 **La trazabilidad va del registro interno hacia la historia, nunca al revés.** El registro
de definiciones pendientes cita a qué historia afecta cada una; la historia no cita al
registro. Invertirlo convierte el entregable en un documento que solo funciona con el repo
al lado.

**Test:** leé la historia imaginando que la abrís en el gestor de tickets sin acceso a nada
más. Si alguna línea te manda a un lugar al que no podés ir, sobra.

## Qué hace bueno a un Check IA

📌 **No reformules el `Entonces` con otras palabras. Agregá precisión de implementación.**

Inútil:
```
- Se muestra un mensaje de error.        <- ya lo dijo el Entonces
- El sistema funciona correctamente.     <- no es verificable
```

Hace trabajo:
```
- La búsqueda se aplica sobre el conjunto completo de registros, no sobre la página visible.
- No cargar un archivo nuevo no se interpreta como campo vacío.
- La baja no se ejecuta al accionar el control, sino únicamente al confirmar el diálogo.
```

El segundo es el canónico: reutilizar la validación del alta en el formulario de edición y
terminar borrando el archivo que nadie quiso tocar. Aparece solo, en todos los ABM, si nadie
lo escribe.

**Método:** por cada escenario preguntarse *"¿cuál es la forma más plausible de implementar
esto mal?"* — y escribir esa condición.

## 🔴 Un Check IA no decide reglas de negocio

Es la escapatoria más fácil de este bloque: *"el Check IA es técnico, así que acá puedo
precisar"*. **No.** La ley de no inventar rige adentro del Check IA igual que afuera, y acá
es más peligrosa: nadie audita un bullet técnico, y una regla de producto disfrazada de
verificación entra al sprint sin que nadie la haya decidido.

Pasá cada bullet por esta pregunta:

| | |
|---|---|
| **¿Previene una trampa de implementación conocida?** | **Se queda.** No decide nada del negocio, evita un bug |
| **¿Resuelve una decisión de producto que la fuente no muestra?** | **Va a definiciones pendientes**, y el bullet se reescribe para cubrir la parte observable sin decidir la regla |

📌 **No lo borres: reescribilo.** El objetivo no es un Check IA más flojo, es que el
desarrollador reciba precisión donde la hay y una señal clara de "esto no está definido"
donde no la hay.

### El ejemplo, con las dos caras en el mismo campo

Un filtro por rango de fechas, sobre un listado que muestra solo fecha y un detalle que
muestra fecha y hora.

```
Decide una regla de producto  ->  fuera
- El rango incluye los registros de la fecha desde y de la fecha hasta.

Previene una trampa            ->  se queda
- Los registros tienen hora de recepción además de fecha, pero el listado muestra solo
  la fecha: comparar la fecha hasta contra el inicio del día excluye todos los mensajes
  recibidos ese día.
```

El primero decide algo que nadie definió. El segundo no decide nada — describe un bug que
aparece **con cualquier criterio que se elija**, y que no se ve mirando la pantalla del
listado. Ese es el trabajo del bloque.

## Antes de dar por terminada una historia

- [ ] Cada obligatoriedad tiene su asterisco rojo en la maqueta
- [ ] Cada literal de UI fue leído, no supuesto, y corresponde a **este** módulo
- [ ] Cada número sale de la maqueta o del documento
- [ ] Cada regla de negocio tiene al menos un escenario
- [ ] Cada escenario tiene Resultado esperado y Check IA
- [ ] Ningún Check IA repite el `Entonces` con otras palabras
- [ ] Ningún Check IA decide una regla de negocio que la fuente no muestra
- [ ] Lo que no se pudo responder está en definiciones pendientes, no completado por analogía

## Este checklist no reemplaza la verificación

Lo pasa el mismo que escribió, con el contexto ya formado por sus propias decisiones. Sirve
para no entregar cualquier cosa; no sirve para detectar la ficción plausible, porque cada
afirmación inventada tuvo una razón al momento de escribirla.

Para eso está el agente **`hu-refutador`**, que llega sin esa razón y solo puede confiar en
lo que ve. Devuelve, por cada afirmación: `sostenido`, `contradicho` o `sin-sustento` — y
cada `sin-sustento` es una definición pendiente que alguien iba a inventar.
