# Mapa de superficie de ataque · GitLab

> Reconocimiento **pasivo** del programa de bug bounty de GitLab en HackerOne, del 2026-10-28 al 2026-10-31.
> Alcance en [`alcance.md`](alcance.md) y [`scope.txt`](scope.txt). Cada dato remite a su entrada del [`cuaderno.md`](cuaderno.md) con la referencia **[T*n* · hora UTC]** (*n* = número de técnica). Las salidas en bruto están en [`evidencias/`](evidencias/).

---

## 1. Resumen

**GitLab Inc.** (EE. UU.) opera su plataforma de forma **multinube con Google Cloud como base** (46 % de las IP), **Cloudflare** como proxy y WAF delante de lo público (45 %) y un uso acotado de **AWS** (9 %). El correo y la identidad de los empleados están en **Google Workspace**, con **DMARC en `reject`** (no se puede suplantar @gitlab.com desde fuera) y herramientas internas tras **Okta**. El alcance real del programa vive casi entero en los **comodines** (`*.gitlab.net` sobre todo): de gitlab.com solo entran 7 nombres listados uno a uno (la raíz y 6 subdominios).

**Lo más relevante encontrado:**
- Dos niveles de exposición: lo público y lo crítico está **protegido tras Cloudflare**, pero muchos **entornos de desarrollo, versiones y pruebas** (dev.gitlab.org, `*.env.release`, `*.testbed`, ops) están en **Google Cloud directo y con SSH abierto a internet**, saltándose Teleport, que es su acceso oficial de administradores.
- **customers.gitlab.com** concentra el mayor valor: pagos, facturación, login por enlace mágico y un panel `/admins/`.
- Varias **fugas de información interna** en fuentes públicas: IP privadas en el DNS, un listado de directorios abierto en preproducción y documentación interna indexada.
- Buena higiene general: 0 ficheros sensibles en los dorks, security.txt firmado, cabeceras de seguridad completas.
- **Dos trampas evitadas:** las "82 CVE" que Shodan atribuía a GitLab eran de un tercero que compartía una IP de balanceador de AWS, y Netcraft daba DNSSEC como activado cuando `dig` demostró que no lo está. **Ningún dato de una fuente se da por bueno sin contrastarlo.**

De aquí salen los **3 puntos de interés** de la sección 5.

---

## 2. Dominios y subdominios

**De dónde salen.** Con subfinder y crt.sh se reunieron **2974** nombres únicos. El mismo `scope-guard` que usará el agente los clasificó en **2132 dentro** y **842 fuera** del alcance [T3 · 12:10]. De los de dentro se apartaron **1084 review apps**: entornos efímeros que se crean por cada merge request [T3 · 12:12–12:14]. De los **1048** restantes, **247 resuelven** en DNS [T3 · 12:17]. El mapa se construye con esos 247: el 76 % de los nombres no resuelve, porque son históricos de crt.sh o solo internos.

**Cómo leer la tabla.**
- *En alcance* = dentro por nombre (scope-guard) **y** sin apuntar a un servicio de terceros (decisión 3 de `alcance.md`).
- *Protección* = **Cloudflare** si la IP es de Cloudflare (proxy + WAF, origen oculto) o **directo** si la IP es de Google Cloud o de AWS sin ese escudo [T4 · 12:29].
- Las familias con muchos nombres se agrupan en una fila. La lista completa de los 247, con su IP, está en [`evidencias/resueltos.txt`](evidencias/resueltos.txt).

### 2.1 Dominios del programa listados uno a uno

| Subdominio | IP | En alcance | Protección | Para qué parece servir | Cuaderno |
|---|---|---|---|---|---|
| gitlab.com | 172.65.251.78 | Sí | Cloudflare | La aplicación principal (SaaS). Titular "GitLab Inc." según Netcraft | [T2 · 11:56] [T4 · 12:38] |
| registry.gitlab.com | 35.227.35.254 | Sí | **Directo (GCP)** | Registro de contenedores. Shodan: solo 80/443, sin CVE | [T3 · 12:17] [T5 · 31/10 17:34] |
| customers.gitlab.com | 104.18.39.11 | Sí | Cloudflare | Portal de clientes: suscripciones, pagos, facturas. Login con enlace mágico por correo. `robots.txt` oculta `/admins/` | [T6 · 12:46] [T7 · 12:53] |
| about.gitlab.com | 104.18.28.129 | Sí | Cloudflare | Web corporativa (Nuxt / Vue.js) | [T6 · 12:46] [T4 · 12:38] |
| docs.gitlab.com | 104.18.9.44 | Sí | Cloudflare | Documentación del producto | [T3 · 12:17] |
| design.gitlab.com | 35.185.44.232 | Sí | GitLab Pages | Sistema de diseño (CNAME a gitlab-org.gitlab.io) | [T3 · 12:17] [T6 · 12:46] |
| advisories.gitlab.com | 35.185.44.232 | Sí | GitLab Pages | Avisos de seguridad (CNAME a pages.gitlab.io) | [T3 · 12:17] [T6 · 12:46] |

