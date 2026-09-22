# D4: verificar lo que se renderiza, sin inventar el tamaño de la pantalla

**Estado:** construido · **Fecha:** 2026-09-20

## Qué problema resuelve

> "El código de las aplicaciones debe ser responsive, adaptándose al dispositivo con el que se
> visualiza." — ES0901 §7.1 D4, pág. 12

Después de D3, que no admitía comprobación mecánica, D4 vuelve a un `CHECK`: tiene comportamiento
observable. Se renderiza, se varía el viewport, se mira qué pasa. Sus dos controles
—`responsive-ui-required` y `responsive-behavior`— están declarados y no existen.

Lo que hace difícil a D4 no es la regla, son dos huecos que la regla no llena:

1. **El estándar no dice contra qué tamaños.** No nombra breakpoints, ni modelos de dispositivo, ni
   cuántos viewports hay que probar. Escribir `320 · 768 · 1024 · 1440` en un archivo del harness y
   verificarlos como si fueran la norma es inventar texto normativo — el mismo error que D3 cerró
   con su vocabulario de dimensiones, acá con números.
2. **Todo lo fácil de comprobar es lo que no prueba nada.** Que Bootstrap esté instalado, que
   Obelisco esté instalado, que haya media queries, que el framework soporte layouts adaptables:
   todo eso se detecta en segundos y ninguno dice si la aplicación se ve bien en un teléfono. Un
   check que los mire se pone verde siempre.

## Qué queda afuera

- **Correr un navegador.** El harness no renderiza nada y no abre Playwright. La corrida entra como
  **dato**: un reporte de ejecución con su build, su runtime y sus resultados por viewport. Quien la
  ejecute son las skills que ya están instaladas —`dev-responsive`, `dev-test-automation`,
  `dev-quality-validation`—, y cablear esa ejecución es otro cambio.
- **Un segundo framework de automatización.** No se crea ninguno para D4. Si mañana hace falta
  ejecutar, se usa la capacidad de calidad que ya existe.
- **Definir la matriz de viewports.** Es configuración operativa del proyecto y entra con su fuente
  declarada. Sin una defendible, el check lo dice y no la completa.
- **Accesibilidad.** Es otra obligación, con su propia skill —`dev-accessibility`— y su propio
  camino. Que algo se adapte al ancho de pantalla no dice nada sobre lectores de pantalla ni sobre
  contraste.
- **La homologación de Obelisco.** Que el design system esté aprobado y en la versión correcta es
  G1. D4 no lo verifica y no lo hereda.
- **Una `REVIEW` para D4.** El pedido lo dice y se respeta: el resultado central de D4 es
  mecánicamente comprobable y no se le agrega un control cualitativo para emparejarlo con D3.
- **Los otros productores de señales.** `frontendPresent` es la cuarta señal con productor; las diez
  restantes siguen sin nadie.
- **Los otros 58 controles declarados.** Siguen declarados y sin construir.

## Las decisiones, y por qué

### La matriz de viewports se declara con su fuente, o no hay resultado

El check exige una matriz explícita, y exige que diga **de dónde sale**:

```text
PROJECT_UX_REQUIREMENT        lo que el proyecto pidió
GCBA_DESIGN_SYSTEM_GUIDANCE   la guía del organismo o del design system
SUPPORTED_DEVICE_REQUIREMENT  los dispositivos que hay que soportar
TEAM_APPROVED_TEST_PROFILE    un perfil de prueba que el equipo aprobó
```

Sin matriz, o con una que no declara su fuente: `VIEWPORT_MATRIX_UNRESOLVED`. No es un `PARTIAL`
—no falta ejecutar algo, falta saber qué había que ejecutar— y no es un `FAIL`.

Se descartó que el harness traiga una matriz por defecto. Un default se lee normativo: la primera
persona que lo vea va a asumir que el estándar pide esos cuatro anchos, y no los pide.

🔴 **Ningún artefacto de D4 trae un valor de breakpoint.** Es un escenario y se verifica por patrón,
igual que la guarda de internos de proveedor en D1 y D2.

### El check mira una corrida, no el repositorio

