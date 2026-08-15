# GuiaDGISIS — Guía de Procesos (DGISIS - Gerencia Operativa de Proyectos)

> Fuente: normativa/fuentes/Guía de Procesos - DGISIS.pdf
> Versión 1.0 · 17 páginas · extractado el 2026-08-12
> Este extracto conserva las reglas exigibles. NO reemplaza al PDF para lo que
> figure abajo como no citable.

**Numeración de páginas — leer antes de citar.** Todas las referencias `(pág. N)` de este
extracto son **páginas del PDF** (las que sirven para `Read ... pages=N`). El pie impreso
del documento muestra **N−1**, porque la portada no lleva pie: el pie "1" está en la página
2 del PDF y el pie "16" en la página 17. El índice interno del documento usa la numeración
impresa, no la del PDF.

Título exacto en la portada (pág. 1): "DGISIS - Gerencia Operativa de Proyectos / Guía de
Procesos / Versión 1.0". Pie de página corriente: "Guía de Procesos - DGISIS - TecBA".

---

## Lo que NO se puede citar desde acá

- **CUIL del Responsable GCBA de la App (pág. 13).** El modelo de ticket de OpenID trae un
  CUIL real de una persona. Está **deliberadamente omitido** de este extracto por tratarse
  de un dato personal; la regla ("hay que consignar responsable, CUIL y correo") sí está
  conservada más abajo. El valor concreto se lee en la pág. 13 del PDF.

Fuera de eso, todo lo demás del documento se convirtió limpio y es citable. En particular:

- La tabla **"Historial de cambios" (pág. 2)** se verificó **contra el PDF maquetado**: son
  tres columnas (Fecha · Nombre · Descripción) y tres filas alineadas, cada fecha con su autor
  y su descripción, sin fusión de celdas. Es citable — "15/04/2026 · Belio Gaston · Complemento
  de información" es una fila única e inequívoca. (El historial de versiones queda igualmente
  fuera del alcance exigible de este extracto; si hace falta, se lee en la pág. 2 del PDF.)
- La tabla de componentes del ticket de repositorios (pág. 8) se verificó **contra el PDF
  maquetado** y conserva su alineación de tres columnas. Es citable.
- El bloque "Características" del ticket de OpenID (pág. 14) **no usa casillas gráficas**:
  las marcas son la letra "X" en texto plano, resaltada en amarillo. Se verificó contra el
  PDF maquetado. Es citable.
- **Ninguna regla vive únicamente en una imagen.** Las capturas de pantalla de JIRA
  (págs. 16 y 17) y la captura de etiquetas de SADE (pág. 16) sólo ilustran pasos que el
  cuerpo del texto ya enuncia. Se verificaron una por una.

---

## Alcance y estado del documento

- **El documento cubre el inicio de un proyecto a medida, no su mantenimiento** (págs. 4 a 17).
  El índice (pág. 3) declara tres bloques: "Inicio de Proyecto a Medida", "Integraciones" y
  "Mantenimiento de Producto".
- **La sección "Mantenimiento de Producto" está abierta pero vacía de procedimiento**
  (pág. 17). Anuncia contenido que el documento no entrega: "A partir de este momento,
  comenzarás a involucrarte en distintos tipos de solicitudes y gestiones vinculadas al
  mantenimiento y evolución del sistema. A continuación, se detallan las principales tareas
  y situaciones en las que podrás participar, junto con una guía general sobre cómo
  abordarlas." — y el documento termina ahí. **No hay proceso de mantenimiento citable
  desde este documento.**

---

## Etapa de análisis

- **Antes de definir alcance hay que leer la Especificación Prefuncional** (pág. 4) —
  "Revisión Documental: Leer exhaustivamente la Especificación Prefuncional elaborada por el
  equipo de iniciativas o el documento de alcance disponible, y/o la documentación brindada
  por el usuario."
- **Hay que coordinar una reunión con el equipo de iniciativas** para comprender el contexto
  del requerimiento (pág. 4).
- **El alcance se parte en MVP y fases futuras** (pág. 4) — "Alcance: Identificar qué
  funcionalidades son críticas para la primera salida a producción (MVP) y cuáles quedan
  postergadas para fases futuras."
- **Las integraciones externas se detectan en esta etapa** y se identifica cuáles son
  críticas para la primera etapa (pág. 4).