### 2.2 Subdominios bajo los comodines `*.gitlab.net`, `*.gitlab.org` y `*.gitlap.com`

| Subdominio (o familia) | IP | En alcance | Protección | Para qué parece servir | Cuaderno |
|---|---|---|---|---|---|
| **dev.gitlab.org** | 34.139.135.192 | Sí | **Directo (GCP)** | Instancia GitLab CE de desarrollo con login de Google. Shodan: SSH 22, 80, 443 y 5005. Confirmado por 3 técnicas | [T5 · 12:41] [T6 · 12:46] [T7 · 12:53] |
| **ops.gitlab.net** | 172.65.19.90 | Sí | Cloudflare | "Internal GitLab for Operations": instancia GitLab interna de operaciones | [T3 · 12:17] [T7 · 12:53] |
| **kas.ops / registry.ops.gitlab.net** | 35.238.98.95 | Sí | **Directo (GCP)** | Agente de Kubernetes y registro de la instancia de operaciones. Shodan: **SSH 22** | [T5 · 31/10 17:34] |
| **gitlab.\*-stable-security-get.env.release.gitlab.net** (7) + custom-models-online/offline (2) | 34.179.141.159, 136.92.0.142… | Sí | **Directo (GCP)** | Instancias GitLab por versión (18-11 a 19-5). **SSH abierto en 6 de las 9** | [T3 · 12:17] [T5 · 12:41] [T5 · 31/10 17:34] |
| **\*.testbed.gitlab.net** (14) | 34.73.165.75, 35.196.18.43… | Sí | **Directo (GCP y AWS)** | Arquitecturas de referencia (1k, 2k, 10k, 50k e híbridas en AWS). SSH en 22 y 2222 | [T3 · 12:17] [T5 · 31/10 17:34] |
| policy-framework-preview.gitlab.net | 34.63.12.103 | Sí | **Directo (GCP)** | Instancia GitLab de vista previa (Ubuntu). SSH 22 | [T5 · 31/10 17:34] |
| argocd, vault, sentry, new-sentry, log, dashboards, portal, static-objects, mimir-us-east1, pulp.pre… (21) | 104.18.40.188 / 172.64.147.68 | Sí | Cloudflare | Herramientas internas detrás de la **misma** puerta de Cloudflare: despliegue (Argo CD), secretos (Vault), errores (Sentry), métricas | [T3 · 12:17] |
| pulp.pre.gitlab.net | 104.18.40.188 | Sí | Cloudflare | Repositorio de paquetes de preproducción con **listado de directorios abierto** | [T7 · 12:53] |
| production.teleport.gitlab.net · staging.teleport | 34.27.152.121 · 35.243.149.188 | Sí | Directo (GCP) | Teleport: puerta de acceso de los administradores. Producción: solo 443 | [T3 · 12:17] [T5 · 12:41] |
| atlantis-\*.ops.gke.gitlab.net (8) | 34.160.239.33 | Sí | Directo (GCP) | Atlantis: automatización de Terraform (infraestructura como código) | [T3 · 12:17] |
| alertmanager-0/1/2.ops.gke · mimir.ops/pre.gke · promlens · grafana.northstar.autoflow | 34.102.202.123, 34.160.8.21… | Sí | Directo (GCP) | Monitorización y alertas. promlens y grafana.northstar: balanceadores con cientos de puertos (artefacto) | [T3 · 12:17] [T5 · 12:41] |
| log.gprd · log.pre · nonprod-log · monitoring-log | 34.149.206.63, 34.98.99.198 | Sí | Directo (GCP) | Logs. log.gprd = Kibana / Elastic con login de **Okta** (visto en Google); los otros, por el nombre | [T7 · 12:53] |
| \*.svc.gitlab.net (25) | 104.18.x.x | Sí | Cloudflare | Microservicios de la plataforma (AI gateway, IAM, feature flags, catálogo, gestor de secretos…), en variantes GKE y EKS | [T3 · 12:17] |
| \*.secauto-dev / \*.secauto-live.sec.gitlab.net (47 + 23) | 34.123.229.196 · 34.70.71.242 | Sí | Directo (GCP) | Automatización del equipo de seguridad (h1bot, h1-import, h1-attachments para sus informes de HackerOne). Los mismos servicios en desarrollo y en producción | [T3 · 12:17] |
| corpsec-\* (8) + api.corpsecdevices | 34.50.155.139, 34.102.251.100… | Sí | Directo (GCP) | Gestión de equipos corporativos: munki (macOS), PKI, VDI, flota. Cuadra con los TXT de Jamf y Apple | [T2 · 11:56] [T3 · 12:17] |
| theseus.gitlab.net | 35.185.44.232 | Sí | GitLab Pages | Documentación de la plataforma interna de desarrollo (nombres de herramientas, arquitectura) | [T7 · 12:53] |
| events / snowplow\*.trx.gitlab.net (5) | IP de ELB de AWS (18.219.104.126…) | Sí | **ELB de AWS compartido** | Colector de analítica Snowplow. Las IP de ELB se **reutilizan entre clientes**: 4 terceros vistos en ellas | [T5 · 12:41] [T5 · 31/10 17:34] |
| comp-calculator · conservatory · nominatorbot | 34.138.170.206 | Sí | Directo (GCP) | Herramientas internas con **certificado autofirmado** | [T5 · 12:41] |
| version-production / version-staging.gitlab.org (4) | 35.190.167.255 · 34.73.118.39 | Sí | Directo (GCP) | Servicio "GitLab - Versions" (login) | [T7 · 12:53] |
| api.gitlab.org · www.gitlab.org | 188.114.96.5 | Sí | Cloudflare | Web y API del dominio .org (por el nombre, sin confirmar) | [T3 · 12:17] |
| vault / mimir-gateway-private / apt-mirror / zoekt (.ops, .pre, .gprd, .gstg .gke) (8) | **10.216.x · 10.224.x · 10.250.x · 10.232.x** | Sí (no alcanzables) | IP privada | **El DNS público publica IP internas** (RFC 1918), una red por entorno | [T3 · 12:17] |
| opencti / openbas (.cti.sec) (4) | 34.49.10.178 | **No (dudoso)** | Directo (GCP) | Software de inteligencia de amenazas de terceros, autoalojado. Fuera por criterio conservador | [T3 · 12:17] |
| Entornos personales (\*-dev, \*-test con alias de personas) | varias | Sí | Cloudflare / GCP | Pruebas de empleados. Se anota el patrón, sin publicar nombres | [T3 · 12:14] |

