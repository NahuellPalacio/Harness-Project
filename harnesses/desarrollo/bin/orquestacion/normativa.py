"""Las reglas de ES0901 §7.1 como dato, y cuales aplican a un plan.

Dos archivos, y cada uno contesta una pregunta distinta:

    es0901-7.1.json                   el TEXTO citado y la pagina. La fuente
    es0901-7.1-normative-matrix.json  la clasificacion. La resuelve `matriz.py`

`aplicables` y `aviso_de_matriz` siguen contestando lo mismo que antes -son lo que el plan
ya consume en `applicableStandards`- y al lado esta `resolucion`, que devuelve el bloque
normativo completo. Cambiarle el tipo a un campo que alguien ya lee es romper a distancia.

🔴 Una regla sin `conditions` declaradas NUNCA se cita como aplicable. Las 26 reglas entran
con su id, su texto y su pagina, y la clasificacion -owners, skills, policies, checks- entra
vacia: clasificarlas es trabajo de criterio que alguien tiene que validar contra el
estandar, y una matriz inventada se lee igual de autoritativa que una real.

La consecuencia se acepta y se declara: hoy el plan cita pocas reglas, y dice cuantas quedan
sin clasificar para que el hueco se vea en cada corrida.
"""
import io
import json

from . import roster

_CACHE = {}


def cargar(desde=None):
    """El catalogo normativo. Vacio si no se encontro."""
    if "normativa" in _CACHE:
        return _CACHE["normativa"]
    ruta = roster.ruta_de_regla("es0901-7.1.json", desde or __file__)
    datos = {"rules": []}
    if ruta:
        try:
            with io.open(ruta, encoding="utf-8-sig") as f:
                datos = json.load(f)
        except (ValueError, OSError):
            datos = {"rules": []}
    _CACHE["normativa"] = datos
    return datos


def reglas(desde=None):
    return cargar(desde).get("rules", [])


def sin_clasificar(desde=None):
    """Las que todavia no tienen condiciones: no se pueden citar."""
    return [r for r in reglas(desde) if not r.get("conditions")]


def aplicables(dominios, desde=None):
    """Los ids de las reglas cuyas condiciones coinciden con el plan.

    Hoy la unica condicion soportada es `domains`. Se sostiene a proposito: agregar un
    lenguaje de condiciones antes de tener una sola regla clasificada seria disenar para un
    caso que nadie vio.
    """
    salida = []
    for regla in reglas(desde):
        condiciones = regla.get("conditions") or {}
        if not condiciones:
            continue
        exigidos = condiciones.get("domains")
        if exigidos and not (set(exigidos) & set(dominios)):
            continue
        salida.append(regla["id"])
    return sorted(salida)


def aviso_de_matriz(desde=None):
    """Lo que el plan tiene que decir sobre la matriz pendiente, o "" si esta completa."""
    faltan = sin_clasificar(desde)
    todas = reglas(desde)
    if not faltan:
        return ""
    return ("%d de las %d reglas de ES0901 §7.1 estan sin clasificar y por eso no se citan: "
            "la matriz normativa todavia no se construyo." % (len(faltan), len(todas)))


# -- la clasificacion, que vive en la matriz -----------------------------------

