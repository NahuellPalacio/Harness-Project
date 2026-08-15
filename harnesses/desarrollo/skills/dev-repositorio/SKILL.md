---
name: dev-repositorio
description: Use when creating or structuring the Git repository of a GCBA/ASI project — laying out source/ and scripts/, writing README.md, CHANGELOG.md, UPGRADE.md or .gitignore, naming the develop and master branches, cutting a semantic version tag with -BETA, -RC or -HOTFIX, deciding which number to bump after a failed release candidate, assembling the software package for an entrega, or working out which manuals, scripts and documents have to ship with the code and through which channel each one goes.
---

# Repositorio, ramas, versiones y entrega

El repositorio no lo creás vos: "El sistema de control de versiones seleccionado por la ASI es
GIT" y "La ASI generará el repositorio del proyecto y otorgará los accesos en GIT al momento del
iniciar el proyecto" (ES0901 pág. 26). Todo lo de abajo es obligatorio "tanto para aplicaciones
nuevas como entregas de nuevas versiones de aplicaciones existentes" (ES0901 pág. 26).

## Qué va al repositorio y qué no

- **Todo el material entregable va a GIT** — "Todo el código fuente necesario para un proyecto,
  así como también para el esquema, sus migraciones, scripts y todo el material entregable para
  el proyecto, deberá estar presente en el repositorio GIT" (ES0901 pág. 26).
- **La documentación del proyecto NO va al repositorio** — funcionales y arquitectura "debe
  residir en el SharePoint de ASI" (ES0901 pág. 26). La pág. 7 manda esa misma documentación del
  proyecto a la herramienta colaborativa, sin recortar nada: **el documento no articula las dos
  disposiciones** y acá tampoco se las concilia (ver contradicción 5).
- **El código fuente es un entregable** y "debe ser impactado en el repositorio definido por la
  Agencia para tal fin" (ES0901 pág. 4).
- **La estructura de carpetas no la inventás**: "Clonar el repositorio para obtener la estructura
  de carpetas estándar" y "Realizar el commit de los archivos generados respetando la estructura
  de carpetas" (ES0901 pág. 28, pasos 3 y 4).
- **Acceso**: key SSH vinculada en el profile de GIT, o cliente GIT tipo UI con usuario y
  contraseña (ES0901 pág. 28). A los **60 días de inactividad el usuario se desactiva** y hay
  que pedir la reactivación a la mesa de ayuda de la Agencia (ES0901 pág. 28).

## La estructura del repositorio

**`source/`** — "debe estar contenido todo el código fuente de la aplicación y el archivo de
configuración de dependencias, el cuál debe listar las mismas especificando el **número de
versión exacta** para cada una de ellas. **No se aceptarán paquetes compilados como parte de la
entrega**" (ES0901 pág. 26). Ojo con la contradicción 3 sobre paquetes compilados.
El Anexo III nombra el archivo de dependencias para tres tecnologías (ES0901 pág. 38): Laravel PHP
→ `composer.json` **"en la raíz del proyecto"**; Node.js → `package.json`, sin indicar ubicación;
Java → `pom.xml` "donde se declare las dependencias y versiones a utilizar", tampoco con ubicación.
La raíz está exigida **sólo para `composer.json`**: que `package.json` y `pom.xml` vayan ahí es
convención de npm y Maven, no algo que el estándar diga. Y la página lista esas tres tecnologías
sin declarar que sean las únicas.
*El check `dev-dependencias` marca los rangos (`^`, `~`, `latest`): versión exacta, siempre.*

**`scripts/`** *(condicional: sólo si el despliegue es en máquinas virtuales)* — "Es obligatorio
contar en la carpeta scripts para el caso de utilizar despliegues en máquinas virtuales. Debe
contar con los comandos necesarios para efectuar un rollback en caso de que el deploy falle. Dicho
script deberá efectuar tanto rollback de código como de base de datos y configuración"
(ES0901 pág. 26). Además:

- **Evitar la pérdida de datos en el rollback es responsabilidad del desarrollador** — "Es
  responsabilidad del desarrollador mantener la lógica necesaria para evitar que se pierda
  información valiosa en este proceso" (ES0901 pág. 26).
- **Todo script necesita una verificación adicional** que valide si la ejecución fue exitosa
  (ES0901 pág. 27), y "debe ser utilizado el comando de mayor nivel de información (verbose)"
  (ES0901 pág. 27).
- Para versionar la estructura de la base de datos se usan los administradores de migración del
  framework, "evitando utilizar scripts" (ES0901 pág. 38), por el riesgo de la ejecución manual
  sobre bases productivas (ES0901 pág. 36).

