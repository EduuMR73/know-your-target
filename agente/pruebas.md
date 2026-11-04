# Pruebas del agente · GitLab (HackerOne)

Pruebas de la Parte 2 con `aap-base` (commit `6068423`), en la Kali del laboratorio (`alumno3`).
El `scope.txt` es **el mismo de la Parte 1** (copiado tal cual a `~/aap-base/scope.txt`).

## Preparación

| Cuándo | Qué hice | Qué salió |
|---|---|---|
| 2026-11-04 ~11:55 UTC | `git status` en `~/aap-base` | Los 19 ficheros salían como modificados. Con `git diff -w --ignore-cr-at-eol` no quedaba ningún cambio real: eran finales de línea `CRLF` de Windows. Se restauraron con `git restore .` y un control previo que abortaba si había cambios reales |
| 2026-11-04 ~11:57 UTC | `git pull` | Avance rápido `d89f296..6068423`: 5 commits del profesor (IA del aula, DNS y crt.sh incluidas, RDAP directo) |
| 2026-11-04 ~11:58 UTC | `pytest -q alcance motor herramientas` | `44 passed` |
| 2026-11-04 ~11:59 UTC | `scp` del `scope.txt` de la Parte 1 a la Kali; `file scope.txt` | `Unicode text, UTF-8 text` (sin `CRLF`) |

## 2.1 Comprobación del alcance (`scope.txt`)

**2026-11-04 12:00 UTC** · `$ .venv/bin/python comprobar_alcance.py` (script en [`src/comprobar_alcance.py`](src/comprobar_alcance.py))

El script carga las reglas con las mismas funciones que usa el `scope-guard` (`cargar` y `en_alcance` de `alcance/alcance.py`), así que lo que se comprueba es el código real del agente. La batería A usa un `scope.txt` temporal con el alcance del ejemplo. La batería B usa mi `scope.txt`.

Cómo decide el `scope-guard`, en este orden: 1) normaliza el objetivo (quita esquema, puerto, ruta y mayúsculas); 2) las exclusiones `!` ganan siempre; 3) coincidencia exacta; 4) comodines y rangos; 5) todo lo demás queda fuera (lista blanca).

### A) Batería de ejemplo del enunciado

`scope.txt` de ejemplo: `*.empresa.com`, `!blog.empresa.com`, `10.10.0.0/24`, `!10.10.0.1`.

| Objetivo | Regla que prueba | Esperado | Obtenido | ¿OK? |
|---|---|---|---|---|
| `api.empresa.com` | comodín *.empresa.com | Dentro | Dentro | ✅ |
| `https://API.Empresa.com/login` | normaliza esquema, mayúsculas y ruta | Dentro | Dentro | ✅ |
| `blog.empresa.com` | exclusión !blog | Fuera | Fuera | ✅ |
| `empresa.com` | el comodín no incluye el dominio raíz | Fuera | Fuera | ✅ |
| `empresa.com.evil.net` | sufijo engañoso | Fuera | Fuera | ✅ |
| `otraempresa.com` | otra empresa (lista blanca) | Fuera | Fuera | ✅ |
| `10.10.0.7` | rango 10.10.0.0/24 | Dentro | Dentro | ✅ |
| `http://10.10.0.7:8080/admin` | normaliza puerto y ruta | Dentro | Dentro | ✅ |
| `10.10.0.1` | IP excluida !10.10.0.1 | Fuera | Fuera | ✅ |
| `10.10.1.7` | IP fuera del rango | Fuera | Fuera | ✅ |

**10/10 correctos**

### B) Casos reales de GitLab (mi `scope.txt`)

