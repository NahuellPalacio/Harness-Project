---
name: dev-ambientes
description: Use when planning or executing an environment promotion (DESA/DEV → QA → HML → PRD), preparing a delivery package for the ASI, estimating how far a build is from production, or working out which approvals, informes and evidence a change needs — including categorizing a change as menor or regular, assembling the FUR and its mandatory entregables, requesting the DEV environment, database, S3 bucket, repository or OpenID credentials, and knowing who signs off at each gate.
---

# Pases de ambiente y control de cambios

Dos normas gobiernan esto y se leen juntas: **PC0901** dice quién aprueba, qué evidencia hace falta y en qué
orden; la **Guía de Procesos de DGISIS** dice cómo se pide cada ambiente y cada recurso. Cada regla lleva
documento y página del PDF para poder verificarla. El check `dev-infra-en-codigo` ya cubre mecánicamente la
infraestructura declarada en el repo.

## 1. Primero categorizá el cambio — define todo lo demás

- **Cambio Menor**: cambio sobre software preexistente en Testing, Homologación y Producción, sin impacto de riesgo
  potencial en el ambiente (PC0901 pág. 4). Ejemplos de la norma: logos, labels, información estática.
- **Las ocho condiciones del Cambio Menor son conjuntivas** (PC0901 pág. 4): no afecta datos · no afecta el
  esquema de seguridad · no requiere cambios de infraestructura · no afecta la arquitectura · no se relaciona
  con aplicación o software crítico del GCABA · no afecta la funcionalidad · no afecta a otras aplicaciones ·
  ante implementación no satisfactoria, riesgos y resolución de impacto menor.
- **Basta incumplir una y pasa a Cambio Regular**, que se define por exclusión (PC0901 pág. 4).
- **Regular Caso 1**: aplicación o producto nuevo provisto por un Organismo (PC0901 pág. 5).
  **Regular Caso 2**: versión nueva o cambio evolutivo de una aplicación que ya está en PRD (PC0901 pág. 8).
- 🔴 **Tu categorización no es final.** El Líder Técnico evalúa la solicitud y determina si es correcta o si
  corresponde tratarla como Caso 2 (PC0901 pág. 10). No armes el cronograma como si ya estuviera aceptada.

## 2. Qué entregás según el caso

| Caso | Documentación mínima y obligatoria |
|---|---|
| **Regular 1** | FUR (o equivalente) a partir de comunicación oficial al Director Ejecutivo de la ASI, con: a. Manual de Instalación · b. Documento de Arquitectura de la Aplicación · c. Documento de Alcance Funcional · d. Definición de los Requerimientos Funcionales y no Funcionales (PC0901 págs. 5-6) |
| **Regular 2** | FUR **condicional**: el Líder Técnico evalúa el impacto y concluye si hace falta. Con: a. Instructivo de Instalación de la Versión · b. toda la documentación del Estándar de Desarrollo actualizada con los cambios · c. registro de los requerimientos en la herramienta de seguimiento provista por la ASI (PC0901 pág. 8) |
| **Menor** | a. Instructivo de Implementación del Cambio · b. registro del cambio en la herramienta de seguimiento provista por la ASI (PC0901 pág. 10) |

- **El registro tiene granularidad exigida**: los cambios deben identificarse "con un nivel de granularidad
  tal, que permitan entender, verificar y generar la trazabilidad" (PC0901 págs. 8 y 10). Un ticket que dice
  "mejoras varias" no cumple.
- En Caso 1, **los demás entregables del Estándar de Desarrollo siguen siendo exigibles** durante la
  ejecución del proceso, no sólo los cuatro de entrada (PC0901 pág. 6).
- 🔴 **La ASI puede rechazar la documentación** por falta de completitud o de detalle, y puede pedir
  replanificar las fechas comprometidas (PC0901 págs. 6, 8 y 10).
- **El repositorio es canal de entrega, no reemplaza la entrega formal** (PC0901 pág. 6); lo solicita el
  Líder Técnico. En Caso 2 y en Menor se reutiliza el ya creado, y hay que avisarle al Líder Técnico y al
  Coordinador del Cambio que hay algo nuevo (PC0901 págs. 8 y 10).

## 3. La cadena de pases: quién pide, quién instala, qué la desbloquea

