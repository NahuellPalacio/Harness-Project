# Obelisco — Guía de adopción de Obelisco v2

> Fuente: normativa/fuentes/_Obelisco-V2_docs_Guía_de_adopción_de_Obelisco_v2.pdf
> Version sin numero, 20/03/2025 · 3 paginas · extractado el 2026-08-12
> Este extracto conserva las reglas exigibles. NO reemplaza al PDF para lo que
> figure abajo como no citable.

Nota de método: el texto plano convertido del PDF llega con cadenas descolocadas
(p. ej. `3 F App Success Criterion 2.4.1 ocus earance`, `Le u r n est a guía`,
`q re uisitos`, `niveles - AA AAA`). Todas las citas de este extracto fueron
re-verificadas contra el render de la página correspondiente, no contra el texto
plano. El documento **no contiene tablas**.

---

## Lo que NO se puede citar desde acá

- **Diagrama del proceso de contribución (pág. 2).** Es una imagen raster (4096×3478 px)
  sin capa de texto: no existe en el texto extraído del PDF. Los nodos están transcriptos
  más abajo desde el render de alta resolución, pero **la transcripción no proviene de una
  capa de texto**. Si la redacción exacta de un nodo es load-bearing (p. ej. para un
  criterio de aceptación), releer la pág. 2 del PDF antes de citarla palabra por palabra.
- **Contenido de las guías enlazadas por hipervínculo.** El PDF las nombra y linkea pero
  **no las incluye**. Nada de su contenido es citable desde acá: guía de instalación,
  guía de importaciones, modelo de contribución (`CONTRIBUTING.md`), documentación de
  estilos y componentes, entorno de pruebas de Obelisco, releases, criterios y requisitos
  de la ASI, texto de WCAG, ley 26.653 y resolución N° 94/SECITD/23.
- **Capturas de pantalla de la instalación en Figma (pág. 1, pasos 1 a 4).** Diez imágenes
  de la UI de Figma, sin capa de texto, numeradas dentro de cada paso (paso 1: 1/2/3 ·
  paso 2: 1/2 · paso 3: 1/2 · paso 4: 1/2/3). Ilustran los pasos; el texto de cada paso sí
  está abajo. No hay regla que viva únicamente en esas capturas.
- **Ramificación faltante en el diagrama (pág. 2).** El nodo de decisión
  "Anteriormente, ¿La solución fue sugerida por otra persona?" de la **segunda fila** no
  tiene salida por "NO" en el diagrama. Qué hacer en ese caso **no está definido en el
  documento**: no completar por analogía con la tercera fila.

---

## Alcance del documento (pág. 1, 2 y 3)

- **El modelo de adopción se sigue para trabajar con el sistema de diseño** (pág. 1) —
  encabezado repetido en las tres páginas: "Seguí el modelo de adopción de Obelisco v2
  para trabajar con el sistema de diseño en tus activos digitales. Obelisco ofrece
  información para diseñadores y para desarrolladores, como una forma de agilizar los
  procesos de adopción para cada una de las áreas involucradas."
- **Obelisco es el punto de partida, no una opción** (pág. 1) — "El sistema de diseño
  Obelisco es el punto de partida para crear productos digitales con los más altos
  estándares de accesibilidad y usabilidad web."

## Principios de diseño (pág. 1)

Siete principios, todos redactados como "El diseño debe…". Son exigibles por su redacción.

- **Igualdad de uso** (pág. 1) — "El diseño debe ser fácil y entendible para todas las
  personas, independientemente de sus capacidades y contextos."
- **Flexibilidad** (pág. 1) — "El diseño debe adecuarse a un amplio rango de preferencias
  y habilidades individuales."
- **Simple e intuitivo** (pág. 1) — "El diseño debe ser fácil de entender,
  independientemente de la experiencia, los conocimientos, las habilidades o la
  concentración de la persona usuaria."
- **Información fácil de percibir** (pág. 1) — "El diseño debe ser capaz de interactuar e
  intercambiar información con la persona usuaria, en cuales sean las condiciones físicas
  o capacidades sensoriales de la misma." (redacción textual del documento)
- **Tolerante a errores** (pág. 1) — "El diseño debe minimizar las acciones accidentales y
  prevenir las acciones fortuitas, que puedan tener consecuencias graves o no deseadas en
  la experiencia de la persona usuaria."