### 2.3 Fuera de alcance (vistos, pero no se tocan)

| Subdominio (o familia) | Destino | Por qué está fuera | Cuaderno |
|---|---|---|---|
| \*.runway.gitlab.net (244 + la raíz) | — | Excluido expresamente por el programa (decisión 6 para la raíz) | [T3 · 12:12] |
| support.gitlab.com | gitlab.zendesk.com | Excluido; SaaS de **terceros** (Zendesk) | [T8 · 12:57] |
| status.gitlab.com | hostedstatus.com | Excluido; SaaS de **terceros** (Status.io) | [T8 · 12:57] |
| auth.gitlab.com · gprd.gitlab.com · email.customers.gitlab.com | — (vistos en el certificado) | Subdominios de gitlab.com no listados (decisión 1) | [T4 · 12:38] |
| Otros 598 \*.gitlab.com | — | Sin comodín en gitlab.com (decisión 1) | [T3 · 12:10] |

**Conclusiones de la sección.**
- La superficie real en alcance está casi entera en los **comodines** (`*.gitlab.net` sobre todo): de gitlab.com solo entran 7 nombres (la raíz y 6 subdominios).
- **Dos niveles de exposición:** las herramientas internas sensibles (Vault, Argo CD, Sentry) están detrás de Cloudflare, pero los **entornos de prueba y de versiones** (dev.gitlab.org, *.env.release, *.testbed, la instancia de ops) están en Google Cloud **directo** y muchos con **SSH abierto a internet**.