| Objetivo | Regla que prueba | Esperado | Obtenido | ¿OK? |
|---|---|---|---|---|
| `gitlab.com` | dominio exacto | Dentro | Dentro | ✅ |
| `https://Docs.GitLab.com/ee/api/` | exacto docs.gitlab.com + normalización | Dentro | Dentro | ✅ |
| `dev.gitlab.org` | comodín *.gitlab.org | Dentro | Dentro | ✅ |
| `ops.gitlab.net` | comodín *.gitlab.net | Dentro | Dentro | ✅ |
| `gitlab.org` | el comodín *.gitlab.org no incluye la raíz | Fuera | Fuera | ✅ |
| `www.gitlab.com` | no hay *.gitlab.com: solo hosts exactos | Fuera | Fuera | ✅ |
| `runway.gitlab.net` | exclusión !runway.gitlab.net | Fuera | Fuera | ✅ |
| `x.runway.gitlab.net` | exclusión !*.runway.gitlab.net gana al comodín | Fuera | Fuera | ✅ |
| `support.gitlab.com` | exclusión !support.gitlab.com | Fuera | Fuera | ✅ |
| `gitlab.com.evil.net` | sufijo engañoso | Fuera | Fuera | ✅ |
| `evilgitlab.net` | parecido pero no es subdominio | Fuera | Fuera | ✅ |
| `github.com` | otra empresa (lista blanca) | Fuera | Fuera | ✅ |

**12/12 correctos**

### Por qué elegí estos casos

Cada caso real comprueba una decisión de [`alcance.md`](../alcance.md):

- `gitlab.org` fuera → **decisión 2**: un comodín no incluye el dominio raíz.
- `www.gitlab.com` fuera → **decisión 1**: `gitlab.com` no tiene comodín; solo entran los hosts que el programa lista uno por uno.
- `runway.gitlab.net` y `x.runway.gitlab.net` fuera → **decisión 6**: la exclusión del programa (`*.runway.gitlab.net`) no cubre la raíz, que entraría por `*.gitlab.net`. Por eso añadí `!runway.gitlab.net`. Sin esa línea, este caso habría salido **Dentro**.
- `gitlab.com.evil.net` y `evilgitlab.net` → intentos de engañar una comparación de texto ingenua (por ejemplo, "contiene `gitlab.com`").

No hizo falta corregir el `scope.txt`: todos los casos salieron como se esperaba a la primera.

## 2.2 Herramientas

### Qué herramientas tiene el agente

| Herramienta | Origen | Qué obtiene | Técnica de la Parte 1 |
|---|---|---|---|
| `whois_dominio` | Ejemplo de `aap-base` | Registro del dominio (WHOIS con respaldo RDAP) | 1 |
| `dns_registros` | Incluida en `aap-base` (commit `6068423`) | Registros A, AAAA, MX, NS, TXT, CNAME y SOA | 2 |
| `subdominios_crtsh` | Incluida en `aap-base` (commit `6068423`) | Subdominios de certificados, filtrados por alcance | 3 |
| **`ficheros_expuestos`** | **Propia** | `robots.txt` y `/.well-known/security.txt` | 6 |
| **`infraestructura_dominio`** | **Propia** | Resuelve el dominio (A) y consulta InternetDB por cada IP | 5 (+ la opcional de resolver subdominios) |

El enunciado pide al menos dos herramientas además de `whois_dominio`. Pone `dns_registros` y `subdominios_crtsh` como ejemplo, pero la versión actual de `aap-base` ya las incluye hechas por el profesor. Por eso he escrito **dos herramientas propias más**. Código: [`src/bloque_herramientas_propias.py`](src/bloque_herramientas_propias.py), que se añade al final de `herramientas/tus_herramientas.py`, y registro en `lanzar.py`.

### Cómo cumplen las reglas de los apuntes

| Regla | `ficheros_expuestos` | `infraestructura_dominio` |
|---|---|---|
| Protegida por el `scope-guard` | `@protegida(objetivo="dominio")` | `@protegida(objetivo="dominio")` |
| Sin shell | Solo `urllib` (HTTP desde Python) | `dig` con lista de argumentos, sin `shell=True` |
| Tiempo máximo | 20 s por fichero | 20 s para `dig` y 20 s por IP |
| Salida recortada | Lee como máximo 20 KB; 1400 caracteres por fichero y 3000 en total | Como máximo 5 IP (`MAX_IPS`); 3000 caracteres |
| Filtrada por el alcance | Solo sigue redirecciones a hosts en alcance (ver abajo) | Omite los *hostnames* de InternetDB que están fuera del alcance y dice cuántos omite |
| Errores como texto | `HTTP 404 (...)`, `BLOQUEADO: redirección...`, `ERROR: ...` | Distingue `SIN DATOS` (404) de `ERROR: límite de peticiones` (429) |
| Ritmo | 2 peticiones por llamada | Pausa de 1,5 s entre IP |

