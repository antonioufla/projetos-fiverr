import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Teste projetos-fiverr")
VERSAO = os.getenv("VERSAO", "dev")


@app.get("/saude")
def saude():
    return {"ok": True, "versao": VERSAO}


@app.get("/", response_class=HTMLResponse)
def inicio():
    return f"""<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><title>Teste</title>
<style>body{{font-family:system-ui;background:#0f172a;color:#e2e8f0;display:grid;place-items:center;height:100vh;margin:0}}div{{text-align:center}}h1{{color:#22c55e}}</style></head>
<body><div><h1>Deploy funcionando ✅</h1><p>Python + uvicorn, roteado pelo Traefik.</p><p>Versao: {VERSAO}</p></div></body></html>"""
