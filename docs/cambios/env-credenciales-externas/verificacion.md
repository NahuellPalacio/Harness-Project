# Verificación — Las credenciales externas del proyecto: `.env` y `.env.example`

**Estado:** cerrado · **Fecha:** 02-09-2026

Este documento es lo que cierra el cambio según [ADR-0006](../../adr/0006-sdd-como-metodo-de-los-proyectos.md):
el veredicto por escenario de quien verificó, que no es quien construyó.

**Primera pasada de `harness-spec-refuter`**, el 02-09-2026 — este cambio no tenía
`verificacion.md` todavía. Corrió `.\tests\Invoke-Tests.ps1` completo (**801/801**) y reprodujo a
mano, fuera de la suite, los nueve escenarios: los seis de instalador sobre proyectos descartables
propios (no los que usó la suite), y los tres del catálogo de secretos directo contra
`lib/secretos.py`, en memoria, sin tocar el disco del repositorio.

**Resultado: 9 escenarios sostenidos, 0 leídos, 0 contradichos, 0 sin sustento.**

**El cambio cierra.**

## Los veredictos

| # | Escenario | Veredicto | Rojo visto | Dónde se prueba |
|---|---|---|---|---|
| E-01 | Instalación nueva deja `.env.example` idéntico a la plantilla | sostenido | no consta | `17-env-instalador.ps1` |
| E-02 | Sin `desarrollo`, no se escribe ninguno de los dos | sostenido | no consta | `17-env-instalador.ps1` |
| E-03 | `-Update` pisa `.env.example` con la plantilla actual | sostenido | sí | `17-env-instalador.ps1` |
| E-04 | `.env` nace con las mismas variables, con placeholder | sostenido | no consta | `17-env-instalador.ps1` |
| E-05 | `-Update` no toca un `.env` preexistente | sostenido | sí | `17-env-instalador.ps1` |
| E-06 | `-Uninstall` conserva `.env` y `.env.example` | sostenido | sí | `17-env-instalador.ps1` |
| E-07 | Un token con forma `glpat-…` dispara `token-gitlab`, alta | sostenido | sí | `04_secretos.py::test_paridad_con_powershell` |
| E-08 | Un token con forma `sha256~…` dispara `token-openshift`, alta | sostenido | sí | `04_secretos.py::test_paridad_con_powershell` |
| E-09 | El `.env.example` real no dispara ningún patrón | sostenido | sí | `04_secretos.py::test_e09_env_example_no_dispara_nada` |

> 📌 **`rojo visto: no consta` no invalida un veredicto, lo pondera.** E-01, E-02 y E-04 no se
> vieron romperse a propósito; E-03, E-05, E-06, E-07, E-08 y E-09 sí, cada uno reproducido tanto
> por quien construyó como, de forma independiente, por el refutador.

## Lo que la verificación encontró y no habría encontrado un test verde

1. **Una sola mutación confirmó dos escenarios a la vez, y el refutador lo reprodujo por su
   cuenta.** Volver a sumar `.env.example` a `$instalados` —el error obvio, calcado del resto del
   código de instalación— rompe E-03 y E-06 juntos: entrar al inventario del lockfile lo vuelve
   "editado a mano" para `-Update` (que lo preserva como `.nuevo` en vez de pisarlo) y borrable
   para `-Uninstall`. Las dos consecuencias comparten una sola causa.
2. **Un detalle de trazabilidad, señalado y no contado como falla:** `test_paridad_con_powershell`
   —el test genérico que cubre E-07 y E-08 vía los casos del fixture— no nombra esos ids en su
   propio docstring; la mención vive en el comentario de `test_e09_env_example_no_dispara_nada`.
   Es el mismo patrón que ya usan `token-github` y `token-slack` en el mismo archivo —ninguno de
   los dos está nombrado por id en el docstring genérico tampoco—, así que no es una desviación
   nueva de este cambio.
3. **Nada más.** Los nueve escenarios resultaron sólidos en la primera pasada.

## Lo que queda abierto, anotado y no escondido

Nada de este cambio queda abierto. Lo declarado afuera en la spec —el consumidor que
efectivamente lea estas variables, el patrón de Jira, la generalización a otros harnesses— es
trabajo futuro, no una verificación pendiente.

## Lo que ningún test cubre y se mira con los ojos

Nada. El sujeto de los nueve escenarios es el comportamiento de `install.ps1` y del catálogo de
secretos, los dos deterministas y sin modelo de por medio — no hay escenario de lectura en este
cambio.