| Ambiente | Lo gestiona / pide (PC0901) | Lo instala | No se entra sin |
|---|---|---|---|
| DESA | Líder Técnico gestiona creación y accesos (pág. 6) | Soporte de Desarrollo (pág. 5) | — |
| QA | Líder Técnico solicita la instalación (págs. 6 y 8) | Soporte de Desarrollo (pág. 5) | Entregables verificados y validados por el Líder Técnico |
| HML | Líder Técnico o quien designe (págs. 7 y 9) | Infraestructura (pág. 5) | Homologación en QA |
| PRD | Líder Técnico o quien designe (págs. 7 y 10) | Infraestructura (pág. 5) | Resultado favorable de las pruebas de aceptación |

- **DESA es verificación obligatoria previa a la entrega, en los tres carriles**: el Desarrollador debe verificar
  en la infraestructura de la ASI que el paquete funciona antes de entregar (PC0901 págs. 6, 8 y 11 — sí, también
  en el Cambio Menor).
- **Antes de habilitar pruebas en QA**, el Líder Técnico o quien designe verifica la instalación, parametriza
  el aplicativo y avisa a Calidad (PC0901 págs. 6 y 9). Sólo informa disponibilidad del ambiente si el manual
  (Caso 1) o el instructivo de instalación de la versión (Caso 2) es "claro y consistente con las tareas a
  realizar" y la aplicación quedó correctamente instalada, configurada y parametrizada (PC0901 págs. 6 y 9).
- **Instalación fallida**: el Coordinador de Instalación avisa al Líder Técnico para las correcciones (PC0901 págs. 6 y 9).
- **En HML hay que verificar instalación y parametrización** de modo que puedan realizarse las pruebas de
  aceptación (PC0901 págs. 7 y 9), e informar el avance al Coordinador del Cambio.
- **En Cambio Menor el pase a HML depende de que la instalación en QA resulte exitosa**: el Líder Técnico
  verifica el cambio y recién ahí lo gestiona para HML (PC0901 pág. 11).

## 4. Evidencia: dos informes en serie, no en paralelo

- **Calidad emite el "Informe de Resultados de Pruebas en QA"** (PC0901 págs. 6-7 y 9). Si no resulta exitoso
  se reportan incidentes, se especifican los bugs con su criticidad y se informa el estado, en ciclo iterativo
  hasta la aprobación definitiva.
- 🔴 **Seguridad arranca recién una vez aprobado el informe de calidad**, y emite el "Informe de Resultados de
  Assessment de la Aplicación en QA" (PC0901 págs. 7 y 9). Son dos ciclos encadenados: no los planifiques solapados.
- **Las correcciones de seguridad abarcan aplicación e infraestructura** y el ciclo se repite "desde donde se
  requiera" (PC0901 págs. 7 y 9): puede mandarte atrás de la etapa de calidad.
- **"Homologada en QA" tiene definición exacta: los dos informes aprobados** (PC0901 págs. 7 y 9). Sin eso no hay HML.
- **En Caso 2 son exigibles pruebas sobre los cambios _y_ pruebas de regresión** (PC0901 pág. 9). El Caso 1 no las nombra.
- **Aceptación en HML**: quien acepta debe hacer "el análisis detallado y aprobación del contenido, y la forma
  en cómo se presentará la información" (PC0901 págs. 7 y 9) — no es una pasada por la pantalla. El Coordinador
  del Cambio es responsable de pedirle los resultados al Propietario (PC0901 págs. 7 y 9).
- ⚠️ **El procedimiento de Cambio Menor no menciona a Calidad, ni pruebas de seguridad, ni ninguno de los dos
  informes** (PC0901 págs. 10-11). Tampoco dice que estén dispensados. No infieras ni la exigencia ni la
  dispensa: preguntale al Líder Técnico y dejá el criterio escrito.

## 5. Producción: dos planes, y la habilitación es un paso aparte

- **El lanzamiento es responsabilidad del Propietario**, con plan de implementación y plan de puesta en marcha
  (PC0901 págs. 7 y 9-10): aspectos técnicos, capacitación a usuarios, Mesa de Ayuda Funcional de Soporte,
  normativas y procedimientos, y comunicación formal con las áreas involucradas.
- **El Líder Técnico o quien designe ejecuta el plan**: solicita la puesta en producción, verifica y comunica
  que quedó correctamente implementada (PC0901 págs. 7 y 10).
