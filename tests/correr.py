# tests/correr.py — sin dependencias: no hace falta pytest ni nada instalado.
import argparse, importlib.util, sys, traceback
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


class Resultados:
    def __init__(self):
        self.filas = []          # (grupo, nombre, ok, detalle)
        self.grupo = "(sin grupo)"

    def _add(self, nombre, ok, detalle=""):
        self.filas.append((self.grupo, nombre, ok, detalle))

    def igual(self, nombre, esperado, obtenido):
        self._add(nombre, esperado == obtenido,
                  "" if esperado == obtenido else "esperado <%r> / obtenido <%r>" % (esperado, obtenido))

    def contiene(self, nombre, aguja, pajar):
        self._add(nombre, aguja in (pajar or ""), "" if aguja in (pajar or "") else "no contiene <%s>" % aguja)

    def no_contiene(self, nombre, aguja, pajar):
        self._add(nombre, aguja not in (pajar or ""), "" if aguja not in (pajar or "") else "contiene <%s>" % aguja)

    def vacio(self, nombre, valor):
        self._add(nombre, not valor, "" if not valor else "no esta vacio: <%r>" % (valor,))

    def verdadero(self, nombre, condicion):
        self._add(nombre, bool(condicion), "" if condicion else "es falso")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-k", default="")
    ap.add_argument("--detallado", action="store_true")
    args = ap.parse_args()

    t = Resultados()
    casos = sorted((RAIZ / "tests" / "casos").glob("*.py"))
    if args.k:
        casos = [c for c in casos if args.k in c.name]

    for caso in casos:
        t.grupo = caso.stem
        spec = importlib.util.spec_from_file_location("caso_" + caso.stem, caso)
        modulo = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(modulo)
        except Exception:
            t._add("el archivo de casos se pudo cargar", False, traceback.format_exc(limit=3))
            continue
        for nombre in sorted(dir(modulo)):
            if not nombre.startswith("test_"):
                continue
            try:
                getattr(modulo, nombre)(t)
            except Exception:
                t._add(nombre, False, traceback.format_exc(limit=3))

    fallaron = [f for f in t.filas if not f[2]]
    grupos = {}
    for grupo, nombre, ok, detalle in t.filas:
        g = grupos.setdefault(grupo, [0, 0])
        g[0] += 1
        if ok:
            g[1] += 1
    print("\ngcba-harness - tests (python)\n")
    for grupo, (total, ok) in grupos.items():
        estado = "OK   " if total == ok else "FALLA"
        print("  %s %s  (%d)" % (estado, grupo, total))
    for grupo, nombre, ok, detalle in t.filas:
        if not ok or args.detallado:
            print("    %s %s / %s %s" % ("ok " if ok else "MAL", grupo, nombre, detalle))
    print("\n%d/%d pasaron." % (len(t.filas) - len(fallaron), len(t.filas)))
    sys.exit(1 if fallaron else 0)


if __name__ == "__main__":
    main()
