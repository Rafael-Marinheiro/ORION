from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import AuditoriaSubmissaoRodada, CEOGrupoRodada, Decisao, GameConfig, Grupo, Jogo, Rodada, User


class GerenciamentoJogoViewTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email_usuario="professor@teste.com", nome_usuario="Professor",
            password="senha123", tipo_usuario="gamemaster",
        )
        self.usuario = User.objects.create_user(
            email_usuario="ceo@teste.com", nome_usuario="CEO Vega", password="senha123"
        )
        self.jogo = Jogo.objects.create(nome="Turma A", config=GameConfig.objects.create())
        self.vega = Grupo.objects.create(nome="Equipe Vega", jogo=self.jogo)
        self.rigel = Grupo.objects.create(nome="Equipe Rigel", jogo=self.jogo)
        self.outro_jogo = Jogo.objects.create(nome="Turma B", config=GameConfig.objects.create())
        self.outra_equipe = Grupo.objects.create(nome="Equipe Oculta", jogo=self.outro_jogo)

    def test_exibe_status_de_submissao_por_grupo_na_rodada_aberta(self):
        rodada = Rodada.objects.create(
            jogo=self.jogo, numero=1, fim=timezone.now() + timedelta(hours=1)
        )
        CEOGrupoRodada.objects.create(grupo=self.vega, rodada=1, usuario=self.usuario)
        decisao = Decisao.objects.create(grupo=self.vega, rodada=1, descricao="Decisão", quantidade=1)
        AuditoriaSubmissaoRodada.objects.create(
            grupo=self.vega, rodada=1, usuario=self.usuario, decisao=decisao
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("gerenciamento_jogo"))

        self.assertContains(response, "Turma A · Rodada 1")
        self.assertContains(response, "1 de 2")
        self.assertContains(response, "1 pendente")
        self.assertContains(response, "Equipe Vega")
        self.assertContains(response, "CEO Vega")
        self.assertContains(response, "Enviado")
        self.assertContains(response, "Equipe Rigel")
        self.assertContains(response, "Pendente")
        self.assertNotContains(response, "Equipe Oculta")

    def test_rodada_de_prazo_vencido_continua_na_tela(self):
        """11.1: quem fecha a rodada e o servico automatico.

        Ate 25/09/2026 a tela filtrava por `fim > agora`: a rodada sumia no
        instante do prazo. Se o fechamento automatico estivesse parado, o
        professor lia "nenhuma rodada em andamento" e nao havia sinal algum
        de que o prazo tinha vencido sem processamento.
        """
        Rodada.objects.create(
            jogo=self.jogo, numero=1, fim=timezone.now() - timedelta(minutes=10)
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("gerenciamento_jogo"))

        self.assertContains(response, "aguardando fechamento")
        self.assertTrue(response.context["paineis"][0]["vencida"])

    def test_rodada_fechada_sai_da_tela(self):
        Rodada.objects.create(
            jogo=self.jogo, numero=1,
            fim=timezone.now() - timedelta(minutes=10), fechada=True,
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("gerenciamento_jogo"))

        self.assertEqual(response.context["paineis"], [])
        self.assertContains(response, "Nenhuma rodada em andamento")

    def test_a_tela_da_acesso_a_abertura_da_rodada(self):
        """10.3 poe "Abrir / Fechar rodada" nesta tela, nao so no menu."""
        self.client.force_login(self.admin)

        response = self.client.get(reverse("gerenciamento_jogo"))

        self.assertContains(response, reverse("abrir_rodada"))

    def test_restringe_a_tela_ao_administrador(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("gerenciamento_jogo"))

        self.assertEqual(response.status_code, 403)
