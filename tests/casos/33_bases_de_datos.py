# Gestion de ambientes de base de datos: decidir y denegar ANTES de abrir la conexion.
#
# Escenarios E-01 a E-37 de docs/cambios/gestion-de-ambientes-de-base-de-datos/spec.md. Entre
# parentesis, el DB-nn del pedido de instalacion.
#
# 🔴 Nada de esto se conecta a una base. Lo que se verifica es la COMPUERTA: que DEV sea el unico
# ambiente que permite mutar, que la clase de una operacion no se pueda bajar, que un DELETE sin
# alcance establecido sea destructivo, que el riesgo salga de la compuerta que ya existe y no de una
# segunda escala, y que el resolvedor no tenga forma de conseguir una credencial.
#
# 🔴 Tres escenarios son PRODUCTOS y no listas: E-06 (las formas de ambiente invalido), E-23
# (ambientes de promocion x tabla de operaciones) y E-34 (las formas de dato faltante). Si alguno
# se degradara a una lista, el resto seguiria en verde y la compuerta dejaria de ser una compuerta.
import ast
import importlib.util
import io
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "harnesses" / "desarrollo" / "bin"
REGLAS = RAIZ / "harnesses" / "desarrollo" / "reglas"
SCHEMAS = RAIZ / "comun" / "schemas"

sys.path.insert(0, str(BIN))
from orquestacion import bases                      # noqa: E402
from orquestacion import tools as c_tools           # noqa: E402
import rutas as rutas_mod                           # noqa: E402


