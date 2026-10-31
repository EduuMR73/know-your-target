# Know Your Target · GitLab

Proyecto 1 de la unidad **UD1 · Eyes on Target** (Hacking Ético). Mapa de la superficie de ataque de un objetivo real usando **solo técnicas pasivas**, y comparación con un agente de IA.

- **Autor:** Eduardo Moreno Rodríguez ([@EduuMR73](https://github.com/EduuMR73))
- **Objetivo:** programa de bug bounty de **GitLab** en HackerOne — <https://hackerone.com/gitlab>
- **Fechas de reconocimiento:** del 28/10/2026 al 31/10/2026
- **Herramienta de clasificación de alcance:** `scope-guard` de `aap-base` (misma que usa el agente)

## Por qué GitLab

Programa **público y activo**, con **alcance amplio por comodines** (`*.gitlab.net`, `*.gitlab.org`, `*.gitlap.com`) en vez de un solo dominio, y con exclusiones interesantes (`*.runway.gitlab.net`, servicios de terceros) que obligan a interpretar el alcance con cuidado. Mozilla estaba en pausa y Amazon tenía un alcance ambiguo. Detalle en [`cuaderno.md`](cuaderno.md) (Fase 0).

## Contenido del repositorio

| Documento | Qué es |
|---|---|
| [`alcance.md`](alcance.md) | El programa, las reglas que afectan al proyecto y **6 decisiones de interpretación** del alcance |
| [`scope.txt`](scope.txt) | El alcance como lista (lo que usa el `scope-guard`): 3 comodines + 7 dominios dentro, exclusiones fuera |
| [`cuaderno.md`](cuaderno.md) | Cuaderno de trabajo: cada acción con hora (UTC), comando, resultado, **por qué importa** y siguiente paso |
| [`mapa.md`](mapa.md) | El mapa de superficie de ataque: resumen, dominios y subdominios, infraestructura, correos y **3 puntos de interés** |
| [`evidencias/`](evidencias/) | Salidas en bruto que respaldan cada dato del mapa |

### Dentro de `evidencias/`

| Fichero | Contenido |
|---|---|
| `resueltos.txt` | Los 247 subdominios vivos con su IP |
| `ip_asn.txt` | Propietario (ASN) de cada IP pública |
| `internetdb/` | Respuestas de Shodan InternetDB por IP |
| `ficheros/` | `robots.txt` y `security.txt` de los sitios en alcance |
| `scripts/` | Script del cruce IP ↔ subdominio ([`cruce_internetdb.py`](evidencias/scripts/cruce_internetdb.py)) |

## Las 8 técnicas de reconocimiento pasivo

Todas documentadas en [`cuaderno.md`](cuaderno.md), cada una con su "por qué importa":

1. **Registro del dominio** — RDAP (el lab bloquea el puerto 43 de whois)
2. **Registros DNS** — `dig`: MX de Google, DMARC `reject`, 32 TXT
3. **Subdominios** — subfinder + crt.sh → 2974 → 247 vivos en alcance
4. **Huella tecnológica** — ASN (Team Cymru) + Netcraft
5. **Servicios expuestos** — Shodan InternetDB (incluye un falso positivo de 82 CVE demostrado)
6. **Ficheros expuestos** — `robots.txt` y `security.txt`
7. **Google dorks** — 8 búsquedas
8. **Correos** — theHarvester + Hunter.io (patrón `{f}{last}`)

## Metodología

- **Solo técnicas pasivas:** todas las consultas van a **fuentes públicas de terceros** (crt.sh, InternetDB, Netcraft…), nunca al objetivo. No se escanean puertos, no se interactúa con personas, no se crean cuentas.
- **Cada dato con su "por qué importa"** y **trazable**: en `mapa.md`, la etiqueta `[T<n> · hora]` remite a la entrada del cuaderno de esa técnica.
- **Reconocimiento hecho en un laboratorio Kali**; las evidencias se trajeron a este repositorio.

---

> Parte 2 (First Agent) y Parte 3 (análisis comparativo): en curso.
