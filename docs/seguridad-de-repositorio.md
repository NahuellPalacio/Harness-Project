# Integridad de repositorio: investigar sin destruir la escena

Cuando se sospecha que a un repositorio le entraron, el comportamiento por defecto de un asistente
es el peor posible: **arreglar**. El commit revertido, el archivo sospechoso borrado, la credencial
rotada y el `force-push` se llevan puesta la única evidencia de qué pasó.

```
preservar
antes de
cambiar
```

Eso es todo lo que esta capacidad instala, y por qué existe.

## No es una regla

Es una **capacidad transversal**, como el Bloque 4 y la gestión de ambientes de base de datos. No
tiene señal de aplicabilidad, no entra en la matriz de ES0901 ni en la de ES0902, y no se declara en
el registro de controles.

Puede **producir evidencia** para reglas de seguridad —`O1`, `O2`, `Vu2`, `Vu7` a `Vu10`, el flujo de
evaluación, la gestión de vulnerabilidades—. No es una de ellas.

🔴 **Que una revisión no encuentre nada no es una aprobación de seguridad.** El resultado no lleva
ningún estado oficial de ES0902 y no mueve el que resuelve `evaluacion`. Son dos preguntas
distintas: *"¿alguien tocó esto?"* y *"¿está aprobado?"*.

Y no crea ningún agente ni ninguna skill. Los dueños son `dev-security` y las tres que ya están
instaladas. Si algún día una capacidad real demuestra que no alcanzan, eso se rutea con el estado
que ya existe —`SPECIALIZED_SKILL_GAP`— y se decide aparte.

## Tres modos, y uno invierte los defaults

```
NORMAL                el flujo de siempre
SECURITY_ASSESSMENT   analisis interno y preparacion de evidencia de ES0902
SECURITY_INCIDENT     se sospecha compromiso
```

En `SECURITY_INCIDENT` ninguna de estas seis corre automáticamente:

```
remediacion de codigo           borrado de archivos
rotacion de credenciales        actualizacion de dependencias
reescritura de historia         limpieza de artefactos sospechosos
```

🔴 **Recomendar sigue permitido, y es lo único que queda permitido.** Esa diferencia es toda la
capacidad: un harness que recomienda revertir un commit es útil, y uno que lo revierte solo destruyó
la evidencia de qué se revirtió. Ejecutar exige autorización explícita citada, la evidencia ya
preservada, y la compuerta de riesgo de tools que ya existe.

## La rama actual no es una línea de base

Comparar contra la rama por defecto cuando el problema puede ser que alguien escribió en ella es
comparar el repositorio consigo mismo.

```
APPROVED_RELEASE   DEPLOYED_RELEASE   SECURITY_APPROVED_RELEASE
HUMAN_CONFIRMED    OTHER_AUTHORITATIVE
```

🔴 `main`, `master`, `HEAD~1`, el último tag y *"el commit anterior al reporte"* **no son fuentes:
son ubicaciones**. Adentro del módulo no hay ningún nombre de rama, y por eso no puede elegir la más
cómoda. Sin las cinco cosas del contrato —repositorio, ref, commit, fuente de la lista y evidencia—:
`TRUSTED_BASELINE_UNRESOLVED`, y el análisis sigue en modo degradado con la limitación escrita en el
resultado.

📌 `HUMAN_CONFIRMED` exige además **quién firmó**. Es la fuente que más fácil se escribe sola.

Y la línea de base es evidencia inmutable de esa revisión: cambiarla no la actualiza, **crea otra**.
El id del contexto se deriva del repositorio, del commit y de la fuente.

## El inventario es determinista, o no sirve

La misma línea de base y la misma evidencia producen el mismo inventario, siempre, y el orden de
entrada no lo cambia. Sin eso, dos corridas de la misma investigación se contradicen y ninguna se
puede citar.

```
COMMITS              FILES_ADDED         FILES_MODIFIED      FILES_DELETED
DEPENDENCY_CHANGES   LOCKFILE_CHANGES    CICD_CHANGES        BUILD_CHANGES
AUTH_CHANGES         NETWORK_DESTINATIONS                    BINARY_ARTIFACTS
```

