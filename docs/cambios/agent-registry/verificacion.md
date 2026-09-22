# Verificación — El registro de agentes: la existencia se declara y se valida, no se adivina

**Estado:** cerrado · **Fecha:** 22-09-2026 · **Versión:** 0.19.0

Este documento es lo que cierra el cambio según
[ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md): el veredicto por escenario de quien
verificó, que no es quien construyó. Los veredictos los emitió `harness-spec-refuter` el
22-09-2026, en **dos pasadas**, corriendo `python tests/correr.py -k 22_registro_agentes
--detallado` sobre el árbol de release de 0.19.0, sin ES0902 O1 ni O2. La segunda pasada sumó
mutaciones en memoria propias sobre `resolver_ruteo` y `skills_de`.

**Resultado: 33 escenarios sostenidos, 0 contradichos, 0 leídos, 0 sin sustento.**

Son 33 contando E-10b, E-10c, E-15b y E-18b como escenarios propios, como los escribe la spec.

La primera pasada rindió 31 sostenidos, **1 contradicho** —E-02— y **1 sin sustento** —E-13—, y el
cambio no cerró. El código de `registro_agentes.py` **no se tocó**: E-02 era la spec
contradiciéndose y E-13 era un test que cubría una de cuatro.

## La tabla

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Los diez agentes resuelven del registro, con la matriz §7.1 vacía | sostenido | sí | `22_registro_agentes`, `test_e01_los_diez_resuelven_del_registro` |
| E-02 | Un agente no declarado no rutea: sin archivo `AGENT_NOT_FOUND`, con archivo el `ORPHAN_AGENT` de E-18 | sostenido | sí | `test_e02_un_agente_que_no_esta_declarado` — segunda pasada |
| E-03 | Un `.md` en disco no declara un agente | sostenido | sí | `test_e03_un_archivo_no_declara_un_agente` |
| E-04 | El registro valida contra su schema, y el schema entra en el subconjunto | sostenido | sí | `test_e04_el_registro_valida_contra_su_schema` |
| E-05 | Un solo roster; `roster.json` sin `agents` ni `skills` | sostenido | sí | `test_e05_hay_un_solo_roster` |
| E-06 | `dev-tool-builder` es `VALID` con cero skills | sostenido | sí | `test_e06_infraestructura_con_cero_skills` |
| E-07 | Orquestador y crítico son `VALID` con cero skills | sostenido | sí | `test_e07_orquestador_y_critico_con_cero_skills` |
| E-08 | Especialista sin ninguna `INSTALLED`: `AGENT_SKILL_POLICY_INVALID` | sostenido | sí | `test_e08_un_especialista_sin_skills_instaladas` |
| E-09 | Tipo inválido: `AGENT_TYPE_INVALID` | sostenido | sí | `test_e09_un_tipo_que_no_existe` |
| E-10 | `AGENT_FILE_MISSING` y `AGENT_ID_MISMATCH` | sostenido | sí | `test_e10_archivo_que_falta_y_identidad_que_no_coincide` |
| E-10b | Id duplicado: `DUPLICATE_AGENT_ID` | sostenido | sí | `test_e10b_dos_agentes_con_el_mismo_id` |
| E-10c | Dominio con dos dueños: `DUPLICATE_DOMAIN_OWNER` | sostenido | sí | `test_e10c_dos_duenos_del_mismo_dominio` |
| E-11 | `INSTALLED` con archivo: `SKILL_AVAILABLE`, rutea | sostenido | sí | `test_e11_una_skill_instalada` |
| E-12 | `dev-miba` y `dev-esb` son `DECLARED_NOT_INSTALLED` y dan `SPECIALIZED_SKILL_GAP` | sostenido | sí | `test_e12_las_dos_pendientes` |
| E-13 | `dev-integration` es `VALID_WITH_PENDING_SKILLS` y sus otras cuatro skills rutean | sostenido | sí | `test_e13_el_agente_sigue_valido_con_pendientes` — segunda pasada; la primera frase la cubre `test_e12` |
| E-14 | `INSTALLED` sin archivo: `SKILL_FILE_MISSING` | sostenido | sí | `test_e14_una_instalada_sin_su_archivo` |
| E-15 | Skill bajo dos dueños: `SKILL_OWNER_CONFLICT` | sostenido | sí | `test_e15_la_misma_skill_bajo_dos_duenos` |
| E-15b | `# Skill:` ajeno: `SKILL_ID_MISMATCH` | sostenido | sí | `test_e15b_una_skill_que_dice_ser_otra` |
| E-16 | `DEPRECATED` no rutea | sostenido | sí | `test_e16_una_skill_deprecada_no_rutea` |
| E-17 | `SKILL_NOT_DECLARED_FOR_AGENT` no es `UNDECLARED_SKILL` | sostenido | sí | `test_e17_una_skill_que_el_agente_no_declara` |
| E-18 | `dev-iniciador-code` es `ORPHAN_AGENT`: no se adopta, no se borra, no rutea | sostenido | sí | `test_e18_el_huerfano` |
| E-18b | Huérfano reconocido es aviso; uno nuevo es error; ninguno rutea | sostenido | sí | `test_e18b_conocido_es_aviso_y_nuevo_es_error` |
| E-19 | Skill en disco sin declarar: `UNDECLARED_SKILL` | sostenido | sí | `test_e19_una_skill_en_disco_sin_declarar` |
| E-20 | Las cuentas del reporte se calculan | sostenido | sí | `test_e20_las_cuentas_se_calculan` |
| E-21 | `dev-backend` rutea | sostenido | sí | `test_e21_dev_backend_rutea` |
| E-22 | `dev-quality` con `dev-test-automation` es `ROUTABLE` | sostenido | sí | `test_e22_quality_con_su_skill` |
| E-23 | Todo estado de error rutea cerrado | sostenido | sí | `test_e23_todo_error_rutea_cerrado` |
| E-24 | `SPECIALIZED_SKILL_GAP` no deriva a `dev-tool-builder` | sostenido | sí | `test_e24_un_hueco_de_skill_no_llama_al_constructor` |
| E-25 | `CAPABILITY_GAP` deriva; los dos huecos no se mezclan | sostenido | sí | `test_e25_un_hueco_de_capacidad_si_deriva` |
| E-26 | La unidad recibe agente, skills y `agentExists` del registro | sostenido | sí | `test_e26_la_unidad_sale_del_registro` |
| E-27 | La unidad lleva el estado de cada skill | sostenido | sí | `test_e27_la_unidad_lleva_el_estado_de_cada_skill` |
| E-28 | Con la matriz vacía, ningún agente válido da `agentExists: false` | sostenido | sí | `test_e28_la_matriz_vacia_no_borra_agentes` |
| E-29 | Alta, baja o renombre de un `.md` sin tocar el registro pone la suite en rojo | sostenido | sí | `test_e29_la_compuerta_mira_registro_contra_disco` |

