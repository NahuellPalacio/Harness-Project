# El primer recorrido, corrido de verdad

**Fecha:** 2026-08-21 · **Sobre:** este mismo repositorio, `gcba-harness` v0.13.0

🔴 **Esto no es una verificación.** Es la evidencia que la Task 5 del plan tenía que producir:
cuánto sale un recorrido, y qué se observó al leer lo que dejó escrito. El veredicto lo escribe
`harness-spec-refuter` en `verificacion.md`, y quien construyó no verifica.

## Lo que costó, que era el número que no tenía nadie

| | |
|---|---|
| Corpus | 180 archivos versionados · ~21.900 líneas |
| | 86 `.md` · 34 `.py` · 17 `.json` · 13 `.ps1` · 3 `.html` · 2 `.ts` |
| **Tokens** | **140.840** |
| **Reloj** | **9 min 45 s** |
| Llamadas a herramienta | 40 |
| Salida | 13 fichas + `indice.md` · 705 líneas |

Rendimiento: **unos 780 tokens por archivo versionado**, o **6,4 tokens por línea de corpus**.
Sirve para estimar antes de correrlo en otro lado: un repo de 1.000 archivos del mismo perfil se
va a ir cerca de 780.000 tokens, y ahí la sugerencia de `SessionStart` deja de ser inocente.

📌 **El número depende del perfil del corpus, no solo del tamaño.** Este repo es 86 `.md` de
documentación densa; un repo de código tiene más archivos y menos prosa por archivo. Antes de
prometer el número en otro proyecto hay que volver a medirlo.

## Lo que se observó al leer lo escrito

**El check no encontró nada.** `dev-codebase-forma.py` corrido sobre los 14 archivos: cero
hallazgos. La biyección índice↔fichas cierra en los dos sentidos y las trece fichas tienen sus
cuatro secciones con el título exacto.

**El riesgo que E-09 no cubre no se materializó.** Las cuatro secciones podían estar y no decir
nada; no fue el caso. Se contrastó la ficha `comun/hooks` contra el código, que es la parte de
este repo que más se conoce, y todo lo afirmado se sostiene. Dos datos se verificaron uno por uno
porque son los que un resumen inventa:

- *"doce patrones (diez de confianza alta, dos media) y quince patrones de excepción"* — el
  catálogo tiene exactamente 12, con 10 `alta` y 2 `media`, y 15 patrones de ignorar.
- La razón por la que `lib/reglas.py` carga los checks por ruta y no por nombre de módulo —los
  nombres llevan guiones— está bien contada y es la real.

**El agrupamiento no fue mecánico.** Trece módulos para 180 archivos, agrupados por lo que alguien
nombraría en voz alta: *el instalador, los hooks, los checks, la suite, la normativa*. Los cinco
checks de `desarrollo` y el de `comun` quedaron en una sola ficha aunque vivan en dos árboles
distintos, porque comparten contrato y presupuesto. Era el riesgo más probable —una ficha por
archivo, o sea un listado de directorio— y no ocurrió.

**Nada se escribió fuera de `docs/codebase/`.** `git status` no muestra ningún otro archivo nuevo
ni modificado por el recorrido.

**Lo no versionado quedó afuera solo.** El agente reportó que `docs/cambios/mapa-en-la-bitacora/spec.md`
existe en disco y no está en `git ls-files`, así que no lo indexó. Es E-12 funcionando por
construcción, y de paso encontró un archivo sin commitear que nadie había mirado.

## Lo que este recorrido no pudo mostrar

Tres escenarios quedaron sin evidencia, y no por descuido:

- **E-13** (un segundo recorrido no duplica fichas) — cuesta otros 140.000 tokens. Se mide cuando
  haya una razón para volver a correrlo, no para producir una marca.
- **E-14** (una ficha huérfana se reporta y no se borra) — no había fichas previas: era el primer
  recorrido. Solo se puede observar en el segundo.
- **E-17** (un repositorio sin código no escribe nada) — este repo tiene código.

## Hallazgos del recorrido, que no son sobre el recorrido

Lo que el agente encontró mirando el repo, y que es el primer rédito de tenerlo:

1. **`tests/generar-testigo.ps1` no se puede ejecutar.** Importa `Hook.psm1`, `Secretos.psm1`,
   `Reglas.psm1` y `Zonas.psm1` de `comun/hooks/lib/`, y los cuatro dejaron de existir al portar
   los hooks a Python en 0.13.0. Verificado: no hay ningún `.psm1` en ese directorio. Queda
   anotado en `Pendientes/Fix-Harness/PENDIENTES-FH.md`.

2. **Datos personales en el repo, nombrados por archivo y nunca por valor.** El nombre de pila del
   dueño en `docs/memoria.md` y en dos archivos más, y su usuario de GitHub en la URL de clonado
   de `docs/instalacion.md`. Parece deliberado; se nombra porque el repositorio es público y la
   decisión no está escrita en ningún lado.

3. **Y la manera correcta ya está en el repo, como referencia:** `normativa/extractos/GuiaDGISIS.md`
   y `dev-tramites-asi/SKILL.md` declaran que el CUIL real de una persona **está omitido a
   propósito**. Se comprobó que efectivamente no está: queda la regla, no el dato.