🔴 **La clase de un archivo la declara la evidencia normalizada**, no la deduce el módulo del nombre
del archivo: deducir que algo es un pipeline porque está en una carpeta que se llama así es la misma
trampa que `tmp` en un path. Un archivo sin clase queda `UNCLASSIFIED_CHANGE` y deja la revisión
`REVIEW_INCOMPLETE`.

## Un indicador débil no es malware

```
eval    exec    Base64    un comando de shell    un dominio nuevo    una dependencia nueva
```

Los seis aparecen en código legítimo todos los días.

```
indicador debil solo o acumulado  ->  confianza LOW, SUSPICIOUS_BEHAVIOR_DETECTED
evidencia DIRECTA citada + confianza alta  ->  recien ahi, confirmado
```

Acumular seis coincidencias que aparecen en cualquier repositorio no produce una séptima cosa:
produce seis coincidencias.

🔴 **El harness no reporta intención.** Dice qué cambió, con qué evidencia y con cuánta confianza. La
metadata de identidad es evidencia, no prueba: nadie es declarado malicioso por su nombre ni por la
hora de su commit.

## Confianza y severidad son dos ejes

```
confianza   LOW / MEDIUM / HIGH   cuanto sostiene la evidencia
severidad   la de ES0902          cuanto pesa, y la firma el mapeo autoritativo
```

La severidad sale de `evaluacion` con la **misma** compuerta que el umbral de G2: el mapeo tiene que
declararse autoritativo y traer evidencia, porque decidir que un `medium` de una herramienta es el
`LOW` del estándar lo tiene que firmar alguien. Sin eso: `SECURITY_SEVERITY_UNRESOLVED`. Esta
capacidad **no declara ningún valor de severidad propio**.

Y no se derivan una de la otra en ninguna dirección: mezclarlas produce las dos formas del error, lo
grave con poca evidencia tratado como certeza y lo cierto pero menor tratado como crisis.

## El secreto no sale en claro de ningún lado

```
se redacta      el valor nunca viaja
se huella       para poder correlacionar sin exponer
se ubica        archivo y posicion, que es lo que sirve para arreglarlo
```

Y el alcance es todo lo que sale: el hallazgo, el reporte, los avisos y **la contabilidad del Bloque
4**, que mide tiempo, tokens y costo del análisis y no guarda ni un secreto, ni un payload, ni el
cuerpo de un script.

## Estático primero

Lo dinámico exige las cuatro: ambiente aislado, autorización explícita, contención de red y
evidencia preservada, y además pasa por la compuerta de riesgo de tools **que ya existe**. Sin
ambiente aislado: `DYNAMIC_ANALYSIS_ENVIRONMENT_UNAVAILABLE`. Un binario sospechoso no se ejecuta
automáticamente, y una tool que ejecute código sospechoso en el host no puede nacer de bajo riesgo.

📌 No hay una compuerta propia: tener dos es tener una que un día dice que sí.

## Investigar y remediar no son el mismo paso

La investigación es de sólo lectura. La remediación aprobada es **otra unidad de trabajo** que
conserva el enlace a los hallazgos que la originaron, y el registro del incidente no se borra cuando
termina. Mutar y averiguar en el mismo paso implícito es cómo se pierde la respuesta a *"qué había
antes"*.

La compuerta humana —`HUMAN_SECURITY_REVIEW_REQUIRED`— es el default en las siete: comportamiento
confirmado, sospecha de confianza alta, propuesta de remediación, rotación de credenciales,
ejecución dinámica, línea de base en disputa y evidencia contradictoria.

## El núcleo no sabe de proveedores

Los adaptadores traducen la forma de GitLab y de GitHub a una evidencia normalizada, y ningún campo
propio de un proveedor llega a un hallazgo. El día que entre el tercero, lo que no puede pasar es
tener que tocar el núcleo — y el núcleo es lo que decide si algo es sospechoso.
