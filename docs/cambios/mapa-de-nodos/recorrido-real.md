# El recorrido del mapa de nodos, corrido de verdad

**Fecha:** 2026-08-22 · **Sobre:** un clon de `ProtfolioPersonal`, Next.js con TypeScript, con el
harness instalado por `install.ps1` (`-Harness desarrollo`, v0.13.0, 50 archivos en el lockfile)

🔴 **Esto no es una verificación, y no es la lectura.** Es el registro de la corrida: qué costó y
qué quedó escrito. La lectura que pide [ADR-0009](../../adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md)
va en [`lectura.md`](lectura.md) y **la firma alguien que no construyó** — este archivo lo escribió
quien construyó, así que no puede sustituirla. El veredicto lo escribe `harness-spec-refuter` en
`verificacion.md`.

## Por qué sobre un proyecto ajeno y no sobre este repo

Las 13 fichas de `gcba-harness` ya estaban enlazadas **a mano, por quien construyó el cambio**.
Correr el recorrido acá habría medido si el agente reproduce un trabajo que ya estaba hecho, no si
lo hace. Y el proyecto elegido no es Python: el recorredor no puede apoyarse en lo que ya conoce de
la fábrica.

El costo de esa decisión está abajo, en lo que el recorrido no pudo mostrar.

## Lo que costó

| | |
|---|---|
| Corpus | 40 archivos versionados · 2.019 líneas (sin `package-lock.json` ni el PDF) |
| | 18 `.tsx` · 12 `.ts` · 6 `.json` · 1 `.mjs` · 1 `.css` · 1 `.pdf` |
| **Tokens** | **85.719** |
| **Reloj** | **7 min 38 s** |
| Llamadas a herramienta | 32 |
| Salida | 9 fichas + `indice.md` · 365 líneas · más `mapa.html` |

Rendimiento: **2.143 tokens por archivo versionado**, o **42 tokens por línea de corpus**.

📌 **Los dos números contradicen al recorrido anterior, y la contradicción informa.** El del
21-08-2026 sobre este repo dio 780 tokens por archivo y 6,4 por línea. Este dio casi tres veces más
por archivo y casi siete veces más por línea. No es que el código sea siete veces más caro de leer:
es que **el costo fijo —leer el contrato, la config, `git ls-files`, decidir los módulos— se
reparte entre 40 archivos en vez de 180**. La estimación por archivo no escala hacia abajo, y
cualquier promedio sacado de una sola corrida va a mentir en la otra punta.

## Lo que quedó escrito, medido

No son observaciones: son cuentas que cualquiera puede rehacer sobre el material del apéndice.

- **10 archivos** en `docs/codebase/`: nueve fichas y el índice, más `mapa.html`.
- **El mapa:** 9 nodos, 20 aristas, 1 huérfana — `app.md`.
- **Orden de escritura**, por hora de modificación: las nueve fichas entre las 01:46:02 y las
  01:48:05, `indice.md` a las **01:48:14**, `mapa.html` a las **01:48:25**.
- **El check no encontró nada.** `dev-codebase-forma.py` corrido sobre los diez `.md`: cero
  hallazgos. Ningún enlace roto, ningún `[[wikilink]]`, las cuatro secciones en las nueve fichas.
- **Nada escrito afuera.** `git status` sobre el clon: `docs/` sin seguimiento, y los dos cambios
  que había dejado el instalador antes de empezar —`.gitignore` modificado y `CLAUDE.md` nuevo—.

### La matriz de aristas

| Ficha | Enlaces | A quién |
|---|---|---|
| `app.md` | 4 | `components-layout.md`, `components-sections.md`, `config.md`, `i18n.md` |
| `components-layout.md` | 2 | `i18n.md`, `lib.md` |
| `components-sections.md` | 5 | `components-ui.md`, `data.md`, `i18n.md`, `lib.md`, `types.md` |
| `components-ui.md` | 2 | `i18n.md`, `lib.md` |
| `config.md` | 1 | `i18n.md` |
| `data.md` | 2 | `i18n.md`, `types.md` |
| `i18n.md` | 1 | `config.md` |
| `lib.md` | 1 | `types.md` |
| `types.md` | 2 | `data.md`, `i18n.md` |