**Decisiones de diseño**

1. **El `scope-guard` se podía rodear con una redirección.** `@protegida` solo comprueba el **argumento** de la herramienta, pero `urllib` sigue las redirecciones HTTP (301/302) **solo**. Si `about.gitlab.com/robots.txt` respondiera "muévete a `otraempresa.com`", la herramienta acabaría pidiendo un host fuera de alcance sin que nadie lo comprobara. Por eso `ficheros_expuestos` usa su propio manejador (`_RedireccionEnAlcance`), que pasa **cada salto** por `filtrar()` del `scope-guard` y lo corta si sale del alcance. Lo comprobé con un servidor HTTP local: la redirección a `evil.example` se bloquea y la redirección interna se sigue.
2. **`infraestructura_dominio` recibe un dominio, no una IP.** Mi `scope.txt` no tiene IP (el programa autoriza dominios), así que una herramienta que recibiera una IP quedaría siempre `BLOQUEADO`. El guardia comprueba el dominio, y las IP salen de resolver un dominio autorizado. Aun así, la IP puede ser de un CDN o de un tercero, y la propia herramienta se lo advierte al modelo.
3. **"Sin datos" no es lo mismo que "error".** En la Parte 1 (técnica 5), 44 IP devolvieron `Rate limit exceeded` y al principio las anoté como "sin datos". Esta herramienta lo distingue explícitamente, para que el agente no cometa el mismo error.
4. **Las CVE solo se cuentan** y se marcan "sin verificar": InternetDB las deduce por versión. En la Parte 1 ya vi un falso positivo de 82 CVE.

### Pruebas automáticas

**2026-11-04 ~12:05 UTC** · `$ .venv/bin/python -m pytest -q alcance motor herramientas` → `1 failed, 53 passed`

- [`src/test_mis_herramientas.py`](src/test_mis_herramientas.py) tiene 10 pruebas sin red: las dos herramientas están activas y protegidas; fuera de alcance devuelven `BLOQUEADO` **sin ejecutar `dig` ni salir a la red**; una redirección fuera de alcance se bloquea; se filtran los *hostnames* y se descartan los CNAME; se distingue el límite de peticiones de "sin datos"; y se respeta `MAX_IPS`.
- **El fallo es esperado:** `test_recon.py::test_tres_herramientas_disponibles_en_prompt_y_motor` comprueba que la lista `HERRAMIENTAS` tenga **exactamente** las 3 herramientas iniciales. Ahora tiene 5 porque añadí las mías (`Left contains 2 more items, first extra item: 'ficheros_expuestos'`). No es un error del código: el test hace su trabajo, que es avisar de que la lista cambió.

### Prueba manual (dentro y fuera del alcance)

**2026-11-04 12:06 UTC** · `$ .venv/bin/python probar_herramientas.py | tee salida/prueba_manual.txt` (script en [`src/probar_herramientas.py`](src/probar_herramientas.py))

**Fuera de alcance: las 5 herramientas.** No basta con probar las mías: tienen que estar protegidas todas.

| Herramienta | `support.gitlab.com` (excluido) | `github.com` (otra empresa) |
|---|---|---|
| `whois_dominio` | `BLOQUEADO` ✅ | `BLOQUEADO` ✅ |
| `dns_registros` | `BLOQUEADO` ✅ | `BLOQUEADO` ✅ |
| `subdominios_crtsh` | `BLOQUEADO` ✅ | `BLOQUEADO` ✅ |
| `ficheros_expuestos` | `BLOQUEADO` ✅ | `BLOQUEADO` ✅ |
| `infraestructura_dominio` | `BLOQUEADO` ✅ | `BLOQUEADO` ✅ |

Además de la respuesta, el `scope-guard` deja un aviso en el log por cada bloqueo:

