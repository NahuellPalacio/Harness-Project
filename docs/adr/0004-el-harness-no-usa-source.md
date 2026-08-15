---
estado: aceptada
creado: 2026-08-05
---

# ADR-0004 — El harness no usa la estructura `source/` de ES0901

## Contexto

ES0901 v6.3, Anexo I, fija la estructura obligatoria de un repositorio del organismo:

> *"En la carpeta `source/` debe estar contenido todo el código fuente de la aplicación y el
> archivo de configuración de dependencias, el cuál debe listar las mismas especificando el
> número de versión exacta para cada una de ellas."*

Este repositorio no la respeta: el código está en `comun/`, `harnesses/` y `scripts/`, no en
`source/`.

Eso plantea un problema de autoridad. Un harness cuyo trabajo es verificar que otros cumplan
ES0901 no puede incumplirlo sin decir nada.

## Decisión

**El harness no adopta `source/`, y lo deja escrito acá.**

El fundamento: ES0901 gobierna **software de aplicación que se homologa ante ASI** — lo que
atraviesa el circuito DEV → QA → HML → PRD, recibe assessment de seguridad y se despliega en
la infraestructura del organismo. Este repositorio es **tooling interno de escritorio**: no
se despliega, no expone servicios, no tiene ambientes y nunca va a pasar por homologación.
Aplicarle la estructura de una aplicación desplegable agrega ceremonia sin agregar garantía.

**Pero sí se cumple todo lo que es gratis y sirve igual:**

| Exigencia de ES0901 | Estado |
|---|---|
| `README.md` en la raíz con lo necesario para la primera instalación | ✅ |
| `CHANGELOG.md` a nivel funcional | ✅ |
| `UPGRADE.md` con las instrucciones de migración entre versiones | ✅ |
| `.gitignore` con lo que no forma parte del proyecto | ✅ |
| `scripts/` con capacidad de rollback | ✅ — acá el rollback es restaurar el backup del proyecto |
| Versionado semántico `MAJOR.MINOR.PATCH` | ✅ — `VERSION` |
| Rama `develop` | ✅ — ver [ADR-0001](0001-rama-de-desarrollo-se-llama-develop.md) |
| Carpeta `source/` | ❌ — **este ADR** |
| Endpoints `/health/liveness` y `/health/readiness` | ❌ — no aplica, no es un servicio |
| Cobertura de tests ≥ 80% | ⚠️ — hay tests, sin umbral formal medido |

## Consecuencias

**A favor:**
- La estructura del repo es la que el problema pide: `comun/` versus `harnesses/<id>/` es la
  distinción central del diseño, y meterla adentro de `source/` la escondería.
- **Se cumple la parte de ES0901 que aporta valor real** — que alguien pueda instalar,
  actualizar y revertir leyendo el repo — sin la parte que solo aplica a aplicaciones.
- El desvío está documentado, fechado y con argumento. Esa es exactamente la conducta que el
  harness le va a pedir a los demás cuando avise sobre una norma.

**En contra:**
- Un revisor de ASI que audite el repo por checklist va a marcar la falta de `source/`. La
  respuesta es este archivo, pero hay que darla.
- Si en algún momento el harness se distribuyera como paquete formal del organismo, habría
  que reestructurar.

## La regla general que deja

📌 **Un harness que ignora una norma en silencio no tiene autoridad para exigirla.**

Desviarse de un estándar es legítimo cuando el estándar no aplica. Lo que no es legítimo es
hacerlo sin dejar el argumento por escrito, porque entonces no es una decisión: es un
descuido que todavía nadie encontró.

## Revisión

Se revisa si este repositorio deja de ser tooling de escritorio — por ejemplo, si se
despliega como servicio o si pasa a ser un entregable formal ante ASI.
