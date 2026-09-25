"""Jira Cloud. Solo lo necesario para saber si esta disponible y que se puede leer.

Auth Basic con `usuario:token` en base64, que es lo que Jira Cloud espera de un API
token -no un Bearer-. El token nunca va en la URL: una URL queda en logs de proxy, en
el historial del navegador y en cualquier traza intermedia.

Lee, y no interpreta. Los metodos de lectura devuelven la respuesta cruda: normalizar
los campos de un issue es trabajo del Context Resolver, y un adapter que ademas interpreta
se vuelve el lugar donde nadie sabe si un campo vacio vino asi o lo vacio el adapter.
"""
import base64
import os
import re
from urllib.parse import quote

from . import http
from .base import Integracion, diagnostico_de

CAPACIDADES = ("jira.issue.read", "jira.issue.search", "jira.attachment.read")

# La consulta de la sonda. Verificada contra el Jira Cloud del organismo el 25-09-2026: Cloud
# rechaza con 400 una JQL sin restriccion (`order by created DESC` sola), y esta la acepta. Un
# 200 con `issues: []` -una instancia sin issues en 30 dias- sigue siendo busqueda disponible.
JQL_DE_SONDA = "created >= -30d order by created DESC"

# El error local de `buscar` cuando la JQL no tiene restriccion: no se sale a la red.
JQL_SIN_RESTRICCION = "JQL_UNBOUNDED"

_ORDER_BY = re.compile(r"(?i)\border\s+by\b")
_CLAVE_DE_ISSUE = re.compile(r"^[A-Z][A-Z0-9_]*-[0-9]+$")


def jql_acotada(jql):
    """Si la JQL tiene una clausula antes del ORDER BY. Vacia o solo orden, no."""
    texto = str(jql or "").strip()
    return bool(_ORDER_BY.split(texto, 1)[0].strip())


