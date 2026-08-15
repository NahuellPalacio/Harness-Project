---
name: dev-tramites-asi
description: Use when requesting something from ASI or DGISIS by ticket — OpenID Connect credentials, a DEV environment on OpenShift, an Oracle database, an S3 bucket, a code repository or access to one, AD / VPN / Jira / SADE user accounts, QA logs — or when writing the body of a NOC or Jira request (ADHERR project, gray ticket) and you need the exact channel, the fields the model ticket carries, which ones the source actually marks mandatory, and what has to be attached.
---

# Trámites ante ASI y DGISIS

Todo lo de acá sale de la **Guía de Procesos - DGISIS, versión 1.0, 17 páginas**, que cubre el inicio de un
proyecto a medida, no su mantenimiento (GuiaDGISIS págs. 4-17). Las páginas citadas son **páginas del PDF**:
el pie impreso muestra N−1 porque la portada no lleva pie (GuiaDGISIS pág. 1).

## La distinción que no se puede pisar: obligatorio ≠ viñeta del modelo

La fuente marca obligatoriedad en muy pocos lugares; el resto son viñetas de un modelo de ticket de ejemplo.
Convertir una viñeta en requisito es inventar norma.

- **Marcas textuales de obligatoriedad:** sólo los rótulos 7 y 8 del ticket de OpenID — "7. Valid Redirect
  URIs (obligatorio en PRD)" y "8. Valid Post Logout Redirect URIs (recomendado)". Los otros 11 campos de ese
  modelo **no llevan marca** (GuiaDGISIS pág. 13).
- **Requisitos formales** (la fuente escribe "Requisitos" o "es requisito"): adjuntar el documento de setup al
  pedido de repositorio (pág. 8) y al de entorno DEV (pág. 11); formulario de AD + foto del DNI para el alta
  en producción (pág. 7); informar sector y repartición en el alta SADE (pág. 16); usuario HML para quien
  desarrolle o pruebe (pág. 6).
- **Viñetas sin marca:** las cuatro del modelo de bucket S3 (GuiaDGISIS págs. 14-15). Completalas igual, pero
  no las declares obligatorias en un documento propio.
- Las "X" del bloque **Características** de OpenID marcan lo elegido **en ese ejemplo**, no un mandato del
  proceso (GuiaDGISIS pág. 14).

## Antes de abrir cualquier ticket

- **Persona nueva en el proveedor → primero la gestión de usuario, después los accesos**; AD es prerrequisito
  de cualquier sistema interno (GuiaDGISIS pág. 6).
- El aplicativo debe cumplir los estándares de desarrollo y seguridad para llegar a producción, y toda
  propuesta de arquitectura se basa en el estándar homologado vigente (GuiaDGISIS págs. 5 y 12).
- **La instancia de Jira es `https://asijira.buenosaires.gob.ar/browse/<KEY>`** — dato de las anotaciones de
  enlace, no del texto visible (GuiaDGISIS págs. 5 y 10).
- El lado código de la infra (Dockerfiles, manifiestos, versiones) lo revisa el check `dev-infra-en-codigo`;
  acá va sólo el lado trámite.

## Canales y tickets de ejemplo

