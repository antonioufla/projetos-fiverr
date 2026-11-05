from django.contrib import admin
from django.urls import include, path

from entregas import views as entregas_views

urlpatterns = [
    path("saude", entregas_views.saude, name="saude"),
    path("saude/", entregas_views.saude),
    path("admin/", admin.site.urls),
    path("", include("entregas.urls")),
]

handler404 = "entregas.views.pagina_nao_encontrada"
