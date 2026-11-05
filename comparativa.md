# Comparativa · Yo frente al agente

> Comparación entre el reconocimiento manual de la Parte 1 ([`mapa.md`](mapa.md), [`cuaderno.md`](cuaderno.md)) y la ejecución del agente `aap-base` de la Parte 2 ([`agente/informe.md`](agente/informe.md), [`agente/traza.log`](agente/traza.log), [`agente/pruebas.md`](agente/pruebas.md)) contra el mismo objetivo (GitLab, HackerOne) y el mismo [`scope.txt`](scope.txt).

<!-- ESTADO: esqueleto. La columna "Lo encontré yo" está completa; la del agente se rellena con la traza de la ejecución 2.4. -->

## 0. Predicciones (escritas ANTES de ejecutar el agente)

Escritas el 2026-11-04, antes de tener ninguna respuesta del modelo, a partir de lo que sé del `scope.txt`, de las herramientas y del motor. En la sección 3.2 se comprueba si se cumplieron.

| # | Predicción | Por qué lo espero | ¿Se cumplió? |
|---|---|---|---|
| P1 | El agente encontrará **muchos menos subdominios** que yo | `subdominios_crtsh` recibe un dominio y el `scope-guard` comprueba ese dominio. Las raíces `gitlab.net` y `gitlab.org` están **fuera** (un comodín no incluye la raíz, decisión 2 de `alcance.md`), así que no puede pedir `%.gitlab.net` a crt.sh. Con `gitlab.com` solo pasan el filtro los 7 hosts listados. Además, no tiene subfinder | ⏳ |
| P2 | `whois_dominio` y `subdominios_crtsh` sobre `gitlab.net`/`gitlab.org` darán `BLOQUEADO` | El mismo motivo: son raíces fuera del alcance | ⏳ |
| P3 | No podrá consultar **DMARC** | Está en `_dmarc.gitlab.com`, un subdominio de `gitlab.com` no listado → fuera del alcance | ⏳ |
| P4 | No dirá nada de **DNSSEC**, del **patrón de correo** ni de **dorks** | No tiene herramienta para eso (`dns_registros` no admite DS/DNSKEY; no hay Hunter ni Google) | ⏳ |
| P5 | Dirá el **proveedor de hosting** de las IP solo por inferencia | No tiene una herramienta de ASN; solo la etiqueta `cloud` de InternetDB y nombres como `googleusercontent` | ⏳ |
| P6 | Si consulta `infraestructura_dominio` en hosts directos (p. ej. `dev.gitlab.org`), verá el **SSH** igual que yo | Usa la misma fuente (InternetDB) | ⏳ |

## 1. La comparación (3.1)

Fechas: yo, del 2026-10-28 al 2026-10-31; el agente, el 2026-11-04 (⏳). Las referencias **[T*n* · hora]** remiten al cuaderno; las del agente, a la traza (`paso N`).

### Técnica 1 · Registro del dominio

| Dato | Lo encontré yo | Lo encontró el agente | ¿Coincide? | Observaciones |
|---|---|---|---|---|
| Registrador | Gandi SAS en los 4 dominios [T1 · 11:54] | ⏳ | ⏳ | |
| Titular | Oculto por el RGPD; "GitLab Inc." según Netcraft [T4 · 12:38] | ⏳ | ⏳ | |
| Servidores DNS | Cloudflare, con dos pares de NS (dos cuentas) [T1 · 11:54] [T2 · 11:56] | ⏳ | ⏳ | |
| DNSSEC | Desactivado (Netcraft decía lo contrario) [T4 · 12:39] | ⏳ | ⏳ | P4 |

### Técnica 2 · DNS

| Dato | Lo encontré yo | Lo encontró el agente | ¿Coincide? | Observaciones |
|---|---|---|---|---|
| Correo (MX) | Google Workspace (`aspmx.l.google.com`) [T2 · 11:56] | ⏳ | ⏳ | |
| SPF | Valimail (`include:...vali.email ~all`) [T2 · 11:56] | ⏳ | ⏳ | |
| DMARC | `p=reject; pct=100` [T2 · 11:56] | ⏳ | ⏳ | P3 |
| TXT de verificación (SaaS) | 32 registros: Atlassian, Stripe, Okta, OpenAI, Jamf… [T2 · 11:56] | ⏳ | ⏳ | |

### Técnica 3 · Subdominios

| Dato | Lo encontré yo | Lo encontró el agente | ¿Coincide? | Observaciones |
|---|---|---|---|---|
| Nombres únicos | 2974 (subfinder + crt.sh) [T3 · 12:10] | ⏳ | ⏳ | P1 |
| En alcance | 2132 (842 fuera) [T3 · 12:10] | ⏳ | ⏳ | P1 |
| Review apps apartadas | 1084 [T3 · 12:12] | ⏳ | ⏳ | |
| Resuelven en DNS | 247 [T3 · 12:17] | ⏳ | ⏳ | |
| IP privadas en el DNS público | 8 nombres (10.216.x, 10.224.x, 10.250.x, 10.232.x) [T3 · 12:17] | ⏳ | ⏳ | |