- **Alineación con stakeholders** (pág. 4): solicitar contactos de los referentes del negocio,
  coordinar reunión de presentación, validar el entendimiento del proceso de negocio, llevar
  dudas específicas y una propuesta de alcance inicial, recoger feedback y ajustar la
  definición del MVP, y realizar nuevas reuniones si es necesario.

## Estimación y acuerdo administrativo

- **La estimación se pide por duplicado** (págs. 4-5): al proveedor designado por la gerencia
  se le solicita "una propuesta de arquitectura y un orden de magnitud (estimación temprana a
  gran escala) por el MVP definido" (pág. 4), y **también** al equipo de Arquitectura de
  DGISIS "para tener una segunda mirada sobre el proyecto" (pág. 5).
- **Hay que agendar una reunión con ambos equipos** para explicarles el contexto y la
  necesidad antes de que hagan las propuestas (pág. 5).
- **Si las propuestas difieren, decide la gerencia** (pág. 5) — "Se comparan ambas propuestas,
  y de diferir, se abordará con la gerencia cuál debe ser considerada y/o si se debe ajustar
  alguna."
- **Toda propuesta de arquitectura se basa en el estándar vigente** (pág. 5) — "Recordar que
  las propuestas de arquitectura siempre se deben basar en el estándar homologado de
  desarrollo y seguridad vigente."
- **La aprobación verbal no alcanza: hace falta aprobación formal por comunicación oficial**
  (pág. 5) — "De ser aprobada verbalmente, inicia un circuito administrativo del cual se
  encarga la gerencia, que es enviar una comunicación oficial adjuntando la propuesta con el
  orden de magnitud, para que el usuario de su aprobación formal por el mismo medio, con el
  objetivo de formalizar el acuerdo de pago."
- **La gestión del proyecto no arranca antes del acuerdo de pago** (pág. 5) — "Formalizado el
  acuerdo de pago, podremos iniciar la gestión del proyecto."

---

## Creación del proyecto en Jira

- **Canal: "JIRA en el proyecto ADHERR."** Ticket ejemplo: `ADHERR-7506` (pág. 5).
- **Hay que completar la ficha del proyecto** (pág. 5) — "Deberemos completar la ficha del
  proyecto con la información correspondiente, dado que se requiere adjuntar el ticket para
  la solicitud." **Ojo con la redacción del original**: lo que la fuente dice que se requiere
  adjuntar es "el ticket", no la ficha. No se corrige acá: se cita como está.
- **Campos del modelo de ticket** (pág. 5), textual: "Nombre del proyecto: [ej Sistema de
  Gestión de Residencias]" · "Abreviatura de proyecto/clave de proyecto: [ej APP_RESI]" ·
  "Se adjunta setup de proyecto."

## Accesos al proyecto en Jira

- **El acceso se otorga por perfil, no por persona** (pág. 6) — "para una mejor gestión, dado
  que los equipos son susceptibles a cambios, el acceso se realiza por perfil, y no por
  persona. Garantizando que cualquier persona del equipo del proveedor pueda acceder al
  proyecto".
- **Canal: "JIRA en el proyecto ADHERR."** Ticket ejemplo: `ADHERR-7537` (pág. 6).
- **Modelo de ticket** (pág. 6), textual: "Se solicita agregar [Clave de proyecto] al perfil
  de Zafirus, para que todos los que posean dicho perfil tengan acceso al proyecto."
- **Si la persona es nueva en el proveedor, primero va la gestión de usuario** (pág. 6) —
  "Tener en cuenta que esto aplica si la persona ya era parte de algún proyecto y tiene
  usuario. Si la persona es nueva en el proveedor, y este será su primer proyecto,
  requerimos primero iniciar la gestión de usuario, para luego poder dar estos accesos."

---

## Alta de usuario en Active Directory (AD) — sólo usuarios nuevos

- **AD es prerrequisito de cualquier sistema interno** (pág. 6) — "Para autenticarnos en
  cualquier sistema interno, primero necesitaremos estar dados de alta en este directorio, y
  posteriormente en el sistema en cuestión si es que maneja también gestión de usuarios."
- **AD tiene exactamente dos ambientes** (pág. 6) — "Active Directory solo posee dos
  ambientes, HML y PRD."
