from django.contrib import admin

from .models import ArquivoDeEntrega, Cliente, Pedido


class PedidoInline(admin.TabularInline):
    model = Pedido
    extra = 0
    show_change_link = True
    fields = ("referencia", "titulo", "status", "prazo")


class ArquivoDeEntregaInline(admin.TabularInline):
    model = ArquivoDeEntrega
    extra = 1
    fields = ("rotulo", "arquivo", "enviado_em")
    readonly_fields = ("enviado_em",)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("slug", "nome_exibicao", "user", "ativo", "criado_em")
    list_filter = ("ativo",)
    search_fields = ("slug", "nome_exibicao", "user__username")
    autocomplete_fields = ("user",)
    readonly_fields = ("criado_em",)
    inlines = (PedidoInline,)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("referencia", "titulo", "cliente", "status", "prazo", "atualizado_em")
    list_filter = ("status", "cliente")
    search_fields = ("referencia", "titulo", "cliente__slug", "cliente__nome_exibicao")
    autocomplete_fields = ("cliente",)
    readonly_fields = ("criado_em", "atualizado_em")
    date_hierarchy = "criado_em"
    inlines = (ArquivoDeEntregaInline,)
    fieldsets = (
        (None, {"fields": ("cliente", "referencia", "titulo", "status", "prazo")}),
        (
            "Interno",
            {
                "fields": ("notas_internas",),
                "description": "A página do cliente não mostra estas notas.",
            },
        ),
        ("Datas", {"fields": ("criado_em", "atualizado_em")}),
    )


@admin.register(ArquivoDeEntrega)
class ArquivoDeEntregaAdmin(admin.ModelAdmin):
    list_display = ("rotulo", "pedido", "cliente_do_pedido", "enviado_em")
    list_select_related = ("pedido", "pedido__cliente")
    search_fields = ("rotulo", "pedido__referencia", "pedido__cliente__slug")
    autocomplete_fields = ("pedido",)
    readonly_fields = ("enviado_em",)

    @admin.display(description="Cliente")
    def cliente_do_pedido(self, obj):
        return obj.pedido.cliente


admin.site.site_header = "Viral Media"
admin.site.site_title = "Entregas"
admin.site.index_title = "Pedidos e arquivos"