---

## 3. Infraestructura y servicios

### 3.1 Registro de los dominios y DNS

| Dato | Valor | Por qué importa | Cuaderno |
|---|---|---|---|
| Registrador | Gandi SAS en los 4 dominios (gitlab.com, .net, .org, gitlap.com). Titular oculto por el RGPD | Mismo registrador = misma gestión. La titularidad de gitlab.com la confirma Netcraft ("GitLab Inc.") | [T1 · 11:54] [T4 · 12:38] |
| Servidores DNS | Cloudflare. gitlab.com usa un par de NS y los otros 3 dominios otro par | Cloudflare asigna el par por cuenta: **dos cuentas**. Hipótesis: separan la plataforma de producción del resto | [T1 · 11:54] [T2 · 11:56] |
| DNSSEC | **Desactivado** en los 4 | Netcraft decía "Enabled", pero `dig` no devuelve DS ni DNSKEY: **Netcraft se equivoca**. Los ataques de red están fuera del alcance, así que queda como observación | [T1 · 11:54] [T4 · 12:39] |

### 3.2 Hosting y servicios en la nube

Propietario (ASN) de las **146 IP públicas** de los 247 subdominios vivos, consultado por DNS a Team Cymru [T4 · 12:29]:

| Proveedor | IP | % | Qué hay ahí |
|---|---|---|---|
| **Google Cloud** (AS396982 + AS15169/19527/43515) | 67 | 46 % | **La infraestructura principal**: cientos de nombres `*.gke.gitlab.net` (Kubernetes en GCP), entornos de prueba, monitorización, registry.gitlab.com. El programa lo confirma: "gitlab.com: Google Cloud Platform" |
| **Cloudflare** (AS13335) | 65 | 45 % | Proxy + WAF delante de las webs públicas (gitlab.com, about, docs, customers) y de las herramientas internas sensibles |
| **AWS** (AS16509 + AS14618) | 14 | 9 % | Uso acotado: colector de analítica Snowplow (events.gitlab.net) y variantes híbridas de los testbed |

- **Multinube con GCP como base.** AWS es IaaS (servidores alquilados), así que sigue siendo infraestructura de GitLab y no un tercero (decisión 3) [T3 · 12:17].
- **GitLab Pages** (servicio propio, CNAME a `*.gitlab.io`) sirve las webs estáticas: design, advisories, theseus, nix… [T3 · 12:17].
- Además, **8 nombres resuelven a IP privadas** (10.216.x gprd · 10.224.x gstg · 10.250.x ops · 10.232.x pre): el DNS público revela el direccionamiento interno por entorno y que hay un Vault interno en ops y en pre [T3 · 12:17].

### 3.3 Tecnologías

| Capa | Tecnologías | Fuente | Cuaderno |
|---|---|---|---|
| Web pública | Cloudflare · TLS 1.3 con PFS · certificado DV de Sectigo · cabeceras HSTS, CSP, X-Frame-Options, X-Content-Type-Options y Referrer-Policy | Netcraft | [T4 · 12:38] |
| Frontend | about.gitlab.com hecho con Nuxt (Vue.js) | robots.txt | [T6 · 12:46] |
| Marketing | Marketo y Optimizely (rastreadores) | Netcraft | [T4 · 12:38] |
| Plataforma | Kubernetes (GKE en Google y EKS en AWS), microservicios `*.svc.gitlab.net` | Nombres DNS | [T3 · 12:17] |
| Despliegue e infraestructura como código | Argo CD (despliegue continuo), Atlantis (Terraform) | Nombres DNS | [T3 · 12:17] |
| Secretos y acceso | HashiCorp Vault (secretos), Teleport (acceso de administradores) | Nombres DNS + Shodan | [T3 · 12:17] [T5 · 12:41] |
| Observabilidad | Sentry, Prometheus / Mimir, Grafana, Alertmanager, Kibana / Elastic | Nombres DNS + dorks | [T3 · 12:17] [T7 · 12:53] |
| Sistemas (según Shodan) | GitLab CE/EE, nginx, Ubuntu, Debian, OpenSSH 8.9p1 / 9.2p1 / 9.6p1 / 10.0p2, uvicorn (Python) | InternetDB | [T5 · 12:41] [T5 · 31/10 17:34] |
| Equipos de empleados | Flota de Mac: Jamf + munki (`corpsec-munki-repo`) | TXT + nombres DNS (dos técnicas) | [T2 · 11:56] [T3 · 12:17] |

