# El reporte de seguridad: cómo se lee

Qué dice el tablero de seguridad de una tarea, de dónde sale cada número, y —sobre todo— qué
**no** dice.

🔴 **La revisión interna del harness no es aprobación oficial de GCBA/DGSEI.** Ningún estado del
tablero la reemplaza. Mientras no haya evidencia externa de la aprobación, el pie del reporte lo
dice.

## Cómo se genera

```powershell
python .claude\harness\bin\desarrollo\dev-harness.py seguridad GCBA-1234 --conocimiento --resumen --reporte
```

- `--conocimiento` suma al libro el estado de ES0902 que dejó `dev-harness.py fuentes` en
  `.claude\harness.fuentes.json`.
- `--resumen` escribe `security-summary.json`.
- `--reporte` escribe además `security-status.md` y `security-status.html`.
- Sin ninguno, muestra el estado por pantalla y no escribe nada.

Todo queda en `.claude\runtime\security\<tarea>\`:

```
security-ledger.ndjson   el libro: lo que pasó, en orden, sin borrar nada   la fuente
security-summary.json    el resumen, calculado del libro                     determinista
security-status.md       el reporte en texto
security-status.html     el tablero; el PDF sale de imprimir esta página
```

El md y el html se generan del resumen y de nada más. Si un número del tablero te parece raro,
está en `security-summary.json` en la ruta que dice el atributo `data-field` del html.

🔴 **Un libro vacío es lo normal hoy.** Nada del harness corre los checks contra un proyecto
real todavía: los eventos los van a escribir los productores cuando exista el ejecutor. Por eso
un tablero recién generado casi siempre dice `BLOCKED` o `REVIEW_INCOMPLETE`, y es verdad.

## La página 1, en quince segundos

Cuatro tarjetas, siempre:

| Tarjeta | Qué contesta |
|---|---|
| Estado de seguridad del sistema | ¿Se puede avanzar? |
| Condiciones de bloqueo | ¿Qué lo impide, y cuántas son? |
| Cobertura normativa | ¿Cuánto de lo aplicable se miró, y cuánto quedó resuelto? |
| Aprobación oficial | ¿Hay aprobación de DGSEI, o solo revisión interna? |

### El estado del sistema

Se decide en este orden, y gana el primero que se cumpla:

| Estado | Cuándo |
|---|---|
| `BLOCKED` | El conocimiento de ES0902 no está verificado, o falta; o hay una revisión de incidente sin línea de base confiable |
| `REVIEW_INCOMPLETE` | Hay reglas aplicables sin evaluar o sin resolver, evidencia necesaria sin verificar, o la revisión de integridad quedó incompleta |
| `ACTION_REQUIRED` | Hay algo que corregir: una regla en `FAIL`, un hallazgo crítico abierto, un hallazgo que su productor marcó bloqueante, integridad sospechosa o confirmada, o una reevaluación pedida |
| `READY_FOR_SECURITY_REVIEW` | Ninguna de las anteriores |

Una regla en `FAIL` junto con otra sin evaluar da `REVIEW_INCOMPLETE`, no `ACTION_REQUIRED`. El
`FAIL` no se esconde por eso: está en la lista de bloqueos y en la grilla.

`READY_FOR_SECURITY_REVIEW` quiere decir "lista para pedir la revisión de seguridad". No es una
aprobación.

### Por qué casi seguro dice `BLOCKED`

ES0902 todavía no tiene hash aceptado en `source-registry.json`, así que su frescura da
`FRESHNESS_UNVERIFIED`. Con el conocimiento sin verificar el harness no se trata a sí mismo como
al día, y el tablero lo dice. No es un defecto del reporte: es el pendiente de aceptar el hash.

### La cobertura son dos números

```
aplicables                   = PASS + FAIL + UNRESOLVED + NOT_EVALUATED
cobertura de la evaluación   = PASS + FAIL + UNRESOLVED   sobre aplicables
resolución de la evidencia   = PASS + FAIL                sobre aplicables
```

Una regla `NOT_APPLICABLE` no cuenta. Una regla sin evaluar sí cuenta, en el denominador. Si
ninguna regla aplica, los dos dicen `N/D`: no hay de qué sacar un porcentaje, y `100%` sería
mentir.

🔴 **No hay puntaje.** Ni "87/100" ni "riesgo bajo". Un número único promedia una falla crítica
con veinte reglas en verde y la esconde. Estado, cobertura, hallazgos y bloqueos se leen por
separado.

## La grilla de ES0902

Las 21 reglas, en el orden del estándar. Cada casilla dice uno de cinco valores:

| Valor | Qué quiere decir |
|---|---|
| `PASS` | La regla se evaluó y cumple |
| `FAIL` | Se evaluó y no cumple. Bloquea |
| `UNRESOLVED` | Se evaluó y no se pudo concluir, o tiene una excepción (`OVERRIDDEN`) |
| `NOT_APPLICABLE` | No aplica a esto |
| `NOT_EVALUATED` | No hay ninguna evaluación de esa regla en el libro |

Dos cosas que conviene saber:

- **Una excepción autorizada sale como `UNRESOLVED`.** El tablero no tiene dónde mostrarla y no
  la convierte en `PASS`. En la tabla de cumplimiento normativo, la columna "Resultado del motor"
  conserva `OVERRIDDEN`.
- **Un check en `PASS` no pone ninguna regla en `PASS`.** C3 y Ve1 comparten controles; que el
  control pase no dice nada del resultado de ninguna de las dos. Solo la evaluación de la regla
  lo define.

Los ocho dominios del reporte (Gobierno, Identidad y sesión, etcétera) agrupan reglas para
leerlas. No son reglas nuevas ni cambian ningún resultado.

## La evaluación y la aprobación

Son dos estados distintos y ninguno se deduce del otro.

- **Estado de la evaluación**: en qué punto del flujo de ES0902 está la evaluación de seguridad.
  `G2_THRESHOLD_SATISFIED` quiere decir que el umbral de vulnerabilidades de G2 da, nada más.
  `REASSESSMENT_REQUIRED` suma un bloqueo.
- **Aprobación oficial**: sale de la evidencia de C2. Solo es `EXTERNAL_APPROVAL_EVIDENCED` si la
  aprobación es de una autoridad externa, en QA, y del mismo release que se está evaluando.
  `EXTERNAL_APPROVAL_STALE` es una aprobación que valió y ya no vale: la de otro release, o la que
  C2 da por cambiada o a reevaluar. Una que nunca valió —de un productor interno, o emitida en
  otro ambiente que QA— es `UNRESOLVED`.

## Los hallazgos

La severidad (`CRITICAL` … `INFORMATIONAL`) y la confianza van en columnas separadas: un hallazgo
crítico con confianza baja es eso, no un hallazgo "medio". Los totales por severidad cuentan los
hallazgos vigentes; uno resuelto sigue en el detalle con su estado `RESOLVED`. Uno que se
resolvió y volvió a abrirse figura como `REOPENED`.

Un hallazgo `HIGH` o menor no bloquea, salvo que quien lo produjo lo haya marcado bloqueante.

## La integridad del repositorio

`NO_SUSPICIOUS_INDICATORS_DETECTED` quiere decir que la revisión no encontró indicadores. Es el
resultado de lo que se revisó, no una garantía sobre el repositorio. Si no hay revisión de
integridad en el libro, el panel dice `NOT_EVALUATED` y no cambia el estado del sistema: la
integridad es una capacidad del harness, no una regla.

## La evidencia

Cinco contadores —verificada, faltante, en conflicto, pruebas inseguras salteadas y sin
resolver— que cuentan el último estado de cada evidencia. "Prueba insegura salteada" es un check
que no corrió su prueba porque correrla era riesgoso: la evidencia que iba a dar no existe.

## La tarjeta de ejecución

Si la tarea tiene contabilidad del Bloque 4 (`.claude\runtime\accounting\<tarea>\summary.json`),
el reporte muestra sus tiempos, tokens y costos copiados tal cual. No los recalcula ni escribe
nada en `accounting\`. Si no hay contabilidad, la tarjeta no aparece.

## Cómo saber qué foto estás leyendo

Cada reporte trae un `reportId` y una `snapshotFingerprint`: la huella de todo lo que se usó para
calcularlo, que es el libro, la matriz de ES0902, los dominios del reporte y la contabilidad del
Bloque 4 si la hay. Las mismas entradas dan siempre el mismo resumen, byte a byte, y la misma
huella. Dos reportes con huellas distintas salieron de entradas distintas.

La hora que figura como "generado" es la del último evento del libro, no la de cuando corriste
el comando.