Todos los tests están en `tests/casos/22_registro_agentes.py`.

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** Es la marca que pide
> ADR-0006: un test que nunca se vio fallar no probó que puede fallar. Acá no hay ninguno.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **E-02 contradecía a E-18.** Decía que un agente no declarado da `AGENT_NOT_FOUND` "aunque su
   archivo exista en disco", y E-18 —junto con la sección "El disco diagnostica, el registro
   decide"— pide `ORPHAN_AGENT` para ese mismo caso. El test de E-02 usaba `dev-inventado`, sin
   archivo, justo la mitad donde no había conflicto. Se corrigió la **redacción** de E-02, con una
   nota fechada en la spec, y el test ahora cubre las dos mitades. La segunda pasada juzgó la
   corrección y la dio por legítima: no se perdió ninguna afirmación, porque el caso con archivo ya
   lo sostenía E-18 con su propio test.
2. **E-13 afirmaba cuatro y probaba una.** El test ruteaba sólo `dev-openid-connect`. Ahora saca
   las skills instaladas del registro, afirma que son exactamente cuatro y cuáles, y rutea cada
   una. Una mutación que deja de rutear una sola —`dev-service-integration`— lo pone en rojo.

## Lo que queda abierto, anotado y no escondido

1. **La primera frase de E-13 la sostiene un test con el nombre de E-12.** "Una skill
   `DECLARED_NOT_INSTALLED` no se rutea" pone la suite en rojo si se rompe, pero lo detecta
   `test_e12`, no `test_e13`. No afecta el veredicto; se anota para quien toque esos tests.

## Lo que ningún test cubre y se mira con los ojos

Que el orquestador, en una sesión real, respete el `routable: false` del registro al elegir a quién
delegar. El registro decide y la suite lo prueba; lo que haga un modelo con esa decisión se ve
abriendo una sesión.
