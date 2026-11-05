import re
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .constantes import REFERENCIA_RE, SLUG_RE, SLUGS_RESERVADOS

_NAO_SEGURO = re.compile(r"[^A-Za-z0-9._-]+")


class CampoSlug(models.SlugField):
    """Slug de subdomínio: minúsculo, sem underscore."""

    default_validators = [
        RegexValidator(SLUG_RE.pattern, "Use letras minúsculas, números e hífen."),
    ]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 63)
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        valor = super().to_python(value)
        if isinstance(valor, str):
            return valor.strip().lower()
        return valor


def caminho_arquivo_entrega(instance, filename):
    nome = _NAO_SEGURO.sub("_", Path(filename).name).strip("._") or "arquivo"
    slug = instance.pedido.cliente.slug
    referencia = instance.pedido.referencia
    return f"entregas/{slug}/{referencia}/{nome}"


class Cliente(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cliente",
        verbose_name="usuário",
    )
    slug = CampoSlug(
        unique=True,
        verbose_name="slug",
        help_text="Subdomínio: https://<slug>.viralmedia.vip",
    )
    nome_exibicao = models.CharField("nome de exibição", max_length=200)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["slug"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(slug__in=sorted(SLUGS_RESERVADOS)),
                name="cliente_slug_nao_reservado",
            ),
        ]

    def __str__(self):
        return f"{self.nome_exibicao} ({self.slug})"

    def clean(self):
        super().clean()
        if self.slug:
            self.slug = self.slug.strip().lower()
        if self.slug in SLUGS_RESERVADOS:
            raise ValidationError({"slug": "Este subdomínio é reservado."})

    def save(self, *args, **kwargs):
        if self.slug:
            self.slug = self.slug.strip().lower()
        if self.slug in SLUGS_RESERVADOS or SLUG_RE.fullmatch(self.slug or "") is None:
            raise ValidationError({"slug": "Slug inválido para subdomínio."})
        super().save(*args, **kwargs)


class Pedido(models.Model):
    class Status(models.TextChoices):
        PROPOSTO = "proposto", "Proposto"
        EM_ANDAMENTO = "em_andamento", "Em andamento"
        EM_REVISAO = "em_revisao", "Em revisão"
        ENTREGUE = "entregue", "Entregue"
        PAGO = "pago", "Pago"
        CANCELADO = "cancelado", "Cancelado"

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="pedidos",
        verbose_name="cliente",
    )
    referencia = models.CharField(
        "referência",
        max_length=64,
        validators=[
            RegexValidator(
                REFERENCIA_RE.pattern,
                "Use letras, números, hífen ou underscore.",
            )
        ],
        help_text="Identificador na plataforma, por exemplo FO6315C2D0C48.",
    )
    titulo = models.CharField("título", max_length=200)
    status = models.CharField(
        "status",
        max_length=20,
        choices=Status.choices,
        default=Status.PROPOSTO,
    )
    prazo = models.DateField(null=True, blank=True)
    notas_internas = models.TextField(
        "notas internas",
        blank=True,
        help_text="Só aparece no admin. A página do cliente não mostra este texto.",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"
        ordering = ["-atualizado_em", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["cliente", "referencia"],
                name="pedido_referencia_unica_por_cliente",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    status__in=[
                        "proposto",
                        "em_andamento",
                        "em_revisao",
                        "entregue",
                        "pago",
                        "cancelado",
                    ]
                ),
                name="pedido_status_valido",
            ),
        ]

    def __str__(self):
        return f"{self.referencia} — {self.titulo}"

    def save(self, *args, **kwargs):
        if REFERENCIA_RE.fullmatch(self.referencia or "") is None:
            raise ValidationError({"referencia": "Referência inválida."})
        if self.status not in self.Status.values:
            raise ValidationError({"status": "Status inválido."})
        super().save(*args, **kwargs)


class ArquivoDeEntrega(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="arquivos",
        verbose_name="pedido",
    )
    arquivo = models.FileField("arquivo", upload_to=caminho_arquivo_entrega, max_length=255)
    rotulo = models.CharField("rótulo", max_length=200)
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "arquivo de entrega"
        verbose_name_plural = "arquivos de entrega"
        ordering = ["-enviado_em", "-id"]

    def __str__(self):
        return self.rotulo

    def tamanho_bytes(self):
        try:
            return self.arquivo.size
        except (OSError, ValueError):
            return None


@receiver(post_delete, sender=ArquivoDeEntrega)
def apagar_arquivo_do_disco(sender, instance, **kwargs):
    arquivo = instance.arquivo
    if arquivo and arquivo.name:
        arquivo.delete(save=False)