- 🔴 **Instalado no es habilitado.** El Propietario verifica funcionalmente y aprueba el contenido ya en PRD, y
  recién entonces el Líder Técnico solicita la habilitación del cambio en PRD (PC0901 págs. 7 y 10).
- **Si el Propietario no aprueba el contenido, o la ASI considera técnicamente no viable el pase, se cancela la
  implementación** y se evalúan los pasos siguientes (PC0901 págs. 8 y 10).
- En Cambio Menor, el Coordinador del Cambio comunica la implementación y pide los resultados de aceptación; con
  resultado favorable el Líder Técnico coordina la puesta en producción y notifica al Propietario la habilitación en PRD (PC0901 pág. 11).

## 6. Pedir los ambientes y sus recursos

- **Nada arranca antes del acuerdo de pago formalizado** (GuiaDGISIS pág. 5). La aprobación verbal no alcanza:
  la gerencia envía comunicación oficial con la propuesta y el usuario aprueba formalmente por el mismo medio.
- 🔴 **El entorno DEV no se pide sin código**: hace falta un primer push de código mínimo en la rama `dev` de cada
  componente (GuiaDGISIS pág. 10). El ticket va **gris**, tipo "ASI Soporte Desarrollo y Deploy", en el proyecto
  propio, y **se deja sin asignar** para que lo tome implementaciones (pág. 10). El entorno se levanta en
  OpenShift (OCP) (pág. 11).
- **La imagen del entorno se construye a partir del "Setup de proyecto"**, con versión de lenguaje y frameworks
  por componente (GuiaDGISIS pág. 11). Si ese documento está mal, el entorno sale mal.
- **Los repositorios se piden por componente del MVP** (GuiaDGISIS pág. 8). Los accesos iniciales los gestiona
  ADHERR en el mismo pedido, a partir del documento de setup; las altas posteriores se piden de a una (pág. 8).
- **Toda aplicación nueva lleva base de datos** (GuiaDGISIS pág. 9). La Guía sólo documenta el pedido de Oracle;
  las credenciales se piden en ese mismo ticket. **Si el sistema guarda archivos, va a S3** — no declara
  alternativa — y se piden bucket y credenciales (pág. 14).
- **Usuario en AD de HML es requisito para desarrollar o probar**: habilita "todos los ambientes bajos" (GuiaDGISIS
  pág. 6). El alta en productivo exige además el formulario "Solicitud de registro en Active Directory" y foto del DNI, frente y dorso (pág. 7).
- **El primer deploy sirve para testear el pipeline**; los ajustes posteriores van por un ticket gris nuevo (pág. 11).
- **Logs**: el ambiente bajo de Kibana no está operativo — los de DEV se consultan directamente desde OpenShift
  y los de QA se piden por ticket gris en el proyecto propio, sin asignar (GuiaDGISIS págs. 9-10).
- 🔴 **OpenID PRD es una dependencia de cronograma**: en el primer pedido se solicitan DEV, QA y HML; PRD se
  solicita después, una vez aprobado el assessment de seguridad, ya pasado HML (GuiaDGISIS pág. 12).
- **Cumplir los estándares es condición para llegar a una instancia productiva**, y el vigente se consulta
  siempre en el sitio de la Agencia, no en una copia local (GuiaDGISIS pág. 12):
  `https://buenosaires.gob.ar/gcaba_historico/agencia-de-sistemas-de-informacion/estandares-de-la-agencia`
  (destino real del hipervínculo; no está impreso en el cuerpo del documento).

| Trámite | Canal (textual de la Guía) | Pág. |
|---|---|---|
| Entorno DEV en OpenShift | JIRA — ticket gris "ASI Soporte Desarrollo y Deploy", proyecto propio, sin asignar | 10-11 |
| Repositorio de código | JIRA en el proyecto ADHERR | 7-8 |
| Acceso a repositorio existente | JIRA en el proyecto ADHERR | 8 |
| Base de datos DEV (Oracle) | "Canal: JIRA" — ver contradicción 11 | 9 |
| Bucket S3 | NOC → Nueva Solicitud → Servicios Infra → Solicitud a Storage y Backup → ASI-DGINFRA-ALMACENAMIENTO DE DATOS | 14 |
| Credenciales OpenID | NOC → Nueva Solicitud → Seguridad Informática → Requerimiento de seguridad → ASI-DGSEI-IDENTIDAD | 12 |
| Alta en Active Directory | NOC → Nueva Solicitud → Seguridad Informática → Requerimiento de seguridad → ASI-DGSEI-IDENTIDAD | 6 |
| Logs de QA | Ticket gris en el proyecto propio, sin asignar | 10 |
| Acceso a Kibana ambiente alto | NOC → Nueva Solicitud → Servicios Infra → Solicitud a servidores → ASI-DGINFRA-ADMINISTRACION DE SERVIDORES | 10 |

