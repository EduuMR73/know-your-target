# Cuaderno de trabajo · GitLab

Formato de cada entrada: cuándo · objetivo (y si está en alcance) · qué hice · qué salió · **por qué importa** (¿es interesante o no, y por qué?) · siguiente paso.

**Horas en UTC** (`date -u`), como en los logs reales, para poder cruzarlas con la actividad del objetivo. Hora de España = UTC+1.

---

## Fase 0 · Elección del objetivo y alcance

2026-10-28 antes de las 10:40 UTC (hora exacta no anotada) · objetivo: programas candidatos (sin interacción con ningún objetivo)
$ curl -sL https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data/hackerone_data.json -o h1.json
-> volcado público de los alcances de HackerOne. GitLab (*.gitlab.net, *.gitlab.org, *.gitlap.com), Amazon VRP (26 comodines, exclusiones AWS ambiguas), Alibaba VDP (28 comodines, sin exclusiones)
-> Mozilla no aparece en el volcado; en hackerone.com/mozilla: "taking a break and is not accepting new submissions" -> descartado (no está activo)
por qué importa: el volcado permite filtrar programas con comodín sin recorrer las plataformas una a una, pero tiene retraso, así que el alcance oficial se confirma siempre en la web del programa. Un programa pausado no da autorización: auditarlo sería trabajar sin contrato
siguiente: elegir entre GitLab, Amazon y AliExpress

2026-10-28 antes de las 10:40 UTC (hora exacta no anotada) · objetivo: GitLab (elegido)
$ navegador: https://hackerone.com/gitlab?type=team  y  https://hackerone.com/gitlab/policy_scopes?type=team
-> política actualizada el 2026-10-05; alcance actualizado el 2026-05-27; 44 activos (19 dentro). Coincide con el volcado de bounty-targets-data
-> reglas clave: sin actividad de alto volumen ni disruptiva, sin contacto con empleados, subdominios con servicios de terceros fuera de alcance, *.runway.gitlab.net fuera
por qué importa: la exclusión de *.runway.gitlab.net dentro de *.gitlab.net y la de "servicios de terceros" significan que el nombre del dominio NO basta para saber si algo está en alcance: habrá que resolver cada subdominio y mirar a dónde apunta. Es la regla que más va a condicionar el mapa
siguiente: redactar alcance.md y scope.txt

2026-10-28 10:40 UTC · objetivo: GitLab
$ redacción de alcance.md y scope.txt
-> 3 comodines + 7 dominios dentro; 4 comodines + 18 dominios fuera
-> decisión: los subdominios de gitlab.com no listados se tratan como fuera de alcance (la política dice "isn't encouraged")
por qué importa: scope.txt es lo que usará el scope-guard del agente en la Parte 2; un error aquí se traslada al agente. Elegir la interpretación conservadora protege legalmente: ante la duda, fuera
siguiente: 1.3 reconocimiento pasivo, empezando por whois de los dominios en alcance

---

## Fase 1 · Reconocimiento pasivo

### Paso 0 · Entorno de trabajo

2026-10-28 10:59 UTC · objetivo: ninguno (preparación del entorno)
$ mkdir -p ~/kyt/raw && cd ~/kyt
$ curl -s ifconfig.me
$ which whois dig subfinder theHarvester jq curl
-> máquina: Kali del laboratorio del instituto (alumno3), con acceso por VPN WireGuard + noVNC
-> IP pública de salida: 90.170.x.x (enmascarada en este repo público; ver la nota de abajo)
-> herramientas disponibles: whois, dig, subfinder, theHarvester, jq, curl (las 6)
por qué importa: la política de GitLab pide anotar las IP usadas durante la investigación ("keep note of any IP addresses you use"); si GitLab viera tráfico de esa IP, se puede atribuir a este trabajo.
   · por qué está enmascarada (2026-11-06): la anotación de la IP se cumple igual: si GitLab la pidiera, se le daría completa. En un repo público no aporta nada al lector, y sí identifica la conexión del instituto: cualquiera podría usarla para escanearla, atribuirle tráfico o saber desde dónde trabajamos. Es la misma regla que aplico al objetivo: no publicar datos que no hacen falta (minimización) Las salidas en bruto se guardan en ~/kyt/raw/ como evidencia, para que cada dato del mapa se pueda rastrear
siguiente: técnica 1, whois de gitlab.com, gitlab.net, gitlab.org y gitlap.com

### Técnica 1 · Registro del dominio

2026-10-28 11:50 UTC · objetivo: gitlab.com (en alcance), gitlab.net, gitlab.org, gitlap.com (raíces de los comodines: no en alcance, pero consultar un registro público no toca al objetivo)
$ for d in gitlab.com gitlab.net gitlab.org gitlap.com; do whois "$d" > "raw/whois_$d.txt"; echo "===== $d"; grep -iE "^ *(registrar:|creation date|registry expiry|registrar registration expiration|name server|registrant (organization|country)|dnssec)" "raw/whois_$d.txt" | sort -u; done
-> los 4 fallan al instante: "connect: Network is unreachable"; los raw/whois_*.txt quedan vacíos
por qué importa: sin whois no hay técnica 1; antes de cambiar de herramienta hay que saber POR QUÉ falla (¿el objetivo, la herramienta o mi red?)
siguiente: comprobar si la red del lab bloquea el puerto 43 (whois) frente al 443 (HTTPS)

2026-10-28 entre 11:50 y 11:54 UTC (hora exacta no anotada; acotada por los date -u anterior y posterior) · objetivo: ninguno (diagnóstico de mi propia red)
$ timeout 8 bash -c '</dev/tcp/whois.verisign-grs.com/43'
$ timeout 8 bash -c '</dev/tcp/rdap.verisign.com/443'
-> 43 BLOQUEADO · 443 ABIERTO
por qué importa: el firewall del laboratorio solo deja salir tráfico web. Es una limitación de MI entorno, no del objetivo. Se sustituye whois por RDAP (RFC 9083), su sucesor oficial: mismos datos de registro, en JSON y por HTTPS
siguiente: repetir la consulta por RDAP

