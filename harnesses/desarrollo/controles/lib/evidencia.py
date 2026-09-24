"""La evidencia de los checks de ES0902: catalogo cerrado, igualdad de ids y regla de salida.

🔴 **Esto no es un control.** No se declara en `control-registry.json` y no aprueba nada. Es la
forma de leer evidencia que Vu1 y Vu2 aprendieron en sus refutaciones, escrita una vez para no
copiarla una tercera:

1. Un catalogo **cerrado**: un campo que no esta declarado deja el item mal formado, asi que no hay
   donde guardar un valor sensible. Lo repetido o mal formado no cuenta, y queda anotado.
2. Un id **nombra** a otro por igualdad de texto en NFC, recorriendo los textos del item. No por
   subcadena del JSON escapado: `ciudadano-v2` no es `ciudadano`, y un id con acentos es un id.
3. Una **regla de salida** unica: nada con forma de credencial sale, venga de donde venga. La clave
   termina en la palabra (`DB_PASSWORD=` si, `passwordPolicy:` no), un `:` o una `/` antes no la
   esconde, y de un ARN se saca solo el prefijo de un secreto de un gestor. Una cookie o un id de
   sesion (`JSESSIONID=`, `sid=`, `Cookie: SESSION=`), un codigo de autorizacion (`code=`) y un
   `id_token_hint` son credenciales: lo son para Vu3, que gobierna justamente la sesion. Una
   cookie es `NOMBRE=VALOR`, asi que `session:portal`, `cookie:check-1` o `consid=3` son ids. Un
   `code` suelto es siempre un codigo de autorizacion, tambien con un valor de solo digitos.
   Una contrasena se reconoce por la palabra que la anuncia, como en E-03b del reporte de
   seguridad: `password`, `passwd`, `pwd`, `pass`, `passphrase`, `contraseña`, `contrasenia` o
   `clave`, sin letra ni digito pegado antes y sin letra, digito ni `_` pegado despues, seguida de
   un valor (`clave: x`, `pass=x`, `--password x`; `password_hash=` y `bypass=` no). Para las
   palabras en castellano y para `pass` un espacio solo no separa: tiene que haber `:`, `=`, `=>`,
   `:=`, `>` o una comilla, asi "la clave del tramite es obligatoria" y "pass-through" salen
   enteras (Vu5, refutador, pase 1). `pw` y `pin` cuentan seguidos de `:` o `=`. El texto se
   compara en NFC, asi que una `ñ` descompuesta tambien cuenta.
   La regla alcanza tambien a las claves de un diccionario: una clave con forma de credencial sale
   `[redactado]`, y si dos claves se redactan igual no se funden: la segunda sale
   `[redactado]-2`, en el orden de las claves originales.
4. Un id de evidencia que no es texto, o que esta vacio, no es un id: el item es ilegible y no
   se usa como clave de nada.

Vu1 y Vu2 todavia tienen su copia. Migrarlos es trabajo aparte, anotado en `PENDIENTES-FH.md`.
"""
import json
import re
import unicodedata

SECRETOS = tuple(re.compile(p) for p in (
    # La clave termina en la palabra, con cualquier prefijo: `DB_PASSWORD=`, `JSESSIONID=`.
    r"(?i)(?<![\w-])[\w-]*?(password|passwd|pwd|secret|token|api[_-]?key|sessionid|session_id|"
    r"sessid|id_token_hint|auth(orization)?[_-]?code)[\"']?\s*[:=]\s*\S",
    # Una cookie es NOMBRE=VALOR, y la palabra es la clave entera o su ultimo tramo:
    # `SESSION=`, `KEYCLOAK_SESSION=`, `sid=` si; `session:portal` y `consid=3` no.
    r"(?i)(?<![\w-])([\w-]*[_-])?(session|sid|cookie)[\"']?\s*=\s*\S",
    # El encabezado, con la cookie que sea: `Cookie: foo=` si, `cookie:check-1` no.
    r"(?i)(?<![\w-])(set-)?cookie\s*:\s*[^\s=;:]+=\S",
    # `code=` suelto es el codigo de autorizacion de OAuth, con el valor que sea: uno de solo
    # digitos tambien lo es (refutador, pase 3). `status_code=` no, por el `_` de antes.
    r"(?i)(?<![\w-])code\s*[:=]\s*\S",
    # E-03b del reporte de seguridad: la palabra anuncia la contrasena, y despues viene un valor.
    # En ingles un espacio alcanza: `--password x`, `set password x`.
    r"(?i)(?<![A-Za-z0-9])(passphrase|password|passwd|pwd)"
    r"(?![A-Za-z0-9_])[ \t\"'`:=>\-\\]*[^\s\"'`<,;\\]",
    # En castellano y con `pass` no: la palabra aparece en prosa. Hace falta un separador de verdad.
    r"(?i)(?<![A-Za-z0-9])(pass|contrase(ñ|n)a|contrasenia|clave)(?![A-Za-z0-9_])"
    r"[ \t]*(=>|:=|[:=>\"'`])[ \t\"'`:=>\-\\]*[^\s\"'`<,;\\]",
    # `pw` y `pin`, solo seguidos de `:` o `=`.
    r"(?i)(?<![A-Za-z0-9])(pw|pin)(?![A-Za-z0-9_])[ \t]*[:=][ \t\"'`]*[^\s\"'`<,;\\]",
    r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}",
    r"://[^/\s:@]+:[^/\s@]+@",
    r"\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----"))
