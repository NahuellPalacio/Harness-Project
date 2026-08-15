---
name: dev-pantalla
description: Use when building or reviewing a screen, page, view, form, table, modal, navbar or any UI component of a GCBA product — writing or changing HTML, JSX, Blade or Angular templates, CSS classes, icons, focus styles, hover states, validation messages or anything a person will see rendered — and especially when deciding whether to hand-roll a custom component instead of reusing an Obelisco one, when pulling in a third-party UI library, or when a screen has to survive an accessibility review before approval.
---

# Pantallas y componentes con Obelisco v2

Obelisco ofrece "una librería de elementos y estilos prediseñados accesibles" (Obelisco
pág. 1); lo que se importa son "estilos, tipografía, iconografía y scripts" (Obelisco
pág. 3). Y no es una preferencia de equipo: "El sistema de diseño Obelisco es el punto de
partida para crear productos digitales con los más altos estándares de accesibilidad y
usabilidad web" (Obelisco pág. 1).

**Esta skill sola no alcanza para implementar, y el PDF de la guía de adopción tampoco.**
La guía nombra y enlaza la guía de instalación, la de importaciones, la documentación de
estilos y componentes y los criterios de la ASI (Obelisco pág. 1), más el entorno de pruebas
(Obelisco pág. 3) — y no incluye el contenido de ninguna. Lo que está acá es lo exigible que
sí quedó escrito en el documento; el cómo se escribe cada componente vive en
`gcba.github.io/Obelisco-V2`.

## Antes de tocar marcado

- **Consultar la documentación es condición, no sugerencia** — "Para construir productos
  digitales que implementen Obelisco correctamente es importante consultar la documentación
  a disposición en la web, y así evitar malas prácticas y/o generar deuda técnica"
  (Obelisco pág. 1).
- **Node 18 en adelante** para instalar Obelisco v2 (Obelisco pág. 1).
- **La instalación se hace siguiendo la guía de instalación**, y las importaciones de
  estilos, tipografía, iconografía y scripts siguiendo la guía de importaciones — ambas en
  la web de Obelisco (Obelisco pág. 1 y pág. 3).
- **No hay excusa de stack**: Obelisco ofrece "una librería de elementos y estilos
  prediseñados accesibles, que pueden integrarse a cualquier aplicación web
  independientemente de la tecnología o framework con el que trabajes" (Obelisco pág. 1).
  Que el proyecto sea Angular, React o Blade no habilita reemplazarla.
- **La rama tiene que estar actualizada con la última versión de Obelisco**, monitoreando
  releases en GitHub (Obelisco pág. 3). Mantener el producto al día con actualizaciones y
  versionados es requisito explícito (Obelisco pág. 1). El check `dev-dependencias` vigila
  versiones homologadas; el seguimiento de releases de Obelisco es tarea humana.

## Cuándo se puede escribir un componente propio

Dos prohibiciones directas del checklist de desarrolladores (Obelisco pág. 3):

- **"Se utilizan los componentes de Obelisco v2 (ej.: botones, formularios, navegación) en
  lugar de soluciones personalizadas."** Escribir un botón propio porque "es más rápido" es
  incumplimiento, no atajo.
- **"Se usan las clases de Obelisco v2 y no de otras librerías."** Nada de Tailwind,
  Material o utilidades de otro design system encima de la pantalla.

⚠️ Tensión entre fuentes, sin resolver. La guía de adopción no menciona Bootstrap ni una vez
y su checklist prohíbe usar clases "de otras librerías" (Obelisco pág. 3). ES0901 pág. 35
dice lo contrario de refilón: "Por resolución RES-94-SECITD-23, para el desarrollo debe
utilizarse Obelisco como sistema de diseño, el cual a su vez utiliza Bootstrap como
librería", y homologa una versión de Bootstrap en su tabla de Sistema de Diseño. Ninguna de
las dos dice si escribir clases de Bootstrap a mano cuenta como "otra librería". No está
definido: preguntar antes de apoyarse en utilidades de Bootstrap.

