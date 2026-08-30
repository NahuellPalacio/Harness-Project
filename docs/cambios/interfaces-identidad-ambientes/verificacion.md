# Verificación — Paso 4 del contrato: `interfaces`, `identity_and_access` y `environments`

**Estado:** cerrado · **Fecha:** 28-08-2026, lectura firmada el 30-08-2026 · **Versión:** 0.14.0

Este documento es lo que cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md):
el veredicto por escenario de quien verificó, que no es quien construyó. Los veredictos los emitió
`harness-spec-refuter` en dos pasadas: el 28-08-2026, corriendo la suite completa —658/658, dos
motores, sin asumir una corrida anterior— y leyendo el código real de `comun/bin/contexto-armar.py`,
`comun/schemas/project-context.schema.json` y `tests/casos/15_contexto_paso4.py`; y el 30-08-2026,
verificando la firma de [`lectura.md`](lectura.md) —`Leyó: Nahue Palacio`— contra el
`project-context.json` v1.1 real de un recorrido sobre `C:\Users\Asus\lecturas-0.14.0\reservas`
(`repo_revision d5ea7aea49c7869d02eb79cec7549a5355502c91`) y contra `src/api/*.ts` de ese repositorio.

**Resultado: 17 escenarios sostenidos, 1 leído (independiente), 0 contradichos, 0 sin sustento.**

**El cambio cierra.** E-18 pasó a `leído` con una lectura que cumple las cuatro condiciones de
[ADR-0009](../../adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md), incluida la
verificación de que el conflicto de `owning_component` (`src/api` vs `src-api`) que la lectura cita
está realmente en `gaps_and_conflicts.conflicts` del contrato, no inventado.

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | `schema_version: 1.0` no valida contra el schema v1.1 | sostenido | sí | `15_contexto_paso4.py::test_e01_...` |
| E-02 | El schema v1.1 sólo usa las seis palabras soportadas, en ninguna rama | sostenido | sí | `15_contexto_paso4.py::test_e02_...` |
| E-03 | Los tres bloques nuevos son `required`, tres casos por separado | sostenido | sí, los tres casos | `15_contexto_paso4.py::test_e03_...`, copia descartable del bin |
| E-04 | `interface_id` duplicado: se conserva la primera fila, se anota el conflicto | sostenido | sí | `15_contexto_paso4.py::test_e04_...` |
| E-05 | `type` fuera del enum no valida, sobre una fixture con interfaz real | sostenido | sí | `15_contexto_paso4.py::test_e05_...` |
| E-06 | Un OpenAPI commiteado resuelve `request/response_contract_ref` a su `source_id` | sostenido | sí | `15_contexto_paso4.py::test_e06_...` |
| E-07 | `owning_component` existente e inexistente, misma fixture, las dos mitades | sostenido | sí, las dos mitades | `15_contexto_paso4.py::test_e07_...` |
| E-08 | Sin `## Interfaces`, el bloque no se omite: viaja vacío y declarado | sostenido | sí | `15_contexto_paso4.py::test_e08_...` |
| E-09 | Ninguna propiedad del schema, en ninguna rama, es una credencial | sostenido | sí | `15_contexto_paso4.py::test_e09_...` |
| E-10 | Secretos en los tres bloques nuevos se detectan; el contrato real de este repo, limpio | sostenido | sí | `15_contexto_paso4.py::test_e10_...`, con control positivo |
| E-11 | `kind` normaliza por substring: los seis casos conocidos y `other` | sostenido | sí | `15_contexto_paso4.py::test_e11_...` |
| E-12 | Un ambiente `prd` fuerza `allowed_mutations: read-only`, con el conflicto anotado | sostenido | sí | `15_contexto_paso4.py::test_e12_...` |
| E-13 | `base_urls` sólo lleva URLs que estén en un archivo versionado | sostenido | sí, las dos mitades | `15_contexto_paso4.py::test_e13_...` |
| E-14 | `missing[]` declara exactamente dos bloques sin modelar, ninguno de los tres nuevos | sostenido | sí | `15_contexto_paso4.py::test_e14_...` |
| E-15 | `context_hash` cambia con `environments`, aislado de `docs_revision` | sostenido | sí, y reescrito | `15_contexto_paso4.py::test_e15_...` |
| E-16 | `[[wiki]]` o enlace roto en las secciones nuevas dispara hallazgo; uno real, no | sostenido | sí | `15_contexto_paso4.py::test_e16_...` |
| E-17 | El schema instalado declara `project-context/1.1` en el lockfile | sostenido | sí | `14-contexto-instalador.ps1`, grupo "el contrato del contexto" |
| E-18 | El contrato de un recorrido real no inventa interfaces, roles ni ambientes | leído, independiente | no consta | [`lectura.md`](lectura.md) — Nahue Palacio, 30-08-2026 |

📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** No aplica acá: los diecisiete
escenarios de la suite tienen su rojo visto, incluido E-15 —ver abajo, es el más elocuente del lote.

## E-15, el escenario que se reescribió durante la verificación

No es un `contradicho` — el escenario terminó `sostenido` — pero merece su propia sección porque el
camino hasta ahí encontró un defecto real en el propio test, y ADR-0006 pide que eso se diga, no que
se pula en silencio.

La primera versión de E-15 comparaba `meta.context_hash` entre dos corridas cuyo `proyecto.md`
difería sólo en `## Ambientes`. La verificación encontró que **esa comparación no prueba lo que dice
probar**: `meta.docs_revision` se calcula con `hash_de_fichas()`, que hashea todos los `.md` de
`docs/codebase/` —`proyecto.md` incluido—, así que reescribir `proyecto.md` mueve el hash general
sin que importe si `armar()` suma los tres bloques nuevos al documento antes o después de sellar
`context_hash`. Se confirmó rompiendo exactamente ese defecto —los tres bloques reemplazados por
objetos vacíos y fijos, desconectados de lo parseado— y el escenario, tal como estaba escrito,
siguió en verde.

```
Mutación: interfaces/identity_and_access/environments hardcodeados a bloques vacíos en armar()
Resultado esperado: E-15 en rojo
Resultado real: E-15 en verde (98/100 del archivo, sin marca en E-15)
```

El escenario se reescribió para mantener `proyecto.md` **byte a byte idéntico** entre las dos
corridas —`docs_revision` fijo, verificado por el propio test— y variar en cambio el contenido de un
archivo versionado *fuera* de `docs/codebase/`, de modo que la única causa posible de un hash
distinto sea el bloque `environments` ya calculado. Sobre la versión reescrita, la misma mutación
**sí** se ve: el script crashea con `IndexError` justo donde `environments.items` se asume no vacío.

**La decisión: se corrigió el test, no se aflojó el escenario.** La proposición de la spec —el hash
cambia con los tres bloques nuevos— sigue siendo la misma; lo que cambió es cómo se aísla la causa.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **Dos errores de prosa en la spec**, sin efecto en el código: la nota sobre `CONTRATOS` decía
   "los ocho nombres" cuando son seis (tres extensiones de `openapi` más tres de `swagger`; los
   otros dos elementos de `CONTRATOS` son de tipo `config`, no cuentan para esta regla), repetido en
   dos lugares. Corregido en la spec el mismo día.
2. **La tabla "Qué se construye" atribuía una edición a `tests/casos/13_contexto.py`** que ese
   archivo nunca necesitó: no hardcodea ningún literal de versión de schema, carga el schema real
   dinámicamente. La fila se sacó de la tabla.
3. **El defecto de E-15**, ya descripto arriba: es el hallazgo que justifica que la verificación
   exista. Un test que siempre pasa —incluso cuando la implementación está rota de la forma exacta
   que dice proteger— no verifica nada, y sin romperlo a propósito nadie lo hubiera notado.

## E-18, firmada el 30-08-2026

Hizo falta una corrida nueva: el `project-context.json` que existía cuando se escribió este
documento estaba en v1.0, de antes de este mismo cambio, sin los bloques `interfaces` /
`identity_and_access` / `environments`. Se actualizó el harness instalado en el banco de pruebas
(`install.ps1 -Update`), se corrió `dev-iniciador-code` de nuevo sobre `reservas`, y recién sobre
ese contrato v1.1 hubo algo real que leer. `mapa.html` y las fichas de módulo salieron idénticos —
sólo cambiaron `proyecto.md` y `project-context.json`, confirmado por `git status`.

Nada más quedó abierto por este cambio específico: la suite corre en dos motores, 658/658, y los
diecisiete escenarios deterministas están sostenidos.

## Lo que ningún test cubre y se mira con los ojos

**Que el contrato describa el proyecto que recorrió y no lo invente.** Es E-18, y es lo único de
esta spec que un test no puede alcanzar: el sujeto es una corrida real de `dev-iniciador-code`, y la
suite de este repositorio son tests deterministas y sin red.

Como referencia mientras se espera la lectura: `docs/codebase/proyecto.md` de este mismo repositorio
declara `## Interfaces` e `## Identidad y acceso` vacíos —con una nota de por qué no aplican, no una
tabla en blanco— y `## Ambientes` con dos entradas reales, `fabrica` y `proyecto-instalado`, ninguna
`prd`. El `project-context.json` regenerado coincide campo por campo con eso. No es la lectura —la
escribió quien construyó— pero es la evidencia que alguien que sí pueda firmar va a mirar primero.