```
bloqueado ficheros_expuestos(dominio='support.gitlab.com')
bloqueado infraestructura_dominio(dominio='github.com')
ficheros_expuestos(dominio='support.gitlab.com') -> BLOQUEADO: support.gitlab.com está fuera del alcance autorizado.
```

**Dentro del alcance**

`ficheros_expuestos(dominio="about.gitlab.com")`:

```
/robots.txt -> HTTP 200 (URL final: https://about.gitlab.com/robots.txt)
# START nuxt-robots (indexable)
User-agent: *
Disallow: /search/
...
Disallow: /api/
Disallow: /exp/
...
# Partner papers are noindexed; AI crawlers still fetch and cite page copy, so block the folder.
User-agent: GPTBot
...
Disallow: /resources/it-revolution/
...
/.well-known/security.txt -> HTTP 404 (Not Found): no disponible o acceso denegado.
```

`infraestructura_dominio(dominio="dev.gitlab.org")`:

```
dev.gitlab.org resuelve a 1 IP:
- 34.139.135.192: puertos [22, 80, 443, 5005]; hostnames en alcance ['dev.gitlab.org'] (1 fuera de alcance omitidos); CPE ['cpe:/a:ruby-lang:ruby', 'cpe:/o:canonical:ubuntu_linux', 'cpe:/a:openbsd:openssh:8.9p1', 'cpe:/a:f5:nginx', 'cpe:/a:rubyonrails:rails', 'cpe:/a:gitlab:gitlab']; etiquetas ['cloud', 'pqc']; CVE que lista Shodan: 0 (sin verificar, deducidas por versión)
```

**Contraste con la Parte 1**

| Dato | Parte 1 (a mano, 2026-10-28) | Herramienta (2026-11-04) | ¿Coincide? |
|---|---|---|---|
| `robots.txt` de `about.gitlab.com` | 200, `nuxt-robots` con `/search/`, `/api/` y `/exp/` | Igual | Sí |
| `security.txt` de `about.gitlab.com` | 404 (`curl -o` guardó la página HTML de error) | `HTTP 404`, sin cuerpo | Sí, y la herramienta lo dice más claro |
| Puertos de `34.139.135.192` | 22, 80, 443, 5005 | 22, 80, 443, 5005 | Sí |
| CPE | 4 (GitLab, nginx, Ubuntu, OpenSSH 8.9p1) | 6 (además, Ruby y Rails) | Parcial: InternetDB actualizó sus datos entre las dos fechas |
| *Hostnames* | `dev.gitlab.org` y `192.135.139.34.bc.googleusercontent.com` | `dev.gitlab.org` (1 omitido) | Sí: el omitido es el DNS inverso de Google Cloud, fuera de alcance, y se filtra bien |

**Por qué importa**

- `dev.gitlab.org` expone **SSH (22)** y un puerto poco común, el **5005**, en una IP de Google Cloud sin CDN delante. Coincide con el punto de interés de la Parte 1.
- El `robots.txt` de `about.gitlab.com` bloquea **expresamente a los rastreadores de IA** (`GPTBot`, `ClaudeBot`, etc.) en `/resources/it-revolution/`. No es un riesgo de seguridad, pero dice algo de la organización: protege contenido de partners frente al scraping.

## 2.3 Cómo se construye el prompt

`motor/prompt.py` monta el prompt de sistema rellenando dos huecos de la plantilla `instrucciones.md`:

```
instrucciones.md (texto fijo)
   {alcance}       <- scope.txt: línea "Autorizado: ..." y línea "Excluido (nunca): ..."
   {herramientas}  <- lista HERRAMIENTAS de lanzar.py: "- nombre: primera línea del docstring"
   = prompt de sistema
```

### Prompt final (el que usa el agente)

**2026-11-04 ~12:20 UTC** · `$ .venv/bin/python lanzar.py --ver-prompt > salida/prompt_final.txt`