| Trámite | Canal (textual) | Ticket ejemplo | Pág. |
|---|---|---|---|
| Creación de proyecto en Jira | JIRA en el proyecto ADHERR | ADHERR-7506 | 5 |
| Accesos al proyecto en Jira | JIRA en el proyecto ADHERR | ADHERR-7537 | 6 |
| Alta de usuario en AD | NOC → Nueva Solicitud → Seguridad Informática → Requerimiento de seguridad → ASI-DGSEI-IDENTIDAD | NOC 1562237 | 6 |
| Alta de VPN | NOC → Nueva Solicitud → Seguridad Informática → Requerimiento de seguridad → ASI-DGSEI-ACCESOS | NOC 1595496 | 7 |
| Alta de usuario Jira | Formulario a la gerencia (no es ticket) | — | 7 |
| Creación de repositorio | JIRA en el proyecto ADHERR | ADHERR-7536 | 7 |
| Acceso a repositorio existente | JIRA en el proyecto ADHERR | ADHERR-6448 | 8 |
| Base de datos DEV (Oracle) | JIRA | 1575108 | 9 |
| Logs de QA | Ticket gris en el proyecto propio | APPDECJUV2-2512 | 10 |
| Acceso a Kibana ambiente alto | NOC → Nueva Solicitud → Servicios Infra → Solicitud a servidores → ASI-DGINFRA-ADMINISTRACION DE SERVIDORES | — | 10 |
| Entorno DEV en OpenShift | JIRA — ticket gris, tipo "ASI Soporte Desarrollo y Deploy" | APPRESI-7 | 10-11 |
| Credenciales OpenID | NOC → Nueva Solicitud → Seguridad Informática → Requerimiento de seguridad → ASI-DGSEI-IDENTIDAD | 1565975 | 12 |
| Bucket S3 | NOC → Nueva Solicitud → Servicios Infra → Solicitud a Storage y Backup → ASI-DGINFRA-ALMACENAMIENTO DE DATOS | 1567809 | 14 |
| Integración SADE | Mail al equipo de Integraciones | — | 15 |
| Alta usuario SADE PRD | Mail al ALS del área | — | 15 |
| Alta usuario SADE HML | Jira en el proyecto APPSADE | APPSADE-73592 | 15 |

## Alta de personas

- **AD tiene exactamente dos ambientes: HML y PRD.** Quien desarrolle o pruebe necesita usuario **HML** para
  usar todos los ambientes bajos. Los ingresantes a Gobierno ya vienen con alta productiva; los de proveedor
  hay que gestionarlos (GuiaDGISIS pág. 6).
- **Cuerpo del ticket de AD** (GuiaDGISIS págs. 6-7): "Se solicita realizar el alta en Active Directory." ·
  "Se solicita generar usuario de prueba en [ambientes. Ej HML y PRD]" · NOMBRE · APELLIDO · CUIL · CORREO ·
  "REPARTICION: DGISIS".
- **Sólo para PRD es requisito adjuntar** el formulario "Solicitud de registro en Active Directory" (plantilla
  del proveedor, en PDF ya completado) y **foto del DNI, frente y dorso** (GuiaDGISIS pág. 7).
- **VPN**: mismo bloque de datos, cuerpo "Se solicita realizar el alta de usuario VPN." (GuiaDGISIS pág. 7).
- **Usuario Jira no se pide por ticket**: formulario "Solicitud de alta de usuarios en Jira" a la gerencia,
  porque consume licencia (GuiaDGISIS pág. 7).

## Proyecto y accesos en Jira (ADHERR)

- Creación (GuiaDGISIS pág. 5), textual: "Nombre del proyecto: [ej Sistema de Gestión de Residencias]" ·
  "Abreviatura de proyecto/clave de proyecto: [ej APP_RESI]" · "Se adjunta setup de proyecto."
- La fuente dice que hay que completar la ficha del proyecto porque "se requiere adjuntar **el ticket** para
  la solicitud" (GuiaDGISIS pág. 5). La redacción del original es ambigua: citala como está, no la corrijas.
- **El acceso se da por perfil, no por persona**, porque los equipos cambian (GuiaDGISIS pág. 6). Cuerpo: "Se
  solicita agregar [Clave de proyecto] al perfil de Zafirus, para que todos los que posean dicho perfil tengan
  acceso al proyecto."

## Repositorios

- Se piden los repositorios de **los componentes del MVP**: lo típico es front y back, pero depende de la
  arquitectura definida (GuiaDGISIS pág. 8).
- El cuerpo lleva una tabla de tres columnas — **Componente · Tecnología · Nombre** (ej. Frontend / Angular /
  Residencias-front) — y debajo "Abreviatura de proyecto: APP_RESI". Todos los valores del original llevan el
  prefijo "Ej": son ejemplos (GuiaDGISIS pág. 8).
