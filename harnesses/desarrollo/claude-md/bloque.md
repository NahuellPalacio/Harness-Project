## Trabajo técnico

**Las versiones de las dependencias las fija ASI.** No se elige una versión: se toma la
homologada en el estándar de desarrollo vigente. La tolerancia es de una sola versión de
estándar anterior; dos o más atrás, el despliegue no se completa.

**La configuración va afuera del código.** Bases de datos, servicios externos, URLs y paths
se leen de un archivo externo o del entorno. Nada de eso se escribe en el fuente, ni siquiera
para probar.

**Los servidores se referencian por nombre DNS, jamás por IP.**

**Ante un error inesperado no se expone nada de la infraestructura** — ni servidor, ni IP,
ni path, ni stack. El código de estado de un error del aplicativo es 500 y no se reemplaza
por otro.

**Obelisco es obligatorio por resolución**, no por preferencia. Se usan sus componentes y
sus clases, no soluciones propias ni las de otras librerías.

**La accesibilidad es exigible por ley.** Contraste, jerarquía de encabezados, `label`
vinculado, texto alternativo y foco visible no son mejoras: son condición de aprobación.

📌 Las reglas completas de estructura de repositorio, diseño de APIs y accesibilidad están
en skills. Se invocan cuando hacen falta, no se cargan siempre.
