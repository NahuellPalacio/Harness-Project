"""GitLab. El token viaja en el header PRIVATE-TOKEN, nunca en la URL.

El descubrimiento tiene dos caminos, y el primero es mejor: `/personal_access_tokens/self`
devuelve los scopes reales del token, asi que el harness puede decir que puede hacer sin
sondear un solo endpoint de datos. Ese endpoint no existe en instancias viejas -404-, y
ahi se cae al sondeo, que es mas ruidoso pero funciona en cualquier version.

No resuelve contexto ni lee commits: eso es Bloque 2.
"""
from .base import Integracion

CAPACIDADES = ("gitlab.project.read", "gitlab.repository.read",
               "gitlab.branch.read", "gitlab.merge_request.read")

# Que habilita cada scope. `api` y `read_api` dan la API de lectura entera;
# `read_repository` es solo git -clonar y leer archivos-, y no alcanza para listar
# ramas por la API ni para ver merge requests.
_POR_SCOPE = {
    "api": CAPACIDADES,
    "read_api": CAPACIDADES,
    "read_repository": ("gitlab.repository.read",),
}


class IntegracionGitLab(Integracion):
    nombre = "gitlab"
    etiqueta = "GitLab"
    clave_token = "GITLAB_TOKEN"
    campos = ("baseUrl",)
    CAPACIDADES = CAPACIDADES

    camino_de_validacion = "/api/v4/user"

    def cabeceras(self):
        return {"PRIVATE-TOKEN": self.token() or "", "Accept": "application/json"}

    def descubrir_capacidades(self):
        respuesta = self.pedir("/api/v4/personal_access_tokens/self")
        datos = respuesta.datos() if respuesta.ok else None
        if isinstance(datos, dict) and isinstance(datos.get("scopes"), list):
            return self._por_scopes(datos["scopes"])
        return self._por_sondeo()

    def _por_scopes(self, scopes):
        capacidades = set()
        for scope in scopes:
            capacidades.update(_POR_SCOPE.get(str(scope), ()))
        return sorted(capacidades)

    def _por_sondeo(self):
        """GitLab viejo: se pregunta a los endpoints en vez de a los scopes."""
        capacidades = []
        if self.pedir("/api/v4/projects?membership=true&per_page=1").ok:
            capacidades += ["gitlab.project.read", "gitlab.repository.read", "gitlab.branch.read"]
        if self.pedir("/api/v4/merge_requests?scope=all&per_page=1").ok:
            capacidades.append("gitlab.merge_request.read")
        return capacidades
