# Bitácora por versión

Una nota por versión, con lo que se trabajó: qué se hizo, qué se decidió y por qué, qué se
rompió en el camino y **qué quedó abierto**.

## Por qué existe, si ya hay un CHANGELOG

Porque contestan preguntas distintas y las dos hacen falta.

| | Para quién | Qué contesta |
|---|---|---|
| `CHANGELOG.md` | Quien **instala o actualiza** | Qué cambió y qué significa para mí |
| `docs/versiones/` | Quien **sigue el trabajo** | Qué pasó acá, por qué está así, y dónde seguir |

El `CHANGELOG` mira hacia afuera y se escribe para no romperle nada a nadie. La bitácora mira
hacia adentro: guarda el razonamiento, los caminos que se probaron y se descartaron, y las
puntas sueltas.

📌 **La sección que justifica todo esto es "Dónde seguir".** Una conversación de trabajo se
compacta y se pierde el hilo: qué estábamos por hacer, qué habíamos decidido, qué faltaba
verificar. Eso no entra en un changelog —a quien actualiza no le importa— pero es exactamente
lo que hace falta para retomar.

## Cómo se escribe una

Al cerrar una versión, antes o justo después del commit. La plantilla es
[`_plantilla.md`](_plantilla.md); las secciones son fijas y ninguna se omite: si algo no
aplica, se escribe que no aplica. Una sección ausente se lee como olvido, no como vacío.

**Lo que se anota es lo que no se puede reconstruir después.** El diff está en git y el qué
cambió está en el `CHANGELOG`. Acá va lo que solo existía en la cabeza de quien lo hizo: por
qué se descartó la otra opción, qué se probó y no anduvo, qué quedó a medias y por qué.

**No inventar.** Igual que en el resto del repo. Si no te acordás de por qué se tomó una
decisión, escribí que no está registrado. Un motivo inventado se lee bien y nadie lo cuestiona.

## El índice

| Versión | Fecha | Qué trajo |
|---|---|---|
| [0.14.0](0.14.0.md) | 21-08-2026 | El primer recorrido del código y `docs/codebase/`; ADR-0008, lo externo nunca es requisito. **Sin cerrar: falta el veredicto** |
| [0.13.0](0.13.0.md) | 17-08-2026 | Los cuatro hooks, los cinco checks y la suite, de PowerShell a Python; el shim `.sh` que faltaba |
| [0.12.0](0.12.0.md) | 13-08-2026 | Esta bitácora, y el detector de secretos que bloqueaba su propia documentación |
| [0.11.0](0.11.0.md) | 13-08-2026 | `desarrollo` ya sabe: 8 skills, `dev-refutador` y la normativa destilada |
| [0.10.0](0.10.0.md) | 12-08-2026 | `desarrollo` deja de estar vacío: sus primeros cuatro checks |
| [0.9.0](0.9.0.md) | 12-08-2026 | Los dos silencios que quedaban en el `CLAUDE.md` |
| [0.8.0](0.8.0.md) | 12-08-2026 | La primera skill de `comun/`: `instalar-desde-github` |
| [0.7.0](0.7.0.md) | 11-08-2026 | Los dos harness conviven de verdad; instalar es aditivo |
| [0.6.0](0.6.0.md) | 11-08-2026 | La capa de memoria. El esqueleto queda terminado |
| [0.5.0](0.5.0.md) | 10-08-2026 | `analisis` deja de estar vacío, con verificación independiente |
| [0.4.0](0.4.0.md) | 10-08-2026 | La regla de secretos punta a punta |
| [0.3.0](0.3.0.md) | 06-08-2026 | `install.ps1`: el harness ya es instalable |
| [0.2.0](0.2.0.md) | 06-08-2026 | Infraestructura de hooks con sus tests |
| [0.1.0](0.1.0.md) | 05-08-2026 | Estructura inicial y las cuatro decisiones que la fundan |

⚠️ **Las notas de 0.1.0 a 0.6.0 se reconstruyeron** a partir del `CHANGELOG` y de los cuerpos
de los commits, que son detallados. Lo que ahí figura sale de esas dos fuentes; lo que no se
pudo reconstruir está marcado como tal, no completado.
