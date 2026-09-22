"""Check normativo: la version esta homologada dentro de su rama.

    source: ES0901 / 6.3 / 7.1 / G1

🔴 **El parche sube dentro de su rama, y nada mas.** Homologada `8.2.30`: `8.2.31` vale,
`8.2.29` no. Una rama que no figura no se vuelve valida sola — mas vieja es
`NOT_HOMOLOGATED`, mas nueva es `ASI_EVALUATION_REQUIRED` porque nadie la evaluo todavia.

🔴 **Deprecada no es homologada.** Se tolera con observacion formal de actualizacion, sigue
apareciendo en el reporte, y la ASI puede rechazarla igual por vulnerabilidad critica o
incompatibilidad: el estado dice "tolerada", nunca "aprobada".

🔴 **Dos estandares atras no se infiere.** El Anexo II instalado es el de 6.3 y no trae
historia. Afirmar que una version esta dos estandares atras necesita el catalogo de esas
versiones; sin el es `VERSION_HISTORY_REQUIRED` y no bloquea nada por deduccion.

🔴 **`latest` no es una version.** Ni `*`, ni una rama sin fijar. No hay contra que
compararlas: `UNRESOLVED`.
"""
import os
import sys

_BIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_BIN, "bin") not in sys.path:
    sys.path.insert(0, os.path.join(_BIN, "bin"))

from orquestacion import anexo2                  # noqa: E402

CONTROL = "technology-version-compliance"
TIPO = "CHECK"
REGLA = "G1"

OBSERVACION_DEPRECADA = ("version deprecada: se tolera con observacion formal de "
                         "actualizacion. La ASI puede rechazarla igual dentro de la ventana")


def evaluar(item, catalogo=None, contexto=None, desde=None):
    """El estado de la version declarada, con su motivo y su trazabilidad."""
    doc = catalogo if catalogo is not None else anexo2.cargar(desde)
    nombre = (item or {}).get("technology") or ""
    cruda = (item or {}).get("version")
    salida = {"control": CONTROL, "technology": nombre, "declaredVersion": cruda,
              "source": dict(anexo2.TRAZA)}

    entrada = anexo2.buscar(nombre, doc, desde)
    if entrada is None:
        salida.update({"state": anexo2.EVALUACION_ASI,
                       "reason": "la tecnologia no figura en el Anexo II"})
        return salida

    salida["entry"] = entrada.get("id")
    salida["sourcePage"] = entrada.get("sourcePage")
    regla = entrada.get("versionRule", "DEFAULT")

    if regla == "PROVIDER_ASSIGNED_BY_DGSEI":
        salida.update({"state": anexo2.FALTA_PROVEEDOR,
                       "reason": "la version la asigna DGSEI: no se compara contra el catalogo"})
        return salida

    if regla in ("CONTEXT_DEPENDENT", "FRAMEWORK_DEPENDENT"):
        return _dependiente_de_framework(salida, entrada, doc, contexto, desde)

    # Paso 1: la forma. Lo que no esta escrito como lo escribe el Anexo II no se adivina.
    pedida = anexo2.version_pedida(cruda)
    if pedida is None:
        salida.update({"state": anexo2.SIN_RESOLVER,
                       "reason": "la version declarada no se puede contrastar contra el "
                                 "catalogo: no esta escrita como la escribe el Anexo II, o es "
                                 "`latest` o una rama sin fijar"})
        return salida
    if pedida["qualifier"]:
        salida["declaredQualifier"] = pedida["qualifier"]

    homologadas = [anexo2.parsear(v) for v in entrada.get("homologatedVersionsRaw") or []]
    deprecadas = [anexo2.parsear(v) for v in entrada.get("deprecatedVersionsRaw") or []]
    # Un calificativo de soporte que la tecnologia usa no cambia el artefacto, en ninguna
    # comparacion; uno que no usa objeta en toda rama listada.
    soporte = anexo2.soporte_de(entrada)
    vistas = [(p, anexo2.comparar(pedida, p, soporte), origen)
              for origen, lista in ((anexo2.HOMOLOGADA, homologadas), (anexo2.DEPRECADA, deprecadas))
              for p in lista]

    # Paso 2: el calificativo contra toda rama listada donde cae el numero, antes que el numero.
    por_calificativo = _por_calificativo(salida, vistas)
    if por_calificativo is not None:
        return por_calificativo

    # Paso 3: la rama y el numero.
    for p, donde, origen in vistas:
        if donde == anexo2.COINCIDE and origen == anexo2.HOMOLOGADA:
            salida.update({"state": anexo2.HOMOLOGADA, "matched": p["raw"],
                           "reason": "cae en la rama homologada %s" % p["raw"]})
            if p["qualifier"]:
                salida["qualifier"] = p["qualifier"]
            return salida
    for p, donde, origen in vistas:
        if donde == anexo2.COINCIDE and origen == anexo2.DEPRECADA:
            salida.update({"state": anexo2.DEPRECADA, "matched": p["raw"],
                           "observation": OBSERVACION_DEPRECADA,
                           "reason": "figura entre las versiones deprecadas"})
            if p["qualifier"]:
                salida["qualifier"] = p["qualifier"]
            return salida
    return _fuera_de_rama(salida, pedida["version"], homologadas)


