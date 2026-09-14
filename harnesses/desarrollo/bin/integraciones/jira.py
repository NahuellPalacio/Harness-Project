"""Jira Cloud. Solo lo necesario para saber si esta disponible y que se puede leer.

Auth Basic con `usuario:token` en base64, que es lo que Jira Cloud espera de un API
token -no un Bearer-. El token nunca va en la URL: una URL queda en logs de proxy, en
el historial del navegador y en cualquier traza intermedia.

No resuelve tickets ni arma fichas de proyecto: eso es Bloque 2.
"""
import base64

from .base import Integracion

CAPACIDADES = ("jira.issue.read", "jira.issue.search", "jira.attachment.read")


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

    def descubrir_capacidades(self):
        """Sondea de verdad: una capacidad se declara cuando el endpoint contesta.

        La busqueda tiene dos caminos porque Atlassian movio el endpoint: `/search/jql`
        es el actual y `/search` el que quedo en instancias viejas. Si el primero
        contesta 404 o 410 se prueba el segundo, y recien ahi se declara el hueco.
        """
        capacidades = []

        respuesta = self.pedir("/rest/api/3/search/jql?jql=order+by+created+DESC&maxResults=1")
        if respuesta.codigo in (404, 410):
            respuesta = self.pedir("/rest/api/3/search?maxResults=0")
        if respuesta.ok:
            capacidades.append("jira.issue.read")
            capacidades.append("jira.issue.search")

        if self.pedir("/rest/api/3/attachment/meta").ok:
            capacidades.append("jira.attachment.read")

        return capacidades
