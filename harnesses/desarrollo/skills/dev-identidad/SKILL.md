---
name: dev-identidad
description: Use when implementing or reviewing login, logout, session handling, tokens, roles or permissions in a GCBA / DGISIS application — wiring OpenID Connect against Keycloak, integrating BA ID / miBA for citizens or Active Directory for internal users, choosing where the session lives, setting session or token expiry, building the roles-and-permissions backoffice, deciding which endpoints stay public, or filling in the authentication section of the architecture document or the API contract.
---

# Autenticación, sesión y permisos

Todo lo que sigue sale del **ES0901 — Estándar de Desarrollo ASI v6.3** y del **ES0902 —
Estándar de Seguridad v6.2**. Aplican a todas las aplicaciones del GCABA, incluidas las
compradas y las de terceros. **El cumplimiento es total**: apartarse de un punto exige acuerdo
por contrato con aprobación de la ASI, no es decisión del equipo (ES0901 pág. 3; ES0902
pág. 3).

Cuando el estándar no define algo, acá dice **"no lo fija"**. Eso no habilita a completar con
buenas prácticas de la industria: es una definición pendiente que se pide y se documenta.

## La autenticación nunca es propia

- **Toda aplicación necesita autenticación si el acceso a sus funcionalidades o datos
  requiere identificar usuarios.** Sólo pueden permitir acceso anónimo las que publiquen
  **exclusivamente** información pública (ES0901 pág. 3, C1).
- **Las credenciales no se ingresan en tu aplicación.** "Toda autenticación en las
  aplicaciones del GCABA deberá delegar el ingreso de credenciales de usuarios" (ES0901
  pág. 12, D2). De ahí se sigue que no hay pantalla propia de usuario y contraseña.
  **Hasta ahí llega la norma**: ni ES0901 ni ES0902 dicen nada sobre almacenar contraseñas ni
  sobre flujos propios de recuperación — no lo fijan. Al contrario, ES0901 pág. 42 enumera
  "Modificación en el flujo de autenticación (login, registro, recuperación de contraseña)"
  entre los motivos de assessment, o sea que contempla que ese flujo pueda existir dentro del
  alcance de la aplicación. Si tu diseño necesita uno, se pregunta: no está ni prohibido ni
  autorizado por estos dos documentos.
- **El protocolo es OpenID Connect** y el proveedor de identidad es **Keycloak, gestionado
  por la DGSEI**: "el proveedor autorizado y obligatorio de identidad para la implementación
  de OpenID en los entornos del GCABA" (ES0902 pág. 3, C1; ES0901 pág. 19).
- **El OpenID viejo está cerrado.** "No se brindarán credenciales sobre el anterior OpenID
  (`https://oauth2-server.apps.buenosaires.gob.ar/`)"; las nuevas versiones redirigen a
  `https://identidad-gcaba.apps.buenosaires.gob.ar/` (ES0901 pág. 19; ES0902 pág. 3). Si
  encontrás la URL vieja en el código o en un config, es deuda: hay que migrar.
- **Tres obligaciones, textuales, de la aplicación** (ES0902 pág. 3; ES0901 pág. 19):
  integrarse con Keycloak "utilizando los flujos adecuados de OpenID"; **registrarse en el
  servidor correspondiente**; y respetar "las políticas de autenticación, autorización y
  protección de recursos definidas por la ASI".
- **Los servicios se protegen con token** (ES0901 pág. 13, D8). El estándar no nombra formato
  ni algoritmo.

## Ciudadano: BA ID / miBA

- **Si hay interacción con el ciudadano, el frontend va con BAID**: "Toda aplicación que
  genere una interacción con el ciudadano debe contar con la autenticación con BAID en su
  frontend" (ES0901 pág. 18) — es **la autenticación única de ciudadano del GCABA** (ES0901
  pág. 12, D1). El servicio lo provee **miBA**, "siguiendo las especificaciones de OpenID
  Connect" (ES0901 pág. 18).
- **El flujo concreto —login, registro, completar datos faltantes, autorización— no está
  escrito en ninguna parte del texto del estándar.** Vive únicamente en el diagrama de la
  **pág. 18 del PDF de ES0901**. Antes de derivar un solo requerimiento de ese flujo, abrí la
  página. Ver la sección de abajo.
- **Mobile no queda afuera**: todo diseño mobile debe "integrarse con los mecanismos de
  autenticación aprobados por el GCABA", híbridas incluidas (ES0901 pág. 17).

## Agente interno: Active Directory

- **Todo lo que no es de uso directo del ciudadano pasa por AD**: "Toda aplicación o
  autenticación que no sea de uso directo del ciudadano debe pasar por el Active Directory
  del GCABA. Es decir, debe autenticar contra el directorio de GCBA delegando el ingreso de
  las credenciales en el portal de autenticación del OpenID administrado por la DGSEI"
  (ES0901 pág. 19).
