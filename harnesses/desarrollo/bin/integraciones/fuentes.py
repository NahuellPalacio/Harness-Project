"""El descubrimiento de fuentes: que hay hoy del otro lado del canal configurado.

Compara la metadata de los adjuntos de la Ficha contra el registro de fuentes y devuelve
OBSERVACIONES. No resuelve estados, no decide nada y no imprime: eso es de `frescura.py` y de
la CLI. Un modulo que observa y ademas decide es el lugar donde nadie sabe si una fuente quedo
en alerta porque el documento cambio o porque el descubrimiento se equivoco.

🔴 **Primero la metadata, el documento despues.** Bajar seis PDF en cada corrida para hashear
lo mismo es una llamada de red por documento por sesion. La regla, en orden:

    metadata relevante sin cambios          no se baja nada
    version distinta de la aceptada         no hace falta bajar para decidirlo
    MISMA version, identidad distinta       se baja y se hashea ANTES de resolver

El tercero es el caso en que la metadata no alcanza, y es justo el caso que importa: un
documento reemplazado sin subir la version.

🔴 **La Ficha es de lectura.** Este modulo no transiciona, no comenta, no sube nada y no
borra: el unico verbo que usa es bajar un adjunto, y lo recibe inyectado.

🔴 **El hash es del archivo original.** El markdown del extracto es destilado propio y se
reescribe solo; su hash no dice nada sobre la fuente.
"""
import hashlib
import io
import os
import re

# Cuanto se lee por vez al hashear. Un PDF de la normativa entra en memoria sin drama, pero
# el tamaño lo elige quien sube el archivo y no nosotros.
BLOQUE = 65536

# Como se busca la version en el texto de la Ficha cuando el nombre del archivo no la trae.
# Es una linea explicita -"ES0901: 6.4"-, no una inferencia sobre la prosa.
_EN_FICHA = r"(?im)^[ \t>*-]*%s[ \t]*(?:version|versión)?[ \t]*[:=][ \t]*v?([0-9]+(?:\.[0-9]+)*)[ \t]*$"


def sha256_de(ruta):
    """El SHA-256 del archivo, en minuscula. None si no se pudo leer."""
    h = hashlib.sha256()
    try:
        with io.open(ruta, "rb") as f:
            for bloque in iter(lambda: f.read(BLOQUE), b""):
                h.update(bloque)
    except OSError:
        return None
    return h.hexdigest()


def version_en_nombre(patron, nombre):
    """La version que el nombre del archivo declara, o None.

    Un patron sin grupo de captura vale igual: sirve para reconocer el archivo, y entonces la
    version queda sin resolver. Reconocer el documento y saber su version son dos cosas.
    """
    if not patron or not nombre:
        return None
    try:
        m = re.search(patron, nombre)
    except re.error:
        return None
    if not m or not m.groups():
        return None
    return m.group(1)


def version_en_ficha(texto, sid):
    if not texto or not sid:
        return None
    m = re.search(_EN_FICHA % re.escape(sid), texto)
    return m.group(1) if m else None


def reconoce(entrada, nombre):
    """Si este archivo es el de esta fuente.

    Por el patron declarado, y si no hay patron, porque el nombre nombra al id. Lo que NO se
    hace es adivinar por parecido: un adjunto que nadie pudo reconocer es una fuente que falta,
    y eso se dice.
    """
    if not nombre:
        return False
    patron = entrada.get("filenamePattern")
    if patron:
        try:
            return re.search(patron, nombre) is not None
        except re.error:
            return False
    sid = str(entrada.get("id") or "")
    return bool(sid) and sid.lower() in nombre.lower()


# -- la observacion ------------------------------------------------------------

def _observacion(sid):
    return {"id": sid, "found": False, "attachmentId": None, "filename": None,
            "size": None, "created": None, "observed_version": None,
            "observed_sha256": None, "downloaded": False, "local_path": None,
            "identity_changed": None, "evidence": []}


def _identidad_igual(obs, previo):
    """Si lo observado es el mismo adjunto que la ultima vez, en todo lo que se mira."""
    if not previo:
        return False
    return all(obs.get(campo) == previo.get(campo)
               for campo in ("attachmentId", "filename", "size", "created"))


def hay_que_bajar(entrada, obs, previo):
    """Si hace falta el documento para poder resolver. Devuelve (bool, motivo)."""
    version_registro = entrada.get("version")
    sha_registro = entrada.get("sha256")

    # 🔴 La metadata sin cambios manda, y manda SOLA. La version anterior de esta regla dejaba
    # pasar el caso en que el estado anterior no tenia hash -porque la descarga habia fallado-:
    # ahi caia en la regla del hash aceptado y volvia a bajar el documento TODAS las sesiones,
    # con la metadata sin mover. Reintentar es una decision de alguien, no un efecto de abrir
    # una sesion; mientras tanto la fuente queda sin verificar, que se ve y no miente.
    if _identidad_igual(obs, previo):
        if previo.get("observed_sha256") or sha_registro is None:
            return False, "la metadata del adjunto no cambio: no se baja nada"
        return False, ("la metadata del adjunto no cambio: no se baja nada, y sin hash "
                       "observado la integridad queda sin verificar")

    if (version_registro and obs.get("observed_version")
            and str(obs["observed_version"]) == str(version_registro)
            and not _identidad_igual(obs, previo)):
        return True, ("misma version con identidad de adjunto distinta: se baja y se hashea "
                      "antes de resolver")

    if sha_registro and not obs.get("observed_sha256"):
        return True, "hay un hash aceptado y no hay con que compararlo todavia"

    return False, "la version alcanza para resolver sin bajar el documento"