- **Requisito: adjuntar el documento "Setup de Proyecto"** (GuiaDGISIS pág. 8).
- **Los accesos iniciales los gestiona ADHERR con ese mismo pedido**, porque el setup trae el detalle de los
  usuarios que accederán (GuiaDGISIS pág. 8): no abras un ticket aparte para ellos.
- **Altas posteriores, de a una** (GuiaDGISIS pág. 8): "De ingresar una persona al equipo luego de que el
  repositorio haya sido creado, se debe solicitar que se agregue su acceso de manera individual." El cuerpo del
  ticket está en la página siguiente (GuiaDGISIS pág. 9): "Se solicita brindar acceso al siguiente repositorio
  con permisos de desarrollador: [URL del/de los repositorios] para el siguiente usuario:" + NOMBRE · APELLIDO ·
  CUIL · CORREO. El único permiso nombrado es **desarrollador**; el documento no enumera otros niveles.

## Base de datos DEV

- Todo sistema nuevo requiere base de datos y el motor depende de la arquitectura definida, pero **el
  documento sólo documenta el pedido de Oracle** (GuiaDGISIS pág. 9): para otro motor no hay procedimiento
  citable.
- Cuerpo textual (GuiaDGISIS pág. 9): "Se solicita la creación de una base de datos en el entorno DEV para el
  nuevo proyecto: … / Motor Oracle, versión [número de versión requerida. Ej 19c]. / El esquema debería
  llamarse [establecer un nombre para identificar al esquema]. / Por favor, compartir las credenciales para
  conectar la base de datos al backend del aplicativo."
- **Las credenciales se piden en ese mismo ticket**, en la última línea. Ojo con el canal: ver contradicciones.

## Entorno DEV en OpenShift y primer deploy

- **Prerrequisito**: pedirle al proveedor un primer push de código mínimo en la rama `dev` de cada componente
  (GuiaDGISIS pág. 10).
- **Ticket gris, tipo "ASI Soporte Desarrollo y Deploy", en el proyecto propio, y se deja sin asignar** para
  que lo tome el equipo de implementaciones (GuiaDGISIS pág. 10).
- Cuerpo (GuiaDGISIS pág. 11): "Solicitamos la generación del entorno DEV en OpenShift (OCP) para el nuevo
  proyecto [Nombre del proyecto]." + "1. La creación del proyecto correspondiente en OpenShift." + "2. La
  asignación de accesos sobre el proyecto en Openshift para los referentes y participantes detallados en el
  documento adjunto «Setup del proyecto»." + un bloque "Repositorios:" con la URL del frontend y la del backend.
- **Adjuntar el setup con versión de lenguaje y frameworks de cada componente: de ahí se construye la imagen
  del entorno** (GuiaDGISIS pág. 11).
- Con el código mínimo cargado, avisarle al proveedor que haga un primer deploy **para testear el pipeline**;
  los ajustes que aparezcan después van por un **nuevo ticket gris** (GuiaDGISIS pág. 11).

## Credenciales OpenID Connect

- **Todo proyecto de usuarios internos del Gobierno autentica contra AD por OpenID Connect** y hay que pedir
  credenciales para ser dado de alta como consumidor (GuiaDGISIS pág. 12).
- **Primer pedido: DEV, QA y HML. PRD va después, con el assessment de seguridad aprobado (posterior al pasaje
  a HML).** Los entornos se declaran en el campo "Ambiente de la app" (GuiaDGISIS pág. 12).
- **La URL de la aplicación es la del frontend de DEV que provee implementaciones**; las de QA y HML se
  deducen reemplazando el nombre del ambiente (GuiaDGISIS pág. 12).
- **Redirect URIs = URL del frontend + `/callback`**, más una URI de localhost **sólo para DEV**, validando
  antes cuál es la dirección requerida (GuiaDGISIS pág. 12). Esa URI queda atada al client ID de DEV, y el
  `:4200` del ejemplo es del ejemplo, no un valor normativo (pág. 13).
