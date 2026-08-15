---
name: dev-seguridad
description: Use when writing or reviewing code that handles user data, sessions, login, roles or permissions, form and API validation, file upload or download, error messages, logs or health endpoints in a GCBA application — and when preparing a security assessment, completing the WAF form, assembling the entregables the security team asks for, or working out what still blocks a build from moving to QA, homologación or producción (HML/PRD), including hotfix releases and SAST/DAST/dependency-scanning failures.
---

# Seguridad exigible al escribir código

El estándar de seguridad de la ASI es el ES0902 y se complementa con el de desarrollo, el ES0901. No
es una guía de buenas prácticas: "todos los sistemas que se desarrollen en el ámbito de los proyectos
de GCABA deben respetar la totalidad de los criterios aquí descriptos" —la única salida es un acuerdo
distinto por contrato **con aprobación de la ASI**— y aplica igual a software comercial, de terceros y
open source (ES0902 pág. 3).

Los checks del harness ya cubren lo mecánico: `dev-dependencias` (rangos de versión), `dev-api-rutas`,
`dev-infra-en-codigo` —la regla de referenciar servidores por nombre DNS "jamás por su dirección IP"
(ES0901 pág. 9)— y `dev-accesibilidad-html`. Acá va el resto.

## Validaciones y datos del usuario

- **Vu5 — toda validación del lado del cliente debe estar espejada del lado del servidor** (ES0902
  pág. 7). El ES0901 lo repite: "Las validaciones se realizan con control duplicado, por frontend y
  backend" (P5, ES0901 pág. 13). Una validación que sólo vive en el formulario es incumplimiento.
- **Vu2 — "Todo dato sensible no puede ser enviado en texto plano"** (ES0902 pág. 7). El documento
  **no define qué es un dato sensible**: si el caso es dudoso, se pregunta.
- **Vu9 — lo público también se controla** (ES0902 pág. 7): "Las aplicaciones que expongan
  funcionalidades accesibles sin autenticación a través de interfaces públicas (web o API), deberán
  contemplar mecanismos de control de uso que mitiguen riesgos por consumo excesivo o automatizado de
  recursos". No nombra técnica ni umbral.
- **El navegador no guarda nada** — "en los navegadores no debe residir ningún dato, tabla, archivo o
  documento excepto durante el tiempo que dure una transacción" (ES0901 pág. 7).
- **El volumen de información transferida tiene que estar controlado** (C1, ES0901 pág. 13), y la app
  se conecta a la base "con los mínimos permisos necesarios para ejecutar las transacciones" (ES0901
  pág. 9).

## Sesión, autenticación y roles

- **Vu1 — toda página de autenticación con captcha _o_ bloqueo por intentos de sesión** (ES0902
  pág. 7). Es alternativa, no acumulativa. Dice que la funcionalidad "se encuentra contenida en
  OpenID", pero no que quede satisfecha sola: la obligación sigue siendo de la aplicación.
- **Vu3 — cerrar la ventana o el browser no puede dejar la sesión activa** (ES0902 pág. 7).
- **Vu4 — toda sesión en stand by tiene que tener un tiempo límite**, "independientemente del límite de
  tiempo que posee el token de autenticación del OpenID" (ES0902 pág. 7). **El documento no fija el
  valor**: exige que el límite exista, no dice cuál. No inventes un número.
- **Vu8 — "Los perfiles de usuarios armados en las aplicaciones deben respetar los roles asignados"**
  (ES0902 pág. 7).
- **OpenID Connect con Keycloak, obligatorio** (ES0902 pág. 3): es "el proveedor autorizado y
  obligatorio de identidad" en los entornos del GCABA, gestionado por la DGSEI. La aplicación debe
  integrarse con los flujos adecuados de OpenID, registrarse en el servidor correspondiente y respetar
  las políticas de autenticación, autorización y protección de recursos de la ASI. Sobre el OpenID
  anterior (`https://oauth2-server.apps.buenosaires.gob.ar/`) ya no se dan credenciales: las nuevas
  versiones redirigen a `https://identidad-gcaba.apps.buenosaires.gob.ar/`. Lo que interactúa con el
  ciudadano se autentica con BAID en el frontend (ES0901 pág. 18); lo que no es de uso directo del
  ciudadano pasa por el Active Directory del GCABA (ES0901 pág. 19).
