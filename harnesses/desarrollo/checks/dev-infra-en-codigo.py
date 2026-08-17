"""Check: la infraestructura no se escribe en el codigo (ES0901).

Dos reglas del bloque comun de desarrollo, comprobables sin criterio humano:

  - Los servidores se referencian por nombre DNS, jamas por IP. Una IP en el fuente
    ata el codigo a una maquina puntual; el dia que cambia hay que recompilar para
    arreglar algo que era configuracion.
  - La configuracion va afuera del codigo. Bases, servicios externos y URLs se leen
    del entorno o de un archivo externo, ni siquiera para probar.

No pisa al hook de secretos, que es otra cosa y si bloquea: una IP no es un secreto.
Lo que se reporta aca es acoplamiento, no filtracion.

Una IP solo se reporta cuando esta en posicion de host -en una URL, un host:, una
cadena de conexion-. Suelta puede ser una version, una mascara o un dato de prueba, y
reportarla seria ruido. Las de loopback y las de documentacion no se tocan nunca.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import dev  # noqa: E402

EXTENSIONES = [
    ".ts", ".js", ".java", ".cs", ".php", ".py", ".yml", ".yaml", ".json", ".xml",
    ".properties", ".conf", ".ini",
]

# Loopback, "cualquier interfaz" y los rangos que la RFC 5737 reserva justamente para
# documentacion y ejemplos. Ninguno ata el codigo a una maquina real.
IPS_INOCENTES = ["127.0.0.1", "0.0.0.0", "255.255.255.255", "1.2.3.4"]
RANGOS_DE_EJEMPLO = r"^(192\.0\.2\.|198\.51\.100\.|203\.0\.113\.)"

# La IP tiene que estar donde va un host. Suelta en el texto es cualquier otra cosa.
POSICIONES = [
    r"https?://(\d{1,3}(?:\.\d{1,3}){3})",
    r"(?i)\b(?:host|server|hostname|servidor|addr|address|ip)\s*[:=]\s*[\"']?(\d{1,3}(?:\.\d{1,3}){3})",
    r"(?i)(?:Data\s+Source|Server|Host)\s*=\s*(\d{1,3}(?:\.\d{1,3}){3})",
    r"(?i)\b(?:jdbc|mongodb|redis|amqp|mysql|postgres(?:ql)?):[^\s\"']*?@?(\d{1,3}(?:\.\d{1,3}){3})",
]


def verificar(evento, proyecto, config):
    """Devuelve cero o mas strings. Cada string es un hallazgo."""
    archivo = dev.archivo_escrito(evento)
    if archivo is None:
        return []
    if dev.es_ruta_generada(archivo["ruta"]):
        return []

    if archivo["extension"] not in EXTENSIONES:
        return []

    ips = []
    ya_vistas = []

    for p in POSICIONES:
        for m in re.finditer(p, archivo["texto"]):
            ip = m.group(1)
            if not ip:
                continue
            if ip in IPS_INOCENTES:
                continue
            if re.match(RANGOS_DE_EJEMPLO, ip):
                continue

            # Un octeto fuera de rango significa que no era una IP: una version, una
            # fecha.
            if any(int(o) > 255 for o in ip.split(".")):
                continue

            linea = dev.linea_de(archivo["texto"], m.start())
            etiqueta = "%s (L%d)" % (ip, linea)
            if etiqueta in ya_vistas:
                continue
            ya_vistas.append(etiqueta)
            ips.append(etiqueta)

    if not ips:
        return []

    return [
        "[ES0901] %s: servidor referenciado por IP — %s. "
        "Los servidores se nombran por DNS. Una IP en el fuente ata el codigo a una maquina: el dia que cambia "
        "hay que tocar y desplegar el aplicativo para arreglar algo que era configuracion."
        % (archivo["nombre"], dev.formatear_lista(ips))
    ]