PREFIJO_DE_GESTOR = re.compile(r"arn:aws[\w-]*:secretsmanager:[a-z0-9-]+:[0-9]+:secret:")
REDACTADO = "[redactado]"

TEXTO, LISTA, BOOLEANO = "text", "list-of-text", "bool"
MAL_FORMADA = "malformed-evidence"


def es_secreto(texto):
    if not isinstance(texto, str):
        return False
    resto = PREFIJO_DE_GESTOR.sub("", unicodedata.normalize("NFC", texto))
    return any(p.search(resto) for p in SECRETOS)


def depurar(dato):
    """La regla de salida: todo texto con forma de credencial sale `[redactado]`."""
    if isinstance(dato, dict):
        # 🔴 Las claves tambien: un id que sale como clave es un id (refutador de Vu4, pase 1). Dos
        # claves que se redactan igual no se funden: se numeran en el orden de las originales, y
        # nunca pisan una clave que ya estaba.
        nombres, usados = {}, {k for k in dato if not es_secreto(k)}
        for k in sorted((k for k in dato if es_secreto(k)), key=str):
            nombre, n = REDACTADO, 1
            while nombre in usados:
                n += 1
                nombre = "%s-%d" % (REDACTADO, n)
            usados.add(nombre)
            nombres[k] = nombre
        return {nombres.get(k, k): depurar(v) for k, v in dato.items()}
    if isinstance(dato, list):
        return [depurar(v) for v in dato]
    return REDACTADO if es_secreto(dato) else dato


def textos(dato):
    if isinstance(dato, dict):
        for k, v in dato.items():
            yield str(k)
            yield from textos(v)
    elif isinstance(dato, list):
        for v in dato:
            yield from textos(v)
    elif isinstance(dato, str):
        yield dato


def nfc(texto):
    return unicodedata.normalize("NFC", texto) if isinstance(texto, str) else texto


def igual(a, b):
    """🔴 La unica comparacion de ids, en NFC. Lo legible y lo ilegible se nombran con la misma
    regla: si no, un "no" legible pesa menos que uno mal formado (Vu2, segundo pase)."""
    return nfc(a) == nfc(b)


def en(ident, lista):
    return any(igual(ident, x) for x in (lista or []))


def menciona(dato, ident):
    """Si algun texto del dato ES el id, en NFC."""
    buscado = nfc(ident)
    return any(nfc(t) == buscado for t in textos(dato))


def bien_formada(e, forma, obligatorios):
    """Si el item tiene la forma declarada y ningun campo de mas."""
    if not isinstance(e, dict) or set(e) - set(forma):
        return False
    for campo, tipo in forma.items():
        valor = e.get(campo)
        if valor is None:
            if campo in obligatorios:
                return False
            continue
        if tipo == TEXTO and not isinstance(valor, str):
            return False
        if tipo == LISTA and not (isinstance(valor, list) and all(isinstance(v, str) for v in valor)):
            return False
        if tipo == BOOLEANO and not isinstance(valor, bool):
            return False
    referencia = e.get("reference")
    return referencia is None or bool(referencia.strip())


def id_de(e):
    """El id del item en NFC, o `None` si no tiene uno: texto y no vacio.

    🔴 Es la unica puerta de un id a una comparacion o a una clave. Una lista o un dict como id
    no es un id, y usarlo de clave rompia la evaluacion en vez de impedir el PASS (Vu3, pase 2).
    """
    ident = e.get("evidenceId") if isinstance(e, dict) else None
    return nfc(ident) if isinstance(ident, str) and ident.strip() else None


def etiqueta(e):
    """Como se nombra un item en la salida: su id si lo tiene, y si no `malformed-evidence`."""
    return e["evidenceId"] if id_de(e) is not None else MAL_FORMADA


def catalogo(caso, forma, obligatorios):
    """(catalogo, crudas, repetidos, torcidas). Lo repetido o mal formado no cuenta."""
    crudas = (caso or {}).get("evidence")
    crudas = crudas if isinstance(crudas, list) else []
    # 🔴 Los ids se normalizan ANTES de contar: dos ids iguales en NFC son el mismo id, repetido.
    # El catalogo se indexa en NFC, y quien busca en el busca en NFC (Vu2, tercer pase).
    ids = [i for i in map(id_de, crudas) if i is not None]
    repetidos = sorted({i for i in ids if ids.count(i) > 1})
    sanas, torcidas = {}, set()
    for e in crudas:
        ident = id_de(e)
        if ident is None or not bien_formada(e, forma, obligatorios):
            torcidas.add(etiqueta(e))
        elif ident not in repetidos:
            sanas[ident] = e
    return sanas, crudas, repetidos, sorted(torcidas)


def claves(lista):
    """Un conjunto de ids citados, en NFC, para buscar en el catalogo."""
    return {nfc(x) for x in (lista or []) if isinstance(x, str)}


def ilegibles_sobre(ident, catalogo_, crudas):
    """Los items que nombran `ident` y no se pueden leer: repetidos, mal formados o sin id."""
    salida = set()
    for e in crudas:
        propio = id_de(e)
        legible = propio is not None and catalogo_.get(propio) is e
        if not legible and menciona(e, ident):
            salida.add(etiqueta(e))
    return sorted(salida)


def ordenadas(lista):
    """Toda lista de salida se ordena por su contenido completo."""
    return sorted(lista, key=lambda x: json.dumps(x, sort_keys=True, default=str))