## Lo que este recorrido no pudo mostrar

- **El segundo recorrido.** No se corrió dos veces, así que no dice nada sobre si una segunda
  pasada duplica fichas o las pisa. Eso es E-13 del cambio `iniciador-code`, no de éste, pero
  seguía sin observarse y sigue.
- **Un proyecto grande.** 40 archivos son pocos. El riesgo de escala que la spec declara —trece
  nodos se leen, trescientos son una nube— no se tocó ni de lejos.
- **El mapa en el navegador.** Nada de acá dice que el panel abra ni que la rueda desplace. Es el
  agujero declarado de la spec, y sigue abierto: se cierra abriendo el archivo, no leyendo esto.
- **Las versiones homologadas.** El agente lo dice en su informe: `verificarVersionesHomologadas`
  está en `true` en la config y no las verificó, porque no tenía el estándar a mano y no lo iba a
  inventar. Es la regla de no inventar funcionando, y también una capacidad que no corrió.

## Hallazgos del recorrido, que no son sobre el recorrido

Salieron del informe del agente, que tiene por contrato reportar lo que ve. Son del proyecto
recorrido, no del harness, y quedan acá porque el clon es descartable y el proyecto real no:

1. **`skillCategories` no declara la pestaña `cloud`**, que sí existe en el tipo `SkillCategory`.
   AWS está cargada con esa categoría, así que no aparece bajo ningún filtro salvo «Todos».
   `src/data/skills.ts` contra `src/types/index.ts`.
2. **`nav.download_cv` está en los dos diccionarios y no lo usa ningún componente.** No hay botón
   de descarga, y el PDF está en la raíz y no en `public/` —que no existe—, así que hoy tampoco
   sería servible.
3. **Los metadatos del sitio están en español fijo**, fuera de las traducciones: la versión en
   inglés sirve título, descripción y Open Graph en español.
4. **Una URL de servicio externo literal como fallback** en `src/components/sections/Contact.tsx`:
   el endpoint se lee de `NEXT_PUBLIC_FORMSPREE_ENDPOINT` pero queda una URL de Formspree escrita
   en el fuente. No es un secreto —es un identificador público de formulario— y contradice igual la
   regla de que los servicios externos se leen del entorno.
5. **El CV en PDF está versionado en la raíz.** No es un defecto y es una decisión que conviene
   tomar despierto: un CV en el historial de git es más difícil de sacar después que de no poner
   ahora.

**Secretos: ninguno.** Y los datos personales del portfolio —mail, LinkedIn, historial laboral—
están en el proyecto por diseño; el agente los nombró **por archivo y nunca por valor**, que es su
regla. Por eso el material de abajo se puede versionar acá sin arrastrar nada.

## El informe que devolvió el agente, textual

Va entero y sin editar porque **E-20 se lee sobre esto**, no sobre las cuentas de arriba: el
escenario dice que el reporte declara nodos, aristas y cuáles son las huérfanas. Resumirlo sería
quitarle al que lee justo lo que tiene que juzgar.

