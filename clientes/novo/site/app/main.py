"""Site Viral Media (substituto do WordPress). Paginas estaticas + pedidos de orcamento.

- POST   /api/pedido          recebe o formulario (honeypot + limite por IP), grava em SQLite
- GET    /api/pedidos         lista os pedidos (Authorization: Bearer <token>)
- DELETE /api/pedidos/{id}    apaga um pedido (mesmo token)

O token nao fica no Git: so o SHA-256 dele (PEDIDOS_TOKEN_SHA256). Para trocar, gere outro
token e coloque o novo hash em PEDIDOS_TOKEN_SHA256 no .env.secrets do servidor (tem prioridade).
Banco: $DADOS/pedidos.db (volume persistente /srv/dados).
"""
import hashlib
import hmac
import json
import os
import re
import sqlite3
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

AQUI = Path(__file__).parent
VERSAO = os.getenv("VERSAO", "dev")
DADOS = Path(os.getenv("DADOS", "/srv/dados"))
TOKEN_SHA256 = os.getenv("PEDIDOS_TOKEN_SHA256", "ba8409e14796355eb0aa10501b625f5b500785b4ebde16094d7c4774fc50862f").strip().lower()
TIPOS = {"chatbot", "app", "landing", "logo", "prompts", "python", "make", "outro"}

CANONICO = os.getenv("CANONICO", "").strip().lower()  # ex.: viralmedia.vip (ativa o redirecionamento)
# Enderecos do WordPress antigo: mandam para a pagina inicial em vez de dar erro
ANTIGOS = {"/pv_felipe", "/pv01", "/terms", "/privacy-policy-2", "/sample-page", "/home", "/feed",
           "/comments/feed", "/wp-admin", "/wp-login.php", "/wp-json", "/xmlrpc.php"}

app = FastAPI(title="Viral Media", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=AQUI / "static"), name="static")


@app.middleware("http")
async def canonico(request: Request, call_next):
    # com CANONICO definido, o subdominio de teste (novo.) redireciona para o dominio principal
    host = request.headers.get("host", "").split(":")[0].lower()
    if CANONICO and host.startswith("novo.") and request.url.path != "/saude" and request.method in ("GET", "HEAD"):
        destino = f"https://{CANONICO}{request.url.path}" + (f"?{request.url.query}" if request.url.query else "")
        return RedirectResponse(destino, status_code=301)
    return await call_next(request)