## 7. Estimar cuánto falta para producción

🔴 **PC0901 no fija ningún plazo, porcentaje, tamaño ni umbral cuantitativo.** Cualquier duración sale del
equipo, no de la norma, y hay que decirlo así. No la busques en el PDF: no está.

Lo que la norma sí da es una secuencia que no se comprime. En Caso 1 y Caso 2, en orden:

1. Documentación de entrada aceptada por la ASI (puede rechazarse y forzar replanificación).
2. Verificación en DESA por el Desarrollador, previa a la entrega.
3. Instalación y parametrización en QA verificadas, con manual/instructivo claro y consistente.
4. "Informe de Resultados de Pruebas en QA" aprobado — ciclo iterativo hasta aprobación definitiva.
5. "Informe de Resultados de Assessment de la Aplicación en QA" aprobado — arranca recién con el anterior
   aprobado, y puede devolver el trabajo "desde donde se requiera".
6. Instalación y parametrización en HML verificadas.
7. Pruebas de aceptación con resultado favorable, recabadas por el Coordinador del Cambio.
8. Plan de implementación y plan de puesta en marcha del Propietario.
9. Instalación en PRD, verificación, y solicitud de habilitación del cambio.

Los tres puntos donde el cronograma se rompe: rechazo de documentación con replanificación de fechas (PC0901
págs. 6, 8 y 10), el ciclo de vulnerabilidades que reabre etapas anteriores (PC0901 págs. 7 y 9), y el pedido de
OpenID PRD que no se puede adelantar (GuiaDGISIS pág. 12).

⚠️ **Después de PRD estas fuentes no tienen proceso.** "Mantenimiento de Producto" está anunciada en el índice
y abierta en el cuerpo, pero el documento termina sin detallar ninguna tarea (GuiaDGISIS pág. 17).

## Lo que hay que ir a buscar al PDF

- **Anexo I — diagrama BPMN "CAMBI-010 Cambios en Software de Aplicación" (PC0901 pág. 12).** Esa página no
  tiene capa de texto: carriles, actividades, identificadores `CAMBI-010-xxx`, artefactos documentales y flujos
  existen sólo como imagen, e incluyen pasos que el cuerpo del documento no describe. **Cualquier cita literal
  de una etiqueta, un identificador o un flujo exige abrir la pág. 12 del PDF.**
- **Identificador de la primera actividad, "Solicitar Cambio" (PC0901 pág. 12).** Está ocluido por el círculo
  del evento "Inicio" en el original: **no se puede citar ni releyendo el PDF.**
- **CUIL del Responsable GCBA de la App, en el modelo de ticket de OpenID (GuiaDGISIS pág. 13).** Dato personal
  real, omitido a propósito. La regla —consignar responsable, CUIL y correo— está arriba; el valor, en el PDF.
- **Historial de versiones de la Guía (GuiaDGISIS pág. 2).** Fuera del alcance exigible; si hace falta, en el PDF.

## Contradicciones sin resolver

Se registran con sus dos lados. **Elegir un lado en silencio es inventar una norma.**

1. **Cuántos ambientes hay y cómo se llama el primero.**
   - PC0901 pág. 3: cuatro ambientes — Desarrollo (**DESA**), Testing (QA), Homologación (HML), Producción (PRD).
   - La Guía nunca dice DESA: opera con **DEV** — "entorno DEV" en OpenShift (GuiaDGISIS págs. 10-11), base de
     datos "en el entorno DEV" (pág. 9), "bucket en S3 DEV" (pág. 14), credenciales OpenID "DEV, QA y HML" (pág. 12).
   - Y no todos los servicios tienen cuatro: **AD "solo posee dos ambientes, HML y PRD"** (GuiaDGISIS pág. 6);
     SADE tiene dos, HML y PRD (pág. 15); Kibana tiene dos, "ambiente bajo" (DEV + QA) y "ambiente alto"
     (HML + PRD) (págs. 9-10).
   - Corolario que ninguna fuente responde: si AD sólo existe en HML y PRD, pero se piden credenciales OpenID
     contra AD para DEV y QA (GuiaDGISIS págs. 6 y 12), no está dicho contra qué instancia autentican DEV y QA.
   - **En la práctica**: en un ticket, usá el nombre del documento del trámite que estás haciendo; en un plan de
     pases, declará explícitamente qué nomenclatura usás y para qué servicio.
