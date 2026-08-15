# Fuentes de la normativa

Acá van los PDF originales de los estándares del GCBA. **Esta carpeta está gitignoreada**: son
documentación interna del organismo y este repo es público, así que los archivos no se
distribuyen. Lo que sí se versiona son los extractos en markdown, en `../extractos/`, que son
destilado propio.

## Hace falta tenerlos?

Para **usar** el harness, no. `normativa/` nunca se copia a un proyecto y ningún hook, check ni
skill abre un PDF en tiempo de ejecución. El harness funciona con esta carpeta vacía.

Para **escribir o revisar un extracto**, sí. Un extracto sin la fuente al lado no se puede
verificar, y la regla del harness es que un extracto se refuta contra su fuente, no contra el
recuerdo de nadie.

## Cuáles son

| Archivo | Qué es |
|---|---|
| `ES0901 - Estandar de Desarrollo ASI v6.3.pdf` | Estándar de desarrollo |
| `ES0902 - Estándar de Seguridad V6.2.pdf` | Estándar de seguridad |
| `ES0903 - Estandar de Desarrollo de API v2.2.pdf` | Estándar de APIs |
| `Guía de Procesos - DGISIS.pdf` | Procesos de la dirección |
| `CambiosenSoftwaredeAplicacion.pdf` | Procedimiento de cambios |
| `_Obelisco-V2_docs_Guía_de_adopción_de_Obelisco_v2.pdf` | Guía de adopción de Obelisco v2 |

Se piden por los canales internos de DGISIS. Los nombres de archivo importan: los extractos
citan la fuente por nombre y versión.