- **Post Logout Redirect URIs = URL del frontend + `/login`** (GuiaDGISIS pág. 12).
- **Los 13 campos, en orden** (GuiaDGISIS págs. 13-14): 1. Responsable GCBA de la App (nombre – CUIL – correo
  – "GO Proyectos DGISIS") · 2. Repartición responsable ("DGISIS") · 3. Ambiente de la App · 4. Nombre de la
  aplicación · 5. URL de la aplicación · 6. Breve descripción · 7. Valid Redirect URIs (obligatorio en PRD) ·
  8. Valid Post Logout Redirect URIs (recomendado) · 9. Método de validación actual y endpoints ·
  10. Justificación de scopes adicionales (si corresponde) · 11. Tema · 12. Tipo de usuarios · 13. Assessment
  de seguridad (solo PRD).
- **Catálogo de scopes del servicio** (GuiaDGISIS pág. 14): `openid` es el default; `dn` y `email` son
  opcionales; `ad_groups` y `email_alternativo` son adicionales, y los adicionales se justifican en el campo
  10 (pág. 13). El mismo bloque ofrece "Recaptcha Google Enterprise Invisible" y MFA (forzado por usuario /
  por la App / no utilizar): en el ejemplo está marcado "No utilizar MFA".
- **Un mismo client id puede gestionar múltiples frontends desde un backend común** (GuiaDGISIS pág. 14),
  textual: "Un mismo client id puede gestionar múltiples frontends desde un backend común. Ej, un sistema que
  tiene un backend pero tiene un frontend de cara al usuario final y otro frontend de cara al administrador
  podrá gestionarse la redirección hacia uno u otro desde un backend con el mismo client id." Es una
  posibilidad ("puede", "podrá"), no una instrucción: el documento **no** prohíbe pedir credenciales separadas,
  y su ejemplo supone un backend único. Con dos backends o dos aplicaciones separadas no hay regla citable.

## Bucket S3

- Si el sistema guarda archivos va a **S3 provisto por Almacenamiento de Datos de Infraestructura** — la
  fuente no declara alternativa — y se piden **el bucket y las credenciales** (GuiaDGISIS pág. 14).
- Viñetas del modelo, sin marca de obligatoriedad (GuiaDGISIS págs. 14-15): "Nombre sugerido del bucket" ·
  "Cuota de espacio necesaria en GB" · "Ministerio/Repartición/Secretaría" de los dueños/cliente de la
  aplicación · "Nombre y correo electrónico de uno o más responsables técnicos" (analistas técnicos DGISIS y
  gerencia).
- El nombre se elige **"en relación a la aplicación"**; no hay patrón formal ni largo máximo (GuiaDGISIS pág. 14).

## Logs

- Kibana tiene ambiente bajo (DEV y QA) y ambiente alto (HML y PRD), pero **el bajo no está operativo**: los
  logs de DEV se leen directamente en OpenShift y los de QA se piden al equipo de implementaciones
  (GuiaDGISIS págs. 9-10).
- Logs de QA: **ticket gris en el proyecto propio, sin asignar** (GuiaDGISIS pág. 10). Cuerpo: "Se solicita
  adjuntar los logs del ambiente QA del componente [nombre del componente]. / [URL del componente]".
- Acceso al ambiente alto de Kibana (GuiaDGISIS pág. 10): "Se solicita dar de alta el siguiente usuario para
  acceder a Kibana: [Nombre completo] - [CUIL] - [Mail]".

## Integración SADE

- **Primero se contacta por mail al equipo de Integraciones** con una breve descripción del proyecto y el
  objetivo de la integración, para que orienten sobre los servicios adecuados. Los dos contactos
  con nombre y apellido están en la GuiaDGISIS pág. 15 — no se transcriben acá porque este
  repo es público y son datos personales de terceros.