- **Los ingresantes a Gobierno ya vienen con alta; los de proveedor hay que gestionarlos**
  (pág. 6) — "Para las personas ingresantes a Gobierno, su alta en AD productivo estará
  generada antes de ingresar. Para las personas ingresantes a un equipo proveedor de
  desarrollo, tendremos que gestionar el alta."
- **Usuario HML obligatorio para desarrollar o probar** (pág. 6) — "Para una persona que
  participará en el desarrollo o realizará pruebas, es requisito que tenga usuario en el
  entorno de HML para la utilización de todos los ambientes bajos."
- **Canal** (pág. 6), textual: "Canal: NOC → Nueva Solicitud → Seguridad Informática →
  Requerimiento de seguridad → ASI-DGSEI-IDENTIDAD". Ticket ejemplo: `NOC 1562237`.
- **Datos del modelo de ticket** (págs. 6-7): "Se solicita realizar el alta en Active
  Directory." · "Se solicita generar usuario de prueba en [ambientes. Ej HML y PRD]" ·
  NOMBRE, APELLIDO, CUIL, CORREO, "REPARTICION: DGISIS".
- **Requisito adicional sólo para producción** (pág. 7), textual: "Para el alta en ambiente
  productivo es requisito adjuntar: Formulario "Solicitud de registro en Active Directory"
  (el proveedor ya tiene la plantilla, nos lo comparte en PDF con la información de la
  persona completada) e Incluir foto del DNI (frente y dorso, provista por el proveedor)."

## Alta de VPN — sólo usuarios nuevos

- **Canal** (pág. 7), textual: "Canal: NOC → Nueva Solicitud → Seguridad Informática →
  Requerimiento de seguridad → ASI-DGSEI-ACCESOS". Ticket ejemplo: `NOC 1595496`.
- **Datos del modelo de ticket** (pág. 7): "Se solicita realizar el alta de usuario VPN." ·
  NOMBRE, APELLIDO, CUIL, CORREO, "REPARTICION: DGISIS".

## Alta de usuario Jira — sólo usuarios nuevos

- **No se pide por ticket: va por la gerencia con formulario** (pág. 7) — "Completar
  formulario "Solicitud de alta de usuarios en Jira" y compartir a la gerencia, solicitando
  su gestión."
- **El motivo es la licencia** (pág. 7) — "El alta de usuario JIRA requiere la asignación de
  una licencia de Jira, por lo que requiere que sea gestionado por la gerencia."

---

## Repositorio de código

- **Canal: "JIRA en el proyecto ADHERR."** Ticket ejemplo: `ADHERR-7536` (pág. 7).
- **Se pide por ticket dirigido a ADHERR** (pág. 8) — "Solicitar la creación del repositorio
  mediante un ticket en Jira dirigido a ADHERR."
- **Se piden los repositorios de los componentes del MVP** (pág. 8) — "se solicitará la
  creación de los repositorios para los componentes identificados como necesarios para el
  desarrollo del MVP. La mayoría de los sistemas requerirán un frontend y un backend, pero
  puede haber sistemas que requieran de otros componentes adicionales. Esto dependerá
  netamente de la arquitectura definida y de la necesidad del sistema."
- **Estructura de la tabla del modelo de ticket** (pág. 8) — verificada contra el PDF
  maquetado, tres columnas:

  | Componente | Tecnología | Nombre |
  |---|---|---|
  | Ej Frontend | Ej Angular | Ej Residencias-front |
  | Ej Backend | Ej NestJS | Ej Residencias-back |

  Debajo de la tabla, dentro del mismo recuadro: "Abreviatura de proyecto: APP_RESI".
  (Todos los valores llevan el prefijo "Ej" en el original: son ejemplos, no valores fijos.)
- **Requisito** (pág. 8), textual: "Adjuntar el documento "Setup de Proyecto"."

## Accesos al repositorio

- **Los accesos iniciales los gestiona ADHERR con el mismo pedido de creación** (pág. 8) —
  "En la etapa de creación del repositorio, se adjunta el documento de setup que posee el
  detalle de todos los usuarios que accederán al mismo, por lo que ADHERR ya gestiona los
  accesos en ese mismo pedido."
