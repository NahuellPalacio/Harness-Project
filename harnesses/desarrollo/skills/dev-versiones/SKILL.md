---
name: dev-versiones
description: Use when choosing, pinning or bumping the version of a language, framework, library, ORM, package manager or database engine on a GCBA project — editing or reviewing package.json, composer.json, pom.xml or requirements.txt, adding or upgrading a dependency, deciding between npm and yarn, picking Oracle vs MariaDB vs PostgreSQL vs MongoDB, judging whether a library that is not on the ASI approved list can be used at all, or checking whether the stack is old enough to get a deployment rejected.
---

# Versiones y dependencias homologadas

**Esta skill no trae ni un número de versión, y es a propósito.** Las versiones homologadas
viven en las tablas del Anexo II del ES0901 (págs. 30-37), y en la conversión a texto del PDF
cinco de esas tablas quedaron con las columnas o las filas corridas: se leen perfectas y son
falsas. Están nombradas una por una más abajo. Un número desalineado es peor que ninguno,
porque nadie lo va a dudar, y rastrear de qué tabla salió el número que alguien pegó en un
ticket cuesta lo mismo que leerlo del PDF. Acá están los criterios, que es lo que se discute en
una revisión; el número se lee del PDF, en la página que figura abajo. Y aunque la tuvieras
bien transcripta, el Anexo II "será actualizado periódicamente por la ASI y constituye la
referencia oficial sobre el stack tecnológico aprobado **al momento del desarrollo**"
(ES0901 pág. 11): la copia de hace seis meses ya no sirve.

## La regla base

- **No se elige la versión, se toma la homologada.** "Todos los desarrollos deben utilizar
  las herramientas y versiones homologadas por la Agencia" (ES0901 pág. 12, principio G1); el
  detalle está en el Anexo II (ES0901 pág. 11).
- **Nunca una beta.** Los paquetes "deberán ser siempre versiones estables y que correspondan
  a la distribución del sistema operativo estándar que se encontrara en los servidores de
  Producción. Bajo ningún concepto se aceptarán versiones 'beta' de ningún paquete de
  software" (ES0901 pág. 10).
- **Lo que cuesta equivocarse**: "El incumplimiento de la regla de sólo paquetes homologados
  puede ocasionar el rechazo del entregable y la necesidad de retrabajo a último momento"
  (ES0901 pág. 25).
- **Todo lo que instales es tuyo.** Cualquier paquete instalado en producción además del
  software de base "será considerado parte de la aplicación, siendo el desarrollador
  responsable de su buen funcionamiento y compatibilidad" con ese software de base y con los
  demás aplicativos de esos servidores (ES0901 pág. 10).

## Cómo se lee una versión homologada, sin mirar la tabla

- **Se homologa la rama, no el patch.** Homologada una herramienta bajo una mayor y menor
  determinada, "se considerarán válidas todas las versiones patch iguales o superiores a la
  versión homologada (mínima), siempre que no introduzcan cambios incompatibles ni
  vulnerabilidades conocidas"; si la tabla lista varias versiones de una misma herramienta,
  cada una sigue el mismo criterio (ES0901 pág. 30).
- **Qué queda afuera** (ES0901 pág. 30): patch inferiores a la mínima homologada; ramas
  menores anteriores; y ramas posteriores, que "deberán atravesar un nuevo proceso de
  evaluación y homologación por parte de la ASI". Adelantarse incumple igual que atrasarse.
- **Bibliotecas: una sola rama menor por versión mayor.** "Se establece como criterio general
  la homologación de una única rama menor por cada versión mayor, priorizando aquella que se
  encuentre vigente, estable y dentro de su ventana de soporte. Dentro de dicha rama menor, se
  consideran válidas las versiones patch iguales o superiores a la homologada"
  (ES0901 pág. 32). Ver contradicción 1.
- **Tolerancia hacia atrás: una sola versión de estándar** (ES0901 pág. 30). Con una versión
  de estándar por detrás pasa, pero "se notificará formalmente al equipo de desarrollo la
  necesidad de realizar una actualización tecnológica y dicha observación quedará registrada
  como condición a regularizar en futuras entregas o evoluciones". Con "dos o más versiones
  de estándar por detrás de la vigente, el proceso de despliegue no podrá ser completado".
  Ojo con la unidad: se cuenta en versiones **del estándar**, no de la herramienta.
