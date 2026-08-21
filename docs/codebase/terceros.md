# terceros

## Qué es

Material bajado de repositorios públicos, guardado aparte de lo propio. **Nada de acá se
instala**: el instalador solo copia desde `comun/` y `harnesses/<id>/`.

Existe para que "de dónde salió esto" tenga siempre respuesta. Un origen sin registrar es peor
que no llevar registro: da falsa sensación de control.

Hoy hay un solo origen incorporado.

## Qué expone

- **`terceros.lock.json`** — la procedencia de todo, mantenida a mano. Por cada origen: repo,
  el commit exacto y completo (nunca una rama, porque las ramas se mueven), licencia, fecha,
  quién lo revisó, si se leyó entero, qué riesgos se detectaron, qué se tomó, **qué se dejó y
  por qué**, y en qué archivo propio se adaptó cada cosa.
- **`LEEME.md`** — las tres reglas operativas: esto no se instala, esto no se edita, y para
  usar algo se copia a lo propio con una nota de procedencia arriba que nombre el repo, el
  commit y la licencia.
- **`gentle-ai/`** — los cuatro archivos que se leyeron de ese proyecto, tal como estaban, más
  su licencia MIT y una lectura completa en `ORIGEN.md` que explica qué es el proyecto y por
  qué no se instaló su binario: es un configurador de agentes igual que este harness y los dos
  escribirían en el mismo `settings.json`.

## De qué depende

- Nada en tiempo de ejecución. Es material inerte: se lee, se decide y se copia a mano.
- Lo que sí depende de acá son dos agentes de `analisis` y, por herencia, el refutador de
  `desarrollo`: llevan arriba la nota de procedencia que apunta a este directorio.
- La disciplina de mantener el lockfile a mano. No hay nada que lo verifique automáticamente.

## Dónde está

- `terceros/terceros.lock.json`
- `terceros/LEEME.md`
- `terceros/gentle-ai/ORIGEN.md`, `LICENSE`, `review-refuter.md`, `review-risk.md`,
  `skill-resolver.md`, `_shared-SKILL.md`
- El fundamento está en `docs/adr/0005-terceros-separados-de-lo-propio.md`.