PAGINA_404 = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Página não encontrada · Viral Media</title><link rel="icon" href="/static/favicon.png">
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
background:linear-gradient(120deg,#0F2340 0%,#0F2E45 55%,#0E4249 100%);color:#fff;text-align:center;padding:24px}
.k{color:#2DD4BF;font-weight:700;letter-spacing:.14em;font-size:13px}h1{font-size:34px;margin:12px 0}p{color:#C3CFDC;margin:0 0 28px}
a{display:inline-block;background:#0F766E;color:#fff;text-decoration:none;font-weight:600;padding:13px 22px;border-radius:10px}a:hover{background:#115E59}</style></head>
<body><div><div class="k">ERRO 404</div><h1>Página não encontrada</h1><p>O endereço que você abriu não existe mais ou mudou de lugar.<br>Page not found.</p>
<a href="/">Ir para a página inicial</a></div></body></html>"""


@app.exception_handler(StarletteHTTPException)
async def erro_http(request: Request, exc: StarletteHTTPException):
    caminho = request.url.path.rstrip("/") or "/"
    if exc.status_code == 404 and not caminho.startswith("/api"):
        if caminho in ANTIGOS or caminho.startswith(("/wp-", "/category/", "/author/", "/tag/")):
            return RedirectResponse("/", status_code=301)
        return HTMLResponse(PAGINA_404, status_code=404)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


# ---------- banco ----------
def _db() -> sqlite3.Connection:
    DADOS.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DADOS / "pedidos.db", timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, criado TEXT NOT NULL, nome TEXT, email TEXT, telefone TEXT,
        tipo TEXT, descricao TEXT, prazo TEXT, idioma TEXT, ip TEXT, agente TEXT)""")
    return con


# ---------- limite por IP: 5 envios a cada 10 min, 20 por dia ----------
_envios: dict[str, deque] = defaultdict(deque)


def _ip(req: Request) -> str:
    return (req.headers.get("cf-connecting-ip") or req.headers.get("x-real-ip")
            or req.headers.get("x-forwarded-for", "").split(",")[0].strip() or (req.client.host if req.client else "?"))


def _limitado(ip: str) -> bool:
    agora = time.time(); fila = _envios[ip]
    while fila and agora - fila[0] > 86400:
        fila.popleft()
    if sum(1 for t in fila if agora - t < 600) >= 5 or len(fila) >= 20:
        return True
    fila.append(agora)
    return False


class Pedido(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=150)
    telefone: str = Field(default="", max_length=40)
    tipo: str = Field(max_length=20)
    descricao: str = Field(min_length=10, max_length=4000)
    prazo: str = Field(default="", max_length=200)
    idioma: str = Field(default="pt", max_length=5)
    site: str = Field(default="", max_length=200)  # honeypot: humano deixa vazio


@app.post("/api/pedido")
def novo_pedido(p: Pedido, req: Request):
    if p.site.strip():  # robo: finge sucesso e descarta
        return {"ok": True}
    ip = _ip(req)
    if _limitado(ip):
        return JSONResponse({"ok": False, "erro": "limite"}, status_code=429)
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", p.email.strip()):
        return JSONResponse({"ok": False, "erro": "email"}, status_code=422)
    tipo = p.tipo if p.tipo in TIPOS else "outro"
    with _db() as con:
        cur = con.execute(
            "INSERT INTO pedidos (criado,nome,email,telefone,tipo,descricao,prazo,idioma,ip,agente) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(timespec="seconds"), p.nome.strip(), p.email.strip(), p.telefone.strip(),
             tipo, p.descricao.strip(), p.prazo.strip(), "en" if p.idioma == "en" else "pt", ip,
             req.headers.get("user-agent", "")[:200]))
    print(f"Novo pedido #{cur.lastrowid} ({tipo})", flush=True)
    return {"ok": True, "id": cur.lastrowid}


def _autorizar(authorization: str | None):
    if not TOKEN_SHA256:
        raise HTTPException(503, "token nao configurado")
    tok = (authorization or "").removeprefix("Bearer ").strip()
    if not tok or not hmac.compare_digest(hashlib.sha256(tok.encode()).hexdigest(), TOKEN_SHA256):
        time.sleep(0.5)
        raise HTTPException(401, "nao autorizado")


@app.get("/api/pedidos")
def listar(authorization: str | None = Header(default=None), desde: str = "", limite: int = 100):
    _autorizar(authorization)
    with _db() as con:
        linhas = con.execute("SELECT * FROM pedidos WHERE criado > ? ORDER BY id DESC LIMIT ?",
                             (desde, max(1, min(limite, 1000)))).fetchall()
    return {"total": len(linhas), "pedidos": [dict(r) for r in linhas]}


@app.delete("/api/pedidos/{pid}")
def apagar(pid: int, authorization: str | None = Header(default=None)):
    _autorizar(authorization)
    with _db() as con:
        n = con.execute("DELETE FROM pedidos WHERE id = ?", (pid,)).rowcount
    if not n:
        raise HTTPException(404, "nao encontrado")
    return {"ok": True, "apagado": pid}


# ---------- paginas e SEO ----------
# Pagina unica em dois idiomas: / (pt-BR) e /en/ (ingles), ambas renderizadas no servidor (legiveis sem JS).
# O ingles vem dos atributos data-en do index.html; o JS continua trocando o idioma na hora.
INDEXNOW_KEY = "795a2ae49401e1a2027eba33694a3e07"  # chave publica do IndexNow (Bing/Yandex); o arquivo /<chave>.txt prova a posse
WHATSAPP = "https://wa.me/5535991187683"
PERFIS = ["https://www.fiverr.com/antoniorochanet", "https://www.upwork.com/freelancers/~011dc6dece52f38d35",
          "https://www.freelancer.com/u/antoniorochaneto", "https://www.99freelas.com.br/user/antonio-elizeu-da-rocha"]
DEMOS = "https://demo.viralmedia.vip"
GET_HEAD = ["GET", "HEAD"]

TEXTOS = {
    "pt": dict(lang="pt-BR", title="Viral Media · Chatbots com IA, apps PWA, landing pages e automações",
               desc="A Viral Media é um estúdio de IA e desenvolvimento de software. Criamos chatbots com IA para sites, aplicativos PWA, landing pages, logos, prompts, scripts em Python e automações com Make.com para pequenas empresas, com entrega online.",
               ogdesc="Estúdio de IA e software: criamos chatbots com IA, aplicativos PWA, landing pages e automações para pequenas empresas. Veja nossas demonstrações ao vivo.",
               ogalt="Viral Media: inteligência artificial aplicada ao seu negócio",
               oglocale="pt_BR", oglocale2="en_US", outra_url="/en/", outra_lang="en", outra_nome="English"),
    "en": dict(lang="en", title="Viral Media · AI chatbots, PWA apps, landing pages and automations",
               desc="Viral Media is an AI and software development studio. We build website AI chatbots, PWA apps, landing pages, logos, prompt packs, Python scripts and Make.com automations for small businesses, delivered online.",
               ogdesc="AI and software studio: we build AI chatbots, PWA apps, landing pages and automations for small businesses. See our live demos.",
               ogalt="Viral Media: artificial intelligence applied to your business",
               oglocale="en_US", oglocale2="pt_BR", outra_url="/", outra_lang="pt-BR", outra_nome="Português"),
}

SERVICOS = [  # (pt nome, pt desc, en nome, en desc)
    ("Chatbot com IA para site", "Atende os visitantes 24 horas com as informações do seu negócio. Instala com uma linha de código.",
     "Website AI chatbot", "Answers your visitors 24/7 with your business information. Installs with one line of code."),
    ("Apps PWA e sistemas web", "Aplicativos instaláveis e sistemas em Python/FastAPI. Também podem ser entregues como APK.",
     "PWA & web apps", "Installable apps and systems in Python/FastAPI. Can also be delivered as an Android APK."),
    ("Landing pages", "Páginas rápidas e responsivas, focadas em transformar visitas em contatos.",
     "Landing pages", "Fast, responsive pages focused on turning visitors into contacts."),
    ("Logos e identidade visual", "Logo, cores e peças básicas da marca, criados com apoio de IA e refinados à mão.",
     "Logos & visual identity", "Logo, colors and basic brand pieces, created with AI support and refined by hand."),
    ("Pacotes de prompts", "Prompts testados para ChatGPT e Claude, organizados para as tarefas do seu dia a dia.",
     "Prompt packs", "Tested prompts for ChatGPT and Claude, organized for your daily tasks."),
    ("Scripts em Python", "Planilhas, relatórios, conversão de PDF e Excel, extração de dados.",
     "Python scripts", "Spreadsheets, reports, PDF and Excel conversion, data extraction."),
    ("Automações com Make.com", "Cenários conectando suas ferramentas, com ChatGPT onde ele faz diferença.",
     "Make.com automations", "Scenarios connecting your tools, with ChatGPT where it adds value."),
]

FAQ = [  # (pt pergunta, pt resposta, en pergunta, en resposta); respostas podem ter HTML simples
    ("Quanto custa um projeto?",
     "Depende do escopo. Depois de entender o que você precisa, enviamos uma proposta por escrito com preço fechado e prazo, antes de começar qualquer trabalho. A primeira conversa não tem custo.",
     "How much does a project cost?",
     "It depends on the scope. Once we understand what you need, we send a written proposal with a fixed price and deadline before any work begins. The first conversation is free."),
    ("Quanto tempo leva para ficar pronto?",
     "Depende do tamanho do projeto. Informamos o prazo por escrito na proposta, e você acompanha o andamento por um link ao vivo desde os primeiros dias.",
     "How long does it take?",
     "It depends on the size of the project. We state the deadline in the written proposal, and you follow progress through a live link from the first days."),
    ("Como o projeto é entregue?",
     "Entregamos tudo online: publicado em um link funcionando ou em arquivos prontos para usar, com o código-fonte em um repositório Git e instruções. Prompts, logos e scripts são entregues como arquivos.",
     "How is the project delivered?",
     "We deliver everything online: published at a working link or as ready-to-use files, with the source code in a Git repository and instructions. Prompts, logos and scripts are delivered as files."),
    ("O chatbot funciona no meu site atual?",
     "Na maioria dos casos, sim. Instalamos o chatbot com uma linha de código, e ele funciona em plataformas que permitem adicionar um script, como WordPress e sites próprios. Ele responde com as informações do seu negócio.",
     "Will the chatbot work on my current website?",
     "In most cases, yes. The chatbot installs with one line of code and works on platforms that let you add a script, such as WordPress and custom sites. It answers using your business information."),
    ("Vocês atendem em inglês e clientes fora do Brasil?",
     "Sim. Atendemos em português e inglês, clientes no Brasil e no exterior.",
     "Do you work in English and with clients outside Brazil?",
     "Yes. We work in Portuguese and English, with clients in Brazil and abroad."),
    ("Posso ver exemplos antes de contratar?",
     'Sim. Temos demonstrações funcionando de um chatbot, de um aplicativo PWA e de uma landing page em <a href="https://demo.viralmedia.vip/">demo.viralmedia.vip</a>.',
     "Can I see examples before hiring?",
     'Yes. We have working demos of a chatbot, a PWA app and a landing page at <a href="https://demo.viralmedia.vip/">demo.viralmedia.vip</a>.'),
    ("Como peço um orçamento?",
     "Preencha o formulário desta página ou fale com a gente pelo WhatsApp +55 35 99118-7683. Respondemos em até um dia útil.",
     "How do I request a quote?",
     "Fill in the form on this page or message us on WhatsApp at +55 35 99118-7683. We reply within one business day."),
]

_TAG_EN = re.compile(r'<(\w+)((?:[^>"\']|"[^"]*"|\'[^\']*\')*?)\sdata-en="([^"]*)"((?:[^>"\']|"[^"]*"|\'[^\']*\')*)>(.*?)</\1>', re.S)
_ALT_EN = {"Tela da demonstração de chatbot com IA no site da Clínica Sorriso": "AI chatbot demo on the Clínica Sorriso dental clinic website",
           "Tela do aplicativo PWA de orçamentos e agenda OrçaFácil": "OrçaFácil quotes and schedule PWA app demo",
           "Tela da landing page de energia solar Lumina Solar": "Lumina Solar energy landing page demo",
           "Foto de Antonio Rocha, fundador da Viral Media": "Photo of Antonio Rocha, founder of Viral Media"}


def _base(req: Request | None = None) -> str:
    if CANONICO:
        return f"https://{CANONICO}"
    return f"https://{req.headers.get('host', 'viralmedia.vip') if req else 'viralmedia.vip'}"


def _staging(req: Request) -> bool:
    # enquanto estiver so no subdominio de teste, nao deixa o Google indexar
    return req.headers.get("host", "").startswith("novo.")


def _esc(t: str) -> str:
    return t.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def _para_ingles(html: str) -> str:
    """Troca o conteudo de cada elemento com data-en pelo ingles e guarda o portugues em data-pt (para o botao PT)."""
    def troca(m):
        tag, a1, en, a2, pt = m.groups()
        return f'<{tag}{a1} data-en="{en}" data-pt="{pt.replace("&", "&amp;").replace(chr(34), "&quot;")}"{a2}>{en}</{tag}>'
    html = _TAG_EN.sub(troca, html)
    for pt, en in _ALT_EN.items():
        html = html.replace(f'alt="{pt}"', f'alt="{en}"')
    return html.replace('aria-label="Mudar idioma / Change language">EN<', 'aria-label="Mudar idioma / Change language">PT<')


def _faq_html() -> str:
    return "\n".join(f'    <details><summary data-en="{_esc(qe)}">{qp}</summary><p data-en="{ae.replace(chr(34), "&quot;")}">{ap}</p></details>'
                     for qp, ap, qe, ae in FAQ)


def _jsonld(idioma: str) -> str:
    b = _base(); en = idioma == "en"
    url = f"{b}/en/" if en else f"{b}/"
    org, pessoa, site = f"{b}/#org", f"{b}/#antonio", f"{b}/#website"
    sem_html = lambda t: re.sub(r"<[^>]+>", "", t)
    grafo = [
        {"@type": ["Organization", "ProfessionalService"], "@id": org, "name": "Viral Media", "url": f"{b}/",
         "logo": f"{b}/static/icon-512.png", "image": f"{b}/static/og.png",
         "description": TEXTOS[idioma]["desc"], "slogan": "Artificial intelligence applied to your business" if en else "Inteligência artificial aplicada ao seu negócio",
         "founder": {"@id": pessoa},
         "areaServed": [{"@type": "Country", "name": "Brazil"}, "Worldwide"],
         "knowsLanguage": ["pt-BR", "en"], "sameAs": PERFIS,
         "contactPoint": {"@type": "ContactPoint", "contactType": "sales", "telephone": "+55 35 99118-7683",
                          "url": WHATSAPP, "availableLanguage": ["Portuguese", "English"]},
         "knowsAbout": ["Artificial intelligence", "AI chatbots", "Progressive Web Apps", "Landing pages", "Python",
                        "FastAPI", "Make.com", "ChatGPT", "Claude", "Prompt engineering", "Logo design"],
         "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Services" if en else "Serviços",
                             "itemListElement": [{"@type": "Offer", "itemOffered": {
                                 "@type": "Service", "name": s[2] if en else s[0], "description": s[3] if en else s[1],
                                 "provider": {"@id": org}, "areaServed": "Worldwide"}} for s in SERVICOS]}},
        {"@type": "Person", "@id": pessoa, "name": "Antonio Rocha", "url": f"{b}/#sobre",
         "image": f"{b}/static/antonio.jpg", "jobTitle": "Founder" if en else "Fundador",
         "worksFor": {"@id": org}, "knowsLanguage": ["pt-BR", "en"], "sameAs": PERFIS + [f"{DEMOS}/"],
         "knowsAbout": ["Python", "FastAPI", "AI chatbots", "PWA", "Make.com", "Prompt engineering"]},
        {"@type": "WebSite", "@id": site, "url": f"{b}/", "name": "Viral Media", "inLanguage": ["pt-BR", "en"],
         "publisher": {"@id": org}},
        {"@type": "WebPage", "@id": f"{url}#pagina", "url": url, "name": TEXTOS[idioma]["title"],
         "description": TEXTOS[idioma]["desc"], "inLanguage": TEXTOS[idioma]["lang"], "isPartOf": {"@id": site},
         "about": {"@id": org}, "primaryImageOfPage": {"@type": "ImageObject", "url": f"{b}/static/og.png", "width": 1200, "height": 630}},
        {"@type": "FAQPage", "@id": f"{url}#faq", "url": url, "inLanguage": TEXTOS[idioma]["lang"], "isPartOf": {"@id": site},
         "mainEntity": [{"@type": "Question", "name": q[2] if en else q[0],
                         "acceptedAnswer": {"@type": "Answer", "text": sem_html(q[3] if en else q[1])}} for q in FAQ]},
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": grafo}, ensure_ascii=False).replace("</", "<\\/")


def _pagina(req: Request, idioma: str) -> HTMLResponse:
    t = TEXTOS[idioma]; b = _base(req)
    html = (AQUI / "index.html").read_text(encoding="utf-8")
    html = html.replace("{{FAQ}}", _faq_html())
    if idioma == "en":
        html = _para_ingles(html)
    troca = {"{{LANG}}": t["lang"], "{{LANGJS}}": idioma, "{{TITLE}}": _esc(t["title"]), "{{DESC}}": _esc(t["desc"]),
             "{{OGDESC}}": _esc(t["ogdesc"]), "{{OGALT}}": _esc(t["ogalt"]), "{{OGLOCALE}}": t["oglocale"],
             "{{OGLOCALE2}}": t["oglocale2"], "{{CANON}}": f"{b}/en/" if idioma == "en" else f"{b}/",
             "{{HOME}}": "/en/" if idioma == "en" else "/", "{{OUTRA_URL}}": t["outra_url"], "{{OUTRA_LANG}}": t["outra_lang"],
             "{{OUTRA_NOME}}": t["outra_nome"], "{{JSONLD}}": _jsonld(idioma), "{{VERSAO}}": VERSAO, "{{URL}}": b}
    for k, v in troca.items():
        html = html.replace(k, v)
    cab = {"Cache-Control": "no-cache", "Content-Language": t["lang"],
           "Link": f'<{b}/>; rel="alternate"; hreflang="pt-BR", <{b}/en/>; rel="alternate"; hreflang="en"'}
    if _staging(req):
        html = html.replace("<head>", '<head>\n<meta name="robots" content="noindex">', 1)
        cab["X-Robots-Tag"] = "noindex"
    return HTMLResponse(html, headers=cab)


@app.middleware("http")
async def cache_estaticos(request: Request, call_next):
    resp = await call_next(request)
    if request.url.path.startswith("/static/") and resp.status_code == 200:
        resp.headers["Cache-Control"] = "public, max-age=604800"
    return resp


@app.get("/saude")
def saude():
    return {"ok": True, "versao": VERSAO}


@app.api_route("/", methods=GET_HEAD, response_class=HTMLResponse)
def inicio(req: Request):
    return _pagina(req, "pt")


@app.api_route("/en/", methods=GET_HEAD, response_class=HTMLResponse)
def inicio_en(req: Request):
    return _pagina(req, "en")


@app.api_route("/en", methods=GET_HEAD)
def en_sem_barra():
    return RedirectResponse("/en/", status_code=301)


ROBOTS_IA = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User", "Claude-SearchBot", "anthropic-ai",
             "PerplexityBot", "Perplexity-User", "Google-Extended", "Googlebot", "Bingbot", "Applebot", "Applebot-Extended",
             "DuckAssistBot", "meta-externalagent", "CCBot", "Amazonbot", "YandexBot"]