- **La asignación de roles la hace la aplicación** (ES0902 pág. 4), "pudiendo utilizar grupos de AD de
  ser necesario", y acotar por árbol o membresías es **recomendación**, no obligación — ojo con los
  verbos. Lo que sí obliga: los permisos y roles "deberán asignarse desde un backoffice de la misma"
  aplicación (ES0901 pág. 19), y los servicios "deben estar protegidos con sistema de token" (D8,
  ES0901 pág. 13).

## Subida y manejo de archivos

- **D7 — si la aplicación gestiona archivos, van al storage estándar del GCABA** (ES0901 pág. 13): "No
  está permitido guardar en forma permanente archivos en forma local. Para los casos temporales la
  destrucción de los mismos debe ser en forma inmediata". Que ese repositorio de adjuntos sea S3 es
  otra regla, en otra página: "La tecnología actual está basada en el protocolo S3 (Simple Storage
  Service)" (ES0901 pág. 19) — el documento no la rotula como D7.
- **En OpenShift no hay disco**: "No está permitido utilizar almacenamiento local, ya que se utiliza el
  concepto de contenedores efímeros" (ES0901 pág. 38). En el servidor de aplicaciones sólo quedan logs
  de debug y temporarios "que pierdan su valor al terminar la transacción que los genera" (ES0901
  pág. 11).
- **Estructura de carpetas** (ES0901 págs. 19-20): planificarla antes de almacenar; evitar concentrar
  tráfico en una sola carpeta; si se guarda por fecha y hora, usar `año / mes / día / hora / minuto /
  segundo`; equilibrar ancho y profundidad; **máximo 20 niveles** —"No crear estructuras de carpetas
  que tengan más de 20 niveles de profundidad." (pág. 19)—; y "Evitar colocar una gran cantidad de
  objetos (más de 100,000) en una sola carpeta" (pág. 20), que con ese verbo es pauta y no
  prohibición.
- **Los archivos subidos por usuarios van al `.gitignore`**, con los de configuración y todo lo que no
  forme parte del proyecto (ES0901 pág. 27). Sumar carga o descarga de archivos **dispara un assessment
  nuevo** (ES0901 pág. 42).

## Mensajes de error

- **Vu6 — "Todos los mensajes de error deben estar customizados"** (ES0902 pág. 7).
- **Vu7 — "Todo el software de base debe estar configurado para no entregar datos privados"** (ES0902
  pág. 7). El documento no enumera qué cuenta como dato privado.
- **Un error no puede filtrar infraestructura**: ante un error inesperado "no debe visualizarse por
  frontend/backend/API características del servidor, IP, path o cualquier información que permita
  conocer propiedades de infraestructura" (ES0901 pág. 22).
- **El código de estado no se disfraza**: hay que "evitar enmascarar los mensajes de error HTTP de
  forma tal que los balanceadores / proxys puedan entender el estado actual del aplicativo"; ante un
  error del aplicativo "la respuesta HTTP de estado debe ser código 500 y el mismo no debe reemplazarse
  por ningún otro código" (ES0901 pág. 22). Customizás el cuerpo; el código queda como está.
- **Los endpoints `/health/liveness` y `/health/readiness` son obligatorios y "no deben exponer datos
  sensibles"** (ES0901 pág. 40). El health check es requisito **excluyente** para homologar y pasar a
  producción (ES0901 pág. 22 y pág. 40).

## Logs y auditoría

- **Los logs no se pueden apagar** — se almacenan remotamente en el repositorio administrado por la ASI
  y los sistemas "no deberán tener ningún archivo de configuración, ni comando alguno o transacción que
  permita deshabilitar la existencia de estos Logs" (ES0901 pág. 10).
