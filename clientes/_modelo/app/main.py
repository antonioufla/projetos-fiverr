import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Projeto")
VERSAO = os.getenv("VERSAO", "dev")


@app.get("/saude")
def saude():
    return {"ok": True, "versao": VERSAO}


@app.get("/", response_class=HTMLResponse)
def inicio():
    return f"<h1>Projeto no ar</h1><p>Versao {VERSAO}</p>"