- **Estar dentro de la ventana no garantiza nada.** "La ASI puede desaprobar o cancelar un
  despliegue aun dentro de la ventana de tolerancia si se detectan vulnerabilidades críticas,
  problemas de soporte o incompatibilidades con la infraestructura utilizada" (ES0901 pág. 30).

## Si la biblioteca no está homologada

La decisión no es del equipo: "Si se necesita utilizar una biblioteca no homologada, la ASI
evaluará tanto su uso como su posible incorporación al estándar". Pero los criterios "aplican
también para bibliotecas que no estén incluidas en el estándar" (ES0901 pág. 12), así que
sirven para saber de antemano si tenés algo defendible.

**Criterios mínimos por versión** (ES0901 págs. 11-12), textuales: "No presentar
vulnerabilidades conocidas." · "Estar homologada en OpenShift para la generación de
imágenes." · "Corresponder a una versión estable con al menos 3 meses de maduración." · "La
última versión publicada debe tener una antigüedad menor a 2 años." · "No estar en estado de
deprecación (EOL). Si el fin de soporte ocurrirá en menos de 6 meses, no podrá agregarse a
este estándar." · "Licenciamiento gratuito y con licencia open source compatible (ej: MIT,
Apache 2.0, BSD, EPL, MPL)."

Los dos criterios de tiempo se leen juntos y matan la mayoría de los casos: lo recién sacado
no llega a los 3 meses de maduración, y lo abandonado pasa los 2 años desde la última
publicación.

**Criterios de comunidad** (ES0901 pág. 12): "Actividad reciente: issues, pull requests y
discusiones resueltas en menos de 1 año."; "Frecuencia de commits y releases regulares."; se
da mayor relevancia a la combinación de métricas (forks + stars + issues/pull requests
recientes) junto con la frecuencia de actualizaciones. Las estrellas solas no son argumento.

**Dos aclaraciones que cambian el trámite:** esos criterios son para incorporar al estándar y
**no aplican a sistemas operativos, plataformas de búsqueda, bases de datos y servidores
web**; y **el toolchain no se homologa uno por uno** —build, bundling y automatización "no
constituyen tecnologías principales sujetas a homologación individual en el presente
estándar"— siempre que sea compatible con lenguajes/frameworks/plataformas homologadas, no
introduzca dependencias incompatibles y cumpla los criterios de actualización, seguridad y
mantenimiento de la ASI; seleccionarlo, configurarlo y actualizarlo es del equipo
(ES0901 pág. 11).

**Trámite**: consultas a `estandares.DGISIS@buenosaires.gob.ar` (ES0901 pág. 12). Y en todos
los casos, "Todo componente adicional utilizado en código debe ser validado y acordado"
(ES0901 pág. 13, principio P6).

**Lo que arrastra sumar o subir una dependencia:** antes del pase a Producción hay que
informar "qué bibliotecas externas utiliza la aplicación", con nombre, versión, sistema
dependiente y servidores donde está instalada —la ASI cruza esa matriz contra las
vulnerabilidades publicadas— y acreditar el derecho de uso si tiene licenciamiento
(ES0901 pág. 10). Y el "agregado o actualización de bibliotecas, frameworks, SDKs o
dependencias" obliga a un **assessment de seguridad nuevo** (ES0901 pág. 42).

## Al revisar composer.json, package.json o pom.xml

- **Versión exacta, siempre.** El archivo de dependencias va en la carpeta `source/` y "debe
  listar las mismas especificando el número de versión exacta para cada una de ellas"
  (ES0901 pág. 26). El check `dev-dependencias` ya marca los rangos: no los busques a mano, usá
  el tiempo en verificar que el número fijado sea el homologado.
- **Cuál archivo según la tecnología** (ES0901 pág. 38): Laravel PHP → `composer.json` "en la
  raíz del proyecto"; Node.js → `package.json`; Java → `pom.xml`, "donde se declare las
  dependencias y versiones a utilizar". La raíz la norma la exige sólo para `composer.json`; de
  los otros dos no dice dónde van, aunque la convención de npm y Maven sea ésa. En Python,
  "solo se admite *requirements.txt*" (ES0901 pág. 28).
- **NPM y nada más.** "el administrador de paquetes permitido es NPM (Node Package Manager). No
  está permitido el uso de YARN u otras alternativas, a fin de garantizar la compatibilidad y
  trazabilidad de dependencias en los entornos de GCABA" (ES0901 pág. 13), repetido para todos
  los entornos Node.js en el Anexo II (ES0901 págs. 31 y 35). Y la versión se mira en el
  registro: "la referencia de versiones homologadas es el registro oficial de NPM. GitHub puede
  no reflejar la totalidad del histórico de versiones publicadas" (ES0901 pág. 35).