> **Qué escribí.** 9 fichas nuevas más `indice.md`, en `docs/codebase/` (`rutaCodebase` de
> `harness.config.json`). El directorio no existía: nadie había mapeado el proyecto, así que no
> dejé ninguna ficha sin tocar ni pisé nada escrito a mano.
>
> Los módulos: `app`, `i18n`, `components/layout`, `components/sections`, `components/ui`, `data`,
> `lib`, `types`, `config`. Cubren los 40 archivos que devuelve `git ls-files`.
>
> **El mapa.** `mapa-codigo.py` corrió sobre las fichas y escribió `docs/codebase/mapa.html`:
> **9 nodos, 20 aristas, 1 huérfana**.
>
> La huérfana es `app.md`, y es correcta: el App Router es el punto de entrada, lo invoca Next.js y
> no lo importa ningún módulo del proyecto. No falta un enlace — no hay quién lo enlace. Vale
> decirlo igual: si mañana aparece una segunda ruta y `app` sigue huérfano, ahí sí hay algo que
> revisar.
>
> **Fichas sin módulo:** ninguna. Índice y fichas cierran en las dos direcciones (verificado).
>
> **Qué no recorrí.** `package-lock.json` (235 KB): generado, no lo leí; las versiones las tomé de
> `package.json`. El PDF del CV: binario, no lo abrí — lo nombro en `config.md` sólo para que ningún
> archivo versionado quede invisible en el índice. `.claude/`: está gitignorado, `git ls-files` no
> lo lista y no es código del proyecto. No verifiqué versiones homologadas contra el estándar de
> ASI, aunque `verificarVersionesHomologadas` está en `true`: no tengo el estándar a mano y no iba a
> inventarlo. No hay tests ni dependencias de testing, así que el `umbralCobertura: 80` de la config
> no tiene hoy contra qué medirse.

📌 **Lo que el informe no dice.** El contrato del agente le pide tres cosas —cuántas escribió,
cuántas dejó igual y qué no recorrió— y las tres están. Lo que no declara con esas palabras es
«cuántas dejé igual»: dice que el directorio no existía, de lo que se deduce que ninguna. Es
correcto y es una deducción del lector, no una afirmación del informe. Quien lea que decida si eso
alcanza.

## El material, para que la lectura sobreviva al temporal

🔴 **Esta sección no está en el precedente, y hay un motivo.** El recorrido del 21-08-2026 fue
sobre este mismo repositorio: su salida quedó versionada sola. Éste fue sobre un clon en un
directorio temporal de sesión, y cuando se limpie no va a quedar nada que leer. Sin el material,
[`lectura.md`](lectura.md) no se puede llenar y los cuatro escenarios quedan `sin sustento` para
siempre.

📌 **`mapa.html` no se copia y no hace falta.** El layout es determinista: con estas nueve fichas
en un directorio, `python comun/bin/mapa-codigo.py <ese directorio>` reproduce el mismo archivo,
byte por byte. El mapa **es** una función de las fichas, y las fichas están acá.

📌 **Va en bloques cercados y no pegado como markdown**, por dos motivos: los títulos de una ficha son `##` y chocarían con las secciones de este documento, y para leer E-01 conviene ver el enlace **como enlace** —`[data](data.md)`— y no su texto renderizado.


### `indice.md`

````markdown
# Índice del código

_(Lo escribe `dev-iniciador-code`. Se regenera entero; no editar a mano.)_

- `app` — El App Router: una sola ruta bajo `[locale]`, el layout y la home → [`app.md`](app.md)
- `components/layout` — Barra fija, pie y selector de idioma → [`components-layout.md`](components-layout.md)
- `components/sections` — Las seis secciones de la home, de Hero a Contact → [`components-sections.md`](components-sections.md)
- `components/ui` — Los siete componentes de presentación reutilizables → [`components-ui.md`](components-ui.md)
- `config` — Build, tipado y sistema de diseño: de acá salen el alias `@/*` y la paleta → [`config.md`](config.md)
- `data` — El contenido del portfolio escrito a mano: experiencia, proyectos y skills → [`data.md`](data.md)
- `i18n` — El bilingüismo entero sobre `next-intl`: rutas, middleware y diccionarios → [`i18n.md`](i18n.md)
- `lib` — `cn()` y el catálogo de animaciones → [`lib.md`](lib.md)
- `types` — Los tipos compartidos, con la forma bilingüe `{ es, en }` en el centro → [`types.md`](types.md)
````

### `app.md`

````markdown
# app

