# Accesibilidad: WCAG 2.2 con Obelisco V2

Cómo el harness hace que una pantalla de un proyecto GCBA cumpla con lo que Obelisco publica y con lo que WCAG 2.2
exige, **sin prometer más de lo que una máquina puede ver**. La spec y su verificación están en
[`docs/cambios/wcag22-obelisco/`](cambios/wcag22-obelisco/spec.md).

## Qué hay, en tres capas

| Capa | Cuándo corre | Qué dice |
|---|---|---|
| **El check liviano** `dev-accesibilidad-html` | Tras cada escritura de HTML, de una plantilla o de JSX/TSX | Solo lo que el archivo decide por sí mismo: un fallo de un criterio, o un defecto de marcado. En silencio si no hay nada |
| **La revisión completa** `review.py` | Cuando el alcance de la tarea lo pide: una pantalla, un formulario, un componente nuevo | Todo lo anterior, más heurísticas, recomendaciones y lo que no pudo decidir; y **qué no analizó** |
| **El registro de evidencia** `a11y-evidence/1` | Al entregar | Criterio por criterio: aprobado, fallido, no aplicable o no probado, con lugar, evidencia y corrección |

La skill `dev-accessibility` es la entrada: es corta, y manda a la guía de la tarea (formularios, teclado y foco, color y
contraste, estructura, contenido dinámico y medios) o a un comando que imprime solo lo que hace falta.

## Las tres fuentes

Cada requisito dice de quién es, y no se mezclan.

| Fuente | Qué es | Etiqueta |
|---|---|---|
| WCAG 2.2 | El requisito normativo del W3C | `wcag` |
| Obelisco V2 | Lo que el sistema de diseño publica para ese componente | `obelisco` |
| Harness y proyecto | Una regla propia, o lo que Obelisco no documenta | `harness` |

La matriz `obelisco-matrix.json` une cada componente y patrón de Obelisco con los criterios que su página declara, los
requisitos que WCAG agrega y cómo se verifica cada uno. Obelisco no publica sección de accesibilidad para validación,
pestañas, tooltip, colapsables, carrusel, switch, navegaciones y pasos de formulario (al 2026-10-23): para esos, los
requisitos son `wcag` o `harness`, y la matriz lo dice.

## El objetivo

**WCAG 2.2 AA**, propuesto por el harness: los 55 criterios de nivel A y AA (31 + 24). WCAG 2.2 tiene 86 criterios (A 31 ·
AA 24 · AAA 31); 4.1.1 Parsing no es uno de ellos, fue retirado y no tiene nivel.

Obelisco pide «WCAG 2.2 en los niveles AA-AAA» y no dice qué AAA. El harness lo lee como AA más los AAA que Obelisco
**nombra**: 2.4.13 Focus Appearance, 3.1.5 Reading Level, 2.2.5 Re-authenticating, 2.4.8 Location y 1.4.6 Contrast
(Enhanced). Son adicionales, solo se exigen si el proyecto los lista en su registro, y nunca se presentan como AA.

## Qué se verifica y qué no

El análisis estático lee HTML, plantillas (Blade, Angular, Twig, Jinja, Handlebars, EJS…) y JSX/TSX con un tokenizador
para cada formato. **No** mira contraste, orden de foco, teclado ni lectores de pantalla, y lo que no puede interpretar —un
componente propio como `<TextField />`, un `{...props}`, un archivo que arma partes con otros— lo lista como **no
analizado**. Las pruebas de navegador, teclado y lector de pantalla figuran como `not_performed` hasta que alguien las
haga: un `pass` que dependa de ellas se rechaza. Un análisis estático limpio no acredita conformidad.

## Un formulario, de punta a punta

El pedido: *agregá el campo «Correo» al alta de turno*.

