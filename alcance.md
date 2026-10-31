# Alcance · GitLab Bug Bounty

## Programa

| Campo | Valor |
|---|---|
| Organización | GitLab Inc. |
| Programa | GitLab Bug Bounty (bug bounty con recompensa, no VDP) |
| Plataforma | HackerOne |
| Política | https://hackerone.com/gitlab?type=team |
| Alcance | https://hackerone.com/gitlab/policy_scopes?type=team |
| Fecha de consulta | 2026-10-28 |
| Última actualización de la política | 2026-10-05 |
| Última actualización del alcance | 2026-05-27 |
| Estado | Activo (último informe resuelto hace 2 días, sin aviso de pausa) |
| Safe Harbor | Gold Standard Safe Harbor |

## Dentro del alcance

### Comodines

| Activo | Descripción del programa |
|---|---|
| `*.gitlab.net` | Hosts propiedad de GitLab y operados por GitLab |
| `*.gitlab.org` | Hosts propiedad de GitLab y operados por GitLab |
| `*.gitlap.com` | Hosts propiedad de GitLab ("gitlap con p") |

### Dominios concretos

| Activo | Notas |
|---|---|
| `gitlab.com` | La aplicación principal (GCP, Rails) |
| `registry.gitlab.com` | Registro de contenedores |
| `customers.gitlab.com` | Portal de clientes. El DoS de servidor queda fuera |
| `about.gitlab.com` | Web estática, sin datos de usuario |
| `docs.gitlab.com` | Documentación, sin datos de usuario |
| `design.gitlab.com` | Sistema de diseño, sin datos de usuario |
| `advisories.gitlab.com` | Avisos de seguridad, sin datos de usuario |

### Otros activos (no son dominios, no van a `scope.txt`)

- Código fuente: `gitlab-org/gitlab`, `gitaly`, `gitlab-pages`, `gitlab-runner`, `gitlab-shell`, `gitlab-vscode-extension`.
- *Your Own GitLab Instance*: una instalación propia.
- *GitLab for Jira Cloud*.
- *Other non-production infrastructure*: "hosts propiedad de GitLab y operados por GitLab, distintos de gitlab.com y de las webs estáticas". No da una lista concreta.

## Fuera del alcance

### Comodines

| Activo | Motivo |
|---|---|
| `*.runway.gitlab.net` | Excluido explícitamente, **aunque esté dentro de `*.gitlab.net`** |
| `*.gitlab-private.org` | Excluido |
| `*.gitlab.cn` | Propiedad de JiHu (otra empresa); se informa a `security@gitlab.cn` |
| `*.service-now.com` | Plataforma ServiceNow de terceros |

### Dominios concretos

`alerts.gitlab.com`, `aptly.gitlab.com`, `dashboards.gitlab.com`, `federal-support.gitlab.com`, `forum.gitlab.com`, `ir.gitlab.com`, `levelup.gitlab.com`, `packages.gitlab.com`, `partners.gitlab.com`, `shop.gitlab.com`, `status.gitlab.com`, `support.gitlab.com`, `translate.gitlab.com`, `us-federal-gitlab.com`, `gitlab.biterg.io`, `gitlabdemo.cloud`, `gitlabsandbox.net`, `gitlabtraining.cloud`.

### Código fuente excluido

`gitlab-org/cli`, `gitlab-org/opstrace/opstrace`, `gitlab-org/opstrace/opstrace-ui`.

### Exclusiones por tipo (de la política)

- **Subdominios de GitLab que ejecutan servicios de terceros**: "strictly out of scope", aunque el nombre sea `*.gitlab.com` o esté bajo un comodín (por ejemplo, un CNAME a un servicio de marketing, de correo o de soporte).
- Instalaciones de GitLab de clientes.
- Contenido de usuarios en GitLab.com.
- Información y hosts intencionadamente públicos.

## Decisiones de interpretación

1. **Los subdominios de `gitlab.com` no tienen comodín.** Solo entran los siete que el programa lista uno por uno. La política dice que probar subdominios "ni explícitamente dentro ni fuera" *"isn't encouraged"*, así que los trato como **fuera de alcance**. Si aparecen en el reconocimiento, se anotan en el mapa pero no se investigan.
2. **Un comodín no incluye el dominio raíz.** `*.gitlab.net` cubre `x.gitlab.net`, pero no `gitlab.net`. Sigo el mismo criterio que la tabla de ejemplo del enunciado (`*.empresa.com` → `empresa.com` fuera), y además el programa no lista esos dominios raíz.
3. **Un subdominio dentro de un comodín que apunte a un tercero queda fuera.** Lo compruebo al resolver cada subdominio (CNAME, whois de la IP) antes de marcarlo como "en alcance" en el mapa.
4. **El alcance de código fuente** (`gitlab.com/gitlab-org/...`) se distingue por ruta, no por dominio, así que no se puede expresar en `scope.txt`. En este proyecto no se analizan repositorios.
5. **"Other non-production infrastructure"** no es una lista concreta: no se añade a `scope.txt`.
6. **`runway.gitlab.net` (la raíz) también se excluye.** El comodín `!*.runway.gitlab.net` no cubre la raíz, que sí entraría por `*.gitlab.net`. La política excluye "*.runway.gitlab.net endpoints" y la raíz es ambigua, así que se añade `!runway.gitlab.net` por criterio conservador. Detectado al leer `alcance/alcance.py` de aap-base (2026-10-28).

## Reglas del programa que afectan a este proyecto

| Pregunta | Respuesta del programa | Qué hago yo |
|---|---|---|
| ¿Permite herramientas automáticas? | No las prohíbe, pero los "Automated scanning reports" quedan fuera y enviar informes de herramientas sin verificar descalifica | Solo herramientas pasivas (fuentes de terceros); todo resultado se verifica a mano |
| ¿Límite de peticiones? | No fija un número, pero prohíbe la "Spam-like or other high volume activity" y cualquier actividad disruptiva; el DoS se prohíbe expresamente en GitLab.com | Ritmo bajo; las consultas van a fuentes públicas (crt.sh, InternetDB…), no a GitLab |
| ¿Prohíbe contactar con empleados? | Sí: saltarse el triaje contactando con miembros del equipo viola el Code of Conduct. La ingeniería social y el phishing quedan fuera | Ningún contacto con personas |
| ¿Requisito de identificación? | Las cuentas de prueba en GitLab.com deben usar el alias `@wearehackerone.com`, y hay que anotar las IP usadas | No creo cuentas (regla del proyecto). Anoto mi IP pública en el cuaderno por buena práctica |
| ¿Credenciales filtradas? | No usarlas para crear accesos nuevos | Si aparecen: se anotan sin el dato, se avisa al profesor y no se usan |
| ¿Divulgación? | Informes resueltos públicos 90 días después del parche | No aplica (no se envía ningún informe) |

## Reglas del proyecto (más estrictas que las del programa)

- Solo técnicas pasivas: nada de escaneo de puertos, escáneres de vulnerabilidades ni fuerza bruta.
- Ninguna interacción con personas.
- No crear cuentas en servicios de GitLab.
- Ante un hallazgo grave (credenciales, panel expuesto, datos personales): no explotarlo ni copiarlo, anotarlo sin el dato sensible y avisar al profesor.