- **Escaso esfuerzo físico** (pág. 1) — "El diseño debe poder ser utilizado de forma
  eficaz y empleando el menor esfuerzo físico posible."
- **Dimensiones apropiadas** (pág. 1) — "El diseño debe responder a las dimensiones de la
  pantalla en que se muestra, y ser capaz de adaptarse responsivamente a cada disposición."

## Marco normativo de accesibilidad (pág. 1)

- **Obelisco sigue W3C / WCAG** (pág. 1) — "El sistema de diseño sigue los criterios y
  pautas establecidas por la World Wide Web Consortium (W3C), en las Web Content
  Accesibility Guidelines (WCAG)". El hipervínculo de "Web Content Accesibility Guidelines
  (WCAG)" apunta a `https://www.w3.org/TR/WCAG22/`. **La pág. 1 no enuncia un nivel de
  conformidad**; el nivel aparece recién en la pág. 3 (ver Checklist para Desarrolladores).
- **Ley 26.653 obliga al Estado** (pág. 1) — "cumple con lo establecido en la ley 26.653 de
  Accesibilidad de la Información, que exige al Estado a respetar las normas y requisitos
  sobre accesibilidad en los diseños de sus productos digitales."
- **Resolución N° 94/SECITD/23** (pág. 1) — "Además, la resolución N° 94/SECITD/23 apunta a
  facilitar el acceso a los contenidos a todas las personas usuarias en igualdad de
  oportunidades."

## Documentación, mantenimiento y seguridad (pág. 1)

- **Consultar la documentación es condición para implementar correctamente** (pág. 1) —
  "Para construir productos digitales que implementen Obelisco correctamente es importante
  consultar la documentación a disposición en la web, y así evitar malas prácticas y/o
  generar deuda técnica."
- **Cumplimiento ASI obligatorio para todo producto digital** (pág. 1) — "Todos los
  productos digitales tienen que cumplir con los criterios y requisitos de la ASI."
- **Mantenerse al día con actualizaciones y versionados** (pág. 1) — "Chequeá las
  comunicaciones de Obelisco sobre actualizaciones y versionados, y mantené tu producto
  digital al día sobre los requerimientos técnicos."

## Configuración para diseñadores (pág. 1)

- **Se requiere cuenta de Figma de plan pago** (pág. 1) — recuadro destacado: "La librería
  de diseño de Obelisco v2 está construida en Figma. Para utilizar cualquier recurso del
  sistema de diseño deberás tener una cuenta parte de un plan pago de Figma (profesional
  en adelante)."
- **Secuencia de instalación de la librería de diseño, seis pasos** (pág. 1) — ⚠️ **el PDF
  los numera `1, 2, 3, 4, 4, 6`**: el numeral 4 aparece dos veces y el 5 no existe
  (verificado en el render de la pág. 1). Se transcriben con la numeración del original,
  sin corregirla. Si se cita "el paso 4" hay que aclarar cuál de los dos.
  - **1.** "Duplicá los archivos de **Foundations** y **Core Components** desde el perfil
    de Obelisco en la Comunidad de Figma."
  - **2.** "Mové los archivos de Foundations y Core Components al espacio de tu equipo o
    proyecto dentro de Figma."
  - **3.** "Publicá los archivos de Foundations y Core Components como librerías."
  - **4.** "Abrí un archivo .fig o creá un nuevo archivo .fig para agregar y utilizar los
    archivos de Foundations y Core Components al mismo."
  - **4.** *(sic — el numeral 4 se repite)* "Leé la documentación disponible sobre Obelisco
    v2 para entender mejor cómo construir aplicaciones web y experiencias digitales con el
    sistema de diseño."
  - **6.** "Empezá a diseñar y trabajar con Obelisco v2."

## Iconografía (pág. 1)

- **Dos librerías oficiales, con jerarquía explícita** (pág. 1) — "Obelisco utiliza
  Material Symbols y Boxicons como librerías de íconos oficiales del sistema de diseño.
  La librería de íconos principal entre ambas opciones es Material Symbols, que además
  cuenta con un plugin en la comunidad de Figma para buscar y consumir íconos directamente
  en tu archivo de diseño."
- **Configuración morfológica obligatoria, aplicable a ambas librerías** (pág. 1) — "Para
  cualquiera de las 2 librerías, la configuración morfológica de los íconos debe ser la
  siguiente:"
  - "**Type:** redondeado (rounded)."
  - "**Fill:** sí."
  - "**Grade:** normal."
  - "**Optical size:** tamaño en px. del ícono a utilizar."