📌 **El número de versión no se copia acá.** Para fijar la versión de Obelisco o de
Bootstrap, abrí el Anexo II de ES0901 en la pág. 35, o invocá `dev-versiones`. Una skill con
una versión clavada envejece en silencio: el estándar se actualiza y la skill sigue diciendo
lo mismo.

El camino de decisión está en el diagrama de contribución (Obelisco pág. 2). En orden:

1. ¿Hay un componente de Obelisco que cubra la necesidad? → Usalo respetando los
   lineamientos de uso. Fin.
2. Si no: ¿hay uno que se pueda **adaptar**? → Si alguien ya propuso esa solución, sumate
   al issue existente en GitHub con lo que sepas.
3. Si no hay nada adaptable: diseñás un concepto nuevo y preguntás si **sirve para otros
   activos digitales** que consuman Obelisco.
   - **No sirve para otros** → implementás la solución **de forma local siguiendo los
     lineamientos de Obelisco**. Local no significa libre.
   - **Sí sirve** → si ya lo propuso otra persona, sumate a ese issue; si no, creás el
     componente siguiendo los lineamientos de la guía de adopción y abrís un issue en
     GitHub como propuesta de componente nuevo.

⚠️ El diagrama es una imagen sin capa de texto: la redacción de arriba es una transcripción.
Si un nodo tiene que ir palabra por palabra en un criterio de aceptación, abrí la pág. 2 del
PDF. Y ojo con el caso sin salida, abajo en "Lo que hay que ir a buscar al PDF".

**Para contribuir hay que tener Obelisco instalado, implementado y en su última versión**
(Obelisco pág. 2). "La vía principal de contacto para contribuir con Obelisco es levantar un
issue en el repositorio de GitHub" (Obelisco pág. 2) — dice **principal**, no única; el
documento no nombra ninguna otra vía, pero tampoco las descarta. Cada caso tiene un template
obligatorio (Obelisco pág. 2). Los casos previstos son tres: reportar un bug o proponer una
mejora técnica, proponer un nuevo caso de uso, aportar código (Obelisco pág. 2). Si ninguno
encaja o es una duda, va un issue en blanco (Obelisco pág. 2).

## Iconografía

- **Material Symbols y Boxicons son las dos librerías oficiales; la principal es Material
  Symbols** (Obelisco pág. 1). Ver contradicción 1: el checklist las presenta como
  equivalentes.
- **Configuración morfológica obligatoria para cualquiera de las dos** (Obelisco pág. 1):
  Type redondeado (rounded) · Fill sí · Grade normal · Optical size igual al tamaño en px
  del ícono. Un ícono outline, sin relleno o con grade alterado no cumple.

## Accesibilidad: lo que ninguna máquina puede verificar

El check `dev-accesibilidad-html` ya marca lo mecánico — `lang` en `<html>`, `alt` ausente
en `<img>`, controles sin forma de nombrarlos, `<h1>` faltante o duplicado. Nada de eso se
repite acá. Lo que sigue es el resto del checklist de accesibilidad (Obelisco pág. 3), que
exige criterio humano y es lo que hace rebotar una pantalla en auditoría.

**Contraste y color**
- Texto: **mínimo 4.5:1**, y **3:1 para texto grande** — SC 1.4.3 Contrast (Minimum)
  (Obelisco pág. 3).
- **Indicador de foco: mínimo 3:1 de contraste** y claramente visible — SC 2.4.13 Focus
  Appearance (Obelisco pág. 3). Borrar el `outline` sin reemplazo es incumplimiento directo.
- El color **no puede ser el único medio** para transmitir información (errores, estado) —
  SC 1.4.1 Use of Color (Obelisco pág. 3).
- Hover y activo necesitan indicador visual **más allá del color** — SC 1.4.1 (Obelisco pág. 3).

**Teclado y foco**
- Todo elemento interactivo — botones, enlaces, formularios — funciona con teclado —
  SC 2.1.1 Keyboard (Obelisco pág. 3). Un `<div onclick>` no cumple.
