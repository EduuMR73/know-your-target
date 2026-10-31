"""Cruce de InternetDB (Shodan) con los subdominios resueltos (técnica 5).

Para cada IP consultada en InternetDB dice qué subdominios de GitLab
apuntan a ella (según resueltos.txt) y qué ve Shodan: puertos, CPE,
nombres de host y CVE. Sirve para detectar IP compartidas con terceros
(los nombres de host de Shodan que no son de GitLab).

Uso (desde la carpeta evidencias/):
    python -I scripts/cruce_internetdb.py
"""
import json
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DOMINIOS_GITLAB = ("gitlab.com", "gitlab.net", "gitlab.org", "gitlap.com")

# resueltos.txt: "subdominio -> [cname.] ip ip ..."
ip_a_subdominios = defaultdict(list)
for linea in (BASE / "resueltos.txt").read_text(encoding="utf-8").splitlines():
    if " -> " not in linea:
        continue
    sub, destinos = linea.split(" -> ", 1)
    for d in destinos.split():
        if not d.endswith("."):  # los CNAME acaban en punto; las IP no
            ip_a_subdominios[d].append(sub)

for f in sorted((BASE / "internetdb").glob("*.json")):
    datos = json.loads(f.read_text(encoding="utf-8"))
    if "error" in datos:  # {"error": "Rate limit exceeded..."}: NO se consultó
        print(f"{f.stem}: ERROR de InternetDB ({datos['error'][:30]}...) -> repetir")
        continue
    if "ip" not in datos:  # {"detail": "No information available"}
        print(f"{f.stem}: sin datos en InternetDB")
        continue
    ajenos = [h for h in datos.get("hostnames", [])
              if not h.endswith(DOMINIOS_GITLAB) and "amazonaws.com" not in h
              and "googleusercontent.com" not in h]
    print(f"{datos['ip']}")
    print(f"  subdominios GitLab: {', '.join(ip_a_subdominios.get(datos['ip'], ['?']))}")
    print(f"  puertos: {len(datos.get('ports', []))} -> {datos.get('ports', [])[:10]}")
    print(f"  cpe: {', '.join(datos.get('cpes', []))}")
    print(f"  CVE: {len(datos.get('vulns', []))} · tags: {', '.join(datos.get('tags', []))}")
    if ajenos:
        print(f"  ¡OJO! nombres de host AJENOS a GitLab: {', '.join(ajenos)}")
