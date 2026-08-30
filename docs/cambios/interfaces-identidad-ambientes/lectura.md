# Lectura de E-18 — `interfaces-identidad-ambientes`

**Quién puede firmar:** cualquiera **menos quien construyó**. Es la misma regla del refutador y por
el mismo motivo: para quien construyó, cada decisión tuvo una razón en su momento.

**Qué es esto:** la vía de verificación que [ADR-0009](../../adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md)
define para los escenarios cuyo sujeto es una corrida de un agente con modelo. El filtro mecánico
de `base_urls` ya lo sostiene E-13 de la suite; esta lectura mira la otra mitad — si el agente
dedujo una interfaz, un rol o un ambiente que ningún archivo del proyecto respalda.

**Qué NO es:** una prueba. Un `leído` cierra un cambio y vale menos que un `sostenido`.

## Cómo se llena

1. **Correr `dev-iniciador-code`** sobre un repositorio real, con el schema del paso 4 ya
   instalado.
2. **Abrir el `project-context.json` que dejó** y contrastar `interfaces`, `identity_and_access` y
   `environments` contra lo que hay de verdad en el repositorio recorrido.
3. **Escribir en `Observado` qué se vio**, no si estaba bien.
4. **Firmar arriba**, con fecha y nombre.

---

**Leyó:** Nahue Palacio · **Fecha:** 30-08-2026 · **Corrida sobre:** `C:\Users\Asus\lecturas-0.14.0\reservas`

---

## E-18 — El contrato de un recorrido real no inventa interfaces, roles ni ambientes

**Observado:** Las interfaces (`reservas-alta`, `reservas-consulta`, `espacios-listado`) coinciden
con las rutas reales de `src/api/main.ts`, y el conflicto de `owning_component` (`src/api` vs
`src-api`) quedó declarado, no inventado. `Identidad y acceso` y `Ambientes` salieron vacíos con su
motivo explícito: no hay mecanismo de auth en el código hoy, y no hay ambiente propio versionado
más allá del proveedor de pagos. Los tres bloques quedaron bien separados entre sí — ninguno
mezcla información del otro. `Identidad y acceso` es el que más información real le falta al
proyecto todavía; eso queda para documentar después, y no es un defecto del contrato: el hueco se
declaró en vez de completarse con una inferencia.