- El **orden del foco sigue una secuencia lógica** — SC 2.4.3 Focus Order (Obelisco pág. 3).
- El **enlace para saltar la navegación está presente y funciona** — SC 2.4.1 Bypass Blocks
  (Obelisco pág. 3). Que exista en el DOM no basta: hay que probarlo.

**Formularios**
- Cada campo tiene un `<label>` **vinculado correctamente** — SC 1.3.1 y SC 3.3.2
  (Obelisco pág. 3). El check ve si el control puede ser nombrado; que la etiqueta describa
  el campo lo verificás vos.
- Los **campos obligatorios se marcan con texto, no solo con color** — SC 3.3.2
  (Obelisco pág. 3). El asterisco rojo solo no alcanza.
- Los **mensajes de error son descriptivos y sugieren la corrección** — SC 3.3.1 Error
  Identification (Obelisco pág. 3). "Campo inválido" no cumple.

**Contenido y enlaces**
- El texto del enlace es descriptivo: "Leé nuestra guía", no "Hacé click acá" — SC 2.4.4
  Link Purpose (In Context) (Obelisco pág. 3).
- Las instrucciones **no dependen de características sensoriales**: nada de "hacé click en
  el botón verde" — SC 1.3.3 Sensory Characteristics (Obelisco pág. 3).
- Se mantiene la legibilidad: lenguaje sencillo, sin jerga — SC 3.1.5 Reading Level
  (Obelisco pág. 3).
- La página tiene un **título único y descriptivo** — SC 2.4.2 Page Titled (Obelisco pág. 3).

**Estructura y semántica**
- Jerarquía de encabezados lógica H1-H6 — SC 2.4.6 Headings and Labels (Level AA)
  (Obelisco pág. 3). El check cuenta los `<h1>`; que la jerarquía tenga sentido, no.
- Elementos HTML semánticos siempre que sea posible (`<section>`, `<nav>`) — SC 4.1.2
  (Obelisco pág. 3).
- **ARIA solo cuando el HTML es insuficiente** — SC 4.1.2 (Obelisco pág. 3). Un
  `role="button"` sobre un `<div>` es la señal de que faltaba un `<button>`.
- Los puntos de referencia `<header>`, `<main>`, `<footer>` estructuran la página — SC 1.3.1
  (Obelisco pág. 3).

**Responsive y multimedia**
- El contenido **se ajusta sin desplazamiento horizontal a 320px de ancho** — SC 1.4.10
  Reflow (Obelisco pág. 3).
- **Zoom hasta 200% sin pérdida de funcionalidad** — SC 1.4.4 Resize Text (Obelisco pág. 3).
- Videos y audios con subtítulos, transcripciones o descripciones de audio — SC 1.2.2
  (Obelisco pág. 3).
- Lo que se reproduce automáticamente se puede pausar o detener — SC 1.4.2 Audio Control
  (Obelisco pág. 3).

## Los siete principios, para cuando hay que discutir una decisión

Todos redactados como "El diseño debe…", así que son exigibles por su redacción
(Obelisco pág. 1): **igualdad de uso** (fácil y entendible para todas las personas,
cualesquiera sean sus capacidades y contextos) · **flexibilidad** (se adecua a un amplio
rango de preferencias y habilidades) · **simple e intuitivo** (independiente de la
experiencia, conocimientos o concentración de la persona usuaria) · **información fácil de
percibir** (interactúa e intercambia información cualesquiera sean las condiciones físicas o
capacidades sensoriales) · **tolerante a errores** (minimiza acciones accidentales y previene
las fortuitas con consecuencias graves) · **escaso esfuerzo físico** · **dimensiones
apropiadas** (responde a la pantalla en que se muestra y se adapta responsivamente).

## Antes de dar la pantalla por terminada

- **Los componentes y estilos se testearon en el entorno de pruebas de Obelisco antes de la
  implementación** (Obelisco pág. 3).
- **Verificaciones manuales**: probado con lector de pantalla (NVDA, VoiceOver) · navegación
  solo con teclado verificada · uso de componentes y estilos validado contra la documentación
  de Obelisco, incluyendo sus pautas de accesibilidad (Obelisco pág. 3).
