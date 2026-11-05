import os
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase, override_settings

from config.segredo import CHAVE_DEV, ler_chave_secreta

from .models import ArquivoDeEntrega, Cliente, Pedido

User = get_user_model()
SENHA = "senha-teste-12345"
NOTA = "segredo-interno-xyz"
TITULO_BOB = "Daily follow-up report (Jump + email + Teams)"
TITULO_ANA = "Pedido da Ana"


class SegredoTests(TestCase):
    def test_ambiente_vence_arquivo(self):
        pasta = Path(self._pasta())
        (pasta / "secret_key").write_text("chave-do-arquivo\n", encoding="utf-8")
        self.assertEqual(
            ler_chave_secreta(pasta, {"DJANGO_SECRET_KEY": "chave-do-ambiente"}),
            "chave-do-ambiente",
        )

    def test_arquivo_quando_nao_ha_ambiente(self):
        pasta = Path(self._pasta())
        (pasta / "secret_key").write_text("chave-do-arquivo\n", encoding="utf-8")
        self.assertEqual(ler_chave_secreta(pasta, {}), "chave-do-arquivo")

    def test_placeholder_sem_fonte(self):
        pasta = Path(self._pasta())
        self.assertEqual(ler_chave_secreta(pasta, {}), CHAVE_DEV)

    def _pasta(self):
        pasta = Path("/tmp/entregas-segredo") / self._testMethodName
        pasta.mkdir(parents=True, exist_ok=True)
        return pasta


class ModeloTests(TestCase):
    def test_slug_reservado_e_rebaixado(self):
        user = User.objects.create_user("u1", password=SENHA)
        cliente = Cliente(user=user, slug="Arquivos", nome_exibicao="X")
        with self.assertRaises(ValidationError):
            cliente.save()

    def test_slug_minusculo_e_caminho_do_arquivo(self):
        user = User.objects.create_user("u2", password=SENHA)
        cliente = Cliente.objects.create(user=user, slug="Cliente-Novo", nome_exibicao="Novo")
        self.assertEqual(cliente.slug, "cliente-novo")
        pedido = Pedido.objects.create(
            cliente=cliente,
            referencia="FO6315C2D0C48",
            titulo="Relatorio",
            status=Pedido.Status.EM_ANDAMENTO,
        )
        with tempfile.TemporaryDirectory() as pasta:
            with override_settings(MEDIA_ROOT=pasta):
                arquivo = ArquivoDeEntrega.objects.create(
                    pedido=pedido,
                    rotulo="Relatorio",
                    arquivo=SimpleUploadedFile("../../relatorio.txt", b"abc"),
                )
        self.assertEqual(
            arquivo.arquivo.name,
            "entregas/cliente-novo/FO6315C2D0C48/relatorio.txt",
        )

    def test_status_invalido(self):
        user = User.objects.create_user("u3", password=SENHA)
        cliente = Cliente.objects.create(user=user, slug="cliente-z", nome_exibicao="Z")
        pedido = Pedido(cliente=cliente, referencia="ABC123", titulo="T", status="nope")
        with self.assertRaises(ValidationError):
            pedido.save()