def resolucion(senales, desde=None, evidencia=None):
    """El bloque normativo de una unidad: que aplica, que no, y que no se sabe.

    Las senales entran de dos formas y las dos siguen andando: booleanos explicitos -la forma
    vieja- o documentos de senal con su evidencia y su productor. Lo que no esta no se deduce:
    la regla queda `APPLICABILITY_UNRESOLVED` con la senal que le falta escrita al lado. La
    evidencia todavia la junta nadie, asi que una unidad real sale casi toda sin resolver — y
    eso es lo que hay, no un defecto que convenga disimular convirtiendo lo ausente en "no
    aplica".

    Lo resuelto viaja al lado, en `signals`: quien lee la unidad ve el valor, su estado y de
    donde salio, sin tener que confiar en un booleano que nadie firmo.

    `evidencia` trae resultados ya corridos, por clave compuesta. Hoy la leen
    `ES0902.C2`, `ES0902.C3`, `ES0902.Vu3`, `ES0902.Vu4`, `ES0902.Vu5`, `ES0902.Vu6`, `ES0902.Vu7` y `ES0902.Vu8`, que ponen su bloque en `standards.ES0902.rules` con referencias y
    no con contenido. Sin resultado el bloque queda sin resolver.
    """
    from . import matriz
    from . import senales as modulo_senales
    try:
        booleanos, resueltas = modulo_senales.normalizar(senales, desde)
    except modulo_senales.SenalInvalida:
        # Sin contrato de senal no se interpreta ninguna: quedan todas sin resolver.
        booleanos, resueltas = {}, {}
    try:
        bloque = matriz.resolver(booleanos, None, desde)
    except matriz.MatrizInvalida:
        # Fallo cerrado: sin matriz no se clasifica nada, y se dice.
        bloque = {"standard": {}, "applicableRules": [], "notApplicableRules": [],
                  "unresolvedRules": [], "declaredPolicies": [], "declaredChecks": [],
                  "evidence": {"signals": {}}}
    bloque["signals"] = resueltas
    bloque["standards"] = {bloque.get("standard", {}).get("id") or "ES0901": _sin_senales(bloque)}

    # 🔴 ES0902 se suma AL LADO, nunca encima. Todo lo de arriba sigue siendo lo de ES0901 y
    # conserva su tipo: quien ya lee `applicableRules` no se entera de que hay un segundo
    # estandar. Cambiarle el tipo a un campo que alguien ya lee es romper a distancia, y es la
    # regla que este modulo declara desde que existe.
    from . import seguridad
    try:
        bloque["standards"][seguridad.ESTANDAR] = seguridad.resolver(booleanos, None, desde)
        # `rules` se suma al bloque de ES0902 y no a `seguridad.resolver`, cuya forma es la misma
        # que la de ES0901 a proposito.
        from . import evaluacion
        aplic, _ = seguridad.resolver_regla(seguridad.regla("C2", None, desde), booleanos)
        bloque["standards"][seguridad.ESTANDAR]["rules"] = {
            "C2": evaluacion.c2_para_unidad(
                aplic, (evidencia if isinstance(evidencia, dict) else {}).get("ES0902.C2"))}
        from . import estandar_de_desarrollo
        bloque["standards"][seguridad.ESTANDAR]["rules"]["C3"] = estandar_de_desarrollo.c3_para_unidad(
            (evidencia if isinstance(evidencia, dict) else {}).get("ES0902.C3"), desde)
        aplic_vu3, _ = seguridad.resolver_regla(seguridad.regla("Vu3", None, desde), booleanos)
        bloque["standards"][seguridad.ESTANDAR]["rules"]["Vu3"] = vu3_para_unidad(
            aplic_vu3, (evidencia if isinstance(evidencia, dict) else {}).get("ES0902.Vu3"))
        aplic_vu4, _ = seguridad.resolver_regla(seguridad.regla("Vu4", None, desde), booleanos)
        bloque["standards"][seguridad.ESTANDAR]["rules"]["Vu4"] = vu4_para_unidad(
            aplic_vu4, (evidencia if isinstance(evidencia, dict) else {}).get("ES0902.Vu4"))
        aplic_vu5, _ = seguridad.resolver_regla(seguridad.regla("Vu5", None, desde), booleanos)
        bloque["standards"][seguridad.ESTANDAR]["rules"]["Vu5"] = vu5_para_unidad(
            aplic_vu5, (evidencia if isinstance(evidencia, dict) else {}).get("ES0902.Vu5"))
        aplic_vu6, _ = seguridad.resolver_regla(seguridad.regla("Vu6", None, desde), booleanos)
        bloque["standards"][seguridad.ESTANDAR]["rules"]["Vu6"] = vu6_para_unidad(
            aplic_vu6, (evidencia if isinstance(evidencia, dict) else {}).get("ES0902.Vu6"))
        # Vu7 es ALWAYS: no hay aplicabilidad que resolver ni que llevar.
        bloque["standards"][seguridad.ESTANDAR]["rules"]["Vu7"] = vu7_para_unidad(
            (evidencia if isinstance(evidencia, dict) else {}).get("ES0902.Vu7"))
        aplic_vu8, _ = seguridad.resolver_regla(seguridad.regla("Vu8", None, desde), booleanos)
        bloque["standards"][seguridad.ESTANDAR]["rules"]["Vu8"] = vu8_para_unidad(
            aplic_vu8, (evidencia if isinstance(evidencia, dict) else {}).get("ES0902.Vu8"))
    except seguridad.SeguridadInvalida as e:
        # Un estandar roto no se lleva puesto al otro. Se dice cual, y ES0901 sigue resolviendo.
        bloque["standards"][seguridad.ESTANDAR] = {
            "standard": {"id": seguridad.ESTANDAR, "version": None, "section": None,
                         "sourceDate": None},
            "applicableRules": [], "notApplicableRules": [], "unresolvedRules": [],
            "declaredPolicies": [], "declaredChecks": [], "declaredReviews": [],
            "evidence": {"signals": {}}, "error": str(e)}
    return bloque