**`.gitignore`** — "deberán incluirse los archivos de configuración y todos aquellos archivos
que no formen parte del proyecto y que por alguna razón existan en el directorio del mismo (Ej.:
archivos de sistema, configuración, archivos subidos por usuarios, etc.)" (ES0901 pág. 27).

**Configuración de entorno**: el YAML de variables **no es un requisito general del repositorio**,
es requisito de plataforma. Para implementar en OpenShift hay que "Poseer un archivo de
configuración YAML para definir todas las variables de entorno e informar la ruta del mismo en el
archivo README.md" (ES0901 pág. 38), y el mismo requisito se repite acotado a ambientes
virtualizados, en la misma página (ES0901 pág. 38). En los hechos alcanza casi siempre —OpenShift es la plataforma
on premise obligatoria (ES0901 pág. 38)—, pero eso es lectura, no lo que dice la viñeta.
Lo que sí es regla general es M2: las variables de entorno —bases de datos, servicios externos,
URLs, protocolos, paths— "deben estar en un archivo externo al código" (ES0901 pág. 14).
*El check `dev-infra-en-codigo` caza las IPs hardcodeadas; la norma exige referenciar por nombre
DNS "jamás por su dirección IP" (ES0901 pág. 9).*

## Los tres archivos de la raíz

- **`README.md`** — "En el directorio raíz del repositorio deberá encontrarse un archivo
  README.md el cual debe contener la información necesaria para realizar la primera
  implementación del aplicativo" (ES0901 pág. 26). Si desplegás en OpenShift o en ambientes
  virtualizados, sumale la ruta del YAML de variables de entorno (ES0901 pág. 38). Y si el
  despliegue "puede poner en riesgo la información almacenada
  en la base de datos del proyecto, se deberá realizar un backup de los datos en el README.md y
  en la solicitud del pedido del pasaje de ambiente" (ES0901 pág. 27).
- **`UPGRADE.md`** — obligatorio sumarle, **por cada nueva versión entregada**, "las
  instrucciones para llevar a cabo la instalación, indicando la fecha en la que se produjo dicha
  actualización" (ES0901 pág. 26). Ejemplos de lo que va ahí: ejecución de script de base de
  datos, agregar variables, montar volúmenes (ES0901 pág. 29).
- **`CHANGELOG.md`** — los cambios de cada versión **a nivel funcional** (ES0901 pág. 26),
  incluyendo: "Nro. de tickets de bugs/requerimientos/incidentes resueltos"; "Funcionalidades
  incluidas (si corresponde),"; "Sprint correspondiente (versión preliminar)" (ES0901 pág. 26).
  Los cambios de **cada tag** se documentan acá (ES0901 pág. 29).

## Ramas

- **Mínimo dos**: una de desarrollo y una principal (ES0901 pág. 27).
- La rama de desarrollo lleva "las entregas parciales y verificaciones implementadas en la
  herramienta con el fin de contar en forma proactiva un auto examen de calidad. Dicha rama es
  de **uso exclusivo del equipo que construye**" (ES0901 pág. 27). Representa "el estado activo
  del entorno de desarrollo (DEV)" e integra "nuevas funcionalidades, cambios o correcciones que
  aún no estén destinados a producción" (ES0901 pág. 28).
- **El pase a la rama principal es con tag** — "Una vez que se cuenta con la versión candidata,
  en condiciones de avanzar a otro ambiente, se actualiza a la rama MASTER con el TAG
  correspondiente" (ES0901 pág. 27).
- En la rama principal "se ejecutarán los mismos controles que en DEVELOP y se avanzará con el
  despliegue si los mismos son satisfactorios" (ES0901 pág. 27).
- **El nombre de las ramas está en contradicción en el propio estándar** (ver abajo). El harness
  tomó una decisión propia: el default es **`develop` en minúsculas**, según `docs/adr/0001` —
  eso es decisión del harness, **no** lectura de la norma. Es WARN y nunca bloquea, y se cambia
  con la clave `ramaDesarrollo` de `harness.config.json` si el referente de ASI del proyecto
  pide otra cosa.

## Tags y versiones

- **El tag sale de la rama principal** — "Al finalizar una versión del software, se debe generar
  un tag desde la rama 'master' en Git siguiendo el esquema de versionado semántico:
  **MAJOR.MINOR.PATCH**" (ES0901 pág. 28).
- **Sufijos** (ES0901 pág. 28):
  - `-BETA` — "Para pruebas funcionales, no funcionales o preparación de ambientes."
  - `-RC` — "Candidata a producción."
  - `-HOTFIX` — "Correcciones urgentes sobre una versión ya productiva."