class ComandoPrimeiroClienteTests(TestCase):
    def test_cria_cliente_e_pedido_sem_ecoar_senha(self):
        senha = "uma-senha-de-teste-bem-longa"
        saida = StringIO()
        with patch.dict(os.environ, {"BBRUBIN_SENHA": senha}):
            call_command("preparar_primeiro_cliente", stdout=saida)
        texto = saida.getvalue()
        self.assertNotIn(senha, texto)
        cliente = Cliente.objects.get(slug="bbrubin123")
        self.assertEqual(cliente.nome_exibicao, "Bob Rubin")
        self.assertTrue(cliente.ativo)
        self.assertFalse(cliente.user.is_staff)
        self.assertTrue(cliente.user.check_password(senha))
        pedido = Pedido.objects.get(referencia="FO6315C2D0C48")
        self.assertEqual(pedido.cliente, cliente)
        self.assertEqual(pedido.titulo, TITULO_BOB)
        self.assertEqual(pedido.status, Pedido.Status.EM_ANDAMENTO)

        cliente.user.set_password("outra-senha-longa-xyz")
        cliente.user.save()
        pedido.status = Pedido.Status.ENTREGUE
        pedido.save()
        with patch.dict(os.environ, {"BBRUBIN_SENHA": senha}):
            call_command("preparar_primeiro_cliente", stdout=StringIO())
        cliente.user.refresh_from_db()
        pedido.refresh_from_db()
        self.assertTrue(cliente.user.check_password("outra-senha-longa-xyz"))
        self.assertEqual(pedido.status, Pedido.Status.ENTREGUE)
        self.assertEqual(Cliente.objects.filter(slug="bbrubin123").count(), 1)
        self.assertEqual(Pedido.objects.filter(referencia="FO6315C2D0C48").count(), 1)

    def test_sem_senha_recusa(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BBRUBIN_SENHA", None)
            with self.assertRaises(CommandError):
                call_command("preparar_primeiro_cliente")

    def test_nao_usa_usuario_de_equipe(self):
        User.objects.create_superuser("bbrubin123", "a@example.com", "senha-staff-12345")
        with patch.dict(os.environ, {"BBRUBIN_SENHA": "uma-senha-de-teste-bem-longa"}):
            with self.assertRaises(CommandError):
                call_command("preparar_primeiro_cliente")
        self.assertFalse(Cliente.objects.filter(slug="bbrubin123").exists())


class PortalTests(TestCase):
    def setUp(self):
        self.bob = self._criar("bbrubin123", "bob", "Bob Rubin")
        self.ana = self._criar("ana-exemplo", "ana", "Ana Exemplo")
        self.pedido_bob = Pedido.objects.create(
            cliente=self.bob,
            referencia="FO6315C2D0C48",
            titulo=TITULO_BOB,
            status=Pedido.Status.EM_ANDAMENTO,
            notas_internas=NOTA,
        )
        self.pedido_ana = Pedido.objects.create(
            cliente=self.ana,
            referencia="OUTRO999",
            titulo=TITULO_ANA,
            status=Pedido.Status.PROPOSTO,
            notas_internas="nota-da-ana",
        )
        self.arquivo_bob = ArquivoDeEntrega.objects.create(
            pedido=self.pedido_bob,
            rotulo="Relatorio",
            arquivo=SimpleUploadedFile("relatorio.txt", b"conteudo-bob"),
        )
        self.arquivo_ana = ArquivoDeEntrega.objects.create(
            pedido=self.pedido_ana,
            rotulo="Anexo",
            arquivo=SimpleUploadedFile("ana.txt", b"conteudo-ana"),
        )

    def _criar(self, slug, username, nome):
        user = User.objects.create_user(username, password=SENHA)
        return Cliente.objects.create(user=user, slug=slug, nome_exibicao=nome, ativo=True)

    def _entrar(self, slug, username, senha=SENHA):
        return self.client.post(
            "/entrar/",
            {"username": username, "password": senha},
            HTTP_HOST=f"{slug}.viralmedia.vip",
        )

    @override_settings(ALLOWED_HOSTS=[".viralmedia.vip"])
    def test_saude_aceita_host_do_portal_com_allowed_hosts_minimo(self):
        ok = self.client.get("/saude", HTTP_HOST="portal.viralmedia.vip")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()["ok"], True)
        direto = self.client.get("/saude", HTTP_HOST="127.0.0.1")
        self.assertEqual(direto.status_code, 400)

    def test_saude(self):
        for host in (
            "portal.viralmedia.vip",
            "arquivos.viralmedia.vip",
            "bbrubin123.viralmedia.vip",
            "desconhecido.viralmedia.vip",
        ):
            resposta = self.client.get("/saude", HTTP_HOST=host)
            self.assertEqual(resposta.status_code, 200, host)
            self.assertEqual(resposta.json()["ok"], True)
            self.assertIn("versao", resposta.json())
        ruim = self.client.get("/saude", HTTP_HOST="evil.example")
        self.assertEqual(ruim.status_code, 400)

    def test_login_lista_so_os_proprios_pedidos(self):
        resposta = self._entrar("bbrubin123", "bob")
        self.assertEqual(resposta.status_code, 302)
        pagina = self.client.get("/", HTTP_HOST="bbrubin123.viralmedia.vip")
        self.assertContains(pagina, TITULO_BOB)
        self.assertContains(pagina, "Em andamento")
        self.assertNotContains(pagina, TITULO_ANA)
        self.assertNotContains(pagina, NOTA)
        self.assertNotContains(pagina, "/admin/")
        detalhe = self.client.get(
            "/pedidos/FO6315C2D0C48/",
            HTTP_HOST="bbrubin123.viralmedia.vip",
        )
        self.assertContains(detalhe, "Relatorio")
        self.assertNotContains(detalhe, NOTA)

    def test_senha_errada_e_credencial_de_outro_cliente(self):
        ruim = self._entrar("bbrubin123", "bob", "nao-e-a-senha")
        self.assertEqual(ruim.status_code, 200)
        self.assertContains(ruim, "incorretos")
        cruzado = self._entrar("ana-exemplo", "bob")
        self.assertEqual(cruzado.status_code, 200)
        self.assertContains(cruzado, "incorretos")
        self.assertNotContains(cruzado, TITULO_ANA)
        depois = self.client.get("/", HTTP_HOST="ana-exemplo.viralmedia.vip")
        self.assertEqual(depois.status_code, 302)

    def test_sessao_nao_vale_em_outro_host(self):
        self.assertEqual(self._entrar("bbrubin123", "bob").status_code, 302)
        cruzado = self.client.get("/", HTTP_HOST="ana-exemplo.viralmedia.vip")
        self.assertEqual(cruzado.status_code, 302)
        self.assertNotIn(TITULO_ANA.encode(), cruzado.content)
        self.assertNotIn(b"conteudo-ana", cruzado.content)
        de_novo = self.client.get("/", HTTP_HOST="bbrubin123.viralmedia.vip")
        self.assertEqual(de_novo.status_code, 302)

    def test_download_so_do_dono(self):
        self._entrar("bbrubin123", "bob")
        url = f"/pedidos/FO6315C2D0C48/arquivos/{self.arquivo_bob.pk}/"
        arquivo = self.client.get(url, HTTP_HOST="bbrubin123.viralmedia.vip")
        self.assertEqual(arquivo.status_code, 200)
        self.assertEqual(arquivo["Content-Type"], "application/octet-stream")
        self.assertTrue(arquivo["Content-Disposition"].startswith("attachment"))
        self.assertEqual(b"".join(arquivo.streaming_content), b"conteudo-bob")
        self.assertIn("private", arquivo["Cache-Control"])

        outro_pedido = f"/pedidos/OUTRO999/arquivos/{self.arquivo_ana.pk}/"
        self.assertEqual(
            self.client.get(outro_pedido, HTTP_HOST="bbrubin123.viralmedia.vip").status_code,
            404,
        )
        referencia_trocada = f"/pedidos/FO6315C2D0C48/arquivos/{self.arquivo_ana.pk}/"
        self.assertEqual(
            self.client.get(referencia_trocada, HTTP_HOST="bbrubin123.viralmedia.vip").status_code,
            404,
        )

        self.client.logout()
        anonimo = self.client.get(url, HTTP_HOST="bbrubin123.viralmedia.vip")
        self.assertEqual(anonimo.status_code, 302)
        self.assertNotEqual(anonimo.content, b"conteudo-bob")

    def test_download_cruzado_nao_entrega_bytes(self):
        self._entrar("bbrubin123", "bob")
        url = f"/pedidos/OUTRO999/arquivos/{self.arquivo_ana.pk}/"
        resposta = self.client.get(url, HTTP_HOST="ana-exemplo.viralmedia.vip")
        self.assertEqual(resposta.status_code, 302)
        self.assertNotIn(b"conteudo-ana", resposta.content)

    def test_cliente_inativo_e_slug_desconhecido(self):
        self._entrar("bbrubin123", "bob")
        self.bob.ativo = False
        self.bob.save()
        sumido = self.client.get("/", HTTP_HOST="bbrubin123.viralmedia.vip")
        self.assertEqual(sumido.status_code, 404)
        self.assertNotContains(sumido, TITULO_BOB, status_code=404)
        desconhecido = self.client.get("/", HTTP_HOST="nao-existe.viralmedia.vip")
        self.assertEqual(desconhecido.status_code, 404)
        www = self.client.get("/", HTTP_HOST="www.viralmedia.vip")
        self.assertEqual(www.status_code, 404)

    def test_admin_so_no_host_da_equipe(self):
        entrada = self.client.get("/admin/login/", HTTP_HOST="arquivos.viralmedia.vip")
        self.assertEqual(entrada.status_code, 200)
        self.assertContains(entrada, "Viral Media")
        self.assertEqual(
            self.client.get("/admin/login/", HTTP_HOST="bbrubin123.viralmedia.vip").status_code,
            404,
        )
        self.assertEqual(
            self.client.get("/admin/", HTTP_HOST="portal.viralmedia.vip").status_code,
            404,
        )
        equipe = self.client.get("/", HTTP_HOST="arquivos.viralmedia.vip")
        self.assertContains(equipe, "Abrir o admin")
        plataforma = self.client.get("/", HTTP_HOST="portal.viralmedia.vip")
        self.assertEqual(plataforma.status_code, 200)
        self.assertNotContains(plataforma, "Abrir o admin")
        self.assertNotContains(plataforma, TITULO_BOB)

        User.objects.create_superuser("antonio", "antonio@example.com", "senha-staff-12345")
        self.assertTrue(self.client.login(username="antonio", password="senha-staff-12345"))
        painel = self.client.get("/admin/", HTTP_HOST="arquivos.viralmedia.vip")
        self.assertEqual(painel.status_code, 200)
        self.assertContains(painel, "Pedidos")
        self.assertContains(painel, "Clientes")
        ficha = self.client.get(
            f"/admin/entregas/pedido/{self.pedido_bob.pk}/change/",
            HTTP_HOST="arquivos.viralmedia.vip",
        )
        self.assertContains(ficha, NOTA)

    def test_cliente_nao_abre_o_admin(self):
        self._entrar("bbrubin123", "bob")
        resposta = self.client.get(
            "/admin/entregas/pedido/",
            HTTP_HOST="arquivos.viralmedia.vip",
            follow=True,
        )
        self.assertNotContains(resposta, NOTA)

    def test_host_com_porta_e_ip(self):
        pagina = self.client.get("/entrar/", HTTP_HOST="bbrubin123.viralmedia.vip:8443")
        self.assertContains(pagina, "Bob Rubin")
        local = self.client.get("/", HTTP_HOST="127.0.0.1:8000")
        self.assertContains(local, "Abrir o admin")

    def test_ignora_x_forwarded_host(self):
        resposta = self.client.get(
            "/",
            HTTP_HOST="arquivos.viralmedia.vip",
            HTTP_X_FORWARDED_HOST="bbrubin123.viralmedia.vip",
        )
        self.assertContains(resposta, "Abrir o admin")
        self.assertNotContains(resposta, TITULO_BOB)

    def test_media_nao_e_publico_e_sair_e_post(self):
        caminho = self.arquivo_bob.arquivo.name
        resposta = self.client.get(f"/media/{caminho}", HTTP_HOST="bbrubin123.viralmedia.vip")
        self.assertEqual(resposta.status_code, 404)
        self.assertNotEqual(resposta.content, b"conteudo-bob")
        self._entrar("bbrubin123", "bob")
        self.assertEqual(
            self.client.get("/sair/", HTTP_HOST="bbrubin123.viralmedia.vip").status_code,
            405,
        )
        self.assertEqual(
            self.client.post("/sair/", HTTP_HOST="bbrubin123.viralmedia.vip").status_code,
            302,
        )

    def test_login_respeita_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        host = "bbrubin123.viralmedia.vip"
        pagina = cliente.get("/entrar/", HTTP_HOST=host)
        self.assertContains(pagina, "csrfmiddlewaretoken")
        token = str(pagina.context["csrf_token"])
        resposta = cliente.post(
            "/entrar/",
            {"username": "bob", "password": SENHA, "csrfmiddlewaretoken": token},
            HTTP_HOST=host,
        )
        self.assertEqual(resposta.status_code, 302)
        lista = cliente.get("/", HTTP_HOST=host)
        self.assertContains(lista, TITULO_BOB)

    def test_robots(self):
        resposta = self.client.get("/robots.txt", HTTP_HOST="bbrubin123.viralmedia.vip")
        self.assertContains(resposta, "Disallow: /")
