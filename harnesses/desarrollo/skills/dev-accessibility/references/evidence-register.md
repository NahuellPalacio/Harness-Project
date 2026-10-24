# Evidence register

One record per change, per criterion: what was approved, what failed, what does not apply and what was not tested, with where, what proves it and how to fix it. Contract name `a11y-evidence/1`. It is a JSON file, validated by `python scripts/wcag.py register validate <file>`.

Start from a template, or from a static review:

```
python scripts/wcag.py register template --level AA --components form-text,button --out evidence.json
python scripts/review.py src/forms/ --register evidence.json --components form-text,button
```

Both put every criterion of the target in `not_tested`, 4.1.1 in `not_applicable`, and the three manual tests in `not_performed`. The review turns into `fail` only what failed by static evidence, with file and line. **It never writes `pass`.**

## Shape

```json
{
  "schema": "a11y-evidence/1",
  "target": { "wcag": "2.2", "level": "AA", "additional": ["2.4.13"] },
  "scope": { "description": "Alta de turno", "files": ["src/alta.tsx"], "components": ["form-text", "button"] },
  "tests": { "browser": "not_performed", "keyboard": "performed", "screen_reader": "not_performed" },
  "static_analysis": { "run": true, "files_analyzed": 3, "not_analyzed": [{ "file": "src/Campo.tsx", "reason": "componente <TextField> no resuelto" }] },
  "criteria": [
    { "sc": "1.1.1", "result": "fail", "location": "src/alta.tsx:42", "evidence": "img-missing-alt: <img>",
      "evidence_types": ["static"], "fix": "Agregar alt con el equivalente de la imagen.", "origin": "wcag", "component": "button" },
    { "sc": "2.1.1", "result": "pass", "evidence": "Recorrido completo con Tab, Enter y Escape",
      "evidence_types": ["keyboard"] },
    { "sc": "1.2.2", "result": "not_applicable", "reason": "La pantalla no tiene video" },
    { "sc": "3.2.3", "result": "not_tested", "reason": "Hace falta el conjunto de páginas" }
  ],
  "summary": { "pass": 1, "fail": 1, "not_applicable": 1, "not_tested": 0, "fail_by_level": { "A": 1, "AA": 0, "AAA": 0 } }
}
```

`summary` is optional. If present, its four counts must equal the rows the target requires (plus 4.1.1), and an optional `fail_by_level` (`{"A": 14, "AA": 11, "AAA": 0}`) must equal the failed rows per level — the mistake of reporting 13 and 12 when the rows give 14 and 11. A row for a criterion the target does not require — an AAA in an AA register — is accepted, is not demanded, and is counted apart (`wcag.py register validate` prints it on its own line); it never enters the summary.

## Results

| Value | Spanish label | Needs |
|---|---|---|
| `pass` | aprobado | `evidence` and `evidence_types`; the manual tests the criterion requires must be `performed` and cited |
| `fail` | fallido | `location`, `evidence` and `fix` |
| `not_applicable` | no aplicable | `reason`, taken from the criterion's own text |
| `not_tested` | no probado | `reason` |

`not_applicable` is for a criterion that does not apply: no video means no 1.2.x; a page that is a step in a process is exempt from 2.4.5. A criterion that applies but could not be assessed — it needs other pages, an asset is missing, the manual pass was not run — is `not_tested`, never `not_applicable`.

## The three manual tests

`browser`, `keyboard` and `screen_reader` are `performed` or `not_performed`, and they start `not_performed`. The criteria data says which ones each criterion needs before it can be `pass` (`wcag.py criterion <id>` prints them); it is a rule of the Harness and it is conservative. A `pass` that cites a test that was not performed is rejected.

| Evidence type | Meaning |
|---|---|
| `static` | a static analysis found it |
| `code_review` | somebody read the code or the content |
| `contrast_computed` | `contrast.py` on explicit pairs |
| `browser`, `keyboard`, `screen_reader` | the manual test of that name |

## What the validator rejects

A missing criterion of the target (no row is dropped silently) · a duplicate or unknown criterion · a result outside the four · `fail` without location, evidence or fix · `pass` without evidence, or without a required manual test · evidence from a manual test that was not performed · `not_applicable` or `not_tested` without a reason · 4.1.1 as anything but `not_applicable` · a `summary` that does not match the rows.

## Before delivering text that cites criteria

`python scripts/wcag.py levels <file>` checks every «SC n.n.n … (Level X)» and every `| n.n.n | name | X |` row against WCAG 2.2. Delivering a wrong level is the commonest error in an accessibility report.