## Qué es

El App Router de Next.js 15. Tiene **una sola ruta** —la home— bajo el segmento dinámico
`[locale]`, y ahí adentro arma el HTML, carga las fuentes, monta el proveedor de traducciones y
apila las seis secciones de la página. Es el punto de entrada del sitio: no lo importa ningún otro
módulo, lo llama el framework.

## Qué expone

- `LocaleLayout` (`layout.tsx`) — layout raíz por idioma. Valida que el `locale` de la URL esté en
  la lista de [i18n](i18n.md) y si no, `notFound()`. Carga Inter y JetBrains Mono con
  `next/font/google` y envuelve el árbol en `NextIntlClientProvider` con los mensajes del locale.
- `metadata` — título, descripción, keywords, autor y Open Graph. Está escrito en español fijo, en
  el código: **no sale de los archivos de traducción**, así que la versión en inglés del sitio
  muestra metadatos en español.
- `Home` (`page.tsx`) — la única página. Renderiza `Navbar`, las seis secciones en orden (Hero,
  About, Skills, Experience, Projects, Contact) y `Footer`.
- `globals.css` — las tres directivas de Tailwind, el reset, el `scroll-behavior: smooth`, el
  scrollbar propio y tres utilidades: `text-balance`, `glow-cyan`, `border-glow-cyan`.

## De qué depende

- [i18n](i18n.md) — `routing` para validar el locale y `getMessages()` para alimentar el proveedor.
- [components/layout](components-layout.md) — `Navbar` y `Footer`.
- [components/sections](components-sections.md) — las seis secciones de la home.
- [config](config.md) — el alias `@/*` de `tsconfig.json` y los tokens de color y tipografía de
  `tailwind.config.ts`, que son los que resuelven las clases que usa el layout.
- Externas: `next`, `next-intl`, `next/font/google`.

## Dónde está

- `src/app/[locale]/layout.tsx`
- `src/app/[locale]/page.tsx`
- `src/app/globals.css`
````

### `components-layout.md`

````markdown
# components/layout

## Qué es

El cascarón de la página: la barra de navegación fija de arriba, el pie de abajo y el selector de
idioma que vive dentro de la barra. Los tres son componentes de cliente (`'use client'`) y son lo
único que se ve en todas las secciones por igual.

## Qué expone

- `Navbar` — barra fija con `z-50` que se vuelve opaca con `backdrop-blur` al pasar los 20px de
  scroll. Tiene los cinco enlaces de ancla (`#about`, `#skills`, `#experience`, `#projects`,
  `#contact`) definidos en la constante local `NAV_LINKS`, el logo `NP.`, el selector de idioma y un
  menú hamburguesa para mobile con su propio estado abierto/cerrado.
- `Footer` — copyright con el año calculado en tiempo de render (`new Date().getFullYear()`),
  enlaces a LinkedIn y a mail, y dos textos traducidos (`footer.rights`, `footer.made_with`).
- `LanguageSwitcher` — el par de botones `ES | EN`. Cambia de idioma con
  `router.replace(pathname, { locale })`, es decir sin recargar y conservando la ruta actual.

## De qué depende

- [i18n](i18n.md) — `useTranslations` para los textos, y `useRouter`/`usePathname` de
  `@/i18n/navigation` en el selector de idioma.
- [lib](lib.md) — `cn()` para componer clases condicionales.
- Externas: `react-icons` (`FaLinkedin`, `HiMail`, `HiMenuAlt3`, `HiX`), `next-intl`.

## Dónde está

- `src/components/layout/Navbar.tsx`
- `src/components/layout/Footer.tsx`
- `src/components/layout/LanguageSwitcher.tsx`
````

### `components-sections.md`

````markdown
# components/sections

## Qué es

Las seis secciones que forman la home, en el orden en que se apilan. Cada una es un componente de
cliente, se envuelve en `SectionWrapper` con un `id` que es el ancla de la navegación, y saca sus
textos de las traducciones y sus datos de [data](data.md).