@app.api_route("/robots.txt", methods=GET_HEAD, response_class=PlainTextResponse)
def robots(req: Request):
    if _staging(req):
        return "User-agent: *\nDisallow: /\n"
    b = _base(req)
    regras = "Allow: /\nDisallow: /api/\n"
    ias = "".join(f"User-agent: {r}\n" for r in ROBOTS_IA)
    return (f"# Viral Media ({b}): buscadores e assistentes de IA sao bem-vindos.\n"
            f"# Resumo para IA / summary for LLMs: {b}/llms.txt\n\n"
            f"User-agent: *\n{regras}\n{ias}{regras}\nSitemap: {b}/sitemap.xml\n")


@app.api_route("/sitemap.xml", methods=GET_HEAD)
def sitemap(req: Request):
    b = _base(req)
    data = datetime.fromtimestamp((AQUI / "index.html").stat().st_mtime, timezone.utc).date().isoformat()
    alt = (f'<xhtml:link rel="alternate" hreflang="pt-BR" href="{b}/"/><xhtml:link rel="alternate" hreflang="en" href="{b}/en/"/>'
           f'<xhtml:link rel="alternate" hreflang="x-default" href="{b}/"/>')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
           f"<url><loc>{b}/</loc><lastmod>{data}</lastmod><changefreq>monthly</changefreq><priority>1.0</priority>{alt}</url>\n"
           f"<url><loc>{b}/en/</loc><lastmod>{data}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority>{alt}</url>\n"
           "</urlset>\n")
    return Response(xml, media_type="application/xml", headers={"Cache-Control": "public, max-age=3600"})