# Los estados del check de Vu3. Escritos aca porque `bin/` no importa los controles.
ESTADOS_DEL_CHECK_VU3 = ("PASS", "FAIL", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED",
                         "SUPPORTED_BROWSER_SCOPE_UNRESOLVED", "BROWSER_SESSION_MODEL_UNRESOLVED",
                         "BROWSER_CLOSE_BEHAVIOR_UNRESOLVED",
                         "OLD_APPLICATION_SESSION_REMAINS_ACTIVE",
                         "BROWSER_SESSION_TERMINATION_TEST_UNSAFE", "TEST_TARGET_UNAVAILABLE")


def _ruta_de_evidencia():
    import os
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        "controles", "lib", "evidencia.py")


def _evidencia_de_controles(ruta=None):
    """`controles/lib/evidencia.py`, por ruta, o `None` si no esta.

    🔴 `bin/` se instala y `controles/` todavia no (ver `PENDIENTES-FH.md`). Sin la regla de salida
    la unidad no se cae: lleva el estado y ningun id. (Refutador de Vu3, pase 1.)
    """
    import importlib.util
    try:
        spec = importlib.util.spec_from_file_location("_normativa_evidencia",
                                                      ruta or _ruta_de_evidencia())
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo
    except (OSError, ImportError, AttributeError, SyntaxError):
        return None


def vu3_para_unidad(aplicabilidad, resultado=None, ruta_de_evidencia=None):
    """El bloque de Vu3 que viaja en la unidad: ids y estados, nunca contenido.

    🔴 Se proyecta un resultado que dice ser del check de Vu3 y nada mas, y pasa por la misma regla
    de salida que el check: ni una cookie ni un token llegan a la unidad, vengan de donde vengan.
    """
    from . import seguridad
    r = resultado if isinstance(resultado, dict) else {}
    estado = r.get("state") if r.get("control") == "browser-close-session-termination" else None
    if estado not in ESTADOS_DEL_CHECK_VU3:
        r, estado = {}, None
    if aplicabilidad != seguridad.APLICABLE:
        r = {}
        estado = (seguridad.NO_APLICABLE if aplicabilidad == seguridad.NO_APLICABLE
                  else seguridad.RESULTADO_SIN_RESOLVER)
    superficies = [s for s in r.get("surfaces") or [] if isinstance(s, dict)]
    ids = set()
    for s in superficies:
        usada = s.get("evidenceUsed") if isinstance(s.get("evidenceUsed"), dict) else {}
        for v in usada.values():
            ids.update(i for i in (v if isinstance(v, list) else []) if isinstance(i, str))
        for c in s.get("combinations") or []:
            if isinstance(c, dict):
                ids.update(i for i in c.get("evidenceUsed") or [] if isinstance(i, str))
    bloque = {"applicability": aplicabilidad,
              "result": estado or seguridad.RESULTADO_SIN_RESOLVER,
              "surfaces": sorted(str(s.get("surfaceId")) for s in superficies),
              "evidence": sorted(ids),
              "source": {"standard": "ES0902", "version": "6.2", "section": "6", "rule": "Vu3"}}
    limpieza = _evidencia_de_controles(ruta_de_evidencia)
    if limpieza is None:
        bloque["surfaces"], bloque["evidence"] = [], []
        return bloque
    return limpieza.depurar(bloque)