## Configuración para desarrolladores (pág. 1)

- **Independencia de tecnología** (pág. 1) — "Obelisco ofrece una librería de elementos y
  estilos prediseñados accesibles, que pueden integrarse a cualquier aplicación web
  independientemente de la tecnología o framework con el que trabajes."
- **Instalación según la guía de instalación** (pág. 1) — "Instalá y vinculá siguiendo las
  instrucciones de la guía de instalación en la web de Obelisco."
- **Umbral de versión de Node** (pág. 1) — "Para instalar Obelisco v2 debes contar con la
  versión de **Node 18 en adelante**." (cita textual: "Para instalar Obelisco v2 debes
  contar con la versión de Node 18 en adelante.")
- **Importaciones según la guía de importaciones** (pág. 1) — "Seguí la guía de
  importaciones para contar con todos los elementos y complementos necesarios para
  utilizar Obelisco v2 correctamente."

## Contribución (pág. 2)

- **Precondición para contribuir: tener Obelisco instalado, implementado y actualizado**
  (pág. 2) — "Antes de poder contribuir, es necesario instalar e implementar correctamente
  el sistema de diseño en tu producto digital; el proceso de contribución se nutre de la
  colaboración, y para lograr un vínculo colaborativo positivo es necesario contar con la
  última versión de Obelisco."
- **Vía principal de contacto: issue en el repositorio de GitHub** (pág. 2) — "La vía
  principal de contacto para contribuir con Obelisco es levantar un issue en el repositorio
  de GitHub." El documento dice **principal**, no única: no nombra ninguna otra vía, pero
  tampoco las descarta. No endurecer a "única".
- **Cada caso tiene template obligatorio** (pág. 2) — "Existen diferentes casos de
  contribución, y cada uno tiene un template para completar antes de levantar el issue."
- **Casos de contribución previstos** (pág. 2) — exactamente tres:
  - "Reportar un bug o proponer una mejora técnica."
  - "Proponer un nuevo caso de uso."
  - "Aportar con código."
- **Seguir el modelo de contribución de GitHub es obligatorio** (pág. 2) — "Para cada uno
  de los casos, es necesario seguir el modelo de contribución detallado en GitHub."
- **El diagrama es la referencia para elegir el caso** (pág. 2) — "Tomá el diagrama de
  contribución como referencia para saber cuál de todos los casos posibles se ajusta a tu
  necesidad."
- **Soporte / casos no cubiertos** (pág. 2) — "Si ninguna de las formas de contribuir se
  ajusta a tu necesidad o querés resolver una duda, podés abrir un issue en blanco en
  GitHub."

### Diagrama de proceso de contribución (pág. 2 — IMAGEN, transcripción no textual)

Transcripción desde el render de la imagen. **Ver "Lo que NO se puede citar desde acá"
antes de citar un nodo palabra por palabra.**

- Inicio: "Tengo un nuevo requerimiento en mi activo digital"
- Decisión 1: "¿Existe un componente en Obelisco que cubra esa necesidad?"
  - **SI** → "Utiliza el componente de Obelisco, respetando los lineamientos de uso" (fin)
  - **NO** → Decisión 2
- Decisión 2: "¿Existe un componente en Obelisco que se pueda adaptar a tu necesidad?"
  - **SI** → Decisión 3
  - **NO** → "Diseñá un nuevo concepto/componente" → Decisión 4
- Decisión 3: "Anteriormente, ¿La solución fue sugerida por otra persona?"
  - **SI** → "Sumate al issue en GitHub con la información que consideres importante" (fin)
  - **NO** → *sin salida en el diagrama; no definido en el documento*
- Decisión 4: "¿El componente puede servir para otros activos digitales que consuman
  Obelisco?"
  - **SI** → Decisión 5
  - **NO** → "Implementá la solución de forma local siguiendo los lineamientos de
    Obelisco" (fin)
- Decisión 5: "Anteriormente, ¿La solución fue sugerida por otra persona?"
  - **SI** → "Sumate al issue en GitHub con la información que consideres importante" (fin)
  - **NO** → "Creá un nuevo componente siguiendo los lineamientos de la guía de adopción"
    → "Creá un Issue en GitHub como propuesta de nuevo componente para Obelisco" (fin)

## Checklists de autovalidación — encuadre (pág. 3)

