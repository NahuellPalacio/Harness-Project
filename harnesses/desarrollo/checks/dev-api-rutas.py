"""Check: nomenclatura de rutas de API (ES0903).

ES0903 fija como se nombra un endpoint. Dos reglas se pueden comprobar sin criterio
humano y sin ambiguedad, y son las dos que mas caro salen de corregir despues:

  1. La ruta lleva la version. Sin version no hay forma de romper el contrato sin
     romperle la aplicacion a alguien.
  2. El recurso es un sustantivo, no un verbo. La accion la dice el metodo HTTP.
     POST /usuarios y POST /crearUsuario hacen lo mismo y solo el primero deja que
     GET, PUT y DELETE signifiquen algo sobre el mismo recurso.

La tercera -plural- solo se reporta cuando es inequivoca: un segmento singular
seguido de un identificador. /usuario/{id} es una coleccion mal nombrada; un /salud
suelto puede ser cualquier cosa y no se toca.

Avisa, no bloquea. Y se calla en cuanto la ruta no parece una ruta de API: un check
de nomenclatura con falsos positivos se desactiva la primera semana.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import dev  # noqa: E402

VERBOS = [
    "get", "post", "put", "patch", "delete", "create", "update", "remove", "add",
    "fetch", "list", "find", "search", "save", "load",
    "crear", "obtener", "listar", "buscar", "guardar", "eliminar", "borrar",
    "actualizar", "modificar", "consultar", "traer", "alta", "baja",
]

EXTENSIONES_POSIBLES = [".yaml", ".yml", ".json", ".raml", ".ts", ".js", ".php", ".java", ".cs", ".py"]


def verificar(evento, proyecto, config):
    """Devuelve cero o mas strings. Cada string es un hallazgo."""
    archivo = dev.archivo_escrito(evento)
    if archivo is None:
        return []
    if dev.es_ruta_generada(archivo["ruta"]):
        return []

    if archivo["extension"] not in EXTENSIONES_POSIBLES:
        return []

    prefijo = "api"
    if config is not None and config.get("prefijoApi"):
        prefijo = str(config["prefijoApi"])

    # Solo rutas que arrancan con el prefijo de API del proyecto. Sin esto el check se
    # pondria a opinar sobre rutas de front, imports y cualquier cadena con barras.
    patron_ruta = "[\"'`](/" + re.escape(prefijo) + "/[^\"'`\\s]*)[\"'`]"
    encontradas = list(re.finditer(patron_ruta, archivo["texto"]))
    if not encontradas:
        return []

    sin_version = []
    con_verbo = []
    singulares = []
    ya_vistas = []

    for m in encontradas:
        ruta = m.group(1)
        if ruta in ya_vistas:
            continue
        ya_vistas.append(ruta)

        linea = dev.linea_de(archivo["texto"], m.start())
        etiqueta = "%s (L%d)" % (ruta, linea)

        if not re.search(r"/v\d+(/|$)", ruta):
            sin_version.append(etiqueta)

        segmentos = [s for s in ruta.split("/") if s]
        for i, s in enumerate(segmentos):
            if (re.match(r"^\{.*\}$", s) or re.match(r"^:", s)
                    or re.match(r"^v\d+$", s) or s == prefijo):
                continue

            # El verbo se busca como palabra entera o como primer termino en
            # camelCase. Sin eso, "postulaciones" se reportaria por empezar con
            # "post". El primer termino se corta primero por el separador explicito
            # -_- y despues se toma la corrida inicial de minusculas.
            base = re.split(r"[-_]", s)[0]
            m_primero = re.match(r"^[A-Za-z][a-z]*", base)
            primer_termino = m_primero.group(0).lower() if m_primero else ""
            if s.lower() in VERBOS or (primer_termino and primer_termino in VERBOS):
                if etiqueta not in con_verbo:
                    con_verbo.append(etiqueta)

            # Singular solo cuando es inequivoco: viene un identificador atras.
            siguiente = segmentos[i + 1] if i + 1 < len(segmentos) else ""
            if re.match(r"^\{.*\}$", siguiente) or re.match(r"^:", siguiente):
                if not re.search(r"s$", s) and not re.match(r"^v\d+$", s):
                    if etiqueta not in singulares:
                        singulares.append(etiqueta)

    hallazgos = []

    if sin_version:
        hallazgos.append(
            "[ES0903] %s: ruta(s) de API sin version — %s. "
            "Deberia ser /%s/v1/... : sin la version en la ruta no hay forma de cambiar el contrato sin romperle la aplicacion a quien ya la consume."
            % (archivo["nombre"], dev.formatear_lista(sin_version), prefijo))

    if con_verbo:
        hallazgos.append(
            "[ES0903] %s: la accion va en el metodo HTTP, no en la ruta — %s. "
            "El recurso se nombra con un sustantivo; que sea alta, consulta o baja lo dice POST, GET o DELETE."
            % (archivo["nombre"], dev.formatear_lista(con_verbo)))

    if singulares:
        hallazgos.append(
            "[ES0903] %s: coleccion en singular — %s. "
            "El segmento que lleva un identificador atras es una coleccion y va en plural."
            % (archivo["nombre"], dev.formatear_lista(singulares)))

    return hallazgos