# Los estados del check de Vu4, por la misma razon.
ESTADOS_DEL_CHECK_VU4 = ("PASS", "FAIL", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED",
                         "SESSION_COVERAGE_UNRESOLVED", "SESSION_TIMEOUT_POLICY_COVERAGE_UNRESOLVED",
                         "SESSION_ACTIVITY_SEMANTICS_UNRESOLVED",
                         "SESSION_INACTIVITY_TIMEOUT_UNRESOLVED", "TOKEN_TIMEOUT_ONLY",
                         "INACTIVE_SESSION_REMAINS_USABLE", "SESSION_INACTIVITY_TIMEOUT_TEST_UNSAFE",
                         "TEST_TARGET_UNAVAILABLE")


def vu4_para_unidad(aplicabilidad, resultado=None, ruta_de_evidencia=None):
    """El bloque de Vu4 que viaja en la unidad: ids y estados, nunca contenido.

    🔴 Igual que Vu3: se proyecta solo un resultado que dice ser del check de Vu4, y pasa por la
    regla de salida de `controles/lib/evidencia.py`. Sin esa lib, el estado viaja y ningun id.
    """
    from . import seguridad
    r = resultado if isinstance(resultado, dict) else {}
    estado = r.get("state") if r.get("control") == "session-inactivity-timeout" else None
    if estado not in ESTADOS_DEL_CHECK_VU4:
        r, estado = {}, None
    if aplicabilidad != seguridad.APLICABLE:
        r = {}
        estado = (seguridad.NO_APLICABLE if aplicabilidad == seguridad.NO_APLICABLE
                  else seguridad.RESULTADO_SIN_RESOLVER)
    sesiones = [s for s in r.get("sessions") or [] if isinstance(s, dict)]
    ids = set()
    for s in sesiones:
        usada = s.get("evidenceUsed") if isinstance(s.get("evidenceUsed"), dict) else {}
        for v in usada.values():
            ids.update(i for i in (v if isinstance(v, list) else []) if isinstance(i, str))
    bloque = {"applicability": aplicabilidad,
              "result": estado or seguridad.RESULTADO_SIN_RESOLVER,
              "sessions": sorted(str(s.get("sessionId")) for s in sesiones),
              "evidence": sorted(ids),
              "source": {"standard": "ES0902", "version": "6.2", "section": "6", "rule": "Vu4"}}
    limpieza = _evidencia_de_controles(ruta_de_evidencia)
    if limpieza is None:
        bloque["sessions"], bloque["evidence"] = [], []
        return bloque
    return limpieza.depurar(bloque)


# Los estados del check de Vu5, por la misma razon.
ESTADOS_DEL_CHECK_VU5 = ("PASS", "FAIL", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED",
                         "CLIENT_VALIDATION_COVERAGE_UNRESOLVED",
                         "CLIENT_SERVER_VALIDATION_MAPPING_UNRESOLVED", "SERVER_VALIDATION_MISSING",
                         "SERVER_VALIDATION_WEAKER", "VALIDATION_EQUIVALENCE_UNRESOLVED",
                         "SERVER_VALIDATION_TEST_UNSAFE", "TEST_TARGET_UNAVAILABLE")


