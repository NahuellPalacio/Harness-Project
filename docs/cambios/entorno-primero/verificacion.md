# Verificación — Bloque 1: la configuración de las integraciones sale del `.env`

**Estado:** cerrado · **Fecha:** 28-09-2026 · **Versión:** sin publicar

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` en dos
pasadas el 28-09-2026. La primera fue sobre los 71 escenarios, con `python tests/correr.py -k
60_entorno` (301/301) y la compuerta entera (`37205/37205`, exit 0). La segunda fue solo sobre
E-32, E-45 y E-55, después de corregirlos (307/307).

**Resultado: 71 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | `setup`, `estado` y `reconfigurar` dicen `ENVIRONMENT_FIRST` y el registro lo guarda | sostenido | sí | `60_entorno_primero.py` |
| E-02 | Ningún agente nuevo contra `426ebeb` | sostenido | sí | `60_entorno_primero.py`, `git ls-tree` |
| E-03 | Ninguna skill nueva contra `426ebeb` | sostenido | sí | `60_entorno_primero.py`, `git ls-tree` |
| E-04 | Se valida con `/rest/api/3/myself` y `/api/v4/user` | sostenido | sí | `60_entorno_primero.py` |
| E-05 | Soportada sin validar figura `DISABLED`; están las siete | sostenido | sí | `60_entorno_primero.py` |
| E-06 | `JIRA_BASE_URL` del `.env` llega como `baseUrl`, fuente `DOTENV` | sostenido | sí | `60_entorno_primero.py` |
| E-07 | `JIRA_USER` del `.env` llega como `usuario`, fuente `DOTENV` | sostenido | sí | `60_entorno_primero.py` |
| E-08 | El token de Jira sale solo de `AlmacenSecretos.get` | sostenido | sí | `60_entorno_primero.py`, almacén espía |
| E-09 | `GITLAB_BASE_URL` llega al adapter de GitLab | sostenido | sí | `60_entorno_primero.py` |
| E-10 | El token de GitLab sale solo del almacén | sostenido | sí | `60_entorno_primero.py`, almacén espía |
| E-11 | El proceso le gana al `.env`, sin conflicto | sostenido | sí | `60_entorno_primero.py`, biblioteca y CLI |
| E-12 | El default solo sin proceso, sin `.env` y sin JSON viejo | sostenido | sí | `60_entorno_primero.py` |
| E-13 | Nada se inventa | sostenido | sí | `60_entorno_primero.py` |
| E-14 | Vacío y `<...>` son ausentes | sostenido | sí | `60_entorno_primero.py` |
| E-15 | Deshabilitada: `NOT_CONFIGURED`, sin faltantes, sin red | sostenido | sí | `60_entorno_primero.py` |
| E-16 | Completa: `AVAILABLE` | sostenido | sí | `60_entorno_primero.py` |
| E-17 | Sin `JIRA_USER`: `NOT_CONFIGURED` sin red | sostenido | sí | `60_entorno_primero.py` |
| E-18 | Se nombra `JIRA_USER` y se dice qué hacer | sostenido | sí | `60_entorno_primero.py` |
| E-19 | Bandera inválida: `ENV_ENABLED_FLAG_INVALID`, sin red, GitLab sigue | sostenido | sí | `60_entorno_primero.py` |
| E-20 | Las formas del booleano | sostenido | sí | `60_entorno_primero.py` |
| E-21 | La proyección lleva `baseUrl` y `usuario` | sostenido | sí | `60_entorno_primero.py` |
| E-22 | La proyección no lleva `JIRA_TOKEN` | sostenido | sí | `60_entorno_primero.py` |
| E-23 | La proyección lleva `gitlab.baseUrl` | sostenido | sí | `60_entorno_primero.py` |
| E-24 | La proyección no lleva `GITLAB_TOKEN` | sostenido | sí | `60_entorno_primero.py` |
| E-25 | Un `SECRET` nunca se proyecta | sostenido | sí | `60_entorno_primero.py` |
| E-26 | La heurística sigue de segunda línea | sostenido | sí | `60_entorno_primero.py` |
| E-27 | Una proyección vieja no le gana al `.env` | sostenido | sí | `60_entorno_primero.py` |
| E-28 | La proyección es determinista | sostenido | sí | `60_entorno_primero.py` |
| E-29 | Sin cambios no se reescribe | sostenido | sí | `60_entorno_primero.py`, mtime |
| E-30 | `-Update` no cambia el `.env` | sostenido | sí | `60-entorno-instalador.ps1` |
| E-31 | El bootstrap deja el `.env` byte a byte | sostenido | sí | `60_entorno_primero.py` |
| E-32 | Lo ajeno al contrato no entra a la resolución ni a ningún archivo | sostenido | sí | `60_entorno_primero.py` (segunda pasada) |
| E-33 | El `.env.example` solo tiene nombres del contrato | sostenido | sí | `60_entorno_primero.py` |
| E-34 | El `.env.example` sin credenciales ni OpenShift | sostenido | sí | `60_entorno_primero.py` |
| E-35 | `setup` no pregunta | sostenido | sí | `60_entorno_primero.py` |
| E-36 | `setup` lista presente y ausente | sostenido | sí | `60_entorno_primero.py` |
| E-37 | `reconfigurar` no muestra valores | sostenido | sí | `60_entorno_primero.py` |
| E-38 | `--token` sigue rechazado | sostenido | sí | `60_entorno_primero.py` |
| E-39 | Ningún token en stdout | sostenido | sí | `60_entorno_primero.py` |
| E-40 | Ningún token en stderr | sostenido | sí | `60_entorno_primero.py` |
| E-41 | Sigue `Read(./.env)` | sostenido | sí | `60_entorno_primero.py` |
| E-42 | Sigue `Read(./.env.*)` | sostenido | sí | `60_entorno_primero.py` |
| E-43 | `session-start.py` no trae el `.env` | sostenido | sí | `60_entorno_primero.py` |
| E-44 | El TaskContext no trae el `.env` | sostenido | sí | `60_entorno_primero.py` |
| E-45 | El libro del Bloque 4 de `contabilidad --ingerir` no trae tokens | sostenido | sí | `60_entorno_primero.py` (segunda pasada) |
| E-46 | El libro de seguridad no trae tokens | sostenido | sí | `60_entorno_primero.py` |
| E-47 | PreToolUse sigue bloqueando | sostenido | sí | `60_entorno_primero.py` |
| E-48 | La auth de Jira no cambió | sostenido | sí | `60_entorno_primero.py` |
| E-49 | La auth de GitLab no cambió | sostenido | sí | `60_entorno_primero.py` |
| E-50 | El descubrimiento no cambió | sostenido | sí | `60_entorno_primero.py` |
| E-51 | Jira sin configurar: tres `DISABLED` | sostenido | sí | `60_entorno_primero.py` |
| E-52 | GitLab sin configurar: cuatro `DISABLED` | sostenido | sí | `60_entorno_primero.py` |
| E-53 | El JSON viejo ayuda a migrar, fuente `LEGACY` | sostenido | sí | `60_entorno_primero.py` |
| E-54 | El `.env` le gana al JSON viejo, y el viejo no vuelve | sostenido | sí | `60_entorno_primero.py` |
| E-55 | La migración no lee, no imprime ni copia secretos | sostenido | sí | `60_entorno_primero.py` (segunda pasada) |
| E-56 | La proyección queda en su lugar, con marca | sostenido | sí | `60_entorno_primero.py` |
| E-57 | `harness --json` dice `ENVIRONMENT_FIRST` | sostenido | sí | `60_entorno_primero.py` |
| E-58 | `envFilePresent` sin valores | sostenido | sí | `60_entorno_primero.py` |
| E-59 | La bienvenida dice Configuración y `Faltan:` | sostenido | sí | `60_entorno_primero.py` |
| E-60 | LISTO, PARCIAL y `ENV_MODEL_READABLE` | sostenido | sí | `60_entorno_primero.py` |
| E-61 | `-Update` no cambia un byte del `.env` | sostenido | sí | `60-entorno-instalador.ps1` |
| E-62 | Se nombran las variables nuevas | sostenido | sí | `60_entorno_primero.py` |
| E-63 | `-Update` repone contrato y bloque de `.env.example` | sostenido | sí | `60-entorno-instalador.ps1` |
| E-64 | `-Update` convierte el JSON viejo en proyección | sostenido | sí | `60-entorno-instalador.ps1` |
| E-65 | `-Update` reescribe `harness.capacidades.json` con `faltan` | sostenido | sí | `60-entorno-instalador.ps1` |
| E-66 | Solo `jira` y `gitlab`, sin OpenShift | sostenido | sí | `60_entorno_primero.py` |
| E-67 | Una integración sin adapter es `ENV_CONTRACT_INVALID` | sostenido | sí | `60_entorno_primero.py` |
| E-68 | Contratos rotos son `ENV_CONTRACT_INVALID` | sostenido | sí | `60_entorno_primero.py` |
| E-69 | `.env` ilegible es `ENV_FILE_UNREADABLE`, sin contenido | sostenido | sí | `60_entorno_primero.py` |
| E-70 | La advertencia no trae valores | sostenido | sí | `60_entorno_primero.py` |
| E-71 | La compuerta en verde | sostenido | no consta | `Invoke-Tests.ps1`, `37205/37205` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar.

La marca `sí` de E-01 a E-70 sale de una pasada de 53 mutaciones: 50 sobre Python, 3 sobre
`install.ps1` y el alta temporal de un agente y una skill. Cada una rompió el código, vio fallar el
escenario y restauró.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-32 decía "no se leen" y el parser lee todas las líneas.** El test solo probaba que no se
   escribían. Se angostó el escenario a "no entran a la resolución", y el test ahora revisa los
   atributos de la `Resolucion`.
2. **E-45 nombraba como sujeto a `contexto`, que no escribe libro del Bloque 4.** El test ya corría
   `contabilidad`. Se corrigió el escenario, no el test.
3. **E-55 no podía ver "no la lee".** El `.env` del test ya traía `JIRA_TOKEN`, así que un token
   leído del JSON viejo no cambiaba nada. Se sumó el caso sin token en el `.env`.
4. **E-70 no podía fallar.** Lo vio la pasada de mutaciones antes del refutador: el test
   concatenaba `describir()` a lo que revisaba.

## Lo que queda abierto, anotado y no escondido

- **E-45 y E-46 son estructurales.** `contabilidad` y `seguridad` no leen el `.env`. El test falla
  solo si alguien agrega esa lectura, que es justamente lo que tiene que atrapar.
- **Quedaron afuera el helper que escribe en el `.env` y OpenShift.** Figuran con su motivo en
  `## Qué queda afuera` de la spec y no están en `Pendientes/`: ninguno es un defecto.
- **Los riesgos de la spec siguen vigentes.** `legado` puede estirar la migración y el `-Update`
  sale a la red.

## Lo que ningún test cubre y se mira con los ojos

- Un `-Update` sobre un proyecto real con Jira y GitLab del organismo configurados en el `.env`.
  La salida tiene que decir `Jira Cloud OK` sin mostrar ningún valor.
- La bienvenida de una sesión real de Claude Code, con la sección `Configuración`.
