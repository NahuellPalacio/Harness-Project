# La regla de secretos

Es lo único que el harness impide. Todo lo demás avisa.

## Dos mecanismos, no dos alternativas

> **`permissions.deny` protege lo que no se debe leer.
> El hook protege lo que no se debe escribir.**

Los dos se instalan siempre y ninguno reemplaza al otro.

### `permissions.deny` — rutas

En `.claude/settings.json`. Impide que Claude Code lea `secrets/`, `.env*`, claves
privadas, keystores, `.npmrc` y compañía.

Ventajas: **costo cero** (no arranca ningún proceso), funciona aunque los hooks estén
rotos, y es auditable de un vistazo por alguien que no conoce el harness.

Verificado: un `Read` sobre `secrets/` devuelve *"denied by your permission settings"*.

> ⚠️ **Límite honesto.** Cubre lo que Claude Code puede resolver como una ruta. Una lectura
> indirecta —construir el path en una variable y leer desde ahí— puede escapar. Es
> *best-effort*, no una garantía. No lo uses como control único sobre material que no
> puede filtrarse.

### El hook `PreToolUse` — contenido

Lo que `deny` no puede ver: el secreto que Claude está por **escribir**, que no vive en
ninguna ruta prohibida. Mira `content`, `new_string`, `command` y las ediciones de
`MultiEdit`.

## Dos niveles de confianza

Esta distinción importa más que los patrones en sí.

| Confianza | Qué hace | Cuándo |
|---|---|---|
| **alta** | **bloquea** | Formas inequívocas. Una clave privada PEM no es otra cosa |
| **media** | **pregunta** | Formas plausibles pero ambiguas. Decide la persona, no el harness |

**El falso positivo es el riesgo existencial de este harness.** Uno que traba trabajo
legítimo se desinstala esa misma semana, y ahí se pierde también la protección que sí
servía. Por eso lo ambiguo pregunta en vez de bloquear.

De alta confianza: claves privadas PEM, identificadores de AWS, tokens de GitHub y Slack,
API keys de Google, JWT emitidos, credenciales embebidas en una URL, contraseñas en cadenas
de conexión, `client_secret` literales, cabeceras `Authorization: Bearer` con token.

De confianza media: asignaciones con nombre de credencial y un valor largo de alta entropía.

## Lo que NO bloquea, a propósito

Referirse a un secreto sin escribirlo es lo correcto, y es frecuente. Nada de esto se traba:

```
password = ${DB_PASSWORD}          const apiKey = process.env.API_KEY
password = $env:DB_PASSWORD        password = os.getenv("DB_PASSWORD")
password = %DB_PASSWORD%           String s = System.getenv("CLIENT_SECRET");
api_key  = "your-api-key-here"     client_secret = "example-para-la-doc"
password = xxxxxxxxxxxx            access_token = <completar-en-el-deploy>
password=
```

Ni tampoco un hash de commit, una ruta larga, o una historia de usuario que hable de
contraseñas. Hay 16 casos negativos cubiertos por tests, y valen tanto como los positivos.

## El motivo nunca repite el secreto

El texto que devuelve el hook entra al contexto de Claude y queda en la transcripción.
Reproducir ahí el valor que se acaba de impedir escribir sería absurdo, así que el mensaje
dice la forma y el largo, no el contenido:

```
Eso es un token de GitHub. Movelo a una variable de entorno y rotalo: un token que
estuvo en un archivo ya no es confiable. [token-github: ghp_A1b2C3d4... (40 caracteres)]
```

Y el motivo siempre dice **qué hacer**, no qué se impidió. `usá una variable de entorno`
sirve; `operación denegada` no.

## Agregar o ajustar un patrón

Todo vive en `comun/reglas/secretos.patrones.json`. **No hace falta tocar una línea de
código**, ni siquiera para cambiar la severidad de un patrón existente.

```jsonc
{
  "id": "token-de-jira",
  "confianza": "alta",              // o "media" para que pregunte en vez de bloquear
  "regex": "...",
  "motivo": "Qué hacer en lugar de esto."
}
```

Si algo produce un falso positivo, hay dos salidas y las dos son legítimas:

1. Agregar el caso a `ignorar.patrones` — la mejor, porque arregla el problema para todos.
2. Bajar el patrón de `alta` a `media`, para que pregunte en vez de bloquear.

Después agregá el caso a `tests/casos/04-secretos.ps1` como `Assert-NoDetecta`. Un falso
positivo que no queda cubierto por un test vuelve.

## La tercera capa

`install.ps1` agrega al `.gitignore` del proyecto el bloque de secretos: `secrets/`,
`.env*`, `*.secret`, `*.pem`, `*.key`, `*.pfx`, `*.p12`, `*.keystore`.

No cuesta nada y ataja el caso que ni `deny` ni el hook ven: el archivo que ya existía
antes de instalar el harness.
