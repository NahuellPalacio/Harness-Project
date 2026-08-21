# docs

## Qué es

La documentación del harness: la puerta de entrada, las guías de uso y las decisiones tomadas
con su fundamento.

Se lee en tres capas. El `README.md` contesta qué es esto y cómo se instala; las guías
contestan cómo funciona cada mecanismo; los ADR contestan **por qué está así** y no de la otra
forma que parecía más obvia.

Hay además dos mapas en HTML que se publican como artefactos web y se actualizan en la misma
URL cuando el flujo cambia.

## Qué expone

- **`README.md`** — qué es un harness, los dos que hay, requisitos, la versión corta de la
  instalación, qué se escribe en el proyecto, cómo se comporta (avisa, casi nunca bloquea) y
  qué recuerda. Declara también el límite honesto de `permissions.deny`: cubre lo que se
  resuelve como una ruta, y una lectura indirecta puede escapar.
- **`instalacion.md`** — el paso a paso completo por PowerShell y por bash, con los problemas
  frecuentes y su salida exacta.
- **`contrato-hooks.md`** — todo lo que hay que saber para escribir un hook: entrada, las tres
  salidas, el silencio, y las trampas nuevas que trajo Python.
- **`memoria.md`** — el principio de la memoria del harness: se lee lo que alguien decidió
  dejar anotado, no se captura nada. Las zonas del `CLAUDE.md` y sus techos.
- **`secretos.md`** — la única regla que bloquea, y por qué son dos mecanismos
  complementarios: uno protege lo que no se debe leer y el otro lo que no se debe escribir.
- **`agregar-un-harness.md`** — cómo agregar el tercero: crear su `manifest.json`, y nada más.
- **`adr/`** — siete decisiones aceptadas: el nombre de la rama de desarrollo, copiar en vez de
  enlazar, Obsidian afuera del harness, no usar la estructura `source/` de ES0901, lo de
  terceros separado de lo propio, SDD como método de los proyectos instalados, y que lo externo
  se aprovecha pero nunca es requisito. **No hay ADR-0007**: la numeración salta.
- **`mapa/`** — dos páginas HTML autocontenidas: una recorre lo que le pasa a un mensaje desde
  que alguien lo escribe, y la otra muestra composición, instalación, runtime y secretos.
  Llevan arriba la URL donde están publicadas, para republicar sin perderla.

## De qué depende

- El código que describe. Una guía que se desactualiza es peor que no tenerla, y varias afirman
  qué test las verifica punta a punta.
- Los mapas dependen de que alguien los republique en la misma URL cuando cambia el flujo; nada
  automático lo comprueba.
- El `README.md` promete comportamientos concretos —que `-WhatIf` no escriba un byte, que
  `-Update` no pise lo editado a mano, que instalar sea aditivo— y esas promesas están
  verificadas en los casos de instalador de la suite.

## Dónde está

- `README.md` — en la raíz.
- `docs/instalacion.md`, `docs/contrato-hooks.md`, `docs/memoria.md`, `docs/secretos.md`,
  `docs/agregar-un-harness.md`
- `docs/adr/0001` a `0006` y `0008` — siete archivos, sin el 0007.
- `docs/mapa/recorrido-mensaje.html`, `docs/mapa/mapa-harness.html`