```
Eres un analista de reconocimiento pasivo dentro de una auditoría autorizada
(programa público de bug bounty). Trabajas solo con las herramientas que se te dan.

## Objetivo y alcance

El objetivo te lo da el usuario. Solo puedes investigar lo que esté dentro de este
alcance autorizado:

Autorizado: *.gitlab.net, *.gitlab.org, *.gitlap.com, gitlab.com, registry.gitlab.com, customers.gitlab.com, about.gitlab.com, docs.gitlab.com, design.gitlab.com, advisories.gitlab.com
Excluido (nunca): *.runway.gitlab.net, runway.gitlab.net, *.gitlab-private.org, *.gitlab.cn, *.service-now.com, alerts.gitlab.com, aptly.gitlab.com, dashboards.gitlab.com, federal-support.gitlab.com, forum.gitlab.com, ir.gitlab.com, levelup.gitlab.com, packages.gitlab.com, partners.gitlab.com, shop.gitlab.com, status.gitlab.com, support.gitlab.com, translate.gitlab.com, us-federal-gitlab.com, gitlab.biterg.io, gitlabdemo.cloud, gitlabsandbox.net, gitlabtraining.cloud

Si una herramienta te responde `BLOQUEADO`, ese objetivo está fuera: no insistas ni
lo intentes por otro camino (otra herramienta, otro nombre, una IP o una URL del
mismo host); anótalo como "fuera de alcance" y sigue con otra cosa. Si el usuario
te pide algo fuera de alcance, no lo investigues y dilo en el informe.

## Herramientas disponibles

- whois_dominio: Consulta el registro WHOIS de un dominio. Devuelve registrador,
- dns_registros: Consulta registros DNS de un dominio. tipo: A, AAAA, MX, NS, TXT, CNAME o SOA.
- subdominios_crtsh: Enumera subdominios de un dominio por transparencia de certificados (crt.sh).
- ficheros_expuestos: Lee robots.txt y /.well-known/security.txt (RFC 9116) de un dominio por HTTPS.
- infraestructura_dominio: Puertos, servicios y CVE que Shodan (InternetDB) ya vio en las IP de un dominio.

## Orden de trabajo

1. Registro del dominio (`whois_dominio`).
2. DNS: NS, MX y TXT (`dns_registros`).
3. Subdominios (`subdominios_crtsh`).
4. Ficheros expuestos de los sitios web en alcance (`ficheros_expuestos`).
5. Infraestructura de los hosts más interesantes (`infraestructura_dominio`).

## Límites

- Como máximo **12 llamadas a herramientas** en total. Elige las que más aporten y no
  repitas una consulta que ya hiciste. Al llegar a 12, escribe el informe.
- Solo técnicas pasivas. Todas las herramientas consultan fuentes públicas de
  terceros, salvo `ficheros_expuestos`, que solo lee `robots.txt` y `security.txt`:
  ficheros públicos pensados para ser leídos. Nada de escaneos ni fuerza bruta.
- Ritmo bajo: el programa prohíbe la actividad de alto volumen.

## Cómo interpretar los resultados

- `SIN DATOS` no es lo mismo que `ERROR`. Un error (límite de peticiones, tiempo
  agotado) significa que **no se sabe**, no que no haya nada.
- Un subdominio en certificados no demuestra que el host exista hoy.
- Una IP puede ser de un CDN o de un tercero (Cloudflare, AWS, Google Cloud): no la
  presentes como "servidor de GitLab" sin más.
- Las CVE de InternetDB se deducen por versión y **no están verificadas**.

## Informe

Termina con un informe en Markdown. Para **cada dato**, indica qué herramienta lo
devolvió, por ejemplo: `NS: ns1.empresa.com (whois_dominio)`. Si no tienes una
herramienta que respalde un dato, no lo incluyas. Si haces una deducción propia,
márcala como **(inferencia)**. Termina con una sección **Limitaciones** que liste
los errores de herramientas y los objetivos bloqueados.
```

### Explicación con mis palabras

**¿Qué viene de mi `scope.txt`?** De mi `scope.txt` vienen las dos líneas `Autorizado:` y `Excluido (nunca):`. El programa lee el fichero, separa las líneas que empiezan con `!` (exclusiones) de las demás (autorizadas) y las escribe como dos listas separadas por comas. Los comentarios con `#` no aparecen. Si cambio el `scope.txt`, cambian esas dos líneas.

