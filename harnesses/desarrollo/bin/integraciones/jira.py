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

from . import http
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

    def buscar(self, jql, maximo=10):
        """Busqueda por JQL. El endpoint nuevo primero, el viejo como caida."""
        from urllib.parse import quote
        camino = "/rest/api/3/search/jql?jql=%s&maxResults=%d&fields=summary,description,issuetype,attachment" % (
            quote(jql), maximo)
        respuesta = self.pedir(camino)
        if respuesta.codigo in (404, 410):
            respuesta = self.pedir(
                "/rest/api/3/search?jql=%s&maxResults=%d&fields=summary,description,issuetype,attachment"
                % (quote(jql), maximo))
        return respuesta

    def bajar_adjunto(self, url, destino):
        """Baja un adjunto a disco. Devuelve (ok, bytes escritos).

        La URL viene del propio issue, no se arma: Jira sirve los adjuntos desde un
        host de contenido que no es el de la API, y adivinarlo es como se rompe.
        """
        respuesta = http.pedir_bytes(url, self.cabeceras(), self.timeout, self.transporte_bytes)
        if not respuesta.ok:
            return False, 0
        datos = respuesta.datos
        carpeta = os.path.dirname(os.path.abspath(destino))
        if carpeta and not os.path.isdir(carpeta):
            os.makedirs(carpeta)
        with open(destino, "wb") as f:
            f.write(datos)
        return True, len(datos)