def _armador():
    spec = importlib.util.spec_from_file_location(
        "armar_db", RAIZ / "comun" / "bin" / "contexto-armar.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


ARMADOR = _armador()

DEV, QA, HML, PRD = "DEV", "QA", "HML", "PRD"
PROMOCION = (QA, HML, PRD)

# Un perfil por ambiente de la misma base logica, con referencias y ningun valor.
def _perfil(ambiente, base="main-database"):
    sufijo = "%s_%s" % (base.replace("-", "_").upper(), ambiente)
    return {"logicalDatabase": base, "environment": ambiente, "engine": "postgresql",
            "version": "15", "hostRef": "DB_%s_HOST" % sufijo,
            "portRef": "DB_%s_PORT" % sufijo, "databaseRef": "DB_%s_NAME" % sufijo,
            "usernameSecretRef": "DB_%s_USER" % sufijo,
            "passwordSecretRef": "DB_%s_PASSWORD" % sufijo}


def _perfiles(ambientes=(DEV, QA, HML, PRD), base="main-database"):
    return {"version": "1.0",
            "profiles": {"%s/%s" % (base, a): _perfil(a, base) for a in ambientes}}


def _pedido(ambiente=DEV, verbo="SELECT", base="main-database", **extra):
    p = {"taskId": "TAR-1", "projectId": "PROY-1", "environment": ambiente,
         "logicalDatabase": base, "declaredVerb": verbo}
    p.update(extra)
    return p


def _resolver(pedido=None, perfiles=None, **extra):
    return bases.resolver(_pedido(**extra) if pedido is None else pedido,
                          perfiles=_perfiles() if perfiles is None else perfiles)


def _op(salida):
    return salida["operation"]


# -- E-01 a E-06 — la politica y los cuatro ambientes --------------------------

def test_e01_la_politica_es_del_harness(t):
    """E-01 (§2) — cuatro ambientes, sus modos, el default DENY, y vive en reglas/."""
    ruta = REGLAS / "database-environment-access-policy.json"
    t.verdadero("E-01 la politica esta en reglas/ del harness", ruta.is_file())
    doc = json.loads(ruta.read_text(encoding="utf-8"))

    t.igual("E-01 declara exactamente cuatro ambientes", [DEV, HML, PRD, QA],
            sorted(doc["environments"]))
    t.igual("E-01 DEV es FULL", "FULL", doc["environments"][DEV]["mode"])
    for ambiente in PROMOCION:
        t.igual("E-01 %s es READ_ONLY" % ambiente, "READ_ONLY",
                doc["environments"][ambiente]["mode"])
    t.igual("E-01 el default deniega", "DENY", doc["default"]["mode"])
    t.igual("E-01 y dice por que", "DATABASE_ENVIRONMENT_UNRESOLVED", doc["default"]["reason"])

    # Y el modulo la lee de ahi, no la trae escrita adentro.
    t.igual("E-01 el modulo lee la politica del archivo", doc, bases.cargar_politica())
    t.vacio("E-01 la politica cumple su schema", bases.validar_politica(doc))

    # 🔴 Y no esta en ningun agente ni skill: la politica es del harness.
    # 📌 No se barre "READ_ONLY" solo: `dev-external-integration` y `dev-openshift` lo usan
    # legitimamente -es un efecto de un contrato de tool-. La firma de ESTA politica es la
    # tabla de los cuatro ambientes junta, mas sus identificadores.
    FIRMAS = ("database-environment-access-policy", "DATABASE_ENVIRONMENT_UNRESOLVED",
              "DATABASE_WRITE_NOT_ALLOWED", "database-profiles")
    for carpeta in ("agents", "skills"):
        for ruta in (RAIZ / "harnesses" / "desarrollo" / carpeta).rglob("*.md"):
            texto = ruta.read_text(encoding="utf-8")
            for firma in FIRMAS:
                t.verdadero("E-01 %s/%s no declara %s" % (carpeta, ruta.name, firma),
                            firma not in texto)
            # 📌 Tampoco se barre la tabla de los cuatro NOMBRES de ambiente: DEV, QA, HML y
            # PRD son los ambientes del GCBA y una skill de despliegue o de CI los nombra con
            # todo derecho. La firma de la POLITICA son sus cuatro bits de permiso juntos —
            # `read`, `write`, `ddl` y `migrations` en un mismo archivo es su bloque de acceso
            # y no es otra cosa.
            t.verdadero("E-01 %s/%s no lleva el bloque de acceso" % (carpeta, ruta.name),
                        not all('"%s"' % b in texto or "%s:" % b in texto
                                for b in ("read", "write", "ddl", "migrations")))


def test_e02_dev_resuelve_full(t):
    """E-02 (DB-01) — FULL con los cuatro permisos en verdadero."""
    salida = _resolver(ambiente=DEV)
    t.igual("E-02 el ambiente viaja", DEV, salida["environment"])
    acceso = bases.acceso_de(DEV)
    t.igual("E-02 el modo es FULL", "FULL", acceso["mode"])
    for permiso in ("read", "write", "ddl", "migrations"):
        t.igual("E-02 DEV permite %s" % permiso, True, acceso[permiso])
    t.igual("E-02 y un SELECT pasa", True, _op(salida)["allowed"])


def test_e03_qa_resuelve_solo_lectura(t):
    """E-03 (DB-02)."""
    acceso = bases.acceso_de(QA)
    t.igual("E-03 el modo es READ_ONLY", "READ_ONLY", acceso["mode"])
    t.igual("E-03 lee", True, acceso["read"])
    for permiso in ("write", "ddl", "migrations"):
        t.igual("E-03 QA no permite %s" % permiso, False, acceso[permiso])


def test_e04_hml_resuelve_solo_lectura(t):
    """E-04 (DB-03)."""
    acceso = bases.acceso_de(HML)
    t.igual("E-04 el modo es READ_ONLY", "READ_ONLY", acceso["mode"])
    t.igual("E-04 lee", True, acceso["read"])
    for permiso in ("write", "ddl", "migrations"):
        t.igual("E-04 HML no permite %s" % permiso, False, acceso[permiso])


def test_e05_prd_resuelve_solo_lectura(t):
    """E-05 (DB-04)."""
    acceso = bases.acceso_de(PRD)
    t.igual("E-05 el modo es READ_ONLY", "READ_ONLY", acceso["mode"])
    t.igual("E-05 lee", True, acceso["read"])
    for permiso in ("write", "ddl", "migrations"):
        t.igual("E-05 PRD no permite %s" % permiso, False, acceso[permiso])


def test_e06_el_ambiente_desconocido_falla_cerrado(t):
    """E-06 (DB-05, §2) — EL PRODUCTO de las formas de ambiente no declarado.

    🔴 No una lista de ejemplos. Ninguna forma de ambiente que la politica no declare puede
    terminar en DEV ni en FULL, y la capitalizacion NO se normaliza: `dev` no es `DEV`. Puede
    parecer hostil y es lo correcto — normalizar el identificador de un ambiente es el atajo por
    el que `prod`, `Prd` y `PROD` acaban resolviendo a algo.
    """
    FORMAS = (
        ("ausente", "__SIN_CLAVE__"),
        ("None", None),
        ("vacio", ""),
        ("un espacio", " "),
        ("solo blancos", "   \t\n "),
        ("minuscula", "dev"),
        ("capitalizado", "Dev"),
        ("PRD capitalizado", "Prd"),
        ("prod", "prod"),
        ("PROD", "PROD"),
        ("PRODUCTION", "PRODUCTION"),
        ("DEV con blancos", " DEV "),
        ("DEV con salto", "DEV\n"),
        ("desconocido", "STAGING"),
        ("un numero", 1),
        ("un booleano", True),
        ("una lista", [DEV]),
        ("un diccionario", {"name": DEV}),
        ("un objeto con mode", {"mode": "FULL"}),
        ("default", "default"),
        ("environments", "environments"),
    )
    # Se cruza con TODOS los verbos: ningun ambiente invalido se salva por el verbo que traiga.
    for nombre, valor in FORMAS:
        for verbo in bases.VERBOS:
            pedido = _pedido(verbo=verbo)
            if valor == "__SIN_CLAVE__":
                pedido.pop("environment")
            else:
                pedido["environment"] = valor
            salida = bases.resolver(pedido, perfiles=_perfiles())
            op = _op(salida)
            t.igual("E-06 %s con %s no se permite" % (nombre, verbo), False, op["allowed"])
            t.igual("E-06 %s con %s dice por que" % (nombre, verbo), bases.SIN_AMBIENTE,
                    op["denialReason"])
            # 📌 `_salida` no emite nunca una clave `access`, asi que la version anterior
            # -`t.igual(..., None, salida.get("access"))`- eran 189 aserciones que no podian
            # fallar con ningun codigo. Lo que si muerde es que no se publique el modo del
            # ambiente y que no haya perfil: un ambiente que no resuelve no tiene ninguno.
            # 📌 `READ_ONLY` SI puede aparecer: es la CLASE de un SELECT, y la
            # clasificacion se calcula antes del ambiente a proposito. Lo que no aparece es
            # el MODO del ambiente, que es lo que "no cae en DEV" quiere decir.
            t.verdadero("E-06 %s con %s no informa el modo de un ambiente" % (nombre, verbo),
                        "FULL" not in repr(salida) and "'mode'" not in repr(salida))
            t.igual("E-06 %s con %s no resuelve un perfil" % (nombre, verbo), None,
                    salida["connectionProfile"])

    # 🔴 Y un ambiente DECLARADO pero no usable tampoco resuelve. Los dos modos que el
    # contrato admite -FULL y READ_ONLY- implican lectura, asi que un bloque sin `read` no es
    # ninguno de los dos: no es un ambiente declarado, y eso es fallar cerrado. La pasada de
    # mutaciones encontro que ninguna asercion lo miraba.
    BASE = json.loads((REGLAS / "database-environment-access-policy.json").read_text(
        encoding="utf-8"))
    INUTILIZABLES = (
        ("sin lectura", dict(BASE["environments"][DEV], read=False)),
        ("con la lectura en texto", dict(BASE["environments"][DEV], read="true")),
        ("con un modo inventado", dict(BASE["environments"][DEV], mode="SUPERUSER")),
        ("con un permiso en texto", dict(BASE["environments"][DEV], write="true")),
        ("sin el bit de ddl", {k: v for k, v in BASE["environments"][DEV].items()
                               if k != "ddl"}),
        ("como texto", "FULL"),
    )
    for nombre, bloque in INUTILIZABLES:
        torcida = json.loads(json.dumps(BASE))
        torcida["environments"][DEV] = bloque
        t.igual("E-06 un DEV %s no resuelve" % nombre, None,
                bases.acceso_de(DEV, politica=torcida))
        op = _op(bases.resolver(_pedido(), politica=torcida, perfiles=_perfiles()))
        t.igual("E-06 un DEV %s no permite" % nombre, False, op["allowed"])
        t.igual("E-06 un DEV %s dice por que" % nombre, bases.SIN_AMBIENTE,
                op["denialReason"])

    # Y los cuatro que si: ninguno se confunde con otro.
    for ambiente in (DEV,) + PROMOCION:
        t.igual("E-06 %s si resuelve" % ambiente, ambiente,
                bases.resolver(_pedido(ambiente=ambiente), perfiles=_perfiles())["environment"])


# -- E-07 a E-12 — la clasificacion, antes de ejecutar -------------------------

def test_e07_la_clase_y_el_efecto_son_dos_campos(t):
    """E-07 (§4, v2 §2) — cinco clases, tres efectos, y la traduccion entre las dos."""
    t.igual("E-07 hay cinco clases de operacion", 5, len(bases.CLASES))
    t.igual("E-07 y son las del pedido",
            ("READ_ONLY", "MUTATING", "DESTRUCTIVE", "DDL", "MIGRATION"), bases.CLASES)

    # 🔴 Los efectos SON los de tools.py, no unos parecidos: se derivan de ahi.
    t.igual("E-07 los efectos son los de tools.SIDE_EFFECTS", c_tools.SIDE_EFFECTS,
            bases.EFECTOS)
    t.igual("E-07 y son tres", 3, len(bases.EFECTOS))

    # La tabla cerrada, y la traduccion verbo -> (clase, efecto).
    ESPERADO = {
        "SELECT": ("READ_ONLY", "READ_ONLY"),
        "INSERT": ("MUTATING", "MUTATING"),
        "UPDATE": ("MUTATING", "MUTATING"),
        # 📌 La ENTRADA de la tabla dice MUTATING; la regla de alcance de E-11 la sube
        # cuando no se puede establecer el WHERE. Aca se afirma la entrada con una sentencia
        # que declara su alcance, y E-11 afirma la regla.
        "DELETE": ("MUTATING", "MUTATING"),
        "CREATE": ("DDL", "MUTATING"),
        "ALTER": ("DDL", "MUTATING"),
        "DROP": ("DDL", "DESTRUCTIVE"),
        "TRUNCATE": ("DDL", "DESTRUCTIVE"),
        "MIGRATION": ("MIGRATION", "MUTATING"),
    }
    # Y la entrada cruda de la tabla, sin pasar por la regla de alcance.
    t.igual("E-07 la entrada de DELETE en la tabla es MUTATING", ("MUTATING", "MUTATING"),
            bases.TABLA["DELETE"])
    t.igual("E-07 y sin sentencia la regla de alcance la sube", "DESTRUCTIVE",
            bases.clasificar("DELETE")["effectiveSideEffects"])

    t.igual("E-07 la tabla tiene nueve verbos", 9, len(bases.VERBOS))
    t.igual("E-07 y son exactamente esos", sorted(ESPERADO), sorted(bases.VERBOS))
    CON_ALCANCE = {"DELETE": "DELETE FROM t WHERE id = 1"}
    for verbo, (clase, efecto) in sorted(ESPERADO.items()):
        r = bases.clasificar(verbo, statement=CON_ALCANCE.get(verbo))
        t.igual("E-07 %s es de clase %s" % (verbo, clase), clase, r["operationClass"])
        t.igual("E-07 %s tiene efecto %s" % (verbo, efecto), efecto,
                r["effectiveSideEffects"])
        t.verdadero("E-07 %s no trae problema" % verbo, not r["problem"])

    # Una migracion declarada irreversible sube a destructiva, y sigue siendo de clase MIGRATION.
    irreversible = bases.clasificar("MIGRATION", migracion={"irreversible": True})
    t.igual("E-07 una migracion irreversible sigue siendo MIGRATION", "MIGRATION",
            irreversible["operationClass"])
    t.igual("E-07 y su efecto sube a destructivo", "DESTRUCTIVE",
            irreversible["effectiveSideEffects"])
    # Y `irreversible` se exige True, no un truthy: un "no" no puede BAJAR nada, pero tampoco
    # tiene que subirlo por error.
    t.igual("E-07 irreversible='no' no es una declaracion", "MUTATING",
            bases.clasificar("MIGRATION", migracion={"irreversible": "no"})[
                "effectiveSideEffects"])

    # Cada clase exige un permiso del ambiente, y cada permiso tiene su estado de negacion.
    t.igual("E-07 cada clase exige un permiso", sorted(bases.CLASES),
            sorted(bases.PERMISO_DE_CLASE))
    t.igual("E-07 MUTATING y DESTRUCTIVE exigen escritura", ["write", "write"],
            [bases.PERMISO_DE_CLASE["MUTATING"], bases.PERMISO_DE_CLASE["DESTRUCTIVE"]])
    t.igual("E-07 DDL exige ddl", "ddl", bases.PERMISO_DE_CLASE["DDL"])
    t.igual("E-07 MIGRATION exige migrations", "migrations",
            bases.PERMISO_DE_CLASE["MIGRATION"])
    t.igual("E-07 READ_ONLY exige lectura", "read", bases.PERMISO_DE_CLASE["READ_ONLY"])


def test_e08_un_verbo_que_la_tabla_no_declara_se_deniega(t):
    """E-08 (DB-27) — y los verbos de metadata no se asumen portables."""
    FORMAS = (
        ("ausente", "__SIN_CLAVE__"), ("None", None), ("vacio", ""), ("un espacio", " "),
        ("minuscula", "select"), ("capitalizado", "Select"),
        ("inventado", "UPSERT"), ("un numero", 1), ("una lista", ["SELECT"]),
        ("un diccionario", {"verb": "SELECT"}), ("dos verbos", "SELECT INSERT"),
        # 🔴 Los de metadata: no son portables entre motores, y EXPLAIN ANALYZE en algunos
        # ejecuta la sentencia. No se asumen: se agregan deliberadamente cuando alguien los
        # necesite para un motor concreto.
        ("SHOW", "SHOW"), ("DESCRIBE", "DESCRIBE"), ("DESC", "DESC"), ("EXPLAIN", "EXPLAIN"),
        ("ANALYZE", "ANALYZE"), ("VACUUM", "VACUUM"), ("CALL", "CALL"), ("EXEC", "EXEC"),
        ("GRANT", "GRANT"), ("REVOKE", "REVOKE"), ("COPY", "COPY"), ("MERGE", "MERGE"),
    )
    # En los CUATRO ambientes, DEV incluido: un verbo sin clasificar no se permite en ninguno.
    for nombre, valor in FORMAS:
        for ambiente in (DEV,) + PROMOCION:
            pedido = _pedido(ambiente=ambiente)
            if valor == "__SIN_CLAVE__":
                pedido.pop("declaredVerb")
            else:
                pedido["declaredVerb"] = valor
            op = _op(bases.resolver(pedido, perfiles=_perfiles()))
            t.igual("E-08 %s en %s no se permite" % (nombre, ambiente), False, op["allowed"])
            t.igual("E-08 %s en %s dice por que" % (nombre, ambiente), bases.SIN_CLASIFICAR,
                    op["denialReason"])

    t.verdadero("E-08 SHOW, DESCRIBE y EXPLAIN no estan en la tabla",
                not {"SHOW", "DESCRIBE", "EXPLAIN"} & set(bases.VERBOS))

    # 🔴 La asimetria, declarada: al VERBO se le quitan los blancos y al AMBIENTE no.
    #
    # Quitarle los blancos a un verbo no puede convertir un verbo de la tabla en otro, y
    # normalizar los dos lados de una comparacion es la doctrina del repositorio. El ambiente
    # es la excepcion y tiene su razon: `prod`, `Prd` y `PRD` son nombres que un proyecto
    # puede usar DE VERDAD para ambientes distintos, asi que normalizarlos mapearia uno a otro
    # en silencio. Un verbo con un espacio al lado es el mismo verbo con ruido de formato.
    t.igual("E-08 un verbo con blancos es el mismo verbo", True,
            _op(_resolver(verbo=" SELECT "))["allowed"])
    t.igual("E-08 y se informa normalizado", "SELECT",
            _op(_resolver(verbo=" SELECT "))["declaredVerb"])
    t.igual("E-08 un ambiente con blancos NO es el mismo ambiente", bases.SIN_AMBIENTE,
            _op(_resolver(ambiente=" DEV "))["denialReason"])


def test_e09_el_barrido_solo_puede_subir(t):
    """E-09 — la asimetria, que es la misma de tools.controlar_riesgo.

    🔴 "Declarar de menos no baja el riesgo, lo esconde." Aca: declarar SELECT con un UPDATE
    adentro no convierte un UPDATE en un SELECT, y declarar UPDATE con un SELECT adentro no
    convierte un UPDATE en un SELECT tampoco.
    """
    SUBEN = (
        ("SELECT", "SELECT 1; UPDATE t SET a=1 WHERE b=2", "MUTATING", "MUTATING"),
        ("SELECT", "SELECT * FROM t; DROP TABLE t", "DDL", "DESTRUCTIVE"),
        ("SELECT", "WITH x AS (SELECT 1) DELETE FROM t", "DESTRUCTIVE", "DESTRUCTIVE"),
        ("SELECT", "WITH x AS (SELECT 1) DELETE FROM t WHERE a=1", "MUTATING", "MUTATING"),
        ("INSERT", "INSERT INTO t SELECT * FROM o; TRUNCATE TABLE o", "DDL", "DESTRUCTIVE"),
        ("UPDATE", "UPDATE t SET a=1 WHERE b=2; ALTER TABLE t ADD c int", "DDL", "MUTATING"),
        ("CREATE", "CREATE TABLE t (a int); DROP TABLE o", "DDL", "DESTRUCTIVE"),
        ("MIGRATION", "ALTER TABLE t ADD c int; DROP COLUMN", "DDL", "DESTRUCTIVE"),
    )
    for verbo, sentencia, clase, efecto in SUBEN:
        r = bases.clasificar(verbo, statement=sentencia)
        t.igual("E-09 %s + %r sube a %s" % (verbo, sentencia[:32], clase), clase,
                r["operationClass"])
        t.igual("E-09 %s + %r con efecto %s" % (verbo, sentencia[:32], efecto), efecto,
                r["effectiveSideEffects"])

    # 🔴 Y NO baja. Un verbo declarado alto con una sentencia de lectura sigue alto.
    NO_BAJAN = (
        ("DROP", "SELECT 1", "DDL", "DESTRUCTIVE"),
        ("TRUNCATE", "SELECT * FROM t", "DDL", "DESTRUCTIVE"),
        ("UPDATE", "SELECT 1", "MUTATING", "MUTATING"),
        ("DELETE", "SELECT 1", "DESTRUCTIVE", "DESTRUCTIVE"),
        ("MIGRATION", "SELECT 1", "MIGRATION", "MUTATING"),
        ("INSERT", "SELECT 1", "MUTATING", "MUTATING"),
    )
    for verbo, sentencia, clase, efecto in NO_BAJAN:
        r = bases.clasificar(verbo, statement=sentencia)
        t.igual("E-09 %s + %r no baja de clase" % (verbo, sentencia), clase,
                r["operationClass"])
        t.igual("E-09 %s + %r no baja de efecto" % (verbo, sentencia), efecto,
                r["effectiveSideEffects"])

    # 🔴 **Y una comilla no baja nada.** Lo trajo la segunda refutacion y era la quinta forma
    # de fail-open, peor que las cuatro anteriores: las otras exigian un verbo raro -`INTO`,
    # `OUTFILE`, `/*!`, un statement que no era texto- y esta es SQL ordinario. El barrido
    # quitaba los comentarios ANTES de tapar los literales, asi que un `--` o un `/*` adentro
    # de un literal se comia todo lo que seguia:
    #
    #     SELECT '--x' ; UPDATE t SET a=1    ->  READ_ONLY, PERMITIDO en los cuatro ambientes
    #     SELECT '--' ; DROP TABLE t         ->  READ_ONLY, PERMITIDO en PRD
    #
    # No es que el barrido no subio: BAJO. El motor ejecuta las dos sentencias y el barrido
    # veia una.
    CON_UNA_COMILLA = (
        ("un -- adentro de un literal", "SELECT '--' ; DROP TABLE t", "DDL", "DESTRUCTIVE"),
        ("y con texto alrededor", "SELECT '--x' ; UPDATE t SET a=1", "MUTATING", "MUTATING"),
        ("un /* adentro de un literal", "SELECT '/*' ; DROP TABLE t /* ' */", "DDL",
         "DESTRUCTIVE"),
        ("una comilla doble", 'SELECT "--" ; DELETE FROM t', "DESTRUCTIVE", "DESTRUCTIVE"),
        ("un -- en el medio de un literal", "SELECT 'a--b'; TRUNCATE TABLE t", "DDL",
         "DESTRUCTIVE"),
        ("un retorno de carro, que postgres corta", "SELECT 1 --\r DROP TABLE t", "DDL",
         "DESTRUCTIVE"),
        ("una comilla doblada", "SELECT 'it''s ; DROP' ; DROP TABLE t", "DDL", "DESTRUCTIVE"),
        # 🔴 **Las CINCO formas de encomillar, no dos.** La tercera refutacion encontro la sexta
        # forma de fail-open y era la misma especie por otra comilla: `_enmascarar` conocia `'`
        # y `"`, y los motores del catalogo tienen tres mas. `engine` es un string libre en el
        # schema de perfil, asi que ningun motor esta fuera de alcance.
        ("dollar-quoting de postgres", "SELECT $$--$$ AS c; DROP TABLE t", "DDL",
         "DESTRUCTIVE"),
        ("dollar-quoting con tag", "SELECT $tag$--$tag$ AS c; DROP TABLE t", "DDL",
         "DESTRUCTIVE"),
        ("dollar-quoting con un UPDATE detras", "SELECT $$--$$ AS c; UPDATE t SET a=1",
         "MUTATING", "MUTATING"),
        ("un alias entre backticks de mysql", "SELECT 1 AS `--`; DROP TABLE t", "DDL",
         "DESTRUCTIVE"),
        ("un alias entre corchetes de t-sql", "SELECT 1 AS [--]; DROP TABLE t", "DDL",
         "DESTRUCTIVE"),
        ("un /* adentro de un corchete", "SELECT 1 AS [/*]; DROP TABLE t /* ] */", "DDL",
         "DESTRUCTIVE"),
        # 🔴 **Las seis formas de la cuarta refutacion.** Ninguna se tapa agregando una comilla
        # mas: las seis salen porque `_candidatos_crudos` lee el texto SIN enmascarar nada y ve
        # el verbo que abre cada sentencia. Cuatro pasadas seguidas encontraron esta misma
        # especie por una comilla distinta, y agregar la septima tampoco habria sido la ultima.
        ("mysql exige un blanco tras el --", "SELECT 1--2; DROP TABLE t", "DDL", "DESTRUCTIVE"),
        ("la comilla escapada con barra", "SELECT 'a\\' -- ' ; DROP TABLE t", "DDL",
         "DESTRUCTIVE"),
        ("postgres anida los bloques", "SELECT 1 /* /* */ -- */ ; DROP TABLE t", "DDL",
         "DESTRUCTIVE"),
        ("dos arrays que cierran juntos",
         "SELECT ARRAY[[1],[2]]; DROP TABLE t; SELECT x[1] FROM u", "DDL", "DESTRUCTIVE"),
        ("un identificador con dos pesos",
         "SELECT a$$b; DROP TABLE t; SELECT c$$d", "DDL", "DESTRUCTIVE"),
        ("el # de mysql con un /* adentro",
         "SELECT 1 # /*\n; DROP TABLE t; SELECT 1 /* */", "DDL", "DESTRUCTIVE"),
        # 🔴 Y la sentencia escondida puede empezar por un PREFIJO en vez de por un verbo: la
        # lectura cruda tiene que mirar los verbos de un `WITH`, no solo su primer token.
        ("una sentencia escondida que empieza con WITH",
         "SELECT 'a''; WITH x AS (SELECT 1) DELETE FROM t' FROM t", "DESTRUCTIVE",
         "DESTRUCTIVE"),
        ("un WITH escondido que termina en DROP",
         "SELECT 'a''; WITH x AS (SELECT 1) DROP TABLE t' FROM t", "DDL", "DESTRUCTIVE"),
    )
    for nombre, sentencia, clase, efecto in CON_UNA_COMILLA:
        r = bases.clasificar("SELECT", statement=sentencia)
        t.igual("E-09 con %s la clase es %s" % (nombre, clase), clase, r["operationClass"])
        t.igual("E-09 con %s el efecto es %s" % (nombre, efecto), efecto,
                r["effectiveSideEffects"])
        # 🔴 Y se mide donde importa. En los tres de promocion se DENIEGA —era ahi donde el
        # `SELECT` con la comilla salia permitido— y en DEV se permite, porque DEV es el unico
        # ambiente que muta: lo que cambia en DEV es la CLASE con la que pasa.
        for ambiente in PROMOCION:
            op = _op(bases.resolver(_pedido(ambiente=ambiente, statement=sentencia),
                                    perfiles=_perfiles()))
            t.igual("E-09 con %s no se permite en %s" % (nombre, ambiente), False,
                    op["allowed"])
        en_dev = bases.resolver(_pedido(ambiente=DEV, statement=sentencia),
                                perfiles=_perfiles())
        # 📌 La clase, y no solo el riesgo. `riesgo_de("READ_ONLY","DEV")` y
        # `riesgo_de("MUTATING","DEV")` devuelven los DOS `HIGH` sin aprobacion, asi que para
        # las filas MUTANTES afirmar el riesgo en DEV es inerte: con el bug viejo puesto
        # seguiria en verde. Lo encontro la tercera refutacion. La clase si discrimina en las
        # siete filas, y el riesgo se conserva porque muerde en las destructivas.
        t.igual("E-09 con %s en DEV la clase sigue siendo la alta" % nombre, clase,
                _op(en_dev)["operationClass"])
        t.igual("E-09 con %s en DEV el efecto tambien" % nombre, efecto,
                _op(en_dev)["effectiveSideEffects"])
        t.igual("E-09 con %s en DEV el riesgo sube" % nombre,
                "CRITICAL" if efecto == "DESTRUCTIVE" else "HIGH", en_dev["risk"]["level"])
        t.igual("E-09 con %s en DEV la aprobacion la decide el efecto" % nombre,
                efecto == "DESTRUCTIVE", en_dev["risk"]["approvalRequired"])

    # 📌 Y al reves: un verbo adentro de un literal, SIN un `;` de por medio, no sube nada. Es
    # lo que el enmascarado sigue ganando, y es la razon por la que la lectura cruda mira solo
    # el verbo que ABRE cada sentencia y no todos los que aparecen.
    NO_SUBEN = (
        ("un comentario con una comilla adentro", "SELECT 1 -- it's fine\n ; SELECT 2"),
        ("un bloque con una comilla adentro", "SELECT 1 /* it's fine */ ; SELECT 2"),
        ("un ; adentro de un literal", "SELECT 'a;b' FROM t"),
        ("un literal con una barra", "SELECT 'a/*b' FROM t"),
        ("un verbo adentro de un literal", "SELECT * FROM t WHERE accion = 'DELETE'"),
        ("dos verbos adentro de un literal", "SELECT * FROM t WHERE nota = 'no DROP ni TRUNCATE'"),
        ("un array anidado de postgres", "SELECT ARRAY[[1,2],[3,4]] FROM t"),
        ("un identificador con dos pesos", "SELECT a$$b FROM t"),
        ("una directiva de oracle", "SELECT $$PLSQL_LINE FROM dual"),
        ("un subindice de array", "SELECT x[1] FROM u"),
    )
    for nombre, sentencia in NO_SUBEN:
        t.igual("E-09 con %s sigue siendo READ_ONLY" % nombre, "READ_ONLY",
                bases.clasificar("SELECT", statement=sentencia)["effectiveSideEffects"])

    # 🔴 Y el `$` pegado a un identificador NO abre un dollar-quote. Se mide sobre el
    # enmascarado y no sobre la clase, porque la lectura cruda tapa el agujero igual y sin esto
    # la asercion no distinguiria: lo que se rompe sin el lookbehind es que `a$$b ... c$$d` se
    # traga TODO lo que hay en el medio, y ahi el enmascarado deja de decir la verdad.
    CON_PESOS = "SELECT a$$b; DROP TABLE t; SELECT c$$d"
    partes, entero = bases._sentencias(CON_PESOS)
    t.igual("E-09 `a$$b` no abre un dollar-quote: siguen siendo tres sentencias", 3,
            len(partes))
    t.verdadero("E-09 y el texto queda entero", entero)
    t.contiene("E-09 y el DROP sigue a la vista para el enmascarado", "DROP", " | ".join(partes))

    # 🔴 **Lo que el diseno CUESTA, medido y no escondido.** Un `;` adentro de un literal,
    # seguido de un verbo de la tabla, se deniega. `SELECT 'a''; DROP TABLE t' FROM t` es una
    # sola sentencia para Postgres —la comilla doblada no cierra— y son dos para un motor que
    # lea `''` distinto. **El harness no puede saber cual**: donde termina un literal lo decide
    # el dialecto y `engine` es un string libre. Cuando las dos lecturas discrepan se toma la
    # peligrosa, que es lo que el pedido de instalacion dice con todas las letras: *una negacion
    # falsa es aceptable y un permiso falso no*.
    EL_PRECIO = (
        ("una comilla doblada con un ; adentro", "SELECT 'a''; DROP TABLE t' FROM t"),
        ("dos comillas dobladas seguidas", "SELECT 'a''''b; DROP TABLE t' FROM t"),
        ("un backtick doblado de mysql", "SELECT 1 AS `a``; DROP TABLE t` FROM x"),
        ("dollar-quoting con un ; adentro", "SELECT $$a; DROP TABLE t$$ FROM t"),
        ("dollar-quoting con tag y un ; adentro", "SELECT $q$a; DROP TABLE t$q$ FROM t"),
    )
    for nombre, sentencia in EL_PRECIO:
        t.igual("E-09 con %s se deniega de mas" % nombre, "DESTRUCTIVE",
                bases.clasificar("SELECT", statement=sentencia)["effectiveSideEffects"])
        # Y el precio es solo ese: el enmascarado SIGUE leyendolas como una sola sentencia, asi
        # que sin el `;` de por medio no habria denegacion.
        una_sola, entero = bases._sentencias(sentencia)
        t.igual("E-09 el enmascarado lee %s como una sola" % nombre, 1, len(una_sola))
        t.verdadero("E-09 y la lee entera: %s" % nombre, entero)

    # 📌 El identificador de T-SQL es el unico que las DOS lecturas deniegan, porque el corchete
    # dejo de ser una forma de comilla: como quoting es de T-SQL y en Postgres y MySQL es
    # subindice de array, y tratarlo como comilla hacia que `SELECT ARRAY[[1,2],[3,4]]` —que
    # esta dos listas mas arriba— cayera denegado en los cuatro ambientes. Se eligio el error
    # que le pasa al motor mas usado; el de T-SQL queda declarado acá y no descubierto despues.
    DE_T_SQL = "SELECT 1 AS [a]]; DROP TABLE t] FROM x"
    t.igual("E-09 un identificador de T-SQL con ; adentro se deniega", "DESTRUCTIVE",
            bases.clasificar("SELECT", statement=DE_T_SQL)["effectiveSideEffects"])
    t.igual("E-09 y el enmascarado tampoco lo lee como uno solo", 2,
            len(bases._sentencias(DE_T_SQL)[0]))

    # 🔴 Y los efectos son **el mismo objeto** que los de `tools`, no una copia con los mismos
    # valores. Comparar por igualdad no podia fallar —`bases.EFECTOS is tools.SIDE_EFFECTS` ya
    # es `True`— y seguiria en verde el dia que alguien escribiera la tupla a mano, que es
    # exactamente lo que el docstring del modulo dice evitar. Lo encontro la tercera refutacion.
    t.verdadero("E-09 los efectos son los de tools, el mismo objeto",
                bases.EFECTOS is c_tools.SIDE_EFFECTS)
    t.igual("E-09 y su orden es el del contrato de riesgo", list(c_tools.SIDE_EFFECTS),
            list(bases.EFECTOS))


def test_e10_una_sentencia_sin_clasificar_deniega_todo(t):
    """E-10 — la union de las clases, y el pedido entero denegado si alguna no se puede leer."""
    # Varias sentencias: gana la mas alta.
    r = bases.clasificar("SELECT", statement="SELECT 1; SELECT 2; UPDATE t SET a=1 WHERE b=1")
    t.igual("E-10 gana la mas alta de todas", "MUTATING", r["effectiveSideEffects"])

    # Una que no se puede clasificar deniega el pedido ENTERO, no se saltea.
    SIN_LEER = (
        "SELECT 1; SHOW TABLES",
        "SHOW TABLES; SELECT 1",
        "SELECT 1; EXPLAIN ANALYZE SELECT 1",
        "SELECT 1; GRANT ALL ON t TO alguien",
        "SELECT 1; CALL algun_procedimiento()",
        "SELECT 1; ;; SELECT 2; VACUUM FULL",
        "DO $$ BEGIN END $$",
        "BEGIN; UPDATE t SET a=1 WHERE b=1; COMMIT",
        "-- solo un comentario",
        "/* nada */",
    )
    # 📌 Una sentencia en BLANCOS no esta aca: es indistinguible de no traer sentencia, y asi la
    # trata E-11 para el DELETE -sin alcance establecido, destructivo-. Pedirle a E-10 que la
    # dejara sin clasificar contradecia a E-11. Lo ilegible es el texto que REDUCE a nada.
    for sentencia in SIN_LEER:
        r = bases.clasificar("SELECT", statement=sentencia)
        t.igual("E-10 %r no se clasifica" % sentencia[:38], bases.SIN_CLASIFICAR, r["problem"])
        op = _op(bases.resolver(_pedido(statement=sentencia), perfiles=_perfiles()))
        t.igual("E-10 %r se deniega en DEV" % sentencia[:38], False, op["allowed"])
        t.igual("E-10 %r con su motivo" % sentencia[:38], bases.SIN_CLASIFICAR,
                op["denialReason"])

    # 🔴 Un `WITH` cuyo cuerpo no lleva ningun verbo de la tabla. Es el UNICO camino que
    # llega a esa guarda -el primer token filtra todo lo demas-, y sin este caso cambiar ese
    # `return` por un `continue` no ponia nada en rojo.
    SOLO_WITH = ("WITH x AS (foo) bar",
                 "WITH x AS (algo) y",
                 "SELECT 1; WITH x AS (nada) z")
    for sentencia in SOLO_WITH:
        t.igual("E-10 %r no se clasifica" % sentencia, bases.SIN_CLASIFICAR,
                bases.clasificar("SELECT", statement=sentencia)["problem"])
    # Y un WITH que SI termina en un verbo de la tabla se clasifica por ese verbo.
    t.igual("E-10 un WITH con una lectura adentro es lectura", "READ_ONLY",
            bases.clasificar("SELECT",
                             statement="WITH x AS (SELECT 1) SELECT * FROM x")[
                "effectiveSideEffects"])

    # 🔴 Un `statement` que NO ES TEXTO se deniega, no se descarta. La version anterior
    # hacia `statement if isinstance(statement, str) else ""`, asi que una lista, un
    # diccionario, bytes o una tupla desactivaban el barrido EN SILENCIO:
    #
    #     resolver(PRD, "SELECT", statement=["DROP TABLE t"])  ->  allowed=True
    #
    # Un DROP declarado como SELECT, permitido en produccion, mandando el SQL como lista. Es
    # fail-OPEN en el unico modulo cuya doctrina entera es fail-closed.
    NO_ES_TEXTO = (["DROP TABLE t"], {"sql": "DROP TABLE t"}, ("DROP TABLE t",),
                   b"DROP TABLE t", 1, True, 3.5, {"DROP"}, object())
    for valor in NO_ES_TEXTO:
        r = bases.clasificar("SELECT", statement=valor)
        t.igual("E-10 un statement %s no se clasifica" % type(valor).__name__,
                bases.SIN_CLASIFICAR, r["problem"])
        for ambiente in (DEV,) + PROMOCION:
            op = _op(bases.resolver(_pedido(ambiente=ambiente, statement=valor),
                                    perfiles=_perfiles()))
            t.igual("E-10 un statement %s no se permite en %s"
                    % (type(valor).__name__, ambiente), False, op["allowed"])
            t.igual("E-10 un statement %s lo dice en %s"
                    % (type(valor).__name__, ambiente), bases.SIN_CLASIFICAR,
                    op["denialReason"])
    # Y `None` SI es "no vino sentencia", que es distinto de "vino mal".
    t.igual("E-10 sin sentencia un SELECT se clasifica", "READ_ONLY",
            bases.clasificar("SELECT", statement=None)["effectiveSideEffects"])

    # 🔴 Un comentario condicional de motor -`/*! ... */`- NO es un comentario: MySQL lo
    # EJECUTA. Tratarlo como inerte convertia `SELECT 1 /*! ; UPDATE t SET a=1 */` en un
    # SELECT permitido. Un barrido no es un parser, asi que se deniega.
    EJECUTABLES = ("SELECT 1 /*! ; UPDATE t SET a=1 */",
                   "SELECT 1 /*!40000 ; DROP TABLE t */",
                   "/*! UPDATE t SET a=1 */ SELECT 1",
                   "SELECT /*!*/ 1")
    for sentencia in EJECUTABLES:
        t.igual("E-10 %r no se clasifica" % sentencia[:36], bases.SIN_CLASIFICAR,
                bases.clasificar("SELECT", statement=sentencia)["problem"])
        t.igual("E-10 %r no se permite en PRD" % sentencia[:36], False,
                _op(_resolver(ambiente=PRD, statement=sentencia))["allowed"])

    # Los comentarios no permiten bajar nada: se quitan y lo que queda decide.
    t.igual("E-10 un comentario no esconde un DROP", "DESTRUCTIVE",
            bases.clasificar("SELECT", statement="SELECT 1 -- inocente\n; DROP TABLE t")[
                "effectiveSideEffects"])
    t.igual("E-10 ni un comentario de bloque", "DESTRUCTIVE",
            bases.clasificar("SELECT", statement="SELECT 1 /* x */; DROP TABLE t")[
                "effectiveSideEffects"])

    # 🔴 **Un literal o un comentario de bloque sin cerrar no se interpreta a medias.** Taparlo
    # hasta el final del texto escondería lo que venga después —`SELECT 'abc ; DROP TABLE t`—,
    # que es la misma forma de fail-open que la comilla de E-09 por otra puerta. Un motor
    # tampoco lo ejecutaria, asi que el pedido entero queda sin clasificar.
    SIN_CERRAR = (
        "SELECT 'abc ; DROP TABLE t",
        'SELECT "abc ; DROP TABLE t',
        "SELECT 1 /* sin cerrar ; DROP TABLE t",
        "SELECT 'a''b ; TRUNCATE TABLE t",
        "SELECT 1 FROM t WHERE x = '",
        # El backtick sin cerrar tambien.
        "SELECT 1 AS `abc ; DROP TABLE t",
    )
    # 📌 Los `$$` y los `[` sin cerrar NO estan aca, y es deliberado desde la cuarta refutacion:
    # `$$` sin cierre no es texto malformado —`SELECT $$PLSQL_LINE FROM dual` es una directiva
    # valida de Oracle— y `[` dejo de ser una forma de comilla. Los dos casos ahora clasifican
    # por lo que hay detras del `;`, que dice mas que "no se pudo leer".
    for sentencia, efecto in (("SELECT $$abc ; DROP TABLE t", "DESTRUCTIVE"),
                              ("SELECT $tag$abc ; DROP TABLE t", "DESTRUCTIVE"),
                              ("SELECT 1 AS [abc ; DROP TABLE t", "DESTRUCTIVE"),
                              ("SELECT $$PLSQL_LINE FROM dual", "READ_ONLY"),
                              ("SELECT ARRAY[[1,2],[3,4]] FROM t", "READ_ONLY"),
                              ("SELECT a$$b FROM t", "READ_ONLY")):
        t.igual("E-10 %r clasifica en vez de caerse" % sentencia[:34], efecto,
                bases.clasificar("SELECT", statement=sentencia)["effectiveSideEffects"])
    for sentencia in SIN_CERRAR:
        r = bases.clasificar("SELECT", statement=sentencia)
        t.igual("E-10 %r no se clasifica" % sentencia[:36], bases.SIN_CLASIFICAR, r["problem"])
        for ambiente in (DEV,) + PROMOCION:
            op = _op(bases.resolver(_pedido(ambiente=ambiente, statement=sentencia),
                                    perfiles=_perfiles()))
            t.igual("E-10 %r no se permite en %s" % (sentencia[:28], ambiente), False,
                    op["allowed"])
            t.igual("E-10 %r con su motivo en %s" % (sentencia[:28], ambiente),
                    bases.SIN_CLASIFICAR, op["denialReason"])
    # Y el mismo texto CERRADO si se lee, o el escenario estaria probando que lo roto falla.
    t.igual("E-10 el mismo texto cerrado si se lee", "DESTRUCTIVE",
            bases.clasificar("SELECT", statement="SELECT 'abc' ; DROP TABLE t")[
                "effectiveSideEffects"])
    t.igual("E-10 y el bloque cerrado tambien", "READ_ONLY",
            bases.clasificar("SELECT", statement="SELECT 1 /* cerrado */ FROM t")[
                "effectiveSideEffects"])


def test_e11_delete_sin_alcance_es_destructivo(t):
    """E-11 — el alcance que no se puede establecer no se asume favorable."""
    CASOS = (
        ("con WHERE", "DELETE FROM t WHERE id = 1", "MUTATING", "MUTATING"),
        ("con where en minuscula", "delete from t where id = 1", "MUTATING", "MUTATING"),
        ("con WHERE y salto", "DELETE FROM t\n WHERE id = 1", "MUTATING", "MUTATING"),
        ("sin WHERE", "DELETE FROM t", "DESTRUCTIVE", "DESTRUCTIVE"),
        ("con el WHERE comentado", "DELETE FROM t -- WHERE id = 1", "DESTRUCTIVE",
         "DESTRUCTIVE"),
        ("con el WHERE en un bloque", "DELETE /* WHERE id=1 */ FROM t", "DESTRUCTIVE",
         "DESTRUCTIVE"),
        ("sin sentencia", None, "DESTRUCTIVE", "DESTRUCTIVE"),
        ("con la sentencia vacia", "", "DESTRUCTIVE", "DESTRUCTIVE"),
        ("con la sentencia en blancos", "   ", "DESTRUCTIVE", "DESTRUCTIVE"),
    )
    for nombre, sentencia, clase, efecto in CASOS:
        r = bases.clasificar("DELETE", statement=sentencia)
        t.igual("E-11 un DELETE %s es %s" % (nombre, clase), clase, r["operationClass"])
        t.igual("E-11 un DELETE %s tiene efecto %s" % (nombre, efecto), efecto,
                r["effectiveSideEffects"])

    # 🔴 El WHERE tiene que ser **del DELETE**, no de cualquier parte de la sentencia. La
    # version anterior buscaba el token en el texto entero, y estos tres BORRAN LA TABLA
    # ENTERA y salian MUTATING —o sea HIGH sin aprobacion en DEV cuando corresponde CRITICAL
    # con aprobacion, o sea el DELETE completo aplicandose sin que una persona decida—:
    DE_OTRA_CLAUSULA = (
        ("el WHERE es del CTE", "WITH x AS (SELECT * FROM o WHERE a=1) DELETE FROM t"),
        ("el WHERE es del subquery", "DELETE FROM t USING (SELECT id FROM o WHERE x=1) s"),
        ("el WHERE es un identificador", 'DELETE FROM "where"'),
        ("el WHERE lleva esquema", "DELETE FROM esquema.where"),
        ("el WHERE es de otro DELETE", "DELETE FROM a WHERE x=1; DELETE FROM b"),
        ("el WHERE esta anidado dos veces",
         "DELETE FROM t USING (SELECT id FROM (SELECT * FROM z WHERE q=1) y) s"),
        ("el WHERE esta en un literal", "DELETE FROM t /* x */ -- nada\n"),
    )
    for nombre, sentencia in DE_OTRA_CLAUSULA:
        r = bases.clasificar("DELETE", statement=sentencia)
        t.igual("E-11 cuando %s es destructivo" % nombre, "DESTRUCTIVE",
                r["effectiveSideEffects"])
        t.igual("E-11 cuando %s es de clase destructiva" % nombre, "DESTRUCTIVE",
                r["operationClass"])
        # Y el efecto es medible en la compuerta: CRITICAL con aprobacion, no HIGH sin ella.
        salida = _resolver(ambiente=DEV, verbo="DELETE", statement=sentencia)
        t.igual("E-11 cuando %s exige aprobacion en DEV" % nombre, True,
                salida["risk"]["approvalRequired"])
        t.igual("E-11 cuando %s el riesgo es CRITICAL" % nombre, "CRITICAL",
                salida["risk"]["level"])

    # Y un WHERE que SI es del DELETE, aunque tenga un subquery adentro, establece el alcance.
    CON_ALCANCE_PROPIO = (
        ("con un subquery adentro", "DELETE FROM t WHERE id IN (SELECT x FROM o)"),
        ("con parentesis alrededor", "DELETE FROM t WHERE (a=1 AND b=2)"),
        ("con un CTE y su propio WHERE",
         "WITH x AS (SELECT 1) DELETE FROM t WHERE id IN (SELECT * FROM x)"),
    )
    for nombre, sentencia in CON_ALCANCE_PROPIO:
        t.igual("E-11 un DELETE %s tiene alcance" % nombre, "MUTATING",
                bases.clasificar("DELETE", statement=sentencia)["effectiveSideEffects"])

    # 🔴 Y en un pedido de varias, basta UNO sin alcance.
    t.igual("E-11 uno sin alcance entre dos sube todo", "DESTRUCTIVE",
            bases.clasificar("DELETE",
                             statement="DELETE FROM a WHERE x=1; DELETE FROM b")[
                "effectiveSideEffects"])

    # 🔴 **La imagen espejo del CTE, que la segunda refutacion encontro.** El arreglo anterior
    # cubria "el WHERE esta en la CTE y el DELETE afuera" y no su reverso: el DELETE adentro de
    # la CTE y el WHERE del SELECT de afuera. La busqueda hacia `max(0, profundidad - 1)`, que
    # es justamente perder la unica senal de que se salio del alcance, asi que el `)` que cierra
    # la CTE dejaba la profundidad en cero y el WHERE de afuera contaba.
    #
    #     WITH d AS (DELETE FROM a RETURNING *) SELECT * FROM d WHERE id > 5
    #
    # Ese DELETE borra la tabla `a` ENTERA y salia MUTATING: HIGH sin aprobacion en DEV, cuando
    # corresponde CRITICAL con aprobacion.
    EL_ESPEJO = (
        ("el DELETE esta en la CTE y el WHERE afuera",
         "WITH d AS (DELETE FROM a RETURNING *) SELECT * FROM d WHERE id > 5"),
        ("con dos CTE", "WITH a AS (SELECT 1), d AS (DELETE FROM b RETURNING *) "
                        "SELECT * FROM d WHERE id > 5"),
        ("el WHERE del otro DELETE esta en un literal",
         "DELETE FROM t WHERE x='--' ; DELETE FROM b"),
        ("hay dos DELETE y uno esta en una CTE sin alcance",
         "WITH d AS (DELETE FROM a RETURNING *) DELETE FROM b WHERE id=1"),
        # 🔴 El caso que obliga a mirarlos TODOS y no al primero: el primer DELETE declara su
        # alcance y el segundo no. Mirando solo el primero, este borra la tabla `b` entera y
        # sale MUTATING. Y es una sola sentencia, asi que partir por `;` no lo alcanza.
        ("el primero tiene alcance y el segundo no",
         "WITH d AS (DELETE FROM a WHERE id=1 RETURNING *) DELETE FROM b"),
        # Las seis formas de la cuarta refutacion, del lado del alcance: el segundo DELETE no
        # declara el suyo y borra la tabla entera.
        ("mysql no corta el -- sin blanco", "DELETE FROM t WHERE id=1--2; DELETE FROM b"),
        ("postgres anida los bloques",
         "DELETE FROM t WHERE id=1 /* /* */ -- */ ; DELETE FROM b"),
        ("la comilla escapada con barra",
         "DELETE FROM t WHERE x='a\\' -- ' ; DELETE FROM b"),
        ("dos arrays que cierran juntos",
         "DELETE FROM t WHERE tags=ARRAY[[1],[2]]; DELETE FROM b; SELECT x[1] FROM u"),
        ("un identificador con dos pesos",
         "DELETE FROM t WHERE x=a$$b; DELETE FROM c; SELECT d$$e"),
    )
    for nombre, sentencia in EL_ESPEJO:
        r = bases.clasificar("DELETE", statement=sentencia)
        t.igual("E-11 cuando %s es destructivo" % nombre, "DESTRUCTIVE",
                r["effectiveSideEffects"])
        salida = _resolver(ambiente=DEV, verbo="DELETE", statement=sentencia)
        t.igual("E-11 cuando %s exige aprobacion en DEV" % nombre, True,
                salida["risk"]["approvalRequired"])
        t.igual("E-11 cuando %s el riesgo es CRITICAL" % nombre, "CRITICAL",
                salida["risk"]["level"])

    # 📌 Y un DELETE que SI declara su alcance adentro de una CTE sigue siendo MUTATING: el
    # arreglo no puede ser "todo lo que este en una CTE es destructivo".
    t.igual("E-11 un DELETE con su WHERE adentro de la CTE tiene alcance", "MUTATING",
            bases.clasificar("DELETE",
                             statement="WITH d AS (DELETE FROM a WHERE id=1 RETURNING *) "
                                       "SELECT * FROM d")["effectiveSideEffects"])
    t.igual("E-11 y con una comilla doblada adentro del WHERE tambien", "MUTATING",
            bases.clasificar("DELETE",
                             statement="DELETE FROM t WHERE x='it''s'")[
                "effectiveSideEffects"])


def test_e12_el_resolvedor_no_ejecuta_nada(t):
    """E-12 (DB-28, §4) — se verifica sobre EL MODULO, no sobre una salida.

    🔴 Una promesa sobre lo que un modulo NO hace no se prueba mirando lo que devolvio una vez.
    El sujeto es lo que el archivo importa y lo que llama.
    """
    fuente = (BIN / "orquestacion" / "bases.py").read_text(encoding="utf-8")
    arbol = ast.parse(fuente)

    importados = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            importados.update(a.name.split(".")[0] for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.module:
                importados.add(nodo.module.split(".")[0])
            if nodo.level:
                importados.update(a.name.split(".")[0] for a in nodo.names)

    # 🔴 El conjunto ENTERO va clavado, no una lista negra. Una lista negra no ve el driver
    # numero once; esto obliga a mirar cualquier import nuevo.
    # 📌 `roster` entro cuando se arreglo la resolucion de rutas: `reglas/` cuelga a
    # distinta altura instalado que en el repositorio, y `roster.ruta_de_regla` existe por eso.
    t.igual("E-12 el modulo importa exactamente esto",
            ["io", "json", "os", "re", "roster", "rutas", "sys", "tools"],
            sorted(importados))

    DRIVERS = ("psycopg2", "psycopg", "pymysql", "MySQLdb", "sqlite3", "pyodbc", "cx_Oracle",
               "oracledb", "sqlalchemy", "asyncpg", "pymssql", "mariadb", "ibm_db", "socket",
               "subprocess", "urllib", "requests", "http", "ssl")
    for driver in DRIVERS:
        t.verdadero("E-12 no importa %s" % driver, driver not in importados)
    t.verdadero("E-12 y no importa el almacen de secretos",
                "integraciones" not in importados and "almacen" not in importados)

    # Ni nombra una funcion de ejecucion, ni abre nada.
    llamadas = {n.func.attr for n in ast.walk(arbol)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    # 📌 `get` y `set` NO estan en la lista: son acceso a un diccionario y la funcion del
    # borde los usa contra el almacen que RECIBE. Lo que prueba que el modulo no puede llegar a
    # una credencial es el conjunto de imports clavado de arriba, no el nombre de un metodo.
    for prohibida in ("connect", "execute", "executemany", "cursor", "commit", "rollback",
                      "system", "popen", "spawn", "Popen"):
        t.verdadero("E-12 no llama a .%s()" % prohibida, prohibida not in llamadas)

    # Y `resolver` no llama a la funcion del borde de ejecucion.
    cuerpo = [n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name == "resolver"]
    t.igual("E-12 resolver existe una sola vez", 1, len(cuerpo))
    internas = {n.func.id for n in ast.walk(cuerpo[0])
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    t.verdadero("E-12 resolver no llama a resolver_secreto",
                "resolver_secreto" not in internas)

    # La decision se toma con el pedido y la politica, y nada mas: sin red, sin disco del
    # proyecto, sin almacen. Para el mismo pedido devuelve siempre lo mismo.
    pedido = _pedido(ambiente=PRD, verbo="UPDATE")
    primera = bases.resolver(pedido, perfiles=_perfiles())
    segunda = bases.resolver(pedido, perfiles=_perfiles())
    t.igual("E-12 la misma entrada da la misma salida", primera, segunda)


# -- E-13 a E-17 — DEV, que es FULL y no es sin restricciones ------------------

def test_e13_select_en_dev_se_permite(t):
    """E-13 (DB-06)."""
    op = _op(_resolver(ambiente=DEV, verbo="SELECT"))
    t.igual("E-13 se permite", True, op["allowed"])
    t.igual("E-13 sin motivo de negacion", None, op["denialReason"])
    t.igual("E-13 de clase READ_ONLY", "READ_ONLY", op["operationClass"])


def test_e14_update_en_dev_se_permite(t):
    """E-14 (DB-07)."""
    op = _op(_resolver(ambiente=DEV, verbo="UPDATE",
                       statement="UPDATE t SET a=1 WHERE b=2"))
    t.igual("E-14 se permite", True, op["allowed"])
    t.igual("E-14 de clase MUTATING", "MUTATING", op["operationClass"])
    t.igual("E-14 con efecto MUTATING", "MUTATING", op["effectiveSideEffects"])


def test_e15_alter_en_dev_se_permite_y_la_compuerta_decide(t):
    """E-15 (DB-08) — el ambiente permite; la compuerta de riesgo opina aparte."""
    salida = _resolver(ambiente=DEV, verbo="ALTER", statement="ALTER TABLE t ADD c int")
    t.igual("E-15 el ambiente lo permite", True, _op(salida)["allowed"])
    t.igual("E-15 de clase DDL", "DDL", _op(salida)["operationClass"])
    t.igual("E-15 con efecto MUTATING", "MUTATING", _op(salida)["effectiveSideEffects"])
    t.igual("E-15 y el riesgo es el que la compuerta deriva", "HIGH", salida["risk"]["level"])
    t.igual("E-15 sin exigir aprobacion", False, salida["risk"]["approvalRequired"])


def test_e16_lo_destructivo_en_dev_pasa_por_la_compuerta_que_ya_existe(t):
    """E-16 (DB-09) — el riesgo sale de tools.py, y los numeros se midieron.

    🔴 Dos escalas de riesgo en el mismo harness es UNA escala: la segunda se usa para
    justificar lo que la primera no dejaba pasar. Aca no hay segunda.
    """
    salida = _resolver(ambiente=DEV, verbo="DROP", statement="DROP TABLE t")
    t.igual("E-16 el ambiente lo permite", True, _op(salida)["allowed"])
    t.igual("E-16 con efecto destructivo", "DESTRUCTIVE", _op(salida)["effectiveSideEffects"])
    t.igual("E-16 el riesgo es CRITICAL", "CRITICAL", salida["risk"]["level"])
    t.igual("E-16 y exige aprobacion humana", True, salida["risk"]["approvalRequired"])

    # 🔴 Los cuatro valores MEDIDOS contra la implementacion actual, exactos. El dia que
    # alguien toque derivar_riesgo, este test obliga a volver.
    MEDIDO = {
        ("READ_ONLY", DEV): ("HIGH", False),
        ("READ_ONLY", QA): ("HIGH", False),
        ("READ_ONLY", HML): ("HIGH", False),
        ("READ_ONLY", PRD): ("HIGH", False),
        ("MUTATING", DEV): ("HIGH", False),
        ("MUTATING", QA): ("HIGH", False),
        ("MUTATING", HML): ("HIGH", False),
        ("MUTATING", PRD): ("CRITICAL", True),
        ("DESTRUCTIVE", DEV): ("CRITICAL", True),
        ("DESTRUCTIVE", QA): ("CRITICAL", True),
        ("DESTRUCTIVE", HML): ("CRITICAL", True),
        ("DESTRUCTIVE", PRD): ("CRITICAL", True),
    }
    for (efecto, ambiente), (nivel, aprueba) in sorted(MEDIDO.items()):
        r = bases.riesgo_de(efecto, ambiente)
        t.igual("E-16 %s en %s es %s" % (efecto, ambiente, nivel), nivel, r["level"])
        t.igual("E-16 %s en %s aprobacion=%s" % (efecto, ambiente, aprueba), aprueba,
                r["approvalRequired"])
        t.verdadero("E-16 %s en %s usa la escala de tools" % (efecto, ambiente),
                    r["level"] in c_tools.RIESGOS)

    # Y el contrato que se le pasa a la compuerta declara lo que el pedido exige.
    contrato = bases.contrato_de_riesgo("MUTATING", PRD)
    t.igual("E-16 declara que sale a la red", True, contrato["networkAccess"])
    t.igual("E-16 y que necesita un secreto", True, contrato["secretsRequired"])
    t.igual("E-16 con alcance de sistema externo", "external-system",
            contrato["blastRadius"]["scope"])
    t.igual("E-16 e impacto de produccion solo en PRD", True,
            contrato["blastRadius"]["productionImpact"])
    for ambiente in (DEV, QA, HML):
        t.igual("E-16 y no en %s" % ambiente, False,
                bases.contrato_de_riesgo("MUTATING", ambiente)["blastRadius"][
                    "productionImpact"])

    # 🔴 El nivel lo calcula tools, no este modulo: se contrasta contra la funcion misma.
    for efecto in c_tools.SIDE_EFFECTS:
        for ambiente in (DEV, QA, HML, PRD):
            esperado = c_tools.derivar_riesgo(bases.contrato_de_riesgo(efecto, ambiente))
            t.igual("E-16 %s/%s coincide con tools.derivar_riesgo" % (efecto, ambiente),
                    esperado, bases.riesgo_de(efecto, ambiente)["level"])


def test_e17_el_descubrimiento_de_esquema_en_dev_precede_a_la_mutacion(t):
    """E-17 (DB-29) — es READ_ONLY y se puede hacer antes de mutar."""
    op = _op(_resolver(ambiente=DEV, verbo="SELECT",
                       statement="SELECT table_name FROM information_schema.tables"))
    t.igual("E-17 se permite", True, op["allowed"])
    t.igual("E-17 y es de solo lectura", "READ_ONLY", op["operationClass"])

    # Y el flujo declarado empieza por el descubrimiento y termina en el artefacto de promocion.
    flujo = bases.FLUJO_DEV_PRIMERO
    t.igual("E-17 el descubrimiento es el segundo paso", "schema-discovery", flujo[1])
    t.verdadero("E-17 y precede a aplicar en DEV",
                flujo.index("schema-discovery") < flujo.index("apply-in-dev"))
    t.verdadero("E-17 que precede a validar", flujo.index("apply-in-dev") < flujo.index(
        "schema-validation"))
    t.igual("E-17 y el ultimo paso es el artefacto versionado", "promotion-artifact",
            flujo[-1])


# -- E-18 a E-23 — QA, HML y PRD -----------------------------------------------

def test_e18_select_se_permite_en_los_tres(t):
    """E-18 (DB-10, DB-16, DB-20)."""
    for ambiente in PROMOCION:
        op = _op(_resolver(ambiente=ambiente, verbo="SELECT", statement="SELECT 1"))
        t.igual("E-18 SELECT en %s se permite" % ambiente, True, op["allowed"])
        t.igual("E-18 SELECT en %s no tiene motivo de negacion" % ambiente, None,
                op["denialReason"])


def test_e19_la_escritura_se_deniega_en_los_tres(t):
    """E-19 (DB-11, DB-12, DB-13, DB-17, DB-21, DB-22)."""
    for ambiente in PROMOCION:
        for verbo, sentencia in (("INSERT", "INSERT INTO t VALUES (1)"),
                                 ("UPDATE", "UPDATE t SET a=1 WHERE b=2"),
                                 ("DELETE", "DELETE FROM t WHERE id=1")):
            op = _op(_resolver(ambiente=ambiente, verbo=verbo, statement=sentencia))
            t.igual("E-19 %s en %s se deniega" % (verbo, ambiente), False, op["allowed"])
            t.igual("E-19 %s en %s con su estado" % (verbo, ambiente), bases.SIN_ESCRITURA,
                    op["denialReason"])


def test_e20_el_ddl_se_deniega_en_los_tres(t):
    """E-20 (DB-14, DB-18, DB-23)."""
    for ambiente in PROMOCION:
        for verbo in ("CREATE", "ALTER", "DROP", "TRUNCATE"):
            op = _op(_resolver(ambiente=ambiente, verbo=verbo))
            t.igual("E-20 %s en %s se deniega" % (verbo, ambiente), False, op["allowed"])
            t.igual("E-20 %s en %s con su estado" % (verbo, ambiente), bases.SIN_DDL,
                    op["denialReason"])


def test_e21_la_migracion_se_deniega_en_los_tres(t):
    """E-21 (DB-15, DB-19, DB-24)."""
    for ambiente in PROMOCION:
        op = _op(_resolver(ambiente=ambiente, verbo="MIGRATION"))
        t.igual("E-21 la migracion en %s se deniega" % ambiente, False, op["allowed"])
        t.igual("E-21 en %s con su estado" % ambiente, bases.SIN_MIGRACION,
                op["denialReason"])
    # Y en DEV si.
    t.igual("E-21 en DEV se permite", True,
            _op(_resolver(ambiente=DEV, verbo="MIGRATION"))["allowed"])


def test_e22_los_tres_sirven_para_inspeccionar_con_select(t):
    """E-22 (DB-30) — y la tabla es cerrada: los verbos de metadata no se asumen portables."""
    CONSULTAS = (
        ("esquema", "SELECT table_name FROM information_schema.tables"),
        ("columnas", "SELECT column_name FROM information_schema.columns WHERE x=1"),
        ("indices", "SELECT indexname FROM pg_indexes"),
        ("restricciones", "SELECT conname FROM pg_constraint"),
        ("diagnostico", "SELECT count(*) FROM t"),
        ("validacion", "SELECT 1 FROM t WHERE a IS NULL"),
        ("historial de migraciones", "SELECT version FROM schema_migrations"),
    )
    for ambiente in PROMOCION:
        for nombre, sentencia in CONSULTAS:
            op = _op(_resolver(ambiente=ambiente, verbo="SELECT", statement=sentencia))
            t.igual("E-22 %s en %s se permite" % (nombre, ambiente), True, op["allowed"])

    # 🔴 Y los de metadata de un motor concreto caen en UNCLASSIFIED en los CUATRO ambientes.
    for verbo in ("SHOW", "DESCRIBE", "EXPLAIN"):
        for ambiente in (DEV,) + PROMOCION:
            op = _op(_resolver(ambiente=ambiente, verbo=verbo))
            t.igual("E-22 %s en %s falla cerrado" % (verbo, ambiente), bases.SIN_CLASIFICAR,
                    op["denialReason"])


def test_e23_el_producto_de_promocion_por_operaciones(t):
    """E-23 — EL PRODUCTO ENTERO, no la lista de veinte celdas del pedido.

    🔴 Para los tres ambientes de promocion, por cada verbo de la tabla cerrada y por cada
    variante de sentencia, SOLO una operacion cuyo efecto sea READ_ONLY puede salir permitida.
    La lista del pedido queda cubierta, y tambien la celda que nadie escribio.
    """
    VARIANTES = (
        ("sin sentencia", None),
        ("con una lectura", "SELECT 1"),
        ("con su propia forma", "__PROPIA__"),
        ("con una escritura adentro", "SELECT 1; UPDATE t SET a=1 WHERE b=1"),
        ("con un DROP adentro", "SELECT 1; DROP TABLE t"),
        ("con un DELETE sin alcance", "SELECT 1; DELETE FROM t"),
    )
    PROPIA = {"SELECT": "SELECT 1", "INSERT": "INSERT INTO t VALUES (1)",
              "UPDATE": "UPDATE t SET a=1 WHERE b=2", "DELETE": "DELETE FROM t WHERE id=1",
              "CREATE": "CREATE TABLE t (a int)", "ALTER": "ALTER TABLE t ADD c int",
              "DROP": "DROP TABLE t", "TRUNCATE": "TRUNCATE TABLE t",
              "MIGRATION": "ALTER TABLE t ADD c int"}

    permitidos, denegados = 0, 0
    for ambiente in PROMOCION:
        for verbo in bases.VERBOS:
            for nombre, sentencia in VARIANTES:
                if sentencia == "__PROPIA__":
                    sentencia = PROPIA[verbo]
                for irreversible in (None, True):
                    pedido = _pedido(ambiente=ambiente, verbo=verbo, statement=sentencia)
                    if irreversible is not None:
                        pedido["migration"] = {"irreversible": irreversible}
                    salida = bases.resolver(pedido, perfiles=_perfiles())
                    op = _op(salida)
                    etiqueta = "%s/%s/%s/irrev=%s" % (ambiente, verbo, nombre, irreversible)

                    if op["allowed"]:
                        permitidos += 1
                        # 🔴 La unica forma de salir permitido es tener efecto READ_ONLY.
                        t.igual("E-23 %s permitido solo si es de lectura" % etiqueta,
                                "READ_ONLY", op["effectiveSideEffects"])
                        t.igual("E-23 %s y de clase READ_ONLY" % etiqueta, "READ_ONLY",
                                op["operationClass"])
                        t.igual("E-23 %s sin motivo de negacion" % etiqueta, None,
                                op["denialReason"])
                    else:
                        denegados += 1
                        t.verdadero("E-23 %s deniega con un estado del contrato" % etiqueta,
                                    op["denialReason"] in bases.ESTADOS_DE_FALLA)
                        t.verdadero("E-23 %s no informa un estado del borde" % etiqueta,
                                    op["denialReason"] not in bases.ESTADOS_DEL_BORDE)
                        # 🔴 La segunda clausula del escenario: **el estado que le corresponde
                        # a su clase**. La version anterior solo afirmaba que el motivo
                        # estuviera entre los diez, y con eso un DROP en QA denegado con
                        # DATABASE_WRITE_NOT_ALLOWED pasaba en verde. El esperado se DERIVA de
                        # la clase, no se escribe: clase -> permiso -> estado.
                        esperado = bases.NEGACION_DE_PERMISO[
                            bases.PERMISO_DE_CLASE[op["operationClass"]]]
                        t.igual("E-23 %s deniega con el estado de su clase" % etiqueta,
                                esperado, op["denialReason"])

    # Los numeros exactos, para que la cobertura del producto no se pueda achicar en silencio.
    t.igual("E-23 se recorrieron 324 celdas", 324, permitidos + denegados)
    # 3 ambientes x SELECT x las tres variantes que no suben el efecto x 2 de irreversible.
    t.igual("E-23 y solo dieciocho salieron permitidas", 18, permitidos)


# -- E-24 a E-28 — los perfiles y los secretos ---------------------------------

def test_e24_cada_ambiente_resuelve_su_propio_perfil(t):
    """E-24 (DB-26) — y dos ambientes no comparten instancia por defecto."""
    perfiles = _perfiles()
    vistos = {}
    for ambiente in (DEV,) + PROMOCION:
        salida = bases.resolver(_pedido(ambiente=ambiente), perfiles=perfiles)
        perfil = salida["connectionProfile"]
        t.igual("E-24 el ambiente viaja arriba", ambiente, salida["environment"])
        t.contiene("E-24 y el perfil de %s es el de %s" % (ambiente, ambiente), ambiente,
                   perfil["hostRef"])
        vistos[ambiente] = perfil["hostRef"]
    t.igual("E-24 los cuatro hostRef son distintos", 4, len(set(vistos.values())))

    # 🔴 El perfil de un ambiente NO contesta por otro: con solo el de DEV cargado, QA no
    # resuelve. Asumir que dos ambientes comparten instancia es como un UPDATE que alguien
    # creia de QA llega a PRD.
    solo_dev = _perfiles(ambientes=(DEV,))
    t.igual("E-24 con solo DEV cargado, DEV resuelve", DEV,
            bases.resolver(_pedido(ambiente=DEV), perfiles=solo_dev)["environment"])
    for ambiente in PROMOCION:
        salida = bases.resolver(_pedido(ambiente=ambiente), perfiles=solo_dev)
        t.igual("E-24 y %s no hereda el de DEV" % ambiente, None, salida["connectionProfile"])
        t.igual("E-24 %s dice que le falta el perfil" % ambiente, bases.SIN_PERFIL,
                _op(salida)["denialReason"])

    # Y dos bases logicas distintas tampoco se mezclan.
    otra = bases.resolver(_pedido(base="reportes"), perfiles=_perfiles())
    t.igual("E-24 otra base logica no usa el perfil de la primera", bases.SIN_PERFIL,
            _op(otra)["denialReason"])


def test_e25_sin_perfil_no_se_inventa_ninguno(t):
    """E-25 (§10) — y el archivo que el harness instala esta VACIO."""
    ruta = REGLAS / "database-profiles.json"
    t.verdadero("E-25 el archivo de perfiles existe", ruta.is_file())
    doc = json.loads(ruta.read_text(encoding="utf-8"))
    t.igual("E-25 y se instala vacio", {}, doc["profiles"])
    t.igual("E-25 el modulo lo lee de ahi", doc, bases.cargar_perfiles())

    # 🔴 El harness no sabe donde vive la base de nadie: sin perfil, no se inventa.
    salida = bases.resolver(_pedido(), perfiles=doc)
    t.igual("E-25 sin perfil no se permite", False, _op(salida)["allowed"])
    t.igual("E-25 y lo dice", bases.SIN_PERFIL, _op(salida)["denialReason"])
    t.igual("E-25 sin publicar un perfil", None, salida["connectionProfile"])
    t.verdadero("E-25 y sin inventar un host", "localhost" not in repr(salida)
                and "127.0.0.1" not in repr(salida))

    # Una negacion mas fuerte manda sobre la falta de perfil: un DROP en PRD dice DDL, no perfil.
    fuerte = bases.resolver(_pedido(ambiente=PRD, verbo="DROP"), perfiles=doc)
    t.igual("E-25 una negacion del ambiente manda sobre la del perfil", bases.SIN_DDL,
            _op(fuerte)["denialReason"])


def test_e26_ningun_valor_de_credencial_sale_del_modulo(t):
    """E-26 (DB-25, §6) — el barrido corre sobre TODA salida del modulo, no sobre una.

    🔴 El perfil lleva solo referencias. Lo que se verifica es que ninguna salida de ninguna
    funcion publica pueda llevar un valor con forma de credencial.
    """
    # Un perfil que ALGUIEN escribio mal: con los valores adentro. El schema lo rechaza...
    envenenado = dict(_perfil(DEV), password="hunter2", username="admin")
    t.verdadero("E-26 el schema rechaza un perfil con valores",
                bool(bases.validar_perfil(envenenado)))

    # ...y el modulo no los propaga ni si alguien saltea el schema.
    perfiles = {"version": "1.0", "profiles": {"main-database/DEV": envenenado}}
    salida = bases.resolver(_pedido(), perfiles=perfiles)
    texto = repr(salida)
    for valor in ("hunter2", "admin"):
        t.verdadero("E-26 el valor %r no sale en la salida" % valor, valor not in texto)

    # El perfil que se publica lleva SOLO los campos del contrato, y todos son referencias.
    limpio = bases.resolver(_pedido(), perfiles=_perfiles())["connectionProfile"]
    t.igual("E-26 el perfil publicado declara exactamente los campos del contrato",
            ["databaseRef", "engine", "hostRef", "passwordSecretRef", "portRef",
             "usernameSecretRef", "version"], sorted(limpio))
    # 🔴 `passwordSecretRef` SI se publica: es una REFERENCIA, y el contrato del pedido dice
    # devolverla. Lo que nunca sale es un valor. Se afirma la diferencia.
    t.verdadero("E-26 la referencia de la contrasena es un nombre, no un valor",
                limpio["passwordSecretRef"].endswith("_PASSWORD")
                and "=" not in limpio["passwordSecretRef"])

    # 🔴 **TODA** salida del modulo, y el sujeto se DERIVA de el. La version anterior recorria
    # nueve entradas escritas a mano y dejaba cinco funciones publicas afuera —una de ellas,
    # `validar_perfil`, devuelve valores del documento adentro del texto de su error—. El
    # sujeto es "lo que sale del modulo", no la lista que este test eligio.
    import inspect
    publicas = sorted(n for n, f in vars(bases).items()
                      if not n.startswith("_") and inspect.isfunction(f)
                      and f.__module__ == bases.__name__)

    # 📌 El veneno va en claves que NO son del contrato. Una **referencia** publicada no es
    # una fuga: el contrato del pedido dice devolver `usernameSecretRef` y `passwordSecretRef`,
    # y lo que ahi vive es el NOMBRE de un secreto. Lo que no puede salir es un VALOR, y la
    # forma de que uno llegue al archivo es que alguien escriba campos de mas.
    ENVENENADO = dict(_perfil(DEV), password="hunter2", username="hunter2admin",
                      passwd="hunter2", secret="hunter2")
    perfiles_malos = {"version": "1.0", "profiles": {"main-database/DEV": ENVENENADO}}

    LLAMADAS = {
        "acceso_de": lambda: bases.acceso_de(DEV),
        "cargar_perfiles": lambda: bases.cargar_perfiles(),
        "cargar_politica": lambda: bases.cargar_politica(),
        "clasificar": lambda: bases.clasificar("DELETE"),
        "clave_de_perfil": lambda: bases.clave_de_perfil("main-database", DEV),
        "contrato_de_riesgo": lambda: bases.contrato_de_riesgo("MUTATING", PRD),
        "perfil_de": lambda: bases.perfil_de("main-database", DEV, perfiles=perfiles_malos),
        "referencias_de": lambda: bases.referencias_de(ENVENENADO),
        "resolver": lambda: bases.resolver(_pedido(), perfiles=perfiles_malos),
        "resolver_secreto": lambda: bases.resolver_secreto("DB_MAIN_DEV_PASSWORD", None),
        "riesgo_de": lambda: bases.riesgo_de("DESTRUCTIVE", PRD),
        "validar_perfil": lambda: bases.validar_perfil(ENVENENADO),
        "validar_politica": lambda: bases.validar_politica(bases.cargar_politica()),
    }
    # 🔴 El invariante: el barrido cubre TODAS las publicas. Una funcion nueva rompe el test.
    t.igual("E-26 el barrido cubre todas las funciones publicas del modulo", publicas,
            sorted(LLAMADAS))

    # Y los caminos de `resolver` que no son el feliz, que tambien son salida del modulo.
    EXTRA = {
        "resolver denegado": lambda: bases.resolver(_pedido(ambiente=PRD, verbo="DROP"),
                                                    perfiles=perfiles_malos),
        "resolver sin ambiente": lambda: bases.resolver(_pedido(ambiente="prod"),
                                                        perfiles=perfiles_malos),
        "resolver sin clasificar": lambda: bases.resolver(_pedido(verbo="SHOW"),
                                                          perfiles=perfiles_malos),
        "resolver sin perfil": lambda: bases.resolver(_pedido(base="otra"),
                                                      perfiles=perfiles_malos),
    }

    # 🔴 Lo que no puede salir es el VALOR de un campo que lleva un secreto. Un perfil bien
    # escrito lleva ahi una referencia; si alguien escribio el valor, no viaja.
    # 🔴 Lo que se barre son VALORES, no nombres de clave. `passwd` suelto estaba en la lista
    # y lo hacia disparar el rechazo de `validar_perfil` —"`$.passwd`: el schema no declara
    # esta clave"—, que es exactamente lo que ese mensaje tiene que decir: nombrar la clave
    # prohibida es como alguien sabe que sacar. Un valor declarado sí va en la lista.
    PALABRAS = ("hunter2", "hunter2admin", "password=", "passwd=", "secret=",
                "BEGIN PRIVATE KEY", "Bearer ", "Basic ")
    todas = dict(LLAMADAS)
    todas.update(EXTRA)
    for nombre, llamar in sorted(todas.items()):
        texto = repr(llamar())
        for palabra in PALABRAS:
            t.verdadero("E-26 %s no lleva %r" % (nombre, palabra), palabra not in texto)

    # 📌 Y el residuo, clavado en verde: el validador compartido **imprime el dato** en el
    # mensaje de `enum`, asi que un valor puesto en `environment` —que NO es un campo de
    # secreto— vuelve en el texto del error. No es una fuga de credencial y es la unica salida
    # del modulo que devuelve un valor del documento. Queda dicho para que el dia que alguien
    # ponga un enum sobre un campo de secreto, este test obligue a hablarlo.
    eco = bases.validar_perfil(dict(_perfil(DEV), environment="valor-cualquiera"))
    t.contiene("E-26 el mensaje de enum del validador devuelve el dato", "valor-cualquiera",
               " ".join(eco))

    # Y el rechazo de una clave de mas la NOMBRA, que es deseable: es como alguien sabe que
    # sacar del archivo. Nombrar la clave no es publicar el valor.
    rechazo = " ".join(bases.validar_perfil(ENVENENADO))
    for clave in ("password", "username", "passwd", "secret"):
        t.contiene("E-26 el rechazo nombra la clave de mas `%s`" % clave, clave, rechazo)
    for valor in ("hunter2", "hunter2admin"):
        t.verdadero("E-26 y no publica su valor %r" % valor, valor not in rechazo)
    t.igual("E-26 y el unico enum del contrato de perfil es el ambiente", ["environment"],
            [c for c, r in sorted(
                (json.loads((SCHEMAS / "database-profile.schema.json").read_text(
                    encoding="utf-8"))["properties"]).items()) if "enum" in r])

    # Y las referencias son nombres, no valores: ninguna trae un `=`.
    for clave, ref in sorted(bases.referencias_de(_perfil(DEV)).items()):
        t.verdadero("E-26 %s es una referencia y no un valor" % clave,
                    "=" not in ref and " " not in ref)


def test_e27_el_resolvedor_no_habla_con_el_almacen(t):
    """E-27 (§6) — estructural: el modulo no tiene forma de conseguir una credencial."""
    fuente = (BIN / "orquestacion" / "bases.py").read_text(encoding="utf-8")
    arbol = ast.parse(fuente)

    # 🔴 Ninguna linea de import nombra el almacen ni el paquete donde vive.
    lineas = [n for n in ast.walk(arbol) if isinstance(n, (ast.Import, ast.ImportFrom))]
    texto_de_imports = " ".join(
        (getattr(n, "module", None) or "") + " " + " ".join(a.name for a in n.names)
        for n in lineas)
    for palabra in ("almacen", "integraciones", "AlmacenSecretos"):
        t.verdadero("E-27 ningun import nombra %s" % palabra,
                    palabra not in texto_de_imports)

    # Y `resolver` no menciona el nombre `almacen` en ninguna parte de su cuerpo.
    cuerpo_resolver = [n for n in arbol.body
                       if isinstance(n, ast.FunctionDef) and n.name == "resolver"]
    nombres = {n.id for n in ast.walk(cuerpo_resolver[0]) if isinstance(n, ast.Name)}
    nombres |= {n.arg for n in ast.walk(cuerpo_resolver[0]) if isinstance(n, ast.arg)}
    t.verdadero("E-27 resolver no nombra el almacen", "almacen" not in nombres)
    # 🔴 La funcion del borde RECIBE el almacen, no lo importa. Con eso "el resolvedor no puede
    # conseguir un secreto" es una propiedad de la forma del modulo y no una costumbre.
    borde = [n for n in arbol.body
             if isinstance(n, ast.FunctionDef) and n.name == "resolver_secreto"]
    t.igual("E-27 la funcion del borde existe", 1, len(borde))
    argumentos = [a.arg for a in borde[0].args.args]
    t.verdadero("E-27 y recibe el almacen como parametro", "almacen" in argumentos)

    # Sin almacen no adivina nada.
    t.igual("E-27 sin almacen no resuelve un secreto", bases.SIN_SECRETO,
            bases.resolver_secreto("DB_MAIN_DEV_PASSWORD", None)["state"])

    # Y la salida de `resolver` lleva referencias, nunca un valor resuelto.
    salida = bases.resolver(_pedido(), perfiles=_perfiles())
    t.verdadero("E-27 la salida no trae un campo de valor",
                not [k for k in repr(salida).split("'") if k.endswith("SecretValue")])


def test_e28_una_referencia_que_no_existe_se_resuelve_en_el_borde(t):
    """E-28 (§10) — DATABASE_SECRET_UNRESOLVED es del borde, no de la resolucion."""
    class Almacen(object):
        def __init__(self, tiene):
            self._tiene = tiene

        def exists(self, nombre):
            return nombre in self._tiene

        def get(self, nombre):
            return self._tiene.get(nombre)

    vacio = Almacen({})
    t.igual("E-28 una referencia que el almacen no tiene", bases.SIN_SECRETO,
            bases.resolver_secreto("DB_MAIN_DEV_PASSWORD", vacio)["state"])
    t.verdadero("E-28 y no devuelve ningun valor",
                "value" not in bases.resolver_secreto("DB_MAIN_DEV_PASSWORD", vacio))

    lleno = Almacen({"DB_MAIN_DEV_PASSWORD": "algo"})
    r = bases.resolver_secreto("DB_MAIN_DEV_PASSWORD", lleno)
    t.igual("E-28 una que si existe se resuelve", "RESOLVED", r["state"])
    t.igual("E-28 y la referencia viaja", "DB_MAIN_DEV_PASSWORD", r["reference"])

    # 🔴 Y la resolucion del ambiente NO cambia por eso: la decision ya estaba tomada.
    salida = bases.resolver(_pedido(), perfiles=_perfiles())
    t.igual("E-28 la decision no depende del almacen", True, _op(salida)["allowed"])
    t.verdadero("E-28 y no hay ningun estado de secreto en la resolucion",
                bases.SIN_SECRETO not in repr(salida))
    t.verdadero("E-28 el estado del secreto es del borde",
                bases.SIN_SECRETO in bases.ESTADOS_DEL_BORDE)


# -- E-29 a E-32 — la promocion y las fronteras --------------------------------

def test_e29_ninguna_migracion_se_aplica_en_promocion(t):
    """E-29 (§8) — por ningun camino, y la negacion nombra la via que si existe."""
    for ambiente in PROMOCION:
        for sentencia in (None, "ALTER TABLE t ADD c int", "SELECT 1",
                          "CREATE TABLE t (a int)", "DROP TABLE t"):
            for irreversible in (None, False, True):
                pedido = _pedido(ambiente=ambiente, verbo="MIGRATION", statement=sentencia)
                if irreversible is not None:
                    pedido["migration"] = {"irreversible": irreversible}
                op = _op(bases.resolver(pedido, perfiles=_perfiles()))
                t.igual("E-29 migracion en %s (%r, irrev=%s) se deniega"
                        % (ambiente, sentencia, irreversible), False, op["allowed"])
                t.verdadero("E-29 migracion en %s (%r, irrev=%s) con un estado de negacion"
                            % (ambiente, sentencia, irreversible),
                            op["denialReason"] in (bases.SIN_MIGRACION, bases.SIN_DDL))

    # 🔴 Y la via que si existe la nombra **LA DENEGACION**, no una constante del modulo.
    # La version anterior afirmaba `"artifact" in REMEDIO_DE_PROMOCION`, que prueba que la
    # constante dice la palabra — no que el resultado la lleve. La salida no la llevaba.
    for ambiente in PROMOCION:
        for verbo, estado in (("MIGRATION", bases.SIN_MIGRACION),
                              ("UPDATE", bases.SIN_ESCRITURA),
                              ("DROP", bases.SIN_DDL)):
            salida = _resolver(ambiente=ambiente, verbo=verbo)
            t.igual("E-29 %s en %s se deniega" % (verbo, ambiente), estado,
                    _op(salida)["denialReason"])
            t.verdadero("E-29 %s en %s: la denegacion trae el remedio" % (verbo, ambiente),
                        bool(salida["remediation"]))
            t.contiene("E-29 %s en %s: nombra el artefacto versionado" % (verbo, ambiente),
                       "artifact", salida["remediation"].lower())
            t.contiene("E-29 %s en %s: y el proceso de despliegue" % (verbo, ambiente),
                       "deployment", salida["remediation"].lower())
            t.contiene("E-29 %s en %s: el remedio viaja en el resultado" % (verbo, ambiente),
                       "artifact", repr(salida).lower())

    # Y donde no hay nada que remediar por esta via, no se inventa un remedio.
    t.igual("E-29 una migracion permitida en DEV no trae remedio", None,
            _resolver(ambiente=DEV, verbo="MIGRATION")["remediation"])
    t.igual("E-29 un verbo sin clasificar tampoco", None,
            _resolver(ambiente=PRD, verbo="SHOW")["remediation"])
    t.igual("E-29 ni un ambiente que no resuelve", None,
            _resolver(ambiente="prod", verbo="UPDATE")["remediation"])


def test_e30_el_flujo_dev_primero_esta_declarado_y_ordenado(t):
    """E-30 (§7) — el orden lo expone el modulo, no es una lista suelta en la doc."""
    flujo = bases.FLUJO_DEV_PRIMERO
    t.igual("E-30 son nueve pasos", 9, len(flujo))
    t.igual("E-30 sin repetidos", 9, len(set(flujo)))
    ESPERADO = ("resolve-dev-profile", "schema-discovery", "change-plan", "migration-artifact",
                "risk-classification", "apply-in-dev", "schema-validation", "tests",
                "promotion-artifact")
    t.igual("E-30 y en este orden", ESPERADO, flujo)
    # Los pares que importan.
    for antes, despues in (("resolve-dev-profile", "schema-discovery"),
                           ("schema-discovery", "change-plan"),
                           ("change-plan", "migration-artifact"),
                           ("migration-artifact", "risk-classification"),
                           ("risk-classification", "apply-in-dev"),
                           ("apply-in-dev", "schema-validation"),
                           ("schema-validation", "tests"),
                           ("tests", "promotion-artifact")):
        t.verdadero("E-30 %s precede a %s" % (antes, despues),
                    flujo.index(antes) < flujo.index(despues))

    # Y la doc lo cuenta.
    doc = (RAIZ / "docs" / "bases-de-datos.md").read_text(encoding="utf-8")
    for paso in flujo:
        t.contiene("E-30 la doc nombra %s" % paso, paso, doc)


def test_e31_no_se_crea_ningun_agente_ni_ninguna_skill(t):
    """E-31 (§9) — el pedido lo prohibe, y los siete que nombra ya existen."""
    agentes = sorted(p.stem for p in (RAIZ / "harnesses" / "desarrollo" / "agents"
                                      ).glob("*.md"))
    skills = sorted(p.name for p in (RAIZ / "harnesses" / "desarrollo" / "skills").iterdir()
                    if p.is_dir())
    t.igual("E-31 siguen siendo 11 agentes", 11, len(agentes))
    t.igual("E-31 y 27 skills", 27, len(skills))
    t.verdadero("E-31 ninguno nuevo de base de datos",
                not [x for x in agentes + skills if "database" in x or "bases" in x])

    # Los dos agentes y las cinco skills que el pedido nombra ya existen.
    for agente in ("dev-backend", "dev-devops"):
        t.verdadero("E-31 el agente %s ya existe" % agente, agente in agentes)
    for skill in ("dev-data", "dev-persistence", "dev-environments", "dev-deployment",
                  "dev-ci-cd"):
        t.verdadero("E-31 la skill %s ya existe" % skill, skill in skills)

    # Y esta capacidad no declara dueno: no hay un campo de propiedad en ninguno de sus archivos.
    #
    # 📌 Son los SEIS archivos del cambio, no solo el modulo. El escenario dice "ningun archivo
    # nuevo declara un dueno" y el barrido miraba uno: el sujeto del test era mas angosto que el
    # del escenario. Lo señalo la tercera refutacion.
    ARCHIVOS = (BIN / "orquestacion" / "bases.py",
                REGLAS / "database-environment-access-policy.json",
                REGLAS / "database-profiles.json",
                SCHEMAS / "database-environment-access-policy.schema.json",
                SCHEMAS / "database-profile.schema.json",
                RAIZ / "docs" / "bases-de-datos.md")
    t.igual("E-31 son seis archivos nuevos", 6, len(ARCHIVOS))
    for ruta in ARCHIVOS:
        t.verdadero("E-31 %s existe" % ruta.name, ruta.exists())
        fuente = ruta.read_text(encoding="utf-8")
        t.verdadero("E-31 %s no declara un dueno nuevo" % ruta.name,
                    "owner" not in fuente.lower().replace("ownership", ""))


def test_e32_la_politica_es_del_harness_y_no_entra_en_la_matriz(t):
    """E-32 (§1, §9) — ni en la matriz normativa ni en el registro de controles."""
    from orquestacion import controles as c_controles
    from orquestacion import matriz as c_matriz

    # No se toco la matriz ni el registro de controles.
    t.igual("E-32 siguen siendo 24 reglas", 24, len(c_matriz.reglas()))
    t.igual("E-32 y 52 controles", 52, c_controles.reporte()["summary"]["declaredControls"])
    t.igual("E-32 sin archivos de control sin declarar", [],
            c_controles.reporte()["undeclared"])

    # Y nada de esto aparece ahi.
    for texto in (repr(c_matriz.reglas()), repr(c_controles.cargar())):
        # 📌 No se barre la palabra "database": la fila de P7 la usa en prosa legitima
        # -"Business logic must not reside in the database layer"-. El sujeto son los
        # identificadores de ESTA capacidad.
        for palabra in ("bases.py", "DATABASE_", "database-environment-access-policy",
                        "database-profiles", "database-profile.schema"):
            t.verdadero("E-32 %r no aparece en la normativa" % palabra, palabra not in texto)

    # 🔴 La politica y los perfiles son DOS archivos, y el del proyecto no se lee como
    # politica. La version anterior afirmaba "un proyecto no puede volver FULL a PRD" y lo
    # demostraba pasando la politica falsa por `perfiles=`, que nunca se lee como politica:
    # probaba la proposicion vecina. Lo que se afirma es lo que de verdad protege.
    t.verdadero("E-32 la politica y los perfiles son archivos distintos",
                bases.POLITICA != bases.PERFILES)
    perfiles_con_politica = {"version": "1.0", "profiles": {},
                             "environments": {PRD: {"mode": "FULL", "read": True,
                                                    "write": True, "ddl": True,
                                                    "migrations": True}}}
    op = _op(bases.resolver(_pedido(ambiente=PRD, verbo="UPDATE"),
                            perfiles=perfiles_con_politica))
    t.igual("E-32 un `environments` en el archivo de perfiles no es una politica", False,
            op["allowed"])
    t.igual("E-32 y se deniega por escritura", bases.SIN_ESCRITURA, op["denialReason"])

    # 🔴 Lo que protege es que el ARCHIVO es del harness y que `resolver` lo lee por defecto.
    # `politica=` es una costura de test —y una inyeccion en proceso, que no es una frontera
    # de confianza: quien puede llamar a `resolver(politica=...)` ya esta adentro del harness—.
    # Lo que se afirma es que sin ese parametro manda el archivo instalado.
    instalada = bases.cargar_politica()
    t.igual("E-32 sin argumento, `resolver` usa la politica instalada",
            instalada["environments"][PRD], bases.acceso_de(PRD))
    t.igual("E-32 y PRD viene READ_ONLY de ahi", "READ_ONLY",
            instalada["environments"][PRD]["mode"])
    for verbo, estado in (("UPDATE", bases.SIN_ESCRITURA), ("DROP", bases.SIN_DDL),
                          ("MIGRATION", bases.SIN_MIGRACION)):
        t.igual("E-32 %s en PRD se deniega con la politica instalada" % verbo, estado,
                _op(_resolver(ambiente=PRD, verbo=verbo))["denialReason"])

    # Y una politica inyectada con la forma equivocada se rechaza, no se usa a medias.
    MALAS = ({}, {"environments": {}}, {"environments": "x"},
             {"environments": {PRD: {"mode": "SUPERUSER", "read": True, "write": True,
                                     "ddl": True, "migrations": True}}},
             {"environments": {PRD: {"mode": "FULL", "read": False, "write": True,
                                     "ddl": True, "migrations": True}}},
             {"environments": {PRD: {"mode": "FULL", "read": True, "write": "si",
                                     "ddl": True, "migrations": True}}})
    for mala in MALAS:
        t.igual("E-32 una politica mal formada no resuelve un ambiente", None,
                bases.acceso_de(PRD, politica=mala))
        t.igual("E-32 y el pedido se deniega", bases.SIN_AMBIENTE,
                _op(bases.resolver(_pedido(ambiente=PRD, verbo="UPDATE"), politica=mala,
                                   perfiles=_perfiles()))["denialReason"])

    # Ni `permisos-por-capacidad.json` gano una capacidad de base de datos: es un hueco correcto.
    permisos = json.loads((REGLAS / "permisos-por-capacidad.json").read_text(encoding="utf-8"))
    t.verdadero("E-32 no hay capacidad de base de datos declarada",
                not [c for c in permisos["capacidades"] if c.startswith("database")])


# -- E-33 a E-35 — los estados y el fail-closed --------------------------------

def test_e33_los_diez_estados_existen_y_ninguno_permite(t):
    """E-33 (§10)."""
    ESPERADOS = ("DATABASE_ENVIRONMENT_UNRESOLVED", "DATABASE_PROFILE_NOT_FOUND",
                 "DATABASE_SECRET_UNRESOLVED", "DATABASE_OPERATION_UNCLASSIFIED",
                 "DATABASE_WRITE_NOT_ALLOWED", "DATABASE_DDL_NOT_ALLOWED",
                 "DATABASE_MIGRATION_NOT_ALLOWED", "DATABASE_CONNECTION_FAILED",
                 "DATABASE_PERMISSION_DENIED", "DATABASE_SCHEMA_DISCOVERY_FAILED")
    t.igual("E-33 son diez", 10, len(bases.ESTADOS_DE_FALLA))
    t.igual("E-33 sin repetidos", 10, len(set(bases.ESTADOS_DE_FALLA)))
    t.igual("E-33 y son exactamente los del contrato", sorted(ESPERADOS),
            sorted(bases.ESTADOS_DE_FALLA))

    # Cuatro son del borde de ejecucion: el resolvedor no los produce.
    t.igual("E-33 cuatro son del borde", 4, len(bases.ESTADOS_DEL_BORDE))
    for estado in bases.ESTADOS_DEL_BORDE:
        t.verdadero("E-33 %s es un estado de falla" % estado,
                    estado in bases.ESTADOS_DE_FALLA)
    t.igual("E-33 y el resolvedor produce los otros seis", 6,
            len(bases.ESTADOS_DEL_RESOLVEDOR))
    t.vacio("E-33 los dos conjuntos no se solapan",
            sorted(set(bases.ESTADOS_DEL_BORDE) & set(bases.ESTADOS_DEL_RESOLVEDOR)))

    # 🔴 Y la tercera clausula del escenario, que vivia en E-23, E-34 y E-35 y no acá: **ninguno
    # de los diez viene con `allowed: true`**. Se recorren los seis que el resolvedor produce,
    # forzando cada uno con el pedido que lo provoca; los cuatro del borde no los produce nadie
    # y por eso no tienen caso. Lo señaló la tercera refutación.
    PROVOCAN = (
        ("DATABASE_ENVIRONMENT_UNRESOLVED", _pedido(ambiente="ninguno")),
        ("DATABASE_PROFILE_NOT_FOUND", _pedido(base="una-que-no-existe")),
        ("DATABASE_OPERATION_UNCLASSIFIED", _pedido(statement="SHOW TABLES")),
        ("DATABASE_WRITE_NOT_ALLOWED", _pedido(ambiente=PRD, verbo="UPDATE")),
        ("DATABASE_DDL_NOT_ALLOWED", _pedido(ambiente=PRD, verbo="CREATE")),
        ("DATABASE_MIGRATION_NOT_ALLOWED", _pedido(ambiente=PRD, verbo="MIGRATION")),
    )
    vistos = []
    for estado, pedido in PROVOCAN:
        op = _op(bases.resolver(pedido, perfiles=_perfiles()))
        t.igual("E-33 %s se produce" % estado, estado, op["denialReason"])
        t.igual("E-33 %s no viene con allowed true" % estado, False, op["allowed"])
        vistos.append(estado)
    t.igual("E-33 se provocaron los seis del resolvedor",
            sorted(bases.ESTADOS_DEL_RESOLVEDOR), sorted(vistos))


def test_e34_todo_dato_faltante_falla_cerrado(t):
    """E-34 (§10) — EL PRODUCTO de las formas de dato faltante.

    🔴 "Missing data must fail closed." Ninguna combinacion de campo ausente, vacio, en blancos
    o del tipo equivocado puede producir `allowed: true`.
    """
    CAMPOS = ("taskId", "projectId", "environment", "logicalDatabase", "declaredVerb")
    FORMAS = (("ausente", "__SIN_CLAVE__"), ("None", None), ("vacio", ""),
              ("un espacio", " "), ("blancos", " \t\n "), ("un numero", 7),
              ("un booleano", False), ("una lista", []), ("un diccionario", {}),
              ("una lista con algo", ["x"]))

    # Uno por uno.
    for campo in CAMPOS:
        for nombre, valor in FORMAS:
            pedido = _pedido()
            if valor == "__SIN_CLAVE__":
                pedido.pop(campo)
            else:
                pedido[campo] = valor
            salida = bases.resolver(pedido, perfiles=_perfiles())
            op = _op(salida)
            t.igual("E-34 %s %s no permite" % (campo, nombre), False, op["allowed"])
            t.verdadero("E-34 %s %s deniega con un estado del contrato" % (campo, nombre),
                        op["denialReason"] in bases.ESTADOS_DE_FALLA)

    # Y de a pares, que es donde una guarda puede tapar a otra.
    for a in CAMPOS:
        for b in CAMPOS:
            if a >= b:
                continue
            pedido = _pedido()
            pedido.pop(a)
            pedido[b] = "  "
            op = _op(bases.resolver(pedido, perfiles=_perfiles()))
            t.igual("E-34 sin %s y con %s en blancos no permite" % (a, b), False,
                    op["allowed"])

    # El pedido entero ausente, vacio o del tipo equivocado.
    for nombre, pedido in (("None", None), ("vacio", {}), ("una lista", []),
                           ("un texto", "SELECT"), ("un numero", 1)):
        op = _op(bases.resolver(pedido, perfiles=_perfiles()))
        t.igual("E-34 un pedido %s no permite" % nombre, False, op["allowed"])
        t.verdadero("E-34 un pedido %s deniega con un estado" % nombre,
                    op["denialReason"] in bases.ESTADOS_DE_FALLA)

    # Y los perfiles malformados: tampoco permiten, y no rompen el modulo.
    for nombre, perfiles in (("None", None), ("vacio", {}), ("sin profiles", {"version": "1"}),
                             ("profiles como lista", {"profiles": []}),
                             ("profiles como texto", {"profiles": "x"}),
                             ("un perfil como texto",
                              {"profiles": {"main-database/DEV": "x"}}),
                             ("una lista", []), ("un texto", "x")):
        op = _op(bases.resolver(_pedido(), perfiles=perfiles))
        t.igual("E-34 perfiles %s no permite" % nombre, False, op["allowed"])
        t.igual("E-34 perfiles %s dice que falta el perfil" % nombre, bases.SIN_PERFIL,
                op["denialReason"])


def test_e35_todo_resultado_conserva_su_contrato(t):
    """E-35 — los dos campos de la clasificacion, siempre, y `allowed` coherente con el modo."""
    CASOS = (
        ("permitido", _pedido(ambiente=DEV, verbo="SELECT")),
        ("denegado por escritura", _pedido(ambiente=PRD, verbo="UPDATE")),
        ("denegado por ddl", _pedido(ambiente=QA, verbo="DROP")),
        ("denegado por migracion", _pedido(ambiente=HML, verbo="MIGRATION")),
        ("sin clasificar", _pedido(verbo="SHOW")),
        ("sin ambiente", _pedido(ambiente="prod")),
        ("sin perfil", _pedido(base="inexistente")),
    )
    for nombre, pedido in CASOS:
        salida = bases.resolver(pedido, perfiles=_perfiles())
        op = _op(salida)
        # 📌 `remediation` entro cuando se arreglo E-29: la denegacion tiene que NOMBRAR la
        # via que si existe, y una constante del modulo no es la denegacion. Va siempre como
        # clave —`None` cuando no hay nada que remediar por esta via— para que el contrato de
        # la salida no dependa del camino.
        t.igual("E-35 %s: la salida declara sus seis bloques" % nombre,
                ["connectionProfile", "environment", "logicalDatabase", "operation",
                 "remediation", "risk"], sorted(salida))
        t.igual("E-35 %s: la operacion declara sus cinco campos" % nombre,
                ["allowed", "declaredVerb", "denialReason", "effectiveSideEffects",
                 "operationClass"], sorted(op))
        t.igual("E-35 %s: el riesgo declara sus dos campos" % nombre,
                ["approvalRequired", "level"], sorted(salida["risk"]))
        t.verdadero("E-35 %s: allowed es booleano" % nombre, isinstance(op["allowed"], bool))
        if op["allowed"]:
            t.igual("E-35 %s: permitido no lleva motivo" % nombre, None, op["denialReason"])
            t.verdadero("E-35 %s: y su efecto lo habilita el modo" % nombre,
                        bases.acceso_de(salida["environment"])[
                            bases.PERMISO_DE_CLASE[op["operationClass"]]] is True)
        else:
            t.verdadero("E-35 %s: denegado lleva un motivo del contrato" % nombre,
                        op["denialReason"] in bases.ESTADOS_DE_FALLA)

    # 🔴 Y ningun estado de falla sale con `allowed: true`, por ningun camino de los de arriba.
    t.verdadero("E-35 ningun estado de falla viene permitido",
                not [n for n, p in CASOS
                     if _op(bases.resolver(p, perfiles=_perfiles()))["allowed"]
                     and _op(bases.resolver(p, perfiles=_perfiles()))["denialReason"]])


# -- E-36 — el contrato de los schemas -----------------------------------------

def test_e36_el_validador_lee_los_schemas_del_pedido(t):
    """E-36 — `$defs`, `$ref` local y `additionalProperties: false`, y lo que no se soporta."""
    politica = json.loads(
        (SCHEMAS / "database-environment-access-policy.schema.json").read_text(
            encoding="utf-8"))
    perfil = json.loads(
        (SCHEMAS / "database-profile.schema.json").read_text(encoding="utf-8"))

    # Los dos se leen tal como vinieron, sin adaptarlos.
    for nombre, esquema in (("la politica", politica), ("el perfil", perfil)):
        ARMADOR.controlar_soporte(esquema)
        t.verdadero("E-36 %s usa additionalProperties" % nombre,
                    "additionalProperties" in repr(esquema))
    t.verdadero("E-36 la politica usa $defs y $ref", "$defs" in politica
                and "$ref" in repr(politica))

    # Y validan lo que tienen que validar.
    doc = json.loads((REGLAS / "database-environment-access-policy.json").read_text(
        encoding="utf-8"))
    t.vacio("E-36 la politica instalada cumple su schema",
            ARMADOR.validar(doc, politica))

    # 🔴 Un ambiente que la politica no declara se RECHAZA. Es la mitad de la seguridad de esto.
    de_mas = json.loads(json.dumps(doc))
    de_mas["environments"]["PROD"] = dict(de_mas["environments"][PRD])
    t.verdadero("E-36 un ambiente de mas se rechaza",
                bool(ARMADOR.validar(de_mas, politica)))
    # Y un campo de mas adentro de un ambiente, tambien: el `$ref` se resolvio de verdad.
    adentro = json.loads(json.dumps(doc))
    adentro["environments"][DEV]["bypass"] = True
    errores = ARMADOR.validar(adentro, politica)
    t.verdadero("E-36 un campo de mas adentro de un ambiente se rechaza", bool(errores))
    t.contiene("E-36 y el error nombra la ruta resuelta", "environments.DEV.bypass",
               " ".join(errores))
    # Un modo que no existe, tambien.
    t.verdadero("E-36 un modo inventado se rechaza", bool(ARMADOR.validar(
        {"version": "1", "environments": dict(
            doc["environments"], DEV=dict(doc["environments"][DEV], mode="SUPERUSER")),
         "default": doc["default"]}, politica)))

    # El perfil: sin valores de credencial, y con el ambiente exacto.
    bueno = _perfil(DEV)
    t.vacio("E-36 un perfil bien formado valida", ARMADOR.validar(bueno, perfil))
    t.verdadero("E-36 un perfil con una contrasena en claro se rechaza",
                bool(ARMADOR.validar(dict(bueno, password="hunter2"), perfil)))
    t.verdadero("E-36 y uno con el ambiente en minuscula",
                bool(ARMADOR.validar(dict(bueno, environment="dev"), perfil)))
    for campo in ("logicalDatabase", "environment", "engine", "hostRef", "portRef",
                  "databaseRef", "usernameSecretRef", "passwordSecretRef"):
        sin = dict(bueno)
        sin.pop(campo)
        t.verdadero("E-36 un perfil sin %s se rechaza" % campo,
                    bool(ARMADOR.validar(sin, perfil)))

    # 🔴 Y lo que el validador NO soporta lo dice, en vez de saltearlo.
    NO_SOPORTADO = (
        ("un $ref a otro archivo", {"$ref": "otro.json#/$defs/x"}),
        ("un $ref a una URL", {"$ref": "https://ejemplo/x"}),
        ("un $ref que no existe", {"$ref": "#/$defs/inexistente"}),
        ("un $ref con otras reglas", {"$ref": "#/$defs/a", "type": "string",
                                      "$defs": {"a": {"type": "string"}}}),
        ("additionalProperties true", {"type": "object", "properties": {},
                                       "additionalProperties": True}),
        ("additionalProperties sin properties", {"type": "object",
                                                 "additionalProperties": False}),
        ("un mapa con un tipo mal escrito adentro",
         {"type": "object", "additionalProperties": {"type": "strng"}}),
        ("una palabra que no interpreta", {"type": "object", "oneOf": []}),
    )
    for nombre, esquema in NO_SOPORTADO:
        if "$defs" not in esquema and "$ref" in esquema:
            esquema = dict(esquema, **{"$defs": {"a": {"type": "string"}}}) \
                if esquema["$ref"] == "#/$defs/a" else esquema
        try:
            ARMADOR.controlar_soporte(esquema)
            t.verdadero("E-36 %s se rechaza" % nombre, False)
        except ARMADOR.SchemaNoSoportado:
            t.verdadero("E-36 %s se rechaza" % nombre, True)

    # 🔴 `additionalProperties` con un SCHEMA si se interpreta: es como se declara un mapa de
    # clave libre a objeto con forma, y lo pidio el estado de las fuentes. Se amplio el
    # validador en vez de aflojar el contrato, que es la mitad que este escenario cuida: lo que
    # entra a interpretarse VALIDA de verdad, y lo que no se interpreta se sigue rechazando.
    mapa = {"type": "object", "additionalProperties": {"type": "object", "required": ["a"],
                                                       "properties": {"a": {"type": "string"}}}}
    ARMADOR.controlar_soporte(mapa)
    t.vacio("E-36 un mapa valido pasa", ARMADOR.validar({"x": {"a": "1"}}, mapa))
    t.verdadero("E-36 y uno con el valor de otro tipo no",
                bool(ARMADOR.validar({"x": {"a": 1}}, mapa)))
    t.verdadero("E-36 ni uno al que le falta lo obligatorio",
                bool(ARMADOR.validar({"x": {}}, mapa)))

    # 📌 La guarda del `$ref` no local y la de "ese `$defs` no existe" rechazan las dos, asi
    # que sacar la primera no cambia el veredicto — cambia el MENSAJE, y un rechazo que no dice
    # por que es un rechazo que alguien no sabe como arreglar. Se afirma el mensaje.
    for nombre, ref in (("otro archivo", "otro.json#/$defs/x"),
                        ("una URL", "https://ejemplo/x"),
                        ("un puntero raro", "#/definitions/x")):
        try:
            ARMADOR.controlar_soporte({"$ref": ref})
            t.verdadero("E-36 un $ref a %s se rechaza" % nombre, False)
        except ARMADOR.SchemaNoSoportado as e:
            t.contiene("E-36 el rechazo de %s dice que solo resuelve lo local" % nombre,
                       "referencias locales", str(e))

    # Un `$defs` con un tipo mal escrito se descubre aunque nadie lo referencie.
    try:
        ARMADOR.controlar_soporte({"type": "object", "properties": {},
                                   "$defs": {"suelto": {"type": "strng"}}})
        t.verdadero("E-36 un $defs sin usar con un tipo mal escrito se descubre", False)
    except ARMADOR.SchemaNoSoportado:
        t.verdadero("E-36 un $defs sin usar con un tipo mal escrito se descubre", True)

    # 🔴 Una CADENA de `$ref` locales se resuelve hasta el final. La primera version resolvia
    # un solo salto: `controlar_soporte` seguia la cadena y decia "soportado", y `validar` se
    # quedaba con un diccionario cuya unica clave era `$ref` —sin `type`, sin `properties`, sin
    # `required`— y devolvia `[]` sobre CUALQUIER dato. El sello de "soportado" era lo que
    # volvia peligrosa a esa rama.
    cadena = {"type": "object", "properties": {"a": {"$ref": "#/$defs/uno"}},
              "$defs": {"uno": {"$ref": "#/$defs/dos"},
                        "dos": {"type": "object",
                                "properties": {"x": {"type": "string"}},
                                "required": ["x"], "additionalProperties": False}}}
    ARMADOR.controlar_soporte(cadena)
    t.vacio("E-36 una cadena de $ref valida un dato correcto",
            ARMADOR.validar({"a": {"x": "ok"}}, cadena))
    for dato, que in (({"a": {"basura": 1}}, "una clave de mas y una que falta"),
                      ({"a": "no es objeto"}, "un tipo equivocado"),
                      ({"a": {"x": 7}}, "un tipo equivocado adentro"),
                      ({"a": {}}, "un obligatorio que falta")):
        t.verdadero("E-36 una cadena de $ref rechaza %s" % que,
                    bool(ARMADOR.validar(dato, cadena)))
    # Y da lo mismo que apuntar directo al final de la cadena.
    directo = {"type": "object",
               "properties": {"a": cadena["$defs"]["dos"]}}
    t.igual("E-36 la cadena valida igual que el $defs directo",
            ARMADOR.validar({"a": {"basura": 1}}, directo),
            ARMADOR.validar({"a": {"basura": 1}}, cadena))

    # Un ciclo se rechaza: devolverlo resuelto a medias es lo mismo de antes.
    for nombre, ciclo in (
            ("de dos pasos",
             {"type": "object", "properties": {"a": {"$ref": "#/$defs/uno"}},
              "$defs": {"uno": {"$ref": "#/$defs/dos"}, "dos": {"$ref": "#/$defs/uno"}}}),
            ("sobre si mismo",
             {"type": "object", "properties": {"a": {"$ref": "#/$defs/uno"}},
              "$defs": {"uno": {"$ref": "#/$defs/uno"}}})):
        try:
            ARMADOR.controlar_soporte(ciclo)
            t.verdadero("E-36 un ciclo %s se rechaza" % nombre, False)
        except ARMADOR.SchemaNoSoportado as e:
            t.contiene("E-36 un ciclo %s se rechaza por ciclo" % nombre, "ciclo", str(e))

    # 🔴 Y la ampliacion es ADITIVA, medido y no afirmado: TODOS los schemas del repositorio se
    # soportan y validan **su documento instalado** exactamente igual que antes.
    #
    # 🔴 **La lista exacta, no el conteo.** Esto fijaba `len(esquemas) == 18` y era una asercion
    # sobre el REPOSITORIO y no sobre este cambio: cualquier otra rama que sume un contrato la
    # pone en rojo sin que nada de acá se haya movido, y quien la actualiza no es quien escribió
    # el schema nuevo. Lo que este cambio tiene que sostener son dos cosas, y las dos se afirman:
    #
    #   1. los DIECIOCHO que existian cuando se construyo siguen estando, nombrados uno por uno
    #      -asi un contrato que desaparece se ve, que es lo que el conteo protegia-;
    #   2. **todos** los del repositorio se soportan, los dieciocho y los que vengan, que es el
    #      invariante de aditividad y no depende de cuantos haya.
    LOS_DIECIOCHO = (
        "agent-registry", "annex-ii-technology-catalog", "budget-policy", "control-registry",
        "database-environment-access-policy", "database-profile",
        "es0901-7.1-normative-matrix", "es0902-cross-standard-map",
        "es0902-normative-matrix", "es0902-security-deliverables",
        "execution-accounting-event", "normative-review", "normative-signal",
        "orchestration-plan", "project-context", "task-context", "tool-contract",
        "tool-registry")
    esquemas = sorted(p.name for p in SCHEMAS.glob("*.schema.json"))
    t.igual("E-36 son dieciocho los que este cambio conocio", 18, len(LOS_DIECIOCHO))
    for nombre in LOS_DIECIOCHO:
        t.verdadero("E-36 sigue estando %s" % nombre,
                    ("%s.schema.json" % nombre) in esquemas)
    for nombre in esquemas:
        esquema = json.loads((SCHEMAS / nombre).read_text(encoding="utf-8"))
        ARMADOR.controlar_soporte(esquema)
    # Los dos documentos de este cambio, y los tres registros que ya estaban.
    INSTALADOS = (
        ("database-environment-access-policy", REGLAS / "database-environment-access-policy.json"),
        ("database-profile", None),
        ("control-registry", REGLAS / "control-registry.json"),
        ("agent-registry", REGLAS / "agent-registry.json"),
        ("es0901-7.1-normative-matrix", REGLAS / "es0901-7.1-normative-matrix.json"),
    )
    for nombre, ruta in INSTALADOS:
        if ruta is None:
            continue
        esquema = json.loads((SCHEMAS / ("%s.schema.json" % nombre)).read_text(
            encoding="utf-8"))
        t.vacio("E-36 %s sigue validando su documento instalado" % nombre,
                ARMADOR.validar(json.loads(ruta.read_text(encoding="utf-8")), esquema))


# -- E-37 — la compuerta arranca en un arbol instalado -------------------------

def test_e37_la_compuerta_arranca_en_un_arbol_instalado(t):
    """E-37 — `reglas/` cuelga a distinta altura instalado, y por eso existe `roster`.

    🔴 Este escenario lo trajo la refutacion, y es lo que decide si la capacidad EXISTE en un
    proyecto. `bases._ruta_de_regla` usaba `rutas.localizar(("reglas", nombre))` sin raices
    extra, igual que si el arbol de la fabrica fuera el unico: instalado, `reglas/` cuelga de
    `.claude/harness/reglas/<id>/`, la politica no se encontraba y **la compuerta entera
    levantaba `BasesInvalida`**. Verde donde corre la suite, muerta donde corre el harness.

    Es textualmente lo que el docstring de `roster` avisa: *dos busquedas de rutas con
    criterios parecidos terminan en que un dia una encuentra el archivo y la otra no.*
    """
    import shutil
    import tempfile
    from orquestacion import roster as c_roster

    # 1. Estructural: sale de `roster`, como todo el resto de `orquestacion/` que lee reglas.
    fuente = (BIN / "orquestacion" / "bases.py").read_text(encoding="utf-8")
    t.contiene("E-37 la ruta de una regla sale de roster", "roster.ruta_de_regla", fuente)
    t.verdadero("E-37 y no de una localizacion sin raices extra",
                'rutas.localizar(("reglas"' not in fuente)

    # 2. Y de verdad: se arma la forma que deja el instalador y se resuelve desde ahi.
    tmp = tempfile.mkdtemp(prefix="bases-inst")
    try:
        binario = Path(tmp) / ".claude" / "harness" / "bin" / "desarrollo" / "orquestacion"
        reglas_h = Path(tmp) / ".claude" / "harness" / "reglas"
        reglas_d = reglas_h / "desarrollo"
        esquemas = Path(tmp) / ".claude" / "harness" / "schemas"
        for d in (binario, reglas_d, esquemas):
            d.mkdir(parents=True)
        # El marcador por el que `rutas.raiz_del_harness` reconoce la raiz.
        (reglas_h / "secretos.patrones.json").write_text("{}", encoding="utf-8")
        for nombre in ("database-environment-access-policy.json", "database-profiles.json"):
            shutil.copy(str(REGLAS / nombre), str(reglas_d / nombre))
        for esquema in SCHEMAS.glob("*.schema.json"):
            shutil.copy(str(esquema), str(esquemas / esquema.name))
        desde = binario / "bases.py"
        desde.write_text("# marcador\n", encoding="utf-8")

        # La busqueda vieja NO lo encuentra; la de roster SI. Es el defecto, en una linea.
        t.igual("E-37 una localizacion sin raices extra no lo encuentra", None,
                rutas_mod.localizar(
                    ("reglas", "database-environment-access-policy.json"), str(desde)))
        t.verdadero("E-37 y roster si",
                    bool(c_roster.ruta_de_regla(
                        "database-environment-access-policy.json", str(desde))))

        # Y con eso la compuerta arranca: politica, perfiles, acceso y una resolucion.
        doc = bases.cargar_politica(desde=str(desde))
        t.igual("E-37 la politica se lee del arbol instalado", [DEV, HML, PRD, QA],
                sorted(doc["environments"]))
        t.vacio("E-37 y cumple su schema", bases.validar_politica(doc, desde=str(desde)))
        t.igual("E-37 los perfiles tambien, y siguen vacios", {},
                bases.cargar_perfiles(desde=str(desde))["profiles"])
        t.igual("E-37 DEV resuelve FULL instalado", "FULL",
                bases.acceso_de(DEV, desde=str(desde))["mode"])
        for ambiente in PROMOCION:
            t.igual("E-37 %s resuelve READ_ONLY instalado" % ambiente, "READ_ONLY",
                    bases.acceso_de(ambiente, desde=str(desde))["mode"])

        # Y un pedido entero no levanta: deniega por falta de perfil, que es lo correcto.
        salida = bases.resolver(_pedido(), desde=str(desde))
        t.igual("E-37 un pedido resuelve sin levantar", bases.SIN_PERFIL,
                _op(salida)["denialReason"])
        t.igual("E-37 y un DROP en PRD se deniega instalado", bases.SIN_DDL,
                _op(bases.resolver(_pedido(ambiente=PRD, verbo="DROP"),
                                   desde=str(desde)))["denialReason"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