- **Para qué sirven** (pág. 3) — "Obelisco ofrece checklists de autovalidación para evaluar
  el nivel de adopción y cumplimiento de criterios en los productos digitales. Podés
  utilizarlas como guía para incorporar mejoras y buenas prácticas en tu producto digital."
- El documento las presenta como **guía de autovalidación**; no enuncia en la pág. 3 quién
  audita ni con qué frecuencia. No está definido.

## Checklist de Accesibilidad (pág. 3)

Nueve bloques numerados. Cada ítem de los bloques 1 a 8 lleva el Success Criterion tal como
lo cita el documento; los del bloque 9 no llevan ninguno.

**1. Principios generales — Estructura de la página** (pág. 3)
- "Se utiliza una jerarquía de encabezados lógica (H1-H6)." — *Success Criterion 2.4.6
  Headings and Labels (Level AA)*
- "La página tiene un título único y descriptivo." — *Success Criterion 2.4.2 Page Titled*
- "El atributo de idioma está definido (ej.: `<html lang="es">`)." — *Success Criterion
  3.1.1 Language of Page*
- "El enlace para saltar la navegación está presente y funciona." — *Success Criterion
  2.4.1 Bypass Blocks*

**2. Marcado semántico — HTML y ARIA** (pág. 3)
- "Se usan elementos HTML semánticos siempre que sea posible (ej.: `<section>`, `<nav>`)."
  — *Success Criterion 4.1.2 Name, Role, Value*
- "Los roles/etiquetas ARIA se usan solo cuando HTML es insuficiente." — *Success Criterion
  4.1.2 Name, Role, Value*
- "Los puntos de referencia (ej.: `<header>`, `<main>`, `<footer>`) estructuran la página."
  — *Success Criterion 1.3.1 Info and Relationships*

**3. Claridad del contenido — Textos y enlaces** (pág. 3)
- "El texto de los enlaces es descriptivo y significativo (ej.: *"Leé nuestra guía"* en
  lugar de *"Hacé click acá"*)." — *Success Criterion 2.4.4 Link Purpose (In Context)*
- "Las instrucciones no dependen de características sensoriales (ej.: *"Hacé click en el
  botón verde"*)." — *Success Criterion 1.3.3 Sensory Characteristics*
- "Se mantiene la legibilidad del contenido (ej.: lenguaje sencillo, evita jerga)." —
  *Success Criterion 3.1.5 Reading Level*

**4. Navegación por teclado — Funcionalidad** (pág. 3)
- "Todos los elementos interactivos (botones, enlaces, formularios) funcionan con el
  teclado." — *Success Criterion 2.1.1 Keyboard*
- "El orden del foco sigue una secuencia lógica." — *Success Criterion 2.4.3 Focus Order*
- **Umbral de contraste del indicador de foco** — "Los indicadores de foco son claramente
  visibles (mínimo 3:1 de contraste)." — *Success Criterion 2.4.13 Focus Appearance*
  (el documento numera el criterio **2.4.13**; el hipervínculo apunta a
  `w3.org/WAI/WCAG22/Understanding/focus-appearance.html`)

**5. Color y contraste — Diseño visual** (pág. 3)
- **Umbrales de contraste de texto** — "El texto tiene una relación de contraste de al
  menos 4.5:1 (3:1 para texto grande)." — *Success Criterion 1.4.3 Contrast (Minimum)*
- "El color no es el único medio para transmitir información (ej.: *errores, estado*)." —
  *Success Criterion 1.4.1 Use of Color*
- "Los estados interactivos (hover, activo) tienen indicadores visuales claros más allá del
  color." — *Success Criterion 1.4.1 Use of Color*

**6. Formularios y campos — Etiquetas y validación** (pág. 3)
- "Cada campo del formulario tiene una etiqueta `<label>` vinculada correctamente." —
  *Success Criterion 1.3.1 Info and Relationships, Success Criterion 3.3.2 Labels or
  Instructions*
- "Los campos obligatorios se marcan con texto, no solo con color." — *Success Criterion
  3.3.2 Labels or Instructions*
- "Los mensajes de error son descriptivos y sugieren correcciones." — *Success Criterion
  3.3.1 Error Identification*

**7. Multimedia — Imágenes y medios** (pág. 3)
- "Las imágenes tienen texto alternativo significativo (o `alt=""` si son decorativas)." —
  *Success Criterion 1.1.1 Non-text Content*