### 3.4 Correo

| Dato | Valor | Por qué importa | Cuaderno |
|---|---|---|---|
| MX | Google (`aspmx.l.google.com` + alt1-4) | Correo e identidad de los empleados en **Google Workspace** | [T2 · 11:56] |
| SPF | Gestionado por Valimail (`include:...vali.email ~all`) | SPF dinámico, gestionado por un tercero especializado | [T2 · 11:56] [T4 · 12:39] |
| DMARC | `p=reject; pct=100` | **Punto fuerte**: el correo que suplanta a @gitlab.com se rechaza | [T2 · 11:56] |
| SPF antiguo (Netcraft, cacheado) | Zendesk, Salesforce, Zuora, Marketo, Mailgun | Histórico: qué servicios enviaban correo en nombre de GitLab | [T4 · 12:38] [T4 · 12:39] |

### 3.5 Servicios de terceros (SaaS)

Salen de los **32 registros TXT** de verificación [T2 · 11:56], de los CNAME [T8 · 12:57] y de los dorks [T7 · 12:53]. **Todos están fuera del alcance** ("strictly out of scope"); sirven para entender la organización y para clasificar subdominios.

| Área | Servicios |
|---|---|
| Identidad | Google Workspace, Microsoft, Adobe (SSO), **Okta** (login de Kibana) |
| Colaboración | Atlassian, Smartsheet, DocuSign, Zapier |
| Ventas, soporte y pagos | Drift, Decagon, Stripe, **Zendesk** (support.gitlab.com), **Status.io** (status.gitlab.com) |
| Correo transaccional | Mailgun |
| Otros | OpenAI (IA), OneTrust (privacidad), Workday (RR. HH.), Jamf y Apple (gestión de equipos) |

### 3.6 Lo que muestra Shodan (InternetDB)

Se consultaron las **81 IP que no son de Cloudflare**: las de Cloudflare enseñarían los puertos de Cloudflare, no los de GitLab. Resultado: **71 con datos y 10 sin datos** [T5 · 12:41] [T5 · 31/10 17:34].

| Observación | Detalle | Interpretación |
|---|---|---|
| Puertos | 80 (55 IP), 443 (53), **22 / SSH (12)**, 2222 (3), 5005 (1) | La mayoría solo web. **SSH abierto a internet en 12 IP**: dev.gitlab.org, *.env.release, *.testbed, policy-framework-preview y kas/registry.ops |
| Puertos 2222 y 5005 | 2222 en 1k/2k/10k.testbed · 5005 en dev.gitlab.org | 2222 = SSH alternativo típico de GitLab en contenedor; 5005 = típico del registro de contenedores de GitLab |
| 4 IP con cientos de puertos | api.corpsecdevices (675), promlens (834), corpsec-fleet-hooks (437), grafana.northstar (325) | **Artefacto**: balanceadores de Google que aceptan cualquier conexión. No son servicios reales, se descartan |
| 82 CVE en 18.219.104.126 | PHP 8.0.30 + Apache 2.4.58 | **Falso positivo demostrado**: es una IP de balanceador de AWS compartida. Shodan ve en ella pizzaraul.work, que es de otro cliente. **No se atribuye a GitLab** |
| 1 CVE en 77.112.131.85 | akka-http 10.2.9 (CVE-2023-33251) en snowplowprd.trx.gitlab.net | En esta IP Shodan solo ve nombres de GitLab, y akka-http encaja con el colector de Snowplow. **Candidato a verificar**: InternetDB deduce la CVE por la versión, no la comprueba |
| Certificado autofirmado | comp-calculator, conservatory, nominatorbot (34.138.170.206) | Herramientas internas montadas con menos cuidado |
| Etiqueta "pqc" | Varios servicios de GCP | Criptografía post-cuántica activada: buena práctica |

**Lección de esta sección:** 4 IP de balanceadores de AWS de events.gitlab.net y events-stg.gitlab.net aparecen también con nombres de otras empresas (pizzaraul.work, pelsisdigital.com, seinetwork.io, dicomassist.app). **Lo que Shodan ve en una IP compartida no se le puede atribuir al objetivo sin comprobar quién más vive ahí.**

---

## 4. Correos y personas