1. **`dev-ui` elige y enlaza.** El campo es un `OBELISCO_COMPONENT` (`form-text`) dentro del patrón `form-pattern`.
   `wcag.py component form-text` imprime lo que Obelisco declara para el campo de texto (1.1.1, 1.3.1, 1.4.11, 2.1.1,
   2.4.6, 2.4.7, 3.3.2, 4.1.2), lo que WCAG agrega (1.3.5 `autocomplete`, 2.5.3, 1.4.1, 3.3.8) y cómo se verifica. El
   resultado de `dev-ui` lleva una fila `accessibilityLinks` por componente.
2. **Se escribe el archivo y el check liviano habla.** Si el primer borrador es:

   ```tsx
   <input id="correo" name="correo" type="email" />
   ```

   el aviso es:

   ```
   [a11y] alta.tsx: 1 control con id y sin <label for> en este archivo — L5 (criterio 4.1.2, nivel A). Un id solo no es un
   nombre. Si la etiqueta vive en otro archivo, confirmalo; si no, falta.
   ```

   El `id` no es una etiqueta. Con la etiqueta, y con el `autocomplete` que pide 1.3.5, queda en silencio:

   ```tsx
   <label htmlFor="correo">Correo electrónico</label>
   <input id="correo" name="correo" type="email" autoComplete="email" required />
   ```

3. **Se cierra la unidad: revisión completa.** `review.py src/alta.tsx --register evidencia.json --components form-text,form-pattern,button`
   dice «Sin hallazgos estáticos en 1 archivo(s). Eso no acredita conformidad.», la cobertura, y escribe un borrador del
   registro con los 55 criterios en `not_tested`.
4. **Contraste, con números.** El borde del campo: `contrast.py "#767676" "#ffffff"` da 4,54:1 (1.4.11 pide 3:1; el texto,
   1.4.3, 4,5:1). Un color con transparencia se compone antes de medir; un fondo translúcido sin base no da número.
5. **Pruebas manuales.** Teclado (Tab, Enter, orden), lector de pantalla (etiqueta, instrucciones, error anunciado),
   navegador (etiqueta visible, contraste renderizado, zoom al 200 % y reflujo a 320 px, tamaño de objetivo de 24 px).
   Cada una se marca `performed` solo si se corrió.
6. **Se entrega** el registro validado (`wcag.py register validate evidencia.json`), las filas `accessibilityLinks`, las
   entradas `wcag` de `dev-responsive` y el estado de las tres pruebas. `dev-frontend` lo devuelve en
   `accessibilityEvidence`; `dev-quality-validation` lo consume.

## Comandos

Desde `.claude/skills/dev-accessibility/` en un proyecto instalado:

| Comando | Para qué |
|---|---|
| `python scripts/wcag.py count` | Cuántos criterios hay, por nivel (sale de los datos) |
| `python scripts/wcag.py criterion 2.4.11` | Un criterio: nivel, pruebas que exige, texto normativo |
| `python scripts/wcag.py task forms` | Los criterios de una tarea y su guía |
| `python scripts/wcag.py component form-text` | La fila de Obelisco |
| `python scripts/wcag.py levels informe.md` | Marca los pares «criterio / nivel» mal escritos |
| `python scripts/wcag.py register template --level AA` | Un registro vacío |
| `python scripts/wcag.py register validate evidencia.json` | Valida un registro |
| `python scripts/review.py src/ --register evidencia.json` | Revisión completa estática y borrador del registro |
| `python scripts/contrast.py "#333" "rgba(255,255,255,0.8)" --backdrop "#003366"` | Contraste con la transparencia compuesta |

## De dónde sale cada dato

Los niveles, nombres y conteos están en `references/wcag22-criteria.json`, contrastado en los tests contra
`https://www.w3.org/WAI/WCAG22/wcag.json` (`tests/fixtures/wcag22-w3c.json`). El texto normativo, las técnicas y los
procedimientos de prueba están en `references/wcag22/`, importados de la skill `wcag22` con su procedencia en `SOURCE.md`.
Las páginas de Obelisco se consultaron el 2026-10-23: la matriz cita cada una y su fecha, y puede quedar vieja.
