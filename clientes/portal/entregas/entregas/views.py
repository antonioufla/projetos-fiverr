import os
import re
from functools import wraps
from pathlib import Path

from django.contrib.auth import login, logout
from django.db.models import Count
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import FormularioEntrar
from .models import ArquivoDeEntrega

_NAO_SEGURO = re.compile(r"[^A-Za-z0-9._-]+")


def saude(request):
    return JsonResponse({"ok": True, "versao": os.environ.get("VERSAO", "dev")})


def robots(request):
    return HttpResponse("User-agent: *\nDisallow: /\n", content_type="text/plain")


def favicon(request):
    return HttpResponse(status=204)


def pagina_nao_encontrada(request, exception):
    resposta = render(request, "404.html", status=404)
    resposta.headers["X-Frame-Options"] = "DENY"
    return resposta


def csrf_falhou(request, reason=""):
    resposta = render(request, "403_csrf.html", status=403)
    resposta.headers["X-Frame-Options"] = "DENY"
    return resposta


def _pagina_plataforma(request):
    return render(
        request,
        "entregas/plataforma.html",
        {"mostrar_admin": getattr(request, "modo", "") == "admin"},
    )


def so_cliente(view):
    @wraps(view)
    def _view(request, *args, **kwargs):
        cliente = getattr(request, "cliente", None)
        if cliente is None or not cliente.ativo:
            raise Http404()
        if not request.user.is_authenticated or request.user.pk != cliente.user_id:
            logout(request)
            return redirect("entrar")
        return view(request, *args, **kwargs)

    return _view


@require_http_methods(["GET", "HEAD"])
def inicio(request):
    cliente = getattr(request, "cliente", None)
    if cliente is None:
        return _pagina_plataforma(request)
    if not request.user.is_authenticated or request.user.pk != cliente.user_id:
        return redirect("entrar")
    pedidos = cliente.pedidos.annotate(qtd_arquivos=Count("arquivos"))
    return render(request, "entregas/lista.html", {"pedidos": pedidos})


@require_http_methods(["GET", "HEAD", "POST"])
def entrar(request):
    cliente = getattr(request, "cliente", None)
    if cliente is None:
        return _pagina_plataforma(request)
    if request.user.is_authenticated and request.user.pk == cliente.user_id:
        return redirect("inicio")

    if request.method == "POST":
        form = FormularioEntrar(request, data=request.POST)
        if form.is_valid():
            usuario = form.get_user()
            if usuario.is_active and usuario.pk == cliente.user_id and cliente.ativo:
                login(request, usuario)
                return redirect("inicio")
            form.add_error(None, "Usuário ou senha incorretos.")
    else:
        form = FormularioEntrar(request)
    return render(request, "entregas/entrar.html", {"form": form})


@require_http_methods(["POST"])
def sair(request):
    logout(request)
    return redirect("entrar")


@require_http_methods(["GET", "HEAD"])
@so_cliente
def detalhe(request, referencia):
    pedido = get_object_or_404(
        request.cliente.pedidos.prefetch_related("arquivos"),
        referencia=referencia,
    )
    return render(request, "entregas/detalhe.html", {"pedido": pedido})


def _nome_download(arquivo):
    nome = _NAO_SEGURO.sub("_", Path(arquivo.arquivo.name).name).strip("._")
    return (nome or "entrega")[:180]


@require_http_methods(["GET", "HEAD"])
@so_cliente
def baixar(request, referencia, arquivo_id):
    arquivo = get_object_or_404(
        ArquivoDeEntrega.objects.select_related("pedido__cliente"),
        pk=arquivo_id,
        pedido__referencia=referencia,
        pedido__cliente=request.cliente,
    )
    if not arquivo.arquivo or not arquivo.arquivo.name:
        raise Http404()
    try:
        if not arquivo.arquivo.storage.exists(arquivo.arquivo.name):
            raise Http404()
        handle = arquivo.arquivo.open("rb")
    except OSError as exc:
        raise Http404() from exc
    resposta = FileResponse(
        handle,
        as_attachment=True,
        filename=_nome_download(arquivo),
        content_type="application/octet-stream",
    )
    resposta["Cache-Control"] = "private, no-store"
    resposta["X-Content-Type-Options"] = "nosniff"
    return resposta