Lo que sostiene un `PASS` es **evidencia de comportamiento renderizado**, y las clases de evidencia
se parten para que eso no se pueda confundir:

```text
RENDERED_BEHAVIOR_RUN       una corrida sobre el objetivo, con su build y su runtime
SCREENSHOT                  una imagen de esa corrida
HUMAN_CONFIRMATION          alguien lo miró
REPOSITORY_DEPENDENCY       Bootstrap, Obelisco: que están instalados
STYLESHEET_CONFIGURATION    media queries, hoja mobile
DESIGN_SYSTEM_USAGE         se usa el design system
AGENT_STATEMENT             alguien dice que es responsive
```

Sólo la primera sostiene un caso que pasa. Las tres últimas **nunca** sostienen nada: son evidencia
de lo que hay, no de lo que se ve. Una captura y una confirmación humana acompañan y no alcanzan
solas: una captura de desktop es exactamente la forma en que un frontend roto en mobile pasa.

### La evidencia está atada al build y al runtime que se probaron

Una corrida sobre otro build es una corrida sobre otro sistema. La evidencia puede declarar
`buildId` y `runtime`; si declara uno distinto al del caso, no cuenta. Es la misma regla de alcance
que D1 y D2 aplican a la aplicación y al ambiente, con los dos campos que acá importan.

Eso es también lo que hace determinista al check: para un build, una matriz, un runtime y un
conjunto de datos fijos, el resultado es el mismo. Lo dice el pedido y se comprueba.

### `PARTIAL` no se sube a `PASS`, y el desktop no tapa al mobile

Siete estados, uno aprueba:

```text
PASS                        todos los casos requeridos corrieron, sin defecto material
FAIL                        un defecto material en un viewport requerido
PARTIAL                     falta ejecutar casos, o falta evidencia
NOT_APPLICABLE              frontendPresent = FALSE
APPLICABILITY_UNRESOLVED    frontendPresent = UNRESOLVED
VIEWPORT_MATRIX_UNRESOLVED  no se sabe contra qué había que probar
TEST_TARGET_UNAVAILABLE     no hubo dónde correr
```

Un caso que no se ejecutó deja el resultado en `PARTIAL` aunque todos los demás pasen. Y un `FAIL`
en un viewport requerido manda sobre cualquier cantidad de viewports que pasen: ignorar el mobile
porque el desktop anda es el modo de falla que el pedido nombra explícitamente.

### Un defecto pesa por materialidad

La misma palabra que D3, por la misma razón. Un defecto declarado `MATERIAL` —contenido recortado,
superposición, una acción crítica inalcanzable, scroll horizontal por layout, navegación o
formularios inusables— da `FAIL`. Uno `MINOR` no. Y un defecto **sin materialidad declarada** no se
ablanda: deja el caso sin resolver y el resultado en `PARTIAL`.

### D4 no contesta por accesibilidad ni por G1

Son tres preguntas distintas sobre la misma pantalla:

```text
G1  el design system esta homologado y en la version correcta
D4  la interfaz se adapta al dispositivo
    la interfaz es accesible          ← otra obligacion, otra skill
```

El resultado de D4 no nombra ninguna de las otras dos, y que Obelisco esté instalado y homologado no
mueve su resultado ni un estado.

## Qué se construye

| Artefacto | Qué hace |
|---|---|
| `harnesses/desarrollo/controles/policies/responsive-ui-required.md` | El contrato de la policy |
| `harnesses/desarrollo/controles/checks/responsive-behavior.py` | El check: matriz, corrida, defectos y las tres fronteras |
| `harnesses/desarrollo/reglas/control-registry.json` | Suma los dos controles de D4 |
| `docs/normativa-7.1.md` | La cuarta señal y el primer check que mira una corrida |
| `tests/casos/29_d4_comportamiento_responsive.py` | Los escenarios de este cambio |

La fila de `D4` en la matriz **no se toca**: ya declara su modo, su señal, su policy y su check, y
no se le agrega una review. No se agrega ningún módulo de señales: se reusa el de D1.

## Escenarios verificables