- "Los videos/audios tienen subtítulos, transcripciones o descripciones de audio." —
  *Success Criterion 1.2.2 Captions (Prerecorded)*
- "Los medios que se reproducen automáticamente pueden pausarse o detenerse." — *Success
  Criterion 1.4.2 Audio Control*

**8. Diseño responsivo — Móvil y zoom** (pág. 3)
- **Umbral de ancho** — "El contenido se ajusta sin desplazamiento horizontal en pantallas
  de 320px de ancho." — *Success Criterion 1.4.10 Reflow*
- **Umbral de zoom** — "Soporta zoom de hasta 200% sin pérdida de funcionalidad." —
  *Success Criterion 1.4.4 Resize Text*

**9. Pruebas y validación** (pág. 3)
- *Verificaciones manuales:*
  - "Probado con lectores de pantalla (ej.: NVDA, VoiceOver)."
  - "Navegación solo con teclado verificada."
  - "Uso de componentes y estilos validado según la documentación de Obelisco, incluyendo
    pautas de accesibilidad."
- *Herramientas automatizadas:*
  - "Uso de Axe o WAVE para detectar problemas técnicos."
  - "Contraste de color validado con herramientas como Stark o Contrast Checker."

## Checklist para Diseñadores (pág. 3)

**1. Configuración inicial — Librerías en Figma**
- "Los archivos de Foundations y Core Components se duplicaron desde el perfil de Obelisco
  en la Comunidad de Figma y se movieron al espacio de tu equipo/proyecto."
- "Foundations y Core Components están publicados como bibliotecas en Figma y habilitados
  en tu archivo de diseño."

**1. Configuración inicial — Iconografía**
- "Se utiliza Material Symbols (redondeados, rellenos, grado normal) o Boxicons según las
  pautas de Obelisco."

**2. Documentación y cumplimiento — Lineamientos de uso**
- "Los componentes y estilos se alinean con la documentación de Obelisco (ej.: uso del
  componente, buenas y malas prácticas del componente/estilo)."
- "El diseño cumple con los principios y con los criterios de accesibilidad del sistema de
  diseño."

## Checklist para Desarrolladores (pág. 3)

**1. Configuración inicial — Instalación de Obelisco**
- "Obelisco v2 está instalado siguiendo los pasos descritos en la guía de instalación."
- "Las importaciones de estilos, tipografía, iconografía y scripts están implementadas
  según la guía de importaciones."

**2. Implementación de elementos — Componentes de Obelisco**
- **Prohibición de soluciones propias** — "Se utilizan los componentes de Obelisco v2
  (ej.: botones, formularios, navegación) en lugar de soluciones personalizadas."
- **Prohibición de clases de terceros** — "Se usan las clases de Obelisco v2 y no de otras
  librerías."

**2. Implementación de elementos — Iconografía**
- "Se utiliza Material Symbols (redondeados, rellenos, grado normal) o Boxicons según las
  pautas de Obelisco."

**3. Calidad del código — Versionado**
- "Las ramas están actualizadas con la última versión de Obelisco (monitorear releases en
  GitHub)."

**4. Cumplimiento legal y técnico — Accesibilidad**
- **Nivel de conformidad exigido** — "Se verificó el cumplimiento de WCAG 2.2 en los
  niveles AA-AAA y la ley 26.653 de Accesibilidad de la Información."

**4. Cumplimiento legal y técnico — Seguridad**
- "Se verificó el cumplimiento de los criterios y requisitos de la ASI."

**5. Pruebas y validación — Verificaciones manuales**
- "Los componentes y estilos se testearon en el entorno de pruebas de Obelisco antes de la
  implementación."

## Hipervínculos presentes en el PDF (inventario)

Extraídos de las anotaciones del PDF. **La asignación anclaje↔URL no pudo verificarse
anotación por anotación**; se listan tal cual, y el emparejamiento sólo es seguro donde la
ruta es autodescriptiva. Ninguno de estos destinos está incluido en el PDF.

- `https://gcba.github.io/` · `https://gcba.github.io/Obelisco-V2/getting-started/installation`
  · `https://gcba.github.io/Obelisco-V2/getting-started/imports`
  · `https://gcba.github.io/Obelisco-V2/getting-started/editor`
  · `https://gcba.github.io/Obelisco-V2/documentation/releases`
