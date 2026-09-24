# Verificación — ES0902 O2: quién controla la seguridad, y por qué el harness no puede ser

**Estado:** cerrado · **Fecha:** 22-09-2026 · **Versión:** 0.20.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el 22-09-2026
en **dos pases**: el primero contradijo E-11 y E-25, el cambio volvió a construcción, y el segundo
los sostuvo. Corrió `python tests/correr.py -k 40_es0902` y la compuerta completa
`.\tests\Invoke-Tests.ps1`, y sondeó por afuera de las aserciones lo que se le pidió apretar —los
caminos a `FAIL`, la deducción de pertenencia, el orden entre tipos de alcance y las siete
condiciones de `PASS`—.

**Resultado: 28 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | O2 sigue `ALWAYS` con cero señales | sostenido | sí | `40_es0902_o2/test_e01`, la fila puesta en `CONDITIONAL` |
| E-02 | El dueño sigue siendo `dev-security` | sostenido | sí | `test_e02`, el dueño cambiado a `dev-backend` |
| E-03 | Una policy, un check, cero reviews, con sus ids literales | sostenido | sí | `test_e03`, el id de la policy renombrado |
| E-04 | O2 no entra en `ALGORITMOS`: sale por el camino genérico | sostenido | sí | `test_e04`, O2 agregado a la tabla |
| E-05 | Instalar O2 no agrega filas | sostenido | sí | `test_e05`, una regla `O3` agregada |
| E-06 | El registro se instala vacío y valida, también instalado | sostenido | sí | `test_e06`, una autoridad precargada en el archivo |
| E-07 | Sin autoridad declarada, ni `PASS` ni `FAIL` | sostenido | sí | `test_e07`, el estado del registro vacío cambiado |
| E-08 | El schema rechaza lo que no declara, en las cuatro capas | sostenido | sí | `test_e08`, `additionalProperties` sacado de la autoridad |
| E-09 | Ejecutar no es controlar, las cinco responsabilidades | sostenido | sí, específico | `test_e09`, las cinco agregadas a las de control |
| E-10 | Un ejecutor externo no invalida la autoridad | sostenido | sí | `test_e10`, `controla` devolviendo siempre verdadero |
| E-11 | No hay camino de un agente a una autoridad | sostenido | sí | `test_e11`, `registro_agentes` importado en el módulo |
| E-12 | `VERIFIED` sin evidencia no alcanza | sostenido | sí | `test_e12`, la etiqueta aceptada sola |
| E-13 | La pertenencia no se deduce, las cinco formas | sostenido | sí, específico | `test_e13`, `DGSEI` cableado como literal |
| E-14 | `NOT_GCABA` es el único camino a `FAIL` | sostenido | sí, las dos mitades | `test_e14`, un estado sin resolver convertido en `FAIL`, y el chequeo de conflicto apagado |
| E-15 | Lo que falta tiene su propio estado, los siete | sostenido | sí | `test_e15`, uno sacado de `SIN_RESOLVER` |
| E-16 | La autoridad de otro proyecto no cubre | sostenido | sí | `test_e16`, la cobertura ignorada |
| E-17 | La contención la declara el objetivo, y `GLOBAL` no es excepción | sostenido | sí | `test_e17`, `GLOBAL` cubriendo todo |
| E-18 | Varias autoridades con alcances explícitos conviven | sostenido | sí | `test_e18`, la autoridad informada tomada de la primera del registro |
| E-19 | Una autoridad vencida no rige | sostenido | sí | `test_e19`, el corte de vencimiento anulado |
| E-20 | Sin `effectiveTo` no hay vigencia, las cuatro formas | sostenido | sí | `test_e20`, la ausencia tratada como vigente |
| E-21 | Dos organizaciones sobre el mismo objetivo, en conflicto | sostenido | sí | `test_e21`, el chequeo de conflicto apagado |
| E-22 | Dos registros de la misma organización no son conflicto | sostenido | sí | `test_e22`, el conflicto comparando por `authorityId` |
| E-23 | Si sólo uno rige, resuelve el vigente | sostenido | sí | `test_e23`, las vencidas contadas como vigentes |
| E-24 | `PASS` exige las siete condiciones | sostenido | sí | `test_e24`, el caso base dejando de aprobar |
| E-25 | `PASS` de O2 no aprueba nada más | sostenido | sí | `test_e25`, un literal `SECURITY_APPROVED` metido en el módulo |
| E-26 | Los nueve estados con ese nombre, uno solo aprueba | sostenido | sí | `test_e26`, un estado renombrado |
| E-27 | Todo resultado conserva `ES0902 / 6.2 / §3 / O2` | sostenido | sí | `test_e27`, la sección cambiada a `7.1` |
| E-28 | Ningún agente nuevo, y los dos controles instalados | sostenido | sí | `test_e28`, el check sacado del registro |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Los 28 de esta tabla llevan
> `sí`: la pasada se corrió entera, mutación por mutación, con `__pycache__` borrado antes y después
> de cada una, y las tres aserciones que cambiaron después del primer veredicto se volvieron a ver
> en rojo con la suya.