- **Nada de lenguaje puro.** "No se permite el uso del lenguaje puro ('vanilla') sin el
  soporte de su respectivo framework"; las bibliotecas de bajo nivel "podrán utilizarse
  únicamente cuando estén integrados de forma indirecta a través del framework correspondiente
  (por ejemplo, conectores de base de datos usados por un ORM)" (ES0901 pág. 13). En Python lo
  repite con nombre y apellido: los conectores valen "exclusivamente como conectores de base de
  datos subyacentes, utilizadas a través de un framework aprobado (ej. Django, FastAPI) y en
  combinación con un ORM estructurado como SQLAlchemy. Su uso directo (sin ORM ni framework) no
  está autorizado" (ES0901 pág. 34). Un conector suelto en dependencias es un hallazgo.
- **Migraciones antes que scripts**: "Se deben utilizar las herramientas disponibles dentro del
  framework elegido para versionar la estructura de base de datos (administradores de migración
  de bases de datos) evitando utilizar scripts" (ES0901 pág. 38). La pág. 36 vuelve sobre lo
  mismo pero más flojo —"se insta a utilizar administradores de migración de bases de datos en
  los procesos de despliegue"—, así que el literal exigible es el de la 38. Para Laravel, Django
  y Entity Framework Core "la versión de estos administradores de migración está sujeta a la del
  framework utilizado" (ES0901 pág. 36): ahí no hay número propio que buscar.
- **Sin compilados en la entrega**: "No se aceptarán paquetes compilados como parte de la
  entrega" (ES0901 pág. 26). Ver contradicción 3.

## Motor de base de datos

- **La versión se valida antes, no después**: "para nuevas implementaciones, se deberá validar
  previamente con DGISIS y DGINFRA la versión del motor a utilizar" (ES0901 pág. 32). Mirar la
  tabla no alcanza. No es el único caso con validación previa: la solución híbrida Ionic +
  Capacitor "deberá ser validada previamente por la ASI" (ES0901 pág. 17) y el uso de
  plataformas Cloud "deberá ser evaluado por la ASI" (ES0901 pág. 17).
- **PostgreSQL es una excepción, no una alternativa**: "Elegible solo cuando sea obligatorio
  para: uso de PostGIS, enlatados (sin otra opción), necesidad de múltiples esquemas en una
  sola DB, que no pueda utilizarse Oracle o MariaDB (ej: X-Road), etc. Se deberá justificar
  debidamente el caso y se analizará con DGINFRA cada implementación" (ES0901 pág. 32).
- **Documental**: "En ningún caso puede utilizarse como BD relacional y en sistemas
  transaccionales. La BD documental homologada es MongoDB" (ES0901 pág. 20).
- **Qué motor recomienda cada arquitectura**: monolítica estructurada → "MariaDB + ORM
  (Eloquent)"; monolítica modular → "Oracle, MariaDB" (ES0901 pág. 14); SOA → "Motor de base de
  datos: ORACLE."; microservicios → "Oracle o base por microservicio (persistencia políglota)"
  (ES0901 pág. 15). El documento los lista entre las herramientas **recomendadas** de cada
  arquitectura, no como asignación obligatoria: no alcanzan para cerrar una revisión con "es
  SOA, entonces tiene que ser Oracle". Lo que sí es obligatorio es validar previamente la
  versión del motor con DGISIS y DGINFRA (pág. 32).

## Elecciones que hay que resolver antes de mirar la versión

Si la herramienta no pasa el filtro, qué versión está homologada no importa.

- **.NET**: "Se deberá justificar debidamente el motivo de su elección" (ES0901 pág. 31).
- **Servidor web y colas**: Nginx "podrá emplearse únicamente en escenarios puntuales donde no
  exista otra alternativa técnica viable. Por defecto, el servidor web de uso preferente es
  Apache HTTP Server"; y "Por defecto, el gestor de colas es Apache Kafka" (ES0901 pág. 36).
- **BPM**: la ASI "homologa las versiones Community (CE) de CIB seven" (ES0901 pág. 36). Una
  edición enterprise no está homologada aunque el número de versión coincida.