Entre paréntesis, el `D4-nn` del pedido de instalación.

### La señal

- **E-01** — `D4` es `CONDITIONAL` sobre `frontendPresent`, y su identidad normativa no cambia.
  (D4-01) · rojo visto: si
- **E-02** — `frontendPresent = TRUE` con evidencia deja `D4` aplicable, con sus dos controles.
  (D4-02) · rojo visto: si
- **E-03** — `FALSE` con evidencia deja `D4` en `notApplicableRules`. (D4-03)
  · rojo visto: si
- **E-04** — Sin señal, `D4` queda `APPLICABILITY_UNRESOLVED` con la señal que falta escrita al
  lado. (D4-04) · rojo visto: si
- **E-05** — Lo ausente nunca se convierte en `FALSE`: que no aparezca una carpeta `frontend` no es
  evidencia de que no haya frontend. (D4-05) · rojo visto: si
- **E-06** — La señal es reusable: el mismo productor y el mismo resultado resuelven cualquier regla
  que la declare, y sumar un consumidor no pide una línea de código. (D4-06)
  · rojo visto: si
- **E-07** — Una unidad de sólo backend o API resuelve la señal en `FALSE` con su evidencia y `D4`
  no aplica. (D4-08) · rojo visto: si

### La forma del control

- **E-08** — `D4` declara **una** policy y **un** check, y ninguna review. (D4-07)
  · rojo visto: si

### Lo que no alcanza

- **E-09** — Que Bootstrap esté instalado no hace `PASS`. (D4-09) · rojo visto: si
- **E-10** — Que Obelisco esté instalado no hace `PASS`, y que G1 lo dé por homologado tampoco.
  (D4-10) · rojo visto: si
- **E-11** — Que existan media queries o una hoja de estilos mobile no hace `PASS`. (D4-11)
  · rojo visto: si
- **E-12** — Una captura de pantalla, sola, no hace `PASS`. (D4-18) · rojo visto: si
- **E-13** — Que alguien afirme que es responsive tampoco. · rojo visto: si

### La matriz de viewports

- **E-14** — Sin matriz de viewports: `VIEWPORT_MATRIX_UNRESOLVED`, que no es `PARTIAL` ni `FAIL`.
  (D4-12) · rojo visto: si
- **E-15** — Una matriz que no declara de dónde sale tampoco vale: la fuente es parte del contrato.
  · rojo visto: si
- **E-16** — Ningún artefacto de `D4` trae un valor de breakpoint ni un modelo de dispositivo, y la
  guarda se prueba contra fugas. (D4-24) · rojo visto: si

### La corrida

- **E-17** — Sin objetivo donde correr: `TEST_TARGET_UNAVAILABLE`, y no se colapsa en `PASS`.
  · rojo visto: si
- **E-18** — Recorte de contenido o superposición material en un viewport requerido: `FAIL`.
  (D4-14) · rojo visto: si
- **E-19** — Una acción crítica inalcanzable en un viewport requerido: `FAIL`. (D4-15)
  · rojo visto: si
- **E-20** — Un caso requerido que no se ejecutó deja el resultado en `PARTIAL`, aunque todos los
  demás pasen. (D4-16) · rojo visto: si
- **E-21** — Todos los casos requeridos ejecutados, sin defecto material y con evidencia de la
  corrida: `PASS`. (D4-17) · rojo visto: si
- **E-22** — Que el desktop pase no tapa un mobile que falla. · rojo visto: si
- **E-23** — La evidencia tiene que estar atada al build y al runtime probados; una de otra corrida
  no sostiene el `PASS`. (D4-19) · rojo visto: si
- **E-24** — Misma entrada, mismo resultado, y el resultado conserva build, runtime y matriz.
  (D4-13) · rojo visto: si
- **E-25** — Un defecto sin materialidad declarada no se ablanda: deja el caso sin resolver y el
  resultado en `PARTIAL`. · rojo visto: si
- **E-26** — De los siete estados, `PASS` es el único que aprueba. · rojo visto: si

### Las fronteras, los agentes y la instalación

