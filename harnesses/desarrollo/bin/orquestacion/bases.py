"""Los ambientes de base de datos: que operacion puede correr en cual, decidido ANTES de conectar.

Capacidad transversal del harness. **No es una regla de ES0901**: no tiene senal de aplicabilidad,
no entra en la matriz normativa y no figura en el registro de controles. Las reglas normativas
verifican cumplimiento; esto decide y deniega.

    DEV  ->  FULL
    QA   ->  READ_ONLY
    HML  ->  READ_ONLY
    PRD  ->  READ_ONLY

    lo que la politica no declara  ->  DENY / DATABASE_ENVIRONMENT_UNRESOLVED

🔴 **Los permisos nativos de la base son la segunda barrera, no la primera.** Un usuario de solo
lectura en PRD es una buena practica y no es un control del harness: nadie lo verifica desde aca y
nadie se enteraria si cambiara. Esta es la primera barrera.

🔴 **La clase de la operacion y su efecto son dos dimensiones.** La clase decide el permiso -se
cruza contra el bit del ambiente-, y el efecto decide el riesgo -se le pasa a la compuerta que ya
existe-. Fundirlas en una escala ordenada de cinco seria inventar una segunda doctrina de riesgo, y
dos escalas de riesgo en el mismo harness es UNA escala: la segunda se usa para justificar lo que la
primera no dejaba pasar.

🔴 **La clasificacion se declara y se verifica, y el barrido solo puede SUBIR.** Es la misma
asimetria que ya hace cumplir `tools.controlar_riesgo`: declarar de menos no baja el riesgo, lo
esconde. Un barrido NO es un parser, asi que lo que no puede clasificar se DENIEGA: una negacion
falsa es aceptable y un permiso falso no.

🔴 **El identificador de ambiente es exacto y sensible a mayusculas.** `dev` no es `DEV`.
Normalizarlo es el atajo por el que `prod`, `Prd` y `PROD` acaban resolviendo a algo.

🔴 **Este modulo no importa un driver, no abre una conexion, no ejecuta una sentencia y no habla
con el almacen de secretos.** No lo importa: la funcion del borde de ejecucion RECIBE el almacen
como parametro, asi que "el resolvedor no puede conseguir una credencial" es una propiedad de la
forma de este archivo y no una costumbre. Lo que devuelve son referencias y decisiones.
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rutas                                     # noqa: E402
from . import roster                              # noqa: E402
from . import tools                               # noqa: E402

POLITICA = "database-environment-access-policy.json"
PERFILES = "database-profiles.json"
SCHEMA_DE_POLITICA = "database-environment-access-policy.schema.json"
SCHEMA_DE_PERFIL = "database-profile.schema.json"

# Los cuatro que la politica declara. La lista esta aca para nombrarlos, no para decidir: la
# decision sale del archivo, y un ambiente que el archivo no declare no resuelve.
AMBIENTES_DE_PROMOCION = ("QA", "HML", "PRD")
PERMISOS = ("read", "write", "ddl", "migrations")
MODOS = ("FULL", "READ_ONLY")

# -- las dos dimensiones -------------------------------------------------------

SOLO_LECTURA = "READ_ONLY"
MUTANTE = "MUTATING"
DESTRUCTIVA = "DESTRUCTIVE"
DDL = "DDL"
MIGRACION = "MIGRATION"
CLASES = (SOLO_LECTURA, MUTANTE, DESTRUCTIVA, DDL, MIGRACION)

# 🔴 Los efectos SON los de tools.py, no unos parecidos. Se leen de ahi para que no puedan
# divergir: el dia que esa tupla cambie, esto cambia con ella.
EFECTOS = tools.SIDE_EFFECTS

# La tabla CERRADA: verbo -> (clase, efecto). Nueve, y nada mas.
#
# 🔴 `SHOW`, `DESCRIBE` y `EXPLAIN` NO estan, y es deliberado: no son portables entre motores, y
# `EXPLAIN ANALYZE` en algunos EJECUTA la sentencia. Cuando alguien necesite el verbo de un motor
# concreto se agrega a mano, con el motor nombrado. No se infiere que lo que suena a lectura lo sea.
TABLA = {
    "SELECT": (SOLO_LECTURA, "READ_ONLY"),
    "INSERT": (MUTANTE, "MUTATING"),
    "UPDATE": (MUTANTE, "MUTATING"),
    "DELETE": (MUTANTE, "MUTATING"),        # el alcance lo ajusta el barrido
    "CREATE": (DDL, "MUTATING"),
    "ALTER": (DDL, "MUTATING"),
    "DROP": (DDL, "DESTRUCTIVE"),
    "TRUNCATE": (DDL, "DESTRUCTIVE"),
    "MIGRATION": (MIGRACION, "MUTATING"),
}
VERBOS = tuple(sorted(TABLA))

# Lo unico que puede preceder a un verbo de la tabla adentro de una sentencia. Un primer token
# que no sea un verbo ni esto deja la sentencia sin clasificar.
PREFIJOS = ("WITH",)

# 🔴 Los modificadores que convierten una LECTURA en una ESCRITURA. No son verbos -no abren una
# sentencia- y por eso la tabla de nueve no los ve, pero `SELECT * INTO copia FROM t` escribe
# una tabla y `SELECT ... INTO OUTFILE` escribe un archivo. La spec nombra `SELECT ... INTO` con
# esas palabras como el ejemplo de "una manera de que un UPDATE se lea como un SELECT", y el
# barrido no lo subia. Cada uno declara a que efecto sube.
MODIFICADORES = {
    "INTO": ("MUTATING", MUTANTE),
    "OUTFILE": ("DESTRUCTIVE", DESTRUCTIVA),
    "DUMPFILE": ("DESTRUCTIVE", DESTRUCTIVA),
}

# El comentario condicional de MySQL. No es un comentario: se ejecuta.
COMENTARIO_EJECUTABLE = "/*!"

# Que bit del ambiente exige cada clase. La clase decide el PERMISO.
PERMISO_DE_CLASE = {
    SOLO_LECTURA: "read",
    MUTANTE: "write",
    DESTRUCTIVA: "write",
    DDL: "ddl",
    MIGRACION: "migrations",
}

# Cuando hay empate de efecto, gana la clase mas angosta: informar la compuerta mas especifica
# dice mejor por que se nego. `migrations` y `ddl` son bits aparte de `write`.
PRECEDENCIA = (MIGRACION, DDL, DESTRUCTIVA, MUTANTE, SOLO_LECTURA)

# -- los diez estados ----------------------------------------------------------

SIN_AMBIENTE = "DATABASE_ENVIRONMENT_UNRESOLVED"
SIN_PERFIL = "DATABASE_PROFILE_NOT_FOUND"
SIN_SECRETO = "DATABASE_SECRET_UNRESOLVED"
SIN_CLASIFICAR = "DATABASE_OPERATION_UNCLASSIFIED"
SIN_ESCRITURA = "DATABASE_WRITE_NOT_ALLOWED"
SIN_DDL = "DATABASE_DDL_NOT_ALLOWED"
SIN_MIGRACION = "DATABASE_MIGRATION_NOT_ALLOWED"
SIN_CONEXION = "DATABASE_CONNECTION_FAILED"
SIN_PERMISO = "DATABASE_PERMISSION_DENIED"
SIN_ESQUEMA = "DATABASE_SCHEMA_DISCOVERY_FAILED"

ESTADOS_DE_FALLA = (SIN_AMBIENTE, SIN_PERFIL, SIN_SECRETO, SIN_CLASIFICAR, SIN_ESCRITURA,
                    SIN_DDL, SIN_MIGRACION, SIN_CONEXION, SIN_PERMISO, SIN_ESQUEMA)

# Estos cuatro los produce quien EJECUTA, no el resolvedor: hacen falta una conexion, un almacen
# o una base contestando. Declararlos aca es lo que permite que quien ejecute no invente otros.
ESTADOS_DEL_BORDE = (SIN_SECRETO, SIN_CONEXION, SIN_PERMISO, SIN_ESQUEMA)
ESTADOS_DEL_RESOLVEDOR = tuple(e for e in ESTADOS_DE_FALLA if e not in ESTADOS_DEL_BORDE)

# Que estado le toca a cada permiso negado.
# 📌 La entrada de `read` es inalcanzable por construccion: `acceso_de` devuelve None si el
# ambiente no declara `read: True`, asi que una clase READ_ONLY nunca llega a negarse. Esta
# para que la busqueda no explote y no para que se use; una mutacion no la puede matar.
NEGACION_DE_PERMISO = {"write": SIN_ESCRITURA, "ddl": SIN_DDL, "migrations": SIN_MIGRACION,
                       "read": SIN_AMBIENTE}

RESUELTO = "RESOLVED"

# -- el flujo DEV primero ------------------------------------------------------

FLUJO_DEV_PRIMERO = ("resolve-dev-profile", "schema-discovery", "change-plan",
                     "migration-artifact", "risk-classification", "apply-in-dev",
                     "schema-validation", "tests", "promotion-artifact")

REMEDIO_DE_PROMOCION = ("a database change for QA, HML or PRD travels as a versioned migration "
                        "artifact through the established deployment/CI-CD process, never as a "
                        "direct mutation")


class BasesInvalida(Exception):
    """La politica no se pudo leer. Nunca se degrada a un permiso."""


# -- lo declarado --------------------------------------------------------------

def _texto(valor):
    """El texto declarado, sin los blancos. Vacio si no es texto o no dice nada.

    🔴 Un espacio no es un dato declarado, y un numero, un booleano, una lista o un diccionario
    donde va un texto tampoco: `str(7)` seria "7" y eso es inventarle un valor a un campo que
    vino mal. Se exige `str`.
    """
    if not isinstance(valor, str):
        return ""
    return valor.strip()


def _crudo(valor):
    """El identificador tal como vino, SIN normalizar la capitalizacion.

    🔴 Esta funcion existe para que la decision de no normalizar sea visible. `dev` no es `DEV`:
    normalizar un identificador de ambiente es como `prod` y `PROD` terminan resolviendo a algo.
    """
    return valor if isinstance(valor, str) else ""


# -- la politica y los perfiles ------------------------------------------------

def _armador():
    from . import tools as _t
    return _t._armador()


def _ruta_de_regla(nombre, desde=None):
    """La ruta de un archivo de `reglas/`, en el repositorio Y en un proyecto instalado.

    🔴 Sale de `roster.ruta_de_regla` y no de `rutas.localizar`, que es lo que este modulo
    hacia al principio. `reglas/` cuelga a distinta altura instalado -`.claude/harness/reglas/
    <id>/`- que en el arbol de la fabrica, y `rutas.localizar` sin raices extra encuentra el
    archivo donde corre la suite y NO donde corre el harness: la compuerta entera levantaba
    `BasesInvalida` en un proyecto real y ningun test lo miraba.

    Es exactamente lo que el docstring de `roster` avisa: *dos busquedas de rutas con criterios
    parecidos terminan en que un dia una encuentra el archivo y la otra no.* Lo encontro el
    refutador armando el arbol instalado a mano.
    """
    return roster.ruta_de_regla(nombre, desde or __file__)


def _cargar_json(ruta, que):
    if ruta is None or not os.path.isfile(ruta):
        raise BasesInvalida("no esta %s. La compuerta no decide sin su contrato." % que)
    with io.open(ruta, encoding="utf-8") as f:
        return json.load(f)


def cargar_politica(desde=None):
    """La politica de acceso, del HARNESS. Un proyecto no la edita."""
    return _cargar_json(_ruta_de_regla(POLITICA, desde), POLITICA)


def cargar_perfiles(desde=None):
    """Los perfiles de conexion, del PROYECTO. Se instalan vacios."""
    return _cargar_json(_ruta_de_regla(PERFILES, desde), PERFILES)


def _cargar_schema(nombre, desde=None):
    ruta = rutas.localizar(("schemas", nombre), desde or __file__)
    return _cargar_json(ruta, nombre)


def _validar_contra(documento, nombre, desde=None):
    armador = _armador()
    if armador is None:
        raise BasesInvalida("no esta contexto-armar.py, de donde sale el validador.")
    esquema = _cargar_schema(nombre, desde)
    armador.controlar_soporte(esquema)
    return armador.validar(documento, esquema)


def validar_politica(documento, desde=None):
    """Lista de problemas de la politica contra su schema. Vacia es bien formada."""
    return _validar_contra(documento, SCHEMA_DE_POLITICA, desde)


def validar_perfil(perfil, desde=None):
    """Lista de problemas de un perfil contra su schema.

    🔴 El schema lleva `additionalProperties: false`, asi que un perfil con una contrasena en
    claro se RECHAZA. Es la mitad de la seguridad de esto.
    """
    return _validar_contra(perfil, SCHEMA_DE_PERFIL, desde)


def acceso_de(ambiente, politica=None, desde=None):
    """El bloque de acceso de un ambiente, o None si la politica no lo declara.

    La comparacion es EXACTA: no se normaliza la capitalizacion ni se quitan blancos.
    """
    doc = cargar_politica(desde) if politica is None else politica
    if not isinstance(doc, dict):
        return None
    ambientes = doc.get("environments")
    if not isinstance(ambientes, dict):
        return None
    if not isinstance(ambiente, str) or ambiente not in ambientes:
        return None
    acceso = ambientes[ambiente]
    if not isinstance(acceso, dict) or acceso.get("mode") not in MODOS:
        return None
    # Los dos modos implican lectura. Un ambiente que no la permite no es ninguno de los dos,
    # asi que no es un ambiente declarado — y eso es fallar cerrado, no un permiso raro.
    if acceso.get("read") is not True:
        return None
    for permiso in PERMISOS:
        if not isinstance(acceso.get(permiso), bool):
            return None
    return dict(acceso)


# -- la clasificacion ----------------------------------------------------------

_COMENTARIO_DE_BLOQUE = re.compile(r"/\*.*?\*/", re.S)
_COMENTARIO_DE_LINEA = re.compile(r"--[^\n]*")
_PRIMER_TOKEN = re.compile(r"\s*([A-Za-z_]+)")


# Las formas de encomillar que el enmascarado conoce, con su cierre.
#
# 🔴 **Y esta lista NO es de lo que se puede confiar.** Cuatro refutaciones seguidas encontraron
# la misma especie de defecto por una comilla distinta cada vez -`--` adentro de un literal, el
# dollar-quoting, los backticks, los corchetes, `1--2` de MySQL, `\'`, los bloques anidados de
# Postgres, `a$$b`, el `#`- y cada arreglo agregaba una forma y esperaba que fuera la ultima.
# No lo era, y no lo iba a ser: **donde termina un literal depende del dialecto**, y `engine` es
# un string libre en `database-profile.schema.json`, asi que ningun motor esta fuera de alcance.
#
# Asi que el enmascarado dejo de ser la red. Es una ayuda para NO denegar de mas -que un `DROP`
# adentro de una cadena no suba la clase- y **la seguridad la sostiene `_candidatos_crudos`**,
# que lee el texto sin enmascarar nada. Un error de enmascarado ahora solo puede producir una
# negacion falsa, que es la direccion aceptable, y nunca un permiso falso.
#
# 📌 El corchete se saco. Como quoting es de T-SQL; en Postgres y MySQL es subindice de array, y
# `SELECT ARRAY[[1,2],[3,4]]` -nada exotico- terminaba DENEGADO en los cuatro ambientes porque
# el `]]` no era un cierre escapado sino dos arrays que cierran. Con la lectura cruda ya no hace
# falta para la seguridad, y sacarlo saca la negacion falsa.
CIERRE_DE = {"'": "'", '"': '"', "`": "`"}
ABIERTAS = tuple(sorted(CIERRE_DE))

# El dollar-quoting de Postgres: `$$...$$` y `$tag$...$tag$`. El tag es un identificador, asi
# que `$1` -un placeholder- NO abre nada: exige el `$` de cierre pegado al tag. Y el `$` no
# puede venir pegado a un identificador, porque `a$$b` es un nombre de columna legal en MySQL
# y en Oracle y no abre nada.
_DOLAR = re.compile(r"(?<![A-Za-z0-9_$])\$([A-Za-z_][A-Za-z0-9_]*)?\$")

COMENTARIO_DE_LINEA = "--"
COMENTARIO_ABRE = "/*"
COMENTARIO_CIERRA = "*/"

# 📌 El `#` de MySQL no se maneja, y **no porque denegar de mas sea gratis**: sin la lectura
# cruda, no manejarlo tambien permitia de mas -un `/*` adentro de un `#` si se manejaba y tapaba
# lo que venia detras-. Con la lectura cruda eso ya no puede pasar, y lo unico que queda de no
# manejarlo es que un `#` legitimo de MySQL deniegue de mas.


def _enmascarar(texto):
    """(texto con literales y comentarios tapados, si quedo entero). UNA sola pasada.

    🔴 **Dos pasadas no se pueden ordenar bien, y eso era un fail-open.** La version anterior
    hacia `_sin_literales(_sin_comentarios(texto))`: un `--` o un `/*` ADENTRO de un literal no
    es un comentario para ningun motor, pero para el barrido si, y se comia todo lo que seguia:

        SELECT '--x' ; UPDATE t SET a=1        salia READ_ONLY y PERMITIDO en los cuatro
        SELECT '--' ; DROP TABLE t             salia READ_ONLY y PERMITIDO en PRD

    Y al reves tampoco: tapando literales primero, la comilla de `-- it's fine` se aparea con
    la siguiente comilla del texto y se traga la sentencia que haya en el medio. No hay orden
    correcto entre dos pasadas, asi que se recorre el texto UNA vez y en cada posicion gana lo
    que empieza primero, que es exactamente lo que hace un motor.

    🔴 **Un literal o un comentario de bloque sin cerrar deja el texto sin establecer.** Tapar
    hasta el final escondria lo que venga despues -`SELECT 'abc ; DROP TABLE t`-, asi que se
    devuelve `entero=False` y el pedido se deniega. Un motor tampoco lo ejecutaria.
    """
    salida = []
    i, n = 0, len(texto)
    entero = True
    while i < n:
        c = texto[i]
        dolar = _DOLAR.match(texto, i) if c == "$" else None
        if c in ABIERTAS:
            cierra = CIERRE_DE[c]
            cierre = texto.find(cierra, i + 1)
            # El cierre doblado -`'it''s'`, `` `a``b` ``, `[a]]b]`- no cierra: sigue adentro.
            #
            # 📌 Para las formas SIMETRICAS -`'`, `"`, `` ` ``- es cinturon y tiradores: medido,
            # ninguna entrada las discrimina, porque sin el bucle `'a''b'` se lee como dos
            # literales pegados y se tapa el mismo tramo.
            #
            # Para el corchete SI cambia, y en la direccion de la negacion falsa, no del permiso
            # falso: `[a]]; DROP TABLE t]` es UN identificador de T-SQL, y sin el bucle el
            # corchete cierra temprano, el `;` parte la sentencia y un `DROP` que nunca existio
            # sale destructivo. Se deniega una consulta legitima y quien la escribio no tiene
            # como saber por que.
            while cierre != -1 and cierre + 1 < n and texto[cierre + 1] == cierra:
                cierre = texto.find(cierra, cierre + 2)
            if cierre == -1:
                entero = False
                fin = n
            else:
                fin = cierre + len(cierra)
        elif dolar is not None:
            marca = dolar.group(0)
            cierre = texto.find(marca, dolar.end())
            if cierre == -1:
                # 🔴 Un `$$` que no cierra NO es texto malformado: `SELECT $$PLSQL_LINE FROM
                # dual` es una directiva de Oracle perfectamente valida. A diferencia de una
                # comilla sin cerrar, aca lo correcto es concluir que no era un dollar-quote y
                # seguir de largo. Lo que venga detras lo ve la lectura cruda igual.
                salida.append(c)
                i += 1
                continue
            fin = cierre + len(marca)
        elif texto.startswith(COMENTARIO_DE_LINEA, i):
            fin = i
            while fin < n and texto[fin] not in "\n\r":
                fin += 1
        elif texto.startswith(COMENTARIO_ABRE, i):
            cierre = texto.find(COMENTARIO_CIERRA, i + len(COMENTARIO_ABRE))
            if cierre == -1:
                entero = False
                fin = n
            else:
                fin = cierre + len(COMENTARIO_CIERRA)
        else:
            salida.append(c)
            i += 1
            continue
        salida.append(" " * (fin - i))
        i = fin
    return "".join(salida), entero


def _sentencias(texto):
    """(sentencias del pedido, si el texto quedo entero). Sin comentarios y sin `;` de literal."""
    limpio, entero = _enmascarar(texto)
    return [s.strip() for s in limpio.split(";") if s.strip()], entero


def _verbos_en(sentencia):
    return [v for v in VERBOS if re.search(r"(?i)\b%s\b" % v, sentencia)]


def _candidatos_crudos(texto):
    """Los (clase, efecto) que el texto declara leido SIN enmascarar nada.

    🔴 **Esta es la red, y el enmascarado no lo es.** Las seis formas de la cuarta refutacion
    -y las de la tercera, y las de la segunda- comparten un esqueleto: el tramo que el
    enmascarado tapa no coincide con el que tapa el motor, y en cuanto difieren, un `--`, un
    `/*` o una comilla se come el `;` y el verbo que venia detras. Cada arreglo agregaba una
    forma mas; ninguno podia ser el ultimo, porque donde termina un literal lo decide el
    dialecto y `engine` es un string libre.

    Aca no se enmascara nada, asi que ningun error de enmascarado puede esconder un verbo:

        SELECT 1--2; DROP TABLE t                       MySQL exige un blanco tras el `--`
        SELECT 'a\\' -- ' ; DROP TABLE t                 `\\'` es comilla escapada en MySQL
        SELECT 1 /* /* */ -- */ ; DROP TABLE t          Postgres ANIDA los bloques
        SELECT ARRAY[[1],[2]]; DROP TABLE t             `]]` son dos arrays, no un escape
        SELECT a$$b; DROP TABLE t; SELECT c$$d          `a$$b` es un identificador legal
        SELECT 1 # /*\\n; DROP TABLE t; SELECT 1 /* */   el `#` esconde un `/*` que si se maneja

    🔴 **Solo el verbo que ABRE cada sentencia.** No todos los que aparecen en el texto: el
    ataque siempre esconde una SENTENCIA, y una sentencia empieza por su verbo. Contar todos
    convertiria `WHERE accion = 'DELETE'` en una operacion destructiva, que es una negacion
    falsa cara y evitable. Y un primer token que la tabla no declara **se ignora** en esta
    lectura -no se deniega-, porque partir el texto crudo por `;` parte tambien los literales:
    `SELECT 'a;b' FROM t` da un pedazo que empieza con `b'` y no es una sentencia de nadie.
    """
    candidatos = []
    for parte in texto.split(";"):
        if not parte.strip():
            continue
        encontrado = _PRIMER_TOKEN.match(parte)
        primero = encontrado.group(1).upper() if encontrado else ""
        if primero in TABLA:
            clase, efecto = TABLA[primero]
            if primero == "DELETE" and not _tiene_alcance(parte):
                clase, efecto = DESTRUCTIVA, "DESTRUCTIVE"
            candidatos.append((clase, efecto))
        elif primero in PREFIJOS:
            # `WITH x AS (...) DELETE FROM t`: el verbo que manda esta despues del prefijo.
            for v in _verbos_en(parte):
                clase, efecto = TABLA[v]
                if v == "DELETE" and not _tiene_alcance(parte):
                    clase, efecto = DESTRUCTIVA, "DESTRUCTIVE"
                candidatos.append((clase, efecto))
    return candidatos


_LITERAL = re.compile(r"'[^']*'|\"[^\"]*\"")


def _sin_literales(sentencia):
    """La sentencia con literales, identificadores entre comillas y comentarios tapados.

    Es `_enmascarar` sin el dato de si quedo entero: lo usa la busqueda de alcance, que ya
    trabaja sobre una sentencia que paso por `_sentencias`.
    """
    return _enmascarar(sentencia)[0]


def _tiene_alcance(sentencia):
    """Si el DELETE de esta sentencia declara SU alcance.

    🔴 No alcanza con que la palabra `where` este en algun lugar del texto. La version anterior
    buscaba el token en la sentencia entera, y con eso estos tres BORRAN LA TABLA ENTERA y
    salian MUTATING —o sea HIGH sin aprobacion en DEV, cuando corresponde CRITICAL con
    aprobacion—:

        WITH x AS (SELECT * FROM o WHERE a=1) DELETE FROM t     el WHERE es del CTE
        DELETE FROM t USING (SELECT id FROM o WHERE x=1) s      el WHERE es del subquery
        DELETE FROM "where"                                     el WHERE es un identificador

    Asi que el WHERE tiene que estar DESPUES del DELETE, a profundidad cero de parentesis, y no
    precedido por un punto. No es un parser: es una busqueda de token con profundidad, y lo que
    no puede establecer lo resuelve para el lado seguro.
    """
    limpia = _sin_literales(sentencia)
    borrados = list(re.finditer(r"(?i)\bdelete\b", limpia))
    if not borrados:
        return False
    # 🔴 TODOS, no el primero. `WITH x AS (DELETE FROM a) DELETE FROM b` tiene dos, y que uno
    # declare su alcance no dice nada del otro. Basta que a uno le falte para que no se pueda
    # establecer, y eso lo sube a destructivo.
    return all(_alcance_desde(limpia[b.end():]) for b in borrados)


def _alcance_desde(resto):
    """Si despues de un DELETE hay un WHERE que es SUYO.

    🔴 Un parentesis que cierra mas de lo que se abrio es el de la expresion que CONTIENE a
    este DELETE, y lo que viene despues ya no le pertenece. Sin esto:

        WITH d AS (DELETE FROM a RETURNING *) SELECT * FROM d WHERE id > 5

    borra la tabla `a` entera y salia MUTATING -HIGH sin aprobacion- porque el WHERE del SELECT
    de afuera caia a profundidad cero. La version anterior hacia `max(0, profundidad - 1)`, que
    es justamente perder la unica senal de que se salio del alcance.
    """
    profundidad = 0
    for hallado in re.finditer(r"(?i)[()]|(?<![.\w])where(?![\w])", resto):
        texto = hallado.group(0)
        if texto == "(":
            profundidad += 1
        elif texto == ")":
            if profundidad == 0:
                return False
            profundidad -= 1
        elif profundidad == 0:
            return True
    return False


def _mas_alto(candidatos):
    """(clase, efecto) del candidato de mayor efecto; ante empate, la clase mas angosta."""
    tope = max(EFECTOS.index(efecto) for _, efecto in candidatos)
    empatados = [clase for clase, efecto in candidatos if EFECTOS.index(efecto) == tope]
    for clase in PRECEDENCIA:
        if clase in empatados:
            return clase, EFECTOS[tope]
    return empatados[0], EFECTOS[tope]


def clasificar(verbo, statement=None, migracion=None):
    """{operationClass, effectiveSideEffects, problem} de una operacion declarada.

    El efecto efectivo es el MAXIMO entre lo declarado y lo que el barrido detecta. Nunca baja.
    Una sentencia que el barrido no puede leer deja el pedido ENTERO sin clasificar.
    """
    salida = {"operationClass": None, "effectiveSideEffects": None, "problem": None}
    declarado = _texto(verbo)
    if declarado not in TABLA:
        salida["problem"] = SIN_CLASIFICAR
        return salida

    clase, efecto = TABLA[declarado]

    # 🔴 Un `statement` que no es texto NO se descarta: se deniega. La version anterior hacia
    # `statement if isinstance(statement, str) else ""`, asi que una lista, un diccionario,
    # bytes o una tupla desactivaban el barrido en silencio y un `["DROP TABLE t"]` declarado
    # SELECT salia PERMITIDO en PRD. Es la regla que `_texto` ya documenta para los demas
    # campos, y la unica coherente con "una negacion falsa es aceptable y un permiso falso no".
    if statement is not None and not isinstance(statement, str):
        salida["problem"] = SIN_CLASIFICAR
        return salida

    texto = statement if isinstance(statement, str) else ""

    # 🔴 Un comentario condicional de motor -`/*! ... */`- NO es un comentario: MySQL lo
    # EJECUTA. Quitarlo como si fuera inerte convertia `SELECT 1 /*! ; UPDATE t SET a=1 */` en
    # un SELECT permitido. Un barrido no es un parser, asi que no se intenta interpretarlo:
    # se deniega. Deniega de mas -un hint legitimo de MySQL tambien- y es la direccion correcta.
    if COMENTARIO_EJECUTABLE in texto:
        salida["problem"] = SIN_CLASIFICAR
        return salida

    sentencias, entero = _sentencias(texto) if texto.strip() else ([], True)

    # 🔴 Un literal o un comentario de bloque sin cerrar: el texto no se puede establecer y no
    # se interpreta a medias. Un motor tampoco lo ejecutaria.
    if not entero:
        salida["problem"] = SIN_CLASIFICAR
        return salida

    if texto.strip() and not sentencias:
        # Habia texto y despues de quitar comentarios no quedo ninguna sentencia.
        salida["problem"] = SIN_CLASIFICAR
        return salida

    # El alcance de un DELETE declarado: se establece solo si TODAS las sentencias que borran
    # lo declaran. Sin sentencia, no se puede establecer.
    if declarado == "DELETE":
        borrados = [s for s in sentencias if "DELETE" in _verbos_en(s)]
        if not borrados or [s for s in borrados if not _tiene_alcance(s)]:
            efecto = "DESTRUCTIVE"
            clase = DESTRUCTIVA

    if declarado == "MIGRATION" and isinstance(migracion, dict):
        if migracion.get("irreversible") is True:
            efecto = "DESTRUCTIVE"

    candidatos = [(clase, efecto)]

    # 🔴 La lectura CRUDA, primero. Es la que sostiene la seguridad: el enmascarado de abajo
    # solo puede bajar lo que ve, y esto ya vio lo que hay. Ver `_candidatos_crudos`.
    candidatos.extend(_candidatos_crudos(texto))

    for sentencia in sentencias:
        encontrado = _PRIMER_TOKEN.match(sentencia)
        primero = encontrado.group(1).upper() if encontrado else ""
        if primero not in TABLA and primero not in PREFIJOS:
            # `SHOW`, `EXPLAIN`, `CALL`, `GRANT`, `BEGIN`, `DO`… Un barrido no es un parser.
            salida["problem"] = SIN_CLASIFICAR
            return salida
        vistos = _verbos_en(sentencia)
        if not vistos:
            salida["problem"] = SIN_CLASIFICAR
            return salida
        for v in vistos:
            c, e = TABLA[v]
            if v == "DELETE" and not _tiene_alcance(sentencia):
                c, e = DESTRUCTIVA, "DESTRUCTIVE"
            candidatos.append((c, e))
        # 🔴 Y los modificadores que convierten una lectura en una escritura, que no son verbos.
        for modificador, (efecto_m, clase_m) in sorted(MODIFICADORES.items()):
            if re.search(r"(?i)(?<![.\w])%s(?![\w])" % modificador, sentencia):
                candidatos.append((clase_m, efecto_m))

    clase_final, efecto_final = _mas_alto(candidatos)
    salida["operationClass"] = clase_final
    salida["effectiveSideEffects"] = efecto_final
    return salida


# -- el riesgo, que sale de la compuerta que ya existe -------------------------

def contrato_de_riesgo(efecto, ambiente):
    """El contrato de tool que describe una operacion de base de datos.

    No es una escala nueva: es la traduccion al contrato que `tools.py` ya sabe leer. Una base
    esta del otro lado de la red y hace falta una credencial para ejecutar, asi que las dos
    banderas van en verdadero siempre; el impacto de produccion, solo en PRD.
    """
    return {"sideEffects": efecto if efecto in EFECTOS else "DESTRUCTIVE",
            "networkAccess": True,
            "secretsRequired": True,
            "blastRadius": {"scope": "external-system",
                            "productionImpact": ambiente == "PRD"}}


def riesgo_de(efecto, ambiente):
    """{level, approvalRequired}, los dos calculados por `tools.py`.

    🔴 No hay una segunda escala. El nivel lo deriva `tools.derivar_riesgo` y la aprobacion la
    decide `tools.exige_aprobacion_humana`. Lo que este modulo hace es armarles la entrada.
    """
    contrato = contrato_de_riesgo(efecto, ambiente)
    nivel = tools.derivar_riesgo(contrato)
    contrato["riskLevel"] = nivel
    return {"level": nivel, "approvalRequired": tools.exige_aprobacion_humana(contrato)}


# -- los perfiles --------------------------------------------------------------

CAMPOS_DE_PERFIL = ("engine", "version", "hostRef", "portRef", "databaseRef",
                    "usernameSecretRef", "passwordSecretRef")
CAMPOS_DE_REFERENCIA = ("hostRef", "portRef", "databaseRef", "usernameSecretRef",
                        "passwordSecretRef")


def clave_de_perfil(base, ambiente):
    """La clave de un perfil. Cada par de base logica y ambiente es una entrada distinta.

    🔴 Nunca se infiere que dos ambientes comparten instancia. Asumirlo es como un `UPDATE` que
    alguien creia de QA llega a PRD.
    """
    return "%s/%s" % (base, ambiente)


def referencias_de(perfil):
    """Solo las referencias del perfil. Nombres, nunca valores."""
    if not isinstance(perfil, dict):
        return {}
    return {c: _texto(perfil.get(c)) for c in CAMPOS_DE_REFERENCIA
            if _texto(perfil.get(c))}


def perfil_de(base, ambiente, perfiles=None, desde=None):
    """El perfil de ese par, o None. El harness no sabe donde vive la base de nadie."""
    doc = cargar_perfiles(desde) if perfiles is None else perfiles
    if not isinstance(doc, dict):
        return None
    tabla = doc.get("profiles")
    if not isinstance(tabla, dict):
        return None
    perfil = tabla.get(clave_de_perfil(base, ambiente))
    if not isinstance(perfil, dict):
        return None
    # 🔴 Lo que se publica son los campos del contrato y nada mas. Si alguien escribio un valor
    # de credencial adentro del archivo, no viaja: el schema lo rechaza y esto no lo copia.
    publicado = {c: perfil.get(c) for c in CAMPOS_DE_PERFIL if c in perfil}
    return publicado or None


# -- la resolucion -------------------------------------------------------------

def _remedio_de(ambiente, motivo):
    """Que hacer en lugar de lo que se nego, cuando hay algo que hacer.

    🔴 Esto viaja EN LA SALIDA. La version anterior lo tenia en una constante del modulo y el
    test afirmaba que LA CONSTANTE nombraba el artefacto versionado — no que la denegacion lo
    nombrara, que es lo que el escenario pide. Una negacion que no dice que hacer en su lugar
    es una negacion que alguien evade por otro camino.
    """
    if ambiente in AMBIENTES_DE_PROMOCION and motivo in (SIN_ESCRITURA, SIN_DDL,
                                                          SIN_MIGRACION):
        return REMEDIO_DE_PROMOCION
    return None


def _salida(ambiente, base, verbo, clase=None, efecto=None, permitido=False, motivo=None,
            perfil=None, riesgo=None):
    return {
        "environment": ambiente or None,
        "logicalDatabase": base or None,
        "operation": {"declaredVerb": verbo or None, "operationClass": clase,
                      "effectiveSideEffects": efecto, "allowed": bool(permitido),
                      "denialReason": motivo},
        "connectionProfile": perfil,
        "risk": riesgo or riesgo_de("DESTRUCTIVE", ambiente),
        "remediation": _remedio_de(ambiente, motivo),
    }


def resolver(pedido, politica=None, perfiles=None, desde=None):
    """La decision sobre una operacion de base de datos, ANTES de abrir la conexion.

        {"taskId", "projectId", "environment", "logicalDatabase", "declaredVerb",
         "statement", "migration": {"irreversible"}}

    Devuelve el ambiente, la base logica, la operacion -con sus dos dimensiones, si se permite y
    por que no-, el perfil con sus referencias y el riesgo.

    🔴 No importa un driver, no abre una conexion, no ejecuta nada y no habla con el almacen de
    secretos. Para el mismo pedido devuelve siempre lo mismo.
    """
    p = pedido if isinstance(pedido, dict) else {}
    verbo = _texto(p.get("declaredVerb"))
    ambiente = _crudo(p.get("environment"))
    base = _texto(p.get("logicalDatabase"))

    # 1. La clasificacion primero: un verbo que la tabla no declara es lo mas especifico que se
    #    puede decir de un pedido, y no depende del ambiente.
    clasificada = clasificar(verbo, p.get("statement"), p.get("migration"))
    if clasificada["problem"]:
        return _salida(ambiente.strip() or None, base, verbo, motivo=SIN_CLASIFICAR)

    clase = clasificada["operationClass"]
    efecto = clasificada["effectiveSideEffects"]

    # 2. El ambiente, exacto. Y la trazabilidad del pedido, que tambien es dato requerido: sin
    #    tarea y sin proyecto no hay contexto declarado en el que resolver un ambiente.
    acceso = acceso_de(ambiente, politica, desde)
    if acceso is None or not _texto(p.get("taskId")) or not _texto(p.get("projectId")):
        return _salida(ambiente.strip() or None, base, verbo, clase, efecto,
                       motivo=SIN_AMBIENTE)

    riesgo = riesgo_de(efecto, ambiente)

    # 3. El permiso que la clase exige contra el bit del ambiente.
    permiso = PERMISO_DE_CLASE[clase]
    if acceso.get(permiso) is not True:
        return _salida(ambiente, base, verbo, clase, efecto,
                       motivo=NEGACION_DE_PERMISO[permiso], riesgo=riesgo)

    # 4. El perfil. Una negacion del ambiente manda sobre la falta de perfil: decir "falta el
    #    perfil" cuando lo que pasa es que la operacion no se permite esconde el mensaje que
    #    importa.
    if not base:
        return _salida(ambiente, None, verbo, clase, efecto, motivo=SIN_PERFIL, riesgo=riesgo)
    perfil = perfil_de(base, ambiente, perfiles, desde)
    if perfil is None:
        return _salida(ambiente, base, verbo, clase, efecto, motivo=SIN_PERFIL, riesgo=riesgo)

    return _salida(ambiente, base, verbo, clase, efecto, permitido=True, perfil=perfil,
                   riesgo=riesgo)


# -- el borde de ejecucion -----------------------------------------------------

def resolver_secreto(referencia, almacen):
    """El unico lugar del modulo que toca un almacen de secretos, y lo RECIBE.

    🔴 No se importa el almacen: se lo pasan. Con eso, "el resolvedor no puede conseguir una
    credencial" es una propiedad de la forma de este archivo y no una costumbre que alguien
    tenga que recordar.

    🔴 Y el valor no vuelve en el resultado. Lo que vuelve es si la referencia se pudo resolver.
    Un mensaje que dice "no se pudo resolver DB_PASSWORD=abc123" acaba de publicar el secreto en
    la consola, en la transcripcion de la sesion y en el contexto del modelo.
    """
    nombre = _texto(referencia)
    if not nombre or almacen is None:
        return {"reference": nombre or None, "state": SIN_SECRETO}
    try:
        existe = almacen.exists(nombre)
    except Exception:
        return {"reference": nombre, "state": SIN_SECRETO}
    if not existe:
        return {"reference": nombre, "state": SIN_SECRETO}
    return {"reference": nombre, "state": RESUELTO}
