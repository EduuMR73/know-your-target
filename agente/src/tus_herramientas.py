"""Herramientas iniciales de reconocimiento. AQUÍ PUEDES AÑADIR LAS TUYAS.

WHOIS (whois.py), DNS y crt.sh ya están implementadas y activas en lanzar.py.
DNS y crt.sh proceden de la solución del profesor (herramientas/recon.py).

Para ampliar: una tarea por función, @protegida, sin shell, con timeout,
salida recortada, errores como texto y resultados filtrados por el alcance.
Importa tu nueva función en lanzar.py y añádela a HERRAMIENTAS.

Ideas: subdominios_subfinder, wayback_urls, correos (theHarvester / hunter.io),
infraestructura_ip, correo_postura (SPF/DMARC/MTA-STS/CAA), urlscan, shodan_host.
"""

import json
import subprocess
import urllib.parse
import urllib.request

from guard import protegida, filtrar
from whois import recortar

UA = "aap-recon/1.0 (educativo; IES Rafael Alberti)"
TIPOS_DNS = {"A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"}


def _http(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


@protegida(objetivo="dominio")
def dns_registros(dominio: str, tipo: str = "A") -> str:
    """Consulta registros DNS de un dominio. tipo: A, AAAA, MX, NS, TXT, CNAME o SOA.
    Devuelve los valores, uno por línea."""
    tipo = tipo.upper()
    if tipo not in TIPOS_DNS:
        return f"ERROR: tipo DNS no válido ({tipo}). Usa uno de: {', '.join(sorted(TIPOS_DNS))}."
    try:
        r = subprocess.run(["dig", "+short", tipo, dominio],
                           capture_output=True, text=True, timeout=20)
    except subprocess.TimeoutExpired:
        return "ERROR: dig no respondió en 20 segundos."
    except OSError as e:
        return recortar(f"ERROR: no se pudo ejecutar dig: {e}")
    if r.returncode != 0:
        return recortar(f"ERROR: dig falló ({r.returncode}): {r.stderr.strip() or 'sin detalles'}")
    salida = recortar(r.stdout.strip())
    return salida or f"Sin registros {tipo} para {dominio}."


@protegida(objetivo="dominio")
def subdominios_crtsh(dominio: str) -> str:
    """Enumera subdominios de un dominio por transparencia de certificados (crt.sh).
    Pasivo: no toca el objetivo. Devuelve solo los subdominios dentro del alcance."""
    url = f"https://crt.sh/?q=%25.{urllib.parse.quote(dominio)}&output=json"
    try:
        datos = json.loads(_http(url, timeout=90))
    except Exception as e:
        return (f"ERROR: crt.sh no respondió ({e}). crt.sh suele ir lento; "
                "puedes reintentar más tarde o añadir otra fuente de subdominios.")
    if not isinstance(datos, list) or any(
        not isinstance(fila, dict) or not isinstance(fila.get("name_value"), str)
        for fila in datos
    ):
        return "ERROR: crt.sh devolvió un formato de certificados inesperado."
    nombres = set()
    for fila in datos:
        for n in str(fila.get("name_value", "")).splitlines():
            n = n.strip().lstrip("*.").lower()
            if n:
                nombres.add(n)
    dentro, fuera = filtrar(sorted(nombres))
    cab = f"{len(dentro)} subdominios en alcance ({fuera} filtrados por estar fuera):\n"
    return recortar(cab + "\n".join(dentro))


# ===========================================================================
# HERRAMIENTAS PROPIAS · Eduardo Moreno (@EduuMR73) · Know Your Target (GitLab)
# Repiten dos técnicas de la Parte 1: ficheros expuestos e InternetDB.
# ===========================================================================

import ipaddress
import time
import urllib.error

PAUSA_INTERNETDB = 1.5   # segundos entre IP: ritmo bajo (en la Parte 1 saltó el límite)
MAX_IPS = 5              # como mucho 5 IP por dominio: salida corta y pocas peticiones
MAX_BYTES = 20000        # no descargar ficheros enormes


class RedireccionBloqueada(Exception):
    """El servidor intentó mandarnos a un host fuera del alcance."""


class _RedireccionEnAlcance(urllib.request.HTTPRedirectHandler):
    """El scope-guard solo comprueba el argumento de la herramienta. Si el servidor
    responde con una redirección (301/302) a otro host, urllib la seguiría sin
    preguntar: así se podría salir del alcance. Este manejador comprueba cada salto."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        destino = urllib.parse.urlsplit(newurl).hostname or ""
        if not filtrar([destino])[0]:
            raise RedireccionBloqueada(f"HTTP {code} hacia {destino}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_NAVEGADOR = urllib.request.build_opener(_RedireccionEnAlcance)


def _leer_fichero(dominio: str, ruta: str) -> str:
    req = urllib.request.Request(f"https://{dominio}{ruta}", headers={"User-Agent": UA})
    try:
        with _NAVEGADOR.open(req, timeout=20) as r:
            cuerpo = r.read(MAX_BYTES).decode("utf-8", "replace").strip()
            return f"{ruta} -> HTTP {r.status} (URL final: {r.geturl()})\n{cuerpo or '(vacío)'}"
    except RedireccionBloqueada as e:
        return f"{ruta} -> BLOQUEADO: redirección fuera de alcance ({e}). No se siguió."
    except urllib.error.HTTPError as e:
        return f"{ruta} -> HTTP {e.code} ({e.reason}): no disponible o acceso denegado."
    except Exception as e:
        return f"{ruta} -> ERROR: {e}"


@protegida(objetivo="dominio")
def ficheros_expuestos(dominio: str) -> str:
    """Lee robots.txt y /.well-known/security.txt (RFC 9116) de un dominio por HTTPS.
    robots.txt muestra rutas que el dueño no quiere indexar; security.txt, a quién
    avisar de un fallo. Solo sigue redirecciones que estén dentro del alcance."""
    partes = [_leer_fichero(dominio, "/robots.txt"),
              _leer_fichero(dominio, "/.well-known/security.txt")]
    return recortar("\n\n".join(recortar(p, 1400) for p in partes))


def _ips(dominio: str) -> list[str]:
    """IP de los registros A (dig, sin shell). Descarta los CNAME intermedios."""
    r = subprocess.run(["dig", "+short", "A", dominio],
                       capture_output=True, text=True, timeout=20)
    ips = []
    for linea in r.stdout.split():
        try:
            ips.append(str(ipaddress.ip_address(linea)))
        except ValueError:
            pass
    return ips


def _internetdb(ip: str) -> str:
    try:
        d = json.loads(_http(f"https://internetdb.shodan.io/{ip}", timeout=20))
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode("utf-8", "replace")
        if e.code == 429 or "rate" in cuerpo.lower():
            return f"- {ip}: ERROR: límite de peticiones (HTTP {e.code}). NO significa 'sin datos'."
        if e.code == 404:
            return f"- {ip}: SIN DATOS (InternetDB no tiene información de esta IP)."
        return f"- {ip}: ERROR: HTTP {e.code}."
    except Exception as e:
        return f"- {ip}: ERROR: {e}"
    if "detail" in d:  # algunas respuestas de error llegan con 200
        if "rate" in str(d["detail"]).lower():
            return f"- {ip}: ERROR: límite de peticiones. NO significa 'sin datos'."
        return f"- {ip}: SIN DATOS ({d['detail']})."
    hosts, fuera = filtrar(d.get("hostnames", []))
    return (f"- {ip}: puertos {d.get('ports') or 'ninguno'}; "
            f"hostnames en alcance {hosts or 'ninguno'} ({fuera} fuera de alcance omitidos); "
            f"CPE {d.get('cpes') or 'ninguno'}; etiquetas {d.get('tags') or 'ninguna'}; "
            f"CVE que lista Shodan: {len(d.get('vulns', []))} (sin verificar, deducidas por versión)")


@protegida(objetivo="dominio")
def infraestructura_dominio(dominio: str) -> str:
    """Puertos, servicios y CVE que Shodan (InternetDB) ya vio en las IP de un dominio.
    Resuelve el dominio (registros A) y consulta InternetDB por cada IP, sin enviar
    nada al objetivo. Ojo: la IP puede ser de un CDN o de un tercero. Distingue
    'SIN DATOS' de 'ERROR' (p. ej., límite de peticiones)."""
    try:
        ips = _ips(dominio)
    except subprocess.TimeoutExpired:
        return "ERROR: dig no respondió en 20 segundos."
    except OSError as e:
        return recortar(f"ERROR: no se pudo ejecutar dig: {e}")
    if not ips:
        return f"Sin registros A para {dominio}: no hay IP que consultar."
    extra = f" (se consultan las {MAX_IPS} primeras)" if len(ips) > MAX_IPS else ""
    lineas = [f"{dominio} resuelve a {len(ips)} IP{extra}:"]
    for i, ip in enumerate(ips[:MAX_IPS]):
        if i:
            time.sleep(PAUSA_INTERNETDB)
        lineas.append(_internetdb(ip))
    return recortar("\n".join(lineas))