- **BETA nunca llega a producción** — "Estas versiones solo podrán llegar al ambiente de QA,
  pero nunca a producción" (ES0901 pág. 29).
- **Una RC que no llega a producción se incrementa, no se reemplaza** — si "1.0.0-RC" no llega
  (por ejemplo, por vulnerabilidades de seguridad), "se debe crear una nueva versión
  incrementando su número, por ejemplo '1.0.1-RC'. Este proceso se repite hasta que una versión
  RC cumpla con los criterios para ser liberada en producción" (ES0901 pág. 29).
- **HOTFIX sale siempre de una versión ya productiva**, "Solo corrige errores o vulnerabilidades
  detectadas en una versión previa que no permite al ambiente productivo funcionar, sin agregar
  nuevas funcionalidades ni cambios mayores" (ES0901 pág. 29). En el ticket de despliegue "se
  deberá especificar el motivo por el cual se considera a la versión como un HOTFIX"
  (ES0901 pág. 29).
- **Ejemplo textual del estándar** (ES0901 pág. 29): si "2.4.0-RC" fue liberada en producción,
  el primer hotfix es 2.4.1-HOTFIX y el segundo 2.4.2-HOTFIX; para los sucesivos casos podría
  darse 2.5.0-BETA, 2.5.1-BETA, 2.5.2-RC, 2.5.3-HOTFIX.
- **Unicidad** — "Los números de versión nunca deben repetirse" y hay que "Asegurarse que todo
  tag sea único y numerado correlativamente" (ES0901 pág. 29).
- **Los tags disparan controles**: cada proyecto Git tiene Code Quality (Code Climate Engines),
  SAST, DAST (OWASP ZAP) y Dependency Scanning, y "Dichas revisiones se activan a partir de los
  commits y tags que se van generando" (ES0901 págs. 27-28). En Python, el Dependency Scanning
  **solo admite `requirements.txt`** (ES0901 pág. 28).

## El paquete de entrega

Por cada entrega acordada, el **Paquete de Software** incluye (ES0901 pág. 6):

- "Código fuente subido en el repositorio e implementado en DEV."
- Documentos de control de cambios.
- Cobertura de tests unitarios — **el umbral está en contradicción, ver abajo**.
- "Archivos de configuración de Varnish (definición y actualización)."
- "Plan de pruebas de funcionalidades core (.jmx)."
- Manual de Instalación y Manual de Operación.
- "Instalación de todos los componentes de software adicionales necesarios para el correcto
  funcionamiento de lo entregado."

Los demás entregables del proyecto son Documento Plan de Proyecto, Especificaciones, Documento
de Arquitectura (ES0901 pág. 6), Manual de Usuario, Material de Capacitación y Minutas e
Informes de avances (ES0901 pág. 7).

Y tres obligaciones más de §6.8 (ES0901 pág. 10). Sólo la primera está atada al pedido de pase a
Producción; las otras dos la página las enuncia sin momento procesal:

- **Matriz de dependencias**, al pedir el pase — "Al momento de solicitar el pase del sistema al
  entorno de Producción, se deberá informar qué bibliotecas externas utiliza la aplicación", con
  nombre, versión, sistema dependiente y servidores donde está instalada; la ASI cruza esa matriz
  con las vulnerabilidades publicadas (ES0901 pág. 10).
- **Licencias** — los componentes sujetos a licenciamiento "deberán ser entregados por el
  desarrollador conjuntamente con la documentación que acredite la legítima propiedad o derecho
  de uso de dichas licencias" (ES0901 pág. 10). La página no lo ata al pase a Producción.
- **Nada 'beta' entre los paquetes instalados** — "Bajo ningún concepto se aceptarán versiones
  'beta' de ningún paquete de software" (ES0901 pág. 10). No es un entregable: es una prohibición
  general sobre los paquetes de software a instalar, sin momento procesal asociado.

**Plazos y aceptación:** todos los entregables salvo el Paquete de Software tienen "un límite de
tiempo estipulado de 10 días hábiles", extensible previa solicitud justificada (ES0901 pág. 23).
Se acepta con "0% incidentes críticos y 0% incidentes mayores" y "0% incidentes de prioridad
urgente y 0% incidentes de prioridad alta" (ES0901 pág. 23). Y el incumplimiento de la regla de
sólo paquetes homologados "puede ocasionar el rechazo del entregable y la necesidad de retrabajo
a último momento" (ES0901 pág. 25).

## Lo que hay que ir a buscar al PDF