> Se publican **cifras y patrones, nunca correos ni nombres** concretos: son datos personales y no hacen falta para la fase activa. La ingeniería social y el contacto con empleados están **fuera del alcance** del programa y de este proyecto, así que esta sección es contexto, no vía de ataque.

### 4.1 Patrón de correo

| Dato | Valor | Cuaderno |
|---|---|---|
| **Patrón** | **`{f}{last}@gitlab.com`**: inicial del nombre + apellido, todo junto | [T8 · 31/10 ~17:46] |
| Fuente | API de Hunter.io (`domain-search`, `organization: GitLab`) | [T8 · 31/10 ~17:46] |
| Confianza | **Una sola fuente.** theHarvester (6 fuentes gratuitas) devolvió 0 correos, así que no hay con qué contrastarlo. Hunter **infiere** el patrón a partir de los correos que tiene indexados → "patrón según Hunter", no dato confirmado | [T8 · 12:57] [T8 · 31/10 ~17:46] |

### 4.2 Correos indexados públicamente (Hunter.io)

| Tipo | Cantidad |
|---|---|
| **Total @gitlab.com** | **651** |
| Personas | 375 |
| Cargos directivos | 3 |
| Genéricos (buzones de equipo) | 276 |

Por departamento (de los que Hunter sabe clasificar): **IT/Engineering 43** · Support 4 · Writing & Communication 3 · Sales 2 · Marketing 2 · Executive, Finance, Management, Arts & Design, Product y Procurement 1 cada uno · desconocido 315 [T8 · 13:12].

**Por qué importa:** con el patrón, cualquier nombre público se convierte en un correo válido. **IT/Engineering es el departamento más expuesto**, y es justo el que tiene acceso a la infraestructura de la sección 3 (Vault, Teleport, Argo CD). El contrapeso es **DMARC `p=reject`**, que impide suplantar @gitlab.com desde fuera [T2 · 11:56], y que el acceso a las herramientas internas pasa por **Google y Okta** [T2 · 11:56] [T7 · 12:53].

### 4.3 Lo que se ha averiguado de la organización

| Aspecto | Qué se sabe | Cuaderno |
|---|---|---|
| Quién es | **GitLab Inc.**, Estados Unidos (titular según Netcraft). gitlab.com se registró en 2004, antes de que existiera GitLab: el dominio se adquirió después | [T1 · 11:54] [T4 · 12:38] |
| Otra empresa con la marca | `*.gitlab.cn` es de **JiHu**, empresa distinta con su propio canal de seguridad → fuera de alcance | `alcance.md` |
| Identidad y herramientas de los empleados | Google Workspace (correo e identidad), Okta en herramientas internas, flota de **Mac** gestionada con Jamf y munki | [T2 · 11:56] [T3 · 12:17] [T7 · 12:53] |
| Áreas de negocio visibles | Soporte en Zendesk, RR. HH. en Workday, ventas y pagos en Drift, Decagon y Stripe, marketing en Marketo | [T2 · 11:56] [T4 · 12:38] [T7 · 12:53] [T8 · 12:57] |
| Equipo de seguridad maduro | Automatiza la gestión de sus informes de HackerOne (h1bot, h1-import, h1-attachments, con entorno dev y live), publica un `security.txt` firmado con PGP (RFC 9116), usa herramientas de inteligencia de amenazas (OpenCTI, OpenBAS) y DMARC en `reject` | [T3 · 12:17] [T6 · 12:46] [T2 · 11:56] |
| Cultura de ingeniería | Las review apps crean un entorno por cada merge request (1084 nombres en crt.sh); hay entornos personales de empleados; documentación interna publicada (theseus.gitlab.net) | [T3 · 12:12] [T3 · 12:14] [T7 · 12:53] |

**Fuga de información menor:** los nombres de las review apps revelan nombres de ramas de desarrollo, y algunos subdominios llevan alias de empleados. No es explotable, pero un atacante sabría en qué se está trabajando y quién. Se anota el patrón, sin publicar nombres [T3 · 12:12] [T3 · 12:14].

---

## 5. Puntos de interés

Criterios para elegirlos: (1) **en alcance**, (2) **evidencia de más de una técnica**, (3) **exposición sin la protección de Cloudflare** o **valor alto del activo**. Todo lo que sigue es una **hipótesis** que se verificaría en la fase activa, siempre dentro de las reglas del programa. En recon pasivo solo se observa: no se prueba ninguno.