- **Editor de texto enriquecido**: se homologa Quill; "CKEditor 5 y TinyMCE podrán evaluarse
  únicamente mediante assessment técnico-legal específico, ya que sus licenciamientos poseen
  limitaciones en términos legales/comerciales" (ES0901 pág. 35).
- **OpenID Connect y Keycloak** no tienen versión en la tabla: "serán provistas por la DGSEI
  al momento de ser requeridas para un fin específico" (ES0901 pág. 37). No lo busques:
  pedilo.

## Kotlin y Java van juntos

"Siempre verificar compatibilidad de Kotlin con versiones homologadas de Java, ya que para
compilación mobile y desarrollos backend, se utiliza ese lenguaje" (ES0901 pág. 31). Tomar la
versión de Kotlin de la tabla sin cruzarla contra la de Java homologada es media decisión. La
nota está repetida al pie de frameworks backend con otra redacción: ver contradicción 2.

## Lo que hay que ir a buscar al PDF

**Ningún número de versión sale de acá.** Cinco tablas del Anexo II se convirtieron a texto con
las columnas o las filas corridas: la de **Framework Frontend (pág. 31) es la más peligrosa del
documento** —deja frameworks sin versión y le asigna a uno las versiones de otro—; la de
**Biblioteca Java (pág. 33)** separa nombres y versiones en bloques distintos y ninguna fila
coincide con sus valores; **Biblioteca Angular (pág. 34)**, **LMS (pág. 35)** y **DMS
(pág. 36)** tienen filas o encabezados corridos. Las demás tablas del Anexo II no están
marcadas como corridas —desconfiar de todas por igual sólo hace perder el rastro de estas
cinco—, lo que no las vuelve citables de memoria: el número se lee igual del PDF.

Abrí el PDF en la página que corresponda y leé la fila entera de punta a punta: "Versiones
Deprecadas" y "Versiones Homologadas" son columnas contiguas y confundirlas es el error caro.

| Qué buscás | Página |
|---|---|
| Lenguajes (PHP, Python, Java/OpenJDK, Node.js, Kotlin, Swift) · Frameworks Frontend · Frameworks Backend | 31 |
| Motores de base de datos · Plataformas de búsqueda | 32 |
| Bibliotecas Android | 32-33 |
| Bibliotecas Java | 33 |
| Bibliotecas Python | 33-34 |
| Bibliotecas Angular · Bibliotecas JavaScript | 34 |
| Bibliotecas .NET y otras · Sistema de Diseño (Obelisco, Bootstrap) | 35 |
| CMS · LMS · DMS · Administradores de migración de base de datos | 35-36 |
| BPM · colas · servidor web · sistemas operativos · seguridad | 36-37 |

Antes de citar cualquiera de esas filas en un pliego, un ticket o un criterio de aceptación,
confirmá que estás mirando el Anexo II vigente y no la copia que quedó en el proyecto
(ES0901 pág. 11).

## Contradicciones sin resolver

1. **Una única rama menor por versión mayor, contra las propias tablas.** La pág. 32 fija como
   criterio general "la homologación de una única rama menor por cada versión mayor"; en esa
   misma página, la tabla de bibliotecas Android homologa tres ramas menores distintas de una
   misma versión mayor para una sola biblioteca, y en frameworks backend (pág. 31) hay
   herramientas con dos. El criterio está redactado para "bibliotecas" y el documento no
   declara si las tablas lo excepcionan o lo contradicen. Si tu caso depende de eso, preguntá.

2. **La nota de Kotlin aparece dos veces con distinto alcance.** Pág. 31: verificar
   compatibilidad "con versiones homologadas de Java, ya que para **compilación mobile y
   desarrollos backend**, se utiliza ese lenguaje". Pág. 32, al pie de frameworks backend: "con
   **las** versiones homologadas de Java, ya que **en desarrollos backend**", sin mencionar la
   compilación mobile. No se declara cuál prevalece: queda indefinido si la verificación es
   exigible en un proyecto puramente mobile.

3. **Paquetes compilados: se rechazan y se exigen.** Pág. 26 (Anexo I, carpeta `source/`): "No
   se aceptarán paquetes compilados como parte de la entrega." Pág. 10 (§6.8): si es necesario
   instalarlos, "serán considerados parte de la aplicación debiendo suministrarse
   **pre-compilados e integrados en ella**", con obligación de declararlos, documentarlos y
   mantenerlos actualizados. No se declara si una regla acota a la otra (repositorio contra
   instalación en servidores) ni cuál prevalece.