- El criterio literal es **"de uso directo del ciudadano"** (ES0901 pág. 19): el backoffice de
  una aplicación ciudadana cae de este lado, porque lo operan agentes.
- **Ojo con los verbos.** Usar grupos de AD es potestativo —"pudiendo utilizar grupos de AD de
  ser necesario"— y acotar el acceso por ubicación en el árbol de AD o por membresías es
  **recomendación**, no obligación: "Se recomienda acotar la autenticación del usuario en base
  a su ubicación en el árbol de AD o por membresías de grupos" (ES0901 pág. 19; ES0902 pág. 4).
  No lo escribas como requisito duro en una HU ni en el documento de arquitectura.

## Configuración por ambiente

- **Nada de esto va hardcodeado.** Las variables de entorno —"bases de datos, servicios
  externos, URLs, protocolos, paths, etc."— van en un archivo externo al código (ES0901
  pág. 14, M2). El issuer, el `client_id`, los redirect URI y el secret del cliente son eso.
- **La imagen se construye una sola vez en Calidad y se promueve sin modificaciones**; cada
  ambiente aplica su configuración por variables externas —"config maps, secrets u otros
  mecanismos de inyección de configuración"— (ES0901 pág. 38). Si tu login necesita un build
  distinto por ambiente, el diseño está mal. El YAML de variables es obligatorio y su ruta se
  informa en el `README.md` (ES0901 pág. 38).
- **Al IdP se le pega por nombre DNS, jamás por IP**: toda referencia a un servidor se hace
  "por su nombre DNS, jamás por su dirección IP" (ES0901 pág. 9). El check
  `dev-infra-en-codigo` ya marca las IPs literales.
- La app "debe estar preparada para funcionar bajo protocolo HTTPS (protocolos relativos)"
  (ES0901 pág. 14, M2). Y hay techo de 30 segundos: "Toda petición o servicio expuesto por la
  aplicación debe responder en menos de 30 segundos. En caso contrario, la plataforma OpenShift
  finalizará la solicitud por timeout" (ES0901 pág. 21). **El sujeto son las peticiones que la
  aplicación expone** —tu endpoint de callback del IdP entre ellas—, no las llamadas salientes
  de tu app hacia el IdP: para ésas el estándar no fija techo.

## Sesión y tokens

- **La sesión no puede vivir en la memoria de una instancia.** Los servidores de aplicación de
  una granja "serán entre sí totalmente independientes, es decir que no emplearán ningún
  mecanismo de acoplamiento entre ellos", con balanceo Round Robin (ES0901 pág. 9), y la
  escalabilidad horizontal se exige con servidores "granjeables y stateless" (ES0901 pág. 22).
  Consecuencia directa: cualquier diseño que suponga que el usuario vuelve al mismo pod está
  fuera de norma.
- **Tampoco en el servidor de aplicaciones**: "no se debe almacenar ninguna información
  relevante en los servidores de aplicaciones. Solo podrán almacenarse en el servidor de
  aplicación los logs de debug y archivos temporarios que pierdan su valor al terminar la
  transacción que los genera" (ES0901 pág. 11). Y en OpenShift "no está permitido utilizar
  almacenamiento local, ya que se utiliza el concepto de contenedores efímeros" (pág. 38).
- **Y tampoco en el navegador**: "en los navegadores no debe residir ningún dato, tabla,
  archivo o documento excepto durante el tiempo que dure una transacción. Toda información
  deberá ser almacenada en servidores específicos" (ES0901 pág. 7). Cualquier cosa que dejes
  del lado del cliente tenés que poder justificarla contra esa frase.
- El estándar **no fija** dónde vive la sesión. Lo único que sí fija: para caché de datos
  "deben utilizarse los servicios de Redis provistos por la Agencia" (ES0901 pág. 21).
- **Cerrar el browser tiene que matar la sesión**: "Toda aplicación que se cierra a través de las
  ventanas o en forma directa del browser, no debe dejar la sesión activa" (ES0902 pág. 7, Vu3).
- **La sesión en stand by tiene que tener un límite de tiempo**, "independientemente del límite
  de tiempo que posee el token de autenticación del OpenID" (ES0902 pág. 7, Vu4). Son dos relojes
  distintos y **ningún documento fija el valor de ninguno**: ver contradicción 2.
- **Ningún dato sensible viaja en texto plano** (ES0902 pág. 7, Vu2). El documento no define
  qué es "dato sensible": si tu caso es dudoso, se pregunta, no se decide.

## Roles y permisos

- **Los roles los asigna tu aplicación, no el IdP**: "La asignación de roles a los usuarios es
  una función que queda delegada a la propia aplicación" (ES0901 pág. 19; ES0902 pág. 4).
