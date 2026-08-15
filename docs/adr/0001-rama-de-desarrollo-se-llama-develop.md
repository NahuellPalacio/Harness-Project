---
estado: aceptada
creado: 2026-08-05
---

# ADR-0001 — La rama de desarrollo se llama `develop`

## Contexto

El harness necesita poder verificar el nombre de la rama de desarrollo. Al ir a buscar la
norma, aparecieron **tres nombres distintos en documentación oficial vigente**:

| Fuente | Nombre |
|---|---|
| ES0901 v6.3, Anexo I §4 | `DEVELOP` / `MASTER`, en mayúsculas |
| ES0901 v6.3, Anexo I §7 | `'develop'` / `'master'`, en minúsculas |
| Guía de Procesos DGISIS v1.0 | `dev` — *"un primer push de código mínimo en la rama `dev`"* |

Las dos primeras están **en el mismo anexo del mismo documento**. La tercera es la que se usa
operativamente cuando se pide la creación del repositorio.

No hay forma de cumplir las tres. Y no verificar nada tampoco sirve: la convención de ramas
es una de las pocas reglas de ES0901 que un script puede comprobar de verdad.

## Decisión

**El default es `develop`, en minúsculas.**

Tres razones, en orden de peso:

1. **Es el nombre canónico de git-flow**, del que las tres variantes derivan. Elegirlo reduce
   el problema de "cuál de tres nombres" a "cuál de dos cajas", que es una discusión mucho
   más chica.
2. **Minúsculas porque las refs de git son sensibles a mayúsculas y el filesystem de Windows
   no.** Un repo con `DEVELOP` y `develop` produce colisiones de refs que se diagnostican
   muy mal, y todo el equipo trabaja en Windows.
3. `dev` es el más corto y el más ambiguo — se confunde con el nombre del ambiente, que en la
   propia Guía de Procesos aparece en las URLs (`residencias-dev.gcba.gob.ar`).

**Y tres reglas de implementación, que importan tanto como la elección:**

- Es **WARN, nunca bloqueo**. Nadie queda trabado por esto.
- El aviso **cita las tres variantes y este ADR**. Quien lo recibe tiene que poder ver que es
  un conflicto normativo real y no un capricho del harness.
- `harness.config.json` tiene la clave `ramaDesarrollo`. El proyecto cuyo referente de ASI
  pida otra cosa la cambia y listo.

## Consecuencias

**A favor:**
- El check existe, que es mejor que no tener ninguno por no poder elegir.
- Disentir es barato: una clave en un archivo de configuración del proyecto.
- El conflicto queda **documentado y visible** en vez de resuelto en silencio. Alguien que se
  cruce con la contradicción en ES0901 va a encontrar acá que ya la vimos.

**En contra:**
- Si DGISIS estandariza en `dev`, hay que cambiar el default y avisar a todos los proyectos
  instalados. Es un `-Update` y una línea del `CHANGELOG`, pero es trabajo.
- Un proyecto que use `dev` va a ver el aviso hasta que alguien configure la clave. Molesta,
  aunque no traba.

## Revisión

Se revisa **si ASI publica una versión de ES0901 que resuelva la contradicción interna del
Anexo I**, o si DGISIS emite una instrucción explícita sobre el nombre de la rama.

Mientras tanto, el harness no tiene autoridad para inventar la norma: solo elige un default
razonable, muestra el conflicto y deja disentir.