- **E-27** — El resultado de `D4` no emite ningún veredicto de accesibilidad ni de `G1`, y el
  inventario de G1 dando Obelisco por homologado no mueve su estado. · rojo visto: si
- **E-28** — No se crea un segundo framework de automatización: las skills que ejecutarían son las
  que ya están instaladas y se resuelven contra el registro de agentes. (D4-21, §6)
  · rojo visto: si
- **E-29** — La unidad de trabajo propaga `frontendPresent` con su evidencia, la policy y el check.
  (D4-20) · rojo visto: si
- **E-30** — Antes de instalar, los dos controles son `DECLARED_POLICY_NOT_INSTALLED` y
  `DECLARED_CHECK_NOT_INSTALLED`; después desaparecen **sin tocar la identidad normativa de D4**.
  (D4-22) · rojo visto: si
- **E-31** — Todo resultado de `D4` conserva la tupla `ES0901 / 6.3 / 7.1 / D4`. (D4-23)
  · rojo visto: si

## Cómo se verifica

Los 31 pasan por la suite, en `tests/casos/29_d4_comportamiento_responsive.py`. Ninguno necesita
lectura.

🔴 **Lo que este cambio verifica es el control, no una aplicación.** Ningún caso renderiza nada: los
reportes de corrida, las matrices y los defectos se arman en memoria. Que la aplicación de un
proyecto sea efectivamente responsive lo dice una corrida real, y este cambio promete que esa
corrida es lo único que puede hacerla pasar.

E-16 se verifica en dos mitades, igual que su par en D1 y D2: los patrones sobre los dos archivos de
D4 —anchos en píxeles, nombres de modelos de dispositivo, listas de breakpoints— y una inyección de
fugas que exige que cada una ponga el caso rojo. La mitad de fugas afirma primero que el texto base
no matchea ningún patrón, que es la premisa que la vuelve no vacía.

## Riesgos conocidos

- **Nadie ejecuta todavía la corrida.** El check evalúa un reporte y no hay quien lo produzca. Una
  unidad real sale `PARTIAL` o `TEST_TARGET_UNAVAILABLE` hasta que alguien cablee la ejecución.
- **`VIEWPORT_MATRIX_UNRESOLVED` puede volverse cómodo.** Es el estado que no obliga a nada y que se
  justifica solo: basta no declarar la matriz. Lo que lo contiene es que no aprueba; lo que no lo
  contiene es nada.
- **La materialidad de un defecto la declara quien reporta.** Es el mismo eje que D3 y el mismo
  riesgo: lo elige la misma persona o herramienta que escribe el hallazgo. Omitirlo no da el lado
  suave, que es lo único que lo contiene.
- **La matriz declarada puede ser mala.** Un `TEAM_APPROVED_TEST_PROFILE` con un solo viewport de
  desktop cumple el contrato y no prueba nada. El check exige que la fuente esté declarada, no que
  la matriz sea representativa.
- **La frontera con accesibilidad no la hace cumplir nada.** Está escrita y testeada; el día que
  alguien meta una verificación de contraste adentro del check de D4, los tests siguen verdes.
- **La guarda de E-16 tiene una mitad que es enumeración.** Los números se cubren con un
  invariante —un artefacto de D4 no lleva ninguno— y eso no depende de acertarle a una lista. Las
  marcas de dispositivo no tienen invariante equivalente: se cubren con una lista de veinte más la
  forma genérica *marca + número de modelo*, que es lo que hace que la lista no tenga que estar
  completa. Una marca nueva mencionada **sin** número de modelo sigue entrando en verde, y también
  la variante en minúscula con modelo —`fairphone 5`—, porque esa forma exige mayúscula inicial.
- **El invariante "ningún número" choca con el estilo de citación de la casa.** De los siete
  policies instalados, el de D4 es el único sin números: los otros citan la página del estándar. El
  día que alguien le agregue `pág. 12` a este —lo que cuatro de los otros ya hacen— E-16 se pone
  rojo contra contenido correcto, y el arreglo bajo presión va a ser aflojar la mitad que hoy es
  invariante. **Esta guarda no se va a romper por una fuga: se va a romper por una edición
  correcta.**