Es la capa donde se decide *qué* se muestra; el *cómo* está en [components/ui](components-ui.md).

## Qué expone

- `Hero` (`#hero`) — la portada a pantalla completa. Única sección que **no** usa `SectionWrapper`:
  arma su propio `<section>` para poder poner la grilla de fondo y los dos gradientes radiales.
  Parte `hero.role` por el carácter `&` para colorear las dos mitades distinto — si esa traducción
  pierde el `&`, la segunda mitad queda vacía.
- `About` (`#about`) — dos párrafos de bio, ubicación y educación, y tres tarjetas de propuesta de
  valor definidas en la constante local `VALUE_PROPS` (ícono y color están en el código; título y
  descripción, en las traducciones).
- `Skills` (`#skills`) — filtro por categoría con estado local (`'all'` o una `SkillCategory`) y la
  grilla de barras. Las etiquetas de las pestañas salen de `skillCategories`, no de las
  traducciones.
- `Experience` (`#experience`) — la línea de tiempo. Arma el período como
  `inicio — fin`, y si `period.end` es `null` usa el texto traducido `experience.present`.
- `Projects` (`#projects`) — grilla de tarjetas de proyecto, hasta tres columnas.
- `Contact` (`#contact`) — datos de contacto y el formulario. Valida con un esquema Zod local
  (`name` ≥ 2, `email` con formato, `message` ≥ 10) vía `react-hook-form`, y hace `POST` con `fetch`
  a un endpoint de Formspree. Maneja cuatro estados: `idle`, `sending`, `success`, `error`.
- 🔴 En `Contact.tsx` el endpoint se lee de `process.env.NEXT_PUBLIC_FORMSPREE_ENDPOINT` pero tiene
  una **URL de Formspree escrita como fallback en el código**. No es un secreto, pero es
  configuración adentro del fuente: contradice la regla del repo de que servicios externos y URLs
  se leen del entorno.

## De qué depende

- [components/ui](components-ui.md) — `SectionWrapper`, `SectionTitle`, `Button`, `SkillBar`,
  `TimelineItem`, `ProjectCard`.
- [data](data.md) — `experiences`, `projects`, `skills`, `skillCategories`.
- [lib](lib.md) — las variantes de animación (`fadeInUp`, `fadeInRight`, `staggerContainer`) y `cn()`.
- [types](types.md) — `SkillCategory`, que tipa el estado del filtro de `Skills`.
- [i18n](i18n.md) — `useTranslations` para los textos y `useLocale` para elegir la rama `es`/`en` de
  los datos bilingües.
- Externas: `framer-motion`, `react-hook-form`, `@hookform/resolvers/zod`, `zod`, `react-icons`.

## Dónde está

- `src/components/sections/Hero.tsx`
- `src/components/sections/About.tsx`
- `src/components/sections/Skills.tsx`
- `src/components/sections/Experience.tsx`
- `src/components/sections/Projects.tsx`
- `src/components/sections/Contact.tsx`
````

### `components-ui.md`

````markdown
# components/ui

## Qué es

Los siete componentes de presentación reutilizables. No saben nada del contenido del portfolio:
reciben todo por props ya resuelto al idioma correcto y se ocupan del layout, los estilos y las
animaciones. Es la librería propia del proyecto.

📌 El estándar del repo pide componentes de Obelisco. Estos son propios, hechos con Tailwind. Queda
señalado, no resuelto.

## Qué expone

- `SectionWrapper` — el `<section>` con `id`, padding y ancho máximo de 6xl. Dispara la animación
  de entrada con `whileInView` y `viewport={{ once: true, margin: '-80px' }}`, y reparte el
  `staggerContainer` a los hijos. Todas las secciones menos `Hero` pasan por acá.