- **M1 — logueo estándar con errores, alertas y registro de transacciones core** que permita medir la
  salud del sistema; "El nivel de logueo debe poder parametrizarse sin requerir un despliegue" (ES0901
  pág. 14). Las excepciones se capturan y registran según el estándar de la tecnología, y el GCABA
  centraliza en el stack ELK (ES0901 pág. 23).
- **C3 — los procesos de auditoría se depuran desde un backoffice y con acceso restringido**, teniendo
  en cuenta las fechas de registración (ES0901 pág. 13).
- **Las variables de entorno van en un archivo externo al código** — bases de datos, servicios
  externos, URLs, protocolos, paths (M2, ES0901 pág. 14).

## Lo que corre solo en el pipeline

Cada proyecto Git tiene asociados Code Quality, SAST, DAST —basado en OWASP Zed Attack Proxy, ZAP— y
Dependency Scanning, activados por los commits y tags según la tecnología (ES0901 págs. 27-28); la
integración continua ya corre detección de vulnerabilidades sobre el código y sobre la app implementada
en DEV (ES0901 pág. 5).

SAST por lenguaje (ES0901 pág. 27): .NET → Security Code Scan · C/C++ → Flawfinder · Go → Gosec ·
Groovy, Java y Scala (Ant, Gradle, Maven, SBT) → find-sec-bugs · JavaScript → ESLint security plugin ·
Node.js → NodeJsScan · PHP → phpcs-security-audit · Python → bandit · Ruby on Rails → brakeman ·
TypeScript → TSLint Config Security. Dependency Scanning (ES0901 pág. 28): gemnasium siempre, más
Retire.js en JavaScript (npm) y bundler-audit en Ruby (gem); en Python (pip) **sólo se admite
`requirements.txt`**.

De Ve1 —sólo herramientas y versiones homologadas por la ASI (ES0902 pág. 8)— se ocupa
`dev-dependencias`; dos reglas vecinas necesitan a una persona: Ve2, "antes de utilizarlas se debe
consensuar con el área de Infraestructura si está permitido su uso" para las versiones indicadas como
más seguras (ES0902 pág. 8), y la declaración de bibliotecas externas al pedir el pase a Producción
—nombre, versión, sistema dependiente y servidores—, porque la ASI cruza contra esa matriz las
vulnerabilidades publicadas (ES0901 pág. 10). Y "bajo ningún concepto se aceptarán versiones 'beta' de
ningún paquete de software" (ES0901 pág. 10).

**Vu10 fija la referencia** (ES0902 pág. 7): web `https://owasp.org/www-project-top-ten/` · APIs y web
services `https://owasp.org/www-project-api-security/` · mobile
`https://owasp.org/www-project-mobile-top-10/`. La revisión de código de la ASI incluye "Controles
estáticos de OWASP" (ES0901 pág. 24).

## El assessment: la compuerta antes de HML y PRD

- **Es obligatorio y se hace en QA** — "El assessment de seguridad es un control obligatorio que debe
  cumplirse antes de que una aplicación pase a ambientes superiores (HML y PRD). Se realiza en el
  ambiente de QA", y "Todo desarrollo debe contar con un assessment aprobado para poder avanzar hacia
  homologación y producción" (ES0901 pág. 42). En el ES0902 es condición de calidad: "Las aplicaciones
  homologadas deben tener el aprobado a nivel seguridad en el ambiente QA" (C2, ES0902 pág. 4).
- **Se repite cuando** (ES0901 pág. 42): hay desarrollo y pasaron más de 20 días desde el anterior; hay
  correcciones de vulnerabilidades detectadas previamente (assessment parcial); ocurre un incidente de
  seguridad; o hay desarrollo con cambios en funcionalidades y/o endpoints dentro de esos 20 días.