La compuerta, al cierre:

```
.\tests\Invoke-Tests.ps1
  250/250 pasaron (PowerShell)
  24625/24625 pasaron (python), de los cuales 281 son 40_es0902_o2_autoridad_de_control
  24875/24875 pasaron
```

## E-11 y E-25, los dos contradichos del primer pase

Los dos eran **la misma falla, dos veces, y era de la spec y no del código**: una proposición de la
forma *"el módulo no nombra X"* que el artefacto rompe en su propio docstring.

```
E-11  "el módulo no nombra a `dev-security`"     lo nombra en la línea 15, para declarar la frontera
E-25  "el módulo no nombra `APPROVED` ni `C2`"   nombra a `C2` en la línea 36, por lo mismo
```

El guard del test —`_literales()`, que resta los docstrings— estaba construido de modo que no
alcanzaba la afirmación. Y el docstring **es devolvible**: `modulo.__doc__` contiene las dos
cadenas.

**La decisión: se arregló la spec, no el docstring.** Las dos líneas de prosa son exactamente las
que declaran el límite —*"el harness no puede ser la autoridad: ni `dev-security`, ni sus skills…"*,
*"`PASS` no es la evaluación de seguridad, no es C2…"*— y borrarlas para que un escenario mal
escrito pase habría dejado el artefacto peor y el test igual de flojo. La proposición era un **mal
proxy**: medía el archivo para hablar de un camino.

Lo que quedó en su lugar es más fuerte que lo que había:

```
E-11  el módulo NO IMPORTA NI LEE el registro de agentes   barrido de imports por AST,
      + ningún literal OPERATIVO nombra un agente o skill  con la lista completa clavada
      + una autoridad que dice ser un agente no establece nada
E-25  ningún literal OPERATIVO nombra `APPROVED` ni `C2`   + las tres proposiciones que ya estaban,
      y una cuarta promovida del test a la spec
```

El refutador midió el barrido nuevo contra cinco mutaciones y muerde en cuatro: un import de
`registro_agentes` arriba, uno anidado adentro de una función, uno por `importlib`, y **cualquier
import de más**, porque la comparación es por igualdad exacta contra la lista. La quinta —
`__import__` dinámico, sin sentencia `import`— se le escapa, y no aplica hoy: el módulo no tiene
ninguna llamada de carga dinámica, verificado sobre la lista completa de sus llamadas.

Y se agregó a la spec, en `Cómo se verifica`, la nota que evita que vuelva a pasar: **un escenario
que dice "el módulo no nombra X" mide el archivo y no el comportamiento, y prohíbe la línea de prosa
que declara la frontera.**

## Lo que la verificación encontró y no habría encontrado un test verde

1. **Los dos contradichos de arriba.** Un test verde no los podía encontrar: el guard estaba escrito
   para no mirar donde estaba la ocurrencia.

2. **Una aserción muerta adentro de E-14.** La escribí yo, y comparaba `"PASS"` con `"PASS"` sin
   llamar nunca al check:

   ```python
   t.igual("E-14 con un organismo del GCABA al lado no reprueba", "PASS",
           _estado([...]) if False else "PASS")
   ```

   El `if False else "PASS"` abarcaba el tercer argumento entero. Era la única del archivo así, y
   llevaba la marca `rojo visto: si` de un escenario que nunca la pudo ver en rojo. Reemplazada por
   una viva: con un organismo del GCABA controlando al lado, una ajena da
   `CONFLICTING_SECURITY_AUTHORITY_EVIDENCE` y no `FAIL`. La propiedad que decía cubrir se cumple
   —el refutador la barrió aparte con 324 casos de dos autoridades— así que no cambió ningún
   veredicto; lo que cambió es que ahora la sostiene una aserción.

