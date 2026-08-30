---
estado: aceptada
creado: 2026-08-30
---

# ADR-0010 — Firma delegada de una lectura, cuando son muchas

## Contexto

Al 30-08-2026 hay **dieciséis** escenarios de lectura sin firmar, en cuatro archivos vivos:
`iniciador-code` (nueve — E-07, E-11, E-12, E-13, E-14, E-15, E-16, E-17, E-20b),
`contexto-de-proyecto` (uno — E-20), `dev-refutador-lee-el-contrato` (dos — E-08, E-09) e
`interfaces-identidad-ambientes` (uno — E-18, y ese directorio ni siquiera tiene `lectura.md`
todavía). Un quinto archivo, `mapa-de-nodos` (cuatro), **queda fuera de esta decisión por
completo**: Nahue lo dejó diferido a propósito el 22-08-2026, ratificado el 28-08-2026 —
*"esta firma se va a hacer cuando lo corro en el proyecto"*— y esta ADR no lo toca ni lo cuenta.

[ADR-0009](0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md) puso una condición dura
en el cuarto veredicto: *"Quien leyó está nombrado y no es quien construyó."* Es la misma regla
que ya rige a los tres refutadores del repositorio —`harness-spec-refuter`, `dev-refutador`,
`hu-refutador`— y viene de más atrás, de [ADR-0006](0006-sdd-como-metodo-de-los-proyectos.md):
*"Quien construye no verifica, porque para quien construyó cada decisión tuvo una razón en su
momento."*

Nahue pidió aflojar esa regla: *"si tenemos que firmar lo podes hacer vos y esa regla la podemos
cambiar por qué ya las decisiones las tomamos en su momento en conjunto"* (30-08-2026). La
objeción que se le devolvió no fue teórica: en esta misma semana de trabajo, tres defectos reales
los encontró alguien sin el punto ciego de quien construyó, nunca el agente revisando lo propio.

1. **El `rojo visto` de E-01 era timing-dependiente.** `harness-spec-refuter`, corriendo la
   mutación de verdad tres veces, encontró que comparar solo bytes fallaba en 2 de 3 —
   `docs/cambios/dev-refutador-lee-el-contrato/verificacion.md`. Quien construyó lo había dado
   por verde.
2. **Una fuente borrada quedaba `status: "current"`.** Lo encontró el propio recorrido corriendo
   sobre `reservas`, un proyecto que el agente no conocía de antes —
   `Pendientes/Fix-Harness/PENDIENTES-FH.md`, *"The contract calls a source `current`..."*, y
   `C:\Users\Asus\lecturas-0.14.0\corrida-3-informe.md`.
3. **Un bullet que envolvía a dos líneas entraba cortado a la mitad.** Misma corrida, mismo
   archivo, mismo motivo: nadie construyendo el script lo había visto, porque este repositorio
   escribe sus bullets en una sola línea y hizo falta un proyecto ajeno para que el defecto
   apareciera.

Ninguno de los tres lo vio el agente mirando su propio trabajo. Los tres los vio un refutador
corriendo la mutación de nuevo, o un recorrido sobre terreno que quien construyó no conocía. Es
la evidencia concreta de que la condición 3 de ADR-0009 no es ceremonia: es la que atrapa esto.

Al mismo tiempo, la objeción no resuelve el problema real que Nahue nombra: **hoy hay dieciséis
lecturas pendientes y una sola persona para dictarlas todas**, y una regla que exige su presencia
para cada una, sin distinguir volumen, hace que la vía de ADR-0009 —pensada para que un cambio
correcto pueda cerrar— termine bloqueando exactamente lo que existía para destrabar. Su segundo
mensaje da el criterio real: *"si son muchos los firmas, si son muy pocos los consultamos
conmigo... vos me traes y me lo consultas, te parece?"*

## Decisión

**Con cinco escenarios pendientes de firma o más, en el mismo `lectura.md`, quien construyó puede
firmar — y la firma queda rotulada como delegada, nunca como si fuera una lectura independiente.**
Con menos de cinco, no cambia nada: se firma como ya lo permite ADR-0009, formalizando el camino
que ya se había ofrecido — una sesión de firma dictada, sin ceremonia de ir al `.md`.

