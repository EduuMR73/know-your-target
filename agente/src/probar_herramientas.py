"""Prueba manual de las herramientas (2.2): fuera de alcance -> BLOQUEADO; dentro -> algo útil."""
import sys
for c in ("alcance", "motor", "herramientas"):
    sys.path.insert(0, c)
from alcance import cargar
from guard import fijar_scope
import lanzar
from tus_herramientas import ficheros_expuestos, infraestructura_dominio

fijar_scope(cargar("scope.txt"))
print("=== FUERA de alcance: las 5 herramientas ===")
for h in lanzar.HERRAMIENTAS:
    for d in ("support.gitlab.com", "github.com"):
        print(f"{h.__name__}(dominio={d!r}) -> {h(dominio=d)}")
print("\n=== DENTRO: ficheros_expuestos(about.gitlab.com) ===")
print(ficheros_expuestos(dominio="about.gitlab.com"))
print("\n=== DENTRO: infraestructura_dominio(dev.gitlab.org) ===")
print(infraestructura_dominio(dominio="dev.gitlab.org"))
