import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from entregas.models import Cliente, Pedido

SLUG = "bbrubin123"
NOME = "Bob Rubin"
REFERENCIA = "FO6315C2D0C48"
TITULO = "Daily follow-up report (Jump + email + Teams)"


class Command(BaseCommand):
    help = (
        "Cria o cliente bbrubin123 e o pedido FO6315C2D0C48. "
        "A senha é lida só de BBRUBIN_SENHA no ambiente."
    )

    def handle(self, *args, **options):
        senha = os.environ.get("BBRUBIN_SENHA", "")
        if not senha:
            raise CommandError(
                "Defina BBRUBIN_SENHA no ambiente. Não grave a senha no repositório."
            )
        username = os.environ.get("BBRUBIN_USERNAME", SLUG).strip()
        if not username:
            raise CommandError("BBRUBIN_USERNAME vazio.")

        User = get_user_model()
        user = User.objects.filter(username=username).first()
        if user is None:
            user = User(username=username, is_staff=False, is_superuser=False, is_active=True)
            try:
                validate_password(senha, user)
            except ValidationError as exc:
                raise CommandError("Senha recusada: " + " ".join(exc.messages)) from exc
            user.set_password(senha)
            user.save()
            self.stdout.write("Usuário criado. A senha ficou só no ambiente, não no log.")
        else:
            if user.is_staff or user.is_superuser:
                raise CommandError(
                    "Esse usuário é da equipe. Use outro BBRUBIN_USERNAME para o cliente."
                )
            self.stdout.write("Usuário já existia. A senha foi mantida.")

        ligado = Cliente.objects.filter(user=user).first()
        if ligado is not None and ligado.slug != SLUG:
            raise CommandError("Esse usuário já está ligado a outro cliente.")

        cliente = Cliente.objects.filter(slug=SLUG).first()
        if cliente is None:
            cliente = Cliente(user=user, slug=SLUG, nome_exibicao=NOME, ativo=True)
            cliente.full_clean()
            cliente.save()
            self.stdout.write("Cliente bbrubin123 criado (Bob Rubin).")
        elif cliente.user_id != user.id:
            raise CommandError("O slug bbrubin123 já pertence a outro usuário.")
        else:
            self.stdout.write("Cliente bbrubin123 já existia.")

        pedido = Pedido.objects.filter(cliente=cliente, referencia=REFERENCIA).first()
        if pedido is None:
            pedido = Pedido(
                cliente=cliente,
                referencia=REFERENCIA,
                titulo=TITULO,
                status=Pedido.Status.EM_ANDAMENTO,
            )
            pedido.full_clean()
            pedido.save()
            self.stdout.write("Pedido FO6315C2D0C48 criado com status em_andamento.")
        else:
            self.stdout.write(
                f"Pedido FO6315C2D0C48 já existia (status {pedido.status}). Nada alterado."
            )