- `SectionTitle` — `h2` con subtítulo opcional y la barrita cian de abajo.
- `Button` — variantes `primary` / `outline` / `ghost` y tamaños `sm` / `md` / `lg`. Es un
  `forwardRef`; si recibe `href` renderiza un `<a>` en vez de un `<button>` —y en ese caso el `ref`
  y los `...props` del botón se pierden.
- `Badge` — pastilla con variantes `default` / `cyan` / `purple` / `emerald` / `outline`, en
  tipografía mono.
- `SkillBar` — nombre, porcentaje y la barra que se llena con `whileInView`, con retardo escalonado
  según el `index`.
- `TimelineItem` — el ítem de la línea de tiempo: punto, línea vertical (que se omite en el último),
  rol, empresa, período, viñetas de descripción y badges de tecnología.
- `ProjectCard` — la tarjeta de proyecto. Único componente de esta capa con estado propio: expande
  y contrae el detalle (desafío, solución, resultados) con `AnimatePresence`. También es el único
  que llama a `useTranslations` por su cuenta, para los rótulos de ese detalle.

## De qué depende

- [lib](lib.md) — `cn()` y las variantes de animación (`scaleIn`, `fadeInUp`, `fadeInLeft`,
  `staggerContainer`).
- [i18n](i18n.md) — solo `ProjectCard`, con `useTranslations('projects')`.
- Externas: `framer-motion`, `react`, `clsx` y `tailwind-merge` (indirectas, vía `cn`).

## Dónde está

- `src/components/ui/SectionWrapper.tsx`
- `src/components/ui/SectionTitle.tsx`
- `src/components/ui/Button.tsx`
- `src/components/ui/Badge.tsx`
- `src/components/ui/SkillBar.tsx`
- `src/components/ui/TimelineItem.tsx`
- `src/components/ui/ProjectCard.tsx`
````

### `config.md`

````markdown
# config

## Qué es

Los archivos de la raíz que definen cómo se construye, se tipa y se estiliza el proyecto. No tienen
lógica propia, pero de acá salen dos cosas de las que depende todo el código: el alias `@/*` y la
paleta de Tailwind.

## Qué expone

- `package.json` — Next.js `15.3.9`, React `19`, TypeScript `5.7`, `next-intl` `3.26.5`,
  `framer-motion` `11`, `tailwindcss` `3.4`, `react-hook-form` + `zod` + `@hookform/resolvers`,
  `react-icons`, `clsx` y `tailwind-merge`. Scripts: `dev`, `build`, `start`, `lint`. No hay script
  de test ni dependencias de testing.
- `next.config.ts` — `reactStrictMode: true` y el plugin de `next-intl` apuntando a
  `./src/i18n/request.ts`.
- `tsconfig.json` — `strict: true`, `moduleResolution: 'bundler'`, target ES2017 y el alias
  `@/* → ./src/*` que usan todos los imports del proyecto.
- `tailwind.config.ts` — el sistema de diseño: paleta oscura (`background`, `accent` con cian,
  púrpura y esmeralda, `text`, `border`), fuentes Inter y JetBrains Mono, la grilla de fondo del
  hero, tres sombras de glow y las animaciones `bounce-slow`, `pulse-slow` y `fade-in`. Sin plugins.
- `postcss.config.mjs` — Tailwind y Autoprefixer.
- `.eslintrc.json` — extiende `next/core-web-vitals`, nada más.
- `.gitignore` — el estándar de Next.js más dos bloques delimitados del harness: uno que ignora
  `.claude/` salvo `settings.json.ejemplo`, y otro de secretos (`.env*`, `secrets/`, `*.key`,
  `*.pem`, `*.pfx`, `*.p12`, `*.keystore`).

## De qué depende

- [i18n](i18n.md) — `next.config.ts` referencia por ruta a `src/i18n/request.ts`. Es el único
  acoplamiento del build al código.
- Externas: todo el ecosistema Next.js / Tailwind / PostCSS listado arriba.

## Dónde está