def vu5_para_unidad(aplicabilidad, resultado=None, ruta_de_evidencia=None):
    """El bloque de Vu5 que viaja en la unidad: ids y estados, nunca contenido.

    🔴 Igual que Vu4: se proyecta solo un resultado que dice ser del check de Vu5, y pasa por la
    regla de salida de `controles/lib/evidencia.py`. Sin esa lib, el estado viaja y ningun id.
    Ni la descripcion de una restriccion ni una operacion del servidor llegan a la unidad.
    """
    from . import seguridad
    r = resultado if isinstance(resultado, dict) else {}
    estado = r.get("state") if r.get("control") == "client-server-validation-parity" else None
    if estado not in ESTADOS_DEL_CHECK_VU5:
        r, estado = {}, None
    if aplicabilidad != seguridad.APLICABLE:
        r = {}
        estado = (seguridad.NO_APLICABLE if aplicabilidad == seguridad.NO_APLICABLE
                  else seguridad.RESULTADO_SIN_RESOLVER)
    clientes = [c for c in r.get("clients") or [] if isinstance(c, dict)]
    ids = set()
    for c in clientes:
        for v in c.get("validations") or []:
            usada = (v.get("evidenceUsed") if isinstance(v, dict)
                     and isinstance(v.get("evidenceUsed"), dict) else {})
            for u in usada.values():
                ids.update(i for i in (u if isinstance(u, list) else []) if isinstance(i, str))
    bloque = {"applicability": aplicabilidad,
              "result": estado or seguridad.RESULTADO_SIN_RESOLVER,
              "clients": sorted(str(c.get("clientSurfaceId")) for c in clientes),
              "evidence": sorted(ids),
              "source": {"standard": "ES0902", "version": "6.2", "section": "6", "rule": "Vu5"}}
    limpieza = _evidencia_de_controles(ruta_de_evidencia)
    if limpieza is None:
        bloque["clients"], bloque["evidence"] = [], []
        return bloque
    return limpieza.depurar(bloque)



# Los estados del check de Vu6, por la misma razon.
ESTADOS_DEL_CHECK_VU6 = ("PASS", "FAIL", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED",
                         "ERROR_SURFACE_COVERAGE_UNRESOLVED", "DEFAULT_ERROR_EXPOSED",
                         "RAW_TECHNICAL_ERROR_EXPOSED", "INFRASTRUCTURE_DETAIL_EXPOSED",
                         "ERROR_CUSTOMIZATION_UNRESOLVED", "HTTP_ERROR_SEMANTICS_MASKED",
                         "ERROR_MESSAGE_TEST_UNSAFE", "TEST_TARGET_UNAVAILABLE")