class IntegracionJira(Integracion):
    nombre = "jira"
    etiqueta = "Jira Cloud"
    clave_token = "JIRA_TOKEN"
    campos = ("baseUrl", "usuario")
    CAPACIDADES = CAPACIDADES

    camino_de_validacion = "/rest/api/3/myself"

    def cabeceras(self):
        credencial = "%s:%s" % (self.configuracion.get("usuario", ""), self.token() or "")
        codificada = base64.b64encode(credencial.encode("utf-8")).decode("ascii")
        return {"Authorization": "Basic " + codificada, "Accept": "application/json"}

    def secretos(self):
        """El token, la credencial Basic y el usuario: lo que se manda y no puede volver."""
        usuario = str(self.configuracion.get("usuario", "") or "")
        token = self.token() or ""
        credencial = base64.b64encode(("%s:%s" % (usuario, token)).encode("utf-8")).decode("ascii")
        return [s for s in (token, credencial, usuario) if s]

    def descubrir_capacidades(self):
        """Sondea de verdad: una capacidad se declara cuando SU endpoint contesta.

        🔴 Cada capacidad se sondea por si misma. `jira.issue.read` se declaraba por el
        resultado de la busqueda, que es otra capacidad: con la busqueda rota el token leia
        issues y el harness decia que no.

        🔴 Sin caida a `/rest/api/3/search`. Un 400 de `/search/jql` es la consulta rechazada,
        no un endpoint inexistente, y en Jira Cloud `/search` contesta 410. Lo que falta se
        dice en `diagnostico`, con el pedido y el codigo.
        """
        capacidades = []
        self.diagnostico = []

        busqueda = self.buscar(JQL_DE_SONDA, maximo=1, campos="summary")
        clave = None
        if busqueda.ok:
            capacidades.append("jira.issue.search")
            issues = (busqueda.datos() or {}).get("issues") or []
            primero = issues[0] if issues and isinstance(issues[0], dict) else {}
            clave = primero.get("key") if _CLAVE_DE_ISSUE.match(str(primero.get("key") or "")) \
                else None
        else:
            self._anotar("jira.issue.search", "la busqueda de prueba", busqueda)

        if clave:
            lectura = self.pedir("/rest/api/3/issue/%s?fields=summary" % quote(clave))
            if lectura.ok:
                capacidades.append("jira.issue.read")
            else:
                self._anotar("jira.issue.read", "la lectura del issue %s" % clave, lectura)
        else:
            # Sin un issue a mano -la busqueda fallo o no trajo ninguno- se pregunta por el
            # permiso de ver proyectos, que es el que deja leer un issue.
            permisos = self.pedir("/rest/api/3/mypermissions?permissions=BROWSE_PROJECTS")
            tiene = (((permisos.datos() or {}).get("permissions") or {})
                     .get("BROWSE_PROJECTS") or {}).get("havePermission") if permisos.ok else None
            if tiene is True:
                capacidades.append("jira.issue.read")
            elif permisos.ok:
                self.diagnostico.append(
                    "jira.issue.read: %s dice que el token no tiene el permiso BROWSE_PROJECTS."
                    % self.etiqueta)
            else:
                self._anotar("jira.issue.read", "la consulta de permisos", permisos)

        adjuntos = self.pedir("/rest/api/3/attachment/meta")
        if adjuntos.ok:
            capacidades.append("jira.attachment.read")
        else:
            self._anotar("jira.attachment.read", "la configuracion de adjuntos", adjuntos)

        return capacidades

    def _anotar(self, capacidad, que, respuesta):
        self.diagnostico.append(diagnostico_de(capacidad, que, respuesta, self.etiqueta,
                                               self.secretos()))

    # -- lectura ---------------------------------------------------------------
    #
    # Lo que sigue lo consume el Context Resolver. Cada metodo devuelve la Respuesta
    # cruda, sin interpretar: normalizar los campos de un issue es trabajo del
    # resolvedor, y un adapter que ademas interpreta se vuelve el lugar donde nadie
    # sabe si un campo vacio vino asi o lo vacio el adapter.

    def issue(self, clave):
        """Un issue con los campos que el contexto necesita, no con todos."""
        campos = ("summary,description,issuetype,status,priority,labels,parent,"
                  "issuelinks,project,attachment")
        return self.pedir("/rest/api/3/issue/%s?fields=%s" % (clave, campos))

    def buscar(self, jql, maximo=10, campos="summary,description,issuetype,attachment"):
        """Busqueda por JQL en `/search/jql`, sin caida a `/search`.

        🔴 Una JQL sin restriccion no sale a la red: Jira Cloud la rechaza con 400, y una
        busqueda que depende de eso falla lejos de donde se escribio. Vuelve una respuesta
        local con `error = JQL_UNBOUNDED`.
        """
        if not jql_acotada(jql):
            return http.Respuesta(0, "", JQL_SIN_RESTRICCION)
        camino = "/rest/api/3/search/jql?jql=%s&maxResults=%d&fields=%s" % (
            quote(jql), maximo, campos)
        return self.pedir(camino)

    def bajar_adjunto(self, url, destino):
        """Baja un adjunto a disco. Devuelve (ok, bytes escritos, motivo).

        La URL viene del propio issue, no se arma: Jira sirve los adjuntos desde un
        host de contenido que no es el de la API, y adivinarlo es como se rompe.

        🔴 Jira Cloud contesta 303 a una URL firmada. `http.descargar` sigue ese salto, uno
        solo, a https y SIN la credencial. Si falla no se escribe nada, y el motivo dice por
        que sin nombrar la URL firmada.
        """
        respuesta = http.descargar(url, self.cabeceras(), self.timeout, self.transporte_bytes)
        if not respuesta.ok or respuesta.error:
            return False, 0, http.motivo_de_descarga(respuesta)
        datos = respuesta.datos
        carpeta = os.path.dirname(os.path.abspath(destino))
        if carpeta and not os.path.isdir(carpeta):
            os.makedirs(carpeta)
        with open(destino, "wb") as f:
            f.write(datos)
        return True, len(datos), ""
