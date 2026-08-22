# gcba-harness

This repository is the factory of the harness. Every version released from here has to be
installed again wherever the harness is already in use.

## Always on

Skill `concise-replies` (`.claude/skills/concise-replies/SKILL.md`) governs every reply of every
session in this repository. Read it before answering.

## How work is done here

The method is [ADR-0006](docs/adr/0006-sdd-como-metodo-de-los-proyectos.md):

```
especificar   que se construye y como se prueba que cumple
construir
testear       los tests salen de la spec, con el codigo ya armado
verificar     alguien distinto contrasta contra la spec
```

The artifacts of a change live in `docs/cambios/<slug>/` — `spec.md`, and `verificacion.md` when it
is verified. Scenarios are numbered `E-nn` and each carries the mark `rojo visto`. A test that
covers a scenario names its id in the title or in a comment.

Whoever builds does not verify. `harness-spec-refuter` rules against the spec and does not write
its own verdict.

Four verdicts: `sostenido`, `contradicho`, `leído`, `sin sustento`. A verdict with any
`contradicho` or `sin sustento` does not close the change. A `verificacion.md` that exists closes
nothing on its own.

`leído` is [ADR-0009](docs/adr/0009-un-escenario-sobre-un-modelo-se-verifica-por-lectura.md) and it
is narrow: **only a scenario whose subject is a run of a model**, marked `· verificación: lectura`
in the spec, with a dated reading by a named person who is not the builder. It closes a change
and it is weaker than `sostenido` — count the two separately, never folded together. Anything a
deterministic test could reach does not get the mark.

## The gate

```powershell
.\tests\Invoke-Tests.ps1
```

Green before anything is called done. 399 tests, two engines, one exit code. `install.ps1` uses the
same suite as its own gate.

🔴 If the suite is killed mid-run, check the tree before anything else. `tests/casos/03-instalador.ps1`
breaks versioned files on purpose and restores them in a `finally` that does not survive the process
being killed — it already left `pre-tool-use.py`, the only blocking rule of the harness, broken in
the tree during 0.13.0:

```bash
git checkout -- comun/hooks/pre-tool-use.py comun/hooks/lib/zonas.py
```

## Who owns what

| Agent | Owns |
|---|---|
| `harness-hook-engineer` | `comun/hooks/`, `comun/checks/`, `*/checks/` |
| `harness-backend-engineer` | `install.ps1`, `tests/`, manifests, lockfile |
| `harness-staff-engineer` | Performance, size, simplicity — behaviour frozen |
| `harness-spec-refuter` | Verdicts against a spec. Runs the tests, writes nothing |
| `harness-budget-auditor` | Always-loaded context cost and the `CLAUDE.md` ceilings |

## The skills of the factory

| Skill | When |
|---|---|
| `write-a-spec` | Starting a change, before writing code |
| `write-a-verdict` | The refuter ruled and the verdict has to be recorded |
| `close-a-version` | The change closed and the version has to be released |
| `note-a-pending` | Something appears that will not be done now |

## Language

Spanish, rioplatense, for everything that ships: `comun/`, `harnesses/`, `docs/`, `CHANGELOG.md`,
commit messages and every reply. English inside `.claude/`, `Pendientes/`, file names, commands,
code and identifiers.

## Pending work

`Pendientes/Fix-Harness/PENDIENTES-FH.md` holds bugs and fixes.
`Pendientes/Ideas-Harness/PENDIENTES-I.md` holds ideas.

Both files are written in English and both are the source of work for the agents that will run
this factory. An item that closes leaves these files and lands in its version note, under
`docs/versiones/`.
