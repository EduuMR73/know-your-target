"""Lanza el agente de reconocimiento.

    # Clave con límite de gasto puesto en el proveedor, en el entorno o en .env:
    echo 'AAP_API_KEY=...' > .env && chmod 600 .env      # y AAP_URL si no es OpenRouter
    python lanzar.py "Investiga empresa.com"
"""

import argparse
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).parent
for carpeta in ("alcance", "motor", "herramientas"):
    sys.path.insert(0, str(RAIZ / carpeta))

from agente import Agente, LimiteAlcanzado  # noqa: E402
from alcance import cargar                  # noqa: E402
from modelo import Modelo                   # noqa: E402
from prompt import construir                # noqa: E402
from traza import Traza                     # noqa: E402
from whois import whois_dominio             # noqa: E402
from tus_herramientas import dns_registros, subdominios_crtsh, ficheros_expuestos, infraestructura_dominio  # noqa: E402

# A medida que construyas tus herramientas en herramientas/tus_herramientas.py,
# impórtalas aquí y añádelas a la lista. Por ejemplo:
#   from tus_herramientas import subdominios_subfinder

HERRAMIENTAS = [
    whois_dominio,
    dns_registros,
    subdominios_crtsh,
    ficheros_expuestos,        # propia: robots.txt + security.txt
    infraestructura_dominio,   # propia: dig + InternetDB
]


def cargar_env(ruta: Path) -> None:
    """Lee CLAVE=valor de .env sin pisar lo que ya esté en el entorno."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if "=" in linea and not linea.lstrip().startswith("#"):
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip().strip("\"'"))


def main():
    cargar_env(RAIZ / ".env")
    p = argparse.ArgumentParser()
    p.add_argument("objetivo", nargs="?", help="lo que le pides al agente")
    p.add_argument("--modelo", default=os.environ.get("AAP_MODELO", "openai/gpt-4o-mini"))
    p.add_argument("--max-pasos", type=int, default=15)
    p.add_argument("--max-tokens", type=int, default=60_000)
    p.add_argument("--ver-prompt", action="store_true",
                   help="muestra el prompt de sistema ya montado y sale (no llama al modelo)")
    a = p.parse_args()

    scope = cargar(RAIZ / "scope.txt")
    plantilla = (RAIZ / "instrucciones.md").read_text(encoding="utf-8")
    instrucciones = construir(plantilla, scope, HERRAMIENTAS)

    if a.ver_prompt:
        print(instrucciones)
        return
    if not a.objetivo:
        p.error("falta el objetivo (o usa --ver-prompt para ver el prompt)")

    agente = Agente(
        modelo=Modelo(a.modelo),
        instrucciones=instrucciones,
        herramientas=HERRAMIENTAS,
        scope=scope,
        traza=Traza(RAIZ / "salida" / "traza.jsonl"),
        max_pasos=a.max_pasos,
        max_tokens=a.max_tokens,
    )
    try:
        informe = agente.ejecutar(a.objetivo)
    except LimiteAlcanzado as e:
        print(f"Parado: {e}", file=sys.stderr)
        sys.exit(1)
    (RAIZ / "salida" / "informe.md").write_text(informe, encoding="utf-8")
    print(informe)
    print(f"\nTokens: {agente.tokens}", file=sys.stderr)


if __name__ == "__main__":
    main()