- **Las altas posteriores se piden de a una** (pág. 8) — "De ingresar una persona al equipo
  luego de que el repositorio haya sido creado, se debe solicitar que se agregue su acceso de
  manera individual."
- **Canal: "JIRA en el proyecto ADHERR."** Ticket ejemplo: `ADHERR-6448` (pág. 8).
- **Modelo de ticket** (pág. 9), textual: "Se solicita brindar acceso al siguiente repositorio
  con permisos de desarrollador: [URL del/de los repositorios] para el siguiente usuario:"
  seguido de NOMBRE, APELLIDO, CUIL, CORREO. **El permiso nombrado es "desarrollador"**; el
  documento no enumera otros niveles de permiso.

---

## Base de datos DEV

- **Toda aplicación nueva lleva base de datos** (pág. 9) — "Todo sistema nuevo, requerirá una
  base de datos. El motor de la base de datos a solicitar dependerá de la arquitectura
  definida."
- **Canal (para Oracle): "Canal: JIRA"**. Ticket ejemplo: `1575108` (pág. 9). Ver
  "Contradicciones internas": el formato de ese número no coincide con el de los demás
  tickets de JIRA del documento.
- **El documento sólo documenta el pedido de Oracle** (pág. 9) — "Para solicitar la creación
  de una Base de datos Oracle:". No hay procedimiento para otros motores.
- **Modelo de ticket** (pág. 9), textual: "Se solicita la creación de una base de datos en el
  entorno DEV para el nuevo proyecto: "Sistema de Gestión de Residencias" / Motor Oracle,
  versión [número de versión requerida. Ej 19c]. / El esquema debería llamarse [establecer un
  nombre para identificar al esquema]. / Por favor, compartir las credenciales para conectar
  la base de datos al backend del aplicativo."
- **Las credenciales se piden en el mismo ticket** (pág. 9), según la última línea del modelo.

---

## Kibana y logs

- **Kibana tiene dos ambientes: "Ambiente bajo" y "Ambiente alto"** (pág. 9).
- **El ambiente bajo concentra DEV y QA; el alto, HML y PRD** (págs. 9-10) — "El ambiente bajo
  concentra los logs correspondientes a los entornos DEV y QA de todos los aplicativos." /
  "El ambiente alto centraliza los logs de los entornos HML y PRD de todos los aplicativos."
- **El ambiente bajo no está operativo: los logs de DEV se leen en OpenShift** (págs. 9-10;
  la frase cruza el corte de página) — "Actualmente, este ambiente no se encuentra operativo,
  por lo que los logs de DEV deben consultarse directamente desde OpenShift. Los logs de QA,
  deberán ser solicitados al equipo de implementaciones."
- **Logs de QA: por ticket gris en el proyecto propio** (pág. 10) — "Los logs de QA se deben
  solicitar por ticket gris en el proyecto." Ticket ejemplo: `APPDECJUV2-2512`.
- **El ticket de logs QA se deja sin asignar** (pág. 10) — "Dejar el ticket sin asignar para
  que sea tomado por el equipo de implementaciones."
- **Modelo de ticket de logs QA** (pág. 10), textual: "Se solicita adjuntar los logs del
  ambiente QA del componente [nombre del componente]. / [URL del componente]"
- **Acceso al ambiente alto de Kibana — canal** (pág. 10), textual: "Canal: NOC → Nueva
  Solicitud → Servicios Infra → Solicitud a servidores → ASI-DGINFRA-ADMINISTRACION DE
  SERVIDORES". Modelo: "Se solicita dar de alta el siguiente usuario para acceder a Kibana:
  [Nombre completo] - [CUIL] - [Mail]". El documento **no** da ticket de ejemplo para este
  pedido.

---

## Armado del entorno DEV

- **Prerrequisito: push de código mínimo en la rama `dev`** (pág. 10) — "Para proceder con la
  solicitud del armado del entorno DEV, se debe solicitar al proveedor, que haga un primer
  push de código mínimo en la rama dev de cada componente (ej, back y front)."
- **Tipo de ticket** (pág. 10), textual: "Generar un ticket gris (Tipo de ticket: ASI Soporte
  Desarrollo y Deploy) dentro del proyecto propio."
- **Se deja sin asignar** (pág. 10) — "Dejar sin asignar para que sea tomado por el equipo de
  implementaciones."