- `https://github.com/gcba/Obelisco-V2/issues` · `https://github.com/gcba/Obelisco-V2/blob/main/CONTRIBUTING.md`
- `https://www.figma.com/@ObeliscoGCBA` · `https://www.figma.com/pricing/`
  · `https://www.figma.com/community/plugin/1088610476491668236/material-symbols`
  · `https://boxicons.com/`
- `https://www.w3.org/` · `https://www.w3.org/TR/WCAG22/`
  · `https://www.w3.org/WAI/WCAG21/Understanding/…` (24 anotaciones sobre 20 destinos
  distintos; `info-and-relationships`, `labels-or-instructions`, `name-role-value` y
  `use-of-color` aparecen dos veces cada una)
  · `https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html`
- `https://www.argentina.gob.ar/normativa/nacional/ley-26653-175694/texto`
- `https://buenosaires.gob.ar/sites/default/files/2024-11/ck_PE-RES-MJGGC-SECITD-94-23-6626.pdf`
  (resolución N° 94/SECITD/23)
- `https://buenosaires.gob.ar/agencia-de-sistemas-de-informacion/estandares-de-la-agencia`
  (criterios y requisitos de la ASI)
- Herramientas: Axe (Chrome Web Store), WAVE (Edge Add-ons), Stark (Chrome Web Store),
  `https://webaim.org/resources/contrastchecker/`

---

## Contradicciones internas

Se registran, no se resuelven.

1. **Jerarquía entre librerías de íconos: explícita en pág. 1, ausente en pág. 3.**
   - Pág. 1: "La librería de íconos principal entre ambas opciones es Material Symbols".
   - Pág. 3 (ambos checklists, Diseñadores y Desarrolladores): "Se utiliza Material Symbols
     (redondeados, rellenos, grado normal) o **Boxicons** según las pautas de Obelisco."
   - Leído sólo desde la pág. 3, Boxicons es una alternativa equivalente; leído desde la
     pág. 1, es secundaria.

2. **Alcance de la configuración morfológica de los íconos.**
   - Pág. 1: "Para cualquiera de las 2 librerías, la configuración morfológica de los
     íconos debe ser la siguiente" — y lista cuatro propiedades, incluida "Optical size:
     tamaño en px. del ícono a utilizar."
   - Pág. 3: el paréntesis "(redondeados, rellenos, grado normal)" acompaña **sólo** a
     Material Symbols y **omite Optical size**.
   - No queda establecido si la configuración de cuatro propiedades rige también para
     Boxicons según el checklist.

3. **Nivel de conformidad WCAG: sin nivel en pág. 1, "AA-AAA" en pág. 3.**
   - Pág. 1: "El sistema de diseño sigue los criterios y pautas establecidas por la World
     Wide Web Consortium (W3C), en las Web Content Accesibility Guidelines (WCAG)" — sin
     versión ni nivel en el texto.
   - Pág. 3: "Se verificó el cumplimiento de WCAG 2.2 en los niveles AA-AAA".
   - Dentro del propio Checklist de Accesibilidad (pág. 3) sólo **un** ítem declara nivel
     ("Success Criterion 2.4.6 Headings and Labels (Level AA)"). Los bloques 1 a 8 tienen
     **24 ítems con Success Criterion** (4+3+3+3+3+3+3+2), sobre **21 criterios distintos**;
     los **23 ítems restantes no declaran nivel**. Los cinco ítems del bloque 9 (Pruebas y
     validación) no llevan Success Criterion.

4. **Versión de WCAG exigida vs. versión enlazada en el mismo checklist.**
   - El ítem de cumplimiento legal (pág. 3) exige **WCAG 2.2**.
   - Los hipervínculos de los Success Criterion del mismo checklist (pág. 3) apuntan
     mayoritariamente a las páginas Understanding de **WCAG 2.1**
     (`w3.org/WAI/WCAG21/Understanding/…`); la única excepción es Focus Appearance, que
     apunta a `WCAG22`.

5. **El mismo nodo de decisión se resuelve distinto según la rama (pág. 2, imagen).**
   - "Anteriormente, ¿La solución fue sugerida por otra persona?" aparece dos veces en el
     diagrama.
   - En la **tercera fila** tiene salida por SI y por NO ("Creá un nuevo componente
     siguiendo los lineamientos de la guía de adopción").
   - En la **segunda fila** sólo tiene salida por SI; la rama NO no existe en el diagrama.
