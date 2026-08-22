---
estado: aceptada
creado: 2026-08-21
---

# ADR-0009 — Un escenario cuyo sujeto es un modelo se verifica por lectura

## Contexto

`iniciador-code` lleva **tres veredictos y ninguno cierra**. Los tres dan lo mismo donde importa:
**0 contradichos**, la suite entera en verde, y un grupo de escenarios que no tiene con qué
sostenerse. El último dio 13 sostenidos, 0 contradichos, 9 sin sustento.

Ningún comportamiento difiere de lo que la spec afirma. Lo que falta no es corrección: es prueba.

Los nueve comparten una sola propiedad. **Su sujeto es una corrida de un agente con modelo.**
"Terminado un recorrido, existe `indice.md`". "El informe no contiene código fuente". "Un segundo
recorrido no duplica fichas". La suite de este repositorio son 399 tests deterministas y sin red,
y no invoca modelos. No es un hueco de cobertura que alguien no llenó: está afuera de lo que una
suite determinista puede observar.

### Dos intentos de cerrarlos con mecanismo, y qué enseñó cada uno

**E-20 se cortó.** El escenario decía *"el recorrido y el aviso"*; el aviso tenía test y el
recorrido no. Después del veredicto quedó escrito *"el aviso y el check"* —el check nunca fue
parte del escenario— y el recorrido se fue a otro id, en el grupo de lectura. La proposición que
había hecho fallar al escenario cambió de número y de grupo, no de estado. **El corte hizo
desaparecer la mitad difícil.**

**E-07 y E-13 recibieron mecanismo de verdad, y tampoco alcanzó.** Los dos tienen hoy código que
corre, con rojo exclusivo medido: `SessionStart` distingue un recorrido a medias de uno que no
empezó, y `dev-codebase-forma` reporta una ficha duplicada con el original al lado. El refutador
los dejó `sin sustento` igual, y con razón: **comprueban que el harness ve el estado malo, no que
el agente no lo produzca.** Es una proposición vecina, no la del escenario.

Ese es el hallazgo que motiva este ADR. No es que faltara esfuerzo ni ingenio. Es que la
proposición *"el agente no hace X"* no se deja sostener por un test que no corre al agente, y
ningún mecanismo del harness va a cambiar eso.

### Por qué sin una categoría nueva las dos salidas son malas

- **El cambio no cierra nunca.** Un `verificacion.md` con `sin-sustento` manda a trabajar, y acá
  no hay trabajo que hacer: lo que falta no se construye.
- **Se reescriben los escenarios para que quepan en lo que sí se puede probar.** Es escribir la
  spec desde el código, que es exactamente el error que el refutador existe para cazar, cometido
  por quien redacta la spec.

La segunda es peor y es la que sale sola, porque se ve como progreso.

## Decisión

**Un escenario cuyo sujeto es el comportamiento de un modelo se verifica por lectura de una
persona distinta de quien construyó, y su veredicto es `leído`.**

Es un cuarto veredicto, al lado de `sostenido`, `contradicho` y `sin sustento`. Un cambio cierra
sin `contradicho` y sin `sin sustento`; **`leído` cierra, y no vale lo mismo que `sostenido`.**

Cuatro condiciones, y se cumplen las cuatro o el veredicto es `sin sustento`:

1. **La spec lo declara antes, no después.** El escenario lleva la marca
   `· verificación: lectura` y una línea que dice por qué ningún test determinista puede
   sostenerlo. 🔴 **Un escenario que migra a `lectura` después de quedar `sin sustento` es el
   corte de E-20 con otro nombre.** La marca se pone cuando se escribe el escenario, o en una
   corrección que se anota como tal y se nombra en el veredicto siguiente.
2. **La evidencia es un registro fechado que dice qué se observó**, no que se veía bien. Una
   lectura que concluye "cumple" sin nombrar lo que miró no es evidencia de nada.
3. **Quien leyó está nombrado y no es quien construyó.** Es la misma regla que ya rige para el
   refutador, y por el mismo motivo: para quien construyó, cada decisión tuvo una razón en su
   momento.
4. **Sin las tres anteriores, `sin sustento`.** `leído` no es nunca el default y no se deduce.

### El techo, que es lo que evita que esto sea una puerta de atrás

📌 **Solo aplica a escenarios cuyo sujeto es una corrida de un modelo.** Nunca a algo que un test
determinista podría sostener y nadie escribió. Esa es toda la frontera, y es verificable leyendo
el escenario: si el sujeto es un archivo, un directorio, un hook o un check, hay mecanismo posible
y la marca no corresponde.

**El refutador juzga la categoría, no solo la lectura.** Un escenario marcado `lectura` que
podría tener test determinista se rinde `sin sustento`, y el veredicto dice por qué. Es la única
defensa mecánica que tiene esta decisión y hay que usarla.

### Es la misma operación que `rojo visto`

[ADR-0006](0006-sdd-como-metodo-de-los-proyectos.md) ya hizo esto una vez. La garantía del rojo no
se puede comprobar mecánicamente y no se pretende: se hace **visible** con una marca que el
refutador reporta junto al veredicto, y quien lee sabe cuánto vale lo que está leyendo.

`leído` es eso mismo aplicado un escalón más arriba. No convierte una lectura en una prueba.
Hace que la diferencia entre las dos esté escrita en el veredicto en vez de escondida en un
conteo.

## Consecuencias

**A favor:**

- Un cambio correcto puede cerrar. Hoy `iniciador-code` está bloqueado por escenarios que nadie
  puede probar y que nadie sostiene que estén mal.
- **Desaparece el incentivo a recortar escenarios.** Si la mitad difícil tiene una vía de
  verificación propia, ya no hay motivo para hacerla desaparecer en un renumerado — que es
  exactamente lo que pasó con E-20 y lo que este ADR viene a hacer innecesario.
- La spec puede volver a decir lo que el cambio tiene que cumplir, en vez de lo que la suite
  alcanza a mirar. Son dos cosas distintas y se estaban confundiendo.
- El veredicto pasa a tener cuatro estados que se leen distinto, en vez de tres donde uno se
  usaba para dos cosas.

**En contra:**

- 🔴 **Un cambio puede cerrar con proposiciones que nadie probó.** Es el precio, es real y no
  tiene mitigación: `leído` es más débil que `sostenido` y siempre lo va a ser.
- Un conteo de veredictos deja de leerse de un vistazo. "13 sostenidos" y "13 sostenidos, 9
  leídos" no dicen lo mismo, y quien lea rápido va a sumar.
- **Depende de que una persona lea.** Una categoría que nadie llena es peor que no tenerla: el
  cambio queda igual de trabado y ahora además hay un papel vacío.
- Es una categoría que se puede abusar, y el abuso se ve como diligencia. Contra eso está el
  techo, y el techo lo sostiene el refutador.

**Riesgo residual:** una spec que marca `lectura` de más, y un refutador que no lo discute. La
defensa es que el techo es una frase corta y comprobable —¿el sujeto es una corrida de un
modelo?— y que el refutador tiene la instrucción de rendir `sin sustento` cuando la marca no
corresponde.

## Revisión

Se revisa cuando **la suite pueda invocar un modelo** de forma determinista y barata. Ese día los
escenarios marcados `lectura` vuelven a tener mecanismo posible y la marca sobra en la mayoría de
ellos.

También se revisa si aparece un cambio donde los `leído` son mayoría. Eso no sería un problema de
esta decisión sino una señal sobre el cambio: un cambio que casi no se puede probar merece esa
conversación, no una categoría que se la ahorre.