- **Motivos para pedir uno nuevo** (ES0901 pág. 42), en cinco grupos: **1)** endpoints y
  funcionalidades —alta o modificación de endpoints, baja de secciones de frontend o backend, cambios
  en parámetros de formularios o APIs—; **2)** integraciones y recursos externos —APIs externas,
  servicios de terceros, webhooks, iframes o embeds, scripts de terceros: trackers, analytics,
  chatbots—; **3)** configuraciones y controles de seguridad —CORS, CSP, cookies, creación o
  modificación de roles y permisos—; **4)** dependencias e infraestructura —agregar o actualizar
  bibliotecas, frameworks, SDKs, migrar de infraestructura, cambiar protocolos—; **5)** funcionalidades
  críticas —carga o descarga de archivos, cambios en flujos sensibles y "Modificación en el flujo de
  autenticación (login, registro, recuperación de contraseña)"—.
- **Umbral de aprobación (G2, ES0902 pág. 8)** — "Las aplicaciones se aprobarán, a nivel seguridad, si
  las vulnerabilidades detectadas son de una categoría de riesgo bajo, siempre y cuando no supere la
  cantidad de 10 vulnerabilidades de esta categoría." Condición doble: **todas** de riesgo bajo **y** no
  más de 10. Es el único umbral numérico del ES0902.
- **Cumplir las Vu y las Ve no garantiza nada** — "el cumplimiento del punto 6 no asegura la aprobación
  de un assessment de seguridad" (G1, ES0902 pág. 8), y el punto 6 es justamente Vu1–Vu10 y Ve1–Ve2.
- **Reenvío y re-análisis** (ES0902 pág. 8): al reenviar se controla el 100% de las vulnerabilidades
  informadas, pero se aprueba por G2 (G3); al reanalizar una versión con informe previo "se procederá a
  un control total", así que pueden aparecer nuevas y también rige G2 (G4).
- **Qué entregar según el activo** — "se deberá proveer de los elementos que se necesiten de acuerdo al
  tipo de activo" (ES0902 págs. 6-7):
  - **Web Services**: Estructura (todos los métodos y ejemplos específicos de su uso), Datos (los
    necesarios para su utilización) y Servicio (tipo —SOAP, RESTful— e integraciones).
  - **Aplicaciones Web**: Especificaciones (URL o IP; usuarios con todos los roles que maneje la
    aplicación) y Documento de Arquitectura (descripción de los servicios, descripción de
    integraciones, modelo lógico y físico de datos, arquitectura tecnológica).
  - **Aplicaciones Mobile**: lo mismo, con APK en lugar de URL o IP.
  - **Servidores**: IP y usuario administrador, más Documento de Arquitectura con descripción de los
    servicios y arquitectura tecnológica — el único que **no** exige integraciones ni modelo de datos.
  - **Totem**: activo físico y usuarios con todos los roles, más Documento de Arquitectura completo
    (servicios, integraciones, topología y modularización, modelo lógico y físico de datos, políticas
    globales de diseño, arquitectura tecnológica y dimensionamiento).
  - Las **aplicaciones y servicios web** suman el formulario de WAF "suministrado por el equipo de
    Prevención" (ES0902 pág. 6).
- **Cómo se pide y cómo vuelve**: el control tiene dos actividades, "el primero se realizará por
  intermedio de un sistema automatizado y el segundo mediante un circuito interno de la DGSEI" (ES0902
  pág. 5). ⚠️ **Ese circuito existe únicamente dentro de una imagen sin capa de texto en la pág. 5**;
  lo que sigue es transcripción visual, no texto citable: el pedido se genera vía ticket NOC y va al
  Responsable de Seguridad Informática de la DGSEI, que asigna un analista; el ticket se deja resuelto
  adjuntando el informe, con resultado Aprobado o Desaprobado; se emite CCOO si es el primer assessment,
  si cambia el resultado respecto del anterior o si no existe CCOO en los anteriores. Si va a quedar
  escrito en un ticket o en un criterio de aceptación, abrí la pág. 5 del PDF.

## Lo que hay que ir a buscar al PDF