def observar(entradas, adjuntos, previo=None, bajar=None, dir_descargas=None,
             texto_ficha=""):
    """Una observacion por fuente gestionada. Nunca levanta y nunca imprime.

    `entradas`  las del registro de fuentes que se siguen
    `adjuntos`  la metadata cruda de los adjuntos de la Ficha
    `previo`    el mapa `sources` del estado anterior, para no bajar lo que no cambio
    `bajar`     callable(url, destino) -> (ok, bytes). Sin el, no se baja nada y se dice
    """
    previo = previo or {}
    salida = []
    for entrada in entradas:
        sid = str(entrada.get("id") or "")
        obs = _observacion(sid)
        adjunto = _primer_adjunto(entrada, adjuntos)
        if adjunto is None:
            obs["evidence"].append(
                "no hay ningun adjunto que el registro reconozca como %s" % sid)
            salida.append(obs)
            continue

        obs["found"] = True
        obs["attachmentId"] = _texto_o_none(adjunto.get("id"))
        obs["filename"] = _texto_o_none(adjunto.get("filename"))
        obs["size"] = adjunto.get("size") if isinstance(adjunto.get("size"), int) else None
        obs["created"] = _texto_o_none(adjunto.get("created"))
        obs["evidence"].append("adjunto %s de la Ficha" % (obs["filename"] or "sin nombre"))

        version = version_en_nombre(entrada.get("filenamePattern"), obs["filename"])
        if version:
            obs["evidence"].append("version %s leida del nombre del archivo" % version)
        else:
            version = version_en_ficha(texto_ficha, sid)
            if version:
                obs["evidence"].append("version %s leida de la Ficha" % version)
        obs["observed_version"] = version
        if not version:
            obs["evidence"].append(
                "la version no se pudo resolver: ni el nombre del archivo ni la Ficha la dicen")

        anterior = previo.get(sid) or {}
        # None es "no hay con que comparar", y no es lo mismo que "no cambio": la primera vez
        # que se mira una fuente, nadie sabe si el adjunto es el de ayer.
        obs["identity_changed"] = None if not anterior else not _identidad_igual(obs, anterior)
        if _identidad_igual(obs, anterior) and anterior.get("observed_sha256"):
            obs["observed_sha256"] = anterior["observed_sha256"]

        necesita, motivo = hay_que_bajar(entrada, obs, anterior)
        obs["evidence"].append(motivo)
        if necesita:
            _bajar(obs, adjunto, bajar, dir_descargas)
        salida.append(obs)
    return salida


def observar_archivos(entradas, directorio):
    """El modo local: nombre de archivo y SHA-256 del contenido, sin Jira y sin red."""
    try:
        nombres = sorted(n for n in os.listdir(directorio)
                         if os.path.isfile(os.path.join(directorio, n)))
    except (OSError, ValueError):
        nombres = []

    salida = []
    for entrada in entradas:
        sid = str(entrada.get("id") or "")
        obs = _observacion(sid)
        nombre = next((n for n in nombres if reconoce(entrada, n)), None)
        if nombre is None:
            obs["evidence"].append("no hay ningun archivo que el registro reconozca como %s"
                                   % sid)
            salida.append(obs)
            continue
        ruta = os.path.join(directorio, nombre)
        obs["found"] = True
        obs["filename"] = nombre
        obs["local_path"] = ruta
        try:
            obs["size"] = os.path.getsize(ruta)
        except OSError:
            obs["size"] = None
        obs["observed_version"] = version_en_nombre(entrada.get("filenamePattern"), nombre)
        obs["observed_sha256"] = sha256_de(ruta)
        obs["evidence"].append("archivo local %s" % nombre)
        obs["evidence"].append("sha256 del archivo original")
        if not obs["observed_version"]:
            obs["evidence"].append(
                "la version no se pudo resolver del nombre del archivo")
        salida.append(obs)
    return salida


# -- lo de adentro -------------------------------------------------------------

def _texto_o_none(valor):
    return str(valor) if valor not in (None, "") else None


def _primer_adjunto(entrada, adjuntos):
    """El primero que el registro reconoce, en orden estable por nombre."""
    candidatos = [a for a in (adjuntos or [])
                  if isinstance(a, dict) and reconoce(entrada, str(a.get("filename") or ""))]
    candidatos.sort(key=lambda a: str(a.get("filename") or ""))
    return candidatos[0] if candidatos else None


def _bajar(obs, adjunto, bajar, dir_descargas):
    url = str(adjunto.get("content") or "")
    if bajar is None or not url or not dir_descargas:
        obs["evidence"].append(
            "el documento no se pudo bajar: sin capacidad de lectura de adjuntos, la "
            "integridad de esta fuente queda sin verificar")
        return
    destino = os.path.join(dir_descargas, obs["filename"] or (obs["id"] + ".bin"))
    motivo = ""
    try:
        vuelta = bajar(url, destino)
        ok = bool(vuelta[0])
        # Quien baja puede decir por que no pudo: el tercer elemento. Un `bajar` de dos
        # elementos -los dobles de los tests- sigue andando.
        motivo = str(vuelta[2]) if len(vuelta) > 2 and vuelta[2] else ""
    except OSError:
        ok = False
    if not ok:
        obs["evidence"].append("el documento no se pudo bajar" + (": " + motivo if motivo else ""))
        return
    obs["downloaded"] = True
    obs["local_path"] = destino
    obs["observed_sha256"] = sha256_de(destino)
    obs["evidence"].append("sha256 del archivo original bajado")