2026-10-28 11:54 UTC · objetivo: gitlab.com (en alcance), gitlab.net, gitlab.org, gitlap.com (raíces, solo registro público)
$ for d in gitlab.com gitlab.net gitlab.org gitlap.com; do curl -sL "https://rdap.org/domain/$d" > "raw/rdap_$d.json"; echo "===== $d"; jq -r '
    "Registrador: " + ([.entities[]? | select(.roles[]? == "registrar") | .vcardArray[1][]? | select(.[0]=="fn") | .[3]] | first // "?"),
    (.events[]? | select(.eventAction=="registration" or .eventAction=="expiration") | "\(.eventAction): \(.eventDate)"),
    "DNS: " + ([.nameservers[]?.ldhName] | join(", ")),
    "DNSSEC: " + ((.secureDNS.delegationSigned // false) | tostring)
  ' "raw/rdap_$d.json"; done
-> gitlab.com · Gandi SAS · alta 2004-01-15 · caduca 2027-01-15 · NS diva/jermaine.ns.cloudflare.com · DNSSEC no
-> gitlab.net · Gandi SAS · alta 2004-04-21 · caduca 2027-04-21 · NS arya/hal.ns.cloudflare.com · DNSSEC no
-> gitlab.org · Gandi SAS · alta 2010-01-19 · caduca 2027-01-19 · NS arya/hal.ns.cloudflare.com · DNSSEC no
-> gitlap.com · Gandi SAS · alta 2013-01-11 · caduca 2027-01-11 · NS arya/hal.ns.cloudflare.com · DNSSEC no
-> titular: no aparece (RDAP lo oculta por el RGPD)
por qué importa:
   · titularidad: mismo registrador y DNS en Cloudflare en los 4; gitlab.net/.org y gitlap.com comparten el MISMO par de NS, y Cloudflare asigna el par por cuenta -> misma cuenta, mismo dueño administrativo. Se INFIERE que son de GitLab (el titular está oculto), lo que da confianza en los comodines del alcance
   · gitlab.com usa OTRO par de NS -> otra cuenta de Cloudflare. Hipótesis: separan la plataforma de producción del resto de dominios
   · gitlab.com se registró en 2004, antes de que existiera GitLab (2011): el dominio se adquirió después. Contexto para el resumen, no es un riesgo
   · caducidades en ene-2027 (renovación anual normal). No es un riesgo salvo que no renueven; se anota y se descarta
   · DNSSEC desactivado en los 4: las respuestas DNS no se pueden verificar criptográficamente. Interesante para el mapa, pero los ataques de red (MitM) están FUERA del alcance del programa -> observación, no punto de ataque
   · Gandi: registrador europeo serio, pero no especializado en protección de marca (MarkMonitor, CSC). Contexto
   · NS en Cloudflare: SUGIERE CDN/WAF de Cloudflare, no lo prueba -> se comprueba en la técnica 4
siguiente: técnica 2, registros DNS (NS, MX, TXT, SPF, DMARC) con dig

### Técnica 2 · Registros DNS

2026-10-28 11:56 UTC · objetivo: gitlab.com (en alcance)
$ dig +short gitlab.com A
-> 172.65.251.78 (el puerto 53 funciona desde el lab, a diferencia del 43)
siguiente: resto de registros

2026-10-28 11:56 UTC · objetivo: gitlab.com (en alcance), _dmarc.gitlab.com (no listado; ver la nota del final)
$ for t in NS A AAAA MX TXT; do dig +short gitlab.com $t | tee -a raw/dns_gitlab.com.txt; done
$ dig +short _dmarc.gitlab.com TXT | tee -a raw/dns_gitlab.com.txt
-> NS: diva.ns.cloudflare.com, jermaine.ns.cloudflare.com (coincide con RDAP)
-> A: 172.65.251.78 · AAAA: 2606:4700:90:0:f22e:fbec:5bed:a9b9
-> MX: aspmx.l.google.com + alt1-4 (Google Workspace)
-> SPF: v=spf1 include:%{i}._ip.%{h}._ehlo.%{d}._spf.vali.email ~all
-> DMARC: v=DMARC1; p=reject; pct=100; rua=mailto:dmarc_agg@vali.email
-> TXT (32 registros, incluido el SPF) · verificaciones: Google (x7), Microsoft MS= (x2), Adobe IdP, Atlassian, Mailgun (x2), Smartsheet, GlobalSign, Jamf, Apple, Decagon, GitLab Pages, OneTrust (x2), Drift, Serval, Uber, OpenAI, DocuSign, Zapier, Stripe
-> sin identificar: "v=MCPv1; k=ed25519; p=...", "asv=...", "verification_token=..."
por qué importa:
   · A y AAAA en rangos de Cloudflare (172.64.0.0/13, 2606:4700::/32): gitlab.com estaría detrás del proxy de Cloudflare, con el origen oculto. Pendiente de confirmar con el whois de la IP (técnica 4)
   · MX de Google: el correo y la identidad de los empleados están en Google Workspace
   · DMARC p=reject al 100% + SPF gestionado por Valimail: la suplantación de @gitlab.com se rechaza. PUNTO FUERTE. Además, los problemas de SPF/DKIM están fuera del alcance del programa -> se descarta como vía
   · los TXT revelan los SaaS internos sin tocar nada: identidad (Google, Microsoft, Adobe SSO), Macs gestionados con Jamf, colaboración (Atlassian, Smartsheet, DocuSign, Zapier), correo transaccional (Mailgun), ventas y soporte (Drift, Decagon, Stripe), IA (OpenAI), privacidad (OneTrust)
   · son servicios de TERCEROS -> fuera de alcance ("strictly out of scope"); se usan como contexto y para clasificar subdominios en la técnica 3 (un CNAME a Mailgun, Atlassian, etc. = tercero = fuera)
   · los 3 TXT sin identificar se dejan como "pendiente de investigar", sin suponer de qué son
   · (nota añadida el 2026-11-06, al revisar) _dmarc.gitlab.com no es un host, sino un nombre DNS donde cada dominio publica su política de correo. Leerlo no envía nada a GitLab (la consulta va a los DNS de Cloudflare) y no es "probar" un subdominio: por eso lo consulto, aunque la decisión 1 de alcance.md deja fuera los subdominios no listados. El agente no puede hacerlo, porque su scope-guard aplica el alcance literal
siguiente: técnica 3, subdominios (subfinder + crt.sh) de los dominios en alcance

### Técnica 3 · Subdominios

2026-10-28 11:59 UTC · objetivo: gitlab.com, gitlab.net, gitlab.org, gitlap.com (fuentes públicas: no se consulta al objetivo)
$ for d in gitlab.com gitlab.net gitlab.org gitlap.com; do subfinder -d "$d" -silent > raw/subfinder_$d.txt; curl -s "https://crt.sh/?q=%25.$d&output=json" | jq -r '.[].name_value' | tr 'A-Z' 'a-z' | tr -d '*' | sed 's/^\.//' | sort -u > raw/crtsh_$d.txt; done
-> gitlab.com: subfinder 251 · crt.sh 504
-> gitlab.net: subfinder 1007 · crt.sh 456
-> gitlab.org: subfinder 1118 · crt.sh 1002
-> gitlap.com: subfinder 245 · crt.sh 246
por qué importa: cada fuente ve cosas distintas (subfinder: DNS pasivo y buscadores; crt.sh: certificados emitidos). En gitlab.com, crt.sh encuentra el doble que subfinder; en gitlab.net, al revés. Con una sola fuente se perdería una parte del mapa (dato a comparar con el agente en la Parte 3)
siguiente: unir, quitar duplicados y clasificar por alcance

2026-10-28 12:10 UTC · objetivo: los mismos
(antes: añadido !runway.gitlab.net a scope.txt; al leer alcance/alcance.py se vio que el comodín de exclusión no cubre la raíz, que sí entraba por *.gitlab.net -> decisión 6 de alcance.md)
$ cat raw/subfinder_*.txt raw/crtsh_*.txt | tr 'A-Z' 'a-z' | grep -E '^[a-z0-9._-]+\.(gitlab\.com|gitlab\.net|gitlab\.org|gitlap\.com)$' | sort -u > subdominios_todos.txt
$ ~/aap-base/.venv/bin/python - <<'PY'
import sys; sys.path.insert(0, "/home/alumno/aap-base/alcance")
from alcance import cargar, en_alcance
s = cargar("scope.txt")
todos = open("subdominios_todos.txt").read().split()
dentro = [d for d in todos if en_alcance(d, s)]
fuera  = [d for d in todos if not en_alcance(d, s)]
open("subdominios_dentro.txt","w").write("\n".join(dentro)+"\n")
open("subdominios_fuera.txt","w").write("\n".join(fuera)+"\n")
print(f"únicos: {len(todos)} · dentro: {len(dentro)} · fuera: {len(fuera)}")
for dom in ["gitlab.com","gitlab.net","gitlab.org","gitlap.com"]:
    print(f"  {dom}: dentro {sum(d.endswith('.'+dom) or d==dom for d in dentro)} · fuera {sum(d.endswith('.'+dom) or d==dom for d in fuera)}")
PY
-> únicos: 2974 · dentro: 2132 · fuera: 842
-> gitlab.com: dentro 6 · fuera 598
-> gitlab.net: dentro 763 · fuera 244
-> gitlab.org: dentro 1118 · fuera 0
-> gitlap.com: dentro 245 · fuera 0
por qué importa:
   · se clasifica con el MISMO scope-guard que usará el agente -> mismo criterio de alcance para comparar en la Parte 3
   · gitlab.com: solo 6 dentro = los 6 subdominios listados en el programa; los demás (598) quedan fuera por la decisión 1 (sin comodín)
   · gitlab.net: 244 fuera -> hipótesis: la mayoría son *.runway.gitlab.net (pendiente de verificar)
   · "dentro por nombre" NO es "dentro": el scope-guard no sabe si un subdominio apunta a un tercero (decisión 3). Además, crt.sh guarda nombres históricos que ya no existen -> hay que resolver y filtrar antes del mapa
siguiente: verificar la composición de los "fuera" de gitlab.net y buscar nombres reveladores entre los "dentro"

2026-10-28 12:12 UTC · objetivo: subdominios_dentro.txt / subdominios_fuera.txt (sin consultas externas)
$ grep -E '\.gitlab\.com$' subdominios_dentro.txt
$ echo "total $(grep -c '\.gitlab\.net$' subdominios_fuera.txt) · runway $(grep -c 'runway\.gitlab\.net$' subdominios_fuera.txt)"
$ grep -iE '(^|[.-])(admin|dev|staging|stg|test|internal|vpn|vault|grafana|kibana|prometheus|jenkins|sentry|ops|console|dashboard|db|backup|legacy|old|sandbox)([.-]|[0-9])' subdominios_dentro.txt | wc -l
-> gitlab.com dentro = about, advisories, customers, design, docs, registry (exactamente los 6 del programa)
-> gitlab.net fuera: 244, todos *.runway.gitlab.net -> HIPÓTESIS CONFIRMADA
-> filtro de palabras clave: 1508 coincidencias, casi todas "review apps" (p. ej. 43521838-review-<rama>-<hash>.version-staging.gitlab.org)
por qué importa:
   · las Review Apps de GitLab crean un entorno temporal (con su certificado) por cada merge request -> cientos de nombres efímeros en crt.sh. El filtro saltaba por el nombre del entorno padre (staging, dashboard), no por cada subdominio: un filtro de palabras sin entender la estructura de los datos da RUIDO
   · fuga de información menor: los nombres de rama revelan desarrollo interno (bump-ruby, ap-secure, add-intern...) y el prefijo numérico parece el ID de un proyecto. Interesante como observación, no útil para el mapa (efímeros)
siguiente: apartar las review apps y agrupar por servicio

2026-10-28 12:14 UTC · objetivo: subdominios_dentro.txt (sin consultas externas)
$ grep -v -- '-review-' subdominios_dentro.txt > dentro_sin_review.txt
$ awk -F. '{print $(NF-2)"."$(NF-1)"."$NF}' dentro_sin_review.txt | sort | uniq -c | sort -rn | head -50
-> review apps: 1084 de 2132 (51 %) · quedan 1048
-> grupos principales: gke.gitlab.net 256 · sec.gitlab.net 199 · quality-dashboard.gitlap.com 120 · do.gitlap.com 60 · svc.gitlab.net 40 · release.gitlab.net 40 · testbed.gitlab.net 29 · dev.gitlap.com 24 · ops.gitlab.net 17 · pre.gitlab.net 16 · gstg.gitlab.net 13 · gs-staging.gitlab.org 10 · security.gitlab.net 8 · gprd.gitlab.net 8 · teleport.gitlab.net 7 ...
-> sueltos destacados: vault.gitlab.net, vault-nonprod.gitlab.net, sentry.gitlab.net, sentry.gitlap.com, sentry-infra.gitlap.com, prometheus-app-01/02.gitlab.net, monitor.gitlab.net, prod-log/nonprod-log.gitlab.net, snipeit.gitlab.net, mattermost.gitlab.org, network-scanner.gitlap.com, db-benchmarking.gitlab.net
por qué importa (HIPÓTESIS por el nombre, pendientes de confirmar en la técnica 4):
   · gke = Google Kubernetes Engine -> clústeres de Kubernetes en GCP (coherente con "gitlab.com: Google Cloud Platform" del programa)
   · gprd / gstg / pre -> parecen producción / staging / preproducción: permiten separar producción de pruebas
   · vault (secretos) y teleport (acceso de administradores) -> los de MÁS valor: si estuvieran expuestos, serían la caja fuerte y la puerta de servicio
   · sentry, prometheus, monitor, *-log -> monitorización y errores: suelen filtrar rutas, versiones y trazas
   · dev, testbed, staging, *-stg, db-benchmarking -> entornos de prueba, a menudo menos protegidos
   · snipeit, mattermost -> software de terceros instalado: posiblemente FUERA por la política (software de terceros), a confirmar
   · 2 subdominios llevan lo que parecen alias de personas (máquinas personales): se anota el patrón, sin publicar los nombres
siguiente: resolver los 1048 para saber cuáles siguen vivos y a dónde apuntan (CNAME a terceros = fuera)

> **TÉCNICA OPCIONAL del enunciado** ("resolver los subdominios y mirar de quién es la IP: ¿WAF/CDN o expuesto directo?"). Se aplica aquí (resolución DNS) y en la técnica 4 (propietario de la IP por ASN). Resultado: distingue los hosts tras Cloudflare de los expuestos directamente en GCP/AWS, base de los puntos de interés del mapa.

2026-10-28 12:17 UTC · objetivo: los 1048 de dentro_sin_review.txt (consultas DNS normales, 10 en paralelo, unas 1000 en total)
$ xargs -P 10 -I{} sh -c 'r=$(dig +short +time=2 +tries=1 {} A | tr "\n" " "); [ -n "$r" ] && echo "{} -> $r"' < dentro_sin_review.txt | sort > resueltos.txt
-> vivos: 247 de 1048 (24 %)
-> CNAME fuera de los dominios de GitLab: gitlab.io (11), amazonaws.com (5), pacloudflare.com (1)
-> IP privadas en el DNS público (8 nombres, 4 redes): apt-mirror y zoekt .gprd.gke -> 10.216.8.x · apt-mirror y zoekt .gstg.gke -> 10.224.34.x · vault y mimir-gateway-private .ops.gke -> 10.250.26.x · vault y mimir-gateway-private .pre.gke -> 10.232.20.x (revisado con resueltos.txt completo, copiado a evidencias/)
-> rangos observados: 104.18.x / 172.64.x / 188.114.x (Cloudflare) · 34.x / 35.x (Google Cloud) · 18.x / 52.x (AWS) -> pendiente de confirmar el propietario por ASN
-> destacados: argocd.gitlab.net (tras Cloudflare) · atlantis-*.ops.gke.gitlab.net (6 nombres -> 34.160.239.33) · alertmanager-0/1/2.ops.gke.gitlab.net (GCP directo) · *.testbed.gitlab.net (GCP y AWS)
por qué importa:
   · el 76 % de los nombres no resuelve: históricos de crt.sh o solo internos. El mapa se construye con los 247 vivos, no con los 2974 brutos
   · HALLAZGO (informativo): el DNS público publica IP privadas RFC 1918 -> revela el direccionamiento interno POR ENTORNO (gprd 10.216.x · gstg 10.224.x · ops 10.250.x · pre 10.232.x) y que existe un Vault interno en ops y en pre. No se puede explotar desde fuera, pero es un mapa gratis para un atacante que ya esté dentro
   · lectura completa de resueltos.txt (observaciones a confirmar):
     - muchos servicios internos (argocd, vault, sentry, log, dashboards, portal, static-objects, mimir-us-east1...) comparten el MISMO par de IP de Cloudflare (104.18.40.188 / 172.64.147.68) -> hipótesis: una puerta común de Cloudflare (¿Cloudflare Access?) delante de las herramientas internas
     - registry.gitlab.com (EN ALCANCE, severidad crítica) -> 35.227.35.254, Google Cloud DIRECTO, sin Cloudflare, a diferencia de about/docs/customers
     - *.env.release.gitlab.net: instancias de GitLab por versión (18-11 ... 19-5 stable) expuestas directamente en GCP -> entornos con versiones concretas, posiblemente antiguas
     - *.testbed.gitlab.net: 1k, 2k, 10k, 50k (tamaños de arquitectura de referencia) + variantes híbridas en AWS
     - secauto-dev y secauto-live: los mismos servicios en desarrollo y en producción (h1bot, h1-import, h1-attachments = automatización de los informes de HackerOne del propio equipo de seguridad)
     - corpsec-* (devices, munki-repo, pki, vdi, fleet-hooks): gestión de equipos corporativos; munki = despliegue de software en macOS -> CUADRA con los TXT de Jamf y Apple de la técnica 2 (flota de Macs). Dato confirmado por dos técnicas
     - grafana.northstar.autoflow, promlens, alertmanager-0/1/2 -> herramientas de monitorización en GCP directo
     - opencti / openbas (.cti.sec) -> software de inteligencia de amenazas de terceros, autoalojado: ¿cuenta como "software de terceros" de la política? Ambiguo -> se trata como fuera por criterio conservador
     - ops.gitlab.net -> CNAME a *.pacloudflare.com -> 172.65.19.90 (rango de Cloudflare). pacloudflare.com sería, por tanto, de Cloudflare: pendiente de confirmar con el ASN
     - varios nombres contienen nombres de personas (entornos personales): se anota el patrón, sin publicarlos
   · Cloudflare (proxy + WAF, origen oculto) frente a GCP directo (sin ese escudo): los expuestos directamente son más interesantes para una fase activa
   · gitlab.io = GitLab Pages, servicio PROPIO -> no es tercero. amazonaws.com = servidores de GitLab alojados en AWS (IaaS), no un SaaS ajeno -> siguen siendo de GitLab. Diferencia clave para la decisión 3: alquilar infraestructura (IaaS) frente a usar el servicio de otra empresa (SaaS)
   · pacloudflare.com: no identificado -> pendiente, sin suponer
   · argocd (despliegue continuo en Kubernetes) y atlantis (Terraform) controlan QUÉ se ejecuta y CÓMO es la infraestructura -> candidatos a punto de interés
siguiente: técnica 4, confirmar el propietario de cada IP (ASN) y la huella tecnológica

### Técnica 4 · Huella tecnológica

2026-10-28 12:29 UTC · objetivo: IP de los 247 subdominios vivos (consulta a Team Cymru por DNS, no al objetivo)
$ grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' resueltos.txt | grep -vE '^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)' | sort -u > ips_publicas.txt
$ while read ip; do rev=$(echo "$ip" | awk -F. '{print $4"."$3"."$2"."$1}'); asn=$(dig +short "$rev.origin.asn.cymru.com" TXT | head -1 | tr -d '"' | cut -d'|' -f1 | tr -d ' '); echo "$ip AS$asn"; done < ips_publicas.txt > ip_asn.txt; wc -l ip_asn.txt
$ awk '{print $2}' ip_asn.txt | sort | uniq -c | sort -rn; for a in $(awk '{print $2}' ip_asn.txt | sort -u); do echo "$a = $(dig +short "$a.asn.cymru.com" TXT | tr -d '"' | awk -F'|' '{print $NF}')"; done
-> 146 IP públicas únicas (whois de IP no disponible: puerto 43 bloqueado -> ASN por DNS con Team Cymru)
-> AS13335 CLOUDFLARENET: 65 · AS396982 GOOGLE-CLOUD-PLATFORM: 61 · AS16509 AMAZON-02: 13 · AS14618 AMAZON-AES: 1
-> 6 IP con ASN "AS151691952743515" / "AS1516943515": ERROR DE MI COMANDO. Cymru devuelve varios ASN separados por espacios (IP anunciadas por varias redes) y el tr -d ' ' los pegó. Separados: 15169 (Google), 19527 (Google), 43515 (YouTube, de Google) -> son de Google
-> total corregido: Cloudflare 65 (45 %) · Google 67 (46 %) · AWS 14 (9 %)
por qué importa:
   · las hipótesis por rango de IP de la técnica 3 quedan CONFIRMADAS por ASN: pasan de suposición a dato
   · infraestructura propia en Google Cloud (coherente con "gitlab.com: Google Cloud Platform" del programa y con los cientos de nombres *.gke.gitlab.net); AWS minoritario y acotado (Snowplow, testbed híbridos) -> multinube con GCP como principal
   · casi la MITAD de las IP vivas (Google, 67) está expuesta directamente, sin el proxy/WAF de Cloudflare -> son las más interesantes para una fase activa (p. ej. registry.gitlab.com, alertmanager, *.env.release, *.testbed)
   · lección para la Parte 3: un fallo al procesar la salida de una herramienta generó dos "proveedores" inexistentes. Es el tipo de error (dato mal interpretado) que hay que buscar en el agente
siguiente: tecnologías e histórico de los dominios principales en Netcraft (web)

2026-10-28 12:38 UTC · objetivo: gitlab.com, about.gitlab.com (en alcance; consulta a Netcraft, no al objetivo)
$ navegador: https://sitereport.netcraft.com/?url=https://gitlab.com  y  ?url=https://about.gitlab.com
-> gitlab.com: visto por primera vez en nov-2012 · rank 105 · Cloudflare (AS13335) · titular "GitLab Inc., United States" · certificado DV de Sectigo (de 2026-10-26 a 2027-05-12), TLS 1.3, PFS
-> SAN del certificado: gitlab.com, auth.gitlab.com, customers.gitlab.com, email.customers.gitlab.com, gprd.gitlab.com, www.gitlab.com
-> cabeceras de seguridad: HSTS, CSP (+ report), X-Frame-Options SAMEORIGIN, X-Content-Type-Options, Referrer-Policy
-> rastreadores: Marketo y Optimizely (los dos sitios)
-> about.gitlab.com: visto por primera vez en ago-2014 · Cloudflare · mismas cabeceras y rastreadores
-> DISCREPANCIAS con datos propios: (1) Netcraft dice DNSSEC "Enabled", RDAP decía delegationSigned=false; (2) Netcraft muestra un SPF con zendesk, mktomail, salesforce, zuora, mailgun, sendergen y "-all", mientras que dig (11:56 UTC) devolvió el SPF de Valimail con macros y "~all"
por qué importa:
   · el titular "GitLab Inc." CONFIRMA la titularidad de gitlab.com, que RDAP ocultaba (técnica 1): dos fuentes, un dato
   · el certificado revela auth.gitlab.com y gprd.gitlab.com: subdominios de gitlab.com NO listados -> fuera de alcance (decisión 1), pero confirman el nombre de entorno "gprd" = producción
   · cabeceras de seguridad completas -> sitios bien endurecidos; además, las cabeceras que faltan están fuera del alcance del programa
   · Marketo + Optimizely = stack de marketing (Marketo ya salía en el SPF de Netcraft como mktomail)
   · DISCREPANCIAS: dos fuentes no coinciden -> no se elige una al azar; se comprueba en la fuente primaria y se fecha. Netcraft trabaja con datos cacheados ("fetched 18 days ago"); el SPF que muestra parece una versión antigua o expandida del dinámico de Valimail
siguiente: resolver las discrepancias con dig (DS/DNSKEY para DNSSEC, TXT para SPF)

2026-10-28 12:39 UTC · objetivo: gitlab.com (en alcance)
$ dig +short gitlab.com DS ; dig +short gitlab.com DNSKEY ; dig +short gitlab.com TXT | grep -i spf
-> DS: vacío · DNSKEY: vacío · SPF: "v=spf1 include:%{i}._ip.%{h}._ehlo.%{d}._spf.vali.email ~all"
por qué importa:
   · sin DS ni DNSKEY no hay DNSSEC -> RDAP tenía razón y NETCRAFT SE EQUIVOCA (dato desactualizado o mal detectado). Se mantiene "DNSSEC desactivado"
   · el SPF actual es el de Valimail; el de Netcraft es una versión ANTIGUA. No se descarta: es histórico útil -> antes enviaban correo con Zendesk (soporte), Salesforce (CRM), Zuora (facturación), Marketo (marketing), Mailgun y sendergen. Cuadra con Marketo (rastreador) y Mailgun (TXT de la técnica 2)
   · regla aplicada: ante dos fuentes que se contradicen, manda la fuente primaria consultada en vivo, con fecha. Lo mismo habrá que exigirle al agente (Parte 3)
siguiente: técnica 5, servicios expuestos con InternetDB (Shodan) sobre las IP que NO son de Cloudflare

### Técnica 5 · Servicios expuestos

2026-10-28 12:41 UTC · objetivo: 81 IP públicas de GitLab que NO son de Cloudflare (consulta a InternetDB de Shodan, no al objetivo; 1 s de pausa entre consultas)
$ grep -v 'AS13335' ip_asn.txt | awk '{print $1}' > ips_no_cloudflare.txt
$ while read ip; do curl -s "https://internetdb.shodan.io/$ip" > "raw/internetdb/$ip.json"; sleep 1; done < ips_no_cloudflare.txt
$ cat raw/internetdb/*.json | jq -r '.ports[]?' | sort -n | uniq -c | sort -rn | head -20
$ for f in raw/internetdb/*.json; do jq -r 'select((.vulns|length)>0) | "\(.ip) · \(.vulns|length) CVE · puertos \(.ports|join(","))"' "$f" 2>/dev/null; done
$ cat raw/internetdb/*.json | jq -r '.cpes[]?' | sort | uniq -c | sort -rn | head -20
$ python -I scripts/cruce_internetdb.py   (en Windows, sobre evidencias/: cruce IP -> subdominio con resueltos.txt; ver evidencias/scripts/)
-> puertos: 80 (30 IP), 443 (27), 22 (5), y decenas de puertos altos que aparecen exactamente 2 veces
-> CVE: solo 18.219.104.126 (82 CVE, PHP 8.0.30 + Apache 2.4.58, etiqueta eol-product)
-> CPE: google cloud_platform (13), amazon elastic_load_balancing (4), openssh 9.2p1 (3), debian (3), nginx 1.28.2, uvicorn, gitlab:gitlab, ubuntu, openssh 8.9p1
-> cruce: 18.219.104.126 = events.gitlab.net / snowplow.trx.gitlab.net (ELB de AWS) PERO Shodan la ve también como pizzaraul.work. Igual: 184.34.202.116 -> pelsisdigital.com, 3.151.120.142 -> seinetwork.io
-> cruce: los "miles de puertos" son 2 IP: 34.102.251.100 (api.corpsecdevices.gitlab.net, 675 puertos) y 34.160.8.21 (promlens.gitlab.net, 834 puertos)
-> cruce: SSH 22 en dev.gitlab.org (Ubuntu, OpenSSH 8.9p1, + nginx, gitlab:gitlab, puerto 5005) y en gitlab.19-0 / 19-2 / 19-3-stable-security-get.env.release.gitlab.net (Debian, OpenSSH 9.2p1)
-> cruce: certificado autofirmado en 34.138.170.206 (comp-calculator, conservatory, nominatorbot.gitlab.net)
-> cruce: production.teleport.gitlab.net solo expone 443; etiqueta "pqc" (criptografía post-cuántica) en varios servicios de GCP
por qué importa:
   · FALSO POSITIVO DEMOSTRADO: las 82 CVE, el PHP 8.0.30 (sin soporte) y Apache 2.4.58 son de OTRO cliente (pizzaraul.work) que compartió esa IP de balanceador de AWS. Las IP de los ELB rotan y se reutilizan entre clientes. NO se atribuye a GitLab. Error típico a buscar en el agente (Parte 3): atribuir al objetivo datos de un tercero
   · los "miles de puertos" son balanceadores de Google que aceptan cualquier conexión: artefacto, no servicios -> se descartan
   · dev.gitlab.org (EN ALCANCE por *.gitlab.org): instancia GitLab de desarrollo expuesta directamente, con SSH y el puerto 5005 (habitual en el registro de contenedores de GitLab) -> CANDIDATO A PUNTO DE INTERÉS
   · instancias *.env.release con SSH abierto a internet, aunque la empresa usa Teleport como puerta de acceso -> ¿por qué no pasan por Teleport? Candidatas a punto de interés
   · certificado autofirmado = herramientas internas montadas con menos cuidado -> observación
   · Shodan solo ve lo que escaneó: 3 IP sin datos y las de Cloudflare excluidas a propósito (enseñarían los puertos de Cloudflare, no los de GitLab)
siguiente: técnica 6, robots.txt y security.txt de los sitios web en alcance

2026-10-31 (revisión) · objetivo: evidencias/internetdb/ (sin consultas externas)
$ python -I scripts/cruce_internetdb.py   (al rehacer el cruce para que el cuaderno sea repetible)
-> de los 81 JSON: 34 con datos · 3 "No information available" · 44 {"error": "Rate limit exceeded"}
por qué importa:
   · ERROR MÍO: el sleep 1 fue demasiado rápido y InternetDB cortó las consultas. El resumen con jq (.ports[]?) ignoraba esos ficheros SIN AVISAR, y anoté "3 IP sin datos" cuando en realidad 44 IP NO SE HABÍAN CONSULTADO (entre ellas registry.gitlab.com, candidato a punto de interés)
   · fallo silencioso: un error de la herramienta leído como "no hay nada". Es exactamente lo que hay que buscar en el agente (Parte 3)
   · se corrige el script para distinguir error / sin datos / con datos, y se repiten solo las 44
siguiente: repetir las 44 IP con más pausa y reintentos

2026-10-31 17:34 UTC (fin 17:39 UTC) · objetivo: las 44 IP públicas de GitLab que dieron error (consulta a InternetDB de Shodan, no al objetivo; 3 s de pausa y hasta 3 reintentos)
$ grep -l '"error"' raw/internetdb/*.json | xargs -n1 basename | sed 's/\.json$//' > ips_internetdb_repetir.txt; wc -l ips_internetdb_repetir.txt
$ while read ip; do for i in 1 2 3; do curl -s "https://internetdb.shodan.io/$ip" > "raw/internetdb/$ip.json"; grep -q '"error"' "raw/internetdb/$ip.json" || break; sleep 10; done; sleep 3; done < ips_internetdb_repetir.txt; echo "siguen con error: $(grep -l '"error"' raw/internetdb/*.json | wc -l)"
$ python -I scripts/cruce_internetdb.py   (en Windows, tras traer raw/internetdb con scp -r)
-> 44 de 44 consultadas · siguen con error: 0. Total técnica 5: 71 IP con datos · 10 sin datos · 0 errores
-> OJO, dos fechas: 37 IP consultadas el 2026-10-28 y 44 el 2026-10-31
-> registry.gitlab.com (35.227.35.254): solo 80 y 443, sin CPE ni CVE; Shodan lo nombra registry.gitlab.com y www.registry.gitlab.com
-> 8 IP más con SSH (22): gitlab.18-11-stable-security-get y gitlab.custom-models-online/offline-get (.env.release, Debian, OpenSSH 9.2p1 y 10.0p2) · policy-framework-preview.gitlab.net (GitLab sobre Ubuntu, OpenSSH 9.6p1) · 1k/2k/10k.testbed.gitlab.net (SSH en 22 y 2222, OpenSSH 8.9p1) · kas.ops / registry.ops.gitlab.net
-> otra IP de ELB de AWS de events.gitlab.net compartida con un tercero (dicomassist.app)
-> 77.112.131.85 (snowplowprd.trx.gitlab.net): akka_http 10.2.9 + 1 CVE (CVE-2023-33251), SIN nombres de terceros
-> 2 balanceadores más de Google con cientos de puertos (corpsec-fleet-hooks: 437 · grafana.northstar.autoflow: 325)
-> sin datos (7 nuevas): teleport staging, 50k.testbed, workops, bizops, gitway-gprd, package-hunter, 19-4-stable
por qué importa:
   · registry.gitlab.com sigue siendo interesante por estar en GCP DIRECTO, sin Cloudflare (técnica 3), pero Shodan no ve nada raro: solo web. Ahora es un dato, antes era un hueco
   · SSH abierto a internet pasa de 4 a 12 IP (sin contar los balanceadores de cientos de puertos; por eso el "22 (5)" del 28/10 incluía 1 artefacto). Refuerza el patrón de la técnica 5: entornos de prueba y de versiones (.env.release, testbed) con SSH directo aunque la empresa usa Teleport. Y aparece ops.gitlab.net (la instancia interna de operaciones, técnica 7) con SSH -> punto de interés más sólido
   · el 2222 en los testbed es el puerto SSH alternativo típico de GitLab en contenedor: cuadra con que sean instalaciones de prueba de GitLab (arquitecturas de referencia)
   · ya son 4 los terceros vistos en las IP de los ELB de AWS (pizzaraul.work, pelsisdigital.com, seinetwork.io, dicomassist.app) -> CONFIRMA que las IP de ELB se reutilizan entre clientes y que lo que Shodan ve en ellas NO es atribuible a GitLab
   · CONTRASTE con el falso positivo: en 77.112.131.85 Shodan solo ve nombres de GitLab, y akka-http es la base del colector de Snowplow (el servicio de events/snowplow). Esta CVE SÍ podría ser de GitLab. Pero InternetDB deduce la CVE por la versión (CPE), no la comprueba -> CANDIDATO a verificar, no hallazgo
   · lección: ante un dato de una IP compartida, la pregunta es "¿qué otros nombres ve la fuente en esa IP?". Si hay terceros, no se atribuye; si solo hay del objetivo, se marca como candidato
siguiente: técnica 6 ya hecha (ver abajo); cerrar la técnica 8 (patrón de Hunter)

### Técnica 6 · Ficheros expuestos

2026-10-28 12:46 UTC · objetivo: gitlab.com, about, docs, customers, design, advisories (.gitlab.com) y dev.gitlab.org (todos en alcance). 14 peticiones GET a ficheros públicos, 1 s de pausa, tráfico equivalente al de un navegador
$ mkdir -p raw/ficheros; for h in gitlab.com about.gitlab.com docs.gitlab.com customers.gitlab.com design.gitlab.com advisories.gitlab.com dev.gitlab.org; do for f in robots.txt .well-known/security.txt; do out="raw/ficheros/${h}_$(basename $f)"; code=$(curl -s -m 10 -o "$out" -w "%{http_code}" "https://$h/$f"); echo "$h/$f -> HTTP $code · $(wc -l < "$out") líneas"; sleep 1; done; done
-> robots.txt 200: gitlab.com (117 líneas), dev.gitlab.org (117), about (45), docs (16), customers (5), advisories (4) · design: 302
-> security.txt: 200 solo en gitlab.com (36 líneas) · 404 en about y customers · 302 en docs, design, advisories y dev.gitlab.org
-> copiados a evidencias/ficheros/ y leídos enteros
-> robots de gitlab.com y de dev.gitlab.org: IDÉNTICOS byte a byte (diff). El propio fichero dice que se basa en config/routes.rb del código público de GitLab
-> customers.gitlab.com: "Disallow: /admins/"
-> about.gitlab.com: comentario "nuxt-robots"; bloquea crawlers de IA (GPTBot, ClaudeBot...) en /resources/it-revolution/
-> docs, design y advisories: el 302 apunta a projects.gitlab.io/auth?domain=... (control de acceso de GitLab Pages)
-> dev.gitlab.org/.well-known/security.txt -> redirige a /users/sign_in
-> security.txt de gitlab.com: firmado con PGP, Contact y Policy -> hackerone.com/gitlab, Canonical, Expires 2027-01-31, Preferred-Languages: en
por qué importa:
   · el robots.txt de gitlab.com es el POR DEFECTO del producto (igual en cualquier GitLab): /admin, /api/v* NO son hallazgos. Anotarlo como "ruta de admin descubierta" sería sobreinterpretar (error que hay que vigilar en el agente)
   · que el de dev.gitlab.org sea idéntico + la redirección a sign_in CONFIRMAN que dev.gitlab.org es una instancia GitLab privada que pide login (cuadra con gitlab:gitlab de Shodan, técnica 5)
   · customers.gitlab.com/admins/ SÍ es específico: ruta del panel de administración del portal de clientes y facturación (en alcance, severidad crítica) -> CANDIDATO A PUNTO DE INTERÉS. No se visita: queda para la fase activa
   · docs, design y advisories son GitLab Pages (cuadra con los CNAME a gitlab.io de la técnica 3); about.gitlab.com está hecho con Nuxt (Vue.js) -> huella tecnológica
   · security.txt modélico (RFC 9116, firmado, con caducidad) y apuntando al mismo programa de HackerOne -> confirma el canal oficial del alcance
siguiente: técnica 7, Google dorks (navegador)

### Técnica 7 · Google dorks

2026-10-28 12:53 UTC · objetivo: dominios en alcance (consulta a Google, no al objetivo; 8 búsquedas en el navegador con 5-7 s de pausa; solo se lee la página de resultados, no se abre ningún enlace)
$ dork 1: site:gitlab.net -site:runway.gitlab.net
-> ~7 páginas. ops.gitlab.net "Internal GitLab for Operations" (login) · log.gprd.gitlab.net "Welcome to Elastic... Okta" · portal.gitlab.net y portal.staging "Engineering Portal" · theseus.gitlab.net (docs de la plataforma interna de desarrollo: Hangar, Caproni, common-ci-tasks) · comp-calculator.gitlab.net "no longer available... Workday"
$ dork 2: site:gitlab.org -site:about.gitlab.org   (la exclusión no tiene efecto: about está en .com; error menor del dork)
-> ~3 páginas. dev.gitlab.org: "GitLab Community Edition", login "sign in with Google", grupos públicos indexados (Samples, Cookbooks), página de términos RGPD · le-43521838.version-production.gitlab.org "GitLab - Versions" (login)
$ dork 3: site:gitlap.com -> 0 resultados
$ dork 4: (site:gitlab.net OR site:gitlab.org OR site:gitlap.com) filetype:pdf -> 0 resultados
$ dork 5: (site:gitlab.net OR site:gitlab.org) intitle:"index of"
-> pulp.pre.gitlab.net: listados de directorio del repositorio de paquetes (gitlab-ce / gitlab-ee, el/8, amazon/2022, SRPMS) · runway-docs-*.runway.gitlab.net (FUERA de alcance: no se usa)
$ dork 6: site:gitlab.net (intitle:grafana OR intitle:kibana OR intitle:sentry OR intitle:dashboard)
-> ops.gitlab.net/gitlab-org/grafana-dashboards (repo público en la instancia de ops) · contributors-svc.staging.runway.gitlab.net (FUERA de alcance)
$ dork 7: (site:gitlab.net OR site:gitlab.org OR site:gitlap.com) (ext:log OR ext:env OR ext:sql OR ext:bak OR ext:conf) -> 0 resultados
$ dork 8: site:customers.gitlab.com
-> ~2 páginas. Portal de suscripciones, pagos y facturas; compra de almacenamiento y de minutos de cómputo; inicio de sesión con enlace de un solo uso por correo ("one-time sign-in link") o con la cuenta de GitLab.com
por qué importa:
   · lo NEGATIVO también es dato: 0 PDF, 0 ficheros sensibles (log/env/sql/bak/conf) y 0 resultados de gitlap.com -> buena higiene de indexación
   · Okta en el login de Kibana (log.gprd) -> NUEVO proveedor de identidad para herramientas internas, además de Google Workspace (técnica 2). Workday = RR. HH. (SaaS de terceros: fuera)
   · ops.gitlab.net es una instancia GitLab interna de operaciones, con algún repositorio público indexado (grafana-dashboards)
   · theseus.gitlab.net publica documentación de la plataforma interna de desarrollo (nombres de herramientas internas, arquitectura modular sobre GKE) -> fuga de información de bajo impacto, pero útil para entender la arquitectura
   · dev.gitlab.org = GitLab CE con login de Google y grupos públicos -> 3.ª fuente que confirma qué es (Shodan + robots + dorks)
   · pulp.pre.gitlab.net: listado de directorios ABIERTO en un repositorio de paquetes de PREproducción. Los paquetes de GitLab son públicos, así que el impacto es bajo, pero un listado abierto en preproducción es una mala práctica -> observación
   · customers.gitlab.com: login con enlace mágico por correo + flujos de pago -> superficie de autenticación y de pagos del activo crítico, coherente con su /admins/ (técnica 6)
   · los dorks se cuelan en lo que está fuera de alcance (runway): hay que filtrar los resultados, no solo la consulta
siguiente: técnica 8, correos y patrón de correo (theHarvester)

### Técnica 8 · Correos

2026-10-28 12:57 UTC · objetivo: gitlab.com (en alcance; fuentes públicas, no se consulta al objetivo)
$ theHarvester -d gitlab.com -b crtsh,duckduckgo,hackertarget,otx,rapiddns,urlscan -l 200 -f raw/harvester_gitlab.com > raw/harvester_gitlab.com.txt 2>&1
$ grep -oiE '[a-z0-9._%+-]+@gitlab\.com' raw/harvester_gitlab.com.txt | sort -u > correos.txt
-> correos @gitlab.com: 0. theHarvester termina bien ("Reporting started... JSON File saved"): las 6 fuentes gratuitas no tienen correos -> resultado NEGATIVO, no fallo
-> de rebote, hosts de gitlab.com: support.gitlab.com -> gitlab.zendesk.com · status.gitlab.com -> 34754878.hostedstatus.com (Status.io)
por qué importa:
   · sin fuentes de pago, theHarvester no ve correos de GitLab -> hay que usar la otra herramienta de referencia de la consigna (Hunter.io)
   · support -> Zendesk y status -> Status.io son SaaS de TERCEROS: es justo POR QUÉ el programa excluye support.gitlab.com y status.gitlab.com. Las exclusiones del alcance quedan validadas con datos (y Zendesk ya salía en el SPF antiguo de Netcraft)
siguiente: Hunter.io

2026-10-28 13:12 UTC · objetivo: gitlab.com (consulta a Hunter.io, tercero; cuenta gratuita creada por mí en Hunter, NO en un servicio de GitLab)
$ navegador: https://hunter.io/search/gitlab.com (Domain Search)
-> 651 correos @gitlab.com indexados: personas 375 · cargos directivos 3 · genéricos 276
-> por departamento: IT/Engineering 43 · Support 4 · Writing & Communication 3 · Sales 2 · Marketing 2 · Executive 1 · Finance 1 · Management 1 · Arts & Design 1 · Product 1 · Procurement 1 · desconocido 315
-> la web (plan gratuito) NO muestra el patrón; no se revela ningún correo individual (datos personales, y no hacen falta)
por qué importa:
   · 651 correos públicos = superficie de phishing e ingeniería social enorme (fuera de alcance aquí, pero va al mapa)
   · IT/Engineering es el departamento más expuesto: son los que tienen acceso a la infraestructura (Vault, Teleport, ArgoCD...)
   · en el mapa van las CIFRAS y el PATRÓN, nunca la lista de correos
siguiente: obtener el patrón con la API de Hunter (domain-search devuelve "pattern") desde PowerShell de Windows, con la clave pedida de forma oculta (nunca en la Kali compartida)

2026-10-31 ~17:46 UTC (hora aproximada, tomada al recibir la salida) · objetivo: gitlab.com (en alcance; consulta a la API de Hunter.io, tercero; desde PowerShell de Windows, no desde la Kali)
$ $k = Read-Host "Clave de Hunter" -AsSecureString
$ $key = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($k))
$ (Invoke-RestMethod "https://api.hunter.io/v2/domain-search?domain=gitlab.com&limit=1&api_key=$key").data | Select-Object domain, pattern, organization
$ Remove-Variable key, k
-> domain: gitlab.com · pattern: {f}{last} · organization: GitLab
por qué importa:
   · PATRÓN DE CORREO: inicial del nombre + apellido, todo junto (formato <inicial><apellido>@gitlab.com). Con un nombre público (web, LinkedIn, charlas) se puede deducir el correo de cualquier empleado
   · combinado con los 651 correos indexados y con IT/Engineering como departamento más expuesto: superficie de phishing dirigido muy grande. La ingeniería social y el contacto con empleados están FUERA del alcance del programa y de este proyecto -> va al mapa como dato de contexto, no como vía de ataque
   · el contrapeso es fuerte: DMARC p=reject al 100 % (técnica 2) impide suplantar @gitlab.com desde fuera, y el login de las herramientas internas pasa por Google y Okta (técnicas 2 y 7)
   · limit=1: el patrón viene igual con 1 resultado, así que no se descarga ningún correo personal. La clave se pide oculta y se borra de memoria; nunca toca la Kali compartida, el chat ni las capturas
   · UNA SOLA FUENTE: theHarvester dio 0 correos, así que no hay segunda fuente con la que contrastar el patrón. Hunter lo INFIERE de los correos que tiene indexados -> se presenta como "patrón según Hunter", no como dato confirmado
siguiente: técnicas obligatorias completas -> mapa.md