- **Las versiones homologadas del Anexo II (ES0901 págs. 30-37).** La conversión a texto dejó
  varias tablas con las columnas corridas —Framework Frontend (pág. 31), Biblioteca Java
  (pág. 33), Biblioteca Angular (pág. 34), LMS (pág. 35), DMS (pág. 36)— así que **acá no se
  publica ningún número de versión**: un valor mal leído se lee bien y es falso. Para fijar la
  versión de una herramienta, abrí el PDF. El check `dev-dependencias` compara contra la lista
  configurada en el harness, no contra esta skill.
- **La tabla "Entregable / Contenido" (ES0901 pág. 6).** Su texto extraído mezcla las columnas.
  Si la lista de entregables va a un pliego o a un acta, verificala contra la pág. 6 del PDF.
- **El circuito completo de gestión de cambios (fig. 1, ES0901 pág. 4).** Es una imagen sin capa
  de texto —va de Entrega a Repositorio GCABA, Integración Continua, controles y ambientes—: los
  rótulos exactos y el orden de las flechas se releen del PDF antes de citarlos.
- **El árbol completo de la estructura estándar de carpetas.** El documento nombra `source/` y
  `scripts` (ES0901 pág. 26) y manda a clonar el repositorio para obtener la estructura
  (ES0901 pág. 28), pero **no la publica**. Sale del repo que crea la ASI, no de acá ni por
  analogía.

## Contradicciones sin resolver

1. **Nombre de las ramas: mayúsculas vs. minúsculas.**
   - Pág. 27: "Los proyectos deberán contar como mínimo con una rama **DEVELOP** y una
     **MASTER**."
   - Pág. 28: "El desarrollo continuo debe realizarse en la rama **'develop'**" y "se debe
     generar un tag desde la rama **'master'**".
   - Están en el mismo anexo del mismo documento, y **git distingue mayúsculas de minúsculas**
     en los nombres de rama: no son la misma ref. El estándar no declara cuál es la canónica.
   - El harness eligió `develop` como default (`docs/adr/0001`), en WARN y configurable. Es una
     decisión del harness para poder verificar algo, no una lectura de la norma; el ADR registra
     además una tercera variante que circula en otra documentación vigente del GCBA.

2. **Umbral de cobertura: 80% inclusive vs. estrictamente mayor.**
   - Pág. 6 (Entregables · Paquete de Software): "Cobertura de test unitarios con **piso del
     80%**."
   - Pág. 24 (Condiciones de aceptación · revisión de código): "**Cobertura de código superior a
     80%**".
   - Difieren en el operador (≥80 vs. >80) **y en el objeto medido** (tests unitarios vs.
     código). El documento no reconcilia las dos cifras. Quien tenga que pasar las dos puertas
     va a necesitar superar el 80, pero eso es aritmética del caso, no lo que dice la pág. 6:
     si el número se pacta en un pliego, se pacta con las dos redacciones a la vista.

3. **Paquetes compilados: se rechazan en la entrega vs. se exigen pre-compilados.**
   - Pág. 26 (Anexo I · `source/`): "No se aceptarán paquetes compilados como parte de la
     entrega."
   - Pág. 10 (§6.8): los paquetes compilados "serán considerados parte de la aplicación debiendo
     suministrarse **pre-compilados e integrados en ella**".
   - El documento no declara si una regla acota a la otra (repositorio vs. instalación en los
     servidores) ni cuál prevalece.

4. **Assessment de seguridad del HOTFIX: antes o después de producción.**
   - Pág. 42 (Anexo V): "El assessment de seguridad es un control obligatorio que debe cumplirse
     **antes** de que una aplicación pase a ambientes superiores (HML y PRD)."
   - Pág. 29 (Anexo I · Hotfix): "a este tipo de versión se le realizará el assessment **a
     posteriori** del despliegue productivo. Dicho assessment se realizará en el ambiente de
     QA."
   - El Anexo V no contempla la excepción del hotfix ni el Anexo I remite al Anexo V.

5. **Destino de la documentación del proyecto: SharePoint de ASI vs. herramienta colaborativa.**
   - Pág. 26 (Anexo I): "Se exceptúa la documentación del proyecto (como ser los documentos
     funcionales o arquitectura), que debe **residir en el SharePoint de ASI**."
   - Pág. 7: "La documentación del proyecto se debe entregar en la **herramienta colaborativa del
     proyecto seleccionada**, con excepción del código fuente que se sube al repositorio."
   - Las dos alcanzan a "la documentación del proyecto". El documento no declara si la herramienta
     colaborativa seleccionada es el SharePoint de ASI, ni si una regla acota a la otra. Si el
     destino se pacta en un pliego o en un acta, se pacta con las dos redacciones a la vista.
