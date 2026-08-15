# La memoria del harness

## El principio

> **Se lee lo que alguien decidió dejar anotado. No se captura nada.**

Es la diferencia con una memoria que graba todo por las dudas. Un capturador automático
engancha `PostToolUse` y persiste la salida de cada herramienta — incluida la cadena de
conexión que el agente leyó hace un rato. Ahí el secreto queda en dos lugares en vez de uno,
y eso choca de frente con la única regla que este harness bloquea.

Todo lo que el harness recuerda pasó antes por el filtro humano de *"esto vale la pena
escribirlo"*: un commit, una nota en la caché, una definición pendiente. Por eso no puede
filtrar un token: no tiene de dónde sacarlo.

El precio es real y conviene decirlo: **esta memoria es más pobre.** No sabe qué se habló, ni
qué se probó y se descartó, ni por qué se abandonó un camino a mitad. Solo sabe lo que quedó
escrito.

## Las tres capas

| Qué recuerda | Dónde | Quién lo escribe |
|---|---|---|
| **Decisiones y su porqué** | `docs/adr/` | Una persona, cuando toma la decisión |
| **Trabajo hecho** | `git log` y `CHANGELOG.md` | Quien commitea |
| **Conocimiento del proyecto** | `CLAUDE.md` (caliente) → `docs/conocimiento/` (frío) | El agente durante el trabajo; `flush-memoria` lo baja |

## El `CLAUDE.md` y sus zonas

Se carga entero al abrir la sesión y ocupa ventana de contexto mientras dure. Por eso está
partido, y cada zona tiene una política distinta:

| Zona | Qué va | Techo | ¿Se purga? |
|---|---|---|---|
| `HARNESS:COMUN` | Lo genera el instalador | ~25 | Lo reemplaza `-Update` |
| `ZONA FIJA` | Reglas que deben **ejecutarse** cada turno | 60 | **Nunca** |
| `ZONA MAPA` | Dónde está cada cosa. Verificable contra el disco | 20 | No |
| `ZONA ÍNDICE` | Un puntero por archivo del conocimiento | 25 | Lo mantiene `flush-memoria` |
| `ZONA CACHÉ` | Lo aprendido, todavía sin bajar | 80 | **Es lo único purgable** |

Los techos los mide el check `claude-md-zonas` después de cada escritura, y **avisa, nunca
bloquea**. Sin esa medición, "mantener chico el `CLAUDE.md`" es una intención que dura hasta
la primera semana ocupada: agregar una línea acá siempre va a ser más fácil que escribir una
skill.

📌 La regla que decide dónde va algo: **lo que no se necesita en cada turno no va al
`CLAUDE.md`, va en una skill.** Una skill cuesta unos 100 tokens de nombre y descripción, y se
expande solo cuando alguien la invoca.

## El ciclo de la caché

```
se aprende algo  →  una línea en la ZONA CACHÉ     (barato, no interrumpe la tarea)
                 →  flush-memoria lo baja a docs/conocimiento/
                 →  verifica que quedó completo
                 →  recién ahí lo borra, dejando un puntero en la ZONA ÍNDICE
```

**La invariante, que es lo que hace confiable al mecanismo:**

> Nunca se desaloja lo que no se escribió. Antes de borrar una sección hay que poder señalar
> el archivo que contiene **cada hecho** de esa sección. Ante la duda, no se borra.

Una caché más grande de lo ideal cuesta tokens. Una purga mal hecha pierde conocimiento y
nadie se entera. No es simétrico.

El conocimiento va **adentro del repositorio** a propósito: viaja con el proyecto, lo lee
cualquiera del equipo y queda diffeable. Si viviera en la carpeta personal de alguien, el día
que esa persona no está el conocimiento del proyecto tampoco está.

## Qué te dice al abrir una sesión

`SessionStart` contesta *"¿en qué quedamos?"* sin que tengas que preguntarlo:

```
Nahue - harness: comun, analisis v0.6.0
git: develop, 3 con cambios
Ultimo trabajo:
  - regla de secretos punta a punta
  - install.ps1 ya instalable
En la cache quedo anotado:
  - falta validar ES0903 contra un proyecto con codigo
4 definiciones pendientes abiertas
```

Todo eso sale de fuentes que ya existían. El presupuesto son 12 líneas: se paga una vez por
sesión, pero ocupa ventana todo el rato.

## El nombre

El harness te trata por tu nombre. Se pide al instalar y se guarda en
`harness.config.json`, que después no se toca nunca:

```powershell
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Harness analisis -Usuario "Tu Nombre"
```

Si no lo pasás y hay consola, te lo pregunta. Si no hay consola —en un script, en CI— **aborta
explicando** en vez de colgarse esperando una respuesta que nadie puede dar.

Se usa solo para el trato. **No firma archivos ni atribuye cambios**: para eso está git, que
ya lo hace bien, y así no entran datos personales al repositorio por una vía que nadie
audita.