**¿Qué viene de mis herramientas?** De la lista `HERRAMIENTAS` de `lanzar.py` viene la sección "Herramientas disponibles": una línea por herramienta, con su nombre y la primera línea de su docstring. Lo vi en el `diff`: al añadir `ficheros_expuestos` e `infraestructura_dominio` aparecieron justo esas dos líneas. Por eso es importante que la primera línea del docstring explique bien qué hace la herramienta: es el resumen que la IA ve en el prompt (además, recibe el docstring completo en el esquema de herramientas).

**¿Qué hace ante un `BLOQUEADO`?** El prompt le dice que, si una herramienta responde `BLOQUEADO`, ese objetivo está fuera del alcance: no tiene que insistir ni intentarlo por otro camino (otra herramienta, una IP o una URL del mismo host). Tiene que anotarlo como "fuera de alcance" y seguir con otra cosa. Además, si el usuario le pide algo fuera del alcance, debe decirlo en el informe. De todas formas, aunque la IA no obedeciera, el `scope-guard` lo seguiría bloqueando: el prompt es la instrucción y el guardia es la garantía.

**¿Cómo cita la herramienta de origen?** En la sección "Informe" le pide que, para cada dato, ponga entre paréntesis la herramienta que lo devolvió, con el ejemplo `NS: ns1.empresa.com (whois_dominio)`. Si ninguna herramienta respalda un dato, no lo puede incluir. Y si deduce algo por su cuenta, lo tiene que marcar como (inferencia). Así puedo comprobar cada dato del informe contra la traza.

### Cambio 1: añadir herramientas cambia el prompt

`$ diff salida/prompt_3herr.txt salida/prompt_5herr.txt` (prompt con las 3 herramientas iniciales frente al prompt con las 5, con la plantilla original):

```
22a23,24
> - ficheros_expuestos: Lee robots.txt y /.well-known/security.txt (RFC 9116) de un dominio por HTTPS.
> - infraestructura_dominio: Resuelve un dominio (registros A) y consulta InternetDB de Shodan por cada IP:
```

Solo cambia la lista de herramientas: cada una aporta una línea, con su nombre y la **primera línea** de su docstring.

### Lo que encontré al leer el prompt (y el motor)

1. **Descripciones cortadas.** `prompt.py` solo usa la primera línea del docstring. Por eso `whois_dominio` acaba en `Devuelve registrador,` y mi `infraestructura_dominio` acababa en `por cada IP:`. Pero, leyendo `motor/agente.py` (función `describir`), el modelo recibe cada herramienta **dos veces**: un resumen de una línea en el prompt y el **docstring completo** en el esquema de *function calling*. Así que los avisos sí le llegaban. Aun así, he reescrito la primera línea de mi herramienta para que sea una frase completa. La de `whois_dominio` es código de `aap-base` y no la he tocado.
2. **Los límites no cuadraban.** La plantilla decía "como máximo 20 llamadas", mientras que `lanzar.py` corta a los 15 pasos (`--max-pasos`) y a los 60 000 tokens (`--max-tokens`). Un paso es un turno del modelo, que puede pedir varias herramientas a la vez. Lo importante: si se alcanza un límite, `agente.py` lanza `LimiteAlcanzado` y **no se escribe `informe.md`**. Además, cada paso reenvía toda la conversación, así que los tokens de entrada crecen con cada herramienta.
3. **"Nada que envíe tráfico al objetivo" era ambiguo.** `ficheros_expuestos` sí hace una petición HTTPS al objetivo, aunque sea a ficheros públicos (técnica pasiva 6, "ficheros expuestos", del enunciado).
4. **`traza.jsonl` se borra en cada ejecución** (`Traza.__init__` hace `write_text("")`). Hay que copiarla después de cada lanzamiento, o la del 2.5 pisaría la del 2.4.

### Cambio 2: ajuste de la plantilla `instrucciones.md`

La plantilla ajustada está en [`instrucciones.md`](instrucciones.md). `$ diff salida/prompt_5herr.txt salida/prompt_final.txt`:

