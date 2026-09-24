"""El reporte de seguridad: del libro al tablero, en una sola direccion.

    productores  ->  security-ledger.ndjson  ->  security-summary.json  ->  .md y .html

Presenta lo que el harness ya produjo. No corre checks, no decide el resultado de ninguna
regla y no aprueba nada: copia resultados que salieron de `orquestacion/` y los ordena para
que una persona los lea en quince segundos.

Cuatro reglas que valen para todo lo que cuelga de aca:

    lo que no se evaluo NO es PASS      una regla sin evento es NOT_EVALUATED
    un check NO le pone nota a una regla  solo un RULE_EVALUATION de esa regla la define
    no hay puntaje                       estado, cobertura, hallazgos y bloqueos, separados
    el renderizador NO calcula            md y html leen el resumen y nada mas

🔴 **Este paquete no importa nada de `controles/`.** `controles/` no se instala en los
proyectos, y un import de ahi rompe el reporte justo donde tiene que correr. Tampoco importa
`contabilidad.agregacion` ni `contabilidad.costos`, y nunca escribe bajo
`.claude/runtime/accounting/`: el Bloque 4 se referencia leyendo su `summary.json`, no se
recalcula ni se toca.

🔴 **No hay cliente de modelo ni red.** El reporte es determinista por construccion: la misma
foto del libro da el mismo resumen byte a byte.

🔴 **La revision interna del harness no es aprobacion oficial de GCBA/DGSEI.** El tablero lo
dice cada vez que no hay evidencia externa, y ningun estado interno se traduce en aprobacion.
"""