- **Y se asignan desde un backoffice de la propia aplicación**: "Los permisos y roles en el
  marco de la aplicación deberán asignarse desde un backoffice de la misma" (ES0901 pág. 19).
  No por script, no por INSERT a mano, no por ticket a infraestructura.
- **Los perfiles armados en la aplicación deben respetar los roles asignados** (ES0902 pág. 7, Vu8).
- **Las validaciones del cliente se espejan en el servidor** (ES0902 pág. 7, Vu5; ES0901
  pág. 13, P5). Un menú que esconde un botón no es un permiso: el permiso se verifica en el
  backend.
- **La auditoría se depura desde un backoffice y con acceso restringido**, teniendo en cuenta
  las fechas de registración (ES0901 pág. 13, C3).
- **El Manual de Usuario documenta las funcionalidades de todos los roles y la administración
  de roles, permisos y seguridad** (ES0901 pág. 7). Es entregable, no opcional.

## La pantalla de login, los errores y lo que se loguea

- **Captcha o bloqueo por intentos**: "Toda página de autenticación debe contener captcha o
  bloqueo de usuarios por intentos de sesión, funcionalidad que se encuentra contenida en
  OpenID" (ES0902 pág. 7, Vu1). Es alternativa, no acumulativa — y ver contradicción 3 antes
  de darla por resuelta.
- **Todos los mensajes de error deben estar customizados** (ES0902 pág. 7, Vu6).
- **El error no puede filtrar infraestructura**: "Ante un error inesperado no debe visualizarse
  por frontend/backend/API características del servidor, IP, path o cualquier información que
  permita conocer propiedades de infraestructura". Y no se enmascara el código: si hay error,
  la respuesta es 500 y "no debe reemplazarse por ningún otro código" (ES0901 pág. 22).
- **Endpoints públicos sin autenticación**: si exponés funcionalidad accesible sin login por
  web o API, tenés que contemplar "mecanismos de control de uso que mitiguen riesgos por
  consumo excesivo o automatizado de recursos" (ES0902 pág. 7, Vu9). **No nombra la técnica ni
  fija umbral.**
- **Logueo obligatorio de transacciones core, con nivel parametrizable sin desplegar** (ES0901
  pág. 14, M1). No puede existir configuración ni comando que permita deshabilitar los logs
  (ES0901 pág. 10).
- La pantalla de login es pantalla: aplica responsive (ES0901 pág. 12, D4) y la revisan
  `dev-accesibilidad-html` y `dev-api-rutas` como a cualquier otra.
- Referencia que el propio estándar manda tener en cuenta: OWASP Top Ten y API Security
  (ES0902 pág. 7, Vu10).

## Antes de mandar a QA

- **Tocar identidad dispara un assessment nuevo.** Son motivos explícitos: "Modificación en el
  flujo de autenticación (login, registro, recuperación de contraseña)" y "creación o
  modificación de roles y permisos", además de alterar políticas de CORS, CSP o cookies. El
  assessment es control obligatorio previo a HML y PRD, y se realiza en QA (ES0901 pág. 42) —
  pero el mismo documento manda el assessment del hotfix **después** del despliegue productivo:
  ver contradicción 4, que cae de lleno sobre identidad.
- **Lo que hay que entregar para que te lo revisen** (ES0902 pág. 6, tabla E2 — Aplicaciones
  Web): URL o IP, **"Usuarios con todos los roles que se manejen en la aplicación a revisar"**,
  y el Documento de Arquitectura con descripción de servicios e integraciones. Preparar los
  usuarios de prueba por rol es parte del trabajo de identidad, no un pedido de último momento.
- Además, para aplicaciones y servicios web, **se completa el formulario de políticas de WAF**
  suministrado por el equipo de Prevención (ES0902 pág. 6). Se aprueba sólo si **todas** las
  vulnerabilidades detectadas son de riesgo bajo **y** no superan las 10 (ES0902 pág. 8, G2).

## Lo que hay que ir a buscar al PDF

- **Flujo completo de BA ID — ES0901, pág. 18.** Es una imagen sin capa de texto y sin
  epígrafe. **Todo el flujo de login y registro de BAID vive sólo ahí**: el cuerpo del texto no
  lo describe en ninguna página. Del render se adivinan una cadena Usuario → Web Cliente → miBA,
  ramas de Login y Registro y un paso de completar información antes de la autorización, pero
  **eso no es especificación citable**. Antes de implementar el alta de ciudadano, abrí la
  página y leela.
- **Versiones homologadas de OpenID Connect y de Keycloak — ES0901, Anexo II, págs. 36-37.**
  El estándar no publica número: la nota al pie dice que "las versiones homologadas de estas
  herramientas serán provistas por la DGSEI al momento de ser requeridas para un fin
  específico". Se piden, no se suponen.