- **Canal: "JIRA"**. Ticket ejemplo: `APPRESI-7` (pág. 11).
- **El entorno DEV se levanta en OpenShift (OCP)** (pág. 11). Modelo de ticket, textual:
  "Solicitamos la generación del entorno DEV en OpenShift (OCP) para el nuevo proyecto
  [Nombre del proyecto]." Se solicita: "1. La creación del proyecto correspondiente en
  OpenShift." y "2. La asignación de accesos sobre el proyecto en Openshift para los
  referentes y participantes detallados en el documento adjunto "Setup del proyecto"."
  El modelo lista además "Repositorios:" con "Frontend: [URL del repositorio frontend]" y
  "Backend: [URL del repositorio backend]".
- **Requisito, y de él depende la imagen del entorno** (pág. 11), textual: "Adjuntar el
  documento "Setup de proyecto" con el detalle de las tecnologías (versión de lenguaje y
  frameworks) que aplicarán a cada componente. En base a esto, se construirá la imagen del
  entorno."

## Deploy inicial

- **El primer deploy es para probar el pipeline** (pág. 11) — "Una vez cargado el código
  mínimo se debe informar al proveedor que ya puede realizar un primer deploy para testear el
  pipeline de despliegue y corroborar que sea exitoso."
- **Los ajustes de pipeline van por un ticket gris nuevo** (pág. 11) — "Es probable que en la
  fase de desarrollo aún se identifiquen algunas dependencias que requieran que se ajuste el
  pipeline para el correcto despliegue. En este caso, se puede canalizar el pedido de ajuste
  por un nuevo ticket gris."

---

## Estándares de desarrollo y seguridad

- **Cumplir los estándares es condición para llegar a producción** (pág. 12) — "Recordar
  siempre que el aplicativo debe seguir ciertos estándares de desarrollo y seguridad para
  poder llegar a una instancia productiva."
- **La fuente vigente es el sitio de la Agencia, no una copia local** (pág. 12) — "El estándar
  vigente puede ser consultado siempre en: Estándares de la Agencia | Buenos Aires Ciudad" /
  "Allí puede consultarse el último estándar completo vigente, y el changelog acerca de los
  cambios que sufrió respecto al estándar anterior."
- **URL del hipervínculo** (pág. 12) — el texto visible es sólo "Estándares de la Agencia |
  Buenos Aires Ciudad"; el destino real del enlace, extraído de la anotación del PDF, es
  `https://buenosaires.gob.ar/gcaba_historico/agencia-de-sistemas-de-informacion/estandares-de-la-agencia`
  (nótese el segmento `gcaba_historico` en la ruta). Esta URL **no está impresa en el cuerpo
  del documento**: sale del hipervínculo.
- **Instancia de JIRA** — dato tomado también de las anotaciones de enlace de los tickets de
  ejemplo (págs. 5 y 10), no del texto visible: `https://asijira.buenosaires.gob.ar/browse/<KEY>`.

---

## Integración: OpenID Connect

- **Obligatorio para todo sistema de usuarios internos** (pág. 12) — "Para todos los proyectos
  orientados a usuarios internos del Gobierno, los sistemas deberán implementar autenticación
  contra el Active Directory (AD) mediante el protocolo OpenID Connect."
- **Hay que pedir credenciales para ser dado de alta como consumidor** (pág. 12) — "es
  necesario solicitar las credenciales correspondientes para ser dados de alta como
  consumidores del servicio."
- **Canal** (pág. 12), textual: "Canal: NOC → Nueva Solicitud → Seguridad Informática →
  Requerimiento de seguridad → ASI-DGSEI-IDENTIDAD". Ticket ejemplo: `1565975`.
- **Los entornos pedidos se declaran en el campo "Ambiente de la app"** (pág. 12) — encabeza
  el bloque "Consideraciones para la solicitud": "En el campo Ambiente de la app, se deben
  indicar los entornos para los que se solicitan credenciales."
- **Ambientes que se piden de entrada** (pág. 12) — "Se pueden solicitar en un primer pedido:
  DEV, QA y HML."
- **PRD va después del assessment de seguridad** (pág. 12) — "El entorno PRD deberá
  solicitarse posteriormente, una vez aprobado el assessment de seguridad (luego del pasaje a
  HML)."