3. **Que `FAIL` tiene un solo sitio de emisión, medido y no leído.** Barrido de **3456** casos de
   una autoridad cruzando responsabilidad × membresía × evidencia × `effectiveTo` × `effectiveFrom`
   × alcance × nombre: `FAIL` sale únicamente de `(NOT_GCABA, SECURITY_CONTROL)`. Y de **324** casos
   de dos autoridades: ningún `FAIL` con un organismo del GCABA controlante y vigente al lado. Es la
   propiedad que más importa de esta regla, porque un `FAIL` de más acusa a un organismo.

4. **Que no hay orden implícito entre tipos de alcance, medido sobre la matriz 6×6.** Con el mismo
   `value` y sin cadena declarada, la diagonal aprueba y **nada** fuera de la diagonal cubre. `GLOBAL`
   sobre `PROJECT` no cubre con ningún valor, ni con `*`, ni con `ALL`, ni vacío.

5. **Que las siete condiciones de `PASS` son siete y no seis con una repetida.** Dos comparten estado
   de salida —`AUTHORITY_EVIDENCE_INSUFFICIENT`— pero dan vuelta predicados distintos, `identidad`
   contra `controla`. Sin esa medición, un test con una condición duplicada se lee igual de
   completo.

6. **Que la deducción de pertenencia está cerrada por estructura y no por una lista de prohibidos.**
   Los campos de los que se podría deducir —`domain`, `employer`, `namespace`— los rechaza el schema
   por `additionalProperties: false` antes de llegar al check. No hay de dónde deducir.

## Lo que queda abierto, anotado y no escondido

1. **El barrido de imports de E-11 no atrapa `__import__` dinámico.** Es la única fuga que le queda,
   y hoy no aplica: el módulo no tiene ninguna llamada de carga dinámica —sin `__import__`, sin
   `eval`, sin `exec`, sin `getattr`, sin `importlib`—, verificado sobre la lista completa de sus
   llamadas. Queda dicho acá y no como pendiente porque cerrarlo exigiría un barrido de llamadas que
   ningún otro escenario del harness tiene, y el día que haga falta va a hacer falta para todos.

2. **`reglas/` se sobrescribe en cada `-Update`.** El registro de autoridad es del proyecto y vive
   donde el instalador copia con `-Force`, igual que `database-profiles.json`. Un proyecto que lo
   llene y actualice el harness pierde lo que escribió. Es una deuda que O2 hereda y no crea.

3. **La evidencia de autoridad no la produce nadie todavía.** Mientras el registro esté vacío, toda
   corrida real da `SECURITY_CONTROL_AUTHORITY_UNRESOLVED`. Es el estado correcto y es también el que
   más invita a que alguien llene el archivo con la organización que le parece.

4. **La exigencia de `effectiveTo` va a rozar.** Ninguna acta de asignación escrita hasta hoy tiene
   por qué traer fecha de fin, así que el estado más frecuente con el registro lleno va a ser
   `SECURITY_AUTHORITY_CURRENT_STATUS_UNRESOLVED`. Es lo que el paquete pide —*no reusar en silencio
   una asignación vieja*— y es lo primero que alguien va a querer aflojar.

## Lo que ningún test cubre y se mira con los ojos

- **Que el acta que sostiene una autoridad diga lo que dice.** El check verifica que la evidencia
  sea de una de las seis clases autoritativas y que traiga su referencia. Que esa referencia apunte
  a un documento real, que ese documento asigne el control de seguridad y que lo asigne a ese
  organismo es criterio de quien firma, y ningún test lo puede contradecir. **El nombre de la
  organización no abre ningún camino** —`dev-security` vale lo mismo que `Pepe`—, pero un acta que
  nombre a cualquiera la juzga quien la firma, no el harness.
- **Que el registro de un proyecto instalado esté lleno y al día.** El harness lo instala vacío a
  propósito. Que alguien lo complete, y que lo complete con lo que corresponde, es del proyecto.
