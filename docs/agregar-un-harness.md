# Agregar un harness

Un harness es un conjunto de reglas, skills, agentes y checks para **un tipo de trabajo**. Hoy
hay dos —`analisis` y `desarrollo`— más `comun/`, que es "el harness que siempre está
instalado" y usa exactamente el mismo contrato.

Agregar el tercero es **un solo paso**: crear su `manifest.json`. `install.ps1` descubre
los harness leyendo el directorio, así que no hay que registrarlo en ningún lado ni tocar
el instalador.

## Crear `harnesses/<id>/manifest.json`

```jsonc
{
  "id": "datos",
  "descripcion": "Análisis de datos y dashboards",
  "prefijo": "dat",                    // OBLIGATORIO. Ver abajo.
  "requiereClaudeCode": "2.1.0",
  "claudeMd": "claude-md/bloque.md",   // lo que se inyecta en el CLAUDE.md del proyecto
  "aporta": {
    "skills": ["skills/*"],
    "agents": ["agents/*"],
    "checks": ["checks/*"]
  },
  "config": {                          // knobs con default, sobreescribibles por proyecto
    "umbralFilas": 100000
  }
}
```

Y la estructura al lado:

```
harnesses/datos/
├── manifest.json
├── claude-md/bloque.md
├── skills/
├── agents/
└── checks/
```

Verificá que quedó bien:

```powershell
.\install.ps1 -Doctor        # tiene que listarlo en "harness disponibles"
```

---

## El prefijo, que es lo que hace que esto escale

**Todo asset que aporta un harness lleva su prefijo.** `analisis` prefija `hu-`, `desarrollo`
prefija `dev-`, `datos` prefijaría `dat-`. El prefijo lo declara el `manifest.json` de cada uno.

No es cosmético: es lo que hace **estructuralmente imposible** que dos harness aporten dos
cosas con el mismo nombre. Por eso instalar varios en un mismo proyecto siempre es seguro, y
por eso `install.ps1` no necesita lógica para resolver conflictos — solo verifica que los
prefijos sean disjuntos y aborta si no lo son.

Un proyecto puede tener varios harness a la vez:

```powershell
.\install.ps1 -Project C:\Work\GCBA\MiProyecto -Harness analisis,desarrollo
```

## Dónde va cada cosa — la pregunta que hay que hacerse

Antes de poner una regla en un harness nuevo, pasala por esto:

| Si la regla… | Va a |
|---|---|
| Aplica a cualquier tipo de trabajo | `comun/` |
| Aplica solo a este tipo de trabajo | `harnesses/<id>/` |
| Depende del proyecto, no del tipo de trabajo | `harness.config.json`, con default en el manifest |
| Se necesita **en cada turno** | El bloque `claude-md/` |
| Se necesita **a veces** | Una skill |

La última fila es la que más se viola y la que más caro sale. **Todo lo que no se necesita en
cada turno es una skill**, sin excepciones: una skill cuesta unos 100 tokens de nombre y
descripción, y se expande solo cuando alguien la invoca. Una línea en el bloque del
`CLAUDE.md` ocupa ventana durante toda la sesión, la use alguien o no.

Agregar una línea al `CLAUDE.md` siempre va a ser más fácil que escribir una skill. Por eso
hay techos numéricos por zona y un check que avisa cuando se pasan: sin una compuerta, todo
harness engorda hasta comerse el contexto que vino a ahorrar.

## Dos cosas que un harness NO puede aportar

- **Hooks.** Los cuatro hooks son infraestructura y viven en `comun/hooks/`. Un harness aporta
  `checks/`, que son los que el hook de `PostToolUse` ejecuta. La separación existe para que
  agregar una regla no pueda romper el manejo de stdin, el encoding o el control de errores.
- **Reglas que bloquean.** El único bloqueo del harness es la regla de secretos, y vive en
  `comun/`. Todo lo demás avisa. Ver el `README.md`.