2. **Alcance del proceso.** PC0901 pág. 3: "se enfoca **exclusivamente** en la implementación de nuevas
   aplicaciones o versiones evolutivas y correctivas". PC0901 pág. 5: enumera tres tipos —software de aplicación,
   información por fuera del software, e infraestructura de TI— y ordena que cualquier cambio encuadrable siga el
   proceso. Un cambio de infraestructura entra o no según qué página se lea.
3. **Quién es "Solicitante" y quién responde por el contenido publicado.** PC0901 pág. 4: Propietario, "también
   llamado Solicitante". PC0901 pág. 5: "el solicitante (Propietario **o Referente**)". Y la responsabilidad por
   la información publicada recae en "el Solicitante" en Caso 1 (pág. 7) y en "el Propietario" en Caso 2 (pág. 9):
   si Solicitante puede ser el Referente, los dos casos apuntan a personas distintas.
4. **El Cambio Menor y DESA.** PC0901 pág. 4 lo define como un cambio "en los ambientes Testing, Homologación y
   Producción", sin mencionar DESA. PC0901 pág. 11 exige que el Desarrollador verifique en DESA antes de entregar.
5. **Coordinación con la ASI para el lanzamiento.** Caso 1 (PC0901 pág. 7): "coordinado con la ASI", sin condición.
   Caso 2 (PC0901 pág. 9): "coordinado con la ASI **-si el impacto de los cambios así lo requieren-**".
6. **Mesa de Ayuda.** Caso 1 (PC0901 pág. 7): "**conformación** de Mesa de Ayuda Funcional de Soporte".
   Caso 2 (PC0901 págs. 9-10): "el **aviso** a Mesa de Ayuda Funcional de Soporte".
7. **De qué área es el Coordinador de Instalación.** Cuerpo (PC0901 pág. 5): Área de **Soporte de Desarrollo** en
   DESA y QA, Área de **Infraestructura** en HML y PRD. Anexo I (PC0901 pág. 12, imagen): un solo carril,
   "Coordinador Instalación (Infraestructura / **Soporte DGI**)" — otro nombre de área y sin partición por ambiente.
8. **Rollback.** El diagrama del Anexo I (PC0901 pág. 12, imagen) tiene un flujo "Error" desde "Verificar
   Instalación en PRD" hacia un fin rotulado "Proceso RollBack". El cuerpo (PC0901 págs. 8 y 10) sólo prevé
   "cancelar la implementación"; la palabra rollback no aparece en las páginas 1 a 11 y el texto no define ese
   proceso ni remite a otro documento que lo defina.
9. **El cambio correctivo no tiene encabezado propio.** PC0901 pág. 3 lo define e incluye en el alcance; los
   encabezados de las págs. 5 y 8 sólo nombran "aplicación o producto nuevo" y "versión nueva o cambio evolutivo".
   Queda alcanzado por la rama "versión nueva" del Caso 2, pero ningún título lo nombra.
10. **Cómo se llama el documento adjunto obligatorio.** La Guía lo escribe de cuatro maneras: "setup de proyecto"
    (GuiaDGISIS pág. 5), "Setup de Proyecto" (pág. 8), "Setup del proyecto" (pág. 11) y "Setup de proyecto" (pág. 11).
    En dos de esos lugares es requisito formal. La fuente no aclara si es uno o son varios.
11. **Canal del pedido de base de datos.** GuiaDGISIS pág. 9 declara "Canal: JIRA" y da como ejemplo el ticket
    `1575108`, un número desnudo. En el resto del documento el número desnudo corresponde a NOC, y los de JIRA
    se citan siempre con key (ADHERR-7506, APPRESI-7, APPSADE-73592). Apuntan a sistemas distintos.