Esto es una **excepción visible a la condición 3 de ADR-0009, y a nada más.** Las condiciones 1
(la marca declarada antes), 2 (una observación fechada y concreta, no "cumple") y 4 (el techo que
juzga la categoría) siguen exactamente iguales, con o sin firma delegada. ADR-0009 no se edita:
esta ADR se apoya en ella y le agrega un permiso acotado sobre quién puede sostener la condición 3.

### El umbral: cinco, y por `lectura.md`, no global

**Cinco o más escenarios pendientes en el mismo `lectura.md` es "muchos".** No hay precedente al
que anclarlo — no existe en este repositorio una regla previa que decida *quién verifica* según
un conteo, sólo umbrales sobre *otra cosa*: los 400 ms de `E-29`, los `MAX_HALLAZGOS = 8` de
`comun/hooks/lib/reglas.py:16`, el `RENDER_MAX = 8` de `comun/bin/docimg.py:39`. Cinco se elige
sin mirar primero cómo cae en el backlog de hoy, y se dice acá para que quede a la vista si algún
día se corrige *"para que dé bien"*, que es justo lo que `write-a-verdict` prohíbe para el umbral
de E-29: *"un umbral que se acomoda al resultado deja de medir."*

**Es por archivo, no global**, por tres motivos:

1. **Es la misma granularidad que ya tiene todo lo demás.** `spec.md`, `verificacion.md` y
   `lectura.md` son artefactos por cambio; el resultado de un `verificacion.md` nunca depende del
   estado de otro. Un umbral global inventaría un ledger cruzado que hoy no existe en ningún
   lado, sólo para esta regla.
2. **Un umbral global resucita a `mapa-de-nodos` por la puerta de atrás.** Sumar sus cuatro al
   total empuja a los demás hacia "muchos" aunque cada uno, solo, sea chico — exactamente lo que
   la decisión de Nahue de dejarlo afuera pretende evitar.
3. **La prueba está en los números de hoy.** `iniciador-code` (9) es la única que un umbral
   razonable en cualquier punto entre 3 y 8 deja en "muchos"; `contexto-de-proyecto` (1),
   `dev-refutador-lee-el-contrato` (2) e `interfaces-identidad-ambientes` (1) quedan en "pocos"
   bajo cualquiera de esos valores. Que las tres chicas queden en el camino que no cambia ninguna
   regla es la lectura correcta del pedido de Nahue, no un ajuste posterior.

El conteo se rehace cada vez que alguien va a firmar: **son los `## E-nn` de ese `lectura.md` que
todavía no tienen `Observado` lleno**, en ese momento, no los que tenía el archivo al escribirse.
Un archivo firmado a medias vuelve a contarse por lo que le queda.

### La firma, cuando son muchas

Rotulada, siempre. La etiqueta cambia de palabra a propósito, para que grepear el archivo alcance:

```markdown
**Firmó (delegado):** Claude · **Autorización:** Nahue Palacio — ADR-0010, «si tenemos que firmar
lo podes hacer vos» · **Fecha:** <fecha> · **Corrida sobre:** <repositorio>
```

`Leyó:` sigue significando exactamente lo que significaba antes de esta ADR: un no-constructor.
Escribir `Leyó:` con el nombre de quien construyó es lo que esta decisión existe para no permitir.

**No hace falta un permiso por lote.** La autorización de Nahue es la propia ADR, aceptada una
vez: cruzar el umbral en un `lectura.md` la licencia, sin volver a consultarlo cada vez — es
literalmente lo que pidió: *"esa regla la podemos cambiar."* Pedirle un visto bueno por archivo
reintroduciría la fricción que la excepción existe para sacar.

El archivo declara arriba el conteo que licenció la firma, y no es un dato de confianza: el
refutador lo recuenta contra los `## E-nn` reales del archivo, la misma disciplina con la que ya
juzga si la marca `lectura` está merecida.

```markdown
> 📌 Firma delegada bajo ADR-0010: 9 escenarios pendientes al firmar (≥ 5).
```