### Técnica 4 · Huella tecnológica

| Dato | Lo encontré yo | Lo encontró el agente | ¿Coincide? | Observaciones |
|---|---|---|---|---|
| Hosting | GCP 46 % · Cloudflare 45 % · AWS 9 % (146 IP, ASN por Team Cymru) [T4 · 12:29] | ⏳ | ⏳ | P5 |
| CDN/WAF | Cloudflare delante de gitlab.com, about, docs, customers [T4 · 12:38] | ⏳ | ⏳ | |
| Tecnologías web | TLS 1.3, cabeceras HSTS/CSP, Nuxt en about [T4 · 12:38] [T6 · 12:46] | ⏳ | ⏳ | |

### Técnica 5 · Servicios expuestos (Shodan / InternetDB)

| Dato | Lo encontré yo | Lo encontró el agente | ¿Coincide? | Observaciones |
|---|---|---|---|---|
| IP consultadas | 81 no-Cloudflare → 71 con datos, 10 sin datos [T5 · 12:41] [T5 · 31/10 17:34] | ⏳ | ⏳ | |
| SSH abierto | 12 IP (dev.gitlab.org, *.env.release, *.testbed…) [T5 · 31/10 17:34] | ⏳ | ⏳ | P6 |
| dev.gitlab.org | 22, 80, 443, 5005 [T5 · 12:41] | ⏳ | ⏳ | |
| Falso positivo de 82 CVE (IP de ELB compartida) | Detectado y descartado [T5 · 12:41] | ⏳ | ⏳ | |

### Técnica 6 · Ficheros expuestos

| Dato | Lo encontré yo | Lo encontró el agente | ¿Coincide? | Observaciones |
|---|---|---|---|---|
| security.txt | 200 solo en gitlab.com, firmado con PGP, apunta a HackerOne [T6 · 12:46] | ⏳ | ⏳ | |
| robots.txt de customers | Oculta `/admins/` [T6 · 12:46] | ⏳ | ⏳ | |
| robots.txt de about | Nuxt, `/search/`, `/api/`, `/exp/` [T6 · 12:46] | ⏳ | ⏳ | |

### Técnicas 7 y 8 · Google dorks y correos

| Dato | Lo encontré yo | Lo encontró el agente | ¿Coincide? | Observaciones |
|---|---|---|---|---|
| Dorks | pulp.pre con listado de directorios, theseus, login Okta en Kibana [T7 · 12:53] | ⏳ | ⏳ | P4 |
| Patrón de correo | `{f}{last}@gitlab.com` (Hunter, una sola fuente) [T8 · 31/10 ~17:46] | ⏳ | ⏳ | P4 |

### Puntos de interés

| Mi punto de interés | ¿Lo señaló el agente? | Observaciones |
|---|---|---|
| 1 · Entornos de desarrollo/pruebas directos con SSH | ⏳ | |
| 2 · customers.gitlab.com (pagos + `/admins/`) | ⏳ | |
| 3 · Información interna filtrada (IP privadas, pulp.pre, theseus) | ⏳ | |

### Resumen con números

| Medida | Yo | Agente |
|---|---|---|
| Subdominios en alcance | 2132 (247 vivos) | ⏳ |
| Técnicas cubiertas (de 8) | 8 + 1 opcional | ⏳ |
| Tiempo | ~1 h 30 min de consultas (2026-10-28 11:54–13:12 y 2026-10-31 17:34–17:46), más varias horas de análisis y redacción del mapa | ⏳ |
| Coste | 0 € (herramientas gratuitas; Hunter con cuenta gratuita) | ⏳ tokens de entrada/salida · ⏳ USD (`ia-cupo`) |
| Llamadas a herramientas / bloqueos | — | ⏳ / ⏳ |

## 2. Los fallos del agente (3.2)

Cada fallo, clasificado y con su trozo de traza.

### Omisiones (algo que estaba y no encontró)

⏳

### Errores (dato mal interpretado)

⏳

### Invenciones (afirma algo que ninguna herramienta devolvió)

⏳

### Intentos fuera de alcance (bloqueados por el `scope-guard`)

⏳ (de la ejecución 2.4 y de la 2.5)

## 3. Reflexión (3.3)

<!-- PENDIENTE: lo redacta el alumno, con sus palabras y con ejemplos concretos de la traza. -->

### 1. ¿Qué hizo mejor el agente que yo, y qué hice mejor yo?

⏳

### 2. ¿Por qué falló donde falló?

⏳

### 3. ¿Me fiaría del informe del agente sin revisarlo? ¿Qué comprobaría siempre?

⏳