- `package.json`, `package-lock.json`
- `next.config.ts`
- `tsconfig.json`
- `tailwind.config.ts`
- `postcss.config.mjs`
- `.eslintrc.json`
- `.gitignore`
- `CV-Nahuel.Palacio  Actualizado.pdf` — no es configuración; es el único binario versionado y está
  en la raíz, no en `public/`. Se lo nombra acá para que ningún archivo del repo quede fuera del
  índice.
````

### `data.md`

````markdown
# data

## Qué es

El contenido del portfolio, escrito a mano como constantes TypeScript. No hay CMS, ni base de
datos, ni fetch: cambiar la experiencia laboral o agregar un proyecto es editar estos tres archivos
y volver a construir.

Los textos que dependen del idioma viven acá mismo como objetos `{ es, en }`; los componentes
eligen la rama con `useLocale()`. Es decir que hay **dos fuentes de texto en el proyecto**: estos
archivos para el contenido, y los diccionarios de [i18n](i18n.md) para los rótulos de la interfaz.

## Qué expone

- `experiences: Experience[]` — cinco puestos, del más reciente al más viejo: Tecba (GCBA), Autosal
  S.A, OCA LOG, Kaver Consulting (Makro) y Prisma Medios de Pago (Itrio S.A). Cada uno con rol,
  período con inicio y fin bilingües, viñetas de descripción y lista de tecnologías. `period.end`
  puede ser `null` para indicar "actualidad" —hoy ninguno lo usa: los cinco tienen fin.
- `projects: Project[]` — tres proyectos: automatización de reportes e-commerce, sistema de
  integraciones e-commerce y sistema de gestión de conocimiento. Cada uno con desafío, solución,
  resultados, tecnologías, color de acento y un emoji como ícono.
- `skills: Skill[]` — veintidós habilidades con un `level` numérico de 0 a 100 y una categoría.
- `skillCategories` — las siete pestañas del filtro (`all` más seis categorías) con su etiqueta
  bilingüe. Es un `as const`, así que las claves son literales.
  🔴 Falta la pestaña `cloud`, que sí existe en el tipo `SkillCategory` de [types](types.md). AWS
  está cargada con esa categoría y por eso no aparece bajo ningún filtro salvo "Todos".

## De qué depende

- [types](types.md) — `Experience`, `Project`, `Skill` y sus tipos auxiliares tipan las tres
  constantes.
- Nada externo. Son datos puros, sin imports de librerías.

## Dónde está

- `src/data/experience.ts`
- `src/data/projects.ts`
- `src/data/skills.ts`
````

### `i18n.md`

````markdown
# i18n

## Qué es

Todo el bilingüismo del sitio, montado sobre `next-intl`. Define los dos idiomas (`es` por defecto,
`en`), el middleware que resuelve el idioma a partir de la URL, la carga de los archivos de
mensajes y los helpers de navegación que preservan el locale al cambiar de ruta.

El prefijo de locale es `as-needed`: el español —idioma por defecto— vive en `/` sin prefijo, y el
inglés en `/en`.

## Qué expone

- `routing` (`routing.ts`) — la definición central: `locales: ['es', 'en']`, `defaultLocale: 'es'`,
  `localePrefix: 'as-needed'`. Es la única fuente de verdad de qué idiomas existen.
- `Link`, `redirect`, `usePathname`, `useRouter` (`navigation.ts`) — los envoltorios de navegación
  conscientes del locale. Los usa el selector de idioma para hacer
  `router.replace(pathname, { locale })`.
- El `getRequestConfig` por defecto (`request.ts`) — resuelve el locale de la request, cae al de
  defecto si viene uno desconocido, e importa dinámicamente `messages/<locale>.json`.
- El middleware raíz (`middleware.ts`) — `createMiddleware(routing)` con un matcher que excluye
  `api`, `_next`, `_vercel` y cualquier ruta con extensión.