**Se cuenta aparte, nunca junto con una lectura independiente.** El repositorio ya separa
`leído` de `sostenido` en cada conteo por el mismo motivo con el que separa `rojo visto: sí` de
`no consta`: para que nadie sume dos cosas que no valen lo mismo. La misma lógica exige no perder
la distinción acá. El costo es bajo — una palabra más en la celda del veredicto, siguiendo el
mismo patrón que ya usa la columna `Rojo visto` con sus calificadores libres (`sí, específico`,
`sí, de módulo`) — y el costo de no hacerlo es real: un `leído` delegado y uno independiente no
pesan lo mismo, y esta ADR existe precisamente para que esa diferencia no se esconda.

### La firma, cuando son pocas

No cambia ninguna regla de ADR-0009. Sigue siendo un no-constructor quien observa y firma; quien
construyó sólo transcribe. Lo único que se formaliza es el camino, para que no haga falta la
ceremonia completa de abrir el `.md` en vivo:

1. Se trae el material ya reunido a la sesión — la corrida ya hecha, o se corre si falta.
2. Quien firma —Nahue, u otro no-constructor— mira el material y dicta, con sus palabras, qué
   observó en cada escenario.
3. Quien construyó transcribe textual a `Observado`, sin editar el sentido.
4. La firma queda `**Leyó:** <nombre> · **Fecha:** <fecha> · **Corrida sobre:** <repositorio>`,
   idéntica a una lectura escrita a mano. No lleva rótulo especial porque no lo necesita: es
   exactamente lo que ADR-0009 ya permitía, sólo que dicho en voz alta en vez de tecleado.

## Consecuencias

**A favor:**

- El backlog de dieciséis deja de estar trabado por la disponibilidad de una sola persona para
  dieciséis sesiones de lectura, sin tocar la letra de ADR-0009.
- Sigue habiendo una diferencia visible entre lo que se firmó con el punto ciego de quien
  construyó y lo que no — nunca se dispersa en un `leído` sin más.
- Formaliza algo que ya se estaba haciendo de hecho para los casos chicos, sin necesidad de
  excepción.

**En contra:**

- 🔴 **La condición 3 existe porque atrapa cosas reales, y una firma delegada la pierde para esos
  escenarios exactamente.** Los tres defectos del Contexto no son hipotéticos: son de esta misma
  semana. El rótulo `delegado` no recupera esa capacidad de atrapar — sólo dice, honestamente,
  que no estuvo.
- **El riesgo de partir un cambio en varios `lectura.md` chicos para esquivar el umbral existe y
  no tiene defensa mecánica**, la misma clase de riesgo residual que ya tiene ADR-0009 con la
  marca `lectura` de más: la defensa es que el refutador lo note, no un check.
- **El umbral de cinco no tiene precedente y puede estar mal en cualquier dirección.** Se dice acá
  así, sin maquillaje, y se revisa si la evidencia lo pide.
- Quien lee rápido un `verificacion.md` puede seguir sin fijarse en el calificador y leer
  `leído` sin más — el mismo riesgo que ya corre `leído` contra `sostenido`, un escalón más abajo.

**Riesgo residual:** una firma delegada que resulte equivocada — algo que una lectura
independiente habría visto y esta no. El día que eso pase, se dice en el veredicto que la
encuentre, sin pulirlo, igual que el resto de este repositorio trata sus propios defectos.

## Revisión

Se revisa el mismo día que se revise ADR-0009: si aparece una forma de invocar un modelo desde la
suite, la categoría entera de `lectura` pierde sentido y esta excepción con ella.

Se revisa la primera vez que una firma delegada se demuestre equivocada — algo que una lectura
independiente hubiera atrapado y esta no. No se corrige en silencio: se anota con su número, como
ya hace este repositorio con cada corrección de rumbo.

También se revisa si, sostenido durante dos versiones seguidas, ningún `lectura.md` vuelve a
cruzar el umbral. Sería la señal de que la presión que motivó esta excepción ya no existe, y la
conversación correcta es si sigue haciendo falta tenerla escrita.