def _texto(nome: str) -> Response:
    return Response((AQUI / nome).read_text(encoding="utf-8"), media_type="text/plain; charset=utf-8",
                    headers={"Cache-Control": "public, max-age=3600", "X-Robots-Tag": "noindex"})


@app.api_route("/llms.txt", methods=GET_HEAD)
def llms():
    return _texto("llms.txt")


@app.api_route("/llms-full.txt", methods=GET_HEAD)
def llms_full():
    return _texto("llms-full.txt")


@app.api_route(f"/{INDEXNOW_KEY}.txt", methods=GET_HEAD)
def indexnow_chave():
    return PlainTextResponse(INDEXNOW_KEY)


@app.api_route("/site.webmanifest", methods=GET_HEAD)
def manifest():
    return JSONResponse({"name": "Viral Media · Estúdio de IA e software", "short_name": "Viral Media",
                         "description": "Estúdio de IA e desenvolvimento de software: criamos chatbots com IA, apps PWA, landing pages e automações para pequenas empresas.",
                         "start_url": "/", "display": "browser",
                         "background_color": "#F5F7FA", "theme_color": "#0F2340", "lang": "pt-BR",
                         "icons": [{"src": "/static/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"},
                                   {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png"}]},
                        media_type="application/manifest+json", headers={"Cache-Control": "public, max-age=86400"})


@app.api_route("/favicon.ico", methods=GET_HEAD)
def favicon():
    return Response((AQUI / "static" / "favicon.png").read_bytes(), media_type="image/png",
                    headers={"Cache-Control": "public, max-age=86400"})