- **El contenido de los ocho anexos del ES0902 (A a H), citados en la pág. 5.** Ninguno está en ese PDF
  de 8 páginas: el pedido vía ticket NOC (A), las recomendaciones de seguridad periódicas (B, G, H, F),
  el Circuito Administrativo Interno completo (C), el proceso y las herramientas por tipo de activo (D)
  y las estadísticas (E). **El documento tampoco dice quién los custodia ni a quién se los pide.**
- **Qué "Proceso" y qué "Herramientas" corresponden a cada activo** (ES0902 pág. 5). Las seis columnas
  del diagrama —Sensores, Infraestructura, Mobile, Totem o ATM's, Web Services, Web— tienen cajas
  rotuladas "Proceso" y "Herramientas" **sin contenido**; remiten al Anexo D.
- **Los umbrales de las demás categorías de riesgo.** El ES0902 sólo fija el de riesgo bajo (G2,
  pág. 8). No define medio, alto ni crítico, ni enumera las categorías existentes.
- **El "sistema automatizado" de control, y qué son CCOO y el ticket NOC.** Lo primero se anuncia como
  una de las dos actividades y no se describe en ninguna página (ES0902 pág. 5); lo segundo aparece en
  el diagrama y el documento no lo define en ningún lado. No inferirlo.
- **Qué constituye un "dato sensible" (Vu2) y cuál es el tiempo límite de sesión (Vu4).** Ninguno de
  los dos está en el documento (ES0902 pág. 7). Se preguntan, no se completan.
- **Las tablas de versiones del Anexo II del ES0901 (págs. 30-37).** Cinco de ellas quedaron con las
  columnas o las filas corridas en la conversión a texto —la peor es Framework Frontend, pág. 31;
  también Biblioteca Java pág. 33, Angular pág. 34 y LMS/DMS págs. 35-36—; del resto el extracto no
  dice que estén corridas. Un número tomado de una de esas cinco se lee perfectamente bien y es falso:
  se leen del PDF.
- **Los diagramas del ES0901 sin capa de texto**: el proceso de gestión de cambios (fig. 1, pág. 4) y
  el flujo de login y registro de BA ID (pág. 18), que vive sólo en esa imagen. Antes de derivar de ahí
  un requerimiento de autenticación, releé la pág. 18.

## Contradicciones sin resolver

1. **El assessment del hotfix: antes o después de producción.**
   - ES0901 pág. 42 (Anexo V): "El assessment de seguridad es un control obligatorio que debe cumplirse
     **antes** de que una aplicación pase a ambientes superiores (HML y PRD)", y "Todo desarrollo debe
     contar con un assessment aprobado para poder avanzar hacia homologación y producción."
   - ES0901 pág. 29 (Anexo I, versiones HOTFIX): "Dado que los tiempos de despliegue en producción
     deben ser inmediatos, a este tipo de versión se le realizará el assessment **a posteriori** del
     despliegue productivo. Dicho assessment se realizará en el ambiente de QA."
   - El Anexo V no contempla la excepción del hotfix y el Anexo I no remite al Anexo V. Lo que sí está
     claro en la pág. 29: el hotfix sale siempre de una versión ya productiva, sólo corrige lo que no
     permite funcionar al ambiente productivo, sin funcionalidades nuevas ni cambios mayores, y en el
     ticket "se deberá especificar el motivo por el cual se considera a la versión como un HOTFIX".
2. **Cuántos ambientes hay y cómo se llaman.** ES0901 pág. 3 (C2): "desarrollo, pruebas, homologación y
   producción (DEV, QA, HML y PRD)" — cuatro. ES0901 pág. 9: "Entorno de Desarrollo. Entorno de
   Testing. Entorno de Homologación. Entorno de Producción." — cuatro, con Testing en lugar de QA.
   ES0901 pág. 38 (Anexo III): OpenShift provee "Desarrollo, **Calidad**, Homologación, **Producción
   Interna y Producción DMZ**" — cinco. Importa porque el assessment se define "en QA" y la compuerta
   es "antes de HML y PRD": al pedir un pase, nombrá el ambiente como lo nombra el equipo que lo opera
   y dejá asentada la equivalencia.