### 1 · Entornos de desarrollo, operaciones y pruebas expuestos directamente con SSH

**Qué:** dev.gitlab.org, kas.ops / registry.ops.gitlab.net, las `*.env.release.gitlab.net` (una por versión, de la 18-11 a la 19-5), los `*.testbed.gitlab.net` y policy-framework-preview.gitlab.net.

**Por qué es lo primero:**
- **En alcance** por `*.gitlab.org` y `*.gitlab.net` [T3 · 12:10].
- **Sin Cloudflare:** IP de Google Cloud directo, sin el proxy/WAF que sí protege a gitlab.com. Nada filtra lo que les llega [T4 · 12:29].
- **Son GitLab de verdad** (CPE `gitlab:gitlab` en Shodan), no webs estáticas: el impacto de un fallo sería alto [T5 · 12:41].
- **SSH abierto a internet** en estas instancias, cuando el acceso oficial de administradores es Teleport: es una **puerta lateral** que no pasa por ese control [T5 · 31/10 17:34].
- Las **versiones antiguas** (18-11…) pueden arrastrar fallos ya corregidos en versiones nuevas.

**Qué se miraría en la fase activa:** el **nivel de parche real** de cada instancia (no solo el número de versión que anuncia Shodan, que los backports de Debian/Ubuntu no actualizan) y si ese SSH debería estar detrás de Teleport.

### 2 · customers.gitlab.com: portal de clientes, pagos y panel de administración

**Qué:** el portal de suscripciones, pagos y facturas, con severidad **crítica** en el programa. Su `robots.txt` oculta **`/admins/`**, entra con **enlace mágico por correo** ("one-time sign-in link") y mueve **pagos** (Stripe aparece en los TXT) [T6 · 12:46] [T7 · 12:53] [T2 · 11:56].

**Por qué es interesante:**
- Junta **dinero** (facturación) y un **panel de administración** (`/admins/`): el activo de más valor del alcance.
- El login por enlace mágico es una **superficie de autenticación** distinta de la contraseña clásica, con sus propios riesgos (enlaces que no caducan o reutilizables).
- El propio dueño señala `/admins/` al pedir que no se indexe: una pista de dónde está la zona sensible.

**Qué se miraría en la fase activa:** la robustez del flujo del enlace mágico y los controles de acceso de la zona de administración. **No se visita en recon pasivo.**

### 3 · Información interna filtrada en fuentes públicas

**Qué:** tres fugas de bajo impacto que, juntas, dibujan el interior de la red:
1. El **DNS público publica IP privadas** (RFC 1918): revela el direccionamiento interno por entorno (gprd 10.216.x · gstg 10.224.x · ops 10.250.x · pre 10.232.x) y que hay un **Vault** interno en ops y en pre [T3 · 12:17].
2. **pulp.pre.gitlab.net:** repositorio de paquetes de preproducción con **listado de directorios abierto** [T7 · 12:53].
3. **theseus.gitlab.net:** documentación de la plataforma interna (nombres de herramientas y arquitectura sobre GKE) [T7 · 12:53].

**Por qué es interesante:** ninguna se explota desde fuera, pero a un atacante que ya estuviera dentro le dan un **mapa gratis** de la red interna, de dónde están los secretos (Vault) y de cómo se llama cada herramienta. Es justo lo que un equipo querría **cerrar antes** de la fase activa.

**Qué se miraría en la fase activa:** si esa información debería ser pública y por qué el DNS externo expone direcciones privadas.

### ¿Por qué estos tres y no otros?

| Descartado | Motivo |
|---|---|
| Las 82 CVE de 18.219.104.126 | **Falso positivo**: IP de balanceador de AWS compartida con un tercero (pizzaraul.work) [T5 · 12:41] |
| gitlab.com | Detrás de Cloudflare y muy endurecido (cabeceras completas, DMARC reject) [T4 · 12:38] |
| Los SaaS de terceros (Zendesk, Workday…) | **Fuera de alcance** [T8 · 12:57] |
| Los balanceadores con cientos de puertos | Artefacto de Shodan, no servicios reales [T5 · 31/10 17:34] |

Se priorizan los tres por la combinación **en alcance + expuesto directo (o alto valor) + evidencia de varias técnicas**, que es lo que haría perder menos tiempo en la fase activa.