- **Versiones de las bibliotecas de token y de permisos — ES0901, Anexo II, pág. 34.** Cinco
  tablas del Anexo II se convirtieron a texto con las columnas o las filas corridas —"Framework
  Frontend" (pág. 31), "Biblioteca Java" (pág. 33), "Biblioteca Angular" (pág. 34), "LMS"
  (pág. 35) y "DMS" (pág. 36)—: un número copiado del texto extraído de ésas se lee perfecto y
  es falso. `ngx-permissions` cae justo ahí, en "Bibliotecas Angular". `jwt-decode` y `JOSE`
  están en "Bibliotecas JavaScript" (pág. 34), que **no** figura entre las corridas — no las
  metas en la misma bolsa. Igual, antes de fijar un rango para cualquiera de las tres, abrí la
  página del PDF. El check `dev-dependencias` compara rangos, pero contra la tabla que le
  cargues: si el número de origen está mal, el check confirma un error.
- **Anexos A a H de ES0902 (pág. 5).** El circuito de assessment los referencia, pero ninguno
  está en el PDF de 8 páginas y el documento no dice quién los custodia. No lo infieras.

## Contradicciones sin resolver

Están registradas, no resueltas. **Elegir un lado en silencio es inventar una norma**: si tu
diseño depende de una de estas, preguntá antes de construir.

1. **Keycloak "en todos los casos" vs. BAID para el ciudadano.**
   Lado A (ES0902 pág. 3, C1): "En todos los casos, el proveedor autorizado y obligatorio de
   identidad para la implementación de OpenID en los entornos del GCABA es Keycloak, gestionado
   por la DGSEI." Ni "BAID" ni "miBA" aparecen en ninguna de las 8 páginas de ES0902 — verificado
   sobre el PDF completo, no derivado del extracto.
   Lado B (ES0901 págs. 18-19): el ciudadano va por BAID, con miBA proveyendo el servicio
   "siguiendo las especificaciones de OpenID Connect", y la obligación de Keycloak aparece
   acotada a "las aplicaciones que no poseen interacción con el ciudadano".
   Es tensión **entre documentos**: ninguno la registra como contradicción interna, porque cada
   uno mira sólo el suyo. Si tu aplicación tiene frente ciudadano y backoffice, no supongas que
   es un solo proveedor ni que son dos: preguntá.

2. **Vigencia de la sesión y vigencia del token: dos relojes, ningún número.**
   Lado A (ES0902 pág. 7, Vu4): la sesión en stand by "tiene que tener un tiempo límite para su
   utilización", y ese límite es explícitamente independiente del que "posee el token de
   autenticación del OpenID" — o sea, el estándar afirma que el token tiene vencimiento y exige
   además uno de sesión.
   Lado B: **ninguno de los dos documentos fija un valor**, ni para la sesión ni para el token.
   El reloj del token lo corre un Keycloak que gestiona la DGSEI, no tu equipo (ES0901 pág. 19),
   y lo único que el Anexo II dice de OIDC y Keycloak es que sus versiones homologadas "serán
   provistas por la DGSEI al momento de ser requeridas" (ES0901 pág. 37).
   No inventes un número ni lo copies de otro proyecto: se pide el valor del token a la DGSEI,
   se acuerda el de la sesión y los dos quedan escritos en el documento de arquitectura.

3. **Quién implementa el captcha o el bloqueo por intentos.**
   Lado A (ES0902 pág. 7, Vu1): la funcionalidad "se encuentra contenida en OpenID" — leído
   suelto, no la implementás vos.
   Lado B: Vu1 no dice que quede satisfecha automáticamente; la obligación de que la página de
   autenticación la tenga sigue siendo de la aplicación, que además delega esa página en el
   portal de la DGSEI (ES0901 pág. 19). ES0902 lo registra como observación, no como contradicción
   declarada: verificá contra el portal que el mecanismo esté activo antes de darlo por cumplido.

4. **El assessment del hotfix: antes o después de producción.**
   Lado A (ES0901 pág. 42, Anexo V): "El assessment de seguridad es un control obligatorio que
   debe cumplirse antes de que una aplicación pase a ambientes superiores (HML y PRD). Se realiza
   en el ambiente de QA".
   Lado B (ES0901 pág. 29, HOTFIX): "Dado que los tiempos de despliegue en producción deben ser
   inmediatos, a este tipo de versión se le realizará el assessment a posteriori del despliegue
   productivo. Dicho assessment se realizará en el ambiente de QA."
   Es contradicción **interna** de ES0901, y el Anexo V no contempla la excepción del hotfix.
   Importa acá más que en ningún otro lado: un hotfix sobre el flujo de login es exactamente el
   escenario en que trabajo de identidad llega a producción antes de su assessment. No des por
   cubierto ninguno de los dos lados; preguntá antes de mandar un hotfix de autenticación.
