"""Comprueba el scope-guard con la batería del enunciado (2.1) y con casos reales de GitLab.
Uso: .venv/bin/python comprobar_alcance.py   -> imprime tablas Markdown para pruebas.md"""
import sys, tempfile
sys.path.insert(0, "alcance")
from alcance import cargar, en_alcance

EJEMPLO_SCOPE = "*.empresa.com\n!blog.empresa.com\n10.10.0.0/24\n!10.10.0.1\n"
EJEMPLO = [  # (objetivo, esperado, regla que prueba)
    ("api.empresa.com", True, "comodín *.empresa.com"),
    ("https://API.Empresa.com/login", True, "normaliza esquema, mayúsculas y ruta"),
    ("blog.empresa.com", False, "exclusión !blog"),
    ("empresa.com", False, "el comodín no incluye el dominio raíz"),
    ("empresa.com.evil.net", False, "sufijo engañoso"),
    ("otraempresa.com", False, "otra empresa (lista blanca)"),
    ("10.10.0.7", True, "rango 10.10.0.0/24"),
    ("http://10.10.0.7:8080/admin", True, "normaliza puerto y ruta"),
    ("10.10.0.1", False, "IP excluida !10.10.0.1"),
    ("10.10.1.7", False, "IP fuera del rango"),
]
GITLAB = [
    ("gitlab.com", True, "dominio exacto"),
    ("https://Docs.GitLab.com/ee/api/", True, "exacto docs.gitlab.com + normalización"),
    ("dev.gitlab.org", True, "comodín *.gitlab.org"),
    ("ops.gitlab.net", True, "comodín *.gitlab.net"),
    ("gitlab.org", False, "el comodín *.gitlab.org no incluye la raíz"),
    ("www.gitlab.com", False, "no hay *.gitlab.com: solo hosts exactos"),
    ("runway.gitlab.net", False, "exclusión !runway.gitlab.net"),
    ("x.runway.gitlab.net", False, "exclusión !*.runway.gitlab.net gana al comodín"),
    ("support.gitlab.com", False, "exclusión !support.gitlab.com"),
    ("gitlab.com.evil.net", False, "sufijo engañoso"),
    ("evilgitlab.net", False, "parecido pero no es subdominio"),
    ("github.com", False, "otra empresa (lista blanca)"),
]

def tabla(titulo, scope, casos):
    print(f"\n### {titulo}\n")
    print("| Objetivo | Regla que prueba | Esperado | Obtenido | ¿OK? |")
    print("|---|---|---|---|---|")
    fallos = 0
    for obj, esp, regla in casos:
        got = en_alcance(obj, scope)
        ok = got == esp
        fallos += not ok
        f = lambda b: "Dentro" if b else "Fuera"
        print(f"| `{obj}` | {regla} | {f(esp)} | {f(got)} | {'✅' if ok else '❌'} |")
    print(f"\n**{len(casos) - fallos}/{len(casos)} correctos**")
    return fallos

with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as t:
    t.write(EJEMPLO_SCOPE)
fallos = tabla("A) Batería de ejemplo del enunciado", cargar(t.name), EJEMPLO)
fallos += tabla("B) Casos reales de GitLab (scope.txt)", cargar("scope.txt"), GITLAB)
sys.exit(1 if fallos else 0)