- **La URL de la app se toma del frontend DEV y las demás se deducen** (pág. 12) — "En la URL
  de la aplicación, se debe consignar la URL del frontend de DEV provista por el equipo de
  implementaciones. A partir de esta, se podrán deducir las URLs de QA y HML reemplazando el
  nombre del ambiente."
- **Patrón de Redirect URIs** (pág. 12) — "Para las Redirect URIs, se deberá utilizar:" ·
  "URL del frontend + /callback" · "Incluir también una URI de localhost (solo para DEV),
  validando previamente cuál es la dirección requerida."
- **Patrón de Post Logout Redirect URIs** (pág. 12) — "Para las Post Logout Redirect URIs, se
  deberá utilizar:" · "URL del frontend + /login".
- **La URI de localhost queda atada al client ID de DEV** (pág. 13) — en el modelo de ticket:
  "http://localhost:4200/callback (validar con el proveedor) (solo para client ID DEV)". El
  puerto 4200 aparece **dentro del ejemplo**, no como valor normativo.
- **Obligatoriedad declarada de cada campo** (pág. 13), textual de los rótulos del modelo:
  "7. Valid Redirect URIs (obligatorio en PRD)" y "8. Valid Post Logout Redirect URIs
  (recomendado)". El resto de los campos del modelo no lleva marca de obligatoriedad.
