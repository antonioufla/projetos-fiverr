from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("entrar/", views.entrar, name="entrar"),
    path("sair/", views.sair, name="sair"),
    path("pedidos/<str:referencia>/", views.detalhe, name="detalhe"),
    path(
        "pedidos/<str:referencia>/arquivos/<int:arquivo_id>/",
        views.baixar,
        name="baixar",
    ),
    path("robots.txt", views.robots, name="robots"),
    path("favicon.ico", views.favicon, name="favicon"),
]