| Cambio | Por qué |
|---|---|
| Quitado el párrafo "Esta es una PLANTILLA..." | Era texto para el alumno; el modelo lo leía como ruido |
| El orden de trabajo nombra la herramienta de cada paso y añade los pasos 4 y 5 | Para que el modelo use también mis dos herramientas |
| Máximo **12 llamadas**; al llegar, escribir el informe | Deja margen frente al límite de pasos para que no se corte sin informe |
| Aclarado que `ficheros_expuestos` es la única petición directa, y por qué es pasiva | Quita la ambigüedad del punto 3 |
| "No insistas **por otro camino** (otra herramienta, otro nombre, una IP o una URL)" y "dilo en el informe" | Cierra atajos para salir del alcance (2.5) y deja constancia |
| Nueva sección **"Cómo interpretar los resultados"** | Lecciones de la Parte 1: `SIN DATOS` ≠ `ERROR`, IP de CDN o de terceros, CVE sin verificar |
| Marcar **(inferencia)** y añadir una sección **Limitaciones** | Separa hechos de deducciones; ayuda a detectar invenciones en la Parte 3 |

```
1,5c1,2   párrafo de PLANTILLA -> contexto de bug bounty
16c13,15  BLOQUEADO: se cierran "otros caminos" y se pide anotarlo
24c23     infraestructura_dominio: primera línea completa
28,31c27,31  orden de trabajo con herramientas (5 pasos)
35,37c35,49  límites (12 llamadas, ritmo, pasividad) + "Cómo interpretar los resultados"
43c55,57  informe: (inferencia) y sección Limitaciones
```

### Límite de gasto

La clave del modelo es la **IA del aula**: la entrega el profesor (`~/.aula-ia.env`) y yo no puedo ponerle un tope. `ia-cupo` muestra `Gastado: 0.000000 USD (informativo, sin tope)`, con el contador que se reinicia el 2026-12-01. Por eso pongo el límite en el propio agente y mido el gasto:

1. **Límite en el agente:** se lanza con `--max-pasos` y `--max-tokens` explícitos. Si se superan, el motor se para (`LimiteAlcanzado`).
2. **Límite en las instrucciones:** como máximo 12 llamadas a herramientas.
3. **Medida del coste:** `ia-cupo` antes y después de cada ejecución, y los tokens que imprime `lanzar.py`.

## 2.4 Ejecución contra el objetivo

### Intento 1: la IA del aula no está disponible

**2026-11-04 12:21:43 UTC** · `ia-cupo` → `Gastado: 0.000000 USD`

```
$ time AAP_TIMEOUT=600 .venv/bin/python lanzar.py "Investiga la superficie de ataque de GitLab (su programa de bug bounty en HackerOne) dentro del alcance autorizado. Termina con un informe." --max-pasos 20 --max-tokens 120000
RuntimeError: El servicio de IA no está disponible ahora mismo. Inténtalo más tarde.
real    0m10.862s
```

**2026-11-04 12:21:54 UTC** · `ia-cupo` → `Gastado: 0.000000 USD` (no se gastó nada).

`motor/modelo.py` traduce varios códigos HTTP distintos al mismo mensaje genérico (`UNAVAILABLE`), así que ese mensaje no decía la causa. Lo diagnostiqué así:

- **La red y la clave estaban bien:** `ia-cupo` respondía (mismo servidor, puerto 4001), no hubo un 401 (clave no válida) ni un 403 (modelo no permitido), y el cupo no estaba agotado.
- **Petición mínima al gateway**, sin herramientas, imprimiendo el código HTTP real y sin mostrar la clave:

```
Modelo: corsario-1 | URL: http://10.30.0.6:4000/v1/chat/completions
HTTP 409 -> {"error":{"message":"litellm.APIError: APIError: OpenAIException - instance is stopped ... model group 'corsario-1' failed ... Fallback to _gw_backup_corsario_1 also failed: ... instance is stopped ..."}}
```

**Causa:** la instancia que sirve el modelo `corsario-1` **y también su respaldo** estaban **paradas** (`instance is stopped`, HTTP 409). Es un problema del servidor del aula, no del agente ni de mi configuración. No había ningún `.env` local que interfiriera.