def vu6_para_unidad(aplicabilidad, resultado=None, ruta_de_evidencia=None):
    """El bloque de Vu6 que viaja en la unidad: ids y estados, nunca contenido.

    🔴 Igual que Vu5: se proyecta solo un resultado que dice ser del check de Vu6, y pasa por la
    regla de salida de `controles/lib/evidencia.py`. Sin esa lib, el estado viaja y ningun id.
    Ningun texto de una evidencia -un stack trace, una IP, una ruta- llega a la unidad.
    """
    from . import seguridad
    r = resultado if isinstance(resultado, dict) else {}
    estado = r.get("state") if r.get("control") == "custom-error-message-compliance" else None
    if estado not in ESTADOS_DEL_CHECK_VU6:
        r, estado = {}, None
    if aplicabilidad != seguridad.APLICABLE:
        r = {}
        estado = (seguridad.NO_APLICABLE if aplicabilidad == seguridad.NO_APLICABLE
                  else seguridad.RESULTADO_SIN_RESOLVER)
    superficies = [s for s in r.get("surfaces") or [] if isinstance(s, dict)]
    ids = set()
    for s in superficies:
        for x in s.get("scenarios") or []:
            usada = (x.get("evidenceUsed") if isinstance(x, dict)
                     and isinstance(x.get("evidenceUsed"), dict) else {})
            for u in usada.values():
                ids.update(i for i in (u if isinstance(u, list) else []) if isinstance(i, str))
    bloque = {"applicability": aplicabilidad,
              "result": estado or seguridad.RESULTADO_SIN_RESOLVER,
              "surfaces": sorted(str(s.get("surfaceId")) for s in superficies),
              "evidence": sorted(ids),
              "source": {"standard": "ES0902", "version": "6.2", "section": "6", "rule": "Vu6"}}
    limpieza = _evidencia_de_controles(ruta_de_evidencia)
    if limpieza is None:
        bloque["surfaces"], bloque["evidence"] = [], []
        return bloque
    return limpieza.depurar(bloque)


# Los estados del check de Vu7, por la misma razon. No hay NOT_APPLICABLE: la regla es ALWAYS.
ESTADOS_DEL_CHECK_VU7 = ("PASS", "FAIL", "BASE_SOFTWARE_INVENTORY_UNRESOLVED",
                         "PRIVATE_DATA_CLASSIFICATION_UNRESOLVED",
                         "DISCLOSURE_SURFACE_COVERAGE_UNRESOLVED",
                         "BASE_SOFTWARE_CONFIGURATION_UNRESOLVED",
                         "UNAUTHORIZED_PRIVATE_DATA_DISCLOSURE",
                         "BASE_SOFTWARE_DISCLOSURE_TEST_UNSAFE", "TEST_TARGET_UNAVAILABLE")


def vu7_para_unidad(resultado=None, ruta_de_evidencia=None):
    """El bloque de Vu7 que viaja en la unidad: ids y estados, nunca contenido.

    🔴 Sin `applicability`: la regla es ALWAYS. Como Vu6, se proyecta solo un resultado que dice ser
    del check de Vu7, y pasa por la regla de salida de `controles/lib/evidencia.py`. Sin esa lib, el
    estado viaja y ningun id, ni el ambiente. Ni el texto de una evidencia ni una muestra de un dato
    llegan a la unidad.
    """
    from . import seguridad
    r = resultado if isinstance(resultado, dict) else {}
    estado = (r.get("state") if r.get("control") == "base-software-data-disclosure-configuration"
              else None)
    if estado not in ESTADOS_DEL_CHECK_VU7:
        r, estado = {}, None
    componentes = [c for c in r.get("components") or [] if isinstance(c, dict)]
    ids = set()
    cobertura = r.get("coverage") if isinstance(r.get("coverage"), dict) else {}
    listas = [cobertura.get("inventoryEvidence")]
    listas += [x.get("evidenceUsed") for x in r.get("dataClasses") or [] if isinstance(x, dict)]
    for c in componentes:
        listas.append(c.get("scopeEvidence"))
        for s in c.get("surfaces") or []:
            usada = (s.get("evidenceUsed") if isinstance(s, dict)
                     and isinstance(s.get("evidenceUsed"), dict) else {})
            listas.extend(usada.values())
    for u in listas:
        ids.update(i for i in (u if isinstance(u, list) else []) if isinstance(i, str))
    ambiente = r.get("environment")
    bloque = {"result": estado or seguridad.RESULTADO_SIN_RESOLVER,
              "environment": ambiente if isinstance(ambiente, str) else None,
              "components": sorted(str(c.get("componentId")) for c in componentes),
              "evidence": sorted(ids),
              "source": {"standard": "ES0902", "version": "6.2", "section": "6", "rule": "Vu7"}}
    limpieza = _evidencia_de_controles(ruta_de_evidencia)
    if limpieza is None:
        bloque["environment"], bloque["components"], bloque["evidence"] = None, [], []
        return bloque
    return limpieza.depurar(bloque)