- **El esquema no lo elige el proyecto**: Integraciones determina si va directo con SADE por ESB o por
  interoperabilidad vía XBA, y el equipo correspondiente comparte la documentación de cada servicio
  (GuiaDGISIS pág. 15).
- Para entrar a SADE hacen falta **dos** usuarios: uno de AD y otro habilitado en SADE. SADE tiene dos
  ambientes estables, HML y PRD (GuiaDGISIS pág. 15). El alta en PRD va por mail al ALS del área (pág. 15).
- Alta en HML por Jira APPSADE, y **hay que ponerle al ticket las cuatro etiquetas, con esas cuatro grafías
  distintas: `SGOGIYD` · `SGOGYD` · `SGOIYD` · `SGOYID`** — si no, el equipo no lo recibe en su bandeja
  (GuiaDGISIS pág. 16). Cuerpo: "Se solicita por favor, dar de alta los siguientes usuarios en SADE HML: /
  [Nombre completo] - [CUIL] - [Mail] / Por favor, copiar estructura jerárquica y permisos del perfil [CUIL
  del perfil a copiar]."
- **Es obligatorio informar sector y repartición** (GuiaDGISIS pág. 16): se resuelve indicando el CUIL de un
  usuario existente de la misma área para replicar, o especificándolos explícitamente si no hay perfil de
  referencia.

## Lo que hay que ir a buscar al PDF

- **CUIL del Responsable GCBA de la App, pág. 13.** Es un dato personal real, omitido a propósito del
  extracto. La regla sí está acá — el campo 1 lleva nombre, CUIL y correo —; el valor concreto se lee en el PDF.
- **Historial de versiones del documento, pág. 2.** Queda fuera del alcance exigible; si hace falta, se lee ahí.
- **El estándar vigente no está en este PDF.** El documento remite al sitio de la Agencia, donde está el
  último estándar completo y su changelog (GuiaDGISIS pág. 12). El texto visible es sólo "Estándares de la
  Agencia | Buenos Aires Ciudad"; el destino del hipervínculo es
  `https://buenosaires.gob.ar/gcaba_historico/agencia-de-sistemas-de-informacion/estandares-de-la-agencia`
  (con `gcaba_historico` en la ruta) y **no está impreso en el cuerpo**.

## Contradicciones sin resolver

1. **Nombre del documento que se adjunta.** Cuatro grafías: "setup de proyecto" (pág. 5), "Setup de Proyecto"
   (pág. 8), "Setup del proyecto" (pág. 11) y "Setup de proyecto" (pág. 11). El documento no aclara si es uno
   solo con nombre inestable o varios distintos.
2. **Canal del pedido de base de datos.** La pág. 9 declara "Canal: JIRA" pero el ticket ejemplo es `1575108`,
   número desnudo: en todo el resto del documento el número desnudo es NOC (1562237, 1595496, 1565975,
   1567809) y los de Jira siempre llevan key (ADHERR-7506, APPRESI-7, APPSADE-73592). Canal declarado y
   formato del ejemplo apuntan a sistemas distintos.
3. **Ambientes de AD vs. ambientes de las credenciales OpenID.** La pág. 6 dice que "Active Directory solo
   posee dos ambientes, HML y PRD"; la pág. 12 dice que se autentica contra AD y que en el primer pedido se
   piden credenciales para DEV, QA y HML. Contra qué instancia de AD autentican los clients de DEV y QA no
   está explicado.
4. **Encabezados duplicados.** "Estándares de Desarrollo y Seguridad" figura suelto al final de Estimación
   (pág. 5) y como sección real (págs. 11-12); "Alta de usuario en Active Directory" aparece dos veces en la
   pág. 6. Al citar, aclarar la página.
5. **Mantenimiento de Producto está anunciado y vacío.** La pág. 17 promete detallar tareas y situaciones, y
   el documento termina ahí. **No hay proceso de mantenimiento citable desde este documento**: si te lo piden,
   decilo, no lo completes.