- **Campos del modelo de ticket** (págs. 13-14), en orden: 1. Responsable GCBA de la App
  (nombre – CUIL – correo – "GO Proyectos DGISIS"; el CUIL concreto se omite acá, ver "Lo que
  NO se puede citar desde acá") · 2. Repartición responsable GCBA de la App ("DGISIS") ·
  3. Ambiente de la App ("DEV – QA – HML") · 4. Nombre de la aplicación · 5. URL de la
  aplicación · 6. Breve descripción de la aplicación · 7. Valid Redirect URIs · 8. Valid Post
  Logout Redirect URIs · 9. Método de validación actual y endpoints · 10. Justificación de
  scopes adicionales (si corresponde) · 11. Tema · 12. Tipo de usuarios · 13. Assessment de
  seguridad (solo PRD).
- **Tipo de usuarios en el ejemplo** (pág. 13), textual: "12. Tipo de usuarios / Sí,
  únicamente usuarios internos del GCBA."
- **Bloque "Características" del modelo de ticket** (pág. 14) — verificado contra el PDF
  maquetado. Es un menú de opciones dentro del recuadro del ticket de ejemplo; la "X" marca
  lo elegido **en ese ejemplo**, no un mandato del proceso:
  - "Recaptcha Google Enterprise Invisible."
  - "MFA" → "Forzado por usuario" · "Forzado por la App" · "No utilizar MFA.  **X**"
  - "Scopes" → "Default: openid  **X**" · "Opcional: dn, email" · "Adicionales: ad_groups,
    email_alternativo"
  Es decir: el catálogo de scopes que ofrece el servicio es `openid` (default), `dn` y `email`
  (opcionales), y `ad_groups` y `email_alternativo` (adicionales). El uso de scopes
  adicionales se cruza con el campo "10. Justificación de scopes adicionales (si corresponde)"
  (pág. 13).
- **Un client id puede cubrir varios frontends** (pág. 14) — "Un mismo client id puede
  gestionar múltiples frontends desde un backend común. Ej, un sistema que tiene un backend
  pero tiene un frontend de cara al usuario final y otro frontend de cara al administrador
  podrá gestionarse la redirección hacia uno u otro desde un backend con el mismo client id."

---

## Almacenamiento (S3)

- **Si el sistema guarda archivos, va a S3 — sin alternativa declarada** (pág. 14) — "Siempre
  usamos S3 provisto por el equipo de Almacenamiento de datos del área de Infraestructura."
- **Hay que pedir bucket y credenciales** (pág. 14) — "Debemos solicitar la creación de un
  bucket para el sistema, y credenciales para acceder al mismo."
- **Canal** (pág. 14), textual: "Canal: NOC → Nueva Solicitud → Servicios Infra → Solicitud a
  Storage y Backup → ASI-DGINFRA-ALMACENAMIENTO DE DATOS". Ticket ejemplo: `1567809`.
- **Viñetas del modelo de ticket** (págs. 14-15) — **la fuente no las declara obligatorias**:
  son las viñetas del bloque "Modelo de ticket:" de la "Solicitud de bucket" y ninguna lleva
  marca de obligatoriedad (a diferencia de los campos 7 y 8 del ticket de OpenID, donde la
  fuente sí escribe "(obligatorio en PRD)" y "(recomendado)"). El modelo abre con "Se solicita
  la creación de un bucket en S3 DEV, para la nueva aplicación de Sistema de Gestión de
  Residencias." y sigue, textual: "Nombre sugerido del bucket: [Ej,
  Residencias. Nombrarlo en relación a la aplicación]" · "Cuota de espacio necesaria en GB:
  [Ej, 15gb]" · "Ministerio/Repartición/Secretaría. [Ministerio, Repartición y Secretaría de
  los dueños/cliente de la aplicación]" · "Nombre y correo electrónico de uno o más
  responsables técnicos para contactar por cualquier tema relacionado con el mismo. [Datos de
  Analistas Técnicos DGISIS y Gerencia]".
- **La convención de nombre del bucket es "en relación a la aplicación"** (pág. 14); el
  documento no fija un patrón formal ni un largo máximo.

---

## Integración: SADE

- **El primer paso es contactar al equipo de Integraciones** (pág. 15) — "Si durante el
  análisis del proyecto se identifica la necesidad de integrar con el sistema SADE, se deberá
  contactar al equipo de Integraciones. En ese primer acercamiento, es importante brindar una
  breve descripción del proyecto y detallar el objetivo de la integración, de modo que puedan
  orientar sobre los servicios más adecuados para cubrir la necesidad planteada."
- **El esquema de integración no lo elige el proyecto** (pág. 15) — "el equipo de
  integraciones evaluará el esquema de integración más conveniente. En función de las
  características de cada servicio, se determinará si la comunicación se realizará de forma
  directa con SADE a través del ESB, o bien mediante un esquema de interoperabilidad,
  consumiendo los servicios a través de XBA."
- **La documentación de los servicios la provee el equipo correspondiente** (pág. 15) — "Ya
  sea que se establezca por el ESB o por XBA, el equipo correspondiente nos compartirá la
  documentación de cada servicio, para realizar el análisis técnico, las pruebas necesarias y
  la posterior implementación de las integraciones."
- **Canal: Mail.** Los dos contactos con nombre y apellido están en la pág. 15 del PDF. No se
  transcriben en este extracto: el repo es público y son datos personales de terceros.

### Alta de usuario SADE

- **Doble prerrequisito** (pág. 15) — "Para poder ingresar al sistema SADE, es requisito
  contar previamente con un usuario de AD y, adicionalmente, con un usuario habilitado en
  SADE."
- **SADE tiene dos ambientes estables: "HML (Homologación)" y "PRD (Producción)"** (pág. 15).
- **Alta en PRD: por mail al ALS del área** (pág. 15) — "La solicitud de alta de usuario en
  producción debe solicitarse al ALS de nuestra área. / Canal: Mail".
- **Alta en HML: "Canal: Jira en el proyecto APPSADE."** Ticket ejemplo: `APPSADE-73592`
  (pág. 15).
- **Etiquetas obligatorias del ticket HML** (pág. 16), textual y palabra por palabra —
  "Recordar agregarle al ticket las etiquetas SGOGIYD - SGOGYD - SGOIYD - SGOYID para que el
  equipo correspondiente reciba el ticket en su bandeja."
  Las cuatro etiquetas son variantes ortográficas distintas y hay que poner **las cuatro**:
  `SGOGIYD`, `SGOGYD`, `SGOIYD`, `SGOYID`. La captura de pantalla de la misma página las
  muestra en ese mismo orden y con esa misma grafía.
- **Modelo de ticket** (pág. 16), textual: "Se solicita por favor, dar de alta los siguientes
  usuarios en SADE HML: / [Nombre completo] - [CUIL] - [Mail] / Por favor, copiar estructura
  jerárquica y permisos del perfil [CUIL del perfil a copiar]."
- **Sector y repartición son obligatorios** (pág. 16) — "Dado que es obligatorio informar el
  sector y la repartición, se podrá indicar el CUIL de un usuario existente para replicar
  dicha información, siempre que pertenezca a la misma área. En caso de no contar con un
  perfil de referencia, se deberán especificar explícitamente el sector y la repartición
  correspondientes para avanzar con la solicitud."

---

## Cambios masivos en JIRA

- **Ruta de la funcionalidad** (págs. 16-17), literales de la interfaz: entrar al proyecto y
  ubicar "Ver todas las incidencias y filtros" en la esquina superior derecha (pág. 16) → en
  la vista de listado, botón "Herramientas" en la esquina superior derecha (pág. 16) → dentro
  del menú, "Cambiar en bloque" → "todas las incidencias" (pág. 17) → seleccionar tickets con
  los checkboxes → "Siguiente" para elegir la acción (pág. 17).
- **Acciones masivas disponibles** (pág. 17) — **la enumeración es abierta**: la fuente dice
  "Las acciones disponibles para realizar de forma masiva incluyen:", no que sean todas. Los
  seis ítems que enumera, textuales: "Editar incidencias" · "Mover incidencias" ·
  "Transicionar incidencias" · "Archivar incidencias" · "Comenzar a observar incidencias" ·
  "Dejar de observar incidencias".

---

## Índice rápido de canales y tickets de ejemplo

Todos los valores de esta tabla están citados textualmente arriba, con su página.

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

---

## Contradicciones internas

1. **Nombre exacto del documento adjunto obligatorio.** El mismo entregable aparece con
   cuatro grafías distintas y en dos casos es un requisito formal:
   - pág. 5: "Se adjunta setup de proyecto." (minúsculas, dentro del modelo de ticket)
   - pág. 8: "Adjuntar el documento "Setup de Proyecto"." (bajo "Requisitos:")
   - pág. 11: ""Setup del proyecto"" (dos veces, dentro del modelo de ticket de entorno)
   - pág. 11: "Adjuntar el documento "Setup de proyecto" con el detalle de las tecnologías…"
     (bajo "Requisitos:")
   El documento no aclara si es un único documento con nombre inestable o documentos
   distintos. **No se resuelve acá.**

2. **Canal del pedido de base de datos.** La pág. 9 dice "Canal: JIRA" y da "Ticket ejemplo:
   1575108", un número desnudo. En todo el resto del documento el número desnudo corresponde a
   NOC (pág. 6 "NOC 1562237", pág. 7 "NOC 1595496", pág. 12 "1565975" con canal NOC, pág. 14
   "1567809" con canal NOC), mientras que los tickets de JIRA se citan siempre con key
   (ADHERR-7506, ADHERR-7537, ADHERR-7536, ADHERR-6448, APPRESI-7, APPSADE-73592,
   APPDECJUV2-2512). El canal declarado y el formato del ejemplo apuntan a sistemas distintos.
   **No se resuelve acá.**

3. **Ambientes de AD vs. ambientes de credenciales OpenID contra AD.** La pág. 6 afirma
   "Active Directory solo posee dos ambientes, HML y PRD." La pág. 12 afirma que la
   autenticación es "contra el Active Directory (AD) mediante el protocolo OpenID Connect" y
   que las credenciales "se pueden solicitar en un primer pedido: DEV, QA y HML." El documento
   no explica contra qué instancia de AD autentican los clients de DEV y QA. **No se resuelve
   acá.**

4. **Encabezados duplicados / referencias colgadas.** "Estándares de Desarrollo y Seguridad"
   aparece como línea suelta al final de la sección de Estimación (pág. 5) y otra vez como
   encabezado real de sección con cuerpo (págs. 11-12); el índice (pág. 3) lo lista una sola
   vez. "Alta de usuario en Active Directory (AD) (solo para usuarios nuevos)" aparece dos
   veces en la pág. 6: pegado al final del párrafo anterior y como encabezado real. Afecta a
   la citación: el mismo título identifica dos lugares distintos del documento.

5. **El documento anuncia contenido que no entrega.** La pág. 17 cierra con "A continuación,
   se detallan las principales tareas y situaciones en las que podrás participar, junto con
   una guía general sobre cómo abordarlas." y el documento termina en esa misma página, sin
   detallar ninguna. La sección "Mantenimiento de Producto" queda declarada en el índice
   (pág. 3) y abierta en el cuerpo, pero sin procedimiento.