# Paso 2: lo que el calificativo hace con el estado. Ninguno homologa. UNRESOLVED para el de otro
# tipo o el de soporte que la tecnologia no usa; NOT_HOMOLOGATED solo para otra edicion del mismo
# tipo o un service pack anterior; ASI_EVALUATION_REQUIRED para un service pack posterior.
_CALIFICATIVO = (
    (anexo2.CALIFICATIVO_AJENO, anexo2.SIN_RESOLVER,
     "la rama lista %s y el calificativo declarado es de otro tipo, o de soporte que la "
     "tecnologia no usa: el catalogo no dice nada de lo declarado"),
    (anexo2.FALTA_CALIFICATIVO, anexo2.SIN_RESOLVER,
     "la rama lista %s y la version declarada no dice cual: no hay con que compararla"),
    (anexo2.OTRO_CALIFICATIVO, anexo2.NO_HOMOLOGADA,
     "la rama lista %s y se declara otra edicion: es otro artefacto, no el homologado"),
    (anexo2.SP_ANTERIOR, anexo2.NO_HOMOLOGADA,
     "la rama lista %s y el service pack declarado es anterior"),
    (anexo2.ARRIBA, anexo2.EVALUACION_ASI,
     "la rama lista %s y el service pack declarado es posterior: nadie lo evaluo todavia"),
)


def _por_calificativo(salida, vistas):
    """El numero cae en una rama listada y el calificativo objeta. None si no es el caso."""
    for motivo, estado, texto in _CALIFICATIVO:
        for p, donde, _origen in vistas:
            if donde == motivo:
                salida.update({"state": estado, "matched": p["raw"], "reason": texto % p["raw"]})
                if p["qualifier"]:
                    salida["qualifier"] = p["qualifier"]
                return salida
    return None


def _dependiente_de_framework(salida, entrada, doc, contexto, desde):
    """Sin el framework declarado no hay numero que comparar.

    Con el framework declarado, la entrada HEREDA su estado: una herramienta cuya version el
    estandar define como "framework-dependent" esta homologada exactamente cuando lo esta el
    framework del que depende. La herencia se declara aca; no se deduce en ningun otro lado.
    """
    framework = ((contexto or {}).get("framework") or {})
    nombre = framework.get("technology")
    if not nombre:
        salida.update({"state": anexo2.FALTA_CONTEXTO,
                       "reason": "el catalogo no fija numero: la version depende del "
                                 "framework, y el inventario no dice cual"})
        return salida

    del_framework = evaluar({"technology": nombre, "version": framework.get("version")},
                            doc, None, desde)
    salida.update({"state": del_framework["state"],
                   "inheritedFrom": nombre,
                   "reason": "version dependiente del framework: hereda el estado de %s (%s)"
                             % (nombre, del_framework["state"])})
    return salida


def _fuera_de_rama(salida, pedida, homologadas):
    """La version no cae en ninguna rama listada. Que sea mas vieja o mas nueva no da igual."""
    ramas = [p["version"][:2] for p in homologadas
             if p["kind"] in ("EXACT", "BRANCH") and p.get("version")]
    if not ramas:
        salida.update({"state": anexo2.SIN_RESOLVER,
                       "reason": "la entrada no fija ninguna rama comparable"})
        return salida

    rama_pedida = tuple(pedida[:2])
    if rama_pedida > max(ramas):
        salida.update({"state": anexo2.EVALUACION_ASI,
                       "reason": "la rama %s es posterior a todo lo homologado: nadie la "
                                 "evaluo todavia" % ".".join(str(x) for x in rama_pedida)})
        return salida

    salida.update({"state": anexo2.NO_HOMOLOGADA,
                   "reason": "la version no llega al minimo de su rama, o la rama no esta "
                             "homologada"})
    return salida


def bloqueo_por_antiguedad(item, catalogo_historico=None):
    """Si una version esta dos estandares atras —y por lo tanto bloquea el despliegue—.

    Sin el catalogo de esas versiones no se puede afirmar: `VERSION_HISTORY_REQUIRED`. El
    Anexo II instalado es una foto de 6.3 y no dice que estaba homologado en 6.1.
    """
    salida = {"control": CONTROL, "technology": (item or {}).get("technology"),
              "source": dict(anexo2.TRAZA)}
    if not catalogo_historico:
        salida.update({"state": anexo2.FALTA_HISTORIA,
                       "reason": "para afirmar que una version esta dos estandares atras hace "
                                 "falta el catalogo de esas versiones, y no esta instalado"})
        return salida
    salida.update({"state": anexo2.SIN_RESOLVER,
                   "reason": "hay historia: la comparacion se resuelve contra ella"})
    return salida