- Los diccionarios `messages/es.json` y `messages/en.json`, con ocho grupos de claves: `nav`,
  `hero`, `about`, `skills`, `experience`, `projects`, `contact`, `footer`. Los dos archivos tienen
  exactamente el mismo conjunto de claves.
- 🔴 Hueco: `nav.download_cv` está en los dos diccionarios pero **ningún componente la usa** — no
  hay botón de descarga de CV. El PDF está versionado en la raíz del repo y no en `public/`
  (directorio que no existe), así que hoy tampoco sería servible. Definición pendiente: o se
  implementa el botón, o sobra la clave.

## De qué depende

- [config](config.md) — `next.config.ts` engancha el plugin
  `createNextIntlPlugin('./src/i18n/request.ts')`; sin eso, nada de esto se activa.
- Externas: `next-intl` (`3.26.5`), `next`.

## Dónde está

- `src/i18n/routing.ts`
- `src/i18n/navigation.ts`
- `src/i18n/request.ts`
- `middleware.ts` — en la raíz del repo, no en `src/`
- `messages/es.json`, `messages/en.json`
````

### `lib.md`

````markdown
# lib

## Qué es

Dos utilidades chicas que usa casi todo lo demás: el compositor de clases de Tailwind y el catálogo
de animaciones de Framer Motion. Nada de lógica de negocio.

Que las variantes de animación estén acá y no repetidas en cada componente es lo que hace que todo
el sitio entre en pantalla con el mismo ritmo.

## Qué expone

- `cn(...inputs)` (`utils.ts`) — `clsx` y después `twMerge`. Junta clases condicionales y resuelve
  los conflictos de Tailwind quedándose con la última.
- Las variantes de animación (`animations.ts`), todas del tipo `Variants` con estados `hidden` y
  `visible`: `fadeInUp`, `fadeInDown`, `fadeInLeft`, `fadeInRight`, `scaleIn` y `staggerContainer`
  —esta última no anima nada por sí misma: solo escalona a los hijos cada 0,1 s.
- `fadeInDown` está declarada pero ningún componente la usa hoy.

## De qué depende

- Externas: `clsx`, `tailwind-merge`, y el tipo `Variants` de `framer-motion`.
- Nada de este proyecto: es la otra hoja del grafo, junto con [types](types.md).

## Dónde está

- `src/lib/utils.ts`
- `src/lib/animations.ts`
````

### `types.md`

````markdown
# types

## Qué es

Un único archivo con los tipos compartidos del proyecto. Su idea central es `BilingualString` /
`BilingualArray`: la forma `{ es, en }` que hace que el contenido bilingüe sea un dato y no dos
copias del mismo objeto.

Es la hoja del grafo: no importa nada de nadie.

## Qué expone

- `Locale` — `'es' | 'en'`. Se duplica de hecho con la lista de `locales` de [i18n](i18n.md): son
  dos declaraciones del mismo conjunto que nada obliga a mantener sincronizadas.
- `BilingualString` — `{ es: string; en: string }`.
- `BilingualArray` — `{ es: string[]; en: string[] }`.
- `SkillCategory` — unión de siete categorías: `language`, `database`, `cloud`, `devops`, `api`,
  `management`, `ai`. El filtro de la sección arma su estado como `'all' | SkillCategory`.
  🔴 `skillCategories` en [data](data.md) declara solo seis de las siete: falta `cloud`, así que la
  única habilidad de esa categoría —AWS— no tiene pestaña y solo se ve en "Todos".
- `Skill` — `name`, `level`, `category`, `icon` opcional.
- `Experience` — `id`, `company`, `companyDetail` opcional, `role`, `period` (con `end` anulable),
  `description` y `tech`.
- `Project` — `id`, `title`, `description`, `challenge`, `solution`, `results`, `tech`, `category`,
  `accentColor`, `icon`.

## De qué depende

- Nada. Ni módulos de este proyecto ni librerías externas: son declaraciones de tipo puras.

## Dónde está

- `src/types/index.ts`
````