# Los estados del check de Vu8, por la misma razon.
ESTADOS_DEL_CHECK_VU8 = ("PASS", "FAIL", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED",
                         "ROLE_ASSIGNMENT_SOURCE_UNRESOLVED", "ROLE_PROFILE_MAPPING_UNRESOLVED",
                         "MULTI_ROLE_PROFILE_UNRESOLVED", "ROLE_CHANGE_PROPAGATION_UNRESOLVED",
                         "OVER_PRIVILEGED_PROFILE", "UNDER_PRIVILEGED_PROFILE",
                         "DIRECT_ACCESS_BYPASSES_ROLE", "ROLE_PROFILE_TEST_UNSAFE",
                         "TEST_TARGET_UNAVAILABLE")


def vu8_para_unidad(aplicabilidad, resultado=None, ruta_de_evidencia=None):
    """El bloque de Vu8 que viaja en la unidad: ids y estados, nunca contenido.

    🔴 Igual que Vu6: se proyecta solo un resultado que dice ser del check de Vu8, y pasa por la regla
    de salida de `controles/lib/evidencia.py`. Sin esa lib, el estado viaja y ningun id. Ni una
    identidad de prueba ni el texto de una evidencia llegan a la unidad.
    """
    from . import seguridad
    r = resultado if isinstance(resultado, dict) else {}
    estado = r.get("state") if r.get("control") == "role-profile-consistency" else None
    if estado not in ESTADOS_DEL_CHECK_VU8:
        r, estado = {}, None
    if aplicabilidad != seguridad.APLICABLE:
        r = {}
        estado = (seguridad.NO_APLICABLE if aplicabilidad == seguridad.NO_APLICABLE
                  else seguridad.RESULTADO_SIN_RESOLVER)
    superficies = [s for s in r.get("surfaces") or [] if isinstance(s, dict)]
    ids = set()
    for s in superficies:
        listas = [(s.get(c) or {}).get("evidenceUsed") if isinstance(s.get(c), dict) else None
                  for c in ("roleAssignmentSource", "multiRoleSemantics", "roleChangeSemantics")]
        for m in s.get("mappings") or []:
            usada = (m.get("evidenceUsed") if isinstance(m, dict)
                     and isinstance(m.get("evidenceUsed"), dict) else {})
            listas.extend(usada.values())
        for u in listas:
            ids.update(i for i in (u if isinstance(u, list) else []) if isinstance(i, str))
    bloque = {"applicability": aplicabilidad,
              "result": estado or seguridad.RESULTADO_SIN_RESOLVER,
              "surfaces": sorted(str(s.get("surfaceId")) for s in superficies),
              "evidence": sorted(ids),
              "source": {"standard": "ES0902", "version": "6.2", "section": "6", "rule": "Vu8"}}
    limpieza = _evidencia_de_controles(ruta_de_evidencia)
    if limpieza is None:
        bloque["surfaces"], bloque["evidence"] = [], []
        return bloque
    return limpieza.depurar(bloque)


def _sin_senales(bloque):
    """El bloque de ES0901 sin `signals` ni `standards`: lo que va adentro de `standards`.

    Se copia y no se referencia. Un diccionario que se apunta a si mismo no se serializa, y
    este bloque viaja a un plan en JSON.
    """
    return {k: v for k, v in bloque.items() if k not in ("signals", "standards")}


def estado_de_matriz(desde=None):
    """(estado, errores) de la matriz instalada, o el estado de que no este."""
    from . import matriz
    try:
        return matriz.validar(matriz.cargar(desde), desde)
    except matriz.MatrizInvalida as e:
        return "NORMATIVE_MATRIX_INVALID", [str(e)]
