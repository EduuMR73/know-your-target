"""Pruebas de mis herramientas (ficheros_expuestos, infraestructura_dominio), sin red."""

import io
import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import Mock

import pytest

RAIZ = Path(__file__).parents[1]
for carpeta in ("", "alcance", "motor", "herramientas"):
    sys.path.insert(0, str(RAIZ / carpeta))

import guard
import lanzar
import tus_herramientas as tools


@pytest.fixture(autouse=True)
def scope(monkeypatch):
    monkeypatch.setattr(guard, "SCOPE", (["gitlab.com", "*.gitlab.net"], ["*.runway.gitlab.net"]))
    monkeypatch.setattr(tools.time, "sleep", lambda s: None)


def test_mis_herramientas_estan_activas_y_protegidas():
    nombres = [h.__name__ for h in lanzar.HERRAMIENTAS]
    for h in (tools.ficheros_expuestos, tools.infraestructura_dominio):
        assert h.__name__ in nombres
        assert getattr(h, "protegida", False)


@pytest.mark.parametrize("herramienta", [tools.ficheros_expuestos, tools.infraestructura_dominio])
@pytest.mark.parametrize("dominio", ["github.com", "x.runway.gitlab.net"])
def test_fuera_de_alcance_bloquea_sin_tocar_la_red(monkeypatch, herramienta, dominio):
    prohibido = Mock(side_effect=AssertionError("No debe salir a la red ni ejecutar nada"))
    monkeypatch.setattr(tools.subprocess, "run", prohibido)
    monkeypatch.setattr(tools, "_http", prohibido)
    monkeypatch.setattr(tools._NAVEGADOR, "open", prohibido)
    assert herramienta(dominio=dominio).startswith("BLOQUEADO")


def test_redireccion_fuera_de_alcance_se_bloquea():
    manejador = tools._RedireccionEnAlcance()
    with pytest.raises(tools.RedireccionBloqueada):
        manejador.redirect_request(Mock(), None, 302, "Found", {}, "https://evil.com/robots.txt")


def test_ficheros_expuestos_informa_redireccion_bloqueada(monkeypatch):
    monkeypatch.setattr(tools._NAVEGADOR, "open",
                        Mock(side_effect=tools.RedireccionBloqueada("HTTP 301 hacia evil.com")))
    salida = tools.ficheros_expuestos(dominio="gitlab.com")
    assert salida.count("BLOQUEADO: redirección fuera de alcance") == 2


def _dig(stdout):
    return Mock(return_value=Mock(stdout=stdout, returncode=0, stderr=""))


def test_infraestructura_filtra_hostnames_y_descarta_cname(monkeypatch):
    monkeypatch.setattr(tools.subprocess, "run", _dig("cdn.algo.net.\n1.2.3.4\n"))
    respuesta = {"ports": [443], "hostnames": ["gitlab.com", "otro.ajeno.com"],
                 "cpes": [], "tags": ["cdn"], "vulns": ["CVE-1", "CVE-2"]}
    monkeypatch.setattr(tools, "_http", Mock(return_value=json.dumps(respuesta)))
    salida = tools.infraestructura_dominio(dominio="gitlab.com")
    assert "resuelve a 1 IP" in salida
    assert "['gitlab.com']" in salida and "otro.ajeno.com" not in salida
    assert "1 fuera de alcance omitidos" in salida and "CVE que lista Shodan: 2" in salida


def test_infraestructura_distingue_limite_de_sin_datos(monkeypatch):
    monkeypatch.setattr(tools.subprocess, "run", _dig("1.1.1.1\n2.2.2.2\n"))

    def falso_http(url, timeout=30):
        codigo, cuerpo = ((429, b'{"detail":"Rate limit exceeded"}') if "1.1.1.1" in url
                          else (404, b'{"detail":"No information available"}'))
        raise urllib.error.HTTPError(url, codigo, "x", {}, io.BytesIO(cuerpo))

    monkeypatch.setattr(tools, "_http", falso_http)
    salida = tools.infraestructura_dominio(dominio="gitlab.com")
    assert "1.1.1.1: ERROR: límite de peticiones" in salida
    assert "2.2.2.2: SIN DATOS" in salida


def test_infraestructura_limita_numero_de_ips(monkeypatch):
    monkeypatch.setattr(tools.subprocess, "run", _dig("\n".join(f"10.0.0.{i}" for i in range(9))))
    http = Mock(return_value=json.dumps({"ports": [], "hostnames": []}))
    monkeypatch.setattr(tools, "_http", http)
    salida = tools.infraestructura_dominio(dominio="gitlab.com")
    assert http.call_count == tools.MAX_IPS and "se consultan las 5 primeras" in salida