- **Herramientas**: Axe o WAVE para problemas técnicos; Stark o Contrast Checker para
  contraste (Obelisco pág. 3). No reemplazan lo manual: la lista los pone como bloques
  distintos.
- **Nivel exigido**: "Se verificó el cumplimiento de WCAG 2.2 en los niveles AA-AAA y la ley
  26.653 de Accesibilidad de la Información" (Obelisco pág. 3). La ley 26.653 obliga al
  Estado a respetar las normas de accesibilidad en sus productos digitales, y la resolución
  N° 94/SECITD/23 apunta al acceso en igualdad de oportunidades (Obelisco pág. 1).
- **Todos los productos digitales tienen que cumplir con los criterios y requisitos de la
  ASI** (Obelisco pág. 1 y pág. 3).

## Lo que hay que ir a buscar al PDF

- **El contenido de las guías enlazadas.** El PDF las nombra y linkea pero no las incluye
  (Obelisco pág. 1, pág. 2 y pág. 3): guía de instalación, guía de importaciones,
  documentación de estilos y componentes, `CONTRIBUTING.md`, criterios y requisitos de la
  ASI, texto de WCAG, ley 26.653 y resolución N° 94/SECITD/23 — y el entorno de pruebas, que
  el documento nombra solo en el checklist de la pág. 3. **Nada de su contenido se
  puede citar desde acá.** Para implementar un componente concreto no hay atajo: hay que
  abrir la documentación web.
- **La redacción exacta de los nodos del diagrama de contribución (pág. 2).** Es una imagen
  raster sin capa de texto; lo de arriba es transcripción de un render. Si va palabra por
  palabra en un criterio de aceptación, releé la pág. 2 del PDF.
- **Qué hacer cuando existe un componente adaptable y la solución NO fue sugerida antes.**
  Ese nodo de decisión (segunda fila del diagrama, pág. 2) **no tiene salida por "NO"**. El
  documento no lo define. No completar por analogía con la tercera fila: hay que preguntar.
- **Quién audita las checklists y con qué frecuencia.** La pág. 3 las presenta como guía de
  autovalidación y no lo dice. No está definido.

## Contradicciones sin resolver

1. **Jerarquía entre librerías de íconos.** Pág. 1: "La librería de íconos principal entre
   ambas opciones es Material Symbols". Pág. 3 (checklist): "Se utiliza Material Symbols
   (redondeados, rellenos, grado normal) **o Boxicons** según las pautas de Obelisco" — leído
   solo desde ahí, Boxicons es equivalente; desde la pág. 1, es secundaria.
2. **Alcance de la configuración morfológica.** Pág. 1: las cuatro propiedades rigen "para
   cualquiera de las 2 librerías", Optical size incluida. Pág. 3: el paréntesis
   "(redondeados, rellenos, grado normal)" acompaña **solo** a Material Symbols y **omite
   Optical size**. No queda establecido si los cuatro valores rigen para Boxicons.
3. **Nivel de conformidad WCAG.** Pág. 1 nombra WCAG sin versión ni nivel. Pág. 3 exige
   "WCAG 2.2 en los niveles AA-AAA". Dentro del propio checklist de accesibilidad, de 24
   ítems con Success Criterion sobre 21 criterios distintos, **uno solo declara nivel**
   (2.4.6, Level AA); los otros 23 no.
4. **Versión de WCAG exigida vs. versión enlazada.** El ítem de cumplimiento legal (pág. 3)
   exige WCAG 2.2, pero los hipervínculos de los Success Criterion de ese mismo checklist
   apuntan mayoritariamente a las páginas Understanding de **WCAG 2.1**; la única excepción
   es Focus Appearance, que apunta a WCAG 2.2.
5. **El mismo nodo se resuelve distinto según la rama (pág. 2).** "Anteriormente, ¿La
   solución fue sugerida por otra persona?" aparece dos veces: en la tercera fila tiene
   salida por SI y por NO ("Creá un nuevo componente siguiendo los lineamientos de la guía de
   adopción"); en la segunda fila la rama NO no existe.
