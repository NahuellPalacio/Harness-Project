# El contexto de una tarea

Una clave de Jira entra. Sale un documento que contesta qué hay que hacer, por qué, a qué
proyecto pertenece y cuál es su estado técnico — o declara que no pudo.

```powershell
python .claude\harness\bin\desarrollo\dev-harness.py contexto GCBA-1234
```

```
GCBA-1234 — Agregar el filtro por fecha al listado
------------------------------------------------------------
Tipo        Historia de Usuario
Estado      En curso
Criterios   3
Proyecto    GCBA  ·  ficha GCBA-7
Documentos  4
Repositorio tramites/backoffice
Ramas / MR  1 / 1

Huecos declarados: 2. Estan en gaps_and_conflicts.

TaskContext: C:\...\.claude\contextos\GCBA-1234.json
```

El documento queda en `.claude/contextos/GCBA-1234.json` y valida contra
`comun/schemas/task-context.schema.json`. `--json` lo manda por stdout para consumirlo.

## Qué resuelve, y en qué orden

```
GCBA-1234
     ↓  jira.issue.read
Tarea          tipo, título, descripción, criterios, estado, padre y enlaces
     ↓  jira.issue.search
Ficha          el issue de tipo "Ficha de Proyecto" del mismo proyecto Jira
     ↓  jira.attachment.read
Documentos     los adjuntos de la ficha, bajados y -si markitdown está- extraídos
     ↓  gitlab.*
Repositorio    el proyecto, y las ramas y MR que nombran la clave
     ↓
TaskContext
```

Cada paso pregunta primero al registro que dejó el bootstrap. **Una capacidad que no está
habilitada no se llama: se declara el hueco y se sigue.** La única excepción es
`jira.issue.read`: sin eso no hay tarea, y el comando sale con código 2.

## La Ficha de Proyecto

Es el concepto central, y no es un issue más. Jira guarda ahí el **conocimiento** del
proyecto —objetivos, alcance, reglas de negocio, arquitectura, y los documentos como
adjuntos— mientras que las HU, los bugs y las tasks son **trabajo**.

Se busca por tipo de issue, dentro del mismo proyecto Jira del ticket:

```json
{ "fichaTipoDeIssue": "Ficha de Proyecto" }
```

en `.claude/harness.config.json`. Los campos salen de partir su descripción por
encabezados —`Objetivos`, `Alcance`, `Reglas`, `Arquitectura`— y por eso el bloque viaja
marcado `inferred`: Jira no tiene un campo "objetivos", y esto es una heurística.

> 🔴 **Si hay más de una ficha, no se elige ninguna.** Las dos claves van a `conflicts` y
> la ficha queda vacía. Elegir la primera por fecha sería inventar un criterio que nadie
> escribió, y el contexto saldría con el sello de resuelto sobre una elección invisible.

## Los documentos

Los adjuntos del ticket y de la ficha se bajan a `.claude/contextos/<CLAVE>-adjuntos/`.

| Archivo | Qué pasa |
|---|---|
| `.md`, `.txt`, `.csv`, `.json`, `.yaml` | El texto entra directo |
| `.pdf`, `.docx`, `.pptx`, `.xlsx` | Entra su texto **si markitdown está instalado** |
| Cualquier otro | Queda el archivo y su ficha, sin texto |

Sin markitdown el harness no falla: baja el archivo, deja `extractor: ninguno`,
`text_extracted: false` y un hueco que dice cómo se arregla. Es ADR-0008 al pie — lo
externo se aprovecha, nunca es requisito.

La clasificación (`prd`, `adr`, `regla`, `arquitectura`, `manual`, `diagrama`, `otro`)
sale de patrones sobre el nombre del archivo, y viaja declarada como inferida.

**Cuál de esos documentos hay que leer para esta tarea no lo decide el harness.** Es una
decisión semántica: el contexto declara qué hay y quien tenga un modelo elige.

## El repositorio

De dónde sale, en este orden:

1. `gitlabProyecto`, en el bloque `gitlab` de `.claude/harness.integraciones.json`
2. Una URL de GitLab escrita en la Ficha de Proyecto

Si no está en ninguno de los dos, la sección queda vacía. **No se adivina por el nombre
del proyecto Jira.**

Entran solo las ramas y los merge requests que nombran la clave del ticket: un contexto
con las cuarenta ramas del repositorio no ayuda a entender GCBA-1234, lo tapa.

Y si el proyecto tiene `docs/codebase/project-context.json` —el contrato que escribe
`dev-iniciador-code` al recorrer el código— el `TaskContext` lo **referencia con su hash**,
no lo copia. Son dos contratos: duplicar uno adentro del otro los desincroniza en la
primera actualización.

## Los secretos

Todo texto que viene de afuera pasa por el detector de secretos del harness —el mismo
`comun/reglas/secretos.patrones.json` que usa el hook, importado y no copiado— antes de
tocar el disco.

Lo de confianza **alta** se reemplaza por su muestra segura:

```
"Usa el token [secreto redactado: token-gitlab glpat-A1b2C3... (26 caracteres)] para probar."
```

y el hallazgo queda en `gaps_and_conflicts.redacted_secrets`, sin el valor.

Lo de confianza **media** se declara y **no se toca el texto**. En el hook, lo ambiguo
pregunta y decide una persona; acá no hay a quién preguntarle, y un falso positivo que
mutile una descripción es peor que un aviso.

## Lo que el documento declara cuando no pudo

Ninguna sección se inventa. Lo que no se resolvió sale vacío con su `knowledge_status`
—`missing`, `conflicted`, `inferred`— y el motivo en `gaps_and_conflicts`:

| Lista | Qué junta |
|---|---|
| `missing` | Lo que se buscó y no estaba, con qué se buscó |
| `conflicts` | Dos fuentes que discrepan. Se marca, no se elige |
| `missing_capabilities` | Qué capacidad faltaba y qué sección quedó vacía por eso |
| `redacted_secrets` | Qué se redactó y dónde. Nunca el valor |
| `unresolved_questions` | Lo que hace falta preguntarle a una persona |

## Lo que este bloque no hace

- **No elige qué documento leer.** Declara el corpus; elegir es semántico.
- **No trae los comentarios del ticket.** Un hilo de comentarios es negociación, no
  especificación: mezcla lo decidido con lo discutido y duplica el tamaño del contexto.
  Si el criterio de aceptación real vive ahí, el harness no lo va a ver — está anotado
  como riesgo conocido.
- **No sigue los enlaces.** El padre y los issues enlazados entran como referencia. Un
  resolvedor que sigue enlaces termina bajando el proyecto entero desde un ticket
  cualquiera.
- **No escribe nada en Jira ni en GitLab.** Todo es de lectura.
- **No cachea.** Cada corrida vuelve a preguntar; el archivo anterior se pisa.
- **No orquesta nada.** El `TaskContext` es el insumo del bloque siguiente.
